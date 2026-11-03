"""Frozen RC observation, preparation and joined-use experiments.

The decision accepts only a truth-free consumer contract and observer output.
Independent scalar checks inspect oracle states after that decision commits.
Numerical imports occur only during explicit execution.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
from math import isfinite
from struct import pack

from empirical_lawhood.adapters.simulators.rc_ladder_response.contracts import (
    ResistorCapacitorLadderActionSegment,
    ResistorCapacitorLadderModelConfig,
    ResistorCapacitorLadderNativePanel,
    ResistorCapacitorLadderNumericalCheck,
    ResistorCapacitorLadderStudyConfig,
)
from empirical_lawhood.kernel.serialization import canonical_json_bytes

from .contracts import (
    ARM_IDS, EVIDENCE_ROLE, OUTCOME_STATES, VARIANT_IDS,
    RCChainArmResult, RCChainCaseResult, RCChainDecision, RCChainDesignProof,
    RCChainObservation, RCChainObservationExpectation, RCChainOutcomeCount,
    RCChainProtocol, RCChainSummary, RCChainUnit, RCChainUnitResult,
    RCPrerequisiteChainConfig, decay_factor, fixed_decimal_context,
)

D = Decimal


@fixed_decimal_context
def default_chain_config() -> RCPrerequisiteChainConfig:
    """The complete DC1 exposed roster and choices, without native execution."""
    a = decay_factor(D(2), D(1))
    protocol = RCChainProtocol(
        protocol_id="rc-prerequisite-chain.dc1-v1", capacitance_farads=D(1),
        left_source_resistance_ohms=D(1), right_source_resistance_ohms=D(1),
        receiver_id="capacitor-node-0", quantity_id="capacitor-node-voltage", voltage_unit="V",
        sample_seconds=D(0), available_seconds=D(".04"), decision_seconds=D(".05"),
        observation_error_volts=D(".005"), observation_radius_volts=D(".01"),
        maximum_observation_radius_volts=D(".01"), coarsened_radius_volts=D(".25"),
        biased_error_volts=D("-.4"), late_available_seconds=D(".06"),
        preparation_durations_seconds=(D(0), D(".25"), D(".5"), D(1), D("1.5")),
        support_lower_volts=D("-.1"), support_upper_volts=D(".1"), support_guard_volts=D("1e-12"),
        response_left_voltage_volts=D(1), response_right_voltage_volts=D(0), response_horizon_seconds=D(1),
        prediction_initial_voltage_volts=D(0), response_coefficient_a=a,
        response_coefficient_b_volts=(1 - a) / 2, maximum_task_error_volts=D(".02"),
        completion_deadline_seconds=D("2.60"), conflict_deadline_seconds=D("1.80"),
        output_step_seconds=D(".01"), backward_euler_maximum_step_seconds=D(".0001"),
        maximum_view_defect_volts=D(".005"), maximum_charge_rate_defect_amperes=D(".002"),
        maximum_analytic_defect_volts=D("1e-10"), maximum_analytic_current_defect_amperes=D("1e-10"), maximum_elapsed_seconds=D(600),
        maximum_native_steps=2_000_000, maximum_output_bytes=16 * 1024**2,
        maximum_aggregate_output_bytes=256 * 1024**2, minimum_free_bytes=64 * 1024**2,
    )
    initials = ("-2", "-1.2", "-.4", "-.05", ".05", ".15", ".25", ".4", "1.2", "2", "3")
    return RCPrerequisiteChainConfig("rc-prerequisite-chain.dc1-v1", protocol,
        tuple(RCChainUnit(f"rc-chain-unit-{index:02d}", D(value)) for index, value in enumerate(initials)))


@fixed_decimal_context
def prove_chain(config: RCPrerequisiteChainConfig) -> RCChainDesignProof:
    """Bound the frozen design without observing sources or constructing providers."""
    p = config.protocol
    for value in (p.capacitance_farads, p.left_source_resistance_ohms, p.right_source_resistance_ohms,
                  p.backward_euler_maximum_step_seconds):
        if not isfinite(float(value)) or float(value) <= 0:
            raise ValueError("RC native operands must remain positive and finite in the selected solver representation")
    for unit in config.units:
        if not isfinite(float(unit.initial_voltage_volts)):
            raise ValueError("RC native unit state is not finite in the selected solver representation")
    capacitance = float(p.capacitance_farads)
    left_g, right_g = 1 / float(p.left_source_resistance_ohms), 1 / float(p.right_source_resistance_ohms)
    inverse_c = 1 / capacitance
    conductance = left_g + right_g
    for coefficient in (inverse_c, left_g, right_g, conductance, inverse_c * conductance,
                        conductance / capacitance, left_g / capacitance, right_g / capacitance):
        if not isfinite(coefficient) or coefficient <= 0:
            raise ValueError("RC derived native conductance or state coefficient is not positive and finite")
    left_u, right_u = float(p.response_left_voltage_volts), float(p.response_right_voltage_volts)
    left_forcing = left_g / capacitance * left_u
    right_forcing = right_g / capacitance * right_u
    if not all(isfinite(value) for value in (left_u, right_u, left_forcing, right_forcing, left_forcing + right_forcing)):
        raise ValueError("RC native response boundaries or forcing are not finite in the selected solver representation")

    def bound_grid(horizon: Decimal, *boundaries: Decimal) -> int:
        grid_intervals = horizon / p.output_step_seconds
        if grid_intervals > 4092:
            raise ValueError("RC output grid exceeds its frozen bounded work budget")
        grid = _grid(p, horizon, *boundaries)
        clocks = tuple(float(value) for value in grid)
        if any(not isfinite(value) for value in clocks) or any(right <= left for left, right in zip(clocks, clocks[1:], strict=False)):
            raise ValueError("RC exact output clocks collapse or reverse in the native solver representation")
        effective_step = min(p.backward_euler_maximum_step_seconds,
            min(right - left for left, right in zip(grid, grid[1:], strict=False)))
        if not isfinite(float(effective_step)) or float(effective_step) <= 0:
            raise ValueError("RC effective solver step collapses in the selected native representation")
        raw_steps = horizon / effective_step
        if raw_steps > p.maximum_native_steps:
            raise ValueError("RC effective solver step exceeds its frozen bounded work budget")
        # Each output interval can add a final partial floating-point step.
        return int(raw_steps.to_integral_value(rounding=ROUND_CEILING)) + len(grid)

    source_steps = bound_grid(p.decision_seconds)
    possible_durations = {D(0), *p.preparation_durations_seconds,
                          *(duration / 2 for duration in p.preparation_durations_seconds)}
    arm_steps = max(bound_grid(p.decision_seconds + duration + p.response_horizon_seconds,
        p.decision_seconds, p.decision_seconds + duration) for duration in possible_durations)
    # Four nominal arms, biased selected and timing selected; source is one
    # further nested numerical pair. All other variants refuse before native use.
    per_unit_steps = 6 * arm_steps + source_steps
    total_steps = per_unit_steps * len(config.units)
    if total_steps > p.maximum_native_steps:
        raise ValueError("RC compiled native step bound exceeds its frozen work budget")
    return RCChainDesignProof(config.fingerprint(), len(config.units), len(VARIANT_IDS),
        len(config.units) * (len(ARM_IDS) + len(VARIANT_IDS) - 1), len(config.units) * 14,
        total_steps, p.maximum_output_bytes, p.maximum_aggregate_output_bytes)


def _unit(config: RCPrerequisiteChainConfig, unit_id: str) -> RCChainUnit:
    for unit in config.units:
        if unit.unit_id == unit_id:
            return unit
    raise ValueError("RC requested unit is outside the frozen complete census")


def _grid(p: RCChainProtocol, horizon: Decimal, *boundaries: Decimal) -> tuple[Decimal, ...]:
    count = int(horizon // p.output_step_seconds)
    return tuple(sorted({*(D(index) * p.output_step_seconds for index in range(count + 1)), horizon, *boundaries}))


def _model(config: RCPrerequisiteChainConfig, unit: RCChainUnit, *, model_id: str,
           duration: Decimal | None = None, prep_left: Decimal = D(0), prep_right: Decimal = D(0)) -> ResistorCapacitorLadderModelConfig:
    p = config.protocol
    segments = [ResistorCapacitorLadderActionSegment("00-drift", D(0), p.decision_seconds, D(0), D(0))]
    if duration is None:
        horizon = p.decision_seconds
        boundaries: tuple[Decimal, ...] = ()
    else:
        cutoff = p.decision_seconds + duration
        horizon = cutoff + p.response_horizon_seconds
        if duration:
            segments.append(ResistorCapacitorLadderActionSegment("10-preparation", p.decision_seconds,
                cutoff, prep_left, prep_right))
        segments.append(ResistorCapacitorLadderActionSegment("20-response", cutoff, horizon,
            p.response_left_voltage_volts, p.response_right_voltage_volts))
        boundaries = (p.decision_seconds, cutoff)
    return ResistorCapacitorLadderModelConfig(model_id, 1, (p.capacitance_farads,), (),
        p.left_source_resistance_ohms, p.right_source_resistance_ohms, (unit.initial_voltage_volts,),
        tuple(segments), _grid(p, horizon, *boundaries), True)


def _source(config: RCPrerequisiteChainConfig, unit: RCChainUnit) -> ResistorCapacitorLadderModelConfig:
    return _model(config, unit, model_id=f"{config.config_id}.{unit.unit_id}.measurement-source")


def _expectation(config: RCPrerequisiteChainConfig, unit: RCChainUnit,
                 source: ResistorCapacitorLadderModelConfig) -> RCChainObservationExpectation:
    p = config.protocol
    model_digest = sha256(canonical_json_bytes((p.capacitance_farads, p.left_source_resistance_ohms,
        p.right_source_resistance_ohms, p.receiver_id, p.quantity_id, p.voltage_unit))).hexdigest()
    # This binds the declared source, not a scientific custody authority. Actual
    # publications and completion receipts remain owned by the API artifact plane.
    binding = sha256(canonical_json_bytes((config.fingerprint(), unit.unit_id, source.fingerprint()))).hexdigest()
    return RCChainObservationExpectation(unit.unit_id, config.fingerprint(), model_digest, source.fingerprint(),
        binding, p.receiver_id, p.quantity_id, p.voltage_unit, p.sample_seconds, p.decision_seconds,
        p.maximum_observation_radius_volts)


@fixed_decimal_context
def _observation(p: RCChainProtocol, expected: RCChainObservationExpectation,
                 sampled_voltage: Decimal, variant: str) -> RCChainObservation | None:
    if variant in {"missing", "physical-stop"}:
        return None
    observation = RCChainObservation(f"{expected.unit_id}.{variant}.observation", expected.unit_id,
        expected.config_sha256, expected.model_sha256, expected.source_sha256, expected.source_binding_sha256,
        p.receiver_id, p.quantity_id, p.voltage_unit, p.sample_seconds, p.available_seconds,
        sampled_voltage + (p.biased_error_volts if variant == "biased" else p.observation_error_volts),
        p.coarsened_radius_volts if variant == "coarsened" else p.observation_radius_volts)
    if variant == "late":
        observation = replace(observation, available_seconds=p.late_available_seconds)
    elif variant == "wrong-units":
        observation = replace(observation, voltage_unit="mV")
    elif variant == "wrong-receiver":
        observation = replace(observation, receiver_id="left-source", quantity_id="left-source-voltage")
    elif variant == "wrong-binding":
        observation = replace(observation, source_sha256="0" * 64)
    return observation


@fixed_decimal_context
def _interval(p: RCChainProtocol, lower: Decimal, upper: Decimal, duration: Decimal,
              left: Decimal = D(0), right: Decimal = D(0)) -> tuple[Decimal, Decimal]:
    a = decay_factor(p.decay_rate_per_second, duration)
    equilibrium = (left / p.left_source_resistance_ohms + right / p.right_source_resistance_ohms) / (
        1 / p.left_source_resistance_ohms + 1 / p.right_source_resistance_ohms)
    return equilibrium + (lower - equilibrium) * a, equilibrium + (upper - equilibrium) * a


def _supported(p: RCChainProtocol, lower: Decimal, upper: Decimal, *, guarded: bool) -> bool:
    guard = p.support_guard_volts if guarded else D(0)
    return lower >= p.support_lower_volts + guard and upper <= p.support_upper_volts - guard


@fixed_decimal_context
def decide_preparation(protocol: RCChainProtocol, expectation: RCChainObservationExpectation,
                       observation: RCChainObservation | None) -> RCChainDecision:
    """Choose the shortest admitted duration using only available observer data.

    No unit roster, initial state, native panel or prepared readback is an input.
    Expected source digests are opaque identities, never state estimators.
    """
    if (expectation.receiver_id, expectation.quantity_id, expectation.voltage_unit,
        expectation.sample_seconds, expectation.decision_seconds, expectation.maximum_radius_volts) != (
            protocol.receiver_id, protocol.quantity_id, protocol.voltage_unit, protocol.sample_seconds,
            protocol.decision_seconds, protocol.maximum_observation_radius_volts):
        raise ValueError("RC consumer expectation substitutes the frozen rule's receiver, clock or uncertainty")
    if observation is None:
        return RCChainDecision(None, "UNEVALUABLE", None, None, None, None, None, ("MISSING_OBSERVATION",))
    reasons = []
    for name, code in (("unit_id", "UNIT_BINDING_MISMATCH"), ("config_sha256", "CONFIGURATION_BINDING_MISMATCH"),
                       ("model_sha256", "MODEL_BINDING_MISMATCH"), ("source_sha256", "SOURCE_BINDING_MISMATCH"),
                       ("source_binding_sha256", "DECLARED_SOURCE_BINDING_MISMATCH"),
                       ("receiver_id", "WRONG_RECEIVER"), ("quantity_id", "WRONG_QUANTITY"),
                       ("voltage_unit", "WRONG_UNITS"), ("sample_seconds", "WRONG_SAMPLE_CLOCK")):
        if getattr(observation, name) != getattr(expectation, name):
            reasons.append(code)
    if observation.sample_seconds > observation.available_seconds:
        reasons.append("OBSERVATION_PRECEDES_SAMPLE")
    if observation.available_seconds > expectation.decision_seconds:
        reasons.append("LATE_OBSERVATION")
    if observation.radius_volts > expectation.maximum_radius_volts:
        reasons.append("UNCERTAINTY_EXCEEDS_CONSUMER_LIMIT")
    lower = observation.reported_voltage_volts - observation.radius_volts
    upper = observation.reported_voltage_volts + observation.radius_volts
    if reasons:
        return RCChainDecision(observation.fingerprint(), "REFUSED", None, lower, upper, None, None, tuple(sorted(reasons)))
    drift = protocol.decision_seconds - protocol.sample_seconds
    for duration in protocol.preparation_durations_seconds:
        prepared = _interval(protocol, lower, upper, drift + duration)
        if _supported(protocol, *prepared, guarded=True):
            return RCChainDecision(observation.fingerprint(), "ADMITTED", duration, lower, upper, *prepared, ())
    return RCChainDecision(observation.fingerprint(), "REFUSED", None, lower, upper, None, None,
        ("FINITE_PREPARATION_MENU_CANNOT_CERTIFY_SUPPORT",))


def _study(config: RCPrerequisiteChainConfig, unit: RCChainUnit,
           model: ResistorCapacitorLadderModelConfig) -> ResistorCapacitorLadderStudyConfig:
    p = config.protocol
    return ResistorCapacitorLadderStudyConfig(model.config_id + ".study", unit.unit_id, model,
        min(p.backward_euler_maximum_step_seconds, min(b - a for a, b in zip(model.output_times_seconds, model.output_times_seconds[1:], strict=False))),
        p.maximum_view_defect_volts, p.maximum_charge_rate_defect_amperes)


def _execute(config: RCPrerequisiteChainConfig, unit: RCChainUnit, model: ResistorCapacitorLadderModelConfig):
    from empirical_lawhood.adapters.simulators.rc_ladder_response.campaign import VIEWS, check_native_views, run_native_view
    study = _study(config, unit, model)
    panels = tuple(run_native_view(study, view) for view in VIEWS)
    return panels, check_native_views(study, panels)


@fixed_decimal_context
def _scalar_state(model: ResistorCapacitorLadderModelConfig, time: Decimal) -> Decimal:
    """Independent KCL closed form; never calls the production state-space code."""
    state = model.initial_voltages_volts[0]
    capacitance = model.capacitances_farads[0]
    conductance = 1 / model.left_source_resistance_ohms + 1 / model.right_termination_resistance_ohms
    rate = conductance / capacitance
    cuts = tuple(sorted({D(0), time, *(edge for segment in model.action_segments
        for edge in (segment.start_seconds, segment.end_seconds) if 0 < edge < time)}))
    for start, end in zip(cuts, cuts[1:], strict=False):
        midpoint = (start + end) / 2
        segment = next((segment for segment in model.action_segments if segment.start_seconds <= midpoint < segment.end_seconds), None)
        equilibrium = D(0) if segment is None else (
            segment.left_voltage_volts / model.left_source_resistance_ohms
            + segment.right_voltage_volts / model.right_termination_resistance_ohms) / conductance
        state = equilibrium + (state - equilibrium) * decay_factor(rate, end - start)
    return state


def _verify_panels(config: RCPrerequisiteChainConfig, unit: RCChainUnit,
                   model: ResistorCapacitorLadderModelConfig, panels: tuple[ResistorCapacitorLadderNativePanel, ...],
                   *, allow_analytic_defect: bool = False) -> None:
    p = config.protocol
    if tuple(panel.view_id for panel in panels) != ("backward-euler", "matrix-exponential"):
        raise ValueError("RC retained native evidence substitutes or omits a nested view")
    for panel in panels:
        if (panel.config_id != model.config_id or panel.unit_id != unit.unit_id
            or panel.times_seconds != model.output_times_seconds or any(len(row) != 1 for row in panel.node_voltages_volts)):
            raise ValueError("RC native evidence changes its source, unit, receiver or clock")
        bound = p.maximum_analytic_defect_volts if panel.view_id == "matrix-exponential" else p.maximum_view_defect_volts
        max_defect = max(abs(row[0] - _scalar_state(model, time)) for time, row in zip(panel.times_seconds, panel.node_voltages_volts, strict=True))
        if max_defect > bound and not allow_analytic_defect:
            raise ValueError("RC native evidence fails its independent scalar transient oracle")
        digest = sha256()
        for values in (panel.times_seconds, tuple(row[0] for row in panel.node_voltages_volts),
                       panel.left_boundary_currents_amperes, panel.right_boundary_currents_amperes):
            digest.update(b"".join(pack("<d", float(value)) for value in values))
        if digest.hexdigest() != panel.numerical_summary.trajectory_sha256:
            raise ValueError("RC retained native trajectory differs from its exact numerical summary digest")
        for time, row, left_current, right_current in zip(panel.times_seconds, panel.node_voltages_volts,
            panel.left_boundary_currents_amperes, panel.right_boundary_currents_amperes, strict=True):
            segment = next((segment for segment in model.action_segments if segment.start_seconds <= time < segment.end_seconds), None)
            left = D(0) if segment is None else segment.left_voltage_volts
            right = D(0) if segment is None else segment.right_voltage_volts
            if (abs(left_current - (left - row[0]) / model.left_source_resistance_ohms) > p.maximum_analytic_current_defect_amperes
                or abs(right_current - (right - row[0]) / model.right_termination_resistance_ohms) > p.maximum_analytic_current_defect_amperes):
                raise ValueError("RC native evidence fails independent boundary-current units or source impedance")


def _retained_check(config: RCPrerequisiteChainConfig, unit: RCChainUnit,
                    model: ResistorCapacitorLadderModelConfig, panels) -> ResistorCapacitorLadderNumericalCheck:
    """Project the existing check record from retained panels without solver imports."""
    exact = next(panel for panel in panels if panel.view_id == "matrix-exponential")
    approximate = next(panel for panel in panels if panel.view_id == "backward-euler")
    defect = max(abs(a[0] - b[0]) for a, b in zip(exact.node_voltages_volts, approximate.node_voltages_volts, strict=True))
    charge = max(panel.numerical_summary.maximum_output_grid_charge_rate_defect_amperes for panel in panels)
    reasons = []
    if defect > config.protocol.maximum_view_defect_volts or not all(panel.numerical_summary.converged for panel in panels):
        reasons.append("VOLTAGE_VIEW_DEFECT_ABOVE_FROZEN_LIMIT")
    if charge > config.protocol.maximum_charge_rate_defect_amperes:
        reasons.append("CHARGE_RATE_DEFECT_ABOVE_FROZEN_LIMIT")
    return ResistorCapacitorLadderNumericalCheck(model.config_id + ".study.numerical-check", model.config_id,
        unit.unit_id, ("backward-euler", "matrix-exponential"), defect, charge, 1, 2, not reasons, tuple(sorted(reasons)))


def _measurement_state(p: RCChainProtocol, unit: RCChainUnit, observation: RCChainObservation | None,
                       decision: RCChainDecision, variant: str) -> tuple[str, tuple[str, ...]]:
    if variant == "physical-stop":
        return "UNSUPPORTED", ("PHYSICAL_SENSOR_AND_METROLOGY_UNSUPPORTED",)
    if observation is None:
        return "UNEVALUABLE", ("MISSING_OBSERVATION",)
    # Finite-menu refusal concerns preparation, not the adequacy of the report.
    invalid = tuple(reason for reason in decision.reason_codes if reason != "FINITE_PREPARATION_MENU_CANNOT_CERTIFY_SUPPORT")
    if invalid:
        return "REFUSED", invalid
    if not observation.reported_voltage_volts - observation.radius_volts <= unit.initial_voltage_volts <= observation.reported_voltage_volts + observation.radius_volts:
        return "FAILED", ("OBSERVATION_INTERVAL_MISSES_SAMPLED_STATE",)
    return "PASSED", ()


def _unexecuted_arm(p: RCChainProtocol, decision: RCChainDecision, measurement_state: str, deadline: Decimal,
                    arm_id: str = "selected", reason_codes: tuple[str, ...] | None = None) -> RCChainArmResult:
    reasons = decision.reason_codes if reason_codes is None else reason_codes
    if decision.disposition == "UNSUPPORTED":
        joined = "UNSUPPORTED"
    elif measurement_state == "UNEVALUABLE":
        joined = "UNEVALUABLE"
    else:
        joined = "REFUSED"
    prep = "UNEVALUABLE" if measurement_state in {"UNEVALUABLE", "UNSUPPORTED"} else "REFUSED"
    return RCChainArmResult(arm_id, None, None, None, None, None, None, None,
        p.predicted_endpoint_volts, None, None, None, prep, joined, reasons, None, deadline,
        "NO_RESPONSE", None, (), None)


def _arm_operands(p: RCChainProtocol, decision: RCChainDecision, arm_id: str) -> tuple[Decimal, Decimal, Decimal]:
    if decision.duration_seconds is None:
        raise ValueError("RC arm cannot replace a refused preparation decision")
    duration = decision.duration_seconds
    if arm_id == "unchanged":
        duration = D(0)
    elif arm_id == "insufficient":
        duration /= 2
    return duration, (p.response_left_voltage_volts if arm_id == "wrong" else D(0)), (
        p.response_right_voltage_volts if arm_id == "wrong" else D(0))


def _reduce_arm(config: RCPrerequisiteChainConfig, unit: RCChainUnit, variant: str,
                decision: RCChainDecision, measurement_state: str, arm_id: str,
                model: ResistorCapacitorLadderModelConfig, panels, check) -> RCChainArmResult:
    p = config.protocol
    duration, left, right = _arm_operands(p, decision, arm_id)
    if decision.sample_lower_volts is None or decision.sample_upper_volts is None:
        raise ValueError("RC admitted decision lacks its original observer interval")
    at_decision = _interval(p, decision.sample_lower_volts, decision.sample_upper_volts, p.decision_seconds - p.sample_seconds)
    lower, upper = _interval(p, *at_decision, duration, left, right)
    prospective = _supported(p, lower, upper, guarded=True)
    cutoff = p.decision_seconds + duration
    exact = next(panel for panel in panels if panel.view_id == "matrix-exponential")
    state = exact.node_voltages_volts[exact.times_seconds.index(cutoff)][0]
    actual = _supported(p, state, state, guarded=False)
    endpoint = exact.node_voltages_volts[-1][0]
    task = abs(endpoint - p.predicted_endpoint_volts) <= p.maximum_task_error_volts
    deadline = p.conflict_deadline_seconds if variant == "resource-conflict" else p.completion_deadline_seconds
    completion = cutoff + p.response_horizon_seconds
    reasons = []
    if measurement_state != "PASSED":
        reasons.append("MEASUREMENT_REQUIREMENT_NOT_SUPPLIED")
    if not prospective:
        reasons.append("PROSPECTIVE_SUPPORT_NOT_CERTIFIED")
    if not actual:
        reasons.append("ACTUAL_RESPONSE_CUTOFF_OUTSIDE_SUPPORT")
    if not check.converged:
        reasons.append("NUMERICAL_CONFORMANCE_FAILED")
    if not task:
        reasons.append("TERMINAL_TASK_BAND_MISSED")
    if completion > deadline:
        reasons.append("COMPLETION_DEADLINE_EXCEEDED")
    if not check.converged:
        prep = joined = "UNEVALUABLE"
    elif measurement_state != "PASSED" or not actual:
        prep = "FAILED"
        joined = "FAILED"
    elif not prospective:
        prep = joined = "REFUSED"
    else:
        prep = "PASSED"
        joined = "PASSED" if task and completion <= deadline else "FAILED"
    return RCChainArmResult(arm_id, duration, left, right, lower, upper, prospective, actual,
        p.predicted_endpoint_volts, endpoint, task, check.converged, prep, joined, tuple(sorted(reasons)),
        completion, deadline, "PROSPECTIVE_PACKAGE_USE" if prospective else "DECLINED_DEVELOPMENT_ASSAY", model, panels, check)


@fixed_decimal_context
def failed_unit_result(config: RCPrerequisiteChainConfig, unit_id: str,
                       reason_code: str = "NUMERICAL_EXECUTION_FAILED", *,
                       source_panels: tuple[ResistorCapacitorLadderNativePanel, ...] = ()) -> RCChainUnitResult:
    """A complete retained numerical failure, never an opportunity to retry."""
    if reason_code not in {"NUMERICAL_EXECUTION_FAILED", "NUMERICAL_SOURCE_CONFORMANCE_FAILED"}:
        raise ValueError("RC numerical failure uses its bounded declared reason code")
    unit = _unit(config, unit_id)
    source = _source(config, unit)
    expected = _expectation(config, unit, source)
    decision = RCChainDecision(None, "UNEVALUABLE", None, None, None, None, None, (reason_code,))
    cases = tuple(RCChainCaseResult(variant, expected, None, decision, "UNEVALUABLE", (reason_code,),
        tuple(_unexecuted_arm(config.protocol, decision, "UNEVALUABLE",
            config.protocol.conflict_deadline_seconds if variant == "resource-conflict" else config.protocol.completion_deadline_seconds,
            arm_id) for arm_id in (ARM_IDS if variant == "adequate" else ("selected",)))) for variant in VARIANT_IDS)
    return RCChainUnitResult(unit_id, config.fingerprint(), source, source_panels, cases,
        source_failure_reason_codes=(reason_code,))


@fixed_decimal_context
def evaluate_unit(config: RCPrerequisiteChainConfig, unit_id: str) -> RCChainUnitResult:
    """Execute one complete exposed unit; all comparisons use frozen F_RC."""
    prove_chain(config)
    unit = _unit(config, unit_id)
    p = config.protocol
    source = _source(config, unit)
    expected = _expectation(config, unit, source)
    try:
        source_panels, source_check = _execute(config, unit, source)
    except (ArithmeticError, RuntimeError):
        return failed_unit_result(config, unit_id)
    if not source_check.converged:
        return failed_unit_result(config, unit_id, "NUMERICAL_SOURCE_CONFORMANCE_FAILED", source_panels=source_panels)
    # Native sample is the receiver row. Only its observer export enters the
    # rule; the unit's oracle initial state enters the later assessment.
    sampled = next(panel for panel in source_panels if panel.view_id == "matrix-exponential").node_voltages_volts[0][0]
    commitments = []
    for variant in VARIANT_IDS:
        observation = _observation(p, expected, sampled, variant)
        decision = decide_preparation(p, expected, observation)
        if variant == "physical-stop":
            decision = RCChainDecision(None, "UNSUPPORTED", None, None, None, None, None,
                ("PHYSICAL_SENSOR_AND_METROLOGY_UNSUPPORTED",))
        commitments.append((variant, observation, decision))
    # All controls have committed before any independent oracle is inspected.
    # The native observer's two numerical views above do not provide the oracle.
    _verify_panels(config, unit, source, source_panels)
    cases = []
    for variant, observation, decision in commitments:
        # The commitment is immutable. Oracle containment cannot repair it.
        measurement_state, measurement_reasons = _measurement_state(p, unit, observation, decision, variant)
        arms = []
        for arm_id in (ARM_IDS if variant == "adequate" else ("selected",)):
            deadline = p.conflict_deadline_seconds if variant == "resource-conflict" else p.completion_deadline_seconds
            if decision.disposition != "ADMITTED":
                arms.append(_unexecuted_arm(p, decision, measurement_state, deadline, arm_id))
                continue
            duration, left, right = _arm_operands(p, decision, arm_id)
            model = _model(config, unit, model_id=f"{config.config_id}.{unit_id}.{variant}.{arm_id}",
                duration=duration, prep_left=left, prep_right=right)
            try:
                panels, check = _execute(config, unit, model)
            except (ArithmeticError, RuntimeError):
                failure = RCChainDecision(decision.observation_sha256, "UNEVALUABLE", None,
                    decision.sample_lower_volts, decision.sample_upper_volts, None, None, ("NUMERICAL_EXECUTION_FAILED",))
                arms.append(_unexecuted_arm(p, failure, "UNEVALUABLE", deadline, arm_id))
                continue
            _verify_panels(config, unit, model, panels, allow_analytic_defect=not check.converged)
            arms.append(_reduce_arm(config, unit, variant, decision, measurement_state, arm_id, model, panels, check))
        cases.append(RCChainCaseResult(variant, expected, observation, decision, measurement_state, measurement_reasons, tuple(arms)))
    return RCChainUnitResult(unit_id, config.fingerprint(), source, source_panels, tuple(cases))


@fixed_decimal_context
def verify_unit_result(config: RCPrerequisiteChainConfig, result: RCChainUnitResult) -> None:
    """Authenticate retained joins and equations without repeating native work."""
    unit = _unit(config, result.unit_id)
    if result.config_sha256 != config.fingerprint() or result.evidence_role != EVIDENCE_ROLE:
        raise ValueError("RC retained unit changes its exact configuration or development evidence role")
    if result.source_failure_reason_codes:
        if result != failed_unit_result(config, unit.unit_id, result.source_failure_reason_codes[0], source_panels=result.source_panels):
            raise ValueError("RC retained failed unit omits census or changes its declared numerical failure")
        if result.source_panels:
            _verify_panels(config, unit, result.measurement_source, result.source_panels, allow_analytic_defect=True)
            if _retained_check(config, unit, result.measurement_source, result.source_panels).converged:
                raise ValueError("RC source conformance failure contradicts its retained native check")
        return
    source = _source(config, unit)
    if result.measurement_source != source:
        raise ValueError("RC retained measurement changes its frozen native source")
    _verify_panels(config, unit, source, result.source_panels)
    if not _retained_check(config, unit, source, result.source_panels).converged:
        raise ValueError("RC retained observation source fails its frozen numerical contract")
    expected = _expectation(config, unit, source)
    sampled = next(panel for panel in result.source_panels if panel.view_id == "matrix-exponential").node_voltages_volts[0][0]
    for case in result.cases:
        if case.expectation != expected or case.observation != _observation(config.protocol, expected, sampled, case.variant_id):
            raise ValueError("RC retained observer changes its source binding, complete control or native sample")
        decision = decide_preparation(config.protocol, expected, case.observation)
        if case.variant_id == "physical-stop":
            decision = RCChainDecision(None, "UNSUPPORTED", None, None, None, None, None,
                ("PHYSICAL_SENSOR_AND_METROLOGY_UNSUPPORTED",))
        state, reasons = _measurement_state(config.protocol, unit, case.observation, decision, case.variant_id)
        if case.decision != decision or (case.measurement_state, case.measurement_reason_codes) != (state, reasons):
            raise ValueError("RC retained decision changes its frozen rule, cutoff or postcommitment adequacy")
        for arm in case.arms:
            deadline = config.protocol.conflict_deadline_seconds if case.variant_id == "resource-conflict" else config.protocol.completion_deadline_seconds
            if decision.disposition != "ADMITTED":
                if arm != _unexecuted_arm(config.protocol, decision, state, deadline, arm.arm_id):
                    raise ValueError("RC retained refusal has acquired a response or changed its disposition")
                continue
            if arm.native_model is None and arm.reason_codes == ("NUMERICAL_EXECUTION_FAILED",):
                failure = RCChainDecision(decision.observation_sha256, "UNEVALUABLE", None,
                    decision.sample_lower_volts, decision.sample_upper_volts, None, None, arm.reason_codes)
                if arm != _unexecuted_arm(config.protocol, failure, "UNEVALUABLE", deadline, arm.arm_id):
                    raise ValueError("RC retained arm numerical failure changes its terminal disposition")
                continue
            duration, left, right = _arm_operands(config.protocol, decision, arm.arm_id)
            model = _model(config, unit, model_id=f"{config.config_id}.{unit.unit_id}.{case.variant_id}.{arm.arm_id}",
                duration=duration, prep_left=left, prep_right=right)
            if arm.native_model != model:
                raise ValueError("RC retained arm substitutes the frozen circuit, action or selected duration")
            _verify_panels(config, unit, model, arm.native_panels, allow_analytic_defect=arm.numerical_converged is False)
            check = _retained_check(config, unit, model, arm.native_panels)
            expected_arm = _reduce_arm(config, unit, case.variant_id, decision, state, arm.arm_id, model, arm.native_panels, check)
            if arm != expected_arm:
                raise ValueError("RC retained arm changes its original native evidence or scientific reduction")


@fixed_decimal_context
def summarize_chain(config: RCPrerequisiteChainConfig,
                    results: tuple[RCChainUnitResult, ...]) -> RCChainSummary:
    """Retain the full assigned census; nested arms and views are not replicates."""
    if tuple(result.unit_id for result in results) != tuple(unit.unit_id for unit in config.units):
        raise ValueError("RC summary requires the exact complete assigned unit census in order")
    counts: Counter[tuple[str, str, str, str]] = Counter()
    arm_count = view_count = 0
    for result in results:
        verify_unit_result(config, result)
        view_count += len(result.source_panels)
        for case in result.cases:
            for arm in case.arms:
                arm_count += 1
                view_count += len(arm.native_panels)
                for claim, state in (("rc-m", case.measurement_state), ("rc-p", arm.preparation_state), ("rc-j", arm.joined_state)):
                    counts[(case.variant_id, arm.arm_id, claim, state)] += 1
    census = tuple(RCChainOutcomeCount(variant, arm, claim, state, counts[(variant, arm, claim, state)])
        for variant in VARIANT_IDS for arm in (ARM_IDS if variant == "adequate" else ("selected",))
        for claim in ("rc-j", "rc-m", "rc-p") for state in OUTCOME_STATES)
    return RCChainSummary(config.fingerprint(), tuple(result.unit_id for result in results),
        tuple(result.fingerprint() for result in results), len(config.units), len(config.units) * len(VARIANT_IDS),
        arm_count, view_count, census)


__all__ = ["default_chain_config", "prove_chain", "decide_preparation", "evaluate_unit",
           "failed_unit_result", "verify_unit_result", "summarize_chain"]
