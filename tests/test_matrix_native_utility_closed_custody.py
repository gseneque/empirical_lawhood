# SPDX-License-Identifier: MPL-2.0
"""Closed E2 custody controls on disclosed fixtures; zero native science calls.

One fixture commits a potential-contact header and stops before any native call;
the other refuses before contact. These records are software controls, with no
sampling warrant, scientific qualification or genuine experiment authority.
"""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_science as science
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_custody_records import (
    NativeUtilityCustodyAssessment,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_custody_science import assess_closed_custody
from empirical_lawhood.api import matrix_native_utility_custody_read as custody_reader
from empirical_lawhood.api import matrix_native_utility_read as reader
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, ResourceAdmissionError
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.runtime.recovery import RecoveryTerminalDisposition, TaskRecoveryDisposition
from tests.test_matrix_native_utility import utility_case, copied_preparation, _finite_score

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def closed_case(tmp_path_factory):
    directory = tmp_path_factory.mktemp("e2-closed-custody-no-native")
    case = utility_case(directory, root_count=2)
    case.specification = replace(case.specification,
        criterion=replace(case.specification.criterion, alpha_numerator=1, alpha_denominator=280))
    case.acquisition = r.acquisition_seal(case.specification, case.request)
    preparation = copied_preparation(case, directory / "copied")
    authored = Path(case.plane.root.contract.canonical_path) / "closed-native-e2-authored"
    author_prepared_experiment(preparation=preparation, project_root=ROOT, artifact_writer=case.plane, output_dir=authored)
    first, second = case.specification.root_ids
    original_execute = LocalProcessExecutor.execute
    with pytest.MonkeyPatch.context() as control:
        control.setattr(bindings, "execute_parameter_native_work", lambda *a, **kw: pytest.fail("fixture acquired a native prefix"))
        control.setattr(bindings, "execute_paired_response_native_work", lambda *a, **kw: pytest.fail("fixture acquired native futures"))
        def stop_native(self, runner, context, **kwargs):
            if context.task_id == owner.task_id(first, "prefix"):
                kwargs["native_entry"]()  # Potential contact only; no native executor enters.
                raise ResourceAdmissionError("disclosed software fixture stops after its potential-contact header")
            if context.task_id == owner.task_id(second, "prefix"):
                raise ResourceAdmissionError("disclosed software fixture refuses before native contact")
            return original_execute(self, runner, context, **kwargs)
        control.setattr(LocalProcessExecutor, "execute", stop_native)
        run = run_recursive_wave(directory=authored, project_root=ROOT, artifact_writer=case.plane,
            maximum_parallel_tasks=4)
    assert run["status"] == "BLOCKED" and run["new_native_contact_count"] == 1
    report, products, draft, plan = read_recursive_wave(directory=authored, artifact_writer=case.plane,
        include_products=True)
    _, _, _, payloads = load_authored_wave(directory=authored, artifact_writer=case.plane, lazy_payloads=True)
    raw = payloads["experiment-instance.json"]
    instance = decode_canonical_bytes(raw, ExperimentInstanceBinding, maximum_bytes=len(raw))
    return SimpleNamespace(case=case, directory=authored, report=report, products=products,
        draft=draft, plan=plan, payloads=payloads, instance=instance)


def _read(value, **changes):
    args = dict(directory=value.directory, artifact_writer=value.case.plane,
        specification=value.case.specification, instance=value.instance, payloads=value.payloads,
        report=value.report, products=value.products, draft=value.draft, plan=value.plan)
    args.update(changes)
    return reader.read_development_result(**args)


def test_public_closed_e2_read_retains_unknown_and_no_contact_refusal_without_native_or_fake_score(closed_case, monkeypatch):
    value = closed_case
    monkeypatch.setattr(LocalProcessExecutor, "execute", lambda *a, **kw: pytest.fail("closed read entered executor"))
    public = ExperimentProgrammeService(ROOT, value.case.plane).read(directory=value.directory)
    result = public["scientific_result"]
    assert public["status"] == result["operational_status"] == "BLOCKED"
    assert public["operational_terminal"] == "AUTHENTICATED"
    compact = ExperimentProgrammeService(ROOT, value.case.plane).read(directory=value.directory, allow_partial=True)
    assert compact["operational_terminal"] == "AUTHENTICATED"
    assert result["scientific_completion"].startswith("INCOMPLETE_NATIVE_UTILITY_ASSESSMENT")
    assert result["qualification"] == result["sampling_warrant"] == "NOT_ESTABLISHED"
    assert result["conditional_tail"] == {"numerator": 1, "denominator": 1}
    counts = result["denominators"]["native-utility"]
    assert counts["assigned_units"] == counts["missing_units"] == counts["unevaluable_units"] == 2
    assert counts["successes"] == counts["usable_units"] == 0
    assessment = decode_canonical_bytes(canonical_json_document_bytes(result["assessment"]),
        NativeUtilityCustodyAssessment, maximum_bytes=None)
    assert assessment.outcomes == () and len(assessment.missing_roots) == 2
    assert {gap.disposition for row in assessment.missing_roots for gap in row.gaps} == {
        "UNKNOWN_PARENT_COMPLETION", "NO_CONTACT_RESOURCE_REFUSAL", "DEPENDENCY_BLOCKED"}
    assert not any(hasattr(row, "score") for row in assessment.missing_roots)
    assert all(row.usable is False and row.success is False for row in assessment.missing_roots)


@pytest.mark.parametrize("partial", (False, True))
def test_closed_e2_compact_or_partial_reads_stay_deferred(closed_case, monkeypatch, partial):
    monkeypatch.setattr(custody_reader, "read_closed_partial_result", lambda **kw: pytest.fail("compact read opened scientific custody"))
    if partial:
        result = _read(closed_case, allow_partial=True)
    else:
        result = _read(closed_case, report={**closed_case.report, "typed_product_validation": "DEFERRED"})
    assert result["state"] == "NATIVE_UTILITY_ASSESSMENT_DEFERRED"
    assert result["denominators"]["native-utility"]["successes"] is None


@pytest.mark.parametrize("change", ("no-terminal", "foreign-run", "foreign-plan-digest", "missing-task", "unsettled-task"))
def test_closed_e2_requires_exact_settled_original_terminal_census(closed_case, change):
    value = closed_case
    report = dict(value.report)
    products = dict(value.products)
    if change == "no-terminal":
        products["terminal"] = None
    elif change == "foreign-run":
        report["run_id"] = "run.foreign"
    elif change == "foreign-plan-digest":
        report["execution_plan_sha256"] = "a" * 64
    elif change == "missing-task":
        products["dispositions"] = products["dispositions"][:-1]
    else:
        first, *rest = products["dispositions"]
        products["dispositions"] = ({**first, "operational_status": "NO_COMPLETION_RECEIPT"}, *rest)
    with pytest.raises(PermissionError, match="terminal|run/plan/index|settled"):
        _read(value, report=report, products=products)


@pytest.mark.parametrize("change", ("foreign-event", "foreign-task", "foreign-materialization"))
def test_closed_e2_missing_gap_consumer_rechecks_real_event_task_and_stream_materialization(closed_case, change):
    value = closed_case
    index, recovery, terminal, latest, contacts = custody_reader._closed_context(
        artifact_writer=value.case.plane, report=value.report, products=value.products, plan=value.plan)
    task_id = owner.task_id(value.case.specification.root_ids[0], "prefix")
    task = next(row for row in value.plan.tasks if row.task_id == task_id)
    products = dict(value.products)
    if change == "foreign-event":
        products["recovery_events"] = dict(products["recovery_events"])
        products["recovery_events"][latest[task_id].attempt_id] = replace(
            products["recovery_events"][latest[task_id].attempt_id], task_id="task.foreign")
    elif change == "foreign-task":
        task = next(row for row in value.plan.tasks if row.task_id == owner.task_id(value.case.specification.root_ids[1], "prefix"))
    else:
        chosen = task.external_inputs[0].logical_artifact_id
        external = list(products["external_inputs"])
        i = next(i for i,row in enumerate(external) if row.logical.logical_artifact_id == chosen)
        external[i] = replace(external[i], materialization=replace(external[i].materialization,
            materialization_id="material.foreign-stream-or-source"))
        products["external_inputs"] = tuple(external)
    with pytest.raises(PermissionError, match="event|ancestry|task"):
        custody_reader._gap(task=task, summary=latest[task_id], index=index, recovery=recovery,
            contacts=contacts, products=products, plan=value.plan, receipts=ExternalTaskReceiptStore(value.case.plane))


def _assessment(value):
    return decode_canonical_bytes(canonical_json_document_bytes(_read(value)["assessment"]),
        NativeUtilityCustodyAssessment, maximum_bytes=None)


def _reduce(value, *, outcomes=(), missing_roots=None, **changes):
    assessment = _assessment(value)
    index, _, terminal, _, _ = custody_reader._closed_context(artifact_writer=value.case.plane,
        report=value.report, products=value.products, plan=value.plan)
    args = dict(run_id=value.report["run_id"], execution_plan=value.plan, recovery_index=index,
        operational_terminal=terminal, outcomes=outcomes,
        missing_roots=assessment.missing_roots if missing_roots is None else missing_roots)
    args.update(changes)
    return assess_closed_custody(value.case.specification, value.case.acquisition, **args)


@pytest.mark.parametrize("status,marker", (("BLOCKED", None), ("BLOCKED", "ABSENT"),
    ("FAILED", None), ("FAILED", "ABSENT")))
def test_unclosed_unsuccessful_e2_defers_before_touching_scientific_custody(closed_case, status, marker):
    class Unreadable:
        def __getitem__(self, key):
            raise AssertionError("unclosed read opened scientific custody: " + str(key))
        def __getattribute__(self, key):
            raise AssertionError("unclosed read touched scientific custody: " + key)
    poison = Unreadable()
    report = {"status": status}
    if marker is not None:
        report["operational_terminal"] = marker
    result = reader.read_development_result(directory=poison, artifact_writer=poison,
        specification=closed_case.case.specification, instance=poison, payloads=poison,
        report=report, products=poison, draft=poison, plan=poison)
    assert result["state"] == "NATIVE_UTILITY_ASSESSMENT_DEFERRED"
    assert result["reason_codes"] == ("CLOSED_OPERATIONAL_TERMINAL_NOT_ESTABLISHED",)


@pytest.mark.parametrize("change", ("missing-phase", "foreign-task-pin", "foreign-source"))
def test_pure_closed_reducer_authenticates_all_original_missing_phases_and_sources(closed_case, change):
    value = closed_case
    assessment = _assessment(value)
    first, second = assessment.missing_roots
    with pytest.raises(ValueError, match="unusable|nonsuccess"):
        replace(first, usable=True)
    if change == "missing-phase":
        selected = next(gap for gap in second.gaps if gap.task.object_id == owner.task_id(second.root_id, "response-score"))
        second = replace(second, gaps=(selected,))
    elif change == "foreign-task-pin":
        gap, *rest = second.gaps
        second = replace(second, gaps=(replace(gap, task=replace(gap.task, object_fingerprint="a"*64)), *rest))
    else:
        second = replace(second, source=replace(second.source, object_fingerprint="a"*64))
    with pytest.raises(ValueError, match="phase|terminal row/task|whole root/source"):
        _reduce(value, missing_roots=(first, second))


@pytest.mark.parametrize("field", ("execution_plan", "recovery_index", "operational_terminal"))
def test_pure_closed_reducer_refuses_shaped_untyped_control_records(closed_case, field):
    with pytest.raises(TypeError, match="exact original development"):
        _reduce(closed_case, **{field: SimpleNamespace()})


def test_pure_closed_reducer_refuses_positive_outcome_for_actually_blocked_root(closed_case):
    value = closed_case
    case = value.case
    assessment = _assessment(value)
    protocol = case.request.protocols[0]
    # This disclosed arithmetic score is never inserted into real receipt custody.
    score = _finite_score(case, factor_loss="1")
    outcome = science.assess_score(case.specification, protocol,
        r.panels_for(case.request, case.source), case.acquisition, score)
    original_bytes = outcome.canonical_bytes()
    assert outcome.success and outcome.usable
    with pytest.raises(ValueError, match="unsuccessful original root terminal ancestry"):
        _reduce(value, outcomes=(outcome,), missing_roots=(assessment.missing_roots[1],))
    assert outcome.canonical_bytes() == original_bytes
    with pytest.raises(ValueError, match="omits|whole root/source"):
        _reduce(value, missing_roots=assessment.missing_roots[:-1])


def test_known_contacted_parent_nonsuccess_preserves_contact_without_claiming_nested_completion(closed_case):
    assessment = _assessment(closed_case)
    original = next(gap for row in assessment.missing_roots for gap in row.gaps
        if gap.disposition == "UNKNOWN_PARENT_COMPLETION")
    # Separate software representation control; this synthetic event is never published.
    summary = replace(original.terminal_attempt, disposition=RecoveryTerminalDisposition.FAILED,
        reason_code="disclosed-known-parent-failure")
    event = replace(original.recovery_event, disposition=TaskRecoveryDisposition.FAILED,
        reason_codes=("disclosed-known-parent-failure",))
    known = replace(original, terminal_attempt=summary, recovery_event=event,
        disposition="CONTACTED_PARENT_NON_SUCCESS")
    assert known.native_contact.canonical_bytes() == original.native_contact.canonical_bytes()
    assert not hasattr(known, "completion") and not hasattr(known, "consumed_streams")
    with pytest.raises(ValueError, match="UNKNOWN ancestry"):
        replace(known, disposition="UNKNOWN_PARENT_COMPLETION")
