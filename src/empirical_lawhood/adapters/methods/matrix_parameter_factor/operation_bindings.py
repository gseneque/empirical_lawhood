"""Cold pure parameter-factor declarations; ROOT owns later registration."""

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterAllocation, MatrixParameterHistorySource
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks,
)

from . import independent, science
from .records import (
    MatrixParameterFactorAssessment, MatrixParameterFactorNumericalDesign, MatrixParameterFactorProduct,
    MatrixParameterFactorSource, MatrixParameterFactorSupply, MatrixParameterScalarContrastSpec,
    MatrixParameterScalarDefinition, identity,
)

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

NAMESPACE = 'matrix-parameter-factor-development'
BUDGET = ResourceBudget(1,None,0,None,None,None)
COMMON = tuple(sorted((('allocation',MatrixParameterAllocation),('analysis-provenance',NumericalProducingProvenance),
    ('contrast',MatrixParameterScalarContrastSpec),('coordinate',MatrixParameterCoordinate),
    ('definition',MatrixParameterScalarDefinition),('numerical-design',MatrixParameterFactorNumericalDesign),
    ('parameter-source',MatrixParameterHistorySource),('rule',FactorEventSpec),
    ('source',MatrixParameterFactorSource),('supply',MatrixParameterFactorSupply))))
PHASES = (
    ('measure',tuple(sorted((*COMMON,('history-arrays',None)))),MatrixParameterFactorProduct,ScientificStage.DEVELOP),
    ('assess',tuple(sorted((*COMMON,('factor-arrays',None),('factor-product',MatrixParameterFactorProduct),('history-arrays',None)))),
        MatrixParameterFactorAssessment,ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class MatrixParameterFactorConfig(CanonicalRecord):
    """Compact identity source and public rule; no native histories or arrays."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-parameter-factor/operation-config'
    config_id: str
    operation: str
    source: MatrixParameterFactorSource
    rule: FactorEventSpec

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if (self.operation not in ('measure','assess') or type(self.source) is not MatrixParameterFactorSource
                or type(self.rule) is not FactorEventSpec or self.rule.identity!=self.source.rule
                or self.config_id!=f'config.{NAMESPACE}.{self.source.root_id}.{self.operation}'):
            raise ValueError('parameter factor config changes compact selected source/rule/phase')


def source_operands(source):
    return (identity(source),source.parameter_source,source.allocation,source.coordinate,source.supply,
        source.rule,source.scalar,source.scalar_definition,source.numerical_design,source.producing_provenance)


def scientific_operand_sha256s(config):
    return tuple(sorted({o.object_fingerprint for o in source_operands(config.source)}))


def scientific_unit_ids(config):
    return (config.source.independent_group_id,)


def development_root(sources, *, study_id):
    sources = tuple(sources)
    if (not sources or len({s.allocation for s in sources})!=1 or len({s.roster for s in sources})!=1
            or len(sources)!=len(sources[0].roster) or {s.root_id for s in sources}!={r.root_id for r in sources[0].roster}):
        raise ValueError('parameter factor root omits complete selected coordinate/root allocation')
    for s in sources:
        selected = next(r for r in s.roster if r.root_id==s.root_id)
        if (s.independent_group_id,s.coordinate,s.clock_id)!=(selected.independent_group_id,selected.coordinate,selected.clock_id):
            raise ValueError('parameter factor root changes actual coordinate/group/clock scope')
    units = tuple(sorted({s.independent_group_id for s in sources}))
    views = tuple(sorted({v for s in sources for r in s.roster for v in r.numerical_view_ids}))
    world = 'world.matrix-parameter-factor.exposed'
    question = 'What structural factors are retained in complete authenticated parameter histories?'
    claims = tuple(ClaimSpec('claim.matrix-parameter-factor.'+unit,world,'population.matrix-parameter-factor.exposed',
        question,'Complete declared coordinate/root, both nested views, selected sectors and observation lattice.',
        unit,None,EvidenceCeiling.NON_PROMOTABLE,OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,
        'Geometric contrast and finite equation checks; no physical admission, iid parameter pooling, useful-response relation or qualification.',
        ('assumption.matrix-parameter-factor.exposed',),numerical_view_ids=views) for unit in units)
    return DevelopmentStudySpec(study_id,question,sources[0].allocation,world,WorldKind.NUMERICAL_SIMULATOR,
        units,views,claims,tuple(sorted({o for s in sources for o in source_operands(s)},key=lambda x:x.object_id)))


def scientific_root_validator(config, context):
    configs = tuple(i.record for i in context.config_inputs)
    if type(context.root) is not DevelopmentStudySpec or any(type(c) is not MatrixParameterFactorConfig for c in configs):
        raise ValueError('parameter factor requires exact exposed root and current typed configurations')
    roots = {r.root_id for r in config.source.roster}
    if (len(configs)!=2*len(roots) or {c.source.root_id for c in configs}!=roots
            or any(c.source.roster!=config.source.roster or c.source.allocation!=config.source.allocation for c in configs)
            or any({c.operation for c in configs if c.source.root_id==r}!={'measure','assess'} for r in roots)):
        raise ValueError('parameter factor omits complete coordinate/matched-group/two-phase census')
    for r in roots:
        if len({(identity(c.source),c.rule.identity) for c in configs if c.source.root_id==r})!=1:
            raise ValueError('parameter factor phases substitute selected source or rule')
    expected = development_root(tuple(c.source for c in configs if c.operation=='measure'),study_id=context.root.study_id)
    units = tuple(sorted({s.independent_group_id for s in (c.source for c in configs)}))
    if (context.root!=expected or context.node_id!=f'{NAMESPACE}.{config.source.root_id}.{config.operation}'
            or context.stage is not (ScientificStage.DEVELOP if config.operation=='measure' else ScientificStage.FALSIFY)
            or context.unit_ids!=scientific_unit_ids(config) or context.selected_unit_ids!=units or context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('parameter factor changes exact scientific root/source/stage/access')
    names = {n for n,_ in next(p[1] for p in PHASES if p[0]==config.operation)}
    if config.source.source_state!='COMPLETED':
        names.remove('history-arrays')
    incoming = tuple(l for l in context.links if l.consumer_node_id==context.node_id)
    if len(incoming)!=len(names) or {l.consumer_input_id for l in incoming}!=names:
        raise ValueError('parameter factor omits selected original source or current diagnostic port')
    for link in incoming:
        if link.consumer_input_id.startswith('factor-'):
            if (link.producer_node_id!=f'{NAMESPACE}.{config.source.root_id}.measure'
                    or link.producer_output_id!=('arrays' if link.consumer_input_id=='factor-arrays' else 'product')
                    or link.external_input_id is not None or link.scientific_role!='HISTORY'):
                raise ValueError('parameter factor assessment changes actual measure dependency')
        elif link.external_input_id is None or link.scientific_role!='SOURCE':
            raise ValueError('parameter factor original history is not an ordinary retained source input')
        elif link.external_input_id!='external.'+config.source.root_id+'.'+link.consumer_input_id:
            raise ValueError('parameter factor changes selected original source port binding')


def operation_manifests():
    return tuple(declaration.manifest() for declaration in operation_declarations())


def operation_registrations():
    return tuple(declaration.registration() for declaration in operation_declarations())


def output_codecs():
    return {t.SCHEMA:t for t in (MatrixParameterFactorConfig,MatrixParameterFactorSource,MatrixParameterFactorSupply,
        MatrixParameterFactorNumericalDesign,MatrixParameterScalarContrastSpec,MatrixParameterScalarDefinition,
        MatrixParameterFactorProduct,MatrixParameterFactorAssessment,MatrixParameterHistorySource,MatrixParameterAllocation,
        MatrixParameterCoordinate,FactorEventSpec,NumericalProducingProvenance)}


def operands(source, parameter, supply, rule, contrast, definition, design, provenance):
    source.validate_operands(parameter,supply,rule,contrast,definition,design,provenance)
    return {'source':source,'parameter-source':parameter,'allocation':parameter.allocation,'coordinate':parameter.coordinate,
        'supply':supply,'rule':rule,'contrast':contrast,'definition':definition,'numerical-design':design,'analysis-provenance':provenance}


def development_draft(cases, *, draft_id):
    """Pure finite lowering; a case is the complete typed ordinary input tuple."""
    from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
    from empirical_lawhood.kernel.status import LifecycleStatus
    from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
    cases = tuple(cases)
    records = tuple(operands(*case) for case in cases)
    root = development_root(tuple(case[0] for case in cases),study_id='study.'+draft_id)
    policy = AuthorityPolicy('policy.'+draft_id,'owner.local-researcher','operator.local-development',(root.study_id,),
        frozenset((root.world_kind,)),frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION,)),frozenset((SourceAccessClass.NONE,)),
        ('gate.local-nonactuating-development',),frozenset(),BUDGET,OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.'+draft_id,CampaignNodeKind.EVIDENCE_SNAPSHOT,CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id,root),(),LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.'+draft_id,root.question,(root.system.object_id,),(root.world_id,),tuple(c.claim_id for c in root.claims),
        BUDGET,ObjectIdentity.from_record(policy.policy_id,policy),(DecisionRight('right.'+draft_id,AuthorityAction.REPOSITORY_IMPLEMENTATION,
            'owner.local-researcher',policy.policy_id,False),),(node,),(node.node_id,),(node.node_id,),(),LifecycleStatus.ACTIVE)
    external,operations,links = {},[],[]
    registrations = {r.selection.capability_key:r for r in operation_registrations()}
    for case,values in zip(cases,records,strict=True):
        source,_,supply,rule,*_ = case
        for name,value in values.items():
            if name=='parameter-source':
                ident = source.parameter_source
            elif name=='allocation':
                ident = source.allocation
            elif name=='coordinate':
                ident = source.coordinate
            elif name=='analysis-provenance':
                ident = value.identity
            else:
                ident = rule.identity if name=='rule' else identity(value)
            eid = 'external.'+source.root_id+'.'+name
            external[eid] = RecursiveExternalInput(eid,ident.object_id,value.SCHEMA,'application/json',None,
                OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,value.fingerprint(),'SOURCE')
        if supply.product is not None:
            artifact = supply.product.arrays.array_artifact
            eid = 'external.'+source.root_id+'.history-arrays'
            external[eid] = RecursiveExternalInput(eid,artifact.artifact_id,artifact.payload_schema,artifact.media_type,MAXIMUM_MATRIX_ARRAY_BYTES,
                OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,artifact.sha256,'SOURCE')
        for role,parts,_,_ in PHASES:
            node_id = f'{NAMESPACE}.{source.root_id}.{role}'
            config = MatrixParameterFactorConfig('config.'+node_id,role,source,rule)
            operations.append(RecursiveOperationSpec.from_config(node_id=node_id,selection=registrations[NAMESPACE+'.'+role].selection,
                config_id=config.config_id,config=config,obligation_ids=('obligation.'+node_id+'.complete-scope',),resource_budget=BUDGET))
            for name,_ in parts:
                if name=='history-arrays' and supply.product is None:
                    continue
                if name.startswith('factor-'):
                    links.append(RecursiveInputLink('edge.'+node_id+'.'+name,node_id,name,
                        producer_node_id=f'{NAMESPACE}.{source.root_id}.measure',producer_output_id='arrays' if name=='factor-arrays' else 'product',scientific_role='HISTORY'))
                else:
                    links.append(RecursiveInputLink('edge.'+node_id+'.'+name,node_id,name,external_input_id='external.'+source.root_id+'.'+name,scientific_role='SOURCE'))
    return RecursiveStudyDraft(draft_id,root.question,campaign,(),(),(),tuple(sorted(operations,key=lambda x:x.node_id)),
        tuple(sorted(external.values(),key=lambda x:x.input_id)),tuple(sorted(links,key=lambda x:x.edge_id)),
        tuple(sorted(o.node_id for o in operations)),development_study=root)


def _decode(context, role):
    types = {MatrixParameterFactorConfig.SCHEMA:MatrixParameterFactorConfig,
        **{t.SCHEMA:t for _,t in next(p[1] for p in PHASES if p[0]==role) if t is not None}}
    records,raw = {},[]
    for port in context.input_ports:
        if port.payload_schema==MATRIX_ARRAY_SCHEMA:
            raw.append(port)
        elif port.payload_schema in types and port.payload_schema not in records:
            record = decode_canonical_bytes(port.read(),types[port.payload_schema],maximum_bytes=None)
            if type(record) is MatrixParameterHistorySource:
                expected_id = record.source_id
            elif type(record) is MatrixParameterAllocation:
                expected_id = record.allocation_id
            elif type(record) is MatrixParameterCoordinate:
                expected_id = record.coordinate_id
            elif type(record) is NumericalProducingProvenance:
                expected_id = record.identity.object_id
            else:
                expected_id = identity(record).object_id
            # A current dependent product's logical task artifact ID is owned
            # by the shared compiler, separately from its internal record ID.
            if type(record) is not MatrixParameterFactorProduct and port.artifact_id!=expected_id:
                raise ValueError('parameter factor worker substitutes canonical original artifact identity')
            records[port.payload_schema] = record
        else:
            raise ValueError('parameter factor worker receives undeclared or duplicate input')
    if set(records)!=set(types):
        raise ValueError('parameter factor worker omits exact typed original operands')
    c = records[MatrixParameterFactorConfig.SCHEMA]
    source = records[MatrixParameterFactorSource.SCHEMA]
    parameter = records[MatrixParameterHistorySource.SCHEMA]
    supply = records[MatrixParameterFactorSupply.SCHEMA]
    rule = records[FactorEventSpec.SCHEMA]
    contrast,definition = records[MatrixParameterScalarContrastSpec.SCHEMA],records[MatrixParameterScalarDefinition.SCHEMA]
    design,provenance = records[MatrixParameterFactorNumericalDesign.SCHEMA],records[NumericalProducingProvenance.SCHEMA]
    source.validate_operands(parameter,supply,rule,contrast,definition,design,provenance)
    selected = next(m for m in operation_manifests() if m.capability_key.endswith('.'+role))
    if (c.operation!=role or c.source!=source or c.rule!=rule or context.config.content_sha256!=c.fingerprint()
            or records[MatrixParameterAllocation.SCHEMA]!=parameter.allocation or records[MatrixParameterCoordinate.SCHEMA]!=parameter.coordinate
            or context.task_id!=f'{NAMESPACE}.{source.root_id}.{role}' or context.resource_budget!=BUDGET
            or context.permissions!=selected.permissions or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError('parameter factor worker substitutes frozen source/config/access')
    expected = []
    if source.history_arrays is not None:
        expected.append(('history',source.history_arrays))
    if role=='assess':
        expected.append(('factor',records[MatrixParameterFactorProduct.SCHEMA].arrays.array_artifact))
    if len(raw)!=len(expected):
        raise ValueError('parameter factor worker changes raw availability/census')
    payloads = {}
    for name,artifact in expected:
        matching = tuple(p for p in raw if (p.artifact_id,p.payload_schema,p.media_type,p.size_bytes)==
            (artifact.artifact_id,artifact.payload_schema,artifact.media_type,artifact.size_bytes))
        if len(matching)!=1:
            raise ValueError('parameter factor worker substitutes original raw artifact metadata')
        payloads[name] = matching[0].read()
    return (source,parameter,supply,rule,contrast,definition,design,provenance),records,payloads


class MatrixParameterFactorRunner:
    """Pure source analysis/assessor: no native method or selected native parent."""
    def __init__(self, role):
        self.role = role
        self.manifest = next(m for m in operation_manifests() if m.capability_key.endswith('.'+role))

    def execute(self, context):
        try:
            case,records,raw = _decode(context,self.role)
            ports = {p.output_id.rsplit('.',1)[-1]:p for p in context.output_ports}
            if set(ports)!=({'product','arrays'} if self.role=='measure' else {'product'}):
                raise ValueError('parameter factor worker omits complete selected output census')
            if self.role=='measure':
                payload,product = science.measure(*case,raw.get('history'),artifact_id=ports['arrays'].logical_artifact_id)
                outputs = (TaskOutputPayload(ports['arrays'].output_id,payload),TaskOutputPayload(ports['product'].output_id,product.canonical_bytes()))
            else:
                product = independent.assess(*case,records[MatrixParameterFactorProduct.SCHEMA],raw.get('history'),raw['factor'])
                outputs = (TaskOutputPayload(ports['product'].output_id,product.canonical_bytes()),)
            if ports['product'].payload_schema!=product.SCHEMA:
                raise ValueError('parameter factor output changes actual canonical schema')
            return RunnerResult(tuple(sorted(outputs,key=lambda o:o.output_id)),(ReceiptCheck('complete-parameter-factor-census',True,()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    result = []
    for declaration in operation_declarations():
        m = declaration.manifest()
        role = m.capability_key.rsplit('.',1)[-1]
        _,parts = bundle(role,ExtensionContributionKind.METHOD,m,(),None,namespace=NAMESPACE,maximum_config_bytes=None)
        result.append(declaration.provider_factory(components=tuple(sorted(parts,key=lambda x:x.registration_id))))
    return tuple(result)


def operation_declarations():
    """Own each selected scientific contract and derive its installed projections."""
    return tuple(RecursiveOperationDeclaration(
        capability_key=f'{NAMESPACE}.{role}', capability_version='1.0.0',
        implementation_id=NAMESPACE+'.'+role+'.v1',
        kind=CapabilityKind.ANALYSIS if role=='measure' else CapabilityKind.FALSIFIER,
        config_record_type=MatrixParameterFactorConfig, stage=stage,
        input_ports=tuple(RecursivePortContract(name,record.SCHEMA if record else MATRIX_ARRAY_SCHEMA,
            'application/json' if record else 'application/x-npz',None if record else MAXIMUM_MATRIX_ARRAY_BYTES,
            minimum_count=0 if name=='history-arrays' else 1) for name,record in inputs),
        outputs=tuple(sorted((OutputTemplate('product',output.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','.json'),
            *((OutputTemplate('arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz','.npz'),)
              if role=='measure' else ())),key=lambda value:value.output_id)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=tuple(sorted(('full-raw-operator-eigenpair-witness',
            'actual-parameter-scalar-source','complete-group-view-sector-census'))),
        runner_factory=lambda phase=role:MatrixParameterFactorRunner(phase), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=scientific_operand_sha256s,
            scientific_unit_ids=scientific_unit_ids,scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=identity),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),storage_codecs=MATRIX_STORAGE_CODECS)
        for role,inputs,output,stage in PHASES)
