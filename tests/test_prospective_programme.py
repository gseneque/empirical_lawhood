# SPDX-License-Identifier: MPL-2.0
"""Programme joins over actual public owners and synthetic software authority.

These fixtures provide no genuine grant, scientific evidence or qualification.
The actual-worker case requires a frozen selected source, as its existing owner
does. Cold joins and preview/refusal tests perform no scientific execution.
"""

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
from empirical_lawhood.api.results import CampaignStatusRequest, ResumeCampaignRequest, RunCampaignRequest
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from tests.test_prospective_experiment import selected as prospective_selection  # noqa: F401
from tests.runtime_platform.test_recursive_prospective_workflow import _issue_public_handoff, _run_public_handoff


pytestmark = pytest.mark.parametrize("prospective_selection", [2 * 1024**3], indirect=True)


def _primary_census(selected, control):
    """Snapshot exact primary receipts and every referenced output and sidecar."""
    root = Path(selected.plane.root.contract.canonical_path)
    paths, tasks = set(), {}
    for path in (root / "runs" / control.package.run_plan_id / "receipts").glob("*/*.json"):
        if path.name.endswith(".manifest.json"):
            continue
        receipt = decode_canonical_bytes(path.read_bytes(), CanonicalTaskReceipt, maximum_bytes=1024**2)
        pid, = (int(row.check_id.removeprefix("synthetic-process-")) for row in receipt.checks
            if row.check_id.startswith("synthetic-process-"))
        assert receipt.task_id not in tasks
        tasks[receipt.task_id] = {"attempt_id": receipt.attempt_id, "child_pid": pid,
            "receipt_sha256": receipt.fingerprint()}
        paths.add(path)
        paths.update(root / row.relative_path for row in receipt.output_materializations)
    paths.update(path.with_name(path.name + ".manifest.json") for path in tuple(paths))
    census = {}
    for path in sorted(paths):
        assert path.is_file() and not path.is_symlink()
        raw, stat = path.read_bytes(), path.stat()
        census[path.relative_to(root).as_posix()] = {"size_bytes": len(raw), "sha256": sha256(raw).hexdigest(),
            "mtime_ns": stat.st_mtime_ns}
    return tasks, census


@pytest.fixture(scope="module")
def issued(prospective_selection):  # noqa: F811
    selected = prospective_selection
    patch = pytest.MonkeyPatch()
    try:
        from empirical_lawhood.api import generated_experiment_runtime_bindings as generated
        kind = type(selected.preparation.specification_record)
        patch.setattr(generated, "EXPERIMENT_SPECIFICATION_PROTOCOLS",
            (*generated.EXPERIMENT_SPECIFICATION_PROTOCOLS, (kind.SCHEMA, kind.VERSION, "synthetic.prospective-experiment")))
        parts = _issue_public_handoff(selected.root, patch, handoff_parts=selected.original_parts,
            namespace="prospective-programme")
        control = _run_public_handoff(selected.root, issued_parts=parts, prepare_only=True, process_workers=True)
        loads = []

        def loader(**arguments):
            loads.append(arguments["directory"])
            return load_prepared_prospective_experiment(**arguments, composition=selected.composition,
                candidate_catalog=selected.candidate_catalog)

        programme = ExperimentProgrammeService(selected.root / "checkout", selected.plane, SimpleNamespace(maximum_parallel_tasks=1), loader,
            lambda **_arguments: control.api)
        yield selected, control, programme, loads
    finally:
        patch.undo()


def test_public_programme_preview_keeps_original_authority_boundary(issued):
    selected, control, programme, loads = issued
    report = programme.run(directory=selected.directory, request=RunCampaignRequest(control.package_path))
    assert report["status"] == "BLOCKED" and report["reason_codes"] == ["WRITE_CONFIRMATION_REQUIRED"]
    assert control.executor.invocations == 0
    candidate = control.package.issued_study.candidate
    assert report["programme"]["candidate"] == ObjectIdentity.from_record(candidate.candidate_id, candidate).to_document()
    assert report["programme"]["assigned_tasks"] == 5
    assert loads[-1] == selected.directory


@pytest.mark.parametrize("method,selection_request", (
    ("run", RunCampaignRequest("/unused")),
    ("recover", ResumeCampaignRequest("run.unused")),
    ("read", CampaignStatusRequest("run.unused")),
))
def test_prospective_custody_requires_its_original_typed_request(issued, method, selection_request):
    selected, control, programme, _ = issued
    wrong = ResumeCampaignRequest("run.unused") if method != "recover" else selection_request.run_id
    before = control.executor.invocations
    with pytest.raises(TypeError, match="existing typed campaign"):
        getattr(programme, method)(directory=selected.directory, request=wrong)
    assert control.executor.invocations == before


def test_actual_package_candidate_constraint_refuses_before_execution(issued):
    selected, control, programme, _ = issued
    joined, _ = programme._prospective_context(selected.directory)
    changed = replace(joined.association.candidate, object_fingerprint="f" * 64)
    result = control.api.run_campaign(RunCampaignRequest(control.package_path, confirmed=True), expected_candidate=changed)
    assert not result.succeeded
    assert any("exact outer executable candidate" in row.message for row in result.errors)
    assert control.executor.invocations == 0


def test_public_author_selects_original_prospective_owner_without_development_relabel(issued, monkeypatch):
    from empirical_lawhood.api import prospective_experiment as owner

    selected, control, _, _ = issued
    original = owner.author_prepared_prospective_experiment

    def author(**arguments):
        return original(**arguments, composition=selected.composition, api_factory=selected.api_factory,
            candidate_catalog=selected.candidate_catalog)

    monkeypatch.setattr(owner, "author_prepared_prospective_experiment", author)
    prepared = replace(selected.preparation, prospective_spec=selected.prospective_spec,
        source_configs=(selected.config,))
    service = ExperimentProgrammeService(selected.root / "checkout", selected.plane)
    destination = selected.directory.parent / "public-author-selection"
    report = service.author(preparation=prepared, output_dir=destination)
    loaded = load_prepared_prospective_experiment(directory=destination, project_root=selected.root / "checkout",
        storage_profile=object(), artifact_writer=selected.plane, composition=selected.composition,
        candidate_catalog=selected.candidate_catalog)
    assert report["specification"] == prepared.specification.to_document()
    assert loaded.specification == prepared.specification_record and loaded.allocation == prepared.allocation
    assert loaded.instance.draft.object_fingerprint == prepared.draft.fingerprint()
    assert control.executor.invocations == 0


def test_complete_public_programme_run_status_and_recovery_keep_same_candidate_and_completed_work(issued):
    selected, control, programme, loads = issued
    report = programme.run(directory=selected.directory, request=RunCampaignRequest(control.package_path,
        confirmed=True, reveal_authority_id=control.reveal.authority_id))
    assert report["status"] == "SUCCEEDED", report
    assert control.executor.invocations == 5
    assert len(control.executor.prepared_invocations) == 5
    assert len(set(control.executor.worker_process_ids)) == 5
    assert all(pid != os.getpid() for pid in control.executor.worker_process_ids)
    tasks, before = _primary_census(selected, control)
    plan = control.service._load_status_execution_plan(control.package.run_plan_id)
    contracts = {row.task_id: row for row in control.executor.prepared_invocations}
    assert set(tasks) == set(contracts) == {row.task_id for row in plan.tasks}
    assert set(row["child_pid"] for row in tasks.values()) == set(control.executor.worker_process_ids)
    assert all(tasks[key]["attempt_id"] == row.attempt_id for key, row in contracts.items())
    status = programme.read(directory=selected.directory,
        request=CampaignStatusRequest(control.package.run_plan_id, include_attempt_history=True))
    assert status["status"] == "SUCCEEDED", status
    recovered = programme.recover(directory=selected.directory, request=ResumeCampaignRequest(
        control.package.run_plan_id, confirmed=True, reveal_authority_id=control.reveal.authority_id))
    assert recovered["status"] == "SUCCEEDED", recovered
    assert control.executor.invocations == 5
    assert len(control.executor.prepared_invocations) == 5
    assert len(control.executor.worker_process_ids) == 5
    assert _primary_census(selected, control) == (tasks, before)
    assert report["programme"] == status["programme"] == recovered["programme"]
    assert loads[-3:] == [selected.directory] * 3
    changed = replace(programme._prospective_context(selected.directory)[0].association.candidate,
        object_fingerprint="e" * 64)
    for execute, request in ((control.api.resume_campaign, ResumeCampaignRequest(control.package.run_plan_id, confirmed=True)),
            (control.api.campaign_status, CampaignStatusRequest(control.package.run_plan_id))):
        refused = execute(request, expected_candidate=changed)
        assert not refused.succeeded
        assert any("exact outer executable candidate" in row.message for row in refused.errors)
    assert control.executor.invocations == 5
    assert _primary_census(selected, control) == (tasks, before)
    proof = {"status": "PASSED_AT_STATED_SCOPE", "run_id": control.package.run_plan_id,
        "parent_pid": os.getpid(), "tasks": tasks, "primary_census_before": before,
        "primary_census_after_equal": True, "executor_invocations_after_recovery_and_adversaries": 5,
        "prepared_contracts": {key: {"identity": row.identity.to_document(),
            "implementation": row.implementation.to_document(), "environment": row.environment.to_document()}
            for key, row in contracts.items()},
        "fixture_source": str(Path(__file__).resolve()),
        "limits": ["PURE software fixture; no native scientific acquisition",
            "Synthetic candidate source closure, passthrough inspector and authority records",
            "Actual worker package/import/inventory/environment proof; no genuine candidate clean-closure binding",
            "Qualification NOT_ESTABLISHED"]}
    (selected.root / "actual-prepared-process-programme-proof.json").write_text(json.dumps(proof, sort_keys=True, indent=2) + "\n")
