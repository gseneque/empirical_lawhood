# SPDX-License-Identifier: MPL-2.0
"""Compose an exposed supplied-kinetics assay through the common recursive route."""

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec, RecursiveStudyDraft

from .assay_binding import BUDGET, CLAIM_ID, SYSTEM_ID, WORLD_ID, assay_claim, assay_declaration, assay_units

QUESTION = "Do supplied Rubisco macroscopic kinetics reproduce the complete conditional gas-query history?"


def assay_recursive_draft(config, *, draft_id="draft.rubisco.conditional-assay"):
    """Freeze exact operands without creating prospective or biological authority."""
    config_identity = ObjectIdentity.from_record(config.config_id, config)
    claim = assay_claim()
    study = DevelopmentStudySpec(f"study.{draft_id}", QUESTION,
        ObjectIdentity.from_record(SYSTEM_ID, config), WORLD_ID, WorldKind.NUMERICAL_SIMULATOR,
        assay_units(config), claim.numerical_view_ids, (claim,), (config_identity,))
    policy = AuthorityPolicy(f"policy.{draft_id}", "owner.local-researcher", "operator.local-development",
        (study.study_id,), frozenset((WorldKind.NUMERICAL_SIMULATOR,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(),
        BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    root_id = f"design.{draft_id}"
    node = CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(study.study_id, study), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(f"campaign.{draft_id}", QUESTION, (SYSTEM_ID,), (WORLD_ID,), (CLAIM_ID,),
        BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(f"decision-right.{draft_id}", AuthorityAction.SIMULATION_EXECUTION,
                       "owner.local-researcher", policy.policy_id, False),),
        (node,), (root_id,), (root_id,), (), LifecycleStatus.ACTIVE)
    operation = RecursiveOperationSpec.from_config(node_id="rubisco.conditional-assay",
        selection=assay_declaration().registration().selection, config_id=config.config_id, config=config,
        obligation_ids=("obligation.rubisco.complete-conditional-census",), resource_budget=BUDGET)
    return RecursiveStudyDraft(draft_id, QUESTION, campaign, (), (), (), (operation,), (), (),
        (operation.node_id,), development_study=study)
