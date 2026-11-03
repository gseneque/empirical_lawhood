# SPDX-License-Identifier: MPL-2.0
"""Independent finite-selection checks; no scientific source or IID warrant."""

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.experimental_selection import DeclaredCandidate, DeclaredSelectionDesign, DeclaredSelectionResult, WholeUnitFold
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experimental_selection import (
    evaluate_declared_candidates, freeze_declared_selection, require_development_selection_phase,
    require_frozen_selection_for_phase, selection_score, validate_declared_selection_result, validate_selection_design,
    select_declared_candidate, unentered_declared_selection,
)


def identity(name, schema="empirical-lawhood/testing/selection-operand"):
    return ObjectIdentity(name, schema, "1.0.0", sha256(name.encode()).hexdigest())


def design(count=4):
    source = identity("source.exposed")
    units = tuple(IndependentUnit(f"group.{i:02}", source.object_id, "family.original", ("fine", "primary"), True)
                  for i in range(count + 2))
    allocation = UnitAllocation("allocation.exposed", (source,), units,
        tuple(UnitRoleAssignment(unit.unit_id, "development" if i < count else "confirmation") for i, unit in enumerate(units)))
    candidates = tuple(DeclaredCandidate(key, "family.explicit-ridge", identity("tuning."+key)) for key in ("candidate.a", "candidate.b"))
    specification = DeclaredSelectionDesign("design.explicit", allocation.identity, "development", candidates,
        tuple(WholeUnitFold(unit, i % 2) for i, unit in enumerate(allocation.unit_ids("development"))), 2, 5,
        ("candidate.b", "candidate.a"), "MINIMIZE", "REQUIRE_COMPLETE", identity("target.original"),
        identity("criterion.original"), identity("features.original"))
    return specification, allocation


def evaluate(values, *, count=4, direction="MINIMIZE"):
    specification, allocation = design(count)
    specification = replace(specification, score_direction=direction)
    calls = []
    def fit(**selection):
        calls.append(selection)
        key = selection["candidate"].candidate_id
        return tuple(selection_score(key, unit, selection["fold"], values[key][int(unit.rsplit(".", 1)[1])])
                     for unit in selection["heldout_unit_ids"])
    result = evaluate_declared_candidates(specification, allocation, fit_and_score=fit, result_id="result.original")
    return specification, allocation, result, calls


def test_actual_candidate_fold_calls_move_whole_groups_and_keep_nested_views_out_of_denominator():
    specification, allocation, result, calls = evaluate({"candidate.a": (Decimal(0), Decimal(1), Decimal(2), Decimal(3)),
                                                        "candidate.b": (Decimal(2),)*4})
    assert len(calls) == result.fit_calls == 4
    assert all(call["training_unit_ids"] == (("group.01", "group.03") if call["fold"] == 0 else ("group.00", "group.02")) for call in calls)
    assert all(set(call["training_unit_ids"]).isdisjoint(call["heldout_unit_ids"]) for call in calls)
    assert {unit for call in calls for unit in call["training_unit_ids"] + call["heldout_unit_ids"]} == set(allocation.unit_ids("development"))
    assert tuple(row.mean for row in result.summaries) == (Fraction(3, 2), Fraction(2))
    assert all(row.assigned_units == row.finite_units == 4 for row in result.summaries)
    assert result.selected_candidate_id == "candidate.a"
    assert decode_canonical_bytes(result.canonical_bytes(), DeclaredSelectionResult, maximum_bytes=16384) == result
    assert validate_declared_selection_result(specification, allocation, result) == result


@pytest.mark.parametrize("count", (3, 6, 8))
def test_parameterized_complete_unit_counts_and_rational_means(count):
    _, _, result, _ = evaluate({"candidate.a": tuple(Decimal(i) for i in range(count)), "candidate.b": (Decimal(9),)*count}, count=count)
    assert result.summaries[0].mean == Fraction(count-1, 2)
    assert result.summaries[0].assigned_units == count


def test_exact_low_precision_rational_comparison_and_declared_tie_order():
    _, _, result, _ = evaluate({"candidate.a": (Decimal(".1"), Decimal(".2"), Decimal(".3"), Decimal(".4")),
                              "candidate.b": (Decimal(".25"),)*4})
    assert tuple(row.mean for row in result.summaries) == (Fraction(1, 4), Fraction(1, 4))
    assert result.selected_candidate_id == "candidate.b"
    _, _, maximum, _ = evaluate({"candidate.a": (Decimal(1),)*4, "candidate.b": (Decimal(2),)*4}, direction="MAXIMIZE")
    assert maximum.selected_candidate_id == "candidate.b"


@pytest.mark.parametrize("missing", (None, Decimal("Infinity"), Decimal("-Infinity"), Decimal("NaN")))
def test_one_unevaluable_unit_keeps_full_candidate_denominator_and_cannot_win_by_deletion(missing):
    _, _, result, _ = evaluate({"candidate.a": (Decimal(0), Decimal(0), Decimal(0), missing), "candidate.b": (Decimal(9),)*4})
    first = result.summaries[0]
    assert (first.assigned_units, first.finite_units, first.mean) == (4, 3, None)
    assert result.selected_candidate_id == "candidate.b"
    row = next(row for row in result.scores if row.candidate_id == "candidate.a" and row.unit_id == "group.03")
    assert row.value is None and row.reason_codes


def test_all_unevaluable_candidates_retain_every_slot_without_nomination():
    _, _, result, _ = evaluate({"candidate.a": (None,)*4, "candidate.b": (None,)*4})
    assert result.selected_candidate_id is None and len(result.scores) == 8
    assert all((row.assigned_units, row.finite_units, row.mean) == (4, 0, None) for row in result.summaries)


@pytest.mark.parametrize("damage", ("missing-unit", "protected-unit", "duplicate-unit", "empty-fold", "foreign-allocation", "budget"))
def test_invalid_whole_group_design_refuses_before_fitting(damage):
    specification, allocation = design()
    changes = {
        "missing-unit": {"folds": specification.folds[:-1]},
        "protected-unit": {"folds": (*specification.folds[:-1], WholeUnitFold("group.04", 1))},
        "duplicate-unit": {"folds": (*specification.folds, specification.folds[-1])},
        "empty-fold": {"folds": tuple(replace(row, fold=0) for row in specification.folds)},
        "foreign-allocation": {"allocation": replace(allocation.identity, object_fingerprint="1"*64)},
        "budget": {"maximum_fit_calls": 4},
    }
    calls = []
    with pytest.raises(ValueError):
        bad = replace(specification, **changes[damage])
        evaluate_declared_candidates(bad, allocation, fit_and_score=lambda **kwargs: calls.append(kwargs), result_id="result.refused")
    assert calls == []


@pytest.mark.parametrize("damage", ("drop", "duplicate", "wrong-candidate", "wrong-fold", "protected"))
def test_fitter_cannot_substitute_or_thin_heldout_score_census(damage):
    specification, allocation = design()
    def fit(**call):
        rows = tuple(selection_score(call["candidate"].candidate_id, unit, call["fold"], Decimal(1)) for unit in call["heldout_unit_ids"])
        if damage == "drop":
            return rows[:-1]
        if damage == "duplicate":
            return (rows[0], rows[0])
        if damage == "wrong-candidate":
            return tuple(replace(row, candidate_id="candidate.foreign") for row in rows)
        if damage == "wrong-fold":
            return tuple(replace(row, fold=1-row.fold) for row in rows)
        return (*rows[:-1], replace(rows[-1], unit_id="group.04"))
    with pytest.raises(ValueError, match="heldout score census"):
        evaluate_declared_candidates(specification, allocation, fit_and_score=fit, result_id="result.refused")


def test_operational_fitting_refusal_propagates_exact_exception():
    specification, allocation = design()
    failure = RuntimeError("original fitting refused")
    def refused(**kwargs):
        raise failure
    with pytest.raises(RuntimeError) as captured:
        evaluate_declared_candidates(specification, allocation, fit_and_score=refused, result_id="result.refused")
    assert captured.value is failure


@pytest.mark.parametrize("phase", ("CALIBRATION", "CONFIRMATION", "TRANSFER"))
def test_future_outcomes_cannot_refit_and_require_exact_model_target_criterion_features(phase):
    specification, allocation, result, _ = evaluate({"candidate.a": (Decimal(1),)*4, "candidate.b": (Decimal(2),)*4})
    model = identity("model.fitted")
    frozen = freeze_declared_selection(specification, allocation, result, fitted_model=model, freeze_id="freeze.model")
    options = dict(phase=phase, fitted_model=model, target=specification.target,
        criterion=specification.criterion, features=specification.features)
    assert require_frozen_selection_for_phase(specification, allocation, result, frozen, **options) == frozen
    with pytest.raises(ValueError, match="development outcomes only"):
        require_development_selection_phase(phase)
    for name in ("fitted_model", "target", "criterion", "features"):
        with pytest.raises(ValueError, match="model, target, tolerance or feature"):
            require_frozen_selection_for_phase(specification, allocation, result, frozen, **(options | {name: identity("foreign."+name.replace("_", "-"))}))
    with pytest.raises(ValueError, match="one nominated"):
        freeze_declared_selection(specification, allocation, result, fitted_model=model, freeze_id="freeze.repeat", prior_revision=frozen)


@pytest.mark.parametrize("value", (1.0, True, "1", Fraction(1)))
def test_implicit_float_bool_string_or_fraction_score_conversion_refuses(value):
    with pytest.raises(TypeError, match="Decimal"):
        selection_score("candidate.a", "group.00", 0, value)


def test_strict_design_and_result_contracts_cannot_quietly_change_target_or_selected_candidate():
    specification, allocation, result, _ = evaluate({"candidate.a": (Decimal(1),)*4, "candidate.b": (Decimal(2),)*4})
    assert validate_selection_design(specification, allocation) == allocation.unit_ids("development")
    with pytest.raises(ValueError, match="complete observations"):
        validate_declared_selection_result(specification, allocation, replace(result, selected_candidate_id="candidate.b"))
    with pytest.raises(ValueError):
        replace(specification, missing_policy="DROP_MISSING")


@pytest.mark.parametrize("count", (3, 8))
def test_unentered_trigger_retains_every_reserved_candidate_and_unit_with_zero_fits(count):
    specification, allocation = design(count)
    result = unentered_declared_selection(specification, allocation, result_id="result.unentered", reason="TRIGGER_NOT_MET")
    assert result.fit_calls == 0 and result.selected_candidate_id is None
    assert len(result.scores) == 2*count
    assert all(row.value is None and row.reason_codes == ("SELECTION_UNENTERED", "TRIGGER_NOT_MET") for row in result.scores)
    assert tuple((row.assigned_units, row.finite_units, row.mean) for row in result.summaries) == ((count, 0, None),)*2
    assert validate_declared_selection_result(specification, allocation, result) == result
    with pytest.raises(ValueError, match="one nominated"):
        freeze_declared_selection(specification, allocation, result, fitted_model=identity("model.invented"), freeze_id="freeze.refused")


def test_zero_fit_census_cannot_be_used_to_claim_observed_or_entered_scores():
    specification, allocation, result, _ = evaluate({"candidate.a": (Decimal(1),)*4, "candidate.b": (Decimal(2),)*4})
    with pytest.raises(ValueError, match="actual call census"):
        select_declared_candidate(specification, allocation, result.scores, result_id="result.false-zero", fit_calls=0)
    _, _, missing, _ = evaluate({"candidate.a": (None,)*4, "candidate.b": (None,)*4})
    with pytest.raises(ValueError, match="actual call census"):
        select_declared_candidate(specification, allocation, missing.scores, result_id="result.false-zero", fit_calls=0)
