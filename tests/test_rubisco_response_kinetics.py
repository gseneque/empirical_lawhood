# SPDX-License-Identifier: MPL-2.0
"""Truth-known four-state controls; no enzyme evidence or native acquisition."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction import kinetic_model as model
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model_assessment import assess_four_state
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition

RATES = model.FourStateRates(*(D(x) for x in (2, 3, 5, 7, 17, 13, 11, 19)))


@pytest.mark.parametrize("rates", [RATES, replace(RATES, d_c=D(0), d_o=D(0)), replace(RATES, b=D(0))])
@pytest.mark.parametrize("carbon,oxygen", [("0", "0"), ("0", "10"), ("1", "0"), ("0.1", "2"), ("100", "7")])
def test_exact_balance_competitive_flux_and_independent_assessment(rates, carbon, oxygen):
    query = model.DissolvedGasQuery(D(carbon), D(oxygen))
    result = model.solve_four_state(rates, query, result_id="result.control")
    assert sum(p.fraction for p in result.populations) == 1
    k = result.intrinsic
    denominator = 1 + F(carbon) / k.kc.fraction + F(oxygen) / k.ko.fraction
    assert result.carboxylation_events_per_site_s.fraction == k.kcat_c.fraction * (F(carbon) / k.kc.fraction) / denominator
    assert result.oxygenation_events_per_site_s.fraction == k.kcat_o.fraction * (F(oxygen) / k.ko.fraction) / denominator
    if F(carbon) and F(oxygen):
        assert (result.carboxylation_events_per_site_s.fraction / result.oxygenation_events_per_site_s.fraction
                * F(oxygen) / F(carbon)) == k.specificity.fraction
    assessment = assess_four_state(result, assessment_id="assessment.control")
    assert assessment.disposition is AssessmentDisposition.SATISFIED
    assert assessment.biological_accuracy == "NOT_ESTABLISHED"
    assert decode_canonical_bytes(result.canonical_bytes(), model.FourStateResult, maximum_bytes=1024 * 1024) == result


def test_competing_oxygen_changes_apparent_kc_without_relabelling_intrinsic():
    constants = model.intrinsic_constants(RATES)
    apparent = model.fixed_oxygen_response(constants, o2_um=D(25))
    assert apparent.apparent_kc_um.fraction > constants.kc.fraction
    assert model.fixed_oxygen_response(constants, o2_um=D(0)).apparent_kc_um == constants.kc
    with pytest.raises(ValueError, match="apparent"):
        replace(apparent, interpretation=constants.interpretation)
    with pytest.raises(ValueError, match="intrinsic"):
        replace(constants, interpretation=apparent.interpretation)


def test_common_gating_specificity_invariance_is_conditional_not_preservation_evidence():
    changed = replace(RATES, a=D(200), b=D(3000))
    original, mutant = map(model.intrinsic_constants, (RATES, changed))
    assert original.specificity == mutant.specificity
    assert original.kcat_c != mutant.kcat_c
    assert model.intrinsic_constants(replace(changed, o=D(26))).specificity.fraction == original.specificity.fraction / 2
    sensitivities = {(s.parameter, s.endpoint): s for s in model.endpoint_sensitivities(RATES)}
    assert sensitivities["a", "specificity"].derivative.fraction == 0
    assert sensitivities["b", "specificity"].derivative.fraction == 0


def test_irreversible_zero_reverse_rate_has_no_logarithm_and_exact_derivative():
    rates = replace(RATES, d_c=D(0), d_o=D(0))
    constants = model.intrinsic_constants(rates)
    assert constants.specificity.fraction == F(rates.c) / F(rates.o)
    sensitivity = next(s for s in model.endpoint_sensitivities(rates)
                       if (s.parameter, s.endpoint) == ("d_c", "specificity"))
    assert not sensitivity.positive_parameter
    assert sensitivity.elasticity.fraction == 0
    assert sensitivity.derivative.fraction < 0


def test_all_exact_sensitivities_against_independent_finite_perturbations():
    epsilon = D("1e-12")
    with localcontext() as context:
        context.prec = 50
        for sensitivity in model.endpoint_sensitivities(RATES):
            low = replace(RATES, **{sensitivity.parameter: getattr(RATES, sensitivity.parameter) - epsilon})
            high = replace(RATES, **{sensitivity.parameter: getattr(RATES, sensitivity.parameter) + epsilon})
            difference = (getattr(model.intrinsic_constants(high), sensitivity.endpoint).fraction
                          - getattr(model.intrinsic_constants(low), sensitivity.endpoint).fraction) / F(2 * epsilon)
            assert abs(difference - sensitivity.derivative.fraction) < F(1, 10**20)


def test_independent_assessor_rejects_corrupt_retained_flux_without_reexecuting_producer(monkeypatch):
    result = model.solve_four_state(RATES, model.DissolvedGasQuery(D(2), D(3)), result_id="result.control")
    def forbidden(*args, **kwargs):
        raise AssertionError("assessment repeated producer")
    monkeypatch.setattr(model, "solve_four_state", forbidden)
    monkeypatch.setattr(model, "intrinsic_constants", forbidden)
    changed = replace(result, carboxylation_events_per_site_s=Exact.of(1))
    assessment = assess_four_state(changed, assessment_id="assessment.bad-flux")
    assert assessment.disposition is AssessmentDisposition.FALSIFIED
    assert "FAILED_EVENT-FLUX" in assessment.reason_codes


def test_stationary_result_matches_independent_transient_matrix_exponential():
    # A four-by-four mathematical control, not a molecular/native supplier.
    import numpy as np
    from scipy.linalg import expm

    rates = model.FourStateRates(*(D(1) for _ in range(8)))
    query = model.DissolvedGasQuery(D(2), D(3))
    result = model.solve_four_state(rates, query, result_id="result.transient")
    generator = np.array([[-1, 1, 1, 1], [1, -6, 1, 1], [0, 2, -2, 0], [0, 3, 0, -2]], dtype=float)
    assert np.all(generator.sum(axis=0) == 0)
    transient = expm(generator * 100) @ np.array([1, 0, 0, 0])
    assert np.max(np.abs(transient - [float(p.fraction) for p in result.populations])) < 1e-12


@pytest.mark.parametrize("change", [
    {"a": D(0)}, {"c": D(-1)}, {"d_o": D("-0.1")},
    {"r_o": D("NaN")}, {"clock_unit": "step"},
    {"concentration_convention": "TOTAL_BICARBONATE"},
])
def test_invalid_clocks_units_rates_and_unidentified_zero_activity_refuse(change):
    with pytest.raises((TypeError, ValueError)):
        replace(RATES, **change)


def test_retained_sensitivity_corruption_is_independently_refuted():
    result = model.solve_four_state(RATES, model.DissolvedGasQuery(D(2), D(3)), result_id="result.sensitivity")
    changed = replace(result, sensitivities=(replace(result.sensitivities[0], derivative=Exact.of(99)),
                                            *result.sensitivities[1:]))
    assessment = assess_four_state(changed, assessment_id="assessment.bad-sensitivity")
    assert assessment.disposition is AssessmentDisposition.FALSIFIED
    assert assessment.reason_codes == ("FAILED_SENSITIVITIES",)
