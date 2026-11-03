# SPDX-License-Identifier: MPL-2.0
"""Strict exposed operation contracts on the existing recursive execution route."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificInputRole, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)
from . import science
from .science import CandidateSupply, CandidateFrontierInput, CandidateAssessment, SourceAudit

NAMESPACE = 'rubisco-candidate-inquiry'
MAX_BYTES = None
BUDGET = ResourceBudget(1, None, 0, None, None, None)
MEDIA = 'application/json'
SOURCE_INPUTS = (('source', SourceAudit),)
PHASES = (('supply', SOURCE_INPUTS, CandidateSupply, ScientificStage.SYNTHESIZE),
          ('use', (('instance', CandidateFrontierInput), ('supplier', CandidateSupply)), CandidateAssessment, ScientificStage.FALSIFY))


@dataclass(frozen=True, slots=True)
class InquiryOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/operation-config'
    config_id: str
    operation: str
    source: ObjectIdentity
    operands: tuple[ObjectIdentity, ...]
    scientific_design: SourceAudit

    def __post_init__(self):
        validate_stable_id(self.config_id, field_name='config_id')
        if self.operation not in {'supply', 'use'} or self.config_id != f'config.{NAMESPACE}.{self.operation}':
            raise ValueError('inquiry operation/configuration identity substitution')
        require_sorted_unique_ids(self.operands, attribute='object_id', field_name='operands')
        if (type(self.scientific_design) is not SourceAudit
                or self.source != ObjectIdentity.from_record(self.scientific_design.input_id, self.scientific_design)):
            raise ValueError('Rubisco inquiry changes exact source audit identity')


def scientific_operand_sha256s(config):
    return tuple(sorted({config.source.object_fingerprint, *(v.object_fingerprint for v in config.operands)}))


def scientific_unit_ids(config):
    return (science.UNIT,)


def development_root(config, *, study_id):
    view = f'view.{NAMESPACE}.exposed-nested-conditions'
    claim = ClaimSpec(f'claim.{NAMESPACE}.{config.operation}', f'world.{NAMESPACE}.exposed',
        f'population.{NAMESPACE}.selected', science.QUESTION,
        'One exposed analytic software contrast with nested conditions; no fresh biological or physical independent units.',
        science.UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, 'Exposed scoped composition grants no biological or physical qualification or EL advantage.',
        ('assumption.exposed-scoped-analysis',), numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id, science.QUESTION, config.source, f'world.{NAMESPACE}.exposed',
        WorldKind.ANALYTIC_REFERENCE, (science.UNIT,), (view,), (claim,),
        tuple(sorted({config.source, *config.operands}, key=lambda v: v.object_id)))


def scientific_root_validator(config, context):
    if type(context.root) is not DevelopmentStudySpec or context.root != development_root(config, study_id=context.root.study_id):
        raise ValueError('inquiry changes its exact scientific root, sources, endpoints or exposure')
    phase = next(v for v in PHASES if v[0] == config.operation)
    if (context.node_id != f'{NAMESPACE}.{config.operation}' or context.stage is not phase[3]
            or context.unit_ids != (science.UNIT,) or context.selected_unit_ids != (science.UNIT,)
            or context.complete_unit_census or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('inquiry changes stage, assigned analytic units or access boundary')
    if len(context.config_inputs) != 1 or context.config_inputs[0].record != config:
        raise ValueError('compact inquiry requires its exact single selected operation')
    incoming = tuple(v for v in context.links if v.consumer_node_id == context.node_id)
    expected = {name: (ScientificInputRole.MODEL.value if name == 'supplier' else 'SOURCE') for name, _ in phase[1]}
    if len(incoming) != len(expected) or {v.consumer_input_id for v in incoming} != set(expected):
        raise ValueError('inquiry scientific input role census differs')
    if any(v.scientific_role != expected[v.consumer_input_id] or v.external_input_id is None for v in incoming):
        raise ValueError('inquiry substitutes exact external source or contribution roles')


def operation_manifests():
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_registrations():
    return tuple(declaration.registration() for declaration in operation_declarations())


def output_codecs():
    return {t.SCHEMA: t for t in (InquiryOperationConfig, CandidateSupply, CandidateFrontierInput, CandidateAssessment, *(t for _, t in SOURCE_INPUTS))}


class InquiryRunner:
    def __init__(self, role):
        self.role = role
        self.phase = next(v for v in PHASES if v[0] == role)
        self.manifest = next(v for v in operation_manifests() if v.capability_key == f'{NAMESPACE}.{role}')

    def execute(self, context):
        try:
            _, inputs, output_type, _ = self.phase
            expected = {InquiryOperationConfig.SCHEMA: InquiryOperationConfig, **{t.SCHEMA: t for _, t in inputs}}
            if (context.task_id != f'{NAMESPACE}.{self.role}' or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.resource_budget != BUDGET
                    or len(context.input_ports) != len(expected)
                    or set(p.payload_schema for p in context.input_ports) != set(expected)):
                raise ValueError('inquiry worker input census, resources or access differs')
            records = {}
            for port in context.input_ports:
                if (port.kind is not WorkerInputKind.EXTERNAL or port.media_type != MEDIA
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
                    raise ValueError('inquiry input changes exact exposed external contract')
                payload = port.read()
                if len(payload) != port.size_bytes:
                    raise ValueError('inquiry input differs from retained materialization')
                records[port.payload_schema] = decode_canonical_bytes(payload, expected[port.payload_schema], maximum_bytes=MAX_BYTES)
            config = records[InquiryOperationConfig.SCHEMA]
            if (config.operation != self.role or config.config_id != context.config.config_id
                    or config.fingerprint() != context.config.content_sha256):
                raise ValueError('inquiry worker selected immutable config differs')
            operands = tuple(sorted((record_identity(records[t.SCHEMA]) for _, t in inputs), key=lambda v: v.object_id))
            if operands != config.operands:
                raise ValueError('inquiry operand identity substitution')
            inputs = {name: records[t.SCHEMA] for name, t in inputs}
            if self.role == 'supply':
                product = science.supply(inputs['source'])
            else:
                product = science.assess(inputs['supplier'], inputs['instance'])
            if source_identity(product if self.role == 'supply' else inputs['supplier']) != config.source:
                raise ValueError('inquiry source/config identity substitution')
            outputs = context.output_ports
            if (len(outputs) != 1 or outputs[0].output_id != f'{context.task_id}.product'
                    or outputs[0].payload_schema != output_type.SCHEMA or outputs[0].profile is not ArtifactProfile.CANONICAL_JSON
                    or outputs[0].media_type != MEDIA):
                raise ValueError('inquiry worker exact output contract differs')
            payload = product.canonical_bytes()
            return RunnerResult((TaskOutputPayload(outputs[0].output_id, payload),), (ReceiptCheck('exact-exposed-inquiry-product', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def record_identity(record):
    key = next(getattr(record, name) for name in ('product_id', 'candidate_id', 'instance_id', 'input_id', 'config_id', 'assessment_id') if hasattr(record, name))
    return ObjectIdentity.from_record(key, record)


def source_identity(supplier):
    return ObjectIdentity.from_record(supplier.source.input_id, supplier.source)


def operation_declarations():
    """Own scientific and inquiry contracts and derive installed projections."""
    from .recursive_translation import (
        describe_contributions, inquiry_endpoint_validator, inquiry_evidence_projector,
        inquiry_outcome_projector, next_wave_builder,
    )

    return tuple(RecursiveOperationDeclaration(
        capability_key=f'{NAMESPACE}.{role}', capability_version='1.0.0',
        implementation_id=f'{NAMESPACE}.exact-exposed-{role}-v1', kind=CapabilityKind.ANALYSIS,
        config_record_type=InquiryOperationConfig, stage=stage,
        input_ports=tuple(RecursivePortContract(key, record.SCHEMA, MEDIA, MAX_BYTES) for key, record in inputs),
        outputs=(OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('exact-scientific-scope', 'independent-consumer-verdict', 'zero-native-contacts'),
        runner_factory=lambda phase=role: InquiryRunner(phase), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids, scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions if role=='supply' else None,
            next_wave_builder=next_wave_builder if role=='supply' else None, inquiry_outcome_projector=inquiry_outcome_projector,
            inquiry_evidence_projector=inquiry_evidence_projector, inquiry_endpoint_validator=inquiry_endpoint_validator))
        for role, inputs, output, stage in PHASES)
