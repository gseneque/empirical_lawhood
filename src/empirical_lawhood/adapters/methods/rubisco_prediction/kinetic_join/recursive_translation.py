# SPDX-License-Identifier: MPL-2.0
"""Source-bound W1 design lowering through the existing shared compiler."""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, SourceAccessClass
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry_policy import ScientificInquiryWork
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_decimal, validate_semantic_version, validate_sha256,
    validate_stable_id,
)
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft

from .operation_bindings import (
    BUDGET, MEDIA, NAMESPACE, PHASES, KineticJoinConfig, design, development_root,
    operation_registrations, scope,
)
from ..kinetic_supply import JointKineticSupply, KineticTargetComparison
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery


def kinetic_join_draft(supply, query, comparison, *, relative_tolerance,
                       draft_id="draft.rubisco-kinetic-join.v1"):
    science = design(supply, query, comparison, design_id=NAMESPACE + ".design",
                     relative_tolerance=relative_tolerance)
    root = development_root(science, study_id="study." + draft_id)
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
                       "owner.local-researcher", policy.policy_id, False),),
        (node,), (node_id,), (node_id,), (), LifecycleStatus.ACTIVE)
    registrations = {row.selection.capability_key: row for row in operation_registrations()}
    operations = []
    for role, *_ in PHASES:
        config = KineticJoinConfig(f"config.{NAMESPACE}.{role}", role, science)
        operations.append(RecursiveOperationSpec.from_config(node_id=f"{NAMESPACE}.{role}",
            selection=registrations[f"{NAMESPACE}.{role}"].selection, config_id=config.config_id, config=config,
            obligation_ids=(f"obligation.{NAMESPACE}.{role}.complete-denominator",), resource_budget=BUDGET))
    external, links = [], []
    for port, record, identity, consumer, role in (
        ("supply", supply, science.supply, "assay", "MODEL"),
        ("query", query, science.query, "assay", "ACTION"),
        ("comparison", comparison, science.comparison, "assess", "SOURCE"),
    ):
        input_id = f"external.{NAMESPACE}.{port}"
        external.append(RecursiveExternalInput(input_id, identity.object_id, record.SCHEMA, MEDIA, None,
            OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, record.fingerprint(), role))
        links.append(RecursiveInputLink(f"edge.{NAMESPACE}.{port}", f"{NAMESPACE}.{consumer}", port,
                                       external_input_id=input_id, scientific_role=role))
    links.append(RecursiveInputLink(f"edge.{NAMESPACE}.bridge", f"{NAMESPACE}.assess", "bridge",
        f"{NAMESPACE}.assay", "product", scientific_role="MODEL"))
    ordered = tuple(sorted(operations, key=lambda row: row.node_id))
    return RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), ordered,
        tuple(sorted(external, key=lambda row: row.input_id)), tuple(sorted(links, key=lambda row: row.edge_id)),
        tuple(row.node_id for row in ordered), development_study=root)


@dataclass(frozen=True, slots=True)
class KineticJoinWorkMeaning(CanonicalRecord):
    """Only actually used science; target changes do not recommission an assay."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/kinetic-supply/join-work-meaning"
    operation: str
    capability: str
    version: str
    implementation_sha256: str
    supply: ObjectIdentity
    query: ObjectIdentity
    comparison: ObjectIdentity | None
    numerical_relative_tolerance: Decimal

    def __post_init__(self):
        if self.operation not in {"assay", "assess"} or self.capability != f"{NAMESPACE}.{self.operation}":
            raise ValueError("kinetic work changes its scientific operation")
        validate_stable_id(self.capability)
        validate_semantic_version(self.version)
        validate_sha256(self.implementation_sha256)
        for value, schema in ((self.supply, JointKineticSupply.SCHEMA), (self.query, AssayQuery.SCHEMA)):
            if type(value) is not ObjectIdentity or value.object_schema != schema:
                raise ValueError("kinetic work substitutes its actual scientific operands")
        if ((self.operation == "assay" and self.comparison is not None)
                or (self.operation == "assess" and (type(self.comparison) is not ObjectIdentity
                    or self.comparison.object_schema != KineticTargetComparison.SCHEMA))):
            raise ValueError("kinetic work loses or adds an unused comparison operand")
        validate_decimal(self.numerical_relative_tolerance, field_name="numerical_relative_tolerance", minimum=Decimal(0))
        if self.numerical_relative_tolerance == 0:
            raise ValueError("kinetic work requires its positive numerical tolerance")


def scientific_work(draft, operation_id):
    selected = tuple(row for row in draft.operations if row.node_id in draft.selected_operation_ids)
    if len(selected) != 2 or {row.node_id for row in selected} != {f"{NAMESPACE}.{role}" for role, *_ in PHASES}:
        raise ValueError("kinetic work requires the complete selected registered join")
    operation = next((row for row in selected if row.node_id == operation_id), None)
    if operation is None:
        raise ValueError("kinetic work changes its selected operation")
    config = decode_canonical_bytes(operation.config_payload.encode(), KineticJoinConfig, maximum_bytes=None)
    if (type(draft.development_study) is not DevelopmentStudySpec
            or operation.config_identity != ObjectIdentity.from_record(config.config_id, config)
            or not any(row.selection == operation.selection for row in operation_registrations())
            or operation.node_id != f"{NAMESPACE}.{config.operation}"
            or draft.development_study != development_root(config.science, study_id=draft.development_study.study_id)):
        raise ValueError("kinetic work substitutes its exact code/configuration/root")
    registered = {row.selection.capability_key: row for row in operation_registrations()}
    for peer in selected:
        other = decode_canonical_bytes(peer.config_payload.encode(), KineticJoinConfig, maximum_bytes=None)
        if (other.science != config.science or peer.config_identity != ObjectIdentity.from_record(other.config_id, other)
                or peer.node_id != f"{NAMESPACE}.{other.operation}"
                or peer.selection != registered[f"{NAMESPACE}.{other.operation}"].selection
                or peer.resource_budget != BUDGET):
            raise ValueError("kinetic work changes its full source-bound peer design")
    science = config.science
    expected_links = (
        RecursiveInputLink(f"edge.{NAMESPACE}.bridge", f"{NAMESPACE}.assess", "bridge",
            f"{NAMESPACE}.assay", "product", scientific_role="MODEL"),
        *(RecursiveInputLink(f"edge.{NAMESPACE}.{port}", f"{NAMESPACE}.{consumer}", port,
            external_input_id=f"external.{NAMESPACE}.{port}", scientific_role=role)
          for port, consumer, role in (("comparison", "assess", "SOURCE"),
                                      ("query", "assay", "ACTION"), ("supply", "assay", "MODEL"))),
    )
    expected_inputs = tuple(sorted((RecursiveExternalInput(f"external.{NAMESPACE}.{port}", operand.object_id,
        operand.object_schema, MEDIA, None, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        operand.object_fingerprint, role) for port, operand, role in
        (("supply", science.supply, "MODEL"), ("query", science.query, "ACTION"),
         ("comparison", science.comparison, "SOURCE"))), key=lambda row: row.input_id))
    if (draft.links != tuple(sorted(expected_links, key=lambda row: row.edge_id))
            or draft.external_inputs != expected_inputs):
        raise ValueError("kinetic work substitutes its exact source/input-role graph")
    meaning = KineticJoinWorkMeaning(config.operation, operation.selection.capability_key,
        operation.selection.capability_version, operation.selection.implementation_sha256,
        science.supply, science.query, science.comparison if config.operation == "assess" else None,
        science.numerical_relative_tolerance)
    actual = tuple(sorted((science.supply, science.query) +
        ((science.comparison,) if config.operation == "assess" else ()), key=lambda row: row.object_id))
    method = ObjectIdentity.from_record(f"method.{NAMESPACE}.{config.operation}", meaning)
    scoped = replace(scope(science), receiver_id=operation.node_id, source_config_sha256=meaning.fingerprint())
    return ScientificInquiryWork(method, actual, scoped,
        ObjectIdentity.from_record(f"observation.{NAMESPACE}.{config.operation}", meaning))
