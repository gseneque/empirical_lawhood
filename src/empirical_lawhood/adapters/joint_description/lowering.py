# SPDX-License-Identifier: MPL-2.0
"""Compose authored scientific records into assessed execution operations."""
from empirical_lawhood.science.identity.authority import AuthorityAction,AuthorityPolicy,ResourceBudget,SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec,EvidenceCeiling,OutcomeAccess,VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import ConditionRole,ContributionRole,DevelopmentStudySpec,ScientificConditionScope,ScientificConnectionSpec,ScientificRequirementSpec
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.design.campaigns import CampaignLane,CampaignNode,CampaignNodeKind,CampaignSpec,DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput,RecursiveInputLink,RecursiveOperationSpec,RecursiveStudyDraft
from empirical_lawhood.science.joint_description import MAX_BYTES, MAX_COHORT_BYTES
from empirical_lawhood.adapters.joint_description.records import PHASES,NATIVE_PHASES,config_for,phase_config
from empirical_lawhood.execution.capabilities import CapabilityPermission
from empirical_lawhood.execution.plans import ScientificStage

ACCESS,VISIBILITY=OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY
PERMISSIONS=tuple(sorted((CapabilityPermission.READ_DEVELOPMENT,CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
    CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS)))
WORLD="world.joint-description.new-development"
# Every producer-consumer requirement is represented in the same recursive graph.
EDGES=(
    ("calibrate","calibration","fit","calibration","Calibration-only complete root cohort"),
    ("fit","model","prepare","model","Freeze the response laws before preparing fresh evaluation inputs"),
    ("fit","model","forecast","model","Use the immutable calibration-selected response laws"),
    ("prepare","predictors","forecast","predictors","Supply only past/preparation/action/horizon observations"),
    ("forecast","forecast","evaluate","forecast","Publish forecasts and selected actions before any evaluation response"),
    ("prepare","predictors","evaluate","predictors","Reproduce the exact frozen causal predictor census"),
    ("fit","model","assess","model","Retain calibration-only selection and fitted law provenance"),
    ("forecast","forecast","assess","forecast","Retain every issued forecast and selected/no-entry decision"),
    ("evaluate","outcomes","assess","outcomes","Supply the complete assigned outcome census including failure and nonentry"),
)


def budget(phase,device):
    native=phase in NATIVE_PHASES
    # Native stages publish both the original root returns and the assembled
    # product. The parent charges these distinct byte streams to one allowance.
    output_bytes = 2 * MAX_COHORT_BYTES if native else MAX_BYTES
    return ResourceBudget(1,8*1024**3 if native else 4*1024**3,
        int(native and device=="gpu"),21600 if native else 3600,MAX_BYTES*4,output_bytes)


def stage(phase):
    return ScientificStage.FALSIFY if phase=="assess" else ScientificStage.TRANSFORM


def world_kind(specification):
    # Recorded physical cohorts are analyzed as immutable reference artifacts;
    # no physical system is contacted. R22 additionally runs a native simulator.
    return (WorldKind.ANALYTIC_REFERENCE if specification.family_id in
            ("R01","R02","R13","R14","R15","R16") else WorldKind.NUMERICAL_SIMULATOR)


def root_for(config):
    spec=config.specification
    study="study.joint-description."+spec.fingerprint()
    claim=ClaimSpec("claim."+study,WORLD,"population."+spec.family_id.lower(),spec.question,
        "Finite authored preparations, action menu, receivers, horizons, descriptions and economic prices.",
        "unit.independent-preparation-root",None,EvidenceCeiling.NON_PROMOTABLE,ACCESS,VISIBILITY,
        "Held-out development; minima are conditional on the authored finite menu, not universal irreducibility.",
        ("assumption.independent-preparation-roots",))
    return DevelopmentStudySpec(study,spec.question,spec.identity,WORLD,world_kind(spec),
        spec.all_unit_ids,(),(claim,),tuple(sorted((spec.identity,config.selected_inputs,config.provenance),key=lambda r:r.object_id)))


def contracts(config):
    root=root_for(config);spec=config.specification
    scope=ScientificConditionScope(spec.identity.object_id,WORLD,config.selected_inputs.object_id,
        tuple(r.receiver_id for r in spec.receivers),tuple(r.units for r in spec.receivers),
        "receiver.authored-menu","clock.family-native-units",
        "Independent root with nested authored action, horizon and receiver coordinates; no nested observation is a new independent root.",
        source_config_sha256=spec.fingerprint(),population_id=root.claims[0].relation_id)
    requirements,connections=[],[]
    for parent,output,child,port,purpose in EDGES:
        consumer,producer=phase_config(config,child),phase_config(config,parent)
        identifier=consumer.node_id+"."+port
        requirement=ScientificRequirementSpec("requirement."+identifier,consumer.node_id,ConditionRole.INFORMATIONAL,
            purpose,"Exact specification, causal role, retained parent identity and complete authored independent-unit census.",
            scope,phase_config(config,"assess").node_id,
            "Substitution, outcome leakage, a missing assigned unit, changed predictor or unsupported native claim invalidates the supply.",
            (ContributionRole.INSTANCE_PRODUCT,),background_assumption_ids=("assumption.independent-preparation-roots",))
        connection=ScientificConnectionSpec("connection."+identifier,requirement.requirement_id,producer.node_id,
            output,port,phase_config(config,"assess").node_id,root.claims[0].claim_id,ContributionRole.INSTANCE_PRODUCT,requirement.falsifier)
        requirements.append(requirement);connections.append(connection)
    return tuple(sorted(requirements,key=lambda r:r.requirement_id)),tuple(sorted(connections,key=lambda r:r.connection_id))


def externals(config):
    return tuple(sorted((RecursiveExternalInput("external."+ref.object_id,ref.object_id,ref.object_schema,
        "application/json",MAX_BYTES,ACCESS,VISIBILITY,ref.object_fingerprint,scientific_role="SOURCE")
        for ref in (config.selected_inputs,config.provenance)),key=lambda r:r.input_id))


def links(config):
    rows=[]
    for parent,output,child,port,_ in EDGES:
        producer,consumer=phase_config(config,parent),phase_config(config,child)
        identifier=consumer.node_id+"."+port
        rows.append(RecursiveInputLink("edge."+identifier,consumer.node_id,port,producer.node_id,output,
            scientific_role="OUTCOME" if port=="outcomes" else "HISTORY",
            requirement_id="requirement."+identifier,connection_id="connection."+identifier))
    for phase in NATIVE_PHASES:
        child=phase_config(config,phase)
        for name,ref in (("selected",config.selected_inputs),("provenance",config.provenance)):
            rows.append(RecursiveInputLink("edge."+child.node_id+"."+name,child.node_id,name,
                external_input_id="external."+ref.object_id,scientific_role="SOURCE"))
    return tuple(sorted(rows,key=lambda r:r.edge_id))


def campaign(config):
    root=root_for(config);resources=ResourceBudget.aggregate(budget(p,config.device) for p in PHASES)
    policy=AuthorityPolicy(root.study_id+".policy","human.selected-operator","researcher.new-development",
        ("joint-description.development",),frozenset({root.world_kind}),
        frozenset({AuthorityAction.READ_ONLY_EXPLORATION}),frozenset({SourceAccessClass.NONE}),
        ("new-calibration-and-evaluation",),frozenset(),resources,ACCESS)
    node=CampaignNode(root.study_id+".proposal",CampaignNodeKind.ANALYSIS_PROPOSAL,CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id,root),(),LifecycleStatus.ACTIVE)
    return CampaignSpec(root.study_id+".campaign",root.question,(root.system.object_id,),(WORLD,),
        (root.claims[0].claim_id,),resources,ObjectIdentity.from_record(policy.policy_id,policy),
        (DecisionRight(root.study_id+".right",AuthorityAction.READ_ONLY_EXPLORATION,policy.delegate_id,policy.policy_id,True),),
        (node,),(node.node_id,),(node.node_id,),(),LifecycleStatus.ACTIVE)


def lower(specification,selected,provenance):
    from empirical_lawhood.adapters.joint_description.bindings import operation_declarations
    base=config_for(specification,selected,provenance,"assess")
    configs=tuple(phase_config(base,phase) for phase in PHASES)
    declarations={(d.capability_key.split(".")[-2],d.capability_key.split(".")[-1]):d for d in operation_declarations()}
    operations=tuple(RecursiveOperationSpec.from_config(node_id=c.node_id,
        selection=declarations[c.phase,c.device if c.phase in NATIVE_PHASES else "cpu"].registration().selection,
        config_id=c.config_id,config=c,obligation_ids=("obligation."+c.node_id,),resource_budget=budget(c.phase,c.device)) for c in configs)
    requirements,connections=contracts(base)
    draft=RecursiveStudyDraft(draft_id="draft."+specification.specification_id,question=specification.question,
        campaign=campaign(base),requirements=requirements,connections=connections,suppliers=(),operations=operations,
        external_inputs=externals(base),links=links(base),selected_operation_ids=tuple(c.node_id for c in configs),
        development_study=root_for(base))
    return draft,tuple(sorted(("external."+r.identity.object_id,r) for r in (selected,provenance)))
