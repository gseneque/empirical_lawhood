# SPDX-License-Identifier: MPL-2.0
"""Pure E4 phase dispatch and original-producer refusal controls.

The acquisition compiler is replaced at its existing boundary: these tests
exercise typed phase products, custody metadata and parent refusal, not native
compilation, storage custody, genuine qualification or scientific execution.
"""

from contextlib import nullcontext
from copy import copy
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_acquisition as acquisition
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_acquisition_composition as composition
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as selection
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_workflow as workflow
from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_calibrated_future_bindings as calibrated_future
from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_calibration_bindings as calibration_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_future_bindings as original_future
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration_custody import ScheduledRevisionCalibrationCustody
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_public import ScheduledRevisionPublicCalibration
from empirical_lawhood.api import matrix_revision_calibration_runtime as calibration_runtime, matrix_revision_runtime as runtime
from empirical_lawhood.api import recursive_qualified_parents
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt, ReceiptCheck
from tests.test_matrix_e4_programme_workflow import complete as complete_case  # noqa: F401
from tests.test_matrix_e4_revision_bindings import publication, scope as confirmation_future_scope
from tests.test_matrix_programme_factorial_confirmation import _parent
from tests.test_matrix_programme_selection import exposed, pin  # noqa: F401
from tests.test_matrix_revision_calibration import calibrated  # noqa: F401
from tests.test_matrix_revision_calibration_producer import producer, selected as producer_scope  # noqa: F401
from tests.test_matrix_sampling_follow_on import prior_product
from tests.test_matrix_scheduled_programme_acquisition import declared_root


def _calibration_custody(case, *, calibration=None, configuration=None, logical_id="published.exposed.revision-calibration"):
    calibration = case.result if calibration is None else calibration
    if configuration is None:
        scientific_scope = calibration_owner.ScheduledRevisionCalibrationScope("scope.exposed.join-calibration",
            calibration.specification, original_future.ScheduledRevisionFutureScope("scope.exposed.join-futures",
                case.development, case.nomination, case.frozen, case.programme))
        configuration = calibration_owner.ScheduledRevisionCalibrationConfig(
            "config." + calibration_owner.calibration_task_id(scientific_scope.identity), scientific_scope.identity,
            pin("sources.exposed.join-calibration", calibration_owner.ScheduledRevisionCalibrationSources.SCHEMA),
            case.programme.bank, case.programme.group_ids, case.reduction.reduction_id, case.data.bank_id, calibration.record_id)
    published = publication(calibration, logical_id)
    published = replace(published, logical=replace(published.logical, outcome_access=OutcomeAccess.EVALUATION_SEALED))
    task_id = calibration_owner.calibration_task_id(configuration.scope)
    receipt = CanonicalTaskReceipt("receipt.exposed.join-calibration", "run.exposed.join-calibration", task_id,
        "attempt.exposed.join-calibration", "a" * 40, (), (published.materialization,), (published.logical,),
        (ReceiptCheck(calibration_owner.CHECK, True, ()),), OperationalStatus.SUCCEEDED, ())
    original = prior_product(calibration.identity)
    original = replace(original, prior_execution=replace(original.prior_execution, run_id=receipt.run_id, task_id=task_id,
        receipt=ObjectIdentity.from_record(receipt.receipt_id, receipt), logical_artifact_id=logical_id))
    return ScheduledRevisionCalibrationCustody("custody.exposed.join-calibration",
        ScheduledRevisionPublicCalibration.from_calibration(calibration), original, configuration, published, receipt,
        publication(receipt, "published." + receipt.receipt_id))


def _invocation(case, monkeypatch, *, phase="CONFIRMATION", nomination=None, frozen=None):
    programmes = case.prior.development, case.prior.programme, case.programme
    programme = programmes[{"DEVELOPMENT": 0, "CALIBRATION": 1, "CONFIRMATION": 2}[phase]]
    root = declared_root(programme)
    if phase == "DEVELOPMENT":
        root = replace(root, development_unit_ids=programme.group_ids, evaluation_unit_ids=())
    scope = acquisition.ScheduledProgrammeAcquisitionScope("acquisition." + programme.waves[0].wave_id,
        programme, programme.bank, programme.waves[0], root, _parent(case.prior.programme) if phase == "CONFIRMATION" else None)
    banks, calls = (object(), object(), object()), []
    validate = workflow.ScheduledE4ProgrammeSpecification.validate

    def validate_at_compiler_boundary(specification, development, calibration, confirmation, *, banks=None):
        # Complete immutable phase validation remains real. Authentic bank/native
        # compilation is independently owned and deliberately outside this test.
        if banks is not None:
            assert banks is arguments["banks"]
        return validate(specification, development, calibration, confirmation)

    monkeypatch.setattr(workflow.ScheduledE4ProgrammeSpecification, "validate", validate_at_compiler_boundary)
    base_draft, base_operands = object(), {"original.operand": object()}

    def lower(**values):
        calls.append(values)
        return base_draft, dict(base_operands)

    monkeypatch.setattr(composition, "programme_acquisition_draft", lower)
    arguments = dict(specification=case.specification, development=programmes[0], calibration_programme=programmes[1],
        confirmation_programme=programmes[2], banks=banks, scope=scope, global_parent_binding=object(), proof_owners=(),
        operational_budgets={}, template_bytes=b"original template identity is checked by the compiler", draft_id="draft.exposed.e4-join")
    if phase != "DEVELOPMENT":
        arguments.update(nomination=case.prior.nomination if nomination is None else nomination,
            frozen=case.prior.frozen if frozen is None else frozen)
        if phase == "CONFIRMATION" and arguments["nomination"].trigger_disposition == "TRIGGERED":
            arguments["calibration"] = case.prior.result
    return arguments, calls, base_draft, base_operands


def _forbidden(*_args, **_kwargs):
    pytest.fail("an unselected future or acquisition path was entered")


def test_triggered_confirmation_forwards_exact_complete_custody_to_existing_calibrated_owner(complete_case, monkeypatch):  # noqa: F811
    arguments, calls, draft, operands = _invocation(complete_case, monkeypatch)
    custody = _calibration_custody(complete_case.prior)
    original_bytes = custody.canonical_bytes(), complete_case.prior.result.canonical_bytes()
    seals, received = (object(),), []
    addition = "custody.exposed.join-calibration"

    def lower_calibrated(actual_draft, future, actual_seals, actual_custody):
        received.append((actual_draft, future, actual_seals, actual_custody))
        return actual_draft, {addition: actual_custody}

    monkeypatch.setattr(calibrated_future, "add_calibrated_revision_future_dependencies", lower_calibrated)
    monkeypatch.setattr(original_future, "add_revision_future_dependencies", _forbidden)
    result, records = workflow.e4_acquisition_draft(**arguments, revision_custody=seals, revision_calibration_custody=custody)
    assert result is draft and records == {**operands, addition: custody}
    assert len(calls) == 1 and calls[0]["bank"] is arguments["banks"][2]
    assert calls[0]["calibration_payload"] is None
    actual_draft, future, actual_seals, actual_custody = received[0]
    assert actual_draft is draft and actual_seals is seals and actual_custody is custody
    assert future.programme == complete_case.programme and future.calibration_programme == complete_case.prior.programme
    assert future.calibration == custody.calibration and len(future.calibration.group_ids) == 64
    assert future.nomination_rule == complete_case.specification.nomination_rule
    assert (custody.canonical_bytes(), complete_case.prior.result.canonical_bytes()) == original_bytes


@pytest.mark.parametrize("kind", ("missing", "public-projection", "identity", "same-shaped-object"))
def test_triggered_confirmation_requires_the_actual_closed_producer_custody_type(complete_case, monkeypatch, kind):  # noqa: F811
    arguments, calls, _, _ = _invocation(complete_case, monkeypatch)
    public = ScheduledRevisionPublicCalibration.from_calibration(complete_case.prior.result)
    supplied = {"missing": None, "public-projection": public, "identity": public.identity,
        "same-shaped-object": SimpleNamespace(calibration=public)}[kind]
    with pytest.raises(TypeError, match="actual original revision calibration producer custody"):
        workflow.e4_acquisition_draft(**arguments, revision_calibration_custody=supplied)
    assert calls == []


@pytest.mark.parametrize("damage", ("producer", "receipt", "configuration", "publication"))
def test_cold_custody_revalidation_refuses_inconsistent_original_provenance_before_lowering(complete_case, monkeypatch, damage):  # noqa: F811
    arguments, calls, _, _ = _invocation(complete_case, monkeypatch)
    original = _calibration_custody(complete_case.prior)
    damaged = copy(original)
    if damage == "producer":
        value = replace(original.original, prior_execution=replace(original.original.prior_execution, task_id="task.foreign"))
        object.__setattr__(damaged, "original", value)
    elif damage == "receipt":
        object.__setattr__(damaged, "receipt", replace(original.receipt, checks=()))
    elif damage == "configuration":
        object.__setattr__(damaged, "configuration", replace(original.configuration, calibration_id="calibration.foreign"))
    else:
        object.__setattr__(damaged, "publication", replace(original.publication,
            materialization=replace(original.publication.materialization, physical_sha256="f" * 64)))
    with pytest.raises(ValueError, match="revision calibration custody"):
        workflow.e4_acquisition_draft(**arguments, revision_calibration_custody=damaged)
    assert calls == [] and original.canonical_bytes() != damaged.canonical_bytes()


def test_a_coherent_foreign_calibration_producer_cannot_replace_the_actual_completed_calibration(complete_case, monkeypatch):  # noqa: F811
    arguments, calls, _, _ = _invocation(complete_case, monkeypatch)
    foreign = replace(complete_case.prior.result, record_id="calibration.foreign-complete")
    custody = _calibration_custody(complete_case.prior, calibration=foreign)
    custody.__post_init__()
    with pytest.raises(ValueError, match="actual original complete calibration projection or producer"):
        workflow.e4_acquisition_draft(**arguments, revision_calibration_custody=custody)
    assert calls == []


def test_calibration_keeps_the_original_uncalibrated_future_path_and_opaque_payload_contract(complete_case, monkeypatch):  # noqa: F811
    arguments, calls, draft, operands = _invocation(complete_case, monkeypatch, phase="CALIBRATION")
    received, seals = [], (object(),)

    def original(actual_draft, future, actual_seals):
        received.append((actual_draft, future, actual_seals))
        return actual_draft, {}

    monkeypatch.setattr(original_future, "add_revision_future_dependencies", original)
    monkeypatch.setattr(calibrated_future, "add_calibrated_revision_future_dependencies", _forbidden)
    result, records = workflow.e4_acquisition_draft(**arguments, revision_custody=seals)
    assert result is draft and records == operands and len(calls) == 1
    actual_draft, future, actual_seals = received[0]
    assert actual_draft is draft and actual_seals is seals and future.programme == complete_case.prior.programme
    assert (future.calibration_programme, future.calibration, future.nomination_rule) == (None, None, None)
    assert calls[0]["calibration_payload"] is None


def _untriggered(development_case):
    specification = replace(development_case.specification, trigger=replace(development_case.specification.trigger, threshold=Decimal("1000000")))
    nomination = selection.select_programme_revision(specification, development_case.programme, development_case.reduction, development_case.data,
        nomination_id="nomination.exposed.join-untriggered")
    assert nomination.trigger_disposition == "NOT_TRIGGERED" and nomination.endpoint_fit_calls == 0
    return nomination, selection.freeze_programme_revision(development_case.programme, nomination, freeze_id="freeze.exposed.join-untriggered")


@pytest.mark.parametrize("phase", ("DEVELOPMENT", "CONFIRMATION"))
def test_default_development_and_untriggered_confirmation_leave_original_graph_untouched(complete_case, exposed, monkeypatch, phase):  # noqa: F811
    nomination, frozen = _untriggered(exposed)
    arguments, calls, draft, operands = _invocation(complete_case, monkeypatch, phase=phase, nomination=nomination, frozen=frozen)
    monkeypatch.setattr(original_future, "add_revision_future_dependencies", _forbidden)
    monkeypatch.setattr(calibrated_future, "add_calibrated_revision_future_dependencies", _forbidden)
    result, records = workflow.e4_acquisition_draft(**arguments)
    assert result is draft and records == operands and len(calls) == 1


@pytest.mark.parametrize("phase", ("DEVELOPMENT", "CALIBRATION", "CONFIRMATION"))
def test_original_calibration_custody_cannot_be_attached_to_an_unentered_or_wrong_phase(complete_case, exposed, monkeypatch, phase):  # noqa: F811
    nomination, frozen = _untriggered(exposed) if phase == "CONFIRMATION" else (None, None)
    arguments, calls, _, _ = _invocation(complete_case, monkeypatch, phase=phase, nomination=nomination, frozen=frozen)
    with pytest.raises(ValueError, match="only triggered E4 confirmation"):
        workflow.e4_acquisition_draft(**arguments, revision_calibration_custody=_calibration_custody(complete_case.prior))
    assert calls == []


def test_calibrated_native_parent_still_propagates_refusal_of_actual_original_issue_and_reveal(complete_case, monkeypatch):  # noqa: F811
    scope, custody = confirmation_future_scope(complete_case), _calibration_custody(complete_case.prior)
    records = {scope.SCHEMA: scope, custody.SCHEMA: custody}
    controls = {"input." + schema.rsplit("/", 1)[-1]: SimpleNamespace(logical=SimpleNamespace(payload_schema=schema))
        for schema in records}
    task = SimpleNamespace(scientific_inputs=tuple(SimpleNamespace(consumer_input_id=name, operational_logical_artifact_id=key)
        for name, key in (("revision-scope", "input.revision-future-scope"), ("revision-calibration-custody", "input.revision-calibration-custody"))))
    calls = []

    class Current:
        def __init__(self, **_kwargs):
            pass
        def current_task(self, *_args):
            calls.append("current")
            return object(), object(), task
        def task_inputs(self, *_args):
            return {}, controls
        def control_record(self, manifest, kind, _maximum):
            return records[kind.SCHEMA]
        def original_read_scope(self):
            return nullcontext((SimpleNamespace(require_verification_snapshot=lambda: None), object()))

    def refuse(**values):
        assert values["custody"] is custody and values["future"] is scope
        calls.append("original-calibration-authentication")
        raise PermissionError("original issued calibration or reveal refused")

    monkeypatch.setattr(runtime, "issued_custody_for_supplier", lambda _supplier: Current())
    monkeypatch.setattr(recursive_qualified_parents, "_ParentReadScope", lambda _writer: object())
    monkeypatch.setattr(calibration_runtime, "authenticate_revision_calibration", refuse)
    monkeypatch.setattr(runtime, "_authenticate_prior_execution", _forbidden)
    supplier = SimpleNamespace(writer=SimpleNamespace(verification_scope=lambda: nullcontext(object())), reveal_authority_id=None)
    runner = calibrated_future.operation_factories()[0].runner_factory()
    with pytest.raises(PermissionError, match="original issued calibration or reveal refused"):
        runtime.prepare_revision_future(supplier, object(), runner)
    assert calls == ["current", "original-calibration-authentication"]


def test_matching_public_calibration_does_not_bypass_actual_installed_producer_validation(complete_case, producer_scope, monkeypatch):  # noqa: F811
    values = producer(producer_scope)
    custody = _calibration_custody(producer_scope.original, configuration=producer_scope.config,
        logical_id=values["logical"].logical_artifact_id)
    task, = values["execution_plan"].tasks
    task = replace(task, capability=replace(task.capability, capability_key="foreign.same-output-schema"))
    values["execution_plan"] = replace(values["execution_plan"], tasks=(task,))

    def original_product(*_args, scope_validator):
        scope_validator(writer=object(), **{key: values[key] for key in
            ("binding", "package", "execution_plan", "receipt", "logical")})
        pytest.fail("same output schema cannot supply an original installed calibration producer")

    monkeypatch.setattr(calibration_runtime, "_original_product", original_product)
    monkeypatch.setattr(calibration_runtime, "_record_input", lambda *_args: custody.configuration)
    monkeypatch.setattr(calibration_runtime, "reconstruct_revision_calibration", _forbidden)
    with pytest.raises(PermissionError, match="original installed method"):
        calibration_runtime.authenticate_revision_calibration(writer=object(), custody=custody,
            future=confirmation_future_scope(complete_case), codecs={}, read_scope=object())
