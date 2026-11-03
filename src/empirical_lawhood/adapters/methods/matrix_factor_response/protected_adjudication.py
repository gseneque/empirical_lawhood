# SPDX-License-Identifier: MPL-2.0
"""Reveal the current E3 conditional assessment without inventing sampling warrant.

The original FALSIFY operation owns all scientific arithmetic. This separate
receipt-bound evaluator projects that retained result through the existing
issued/reveal context. No authenticated fixed-map IID sampling assumption is
currently bound, so every projection remains scientifically UNEVALUABLE.
"""

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_sampling_assessment import MatrixSamplingAdmission
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.input_access import validated_scientific_input_edges
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.experimental_statistics import binomial_upper_tail
from empirical_lawhood.runtime.plans import BarrierKind, ExecutionTask, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks

from .experiment_specification import MatrixResponseErrorSpecification
from .protected_experiment_methods import ProtectedE3Assessment, _selected
from .protected_prefix_workers import _read
from .protected_source_records import NAMESPACE, _reference
from .protected_statistical_bindings import BUDGET, _current_dependency, _global_hook, statistical_task_id

KEY = NAMESPACE + '.adjudicate'
MEDIA = 'application/json'
INPUTS = {'specification': MatrixResponseErrorSpecification, 'allocation': UnitAllocation, 'assessment': ProtectedE3Assessment}


def adjudication_task_id(specification, allocation):
    _reference(specification, MatrixResponseErrorSpecification)
    _reference(allocation, UnitAllocation)
    return NAMESPACE + '.adjudicate.' + sha256(canonical_json_bytes((specification, allocation, 'adjudicate'))).hexdigest()


@dataclass(frozen=True, slots=True)
class ProtectedE3AdjudicationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/protected-adjudication-config'
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity

    def __post_init__(self):
        if self.record_id != 'config.' + adjudication_task_id(self.specification, self.allocation):
            raise ValueError('protected E3 adjudication changes its exact selected task identity')

    @property
    def operation(self):
        return 'adjudicate'

    @property
    def mode(self):
        return ''

    @property
    def root(self):
        return None


def _units(config):
    if type(config) is not ProtectedE3AdjudicationConfig:
        raise TypeError('protected E3 adjudication requires its exact outcome-free configuration')
    config.__post_init__()
    return ()


def _operands(config):
    _units(config)
    return tuple(sorted((config.specification.object_fingerprint, config.allocation.object_fingerprint)))


@dataclass(frozen=True, slots=True)
class _RunnerFactory:
    scientific_root_validator: object

    def __call__(self):
        return ProtectedE3Adjudicator(adjudication_declaration(
            scientific_root_validator=self.scientific_root_validator).manifest())


def adjudication_declaration(*, scientific_root_validator):
    _global_hook(scientific_root_validator)
    kinds = (ProtectedE3AdjudicationConfig, ScientificAdjudicationRecord, *INPUTS.values())
    return RecursiveOperationDeclaration(KEY, '1.0.0', KEY + '.conditional-assessment-without-sampling-warrant.v1',
        CapabilityKind.EVALUATOR, ProtectedE3AdjudicationConfig, ScientificStage.EVALUATE,
        tuple(RecursivePortContract(name, kind.SCHEMA, MEDIA, None) for name, kind in sorted(INPUTS.items())),
        (OutputTemplate('adjudication', ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),),
        tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_SEALED_OUTCOMES, CapabilityPermission.REVEAL_OUTCOMES))),
        EvidenceCeiling.RESPONSE, OutcomeAccess.EVALUATOR_REVEAL, VisibilityCeiling.OUTCOME_VISIBLE, BUDGET,
        ('complete-current-assessment-denominator', 'no-invented-sampling-warrant', 'separate-issued-reveal-context'),
        _RunnerFactory(scientific_root_validator), {kind.SCHEMA: kind for kind in kinds},
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=_units, scientific_operand_sha256s=_operands,
            scientific_root_validator=scientific_root_validator, adjudication_output_id='adjudication'),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.REVEAL),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))


def conditional_reasons(specification, allocation, assessment):
    """Check complete retained decisions and exact conditional arithmetic only."""
    _selected(specification, allocation)
    if type(assessment) is not ProtectedE3Assessment:
        raise TypeError('protected E3 adjudication requires the exact retained assessment')
    assessment.__post_init__()
    expected = allocation.unit_ids('evaluation')
    if (assessment.specification != specification.identity or assessment.allocation != allocation.identity
            or tuple(row.unit_id for row in assessment.decisions) != expected
            or any(len(allocation.unit_ids(population.role.lower())) != population.expected_units
                for population in specification.populations)):
        raise ValueError('protected E3 adjudication changes the complete assigned original denominator')
    for row in assessment.decisions:
        if (tuple((baseline, view) for baseline, view, _ in row.comparisons) != (
                ('ALL_ORIGIN_RIDGE', 'fine'), ('ALL_ORIGIN_RIDGE', 'primary'),
                ('RAW_TRAIN_MEDIAN', 'fine'), ('RAW_TRAIN_MEDIAN', 'primary'))
                or row.success != (row.usable and all(value is not None and value > specification.assessment.improvement_margin
                    for _, _, value in row.comparisons))):
            raise ValueError('protected E3 adjudication changes the original strict paired conditional decision')
    tail = binomial_upper_tail(len(expected), assessment.successes, specification.assessment.null_probability)
    if (Fraction(assessment.binomial_tail_numerator, assessment.binomial_tail_denominator) != tail
            or assessment.criterion_met != (tail <= specification.assessment.alpha
                and assessment.usable_units >= specification.assessment.minimum_usable_units)):
        raise ValueError('protected E3 adjudication changes exact complete-denominator conditional arithmetic')
    reasons = {'SAMPLING_ASSUMPTION_NOT_AUTHENTICATED',
        'CONDITIONAL_CRITERION_MET' if assessment.criterion_met else 'CONDITIONAL_CRITERION_NOT_MET',
        'ASSIGNED_CONFIRMATION_UNITS_' + str(len(expected)), 'USABLE_CONFIRMATION_UNITS_' + str(assessment.usable_units),
        'CONDITIONAL_SUCCESSES_' + str(assessment.successes)}
    if assessment.usable_units < len(expected):
        reasons.add('NONUSE_RETAINED_IN_ASSIGNED_DENOMINATOR')
    reasons.update(reason for row in assessment.decisions for reason in row.reasons)
    return tuple(sorted(reasons))


class ProtectedE3Adjudicator:
    def __init__(self, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            return self._execute(context)
        finally:
            if type(context) is TaskContext:
                for port in context.input_ports:
                    port.close()

    def _execute(self, context):
        if type(context) is not TaskContext:
            raise TypeError('protected E3 adjudication requires the actual current prepared task')
        context.__post_init__()
        prepared, authority = context.prepared_invocation, context.scientific_adjudication_context
        if (type(prepared) is not PreparedInvocationContract or type(prepared.execution_task_record) is not ExecutionTask
                or prepared.manifest != self.manifest or self.manifest.capability_key != KEY or prepared.native_effect
                or context.permissions != self.manifest.permissions or not self.manifest.resource_ceiling.contains(context.resource_budget)
                or context.outcome_access is not OutcomeAccess.EVALUATOR_REVEAL
                or prepared.execution_task_record.stage is not ScientificStage.EVALUATE
                or prepared.execution_task_record.barrier is not BarrierKind.REVEAL
                or type(authority) is not ScientificAdjudicationContext
                or authority.execution_plan != prepared.execution_plan
                or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
                or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
                or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
                or authority.plumbing_only or authority.fixture_scope_id is not None):
            raise ValueError('protected E3 adjudication requires its exact issued numerical reveal context before outcome reads')
        authority.__post_init__()
        ports = {port.artifact_id: port for port in context.input_ports}
        contracts = {row.artifact_id: row for row in prepared.inputs}
        config_port = ports.get(context.config.artifact_id)
        if (config_port is None or config_port.kind is not WorkerInputKind.EXTERNAL
                or (config_port.payload_schema, config_port.media_type) != (ProtectedE3AdjudicationConfig.SCHEMA, MEDIA)
                or (context.config.config_schema, context.config.config_schema_sha256) !=
                    (self.manifest.config_schema, self.manifest.config_schema_sha256)):
            raise ValueError('protected E3 adjudication loses its exact automatic configuration')
        config = _read(config_port, contracts[config_port.artifact_id], ProtectedE3AdjudicationConfig)
        if (context.config.config_id != config.record_id or context.config.content_sha256 != config.fingerprint()
                or context.task_id != adjudication_task_id(config.specification, config.allocation)):
            raise ValueError('protected E3 adjudication substitutes the selected current configuration')
        edges = validated_scientific_input_edges(context, config_port=config_port)
        if (len(edges) != 3 or {edge.consumer_input_id for edge in edges} != set(INPUTS)
                or {edge.operational_logical_artifact_id for edge in edges} != set(ports) - {config_port.artifact_id}
                or len(ports) != 4 or any(port.outcome_access not in (OutcomeAccess.OUTCOME_BLIND,
                    OutcomeAccess.DEVELOPMENT_VISIBLE, OutcomeAccess.EVALUATION_SEALED)
                    or port.visibility_ceiling not in (VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.DEVELOPMENT_ONLY)
                    for port in (ports[edge.operational_logical_artifact_id] for edge in edges))):
            raise ValueError('protected E3 adjudication changes exact current whole-unit input edges or receives revealed inputs')
        values = {}
        for edge in edges:
            name, port = edge.consumer_input_id, ports[edge.operational_logical_artifact_id]
            if (port.payload_schema, port.media_type) != (INPUTS[name].SCHEMA, MEDIA):
                raise ValueError('protected E3 adjudication changes the exact input contract')
            if name == 'assessment':
                _current_dependency(context, edge, port, statistical_task_id(config.specification, config.allocation, 'assess'), 'product')
            elif port.kind is not WorkerInputKind.EXTERNAL or edge.producer_task_id is not None:
                raise ValueError('protected E3 adjudication substitutes its original selected external metadata')
            values[name] = _read(port, contracts[port.artifact_id], INPUTS[name])
        specification, allocation, assessment = (values[name] for name in ('specification', 'allocation', 'assessment'))
        if (specification.identity, allocation.identity) != (config.specification, config.allocation):
            raise ValueError('protected E3 adjudication substitutes its actual selected specification or allocation')
        reasons = conditional_reasons(specification, allocation, assessment)
        outputs = prepared.execution_task_record.outputs
        if (len(context.output_ports) != 1 or len(outputs) != 1
                or context.output_ports[0].output_id != context.task_id + '.adjudication'
                or context.output_ports[0].logical_artifact_id is None
                or (context.output_ports[0].payload_schema, context.output_ports[0].profile, context.output_ports[0].media_type) !=
                    (ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA)
                or outputs[0].outcome_access is not authority.outcome_access
                or outputs[0].visibility_ceiling is not authority.visibility_ceiling):
            raise ValueError('protected E3 adjudication changes its actual compiled revealed output contract')
        record = ScientificAdjudicationRecord('adjudication.' + context.run_id + '.' + context.task_id,
            context.run_id, context.task_id, authority.execution_plan, context.input_materialization_ids,
            (context.output_ports[0].logical_artifact_id,), context.dependency_receipt_ids,
            authority.evidence_world_id, authority.evidence_world_kind, authority.relation, authority.independent_unit_id,
            authority.information_cutoffs, authority.visibility_ceiling, authority.outcome_access,
            AdjudicationEvaluability.UNEVALUABLE, ScientificStatus.UNEVALUABLE, AdmissionStatus.UNEVALUABLE, reasons)
        return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, record.canonical_bytes()),),
            (ReceiptCheck('protected-e3-revealed-conditional-assessment-without-authenticated-sampling-warrant', True, ()),))


@dataclass(frozen=True, slots=True)
class ProtectedE3SamplingReadout(CanonicalRecord):
    """Versioned semantic adjudication without rewriting the original result.

    Comparison IID support and each single-query calibration premise are
    independent claims. None grants issue, reveal, source or numerical authority.
    The protected caller retains those original entry and publication checks.
    """

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/protected-sampling-readout'
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    assessment: ObjectIdentity
    comparison: MatrixSamplingAdmission
    calibration: tuple[tuple[str, MatrixSamplingAdmission], ...]
    comparison_status: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_sampling_assessment import E3_CALIBRATION, E3_COMPARISON
        from empirical_lawhood.kernel.serialization import require_sorted_unique_strings, validate_stable_id

        validate_stable_id(self.record_id)
        if (type(self.assessment) is not ObjectIdentity or self.assessment.object_schema != ProtectedE3Assessment.SCHEMA
                or type(self.comparison) is not MatrixSamplingAdmission or self.comparison.premise != E3_COMPARISON
                or self.comparison_status not in ('SUPPORTED', 'NOT_SUPPORTED', 'UNEVALUABLE')
                or self.comparison_status != 'UNEVALUABLE' and self.comparison.disposition != 'SUPPORTED'
                or tuple(unit for unit, _ in self.calibration) != tuple(sorted({unit for unit, _ in self.calibration}))
                or any(type(value) is not MatrixSamplingAdmission or value.premise != E3_CALIBRATION
                    for _, value in self.calibration)):
            raise ValueError('protected E3 sampling readout promotes unsupported or mixed-scope premises')
        self.comparison.__post_init__()
        for unit, value in self.calibration:
            validate_stable_id(unit)
            value.__post_init__()
        require_sorted_unique_strings(self.reason_codes, field_name='protected E3 sampling reasons', allow_empty=False)


def e3_sampling_endpoint_ids(specification):
    """Name the actual fixed fifteen-output map, not a selected outcome subset."""
    specification.__post_init__()
    return tuple(sorted(f'output.{description.lower()}.horizon-{horizon}'
        for description in specification.measurement.descriptions for horizon in specification.measurement.horizons))


def assess_e3_sampling(*, specification, allocation, assessment, calibrated_freeze, model_freeze,
        comparison_request, comparison_evidence=None, calibration_requests=(), calibration_evidence=()):
    """Replay E3 arithmetic and admit separately scoped scientific premises.

    This pure function authenticates no storage. Its owning protected worker
    must first replay the original source/gate and freeze custody; unsupported
    independent-unit or timing claims remain missing scientific evidence.
    Calibration supports marginal coverage for each named query only; even
    support for every query does not establish joint 64-query coverage.
    """
    from empirical_lawhood.adapters.methods.matrix_sampling_assessment import (
        E3_CALIBRATION, E3_COMPARISON, MatrixSamplingRequest, assess_matrix_sampling,
    )
    from .protected_experiment_methods import ProtectedE3FrozenProducts, identity

    reasons = set(conditional_reasons(specification, allocation, assessment))
    if type(calibrated_freeze) is not ProtectedE3FrozenProducts or type(model_freeze) is not ProtectedE3FrozenProducts:
        raise TypeError('E3 sampling requires exact original model and separate calibrated freezes')
    for frozen in (calibrated_freeze, model_freeze):
        frozen.__post_init__()
        if (frozen.specification, frozen.allocation) != (specification.identity, allocation.identity):
            raise ValueError('E3 sampling substitutes its original frozen specification or allocation')
    if (assessment.calibrated_freeze != identity(calibrated_freeze) or calibrated_freeze.calibration is None
            or calibrated_freeze.model_freeze != identity(model_freeze) or model_freeze.calibration is not None
            or calibrated_freeze.models != model_freeze.models or calibrated_freeze.reservation_join != model_freeze.reservation_join):
        raise ValueError('E3 sampling changes its actual separate model/calibration freezes')
    if type(comparison_request) is not MatrixSamplingRequest:
        raise TypeError('E3 sampling requires its exact independent comparison request')
    comparison_request.__post_init__()
    scope = comparison_request.scope
    expected = allocation.unit_ids('evaluation')
    endpoints = e3_sampling_endpoint_ids(specification)
    if (scope.premise != E3_COMPARISON or scope.specification != specification.identity
            or scope.population != allocation.identity or scope.source not in allocation.sources
            or scope.fixed_map != identity(calibrated_freeze) or scope.unit_ids != expected or scope.endpoint_ids != endpoints):
        raise ValueError('E3 sampling changes its complete fixed-map comparison source, endpoints or whole-root scope')
    comparison = assess_matrix_sampling(comparison_request, comparison_evidence)
    calibration = []
    if (type(calibration_requests) is not tuple or type(calibration_evidence) is not tuple
            or any(type(row) is not MatrixSamplingRequest for row in calibration_requests)
            or len(calibration_requests) != len(calibration_evidence)):
        raise TypeError('E3 calibration requires an exact request/evidence pair per declared marginal query')
    for request, evidence in zip(calibration_requests, calibration_evidence, strict=True):
        request.__post_init__()
        current = request.scope
        if (current.premise != E3_CALIBRATION or current.specification != specification.identity
                or current.population != allocation.identity or current.source != scope.source
                or current.fixed_map != identity(model_freeze) or current.endpoint_ids != endpoints
                or current.calibration_unit_ids != allocation.unit_ids('calibration')
                or current.query_unit_ids[0] not in expected):
            raise ValueError('E3 calibration sampling substitutes its original fitted map, complete CAL or marginal query')
        calibration.append((current.query_unit_ids[0], assess_matrix_sampling(request, evidence)))
    if len({unit for unit, _ in calibration}) != len(calibration):
        raise ValueError('E3 sampling repeats a marginal query to imply broader coverage')
    comparison_status = ('SUPPORTED' if assessment.criterion_met else 'NOT_SUPPORTED') if comparison.disposition == 'SUPPORTED' else 'UNEVALUABLE'
    if comparison.disposition == 'SUPPORTED':
        reasons.discard('SAMPLING_ASSUMPTION_NOT_AUTHENTICATED')
    reasons.update(comparison.reason_codes)
    reasons.add('CALIBRATION_COVERAGE_SINGLE_QUERY_MARGINAL_ONLY')
    if len(calibration) != len(expected):
        reasons.add('CALIBRATION_QUERY_SAMPLING_EVIDENCE_INCOMPLETE')
    return ProtectedE3SamplingReadout('sampling.' + assessment.record_id, identity(assessment), comparison,
        tuple(sorted(calibration)), comparison_status, tuple(sorted(reasons)))
