# SPDX-License-Identifier: MPL-2.0
"""Cold scientific configuration for the exposed plant prediction precursor."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from . import records as r

ANALYSIS_UNIT_ID = "rubisco-plant-prediction.analysis.nine-mutants-one-diagnostic"
SOURCE_IDS = ("rubisco-iqbal2023-training-table", "rubisco-mcdonald2026-panel")


@dataclass(frozen=True, slots=True)
class PlantPredictionScienceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/scientific-design"
    science_id: str
    natural_table: ObjectIdentity
    plant_panel: ObjectIdentity
    protocol_sha256: str

    def __post_init__(self):
        if (self.science_id != r.PREFIX + ".scientific-design"
                or self.natural_table != r.natural_identity()
                or self.plant_panel != r.plant_identity()
                or self.protocol_sha256 != r.PROTOCOL_SHA256):
            raise ValueError("plant prediction changes its exact natural/plant source or frozen protocol")


@dataclass(frozen=True, slots=True)
class PlantPredictionSourceConfigV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/operations/source-config"
    config_id: str
    science: PlantPredictionScienceV1

    def __post_init__(self):
        validate_stable_id(self.config_id, field_name="config_id")
        if type(self.science) is not PlantPredictionScienceV1:
            raise ValueError("plant prediction requires its exact frozen typed scientific design")
        self.science.__post_init__()


@dataclass(frozen=True, slots=True)
class PlantPredictionConstructConfigV1(PlantPredictionSourceConfigV1):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/operations/construct-config"


@dataclass(frozen=True, slots=True)
class PlantPredictionEvaluateConfigV1(PlantPredictionSourceConfigV1):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/operations/evaluate-config"


@dataclass(frozen=True, slots=True)
class PlantPredictionAnalysisSystemV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/analysis-system"
    system_id: str
    science: ObjectIdentity
    natural_table: ObjectIdentity
    plant_panel: ObjectIdentity
    analysis_unit_id: str = ANALYSIS_UNIT_ID
    interpretation: str = "ONE_EXPOSED_ANALYTICAL_ASSESSMENT_NINE_FOCAL_ROWS_SIX_SITES_ONE_DIAGNOSTIC_UNKNOWN_BIOLOGICAL_N"

    def __post_init__(self):
        validate_stable_id(self.system_id, field_name="system_id")
        if (self.science.object_schema != PlantPredictionScienceV1.SCHEMA
                or self.natural_table != r.natural_identity()
                or self.plant_panel != r.plant_identity()
                or self.analysis_unit_id != ANALYSIS_UNIT_ID
                or self.interpretation != "ONE_EXPOSED_ANALYTICAL_ASSESSMENT_NINE_FOCAL_ROWS_SIX_SITES_ONE_DIAGNOSTIC_UNKNOWN_BIOLOGICAL_N"):
            raise ValueError("plant prediction changes its source identities or analytical denominator")
