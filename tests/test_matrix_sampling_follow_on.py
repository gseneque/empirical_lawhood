# SPDX-License-Identifier: MPL-2.0
"""Pure follow-on controls; all scientific evidence is explicitly synthetic."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods import matrix_sampling_assessment as sampling
from empirical_lawhood.adapters.methods import matrix_sampling_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_adjudication as e3
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as products
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import MatrixE3RootDecision
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import selected_deanneal_specification
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial_confirmation as e4
from empirical_lawhood.api import matrix_sampling_runtime as runtime
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract, PreparedWorkerEnvironment
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from tests.test_matrix_sampling_admission import evidence_for, pin, request_for


@pytest.fixture(scope="module")
def e3_case():
    specification = selected_deanneal_specification(protocol_sha256="a"*64)
    source = pin("source.exposed.original")
    roles = tuple(sorted((UnitRoleAssignment(f"unit.{population.role.lower()}.{i:03}", population.role.lower())
        for population in specification.populations for i in range(population.expected_units)), key=lambda value: value.unit_id))
    allocation = UnitAllocation("allocation.exposed.sampling", (source,),
        tuple(IndependentUnit(value.unit_id, source.object_id, specification.populations[0].family_id,
            ("fine", "primary"), value.role == "train") for value in roles), roles)
    common = dict(specification=specification.identity, allocation=allocation.identity,
        models=pin("models.original", products.ProtectedE3ModelSet.SCHEMA),
        reservation_join=pin("reservation.original", "empirical-lawhood/matrix-response-experiment/protected-prefit-join"))
    model = products.ProtectedE3FrozenProducts("freeze.model.original", **common, calibration=None, model_freeze=None)
    calibrated = products.ProtectedE3FrozenProducts("freeze.calibrated.original", **common,
        calibration=pin("calibration.original", products.ProtectedE3Calibration.SCHEMA), model_freeze=products.identity(model))
    units = allocation.unit_ids("evaluation")
    decisions = tuple(MatrixE3RootDecision(unit, True, True, tuple((method, view, Decimal(".001"))
        for method in ("ALL_ORIGIN_RIDGE", "RAW_TRAIN_MEDIAN") for view in ("fine", "primary")), ("PAIRED_SUCCESS",)) for unit in units)
    assessment = products.ProtectedE3Assessment("assessment.original", specification.identity, allocation.identity,
        products.identity(calibrated), tuple(pin("forecast." + unit, products.ProtectedE3Forecast.SCHEMA) for unit in units),
        tuple(pin("outcome." + unit, products.ProtectedE3PairedOutcome.SCHEMA) for unit in units), decisions,
        64, 64, 1, 2**64, True, tuple((unit, False, (None,)*15) for unit in units),
        tuple((unit, "INFINITE") for unit in units))
    request = request_for(specification=specification.identity, population=allocation.identity, source=source,
        fixed_map=products.identity(calibrated), unit_ids=units, endpoint_ids=e3.e3_sampling_endpoint_ids(specification))
    return SimpleNamespace(specification=specification, allocation=allocation, assessment=assessment,
        calibrated_freeze=calibrated, model_freeze=model, comparison_request=request)


def evaluate(case, **changes):
    return e3.assess_e3_sampling(**{**vars(case), **changes})


def test_e3_versioned_admission_uses_actual_conditional_math_and_preserves_legacy_bytes(e3_case):
    before = e3_case.assessment.canonical_bytes()
    assert evaluate(e3_case).comparison_status == "UNEVALUABLE"
    admitted = evaluate(e3_case, comparison_evidence=evidence_for(e3_case.comparison_request))
    assert admitted.comparison_status == "SUPPORTED"
    assert "SAMPLING_ASSUMPTION_NOT_AUTHENTICATED" not in admitted.reason_codes
    assert "CALIBRATION_QUERY_SAMPLING_EVIDENCE_INCOMPLETE" in admitted.reason_codes
    assert e3_case.assessment.canonical_bytes() == before
    assert "SAMPLING_ASSUMPTION_NOT_AUTHENTICATED" in e3.conditional_reasons(
        e3_case.specification, e3_case.allocation, e3_case.assessment)
    assert decode_canonical_bytes(admitted.canonical_bytes(), e3.ProtectedE3SamplingReadout, maximum_bytes=None) == admitted


def test_e3_true_sampling_support_retains_a_negative_fixed_criterion(e3_case):
    rows = tuple(replace(value, success=False, comparisons=tuple((method, view, Decimal(0))
        for method, view, _ in value.comparisons), reasons=("NO_PAIRED_IMPROVEMENT",)) for value in e3_case.assessment.decisions)
    assessment = replace(e3_case.assessment, decisions=rows, successes=0,
        binomial_tail_numerator=1, binomial_tail_denominator=1, criterion_met=False)
    result = evaluate(e3_case, assessment=assessment, comparison_evidence=evidence_for(e3_case.comparison_request))
    assert result.comparison_status == "NOT_SUPPORTED"
    assert "CONDITIONAL_CRITERION_NOT_MET" in result.reason_codes


def test_e3_calibration_scope_cannot_supply_comparison_iid_or_joint_query_coverage(e3_case):
    units = e3_case.allocation.unit_ids("calibration")
    query = e3_case.allocation.unit_ids("evaluation")[0]
    request = request_for(sampling.E3_CALIBRATION, specification=e3_case.specification.identity,
        population=e3_case.allocation.identity, source=e3_case.comparison_request.scope.source,
        fixed_map=products.identity(e3_case.model_freeze), unit_ids=tuple(sorted((*units, query))),
        calibration_unit_ids=units, query_unit_ids=(query,), endpoint_ids=e3.e3_sampling_endpoint_ids(e3_case.specification))
    result = evaluate(e3_case, calibration_requests=(request,), calibration_evidence=(evidence_for(request),))
    assert result.comparison_status == "UNEVALUABLE"
    assert result.calibration[0][1].disposition == "SUPPORTED"
    assert "CALIBRATION_COVERAGE_SINGLE_QUERY_MARGINAL_ONLY" in result.reason_codes
    with pytest.raises(ValueError, match="repeats a marginal query"):
        evaluate(e3_case, calibration_requests=(request, request), calibration_evidence=(None, None))
    changed = request_for(sampling.E3_CALIBRATION, specification=e3_case.specification.identity,
        population=e3_case.allocation.identity, source=e3_case.comparison_request.scope.source,
        fixed_map=products.identity(e3_case.calibrated_freeze), unit_ids=tuple(sorted((*units, query))),
        calibration_unit_ids=units, query_unit_ids=(query,), endpoint_ids=e3.e3_sampling_endpoint_ids(e3_case.specification))
    with pytest.raises(ValueError, match="fitted map"):
        evaluate(e3_case, calibration_requests=(changed,), calibration_evidence=(None,))


@pytest.mark.parametrize("damage", ("map", "endpoint", "whole-root"))
def test_e3_sampling_cannot_substitute_actual_map_endpoint_or_population(e3_case, damage):
    scope = e3_case.comparison_request.scope
    change = {"fixed_map": pin("map.foreign")} if damage == "map" else (
        {"endpoint_ids": scope.endpoint_ids[:-1]} if damage == "endpoint" else {"unit_ids": scope.unit_ids[:-1]})
    request = request_for(specification=scope.specification, population=scope.population, source=scope.source,
        fixed_map=scope.fixed_map, unit_ids=scope.unit_ids, endpoint_ids=scope.endpoint_ids)
    changed = replace(request.scope, **change)
    request = replace(request, scope=changed, method=replace(request.method, config=changed.identity))
    with pytest.raises(ValueError, match="whole-root scope"):
        evaluate(e3_case, comparison_request=request)


@pytest.fixture(scope="module")
def factorial_case():
    # Existing fixtures are entirely in-memory typed source/score constructors.
    # No native worker, publication, temporary file or environment is involved.
    from tests import test_matrix_programme_factorial as fixture
    exposed = fixture.exposed.__wrapped__()
    polynomial = fixture.polynomial.__wrapped__(exposed)
    calculation = fixture.assessment.__wrapped__(polynomial)
    specification, programme = polynomial.factorial_specification, polynomial.programme
    request = request_for(sampling.E4_FACTORIAL, specification=specification.identity, population=programme.identity,
        source=programme.bank, fixed_map=specification.identity, unit_ids=programme.group_ids,
        endpoint_ids=tuple(sorted(fixture.method.E4_COMPARISONS)))
    return dict(request=request, evidence=evidence_for(request), programme=programme,
        specification=specification, calculation=calculation)


def test_e4_independent_premise_retains_all_twelve_slots_and_old_conditional_record(factorial_case):
    before = factorial_case["calculation"].canonical_bytes()
    result = e4.assess_factorial_sampling(**factorial_case)
    assert len(result.group_ids) == 32 and len(result.family_slots) == 12
    assert sum(scientific != "UNEVALUABLE" for _, _, scientific in result.family_slots) == 7
    assert all(conditional == scientific for _, conditional, scientific in result.family_slots)
    assert factorial_case["calculation"].canonical_bytes() == before
    missing = e4.assess_factorial_sampling(**{**factorial_case, "evidence": None})
    assert all(scientific == "UNEVALUABLE" for _, _, scientific in missing.family_slots)
    assert decode_canonical_bytes(result.canonical_bytes(), e4.ScheduledFactorialSamplingReadout, maximum_bytes=None) == result


@pytest.mark.parametrize("programme", ("E3", "E4"))
def test_follow_on_registration_uses_real_preparation_and_reveal_with_no_legacy_replacement(programme):
    declaration = bindings.sampling_declaration(programme)
    factory = declaration.provider_factory()
    assert factory.registration.adjudication_output_id == "adjudication"
    assert factory.runner_preparation_factory is not None
    assert tuple(port.port_id for port in declaration.input_ports) == ("custody", "inputs")
    assert declaration.capability_version == "2.0.0"
    assert factory.binding.binding_id == "executable." + bindings.KEYS[programme]
    with pytest.raises(PermissionError, match="parent-side"):
        declaration.runner_factory().execute(SimpleNamespace())


def test_missing_current_grant_refuses_before_any_scientific_input_or_original_read(monkeypatch):
    reads = []
    class RefusingCurrentCustody:
        def __init__(self, **kwargs):
            pass
        def current_task(self, context, runner):
            reads.append("actual-current-grant-check")
            raise PermissionError("actual stored reveal grant absent")
        def task_inputs(self, context, task):
            pytest.fail("scientific input accessed before actual grant")
    monkeypatch.setattr(runtime, "CurrentIssuedTaskCustody", RefusingCurrentCustody)
    with pytest.raises(PermissionError, match="stored reveal grant absent"):
        runtime.prepare_matrix_sampling(SimpleNamespace(writer=object(), reveal_authority_id=None),
            SimpleNamespace(), bindings.MatrixSamplingWorker("E3"))
    assert reads == ["actual-current-grant-check"]


def test_prior_gate_locator_admits_evidence_id_only_as_an_exact_installed_identity_field():
    binding = RecursivePriorExecutionBinding("binding.exposed.sampling", pin("issue.original",
        "empirical-lawhood/runtime/issued-executable-study-manifest"), pin("execution.original",
        "empirical-lawhood/planning/study-operation-authority"), pin("package.original", "empirical-lawhood/api/experiment-package"),
        pin("plan.original", "empirical-lawhood/runtime/execution-plan"), "run.exposed", "task.exposed",
        pin("receipt.original", "empirical-lawhood/runtime/canonical-task-receipt"), "artifact.original",
        pin("evidence.original", "empirical-lawhood/planning/scientific-source-gate-evidence"), record_id_field="evidence_id")
    assert decode_canonical_bytes(binding.canonical_bytes(), RecursivePriorExecutionBinding, maximum_bytes=None) == binding
    with pytest.raises(ValueError, match="identifier field"):
        replace(binding, record_id_field="claimed_sampling_status")
    with pytest.raises(ValueError, match="identifier field"):
        replace(binding, record_id_field=1)


def prior_product(reference):
    binding = RecursivePriorExecutionBinding("binding." + reference.object_id, pin("issue.original",
        "empirical-lawhood/runtime/issued-executable-study-manifest"), pin("execution.original",
        "empirical-lawhood/planning/study-operation-authority"), pin("package.original", "empirical-lawhood/api/experiment-package"),
        pin("plan.original", "empirical-lawhood/runtime/execution-plan"), "run.exposed", "task." + reference.object_id,
        pin("receipt." + reference.object_id, "empirical-lawhood/runtime/canonical-task-receipt"), "artifact." + reference.object_id,
        reference)
    return bindings.MatrixSamplingOriginalProduct(binding, pin("reveal.original", "empirical-lawhood/planning/study-operation-authority"))


class MemoryReader:
    def __init__(self, payload):
        self.stream = BytesIO(payload)
        self.bytes_read = 0
    def read(self, size=-1):
        data = self.stream.read(size)
        self.bytes_read += len(data)
        return data
    def close(self):
        self.stream.close()


def memory_invocation(e3_case):
    """Actual typed contracts and in-memory bytes, without issue/custody claims."""
    data = bindings.MatrixE3SamplingInputs("inputs.exposed.sampling", **vars(e3_case), comparison_evidence=None)
    custody = bindings.MatrixSamplingInvocationCustody("custody.exposed.sampling",
        tuple(prior_product(value) for value in data.original_products), ())
    inputs_ref, custody_ref = bindings._reference(data), bindings._reference(custody)
    task_id = bindings.sampling_task_id("E3", inputs_ref, custody_ref)
    config = bindings.MatrixSamplingConfig("config." + task_id, "E3", inputs_ref, custody_ref, data.unit_ids)
    declaration = bindings.sampling_declaration("E3")
    manifest = declaration.manifest()
    values = (("automatic", config), ("custody", custody), ("inputs", data))
    ports, contracts, external, edges = [], [], [], []
    for name, value in values:
        raw = value.canonical_bytes()
        sealed = name == "inputs"
        access, visibility = (Access.EVALUATION_SEALED, Visibility.PROSPECTIVE) if sealed else (Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
        generic = ArtifactGenericValidation("validation.exposed." + name, "1.0.0", "1"*64, value.SCHEMA, ArtifactProfile.CANONICAL_JSON)
        logical = LogicalArtifactIdentity("artifact." + name, value.fingerprint(), value.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", visibility, (), access, generic)
        binding = WorkerInputBinding(logical.logical_artifact_id, "materialization." + name, value.SCHEMA,
            "application/json", len(raw), visibility, access, WorkerInputKind.EXTERNAL)
        ports.append(WorkerInputPort(binding, MemoryReader(raw)))
        contracts.append(PreparedNativeInputContract(logical, binding, value.fingerprint()))
        external.append(ExternalInputSpec("input." + name, logical.logical_artifact_id, value.fingerprint(), value.SCHEMA,
            "application/json", len(raw), visibility, access, None))
        if name != "automatic":
            edges.append(ScientificInputSpec("edge." + name, name, ScientificInputRole.SOURCE, None, None,
                "external." + name, "scientific." + name, logical.logical_artifact_id, value.SCHEMA, "application/json",
                len(raw), access, visibility, BarrierKind.NONE))
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), "artifact.automatic")
    output_ports = tuple(WorkerOutputPort(task_id + "." + name, kind.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "output." + name) for name, kind in (("adjudication", ScientificAdjudicationRecord), ("product", e3.ProtectedE3SamplingReadout)))
    requirement = CapabilityRequirement(manifest.capability_key, manifest.capability_version, manifest.kind,
        config_ref, manifest.input_schema_ids, manifest.output_schema_ids, manifest.permissions,
        EvidenceCeiling.RESPONSE, Access.EVALUATOR_REVEAL, bindings.BUDGET)
    task = ExecutionTask(task_id, ScientificStage.EVALUATE, requirement, manifest.implementation_sha256, (), tuple(external),
        tuple(ArtifactOutputSpec(port.output_id, port.logical_artifact_id, "exposed/" + name + ".json", port.payload_schema,
            port.profile, port.media_type, Visibility.OUTCOME_VISIBLE, (Visibility.PROSPECTIVE,), Access.EVALUATION_REVEALED)
            for name, port in zip(("adjudication", "product"), output_ports, strict=True)),
        (), BarrierKind.REVEAL, 1, ("obligation.exposed.sampling",), scientific_inputs=tuple(edges))
    plan = pin("plan.exposed.sampling", "empirical-lawhood/runtime/execution-plan")
    authority = ScientificAdjudicationContext(plan, "world.exposed.sampling", WorldKind.NUMERICAL_SIMULATOR,
        pin(bindings.sampling_relation_id(config)), "unit.matrix-whole-root", (pin("cutoff.original", "empirical-lawhood/kernel/information-cutoff"),),
        Visibility.OUTCOME_VISIBLE, Access.EVALUATION_REVEALED)
    context = TaskContext("run.exposed.sampling", task_id, "attempt.exposed.sampling", config_ref,
        tuple(port.binding for port in ports), tuple(ports), output_ports, manifest.permissions,
        Access.EVALUATOR_REVEAL, bindings.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL,
        scientific_adjudication_context=authority)
    package_sources = (("synthetic/exposed.py", "1"*64),)
    implementation = RecursiveImplementationBinding(package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(),
        "2"*64, "3"*40, True)
    prepared = PreparedInvocationContract("prepared.exposed.sampling", manifest, implementation,
        PreparedWorkerEnvironment("/synthetic/python", "4"*64, "/synthetic", ()), context.run_id, task_id,
        context.attempt_id, config_ref, tuple(contracts), output_ports, manifest.permissions, Access.EVALUATOR_REVEAL,
        bindings.BUDGET, WorkerIsolationProfile.TRUSTED_LOCAL, execution_plan=plan,
        execution_task=ObjectIdentity.from_record(task_id, task), execution_task_record=task,
        scientific_adjudication_context=authority, required_input_artifact_ids=tuple(port.artifact_id for port in ports))
    return bindings.MatrixSamplingWorker("E3", prepared_scope=(context.run_id, task_id, context.input_materialization_ids, plan)), replace(context, prepared_invocation=prepared)


def test_registered_worker_executes_exact_in_memory_conditional_route_and_closes_inputs(e3_case):
    runner, context = memory_invocation(e3_case)
    result = runner.execute(context)
    readout = decode_canonical_bytes(result.outputs[1].payload, e3.ProtectedE3SamplingReadout, maximum_bytes=None)
    adjudication = decode_canonical_bytes(result.outputs[0].payload, ScientificAdjudicationRecord, maximum_bytes=None)
    assert readout.comparison_status == "UNEVALUABLE"
    assert adjudication.scientific_status.value == "UNEVALUABLE"
    assert adjudication.matches_context(context.scientific_adjudication_context)
    assert all(port._reader.stream.closed for port in context.input_ports)


def test_absent_or_substituted_parent_preparation_refuses_before_input_reads(e3_case):
    runner, context = memory_invocation(e3_case)
    runner.prepared_scope = (*runner.prepared_scope[:-1], pin("foreign.plan", "empirical-lawhood/runtime/execution-plan"))
    with pytest.raises(PermissionError, match="genuine issued numerical reveal"):
        runner.execute(context)
    assert all(port.bytes_read == 0 for port in context.input_ports)


def test_sampling_custody_rejects_mutable_outer_and_publication_row_sequences(e3_case):
    original = prior_product(products.identity(e3_case.assessment))
    for originals, evidence in (([original], ()), ((original,), [])):
        with pytest.raises(ValueError, match="custody census"):
            bindings.MatrixSamplingInvocationCustody("custody.mutable", originals, evidence)
    request = e3_case.comparison_request
    evidence = evidence_for(request)
    prior = original.prior_execution
    for gates, publications in (([], ()), ((), []), ((), ([pin("mutable.row"), object()],))):
        with pytest.raises(ValueError, match="execution and publication locators"):
            bindings.MatrixSamplingEvidenceCustody("custody.mutable-evidence", evidence.identity, prior, gates, publications,
                None, None)


def test_sampling_worker_rejects_aliased_duplicate_ports_before_read(e3_case):
    runner, context = memory_invocation(e3_case)
    # Model an object corrupted after normal TaskContext validation; the owning
    # scientific consumer must retain its own exact input boundary too.
    object.__setattr__(context, "input_ports", (*context.input_ports, context.input_ports[-1]))
    with pytest.raises(ValueError, match="external input census"):
        runner.execute(context)
    assert all(port.bytes_read == 0 for port in context.input_ports)
