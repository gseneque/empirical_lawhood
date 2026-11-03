# SPDX-License-Identifier: MPL-2.0
"""Exposed authentic-custody clock-domain controls, with no native acquisition."""
from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction
import math

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import representable_clock as clock
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_fidelity_stream as paired
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_science as science
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_battery_segmented_fidelity_stream import _compare, _port, _stream, prepared as prepared_fixture

prepared = prepared_fixture


def test_boundary_metric_refuses_negative_normalized_maximum():
    with pytest.raises(ValueError):
        clock.BoundaryMetric(174, (), 0, (-1, 1))


@pytest.fixture
def selected(prepared, tmp_path):
    left = _stream(prepared, tmp_path / "left")
    right = _stream(prepared, tmp_path / "right", horizon=30, segments=2)
    original = _compare(left, right)
    policy = clock.RepresentableClockPolicy("policy.exposed.binary64", original.control,
        dict(left[0].trace.config.source.source_members)["solvers/base_solver.py"])
    def assess(changed_policy=policy, changed_original=original):
        return clock.assess_representable_clock(changed_policy, changed_original,
            paired.FullStateStreamOperand(left[0], _port(*left)), paired.FullStateStreamOperand(right[0], _port(*right)))
    return original, policy, assess


def test_explicit_binary64_domain_retains_original_real_gaps_and_complete174_census(selected):
    original, _, assess = selected
    result = assess()
    assert original.disposition is A.UNEVALUABLE and len(original.coverage_issues) == 2
    assert result.original_pair == original and result.disposition is A.SATISFIED
    assert tuple(map(len, result.complete_call_censuses)) == (1, 2) and len(result.boundaries) == 1
    assert result.boundaries[0].state_continuity.checked_components == 174
    assert result.boundaries[0].returned_derivative_continuity.checked_components == 174
    assert result.real_open_gaps_retain_original_disposition
    assert not result.whole_time_certified and not result.physical_qualification and not result.later_use_admission
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


@pytest.mark.parametrize("damage", ("control", "source", "weight"))
def test_wrong_selected_policy_source_control_or_comparison_gate_refuses(selected, damage):
    _, policy, assess = selected
    with pytest.raises(ValueError):
        changed = replace(policy, original_control=replace(policy.original_control, object_fingerprint="f" * 64)) if damage == "control" else replace(
            policy, selected_step_source_sha256="f" * 64) if damage == "source" else replace(policy, comparison_atol=D("1e-7"))
        assess(changed)


@pytest.mark.parametrize("damage", ("call", "boundary", "174", "terminal"))
def test_complete_call_boundary_and_native_row_denominators_cannot_be_thinned(selected, damage):
    _, _, assess = selected
    result = assess()
    with pytest.raises(ValueError):
        if damage == "call":
            replace(result, complete_call_censuses=(result.complete_call_censuses[0], result.complete_call_censuses[1][:-1]))
        elif damage == "boundary":
            replace(result, boundaries=())
        elif damage == "174":
            metric = replace(result.boundaries[0].returned_derivative_continuity, checked_components=173)
            replace(result, boundaries=(replace(result.boundaries[0], returned_derivative_continuity=metric),))
        else:
            side = result.complete_call_censuses[1]
            replace(result, complete_call_censuses=(result.complete_call_censuses[0], (*side[:-1], replace(side[-1], exact_end=(61, 1)))))


def test_wider_gap_or_unpaired_suffix_remains_unevaluable(selected):
    original, _, assess = selected
    result = assess()
    wider = replace(original.coverage_issues[0], exact_end=(31, 1))
    changed = replace(original, coverage_issues=(wider, *original.coverage_issues[1:]))
    disposition, reasons = clock._reasons(changed, result.complete_call_censuses, result.boundaries)
    assert disposition is A.UNEVALUABLE and "original-uncovered-span-has-no-exact-source-adjacent-boundary" in reasons
    with pytest.raises(ValueError):
        replace(result, original_pair=changed)


@pytest.mark.parametrize("damage", ("regime", "requested-state", "state", "derivative"))
def test_actual_regime_or_full_one_sided_continuity_cannot_be_bypassed(selected, damage):
    _, policy, assess = selected
    result = assess()
    boundary = result.boundaries[0]
    if damage == "regime":
        boundary = replace(boundary, actual_model_and_scalar_regime_unchanged=False)
    elif damage == "requested-state":
        boundary = replace(boundary, requested_full_state_unchanged=False)
    else:
        left = tuple(float(0).hex() for _ in range(174))
        right = tuple(float(1e-3 if i == 173 else 0).hex() for i in range(174))
        metric = clock._metric(left, right, 174, policy)
        assert metric.failed_components == (173,)
        boundary = replace(boundary, **{("state_continuity" if damage == "state" else "returned_derivative_continuity"): metric})
    with pytest.raises(ValueError):
        replace(result, boundaries=(boundary,))
    disposition, reasons = clock._reasons(result.original_pair, result.complete_call_censuses, (boundary,))
    adverse = replace(result, boundaries=(boundary,), disposition=disposition, reason_codes=reasons)
    assert adverse.disposition is (A.UNEVALUABLE if damage == "regime" else A.FALSIFIED)


def test_actual_changed_regime_event_denominator_is_not_a_constant_regime_pass(selected):
    original, _, assess = selected
    result = assess()
    changed = replace(original, declared_transition_counts=(0, 1))
    disposition, reasons = clock._reasons(changed, result.complete_call_censuses, result.boundaries)
    assert disposition is A.UNEVALUABLE and "independent-regime-change-event-control-unassessed" in reasons


def test_missing_complete174_boundary_derivative_and_nonfinite_operands_refuse(selected):
    _, policy, _ = selected
    values = tuple(float(0).hex() for _ in range(174))
    with pytest.raises(ValueError, match="omits actual full"):
        clock._metric(values, values[:-1], 174, policy)
    assert clock._adjacent(Fraction(30), Fraction.from_float(math.nextafter(30., math.inf)))
    assert not clock._adjacent(Fraction(30), Fraction(31))
    with pytest.raises(ValueError, match="exact finite binary64"):
        clock._adjacent(Fraction(1, 10), Fraction(1))


def test_original_falsified_covered_data_cannot_become_favourable_clock_coverage(prepared, tmp_path):
    left = _stream(prepared, tmp_path / "left")
    right = _stream(prepared, tmp_path / "right", horizon=30, segments=2, changed_state=(173, .001))
    original = _compare(left, right)
    assert original.disposition is A.FALSIFIED
    policy = clock.RepresentableClockPolicy("policy.exposed.adverse", original.control,
        dict(left[0].trace.config.source.source_members)["solvers/base_solver.py"])
    result = clock.assess_representable_clock(policy, original,
        paired.FullStateStreamOperand(left[0], _port(*left)), paired.FullStateStreamOperand(right[0], _port(*right)))
    assert result.disposition is A.FALSIFIED and result.original_pair == original


def test_different_original_operand_evidence_refuses(selected, prepared, tmp_path):
    original, policy, _ = selected
    other = _stream(prepared, tmp_path / "other", horizon=15, segments=4)
    with pytest.raises(ValueError, match="complete original evidence"):
        clock.assess_representable_clock(policy, original,
            paired.FullStateStreamOperand(other[0], _port(*other)), paired.FullStateStreamOperand(other[0], _port(*other)))
    assert science.identity(other[0], "evidence_id") != original.left_evidence
