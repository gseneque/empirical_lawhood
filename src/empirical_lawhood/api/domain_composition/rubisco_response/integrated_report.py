# SPDX-License-Identifier: MPL-2.0
"""Guarded integrated report reading and atomic, explicitly selected export."""

from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_response.integrated_report import build_integrated_report
from empirical_lawhood.domains.rubisco.rubisco_response.integrated_rendering import render_comparison_csv, render_cost_csv, render_decision_csv, render_integrated_attempts, render_integrated_endpoints, render_integrated_parameters, render_integrated_report, render_requirement_csv
from empirical_lawhood.domains.rubisco.rubisco_response.report_rendering import render_reference_report
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, derived_outcome_access, lineage_parent_sort_key
from empirical_lawhood.api.domain_composition.rubisco_response.comparison import read_comparison_analysis
from empirical_lawhood.api.domain_composition.rubisco_response.report import _lineage

REPORT_MEMBERS = ("readout.json", "report.txt", "reference-report.txt", "endpoints.csv", "parameters.csv",
    "comparison.csv", "decisions.csv", "attempts.csv", "costs.csv", "requirements.csv")


def read_integrated_report(*, design, arm_directories, information_cutoff, artifact_writer,
                           decision_directories=None, source_audit=None, nomination_dossier=None, nomination_receipt=None):
    """Authenticate actual original arms/decisions and independently compose findings.

    This entrypoint accepts the current exposed report route. Actual molecular
    preparation has no authenticated input on this route and stays missing.
    Its presence cannot be claimed by supplying an unguarded record here.
    """
    comparison = read_comparison_analysis(design=design, arm_directories=arm_directories,
        information_cutoff=information_cutoff, artifact_writer=artifact_writer, decision_directories=decision_directories,
        source_audit=source_audit, nomination_dossier=nomination_dossier, nomination_receipt=nomination_receipt)
    return build_integrated_report(comparison, report_id="report.rubisco-integrated." + comparison.fingerprint())


def _parents(report, nomination_receipt):
    parents = [parent for arm in report.comparison.arms if arm.report is not None
        for parent in _lineage(arm.report, nomination_receipt)]
    for decision in report.comparison.decisions:
        # The shared InquiryEvidence type fixes this route to development-visible
        # evidence. Preserve every original stock restriction and packet binding.
        parents.extend(ArtifactLineageParent(row.product, row.visibility_ceiling, row.outcome_access) for row in decision.state.stock)
        parents.extend(ArtifactLineageParent(pin, VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
            for pin in (decision.identity, ObjectIdentity.from_record(decision.packet.packet_id, decision.packet)))
    return tuple(sorted(set(parents), key=lineage_parent_sort_key))


def export_integrated_report(*, output_relative_path, design, arm_directories, information_cutoff, artifact_writer,
                             decision_directories=None, source_audit=None, nomination_dossier=None, nomination_receipt=None):
    """Revalidate every original source and decision before atomic publication."""
    validate_relative_locator(output_relative_path)
    for name in REPORT_MEMBERS:
        artifact_writer.root.resolve(output_relative_path + "/" + name, for_write=True)
    inputs = dict(design=design, arm_directories=arm_directories, information_cutoff=information_cutoff,
        artifact_writer=artifact_writer, decision_directories=decision_directories, source_audit=source_audit,
        nomination_dossier=nomination_dossier, nomination_receipt=nomination_receipt)
    report = read_integrated_report(**inputs)
    projections = (render_integrated_report(report), render_reference_report(report.reference),
        render_integrated_endpoints(report), render_integrated_parameters(report), render_comparison_csv(report),
        render_decision_csv(report), render_integrated_attempts(report), render_cost_csv(report), render_requirement_csv(report))
    payloads = (report.canonical_bytes(), *(value.encode("utf-8") for value in projections))
    parents = _parents(report, nomination_receipt)
    ceilings = tuple(row.visibility_ceiling for row in parents)
    access = derived_outcome_access(OutcomeAccess.DEVELOPMENT_VISIBLE, *(row.outcome_access for row in parents))
    visibility = inherited_visibility((VisibilityCeiling.DEVELOPMENT_ONLY, *ceilings), access)
    package_id = "report-package.rubisco-integrated." + sha256(b"".join(sha256(payload).digest() for payload in payloads)).hexdigest()
    writes = tuple(ArtifactWriteRequest("integrated-report-member." + sha256(payload).hexdigest() + "." + name.replace(".", "-"),
        output_relative_path + "/" + name, report.SCHEMA if name == "readout.json" else
        "empirical-lawhood/rubisco-response/integrated-" + name.replace(".", "-"),
        ArtifactProfile.CANONICAL_JSON if name == "readout.json" else ArtifactProfile.TEXT_PARAMETERS,
        "application/json" if name == "readout.json" else "text/csv" if name.endswith(".csv") else "text/plain",
        package_id, output_relative_path, payload, visibility, ceilings, access, lineage_parents=parents)
        for name, payload in zip(REPORT_MEMBERS, payloads, strict=True))
    current = read_comparison_analysis(**inputs)
    if current != report.comparison:
        raise ValueError("integrated report original source, decision or custody changed before publication")
    publications = artifact_writer.write_batch(writes)
    return {"report": report.identity.to_document(), "package_id": package_id,
        "conditional_candidate_action": report.reference.action.conditional_action,
        "biological_candidate_action": report.reference.action.biological_action,
        "combined_milestone": report.milestone.status, "native_entry_status": report.native_entry_status,
        "new_native_calls": 0, "paths": {name: str(artifact_writer.root.resolve(output_relative_path + "/" + name, for_write=False))
            for name in REPORT_MEMBERS}, "publications": [row.to_document() for row in publications]}
