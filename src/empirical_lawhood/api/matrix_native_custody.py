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

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.development_native_custody import (
    DevelopmentNativeCustody, preflight_development_native_store, read_development_native_payload,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactManifest


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
        from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import (
            validate_matrix_runtime_observation_json,
        )
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
    owners = (
        "adapters/methods/matrix_response_study/anisotropic_feasibility.py",
        "adapters/methods/matrix_response_study/geometry_inputs.py",
        "adapters/methods/matrix_response_study/numerical_qualification.py",
        "adapters/methods/matrix_response_study/scientific_seed_inputs.py",
        "adapters/methods/matrix_response_study/contracts.py",
        "adapters/methods/matrix_response_study/shooting_committor.py",
        "adapters/composition/matrix_response_study/design.py",
        "adapters/composition/matrix_response_study/selected_event_inputs.py",
        "adapters/simulators/six_matrix_response/contracts.py",
        "adapters/simulators/six_matrix_response/history_preparation.py",
        "adapters/simulators/six_matrix_response/scientific_inputs.py",
        "adapters/simulators/six_matrix_response/provider.py",
        "adapters/simulators/six_matrix_response/executable_binding.py",
        "adapters/simulators/six_matrix_response/extension_bundle.py",
        "adapters/simulators/six_matrix_response/shooting.py",
        "adapters/simulators/six_matrix_response/simulation.py",
        "adapters/simulators/six_matrix_response/gradients.py",
        "adapters/simulators/six_matrix_response/spectral.py",
        "adapters/simulators/six_matrix_response/model.py",
        "infrastructure/development_native_custody.py",
        "api/matrix_native_custody.py", "api/matrix_geometry.py", "api/selected_events.py",
    )
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
    """Matrix compatibility wrapper preserving exact historical marker bytes."""

    effect_input_type = MatrixNativeEffectInput
