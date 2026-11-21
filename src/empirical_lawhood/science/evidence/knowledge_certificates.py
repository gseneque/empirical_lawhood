# SPDX-License-Identifier: MPL-2.0
"""Portable exact assessment references, without new scientific authority.

The referenced originals retain scientific meaning. These envelopes neither
grant current consumer admission nor authenticate a person's authorship.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import ClaimSpec
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_claim_assessment import InquiryClaimAssessment
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_nonempty, validate_stable_id
from empirical_lawhood.science.models.time import validate_utc_timestamp


def _reference(value, schema=None, version=None):
    if type(value) is not ObjectIdentity:
        raise TypeError("knowledge references require their complete canonical identities")
    value.__post_init__()
    if ((schema is not None and value.object_schema != schema)
            or (version is not None and value.object_version != version)):
        raise ValueError("knowledge reference substitutes its exact record contract")


@dataclass(frozen=True, slots=True)
class KnowledgeAssessmentCertificate(CanonicalRecord):
    """One original scoped finding, including adverse and unevaluable findings."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/knowledge-assessment-certificate"
    certificate_id: str
    contribution: ObjectIdentity
    transport: ObjectIdentity
    replay_specification: ObjectIdentity
    assessment_projection: ObjectIdentity
    subject: ObjectIdentity
    source: ObjectIdentity
    assessment_contract: ObjectIdentity
    method: ObjectIdentity
    disposition: AssessmentDisposition
    interpretation: str = "ORIGINAL_SCOPED_ASSESSMENT_WITHOUT_NEW_ADMISSION"

    def __post_init__(self):
        validate_stable_id(self.certificate_id)
        _reference(self.contribution, ContributionManifest.SCHEMA, ContributionManifest.VERSION)
        _reference(self.transport, "empirical-lawhood/runtime/portable-recursive-contribution", "1.0.0")
        _reference(self.replay_specification, RobustInquirySpecification.SCHEMA, RobustInquirySpecification.VERSION)
        _reference(self.assessment_projection, InquiryClaimAssessment.SCHEMA, InquiryClaimAssessment.VERSION)
        _reference(self.subject, ClaimSpec.SCHEMA, ClaimSpec.VERSION)
        _reference(self.source)
        _reference(self.assessment_contract)
        _reference(self.method, "empirical-lawhood/planning/capability-selection", "1.0.0")
        if (type(self.disposition) is not AssessmentDisposition
                or self.disposition is AssessmentDisposition.NOT_ATTEMPTED
                or self.interpretation != "ORIGINAL_SCOPED_ASSESSMENT_WITHOUT_NEW_ADMISSION"):
            raise ValueError("certificate requires an actual original scientific assessment")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.certificate_id, self)

    @property
    def finding_kind(self):
        return {
            AssessmentDisposition.SATISFIED: "SUPPORTED_SCOPED_ASSESSMENT",
            AssessmentDisposition.FALSIFIED: "ADVERSE_SCOPED_ASSESSMENT",
            AssessmentDisposition.REFUSED: "REFUSED_SCOPED_ASSESSMENT",
            AssessmentDisposition.UNSUPPORTED: "UNSUPPORTED_SCOPED_ASSESSMENT",
            AssessmentDisposition.UNEVALUABLE: "UNEVALUABLE_SCOPED_ASSESSMENT",
        }[self.disposition]


class KnowledgeNoticeKind(StrEnum):
    CORRECTION = "CORRECTION"
    SUPERSESSION = "SUPERSESSION"
    WITHDRAWAL = "WITHDRAWAL"
    CONTRARY_ASSESSMENT = "CONTRARY_ASSESSMENT"


@dataclass(frozen=True, slots=True)
class KnowledgeCertificateNotice(CanonicalRecord):
    """An immutable local custodian assertion, not universal revocation."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/knowledge-certificate-notice"
    notice_id: str
    kind: KnowledgeNoticeKind
    predecessor: ObjectIdentity
    successor: ObjectIdentity | None
    publisher_label: str
    observed_at_utc: str
    reason: str
    authority_scope: str = "LOCAL_CUSTODIAN_ASSERTION_ONLY"

    def __post_init__(self):
        validate_stable_id(self.notice_id)
        validate_stable_id(self.publisher_label)
        validate_utc_timestamp(self.observed_at_utc)
        validate_nonempty(self.reason, field_name="reason")
        if len(self.reason.encode()) > 4096 or type(self.kind) is not KnowledgeNoticeKind:
            raise ValueError("knowledge notice needs a bounded reason and exact update kind")
        _reference(self.predecessor, KnowledgeAssessmentCertificate.SCHEMA, KnowledgeAssessmentCertificate.VERSION)
        if self.successor is not None:
            _reference(self.successor, KnowledgeAssessmentCertificate.SCHEMA, KnowledgeAssessmentCertificate.VERSION)
            if self.successor == self.predecessor:
                raise ValueError("knowledge update cannot replace its predecessor with itself")
        if ((self.kind is KnowledgeNoticeKind.WITHDRAWAL) != (self.successor is None)
                or self.authority_scope != "LOCAL_CUSTODIAN_ASSERTION_ONLY"):
            raise ValueError("knowledge notice changes its successor or local assertion scope")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.notice_id, self)
