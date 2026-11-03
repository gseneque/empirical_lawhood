# SPDX-License-Identifier: MPL-2.0
"""In-memory source-policy adversaries; no fixture files or Git repositories."""

from dataclasses import replace
from hashlib import sha1, sha256
from io import BytesIO
import os
from pathlib import Path
import stat
import tarfile
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure import repository_identity as repository
from empirical_lawhood.infrastructure import source_policy as owner
from empirical_lawhood.infrastructure import source_closure as capture
from empirical_lawhood.infrastructure.study_issue import GitStudySourceClosureInspector
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.study_issue import SelectedSourceManifest, SelectedSourceManifestMember, SourceClosureKind


ROOT = Path(__file__).resolve().parents[1]
STATUS = b"?? WTF.md\n"


class PlanFilesystem:
    """Only the two admitted descriptors exist; every operation stays in memory."""

    def __init__(self):
        self.payload = b"separately disclosed operational plan\n"
        self.mode = stat.S_IFREG | 0o644
        self.present = True
        self.offset = self.reads = self.observations = 0
        self.declared_size = None
        self.changed_descriptor = self.replaced_path = False
        self.opens, self.closed = [], []

    def metadata(self, *, inode=23):
        return SimpleNamespace(st_dev=7, st_ino=inode, st_mode=self.mode, st_nlink=1,
            st_size=len(self.payload) if self.declared_size is None else self.declared_size,
            st_mtime_ns=41, st_ctime_ns=43)

    def open(self, path, flags, *, dir_fd=None):
        self.opens.append((path, flags, dir_fd))
        if dir_fd is None:
            assert path == ROOT and flags & os.O_DIRECTORY and flags & os.O_NOFOLLOW
            return 11
        assert dir_fd == 11 and path == owner.LOCAL_PLAN_NAME
        assert flags & os.O_NOFOLLOW and flags & os.O_NONBLOCK
        if not self.present:
            raise FileNotFoundError(path)
        if stat.S_ISLNK(self.mode):
            raise OSError("no-follow symlink refusal")
        return 12

    def fstat(self, descriptor):
        assert descriptor == 12
        self.observations += 1
        return self.metadata(inode=29 if self.changed_descriptor and self.observations > 1 else 23)

    def stat(self, path, *, dir_fd, follow_symlinks):
        assert path == owner.LOCAL_PLAN_NAME and dir_fd == 11 and not follow_symlinks
        if not self.present:
            raise FileNotFoundError(path)
        return self.metadata(inode=29 if self.replaced_path else 23)

    def read(self, descriptor, size):
        assert descriptor == 12
        self.reads += 1
        raw = self.payload[self.offset:self.offset + size]
        self.offset += len(raw)
        return raw

    def close(self, descriptor):
        self.closed.append(descriptor)


@pytest.fixture
def memory_filesystem(monkeypatch):
    filesystem = PlanFilesystem()
    virtual_os = SimpleNamespace(**{name: getattr(os, name) for name in
        ("O_RDONLY", "O_NOFOLLOW", "O_NONBLOCK", "O_DIRECTORY", "O_CLOEXEC")},
        open=filesystem.open, fstat=filesystem.fstat, stat=filesystem.stat,
        read=filesystem.read, close=filesystem.close)
    monkeypatch.setattr(owner, "os", virtual_os)
    return filesystem


@pytest.mark.parametrize("status", (STATUS, b"?? WTF.md\0"))
def test_local_plan_admission_retains_raw_dirty_status_and_exact_separate_disclosure(memory_filesystem, status):
    admission = owner.inspect_checkout_source(ROOT, status)
    assert admission.raw_status == status and admission.observed_checkout_clean is False
    assert admission.local_plan == owner.LocalPlanDisclosure(owner.LOCAL_PLAN_NAME,
        len(memory_filesystem.payload), sha256(memory_filesystem.payload).hexdigest(), 0o644)
    assert admission.to_mapping() == {"policy": "selected-source-identities-v1",
        "raw_status_sha256": sha256(status).hexdigest(), "observed_checkout_clean": False,
        "changes": ({"status": "??", "relative_path": "WTF.md", "original_path": None},),
        "selected_paths": (), "selected_path_changes": (),
        "local_plan": admission.local_plan.to_mapping()}
    assert memory_filesystem.closed == [12, 11]


def test_empty_status_is_clean_only_when_no_undisclosed_plan_exists(memory_filesystem):
    memory_filesystem.present = False
    admission = owner.inspect_checkout_source(ROOT, b"")
    assert admission.observed_checkout_clean is True and admission.local_plan is None
    assert memory_filesystem.reads == 0 and memory_filesystem.closed == [11]


def test_ignored_or_tracked_plan_cannot_silently_disappear_from_the_disclosure(memory_filesystem):
    with pytest.raises(owner.SourcePolicyError, match="explicit untracked"):
        owner.inspect_checkout_source(ROOT, b"")
    assert memory_filesystem.reads == 0 and memory_filesystem.closed == [11]


@pytest.mark.parametrize("status", (b"!! WTF.md\0", b" M WTF.md\0", STATUS + STATUS))
def test_plan_exception_requires_one_exact_untracked_root_record(memory_filesystem, status):
    with pytest.raises(owner.SourcePolicyError, match="explicit untracked"):
        owner.inspect_checkout_source(ROOT, status)
    assert memory_filesystem.reads == 0


@pytest.mark.parametrize("status", (
    b"?? WTF.md", b"?? WTF.md\n\n", b"bad\n",
    b"XX tracked.py\0", b'?? "WTF.md"\n', b"R  old.py -> new.py\n",
    b"R  new.py\0", b"R  new.py\0\0",
))
def test_malformed_or_ambiguous_git_status_refuses_before_reads(memory_filesystem, status):
    with pytest.raises(owner.SourcePolicyError, match="terminator|malformed|NUL|original path"):
        owner.inspect_checkout_source(ROOT, status)
    assert memory_filesystem.opens == [] and memory_filesystem.reads == 0


def test_unrelated_prose_and_untracked_notes_are_diagnostics_not_a_clean_status_gate(memory_filesystem):
    status = b" M docs/unrelated.md\0?? notes.txt\0?? WTF.md\0"
    admission = owner.inspect_checkout_source(ROOT, status, selected_paths=("src/selected.py", "uv.lock"))
    assert not admission.observed_checkout_clean and admission.selected_path_changes == ()
    assert tuple(row.relative_path for row in admission.changes) == (
        "docs/unrelated.md", "notes.txt", "WTF.md")
    assert admission.local_plan.sha256 == sha256(memory_filesystem.payload).hexdigest()


def test_selected_path_status_is_explicit_diagnostic_and_does_not_claim_byte_authentication(memory_filesystem):
    status = b" M src/selected.py\0?? WTF.md\0"
    admission = owner.inspect_checkout_source(ROOT, status, selected_paths=("src/selected.py",))
    assert admission.selected_path_changes == (owner.CheckoutPathChange(" M", "src/selected.py"),)


def test_nul_rename_preserves_both_exact_paths_and_selected_scope(memory_filesystem):
    memory_filesystem.present = False
    admission = owner.inspect_checkout_source(ROOT, b"R  docs/new name.md\0docs/old name.md\0",
        selected_paths=("docs/old name.md",))
    assert admission.selected_path_changes == (
        owner.CheckoutPathChange("R ", "docs/new name.md", "docs/old name.md"),)


@pytest.mark.parametrize("paths", (["src/code.py"], ("../outside.py",), ("/outside.py",),
    ("src//code.py",), ("src/./code.py",), (".",), ("uv.lock", "src/code.py"), ("uv.lock", "uv.lock")))
def test_selected_scope_requires_sorted_unique_exact_tracked_relative_paths(memory_filesystem, paths):
    with pytest.raises(ValueError, match="exact selected-path scope"):
        owner.inspect_checkout_source(ROOT, STATUS, selected_paths=paths)
    assert memory_filesystem.opens == []


@pytest.mark.parametrize("mode", (stat.S_IFREG | 0o744, stat.S_IFREG | 0o654,
    stat.S_IFREG | 0o645, stat.S_IFIFO | 0o644, stat.S_IFDIR | 0o644))
def test_executable_or_nonregular_plan_refuses_before_content_read(memory_filesystem, mode):
    memory_filesystem.mode = mode
    with pytest.raises(owner.SourcePolicyError, match="regular non-executable"):
        owner.inspect_checkout_source(ROOT, STATUS)
    assert memory_filesystem.reads == 0 and memory_filesystem.closed == [12, 11]


def test_symbolic_link_plan_refuses_without_following_it(memory_filesystem):
    memory_filesystem.mode = stat.S_IFLNK | 0o777
    with pytest.raises(owner.SourcePolicyError, match="identity cannot be authenticated"):
        owner.inspect_checkout_source(ROOT, STATUS)
    assert memory_filesystem.reads == 0 and memory_filesystem.closed == [11]


def test_missing_plan_cannot_be_disclosed_by_status_alone(memory_filesystem):
    memory_filesystem.present = False
    with pytest.raises(owner.SourcePolicyError, match="identity cannot be authenticated"):
        owner.inspect_checkout_source(ROOT, STATUS)
    assert memory_filesystem.closed == [11]


@pytest.mark.parametrize("change", ("truncated", "grown", "descriptor", "path"))
def test_plan_content_extent_descriptor_and_path_are_sealed_before_return(memory_filesystem, change):
    if change == "truncated":
        memory_filesystem.declared_size = len(memory_filesystem.payload) + 1
    elif change == "grown":
        memory_filesystem.declared_size = len(memory_filesystem.payload) - 1
    elif change == "descriptor":
        memory_filesystem.changed_descriptor = True
    else:
        memory_filesystem.replaced_path = True
    with pytest.raises(owner.SourcePolicyError, match="truncated|grew|changed"):
        owner.inspect_checkout_source(ROOT, STATUS)
    assert memory_filesystem.closed == [12, 11]


def test_admission_comparison_preserves_plan_but_allows_unrelated_prose_status_changes():
    original = owner.CheckoutSourceAdmission(STATUS,
        owner.LocalPlanDisclosure(owner.LOCAL_PLAN_NAME, 4, "a" * 64, 0o644))
    owner.require_unchanged_source_admission(original, original)
    unrelated = owner.CheckoutSourceAdmission(STATUS + b" M docs/prose.md\n", original.local_plan)
    owner.require_unchanged_source_admission(original, unrelated)
    for changed in (owner.CheckoutSourceAdmission(b"", None), owner.CheckoutSourceAdmission(STATUS,
            owner.LocalPlanDisclosure(owner.LOCAL_PLAN_NAME, 4, "b" * 64, 0o644))):
        with pytest.raises(owner.SourcePolicyError, match="changed during source verification"):
            owner.require_unchanged_source_admission(original, changed)


def _repository_inputs(monkeypatch, observations):
    payload = b"exact committed input\n"
    status = observations[0].raw_status
    calls = []

    def git(root, *arguments, **kwargs):
        calls.append(arguments)
        if arguments[0] == "rev-parse":
            return b"a" * 40 + b"\n"
        if arguments[0] == "status":
            return status
        if arguments[0] == "ls-files":
            return b"input.json\n"
        assert arguments[0] == "show"
        return payload

    selected = iter(observations)
    monkeypatch.setattr(repository, "_git", git)
    monkeypatch.setattr(repository, "_read_exact_file_snapshot", lambda root, spec: (payload, ("stable",)))
    monkeypatch.setattr(repository, "_require_file_snapshot", lambda root, spec, snapshot: None)
    monkeypatch.setattr(repository, "inspect_checkout_source", lambda root, status, **kwargs: next(selected))
    specification = repository.RepositoryArtifactSpec("input.json", "input.original", "source",
        "empirical-lawhood/testing/original-input", "application/json", 1024)
    return specification, payload, calls


def test_explicit_repository_route_returns_disclosure_and_preserves_tracked_byte_identity(monkeypatch):
    admission = owner.CheckoutSourceAdmission(STATUS,
        owner.LocalPlanDisclosure(owner.LOCAL_PLAN_NAME, 4, "a" * 64, 0o644))
    specification, payload, calls = _repository_inputs(monkeypatch, (admission, admission))
    result = repository.load_admitted_repository_artifacts(ROOT,
        expected_commit="a" * 40, specifications=(specification,))
    assert result.source_admission is admission
    assert result.artifacts[0].sha256 == sha256(payload).hexdigest()
    assert result.artifacts[0].size_bytes == len(payload)
    assert sum(arguments[0] == "status" for arguments in calls) == 2


def test_repository_route_accepts_unrelated_prose_but_refuses_selected_byte_drift(monkeypatch):
    admission = owner.CheckoutSourceAdmission(b" M docs/prose.md\n", None)
    specification, payload, _ = _repository_inputs(monkeypatch, (admission, admission))
    result = repository.load_admitted_repository_artifacts(ROOT,
        expected_commit="a" * 40, specifications=(specification,))
    assert result.source_admission.observed_checkout_clean is False
    assert result.artifacts[0].sha256 == sha256(payload).hexdigest()
    _repository_inputs(monkeypatch, (admission, admission))
    monkeypatch.setattr(repository, "_read_exact_file_snapshot", lambda root, spec: (b"changed selected input", ("changed",)))
    with pytest.raises(repository.RepositoryIdentityError, match="differ from the expected commit"):
        repository.load_admitted_repository_artifacts(ROOT,
            expected_commit="a" * 40, specifications=(specification,))


def test_repository_refuses_selected_path_replacement_at_the_final_boundary(monkeypatch):
    admission = owner.CheckoutSourceAdmission(b" M docs/prose.md\n", None)
    specification, _, _ = _repository_inputs(monkeypatch, (admission, admission))

    def replaced(*args):
        raise repository.RepositoryIdentityError("selected repository input changed during verification")

    monkeypatch.setattr(repository, "_require_file_snapshot", replaced)
    with pytest.raises(repository.RepositoryIdentityError, match="changed during verification"):
        repository.load_admitted_repository_artifacts(ROOT,
            expected_commit="a" * 40, specifications=(specification,))


def test_historical_repository_api_still_refuses_raw_dirty_status(monkeypatch):
    admission = owner.CheckoutSourceAdmission(STATUS,
        owner.LocalPlanDisclosure(owner.LOCAL_PLAN_NAME, 4, "a" * 64, 0o644))
    specification, _, _ = _repository_inputs(monkeypatch, (admission,))
    with pytest.raises(repository.RepositoryIdentityError, match="clean worktree"):
        repository.load_clean_repository_artifacts(ROOT, expected_commit="a" * 40,
            specifications=(specification,))


def test_repository_read_refuses_changed_plan_at_final_source_check(monkeypatch):
    before = owner.CheckoutSourceAdmission(STATUS,
        owner.LocalPlanDisclosure(owner.LOCAL_PLAN_NAME, 4, "a" * 64, 0o644))
    after = owner.CheckoutSourceAdmission(STATUS,
        owner.LocalPlanDisclosure(owner.LOCAL_PLAN_NAME, 4, "b" * 64, 0o644))
    specification, _, _ = _repository_inputs(monkeypatch, (before, after))
    with pytest.raises(repository.RepositoryIdentityError, match="changed during source verification"):
        repository.load_admitted_repository_artifacts(ROOT, expected_commit="a" * 40,
            specifications=(specification,))


def _archive(files, *, archive_mode=0o644, git_mode="100644"):
    output, rows = BytesIO(), []
    with tarfile.open(fileobj=output, mode="w:") as packet:
        for name, raw in sorted(files.items()):
            member = tarfile.TarInfo(name)
            member.mode, member.size = archive_mode, len(raw)
            packet.addfile(member, BytesIO(raw))
            digest = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            rows.append(git_mode.encode() + b" blob " + digest.encode() + b"\t" + name.encode() + b"\0")
    return b"".join(rows), output.getvalue()


def test_complete_archive_census_authenticates_every_original_blob_without_extraction():
    files = {"src/empirical_lawhood/module.py": b"original code\n", "docs/prose.md": b"original prose\n"}
    tree, archive = _archive(files)
    members = capture._archive_census(tree, archive)
    assert tuple(row.relative_path for row in members) == tuple(sorted(files))
    assert all(row.sha256 == sha256(files[row.relative_path]).hexdigest()
        and row.size_bytes == len(files[row.relative_path]) and row.mode == "100644" for row in members)


@pytest.mark.parametrize("archive_mode,git_mode", ((0o664, "100644"), (0o775, "100755"),
    (0o600, "100644"), (0o700, "100755")))
def test_archive_permission_masks_preserve_original_tree_mode_and_blob(archive_mode, git_mode):
    raw = b"original committed source\n"
    tree, archive = _archive({"source.py": raw}, archive_mode=archive_mode, git_mode=git_mode)
    member, = capture._archive_census(tree, archive)
    assert member.mode == git_mode and member.sha256 == sha256(raw).hexdigest()


@pytest.mark.parametrize("archive_mode,git_mode", ((0o755, "100644"), (0o664, "100755"),
    (0o4644, "100644"), (0o2755, "100755"), (0o675, "100755")))
def test_archive_mode_refuses_executable_substitution_and_special_bits(archive_mode, git_mode):
    tree, archive = _archive({"source.py": b"original source"}, archive_mode=archive_mode, git_mode=git_mode)
    with pytest.raises(owner.SourcePolicyError, match="file mode"):
        capture._archive_census(tree, archive)


@pytest.mark.parametrize("damage", ("omitted", "changed", "extra", "mode", "gitlink"))
def test_archive_census_refuses_omissions_substitutions_modes_and_gitlinks(damage):
    files = {"source.py": b"original code\n", "docs/prose.md": b"original prose\n"}
    tree, archive = _archive(files)
    if damage == "omitted":
        del files["source.py"]
        _, archive = _archive(files)
    elif damage == "changed":
        files["source.py"] = b"modified code\n"
        _, archive = _archive(files)
    elif damage == "extra":
        files["extra.py"] = b"undeclared code\n"
        _, archive = _archive(files)
    elif damage == "mode":
        tree = tree.replace(b"100644", b"100755", 1)
    else:
        tree = tree.replace(b"100644 blob", b"160000 commit", 1)
    with pytest.raises(owner.SourcePolicyError, match="census|blob bytes|mode|unsupported|omits"):
        capture._archive_census(tree, archive)


@pytest.mark.parametrize("damage", (None, "bytes", "mode", "changed"))
def test_selected_source_authenticates_actual_bytes_mode_and_descriptor(memory_filesystem, monkeypatch, damage):
    expected = memory_filesystem.payload
    member = capture.TrackedSourceMember("src/empirical_lawhood/module.py", "100644", len(expected), sha256(expected).hexdigest())
    monkeypatch.setattr(capture, "os", owner.os)
    monkeypatch.setattr(capture, "_open_relative_read_only", lambda root, path: 12)
    if damage == "bytes":
        memory_filesystem.payload = b"x" * len(expected)
    elif damage == "mode":
        memory_filesystem.mode = stat.S_IFREG | 0o755
    elif damage == "changed":
        memory_filesystem.changed_descriptor = True
    if damage is None:
        capture._verify_selected_member(ROOT, member)
    else:
        with pytest.raises(owner.SourcePolicyError, match="bytes differ|mode or size|changed during"):
            capture._verify_selected_member(ROOT, member)
    assert memory_filesystem.closed == [12]


@pytest.mark.parametrize("physical_mode,git_mode", ((0o644, "100644"), (0o664, "100644"),
    (0o755, "100755"), (0o775, "100755")))
def test_selected_worktree_uses_git_executable_mode_without_requiring_permission_churn(memory_filesystem, monkeypatch, physical_mode, git_mode):
    raw = memory_filesystem.payload
    memory_filesystem.mode = stat.S_IFREG | physical_mode
    member = capture.TrackedSourceMember("src/empirical_lawhood/module.py", git_mode, len(raw), sha256(raw).hexdigest())
    monkeypatch.setattr(capture, "os", owner.os)
    monkeypatch.setattr(capture, "_open_relative_read_only", lambda root, path: 12)
    capture._verify_selected_member(ROOT, member)
    assert memory_filesystem.closed == [12]


@pytest.mark.parametrize("physical_mode,git_mode", ((0o4644, "100644"), (0o2644, "100644"),
    (0o1644, "100644"), (0o675, "100755")))
def test_selected_worktree_refuses_special_bits_or_missing_git_executable_flag(memory_filesystem, monkeypatch, physical_mode, git_mode):
    raw = memory_filesystem.payload
    memory_filesystem.mode = stat.S_IFREG | physical_mode
    member = capture.TrackedSourceMember("src/empirical_lawhood/module.py", git_mode, len(raw), sha256(raw).hexdigest())
    monkeypatch.setattr(capture, "os", owner.os)
    monkeypatch.setattr(capture, "_open_relative_read_only", lambda root, path: 12)
    with pytest.raises(owner.SourcePolicyError, match="mode or size"):
        capture._verify_selected_member(ROOT, member)


def _capture_inputs(monkeypatch):
    files = {"src/empirical_lawhood/module.py": b"original code\n", "scripts/tool.py": b"original tool\n",
        "uv.lock": b"original lock\n", "pyproject.toml": b"original config\n", "docs/prose.md": b"original prose\n"}
    files.update({name:b"archival operational instructions\n" for name in owner.NESTED_WORK_PLAN_PATHS})
    tree, archive = _archive(files)
    names = {"src/empirical_lawhood/module.py", "scripts/tool.py"}
    status = b" M docs/prose.md\0?? WTF.md\0"
    plan = owner.LocalPlanDisclosure(owner.LOCAL_PLAN_NAME, 5, "a" * 64, 0o644)
    observed = SimpleNamespace(st_dev=7, st_ino=23, st_mode=stat.S_IFREG | 0o644, st_nlink=1,
        st_size=4, st_mtime_ns=41, st_ctime_ns=43)

    def git(root, *arguments):
        if arguments[0] == "rev-parse":
            return b"a" * 40 + b"\n"
        if arguments[0] == "ls-tree":
            return tree
        if arguments[0] == "archive":
            return archive
        assert arguments[0] == "status"
        return status

    calls = []
    monkeypatch.setattr(capture, "_git", git)
    monkeypatch.setattr(capture, "require_executing_target_source", lambda root: calls.append("origin"))
    monkeypatch.setattr(capture, "_source_path_census", lambda root: names)
    monkeypatch.setattr(capture, "inspect_checkout_source", lambda root, raw, **kwargs:
        owner.CheckoutSourceAdmission(raw, plan, kwargs["selected_paths"]))
    monkeypatch.setattr(capture, "_verify_selected_member", lambda root, member: repository._descriptor_identity(observed))
    monkeypatch.setattr(capture, "_open_relative_read_only", lambda root, name: 77)
    monkeypatch.setattr(capture, "os", SimpleNamespace(fstat=lambda fd: observed, close=lambda fd: None))
    return files, names, calls, git


def test_committed_source_companion_allows_unrelated_prose_with_explicit_raw_dirty_disclosure(monkeypatch):
    files, _, calls, _ = _capture_inputs(monkeypatch)
    result = capture.capture_admitted_target_source(ROOT)
    assert result.implementation_commit == "a" * 40
    assert not result.source_admission.observed_checkout_clean
    assert result.source_admission.local_plan is not None
    assert result.source_admission.selected_paths == tuple(sorted(set(files) - {"docs/prose.md"} - owner.NESTED_WORK_PLAN_PATHS))
    assert len(result.tracked_files) == len(files) and calls == ["origin", "origin"]
    assert not hasattr(result, "clean_worktree")


def test_committed_source_capture_rejects_undeclared_executable_members(monkeypatch):
    _, names, _, _ = _capture_inputs(monkeypatch)
    names.add("src/empirical_lawhood/undeclared.py")
    with pytest.raises(owner.SourcePolicyError, match="census differs"):
        capture.capture_admitted_target_source(ROOT)


@pytest.mark.parametrize("mode",("100755","120000"))
def test_committed_archival_path_is_not_an_executable_or_symlink_exception(monkeypatch,mode):
    _capture_inputs(monkeypatch)
    original=capture._archive_census
    name=next(iter(owner.NESTED_WORK_PLAN_PATHS))
    monkeypatch.setattr(capture,"_archive_census",lambda tree,archive:tuple(
        replace(row,mode=mode) if row.relative_path==name else row for row in original(tree,archive)))
    with pytest.raises(owner.SourcePolicyError,match="census differs"):
        capture.capture_admitted_target_source(ROOT)


def test_foreign_loaded_origin_refuses_before_any_git_or_source_read(monkeypatch):
    calls = []

    def foreign(root):
        raise PermissionError("loaded module is outside selected source")

    monkeypatch.setattr(capture, "require_executing_target_source", foreign)
    monkeypatch.setattr(capture, "_git", lambda *args: calls.append(args))
    with pytest.raises(PermissionError, match="outside selected source"):
        capture.capture_admitted_target_source(ROOT)
    assert calls == []


def test_historical_clean_closure_still_refuses_raw_dirty_status(monkeypatch):
    _, _, _, _ = _capture_inputs(monkeypatch)
    with pytest.raises(PermissionError, match="clean target commit"):
        capture.capture_clean_target_closure(ROOT, "historical.clean-only")


def _selected_closure(monkeypatch):
    _capture_inputs(monkeypatch)
    source = capture.capture_admitted_target_source(ROOT)
    monkeypatch.setattr(capture, "capture_admitted_target_source", lambda root: source)
    return capture.capture_target_closure(ROOT, "source.current"), source


def test_current_closure_keeps_manifest_and_operational_disclosure_without_claiming_raw_clean(monkeypatch):
    captured, source = _selected_closure(monkeypatch)
    assert captured.closure.kind is SourceClosureKind.EXACT_SOURCE_CLOSURE
    assert captured.closure.clean_worktree is False
    assert captured.closure.exact_source_manifest == captured.manifest.identity
    assert tuple(member.relative_path for member in captured.manifest.members) == source.source_admission.selected_paths
    assert all(type(member) is SelectedSourceManifestMember for member in captured.manifest.members)
    assert captured.source is source and captured.source.source_admission.local_plan is not None
    assert not hasattr(captured.manifest, "raw_status") and not hasattr(captured.manifest, "local_plan")
    assert decode_canonical_bytes(captured.manifest.canonical_bytes(), SelectedSourceManifest,
        maximum_bytes=len(captured.manifest.canonical_bytes())) == captured.manifest


def test_current_inspector_reconstructs_manifest_and_preserves_original_raw_status_meaning(monkeypatch):
    captured, source = _selected_closure(monkeypatch)
    clean = owner.CheckoutSourceAdmission(b"", None, source.source_admission.selected_paths)
    changed_documentation_status = replace(source, source_admission=clean, final_source_admission=clean)
    monkeypatch.setattr(capture, "capture_admitted_target_source", lambda root: changed_documentation_status)
    inspector = GitStudySourceClosureInspector(ROOT)
    assert inspector.observe(captured.closure) is captured.closure
    assert captured.closure.clean_worktree is False


@pytest.mark.parametrize("damage", ("omitted", "extra", "manifest-id", "commit", "archive", "tree", "schema", "revision"))
def test_current_inspector_refuses_manifest_scope_or_source_identity_substitution(monkeypatch, damage):
    captured, _ = _selected_closure(monkeypatch)
    expected = captured.closure
    if damage == "omitted":
        manifest = replace(captured.manifest, members=captured.manifest.members[:-1])
        expected = replace(expected, exact_source_manifest=manifest.identity)
    elif damage == "extra":
        member = SelectedSourceManifestMember("extra.py", "100644", 5, "b" * 64)
        manifest = replace(captured.manifest, members=tuple(sorted((*captured.manifest.members, member), key=lambda row: row.relative_path)))
        expected = replace(expected, exact_source_manifest=manifest.identity)
    elif damage == "manifest-id":
        expected = replace(expected, exact_source_manifest=replace(captured.manifest, manifest_id="source.other").identity)
    elif damage in ("commit", "archive", "tree"):
        field = {"commit": "implementation_commit", "archive": "implementation_sha256", "tree": "source_tree_sha256"}[damage]
        expected = replace(expected, **{field: "b" * (40 if damage == "commit" else 64)})
    else:
        pin = captured.manifest.identity
        expected = replace(expected, exact_source_manifest=ObjectIdentity(pin.object_id,
            "empirical-lawhood/testing/unsupported-source-manifest" if damage == "schema" else pin.object_schema,
            "9.0.0" if damage == "revision" else pin.object_version, pin.object_fingerprint))
    with pytest.raises(PermissionError, match="supported selected-source|identity changed"):
        GitStudySourceClosureInspector(ROOT).observe(expected)


@pytest.mark.parametrize("damage", ("list", "duplicate", "order", "nonregular", "negative-size"))
def test_manifest_constructor_requires_immutable_unique_exact_regular_member_records(monkeypatch, damage):
    captured, _ = _selected_closure(monkeypatch)
    members = captured.manifest.members
    with pytest.raises(ValueError, match="immutable|census|mode or size"):
        if damage == "list":
            replace(captured.manifest, members=list(members))
        elif damage == "duplicate":
            replace(captured.manifest, members=(members[0], *members))
        elif damage == "order":
            replace(captured.manifest, members=tuple(reversed(members)))
        elif damage == "nonregular":
            replace(members[0], mode="120000")
        else:
            replace(members[0], size_bytes=-1)
