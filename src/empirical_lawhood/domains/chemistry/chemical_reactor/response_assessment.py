"""Reusable Cantera-family preparation and supplied-observation scientific assessment."""
from __future__ import annotations
from decimal import Decimal
import numpy as np
from empirical_lawhood.methods.selective_dependence_response.contracts import SelectiveDependenceResponseActionRealization, SelectiveDependenceResponseCompleteUnitResult, SelectiveDependenceResponseConditionResult, SelectiveDependenceResponseContextDecision, SelectiveDependenceResponseDisposition, SelectiveDependenceResponsePhase, SelectiveDependenceResponseReceiverObservation, digest_ids
from empirical_lawhood.methods.selective_dependence_response.inference import noncompensating_disposition
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.references import NamedDecimal
from empirical_lawhood.methods.selective_dependence_response.preparation_inputs import SelectiveDependenceResponsePreparationInput
from empirical_lawhood.domains.chemistry.chemical_reactor.preparation_inputs import DRAW_VARIABLE_IDS, validate_reviewed_preparation_input


def _decimal(value: float) -> Decimal:
    return Decimal(format(float(value), ".12g"))


def _rng(preparation_input: SelectiveDependenceResponsePreparationInput) -> np.random.Generator:
    if type(preparation_input) is not SelectiveDependenceResponsePreparationInput or preparation_input.draw_variable_ids != DRAW_VARIABLE_IDS:
        raise ValueError("native preparation requires explicit full numerical inputs in the exact variable draw order")
    validate_reviewed_preparation_input(preparation_input)
    return np.random.default_rng(preparation_input.full_seed)


def _preparation(preparation_input: SelectiveDependenceResponsePreparationInput) -> dict[str, float]:
    rng = _rng(preparation_input)
    return {
        "bath-temperature": rng.uniform(292.0, 308.0),
        "cold-checkpoint-temperature": rng.uniform(575.0, 625.0),
        "equivalence-ratio": rng.uniform(0.76, 0.84),
        "heat-transfer-scale": rng.uniform(0.90, 1.10),
        "hot-checkpoint-seed-temperature": rng.uniform(1475.0, 1525.0),
        "inlet-temperature": rng.uniform(290.0, 310.0),
        "reactor-volume": rng.uniform(0.00090, 0.00110),
    }


def assess_cantera_state(design, *, inlet_ch4, final_methane_mole_fraction,
                         carbon_monoxide_mole_fraction, elemental_mass_fractions,
                         peak_temperature, temperature):
    """Reduce already-observed scalar species, element and temperature operands."""
    conversion = 1.0 - final_methane_mole_fraction / inlet_ch4
    co = carbon_monoxide_mole_fraction
    element_error = abs(
        sum(elemental_mass_fractions) - 1.0
    )
    values = {
        "carbon-monoxide": co,
        "element-error": element_error,
        "methane-conversion": conversion,
        "peak-temperature": peak_temperature,
        "temperature": temperature,
    }
    margins = (
        _decimal(float(design.maximum_co_mole_fraction) - co),
        _decimal(float(design.maximum_element_error) - element_error),
        _decimal(conversion - float(design.minimum_conversion)),
        _decimal(float(design.maximum_peak_temperature) - peak_temperature),
        _decimal(
            min(
                temperature - float(design.target_temperature_lower),
                float(design.target_temperature_upper) - temperature,
            )
        ),
    )
    return values, margins


def build_cantera_condition(*, denominator_id, history_id, action_id, horizon_id,
                            requested, accepted, applied_mass_flow, horizon,
                            outside, values, margins, stopped, stop_code):
    """Preserve the complete receiver census and absent margins on native failure."""
    condition_id = f"condition.{denominator_id}.{history_id}.{action_id}.{horizon_id}"
    action = SelectiveDependenceResponseActionRealization(
        realization_id=f"realization.{condition_id}",
        action_id=action_id,
        requested_value=_decimal(requested),
        requested_unit="dimensionless-flow-multiplier",
        accepted_value=_decimal(accepted),
        accepted_unit="dimensionless-flow-multiplier",
        applied_value=_decimal(applied_mass_flow),
        applied_unit="kilogram-per-second",
        realized_value=_decimal(applied_mass_flow * horizon),
        realized_unit="kilogram",
        requested_clock=Decimal("0"),
        accepted_clock=Decimal("0"),
        applied_clock=Decimal("0"),
        realized_clock=_decimal(horizon),
        acceptance_state="rejected-to-hold" if outside else "accepted",
    )
    receivers = tuple(
        SelectiveDependenceResponseReceiverObservation(
            observation_id=f"observation.{condition_id}.{receiver_id}",
            receiver_id=receiver_id,
            value=_decimal(value),
            native_unit=("kelvin" if "temperature" in receiver_id else "dimensionless-fraction"),
            valid=not stopped,
        )
        for receiver_id, value in sorted(values.items())
    )
    margin_ids = (
        "co-ceiling",
        "element-closure",
        "minimum-conversion",
        "peak-temperature-ceiling",
        "target-temperature-band",
    )
    gate_margins = tuple(
        NamedDecimal(value_id=margin_id, value=value, unit="native-margin")
        for margin_id, value in zip(() if stopped else margin_ids, margins, strict=True)
    )
    condition = SelectiveDependenceResponseConditionResult(
        condition_id=condition_id,
        denominator_id=denominator_id,
        history_id=history_id,
        action_id=action_id,
        horizon_id=horizon_id,
        support_state="outside-support" if outside else "inside-support",
        action=action,
        receivers=receivers,
        gate_margins=gate_margins,
        fibre_admitted=None
        if stopped
        else (False if outside else all(value >= 0 for value in margins)),
        disposition=SelectiveDependenceResponseDisposition.UNEVALUABLE,
        stopped=stopped,
        stop_code=stop_code,
    )
    return condition, margins


def adjudicate_cantera_complete_unit(design, *, complete_unit_id, phase, preparation, raw):
    """Assess every predeclared branch without replacing failed or absent operands."""
    conditions = []
    context_decisions = []
    for (denominator_id, history_id, horizon_id), branches in raw.items():
        hold = branches["flow-hold"][1]
        active = {
            action_id: margins
            for action_id, (_, margins) in branches.items()
            if action_id not in {"flow-hold", "flow-outside"}
        }
        fibre = noncompensating_disposition(
            active_action_gate_margins=active,
            hold_gate_margins=hold or None,
        )
        admitted_active_action_ids = tuple(
            sorted(
                action_id
                for action_id, margins in active.items()
                if margins and all(value >= 0 for value in margins)
            )
        )
        active_fibres_complete = all(bool(margins) for margins in active.values())
        hold_viable = None if not hold else all(value >= 0 for value in hold)
        context_decisions.append(
            SelectiveDependenceResponseContextDecision(
                decision_id=f"decision.{denominator_id}.{history_id}.{horizon_id}",
                denominator_id=denominator_id,
                history_id=history_id,
                horizon_id=horizon_id,
                admitted_active_action_ids=admitted_active_action_ids,
                active_fibres_complete=active_fibres_complete,
                hold_action_id="flow-hold",
                hold_viable=hold_viable,
                disposition=fibre,
            )
        )
        for action_id, (condition, margins) in branches.items():
            if condition.stopped:
                disposition = SelectiveDependenceResponseDisposition.UNEVALUABLE
            elif action_id == "flow-outside":
                disposition = SelectiveDependenceResponseDisposition.NONATTEMPT
            elif action_id == "flow-hold":
                disposition = (
                    SelectiveDependenceResponseDisposition.HOLD_ONLY
                    if hold and all(value >= 0 for value in hold)
                    else SelectiveDependenceResponseDisposition.NONATTEMPT
                )
            elif margins and all(value >= 0 for value in margins):
                disposition = SelectiveDependenceResponseDisposition.ACTION_AVAILABLE
            elif fibre is SelectiveDependenceResponseDisposition.HOLD_ONLY:
                disposition = SelectiveDependenceResponseDisposition.HOLD_ONLY
            else:
                disposition = SelectiveDependenceResponseDisposition.NONATTEMPT
            conditions.append(
                SelectiveDependenceResponseConditionResult(
                    condition_id=condition.condition_id,
                    denominator_id=condition.denominator_id,
                    history_id=condition.history_id,
                    action_id=condition.action_id,
                    horizon_id=condition.horizon_id,
                    support_state=condition.support_state,
                    action=condition.action,
                    receivers=condition.receivers,
                    gate_margins=condition.gate_margins,
                    fibre_admitted=condition.fibre_admitted,
                    disposition=disposition,
                    stopped=condition.stopped,
                    stop_code=condition.stop_code,
                )
            )
    ordered = tuple(sorted(conditions, key=lambda value: value.condition_id))
    access = (
        OutcomeAccess.EVALUATION_SEALED
        if phase is SelectiveDependenceResponsePhase.EVALUATION
        else OutcomeAccess.DEVELOPMENT_VISIBLE
    )
    preparation_values = tuple(
        NamedDecimal(
            value_id=key,
            value=_decimal(value),
            unit=("kelvin" if "temperature" in key else "native-preparation-unit"),
        )
        for key, value in sorted(preparation.items())
    )
    return SelectiveDependenceResponseCompleteUnitResult(
        result_id=f"result.{complete_unit_id}",
        target_id=design.target_id,
        complete_unit_id=complete_unit_id,
        phase=phase,
        preparation_values=preparation_values,
        conditions=ordered,
        context_decisions=tuple(sorted(context_decisions, key=lambda value: value.decision_id)),
        expected_condition_ids_sha256=digest_ids(tuple(value.condition_id for value in ordered)),
        source_version=design.cantera_version,
        solver_id="cantera-reactornet-bdf",
        nested_conditions_count_as_units=False,
        outcome_access=access,
    )
