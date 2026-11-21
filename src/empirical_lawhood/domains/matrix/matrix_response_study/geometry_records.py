# SPDX-License-Identifier: MPL-2.0
"""Scientific geometry scan inputs and finite output constraints."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest
from empirical_lawhood.domains.matrix.six_matrix_response.contracts import SixMatrixResponseSixMatrixSourceConfig
from empirical_lawhood.domains.matrix.matrix_response_study.geometry_inputs import MatrixGeometryAllocation, validate_geometry_source

MATRIX_GEOMETRY_INPUT_MAXIMUM_BYTES = 8 * 1024**2
MATRIX_GEOMETRY_RESULT_MAXIMUM_BYTES = 64 * 1024**2


@dataclass(frozen=True, slots=True)
class MatrixGeometryScanInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-geometry/scan-input"
    config_id: str
    allocation: MatrixGeometryAllocation
    source: SixMatrixResponseSixMatrixSourceConfig
    scientific_code_sha256: str
    environment_lock_sha256: str
    numerical_qualification: ArtifactManifest | None = None
    workers: int = 1
    minimum_free_bytes: int = 1024**3
    maximum_output_bytes: int = MATRIX_GEOMETRY_RESULT_MAXIMUM_BYTES

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        validate_geometry_source(self.source)
        for name in ("scientific_code_sha256", "environment_lock_sha256"):
            validate_sha256(getattr(self, name), field_name=name)
        if type(self.workers) is not int or not 1 <= self.workers <= self.source.maximum_worker_processes:
            raise ValueError("Geometry worker count exceeds its existing source contract")
        if self.minimum_free_bytes < 1 or self.maximum_output_bytes != MATRIX_GEOMETRY_RESULT_MAXIMUM_BYTES:
            raise ValueError("Geometry operation lacks its bounded output/free-space contract")

    @property
    def run_id(self) -> str:
        return f"matrix-geometry.run-{self.fingerprint()[:32]}"

