"""Independent scalar and information-schedule falsifiers for the RC chain.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import replace
from decimal import Decimal

import pytest

from empirical_lawhood.adapters.methods.rc_prerequisite_chain.contracts import (
    ARM_IDS,
    EVIDENCE_ROLE,
    VARIANT_IDS,
)
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import (
    decide_preparation,
    default_chain_config,
    evaluate_unit,
    summarize_chain,
    verify_unit_result,
)


@pytest.fixture(scope="module")
def chain():
    config = default_chain_config()
    results = tuple(evaluate_unit(config, unit.unit_id) for unit in config.units)
    return config, results


def _case(result, variant):
    return next(case for case in result.cases if case.variant_id == variant)


def _arm(case, name="selected"):
    return next(arm for arm in case.arms if arm.arm_id == name)


def _initials(config):
    return {unit.unit_id: float(unit.initial_voltage_volts) for unit in config.units}


def _scalar_voltage(protocol, initial, arm, time):
    """KCL solution without a production solver, policy, or decay helper."""
    capacitance = float(protocol.capacitance_farads)
    left_resistance = float(protocol.left_source_resistance_ohms)
    right_resistance = float(protocol.right_source_resistance_ohms)
    conductance = 1 / left_resistance + 1 / right_resistance
    rate = conductance / capacitance
    decision = float(protocol.decision_seconds)
    if time <= decision:
        return initial * math.exp(-rate * time)
    at_decision = initial * math.exp(-rate * decision)
    prep_equilibrium = (
        float(arm.left_voltage_volts) / left_resistance
        + float(arm.right_voltage_volts) / right_resistance
    ) / conductance
    duration = float(arm.duration_seconds)
    cutoff = decision + duration
    if time <= cutoff:
        return prep_equilibrium + (at_decision - prep_equilibrium) * math.exp(
            -rate * (time - decision)
        )
    at_cutoff = prep_equilibrium + (at_decision - prep_equilibrium) * math.exp(
        -rate * duration
    )
    response_equilibrium = (
        float(protocol.response_left_voltage_volts) / left_resistance
        + float(protocol.response_right_voltage_volts) / right_resistance
    ) / conductance
    return response_equilibrium + (at_cutoff - response_equilibrium) * math.exp(
        -rate * (time - cutoff)
    )


def test_complete_development_census_and_distinct_claim_counts(chain):
    config, results = chain
    assert tuple(unit.initial_voltage_volts for unit in config.units) == (
        Decimal("-2"), Decimal("-1.2"), Decimal("-0.4"), Decimal("-0.05"),
        Decimal("0.05"), Decimal("0.15"), Decimal("0.25"), Decimal("0.4"),
        Decimal("1.2"), Decimal("2"), Decimal("3"),
    )
    assert len(results) == 11
    assert {result.unit_id for result in results} == {unit.unit_id for unit in config.units}
    assert all(tuple(case.variant_id for case in result.cases) == VARIANT_IDS for result in results)
    assert all(tuple(arm.arm_id for arm in _case(result, "adequate").arms) == ARM_IDS for result in results)
    assert all(result.evidence_role == EVIDENCE_ROLE for result in results)
    adequate = tuple(_case(result, "adequate") for result in results)
    assert Counter(case.measurement_state for case in adequate) == {"PASSED": 11}
    assert Counter(_arm(case).preparation_state for case in adequate) == {
        "PASSED": 10, "REFUSED": 1,
    }
    assert Counter(_arm(case).joined_state for case in adequate) == {
        "PASSED": 10, "REFUSED": 1,
    }
    summary = summarize_chain(config, results)
    assert summary.unit_count == 11
    assert summary.nested_variant_count == 110
    assert summary.nested_arm_count == 143
    assert summary.nested_view_count == sum(
        len(result.source_panels) + sum(len(arm.native_panels) for case in result.cases for arm in case.arms)
        for result in results
    )
    assert summary.unsupported_prerequisites
    with pytest.raises(ValueError):
        summarize_chain(config, results[:-1])


def test_finite_observation_rule_uses_interval_and_declared_drift(chain):
    config, results = chain
    expected_durations = {
        -2.0: 1.5, -1.2: 1.5, -0.4: 1.0, -0.05: 0.0, 0.05: 0.0,
        0.15: 0.25, 0.25: 0.5, 0.4: 1.0, 1.2: 1.5, 2.0: 1.5,
    }
    for result in results:
        case = _case(result, "adequate")
        initial = _initials(config)[result.unit_id]
        assert case.observation.sample_seconds == Decimal(0)
        assert case.observation.available_seconds == Decimal("0.04")
        assert case.expectation.decision_seconds == Decimal("0.05")
        decision = decide_preparation(config.protocol, case.expectation, case.observation)
        assert decision == case.decision
        if initial == 3.0:
            assert decision.disposition == "REFUSED"
            assert decision.duration_seconds is None
            continue
        duration = float(decision.duration_seconds)
        assert duration == expected_durations[initial]
        report = float(case.observation.reported_voltage_volts)
        radius = float(case.observation.radius_volts)
        decay = math.exp(-2 * (0.05 + duration))
        assert float(decision.prepared_lower_volts) == pytest.approx((report - radius) * decay, abs=2e-12)
        assert float(decision.prepared_upper_volts) == pytest.approx((report + radius) * decay, abs=2e-12)
        assert max(abs(report - radius), abs(report + radius)) * decay < 0.1
        earlier = [float(value) for value in config.protocol.preparation_durations_seconds if float(value) < duration]
        assert all(max(abs(report - radius), abs(report + radius)) * math.exp(-2 * (0.05 + value)) > 0.1 for value in earlier)


def test_native_states_endpoints_and_currents_match_independent_scalar_equation(chain):
    config, results = chain
    protocol = config.protocol
    initial_by_id = _initials(config)
    for result in results:
        initial = initial_by_id[result.unit_id]
        for panel in result.source_panels:
            tolerance = 2e-12 if panel.view_id == "matrix-exponential" else float(protocol.maximum_view_defect_volts)
            for time, row in zip(panel.times_seconds, panel.node_voltages_volts, strict=True):
                assert float(row[0]) == pytest.approx(initial * math.exp(-2 * float(time)), abs=tolerance)
        for case in result.cases:
            for arm in case.arms:
                assert float(arm.predicted_endpoint_volts) == pytest.approx((1 - math.exp(-2)) / 2, abs=2e-12)
                if arm.native_model is None:
                    assert arm.actual_endpoint_volts is None
                    continue
                model = arm.native_model
                assert model.initial_voltages_volts == (Decimal(str(initial)),)
                assert model.capacitances_farads == (Decimal(1),)
                assert model.left_source_resistance_ohms == Decimal(1)
                assert model.right_termination_resistance_ohms == Decimal(1)
                cutoff = float(protocol.decision_seconds + arm.duration_seconds)
                prepared = _scalar_voltage(protocol, initial, arm, cutoff)
                endpoint = _scalar_voltage(protocol, initial, arm, cutoff + float(protocol.response_horizon_seconds))
                assert arm.actual_support == (-0.1 <= prepared <= 0.1)
                assert float(arm.actual_endpoint_volts) == pytest.approx(endpoint, abs=2e-12)
                assert arm.endpoint_within_task == (abs(endpoint - (1 - math.exp(-2)) / 2) <= 0.02)
                for panel in arm.native_panels:
                    tolerance = 2e-12 if panel.view_id == "matrix-exponential" else float(protocol.maximum_view_defect_volts)
                    for time, row, left_current, right_current in zip(
                        panel.times_seconds, panel.node_voltages_volts,
                        panel.left_boundary_currents_amperes,
                        panel.right_boundary_currents_amperes, strict=True,
                    ):
                        voltage = float(row[0])
                        assert voltage == pytest.approx(_scalar_voltage(protocol, initial, arm, float(time)), abs=tolerance)
                        boundary = next((segment for segment in model.action_segments if segment.start_seconds <= time < segment.end_seconds), None)
                        left = float(boundary.left_voltage_volts) if boundary else 0.0
                        right = float(boundary.right_voltage_volts) if boundary else 0.0
                        assert float(left_current) == pytest.approx(left - voltage, abs=2e-12)
                        assert float(right_current) == pytest.approx(right - voltage, abs=2e-12)


def test_package_admission_is_distinct_from_coincidental_task_success(chain):
    config, results = chain
    by_initial = {_initials(config)[result.unit_id]: result for result in results}
    unchanged = _arm(_case(by_initial[0.15], "adequate"), "unchanged")
    assert unchanged.actual_support is False
    assert unchanged.endpoint_within_task is True
    assert unchanged.joined_state != "PASSED"
    assert unchanged.response_role == "DECLINED_DEVELOPMENT_ASSAY"
    half = _arm(_case(by_initial[0.4], "adequate"), "insufficient")
    assert half.actual_support is False
    assert half.endpoint_within_task is True
    assert half.joined_state != "PASSED"
    for name in ("unchanged", "wrong", "insufficient"):
        assert sum(_arm(_case(result, "adequate"), name).actual_support is True for result in results) == 2


def test_bad_measurement_coverage_cannot_be_repaired_with_oracle_truth(chain):
    config, results = chain
    initial_by_id = _initials(config)
    for result in results:
        biased = _case(result, "biased")
        initial = initial_by_id[result.unit_id]
        assert abs(initial - float(biased.observation.reported_voltage_volts)) > float(biased.observation.radius_volts)
        assert biased.measurement_state == "FAILED"
        assert _arm(biased).joined_state != "PASSED"
        assert decide_preparation(config.protocol, biased.expectation, biased.observation) == biased.decision
        adequate = _case(result, "adequate")
        coarse = _case(result, "coarsened")
        assert abs(initial - float(coarse.observation.reported_voltage_volts)) <= float(coarse.observation.radius_volts)
        assert coarse.measurement_state != "PASSED"
        assert coarse.decision.disposition == "REFUSED"
        if initial == 0.4:
            assert adequate.decision.duration_seconds == Decimal(1)
            assert biased.decision.duration_seconds == Decimal(0)
            assert _arm(biased).prospective_support is True
            assert _arm(biased).actual_support is False


def test_individually_adequate_components_can_miss_joined_deadline(chain):
    _, results = chain
    conflicts = tuple(_case(result, "resource-conflict") for result in results)
    assert Counter(case.measurement_state for case in conflicts) == {"PASSED": 11}
    assert Counter(_arm(case).preparation_state for case in conflicts) == {"PASSED": 10, "REFUSED": 1}
    assert Counter(_arm(case).joined_state for case in conflicts) == {"PASSED": 4, "FAILED": 6, "REFUSED": 1}
    for case in conflicts:
        arm = _arm(case)
        if arm.joined_state == "FAILED":
            assert arm.actual_support is True
            assert arm.endpoint_within_task is True
            assert arm.completion_seconds > arm.deadline_seconds


def test_unavailable_or_unsupported_inputs_remain_in_the_complete_census(chain):
    _, results = chain
    for result in results:
        missing = _case(result, "missing")
        assert missing.observation is None
        assert missing.decision.disposition == "UNEVALUABLE"
        assert _arm(missing).joined_state == "UNEVALUABLE"
        for variant in ("late", "wrong-binding", "wrong-receiver", "wrong-units", "coarsened"):
            case = _case(result, variant)
            assert case.decision.disposition == "REFUSED"
            assert _arm(case).native_model is None
            assert not _arm(case).native_panels
        physical = _case(result, "physical-stop")
        assert physical.decision.disposition == "UNSUPPORTED"
        assert _arm(physical).joined_state == "UNSUPPORTED"
        assert _arm(physical).native_model is None


@pytest.mark.parametrize("mutation", [
    {"available_seconds": Decimal("0.0500000001")},
    {"sample_seconds": Decimal("0.01")},
    {"voltage_unit": "mV"},
    {"quantity_id": "left-source-voltage"},
    {"receiver_id": "left-source-boundary"},
    {"unit_id": "wrong-model-preparation"},
    {"model_sha256": "0" * 64},
    {"source_sha256": "0" * 64},
    {"source_binding_sha256": "0" * 64},
    {"config_sha256": "0" * 64},
])
def test_information_quantity_and_source_joins_refuse_before_preparation(chain, mutation):
    config, results = chain
    case = _case(results[0], "adequate")
    bad = replace(case.observation, **mutation)
    decision = decide_preparation(config.protocol, case.expectation, bad)
    assert decision.disposition == "REFUSED"
    assert decision.duration_seconds is None


@pytest.mark.parametrize("requirement_mutation,report_mutation", [
    ({"voltage_unit": "mV"}, {"voltage_unit": "mV"}),
    ({"quantity_id": "left-source-voltage"}, {"quantity_id": "left-source-voltage"}),
    ({"receiver_id": "left-source-boundary"}, {"receiver_id": "left-source-boundary"}),
    ({"sample_seconds": Decimal("0.01")}, {"sample_seconds": Decimal("0.01")}),
    ({"decision_seconds": Decimal("0.06")}, {"available_seconds": Decimal("0.06")}),
    ({"maximum_radius_volts": Decimal("0.25")}, {"radius_volts": Decimal("0.25")}),
])
def test_matching_labels_cannot_redefine_the_frozen_consumer(chain, requirement_mutation, report_mutation):
    config, results = chain
    case = _case(results[0], "adequate")
    changed_requirement = replace(case.expectation, **requirement_mutation)
    changed_report = replace(case.observation, **report_mutation)
    with pytest.raises(ValueError):
        decide_preparation(config.protocol, changed_requirement, changed_report)


def test_all_choices_commit_before_any_development_oracle_assessment(monkeypatch):
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain import science

    config = default_chain_config()
    config = replace(config, units=(config.units[7],))
    decisions = []
    original_decide = science.decide_preparation
    original_scalar = science._scalar_state
    original_measurement = science._measurement_state

    def committed_decision(*args, **kwargs):
        decision = original_decide(*args, **kwargs)
        decisions.append(decision)
        return decision

    def oracle_after_commit(*args, **kwargs):
        assert len(decisions) == len(VARIANT_IDS), "Oracle state was inspected before every assigned choice committed"
        return original_scalar(*args, **kwargs)

    def measurement_after_commit(*args, **kwargs):
        assert len(decisions) == len(VARIANT_IDS), "Measurement truth was inspected before every assigned choice committed"
        return original_measurement(*args, **kwargs)

    monkeypatch.setattr(science, "decide_preparation", committed_decision)
    monkeypatch.setattr(science, "_scalar_state", oracle_after_commit)
    monkeypatch.setattr(science, "_measurement_state", measurement_after_commit)
    evaluate_unit(config, config.units[0].unit_id)


def test_retained_verification_uses_evidence_without_native_reexecution(chain, monkeypatch):
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain import science

    config, results = chain

    def native_forbidden(*args, **kwargs):
        raise AssertionError("Retained verification reacquired numerical evidence")

    monkeypatch.setattr(science, "_execute", native_forbidden)
    for result in results:
        verify_unit_result(config, result)
    result = results[0]
    adequate = _case(result, "adequate")
    changed = replace(adequate, observation=replace(adequate.observation, available_seconds=Decimal("0.06")))
    forged = replace(result, cases=tuple(changed if case.variant_id == "adequate" else case for case in result.cases))
    with pytest.raises(ValueError):
        verify_unit_result(config, forged)
    changed = replace(adequate, decision=replace(adequate.decision, duration_seconds=adequate.decision.duration_seconds / 2))
    forged = replace(result, cases=tuple(changed if case.variant_id == "adequate" else case for case in result.cases))
    with pytest.raises(ValueError):
        verify_unit_result(config, forged)
    selected = _arm(adequate)
    changed_arm = replace(selected, actual_endpoint_volts=selected.actual_endpoint_volts + Decimal("0.001"))
    changed = replace(adequate, arms=tuple(changed_arm if arm.arm_id == "selected" else arm for arm in adequate.arms))
    forged = replace(result, cases=tuple(changed if case.variant_id == "adequate" else case for case in result.cases))
    with pytest.raises(ValueError):
        verify_unit_result(config, forged)


def test_failed_source_conformance_retains_native_evidence_and_every_claim(monkeypatch):
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain import science

    config = default_chain_config()
    config = replace(config, units=(config.units[7],), protocol=replace(
        config.protocol, maximum_view_defect_volts=Decimal("1e-15"),
    ))
    result = evaluate_unit(config, config.units[0].unit_id)
    assert result.source_failure_reason_codes == ("NUMERICAL_SOURCE_CONFORMANCE_FAILED",)
    assert len(result.source_panels) == 2
    assert any(not panel.numerical_summary.converged for panel in result.source_panels)
    assert tuple(case.variant_id for case in result.cases) == VARIANT_IDS
    assert all(case.measurement_state == "UNEVALUABLE" for case in result.cases)
    assert sum(len(case.arms) for case in result.cases) == 13
    assert all(arm.joined_state == "UNEVALUABLE" for case in result.cases for arm in case.arms)

    def native_forbidden(*args, **kwargs):
        raise AssertionError("Failed-source verification reacquired numerical evidence")

    monkeypatch.setattr(science, "_execute", native_forbidden)
    verify_unit_result(config, result)
    summary = summarize_chain(config, (result,))
    assert summary.unit_count == 1
    assert summary.nested_variant_count == 10
    assert summary.nested_arm_count == 13
    assert summary.nested_view_count == 2
    assert all(count.count == 0 for count in summary.outcome_counts if count.state != "UNEVALUABLE")
