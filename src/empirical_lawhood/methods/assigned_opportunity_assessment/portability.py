# SPDX-License-Identifier: MPL-2.0
"""Original receipt-bound contributions and retrospective assessment replay."""

from empirical_lawhood.science.identity.authority import AuthorityAction
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryOutcomeMap, InquiryQuestionKind, InquiryTarget, RobustInquirySpecification, ScientificOutcomeKind
from empirical_lawhood.science.inquiry.recursive_requirements import ContributionRole
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct

from empirical_lawhood.methods.assigned_opportunity_assessment import bindings, design


def replay_specification(draft):
    """Describe a retained claim replay; never represent this as a prior decision."""
    config, operation = bindings.config_from_draft(draft)
    scope = config.assessment.scope
    return RobustInquirySpecification("replay." + draft.fingerprint(),
        "Retrospectively verify the original assigned finite-census assessment without additional acquisition.",
        (), operation.config_identity, scope,
        "An exposed finite-census assessment supplies no population confidence or physical qualification.",
        InquiryQuestionKind.ASSESS,
        InquiryTarget("target." + draft.development_study.fingerprint(), design.QUESTION, scope,
            tuple(r.requirement_id for r in draft.requirements),
            tuple(ObjectIdentity.from_record(c.claim_id, c) for c in draft.development_study.claims),
            "Retain the exact independently assessed original finite predicate, including adverse and missing findings."),
        draft.requirements, draft.connections, draft.requirements[0].requirement_id,
        tuple(sorted((InquiryOutcomeMap("outcome." + kind.value.lower().replace("_", "-"), kind,
            ("retain-original-assessment",), "Preserve the original " + kind.value + " finding and its complete evidence census.",
            "No new acquisition is selected by this retrospective replay.") for kind in ScientificOutcomeKind),
            key=lambda value: value.outcome_id)), AuthorityAction.READ_ONLY_EXPLORATION)


def describe_contributions(draft, products):
    record = bindings.authenticated_assessment(draft, products)
    if record is None:
        return ()
    selected = []
    for value, role in ((record.procedure, ContributionRole.DESIGN_OPERAND),
                        (record, ContributionRole.RETAINED_ANALYSIS_INPUT)):
        matches = tuple((receipt, logical) for receipt in products["receipts"].values()
            for logical in receipt.output_logical_artifacts
            if logical.content_sha256 == value.fingerprint() and logical.payload_schema == value.SCHEMA)
        if len(matches) != 1:
            raise ValueError("finite contribution lacks its exact original producing output")
        receipt, logical = matches[0]
        artifact = products["outputs"][logical.logical_artifact_id]
        if artifact.logical != logical or artifact.materialization.physical_sha256 != value.fingerprint():
            raise ValueError("finite contribution substitutes its original artifact custody")
        selected.append(ContributionProduct("product." + value.identity.object_id, value.identity,
            ArtifactIdentity(logical.logical_artifact_id, "scientific-product", value.SCHEMA, value.fingerprint(),
                logical.media_type, artifact.materialization.size_bytes),
            ObjectIdentity.from_record(receipt.receipt_id, receipt), role,
            draft.development_study.claims[0].evidence_ceiling, logical.outcome_access, logical.visibility_ceiling))
    return (ContributionManifest("contribution." + draft.fingerprint(), design.QUESTION,
        record.disposition + " for the original finite assigned census; no population or physical qualification.",
        record.config.assessment.scope, tuple(sorted(selected, key=lambda value: value.product_id)),
        (record.identity,), () if record.disposition == "SATISFIED" else draft.requirements),)
