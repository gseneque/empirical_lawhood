# SPDX-License-Identifier: MPL-2.0
"""A bounded development selection through the existing packet and source owners."""

from pathlib import Path

from empirical_lawhood.api.application_contracts import ApplicationError


def load_bounded_development(*, directory, plane, maximum_draft_bytes, accept_draft,
        refusal_code="UNSUPPORTED_BOUNDED_DEVELOPMENT_SELECTION"):
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.storage.recursive_custody import read_recursive_bootstrap_record
    from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave

    relative = Path(directory).relative_to(plane.root.contract.canonical_path).as_posix()
    packet = read_recursive_bootstrap_record(plane, relative + "/authored-wave.json", AuthoredRecursiveWave)
    member = next(row for row in packet.members if row.filename == "draft.json")
    if member.size_bytes > maximum_draft_bytes:
        raise ApplicationError(refusal_code, "The selected draft exceeds this bounded presentation route.")
    result = load_authored_wave(directory=directory, artifact_writer=plane, lazy_payloads=True)
    draft = result[1]
    if draft.development_study is None or draft.prospective_draft is not None or not accept_draft(draft):
        raise ApplicationError(refusal_code, "Select the declared exposed development wave for this route.")
    return result
