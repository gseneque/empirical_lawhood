# SPDX-License-Identifier: MPL-2.0
"""Authenticated retained report assembly and atomic, explicitly located export."""

from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_response.finding_report import build_reference_finding_report
from empirical_lawhood.domains.rubisco.rubisco_response.report_rendering import render_attempt_csv, render_endpoint_csv, render_parameter_csv, render_reference_report
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, derived_outcome_access, lineage_parent_sort_key
from empirical_lawhood.api.domain_composition.rubisco_response.biology import read_biological_analysis
from empirical_lawhood.api.domain_composition.rubisco_response.reference import read_reference_analysis


REPORT_MEMBERS = ("readout.json", "report.txt", "endpoints.csv", "parameters.csv", "attempts.csv")


def read_reference_report(*, directory, information_cutoff, artifact_writer,
                          source_audit=None, nomination_dossier=None, nomination_receipt=None):
    """Read actual custody and independently assemble the early scientific findings."""
    analysis = read_biological_analysis(directory=directory, information_cutoff=information_cutoff,
        artifact_writer=artifact_writer, source_audit=source_audit,
        nomination_dossier=nomination_dossier, nomination_receipt=nomination_receipt)
    reference = analysis.reference
    seed = (reference.study.fingerprint() + reference.predictions.fingerprint()
            + analysis.biological_support.fingerprint() + reference.inquiry.state.fingerprint())
    report_id = "report.rubisco-response." + sha256(seed.encode("ascii")).hexdigest()
    return build_reference_finding_report(reference.study, reference.predictions, analysis.biological_support,
        report_id=report_id, references=reference.references,
        producing_receipts=tuple(sorted(reference.producing_receipts, key=lambda row: row.receipt_id)),
        inquiry_specification=reference.inquiry.specification, work_state=reference.inquiry.state)


def _lineage(report, nomination_receipt):
    parents = []
    receipts = report.producing_receipts + (() if nomination_receipt is None else (nomination_receipt,))
    for receipt in receipts:
        for logical in receipt.output_logical_artifacts:
            for pin in (ObjectIdentity.from_record(receipt.receipt_id, receipt),
                        ObjectIdentity.from_record(logical.logical_artifact_id, logical)):
                parents.append(ArtifactLineageParent(pin, logical.visibility_ceiling, logical.outcome_access))
    return tuple(sorted(set(parents), key=lineage_parent_sort_key))


def export_reference_report(*, directory, output_relative_path, information_cutoff, artifact_writer,
                            source_audit=None, nomination_dossier=None, nomination_receipt=None):
    """Publish the closed report package through the ordinary guarded artifact plane.

    Recheck original source/current access immediately before atomic publication.
    Exporting or re-exporting never schedules a worker or changes an original.
    """
    validate_relative_locator(output_relative_path)
    for name in REPORT_MEMBERS:
        artifact_writer.root.resolve(output_relative_path + "/" + name, for_write=True)
    report = read_reference_report(directory=directory, information_cutoff=information_cutoff,
        artifact_writer=artifact_writer, source_audit=source_audit,
        nomination_dossier=nomination_dossier, nomination_receipt=nomination_receipt)
    payloads = (report.canonical_bytes(), render_reference_report(report).encode("utf-8"),
                render_endpoint_csv(report).encode("utf-8"), render_parameter_csv(report).encode("utf-8"),
                render_attempt_csv(report).encode("utf-8"))
    parents = _lineage(report, nomination_receipt)
    # The selected response lane is exposed; stronger inherited visibility and
    # outcome-access restrictions from every original parent remain in force.
    ceilings = tuple(row.visibility_ceiling for row in parents)
    access = derived_outcome_access(OutcomeAccess.DEVELOPMENT_VISIBLE, *(row.outcome_access for row in parents))
    visibility = inherited_visibility((VisibilityCeiling.DEVELOPMENT_ONLY, *ceilings), access)
    package_id = "report-package.rubisco-response." + sha256(b"".join(sha256(payload).digest() for payload in payloads)).hexdigest()
    writes = tuple(ArtifactWriteRequest("report-member." + sha256(payload).hexdigest() + "." + name.replace(".", "-"),
        output_relative_path + "/" + name, report.SCHEMA if name == "readout.json" else
        "empirical-lawhood/rubisco-response/" + name.replace(".", "-"),
        ArtifactProfile.CANONICAL_JSON if name == "readout.json" else ArtifactProfile.TEXT_PARAMETERS,
        "application/json" if name == "readout.json" else "text/csv" if name.endswith(".csv") else "text/plain",
        package_id, output_relative_path, payload, visibility, ceilings, access, lineage_parents=parents)
        for name, payload in zip(REPORT_MEMBERS, payloads, strict=True))
    current = read_reference_analysis(directory=directory, information_cutoff=information_cutoff, artifact_writer=artifact_writer)
    if (current.study != report.study or current.predictions != report.predictions or current.inquiry.state != report.work_state
            or current.inquiry.specification != report.inquiry_specification
            or tuple(sorted(current.producing_receipts, key=lambda row: row.receipt_id)) != report.producing_receipts):
        raise ValueError("report source, work or original custody changed before publication")
    publications = artifact_writer.write_batch(writes)
    return {"report": report.identity.to_document(), "package_id": package_id, "combined_milestone": report.milestone.status,
        "conditional_candidate_action": report.action.conditional_action, "biological_candidate_action": report.action.biological_action,
        "new_native_calls": 0, "paths": {name: str(artifact_writer.root.resolve(output_relative_path + "/" + name, for_write=False))
            for name in REPORT_MEMBERS}, "publications": [row.to_document() for row in publications]}
