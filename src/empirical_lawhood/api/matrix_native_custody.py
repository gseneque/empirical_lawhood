# SPDX-License-Identifier: MPL-2.0
"""Bounded development-native publication through the existing artifact plane.

These operations create actual receipts for completed numerical effects.  They
convey no prospective issue, execution or reveal authority.  An unreceipted
partial publication refuses recovery rather than repeating an uncertain effect.
"""

from hashlib import sha256
from importlib.resources import files
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.storage.artifacts import ExternalArtifactPlane
from empirical_lawhood.storage.development_native_custody import DevelopmentNativeCustody, preflight_development_native_store, read_development_native_payload
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest


def read_matrix_native_payload(writer: ExternalArtifactPlane, manifest: ArtifactManifest, *, maximum_bytes: int) -> bytes:
    return read_development_native_payload(writer, manifest, maximum_bytes=maximum_bytes)


def preflight_matrix_native_store(writer: ExternalArtifactPlane, *, minimum_free_bytes: int) -> None:
    preflight_development_native_store(writer, minimum_free_bytes=minimum_free_bytes)


@dataclass(frozen=True, slots=True)
class MatrixNativeEffectInput(CanonicalRecord):
    """Persisted contact boundary, not completion or retry permission."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-native/effect-input"
    run_id: str
    task_id: str
    configuration: ObjectIdentity


@dataclass(frozen=True, slots=True)
class MatrixNativeRuntimeObservation(CanonicalRecord):
    """Actual native-entry observation, retained separately from source/lock identities."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-native/runtime-observation"
    observation_json: str

    def __post_init__(self):
        from empirical_lawhood.domains.matrix.matrix_response_study.numerical_runtime import validate_matrix_runtime_observation_json
        validate_matrix_runtime_observation_json(self.observation_json)


def _immutable_json(value):
    if isinstance(value, (list, tuple)):
        return tuple(_immutable_json(item) for item in value)
    if isinstance(value, dict):
        return {key: _immutable_json(item) for key, item in value.items()}
    return value


def retain_matrix_native_runtime(custody, observation):
    record = MatrixNativeRuntimeObservation(canonical_json_bytes(_immutable_json(observation)).decode())
    existing = custody.load("runtime-observation", MatrixNativeRuntimeObservation)
    if existing is None:
        custody.retain("runtime-observation", record)
    elif existing != record:
        raise ValueError("Matrix native recovery runtime differs from its actual retained observation")



def matrix_scientific_code_sha256() -> str:
    """Exact scientific owner subset, distinct from a full checkout closure."""
    owners = ('domains/matrix/matrix_response_study/anisotropic_feasibility.py', 'domains/matrix/matrix_response_study/geometry_inputs.py', 'domains/matrix/matrix_response_study/numerical_qualification.py', 'domains/matrix/matrix_response_study/scientific_seed_inputs.py', 'domains/matrix/matrix_response_study/contracts.py', 'domains/matrix/matrix_response_study/shooting_committor.py', 'domains/matrix/matrix_response_study/authoring/design.py', 'domains/matrix/matrix_response_study/selected_event_inputs.py', 'domains/matrix/six_matrix_response/contracts.py', 'domains/matrix/six_matrix_response/history_preparation.py', 'domains/matrix/six_matrix_response/scientific_inputs.py', 'adapters/simulators/six_matrix_response/provider.py', 'adapters/simulators/six_matrix_response/extension.py', 'domains/matrix/six_matrix_response/shooting.py', 'domains/matrix/six_matrix_response/simulation.py', 'domains/matrix/six_matrix_response/gradients.py', 'domains/matrix/six_matrix_response/spectral.py', 'domains/matrix/six_matrix_response/model.py', 'storage/development_native_custody.py', 'api/matrix_native_custody.py', 'api/matrix_geometry.py', 'api/selected_events.py')
    owners = (*owners,
        "domains/matrix/matrix_response_study/geometry_records.py",
        "domains/matrix/matrix_response_study/selected_event_records.py",
        "domains/matrix/matrix_response_study/selected_event_analysis.py")
    package = files("empirical_lawhood")
    rows = []
    for owner in owners:
        digest = sha256()
        total_bytes = 0
        with package.joinpath(owner).open("rb") as stream:
            while chunk := stream.read(65536):
                total_bytes += len(chunk)
                if total_bytes > 16 * 1024**2:
                    raise ValueError("Matrix scientific source owner exceeds its exact byte bound")
                digest.update(chunk)
        rows.append((owner, digest.hexdigest()))
    return sha256(canonical_json_bytes(tuple(rows))).hexdigest()


class MatrixNativeCustody(DevelopmentNativeCustody):
    """Matrix-specific effect markers over the shared native custody lifecycle."""

    effect_input_type = MatrixNativeEffectInput
