# SPDX-License-Identifier: MPL-2.0
"""Finite partial scientific programmes and explicitly selected executable waves."""

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings,
    validate_nonempty, validate_schema, validate_semantic_version, validate_sha256, validate_stable_id,
)
from .campaigns import CampaignSpec
from .study_authoring import CapabilitySelection, StudyDraft, UnresolvedDecision

MAX_RECURSIVE_CONFIG_BYTES = None


def _bounded_document(text: str) -> dict:
    """Read the strict scientific JSON grammar without an added capacity ceiling."""
    # The owner's exact re-encoding comparison below also rejects every
    # duplicate key. Let the C decoder build mappings instead of calling a
    # Python hook for each nested object in every task configuration.
    value = json.loads(text,
                       parse_float=lambda _: (_ for _ in ()).throw(ValueError("binary config number")),
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite config")))
    if not isinstance(value, dict):
        raise ValueError("scientific configuration must be a record mapping")
    return value



@dataclass(frozen=True, slots=True)
class RecursiveOperationSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/recursive-operation-spec"
    node_id: str
    selection: CapabilitySelection
    config_id: str
    config_payload: str
    obligation_ids: tuple[str, ...]
    resource_budget: ResourceBudget
    resource_lock_ids: tuple[str, ...] = ()
    maximum_attempts: int = 1

    def __post_init__(self) -> None:
        validate_stable_id(self.node_id, field_name="node_id")
        validate_stable_id(self.config_id, field_name="config_id")
        raw = self.config_payload.encode("utf-8")
        if not raw:
            raise ValueError("scientific configuration exceeds its closed byte bound")
        value = _bounded_document(self.config_payload)
        if not isinstance(value, dict) or not isinstance(value.get("schema"), str) or not isinstance(value.get("version"), str):
            raise ValueError("operation config must be a versioned canonical scientific record")
        validate_schema(value["schema"])
        validate_semantic_version(value["version"])
        canonical = json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"
        if canonical != self.config_payload:
            raise ValueError("operation scientific configuration must retain canonical bytes")
        require_sorted_unique_strings(self.obligation_ids, field_name="obligation_ids", allow_empty=False)
        require_sorted_unique_strings(self.resource_lock_ids, field_name="resource_lock_ids")
        if not isinstance(self.maximum_attempts, int) or isinstance(self.maximum_attempts, bool) or self.maximum_attempts < 1:
            raise ValueError("operation needs a finite positive attempt limit")

    @property
    def config_identity(self) -> ObjectIdentity:
        document = json.loads(self.config_payload)
        return ObjectIdentity(self.config_id, document["schema"], document["version"],
                              sha256(self.config_payload.encode()).hexdigest())

    @classmethod
    def from_config(cls, *, node_id, selection, config_id, config, obligation_ids,
                    resource_budget, resource_lock_ids=(), maximum_attempts=1):
        if not isinstance(config, CanonicalRecord):
            raise TypeError("operation config requires an immutable scientific record")
        return cls(node_id, selection, config_id, config.canonical_bytes().decode(),
                   obligation_ids, resource_budget, resource_lock_ids, maximum_attempts)


@dataclass(frozen=True, slots=True)
class RecursiveExternalInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/recursive-external-input"
    input_id: str
    logical_artifact_id: str
    payload_schema: str
    media_type: str
    maximum_size_bytes: int | None
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    expected_content_sha256: str | None
    scientific_role: str = "SOURCE"
    parent_substitution: bool = False

    def __post_init__(self) -> None:
        validate_stable_id(self.input_id, field_name="input_id")
        validate_stable_id(self.logical_artifact_id, field_name="logical_artifact_id")
        validate_schema(self.payload_schema)
        validate_nonempty(self.media_type, field_name="media_type")
        if self.maximum_size_bytes is not None and (
                not isinstance(self.maximum_size_bytes, int) or isinstance(self.maximum_size_bytes, bool)
                or self.maximum_size_bytes <= 0):
            raise ValueError("external input needs a positive byte bound or None")
        if self.parent_substitution:
            if self.scientific_role != "PARENT_RECEIPT" or self.expected_content_sha256 is not None:
                raise ValueError("future parent requires an explicit unbound parent receipt slot")
        elif self.expected_content_sha256 is None:
            raise ValueError("existing external input needs its exact content digest")
        if self.expected_content_sha256 is not None:
            validate_sha256(self.expected_content_sha256)


@dataclass(frozen=True, slots=True)
class RecursiveInputLink(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/recursive-input-link"
    edge_id: str
    consumer_node_id: str
    consumer_input_id: str
    producer_node_id: str | None = None
    producer_output_id: str | None = None
    external_input_id: str | None = None
    scientific_role: str = "HISTORY"
    requirement_id: str | None = None
    connection_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("edge_id", "consumer_node_id", "consumer_input_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        internal = self.producer_node_id is not None or self.producer_output_id is not None
        if internal == (self.external_input_id is not None) or (internal and (self.producer_node_id is None or self.producer_output_id is None)):
            raise ValueError("scientific input link needs exactly one complete producer")
        for name in ("producer_node_id", "producer_output_id", "external_input_id", "requirement_id", "connection_id"):
            if getattr(self, name) is not None:
                validate_stable_id(getattr(self, name), field_name=name)


@dataclass(frozen=True, slots=True)
class SupplierProposal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/supplier-proposal"
    proposal_id: str
    requirement_id: str
    operation_ids: tuple[str, ...]
    prerequisite_requirement_ids: tuple[str, ...]
    selected: bool
    explanation: str
    unavailable_reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.proposal_id, field_name="proposal_id")
        validate_stable_id(self.requirement_id, field_name="requirement_id")
        validate_nonempty(self.explanation, field_name="explanation")
        for name in ("operation_ids", "prerequisite_requirement_ids", "unavailable_reason_codes"):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        if not self.operation_ids and not self.unavailable_reason_codes:
            raise ValueError("supplier must declare operations or an unavailable capability")


@dataclass(frozen=True, slots=True)
class RecursiveStudyDraft(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/recursive-study-draft"
    draft_id: str
    question: str
    campaign: CampaignSpec
    requirements: tuple[ScientificRequirementSpec, ...]
    connections: tuple[ScientificConnectionSpec, ...]
    suppliers: tuple[SupplierProposal, ...]
    operations: tuple[RecursiveOperationSpec, ...]
    external_inputs: tuple[RecursiveExternalInput, ...]
    links: tuple[RecursiveInputLink, ...]
    selected_operation_ids: tuple[str, ...]
    development_study: DevelopmentStudySpec | None = None
    prospective_draft: StudyDraft | None = None
    unresolved_decisions: tuple[UnresolvedDecision, ...] = ()
    contribution_parents: tuple[ContributionManifest, ...] = ()
    maximum_objects: int | None = None
    maximum_links: int | None = None
    maximum_depth: int | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.draft_id, field_name="draft_id")
        validate_nonempty(self.question, field_name="question")
        for values, attribute, name in (
            (self.requirements, "requirement_id", "requirements"),
            (self.connections, "connection_id", "connections"),
            (self.suppliers, "proposal_id", "suppliers"),
            (self.operations, "node_id", "operations"),
            (self.external_inputs, "input_id", "external_inputs"),
            (self.links, "edge_id", "links"),
            (self.unresolved_decisions, "decision_id", "unresolved_decisions"),
            (self.contribution_parents, "contribution_id", "contribution_parents"),
        ):
            require_sorted_unique_ids(values, attribute=attribute, field_name=name)
        require_sorted_unique_strings(self.selected_operation_ids, field_name="selected_operation_ids")
        for name in ("maximum_objects", "maximum_links", "maximum_depth"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value <= 0):
                raise ValueError("recursive graph capacity must be positive or unrestricted")
        objects = sum(map(len, (self.operations, self.requirements, self.connections, self.suppliers, self.external_inputs)))
        if ((self.maximum_objects is not None and objects > self.maximum_objects)
                or (self.maximum_links is not None and len(self.links) > self.maximum_links)):
            raise ValueError("authored programme exceeds declared graph bounds")
        if self.development_study is not None and self.prospective_draft is not None:
            raise ValueError("one wave cannot mix development and prospective scientific roots")
        if not set(self.selected_operation_ids).issubset({operation.node_id for operation in self.operations}):
            raise ValueError("selected wave names an absent operation")


@dataclass(frozen=True, slots=True)
class RecursiveScientificSelection(CanonicalRecord):
    """Scientific operands selected for one wave, without an authorization wrapper."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/recursive-scientific-selection"
    selection_id: str
    requirements: tuple[ScientificRequirementSpec, ...]
    connections: tuple[ScientificConnectionSpec, ...]
    operations: tuple[RecursiveOperationSpec, ...]
    external_inputs: tuple[RecursiveExternalInput, ...]
    links: tuple[RecursiveInputLink, ...]
    contribution_parents: tuple[ObjectIdentity, ...]
    scientific_root: ObjectIdentity

    def __post_init__(self) -> None:
        validate_stable_id(self.selection_id, field_name="selection_id")
        for values, attribute, name in (
            (self.requirements, "requirement_id", "requirements"),
            (self.connections, "connection_id", "connections"),
            (self.operations, "node_id", "operations"),
            (self.external_inputs, "input_id", "external_inputs"),
            (self.links, "edge_id", "links"),
            (self.contribution_parents, "object_id", "contribution_parents"),
        ):
            require_sorted_unique_ids(values, attribute=attribute, field_name=name)
        if not self.operations:
            raise ValueError("a selected scientific wave requires operations")


def validate_selected_requirement_graph(*, requirements, suppliers=(), maximum_depth=None):
    """Validate scientific prerequisites independently of operation dependencies.

    Partial, unselected branches remain editable. A selected wave must retain
    every prerequisite and close an acyclic graph within its declared bound.
    Selected supplier prerequisites participate even when the task DAG is flat.
    """
    by_id = {requirement.requirement_id: requirement for requirement in requirements}
    if len(by_id) != len(requirements):
        raise ValueError("selected scientific requirement census is invalid")
    if maximum_depth is not None and (type(maximum_depth) is not int or maximum_depth <= 0):
        raise ValueError("scientific requirement graph depth bound is invalid")
    prerequisites = {key: set(value.further_requirement_ids) for key, value in by_id.items()}
    for proposal in suppliers:
        if proposal.selected and proposal.requirement_id in by_id:
            prerequisites[proposal.requirement_id].update(proposal.prerequisite_requirement_ids)
    if any(not parents.issubset(by_id) for parents in prerequisites.values()):
        raise ValueError("selected scientific requirement graph has unresolved prerequisites")
    levels = {}
    while len(levels) < len(by_id):
        ready = sorted(key for key, parents in prerequisites.items()
                       if key not in levels and parents.issubset(levels))
        if not ready:
            raise ValueError("selected scientific requirement graph contains a prerequisite cycle")
        for key in ready:
            levels[key] = 1 + max((levels[parent] for parent in prerequisites[key]), default=0)
            if maximum_depth is not None and levels[key] > maximum_depth:
                raise ValueError("selected scientific requirement graph exceeds its depth bound")
    for proposal in suppliers:
        if (proposal.selected and proposal.requirement_id in by_id
            and not set(proposal.prerequisite_requirement_ids).issubset(
                by_id[proposal.requirement_id].further_requirement_ids)):
            raise ValueError("selected supplier prerequisites must be declared by the owning scientific requirement")
    return tuple(sorted(levels.items()))


def explain_recursive_draft(draft: RecursiveStudyDraft) -> dict[str, object]:
    """Describe partial decisions and exact selected operands without capability effects."""
    selected = set(draft.selected_operation_ids)
    operations = {operation.node_id: operation for operation in draft.operations}
    selected_requirements = tuple(requirement for requirement in draft.requirements
                                  if requirement.consumer_operation_id in selected)
    unresolved = []
    try:
        validate_selected_requirement_graph(requirements=selected_requirements,
            suppliers=draft.suppliers, maximum_depth=draft.maximum_depth)
    except ValueError as error:
        unresolved.append((draft.draft_id, str(error)))
    for requirement in selected_requirements:
        if requirement.scope is None:
            unresolved.append((requirement.requirement_id, "SCIENTIFIC_SCOPE_REQUIRED"))
        if requirement.assessment_operation_id is None or requirement.assessment_operation_id not in selected:
            unresolved.append((requirement.requirement_id, "SELECTED_ASSESSMENT_REQUIRED"))
    for link in draft.links:
        if link.consumer_node_id in selected and link.producer_node_id is not None and link.producer_node_id not in selected:
            unresolved.append((link.edge_id, "SELECTED_SUPPLIER_REQUIRED"))
    return {
        "draft_id": draft.draft_id, "draft_sha256": draft.fingerprint(), "question": draft.question,
        "authored_operation_count": len(draft.operations), "selected_operation_count": len(selected),
        "selected_operation_ids": tuple(sorted(selected)),
        "selected_operations": tuple({"node_id": operations[node].node_id,
                                      "capability": operations[node].selection.selection_id,
                                      "config_sha256": operations[node].config_identity.object_fingerprint,
                                      "maximum_attempts": operations[node].maximum_attempts,
                                      "resource_budget": operations[node].resource_budget.to_document()['value'],
                                      "resource_lock_ids": operations[node].resource_lock_ids,
                                      "obligation_ids": operations[node].obligation_ids}
                                     for node in sorted(selected)),
        "requirement_count": len(draft.requirements), "connection_count": len(draft.connections),
        "selected_requirement_count": len(selected_requirements),
        "requirements": tuple({"requirement_id": requirement.requirement_id,
                               "consumer": requirement.consumer_operation_id,
                               "condition_role": requirement.condition_role.value,
                               "condition": requirement.condition, "purpose": requirement.purpose,
                               "assessment": requirement.assessment_operation_id,
                               "selected": requirement.consumer_operation_id in selected,
                               "permitted_roles": tuple(role.value for role in requirement.permitted_roles),
                               "scope": None if requirement.scope is None else requirement.scope.to_document()['value'],
                               "further_requirement_ids": requirement.further_requirement_ids,
                               "background_assumption_ids": requirement.background_assumption_ids,
                               "resource_commitment": None if requirement.resource_commitment is None else requirement.resource_commitment.to_document()['value'],
                               "falsifier": requirement.falsifier} for requirement in draft.requirements),
        "connections": tuple(connection.to_document()['value'] for connection in draft.connections),
        "suppliers": tuple({"proposal_id": proposal.proposal_id, "requirement_id": proposal.requirement_id,
                            "operation_ids": proposal.operation_ids, "selected": proposal.selected,
                            "unavailable_reason_codes": proposal.unavailable_reason_codes,
                            "prerequisite_requirement_ids": proposal.prerequisite_requirement_ids,
                            "explanation": proposal.explanation} for proposal in draft.suppliers),
        "unresolved_selected_premises": tuple(sorted(unresolved)),
        "unresolved_decision_ids": tuple(decision.decision_id for decision in draft.unresolved_decisions),
        "unresolved_decisions": tuple(decision.to_document()['value'] for decision in draft.unresolved_decisions),
        "contribution_parents": tuple(parent.to_document()['value'] for parent in draft.contribution_parents),
        "declared_claims": tuple(claim.to_document()['value'] for claim in (
            draft.development_study.claims if draft.development_study is not None
            else draft.prospective_draft.experiment.claims if draft.prospective_draft is not None and draft.prospective_draft.experiment is not None else ())),
        "capacity": {"objects": draft.maximum_objects, "links": draft.maximum_links, "depth": draft.maximum_depth},
        "scientific_root": "DEVELOPMENT" if draft.development_study else "PROSPECTIVE" if draft.prospective_draft else "UNSELECTED",
        "prospective_issue_authority": "NOT_GRANTED_BY_AUTHORING",
    }
