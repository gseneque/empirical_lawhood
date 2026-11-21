"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from hashlib import sha256
from pathlib import PurePosixPath
import tarfile
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.domains.materials.superconductivity.workflow_contracts import MaterialControlWorkflowProfile, WorkflowKind, WorkflowSource
from empirical_lawhood.adapters.simulators.ambient_pressure_superconductor.material_control_source import _external_path, CONTROL_INPUT_ARCHIVE, TUTORIAL_ARCHIVE, TUTORIAL_ARCHIVE_SHA256
from empirical_lawhood._required_inputs import required_external_sha256

def profile_source_identity(profile: MaterialControlWorkflowProfile) -> tuple[str, str, str]:
    archive_relative = (
        TUTORIAL_ARCHIVE
        if profile.source is WorkflowSource.EPW_SUPERCONDUCTING_REFERENCE
        else CONTROL_INPUT_ARCHIVE
    )
    archive_path = _external_path(archive_relative)
    source_sha = (
        TUTORIAL_ARCHIVE_SHA256
        if profile.source is WorkflowSource.EPW_SUPERCONDUCTING_REFERENCE
        else required_external_sha256(
            'EMPIRICAL_LAWHOOD_MATERIAL_CONTROL_CONTROL_INPUT_ARCHIVE_SHA256'
        )
    )
    rows: list[tuple[str, int, str]] = []
    primary_payload: bytes | None = None
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive:
            if not member.isfile():
                continue
            path = PurePosixPath(member.name)
            selected = (
                profile.source is WorkflowSource.SSSP_CONTROL
                and profile.source_root == "/".join(path.parts[:3])
            ) or (
                profile.source is WorkflowSource.EPW_SUPERCONDUCTING_REFERENCE
                and path.parts[:2]
                == (
                    "tutorial04",
                    "exercise1" if profile.prefix == "pb" else "exercise2",
                )
            )
            if not selected:
                continue
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError('material control profile source member cannot be read')
            payload = stream.read(member.size + 1)
            if len(payload) != member.size:
                raise ValueError('material control profile source member size differs')
            digest = sha256(payload).hexdigest()
            rows.append((member.name, member.size, digest))
            if path.name == "scf.in" and (
                "phonon" in path.parts
                or (
                    profile.kind is WorkflowKind.SCF_CLASS and path.parent.name == "scf"
                )
            ):
                primary_payload = payload
    if not rows or primary_payload is None:
        raise ValueError('material control profile source members are incomplete')
    preparation_sha = sha256(canonical_json_bytes(tuple(sorted(rows)))).hexdigest()
    return source_sha, sha256(primary_payload).hexdigest(), preparation_sha
