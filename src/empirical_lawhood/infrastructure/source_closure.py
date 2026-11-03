"""Authenticate selected committed source, retaining historical clean closures.

SPDX-License-Identifier: MPL-2.0
"""

from dataclasses import dataclass, replace
from hashlib import sha1, sha256
from io import BytesIO
import os
from pathlib import Path
import stat
import tarfile

from empirical_lawhood.infrastructure.bounded_process import BoundedProcessError, run_bounded_command
from empirical_lawhood.infrastructure.study_issue import GitStudySourceClosureInspector
from empirical_lawhood.infrastructure.source_origin import (
    require_executing_target_source,
)
from empirical_lawhood.infrastructure.repository_identity import _descriptor_identity, _open_relative_read_only
from empirical_lawhood.infrastructure.source_policy import (
    CheckoutSourceAdmission, InstalledSourceAdmission, SourcePolicyError, inspect_checkout_source, is_work_plan_path, require_unchanged_source_admission,
)
from empirical_lawhood.planning.study_issue import (
    ImplementationSourceClosure, SelectedSourceManifest, SelectedSourceManifestMember, SourceClosureKind,
)

_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
_SOURCE_ROOTS = ("src/empirical_lawhood", "scripts")


@dataclass(frozen=True, slots=True)
class TrackedSourceMember:
    relative_path: str
    mode: str
    size_bytes: int
    sha256: str

    def to_mapping(self):
        return {"relative_path": self.relative_path, "mode": self.mode,
                "size_bytes": self.size_bytes, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class AdmittedTargetSource:
    """Operational committed-source observation; never a legacy clean closure."""

    implementation_commit: str
    implementation_sha256: str
    source_tree_sha256: str
    tracked_files: tuple[TrackedSourceMember, ...]
    source_admission: CheckoutSourceAdmission | InstalledSourceAdmission
    final_source_admission: CheckoutSourceAdmission | InstalledSourceAdmission

    def to_mapping(self):
        return {"implementation_commit": self.implementation_commit,
                "implementation_sha256": self.implementation_sha256,
                "source_tree_sha256": self.source_tree_sha256,
                "tracked_files": tuple(row.to_mapping() for row in self.tracked_files),
                "source_admission": self.source_admission.to_mapping(),
                "final_source_admission": self.final_source_admission.to_mapping()}


@dataclass(frozen=True, slots=True)
class CapturedTargetClosure:
    """Scientific source records plus their separate operational disclosure."""

    closure: ImplementationSourceClosure
    manifest: SelectedSourceManifest
    source: AdmittedTargetSource


def capture_target_closure(root: Path, closure_id: str, *, _admitted_source=None) -> CapturedTargetClosure:
    """Capture a new exact selected-source closure without a raw-clean gate.

    Retain ``manifest`` and the separate ``source`` observation through the
    existing provenance owner. Current consumers reobserve the retained closure
    with the source inspector; they must not recapture and compare the historical
    raw-clean flag after unrelated documentary changes.
    """
    if _admitted_source is None:
        source = capture_admitted_target_source(root)
    else:
        source = _observe_admitted_target_source_current(root, _admitted_source)
    by_path = {row.relative_path: row for row in source.tracked_files}
    members = tuple(SelectedSourceManifestMember(name, by_path[name].mode,
        by_path[name].size_bytes, by_path[name].sha256) for name in source.source_admission.selected_paths)
    manifest = SelectedSourceManifest(closure_id + ".selected-source-manifest", source.implementation_commit,
        source.implementation_sha256, source.source_tree_sha256, members)
    closure = ImplementationSourceClosure(closure_id, SourceClosureKind.EXACT_SOURCE_CLOSURE,
        source.implementation_commit, source.implementation_sha256, source.source_tree_sha256,
        source.final_source_admission.observed_checkout_clean, manifest.identity)
    return CapturedTargetClosure(closure, manifest, source)


def _matches_regular_git_mode(permissions, git_mode):
    if permissions & ~0o777:
        return False
    # Git's executable flag follows owner execute. A non-executable source
    # also refuses newly introduced group/other execution permissions.
    return bool(permissions & stat.S_IXUSR) if git_mode == "100755" else not permissions & 0o111


def _archive_census(tree, archive):
    """Join every committed blob to archive bytes without extracting a tree."""
    entries = {}
    for row in tree.split(b"\0"):
        if not row:
            continue
        metadata, path = row.split(b"\t", 1)
        mode, kind, digest = metadata.decode("ascii").split(" ")
        name = path.decode("utf-8")
        if (kind != "blob" or mode not in ("100644", "100755", "120000") or name in entries
                or not name or name.startswith("/") or ".." in name.split("/")):
            raise SourcePolicyError("committed source census contains unsupported or repeated members")
        entries[name] = (mode, digest)
    members = {}
    with tarfile.open(fileobj=BytesIO(archive), mode="r:") as packet:
        for member in packet:
            if member.isdir():
                continue
            if member.name not in entries or member.name in members:
                raise SourcePolicyError("source archive changes the complete committed member census")
            mode, digest = entries[member.name]
            if mode == "120000" and member.issym():
                raw = member.linkname.encode("utf-8")
            elif mode != "120000" and member.isfile():
                stream = packet.extractfile(member)
                if stream is None:
                    raise SourcePolicyError("source archive omits committed file bytes")
                with stream:
                    raw = stream.read()
                # Git records executable status, not group/world write bits.
                # `git archive` applies tar.umask (default 0002), producing
                # 0664/0775 for ordinary 100644/100755 tree members. Keep the
                # exact tree mode in the census and authenticate archive bytes;
                # reject executable changes and special permission bits.
                if not _matches_regular_git_mode(member.mode, mode):
                    raise SourcePolicyError("source archive changes a committed file mode")
            else:
                raise SourcePolicyError("source archive substitutes a committed member type")
            if sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest() != digest:
                raise SourcePolicyError("source archive changes original committed blob bytes")
            members[member.name] = TrackedSourceMember(member.name, mode, len(raw), sha256(raw).hexdigest())
    if not entries or set(entries) != set(members):
        raise SourcePolicyError("source archive omits members of the complete committed tree")
    return tuple(members[name] for name in sorted(members))


def _source_path_census(root):
    names = set()
    for directory in _SOURCE_ROOTS:
        selected = root / directory
        if selected.is_symlink() or not selected.is_dir():
            raise SourcePolicyError("selected executable source root is absent or symbolic")
        for path in selected.rglob("*"):
            relative = path.relative_to(root)
            if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo"):
                continue
            if path.is_symlink():
                raise SourcePolicyError("selected executable source census refuses symbolic members")
            if is_work_plan_path(relative.as_posix()):
                metadata = path.lstat()
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o111:
                    raise SourcePolicyError("excluded work plans must be regular non-executable files")
                continue
            if path.is_file():
                names.add(relative.as_posix())
            elif not path.is_dir():
                raise SourcePolicyError("selected executable source census refuses nonregular members")
    return names


def _verify_selected_member(root, member):
    if member.mode not in ("100644", "100755"):
        raise SourcePolicyError("selected executable/configuration/input must be a regular committed file")
    descriptor = _open_relative_read_only(str(root), member.relative_path)
    try:
        before = os.fstat(descriptor)
        permissions = stat.S_IMODE(before.st_mode)
        if (not stat.S_ISREG(before.st_mode) or before.st_size != member.size_bytes
                or not _matches_regular_git_mode(permissions, member.mode)):
            raise SourcePolicyError("selected source file type, mode or size differs from its committed identity")
        digest, size = sha256(), 0
        while size < member.size_bytes:
            raw = os.read(descriptor, min(1024 * 1024, member.size_bytes - size))
            if not raw:
                raise SourcePolicyError("selected source file was truncated during authentication")
            digest.update(raw)
            size += len(raw)
        if os.read(descriptor, 1) or digest.hexdigest() != member.sha256:
            raise SourcePolicyError("selected executable/configuration/input bytes differ from the committed source")
        after = os.fstat(descriptor)
        if _descriptor_identity(before) != _descriptor_identity(after):
            raise SourcePolicyError("selected source file changed during authentication")
        return _descriptor_identity(after)
    finally:
        os.close(descriptor)


def capture_admitted_target_source(root: Path, *, selected_paths: tuple[str, ...] = ()) -> AdmittedTargetSource:
    """Authenticate the selected executable/configuration/input bytes at HEAD.

    Complete package resources, scripts, the dependency lock and project config
    are owning executable/environment selections. Callers add exact tracked
    input/configuration paths. Other tracked prose may differ. This does not
    create a scientific source closure, bundle, execution grant or output file.
    """
    root = root.resolve(strict=True)
    if (root / "empirical-lawhood-source.json").exists():
        from empirical_lawhood.infrastructure.selected_candidate import installed_candidate

        candidate = installed_candidate(source_root=root)
        by_path = {row.relative_path: row for row in candidate.tracked_files}
        selected = tuple(sorted({name for name in by_path
            if any(name.startswith(prefix + "/") for prefix in _SOURCE_ROOTS)}
            | {"pyproject.toml", "uv.lock"} | set(selected_paths)))
        if any(name not in by_path for name in selected):
            raise SourcePolicyError("selected input is not part of the installed candidate source")
        # The selected-candidate guard checks current package bytes. Extra
        # copied source inputs remain independently authenticated at their use.
        for name in selected_paths:
            _verify_selected_member(root, by_path[name])
        observation = InstalledSourceAdmission(sha256(candidate.source_bytes).hexdigest(), selected)
        return AdmittedTargetSource(candidate.implementation_commit, candidate.implementation_sha256,
            candidate.source_tree_sha256, candidate.tracked_files, observation, observation)
    require_executing_target_source(root)
    CheckoutSourceAdmission(b"", None, selected_paths)
    commit = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
    tree = _git(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD")
    archive = _git(root, "archive", "HEAD")
    members = _archive_census(tree, archive)
    by_path = {row.relative_path: row for row in members}
    committed_sources = {name for name, member in by_path.items()
        if any(name.startswith(prefix + "/") for prefix in _SOURCE_ROOTS)
        and not (is_work_plan_path(name) and member.mode == "100644")}
    if _source_path_census(root) != committed_sources:
        raise SourcePolicyError("actual executable source census differs from its complete committed selection")
    selected = tuple(sorted(committed_sources | {"pyproject.toml", "uv.lock"} | set(selected_paths)))
    if any(name not in by_path for name in selected):
        raise SourcePolicyError("selected configuration or input is not a member of the committed tree")
    initial = inspect_checkout_source(root, _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        selected_paths=selected)
    snapshots = {name: _verify_selected_member(root, by_path[name]) for name in selected}
    final = inspect_checkout_source(root, _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        selected_paths=selected)
    require_unchanged_source_admission(initial, final)
    if (_git(root, "rev-parse", "HEAD").decode("ascii").strip() != commit
            or _git(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD") != tree
            or _source_path_census(root) != committed_sources):
        raise SourcePolicyError("selected commit, tree or executable source census changed during capture")
    for name, expected in snapshots.items():
        descriptor = _open_relative_read_only(str(root), name)
        try:
            if _descriptor_identity(os.fstat(descriptor)) != expected:
                raise SourcePolicyError("selected source member changed before capture completed")
        finally:
            os.close(descriptor)
    require_executing_target_source(root)
    return AdmittedTargetSource(commit, sha256(archive).hexdigest(), sha256(tree).hexdigest(), members, initial, final)


def require_admitted_target_source_current(root: Path, admitted: AdmittedTargetSource) -> None:
    """Recheck all actual selected bytes and membership; confer no authority."""
    _observe_admitted_target_source_current(root, admitted)


def _observe_admitted_target_source_current(root: Path, admitted: AdmittedTargetSource) -> AdmittedTargetSource:
    """Recheck the operation's census and retain fresh actual observations.

    No archive is reconstructed and no source identity or permission is issued.
    Callers needing operational status receive the actual before/final snapshots.
    """
    if type(admitted) is not AdmittedTargetSource:
        raise TypeError("source recheck requires the actual admitted current source")
    root = root.resolve(strict=True)
    if (type(admitted.tracked_files) is not tuple or not admitted.tracked_files
            or any(type(member) is not TrackedSourceMember for member in admitted.tracked_files)):
        raise TypeError("source recheck requires its complete immutable tracked census")
    names = tuple(member.relative_path for member in admitted.tracked_files)
    if names != tuple(sorted(set(names))):
        raise SourcePolicyError("source recheck changes sorted unique committed membership")
    by_path = {member.relative_path: member for member in admitted.tracked_files}
    expected_sources = {name for name, member in by_path.items()
        if any(name.startswith(prefix + "/") for prefix in _SOURCE_ROOTS)
        and not (is_work_plan_path(name) and member.mode == "100644")}
    if type(admitted.source_admission) is not type(admitted.final_source_admission):
        raise TypeError("source recheck changes its checkout or installed observation kind")
    for admission in (admitted.source_admission, admitted.final_source_admission):
        if type(admission) not in (CheckoutSourceAdmission, InstalledSourceAdmission):
            raise TypeError("source recheck requires the exact installed or checkout source scope")
        admission.__post_init__()
        selected = set(admission.selected_paths)
        if not expected_sources | {"pyproject.toml", "uv.lock"} <= selected <= set(by_path):
            raise SourcePolicyError("source recheck loses its complete selected package, script, build or lock scope")
    require_unchanged_source_admission(admitted.source_admission, admitted.final_source_admission)
    if type(admitted.final_source_admission) is InstalledSourceAdmission:
        from empirical_lawhood.infrastructure.selected_candidate import installed_candidate

        candidate = installed_candidate(source_root=root)
        if (candidate.implementation_commit, candidate.implementation_sha256, candidate.source_tree_sha256,
                candidate.tracked_files) != (admitted.implementation_commit, admitted.implementation_sha256,
                admitted.source_tree_sha256, admitted.tracked_files):
            raise SourcePolicyError("selected installed source identity changed during the operation")
        observation = InstalledSourceAdmission(sha256(candidate.source_bytes).hexdigest(),
            admitted.final_source_admission.selected_paths)
        require_unchanged_source_admission(admitted.final_source_admission, observation)
        if _source_path_census(root) != expected_sources:
            raise SourcePolicyError("selected installed source membership changed during the operation")
        for name in observation.selected_paths:
            _verify_selected_member(root, by_path[name])
        if _source_path_census(root) != expected_sources:
            raise SourcePolicyError("selected installed source membership changed during the final guard")
        return replace(admitted, source_admission=observation, final_source_admission=observation)
    if type(admitted.final_source_admission) is not CheckoutSourceAdmission:
        raise TypeError("source recheck requires the exact installed or checkout source scope")
    require_executing_target_source(root)
    selected = admitted.final_source_admission.selected_paths
    if (_git(root, "rev-parse", "HEAD").decode("ascii").strip() != admitted.implementation_commit
            or _source_path_census(root) != expected_sources):
        raise SourcePolicyError("selected commit or executable source membership changed during the operation")
    before = inspect_checkout_source(root, _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        selected_paths=selected)
    require_unchanged_source_admission(admitted.final_source_admission, before)
    for name in selected:
        _verify_selected_member(root, by_path[name])
    after = inspect_checkout_source(root, _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        selected_paths=selected)
    require_unchanged_source_admission(before, after)
    if (_git(root, "rev-parse", "HEAD").decode("ascii").strip() != admitted.implementation_commit
            or _source_path_census(root) != expected_sources):
        raise SourcePolicyError("selected commit or executable source membership changed during the final guard")
    require_executing_target_source(root)
    return replace(admitted, source_admission=before, final_source_admission=after)


def _git(root: Path, *arguments: str) -> bytes:
    limits = {
        "rev-parse": 128,
        "status": GitStudySourceClosureInspector._MAX_STATUS_BYTES,
        "ls-tree": GitStudySourceClosureInspector._MAX_TREE_BYTES,
        "archive": _MAX_ARCHIVE_BYTES,
    }
    if not arguments or arguments[0] not in limits:
        raise ValueError("unsupported target source capture operation")
    try:
        result = run_bounded_command(
            ("git", *arguments),
            cwd=root,
            timeout_seconds=60,
            maximum_stdout_bytes=limits[arguments[0]],
            maximum_stderr_bytes=64 * 1024,
        )
    except BoundedProcessError as error:
        raise PermissionError(f"target source capture failed: {error}") from error
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise PermissionError(
            f"target source capture failed: {message or result.returncode}"
        )
    return result.stdout


def capture_clean_target_closure(
    root: Path, closure_id: str
) -> ImplementationSourceClosure:
    """Historical raw-clean closure; use the separate admitted-source companion for new source selections."""
    root = root.resolve(strict=True)
    require_executing_target_source(root)
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise PermissionError("fresh native authoring requires a clean target commit")
    archive = _git(root, "archive", "HEAD")
    if len(archive) > _MAX_ARCHIVE_BYTES:
        raise ValueError("target source archive exceeds the bounded authoring limit")
    closure = ImplementationSourceClosure(
        closure_id,
        SourceClosureKind.CLEAN_GIT_COMMIT,
        _git(root, "rev-parse", "HEAD").decode("ascii").strip(),
        sha256(archive).hexdigest(),
        sha256(_git(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD")).hexdigest(),
        True,
    )
    GitStudySourceClosureInspector(root).observe(closure)
    return closure
