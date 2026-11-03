# SPDX-License-Identifier: MPL-2.0
"""Exposed paired response phases using existing compiler and native custody.

Source preparation independently authenticates the original causal supply.
Forecast receives only the public paired design and common origin. Futures
recover completed children before sampling, then retain both complete views.
"""

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorStream
from empirical_lawhood.adapters.methods.matrix_factor_response.operation_bindings import _definition, _outputs, _run_native
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    MatrixParameterFactorAssessment, MatrixParameterFactorProduct, MatrixParameterFactorSource, MatrixParameterFactorSupply,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterHistorySource
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind
from empirical_lawhood.runtime.execution import WorkerInputKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster, NativeSubworkState
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from . import independent, paired_independent, paired_science, science
from .operation_bindings import consume
from .paired_records import (
    MatrixPairedNumericalStandard, MatrixParameterPairedAssessment, MatrixParameterPairedDesign,
    MatrixParameterPairedForecast, MatrixParameterPairedNative, MatrixParameterPairedSource, identity,
)
from .records import MatrixParameterResponseNativeEvent, MatrixParameterResponseOrigin, MatrixParameterResponseSource

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

NAMESPACE = 'matrix-parameter-paired-development'
BUDGET = ResourceBudget(1, None, 0, None, None, None)
ORIGINAL_INPUTS = (
    ('factor-arrays', None), ('factor-assessment', MatrixParameterFactorAssessment),
    ('factor-product', MatrixParameterFactorProduct), ('factor-source', MatrixParameterFactorSource),
    ('history-arrays', None), ('history-source', MatrixParameterHistorySource),
    ('history-supply', MatrixParameterFactorSupply), ('original-source', MatrixParameterResponseSource),
)
PHASES = (
    ('source', (*ORIGINAL_INPUTS, ('origin', MatrixParameterResponseOrigin), ('origin-arrays', None),
        ('source', MatrixParameterPairedSource)), MatrixParameterPairedSource, ScientificStage.PREPARE),
    ('forecast', (('design', MatrixParameterPairedDesign), ('model', MatrixFactorResponseModel),
        ('origin', MatrixParameterResponseOrigin), ('origin-arrays', None)), MatrixParameterPairedForecast, ScientificStage.FREEZE),
    ('futures', (('design', MatrixParameterPairedDesign), ('forecast', MatrixParameterPairedForecast), ('origin', MatrixParameterResponseOrigin),
        ('origin-arrays', None), ('original-source', MatrixParameterResponseSource),
        ('provenance', NumericalProducingProvenance), ('source', MatrixParameterPairedSource),
        ('streams', MatrixFactorStream)), MatrixParameterPairedNative, ScientificStage.ACQUIRE),
    ('assess', (*ORIGINAL_INPUTS, ('forecast', MatrixParameterPairedForecast), ('forecast-arrays', None),
        ('futures', MatrixParameterPairedNative), ('futures-arrays', None), ('origin', MatrixParameterResponseOrigin),
        ('origin-arrays', None), ('source', MatrixParameterPairedSource)), MatrixParameterPairedAssessment, ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class MatrixParameterPairedConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/operation-config'
    config_id: str
    operation: str
    source: MatrixParameterPairedSource

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (self.operation not in ('source', 'futures', 'assess') or type(self.source) is not MatrixParameterPairedSource
                or self.config_id != f'config.{NAMESPACE}.{self.source.root.root_id}.{self.operation}'):
            raise ValueError('paired response changes actual source/root/phase configuration')


@dataclass(frozen=True, slots=True)
class MatrixParameterPairedForecastConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-paired/forecast-config'
    config_id: str
    design: MatrixParameterPairedDesign
    root_id: str
    independent_group_id: str
    clock_id: str

    def __post_init__(self):
        for value in (self.config_id, self.root_id, self.independent_group_id, self.clock_id):
            validate_stable_id(value)
        origin = self.design.common_origin
        if (type(self.design) is not MatrixParameterPairedDesign
                or self.config_id != f'config.{NAMESPACE}.{self.root_id}.forecast'
                or (self.root_id, self.independent_group_id, self.clock_id) !=
                   (origin.root_id, origin.independent_group_id, origin.clock_id)):
            raise ValueError('paired forecast changes source-free common-origin root/group/clock')


def _unit(config):
    return (config.independent_group_id if type(config) is MatrixParameterPairedForecastConfig
            else config.source.root.independent_group_id,)


def _slots(config):
    return tuple(config.source.root.root_id + '.' + branch[1] for branch in paired_science.branch_census(config.source))


def source_operands(source):
    return (identity(source), source.original_source, source.original_allocation, identity(source.design),
        identity(source.design.common_origin), source.design.common_origin.source, source.provenance.identity)


def development_root(sources, *, study_id):
    sources = tuple(sorted(sources, key=lambda source: source.root.root_id))
    if not sources:
        raise ValueError('paired response requires the actual complete original root roster')
    first = sources[0]
    roster = sha256(b''.join(source.root.canonical_bytes() for source in sources)).hexdigest()
    groups = tuple(sorted({source.root.independent_group_id for source in sources}))
    if (len({source.root.root_id for source in sources}) != len(sources)
            or len(sources) != first.requested_roots or len(groups) != first.requested_independent_groups
            or roster != first.allocation_roster_sha256
            or any((source.original_allocation, source.allocation_roster_sha256, source.requested_roots,
                    source.requested_independent_groups) !=
                   (first.original_allocation, first.allocation_roster_sha256, first.requested_roots,
                    first.requested_independent_groups) for source in sources)):
        raise ValueError('paired response omits or substitutes the authenticated allocation root/group census')
    world = 'world.matrix-parameter-paired.exposed'
    question = 'How do same-origin functional responses and five zero-fit descriptions compare at both declared numerical clocks?'
    views = tuple(sorted({view.view_id for source in sources for view in
        (source.design.primary.view, source.design.fine_view)}))
    claims = tuple(ClaimSpec('claim.parameter-paired.' + group, world, 'population.matrix-parameter-paired.exposed',
        question, 'Complete original coordinate/root census; two numerical views, five descriptions, two panels, four actions, three signs and48 receivers.',
        group, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Conditional retained history; independent equation controls and paired functional discrepancy are distinct. No qualification, continuum enclosure or E3 transfer.',
        ('assumption.parameter-paired.exposed',), numerical_view_ids=views) for group in groups)
    operands = tuple(sorted({operand for source in sources for operand in source_operands(source)}, key=lambda value: value.object_id))
    return DevelopmentStudySpec(study_id, question, first.original_allocation, world,
        WorldKind.NUMERICAL_SIMULATOR, groups, views, claims, operands)


def _dependency(name, role):
    if name == 'source' and role != 'source':
        return 'source', 'product', 'HISTORY'
    if name in ('forecast', 'forecast-arrays', 'futures', 'futures-arrays'):
        producer = name.removesuffix('-arrays')
        return producer, 'arrays' if name.endswith('-arrays') else 'product', 'MODEL' if producer == 'forecast' else 'OUTCOME'
    return None


def _external_role(name):
    return 'MODEL' if name == 'model' else 'HISTORY' if name.startswith(('history-', 'factor-')) or name in ('origin', 'origin-arrays') else 'SOURCE'


def scientific_root_validator(config, context):
    configs = tuple(value.record for value in context.config_inputs)
    operations = tuple(value for value in configs if type(value) is MatrixParameterPairedConfig)
    forecasts = tuple(value for value in configs if type(value) is MatrixParameterPairedForecastConfig)
    sources = tuple(value.source for value in operations if value.operation == 'source')
    if (len(configs) != 4 * len(sources) or len(operations) != 3 * len(sources) or len(forecasts) != len(sources)
            or type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(sources, study_id=context.root.study_id)):
        raise ValueError('paired response changes exact system/world/scientific root/complete four phases')
    for source in sources:
        selected = tuple(value for value in operations if value.source.root.root_id == source.root.root_id)
        forecast = tuple(value for value in forecasts if value.root_id == source.root.root_id)
        if (len(selected) != 3 or {value.operation for value in selected} != {'source', 'futures', 'assess'}
                or any(value.source != source for value in selected) or len(forecast) != 1
                or (forecast[0].design, forecast[0].independent_group_id, forecast[0].clock_id) !=
                   (source.design, source.root.independent_group_id, source.root.clock_id)):
            raise ValueError('paired response phases substitute source/design/coordinate/group/clock')
    role = 'forecast' if type(config) is MatrixParameterPairedForecastConfig else config.operation
    root_id = config.root_id if role == 'forecast' else config.source.root.root_id
    phase = next(value for value in PHASES if value[0] == role)
    groups = tuple(sorted({source.root.independent_group_id for source in sources}))
    if (context.node_id != f'{NAMESPACE}.{root_id}.{role}' or context.stage is not phase[3]
            or context.unit_ids != _unit(config) or context.selected_unit_ids != groups
            or context.complete_unit_census != (role == 'futures')
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('paired response changes actual units/views/access or complete native scope')
    incoming = tuple(link for link in context.links if link.consumer_node_id == context.node_id)
    names = {name for name, _ in phase[1] if name != 'streams'}
    if {link.consumer_input_id for link in incoming if not link.consumer_input_id.startswith('streams.')} != names:
        raise ValueError('paired response drops actual phase input operands')
    for link in incoming:
        dependency = _dependency(link.consumer_input_id, role)
        if dependency is not None:
            producer, output, scientific_role = dependency
            if (link.producer_node_id != f'{NAMESPACE}.{root_id}.{producer}' or link.producer_output_id != output
                    or link.external_input_id is not None or link.scientific_role != scientific_role):
                raise ValueError('paired response substitutes genuine source/commitment/native dependency roles')
        elif (link.external_input_id is None or link.producer_node_id is not None
                or link.scientific_role != _external_role(link.consumer_input_id)):
            raise ValueError('paired response changes exact original/public external operand roles')
    expected_streams = tuple('streams.' + stream.purpose_id for stream in config.source.root.streams) if role == 'futures' else ()
    if tuple(sorted(link.consumer_input_id for link in incoming if link.consumer_input_id.startswith('streams.'))) != expected_streams:
        raise ValueError('paired response changes selected future-only two-stream lowering')


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def operation_declarations():
    """Derive cold and executable projections from each original operation."""
    return tuple(RecursiveOperationDeclaration(
        capability_key=f'{NAMESPACE}.{role}', capability_version='1.0.0',
        implementation_id=NAMESPACE+'.'+role+'.v1',
        kind=CapabilityKind.SIMULATOR if role == 'futures' else CapabilityKind.FALSIFIER if role == 'assess' else CapabilityKind.ANALYSIS,
        config_record_type=MatrixParameterPairedForecastConfig if role == 'forecast' else MatrixParameterPairedConfig, stage=stage,
        input_ports=tuple(RecursivePortContract(name, kind.SCHEMA if kind else MATRIX_ARRAY_SCHEMA,
            'application/json' if kind else 'application/x-npz', None if kind else MAXIMUM_MATRIX_ARRAY_BYTES,
            minimum_count=2 if name == 'streams' else 1, maximum_count=None if name == 'streams' else 1)
            for name, kind in sorted(inputs)),
        outputs=tuple(sorted((OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),
            *((OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'),)
                if role in ('forecast', 'futures') else ())), key=lambda row: row.output_id)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('complete-paired-physical-clock-census', 'future-only-native-recovery', 'independent-original-copyproof'),
        runner_factory=lambda phase=role: MatrixParameterPairedNativeRunner(phase) if phase == 'futures' else MatrixParameterPairedRunner(phase),
        record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=_unit,
            native_effect_slot_ids=_slots if role == 'futures' else None, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE if role == 'forecast' else BarrierKind.NONE,
            native_effect=role == 'futures', complete_unit_census=role == 'futures',
            native_work_preparer=prepare_native_work if role == 'futures' else None),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=identity),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,), storage_codecs=MATRIX_STORAGE_CODECS)
        for role, inputs, output, stage in PHASES)


def output_codecs():
    return {kind.SCHEMA: kind for kind in (MatrixParameterPairedConfig, MatrixParameterPairedForecastConfig,
        MatrixParameterPairedSource, MatrixParameterPairedDesign, MatrixPairedNumericalStandard, MatrixParameterPairedForecast,
        MatrixParameterPairedNative, MatrixParameterPairedAssessment, MatrixParameterResponseSource, MatrixParameterResponseOrigin,
        MatrixFactorResponseModel, MatrixFactorStream, NumericalProducingProvenance, MatrixParameterHistorySource,
        MatrixParameterFactorSource, MatrixParameterFactorProduct, MatrixParameterFactorAssessment, MatrixParameterFactorSupply)}


def operands(source, original, parameter, supply, factor_source, product, assessment, model):
    source.validate_original(original, source.design.common_origin)
    original.validate_operands(parameter, supply, factor_source, product, assessment)
    if identity(model) != source.design.primary.model:
        raise ValueError('paired response changes its actual frozen zero-fit model')
    return {'source': source, 'original-source': original, 'history-source': parameter, 'history-supply': supply,
        'factor-source': factor_source, 'factor-product': product, 'factor-assessment': assessment,
        'provenance': source.provenance, 'model': model, 'origin': source.design.common_origin, 'design': source.design}


def development_draft(cases, *, draft_id):
    cases = tuple(cases)
    selected = tuple(operands(*case) for case in cases)
    root = development_root(tuple(case[0] for case in cases), study_id='study.' + draft_id)
    policy = AuthorityPolicy('policy.' + draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION,)), frozenset((SourceAccessClass.NONE,)),
        ('gate.local-nonactuating-development',), frozenset(), BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.' + draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.' + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(claim.claim_id for claim in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('right.' + draft_id, AuthorityAction.REPOSITORY_IMPLEMENTATION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    registrations = {value.selection.capability_key: value for value in operation_registrations()}
    external, operations, links = {}, [], []
    for case, records in zip(cases, selected, strict=True):
        source, original = case[:2]
        for role, inputs, _, _ in PHASES:
            node_id = f'{NAMESPACE}.{source.root.root_id}.{role}'
            config = MatrixParameterPairedForecastConfig('config.' + node_id, source.design, source.root.root_id,
                source.root.independent_group_id, source.root.clock_id) if role == 'forecast' else MatrixParameterPairedConfig('config.' + node_id, role, source)
            operations.append(RecursiveOperationSpec.from_config(node_id=node_id, selection=registrations[NAMESPACE + '.' + role].selection,
                config_id=config.config_id, config=config, obligation_ids=('obligation.' + node_id + '.complete-scope',), resource_budget=BUDGET))
            for name, kind in inputs:
                dependency = _dependency(name, role)
                if dependency is not None:
                    producer, output, scientific_role = dependency
                    links.append(RecursiveInputLink('edge.' + node_id + '.' + name, node_id, name,
                        producer_node_id=f'{NAMESPACE}.{source.root.root_id}.{producer}', producer_output_id=output,
                        scientific_role=scientific_role))
                    continue
                values = tuple(('streams.' + stream.purpose_id, stream, source.root.stream_identity(stream).object_id)
                    for stream in source.root.streams) if name == 'streams' else ((name,
                    original.history_arrays if name == 'history-arrays' else original.factor_arrays if name == 'factor-arrays'
                    else source.design.common_origin.arrays.array_artifact if name == 'origin-arrays' else records[name], None),)
                for port_name, value, artifact_id in values:
                    external_id = 'external.' + source.root.root_id + '.' + port_name
                    raw = kind is None
                    scientific_role = _external_role(name)
                    external[external_id] = RecursiveExternalInput(external_id, value.artifact_id if raw else artifact_id or
                        (value.identity.object_id if type(value) is NumericalProducingProvenance else
                         value.evidence_id if hasattr(value, 'evidence_id') else identity(value).object_id),
                        value.payload_schema if raw else value.SCHEMA, value.media_type if raw else 'application/json',
                        value.size_bytes if raw else len(value.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE,
                        VisibilityCeiling.DEVELOPMENT_ONLY, value.sha256 if raw else value.fingerprint(), scientific_role)
                    links.append(RecursiveInputLink('edge.' + node_id + '.' + port_name, node_id, port_name,
                        external_input_id=external_id, scientific_role=scientific_role))
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), tuple(sorted(operations, key=lambda value: value.node_id)),
        tuple(sorted(external.values(), key=lambda value: value.input_id)), tuple(sorted(links, key=lambda value: value.edge_id)),
        tuple(sorted(value.node_id for value in operations)), development_study=root)


def _decode(context, role):
    phase = next(value for value in PHASES if value[0] == role)
    config_kind = MatrixParameterPairedForecastConfig if role == 'forecast' else MatrixParameterPairedConfig
    expected = {kind.SCHEMA: kind for _, kind in phase[1] if kind is not None and kind is not MatrixFactorStream} | {config_kind.SCHEMA: config_kind}
    records, arrays, streams = {}, {}, []
    dependency_schemas = {MatrixParameterPairedForecast.SCHEMA, MatrixParameterPairedNative.SCHEMA}
    if role in ('futures', 'assess'):
        dependency_schemas.add(MatrixParameterPairedSource.SCHEMA)
    for port in context.input_ports:
        if port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY:
            raise ValueError('paired response changes actual input visibility')
        if port.payload_schema == MATRIX_ARRAY_SCHEMA and port.media_type == 'application/x-npz' and port.artifact_id not in arrays:
            arrays[port.artifact_id] = port
        elif role == 'futures' and port.payload_schema == MatrixFactorStream.SCHEMA:
            streams.append(decode_canonical_bytes(port.read(), MatrixFactorStream, maximum_bytes=None))
        elif port.payload_schema in expected and port.payload_schema not in records and port.media_type == 'application/json':
            records[port.payload_schema] = decode_canonical_bytes(port.read(), expected[port.payload_schema], maximum_bytes=None)
            if port.payload_schema in dependency_schemas and (port.kind is not WorkerInputKind.DEPENDENCY
                    or len(tuple(receipt for receipt in context.dependency_receipts
                        if port.materialization_id in receipt.output_materialization_ids)) != 1):
                raise ValueError('paired response requires genuine ordinary source/forecast/native dependency receipts')
        else:
            raise ValueError('paired response receives duplicate/undeclared/foreign phase operand')
    if set(records) != set(expected) or len(arrays) != sum(kind is None for _, kind in phase[1]):
        raise ValueError('paired response loses actual typed/raw input census')
    config = records[config_kind.SCHEMA]
    source = None if role == 'forecast' else config.source
    root_id = config.root_id if source is None else source.root.root_id
    selected = next(value for value in operation_manifests() if value.capability_key.endswith('.' + role))
    if (context.task_id != f'{NAMESPACE}.{root_id}.{role}' or config.fingerprint() != context.config.content_sha256
            or context.permissions != selected.permissions or context.resource_budget != BUDGET
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or source is not None and records[MatrixParameterPairedSource.SCHEMA] != source
            or tuple(sorted(streams, key=lambda value: value.purpose_id)) != (() if role != 'futures' else source.root.streams)):
        raise ValueError('paired response provider substitutes exact config/source/stream/resource scope')
    design = config.design if source is None else source.design
    origin = records[MatrixParameterResponseOrigin.SCHEMA]
    if origin != design.common_origin:
        raise ValueError('paired response substitutes actual public common origin')
    if role in ('forecast', 'futures') and records[MatrixParameterPairedDesign.SCHEMA] != design:
        raise ValueError('paired phase substitutes its actual separately authenticated public design')
    if source is not None:
        original = records[MatrixParameterResponseSource.SCHEMA]
        source.validate_original(original, origin)
        if role in ('source', 'assess'):
            original.validate_operands(records[MatrixParameterHistorySource.SCHEMA], records[MatrixParameterFactorSupply.SCHEMA],
                records[MatrixParameterFactorSource.SCHEMA], records[MatrixParameterFactorProduct.SCHEMA], records[MatrixParameterFactorAssessment.SCHEMA])
        if role == 'futures' and records[NumericalProducingProvenance.SCHEMA] != source.provenance:
            raise ValueError('paired futures substitutes producing source/code/lock provenance')
    return config, records, arrays


def _original_inputs(records, ports):
    supply, product = records[MatrixParameterFactorSupply.SCHEMA], records[MatrixParameterFactorProduct.SCHEMA]
    return (records[MatrixParameterResponseSource.SCHEMA], records[MatrixParameterHistorySource.SCHEMA], supply,
        records[MatrixParameterFactorSource.SCHEMA], product, records[MatrixParameterFactorAssessment.SCHEMA],
        consume(ports, supply.product.arrays), consume(ports, product.arrays))


def validate_native_transport(source):
    """Admit unchanged closed NPZ geometry before RNG, BEGIN or new contact."""
    validate_parameter_ou_domain(source.design.primary.coordinate)
    n = source.design.primary.horizon_steps[-1]
    # Forty-eight branches x five full members and two retained bridges.
    total = sum(24 * ((3 * multiplier * n + 2) * 2 * 3 * 4 * 4 * 16
                     + (multiplier * n + 1) * (2 * 8 + 8)) for multiplier in (1, 2))
    total += 2 * n * 2 * 3 * 4 * 4 * 16
    if total > MAXIMUM_MATRIX_ARRAY_BYTES:
        raise ValueError('complete paired242-member response requires an explicit chunked successor')
    return total


class MatrixParameterPairedRunner:
    """PURE preparation, source-free forecast and independent assessment."""

    def __init__(self, role):
        self.role = role
        self.manifest = next(value for value in operation_manifests() if value.capability_key.endswith('.' + role))

    def execute(self, context):
        try:
            config, records, ports = _decode(context, self.role)
            origin = records[MatrixParameterResponseOrigin.SCHEMA]
            past = consume(ports, origin.arrays)
            if self.role == 'source':
                source = config.source
                original, *operands = _original_inputs(records, ports)
                independent.validate_original_origin(original, origin, past, *operands)
                raw, result = None, source
            elif self.role == 'forecast':
                output = next(port for port in context.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
                raw, result = paired_science.forecast(config.design, past, records[MatrixFactorResponseModel.SCHEMA],
                    artifact_id=output.logical_artifact_id)
            elif self.role == 'assess':
                forecast, native = records[MatrixParameterPairedForecast.SCHEMA], records[MatrixParameterPairedNative.SCHEMA]
                raw, result = None, paired_independent.assess(config.source, forecast, native, past,
                    consume(ports, forecast.arrays), consume(ports, native.arrays), original_inputs=_original_inputs(records, ports))
            else:
                raise ValueError('paired futures requires genuine guarded native context')
            return _outputs(context, result, raw)
        finally:
            for port in context.input_ports:
                port.close()


def _initial_native_work(context, config, records, ports, expected_parent):
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    source = config.source
    origin = records[MatrixParameterResponseOrigin.SCHEMA]
    forecast = records[MatrixParameterPairedForecast.SCHEMA]
    if (forecast.design != identity(source.design) or forecast.origin != identity(origin)
            or forecast.model != source.design.primary.model):
        raise ValueError('paired futures lacks actual prior source-free forecast commitment')
    past = consume(ports, origin.arrays)
    science.validate_origin_arrays(origin, past)
    roster = paired_science.branch_census(source)
    definitions = tuple(_definition(context, config, source, branch[1],
        (identity(source), identity(source.design), identity(origin), identity(forecast), identity(config)),
        branch[2], expected_parent) for branch in roster)
    frozen = NativeSubworkRoster('selected.native-subwork', expected_parent, tuple(row.identity for row in definitions))
    work = PreparedNativeWork(expected_parent, _unit(config), _slots(config), definitions, (frozen,))
    return work, past, roster


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not MatrixParameterPairedNativeRunner or runner.role != 'futures':
        raise ValueError('parameter response preparation requires its installed original native phase')
    config, records, ports = _decode(context, 'futures')
    return _initial_native_work(context, config, records, ports, expected_parent)[0]


class MatrixParameterPairedNativeRunner(MatrixParameterPairedRunner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, records, ports = _decode(context, 'futures')
            source = config.source
            forecast = records[MatrixParameterPairedForecast.SCHEMA]
            work, past, roster = _initial_native_work(context, config, records, ports, native_subwork.parent_contact)
            definitions = work.definitions
            states = tuple(native_subwork.inspect(definition).state for definition in definitions)
            if any(state not in (NativeSubworkState.NOT_ENTERED, NativeSubworkState.COMPLETED) for state in states):
                raise ValueError('unknown or failed paired child cannot be replayed')
            if any(state is NativeSubworkState.NOT_ENTERED for state in states):
                validate_native_transport(source)
                native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            branches, events = {}, []
            primary_n = source.design.primary.horizon_steps[-1]
            for branch, definition in zip(roster, definitions, strict=True):
                view, branch_id, stream, _, _ = branch
                n = source.design.horizon_steps(view)[-1]
                members = {'positions': ('<c16', (n + 1, 2, 3, 4, 4)), 'momenta': ('<c16', (n + 1, 2, 3, 4, 4)),
                    'noise': ('<c16', (n, 2, 3, 4, 4)), 'alpha_tilde': ('<f8', (n + 1, 2)), 'ticks': ('<i8', (n + 1,)),
                    'bridge': ('<c16', (primary_n, 2, 3, 4, 4))}
                def producer(branch=branch, stream=stream):
                    # The generic guard has recorded BEGIN and contact before
                    # this one selected stream is opened. Recovery never calls it.
                    panel = paired_science.noise_panel(source, stream)
                    return paired_science.native_branch(source, past, branch, panel)
                branches[branch_id] = _run_native(native_subwork, definition, producer, members)
                retained = native_subwork.inspect(definition)
                if retained.state is not NativeSubworkState.COMPLETED:
                    raise ValueError('paired child return remains uncertain; no automatic replay')
                events.append(MatrixParameterResponseNativeEvent(branch_id, definition, retained.begin,
                    retained.contact, retained.completion, retained.receipt))
            panels = {}
            for stream in source.root.streams:
                first = source.design.primary.actions[0].action_id
                panels[stream.panel_id] = {view: branches[f'{view.lower()}.{stream.panel_id}.{first}.hold']['noise']
                    for view in ('PRIMARY', 'FINE')}
                panels[stream.panel_id]['BRIDGE'] = branches[f'primary.{stream.panel_id}.{first}.hold']['bridge']
            output = next(port for port in context.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, result = paired_science.responses(source, forecast, branches,
                tuple(sorted(events, key=lambda event: event.branch_id)), panels, artifact_id=output.logical_artifact_id)
            return _outputs(context, result, raw)
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    factories = []
    for declaration in operation_declarations():
        selected = declaration.manifest()
        role = selected.capability_key.rsplit('.', 1)[-1]
        _, parts = bundle(role, ExtensionContributionKind.METHOD, selected, (), None,
            namespace=NAMESPACE, maximum_config_bytes=None)
        factories.append(declaration.provider_factory(components=tuple(sorted(parts, key=lambda row: row.registration_id))))
    return tuple(factories)
