# SPDX-License-Identifier: MPL-2.0
"""Exposed software observations: no provider allocation, task entry or qualification."""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.api import operational_observation as api
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest
from empirical_lawhood.storage.artifacts import FilesystemState, GuardedExternalRoot
from empirical_lawhood.storage.bounded_io import BoundedFileIOError
from empirical_lawhood.storage.operational_observation import export_snapshot, import_snapshot, read_export, read_retained_observation, read_supervision
from empirical_lawhood.storage.workbench_state import WorkbenchStateStore
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
from empirical_lawhood.execution.operational_observation import DOMAIN_SCHEMA, MAX_BYTES, SELECTION_SCHEMA, document, document_bytes, observation_age, unavailable_domain, validate_domain
from tests.test_deployment_supervision import Actions, Observer, observed, selection as supervisor_selection


@pytest.fixture
def selected(tmp_path, monkeypatch):
    from empirical_lawhood.execution.remote.deployment_supervision import supervise_deployment
    from empirical_lawhood.adapters.cloud.runpod_budget import RunpodBudgetObserver
    from empirical_lawhood.adapters.cloud.skypilot_budget import SkyPilotBudgetActions
    supervisor_path, supervisor = supervisor_selection(tmp_path)
    watch = tmp_path / "supervisor"
    actions = Actions()
    supervise_deployment(supervisor_path, output_directory=watch, observer=Observer([
        observed("82"), {"status": "COMPUTE_ABSENT_VOLUME_RETAINED"}]), actions=actions, sleep=lambda _: None, emit=lambda _: None)
    assert actions.calls == ["retire"]
    monkeypatch.setattr(RunpodBudgetObserver, "observe", lambda *a, **k: pytest.fail("collector contacted provider"))
    monkeypatch.setattr(SkyPilotBudgetActions, "act", lambda *a, **k: pytest.fail("collector acted on compute"))
    root = tmp_path / "operational"
    root.mkdir()
    contract = ExternalRootContract("observation.control", "Exposed observation control", str(root), str(root),
        "empirical-lawhood/testing/observations", 1, allowed_filesystem_types=("ext4",))
    class Inspector:
        available = True
        def inspect(self, _contract):
            return FilesystemState(str(root), self.available, self.available, 10**9, False, None, None, "ext4")
    inspector = Inspector()
    guarded = GuardedExternalRoot(contract, inspector)
    def store(_context, *, path=None):
        return WorkbenchStateStore(guarded, path or root / "selected.json", writable=True)
    monkeypatch.setattr(api, "operational_state_store", store)
    def write(name, value):
        path = tmp_path / name
        raw = document_bytes(value)
        path.write_bytes(raw)
        return {"path": str(path), "sha256": sha256(raw).hexdigest()}
    allocation = write("allocation.json", supervisor.allocation.to_document())
    job = write("job.json", {"evidence_role": "EXPOSED_SOFTWARE_CONTROL", "observation": {
        "cadence_seconds": 30, "stale_after_seconds": 120, "controller_source_sha256": "c" * 64,
        "worker_source_sha256": "d" * 64, "selected_gpu": "EXPOSED_GPU"}})
    binding = {"deployment_id": supervisor.allocation.deployment_id, "investigation_id": "fixture.investigation",
        "selection_id": "fixture.wave", "run_id": "fixture.run", "packet_sha256": "a" * 64,
        "allocation_sha256": allocation["sha256"], "job_card_sha256": job["sha256"],
        "controller_source_sha256": "c" * 64, "worker_source_sha256": "d" * 64}
    selection = {"schema": SELECTION_SCHEMA, "version": "1.0.0", "binding": binding,
        "directory": str(tmp_path / "authored-original"), "allocation": allocation, "job_card": job,
        "supervisors": [{"directory": str(watch), "selection_sha256": sha256((watch / "selection.json").read_bytes()).hexdigest()}],
        "cadence_seconds": 30, "stale_after_seconds": 120, "task_offset": 0, "native_offset": 0,
        "row_limit": 200, "domain_panel": None}
    selection_pin = write("observation-selection.json", selection)
    context = ApplicationContext("fixture", "Exposed observation", Path("/selected/python"), input_root=tmp_path,
        observation_root=root, collection_path=root / "collection.json")
    calls = []
    def execution(_context, selected):
        calls.append(selected)
        return ({"status": "SUCCEEDED", "run_id": binding["run_id"], "task_count": 1, "attempt_count": 1, "offset": 0,
            "rows": [{"task_id": "task.original", "attempt_id": "attempt.original", "ordinal": 1,
                "operational_status": "SUCCEEDED", "receipt_id": "receipt.original"}], "source": None,
            "producing_code_sha256": "d" * 64, "dependency_lock_sha256": "d" * 64, "producing_commit": "e" * 40},
            {"total": 0, "offset": 0, "rows": [], "coverage": "COMPLETE_METADATA_WINDOW", "body_validation": "DEFERRED_TO_ORIGINAL_READER"},
            unavailable_domain(binding))
    monkeypatch.setattr(api, "_observe_execution", execution)
    entry = {"value": {"context_id": "fixture", "selection_id": "fixture.wave", "investigation_id": "fixture.investigation",
        "deployment": {"deployment_id": binding["deployment_id"], "run_id": binding["run_id"],
            **{name: binding[name] for name in ("packet_sha256", "controller_source_sha256", "worker_source_sha256")},
            "allocation": allocation, "job_card": job, "observation_path": str(root / "selected.json")}}}
    monkeypatch.setattr(api, "selected_entry", lambda *_: (entry, "e" * 64))
    return {"context": context, "selection": selection, "pin": selection_pin, "guard": guarded,
        "store": store(context), "root": root, "calls": calls, "entry": entry, "inspector": inspector}


def collect(selected, **changes):
    return api.collect_observation(selected["context"], selected["pin"], collector_id="collector.one", sequence=1,
        output_directory=selected["root"] / "export-01", now="2026-11-11T00:00:00+00:00", **changes)


def imported(selected, exported, **changes):
    return import_snapshot(exported["directory"], expected_manifest_sha256=exported["manifest_sha256"],
        expected_binding=selected["selection"]["binding"],
        expected_allocation=document(Path(selected["selection"]["allocation"]["path"]).read_bytes()),
        store=selected["store"], **changes)


def test_collector_keeps_terminal_science_separate_from_finance_and_retained_volume(selected):
    exported = collect(selected)
    raw, snapshot = read_export(exported["directory"], expected_manifest_sha256=exported["manifest_sha256"])
    assert len(selected["calls"]) == 1 and len(raw) < MAX_BYTES
    assert snapshot["execution"]["status"] == "SUCCEEDED"
    finance = snapshot["financial"]
    assert finance["lifecycle"]["status"] == "COMPUTE_ABSENT_VOLUME_RETAINED"
    assert finance["accounting"]["status"] == "RETIRE_COMPUTE"
    assert finance["accounting"]["remaining_usd"] == "-2.530000000000"
    assert finance["accounting"]["accounted_usd"] == "82.530000000000"
    assert finance["liabilities"].startswith("UNKNOWN")
    assert finance["retained_volume_charges"].startswith("CONTINUING")
    assert snapshot["domain"]["complete_return_count"] is None
    assert snapshot["runtime"]["observed_gpu"] is None
    assert snapshot["return"]["terminal"] is False
    assert all(snapshot[name] == 0 for name in ("provider_calls", "native_calls", "lifecycle_actions"))


def test_verified_import_is_atomic_and_current_application_read_does_not_recollect(selected, monkeypatch):
    result = imported(selected, collect(selected))
    monkeypatch.setattr(api, "_observe_execution", lambda *a, **k: pytest.fail("UI refresh invoked original execution reader"))
    request = ApplicationRequest("refresh", "fixture", "observation.read", (("selection_id", "fixture.wave"),))
    response = execute_application(selected["context"], request)
    assert response.succeeded and response.payload["state_sha256"] == result["state_sha256"]
    assert response.payload["snapshot"]["financial"]["accounting"]["remaining_usd"] == "-2.530000000000"
    selected["inspector"].available = False
    refused = execute_application(selected["context"], request)
    assert not refused.succeeded and refused.payload is None


@pytest.mark.parametrize("damage", ("allocation", "allocation_body", "source", "partial", "oversize", "manifest"))
def test_changed_binding_or_incomplete_transfer_preserves_last_permitted_bytes(selected, damage):
    exported = collect(selected)
    state = imported(selected, exported)
    original = selected["store"].read()
    _, snapshot = read_export(exported["directory"], expected_manifest_sha256=exported["manifest_sha256"])
    snapshot["sequence"] = 2
    if damage in ("allocation", "source"):
        snapshot["binding"]["allocation_sha256" if damage == "allocation" else "worker_source_sha256"] = "f" * 64
    if damage == "source":
        snapshot["execution"]["producing_code_sha256"] = "f" * 64
    if damage == "allocation_body":
        snapshot["financial"]["allocation"]["budget"]["total_usd"] = "800"
    second = export_snapshot(snapshot, root=selected["guard"], output_directory=selected["root"] / "export-02")
    package = Path(second["directory"])
    if damage == "partial":
        (package / "payload/snapshot.json").write_bytes(b"{")
    if damage == "oversize":
        (package / "payload/snapshot.json").write_bytes(b" " * (MAX_BYTES + 1))
    if damage == "manifest":
        second["manifest_sha256"] = "0" * 64
    with pytest.raises((ValueError, OSError, BoundedFileIOError)):
        imported(selected, second, expected_current_sha256=state["state_sha256"])
    assert selected["store"].read() == original


def test_collector_refuses_a_worker_source_different_from_original_execution(selected, monkeypatch):
    original = api._observe_execution
    def substituted(context, selection):
        execution, native, domain = original(context, selection)
        execution["producing_code_sha256"] = "f" * 64
        return execution, native, domain
    monkeypatch.setattr(api, "_observe_execution", substituted)
    with pytest.raises(ValueError, match="worker source"):
        collect(selected)
    assert not (selected["root"] / "export-01").exists()


def test_sequence_order_gaps_and_explicit_restart_do_not_use_equal_time_as_order(selected):
    first = collect(selected)
    state = imported(selected, first)
    _, snapshot = read_export(first["directory"], expected_manifest_sha256=first["manifest_sha256"])
    with pytest.raises(PermissionError, match="regressed or repeated"):
        imported(selected, first, expected_current_sha256=state["state_sha256"])
    snapshot["sequence"] = 3  # Same observation time, later sequence, one transferred window omitted.
    next_export = export_snapshot(snapshot, root=selected["guard"], output_directory=selected["root"] / "third")
    state = imported(selected, next_export, expected_current_sha256=state["state_sha256"])
    assert state["sequence_gap"] == 1
    snapshot.update(collector_id="collector.two", sequence=1, previous_snapshot_sha256=state["snapshot_sha256"])
    restarted = export_snapshot(snapshot, root=selected["guard"], output_directory=selected["root"] / "restart")
    with pytest.raises(PermissionError, match="bind a new collector"):
        imported(selected, restarted, expected_current_sha256=state["state_sha256"])
    state = imported(selected, restarted, expected_current_sha256=state["state_sha256"], restart_from_snapshot_sha256=state["snapshot_sha256"])
    assert read_retained_observation(selected["store"])[1]["retired_collectors"] == ["collector.one"]
    snapshot.update(collector_id="collector.one", sequence=4)
    retired = export_snapshot(snapshot, root=selected["guard"], output_directory=selected["root"] / "retired")
    with pytest.raises(PermissionError, match="retired collector"):
        imported(selected, retired, expected_current_sha256=state["state_sha256"])


def test_stale_source_and_billing_are_explicit_and_selection_change_refuses(selected):
    first = collect(selected)
    _, snapshot = read_export(first["directory"], expected_manifest_sha256=first["manifest_sha256"])
    assert observation_age(snapshot, now="2026-11-11T00:02:01+00:00") == {"age_seconds": 121, "stale": True}
    assert observation_age(snapshot, now="2026-11-11T00:00:10+00:00")["stale"] is False
    with pytest.raises(ValueError, match="future"):
        observation_age(snapshot, now="2026-11-10T00:00:00+00:00")
    Path(selected["pin"]["path"]).write_bytes(b"{}")
    with pytest.raises(PermissionError, match="digest"):
        api.collect_observation(selected["context"], selected["pin"], collector_id="collector.one", sequence=2,
            output_directory=selected["root"] / "refused")
    assert not (selected["root"] / "refused").exists()


def test_new_supervisor_requires_retained_accounting_floor(selected, tmp_path):
    from empirical_lawhood.execution.remote.deployment_supervision import supervise_deployment, SupervisionSelection
    original = selected["selection"]["supervisors"][0]
    first = SupervisionSelection.read(Path(original["directory"]) / "selection.json")
    later = tmp_path / "later"
    later.mkdir()
    path, _ = supervisor_selection(later)
    supervise_deployment(path, output_directory=later / "watch", observer=Observer([observed("82"),
        {"status": "COMPUTE_ABSENT_VOLUME_RETAINED"}]), actions=Actions(), sleep=lambda _: None, emit=lambda _: None)
    selection = {"directory": str(later / "watch"), "selection_sha256": sha256((later / "watch/selection.json").read_bytes()).hexdigest()}
    with pytest.raises(PermissionError, match="accounting floor"):
        read_supervision([original, selection], first.allocation)


def test_domain_contract_does_not_promote_raw_returns_or_task_receipts(selected):
    domain = unavailable_domain(selected["selection"]["binding"])
    assert domain["schema"] == DOMAIN_SCHEMA and validate_domain(domain)
    changed = deepcopy(domain)
    changed["complete_return_count"] = 1
    with pytest.raises(ValueError, match="unavailable reader"):
        validate_domain(changed)
    context = replace(selected["context"], read_access_paths=(Path("/protected/access"),))
    with pytest.raises(ValueError, match="exposed operational"):
        api.collect_observation(context, selected["pin"], collector_id="collector.one", sequence=1,
            output_directory=selected["root"] / "protected-refused")


def test_actual_native_projection_never_opens_force_bodies_or_promotes_metadata(tmp_path, monkeypatch):
    from tests.test_native_training_read_scope import _finished, _no_array_open, _reader
    store, definition, completed = _finished(tmp_path)
    _no_array_open(store.plane, completed.outputs, monkeypatch)
    with store.plane.read_context() as reader:
        row = api.native_progress_record(_reader(reader, store), definition)
        assert row["completion_receipt"] == "SUCCEEDED"
        assert row["publication"] == "COMPLETE_METADATA_CENSUS"
        assert row["state"] == "RECEIPT_METADATA_PRESENT"
        assert "complete_force_return" not in row


def test_return_journal_records_failure_then_verifies_actual_files_without_assessing_science(selected, monkeypatch, tmp_path):
    from empirical_lawhood.api import application_collection, observation_return
    from empirical_lawhood.storage.transfer_files import seal_transfer
    entry = selected["entry"]
    entry["value"]["deployment"]["return_path"] = str(selected["root"] / "return.json")
    monkeypatch.setattr(observation_return, "operational_state_store", api.operational_state_store)
    monkeypatch.setattr(application_collection, "selected_entry", lambda *_: (entry, "e" * 64))
    def call(event, digest=None):
        values = {"selection_id": "fixture.wave", "text": document_bytes(event).decode()}
        if digest:
            values["expected_return_sha256"] = digest
        return execute_application(selected["context"], ApplicationRequest("return.control", "fixture", "observation.record-return", tuple(values.items())))
    failure = call({"stage": "TRANSFER", "action": "FAILED"})
    assert failure.succeeded and failure.payload["status"] == "FAILED"
    payload = tmp_path / "original-return"
    payload.mkdir()
    (payload / "original.json").write_bytes(b'{"original":"exposed software control"}\n')
    seal = seal_transfer(payload, tmp_path / "return-manifest.json", maximum_bytes=1024, maximum_files=1)
    event = {"stage": "BYTE_VERIFICATION", "action": "VERIFY_FILES", "root": str(payload),
        "manifest": seal["manifest"], "manifest_sha256": seal["sha256"]}
    verified = call(event, failure.payload["state_sha256"])
    assert verified.succeeded and verified.payload["status"] == "BYTE_VERIFIED"
    journal = observation_return.read_return(selected["context"], entry=entry, binding=selected["selection"]["binding"])
    by_stage = {row["stage"]: row for row in journal["stages"]}
    assert by_stage["TRANSFER"]["status"] == "FAILED"
    assert by_stage["INDEPENDENT_READING"]["status"] == "UNAVAILABLE"
    assert journal["terminal"] is False
    (payload / "original.json").write_bytes(b'changed')
    refusal = call(event, verified.payload["state_sha256"])
    assert not refusal.succeeded
    assert observation_return.read_return(selected["context"], entry=entry, binding=selected["selection"]["binding"])["revision"] == 2


def test_original_return_must_match_the_deployment_authored_wave():
    from empirical_lawhood.api.observation_return import _require_original_binding
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave
    original = ObjectIdentity("exposed.return.control", AuthoredRecursiveWave.SCHEMA, "1.0.0", "a" * 64)
    _require_original_binding(original.to_document(), {"packet_sha256": "a" * 64})
    with pytest.raises(PermissionError, match="authored wave"):
        _require_original_binding(original.to_document(), {"packet_sha256": "b" * 64})
    other = replace(original, object_schema="empirical-lawhood/testing/different-original")
    with pytest.raises(PermissionError, match="authored wave"):
        _require_original_binding(other.to_document(), {"packet_sha256": "a" * 64})
    sci02 = {"packet_sha256": "a" * 64, "draft_sha256": "b" * 64, "execution_plan_sha256": "c" * 64}
    _require_original_binding(sci02, {"packet_sha256": "a" * 64}, reader_operation="sci02d.findings")
    with pytest.raises(PermissionError, match="authored wave"):
        _require_original_binding(sci02, {"packet_sha256": "b" * 64}, reader_operation="sci02d.findings")


@pytest.mark.parametrize("changed_worker", (False, True))
def test_runtime_telemetry_requires_its_domain_source_and_selected_worker(selected, monkeypatch, changed_worker):
    original = api._observe_execution
    def observe(context, selection):
        execution, native, domain = original(context, selection)
        domain.update(status="SUPPORTED", runtime={"observed_gpu": "EXPOSED_GPU_OBSERVATION", "utilisation": None,
            "memory": "1024 MiB", "process": "EXPOSED_PROCESS", "native_phase": "SCF_ITERATION",
            "observed_utc": "2026-11-10T23:59:30+00:00", "worker_source_sha256": ("f" if changed_worker else "d") * 64,
            "source": {"schema": "empirical-lawhood/testing/runtime", "version": "1.0.0",
                "fingerprint": "e" * 64, "object_id": "exposed.runtime"}})
        return execution, native, domain
    monkeypatch.setattr(api, "_observe_execution", observe)
    if changed_worker:
        with pytest.raises(ValueError, match="selected worker"):
            collect(selected)
        assert not (selected["root"] / "export-01").exists()
        return
    exported = collect(selected)
    imported(selected, exported)
    response = execute_application(selected["context"], ApplicationRequest("runtime", "fixture", "observation.read",
        (("selection_id", "fixture.wave"),)))
    assert response.succeeded
    snapshot = response.payload["snapshot"]
    assert snapshot["runtime"]["observed_gpu"] == "EXPOSED_GPU_OBSERVATION"
    assert snapshot["runtime"]["native_phase"] == "SCF_ITERATION"
    assert snapshot["runtime"]["utilisation"] is None
    assert snapshot["runtime"]["observation"] == snapshot["domain"]["runtime"]
    assert all(snapshot[name] == 0 for name in ("provider_calls", "native_calls", "lifecycle_actions"))
