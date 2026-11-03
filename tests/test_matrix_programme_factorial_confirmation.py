# SPDX-License-Identifier: MPL-2.0
"""Cold protected-route/refusal contracts; synthetic locators supply no authority.

Nothing here issues a scientific experiment, authenticates a qualified parent,
enters native work or claims a genuine confirmation. Actual issued-source and
same-worker acceptance remains a separately retained frozen-source exercise.
"""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial as factorial
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial_confirmation as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial_confirmation_custody as custody
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledCalibration
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_custody import acquisition_phase_roles
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_calibration import ScheduledProgrammeCalibrationEvidence
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_qualified_parent import ScheduledProgrammeQualifiedParentDeclaration
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import ScheduledRevisionTarget
from empirical_lawhood.api import matrix_scheduled_factorial_runtime as api
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole, ScientificConditionScope
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactMaterialization, ArtifactProfile, ArtifactWriteResult, CanonicalTaskReceipt, LogicalArtifactIdentity
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.experimental_factorial import PairInteractionScale
from empirical_lawhood.runtime.experimental_statistics import PairedMeanTAlternative
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, CandidateExecutionPlan, ExecutionTask, PlanLane, ScientificInputRole, ScientificInputSpec, ScientificStage
from empirical_lawhood.runtime.recursive_qualified_parents import RecursiveQualifiedParentBinding
from tests.test_matrix_scheduled_programme_reduction import declared as declared


def _pin(key, schema):
    return ObjectIdentity(key, schema, "1.0.0", sha256(key.encode()).hexdigest())


def _unpublished_descriptor(pin):
    """Only declared metadata, deliberately lacking actual durable custody."""
    generic = ArtifactGenericValidation("validator.synthetic.unpublished", "1.0.0", "1"*64, pin.object_schema,
        ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity("artifact."+pin.object_id, pin.object_fingerprint, pin.object_schema,
        ArtifactProfile.CANONICAL_JSON, "application/json", Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED, generic)
    physical = ArtifactMaterialization("materialization."+pin.object_id, logical.logical_artifact_id,
        "storage.synthetic.unpublished", "unpublished/parent.json", pin.object_fingerprint, 1, "none")
    sidecar = replace(physical, materialization_id="materialization.synthetic.sidecar", relative_path="unpublished/parent.json.manifest.json")
    return ArtifactWriteResult(logical, physical, sidecar, False)


def _parent(programme):
    # Type-correct closed locators remain unauthenticated. The runtime API must
    # load actual issue/grant/receipts rather than trust this descriptor.
    pin = _pin("calibration.synthetic.unpublished", ScheduledCalibration.SCHEMA)
    publication = _unpublished_descriptor(pin)
    producer = _pin("receipt.synthetic.unpublished", CanonicalTaskReceipt.SCHEMA)
    adjudication = _pin("adjudication.synthetic.unpublished", "empirical-lawhood/runtime/scientific-adjudication-record")
    scope = ScientificConditionScope("system.synthetic", "world.synthetic", "source.synthetic", ("receiver",), ("1",),
        "receiver.synthetic", "clock.synthetic", "Unpublished metadata only; no scientific validity warrant.",
        source_config_sha256=pin.object_fingerprint, population_id=pin.object_id)
    product = ContributionProduct("product.synthetic.unpublished", pin,
        ArtifactIdentity(publication.logical.logical_artifact_id, "fixture.unpublished", pin.object_schema,
            pin.object_fingerprint, "application/json", 1), producer, ContributionRole.QUALIFIED_EVIDENTIAL_PARENT,
        EvidenceCeiling.RESPONSE, Access.EVALUATION_SEALED, Visibility.PROSPECTIVE)
    contribution = ContributionManifest("contribution.synthetic.unpublished", "Unpublished closed source locators?",
        "These synthetic descriptors establish no qualification", scope, (product,), (adjudication,), ())
    binding = RecursiveQualifiedParentBinding("binding.synthetic.unpublished", "external.synthetic.unpublished", contribution.contribution_id,
        product.product_id, _pin("issue.synthetic", "empirical-lawhood/runtime/issued-executable-study-manifest"),
        _pin("execution.synthetic", "empirical-lawhood/planning/study-operation-authority"),
        _pin("reveal.synthetic", "empirical-lawhood/planning/study-operation-authority"), "run.synthetic", "calibrate",
        producer.object_id, "qualify", "receipt.synthetic.qualify", "qualify.adjudication", adjudication)
    return ScheduledProgrammeQualifiedParentDeclaration("declaration.synthetic.unpublished", pin, publication, contribution, binding,
        programme.identity, _pin("evidence.synthetic", ScheduledProgrammeCalibrationEvidence.SCHEMA),
        _pin("model.synthetic", "empirical-lawhood/matrix-response-error/model"), programme.criterion, programme.reservation, programme.group_ids)


@pytest.fixture(scope="module")
def criteria(declared):
    original, _ = declared
    programme = replace(original, programme_id="programme.synthetic.factorial-confirmation", mode="E4_CONFIRMATION",
        cases=tuple(replace(row, role="CONFIRMATION") for row in original.cases))
    target = ScheduledRevisionTarget("target.explicit.confirmation", programme.criterion, (1, 2, 3), ("PRIMARY", "FINE"),
        "CUMULATIVE_LOG1P_NORMALIZED_RESPONSE_ERROR_ALL15")
    spec = factorial.ScheduledFactorialSpecification("factorial.explicit.confirmation", programme.identity, target,
        factorial.ENDPOINT, PairInteractionScale.SIGNED_MEAN_DIFFERENCE,
        tuple(factorial.ScheduledFactorialComparison(name, PairedMeanTAlternative.GREATER, Decimal(".1"), None)
            for name in factorial.E4_COMPARISONS), Decimal(".05"), factorial.PROCEDURE,
        factorial.mean_t_requirement("requirement.explicit.confirmation"), (), "REQUIRE_COMPLETE_ASSIGNED_WHOLE_GROUPS")
    config = method.ScheduledFactorialCriteriaConfig("config."+method.freeze_node_id(spec), programme, spec, programme.bank, _parent(original))
    return method.ScheduledFactorialFrozenCriteria("criteria."+spec.specification_id, config, factorial.FAMILY_IDS,
        method.protected_sampling_requirement(spec))


def test_frozen_explicit_design_keeps_full64_576_and_original_science_bytes(criteria):
    raw = criteria.canonical_bytes()
    assert decode_canonical_bytes(raw, method.ScheduledFactorialFrozenCriteria, maximum_bytes=None) == criteria
    config, spec = criteria.configuration, criteria.configuration.specification
    assert len(config.programme.group_ids) == 64 and len(config.programme.cases) == 576 and len(criteria.family_ids) == 12
    assert criteria.sampling_requirement.consumer_operation_id == method.assess_node_id(spec)
    assert criteria.sampling_requirement.condition == spec.sampling_requirement.condition == factorial.SAMPLING_REQUIREMENT
    assert criteria.sampling_requirement.requirement_id != spec.sampling_requirement.requirement_id
    assert spec.sampling_requirement == factorial.mean_t_requirement(spec.sampling_requirement.requirement_id)


@pytest.mark.parametrize("damage", ("family", "requirement", "receiver", "record-id", "programme-mode", "specification"))
def test_freeze_cannot_relabel_original_design_or_transfer_a_development_assumption_receiver(criteria, damage):
    config = criteria.configuration
    with pytest.raises(ValueError):
        if damage == "family":
            replace(criteria, family_ids=criteria.family_ids[:-1])
        elif damage == "requirement":
            replace(criteria, sampling_requirement=replace(criteria.sampling_requirement, condition="Caller claims normality"))
        elif damage == "receiver":
            replace(criteria, sampling_requirement=config.specification.sampling_requirement)
        elif damage == "record-id":
            replace(criteria, record_id="criteria.foreign")
        elif damage == "programme-mode":
            replace(config, programme=replace(config.programme, mode="E4_REVISION_CALIBRATION"))
        else:
            replace(config, specification=replace(config.specification, alpha=Decimal(".01")))


def test_supported_explicit_threshold_edit_creates_distinct_criteria_without_changing_original_programme(criteria):
    config = criteria.configuration
    spec = replace(config.specification, alpha=Decimal(".01"), comparisons=tuple(
        replace(row, null_value=Decimal(".2")) for row in config.specification.comparisons))
    edited = replace(config, config_id="config."+method.freeze_node_id(spec), specification=spec)
    frozen = method.ScheduledFactorialFrozenCriteria("criteria."+spec.specification_id, edited, criteria.family_ids,
        method.protected_sampling_requirement(spec))
    assert frozen.identity != criteria.identity and frozen.configuration.programme.canonical_bytes() == config.programme.canonical_bytes()
    assert frozen.sampling_requirement.consumer_operation_id != criteria.sampling_requirement.consumer_operation_id
    assert criteria.configuration.specification.alpha == Decimal(".05")


def test_cold_declarations_separate_blind_freeze_from_real_reveal_and_do_no_parent_preparation():
    freeze, assess, seal = method.operation_declarations()
    assert (freeze.stage, freeze.execution_properties.barrier, freeze.outcome_access) == (
        ScientificStage.FREEZE, BarrierKind.FREEZE, Access.OUTCOME_BLIND)
    assert (assess.stage, assess.execution_properties.barrier, assess.outcome_access) == (
        ScientificStage.EVALUATE, BarrierKind.REVEAL, Access.EVALUATOR_REVEAL)
    assert (seal.stage, seal.execution_properties.barrier, seal.outcome_access) == (
        ScientificStage.FREEZE, BarrierKind.FREEZE, Access.OUTCOME_BLIND)
    assert {port.port_id for port in seal.input_ports} == {"bank", "programme", "specification", "criteria"}
    calls = []
    supplier = SimpleNamespace(prepare_factorial_task=lambda *args: calls.append(args))
    for declaration in (freeze, assess, seal):
        assert not declaration.execution_properties.native_effect
        factory = declaration.provider_factory()
        runner = factory.runner_factory()
        prepared = factory.runner_preparation_factory(supplier, runner)
        assert type(prepared) is ParentPreparedTaskRunner and calls == []
        with pytest.raises(PermissionError, match="PARENT_RUNNER_PREPARATION_REQUIRED"):
            prepared.execute(object())
    assert calls == []


@pytest.mark.parametrize("role", ("freeze", "assess", "seal"))
def test_unprepared_worker_and_absent_current_authority_refuse_before_any_input_read(role):
    runner = method.ScheduledFactorialProtectedWorker(role)
    class Unread:
        def read(self, *args):
            pytest.fail("unprepared protected worker read an input")
    context = SimpleNamespace(input_ports=(Unread(),))
    with pytest.raises(PermissionError, match="current authority/custody preparation"):
        runner.execute(context)
    def refused(*args):
        raise PermissionError("actual current authority absent")
    supplier = SimpleNamespace(_current=refused, _inputs=lambda *args: pytest.fail("authority refusal reached domain inputs"))
    with pytest.raises(PermissionError, match="actual current authority absent"):
        api.prepare_factorial_task(supplier, context, runner)


@pytest.mark.parametrize("states,expected", (
    (("SUCCEEDED",)*11, "COMPLETED"), (("UNENTERED",)*11, "UNENTERED"),
    (("SUCCEEDED",)*10+("FAILED",), "FAILED"), (("FAILED",)*10+("UNKNOWN",), "UNKNOWN"),
    (("BLOCKED",)*11, "INCOMPLETE"), (("SUCCEEDED",)*10+("UNENTERED",), "INCOMPLETE"),
))
def test_actual_phase_projection_preserves_unknown_and_never_relabels_failure_unentered(states, expected):
    phases = tuple(zip(acquisition_phase_roles("E4_CONFIRMATION"), states, strict=True))
    reasons = () if expected == "COMPLETED" else ("ORIGINAL_CUSTODY_STATE",)
    receipts = tuple(_pin("receipt.synthetic."+name, CanonicalTaskReceipt.SCHEMA)
        for name, state in phases if state == "SUCCEEDED")
    row = method.ScheduledFactorialCaseCustody("root.synthetic", "group.synthetic", expected, phases, receipts, (), reasons)
    assert row.state == expected
    with pytest.raises(ValueError):
        replace(row, state="UNENTERED" if expected != "UNENTERED" else "COMPLETED")


def test_incomplete_original_corpus_retains_full64_576_and_all12_unevaluable_slots(criteria):
    programme = criteria.configuration.programme
    phases = tuple((name, "UNKNOWN") for name in acquisition_phase_roles("E4_CONFIRMATION"))
    cases = tuple(method.ScheduledFactorialCaseCustody(row.root_id, row.independent_group_id, "UNKNOWN", phases,
        (), (), ("NO_ORIGINAL_TERMINAL_CUSTODY",)) for row in programme.cases)
    waves = tuple(method.ScheduledFactorialWaveCustody(row.wave_id, "UNKNOWN", None, None, None,
        ("MISSING_ORIGINAL_RUN_TERMINAL", "NO_ORIGINAL_TERMINAL_CUSTODY"))
        for row in programme.waves)
    slots = tuple(factorial.ScheduledFactorialFamilySlot(name, None, None, "UNEVALUABLE",
        ("INCOMPLETE_ORIGINAL_ACQUISITION_CUSTODY",)) for name in factorial.FAMILY_IDS)
    result = method.ScheduledFactorialConfirmationReadout("readout.synthetic.no-authority",
        _pin("config.synthetic", method.ScheduledFactorialConfirmationConfig.SCHEMA), programme.identity,
        _pin("binding.synthetic", method.ScheduledFactorialCriteriaBinding.SCHEMA), programme.group_ids,
        cases, waves, None, factorial.FAMILY_IDS, slots, factorial.ASSUMPTION_STATUS, "UNEVALUABLE",
        ("SAMPLING_ASSUMPTION_NOT_AUTHENTICATED",))
    assert len(result.cases) == 576 and sum(row.state == "UNKNOWN" for row in result.cases) == 576
    assert len(result.waves) == 16 and all(row.state == "UNKNOWN" for row in result.waves)
    assert result.calculation is None and all(row.p_value is None for row in result.family_slots)
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result
    with pytest.raises(ValueError):
        replace(result, cases=result.cases[:-1])
    with pytest.raises(ValueError):
        replace(result, family_slots=tuple(replace(row, p_value=Decimal(".001")) for row in result.family_slots))
    with pytest.raises(ValueError):
        replace(result, scientific_admission="SUPPORTED")


def test_missing_terminal_does_not_relabel_successful_ordinary_cases_or_collector_and_defers_every_slot(criteria):
    programme = criteria.configuration.programme
    phases = acquisition_phase_roles("E4_CONFIRMATION")
    cases = tuple(method.ScheduledFactorialCaseCustody(row.root_id, row.independent_group_id, "COMPLETED",
        tuple((phase, "SUCCEEDED") for phase in phases),
        tuple(_pin("receipt.synthetic."+row.root_id+"."+phase, CanonicalTaskReceipt.SCHEMA) for phase in phases), (), ())
        for row in programme.cases)
    waves = tuple(method.ScheduledFactorialWaveCustody(row.wave_id, "SUCCEEDED",
        _pin("receipt.synthetic."+row.wave_id+".collect", CanonicalTaskReceipt.SCHEMA), None, None,
        ("MISSING_ORIGINAL_RUN_TERMINAL",)) for row in programme.waves)
    deferred = method.confirmation_deferred_reasons(programme, paired_data=_pin("bank.synthetic", "empirical-lawhood/matrix-scheduled-programme/revision-data-bank"),
        cases=cases, waves=waves)
    assert deferred == ("MISSING_ORIGINAL_RUN_TERMINAL",)
    assert all(row.state == "COMPLETED" for row in cases) and all(row.state == "SUCCEEDED" for row in waves)
    slots = tuple(factorial.ScheduledFactorialFamilySlot(name, None, None, "UNEVALUABLE", deferred) for name in factorial.FAMILY_IDS)
    report = method.ScheduledFactorialConfirmationReadout("readout.synthetic.missing-terminal",
        _pin("config.synthetic", method.ScheduledFactorialConfirmationConfig.SCHEMA), programme.identity,
        _pin("binding.synthetic", method.ScheduledFactorialCriteriaBinding.SCHEMA), programme.group_ids,
        cases, waves, None, factorial.FAMILY_IDS, slots, factorial.ASSUMPTION_STATUS, "UNEVALUABLE", deferred)
    assert report.calculation is None and len(report.cases) == 576 and len(report.family_slots) == 12
    assert all(row.p_value is row.adjusted_p_value is None for row in report.family_slots)
    assert method.confirmation_deferred_reasons(programme, paired_data=None, cases=cases, waves=waves) == (
        "MISSING_ORIGINAL_PAIRED_DATA_BANK", "MISSING_ORIGINAL_RUN_TERMINAL")
    with pytest.raises(ValueError):
        replace(waves[0], reason_codes=())
    with pytest.raises(ValueError):
        replace(waves[0], terminal_status="SUCCEEDED")
    with pytest.raises(ValueError, match="full64/576"):
        method.confirmation_deferred_reasons(programme, paired_data=None, cases=cases[:-1], waves=waves)


def test_declared_runtime_view_without_complete_original_worker_contract_refuses():
    pin = _pin("synthetic", "empirical-lawhood/synthetic/object")
    view = custody.VerifiedFactorialInvocation(pin, pin, pin, pin, pin, pin, pin, None, (), (), pin, None, (), (), None, None)
    with pytest.raises(PermissionError, match="complete worker task/plan contract"):
        view.validate_invocation(SimpleNamespace(prepared_invocation=None))


@pytest.fixture(scope="module")
def declared_acquisition_plan(criteria):
    """Registered operation metadata only, with no receipt or issued authority."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_bindings import operation_factories
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition import NAMESPACE
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import NAMESPACE as COMPACT
    programme = criteria.configuration.programme
    wave = programme.waves[0]
    factories = {value.manifest.capability_key: value for value in operation_factories()}
    names = [(wave.wave_id+".open", "open"), (wave.wave_id+".collect", "collect")]
    names.extend((COMPACT+"."+root+"."+role, role) for root in wave.root_ids for role in acquisition_phase_roles(programme.mode))
    tasks = []
    for task_id, role in names:
        factory = factories[NAMESPACE+"."+role]
        manifest, registration = factory.manifest, factory.registration
        config = CapabilityConfigRef("config."+task_id, manifest.config_schema, manifest.config_schema_sha256,
            sha256(task_id.encode()).hexdigest(), "config."+task_id)
        requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind, config,
            manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions, manifest.maximum_evidence_ceiling,
            manifest.maximum_outcome_access, manifest.resource_ceiling)
        outputs = tuple(ArtifactOutputSpec(task_id+"."+value.output_id, "artifact."+task_id+"."+value.output_id,
            "unpublished/"+task_id+"."+value.output_id+value.filename_suffix, value.payload_schema, value.profile,
            value.media_type, registration.visibility_ceiling, (), manifest.maximum_outcome_access) for value in registration.outputs)
        if role == "open":
            edges = ()
        else:
            opening = tasks[0]
            source = opening.outputs[0]
            edges = (ScientificInputSpec("edge.synthetic."+task_id, "source.open", ScientificInputRole.SOURCE,
                opening.task_id, source.output_id, None, source.logical_artifact_id, source.logical_artifact_id,
                source.payload_schema, source.media_type, None, source.outcome_access, source.visibility_ceiling, opening.barrier),)
        tasks.append(ExecutionTask(task_id, registration.stage, requirement, manifest.implementation_sha256,
            () if role == "open" else (wave.wave_id+".open",), (), outputs, (), registration.barrier, 1,
            ("obligation.synthetic."+task_id,), scientific_inputs=edges))
    return CandidateExecutionPlan("plan.synthetic.unpublished", PlanLane.PROSPECTIVE,
        _pin("run.synthetic.unpublished", "empirical-lawhood/runtime/candidate-run-plan"), "2"*64, "d"*40,
        tuple(sorted(tasks, key=lambda row: row.task_id)), True,
        candidate=_pin("candidate.synthetic.unpublished", "empirical-lawhood/planning/draft-study-candidate"))


@pytest.mark.parametrize("damage", (None, "missing-task", "config-schema", "config-hash", "implementation", "collector", "foreign-wave"))
def test_partial_acquisition_census_reuses_exact_registered_contracts_without_inventing_collector_receipt(criteria, declared_acquisition_plan, damage):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_custody import validate_acquisition_operation_census
    programme, plan = criteria.configuration.programme, declared_acquisition_plan
    wave, operation = programme.waves[0], "collect"
    if damage is None:
        assert validate_acquisition_operation_census(programme, wave, operation, plan) is plan
        return
    if damage == "collector":
        operation = "collect-development"
    elif damage == "foreign-wave":
        wave = replace(wave, wave_id="wave.foreign")
    else:
        task = next(row for row in plan.tasks if row.task_id.endswith(".prefix"))
        if damage == "missing-task":
            plan = replace(plan, tasks=tuple(row for row in plan.tasks if row is not task))
        else:
            if damage == "implementation":
                changed = replace(task, capability_implementation_sha256="3"*64)
            else:
                config = replace(task.capability.config, **({"config_schema": "empirical-lawhood/synthetic/foreign"}
                    if damage == "config-schema" else {"config_schema_sha256": "3"*64}))
                changed = replace(task, capability=replace(task.capability, config=config))
            plan = replace(plan, tasks=tuple(changed if row is task else row for row in plan.tasks))
    with pytest.raises(ValueError):
        validate_acquisition_operation_census(programme, wave, operation, plan)


@pytest.mark.parametrize("case,expected", (("absent", "UNKNOWN"), ("explicit-nonattempt", "UNENTERED"),
    ("ordinary-failed", "FAILED"), ("contact-after-failure", "UNKNOWN"),
    ("contact-wrong-task", None), ("contact-wrong-inputs", None), ("contact-wrong-dependencies", None),
    ("contact-wrong-commit", None)))
def test_readonly_recovery_retains_uncertain_contact_and_refuses_full_contact_substitutions(tmp_path, declared_acquisition_plan, case, expected):
    """Small real custody files around software-only contact metadata.

    The unissued candidate is deliberately incapable of passing the public
    protected preparation route. No engine or registered worker is entered.
    """
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.runtime.native_effects import NativeEffectContact
    from empirical_lawhood.runtime.execution import OperationalFailureClass
    from empirical_lawhood.runtime.recovery import OperationalFailureDiagnostic, TaskRecoveryDisposition, TaskRecoveryEvent, build_run_recovery_index
    from tests.runtime_platform.test_native_subwork import _plane

    original = next(row for row in declared_acquisition_plan.tasks if row.task_id.endswith(".prefix"))
    task = replace(original, dependency_task_ids=(), scientific_inputs=())
    plan = replace(declared_acquisition_plan, tasks=(task,))
    package = SimpleNamespace(run_plan_id=plan.source_plan.object_id, registry=SimpleNamespace(
        capabilities=(SimpleNamespace(capability_key=task.capability.capability_key),)))
    plane = _plane(tmp_path / "software-custody")
    store = ExternalRunRecoveryStore(plane)
    index = build_run_recovery_index(plan, run_id=package.run_plan_id, wave_id="wave.synthetic.partial",
        authority_identities=(_pin("locator.synthetic.unissued", "empirical-lawhood/synthetic/not-an-authority"),))
    store.freeze(index)
    attempt, = index.task(task.task_id).attempts
    if case == "explicit-nonattempt":
        event = TaskRecoveryEvent("recovery-event."+package.run_plan_id+"."+task.task_id+".not-attempted",
            ObjectIdentity.from_record(index.recovery_index_id, index), package.run_plan_id, task.task_id, None, None,
            TaskRecoveryDisposition.NOT_ATTEMPTED, None, None, None, None, (), ("EXPLICIT_SOFTWARE_NONATTEMPT",), None)
        store.append_event(index, event)
    if case in ("ordinary-failed", "contact-after-failure"):
        diagnostic = OperationalFailureDiagnostic.create(OperationalFailureClass.RESOURCE_REFUSAL,
            sanitized_exception_type="SoftwareFixture", sanitized_message="No engine was called")
        store.record_failure(index, task_id=task.task_id, attempt_id=attempt.attempt_id,
            reason_code="SOFTWARE_PRECONTACT_FAILURE", failure=diagnostic)
    if case.startswith("contact"):
        contact = NativeEffectContact(package.run_plan_id, task.task_id, attempt.attempt_id,
            ObjectIdentity.from_record(plan.execution_plan_id, plan), ObjectIdentity.from_record(task.task_id, task),
            plan.implementation_commit, (), ())
        if case == "contact-wrong-task":
            contact = replace(contact, execution_task=replace(contact.execution_task, object_fingerprint="3"*64))
        elif case == "contact-wrong-inputs":
            contact = replace(contact, input_materialization_ids=("materialization.foreign",))
        elif case == "contact-wrong-dependencies":
            contact = replace(contact, dependency_receipt_ids=("receipt.foreign",))
        elif case == "contact-wrong-commit":
            contact = replace(contact, implementation_commit="e"*40)
        contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=contact.execution_plan,
            visibility_ceiling=task.outputs[0].visibility_ceiling, outcome_access=task.capability.requested_outcome_access)
        contacts.begin(contact)
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    if expected is None:
        with pytest.raises(PermissionError, match="original"):
            api._task_state(plane, package, plan, index, task)
    else:
        state, receipt, contact, reasons = api._task_state(plane, package, plan, index, task)
        assert state == expected and receipt is None and reasons
        assert (contact is not None) == case.startswith("contact")
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before
