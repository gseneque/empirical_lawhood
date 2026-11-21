# SPDX-License-Identifier: MPL-2.0
"""Derive the selected common-parent repair graph without entering native work."""

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.execution.plans import ScientificStage
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import GpAmberFragmentRepairInput, GpCarboxylateRepairInput
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import BUDGET, UNIT, GpGeometryRepairConfig, native_input_records, operands, operation_declaration, repair_capability
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


def development_root(config, *, study_id):
    exact(config,GpGeometryRepairConfig)
    view = "view.one-original-gp-geometry-constructed-atoms"
    population = "population.one-source-assembly-constructed-terminal-atoms"
    question = "Can the constructed Gp terminal atoms be repaired while every observed heavy atom remains fixed?"
    denominator = "One original inhibited assembly; all constructed atoms and fixed environment; zero independent biological units."
    assumption = "assumption.dry-ff14sb-inhibited-parent-constructed-only"
    if isinstance(config.source, GpCarboxylateRepairInput):
        view = "view.one-original-gp-geometry-glu213-carboxylates"
        population = "population.one-gp-assembly-eight-lsu-glu213-carboxylates"
        question = "Does the common Gp parent pass the selected force, geometry and displacement screens when inherited Glu213 carboxylates can relax?"
        denominator = ("One inhibited 1BWV assembly with all constructed atoms, all hydrogens, "
                       "24 source-bound inherited heavy atoms across eight LSU copies and zero independent biological units.")
        assumption = "assumption.inhibited-ff14sb-parent-scoped-glu213-refinement"
        if type(config.source) is GpAmberFragmentRepairInput:
            view = "view.one-original-gp-amber-terminal-fragments-glu213"
            question = ("Does the independently reconstructed Amber terminal-fragment parent meet the "
                        "initial stereochemical, final force, geometry and Glu213 displacement screens?")
            assumption = "assumption.inhibited-ff14sb-parent-deterministic-terminal-fragments"
    claim = ClaimSpec("claim.constructed-gp-repair-construction","world.constructed-gp-repair",
        population, question, denominator,
        UNIT,None,EvidenceCeiling.NON_PROMOTABLE,OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY,
        "Construction correspondence does not establish ensemble, force accuracy, kinetics or biological qualification.",
        (assumption,),numerical_view_ids=(view,))
    return DevelopmentStudySpec(study_id,claim.proposition,config.source.identity,claim.world_id,WorldKind.NUMERICAL_SIMULATOR,
        (UNIT,),(view,),(claim,),operands(config))


def native_external_inputs(config):
    return tuple(RecursiveExternalInput("external.constructed-gp-repair." + name, pin.object_id, pin.object_schema,
        "application/json", len(record.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, pin.object_fingerprint, "SOURCE")
        for name, pin, record in native_input_records(config))


def native_input_links(config):
    return tuple(RecursiveInputLink("edge.constructed-gp-repair." + name, repair_capability(config.source), name,
        external_input_id="external.constructed-gp-repair." + name, scientific_role="SOURCE")
        for name, _, _ in native_input_records(config))


def validate_root(config,context):
    if (type(context.root) is not DevelopmentStudySpec
            or context.root != development_root(config,study_id=context.root.study_id)
            or context.node_id != repair_capability(config.source) or context.stage is not ScientificStage.ACQUIRE
            or context.unit_ids != (UNIT,) or context.selected_unit_ids != (UNIT,) or not context.complete_unit_census
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or len(context.config_inputs) != 1 or context.config_inputs[0].record is not config
            or context.config_inputs[0].node_id != repair_capability(config.source) or context.requirements or context.connections
            or context.external_inputs != native_external_inputs(config) or context.links != native_input_links(config)):
        raise ValueError("constructed geometry repair substitutes the complete original scientific scope")


def gp_geometry_repair_draft(config, *, draft_id=None):
    exact(config,GpGeometryRepairConfig)
    draft_id = "draft.constructed-gp-repair."+config.fingerprint() if draft_id is None else draft_id
    root = development_root(config,study_id="study."+draft_id)
    policy = AuthorityPolicy("policy."+draft_id,"owner.local-researcher","operator.local-development",(root.study_id,),
        frozenset((root.world_kind,)),frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION,AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)),("gate.local-nonactuating-development",),frozenset(),BUDGET,OutcomeAccess.DEVELOPMENT_VISIBLE)
    node = CampaignNode("design."+draft_id,CampaignNodeKind.EVIDENCE_SNAPSHOT,CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id,root),(),LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign."+draft_id,root.question,(root.system.object_id,),(root.world_id,),
        tuple(c.claim_id for c in root.claims),BUDGET,ObjectIdentity.from_record(policy.policy_id,policy),
        (DecisionRight("decision-right."+draft_id,AuthorityAction.SIMULATION_EXECUTION,"owner.local-researcher",policy.policy_id,False),),
        (node,),(node.node_id,),(node.node_id,),(),LifecycleStatus.ACTIVE)
    capability = repair_capability(config.source)
    declaration = operation_declaration(carboxylates=type(config.source) is GpCarboxylateRepairInput,
        amber_fragments=type(config.source) is GpAmberFragmentRepairInput)
    operation = RecursiveOperationSpec.from_config(node_id=capability,selection=declaration.registration().selection,
        config_id=config.config_id,config=config,obligation_ids=("obligation.constructed-gp-repair.complete-atom-census",),
        resource_budget=BUDGET,resource_lock_ids=("gp-constructed-geometry-native-worker",),maximum_attempts=1)
    return RecursiveStudyDraft(draft_id,root.question,campaign,(),(),(),(operation,),
        native_external_inputs(config),native_input_links(config),(capability,),development_study=root)
