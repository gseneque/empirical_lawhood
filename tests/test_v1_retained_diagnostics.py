# SPDX-License-Identifier: MPL-2.0
"""Retained failures join real authored tasks without new execution or writes."""

from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import numerical_provenance as provenance
from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.api.experiment_execution_read import read_development_execution
from empirical_lawhood.api.retained_diagnostics import retained_failure_diagnostics
from empirical_lawhood.domains.materials.analytic_material_inquiry.recursive_translation import supply_draft
from empirical_lawhood.domains.materials.electron_gas.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.execution.local.execution import LocalProcessExecutor, ResourceAdmissionError
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from tests.test_recursive_public_service import _plane

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def failed_wave(tmp_path_factory):
    root = tmp_path_factory.mktemp("retained-diagnostic") / "selected"
    plane = _plane(root)
    config = decode_canonical_bytes((ROOT / "programmes/materials/superconductivity/workflows/electron-gas-response/config.json").read_bytes(),
        UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None)
    draft = supply_draft(config, draft_id="draft.diagnostic.resource-refusal")
    source_path = root / "source.json"
    source_path.write_bytes(config.canonical_bytes())
    source = author.implementation_binding(ROOT)
    producing = provenance.capture_numerical_provenance(project_root=ROOT)
    directory = root / "authored"
    def refuse(*_args, **_kwargs):
        raise ResourceAdmissionError("PRIVATE_OPERAND_MUST_NOT_APPEAR")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(author, "implementation_binding", lambda *_args, **_kwargs: source)
        patch.setattr(execution, "implementation_binding", lambda *_args, **_kwargs: source)
        patch.setattr(provenance, "capture_numerical_provenance", lambda **_kwargs: producing)
        author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
            output_dir=directory, input_bindings=((draft.external_inputs[0].input_id, source_path),))
        patch.setattr(LocalProcessExecutor, "execute", refuse)
        report = execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane,
            terminal_product_format="compact")
    assert report["status"] == "BLOCKED"
    return SimpleNamespace(directory=directory, plane=plane, draft=draft)


def _snapshot(root):
    from hashlib import sha256
    return {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()}


def test_failure_joins_authored_configuration_implementation_ancestry_and_retained_event(failed_wave, monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("diagnostic inspection executed or published work")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(failed_wave.plane, "write", forbidden)
    root = Path(failed_wave.plane.root.contract.canonical_path)
    before = _snapshot(root)
    report = execution.read_recursive_wave(directory=failed_wave.directory,
        artifact_writer=failed_wave.plane, terminal_product_format="compact")
    diagnostic, = report["failure_diagnostics"]
    operation, = failed_wave.draft.operations
    assert diagnostic["operation"] == operation.node_id
    assert diagnostic["authored_object"] == failed_wave.draft.draft_id
    assert diagnostic["authored_trace"]["authored_configuration"] == operation.config_identity.to_document()
    assert diagnostic["authored_trace"]["implementation"]["implementation_sha256"] == operation.selection.implementation_sha256
    assert diagnostic["declared_resources"] == operation.resource_budget.to_document()
    assert diagnostic["failure_class"] == "RESOURCE_REFUSAL"
    assert diagnostic["attempt_ordinal"] == 1
    assert (root / diagnostic["evidence"]).is_file()
    assert not diagnostic["automatic_replay_authorized"] and not diagnostic["scientific_evidence"]
    assert "PRIVATE_OPERAND_MUST_NOT_APPEAR" not in json.dumps(report)
    assert before == _snapshot(root)


def test_execution_only_diagnostic_uses_original_draft_without_loading_scientific_bodies(failed_wave, monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("execution-only inspection opened the full scientific wave")
    monkeypatch.setattr(author, "load_authored_wave", forbidden)
    report = read_development_execution(directory=failed_wave.directory, artifact_writer=failed_wave.plane)
    diagnostic, = report["failure_diagnostics"]
    assert diagnostic["authored_object"] == failed_wave.draft.draft_id
    assert diagnostic["authored_trace"] is None
    assert report["scientific_completion"] == "DEFERRED_TO_FULL_READ"
    assert report["new_native_contact_count"] == 0


def test_actual_cli_and_browser_expose_same_retained_failure(failed_wave, monkeypatch):
    from typer.testing import CliRunner
    from empirical_lawhood.api import application
    from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, response_bytes
    from empirical_lawhood.cli import application as terminal
    from empirical_lawhood.cli.app import app
    from empirical_lawhood.workbench.engine import ENGINE_SCHEMA, ENGINE_VERSION, describe_engine, invoke

    context = ApplicationContext("diagnostic.retained", "Retained refusal", Path(sys.executable).absolute())
    request = ApplicationRequest("cli.recursive-execution", context.context_id, "recursive.execution",
        (("directory", str(failed_wave.directory)), ("filter", ""), ("limit", 50)))
    monkeypatch.setattr(application, "application_storage", lambda _context: (None, None, failed_wave.plane))
    monkeypatch.setattr(application, "application_read_access", lambda *_args, **_kwargs: None)
    document = {"schema": ENGINE_SCHEMA, "version": ENGINE_VERSION,
        "context": context.to_document(), "request": request.to_document(),
        "expected_engine": describe_engine()["identity_sha256"]}
    browser = invoke({**document, "client": "browser"})
    monkeypatch.setattr(terminal, "application_context_from_cli", lambda: context)
    result = CliRunner().invoke(app, ["campaign", "recursive-execution", "--authoring-dir", str(failed_wave.directory)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == json.loads(response_bytes(browser))["payload"]
    body = json.loads(result.stdout)
    assert "resource-refusal" in result.stdout
    assert "failure_diagnostics" not in body  # diagnostics travel with paginated task rows
    assert "PRIVATE_OPERAND_MUST_NOT_APPEAR" not in result.stdout


def test_unknown_contact_and_foreign_ancestry_cannot_gain_replay_authority(failed_wave):
    from empirical_lawhood.execution.execution import OperationalFailureClass
    from empirical_lawhood.execution.recovery import OperationalFailureDiagnostic
    _, products, draft, plan = execution.read_recursive_wave(directory=failed_wave.directory,
        artifact_writer=failed_wave.plane, include_products=True, terminal_product_format="compact")
    _, _, _, payloads = author.load_authored_wave(directory=failed_wave.directory,
        artifact_writer=failed_wave.plane, lazy_payloads=True)
    _, _, index = execution._retained_plans(payloads, draft)
    original, = products["recovery_events"].values()
    # A disclosed typed projection control, not an assertion of native contact.
    uncertain = replace(original, reason_codes=("unknown-completion",),
        failure=OperationalFailureDiagnostic.create(OperationalFailureClass.RECOVERY_OBSTRUCTION,
            sanitized_exception_type="Interrupted", sanitized_message="completion uncertain"))
    diagnostic, = retained_failure_diagnostics(plan=plan, index=index,
        events={uncertain.attempt_id: uncertain}, draft=draft)
    assert diagnostic["retry_policy"] == "READ_ONLY_RECONCILIATION"
    assert diagnostic["automatic_replay_authorized"] is False
    with pytest.raises(ValueError, match="attempt ancestry"):
        retained_failure_diagnostics(plan=plan, index=index,
            events={uncertain.attempt_id: replace(uncertain, attempt_id="foreign.attempt")}, draft=draft)


@pytest.mark.parametrize("terminal", (False, True))
def test_nonattempt_diagnostic_joins_exact_event_without_lending_cause_to_prior_blocks(terminal):
    from empirical_lawhood.api.application_projections import execution_projection
    from empirical_lawhood.execution.recovery import ProtocolRunRecoveryIndex, ProtocolTaskRecoveryEvent, TaskRecoveryDisposition
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from tests.test_application_workbench import execution as report_fixture, request

    # Disclosed typed projection control. No nonattempt event is published and
    # no scientific or native fact is asserted by this fabricated presentation.
    event = ProtocolTaskRecoveryEvent("event.nonattempt",
        ObjectIdentity("index.original", ProtocolRunRecoveryIndex.SCHEMA, "1.0.0", "a" * 64),
        "run.original", "task.original", None, None, TaskRecoveryDisposition.NOT_ATTEMPTED,
        None, None, None, None, (), ("dependency-failed",))
    diagnostic = {"operation": event.task_id, "attempt_id": None,
        "retained_event": ObjectIdentity.from_record(event.event_id, event).to_document(),
        "actual": "retained nonattempt control"}
    row = dict(task_id=event.task_id, attempt_id=(event.run_id + "." + event.task_id + ".block-002") if terminal else None,
        ordinal=2 if terminal else None, operational_status="BLOCKED", recovery_event=event.to_document())
    prior = {**row, "attempt_id": event.run_id + "." + event.task_id + ".block-001",
        "ordinal": 1, "recovery_event": None}
    substituted = {**row, "recovery_event": replace(event, reason_codes=("substituted-reason",)).to_document()}
    report = {**report_fixture(), "operational_census": (prior, row, substituted),
        "failure_diagnostics": (diagnostic,)}
    result = execution_projection(report, request=request(), parameters={"limit": 1})
    assert "diagnostic" not in result["page"]["rows"][0]
    result = execution_projection(report, request=request(), parameters={"limit": 1, "cursor": result["page"]["next_cursor"]})
    assert result["page"]["rows"][0]["diagnostic"] == diagnostic
    result = execution_projection(report, request=request(), parameters={"limit": 1, "cursor": result["page"]["next_cursor"]})
    assert "diagnostic" not in result["page"]["rows"][0]
