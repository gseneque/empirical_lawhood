"""Cold frozen historical-operation inputs and analytical system identity.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id

from .records import HistoricalScienceV1


def analysis_unit_id(fold_id: str) -> str:
    validate_stable_id(fold_id, field_name="fold_id")
    return f"rubisco-historical.analysis.{fold_id}"


@dataclass(frozen=True, slots=True)
class HistoricalFitConfigV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/operations/fit-config"
    config_id: str
    science: HistoricalScienceV1
    fold_id: str

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        validate_stable_id(self.fold_id, field_name="fold_id")
        if not isinstance(self.science, HistoricalScienceV1) or self.fold_id not in {f.fold_id for f in self.science.folds}:
            raise ValueError("historical operation changes its typed scientific design or fold")


@dataclass(frozen=True, slots=True)
class HistoricalPredictConfigV1(HistoricalFitConfigV1):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/operations/predict-config"


@dataclass(frozen=True, slots=True)
class HistoricalCommitConfigV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/operations/commit-config"
    config_id: str
    science: HistoricalScienceV1

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        if not isinstance(self.science, HistoricalScienceV1):
            raise ValueError("historical operation requires its typed complete scientific design")


@dataclass(frozen=True, slots=True)
class HistoricalEvaluateConfigV1(HistoricalCommitConfigV1):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/operations/evaluate-config"


@dataclass(frozen=True, slots=True)
class HistoricalAnalysisSystemV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/analysis-system"
    system_id: str
    science: ObjectIdentity
    source: ObjectIdentity
    analysis_unit_ids: tuple[str, ...]
    interpretation: str = "SOFTWARE_TABLE_REANALYSIS_CASES_NOT_BIOLOGICAL_REPLICATES"

    def __post_init__(self) -> None:
        validate_stable_id(self.system_id, field_name="system_id")
        if (not isinstance(self.science, ObjectIdentity) or self.science.object_schema != HistoricalScienceV1.SCHEMA
            or not isinstance(self.source, ObjectIdentity)):
            raise ValueError("historical analytical system needs exact science and original source identities")
        require_sorted_unique_strings(self.analysis_unit_ids, field_name="analysis_unit_ids", allow_empty=False)
        if len(self.analysis_unit_ids) > 5 or any(not u.startswith("rubisco-historical.analysis.") for u in self.analysis_unit_ids):
            raise ValueError("historical analytical system exceeds its declared analysis-case roster")
        if self.interpretation != "SOFTWARE_TABLE_REANALYSIS_CASES_NOT_BIOLOGICAL_REPLICATES":
            raise ValueError("historical analysis cases cannot become biological replicates")
