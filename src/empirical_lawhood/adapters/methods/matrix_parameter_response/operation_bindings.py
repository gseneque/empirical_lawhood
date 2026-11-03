# SPDX-License-Identifier: MPL-2.0
"""Four parameter-response phases using existing compiler/provider/custody."""

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorStream
from empirical_lawhood.adapters.methods.matrix_factor_response.operation_bindings import _definition, _outputs, _run_native
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    MatrixParameterFactorAssessment, MatrixParameterFactorProduct, MatrixParameterFactorSource, MatrixParameterFactorSupply,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterHistorySource
from empirical_lawhood.adapters.simulators.six_matrix_response.simulation import hermitian_noise
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
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

from . import independent, science
from .records import (
    MatrixParameterNativeResponses, MatrixParameterResponseAssessment, MatrixParameterResponseDesign,
    MatrixParameterResponseForecast, MatrixParameterResponseNativeEvent, MatrixParameterResponseOrigin,
    MatrixParameterResponseSource, identity,
)

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

NAMESPACE = 'matrix-parameter-response-development'
BUDGET = ResourceBudget(1, None, 0, None, None, None)
PHASES = (
    ('origin', (('factor-arrays', None), ('factor-assessment', MatrixParameterFactorAssessment),
        ('factor-product', MatrixParameterFactorProduct), ('factor-source', MatrixParameterFactorSource),
        ('history-arrays', None), ('history-source', MatrixParameterHistorySource),
        ('history-supply', MatrixParameterFactorSupply), ('instrument-arrays', None), ('source', MatrixParameterResponseSource)),
        MatrixParameterResponseOrigin, ScientificStage.PREPARE),
    ('forecast', (('model', MatrixFactorResponseModel), ('origin', MatrixParameterResponseOrigin), ('origin-arrays', None)),
        MatrixParameterResponseForecast, ScientificStage.FREEZE),
    ('futures', (('forecast', MatrixParameterResponseForecast), ('origin', MatrixParameterResponseOrigin),
        ('origin-arrays', None), ('provenance', NumericalProducingProvenance), ('source', MatrixParameterResponseSource),
        ('streams', MatrixFactorStream)), MatrixParameterNativeResponses, ScientificStage.ACQUIRE),
    ('assess', (('forecast', MatrixParameterResponseForecast), ('forecast-arrays', None),
        ('futures', MatrixParameterNativeResponses), ('futures-arrays', None), ('origin', MatrixParameterResponseOrigin),
        ('origin-arrays', None), ('source', MatrixParameterResponseSource), ('history-source', MatrixParameterHistorySource),
        ('history-supply', MatrixParameterFactorSupply), ('history-arrays', None), ('factor-source', MatrixParameterFactorSource),
        ('factor-product', MatrixParameterFactorProduct), ('factor-assessment', MatrixParameterFactorAssessment), ('factor-arrays', None)),
        MatrixParameterResponseAssessment, ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/operation-config'
    config_id: str
    operation: str
    source: MatrixParameterResponseSource

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (self.operation not in ('origin', 'futures', 'assess') or type(self.source) is not MatrixParameterResponseSource
                or self.config_id != f'config.{NAMESPACE}.{self.source.root.root_id}.{self.operation}'):
            raise ValueError('parameter response changes exact selected source/root/phase')


@dataclass(frozen=True, slots=True)
class MatrixParameterResponseForecastConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-response/forecast-config'
    config_id: str
    design: MatrixParameterResponseDesign
    root_id: str
    independent_group_id: str
    clock_id: str

    def __post_init__(self):
        for v in (self.config_id, self.root_id, self.independent_group_id, self.clock_id):
            validate_stable_id(v)
        if self.config_id != f'config.{NAMESPACE}.{self.root_id}.forecast' or self.clock_id != self.design.coordinate.clock_id:
            raise ValueError('parameter forecast changes its source-free root/clock configuration')


def _unit(config):
    return (config.independent_group_id if type(config) is MatrixParameterResponseForecastConfig
            else config.source.root.independent_group_id,)


def _slots(config):
    return tuple(config.source.root.root_id + '.' + b[0] for b in science.branch_census(config.source))


def source_operands(source):
    c = source.causal
    return (identity(source), identity(source.allocation), identity(c), identity(source.design), c.history_source,
            c.history_product, c.history_assessment, c.factor_source, c.factor_product, c.factor_assessment,
            source.history_supply, source.provenance.identity)


def development_root(sources, *, study_id):
    sources = tuple(sorted(sources, key=lambda s: s.root.root_id))
    if (not sources or len({identity(s.allocation) for s in sources}) != 1
            or tuple(s.root for s in sources) != sources[0].allocation.roots):
        raise ValueError('parameter response root omits complete selected coordinate/root/group census')
    world = 'world.matrix-parameter-response.exposed'
    question = 'How adequate are five origin-only descriptions under the actual selected parameter response assay?'
    units = tuple(sorted({s.root.independent_group_id for s in sources}))
    views = tuple(sorted({v for s in sources for v in (s.design.coordinate.primary_view.view_id,
                           s.design.coordinate.fine_view.view_id, s.design.view.view_id)}))
    claims = tuple(ClaimSpec('claim.parameter-response.' + unit, world, 'population.matrix-parameter-response.exposed',
        question, 'Complete declared coordinate/root, five descriptions, two panels, four actions, three signs and48 receivers.',
        unit, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Conditional exposed history and finite-dt equation checks; no fresh/IID, continuum bound, useful admission or qualification.',
        ('assumption.parameter-response.exposed',), numerical_view_ids=views) for unit in units)
    operands = tuple(sorted({o for s in sources for o in source_operands(s)}, key=lambda x: x.object_id))
    return DevelopmentStudySpec(study_id, question, identity(sources[0].allocation), world,
        WorldKind.NUMERICAL_SIMULATOR, units, views, claims, operands)


def scientific_root_validator(config, context):
    configs = tuple(i.record for i in context.config_inputs)
    operations = tuple(c for c in configs if type(c) is MatrixParameterResponseConfig)
    forecasts = tuple(c for c in configs if type(c) is MatrixParameterResponseForecastConfig)
    sources = tuple(c.source for c in operations if c.operation == 'origin')
    if (len(configs) != 4 * len(sources) or len(operations) != 3 * len(sources) or len(forecasts) != len(sources)
            or type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(sources, study_id=context.root.study_id)):
        raise ValueError('parameter response substitutes exact scientific root/world/system/complete phases')
    for s in sources:
        selected = tuple(c for c in operations if c.source.root.root_id == s.root.root_id)
        f = tuple(c for c in forecasts if c.root_id == s.root.root_id)
        if (len(selected) != 3 or {c.operation for c in selected} != {'origin', 'futures', 'assess'}
                or any(c.source != s for c in selected) or len(f) != 1
                or (f[0].design, f[0].independent_group_id, f[0].clock_id) != (s.design, s.root.independent_group_id, s.root.clock_id)):
            raise ValueError('parameter response phases substitute source/coordinate/group/clock')
    role = 'forecast' if type(config) is MatrixParameterResponseForecastConfig else config.operation
    root_id = config.root_id if role == 'forecast' else config.source.root.root_id
    phase = next(p for p in PHASES if p[0] == role)
    units = tuple(sorted({s.root.independent_group_id for s in sources}))
    if (context.node_id != f'{NAMESPACE}.{root_id}.{role}' or context.stage is not phase[3]
            or context.unit_ids != _unit(config) or context.selected_unit_ids != units
            or context.complete_unit_census != (role == 'futures')
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('parameter response changes unit/view/access or Native slot scope')
    incoming = tuple(l for l in context.links if l.consumer_node_id == context.node_id)
    names = {n for n, _ in phase[1] if n != 'streams'}
    if {l.consumer_input_id for l in incoming if not l.consumer_input_id.startswith('streams.')} != names:
        raise ValueError('parameter response drops a complete actual phase input')
    for l in incoming:
        if l.consumer_input_id in ('origin', 'origin-arrays', 'forecast', 'forecast-arrays', 'futures', 'futures-arrays'):
            producer = l.consumer_input_id.removesuffix('-arrays')
            if (l.producer_node_id != f'{NAMESPACE}.{root_id}.{producer}'
                    or l.producer_output_id != ('arrays' if l.consumer_input_id.endswith('-arrays') else 'product')
                    or l.external_input_id is not None
                    or l.scientific_role != ('MODEL' if producer == 'forecast' else 'OUTCOME' if producer == 'futures' else 'HISTORY')):
                raise ValueError('parameter response changes genuine committed dependency roles')
        elif l.external_input_id is None or l.scientific_role not in ('SOURCE', 'MODEL', 'HISTORY'):
            raise ValueError('parameter response substitutes original/public scientific operand')
    expected_streams = tuple('streams.' + s.purpose_id for s in config.source.root.streams) if role == 'futures' else ()
    if tuple(sorted(l.consumer_input_id for l in incoming if l.consumer_input_id.startswith('streams.'))) != expected_streams:
        raise ValueError('parameter response changes the future-only two-stream lowering')


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
        config_record_type=MatrixParameterResponseForecastConfig if role == 'forecast' else MatrixParameterResponseConfig, stage=stage,
        input_ports=tuple(RecursivePortContract(name, kind.SCHEMA if kind else MATRIX_ARRAY_SCHEMA,
            'application/json' if kind else 'application/x-npz', None if kind else MAXIMUM_MATRIX_ARRAY_BYTES,
            minimum_count=2 if name == 'streams' else 1, maximum_count=None if name == 'streams' else 1)
            for name, kind in sorted(inputs)),
        outputs=tuple(sorted((OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),
            *((OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'),)
                if role != 'assess' else ())), key=lambda row: row.output_id)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('complete-parameter-causal-clock-and-custody', 'full-mode-and-instrument-witness-reproof', 'future-only-native-recovery'),
        runner_factory=lambda phase=role: MatrixParameterResponseNativeRunner(phase) if phase == 'futures' else MatrixParameterResponseRunner(phase),
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
    return {t.SCHEMA: t for t in (MatrixParameterResponseConfig, MatrixParameterResponseForecastConfig,
        MatrixParameterResponseSource, MatrixParameterResponseOrigin, MatrixParameterResponseForecast,
        MatrixParameterNativeResponses, MatrixParameterResponseAssessment, MatrixFactorResponseModel, MatrixFactorStream,
        NumericalProducingProvenance, MatrixParameterHistorySource, MatrixParameterFactorSource, MatrixParameterFactorProduct,
        MatrixParameterFactorAssessment, MatrixParameterFactorSupply)}


def operands(source, parameter, supply, factor_source, product, assessment, model):
    source.validate_operands(parameter, supply, factor_source, product, assessment)
    if identity(model) != source.design.model:
        raise ValueError('parameter response substitutes selected zero-fit model')
    return {'source': source, 'history-source': parameter, 'history-supply': supply,
            'factor-source': factor_source, 'factor-product': product, 'factor-assessment': assessment,
            'provenance': source.provenance, 'model': model}


def development_draft(cases, *, draft_id):
    cases = tuple(cases)
    original = tuple(operands(*case) for case in cases)
    root = development_root(tuple(case[0] for case in cases), study_id='study.' + draft_id)
    policy = AuthorityPolicy('policy.' + draft_id, 'owner.local-researcher', 'operator.local-development', (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION,)), frozenset((SourceAccessClass.NONE,)),
        ('gate.local-nonactuating-development',), frozenset(), BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.' + draft_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.' + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(c.claim_id for c in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight('right.' + draft_id, AuthorityAction.REPOSITORY_IMPLEMENTATION, 'owner.local-researcher', policy.policy_id, False),),
        (node,), (node.node_id,), (node.node_id,), (), LifecycleStatus.ACTIVE)
    registrations = {r.selection.capability_key: r for r in operation_registrations()}
    external, operations, links = {}, [], []
    for case, records in zip(cases, original, strict=True):
        s = case[0]
        for role, inputs, _, _ in PHASES:
            nid = f'{NAMESPACE}.{s.root.root_id}.{role}'
            cfg = MatrixParameterResponseForecastConfig('config.' + nid, s.design, s.root.root_id, s.root.independent_group_id,
                s.root.clock_id) if role == 'forecast' else MatrixParameterResponseConfig('config.' + nid, role, s)
            operations.append(RecursiveOperationSpec.from_config(node_id=nid, selection=registrations[NAMESPACE + '.' + role].selection,
                config_id=cfg.config_id, config=cfg, obligation_ids=('obligation.' + nid + '.complete-scope',), resource_budget=BUDGET))
            for name, kind in inputs:
                if name in ('origin', 'origin-arrays', 'forecast', 'forecast-arrays', 'futures', 'futures-arrays'):
                    producer = name.removesuffix('-arrays')
                    links.append(RecursiveInputLink('edge.' + nid + '.' + name, nid, name,
                        producer_node_id=f'{NAMESPACE}.{s.root.root_id}.{producer}',
                        producer_output_id='arrays' if name.endswith('-arrays') else 'product',
                        scientific_role='MODEL' if producer == 'forecast' else 'OUTCOME' if producer == 'futures' else 'HISTORY'))
                    continue
                values = tuple(('streams.' + stream.purpose_id, stream, s.root.stream_identity(stream).object_id)
                    for stream in s.root.streams) if name == 'streams' else ((name,
                    s.history_arrays if name == 'history-arrays' else s.factor_arrays if name == 'factor-arrays'
                    else s.instrument_arrays.array_artifact if name == 'instrument-arrays' else records[name], None),)
                for selected, value, aid in values:
                    eid = 'external.' + s.root.root_id + '.' + selected
                    raw = kind is None
                    scientific_role = 'MODEL' if name == 'model' else 'HISTORY' if name.startswith(('history-', 'factor-')) else 'SOURCE'
                    external[eid] = RecursiveExternalInput(eid, value.artifact_id if raw else aid or
                        (value.identity.object_id if type(value) is NumericalProducingProvenance else
                         value.source_id if hasattr(value, 'source_id') else value.evidence_id if hasattr(value, 'evidence_id')
                         else value.product_id if hasattr(value, 'product_id') else value.assessment_id if hasattr(value, 'assessment_id')
                         else identity(value).object_id), value.payload_schema if raw else value.SCHEMA,
                        value.media_type if raw else 'application/json', value.size_bytes if raw else len(value.canonical_bytes()),
                        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
                        value.sha256 if raw else value.fingerprint(), scientific_role)
                    links.append(RecursiveInputLink('edge.' + nid + '.' + selected, nid, selected,
                        external_input_id=eid, scientific_role=scientific_role))
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), tuple(sorted(operations, key=lambda x: x.node_id)),
        tuple(sorted(external.values(), key=lambda x: x.input_id)), tuple(sorted(links, key=lambda x: x.edge_id)),
        tuple(sorted(o.node_id for o in operations)), development_study=root)


def _decode(context, role):
    phase = next(p for p in PHASES if p[0] == role)
    kind = MatrixParameterResponseForecastConfig if role == 'forecast' else MatrixParameterResponseConfig
    expected = {t.SCHEMA: t for _, t in phase[1] if t is not None and t is not MatrixFactorStream} | {kind.SCHEMA: kind}
    records, arrays, streams = {}, {}, []
    for port in context.input_ports:
        if port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY:
            raise ValueError('parameter response changes actual input visibility')
        if port.payload_schema == MATRIX_ARRAY_SCHEMA and port.media_type == 'application/x-npz' and port.artifact_id not in arrays:
            arrays[port.artifact_id] = port
        elif role == 'futures' and port.payload_schema == MatrixFactorStream.SCHEMA:
            streams.append(decode_canonical_bytes(port.read(), MatrixFactorStream, maximum_bytes=None))
        elif port.payload_schema in expected and port.payload_schema not in records and port.media_type == 'application/json':
            records[port.payload_schema] = decode_canonical_bytes(port.read(), expected[port.payload_schema], maximum_bytes=None)
            if port.payload_schema in (MatrixParameterResponseOrigin.SCHEMA, MatrixParameterResponseForecast.SCHEMA,
                                       MatrixParameterNativeResponses.SCHEMA):
                if port.kind is not WorkerInputKind.DEPENDENCY or len(tuple(r for r in context.dependency_receipts
                        if port.materialization_id in r.output_materialization_ids)) != 1:
                    raise ValueError('parameter response requires genuine ordinary product dependency receipt')
        else:
            raise ValueError('parameter response receives duplicate/undeclared/foreign input')
    if set(records) != set(expected) or len(arrays) != sum(t is None for _, t in phase[1]):
        raise ValueError('parameter response loses full typed/raw phase input census')
    cfg = records[kind.SCHEMA]
    s = None if role == 'forecast' else cfg.source
    root_id = cfg.root_id if s is None else s.root.root_id
    m = next(m for m in operation_manifests() if m.capability_key.endswith('.' + role))
    if (context.task_id != f'{NAMESPACE}.{root_id}.{role}' or cfg.fingerprint() != context.config.content_sha256
            or context.permissions != m.permissions or context.resource_budget != BUDGET
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or s is not None and records[MatrixParameterResponseSource.SCHEMA] != s
            or tuple(sorted(streams, key=lambda x: x.purpose_id)) != (() if role != 'futures' else s.root.streams)):
        raise ValueError('parameter response provider substitutes config/source/stream/resources')
    if role in ('origin', 'assess'):
        s.validate_operands(records[MatrixParameterHistorySource.SCHEMA], records[MatrixParameterFactorSupply.SCHEMA],
            records[MatrixParameterFactorSource.SCHEMA], records[MatrixParameterFactorProduct.SCHEMA],
            records[MatrixParameterFactorAssessment.SCHEMA])
    if role == 'futures' and records[NumericalProducingProvenance.SCHEMA] != s.provenance:
        raise ValueError('parameter futures changes actual producing source/lock')
    if MatrixParameterResponseOrigin.SCHEMA in records:
        o = records[MatrixParameterResponseOrigin.SCHEMA]
        design, group, clock = (cfg.design, cfg.independent_group_id, cfg.clock_id) if s is None else (s.design, s.root.independent_group_id, s.root.clock_id)
        if (o.design, o.root_id, o.independent_group_id, o.clock_id) != (design, root_id, group, clock):
            raise ValueError('parameter response substitutes origin/coordinate/group/clock')
    return cfg, records, arrays


def consume(ports, saved):
    artifact = saved.array_artifact if hasattr(saved, 'array_artifact') else saved
    port = ports.get(artifact.artifact_id)
    if port is None or (port.payload_schema, port.media_type, port.size_bytes) != (artifact.payload_schema, artifact.media_type, artifact.size_bytes):
        raise ValueError('parameter response raw publication binding differs')
    raw = port.read()
    if hasattr(saved, 'members'):
        return decode_matrix_arrays(raw, saved)
    return raw


class MatrixParameterResponseRunner:
    """PURE phases expose no native-subwork hook."""
    def __init__(self, role):
        self.role = role
        self.manifest = next(m for m in operation_manifests() if m.capability_key.endswith('.' + role))

    def execute(self, context):
        try:
            _, records, ports = _decode(context, self.role)
            output = next((p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ), None)
            if self.role == 'origin':
                s = records[MatrixParameterResponseSource.SCHEMA]
                supply = records[MatrixParameterFactorSupply.SCHEMA]
                product = records[MatrixParameterFactorProduct.SCHEMA]
                history = consume(ports, supply.product.arrays)
                initial_fp = sha256(np.ascontiguousarray(history['primary_positions'][0], dtype='<c16').tobytes()
                                    + np.ascontiguousarray(history['primary_momenta'][0], dtype='<c16').tobytes()).hexdigest()
                if dict(s.allocation.initial_state_sha256s)[s.root.root_id] != initial_fp:
                    raise ValueError('parameter origin substitutes authenticated matched initial state')
                factor = consume(ports, product.arrays)
                templates = consume(ports, s.instrument_arrays)
                raw, result = science.origin_record(s, history, factor, templates, product, artifact_id=output.logical_artifact_id)
            else:
                origin = records[MatrixParameterResponseOrigin.SCHEMA]
                past = consume(ports, origin.arrays)
                if self.role == 'forecast':
                    raw, result = science.forecast(origin, past, records[MatrixFactorResponseModel.SCHEMA], artifact_id=output.logical_artifact_id)
                elif self.role == 'assess':
                    forecast, native = records[MatrixParameterResponseForecast.SCHEMA], records[MatrixParameterNativeResponses.SCHEMA]
                    s = records[MatrixParameterResponseSource.SCHEMA]
                    supply, product = records[MatrixParameterFactorSupply.SCHEMA], records[MatrixParameterFactorProduct.SCHEMA]
                    original = (records[MatrixParameterHistorySource.SCHEMA], supply, records[MatrixParameterFactorSource.SCHEMA],
                        product, records[MatrixParameterFactorAssessment.SCHEMA], consume(ports, supply.product.arrays), consume(ports, product.arrays))
                    raw, result = None, independent.assess(s, origin, forecast, native,
                        past, consume(ports, forecast.arrays), consume(ports, native.arrays), original_inputs=original)
                else:
                    raise ValueError('parameter futures requires genuine guarded native context')
            return _outputs(context, result, raw)
        finally:
            for p in context.input_ports:
                p.close()


def _initial_native_work(context, config, records, ports, expected_parent):
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    source = records[MatrixParameterResponseSource.SCHEMA]
    origin = records[MatrixParameterResponseOrigin.SCHEMA]
    forecast = records[MatrixParameterResponseForecast.SCHEMA]
    past = consume(ports, origin.arrays)
    science.validate_origin_arrays(origin, past)
    if (origin.source != identity(source.causal) or forecast.origin != identity(origin)
            or forecast.model != source.design.model or forecast.cutoff != source.design.cutoff):
        raise ValueError('parameter futures lacks exact prior causal forecast commitment')
    roster = science.branch_census(source)
    definitions = tuple(_definition(context, config, source, source.root.root_id+'.'+row[0],
        (identity(source), identity(origin), identity(forecast), identity(config)), row[1], expected_parent) for row in roster)
    frozen = NativeSubworkRoster('selected.native-subwork', expected_parent, tuple(row.identity for row in definitions))
    work = PreparedNativeWork(expected_parent, _unit(config), _slots(config), definitions, (frozen,))
    return work, past, roster


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not MatrixParameterResponseNativeRunner or runner.role != 'futures':
        raise ValueError('parameter response preparation requires its installed original native phase')
    config, records, ports = _decode(context, 'futures')
    return _initial_native_work(context, config, records, ports, expected_parent)[0]


class MatrixParameterResponseNativeRunner(MatrixParameterResponseRunner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, records, ports = _decode(context, 'futures')
            s = records[MatrixParameterResponseSource.SCHEMA]
            o, f = records[MatrixParameterResponseOrigin.SCHEMA], records[MatrixParameterResponseForecast.SCHEMA]
            work, past, roster = _initial_native_work(context, config, records, ports, native_subwork.parent_contact)
            definitions = work.definitions
            states = tuple(native_subwork.inspect(d).state for d in definitions)
            if any(state not in (NativeSubworkState.NOT_ENTERED, NativeSubworkState.COMPLETED) for state in states):
                raise ValueError('uncertain or failed parameter branch cannot be replayed')
            if any(state is NativeSubworkState.NOT_ENTERED for state in states):
                native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            n = s.design.horizon_steps[-1]
            members = {'positions': ('<c16', (n + 1, 2, 3, 4, 4)), 'momenta': ('<c16', (n + 1, 2, 3, 4, 4)),
                       'noise': ('<c16', (n, 2, 3, 4, 4)), 'alpha_tilde': ('<f8', (n + 1, 2)), 'ticks': ('<i8', (n + 1,))}
            branches, events = {}, []
            for b, d in zip(roster, definitions, strict=True):
                def producer(b=b):
                    rng = np.random.Generator(np.random.PCG64(b[1].seed))
                    innovations = np.asarray([hermitian_noise(rng=rng, q=2) for _ in range(n)], dtype='<c16')
                    return science.native_branch(s, o, past, f, b, innovations)
                branches[b[0]] = _run_native(native_subwork, d, producer, members)
                retained = native_subwork.inspect(d)
                if retained.state is not NativeSubworkState.COMPLETED:
                    raise ValueError('parameter child return remains uncertain; no automatic replay')
                events.append(MatrixParameterResponseNativeEvent(b[0], d, retained.begin, retained.contact, retained.completion, retained.receipt))
            output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, result = science.responses(s, o, f, branches, tuple(events), artifact_id=output.logical_artifact_id)
            return _outputs(context, result, raw)
        finally:
            for p in context.input_ports:
                p.close()


def operation_factories():
    factories = []
    for declaration in operation_declarations():
        selected = declaration.manifest()
        role = selected.capability_key.rsplit('.', 1)[-1]
        _, parts = bundle(role, ExtensionContributionKind.METHOD, selected, (), None,
            namespace=NAMESPACE, maximum_config_bytes=None)
        factories.append(declaration.provider_factory(components=tuple(sorted(parts, key=lambda row: row.registration_id))))
    return tuple(factories)
