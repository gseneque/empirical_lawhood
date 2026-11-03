# SPDX-License-Identifier: MPL-2.0
"""Future proof-collector controls; no child, native work or scientific authority."""

from concurrent.futures import ThreadPoolExecutor
import gc
import threading
from hashlib import sha256
from types import SimpleNamespace
import weakref

import pytest

from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_e3_public_programme import (
    _ObservedProcessContext, _ObservedProcessExecutor, _PreparedObservation, _release_dedicated_child, _retain_ready_record,
)


def identity():
    return ObjectIdentity("prepared.software.collector", "empirical-lawhood/testing/prepared", "1.0.0", "a" * 64)


class Ready:
    def __init__(self, raw):
        self.raw, self.invocation, self.ready = raw, identity(), True

    def canonical_bytes(self):
        return self.raw


def test_exact_ready_bytes_survive_without_retaining_complete_record(tmp_path):
    raw = b'{"software-control":"' + b"x" * (1024 * 1024) + b'"}\n'
    record = Ready(raw)
    reference = weakref.ref(record)
    retained = _retain_ready_record(record, path=tmp_path / "worker-ready/task.json",
        relative_path="worker-ready/task.json")
    del record
    gc.collect()
    assert reference() is None
    assert retained.path.read_bytes() == raw
    assert retained.proof() == {"invocation": identity().to_document(), "ready": True,
        "relative_path": "worker-ready/task.json", "size_bytes": len(raw), "sha256": sha256(raw).hexdigest()}


@pytest.mark.parametrize("damage", ("changed", "truncated", "missing"))
def test_final_proof_reauthenticates_retained_ready_bytes(tmp_path, damage):
    retained = _retain_ready_record(Ready(b"original software observation\n"),
        path=tmp_path / "task.json", relative_path="worker-ready/task.json")
    if damage == "missing":
        retained.path.unlink()
    else:
        retained.path.write_bytes(b"changed software observation\n" if damage == "changed" else b"x")
    with pytest.raises((AssertionError, BoundedFileIOError, OSError)):
        retained.proof()


def test_prepared_summary_drops_full_contract_graph():
    class Contract:
        def __init__(self):
            self.identity, self.native_effect = identity(), True
            self.complete_metadata = bytearray(1024 * 1024)

    contract = Contract()
    reference = weakref.ref(contract)
    retained = _PreparedObservation.from_contract(contract)
    del contract
    gc.collect()
    assert reference() is None and retained.identity == identity() and retained.native_effect is True


def test_ready_is_written_and_summarized_before_original_admission(tmp_path, monkeypatch):
    executor = object.__new__(_ObservedProcessExecutor)
    executor.ready, executor.contracts, executor.evidence_directory = {}, {}, tmp_path / "worker-ready"
    executor._observation_lock = threading.Lock()
    record = Ready(b"complete software Ready bytes\n")
    contract = SimpleNamespace(task_id="task.actual", identity=identity(), native_effect=True)
    called = []

    def admit(self, observed, actual, *arguments):
        assert observed is record and actual is contract
        assert self.ready["task.actual"].path.read_bytes() == record.canonical_bytes()
        assert self.contracts["task.actual"].identity == contract.identity
        called.append("original-admission")
        return "original-result"

    monkeypatch.setattr(LocalProcessExecutor, "_admit_worker", admit)
    assert executor._admit_worker(record, contract) == "original-result"
    assert called == ["original-admission"]


class Child:
    def __init__(self, *, alive=False):
        self.alive, self.closed, self.observations = alive, False, []

    @property
    def pid(self):
        assert not self.closed, "pid accessed after close"
        self.observations.append("pid")
        return 12345

    @property
    def exitcode(self):
        assert not self.closed, "exitcode accessed after close"
        self.observations.append("exitcode")
        return 0

    def is_alive(self):
        assert not self.closed
        return self.alive

    def close(self):
        assert not self.alive and not self.closed
        self.observations.append("close")
        self.closed = True


def test_completed_dedicated_child_is_released_after_capturing_pid_and_exit_state():
    child = Child()
    retained = _release_dedicated_child(child)
    assert child.closed and retained.pid == 12345 and retained.exitcode == 0
    assert child.observations == ["pid", "exitcode", "close"]


def test_live_or_group_reusable_child_is_never_closed_by_observer():
    child = Child(alive=True)
    with pytest.raises(AssertionError):
        _release_dedicated_child(child)
    assert not child.closed


def test_four_concurrent_child_collectors_keep_exact_per_task_attribution():
    class Context:
        def Process(self, *, task):
            return SimpleNamespace(task=task)

    retained = []
    context = _ObservedProcessContext(Context(), retained)
    rendezvous = threading.Barrier(4)

    def observe(task):
        with context.capture_children() as children:
            context.Process(task=task)
            rendezvous.wait(timeout=5)
            assert len(children) == 1 and children[0].task == task
            return children[0].task

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert tuple(pool.map(observe, range(4))) == tuple(range(4))
    assert retained == []
    with pytest.raises(AssertionError, match="task observation"):
        context.Process(task="unscoped")


def _source_entry_fixture(tmp_path):
    from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_json_document_bytes

    package_sources = (("module.py", "b" * 64),)
    implementation = SimpleNamespace(observed_git_head="a" * 40, package_sources=package_sources,
        code_sources_sha256=sha256(canonical_json_bytes(package_sources)).hexdigest(),
        dependency_lock_sha256="c" * 64)
    context = SimpleNamespace(run_id="run.collector-concurrent")
    contract = SimpleNamespace(implementation=implementation, execution_plan=identity())
    metadata = {"schema": "empirical-lawhood/build/source", "version": "1.0.0",
        "implementation_commit": "a" * 40, "implementation_sha256": "d" * 64,
        "source_tree_sha256": "e" * 64, "tracked_files": [
            {"relative_path": "pyproject.toml", "mode": "100644", "size_bytes": 1, "sha256": "f" * 64},
            {"relative_path": "src/empirical_lawhood/module.py", "mode": "100644", "size_bytes": 1, "sha256": "b" * 64},
            {"relative_path": "uv.lock", "mode": "100644", "size_bytes": 1, "sha256": "c" * 64}]}
    raw = canonical_json_document_bytes(metadata)
    candidate = tmp_path / "operational/source-candidates" / (sha256(raw).hexdigest() + ".json")
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(raw)
    reference = {"relative_path": candidate.relative_to(tmp_path).as_posix(), "sha256": candidate.stem,
        "size_bytes": len(raw), "implementation_commit": "a" * 40,
        "implementation_sha256": "d" * 64, "source_tree_sha256": "e" * 64}
    entry = {"schema": "empirical-lawhood/operational/run-source-entry", "version": "1.0.0",
        "run_id": context.run_id, "candidate": reference, "source_bindings": [identity().to_document()],
        "dependency_lock_sha256": "c" * 64, "scientific_authority": "NONE",
        "worker_source_checks": "REQUIRED_SEPARATELY"}
    raw = canonical_json_document_bytes(entry)
    path = tmp_path / "operational/run-source-entries" / context.run_id / (sha256(raw).hexdigest() + ".json")
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    return context, contract, candidate, path


def test_concurrent_source_proof_reads_candidate_once_without_serializing_child_execution(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure import selected_candidate

    executor = object.__new__(_ObservedProcessExecutor)
    executor.source_custody_root, executor.source_entries = tmp_path, {}
    executor._source_entry_lock = threading.Lock()
    context, contract, candidate, _entry = _source_entry_fixture(tmp_path)
    reads = []
    read_file = selected_candidate.read_bounded_bytes

    def counted(path, **kwargs):
        reads.append(path)
        return read_file(path, **kwargs)

    monkeypatch.setattr(selected_candidate, "read_bounded_bytes", counted)
    children_started = threading.Barrier(4)

    def execute(_task):
        executor._observe_source_entry(context, contract)
        # A proof lock held for child execution would deadlock this barrier.
        children_started.wait(timeout=5)

    with ThreadPoolExecutor(max_workers=4) as pool:
        tuple(pool.map(execute, range(4)))
    assert reads == [candidate] and len(executor.source_entries) == 1


@pytest.mark.parametrize("defect", ("candidate-bytes", "entry-bytes", "foreign-code", "foreign-lock", "foreign-commit", "foreign-plan"))
def test_source_proof_authenticates_candidate_code_lock_and_original_entry_bindings(tmp_path, defect):
    from tests.current_source_entry_proof import current_source_entry_proof

    context, contract, candidate, entry = _source_entry_fixture(tmp_path)
    proof = current_source_entry_proof(tmp_path, context, contract)
    assert proof["entry_receipts"] == [{"path": str(entry), "sha256": entry.stem}]
    assert proof["candidate"]["sha256"] == candidate.stem
    if defect == "candidate-bytes":
        candidate.write_bytes(candidate.read_bytes() + b"changed")
    elif defect == "entry-bytes":
        entry.write_bytes(entry.read_bytes() + b"changed")
    elif defect == "foreign-code":
        contract.implementation.package_sources = (("module.py", "f" * 64),)
    elif defect == "foreign-lock":
        contract.implementation.dependency_lock_sha256 = "f" * 64
    elif defect == "foreign-commit":
        contract.implementation.observed_git_head = "f" * 40
    else:
        contract.execution_plan = ObjectIdentity("foreign.plan", identity().object_schema, identity().object_version, "f" * 64)
    with pytest.raises((AssertionError, ValueError)):
        current_source_entry_proof(tmp_path, context, contract)
