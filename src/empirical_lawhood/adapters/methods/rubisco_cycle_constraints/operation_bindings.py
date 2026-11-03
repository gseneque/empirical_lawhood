# SPDX-License-Identifier: MPL-2.0
"""Registered pure cycle supplier and authentic source-bound later consumers."""
from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import SourceAudit as MacroSourceAudit
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (AssessmentDisposition, AssessmentPhase, DevelopmentStudySpec,
                                                            RequirementSupplyAssessment)
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)
from . import assessment
from .contracts import (NAMESPACE, UNIT, QUESTION, CycleOperationConfig, MechanismSourceAudit, CycleSupply, CycleUseProduct,
                        CycleInstanceInput, identity, scope)

MAX_BYTES = None
MEDIA = 'application/json'
BUDGET = ResourceBudget(1, None, 0, None, None, None)
PHASES = (
    ('reuse', (('instance', CycleInstanceInput), ('macro-source', MacroSourceAudit), ('supplier', CycleUseProduct)), CycleUseProduct, ScientificStage.FALSIFY),
    ('supply', (('source', MechanismSourceAudit),), CycleSupply, ScientificStage.SYNTHESIZE),
    ('use', (('instance', CycleInstanceInput), ('macro-source', MacroSourceAudit), ('supplier', CycleSupply)), CycleUseProduct, ScientificStage.FALSIFY),
)


def scientific_operand_sha256s(config):
    return tuple(sorted({config.design.source.object_fingerprint, *(row.object_fingerprint for row in config.operands)}))


def scientific_unit_ids(config):
    return (UNIT,)


def development_root(config, *, study_id):
    view = 'view.rubisco-cycle.complete-conditional-denominator'
    claim = ClaimSpec(f'claim.{NAMESPACE}.{config.operation}', 'world.rubisco-cycle.analytic',
        'population.rubisco-cycle.hypothetical-conditions', QUESTION,
        'Source-bound conditional model assumptions and complete nested scenarios; no fresh biological or physical independent units.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Independent mathematical supply/use does not infer enzyme microrates, nominate candidates or grant biochemical qualification.',
        config.design.assumptions, numerical_view_ids=(view,))
    operands = tuple(sorted({identity(config.design), config.design.source, *config.operands}, key=lambda row: row.object_id))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(scope(config.design).system_id, config.design), 'world.rubisco-cycle.analytic',
                               WorldKind.ANALYTIC_REFERENCE, (UNIT,), (view,), (claim,), operands)


def scientific_root_validator(config, context):
    phase = next(row for row in PHASES if row[0] == config.operation)
    if (type(context.root) is not DevelopmentStudySpec or context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != f'{NAMESPACE}.{config.operation}' or context.stage is not phase[3]
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record != config):
        raise ValueError('cycle operation changes exact scientific root, units, stage, selected config or access')
    incoming = tuple(row for row in context.links if row.consumer_node_id == context.node_id)
    expected = {name: ('OUTCOME' if config.operation == 'reuse' else 'MODEL') if name == 'supplier' else 'SOURCE' for name, _ in phase[1]}
    if (len(incoming) != len(expected) or {row.consumer_input_id for row in incoming} != set(expected)
            or any(row.external_input_id is None or row.scientific_role != expected[row.consumer_input_id] for row in incoming)):
        raise ValueError('cycle operation changes exact external input or scientific role census')
    for requirement in context.requirements:
        if (requirement.scope != scope(config.design)
                or requirement.consumer_operation_id != context.node_id or requirement.assessment_operation_id != context.node_id):
            raise ValueError('cycle requirement changes original conditional model scope or selected assessor')


def project_cycle_assessments(record, requirement, connection):
    from .recursive_translation import validate_requirement
    validate_requirement(record, requirement, connection)
    evidence = (identity(record),)
    values = []
    for phase in AssessmentPhase:
        disposition = record.disposition
        reasons = () if disposition is AssessmentDisposition.SATISFIED else ('MODEL_PROCEDURE_FAILED_INDEPENDENT_BALANCE',)
        if disposition is not AssessmentDisposition.SATISFIED and phase is AssessmentPhase.ADMISSION:
            disposition = AssessmentDisposition.REFUSED
        if disposition is not AssessmentDisposition.SATISFIED and phase is AssessmentPhase.JOINED:
            disposition = AssessmentDisposition.UNEVALUABLE
        values.append(RequirementSupplyAssessment(f'assessment.{record.instance.instance_id}.{phase.value.lower()}',
            ObjectIdentity.from_record(requirement.requirement_id, requirement), ObjectIdentity.from_record(connection.connection_id, connection),
            phase, disposition, record.instance.instance_id, evidence, reasons))
    return tuple(values)


def operation_manifests():
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_registrations():
    return tuple(declaration.registration() for declaration in operation_declarations())


def output_codecs():
    return {record.SCHEMA: record for record in (CycleOperationConfig, MechanismSourceAudit, CycleSupply, CycleUseProduct, CycleInstanceInput, MacroSourceAudit)}


class CycleRunner:
    def __init__(self, role):
        self.role = role
        self.phase = next(row for row in PHASES if row[0] == role)
        self.manifest = next(row for row in operation_manifests() if row.capability_key == f'{NAMESPACE}.{role}')

    def execute(self, context):
        try:
            _, ports, output_type, _ = self.phase
            expected = {CycleOperationConfig.SCHEMA: CycleOperationConfig, **{record.SCHEMA: record for _, record in ports}}
            if (context.task_id != f'{NAMESPACE}.{self.role}' or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.resource_budget != BUDGET
                    or len(context.input_ports) != len(expected) or {row.payload_schema for row in context.input_ports} != set(expected)):
                raise ValueError('cycle worker substitutes exact input census, resources or access')
            records = {}
            for port in context.input_ports:
                if port.kind is not WorkerInputKind.EXTERNAL or port.media_type != MEDIA or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE:
                    raise ValueError('cycle worker changes exposed canonical source contract')
                payload = port.read()
                if len(payload) != port.size_bytes:
                    raise ValueError('cycle worker changes exact retained source materialization')
                records[port.payload_schema] = decode_canonical_bytes(payload, expected[port.payload_schema], maximum_bytes=None)
            config = records[CycleOperationConfig.SCHEMA]
            if config.operation != self.role or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256:
                raise ValueError('cycle worker substitutes selected immutable config')
            inputs = {name: records[record.SCHEMA] for name, record in ports}
            if tuple(sorted((identity(row) for row in inputs.values()), key=lambda row: row.object_id)) != config.operands:
                raise ValueError('cycle worker substitutes exact configured operands')
            product = assessment.supply(inputs['source']) if self.role == 'supply' else assessment.assess_use(inputs['supplier'], inputs['macro-source'], inputs['instance'])
            design = product.design if type(product) is CycleSupply else product.model.design
            if design != config.design:
                raise ValueError('cycle worker changes mechanism design or original source identity')
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != context.task_id + '.product'
                    or context.output_ports[0].payload_schema != output_type.SCHEMA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON or context.output_ports[0].media_type != MEDIA):
                raise ValueError('cycle worker substitutes exact canonical output census')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, product.canonical_bytes()),),
                                (ReceiptCheck('exact-source-bound-cycle-model-product', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    """Own scientific and inquiry contracts and derive installed projections."""
    from .recursive_translation import (
        describe_contributions, inquiry_endpoint_validator, inquiry_evidence_projector,
        inquiry_outcome_projector, next_wave_builder,
    )

    return tuple(RecursiveOperationDeclaration(
        capability_key=f'{NAMESPACE}.{role}', capability_version='1.0.0',
        implementation_id=f'{NAMESPACE}.source-bound-independent-{role}-v1', kind=CapabilityKind.ANALYSIS,
        config_record_type=CycleOperationConfig, stage=stage,
        input_ports=tuple(RecursivePortContract(key, record.SCHEMA, MEDIA, MAX_BYTES) for key, record in inputs),
        outputs=(OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('complete-latent-denominator', 'independent-normalized-state-balance', 'no-inferred-biological-microrates'),
        runner_factory=lambda phase=role: CycleRunner(phase), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, scientific_root_validator=scientific_root_validator,
            assessment_projector=project_cycle_assessments if role!='supply' else None),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions,
            next_wave_builder=next_wave_builder, inquiry_outcome_projector=inquiry_outcome_projector,
            inquiry_evidence_projector=inquiry_evidence_projector, inquiry_endpoint_validator=inquiry_endpoint_validator))
        for role, inputs, output, stage in PHASES)
