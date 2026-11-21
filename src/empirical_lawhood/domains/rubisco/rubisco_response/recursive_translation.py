# SPDX-License-Identifier: MPL-2.0
"""Lower response selections through the existing scientific graph compiler."""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.science.identity.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_semantic_version, validate_sha256, validate_stable_id
from empirical_lawhood.science.records.status import LifecycleStatus
from empirical_lawhood.design.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.design.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.domains.rubisco.rubisco_response.materials import identities
from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import BUDGET, MAX_INPUT_BYTES, MEDIA, NAMESPACE, PHASES, ResponseOperationConfig, development_root, operation_registrations
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import source_union
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import response_requirement_graph, scientific_scope


def graph_contracts(config):
    graph = response_requirement_graph(config.science)
    requirement = next(row for row in graph.requirements if row.requirement_id == graph.conditional_requirement_id)
    connection, = graph.connections
    external = RecursiveExternalInput("external.rubisco-response.study", config.original_study.object_id,
        config.original_study.object_schema, MEDIA, MAX_INPUT_BYTES, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY, config.original_study.object_fingerprint, "SOURCE")
    links = tuple(sorted((
        *(RecursiveInputLink(f"edge.{NAMESPACE}.{role}.study", f"{NAMESPACE}.{role}", "study",
            external_input_id=external.input_id, scientific_role="SOURCE") for role, *_ in PHASES),
        RecursiveInputLink(f"edge.{NAMESPACE}.prediction", f"{NAMESPACE}.assess", "prediction",
            f"{NAMESPACE}.predict", "product", scientific_role="MODEL",
            requirement_id=requirement.requirement_id, connection_id=connection.connection_id),
    ), key=lambda row: row.edge_id))
    return (requirement,), (connection,), (external,), links


def response_draft(original, selected=None, *, draft_id="draft.rubisco-response.exposed", permitted_refinement_id=None):
    from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import validate_unchanged_sources

    selected = original if selected is None else selected
    validate_unchanged_sources(original, selected)
    base = ResponseOperationConfig(f"config.{NAMESPACE}.predict", "predict", original.identity, selected)
    root = development_root(base, study_id="study." + draft_id)
    policy = AuthorityPolicy("policy." + draft_id, "owner.local-researcher", "operator.local-development",
        (root.study_id,), frozenset((root.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(), BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE)
    node_id = "design." + draft_id
    node = CampaignNode(node_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec("campaign." + draft_id, root.question, (root.system.object_id,), (root.world_id,),
        tuple(row.claim_id for row in root.claims), BUDGET, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight("decision-right." + draft_id, AuthorityAction.SIMULATION_EXECUTION,
            "owner.local-researcher", policy.policy_id, False),), (node,), (node_id,), (node_id,), (), LifecycleStatus.ACTIVE)
    registrations = {row.selection.capability_key: row for row in operation_registrations()}
    operations = []
    for role, *_ in PHASES:
        config = ResponseOperationConfig(f"config.{NAMESPACE}.{role}", role, original.identity, selected,
                                        permitted_refinement_id if role == "assess" else None)
        operations.append(RecursiveOperationSpec.from_config(node_id=f"{NAMESPACE}.{role}",
            selection=registrations[f"{NAMESPACE}.{role}"].selection, config_id=config.config_id, config=config,
            obligation_ids=(f"obligation.{NAMESPACE}.{role}.complete-census",), resource_budget=BUDGET))
    requirements, connections, external, links = graph_contracts(base)
    ordered = tuple(sorted(operations, key=lambda row: row.node_id))
    return RecursiveStudyDraft(draft_id, root.question, campaign, requirements, connections, (), ordered,
        external, links, tuple(row.node_id for row in ordered), development_study=root)


def selected_configs(draft):
    selected = tuple(row for row in draft.operations if row.node_id in draft.selected_operation_ids)
    expected_nodes = tuple(sorted(f"{NAMESPACE}.{phase}" for phase, *_ in PHASES))
    if tuple(row.node_id for row in selected) != expected_nodes or draft.selected_operation_ids != expected_nodes:
        raise ValueError("response work needs the complete producer and independent-assessor selection")
    registrations = {row.selection.capability_key: row for row in operation_registrations()}
    configs = {}
    for operation in selected:
        config = decode_canonical_bytes(operation.config_payload.encode(), ResponseOperationConfig,
                                        maximum_bytes=MAX_INPUT_BYTES)
        if (operation.config_identity != ObjectIdentity.from_record(config.config_id, config)
                or operation.node_id != f"{NAMESPACE}.{config.operation}"
                or operation.selection != registrations[operation.node_id].selection
                or operation.resource_budget != BUDGET):
            raise ValueError("response work substitutes code, configuration, phase or bounded resources")
        configs[config.operation] = config
    base = configs["predict"]
    if configs["assess"].science != base.science or configs["assess"].original_study != base.original_study:
        raise ValueError("response work peers disagree about exact selected sources")
    requirements, connections, external, links = graph_contracts(base)
    if (draft.development_study is None
            or draft.development_study != development_root(base, study_id=draft.development_study.study_id)
            or draft.requirements != requirements or draft.connections != connections
            or draft.external_inputs != external or draft.links != links):
        raise ValueError("response work changes the complete source and assessed-connection graph")
    return configs


@dataclass(frozen=True, slots=True)
class ResponseWorkMeaning(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/work-meaning"
    operation: str
    capability: str
    version: str
    implementation_sha256: str
    operands: tuple[ObjectIdentity, ...]
    permitted_refinement_id: str | None

    def __post_init__(self):
        if self.operation not in {"predict", "assess"} or self.capability != f"{NAMESPACE}.{self.operation}":
            raise ValueError("response work changes its registered scientific operation")
        validate_semantic_version(self.version)
        validate_sha256(self.implementation_sha256)
        identities(self.operands)
        if self.permitted_refinement_id is not None:
            validate_stable_id(self.permitted_refinement_id)
            if self.operation != "assess":
                raise ValueError("prediction work cannot depend on an unused refinement selection")


def scientific_work(draft, operation_id):
    configs = selected_configs(draft)
    phase = operation_id.removeprefix(NAMESPACE + ".")
    if phase not in configs or operation_id != f"{NAMESPACE}.{phase}":
        raise ValueError("response work changes its selected operation")
    config = configs[phase]
    operation = next(row for row in draft.operations if row.node_id == operation_id)
    sources = source_union((config.science.cases.identity, config.science.allocation.identity),
        tuple(supply.identity for supply in config.science.supplies),
        () if phase == "predict" else (config.science.acceptance.identity,),
        () if phase == "predict" else tuple(ObjectIdentity.from_record(row.decision_id, row) for row in config.science.decisions))
    meaning = ResponseWorkMeaning(phase, operation.selection.capability_key, operation.selection.capability_version,
        operation.selection.implementation_sha256, sources, config.permitted_refinement_id)
    scope = replace(scientific_scope(config.science), receiver_id=operation_id,
        source_id=config.science.cases.selection_id, source_config_sha256=meaning.fingerprint(),
        instance_id=config.science.cases.selection_id,
        uncertainty_contract=None if phase == "predict" else config.science.acceptance.identity)
    return ScientificInquiryWork(ObjectIdentity.from_record("method." + operation_id, meaning), sources, scope,
                                  ObjectIdentity.from_record("observation." + operation_id, meaning))
