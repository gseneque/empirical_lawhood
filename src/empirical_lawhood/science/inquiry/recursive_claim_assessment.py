# SPDX-License-Identifier: MPL-2.0
"""Exact target-claim semantics projected by an independent assessment owner.

This record is a read-time projection, not an editable disposition or authority.
The public service reconstructs it from authenticated scientific products through
an installed domain projector. Original inquiry packet bytes remain unchanged.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, ScientificConditionScope
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings


@dataclass(frozen=True, slots=True)
class InquiryClaimAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/inquiry-claim-assessment"
    claim: ClaimSpec
    assessment_contract: ObjectIdentity
    assessment: ObjectIdentity
    producing_receipt: ObjectIdentity
    scope: ScientificConditionScope
    disposition: AssessmentDisposition
    evidence: tuple[ObjectIdentity, ...]
    independent_unit_ids: tuple[str, ...]
    nested_view_ids: tuple[str, ...]
    evidence_ceiling: EvidenceCeiling
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        if type(self.claim) is not ClaimSpec or type(self.scope) is not ScientificConditionScope:
            raise ValueError("target assessment requires its exact typed claim and scope")
        self.claim.__post_init__()
        self.scope.__post_init__()
        if (not isinstance(self.disposition, AssessmentDisposition)
                or self.disposition is AssessmentDisposition.NOT_ATTEMPTED):
            raise ValueError("target assessment requires an actual scientific disposition")
        for record in (self.assessment_contract, self.assessment, self.producing_receipt):
            if type(record) is not ObjectIdentity:
                raise ValueError("target assessment requires exact contract, result and receipt identities")
            record.__post_init__()
        require_sorted_unique_ids(self.evidence, attribute="object_id", field_name="evidence")
        if self.assessment not in self.evidence:
            raise ValueError("target assessment must retain its assessed evidence")
        require_sorted_unique_strings(self.independent_unit_ids, field_name="independent_unit_ids")
        require_sorted_unique_strings(self.nested_view_ids, field_name="nested_view_ids")
        if set(self.independent_unit_ids) & set(self.nested_view_ids):
            raise ValueError("target assessment cannot count nested views as independent units")
        if (self.claim.world_id != self.scope.world_id
                or (self.evidence_ceiling, self.outcome_access, self.visibility_ceiling)
                != (self.claim.evidence_ceiling, self.claim.outcome_access, self.claim.visibility_ceiling)):
            raise ValueError("target assessment changes the claim world or evidence ceiling")

    @property
    def claim_identity(self):
        return ObjectIdentity.from_record(self.claim.claim_id, self.claim)
