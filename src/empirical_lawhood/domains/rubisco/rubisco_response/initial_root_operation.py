# SPDX-License-Identifier: MPL-2.0
"""Ordinary bounded calculation, independent assessment and retained reuse."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract, RegisteredProvenanceRequirement
from empirical_lawhood.execution.recursive_provider import RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.numerical_runtime import validate_kinetic_producing_provenance
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root import assess_initial_root, calculate_initial_root
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootAnalysisInputs, InitialRootScopedAssessment, InitialRootScopedResult
from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import ASSESS, CALCULATE, QUESTION, USE, analysis_arguments, analytic_units, initial_root_requirement_graph, initial_root_scope, nested_views, project_initial_root_connection, reconstruct_assessment
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact

MEDIA = 'application/json'
MAX_INPUT_BYTES = 64 * 2**20
BUDGET = ResourceBudget(1, 512 * 2**20, 0, 60, 128 * 2**20, MAX_INPUT_BYTES)
PHASES = (
    ('calculate', CALCULATE, (('analysis', InitialRootAnalysisInputs),), InitialRootScopedResult, ScientificStage.TRANSFORM),
    ('assess', ASSESS, (('analysis', InitialRootAnalysisInputs), ('result', InitialRootScopedResult)), InitialRootScopedAssessment, ScientificStage.FALSIFY),
    ('use', USE, (('analysis', InitialRootAnalysisInputs), ('original-assessment', InitialRootScopedAssessment), ('result', InitialRootScopedResult)),
        InitialRootScopedAssessment, ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class InitialRootOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-root-operation-config'
    config_id: str
    operation: str
    analysis: InitialRootAnalysisInputs
    parent: ContributionManifest | None = None

    def __post_init__(self):
        if self.operation not in {row[0] for row in PHASES} or self.config_id != 'config.rubisco-response.initial-root-' + self.operation:
            raise ValueError('initial root configuration changes its exact registered operation')
        exact(self.analysis, InitialRootAnalysisInputs)
        if (self.operation == 'use') != (self.parent is not None):
            raise ValueError('initial root use requires its actual retained contribution')
        if self.parent is not None:
            exact(self.parent, ContributionManifest)
            graph = initial_root_requirement_graph(self.analysis, parent=self.parent)
            if len(self.parent.products) != 2 or {row.record.object_schema for row in self.parent.products} != {
                    InitialRootScopedResult.SCHEMA, InitialRootScopedAssessment.SCHEMA}:
                raise ValueError('initial root contribution must retain its complete original result and independent assessment')
            if self.parent.scope != graph.requirements[0].scope:
                raise ValueError('initial root contribution changes its original endpoint scope')

    @property
    def source(self):
        return self.analysis.model.identity

    @property
    def operands(self):
        return tuple(sorted((self.analysis.request.identity, self.analysis.inputs.identity,
            self.analysis.reviews.identity), key=lambda pin: pin.object_id))


def scientific_operands(config):
    analysis = config.analysis
    return tuple(sorted({analysis.identity, analysis.request.identity, analysis.model.identity, analysis.inputs.identity,
        analysis.reviews.identity, *analysis.reviews.original_sources}, key=lambda row: row.object_id))


def development_root(config, *, study_id):
    analysis = config.analysis
    scope = initial_root_scope(analysis)
    claim = ClaimSpec('claim.' + analysis.request.request_id + '.conditional', scope.world_id,
        scope.population_id, QUESTION,
        'Original exposure groups; processing views, chemical alternatives and joint realizations remain nested. Zero independent biological observations.',
        'unit.original-exposure-group', None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'An exposed source-conditioned decision supplies no biological predictive validation or prospective qualification.',
        ('assumption.rubisco.initial-declared-closure',), numerical_view_ids=nested_views(analysis))
    return DevelopmentStudySpec(study_id, QUESTION, analysis.model.identity, scope.world_id, WorldKind.ANALYTIC_REFERENCE,
        analytic_units(analysis), nested_views(analysis), (claim,), scientific_operands(config))


def validate_root(config, context):
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_translation import graph_contracts
    phase = next(row for row in PHASES if row[0] == config.operation)
    requirements, connections, external, links = graph_contracts(config)
    selected_requirements = tuple(row for row in requirements if row.consumer_operation_id in {ASSESS, USE})
    configs = tuple(row.record for row in context.config_inputs)
    expected_phases = {'use'} if config.parent is not None else {'calculate', 'assess'}
    if (any(type(row) is not InitialRootOperationConfig or row.analysis != config.analysis or row.parent != config.parent for row in configs)
            or {row.operation for row in configs} != expected_phases or len(configs) != len(expected_phases)
            or type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != phase[1] or context.stage is not phase[4]
            or context.unit_ids != analytic_units(config.analysis) or context.selected_unit_ids != analytic_units(config.analysis)
            or context.complete_unit_census or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or context.requirements != selected_requirements or context.connections != connections
            or context.external_inputs != external or context.links != links):
        raise ValueError('initial root operation changes its exact source, consumer, complete census or assessed graph')


def output_codecs():
    return {kind.SCHEMA: kind for kind in (InitialRootOperationConfig, InitialRootAnalysisInputs, InitialRootScopedResult, InitialRootScopedAssessment)}


class InitialRootRunner:
    def __init__(self, operation):
        self.phase = next(row for row in PHASES if row[0] == operation)
        self.operation = operation
        self.manifest = next(row.manifest() for row in operation_declarations() if row.capability_key == self.phase[1])

    def execute(self, context):
        try:
            _, capability, inputs, output_type, _ = self.phase
            kinds = {kind.SCHEMA: kind for _, kind in inputs}
            kinds[InitialRootOperationConfig.SCHEMA] = InitialRootOperationConfig
            if (context.task_id != capability or context.permissions != self.manifest.permissions
                    or context.resource_budget != BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or len(context.input_ports) != len(kinds) or {p.payload_schema for p in context.input_ports} != set(kinds)):
                raise ValueError('initial root worker changes its exact input, resource or exposure contract')
            ports = {port.payload_schema: port for port in context.input_ports}
            records = {}
            for schema, port in ports.items():
                expected_kind = WorkerInputKind.DEPENDENCY if self.operation == 'assess' and schema == InitialRootScopedResult.SCHEMA else WorkerInputKind.EXTERNAL
                if (port.kind is not expected_kind or port.media_type != MEDIA or port.size_bytes > MAX_INPUT_BYTES
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError('initial root worker changes exact source kind, bounded bytes or evidence access')
                if expected_kind is WorkerInputKind.DEPENDENCY:
                    receipts = tuple(row for row in context.dependency_receipts if port.materialization_id in row.output_materialization_ids)
                    if len(receipts) != 1 or receipts[0].task_id != CALCULATE:
                        raise ValueError('initial root assessor lacks the exact original calculation receipt')
                raw = port.read(MAX_INPUT_BYTES + 1)
                if len(raw) != port.size_bytes:
                    raise ValueError('initial root input differs from its complete authenticated materialization')
                records[schema] = decode_canonical_bytes(raw, kinds[schema], maximum_bytes=MAX_INPUT_BYTES)
            config = records[InitialRootOperationConfig.SCHEMA]
            if (config.operation != self.operation or config.config_id != context.config.config_id
                    or config.fingerprint() != context.config.content_sha256
                    or ports[InitialRootOperationConfig.SCHEMA].artifact_id != context.config.artifact_id
                    or records[InitialRootAnalysisInputs.SCHEMA] != config.analysis):
                raise ValueError('initial root worker substitutes its immutable source or consumer selection')
            if self.operation == 'calculate':
                product = InitialRootScopedResult(config.analysis.identity, initial_root_scope(config.analysis),
                    calculate_initial_root(**analysis_arguments(config.analysis)))
            else:
                scoped = records[InitialRootScopedResult.SCHEMA]
                if scoped.analysis != config.analysis.identity or scoped.scope != initial_root_scope(config.analysis):
                    raise ValueError('initial root assessor changes its original result scope')
                result = scoped.result
                if self.operation == 'use':
                    for kind in (InitialRootScopedResult, InitialRootScopedAssessment):
                        current = records[kind.SCHEMA]
                        products = tuple(row for row in config.parent.products if row.record == current.identity)
                        if len(products) != 1 or (ports[kind.SCHEMA].artifact_id, ports[kind.SCHEMA].size_bytes) != (
                                products[0].artifact.artifact_id, products[0].artifact.size_bytes):
                            raise ValueError('initial root reuse changes its exact receipt-bound retained products')
                    previous = records[InitialRootScopedAssessment.SCHEMA]
                    if previous.analysis != config.analysis.identity or previous.scope != scoped.scope:
                        raise ValueError('initial root reuse changes its original assessment scope')
                    reconstruct_assessment(config.analysis, result, previous.assessment)
                product = InitialRootScopedAssessment(config.analysis.identity, scoped.scope,
                    assess_initial_root(result=result, **analysis_arguments(config.analysis)))
            outputs = context.output_ports
            if (len(outputs) != 1 or outputs[0].output_id != capability + '.product'
                    or outputs[0].payload_schema != output_type.SCHEMA or outputs[0].profile is not ArtifactProfile.CANONICAL_JSON
                    or outputs[0].media_type != MEDIA):
                raise ValueError('initial root worker changes its complete output contract')
            raw = product.canonical_bytes()
            if len(raw) > BUDGET.output_bytes:
                raise ValueError('initial root result exceeds the selected bounded output allocation')
            return RunnerResult((TaskOutputPayload(outputs[0].output_id, raw),),
                (ReceiptCheck('exact-original-input-and-independent-joint-decision', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_translation import scientific_work
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_inquiry import describe_contributions, endpoint_validator, evidence_projector, next_wave_builder, outcome_projector, record_identity, claim_assessment_projector
    return tuple(RecursiveOperationDeclaration(
        capability_key=capability, capability_version='1.0.0', implementation_id=capability + '.source-conditioned-exact-v1',
        kind=CapabilityKind.ANALYSIS if operation == 'calculate' else CapabilityKind.FALSIFIER,
        config_record_type=InitialRootOperationConfig, stage=stage,
        input_ports=tuple(RecursivePortContract(name, kind.SCHEMA, MEDIA, MAX_INPUT_BYTES) for name, kind in inputs),
        outputs=(OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('complete-joint-dependence-and-alternatives', 'exact-original-source-and-consumer',
            'independent-threshold-and-conjunction-check', 'zero-new-native-acquisition'),
        runner_factory=lambda phase=operation: InitialRootRunner(phase), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=None if operation == 'calculate' else project_initial_root_connection,
            scientific_operand_sha256s=lambda config: tuple(sorted({row.object_fingerprint for row in scientific_operands(config)})),
            scientific_unit_ids=lambda config: analytic_units(config.analysis), native_effect_slot_ids=lambda config: (),
            scientific_root_validator=validate_root),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions,
            next_wave_builder=next_wave_builder, inquiry_endpoint_validator=endpoint_validator,
            inquiry_evidence_projector=evidence_projector, inquiry_outcome_projector=outcome_projector,
            inquiry_record_identity=record_identity, inquiry_work_projector=scientific_work,
            inquiry_claim_assessment_projector=None if operation == 'calculate' else claim_assessment_projector),
        provenance_requirements=(RegisteredProvenanceRequirement('rubisco-response.selected-numerical-profile.v1',
            validate_kinetic_producing_provenance),))
        for operation, capability, inputs, output, stage in PHASES)
