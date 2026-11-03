# SPDX-License-Identifier: MPL-2.0
"""Finite whole-unit selection, independent of model fitting and source science.

A fit call is one declared candidate/fold bundle. Nested targets/views are the
domain's fixed bundle, never more independent units. Complete-unit arithmetic
uses exact Fractions; no IID, inference, exposure or chronological authority is
deduced from these records. Actual freeze-before-future ordering is a registered
graph and custody obligation.
"""

from decimal import Decimal
from fractions import Fraction
from typing import Protocol

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.experimental_selection import (
    CandidateSelectionSummary, DeclaredCandidate, DeclaredSelectionDesign, DeclaredSelectionFreeze,
    DeclaredSelectionResult, SelectionUnitScore,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity


class CandidateFoldFitter(Protocol):
    """A domain fitter returns the complete declared heldout whole-unit census."""
    def __call__(self, *, candidate: DeclaredCandidate, fold: int,
                 training_unit_ids: tuple[str, ...], heldout_unit_ids: tuple[str, ...]) -> tuple[SelectionUnitScore, ...]: ...


def validate_selection_design(design: DeclaredSelectionDesign, allocation: UnitAllocation) -> tuple[str, ...]:
    if type(design) is not DeclaredSelectionDesign or type(allocation) is not UnitAllocation:
        raise TypeError("selection requires its typed design and original allocation")
    design.__post_init__()
    allocation.__post_init__()
    units = allocation.unit_ids(design.development_role)
    if (design.allocation != allocation.identity or not units
            or tuple(row.unit_id for row in design.folds) != units
            or {row.fold for row in design.folds} != set(range(design.fold_count))
            or design.maximum_fit_calls < len(design.candidates) * design.fold_count + 1):
        raise ValueError("selection changes exact development units, whole folds or finite fitting budget")
    return units


def selection_score(candidate_id: str, unit_id: str, fold: int, value: Decimal | None) -> SelectionUnitScore:
    """Keep absent/nonfinite whole-unit scores as explicit unevaluable outcomes."""
    if value is None:
        return SelectionUnitScore(candidate_id, unit_id, fold, None, ("MISSING_WHOLE_UNIT_SCORE",))
    if type(value) is not Decimal:
        raise TypeError("selection scores require Decimal observations or explicit missingness")
    if not value.is_finite():
        return SelectionUnitScore(candidate_id, unit_id, fold, None, ("NONFINITE_WHOLE_UNIT_SCORE",))
    return SelectionUnitScore(candidate_id, unit_id, fold, value, ())


def select_declared_candidate(design: DeclaredSelectionDesign, allocation: UnitAllocation,
                              scores: tuple[SelectionUnitScore, ...], *, result_id: str, fit_calls: int) -> DeclaredSelectionResult:
    units = validate_selection_design(design, allocation)
    expected = tuple((candidate.candidate_id, unit) for candidate in design.candidates for unit in units)
    folds = {row.unit_id: row.fold for row in design.folds}
    if (type(scores) is not tuple or any(type(row) is not SelectionUnitScore for row in scores)
            or tuple((row.candidate_id, row.unit_id) for row in scores) != expected
            or any(row.fold != folds[row.unit_id] for row in scores)
            or type(fit_calls) is not int or fit_calls not in (0, len(design.candidates) * design.fold_count)
            or fit_calls == 0 and any(row.value is not None or "SELECTION_UNENTERED" not in row.reason_codes for row in scores)):
        raise ValueError("selection drops, duplicates or substitutes a declared candidate/unit/fold or actual call census")
    for row in scores:
        row.__post_init__()
    summaries = []
    for candidate in design.candidates:
        values = tuple(row.value for row in scores if row.candidate_id == candidate.candidate_id)
        finite = tuple(value for value in values if value is not None)
        mean = sum(map(Fraction, finite), Fraction(0)) / len(units) if len(finite) == len(units) else None
        summaries.append(CandidateSelectionSummary(candidate.candidate_id, len(units), len(finite),
            None if mean is None else mean.numerator, None if mean is None else mean.denominator))
    eligible = tuple(row for row in summaries if row.mean is not None)
    order = {candidate: index for index, candidate in enumerate(design.tie_order)}
    selected = min(eligible, key=lambda row: (row.mean if design.score_direction == "MINIMIZE" else -row.mean,
                                            order[row.candidate_id])).candidate_id if eligible else None
    return DeclaredSelectionResult(result_id, design.identity, allocation.identity, scores, tuple(summaries), selected, fit_calls)


def unentered_declared_selection(design: DeclaredSelectionDesign, allocation: UnitAllocation,
                                 *, result_id: str, reason: str) -> DeclaredSelectionResult:
    units = validate_selection_design(design, allocation)
    folds = {row.unit_id: row.fold for row in design.folds}
    scores = tuple(SelectionUnitScore(candidate.candidate_id, unit, folds[unit], None,
        tuple(sorted({"SELECTION_UNENTERED", reason}))) for candidate in design.candidates for unit in units)
    return select_declared_candidate(design, allocation, scores, result_id=result_id, fit_calls=0)


def evaluate_declared_candidates(design: DeclaredSelectionDesign, allocation: UnitAllocation,
                                 *, fit_and_score: CandidateFoldFitter, result_id: str) -> DeclaredSelectionResult:
    """Call each code-owned fitter exactly once per declared whole-unit fold.

    The fitter receives disjoint training/heldout unit IDs, not a flattened row
    split. It must return every heldout score, including unavailable outcomes.
    Exceptions propagate; operational failure is never relabelled as science.
    """
    units = validate_selection_design(design, allocation)
    if not callable(fit_and_score):
        raise TypeError("selection fitting needs a code-owned ordinary callback")
    folds = {row.unit_id: row.fold for row in design.folds}
    scores, calls = [], 0
    for candidate in design.candidates:
        for fold in range(design.fold_count):
            training = tuple(unit for unit in units if folds[unit] != fold)
            heldout = tuple(unit for unit in units if folds[unit] == fold)
            returned = fit_and_score(candidate=candidate, fold=fold, training_unit_ids=training, heldout_unit_ids=heldout)
            calls += 1
            if (type(returned) is not tuple or any(type(row) is not SelectionUnitScore for row in returned)
                    or tuple(row.unit_id for row in returned) != heldout
                    or any(row.candidate_id != candidate.candidate_id or row.fold != fold for row in returned)):
                raise ValueError("candidate fitter changes the exact whole-unit heldout score census")
            scores.extend(returned)
    return select_declared_candidate(design, allocation,
        tuple(sorted(scores, key=lambda row: (row.candidate_id, row.unit_id))), result_id=result_id, fit_calls=calls)


def require_development_selection_phase(phase: str) -> None:
    if phase != "DEVELOPMENT":
        raise ValueError("selection and refitting consume development outcomes only")


def freeze_declared_selection(design: DeclaredSelectionDesign, allocation: UnitAllocation, result: DeclaredSelectionResult,
                              *, fitted_model: ObjectIdentity, freeze_id: str,
                              prior_revision: DeclaredSelectionFreeze | None = None) -> DeclaredSelectionFreeze:
    validate_declared_selection_result(design, allocation, result)
    if (prior_revision is not None or result.selected_candidate_id is None or type(fitted_model) is not ObjectIdentity):
        raise ValueError("only one nominated development revision may be frozen; no repeated repair or missing model")
    return DeclaredSelectionFreeze(freeze_id, design.identity, allocation.identity, result.identity, fitted_model,
        design.target, design.criterion, design.features, 1)


def validate_declared_selection_result(design: DeclaredSelectionDesign, allocation: UnitAllocation,
                                       result: DeclaredSelectionResult) -> DeclaredSelectionResult:
    if type(result) is not DeclaredSelectionResult:
        raise TypeError("selection needs its complete typed original result")
    expected = select_declared_candidate(design, allocation, result.scores, result_id=result.result_id, fit_calls=result.fit_calls)
    if result != expected:
        raise ValueError("selection result differs from its declared complete observations and tie rule")
    return result


def require_frozen_selection_for_phase(design: DeclaredSelectionDesign, allocation: UnitAllocation,
                                       result: DeclaredSelectionResult, frozen: DeclaredSelectionFreeze, *, phase: str,
                                       fitted_model: ObjectIdentity, target: ObjectIdentity, criterion: ObjectIdentity,
                                       features: ObjectIdentity) -> DeclaredSelectionFreeze:
    if phase not in ("CALIBRATION", "CONFIRMATION", "TRANSFER"):
        raise ValueError("frozen selection query needs an explicit subsequent scientific phase")
    if type(frozen) is not DeclaredSelectionFreeze:
        raise ValueError("future outcomes require the actual frozen nominated development model")
    expected = freeze_declared_selection(design, allocation, result, fitted_model=fitted_model, freeze_id=frozen.freeze_id)
    if frozen != expected or (target, criterion, features) != (design.target, design.criterion, design.features):
        raise ValueError("future phase changes the original model, target, tolerance or feature transform")
    return frozen
