# SPDX-License-Identifier: MPL-2.0
"""Compose portable assessment references with the existing receipt verifier."""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate, KnowledgeCertificateNotice, KnowledgeNoticeKind
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_claim_assessment import InquiryClaimAssessment
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import RobustInquirySpecification
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.contracts.record_codecs import UnsupportedRecordRevision

from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.recursive_contributions import _publish, _selected_directory, authenticate_recursive_contribution, export_recursive_contribution
from empirical_lawhood.api.recursive_inquiry_claims import project_wave_claim_assessments


MAX_CERTIFICATE_MEMBER_BYTES = 1024 * 1024


def _identity(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


def _projection_identity(record):
    return ObjectIdentity.from_record("claim-assessment." + record.fingerprint(), record)


def _read(directory, name, kind, reference=None):
    raw = read_bounded_bytes(directory / name, maximum_bytes=MAX_CERTIFICATE_MEMBER_BYTES)
    record = decode_canonical_bytes(raw, kind, maximum_bytes=MAX_CERTIFICATE_MEMBER_BYTES)
    if reference is not None and (record.SCHEMA, record.VERSION, record.fingerprint()) != (
            reference.object_schema, reference.object_version, reference.object_fingerprint):
        raise ValueError("certificate member substitutes its exact original record")
    return record


def _require_specification(specification):
    if type(specification) is not RobustInquirySpecification:
        raise TypeError("certificate replay requires its exact version-two assessment specification")
    specification.__post_init__()
    if len(specification.canonical_bytes()) > MAX_CERTIFICATE_MEMBER_BYTES:
        raise ValueError("certificate replay specification exceeds its explicit byte bound")


def _original_projection(specification, manifest, draft, products):
    _require_specification(specification)
    rows = project_wave_claim_assessments(specification=specification, draft=draft, products=products)
    if len(rows) != 1:
        raise ValueError("certificate requires one exact registered original target assessment")
    row, = rows
    if (specification.target.required_claims != (row.claim_identity,)
            or specification.target.scope != row.scope or manifest.scope != row.scope
            or row.assessment not in manifest.assessments
            or row.assessment_contract != specification.distinguishing_assessment
            or draft.development_study is None):
        raise ValueError("certificate substitutes its original claim, contribution scope or assessment")
    selected = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids
                     and op.config_identity == row.assessment_contract)
    if len(selected) != 1:
        raise ValueError("certificate has no exact original assessment implementation")
    operation, = selected
    method = ObjectIdentity.from_record(operation.selection.capability_key + ".v" + operation.selection.capability_version,
                                       operation.selection)
    return row, method


def _certificate(specification, projection, manifest, transport, draft, method):
    operands = (_identity(manifest, "contribution_id"), _identity(transport, "transport_id"),
        _identity(specification, "specification_id"), _projection_identity(projection), projection.claim_identity,
        draft.development_study.system, projection.assessment_contract, method, projection.disposition)
    key = sha256(canonical_json_bytes(operands)).hexdigest()
    return KnowledgeAssessmentCertificate("certificate." + key, *operands)


def produce_assessment_certificate(*, directory, output_directory, specification, project_root, artifact_writer):
    """Export actual retained evidence once, then publish its reference envelope.

    The supplied specification is a retrospective read selection. It is not
    silently installed as an earlier inquiry commitment or execution decision.
    """
    _require_specification(specification)
    destination = preflight_authoring_output_directory(directory=Path(output_directory),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    # The existing export authenticates the original complete custody and the
    # code-owned contribution description. Incomplete destinations are retained.
    export_recursive_contribution(directory=directory, output_dir=destination / "contribution",
        project_root=project_root, artifact_writer=artifact_writer)
    _, transport, manifest, _, products, _, draft = authenticate_recursive_contribution(
        directory=destination / "contribution", artifact_writer=artifact_writer, include_draft=True)
    projection, method = _original_projection(specification, manifest, draft, products)
    certificate = _certificate(specification, projection, manifest, transport, draft, method)
    for name, record in (("replay-specification.json", specification), ("assessment-projection.json", projection),
                         ("certificate.json", certificate)):
        if len(record.canonical_bytes()) > MAX_CERTIFICATE_MEMBER_BYTES:
            raise ValueError("certificate member exceeds its explicit byte bound")
        _publish(artifact_writer, destination, name, record, certificate.certificate_id)
    return verify_assessment_certificate(directory=destination, artifact_writer=artifact_writer,
                                         expected_certificate=certificate.identity)


def authenticate_assessment_certificate(*, directory, artifact_writer, expected_certificate=None):
    """Return original typed records after current producing-custody replay."""
    selected = _selected_directory(directory, artifact_writer)
    certificate = _read(selected, "certificate.json", KnowledgeAssessmentCertificate, expected_certificate)
    if expected_certificate is not None and certificate.identity != expected_certificate:
        raise ValueError("certificate changes the selected complete content identity")
    specification = _read(selected, "replay-specification.json", RobustInquirySpecification,
                          certificate.replay_specification)
    projection = _read(selected, "assessment-projection.json", InquiryClaimAssessment,
                       certificate.assessment_projection)
    _, transport, manifest, report, products, _, draft = authenticate_recursive_contribution(
        directory=selected / "contribution", artifact_writer=artifact_writer, include_draft=True)
    current, method = _original_projection(specification, manifest, draft, products)
    if current != projection or certificate != _certificate(specification, current, manifest, transport, draft, method):
        raise ValueError("certificate no longer matches its exact registered original assessment")
    if _read(selected, "certificate.json", KnowledgeAssessmentCertificate) != certificate:
        raise ValueError("certificate changed during current verification")
    _read(selected, "replay-specification.json", RobustInquirySpecification, certificate.replay_specification)
    _read(selected, "assessment-projection.json", InquiryClaimAssessment, certificate.assessment_projection)
    artifact_writer.root.verify(for_write=False)
    return certificate, projection, specification, manifest, report, products, draft


def verify_assessment_certificate(*, directory, artifact_writer, expected_certificate=None, allow_incomplete=False):
    """Keep provenance, scientific replay, authorship and current admission apart."""
    if type(allow_incomplete) is not bool:
        raise TypeError("partial certificate inspection requires an explicit boolean")
    selected = _selected_directory(directory, artifact_writer)
    identified = _read(selected, "certificate.json", KnowledgeAssessmentCertificate, expected_certificate)
    if expected_certificate is not None and identified.identity != expected_certificate:
        raise ValueError("certificate changes the selected complete content identity")
    report = {"certificate": identified.to_document(), "certificate_identity": identified.identity.to_document(),
        "directory": str(selected), "byte_identity": "MATCHES_SELECTED_IDENTITY" if expected_certificate else "CANONICAL_IDENTIFIED",
        "producing_custody": "NOT_VERIFIED", "scientific_assessment": "NOT_REPLAYED",
        "authorship": "NOT_ATTESTED", "consumer_admission": "NOT_EVALUATED",
        "current_execution_authority": "NONE", "requalification_performed": False,
        "new_native_contacts": 0, "update_freshness": "NO_UPDATE_SOURCES_QUERIED"}
    try:
        certificate, projection, specification, manifest, original, _, _ = authenticate_assessment_certificate(
            directory=selected, artifact_writer=artifact_writer, expected_certificate=identified.identity)
    except (OSError, ValueError, RuntimeError) as error:
        if not allow_incomplete:
            raise
        reason = ("ACCESS_REFUSED" if isinstance(error, PermissionError) else "MISSING_DEPENDENCY"
                  if isinstance(error, FileNotFoundError) else "UNSUPPORTED_REVISION"
                  if isinstance(error, UnsupportedRecordRevision) else "NOT_VERIFIED")
        return {**report, "status": reason, "reason": str(error)[:1024]}
    return {**report, "status": "VERIFIED_ORIGINAL_ASSESSMENT", "producing_custody": "VERIFIED",
        "scientific_assessment": "REGISTERED_REPLAY_MATCHES_ORIGINAL", "finding_kind": certificate.finding_kind,
        "original_disposition": projection.disposition.value, "scope": projection.scope.to_document(),
        "subject": projection.claim.to_document(), "evidence_ceiling": projection.evidence_ceiling.value,
        "outcome_access": projection.outcome_access.value, "visibility_ceiling": projection.visibility_ceiling.value,
        "independent_unit_ids": projection.independent_unit_ids, "nested_view_ids": projection.nested_view_ids,
        "original_assessment_contract": projection.assessment_contract.to_document(),
        "original_evidence": tuple(p.to_document() for p in projection.evidence),
        "remaining_requirements": tuple(r.to_document() for r in manifest.remaining_requirements),
        "replay_selection": specification.specification_id, "replay_selection_is_original_commitment": False,
        "original_run_id": original["run_id"], "cost_scope": "ORIGINAL_RECEIPT_CLOSURE_UNCHANGED_NO_NEW_TOTAL_INFERRED"}


def produce_certificate_notice(*, predecessor_directory, successor_directory=None, kind, publisher_label, reason,
                               output_directory, project_root, artifact_writer):
    """Publish a local assertion with exact history, without changing admission."""
    if type(kind) is not KnowledgeNoticeKind:
        raise TypeError("knowledge update requires its explicit typed relation")
    destination = preflight_authoring_output_directory(directory=Path(output_directory),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    previous = authenticate_assessment_certificate(directory=predecessor_directory, artifact_writer=artifact_writer)
    later = (None if successor_directory is None else authenticate_assessment_certificate(
        directory=successor_directory, artifact_writer=artifact_writer))
    if later is not None and (previous[0].subject != later[0].subject or previous[1].scope != later[1].scope):
        raise ValueError("knowledge notice changes the exact subject or scientific scope")
    now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    values = (kind, previous[0].identity, None if later is None else later[0].identity, publisher_label, now, reason)
    notice = KnowledgeCertificateNotice("knowledge-notice." + sha256(canonical_json_bytes(values)).hexdigest(), *values)
    destination.mkdir(parents=True)
    _publish(artifact_writer, destination, "notice.json", notice, notice.notice_id)
    return {"notice": notice.to_document(), "notice_identity": notice.identity.to_document(),
        "directory": str(destination), "authorship": "NOT_ATTESTED", "consumer_admission": "NOT_EVALUATED",
        "authority_scope": notice.authority_scope, "original_records_rewritten": False}


def verify_certificate_notice(*, directory, artifact_writer, expected_notice,
                              predecessor_directory, successor_directory=None):
    """Verify selected notice bytes and both original assessments, not publisher trust."""
    selected = _selected_directory(directory, artifact_writer)
    notice = _read(selected, "notice.json", KnowledgeCertificateNotice, expected_notice)
    if notice.identity != expected_notice:
        raise ValueError("knowledge notice changes the selected exact identity")
    before = authenticate_assessment_certificate(directory=predecessor_directory,
        artifact_writer=artifact_writer, expected_certificate=notice.predecessor)
    if notice.successor is not None:
        if successor_directory is None:
            raise FileNotFoundError("knowledge notice requires its exact successor evidence")
        after = authenticate_assessment_certificate(directory=successor_directory,
            artifact_writer=artifact_writer, expected_certificate=notice.successor)
        if before[0].subject != after[0].subject or before[1].scope != after[1].scope:
            raise ValueError("knowledge notice changes the exact subject or scientific scope")
    elif successor_directory is not None:
        raise ValueError("withdrawal assertion has no successor certificate")
    if _read(selected, "notice.json", KnowledgeCertificateNotice, expected_notice) != notice:
        raise ValueError("knowledge notice changed during verification")
    artifact_writer.root.verify(for_write=False)
    return {"status": "VERIFIED_SELECTED_NOTICE_AND_REFERENCED_ASSESSMENTS", "notice": notice.to_document(),
        "authorship": "NOT_ATTESTED", "consumer_admission": "NOT_EVALUATED",
        "authority_scope": notice.authority_scope, "current_global_status": "UNKNOWN",
        "original_records_rewritten": False}
