# SPDX-License-Identifier: MPL-2.0
"""Source-bound current sampling graph through the existing recursive services."""

from dataclasses import replace

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from . import operation_bindings as ob


def external_inputs(config):
    return tuple(RecursiveExternalInput("external." + config.node_id + "." + identity.object_id,
        identity.object_id, identity.object_schema, ob.MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, identity.object_fingerprint, "HISTORY") for identity in config.operands)


def input_links(config):
    return tuple(RecursiveInputLink("edge." + config.node_id + "." + identity.object_id, config.node_id,
        ob.input_port_id(identity.object_schema) + "." + identity.object_id,
        external_input_id="external." + config.node_id + "." + identity.object_id,
        scientific_role="HISTORY") for identity in config.operands)


def sampling_control_draft(config, *, draft_id):
    """Lower immutable current inputs without running any molecular science."""
    config.__post_init__()
    root = ob.development_root(config, study_id="study." + draft_id)
    policy = AuthorityPolicy("policy." + draft_id, "owner.local-researcher", "operator.local-development",
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(),
        ob.BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    design_id = "design." + draft_id
    node = CampaignNode(design_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign." + draft_id, ob.QUESTION, (root.system.object_id,), (root.world_id,),
        tuple(row.claim_id for row in root.claims), ob.BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight("decision-right." + draft_id, AuthorityAction.SIMULATION_EXECUTION,
            "owner.local-researcher", policy.policy_id, False),), (node,), (design_id,), (design_id,), (), LifecycleStatus.ACTIVE)
    registration = next(row for row in ob.operation_registrations() if row.selection.capability_key == config.node_id)
    operation = RecursiveOperationSpec.from_config(node_id=config.node_id, selection=registration.selection,
        config_id=config.config_id, config=config,
        obligation_ids=("obligation." + config.node_id + ".complete-original-custody",),
        resource_budget=ob.BUDGET, resource_lock_ids=("rubisco-native-single-worker",), maximum_attempts=1)
    return RecursiveStudyDraft(draft_id, ob.QUESTION, campaign, (), (), (), (operation,), external_inputs(config),
        input_links(config), (config.node_id,), development_study=root)


def scientific_work(draft, operation_id):
    if len(draft.operations) != 1 or draft.selected_operation_ids != (operation_id,):
        raise ValueError("sampling work requires its complete selected original control graph")
    operation = draft.operations[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), ob.SamplingOperationConfig, maximum_bytes=None)
    registration = next(row for row in ob.operation_registrations() if row.selection.capability_key == operation_id)
    if (config.node_id != operation_id or operation.node_id != operation_id
            or operation.config_identity != ObjectIdentity.from_record(config.config_id, config)
            or operation.selection != registration.selection or operation.resource_budget != ob.BUDGET
            or draft.development_study != ob.development_root(config, study_id=draft.development_study.study_id)
            or draft.links != input_links(config) or draft.external_inputs != external_inputs(config)
            or draft.requirements or draft.connections):
        raise ValueError("sampling changes its exact source/plan/input scientific work meaning")
    meaning = ob.work_meaning(config)
    identity = ObjectIdentity.from_record("method." + operation_id, meaning)
    scope = replace(ob.p.scope(config.source), source_id="source.rubisco-sampling-controls",
        source_config_sha256=meaning.fingerprint(), receiver_id=operation_id)
    return ScientificInquiryWork(identity, tuple(sorted((identity, *config.operands), key=lambda row: row.object_id)),
        scope, ObjectIdentity.from_record("observation." + operation_id, meaning))
