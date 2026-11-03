"""Reported substitutions and endpoints with explicit information-role cuts.

These are adapter observations. A reported mutation is not a verified complete
construct, a table row is not an independent biological unit, and a point mean
does not supply a calibrated uncertainty distribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_ids,
    validate_decimal,
    validate_stable_id,
)

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"


@dataclass(frozen=True, slots=True)
class ReportedSubstitutionV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/reported-substitution"
    sample_id: str
    substitution: str

    def __post_init__(self) -> None:
        validate_stable_id(self.sample_id, field_name="sample_id")
        if self.substitution != "WT" and re.fullmatch(
            rf"[{AMINO_ACIDS}][1-9][0-9]{{0,3}}[{AMINO_ACIDS}]", self.substitution
        ) is None:
            raise ValueError("only a reported single substitution or WT is supported")
        if self.substitution != "WT" and self.substitution[0] == self.substitution[-1]:
            raise ValueError("substitution must change the reported residue")

    @property
    def position(self) -> int | None:
        return None if self.substitution == "WT" else int(self.substitution[1:-1])

    @property
    def ancestral_residue(self) -> str | None:
        return None if self.substitution == "WT" else self.substitution[0]

    @property
    def replacement_residue(self) -> str | None:
        return None if self.substitution == "WT" else self.substitution[-1]

    def vector(self) -> tuple[Decimal, ...]:
        """Frozen residue delta used by historical E1; position is not a feature."""
        if self.substitution == "WT":
            return (Decimal(0),) * 20
        return tuple(
            Decimal(int(a == self.replacement_residue) - int(a == self.ancestral_residue))
            for a in AMINO_ACIDS
        )


@dataclass(frozen=True, slots=True)
class ReportedEndpointsV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/reported-endpoints"
    sample_id: str
    turnover_s_inv: Decimal
    specificity_dimensionless: Decimal

    def __post_init__(self) -> None:
        validate_stable_id(self.sample_id, field_name="sample_id")
        for name in ("turnover_s_inv", "specificity_dimensionless"):
            value = validate_decimal(getattr(self, name), field_name=name)
            if value <= 0:
                raise ValueError("reported endpoints must be positive")


def _validate_slice(slice_id: str, fold_id: str, source: ObjectIdentity) -> None:
    validate_stable_id(slice_id, field_name="slice_id")
    validate_stable_id(fold_id, field_name="fold_id")
    if not isinstance(source, ObjectIdentity):
        raise ValueError("slice source must be an exact object identity")


@dataclass(frozen=True, slots=True)
class HistoricalTrainingSliceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-training-slice"
    slice_id: str
    fold_id: str
    source: ObjectIdentity
    features: tuple[ReportedSubstitutionV1, ...]
    endpoints: tuple[ReportedEndpointsV1, ...]

    def __post_init__(self) -> None:
        _validate_slice(self.slice_id, self.fold_id, self.source)
        for name in ("features", "endpoints"):
            require_sorted_unique_ids(getattr(self, name), attribute="sample_id", field_name=name)
        if not 1 <= len(self.features) <= 128 or tuple(f.sample_id for f in self.features) != tuple(
            e.sample_id for e in self.endpoints
        ):
            raise ValueError("training requires exact bounded feature/endpoint correspondence")


@dataclass(frozen=True, slots=True)
class HistoricalFeatureSliceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-feature-slice"
    slice_id: str
    fold_id: str
    source: ObjectIdentity
    features: tuple[ReportedSubstitutionV1, ...]

    def __post_init__(self) -> None:
        _validate_slice(self.slice_id, self.fold_id, self.source)
        require_sorted_unique_ids(self.features, attribute="sample_id", field_name="features")
        if not 1 <= len(self.features) <= 128:
            raise ValueError("feature slice exceeds its bound")


@dataclass(frozen=True, slots=True)
class HistoricalLabelSliceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical-label-slice"
    slice_id: str
    fold_id: str
    source: ObjectIdentity
    endpoints: tuple[ReportedEndpointsV1, ...]

    def __post_init__(self) -> None:
        _validate_slice(self.slice_id, self.fold_id, self.source)
        require_sorted_unique_ids(self.endpoints, attribute="sample_id", field_name="endpoints")
        if not 1 <= len(self.endpoints) <= 128:
            raise ValueError("label slice exceeds its bound")
