# SPDX-License-Identifier: MPL-2.0
"""Small durable execution entries referencing one selected candidate census.

These operational records confer no issue, outcome access or qualification.
The selected-source owner and each worker retain their own admission checks;
entry custody never exports Git history or reconstructs an old installation.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError, read_bounded_bytes
from empirical_lawhood.infrastructure.numerical_provenance import (
    numerical_runtime_observation, observe_worker_environment,
)
from empirical_lawhood.infrastructure.source_closure import (
    _observe_admitted_target_source_current, capture_admitted_target_source,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity

_MAX_METADATA_BYTES = 8 * 1024 * 1024
_MAX_ENTRY_BYTES = 1024 * 1024


class RunSourceAdmissionError(PermissionError):
    """Selected candidate metadata or its durable entry cannot be authenticated."""


@dataclass(frozen=True, slots=True)
class RunSourceAdmission:
    candidate_metadata_path: Path
    candidate_metadata_sha256: str
    receipt_path: Path
    receipt_sha256: str


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode() + b"\n"


def _directory(path):
    """Create a selected operational directory without accepting a link."""
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    else:
        _sync_directory(path.parent)
    if path.is_symlink() or not path.is_dir() or path.resolve(strict=True) != path:
        raise RunSourceAdmissionError("run source custody requires real canonical directories")
    return path


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_once(path, payload, *, maximum_bytes):
    """Publish exact ordinary data; retain and refuse an interrupted write."""
    if len(payload) > maximum_bytes:
        raise RunSourceAdmissionError("run source observation exceeds its bounded metadata allowance")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        try:
            retained = read_bounded_bytes(path, maximum_bytes=maximum_bytes)
        except (BoundedFileIOError, OSError) as error:
            raise RunSourceAdmissionError("retained run source metadata is not readable regular data") from error
        if retained != payload:
            raise RunSourceAdmissionError("retained run source metadata changed its exact bytes")
    else:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _sync_directory(path.parent)


def _capture_source(project_root, *, _admitted_source=None):
    source = (capture_admitted_target_source(project_root) if _admitted_source is None else
        _observe_admitted_target_source_current(project_root, _admitted_source))
    # A pytest invocation additionally authenticates all exposed test bodies.
    # Ordinary installed execution does not import or require those fixtures.
    if "pytest" in sys.modules:
        tests = tuple(sorted(member.relative_path for member in source.tracked_files
            if member.relative_path.startswith("tests/") or member.relative_path == "conftest.py"))
        if not set(tests).issubset(source.final_source_admission.selected_paths):
            # The same authenticated complete census supplies test membership.
            # Expanded scope is reobserved and every selected test body is
            # checked against its committed bytes, not merely relabelled.
            selected = tuple(sorted(set(source.final_source_admission.selected_paths) | set(tests)))
            source = _observe_admitted_target_source_current(project_root, replace(source,
                source_admission=replace(source.source_admission, selected_paths=selected),
                final_source_admission=replace(source.final_source_admission, selected_paths=selected)))
    return source


def _candidate_document(source):
    return {
        "schema": "empirical-lawhood/build/source", "version": "1.0.0",
        "implementation_commit": source.implementation_commit,
        "implementation_sha256": source.implementation_sha256,
        "source_tree_sha256": source.source_tree_sha256,
        "tracked_files": [row.to_mapping() for row in source.tracked_files],
    }


def _admission_summary(observation):
    value = observation.to_mapping()
    return {"policy": value["policy"],
            "observed_checkout_clean": value["observed_checkout_clean"],
            "observation_sha256": sha256(_json_bytes(value)).hexdigest()}


def ensure_run_source_entry(*, project_root: Path, artifact_writer, run_id: str,
                            expected_commit: str, invocation: tuple[str, ...],
                            source_bindings: tuple[ObjectIdentity, ...] = (),
                            _admitted_source=None) -> RunSourceAdmission:
    """Record confirmed entry with a shared candidate reference, without export.

    The writer selects external custody and capacity policy. One content-addressed
    candidate census is shared by runs; their entries contain no copied census,
    source archive, Git database or checkout reconstruction prerequisite.
    """
    if (type(run_id) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}", run_id) is None
            or type(expected_commit) is not str or re.fullmatch(r"[0-9a-f]{40}", expected_commit) is None
            or type(invocation) is not tuple or not invocation
            or any(type(value) is not str or not value or "\0" in value for value in invocation)
            or type(source_bindings) is not tuple
            or any(type(value) is not ObjectIdentity for value in source_bindings)
            or len({value.object_id for value in source_bindings}) != len(source_bindings)):
        raise ValueError("source admission requires exact run, commit, invocation and unique typed bindings")
    project_root = Path(project_root).resolve(strict=True)
    source = _capture_source(project_root, _admitted_source=_admitted_source)
    if source.implementation_commit != expected_commit:
        raise RunSourceAdmissionError("experiment entry selected another actual implementation commit")
    locks = tuple(row.sha256 for row in source.tracked_files if row.relative_path == "uv.lock")
    if len(locks) != 1:
        raise RunSourceAdmissionError("selected candidate omits its exact dependency lock")
    candidate_payload = _json_bytes(_candidate_document(source))
    if len(candidate_payload) > _MAX_METADATA_BYTES:
        raise RunSourceAdmissionError("selected candidate exceeds its bounded metadata allowance")
    candidate_digest = sha256(candidate_payload).hexdigest()
    guard = artifact_writer.root
    root = guard.verify(for_write=True,
        operation_minimum_free_bytes=len(candidate_payload) + _MAX_ENTRY_BYTES)
    if (root == project_root or root.is_relative_to(project_root)
            or project_root.is_relative_to(root)):
        raise RunSourceAdmissionError("experiment source entry requires external operational custody")
    operational = _directory(root / "operational")
    candidates = _directory(operational / "source-candidates")
    candidate_path = candidates / (candidate_digest + ".json")
    _write_once(candidate_path, candidate_payload, maximum_bytes=_MAX_METADATA_BYTES)
    observation = {
        "schema": "empirical-lawhood/operational/run-source-entry", "version": "1.0.0",
        "run_id": run_id,
        "candidate": {"relative_path": candidate_path.relative_to(root).as_posix(),
            "sha256": candidate_digest, "size_bytes": len(candidate_payload),
            "implementation_commit": expected_commit,
            "implementation_sha256": source.implementation_sha256,
            "source_tree_sha256": source.source_tree_sha256},
        "source_before": _admission_summary(source.source_admission),
        "source_after": _admission_summary(source.final_source_admission),
        "parent_environment": observe_worker_environment().to_document(),
        "numerical_runtime": numerical_runtime_observation(),
        "dependency_lock_sha256": locks[0], "invocation": invocation,
        "process_argv": tuple(sys.argv),
        "source_bindings": tuple(value.to_document() for value in sorted(source_bindings, key=lambda value: value.object_id)),
        "storage_root_id": guard.contract.storage_root_id,
        "scientific_authority": "NONE", "worker_source_checks": "REQUIRED_SEPARATELY",
    }
    payload = _json_bytes(observation)
    if len(payload) > _MAX_ENTRY_BYTES:
        raise RunSourceAdmissionError("run source entry exceeds its bounded metadata allowance")
    if guard.verify(for_write=True) != root:
        raise RunSourceAdmissionError("selected run storage root changed during source entry")
    entries = _directory(operational / "run-source-entries")
    run_directory = _directory(entries / run_id)
    receipt_digest = sha256(payload).hexdigest()
    receipt_path = run_directory / (receipt_digest + ".json")
    _write_once(receipt_path, payload, maximum_bytes=_MAX_ENTRY_BYTES)
    if guard.verify(for_write=True) != root:
        raise RunSourceAdmissionError("selected run storage root changed during source entry")
    return RunSourceAdmission(candidate_path, candidate_digest, receipt_path, receipt_digest)


__all__ = ["RunSourceAdmission", "RunSourceAdmissionError", "ensure_run_source_entry"]
