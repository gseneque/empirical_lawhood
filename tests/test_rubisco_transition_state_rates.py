# SPDX-License-Identifier: MPL-2.0
"""Disclosed algebra controls; no enzyme barriers or qualification evidence."""

from dataclasses import replace
from decimal import Decimal as D, ROUND_UP, localcontext
from fractions import Fraction as F
from math import exp

import pytest

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import DissolvedGasQuery, solve_four_state
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rates import PairedActivationRateInput, PairedTransitionStateRate, calculate_transition_state_rate
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rate_assessment import TransitionStateRateAssessment, assess_transition_state_rate
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A


def operands(parameter="a", *, local=False, assessed=True):
    supply = disclosed_supply()
    source = supply.case.sources[0]
    capture = parameter in {"c", "o"}
    selected = PairedActivationRateInput("activation.disclosed." + parameter,
        supply.case.identity, supply.context.identity, parameter, supply.context.temperature_k,
        (D(70000), D(71000)), (D("0.5"), D("0.25")), (D(1), D(2)),
        D(1000000) if capture else None,
        "LOCAL_REQUIRES_ONE_BULK_CONVERSION" if local else "BULK_ALREADY_INCLUDED" if capture else "UNIMOLECULAR",
        (D(3), D(4)) if local else None,
        source, source, source if assessed else None, source, source,
        source if capture else None, source if parameter in {"o", "d_o", "r_o"} else None,
        "dependence.disclosed.shared-snapshot",
        tuple(sorted({source, supply.case.identity, supply.context.identity}, key=lambda row: row.object_id)),
        ("requirement.disclosed.no-biological-evidence",))
    return selected, supply.case, supply.context


def calculate(selected, case, context):
    return calculate_transition_state_rate(selected, case, context, result_id="rate.disclosed." + selected.parameter)


def assess(selected, result, case, context):
    return assess_transition_state_rate(selected, result, case, context, assessment_id="assessment.disclosed.tst")


def test_zero_barrier_has_the_exact_si_attempt_frequency_and_seconds():
    selected, case, context = operands()
    selected = replace(selected, activation_free_energy_j_mol=(D(0), D(0)),
        transmission_coefficients=(D(1), D(1)), prefactor_multipliers=(D(1), D(1)))
    result = calculate(selected, case, context)
    expected = F(D("1.380649e-23")) * F(context.temperature_k) / F(D("6.62607015e-34"))
    assert abs(F(result.wild_type_rate) / expected - 1) < F(1, 10**59)
    assert result.wild_type_rate == result.mutant_rate
    assert result.rate_unit == "s^-1" and result.physical_clock_unit == "s"
    assert result.new_native_calls == 0
    assert assess(selected, result, case, context).disposition is A.SATISFIED


def test_one_molar_source_converts_to_inverse_micromolar_exactly_once():
    unimolecular, case, context = operands()
    capture, _, _ = operands("c")
    first, second = calculate(unimolecular, case, context), calculate(capture, case, context)
    assert second.rate_unit == "uM^-1 s^-1"
    assert F(second.wild_type_rate) * 1_000_000 == F(first.wild_type_rate)
    assert F(second.mutant_rate) * 1_000_000 == F(first.mutant_rate)
    assert assess(capture, second, case, context).disposition is A.SATISFIED


def test_consistent_barrier_standard_state_change_leaves_the_physical_coefficient():
    selected, case, context = operands("c")
    old = replace(selected, concentration_standard_state_um=D(1))
    with localcontext() as arithmetic:
        arithmetic.prec = 70
        rt = D("1.380649e-23") * D("6.02214076e23") * context.temperature_k
        new = replace(selected, activation_free_energy_j_mol=tuple(
            value - rt * D(1000000).ln() for value in old.activation_free_energy_j_mol))
    first, second = calculate(old, case, context), calculate(new, case, context)
    assert abs(F(first.wild_type_rate) / F(second.wild_type_rate) - 1) < F(1, 10**56)
    assert abs(F(first.mutant_rate) / F(second.mutant_rate) - 1) < F(1, 10**56)


def test_local_partition_is_paired_and_cannot_be_applied_to_a_bulk_barrier():
    local, case, context = operands("c", local=True)
    bulk, _, _ = operands("c")
    left, right = calculate(local, case, context), calculate(bulk, case, context)
    assert abs(F(left.wild_type_rate) / F(right.wild_type_rate) - 3) < F(1, 10**57)
    assert abs(F(left.mutant_rate) / F(right.mutant_rate) - 4) < F(1, 10**57)
    assert left.dependence_group_id == local.dependence_group_id
    assert assess(local, left, case, context).disposition is A.SATISFIED
    with pytest.raises(ValueError, match="exactly once"):
        replace(bulk, bulk_partition_factors=(D(3), D(4)))
    with pytest.raises(ValueError, match="exactly once"):
        replace(local, bulk_partition_factors=None)


def test_unimolecular_forward_reverse_pair_obeys_its_declared_free_energy_difference():
    selected, case, context = operands()
    selected = replace(selected, transmission_coefficients=(D(1), D(1)), prefactor_multipliers=(D(1), D(1)))
    reverse = replace(selected, input_id="activation.reverse", parameter="b",
        activation_free_energy_j_mol=(D(65000), D(66000)))
    forward_result, reverse_result = calculate(selected, case, context), calculate(reverse, case, context)
    expected = exp(-5000 / (8.31446261815324 * float(context.temperature_k)))
    assert float(forward_result.wild_type_rate / reverse_result.wild_type_rate) == pytest.approx(expected, rel=1e-13)
    assert forward_result.wild_type_rate > 0 and reverse_result.wild_type_rate > 0


def test_supplied_transmission_and_prefactor_keep_wt_mutant_dependence():
    selected, case, context = operands()
    selected = replace(selected, activation_free_energy_j_mol=(D(70000), D(70000)))
    result = calculate(selected, case, context)
    assert result.wild_type_rate == result.mutant_rate
    changed = replace(selected, prefactor_multipliers=(D(1), D(1)))
    changed_result = calculate(changed, case, context)
    assert abs(F(changed_result.mutant_rate) / F(changed_result.wild_type_rate) - F(1, 2)) < F(1, 10**59)


def test_arithmetic_context_does_not_change_retained_rate_bytes():
    selected, case, context = operands("o", local=True)
    original = calculate(selected, case, context)
    with localcontext() as arithmetic:
        arithmetic.prec = 9
        arithmetic.rounding = ROUND_UP
        repeated = calculate(selected, case, context)
    assert repeated.canonical_bytes() == original.canonical_bytes()


def test_assessor_uses_inverse_log_equations_without_calling_the_producer(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import transition_state_rates as producer
    selected, case, context = operands("o", local=True, assessed=False)
    retained = calculate(selected, case, context)
    monkeypatch.setattr(producer, "calculate_transition_state_rate", lambda *a, **k: pytest.fail("producer entered"))
    checked = assess(selected, retained, case, context)
    assert checked.disposition is A.SATISFIED
    assert checked.physical_admission is A.UNEVALUABLE and checked.new_native_calls == 0
    assert any(name.endswith(".free-energy-assessment") for name in checked.unresolved_requirement_ids)
    altered = replace(retained, mutant_rate=retained.mutant_rate * D(2))
    assert assess(selected, altered, case, context).disposition is A.FALSIFIED
    with pytest.raises(ValueError, match="unresolved requirements"):
        assess(selected, replace(retained, unresolved_requirement_ids=()), case, context)


@pytest.mark.parametrize("parameter", ("a", "b", "c", "d_c", "d_o", "o", "r_c", "r_o"))
def test_all_transition_units_roundtrip_without_physical_admission(parameter):
    selected, case, context = operands(parameter)
    result = calculate(selected, case, context)
    checked = assess(selected, result, case, context)
    assert checked.disposition is A.SATISFIED
    for record, kind in ((selected, PairedActivationRateInput), (result, PairedTransitionStateRate),
            (checked, TransitionStateRateAssessment)):
        assert decode_canonical_bytes(record.canonical_bytes(), kind, maximum_bytes=100_000) == record


def test_context_oxygen_source_and_probability_changes_refuse():
    selected, case, context = operands("o")
    with pytest.raises(ValueError, match="physical temperature"):
        calculate(replace(selected, temperature_k=D(298)), case, context)
    with pytest.raises(ValueError, match="oxygenation transitions"):
        replace(selected, oxygenation_model=None)
    with pytest.raises(ValueError, match="source and model closure"):
        replace(selected, sources=(case.identity,))
    with pytest.raises(ValueError, match="probability support"):
        replace(selected, transmission_coefficients=(D(1), D("1.1")))
    with pytest.raises(ValueError, match="probability support"):
        replace(selected, transmission_coefficients=(D(1), D(0)))
    with pytest.raises(ValueError, match="standard state"):
        replace(selected, concentration_standard_state_um=None)


def test_conditional_values_feed_existing_rate_consumer_without_changed_units():
    supply = disclosed_supply()
    selected, case, context = operands("c")
    result = calculate(selected, case, context)
    rates = replace(supply.scenarios[0].points[0].wild_type, c=result.wild_type_rate)
    solved = solve_four_state(rates, DissolvedGasQuery(D(10), D(250)), result_id="tst.disclosed.consumer")
    assert solved.rates.c == result.wild_type_rate
    assert solved.intrinsic.specificity.fraction > 0


def test_extreme_barrier_cannot_turn_uncertain_or_positive_rate_into_fixed_zero():
    selected, case, context = operands("d_c")
    selected = replace(selected, activation_free_energy_j_mol=(D("1e20"), D("1e20")))
    with pytest.raises(ArithmeticError, match="exact zero"):
        calculate(selected, case, context)


@pytest.mark.parametrize("field", ("selected_input", "retained_result"))
@pytest.mark.parametrize("change", ("schema", "version"))
def test_assessment_preserves_exact_record_types(field, change):
    selected, case, context = operands()
    result = calculate(selected, case, context)
    checked = assess(selected, result, case, context)
    original = getattr(checked, field)
    wrong = context.identity if change == "schema" else replace(original, object_version="9.0.0")
    with pytest.raises(ValueError, match="exact retained input/result type"):
        replace(checked, **{field: wrong})


def test_assessment_tolerance_comparison_does_not_round_residuals():
    selected, case, context = operands()
    checked = assess(selected, calculate(selected, case, context), case, context)
    residual = D("1.00000000000000000001e-50")
    with localcontext() as arithmetic:
        arithmetic.prec = 9
        changed = replace(checked, logarithmic_residuals=(D(0), residual), disposition=A.FALSIFIED)
    assert changed.disposition is A.FALSIFIED
