# SPDX-License-Identifier: MPL-2.0
"""Source → label-isolated construction/freeze → evaluation composition."""

from hashlib import sha256

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from . import records as r
from .operation_bindings import (
    BUDGETS, MEDIA_TYPE, NODE_IDS, PHASES, TOTAL_BUDGET, operation_declarations,
    prediction_development_root, scientific_design,
)
from .operation_contracts import SOURCE_IDS


def plant_prediction_recursive_draft(natural_table, plant_panel, *, protocol_payload: bytes,
                                     draft_id="draft.rubisco.plant-prediction-v1"):
    """Freeze native identities and the complete exposed three-stage graph.

    Construction receives natural training, sequence queries and measured parent
    anchors only. The ordering barrier cannot make already exposed outcomes fresh.
    """
    if type(protocol_payload) is not bytes or sha256(protocol_payload).hexdigest() != r.PROTOCOL_SHA256:
        raise ValueError("plant prediction changes its exact frozen protocol bytes")
    source_specs = PHASES[0][2]
    for source_id, record, (_, kind, maximum) in zip(SOURCE_IDS, (natural_table, plant_panel), source_specs, strict=True):
        if type(record) is not kind:
            raise ValueError("plant prediction requires exact typed native source witnesses")
        record.__post_init__()
        if len(record.canonical_bytes()) > maximum:
            raise ValueError("plant native source exceeds its registered canonical input bound")
        expected = r.natural_identity() if source_id == SOURCE_IDS[0] else r.plant_identity()
        if ObjectIdentity.from_record(source_id, record) != expected:
            raise ValueError("plant prediction substitutes its exact native table or panel")
    science = scientific_design()
    study = prediction_development_root(science, study_id=f"study.{draft_id}")
    policy = AuthorityPolicy(f"policy.{draft_id}", "owner.local-researcher", "operator.local-development",
        (study.study_id,), frozenset((study.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(), TOTAL_BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    root_id = f"design.{draft_id}"
    node = CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(study.study_id, study), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(f"campaign.{draft_id}", study.question, (study.system.object_id,), (study.world_id,),
        tuple(claim.claim_id for claim in study.claims), TOTAL_BUDGET,
        ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(f"decision-right.{draft_id}", AuthorityAction.SIMULATION_EXECUTION,
                       "owner.local-researcher", policy.policy_id, False),),
        (node,), (root_id,), (root_id,), (), LifecycleStatus.ACTIVE)
    registrations = {declaration.config_record_type: declaration.registration() for declaration in operation_declarations()}
    operations = []
    for role, config_type, *_ in PHASES:
        node_id = NODE_IDS[role]
        config = config_type(f"config.{node_id}", science)
        operations.append(RecursiveOperationSpec.from_config(node_id=node_id,
            selection=registrations[config_type].selection, config_id=config.config_id, config=config,
            obligation_ids=(f"obligation.{node_id}.complete-roles",), resource_budget=BUDGETS[role]))
    external, links = [], []
    for source_id, record, (role, _, maximum) in zip(SOURCE_IDS, (natural_table, plant_panel), source_specs, strict=True):
        input_id = "external." + source_id
        external.append(RecursiveExternalInput(input_id, source_id, record.SCHEMA, MEDIA_TYPE, maximum,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, record.fingerprint(), "SOURCE"))
        links.append(RecursiveInputLink(f"edge.{NODE_IDS['source']}.{role}", NODE_IDS["source"], role,
                                       external_input_id=input_id, scientific_role="SOURCE"))
    for consumer, port, producer, output, role in (
        ("construct", "anchors", "source", "anchors", "SOURCE"),
        ("construct", "queries", "source", "queries", "SOURCE"),
        ("construct", "training", "source", "training", "SOURCE"),
        ("evaluate", "commitment", "construct", "commitment", "ACTION"),
        ("evaluate", "labels", "source", "labels", "OUTCOME"),
    ):
        links.append(RecursiveInputLink(f"edge.{NODE_IDS[consumer]}.{port}", NODE_IDS[consumer], port,
                                       NODE_IDS[producer], output, scientific_role=role))
    ordered = tuple(sorted(operations, key=lambda operation: operation.node_id))
    return RecursiveStudyDraft(draft_id, study.question, campaign, (), (), (), ordered,
        tuple(sorted(external, key=lambda value: value.input_id)), tuple(sorted(links, key=lambda value: value.edge_id)),
        tuple(operation.node_id for operation in ordered), development_study=study)
