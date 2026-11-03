# SPDX-License-Identifier: MPL-2.0
"""Source/predict/commit/evaluate graph for the frozen exposed Wilson quartet."""

from hashlib import sha256

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from . import analysis
from .operation_bindings import BUDGET, MAX_BYTES, NODE_IDS, combinations_development_root, operation_declarations
from .operation_contracts import (
    CombinationCommitConfigV1, CombinationEvaluateConfigV1, CombinationPredictConfigV1, CombinationSourceConfigV1,
)
from .source_binding import PROTOCOL_SHA256, TeParentGenbankInputV1, WilsonArticleInputV1, decode_source


def wilson_combinations_recursive_draft(article_input: WilsonArticleInputV1, genbank_input: TeParentGenbankInputV1, *,
                                       protocol_payload: bytes, draft_id="draft.rubisco.wilson-combinations-v1"):
    """Freeze source/selection joins; the source worker independently decodes again.

    Design-time inspection sees already exposed source labels. A posthoc graph
    barrier orders forecast commitment before evaluator label access without
    changing the original exposure or providing a biological qualification.
    """
    if not isinstance(protocol_payload, bytes) or sha256(protocol_payload).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("Wilson composition changes the exact frozen assessment protocol bytes")
    panel, parent = decode_source(article_input, genbank_input)
    science = analysis.wilson_quartet_science(panel, parent)
    study = combinations_development_root(science, study_id=f"study.{draft_id}")
    budget = ResourceBudget(1, BUDGET.memory_bytes, 0, 4 * BUDGET.wall_time_seconds,
                            4 * BUDGET.source_scan_bytes, 4 * BUDGET.output_bytes)
    policy = AuthorityPolicy(f"policy.{draft_id}", "owner.local-researcher", "operator.local-development",
        (study.study_id,), frozenset((study.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(), budget,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    root_id = f"design.{draft_id}"
    node = CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(study.study_id, study), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(f"campaign.{draft_id}", study.question, (study.system.object_id,), (study.world_id,),
        tuple(c.claim_id for c in study.claims), budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(f"decision-right.{draft_id}", AuthorityAction.SIMULATION_EXECUTION,
                       "owner.local-researcher", policy.policy_id, False),),
        (node,), (root_id,), (root_id,), (), LifecycleStatus.ACTIVE)
    registrations = {declaration.config_record_type: declaration.registration() for declaration in operation_declarations()}
    config_types = (CombinationSourceConfigV1, CombinationPredictConfigV1, CombinationCommitConfigV1, CombinationEvaluateConfigV1)
    operations = []
    for role, config_type in zip(("source", "predict", "commit", "evaluate"), config_types, strict=True):
        node_id = NODE_IDS[role]
        config = config_type(f"config.{node_id}", science)
        operations.append(RecursiveOperationSpec.from_config(node_id=node_id,
            selection=registrations[config_type].selection, config_id=config.config_id, config=config,
            obligation_ids=(f"obligation.{node_id}.complete-roles",), resource_budget=BUDGET))
    external, links = [], []
    for role, record in (("article", article_input), ("genbank", genbank_input)):
        if len(record.canonical_bytes()) > MAX_BYTES:
            raise ValueError("canonical native source wrapper exceeds the exact registered input byte bound")
        input_id = f"external.{record.input_id}"
        external.append(RecursiveExternalInput(input_id, record.input_id, record.SCHEMA, "application/json", MAX_BYTES,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, record.fingerprint(), "SOURCE"))
        links.append(RecursiveInputLink(f"edge.{NODE_IDS['source']}.{role}", NODE_IDS["source"], role,
                                       external_input_id=input_id, scientific_role="SOURCE"))
    for consumer, port, producer, output, role in (
        ("predict", "features", "source", "features", "SOURCE"),
        ("predict", "training", "source", "training", "SOURCE"),
        ("commit", "forecast", "predict", "forecast", "MODEL"),
        ("evaluate", "commitment", "commit", "commitment", "ACTION"),
        ("evaluate", "labels", "source", "labels", "OUTCOME"),
    ):
        links.append(RecursiveInputLink(f"edge.{NODE_IDS[consumer]}.{port}", NODE_IDS[consumer], port,
            NODE_IDS[producer], output, scientific_role=role))
    ordered = tuple(sorted(operations, key=lambda v: v.node_id))
    return RecursiveStudyDraft(draft_id, study.question, campaign, (), (), (), ordered,
        tuple(sorted(external, key=lambda v: v.input_id)), tuple(sorted(links, key=lambda v: v.edge_id)),
        tuple(v.node_id for v in ordered), development_study=study)
