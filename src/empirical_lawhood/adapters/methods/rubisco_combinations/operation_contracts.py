# SPDX-License-Identifier: MPL-2.0
"""Frozen inputs for the exposed Wilson combination diagnostic stages."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.adapters.physical.rubisco_kinetics.genbank import NativeTeParentConstructV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import WilsonMutantPanelV1

from .records import CombinationScienceV1

ANALYSIS_UNIT_ID = "rubisco-combinations.analysis.a398t-a48v"


@dataclass(frozen=True, slots=True)
class CombinationSourceConfigV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/operations/source-config"
    config_id: str
    science: CombinationScienceV1

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        if not isinstance(self.science, CombinationScienceV1):
            raise ValueError("combination stage requires its exact typed frozen scientific design")


@dataclass(frozen=True, slots=True)
class CombinationPredictConfigV1(CombinationSourceConfigV1):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/operations/predict-config"


@dataclass(frozen=True, slots=True)
class CombinationCommitConfigV1(CombinationSourceConfigV1):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/operations/commit-config"


@dataclass(frozen=True, slots=True)
class CombinationEvaluateConfigV1(CombinationSourceConfigV1):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/operations/evaluate-config"


@dataclass(frozen=True, slots=True)
class CombinationAnalysisSystemV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/analysis-system"
    system_id: str
    science: ObjectIdentity
    source_panel: ObjectIdentity
    parent: ObjectIdentity
    analysis_unit_id: str = ANALYSIS_UNIT_ID
    interpretation: str = "FOUR_EXPOSED_SOURCE_CORNERS_ONE_SOFTWARE_DIAGNOSTIC_NO_BIOLOGICAL_N"

    def __post_init__(self) -> None:
        validate_stable_id(self.system_id, field_name="system_id")
        if (self.science.object_schema != CombinationScienceV1.SCHEMA
                or self.source_panel.object_schema != WilsonMutantPanelV1.SCHEMA
                or self.parent.object_schema != NativeTeParentConstructV1.SCHEMA
                or self.analysis_unit_id != ANALYSIS_UNIT_ID
                or self.interpretation != "FOUR_EXPOSED_SOURCE_CORNERS_ONE_SOFTWARE_DIAGNOSTIC_NO_BIOLOGICAL_N"):
            raise ValueError("combination analytical system changes exact source/parent identity or diagnostic census")
