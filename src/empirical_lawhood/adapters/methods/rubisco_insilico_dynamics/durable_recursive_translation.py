# SPDX-License-Identifier: MPL-2.0
"""Explicit preparation-control graph; no inferred downstream qualification."""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from . import contracts as c
from . import durable_operation_bindings as ob


def input_identities(config):
    return {"coordinates": config.plan.coordinates, "inventory": config.plan.inventory,
        "nomination": config.plan.nomination, "plan": config.plan.identity,
        "producing-provenance": config.producing_provenance, "source": config.plan.source}


def external_inputs(config):
    # Retained nomination/assemblies inform this control. No unassessed physical
    # model is admitted here and no supplier requirement is declared satisfied.
    return tuple(RecursiveExternalInput("external." + ob.NODE + "." + name,
        identity.object_id, identity.object_schema, ob.MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, identity.object_fingerprint,
        "HISTORY" if name in {"coordinates", "inventory", "nomination"} else "SOURCE")
        for name, identity in sorted(input_identities(config).items()))


def input_links(config):
    return tuple(RecursiveInputLink("edge." + ob.NODE + "." + name, ob.NODE, name,
        external_input_id="external." + ob.NODE + "." + name,
        scientific_role="HISTORY" if name in {"coordinates", "inventory", "nomination"} else "SOURCE")
        for name in sorted(input_identities(config)))


def preparation_control_draft(config, *, draft_id="draft.rubisco-durable-preparation.control01"):
    config.__post_init__()
    root = ob.development_root(config, study_id="study." + draft_id)
    policy = AuthorityPolicy("policy." + draft_id, "owner.local-researcher", "operator.local-development",
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(),
        ob.BUDGET, OutcomeAccess.DEVELOPMENT_VISIBLE)
    node_id = "design." + draft_id
    node = CampaignNode(node_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign." + draft_id, ob.QUESTION, (root.system.object_id,), (root.world_id,),
        tuple(row.claim_id for row in root.claims), ob.BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight("decision-right." + draft_id, AuthorityAction.SIMULATION_EXECUTION,
            "owner.local-researcher", policy.policy_id, False),), (node,), (node_id,), (node_id,), (), LifecycleStatus.ACTIVE)
    registration = ob.operation_registrations()[0]
    operation = RecursiveOperationSpec.from_config(node_id=ob.NODE, selection=registration.selection,
        config_id=config.config_id, config=config,
        obligation_ids=("obligation." + ob.NODE + ".complete-custody-and-denominator",),
        resource_budget=ob.BUDGET, resource_lock_ids=("rubisco-native-single-worker",), maximum_attempts=1)
    return RecursiveStudyDraft(draft_id, ob.QUESTION, campaign, (), (), (), (operation,),
        external_inputs(config), input_links(config), (ob.NODE,), development_study=root)


def validate_graph(context, config):
    if (tuple((row.node_id, row.record) for row in context.config_inputs) != ((ob.NODE, config),)
            or tuple(context.links) != input_links(config)
            or context.requirements or context.connections):
        raise ValueError("preparation control changes exact selected config/input/role census")


@dataclass(frozen=True, slots=True)
class PreparationWorkMeaning(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/preparation-work-meaning"
    physical_operands_json: str
    code_sources: tuple[tuple[str, str], ...]
    dependency_lock_sha256: str
    interpreter_sha256: str
    tleap_sha256: str
    engine_inventory_sha256: str


def work_meaning(config):
    source, plan = config.source, config.plan
    # Operational paths, task labels, checkout HEAD and observation labels do
    # not recommission the same exposed physical request as fresh science.
    physical = {"nomination": plan.nomination, "inventory": plan.inventory, "coordinates": plan.coordinates,
        "constructs": source.constructs, "source_members": tuple((row.member_id, row.sha256) for row in source.source_members),
        "joint_coordinate_views": source.joint_coordinate_views, "parameter_views": source.parameter_views,
        "kcx_aliases": source.kcx_aliases, "chemical_state": source.chemical_state,
        "pH": source.pH, "temperature_kelvin": source.temperature_kelvin, "pressure_atmosphere": source.pressure_atmosphere,
        "water_model": source.water_model, "nonbonded_method": source.nonbonded_method,
        "cutoff_nanometer": source.cutoff_nanometer, "geometry_census": plan.geometry_census,
        "model_census": plan.model_census, "attempted_geometry_ids": plan.attempted_geometry_ids,
        "attempted_model_ids": plan.attempted_model_ids}
    return PreparationWorkMeaning(canonical_json_bytes(physical).decode(), plan.code_sources,
        plan.dependency_lock_sha256, plan.interpreter_sha256, plan.tleap_sha256, plan.engine_inventory_sha256)


def native_effect_slot_ids(config):
    meaning = work_meaning(config)
    return ("native.rubisco-physical-preparation." + sha256(meaning.canonical_bytes()).hexdigest(),)


def scientific_work(draft, operation_id):
    if (operation_id != ob.NODE or len(draft.operations) != 1
            or draft.selected_operation_ids != (ob.NODE,)):
        raise ValueError("preparation work requires its complete selected control graph")
    operation = draft.operations[0]
    config = decode_canonical_bytes(operation.config_payload.encode(), ob.DurablePreparationConfig, maximum_bytes=None)
    if (operation.node_id != ob.NODE or operation.config_identity != ObjectIdentity.from_record(config.config_id, config)
            or operation.selection != ob.operation_registrations()[0].selection
            or operation.resource_budget != ob.BUDGET
            or draft.development_study != ob.development_root(config, study_id=draft.development_study.study_id)
            or draft.links != input_links(config) or draft.external_inputs != external_inputs(config)
            or draft.requirements or draft.connections):
        raise ValueError("preparation work substitutes its source-bound graph/root/operation")
    meaning = work_meaning(config)
    identity = ObjectIdentity.from_record("method." + ob.NODE, meaning)
    scope = replace(c.scope(config.source), source_id="source.rubisco-physical-preparation",
        source_config_sha256=meaning.fingerprint(), receiver_id=ob.NODE)
    return ScientificInquiryWork(identity, tuple(sorted((config.plan.nomination, config.plan.inventory,
        config.plan.coordinates, identity), key=lambda row: row.object_id)), scope,
        ObjectIdentity.from_record("observation." + ob.NODE, meaning))
