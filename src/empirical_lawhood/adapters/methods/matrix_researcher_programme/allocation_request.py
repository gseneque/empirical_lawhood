# SPDX-License-Identifier: MPL-2.0
"""Copied source-allocation choices, separate from scientific design and results."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding


@dataclass(frozen=True, slots=True)
class MatrixProgrammeAllocationRequest(CanonicalRecord):
    """Explicit pre-acquisition materials; no allocation, publication or authority."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-programme/allocation-request"
    record_id: str
    namespace: str
    scientific_design: ObjectIdentity
    exposure_census: ObjectIdentity
    root_seed_material_sha256: str
    future_seed_material_sha256: str
    e4_streams: SelectedE4StreamRecipe
    e5_root_seed_material_sha256: str
    e5_future_seed_material_sha256: str
    files: tuple[ExperimentFileInputBinding, ...]
    metadata_budget: ResourceBudget

    def __post_init__(self):
        from .scientific_design import MatrixProgrammeScientificDesign
        validate_stable_id(self.record_id)
        validate_stable_id(self.namespace)
        for reference, kind in ((self.scientific_design, MatrixProgrammeScientificDesign),
                (self.exposure_census, MatrixFactorExposureCensus)):
            if (type(reference) is not ObjectIdentity or (reference.object_schema, reference.object_version) !=
                    (kind.SCHEMA, kind.VERSION)):
                raise TypeError("programme allocation requires its exact scientific design and current exposure census")
            reference.__post_init__()
        if type(self.e4_streams) is not SelectedE4StreamRecipe or type(self.metadata_budget) is not ResourceBudget:
            raise TypeError("programme allocation requires explicit stream construction and metadata resources")
        self.e4_streams.__post_init__()
        self.metadata_budget.__post_init__()
        materials = (self.root_seed_material_sha256, self.future_seed_material_sha256,
            self.e4_streams.prefix_seed_material_sha256, self.e4_streams.future_seed_material_sha256,
            self.e5_root_seed_material_sha256, self.e5_future_seed_material_sha256)
        if self.e4_streams.family_seed_material_sha256 is not None:
            materials = (*materials, self.e4_streams.family_seed_material_sha256)
        for value in materials:
            validate_sha256(value)
        if len(set(materials)) != len(materials):
            raise ValueError("programme source and future stream materials must all differ")
        if (type(self.files) is not tuple or not self.files
                or any(type(value) is not ExperimentFileInputBinding for value in self.files)
                or tuple(value.identity.artifact_id for value in self.files) !=
                    tuple(sorted({value.identity.artifact_id for value in self.files}))):
            raise ValueError("programme allocation requires its exact sorted original support FILE operands")
        for value in self.files:
            value.__post_init__()
        if any(type(getattr(self.metadata_budget, name)) is not int or getattr(self.metadata_budget, name) < 1
                for name in ("memory_bytes", "source_scan_bytes", "output_bytes")):
            raise ValueError("programme allocation requires finite positive memory, source-scan and publication byte ceilings")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
