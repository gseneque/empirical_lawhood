# SPDX-License-Identifier: MPL-2.0
"""Declared finite selection operands; no source, inference or chronology warrant."""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from .experimental_design import UnitAllocation
from .provenance import ObjectIdentity
from .serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id


@dataclass(frozen=True, slots=True)
class DeclaredCandidate(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-selection/candidate"
    candidate_id: str
    family_id: str
    tuning: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.candidate_id)
        validate_stable_id(self.family_id)
        if type(self.tuning) is not ObjectIdentity:
            raise TypeError("selection candidate needs its immutable declared tuning")


@dataclass(frozen=True, slots=True)
class WholeUnitFold(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-selection/whole-unit-fold"
    unit_id: str
    fold: int

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        if type(self.fold) is not int or self.fold < 0:
            raise ValueError("selection fold requires a nonnegative whole-unit assignment")


@dataclass(frozen=True, slots=True)
class DeclaredSelectionDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-selection/design"
    design_id: str
    allocation: ObjectIdentity
    development_role: str
    candidates: tuple[DeclaredCandidate, ...]
    folds: tuple[WholeUnitFold, ...]
    fold_count: int
    maximum_fit_calls: int
    tie_order: tuple[str, ...]
    score_direction: str
    missing_policy: str
    target: ObjectIdentity
    criterion: ObjectIdentity
    features: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.design_id)
        validate_stable_id(self.development_role)
        if (type(self.allocation) is not ObjectIdentity or self.allocation.object_schema != UnitAllocation.SCHEMA
                or any(type(value) is not ObjectIdentity for value in (self.target, self.criterion, self.features))
                or type(self.candidates) is not tuple or not self.candidates
                or any(type(row) is not DeclaredCandidate for row in self.candidates)
                or tuple(row.candidate_id for row in self.candidates) != tuple(sorted({row.candidate_id for row in self.candidates}))
                or type(self.folds) is not tuple or not self.folds
                or any(type(row) is not WholeUnitFold for row in self.folds)
                or tuple(row.unit_id for row in self.folds) != tuple(sorted({row.unit_id for row in self.folds}))
                or type(self.fold_count) is not int or self.fold_count < 2
                or type(self.maximum_fit_calls) is not int or self.maximum_fit_calls < 1
                or type(self.tie_order) is not tuple or len(self.tie_order) != len(self.candidates)
                or set(self.tie_order) != {row.candidate_id for row in self.candidates}
                or self.score_direction not in ("MINIMIZE", "MAXIMIZE") or self.missing_policy != "REQUIRE_COMPLETE"):
            raise ValueError("selection needs a closed candidate/fold/budget/tie/target contract")
        for row in (*self.candidates, *self.folds):
            row.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.design_id, self)


@dataclass(frozen=True, slots=True)
class SelectionUnitScore(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-selection/unit-score"
    candidate_id: str
    unit_id: str
    fold: int
    value: Decimal | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.candidate_id)
        WholeUnitFold(self.unit_id, self.fold)
        require_sorted_unique_strings(self.reason_codes, field_name="selection missing reasons")
        if (self.value is not None and (type(self.value) is not Decimal or not self.value.is_finite())
                or (self.value is None) != bool(self.reason_codes)):
            raise ValueError("selection retains missing/nonfinite units explicitly without a finite score")


@dataclass(frozen=True, slots=True)
class CandidateSelectionSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-selection/candidate-summary"
    candidate_id: str
    assigned_units: int
    finite_units: int
    mean_numerator: int | None
    mean_denominator: int | None

    def __post_init__(self):
        validate_stable_id(self.candidate_id)
        if (type(self.assigned_units) is not int or self.assigned_units < 1
                or type(self.finite_units) is not int or not 0 <= self.finite_units <= self.assigned_units
                or (self.mean_numerator is None) != (self.finite_units != self.assigned_units)
                or (self.mean_numerator is None) != (self.mean_denominator is None)
                or self.mean_numerator is not None and (type(self.mean_numerator) is not int
                    or type(self.mean_denominator) is not int or self.mean_denominator < 1
                    or Fraction(self.mean_numerator, self.mean_denominator).denominator != self.mean_denominator)):
            raise ValueError("selection mean retains its exact complete-unit denominator")

    @property
    def mean(self):
        return None if self.mean_numerator is None else Fraction(self.mean_numerator, self.mean_denominator)


@dataclass(frozen=True, slots=True)
class DeclaredSelectionResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-selection/result"
    result_id: str
    design: ObjectIdentity
    allocation: ObjectIdentity
    scores: tuple[SelectionUnitScore, ...]
    summaries: tuple[CandidateSelectionSummary, ...]
    selected_candidate_id: str | None
    fit_calls: int

    def __post_init__(self):
        validate_stable_id(self.result_id)
        if (type(self.design) is not ObjectIdentity or self.design.object_schema != DeclaredSelectionDesign.SCHEMA
                or type(self.allocation) is not ObjectIdentity or self.allocation.object_schema != UnitAllocation.SCHEMA
                or type(self.scores) is not tuple or not self.scores or any(type(row) is not SelectionUnitScore for row in self.scores)
                or tuple((row.candidate_id, row.unit_id) for row in self.scores)
                    != tuple(sorted({(row.candidate_id, row.unit_id) for row in self.scores}))
                or type(self.summaries) is not tuple or not self.summaries
                or any(type(row) is not CandidateSelectionSummary for row in self.summaries)
                or tuple(row.candidate_id for row in self.summaries) != tuple(sorted({row.candidate_id for row in self.summaries}))
                or self.selected_candidate_id is not None and self.selected_candidate_id not in {row.candidate_id for row in self.summaries}
                or type(self.fit_calls) is not int or self.fit_calls < 0):
            raise ValueError("selection result changes its complete actual candidate/unit census")
        for row in (*self.scores, *self.summaries):
            row.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id, self)


@dataclass(frozen=True, slots=True)
class DeclaredSelectionFreeze(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/experimental-selection/freeze"
    freeze_id: str
    design: ObjectIdentity
    allocation: ObjectIdentity
    selection: ObjectIdentity
    fitted_model: ObjectIdentity
    target: ObjectIdentity
    criterion: ObjectIdentity
    features: ObjectIdentity
    revision_number: int

    def __post_init__(self):
        validate_stable_id(self.freeze_id)
        if (any(type(row) is not ObjectIdentity for row in (self.design, self.allocation, self.selection,
                    self.fitted_model, self.target, self.criterion, self.features))
                or self.design.object_schema != DeclaredSelectionDesign.SCHEMA
                or self.allocation.object_schema != UnitAllocation.SCHEMA
                or self.selection.object_schema != DeclaredSelectionResult.SCHEMA
                or type(self.revision_number) is not int or self.revision_number != 1):
            raise ValueError("selection freeze retains one original development revision and its exact operands")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.freeze_id, self)
