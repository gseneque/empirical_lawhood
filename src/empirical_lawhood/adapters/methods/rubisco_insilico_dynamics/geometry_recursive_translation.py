# SPDX-License-Identifier: MPL-2.0
"""Explicit reuse graph and scientific work; original geometry is never fresh."""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from . import geometry_operation_bindings as ob
from .durable_recursive_translation import PreparationWorkMeaning, work_meaning as preparation_meaning


def external_inputs(config):
    return tuple(RecursiveExternalInput("external." + ob.NODE + "." + row.object_id, row.object_id, row.object_schema,
        ob.MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, row.object_fingerprint, "HISTORY")
        for row in config.operands)


def input_links(config):
    return tuple(RecursiveInputLink("edge." + ob.NODE + "." + row.object_id, ob.NODE,
        ob.port_id(row.object_schema) + "." + row.object_id, external_input_id="external." + ob.NODE + "." + row.object_id,
        scientific_role="HISTORY") for row in config.operands)


def geometry_reuse_draft(config, *, draft_id):
    config.__post_init__()
    root = ob.development_root(config, study_id="study." + draft_id)
    policy = AuthorityPolicy("policy." + draft_id, "owner.local-researcher", "operator.local-development", (root.study_id,),
        frozenset((root.world_kind,)), frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(), ob.BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    design_id = "design." + draft_id
    design = CampaignNode(design_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign." + draft_id, ob.QUESTION, (root.system.object_id,), (root.world_id,),
        tuple(row.claim_id for row in root.claims), ob.BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight("decision-right." + draft_id, AuthorityAction.SIMULATION_EXECUTION, "owner.local-researcher", policy.policy_id, False),),
        (design,), (design_id,), (design_id,), (), LifecycleStatus.ACTIVE)
    operation = RecursiveOperationSpec.from_config(node_id=ob.NODE, selection=ob.operation_declarations()[0].registration().selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + ob.NODE + ".complete-original-geometry-custody",),
        resource_budget=ob.BUDGET, resource_lock_ids=("rubisco-native-single-worker",), maximum_attempts=1)
    return RecursiveStudyDraft(draft_id, ob.QUESTION, campaign, (), (), (), (operation,), external_inputs(config), input_links(config),
        (ob.NODE,), development_study=root)


@dataclass(frozen=True, slots=True)
class GeometryWorkMeaning(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/geometry-reuse-work-meaning"
    fresh_models: PreparationWorkMeaning
    original_supplies: tuple[ObjectIdentity, ...]
    original_assessments: tuple[ObjectIdentity, ...]


def work_meaning(config):
    return GeometryWorkMeaning(preparation_meaning(config), config.plan.geometry_supplies,
        tuple(row.independent_integrity for row in config.supplies))


def native_effect_slot_ids(config):
    return ("native.rubisco-geometry-reuse." + sha256(work_meaning(config).canonical_bytes()).hexdigest(),)


def scientific_work(draft, operation_id):
    if operation_id != ob.NODE or draft.selected_operation_ids != (ob.NODE,) or len(draft.operations) != 1:
        raise ValueError("geometry reuse work changes its complete selected graph")
    operation = draft.operations[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), ob.GeometryReuseConfig, maximum_bytes=None)
    if (operation.config_identity != ObjectIdentity.from_record(config.config_id, config)
            or operation.selection != ob.operation_declarations()[0].registration().selection
            or operation.resource_budget != ob.BUDGET or draft.links != input_links(config) or draft.external_inputs != external_inputs(config)
            or draft.development_study != ob.development_root(config, study_id=draft.development_study.study_id)
            or draft.requirements or draft.connections):
        raise ValueError("geometry reuse changes original parent/scientific root/work meaning")
    meaning = work_meaning(config)
    identity = ObjectIdentity.from_record("method." + ob.NODE, meaning)
    scope = replace(ob.c.scope(config.source), source_id="source.rubisco-geometry-reuse", source_config_sha256=meaning.fingerprint(), receiver_id=ob.NODE)
    return ScientificInquiryWork(identity, tuple(sorted((identity, *config.operands), key=lambda row: row.object_id)),
        scope, ObjectIdentity.from_record("observation." + ob.NODE, meaning))
