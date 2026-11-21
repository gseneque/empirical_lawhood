# SPDX-License-Identifier: MPL-2.0
"""Independent exact diagnostics and consequential closure counterexamples."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction as F

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import ENDPOINT_ORDER, DissolvedGasQuery, solve_four_state
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.reference_analysis import ConcentrationResponseAssessment, EndpointIdentifiability, MarkovLumpingSelection, StrongLumpingAssessment, assess_concentration_response, assess_endpoint_identifiability, assess_strong_lumping
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A


@pytest.fixture(scope="module")
def retained():
    supply = disclosed_supply()
    rates = supply.scenarios[0].points[0].wild_type
    queries = tuple(DissolvedGasQuery(D(c), D(o)) for c, o in ((0, 0), (0, 20), (1, 0), (2, 3), (10, 20)))
    results = tuple(solve_four_state(rates, query, result_id="result.concentration." + str(i)) for i, query in enumerate(queries))
    return rates, queries, results


def test_two_endpoints_leave_six_local_rate_directions_and_full_constants_leave_four(retained):
    result = retained[2][-1]
    assessed = assess_endpoint_identifiability(result, analysis_id="rank.two")
    assert assessed.exact_rank == 2 and assessed.local_unconstrained_nullity == 6
    for direction in assessed.nullspace:
        assert all(sum(value.fraction * component.fraction for value, component in zip(row, direction, strict=True)) == 0
                   for row in assessed.jacobian)
    full = assess_endpoint_identifiability(result, analysis_id="rank.all", observed_endpoints=ENDPOINT_ORDER)
    assert full.exact_rank == 4 and full.local_unconstrained_nullity == 4
    assert decode_canonical_bytes(assessed.canonical_bytes(), EndpointIdentifiability, maximum_bytes=100_000) == assessed
    with pytest.raises(ValueError, match="exact rank"):
        replace(assessed, exact_rank=8)


def test_distinct_finite_rates_can_have_identical_joint_target_endpoints(retained):
    original = retained[2][-1]
    changed = replace(original.rates, a=D(4), r_c=D(2), c=D("3.6"), b=D(5))
    other = solve_four_state(changed, original.query, result_id="result.unidentified")
    assert other.rates != original.rates
    assert (other.intrinsic.kcat_c, other.intrinsic.specificity) == (original.intrinsic.kcat_c, original.intrinsic.specificity)
    assert other.intrinsic.kc != original.intrinsic.kc
    assert assess_endpoint_identifiability(other, analysis_id="rank.other").exact_rank == 2


def test_zero_reverse_rates_are_boundary_directions_without_logarithms(retained):
    rates = replace(retained[0], d_c=D(0), d_o=D(0))
    result = solve_four_state(rates, retained[1][-1], result_id="result.irreversible")
    assessed = assess_endpoint_identifiability(result, analysis_id="rank.irreversible")
    assert assessed.zero_parameter_ids == ("d_c", "d_o")
    assert assessed.exact_rank == 2
    assert "UNCONSTRAINED" in assessed.interpretation
    limited = assess_endpoint_identifiability(result, analysis_id="rank.only-gating", free_parameters=("a", "b"))
    assert limited.exact_rank == 1 and limited.local_unconstrained_nullity == 1


def test_retained_rank_and_concentration_assessors_do_not_invoke_any_producer(retained, monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_prediction import kinetic_model
    from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism import science
    for owner, names in ((kinetic_model, ("solve_four_state", "intrinsic_constants", "endpoint_sensitivities")),
                         (science, ("stationary", "solve"))):
        for name in names:
            monkeypatch.setattr(owner, name, lambda *a, **k: pytest.fail("producer replayed"))
    assert assess_endpoint_identifiability(retained[2][-1], analysis_id="rank.retained").exact_rank == 2
    assessed = assess_concentration_response(*retained, assessment_id="response.retained")
    assert assessed.disposition is A.SATISFIED and assessed.complete_census
    assert all(row.specificity_from_flux is None for row in assessed.findings[:3])
    assert all(row.specificity_from_flux.fraction == F(18, 5) for row in assessed.findings[3:])
    assert decode_canonical_bytes(assessed.canonical_bytes(), ConcentrationResponseAssessment, maximum_bytes=100_000) == assessed


@pytest.mark.parametrize("change", ("omit", "reorder", "scope", "zero-return", "wrong-sensitivity"))
def test_concentration_census_retains_failed_unknown_and_scope_changed_results(retained, change):
    rates, queries, original = retained
    results = original
    if change == "omit":
        results = original[:-1]
    elif change == "reorder":
        results = tuple(reversed(original))
    elif change == "scope":
        results = (*original[:-1], solve_four_state(replace(rates, a=D(3)), queries[-1], result_id="result.changed"))
    elif change == "zero-return":
        results = (*original[:-1], replace(original[-1], oxygenation_events_per_site_s=Exact.of(0)))
    else:
        last = original[-1]
        derivative = replace(last.sensitivities[0], derivative=Exact.of(3))
        results = (*original[:-1], replace(last, sensitivities=(derivative, *last.sensitivities[1:])))
    assessed = assess_concentration_response(rates, queries, results, assessment_id="response.adverse")
    assert len(assessed.findings) == len(results)
    assert assessed.disposition is (A.UNEVALUABLE if change in {"omit", "reorder"} else A.FALSIFIED)
    if change == "zero-return":
        assert assessed.findings[-1].specificity_from_flux is None
        assert assessed.findings[-1].numerical_gate is A.FALSIFIED
    if change == "wrong-sensitivity":
        with pytest.raises(ValueError, match="failed independent"):
            assess_endpoint_identifiability(results[-1], analysis_id="rank.bad")


def test_no_concentration_data_or_only_one_mixed_query_is_unevaluable(retained):
    rates, queries, results = retained
    assert assess_concentration_response(rates, queries, (), assessment_id="response.none").disposition is A.UNEVALUABLE
    assert assess_concentration_response(rates, queries[-1:], results[-1:], assessment_id="response.one").disposition is A.UNEVALUABLE


def lumping(generator):
    source = disclosed_supply().case.sources[0]
    return MarkovLumpingSelection("lumping.disclosed", source, ("state.a", "state.b", "state.c"),
        tuple(tuple(Exact.of(F(value)) for value in row) for row in generator), ((0, 1), (2,)), source, source)


def test_exact_lumping_and_small_but_nonzero_outgoing_return_error_have_distinct_findings():
    selected = lumping(((-3, 1, 2), (4, -6, 2), (1, 3, -4)))
    assessed = assess_strong_lumping(selected, assessment_id="lumping.exact")
    assert assessed.disposition is A.SATISFIED and assessed.violations == ()
    delta = F(1, 10**30)
    changed = lumping(((-3, 1, 2), (4, -6 - delta, 2 + delta), (1, 3, -4)))
    failed = assess_strong_lumping(changed, assessment_id="lumping.changed")
    assert failed.disposition is A.FALSIFIED
    assert tuple(row[3].fraction for row in failed.violations) == (-delta, delta)
    assert decode_canonical_bytes(failed.canonical_bytes(), StrongLumpingAssessment, maximum_bytes=100_000) == failed
    with pytest.raises(ValueError, match="counterexample"):
        replace(failed, violations=())


def test_lumping_rejects_state_denominator_clock_and_generator_changes():
    selected = lumping(((-3, 1, 2), (4, -6, 2), (1, 3, -4)))
    with pytest.raises(ValueError, match="partition"):
        replace(selected, blocks=((0, 1),))
    with pytest.raises(ValueError, match="physical time"):
        replace(selected, generator_unit="step^-1")
    with pytest.raises(ValueError, match="conservation"):
        lumping(((-3, 1, 3), (4, -6, 2), (1, 3, -4)))
