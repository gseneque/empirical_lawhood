# SPDX-License-Identifier: MPL-2.0
"""Bounded original mass-balance findings; all scientific meaning stays with its reader."""

from empirical_lawhood.api.application_presentations import ApplicationPresentation, PresentationData


def read(context, directory, artifact_writer):
    from empirical_lawhood.api.application_contracts import ApplicationError
    from empirical_lawhood.api.application_development import load_bounded_development
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.methods.mass_balance_starter.records import MAX_BYTES, NAMESPACE, MassSpecification
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.science.identity.provenance import ObjectIdentity

    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "The exposed starter view does not accept protected access selections.")
    def selected(draft):
        return len(draft.operations) == 2 and {
            (row.selection.capability_key, row.selection.capability_version) for row in draft.operations
        } == {(NAMESPACE + ".assess", "1.0.0"), (NAMESPACE + ".predict", "1.0.0")}
    packet, _, source, payloads = load_bounded_development(directory=directory, plane=artifact_writer,
        maximum_draft_bytes=1024**2, accept_draft=selected)
    raw = payloads["experiment-specification.json"]
    decode_canonical_bytes(raw, MassSpecification, maximum_bytes=MAX_BYTES)
    report = read_recursive_wave(directory=directory, artifact_writer=artifact_writer,
        expected_specification_bytes=raw, terminal_product_format="documents")
    science = report["scientific_result"]
    identity = ObjectIdentity.from_record(packet.packet_id, packet).to_document()
    return PresentationData(identity, science["evidence_scope"],
        {key: value for key, value in science.items() if key != "findings"}, tuple(science.get("findings", ())),
        science, {"packet": identity, "implementation": packet.implementation.to_document(),
            "producing_git_head": source.observed_git_head, "dependency_lock_sha256": source.dependency_lock_sha256},
        "Exact original mass values in kg. Missing observations remain unevaluable; execution and forecast supply do not establish the claim.")


APPLICATION_PRESENTATION = ApplicationPresentation("mass-balance.findings", "1.0.0", "Mass-balance findings",
    "mass-balance-starter", "docs/development/mass-balance-starter.md",
    ("unit_id", "predicted_kg", "observed_kg", "absolute_error_kg", "disposition"), 16, read)
