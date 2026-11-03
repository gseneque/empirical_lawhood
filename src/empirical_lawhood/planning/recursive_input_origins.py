# SPDX-License-Identifier: MPL-2.0
"""Explicit input ownership composed with unchanged historical recursive drafts."""

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, validate_nonempty, validate_sha256,
    validate_stable_id,
)


# Portable custody permissions and execution graph information roles are distinct.
# This explicit projection grants no additional custody role or source authority.
_CONTRIBUTION_GRAPH_ROLES = {
    ContributionRole.DESIGN_OPERAND: "MODEL",
    ContributionRole.QUALIFIED_EVIDENTIAL_PARENT: "QUALIFICATION",
    ContributionRole.RETAINED_ANALYSIS_INPUT: "HISTORY",
    ContributionRole.INSTANCE_PRODUCT: "OUTCOME",
}


def contribution_graph_role(role: ContributionRole) -> str:
    """Project a selected portable role into its existing execution graph role."""
    return _CONTRIBUTION_GRAPH_ROLES[ContributionRole(role)]


class RecursiveInputOriginKind(StrEnum):
    SOURCE = "SOURCE"
    CONTRIBUTION = "CONTRIBUTION"


@dataclass(frozen=True, slots=True)
class RecursiveInputOrigin(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/recursive-input-origin"
    input_id: str
    kind: RecursiveInputOriginKind
    expected_content_sha256: str
    scientific_role: str
    parent: ObjectIdentity | None = None
    product_id: str | None = None
    producing_receipt: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.input_id, field_name="input_id")
        validate_sha256(self.expected_content_sha256)
        validate_nonempty(self.scientific_role, field_name="scientific_role")
        if not isinstance(self.kind, RecursiveInputOriginKind):
            raise ValueError("input origin kind must be typed")
        if self.kind is RecursiveInputOriginKind.SOURCE:
            if any(value is not None for value in (self.parent, self.product_id, self.producing_receipt)):
                raise ValueError("source origin cannot claim contribution ownership")
        else:
            if self.parent is None or self.product_id is None or self.producing_receipt is None:
                raise ValueError("contribution origin requires exact parent, product and producing receipt")
            validate_stable_id(self.product_id, field_name="product_id")
            ContributionRole(self.scientific_role)


@dataclass(frozen=True, slots=True)
class RecursiveInputOrigins(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/planning/recursive-input-origins"
    inputs: tuple[RecursiveInputOrigin, ...]

    def __post_init__(self):
        if not isinstance(self.inputs, tuple) or any(not isinstance(value, RecursiveInputOrigin) for value in self.inputs):
            raise ValueError("input origins require a tuple of typed ownership records")
        require_sorted_unique_ids(self.inputs, attribute="input_id", field_name="inputs")

    def validate_draft(self, draft):
        selected = {link.external_input_id for link in draft.links
                    if link.consumer_node_id in draft.selected_operation_ids and link.external_input_id is not None}
        externals = {value.input_id: value for value in draft.external_inputs if value.input_id in selected}
        if {value.input_id for value in self.inputs} != selected:
            raise ValueError("input origins must own every selected external input exactly once")
        parents = {ObjectIdentity.from_record(value.contribution_id, value): value for value in draft.contribution_parents}
        parent_digests = {value.fingerprint() for value in draft.contribution_parents}
        parent_digests.update(product.artifact.sha256 for value in draft.contribution_parents for product in value.products)
        parent_artifact_ids = {product.artifact.artifact_id for value in draft.contribution_parents for product in value.products}
        for origin in self.inputs:
            external = externals[origin.input_id]
            if external.parent_substitution:
                raise ValueError("prospective parent substitution is not a composed input origin")
            graph_role = (origin.scientific_role if origin.kind is RecursiveInputOriginKind.SOURCE
                          else contribution_graph_role(ContributionRole(origin.scientific_role)))
            if (external.expected_content_sha256 != origin.expected_content_sha256
                or external.scientific_role != graph_role):
                raise ValueError("input origin changes selected input digest or role")
            if origin.kind is RecursiveInputOriginKind.SOURCE:
                if origin.expected_content_sha256 in parent_digests or external.logical_artifact_id in parent_artifact_ids:
                    raise ValueError("source origin disguises a selected parent product")
                continue
            parent = parents.get(origin.parent)
            if parent is None:
                raise ValueError("input origin changes its exact selected contribution parent")
            products = tuple(product for product in parent.products if product.product_id == origin.product_id)
            if len(products) != 1:
                raise ValueError("input origin lacks its exact selected contribution product")
            product = products[0]
            if (product.producing_receipt != origin.producing_receipt
                or product.artifact.sha256 != origin.expected_content_sha256
                or product.role.value != origin.scientific_role
                or product.artifact.payload_schema != external.payload_schema
                or product.outcome_access is not external.outcome_access
                or product.visibility_ceiling is not external.visibility_ceiling):
                raise ValueError("input origin changes parent product receipt, digest, role or access")
