# SPDX-License-Identifier: MPL-2.0
"""Conditional paired propagation, independently assessed without acquisition."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import validate_paired_chemical_selection
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_decision, disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import PairedPrediction, predict_paired_rates
from empirical_lawhood.domains.rubisco.rubisco_response.prediction_assessment import PairedPredictionAssessment, assess_paired_prediction
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition


def test_paired_effect_and_independent_assessor_never_call_the_producer(monkeypatch):
    supply = disclosed_supply()
    product = predict_paired_rates(supply, prediction_id="prediction.exposed")
    with monkeypatch.context() as patch:
        def forbidden(*args, **kwargs):
            raise AssertionError("independent assessment called a producer")
        patch.setattr("empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model.solve_four_state", forbidden)
        patch.setattr("empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.science.stationary", forbidden)
        assessment = assess_paired_prediction(supply, product, disclosed_decision(supply), assessment_id="assessment.exposed")
    assert assessment.disposition is AssessmentDisposition.SATISFIED
    assert assessment.conditional_action == "ADVANCE"
    point = product.support.scenarios[0].region.values[0]
    assert point.turnover_ratio == D("1.5")
    assert point.specificity_ratio == 1  # Imposed common gating: conditional cancellation only.
    for record, kind in ((supply, type(supply)), (product, PairedPrediction), (assessment, PairedPredictionAssessment)):
        assert decode_canonical_bytes(record.canonical_bytes(), kind, maximum_bytes=2_000_000) == record


@pytest.mark.parametrize("state", ["UNKNOWN", "FAILED"])
def test_missing_alternatives_survive_prediction_and_independent_readout(state):
    supply = disclosed_supply(scenario_states=("AVAILABLE", state))
    product = predict_paired_rates(supply, prediction_id="prediction.missing")
    assessment = assess_paired_prediction(supply, product, disclosed_decision(supply), assessment_id="assessment.missing")
    assert assessment.disposition is AssessmentDisposition.SATISFIED
    assert assessment.conditional_action == "HOLD"
    assert product.support.scenarios[1].original_state == state
    assert assessment.decision.unresolved_requirement_ids == ("requirement.scenario.02",)


@pytest.mark.parametrize("change", ["drop-point", "change-rate", "bad-balance", "drop-source", "hide-failure"])
def test_retained_correspondence_or_mathematics_tampering_cannot_advance(change):
    supply = disclosed_supply(scenario_states=("AVAILABLE", "FAILED"))
    product = predict_paired_rates(supply, prediction_id="prediction.tamper")
    point = product.points[0]
    if change == "drop-point":
        product = replace(product, points=())
    elif change == "change-rate":
        point = replace(point, wild_type=replace(point.wild_type, rates=replace(point.wild_type.rates, a=D(3))))
        product = replace(product, points=(point,))
    elif change == "bad-balance":
        point = replace(point, wild_type=replace(point.wild_type, populations=tuple(Exact.of(0) for _ in range(4))))
        product = replace(product, points=(point,))
    elif change == "drop-source":
        product = replace(product, support=replace(product.support, shared_sources=()))
    else:
        product = replace(product, support=replace(product.support, expected_scenario_ids=("scenario.01",),
            scenarios=product.support.scenarios[:1]))
    assessment = assess_paired_prediction(supply, product, disclosed_decision(supply), assessment_id="assessment.tamper")
    assert assessment.disposition is AssessmentDisposition.FALSIFIED
    assert assessment.conditional_action == "HOLD" and assessment.decision is None


def test_no_change_cannot_acquire_a_finite_rate_effect():
    supply = disclosed_supply(case_role="NO_CHANGE")
    product = predict_paired_rates(supply, prediction_id="prediction.no-change")
    assert product.support.scenarios[0].region.values[0].turnover_ratio == 1
    changed = disclosed_supply().scenarios[0].points
    scenario = supply.scenarios[0]
    rows = tuple(replace(row, mutant_bounds=(D(4), D(4))) if row.parameter == "a" else row
                 for row in scenario.ledger.bindings)
    with pytest.raises(ValueError, match="no-change"):
        replace(supply, scenarios=(replace(scenario, points=changed, ledger=replace(scenario.ledger, bindings=rows)),))


def test_unknown_rate_needs_an_explicit_requirement_and_cannot_acquire_a_point_estimate():
    supply = disclosed_supply()
    original = supply.scenarios[0]
    unidentified = replace(original.ledger.bindings[0], evidence_kind="UNIDENTIFIED",
        wild_type_bounds=None, mutant_bounds=None, mutation_dependence="UNIDENTIFIED",
        required_relative_accuracy=None, unresolved_requirement_ids=("requirement.rate.a",))
    ledger = replace(original.ledger, bindings=(unidentified, *original.ledger.bindings[1:]))
    with pytest.raises(ValueError, match="sourced ledger"):
        replace(original, ledger=ledger)
    unknown = replace(original, ledger=ledger, points=(), original_state="UNKNOWN",
                      unresolved_requirement_ids=("requirement.rate.a",))
    supplied = replace(supply, scenarios=(unknown,))
    product = predict_paired_rates(supplied, prediction_id="prediction.unidentified")
    assert not product.points
    assessment = assess_paired_prediction(supplied, product, disclosed_decision(supplied),
                                         assessment_id="assessment.unidentified")
    assert assessment.conditional_action == "HOLD"


def test_all_site_chemistry_and_temperature_are_distinct_explicit_selections():
    supply = disclosed_supply()
    chemistry = supply.context.chemistry
    with pytest.raises(ValueError, match="eight"):
        replace(chemistry, sites=chemistry.sites[:-1])
    inhibited = replace(chemistry, sites=(replace(chemistry.sites[0], ligand_state="CABP"), *chemistry.sites[1:]))
    with pytest.raises(ValueError, match="inhibited"):
        replace(supply.context, chemistry=inhibited)
    wrong_mapping = replace(chemistry, sites=(replace(chemistry.sites[0], catalytic_lysine_position_1based=1), *chemistry.sites[1:]))
    with pytest.raises(ValueError, match="catalytic lysine"):
        validate_paired_chemical_selection(supply.case, wrong_mapping)
    historical_temperature = replace(supply.context, temperature_k=D(298))
    assert historical_temperature.identity != supply.context.identity
    with pytest.raises(ValueError, match="context"):
        replace(supply, context=historical_temperature)
    with pytest.raises(ValueError, match="separate assessment"):
        replace(supply.context, temperature_selection="ASSESSED_CONVERSION")


def test_empty_available_support_and_unresolved_chemical_state_never_advance():
    supply = disclosed_supply()
    empty = replace(supply, scenarios=(replace(supply.scenarios[0], points=()),))
    product = predict_paired_rates(empty, prediction_id="prediction.empty")
    result = assess_paired_prediction(empty, product, disclosed_decision(empty), assessment_id="assessment.empty")
    assert result.conditional_action == "HOLD"
    selected = replace(supply, prerequisite_requirement_ids=("requirement.physical-admission",))
    product = predict_paired_rates(selected, prediction_id="prediction.physical")
    result = assess_paired_prediction(selected, product, disclosed_decision(selected), assessment_id="assessment.physical")
    assert result.decision.unresolved_requirement_ids == ("requirement.physical-admission",)
    assert result.conditional_action == "HOLD"
