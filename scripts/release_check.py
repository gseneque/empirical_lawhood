# SPDX-License-Identifier: MPL-2.0
"""Check selected committed source in the sole checkout and retain its packet."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import tarfile
import time
import tomllib
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    **{name: ((), ["tests", "-m", "not native and not held", "-p", "scripts.test_profiles",
                   "--test-profile", name]) for name in ("ci", "integration", "scale")},
    "portable": ((), ["tests", "-m", "not native and not held"]),
    "native-open": (("open-simulators", 'reaction-response-simulators'),
                    ["tests", "-m", "native", "--ignore=tests/test_brian2_native_science.py"]),
    "native-brian2": ((), ["tests/test_brian2_native_science.py", "-m", "native"]),
    "held-reactor": ((), ["tests/test_reactor_batch_input.py", "tests/test_reactor_prepared_input.py",
                          "tests/test_reactor_held_native_science.py", "tests/test_reactor_upstream_binding.py", "-m", "held"]),
    "held-response": ((), ['tests/test_prepared_response_held_source.py', 'tests/test_information_prediction_held_source.py',
                      'tests/test_causal_contrasts_held_source.py', 'tests/test_finite_response_assignment.py',
                      'tests/test_finite_response_stage_input.py', "-m", "held"]),
}


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()



def retained_test_options(packet: Path) -> list[str]:
    """Keep all disclosed control bodies at their selected custody destination."""
    return ["--basetemp", str(packet / "test-artifacts"),
            "-o", f"cache_dir={packet / 'pytest-cache'}",
            "-o", "tmp_path_retention_policy=all", "-o", "tmp_path_retention_count=1"]


def portable_test_environment_policy(packet: Path, checkout: Path) -> dict[str, object]:
    """Bind the once-only portable suite's retained fixtures and coverage owner."""
    return {"pytest_addopts": None, "tmp_path_retention_policy": "all",
            "tmp_path_retention_count": 1, "basetemp": str(packet / "test-artifacts"),
            "coverage_rcfile_sha256": digest((checkout / ".coveragerc").read_bytes())}


def seal_log_snapshot(live: Path, snapshot: Path) -> tuple[int, str]:
    """Bind a new inode to at most the bytes observed when capture stopped.

    A descendant can retain the live inode after subprocess.run returns or is interrupted.
    Renaming that file would not freeze the evidence recorded in the manifest.
    """
    checksum = hashlib.sha256()
    captured = 0
    with live.open("rb") as source, snapshot.open("xb") as destination:
        remaining = os.fstat(source.fileno()).st_size
        while remaining:
            chunk = source.read(min(remaining, 1024 * 1024))
            if not chunk:
                break
            destination.write(chunk)
            checksum.update(chunk)
            captured += len(chunk)
            remaining -= len(chunk)
    return captured, checksum.hexdigest()


def output(command: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def source_identity(root: Path) -> dict[str, object]:
    from empirical_lawhood.infrastructure.source_closure import capture_admitted_target_source

    if __package__:
        from .release_portable_evidence import candidate_inventory, release_input_paths
    else:
        from release_portable_evidence import candidate_inventory, release_input_paths
    selected_paths = release_input_paths(root, revision="HEAD")
    admitted = capture_admitted_target_source(root, selected_paths=selected_paths)
    commit = admitted.implementation_commit
    inventory = candidate_inventory(root, selected_paths=selected_paths, revision=commit, verify_selected=True)
    disclosure = release_source_disclosure(root, selected_paths)
    return {
        "commit": commit, "tree_object": output(["git", "rev-parse", commit + "^{tree}"], cwd=root),
        "tree_inventory_sha256": admitted.source_tree_sha256,
        "archive_sha256": admitted.implementation_sha256,
        "tracked_files": [member.to_mapping() for member in admitted.tracked_files],
        "selected_paths": list(selected_paths), "selected_inventory": inventory,
        "checkout_disclosure": disclosure,
        "tags_at_commit": output(["git", "tag", "--points-at", commit], cwd=root).splitlines(),
        "uv_lock_sha256": digest((root / "uv.lock").read_bytes()),
    }


def release_source_disclosure(root: Path, selected_paths: tuple[str, ...]):
    """Disclose status while refusing undeclared executable or selected inputs."""
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
    from empirical_lawhood.infrastructure.source_closure import _source_path_census
    from empirical_lawhood.infrastructure.source_origin import require_executing_target_source
    from empirical_lawhood.infrastructure.source_policy import (
        DOCUMENT_WORK_PLAN_PATHS, LOCAL_PLAN_NAME, NESTED_WORK_PLAN_PATHS, WORK_PLAN_DIRECTORIES,
        inspect_checkout_source, is_work_plan_path,
    )

    if __package__:
        from .release_portable_evidence import RELEASE_INPUT_FILES, RELEASE_INPUT_ROOTS
    else:
        from release_portable_evidence import RELEASE_INPUT_FILES, RELEASE_INPUT_ROOTS
    require_executing_target_source(root)
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=root)
    admission = inspect_checkout_source(root, status, selected_paths=selected_paths)

    def require_plan_file(name):
        path = root / name
        metadata = path.lstat()
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o111
                or any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(root))):
            raise ValueError("Release operational documents must be regular non-executable files without symlink parents")
        return path, metadata

    for change in admission.changes:
        name = change.relative_path
        if is_work_plan_path(name):
            require_plan_file(name)
            if name in selected_paths:
                raise ValueError("Release selected inputs include a local working plan")
            continue
        if change.status != "??":
            continue
        if (name in selected_paths or name in RELEASE_INPUT_FILES or name.startswith(RELEASE_INPUT_ROOTS)
                or name.startswith("LICENSES/")
                or name.endswith(".md")):
            raise ValueError("Release refuses an undeclared code, test, configuration or researcher input")
        # These excluded notes are ordinary data, never an executable or a
        # symlink exception. Their status remains in the original disclosure;
        # the existing owner still authenticates the local plan's exact bytes.
        try:
            metadata = (root / name).lstat()
        except OSError as error:
            raise ValueError("Release cannot observe its untracked file kind") from error
        if metadata.st_mode & 0o111:
            raise ValueError("Release refuses an undeclared executable input")
    declared = {name for name in selected_paths if name.startswith(("src/empirical_lawhood/", "scripts/"))}
    if _source_path_census(root) != declared:
        raise ValueError("Release executable source census differs from its selected tree")
    plans = {path.name for path in root.glob("*.md") if is_work_plan_path(path.name)}
    for name in WORK_PLAN_DIRECTORIES:
        plan_directory = root / name
        if plan_directory.is_symlink():
            raise ValueError("Release work-plan directory must not be a symlink")
        plans.update(path.relative_to(root).as_posix() for path in plan_directory.rglob("*.md"))
    plans.update(name for name in NESTED_WORK_PLAN_PATHS | DOCUMENT_WORK_PLAN_PATHS
                 if (root / name).exists() or (root / name).is_symlink())
    inventory = []
    for name in sorted(plans):
        path, metadata = require_plan_file(name)
        size, checksum = bounded_file_sha256(path, maximum_bytes=None)
        inventory.append({"path": name, "size_bytes": size, "sha256": checksum,
                          "mode": stat.S_IMODE(metadata.st_mode)})
    return admission.to_mapping() | {"excluded_work_plans": {
        "active_plan": LOCAL_PLAN_NAME, "inventory": inventory,
        "scope": "Preserved operational records; excluded from selected release inputs and distributions.",
    }}


def require_stable_source(before: dict[str, object], after: dict[str, object]) -> None:
    """Compare authenticated selections independently of raw checkout status."""
    selected_before = {key: value for key, value in before.items() if key != "checkout_disclosure"}
    selected_after = {key: value for key, value in after.items() if key != "checkout_disclosure"}
    if selected_before != selected_after:
        raise RuntimeError("source identity changed during the gate")


def source_metadata_bytes(checkout: Path) -> bytes:
    """Use the build owner's exact complete committed-source metadata."""
    if __package__:
        from .build_source_metadata import build_source_metadata
    else:
        from build_source_metadata import build_source_metadata
    return build_source_metadata(checkout)


def _source_metadata_payload(stream, size):
    if size < 0 or size > 8 * 1024**2:
        raise RuntimeError("source metadata exceeds its bounded allowance")
    chunks = []
    remaining = size
    while remaining:
        chunk = stream.read(min(remaining, 1024 * 1024))
        if not chunk:
            raise RuntimeError("source metadata ended before its declared size")
        chunks.append(chunk)
        remaining -= len(chunk)
    if stream.read(1):
        raise RuntimeError("source metadata exceeds its declared size")
    return b"".join(chunks)


def preserve_source_archive(root: Path, packet: Path, source: dict[str, object]):
    """Retain only the selected current tree, with no ancestor Git objects."""
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
    from empirical_lawhood.infrastructure.source_closure import _MAX_ARCHIVE_BYTES, _archive_census, _git
    from empirical_lawhood.infrastructure.source_policy import is_work_plan_path

    if _git(root, "rev-parse", "HEAD").decode("ascii").strip() != source["commit"]:
        raise RuntimeError("source archive requires the admitted commit at HEAD")
    tree = _git(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD")
    payload = _git(root, "archive", "HEAD")
    members = _archive_census(tree, payload)
    if (digest(tree) != source["tree_inventory_sha256"]
            or digest(payload) != source["archive_sha256"]
            or [member.to_mapping() for member in members] != source["tracked_files"]):
        raise RuntimeError("retained source archive differs from the admitted release source")
    if any(is_work_plan_path(member.relative_path) for member in members):
        raise RuntimeError("source archive includes a local working plan")
    if any(member.mode not in ("100644", "100755") for member in members):
        raise RuntimeError("source archive requires regular committed source members")
    if _git(root, "rev-parse", "HEAD").decode("ascii").strip() != source["commit"]:
        raise RuntimeError("selected commit changed during source archive capture")
    path = packet / "source.tar"
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(packet, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    if bounded_file_sha256(path, maximum_bytes=_MAX_ARCHIVE_BYTES) != (len(payload), digest(payload)):
        raise RuntimeError("durable source archive differs from its admitted current bytes")
    return {"schema": "empirical-lawhood/operational/release-source-archive", "version": "1.0.0",
            "path": path.name, "commit": source["commit"], "size_bytes": len(payload),
            "sha256": digest(payload), "tree_inventory_sha256": digest(tree),
            "member_count": len(members), "scientific_authority": "NONE"}


def compare_wheel_source(checkout: Path, wheel: Path) -> list[dict[str, object]]:
    """Bind every package source byte to the shared regular wheel-member owner."""
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
    from empirical_lawhood.infrastructure.source_closure import TrackedSourceMember, _MAX_ARCHIVE_BYTES
    from empirical_lawhood.infrastructure.source_origin import verify_wheel_package_members
    from empirical_lawhood.infrastructure.source_policy import is_work_plan_path

    names = output(["git", "ls-files", "--", "src/empirical_lawhood"], cwd=checkout).splitlines()
    expected = []
    for name in names:
        path = checkout / name
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError("wheel comparison requires a regular selected source member")
        if is_work_plan_path(name):
            if metadata.st_mode & 0o111 or any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(checkout)):
                raise RuntimeError("excluded work plans must be regular non-executable files without symlink parents")
            continue
        size, checksum = bounded_file_sha256(path, maximum_bytes=_MAX_ARCHIVE_BYTES)
        mode = "100755" if metadata.st_mode & stat.S_IXUSR else "100644"
        expected.append(TrackedSourceMember(name, mode, size, checksum))
    result = verify_wheel_package_members(wheel, expected=tuple(expected))
    with zipfile.ZipFile(wheel) as archive:
        if any(is_work_plan_path(name) or is_work_plan_path("src/" + name)
               for name in archive.namelist()):
            raise RuntimeError("wheel/source mismatch: includes a local working plan")
        metadata = [member for member in archive.infolist()
                    if member.filename.endswith(".dist-info/extra_metadata/source.json")]
        if len(metadata) != 1:
            raise RuntimeError("wheel omits its unique complete source metadata")
        member, = metadata
        mode = member.external_attr >> 16
        distribution_root = member.filename.split("/", 1)[0]
        metadata_roots = [row.filename.removesuffix("/METADATA") for row in archive.infolist()
                          if row.filename.endswith(".dist-info/METADATA")]
        if (len(member.filename.split("/")) != 3 or member.is_dir()
                or metadata_roots != [distribution_root]
                or member.file_size > 8 * 1024**2 or mode & 0o7111
                or stat.S_IFMT(mode) not in (0, stat.S_IFREG)):
            raise RuntimeError("wheel source metadata must be bounded ordinary data")
        with archive.open(member) as stream:
            payload = _source_metadata_payload(stream, member.file_size)
        if len(payload) != member.file_size or payload != source_metadata_bytes(checkout):
            raise RuntimeError("wheel source metadata differs from its complete committed identity")
    return result


def compare_sdist_researcher_inputs(checkout: Path, sdist: Path) -> list[dict[str, object]]:
    """Authenticate checkout-owned instructions and copied inputs in the source export."""
    from empirical_lawhood.infrastructure.source_policy import is_work_plan_path

    names = output(["git", "ls-files", "--", "README.md", "CONTRIBUTING.md", "docs", "configs", "programmes",
                    "experiments"], cwd=checkout).splitlines()  # Retained pre-consolidation sources keep their input scope.
    expected = {name: (checkout / name).read_bytes() for name in names if not is_work_plan_path(name)}
    with tarfile.open(sdist, "r:gz") as archive:
        members = archive.getmembers()
        roots = {member.name.split("/", 1)[0] for member in members}
        if len(roots) != 1:
            raise RuntimeError("source distribution has ambiguous roots")
        root = next(iter(roots)) + "/"
        observed = {}
        for member in members:
            name = member.name.removeprefix(root)
            if name in expected:
                if not member.isfile() or name in observed:
                    raise RuntimeError("source distribution researcher input is not one regular member")
                stream = archive.extractfile(member)
                assert stream is not None
                observed[name] = stream.read()
            if is_work_plan_path(name):
                raise RuntimeError("source distribution includes a local working plan")
    if observed != expected:
        missing = sorted(expected.keys() - observed.keys())
        changed = sorted(name for name in expected.keys() & observed.keys() if expected[name] != observed[name])
        raise RuntimeError(f"source distribution researcher inputs differ: missing={missing}, changed={changed}")
    return [{"path": name, "size_bytes": len(payload), "sha256": digest(payload)}
            for name, payload in sorted(observed.items())]


def compare_sdist_committed_source(checkout: Path, sdist: Path) -> list[dict[str, object]]:
    """Authenticate every shipped source byte, including incidental inputs.

    PKG-INFO is ordinary distribution metadata. The generated source metadata
    must equal its complete committed identity. Every other file must be an
    exact regular blob, including inputs outside the portable suite's scope.
    """
    from empirical_lawhood.infrastructure.source_closure import _matches_regular_git_mode
    from empirical_lawhood.infrastructure.source_policy import is_work_plan_path

    if __package__:
        from .release_portable_evidence import _selected_entries
    else:
        from release_portable_evidence import _selected_entries
    entries = _selected_entries(checkout, "HEAD")
    inventory = []
    seen = set()
    source_metadata_seen = False
    with tarfile.open(sdist, "r:gz") as archive:
        members = archive.getmembers()
        roots = {member.name.split("/", 1)[0] for member in members}
        if len(roots) != 1 or next(iter(roots)) in {"", ".", ".."}:
            raise RuntimeError("source distribution has ambiguous roots")
        prefix = next(iter(roots)) + "/"
        for member in members:
            name = member.name.removeprefix(prefix)
            if (name in seen or Path(member.name).is_absolute() or ".." in Path(member.name).parts):
                raise RuntimeError("source distribution has duplicate or escaping members")
            seen.add(name)
            if member.isdir():
                continue
            if not member.isfile():
                raise RuntimeError("source distribution contains a nonregular source member")
            if is_work_plan_path(name):
                raise RuntimeError("source distribution includes a local working plan")
            if name == "PKG-INFO":
                if member.size > 16 * 1024**2 or member.mode & ~0o777 or member.mode & 0o111:
                    raise RuntimeError("source distribution generated metadata is not bounded ordinary data")
                continue
            if name == "empirical-lawhood-source.json":
                if member.size > 8 * 1024**2 or member.mode & ~0o777 or member.mode & 0o111:
                    raise RuntimeError("source distribution source metadata is not bounded ordinary data")
                stream = archive.extractfile(member)
                assert stream is not None
                payload = _source_metadata_payload(stream, member.size)
                if len(payload) != member.size or payload != source_metadata_bytes(checkout):
                    raise RuntimeError("source distribution source metadata differs from its complete committed identity")
                source_metadata_seen = True
                continue
            if name not in entries:
                raise RuntimeError(f"source distribution contains an undeclared source member: {name}")
            mode, object_id = entries[name]
            if not _matches_regular_git_mode(member.mode, mode):
                raise RuntimeError(f"source distribution committed executable mode differs: {name}")
            stream = archive.extractfile(member)
            assert stream is not None
            payload = stream.read()
            if hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest() != object_id:
                raise RuntimeError(f"source distribution differs from its committed source blob: {name}")
            inventory.append({"path": name, "mode": mode, "size_bytes": len(payload), "sha256": digest(payload)})
    if not source_metadata_seen:
        raise RuntimeError("source distribution omits its complete source metadata")
    return sorted(inventory, key=lambda row: row["path"])


def main() -> None:
    if sys.version_info < (3, 11):
        raise SystemExit("Use the selected Python 3.11 environment: uv run --no-sync python scripts/release_check.py ...")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path, help="New packet directory outside the checkout.")
    parser.add_argument("--environment-root", type=Path,
                        help="New directory for fresh environments and temporary files on a POSIX filesystem.")
    parser.add_argument("--profile", choices=tuple(PROFILES), default="portable")
    parser.add_argument("--offline", action="store_true", help="Require already cached Python/build/dependency downloads.")
    parser.add_argument("--portable-evidence", type=Path,
                        help="Reuse one authenticated precommit portable suite with the exact final tree; never rerun it.")
    parser.add_argument("--shard-index", type=int, default=0, help="Zero-based integration/scale module shard.")
    parser.add_argument("--shard-count", type=int, default=1, help="Total integration/scale module shards.")
    args = parser.parse_args()
    if __name__ == "__main__" and not __package__:
        from test_profiles import validate_shard
    else:
        from scripts.test_profiles import validate_shard
    try:
        validate_shard(args.profile, args.shard_index, args.shard_count)
    except ValueError as error:
        parser.error(str(error))
    prior_portable = None
    if args.portable_evidence is not None:
        if args.profile != "portable":
            raise SystemExit("Precommit portable evidence is supported only for the portable artifact gate")
        if __package__:
            from .release_portable_evidence import authenticate_portable_evidence
        else:
            from release_portable_evidence import authenticate_portable_evidence
        prior_portable = authenticate_portable_evidence(args.portable_evidence.absolute(), ROOT)
    source = source_identity(ROOT)
    distribution_version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    packet = args.output_dir.expanduser().absolute()
    if (".." in packet.parts or packet.is_relative_to(ROOT) or packet.exists()
            or any(part.is_symlink() for part in (packet, *packet.parents))):
        raise SystemExit("Select a new output directory outside the source checkout.")
    environment_root = args.environment_root.expanduser().absolute() if args.environment_root else None
    if environment_root is not None:
        if (environment_root.is_relative_to(ROOT) or environment_root.is_relative_to(packet)
                or packet.is_relative_to(environment_root)
                or ".." in environment_root.parts or environment_root.exists()
                or any(part.is_symlink() for part in (environment_root, *environment_root.parents))):
            raise SystemExit("Select a new environment root outside the source checkout and packet.")
    # Observe prerequisites before creating a packet that needs terminal records.
    uv_version = output(["uv", "--version"], cwd=ROOT)
    checkout = ROOT
    environments = environment_root if environment_root else packet / "environments"
    project_environment = environments / "project"
    wheel_environment = environments / "wheel"
    brian2_environment = environments / "brian2"
    temporary_files = environments / "temporary-files"
    logs = packet / "logs"
    manifest = {
        "schema": 'empirical-lawhood/release/check-manifest', "status": "RUNNING",
        "started_utc": datetime.now(timezone.utc).isoformat(), "source": source,
        "profile": args.profile, "uv": uv_version,
        "test_shard": {"index": args.shard_index, "count": args.shard_count},
        "software_scope": {
            "ci": "Bounded portable contracts and installed artifacts; no complete portable coverage claim.",
            "integration": "Selected portable workflow module shard; no distribution build or complete coverage claim.",
            "scale": "Selected portable scale module shard; no distribution build or complete coverage claim.",
        }.get(args.profile, "Selected original verification profile; omitted profiles remain unverified."),
        "test_selection": None,
        "distribution_version": distribution_version,
        "host": {"os": platform.system(), "architecture": platform.machine()},
        "checks": [], "artifacts": [],
        "environment_paths": {"project": str(project_environment), "wheel": str(wheel_environment),
                              "brian2": str(brian2_environment)},
        "checkout": str(checkout), "temporary_files": str(temporary_files),
        "source_archive": None, "final_source_disclosure": None,
        "test_environment_policy": None if prior_portable is not None else {
            "basetemp": str(packet / "test-artifacts"),
            "tmp_path_retention_policy": "all", "tmp_path_retention_count": 1},
        "scientific_ceiling": "Software conformance and exposed development checks; no new qualification or admission.",
        "log_evidence": "Bound snapshots contain observed bytes; descendants may continue writing unbound live logs.",
    }
    offline = ["--offline"] if args.offline else []
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for inherited in ("PYTHONPATH", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "PYTEST_ADDOPTS"):

        environment.pop(inherited, None)

    environment["COVERAGE_RCFILE"] = str(checkout / ".coveragerc")
    environment.update(UV_PROJECT_ENVIRONMENT=str(project_environment), TMPDIR=str(temporary_files),
                       TMP=str(temporary_files), TEMP=str(temporary_files),
                       UV_CACHE_DIR=str(environments / "uv-cache"),
                       XDG_CACHE_HOME=str(environments / "cache"),
                       RUFF_CACHE_DIR=str(environments / "ruff-cache"))
    environment.update({name: "1" for name in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")})

    def run(name: str, command: list[str], *, cwd: Path = checkout,
            env_overrides: dict[str, str] | None = None) -> None:
        if name in {"tests", "build", "installed-smoke", "prior-portable-tree-binding"}:
            require_stable_source(source, source_identity(checkout))
        print(f"release gate: {name}", flush=True)
        began = time.monotonic()
        log = logs / f"{name}.log"
        check = {"name": name, "command": command, "exit_code": None,
                 "disposition": "RUNNING", "log": None, "sha256": None}
        manifest["checks"].append(check)
        try:
            with log.open("w", encoding="utf-8") as stream:
                result = subprocess.run(command, cwd=cwd, env=environment | (env_overrides or {}),
                                        stdout=stream, stderr=subprocess.STDOUT, text=True)
        except BaseException as error:
            check.update(disposition="INTERRUPTED", exception_type=type(error).__name__,
                         diagnostic=str(error), seconds=round(time.monotonic() - began, 3))
            if log.exists():
                check["unbound_live_log"] = log.relative_to(packet).as_posix()
                snapshot = logs / f"{name}.interrupted.log"
                try:
                    captured, checksum = seal_log_snapshot(log, snapshot)
                except OSError as snapshot_error:
                    check["snapshot_failure"] = str(snapshot_error)
                else:
                    check.update(log=snapshot.relative_to(packet).as_posix(),
                                 sha256=checksum, size_bytes=captured)
            raise
        check.update(exit_code=result.returncode,
                     disposition="FAILED" if result.returncode else "PASSED",
                     seconds=round(time.monotonic() - began, 3),
                     unbound_live_log=log.relative_to(packet).as_posix())
        snapshot = logs / f"{name}.sealed.log"
        try:
            captured, checksum = seal_log_snapshot(log, snapshot)
        except BaseException as error:
            check.update(disposition="EVIDENCE_FAILURE", exception_type=type(error).__name__,
                         diagnostic=str(error))
            raise
        check.update(log=snapshot.relative_to(packet).as_posix(), sha256=checksum, size_bytes=captured)
        if name == "tests" and args.profile in ("ci", "integration", "scale"):
            selection = packet / "test-selection.json"
            if selection.exists():
                payload = selection.read_bytes()
                manifest["test_selection"] = {"path": selection.name, "size_bytes": len(payload),
                                              "sha256": digest(payload)}
            elif result.returncode == 0:
                raise RuntimeError("partitioned tests did not retain their selected-case census")
        if result.returncode:
            raise RuntimeError(f"{name} failed (exit {result.returncode}); see {log}")

    try:
        packet.mkdir(parents=True)
        logs.mkdir()
        environments.mkdir(parents=True)
        temporary_files.mkdir()
        manifest["source_archive"] = preserve_source_archive(ROOT, packet, source)
        require_stable_source(source, source_identity(checkout))
        groups, tests = PROFILES[args.profile]
        if args.profile in ("ci", "integration", "scale"):
            tests = [*tests, "--test-shard-index", str(args.shard_index),
                     "--test-shard-count", str(args.shard_count),
                     "--test-selection-output", str(packet / "test-selection.json")]
        group_flags = [flag for group in ("reactor-example", "build", *groups) for flag in ("--group", group)]
        run("locked-install", ["uv", "sync", "--locked", "--python", "3.11.14", *offline, *group_flags])
        if args.profile == "native-brian2":
            run("brian2-install", ["uv", "sync", "--locked", "--python", "3.11.14", *offline],
                cwd=checkout / "programmes/biology/cell-responses/workflows/neuron-current-response/native-env",
                env_overrides={"UV_PROJECT_ENVIRONMENT": str(brian2_environment)})
            environment["EMPIRICAL_LAWHOOD_BRIAN2_PYTHON"] = str(brian2_environment / "bin/python")
        uv_python = ["uv", "run", "--no-sync", "python"]
        run("environment", [*uv_python, "-c",
            "import importlib.metadata as m,json,platform,sys; from pathlib import Path; "
            "import empirical_lawhood; "
            "from empirical_lawhood.infrastructure.source_origin import require_executing_target_source; "
            "root=Path.cwd().resolve(); require_executing_target_source(root); "
            f"selected={distribution_version!r}; "
            "assert empirical_lawhood.__version__ == m.version('empirical-lawhood') == selected, "
            "'source/module/distribution version mismatch'; "
            "print(json.dumps({'python':platform.python_version(), 'executable':sys.executable, "
            "'package_origin':empirical_lawhood.__file__, 'selected_version':selected, "
            "'packages':sorted((d.metadata['Name'],d.version) for d in m.distributions())},indent=2))"])
        if args.profile in ("portable", "ci"):
            run("frozen-rc-numerical-inputs", [*uv_python, "scripts/check_frozen_rc_inputs.py"])
        if args.profile not in ("integration", "scale"):
            # Refuse inexpensive source drift before the complete portable suite.
            run("static-errors", ["uv", "run", "--no-sync", "ruff", "check", "src", "tests", "scripts"])
            for generator in ("extension_bundle_aggregate", "executable_binding_aggregate", "cli_reference", "test_fixture", "operator_examples", "workflow_index", "config_schemas", "integration_examples", "recursive_examples", "matrix_experiment_examples"):
                run(f"generated-{generator}", [*uv_python, f"scripts/generate_{generator}.py", "--check"])
            run("documentation-links", [*uv_python, "scripts/check_documentation.py"])
        if args.profile == "portable" and prior_portable is None:
            environment["COVERAGE_FILE"] = str(packet / ".coverage")
            run("coverage-configuration", [*uv_python, "scripts/check_coverage_inventory.py",
                                           "--checkout", str(checkout)])
            run("tests", [*uv_python, "-m", "coverage", "run", "-m", "pytest",
                          "-q", "-ra", "--fail-on-skip", *retained_test_options(packet), *tests])
            run("critical-coverage", [*uv_python, "-m", "coverage", "report"])
            run("critical-coverage-json", [*uv_python, "-m", "coverage", "json",
                                            "-o", str(packet / "coverage.json")])
            run("critical-coverage-inventory", [*uv_python, "scripts/check_coverage_inventory.py",
                                                "--checkout", str(checkout), "--coverage-json",
                                                str(packet / "coverage.json")])
            manifest["coverage"] = {"path": "coverage.json",
                                    "sha256": digest((packet / "coverage.json").read_bytes()),
                                    "scope": ".coveragerc; parent test process only; no repository-wide coverage claim"}
        elif args.profile != "portable":
            run("tests", [*uv_python, "-m", "pytest", "-q", "-ra", "--fail-on-skip",
                          *retained_test_options(packet), *tests])
        if prior_portable is not None:
            # Preserve precommit attribution and its original immutable files;
            # this gate only adds a verified exact-tree join to the selected commit.
            import shutil
            retained = packet / "precommit-portable"
            retained.mkdir()
            selected_path = args.portable_evidence.absolute()
            shutil.copyfile(selected_path, retained / selected_path.name)
            bindings = [{"path": item["log"]} for item in prior_portable["checks"]]
            bindings += [prior_portable["coverage"], prior_portable["candidate_inventory"]]
            for binding in bindings:
                destination = retained / binding["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    shutil.copyfile(selected_path.parent / binding["path"], destination)
            manifest["precommit_portable"] = {
                "path": "precommit-portable/" + selected_path.name,
                "sha256": digest(selected_path.read_bytes()),
                "candidate_tree": prior_portable["candidate_tree"],
                "final_commit": source["commit"], "suite_invoked_in_this_gate": False,
                "attribution": "Tests ran before this commit on its exact unchanged staged candidate.",
            }
            run("prior-portable-tree-binding", [*uv_python, "-c",
                "from pathlib import Path; from scripts.release_portable_evidence import authenticate_portable_evidence; "
                f"authenticate_portable_evidence(Path({str(retained / selected_path.name)!r}), Path.cwd()); "
                "print('one passing precommit suite authenticated to this exact tree; no tests executed')"])
        if args.profile in ("portable", "ci"):
            artifacts = packet / "artifacts"
            # With neither --wheel nor --sdist, uv builds the wheel THROUGH the
            # newly built sdist. The backend and all its dependencies are locked.
            run("build", ["uv", "build", "--python", str(project_environment / "bin/python"),
                          "--no-build-isolation", *offline, "--out-dir", str(artifacts)])
            wheels = tuple(artifacts.glob("*.whl"))
            sdists = tuple(artifacts.glob("*.tar.gz"))
            if len(wheels) != 1 or len(sdists) != 1:
                raise RuntimeError("expected one new wheel and one new sdist")
            inventory = compare_wheel_source(checkout, wheels[0])
            (packet / "package-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
            researcher_inputs = compare_sdist_researcher_inputs(checkout, sdists[0])
            sdist_inventory = compare_sdist_committed_source(checkout, sdists[0])
            (packet / "sdist-source-inventory.json").write_text(json.dumps(sdist_inventory, indent=2) + "\n")
            manifest["sdist_source_inventory_sha256"] = digest((packet / "sdist-source-inventory.json").read_bytes())
            manifest["sdist_source_members"] = len(sdist_inventory)
            (packet / "researcher-input-inventory.json").write_text(json.dumps(researcher_inputs, indent=2) + "\n")
            manifest["researcher_input_inventory_sha256"] = digest((packet / "researcher-input-inventory.json").read_bytes())
            manifest["researcher_input_members"] = len(researcher_inputs)
            constraints = packet / "wheel-requirements.txt"
            run("wheel-pins", ["uv", "export", "--frozen", "--no-dev", "--group", "reactor-example",
                               "--no-emit-project", "--format", "requirements-txt", "--output-file", str(constraints)])
            wheel_env = wheel_environment
            run("wheel-environment", ["uv", "venv", "--python", "3.11.14", *offline, str(wheel_env)])
            python = wheel_env / "bin/python"
            run("wheel-dependencies", ["uv", "pip", "install", "--python", str(python), *offline,
                                       "--require-hashes", "-r", str(constraints)])
            run("wheel-install", ["uv", "pip", "install", "--python", str(python), *offline, "--no-deps", str(wheels[0])])
            outside = packet / "installed-smoke"
            outside.mkdir()
            run("installed-smoke", [str(python), str(checkout / "scripts/installed_wheel_smoke.py"),
                                     "--checkout", str(checkout), "--output-dir", str(outside)], cwd=outside)
            manifest["artifacts"] = [{"path": path.relative_to(packet).as_posix(),
                                      "size_bytes": path.stat().st_size, "sha256": digest(path.read_bytes())}
                                     for path in (*wheels, *sdists)]
            manifest["packaged_members"] = len(inventory)
            manifest["package_inventory_sha256"] = digest((packet / "package-inventory.json").read_bytes())
        final_source = source_identity(checkout)
        manifest["final_source_disclosure"] = final_source.get("checkout_disclosure")
        require_stable_source(source, final_source)
        manifest["status"] = "PASSED"
    except BaseException as error:
        manifest["status"] = "FAILED"
        manifest["failure"] = str(error)
        manifest["failure_type"] = type(error).__name__
        raise
    finally:
        manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        status = {
            "schema": 'empirical-lawhood/release/status',
            "distribution_version": distribution_version,
            "publication_status": "LOCAL_CANDIDATE_OWNER_REVIEW_PENDING",
            "selected_source": source, "profile": args.profile,
            "software_status": manifest["status"], "host": manifest["host"],
            "software_scope": manifest["software_scope"], "test_shard": manifest["test_shard"],
            "test_selection": manifest["test_selection"],
            "finished_utc": manifest["finished_utc"],
            "manifest_sha256": digest(manifest_bytes),
            "artifacts": manifest["artifacts"], "checks": manifest["checks"],
            "scientific_qualification": {
                "status": "NOT_PERFORMED", "identity": None, "verdict": None,
                "ceiling": manifest["scientific_ceiling"],
            },
            "historical_evidence": "Separate original source identities; receipts not relabeled.",
            "paper_primary_evidence": (
                "Separate selected paper preservation/build evidence; original experimental record "
                "availability is documented by paper provenance. This software gate performs no "
                "paper build or experimental reproduction."
            ),
            "packet_access": "Local maintainer review packet; request permitted access through repository support.",
        }
        # mkdir can be interrupted after creating the directory. Finalize any
        # created packet, including a failure before logs or environments exist.
        if packet.is_dir():
            (packet / "release-manifest.json").write_bytes(manifest_bytes)
            (packet / "release-status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(f"release gate passed: {packet / 'release-manifest.json'}", flush=True)


if __name__ == "__main__":
    main()
