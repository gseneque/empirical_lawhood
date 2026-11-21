# SPDX-License-Identifier: MPL-2.0
"""Join selected Rubisco audit attachments to freshly authenticated originals."""

from empirical_lawhood.science.records.decoding import decode_canonical_record
from empirical_lawhood.science.records.serialization import canonical_json_document_bytes
from decimal import Decimal
from contextlib import ExitStack
from pathlib import Path


def read_assessment(selected, *, primary, artifact_writer):
    """Read the separate closed export through its original complete source guard."""
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
    from empirical_lawhood.api.domain_composition.rubisco_response.initial_model import InitialModelSource
    from empirical_lawhood.api.domain_composition.rubisco_response.initial_root import read_initial_root_export
    with ExitStack() as stack:
        owners, sources = {}, []
        for row in selected.get("sources", ()):
            contract = decode_canonical_record(row["contract"], ExternalRootContract)
            key = contract.canonical_bytes()
            if key not in owners:
                plane = ExternalArtifactPlane(GuardedExternalRoot(contract), validators=integration_artifact_profile_validators())
                plane.root.verify(for_write=False)
                owners[key] = stack.enter_context(plane.read_context())
            sources.append(InitialModelSource(decode_canonical_record(row["identity"], ObjectIdentity),
                owners[key], row["relative_path"]))
        relative = Path(selected["directory"]).relative_to(artifact_writer.root.contract.canonical_path).as_posix()
        read = read_initial_root_export(directory_relative_path=relative, sources=tuple(sources), artifact_writer=artifact_writer)
        if (read["assessment"].identity.to_document() != selected["identity"]
                or read["result"].to_document() != primary.original_report["result"]):
            raise PermissionError("standalone assessment substitutes the original paired root result")
        result = {"scope": "SEPARATE_CLOSED_STANDALONE_ASSESSMENT", "verification": read["verification"],
            "identity": read["assessment"].identity.to_document(), "new_native_calls": 0,
            "records": {name: value.to_document() for name, value in read.items() if hasattr(value, "to_document")},
            "canonical_text": read["assessment"].canonical_bytes().decode()}
        for owner in owners.values():
            owner.require_verification_snapshot()
        return result


def _retained_summary(value):
    """Match the historical readout's exact Decimal-string JSON convention."""
    if isinstance(value, Decimal):
        return str(value)
    if type(value) in (list, tuple):
        return [_retained_summary(item) for item in value]
    if type(value) is dict:
        return {key: _retained_summary(item) for key, item in value.items()}
    return value


def validate_attachment(role, attachment, *, primary, cost):
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_records import InitialRootResult, InitialRootScopedAssessment
    from empirical_lawhood.domains.rubisco.rubisco_response.initial_root_requirements import InitialRootRequirementGraph
    original = primary.original_report
    result = decode_canonical_record(original["result"], InitialRootResult)
    assessment = decode_canonical_record(original["assessment"], InitialRootScopedAssessment)
    graph = decode_canonical_record(original["requirement_graph"], InitialRootRequirementGraph)
    if role == "acquisition":
        if cost is None or any(attachment.get(name) != value for name, value in (
                ("root", result.identity.to_document()), ("assessment", assessment.assessment.identity.to_document()),
                ("requirement_graph", graph.identity.to_document()), ("measured_work_account", cost["account"].identity.to_document()),
                ("joint_outcome", result.joint_outcome))):
            raise PermissionError("acquisition attachment changes its original root, graph, assessment or cost account")
    elif role == "cost-observations":
        if (cost is None or attachment.get("root_outcome") != result.joint_outcome
                or canonical_json_document_bytes(attachment.get("cost_account", {}).get("summary"))
                != canonical_json_document_bytes(_retained_summary(cost["summary"]))):
            raise PermissionError("cost attachment changes its original root or reconstructed work summary")
    elif role == "assessment":
        # A checksum alone cannot establish a separately exported scientific
        # assessment. This route does not replace read_initial_root_export.
        raise ValueError("use the original standalone assessment reader with its complete original sources")
    elif role == "methods":
        if attachment.get("scope") != "RETAINED_AUDIT_METHOD_OBSERVATION" or attachment.get("root") != result.identity.to_document():
            raise PermissionError("method observation omits its original root and declared audit scope")
    else:
        raise ValueError("this domain has no attachment projection for the selected role")

