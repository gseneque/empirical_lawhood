# SPDX-License-Identifier: MPL-2.0
"""Display original dependent opportunities without inventing independent units."""

from empirical_lawhood.api.application_presentations import ApplicationPresentation, PresentationData


def read(context, directory, artifact_writer):
    from empirical_lawhood.api.application_contracts import ApplicationError
    from empirical_lawhood.api.application_development import load_bounded_development
    from empirical_lawhood.api.assigned_opportunity_assessment import read_assigned_opportunity_result
    from empirical_lawhood.methods.assigned_opportunity_assessment.bindings import config_from_draft
    from empirical_lawhood.science.identity.provenance import ObjectIdentity

    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "The exposed opportunity view does not accept protected access selections.")
    def selected(draft):
        config_from_draft(draft)
        return True
    packet, draft, source, _ = load_bounded_development(directory=directory, plane=artifact_writer,
        maximum_draft_bytes=2*1024**2, accept_draft=selected)
    config, _ = config_from_draft(draft)
    report = read_assigned_opportunity_result(directory=directory, artifact_writer=artifact_writer)
    original = {**report, "author_contract": config.author.to_document(),
        "dependent_assessment_contract": config.assessment.to_document(), "source_contract": config.source.to_document()}
    identity = ObjectIdentity.from_record(packet.packet_id, packet).to_document()
    return PresentationData(identity, report["evidence_scope"],
        {key: value for key, value in report.items() if key != "opportunities"}, tuple(report.get("opportunities", ())),
        original, {"packet": identity, "implementation": packet.implementation.to_document(),
            "producing_git_head": source.observed_git_head, "dependency_lock_sha256": source.dependency_lock_sha256},
        "The complete assigned opportunity census retains its original dependence roots, stopping and missingness rules. Nested views are not independent units. Procedure, instance, admission and joined-use findings remain separate.")


APPLICATION_PRESENTATION = ApplicationPresentation("assigned-opportunity.findings", "1.0.0", "Dependent opportunity findings",
    "assigned-opportunity-assessment", "docs/development/inquiry-assessment-extensions.md",
    ("opportunity_id", "status", "independent_unit_id", "dependence_root", "views"), 16, read)
