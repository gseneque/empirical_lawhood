# SPDX-License-Identifier: MPL-2.0
"""One graph-lowering mechanism behind exact compact/chunked record facades."""
from dataclasses import dataclass
from hashlib import sha256
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.runtime.plans import ScientificStage
from collections.abc import Callable
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class HistoryDraftContract:
    namespace: str
    resources: ResourceBudget
    phases: tuple
    identity: Callable
    coordinate_identity: Callable
    development_root: Callable
    registrations: Callable
    external_id: Callable
    config_type: type[CanonicalRecord]


def development_draft(sources, allocation, provenance, *, draft_id, contract):
    """Lower this complete finite domain roster through ordinary authoring types.

    This pure declaration creates no execution authority or input publication.
    The API must use the actually installed catalogue before any real entry.
    """
    from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.status import LifecycleStatus
    from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
    from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
    NAMESPACE, BUDGET, PHASES = contract.namespace, contract.resources, contract.phases
    identity, coordinate_identity = contract.identity, contract.coordinate_identity
    development_root, operation_registrations = contract.development_root, contract.registrations
    external_id, MatrixParameterOperationConfig = contract.external_id, contract.config_type
    sources = tuple(sources)
    coordinates = {coordinate_identity(c):c for c in allocation.coordinates}
    from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_ou_domain import validate_parameter_ou_domain
    for coordinate in allocation.coordinates:
        validate_parameter_ou_domain(coordinate)
    allocation_id, provenance_id = identity(allocation), provenance.identity
    selected_roots = {r.root.root_id:r for r in allocation.roots}
    for source in sources:
        if (source.allocation != allocation_id or source.provenance != provenance_id
                or selected_roots.get(source.root_id) != source.root or source.coordinate not in coordinates
                or source.numerical_view_ids != tuple(sorted((coordinates[source.coordinate].primary_view.view_id,
                    coordinates[source.coordinate].fine_view.view_id)))):
            raise ValueError('compact draft substitutes actual shared allocation/coordinate/provenance')
    root = development_root(sources,study_id='study.'+draft_id)
    policy = AuthorityPolicy('policy.'+draft_id,'owner.local-researcher','operator.local-development',(root.study_id,),
        frozenset((root.world_kind,)),frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION,AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)),('gate.local-nonactuating-development',),frozenset(),BUDGET,OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode('design.'+draft_id,CampaignNodeKind.EVIDENCE_SNAPSHOT,CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id,root),(),LifecycleStatus.ACTIVE)
    campaign = CampaignSpec('campaign.'+draft_id,root.question,(root.system.object_id,),(root.world_id,),
        tuple(c.claim_id for c in root.claims),BUDGET,ObjectIdentity.from_record(policy.policy_id,policy),
        (DecisionRight('right.'+draft_id,AuthorityAction.SIMULATION_EXECUTION,'owner.local-researcher',policy.policy_id,False),),
        (node,),(node.node_id,),(node.node_id,),(),LifecycleStatus.ACTIVE)
    external,operations,links = {},[],[]
    registrations = {r.selection.capability_key:r for r in operation_registrations()}
    for source in sources:
        records = {'source':source,'allocation':allocation,'coordinate':coordinates[source.coordinate],'provenance':provenance}
        for name,record in records.items():
            input_id = external_id(source,name)
            if input_id in external:
                continue
            selected = allocation_id if name == 'allocation' else provenance_id if name == 'provenance' else source.coordinate if name == 'coordinate' else identity(record)
            external[input_id] = RecursiveExternalInput(input_id,selected.object_id,record.SCHEMA,'application/json',None,
                OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,record.fingerprint(),'SOURCE')
        for s in source.root.streams:
            input_id = 'external.'+source.root_id+'.streams.'+s.purpose
            external[input_id] = RecursiveExternalInput(input_id,source.root.stream_identity(s).object_id,s.SCHEMA,'application/json',None,
                OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,s.fingerprint(),'SOURCE')
        for role,parts,_,_ in PHASES:
            node_id = f'{NAMESPACE}.{source.root_id}.{role}'
            config = MatrixParameterOperationConfig('config.'+node_id,role,source)
            operations.append(RecursiveOperationSpec.from_config(node_id=node_id,selection=registrations[NAMESPACE+'.'+role].selection,
                config_id=config.config_id,config=config,obligation_ids=('obligation.'+node_id+'.complete-scope',),resource_budget=BUDGET))
            for name,_ in parts:
                names = tuple('streams.'+s.purpose for s in source.root.streams) if name == 'streams' else (name,)
                for selected in names:
                    if selected in ('history','history-arrays'):
                        links.append(RecursiveInputLink('edge.'+node_id+'.'+selected,node_id,selected,
                            producer_node_id=f'{NAMESPACE}.{source.root_id}.history',producer_output_id='arrays' if selected.endswith('arrays') else 'product',scientific_role='HISTORY'))
                    else:
                        links.append(RecursiveInputLink('edge.'+node_id+'.'+selected,node_id,selected,
                            external_input_id=external_id(source,selected),scientific_role='SOURCE'))
    return RecursiveStudyDraft(draft_id,root.question,campaign,(),(),(),tuple(sorted(operations,key=lambda x:x.node_id)),
        tuple(sorted(external.values(),key=lambda x:x.input_id)),tuple(sorted(links,key=lambda x:x.edge_id)),
        tuple(sorted(o.node_id for o in operations)),development_study=root)



def validate_history_root(config, context, *, contract, scientific_unit_ids):
    MatrixParameterOperationConfig = contract.config_type
    NAMESPACE, PHASES = contract.namespace, contract.phases
    development_root, external_id = contract.development_root, contract.external_id
    configs = tuple(i.record for i in context.config_inputs)
    if any(type(c) is not MatrixParameterOperationConfig for c in configs):
        raise ValueError('compact history mixes foreign scientific configurations')
    sources = tuple(c.source for c in configs if c.operation == 'history')
    if len(configs) != 2*len(sources) or any(
            len(local := tuple(c for c in configs if c.source.root_id == source.root_id)) != 2
            or {c.operation for c in local} != {'history','assess'}
            or any(c.source != source for c in local) for source in sources):
        raise ValueError('compact history omits complete root/two-phase census')
    if type(context.root) is not DevelopmentStudySpec or context.root != development_root(sources,study_id=context.root.study_id):
        raise ValueError('compact history changes its complete selected scientific root')
    units = context.root.assigned_unit_ids
    native = config.operation == 'history'
    if (context.node_id != f'{NAMESPACE}.{config.source.root_id}.{config.operation}'
            or context.stage is not (ScientificStage.ACQUIRE if native else ScientificStage.FALSIFY)
            or context.unit_ids != scientific_unit_ids(config) or context.selected_unit_ids != units
            or context.complete_unit_census != native or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('compact history changes root/source/stage/unit/access census')
    parts = next(p[1] for p in PHASES if p[0] == config.operation)
    names = {name for name,_ in parts if name != 'streams'}
    if native:
        names |= {'streams.'+s.purpose for s in config.source.root.streams}
    incoming = tuple(l for l in context.links if l.consumer_node_id == context.node_id)
    if len(incoming) != len(names) or {l.consumer_input_id for l in incoming} != names:
        raise ValueError('compact history omits an actual ordinary source/stream/array input')
    for link in incoming:
        if link.consumer_input_id in ('history','history-arrays'):
            if (link.producer_node_id != f'{NAMESPACE}.{config.source.root_id}.history'
                    or link.producer_output_id != ('arrays' if link.consumer_input_id.endswith('arrays') else 'product')
                    or link.external_input_id is not None or link.scientific_role != 'HISTORY'):
                raise ValueError('compact assessor changes actual producer/raw history dependency')
        elif (link.external_input_id != external_id(config.source,link.consumer_input_id)
                or link.scientific_role != 'SOURCE'):
            raise ValueError('compact source loses single shared authenticated ordinary operand')



def development_root(sources, *, study_id, source_operands):
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    sources = tuple(sorted(sources,key=lambda s:s.root_id))
    if not sources or len({s.root_id for s in sources}) != len(sources):
        raise ValueError('compact history needs complete unique selected roots')
    first = sources[0]
    scope = sha256(canonical_json_bytes(tuple(s.root for s in sources))).hexdigest()
    units = tuple(sorted({s.root.root.independent_group_id for s in sources}))
    if any((s.allocation,s.provenance,s.allocation_scope_sha256,s.requested_roots,s.requested_groups) !=
           (first.allocation,first.provenance,scope,len(sources),len(units)) for s in sources):
        raise ValueError('compact history omits authenticated shared root/group census')
    world = 'world.matrix-parameter-history-compact.exposed'
    question = 'Do complete parameter-consistent paired histories pass independently expressed native equations?'
    views = tuple(sorted({v for s in sources for v in s.numerical_view_ids}))
    claims = tuple(ClaimSpec('claim.matrix-parameter-history-compact.'+unit,world,'population.matrix-parameter-history.exposed',
        question,'Complete declared coordinate/root histories with every nested numerical state and innovation.',
        unit,None,EvidenceCeiling.NON_PROMOTABLE,OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,
        'No factor utility, relation, continuum error bound, freshness or qualification.',('assumption.matrix-parameter-history.exposed',),
        numerical_view_ids=views) for unit in units)
    return DevelopmentStudySpec(study_id,question,first.allocation,world,WorldKind.NUMERICAL_SIMULATOR,
        units,views,claims,tuple(sorted({operand for s in sources for operand in source_operands(s)},key=lambda x:x.object_id)))

