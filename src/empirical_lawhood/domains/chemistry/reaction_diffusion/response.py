"""Reusable reaction--diffusion preparation, balances and response assessment.

All inputs are supplied arrays, scalar states or typed scientific records.
FiPy mesh construction, integration and version contact remain in the adapter.
"""

from __future__ import annotations
from decimal import Decimal
import numpy as np
from empirical_lawhood.methods.selective_dependence_response.analysis import build_panel
from empirical_lawhood.methods.selective_dependence_response.contracts import SelectiveDependenceResponseActionRealization, SelectiveDependenceResponseCompleteUnitResult, SelectiveDependenceResponseConditionResult, SelectiveDependenceResponseContextDecision, SelectiveDependenceResponseDisposition, SelectiveDependenceResponsePhase, SelectiveDependenceResponseReceiverObservation, digest_ids
from empirical_lawhood.methods.selective_dependence_response.inference import noncompensating_disposition
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import NamedDecimal
from empirical_lawhood.methods.selective_dependence_response.preparation_inputs import SelectiveDependenceResponsePreparationInput
from empirical_lawhood.domains.chemistry.reaction_diffusion.preparation_inputs import DRAW_VARIABLE_IDS, validate_reviewed_preparation_input
from empirical_lawhood.domains.chemistry.reaction_diffusion.contracts import FipyReactionDiffusionResponseFiPyDesign, FipyReactionDiffusionResponseFiPySourceQualification

from dataclasses import dataclass

def as_decimal(value: float) -> Decimal:
    return Decimal(format(float(value), ".12g"))

def preparation_rng(preparation_input: SelectiveDependenceResponsePreparationInput) -> np.random.Generator:
    if type(preparation_input) is not SelectiveDependenceResponsePreparationInput or preparation_input.draw_variable_ids != DRAW_VARIABLE_IDS:
        raise ValueError("native preparation requires explicit full numerical inputs in the exact variable draw order")
    validate_reviewed_preparation_input(preparation_input)
    return np.random.default_rng(preparation_input.full_seed)

def preparation(preparation_input: SelectiveDependenceResponsePreparationInput) -> dict[str, float]:
    rng = preparation_rng(preparation_input)
    return {
        "background-amplitude": rng.uniform(0.0, 0.0010),
        "residual-amplitude": rng.uniform(0.035, 0.045),
        "residual-centre": rng.uniform(0.27, 0.35),
        "residual-width": rng.uniform(0.045, 0.070),
    }

def initial_field(design: FipyReactionDiffusionResponseFiPyDesign, preparation: dict[str, float], *, x: np.ndarray, history_id: str) -> np.ndarray:
    """Construct the declared cleared or residual field on supplied coordinates."""
    values = np.zeros(design.mesh_cells, dtype=float)
    if history_id == "residual-checkpoint":
        values = preparation["background-amplitude"] * (1.0 - x)
        values += preparation["residual-amplitude"] * np.exp(
            -0.5 * ((x - preparation["residual-centre"]) / preparation["residual-width"]) ** 2
        )
    return values


def condition_parameters(design: FipyReactionDiffusionResponseFiPyDesign, *, denominator_id: str, action_id: str, horizon_id: str) -> tuple[float, bool, float, float, float]:
    requested = {
        "source-remove": float(design.action_rates[0]),
        "source-hold": float(design.action_rates[1]),
        "source-inject": float(design.action_rates[2]),
        "source-outside": float(design.outside_action_rate),
    }[action_id]
    outside = action_id == "source-outside"
    accepted = 0.0 if outside else requested
    diffusivity = {
        "diffusivity-low": float(design.diffusivities[0]),
        "diffusivity-high": float(design.diffusivities[1]),
    }[denominator_id]
    horizon = {
        "short": float(design.horizon_seconds[0]),
        "long": float(design.horizon_seconds[1]),
    }[horizon_id]
    return requested, outside, accepted, diffusivity, horizon


def source_mask(x: np.ndarray) -> np.ndarray:
    return (x >= 0.15) & (x <= 0.25)


def field_mass(values: np.ndarray, dx: float) -> float:
    return float(np.sum(values) * dx)


@dataclass(slots=True)
class FieldBalance:
    """Accumulate the declared discrete conservation diagnostic in native order."""
    initial_mass: float
    source_integral: float = 0.0
    decay_integral: float = 0.0
    boundary_outflow_integral: float = 0.0

    def observe(self, *, previous_mass: float, current: np.ndarray, applied: float, source_region: np.ndarray, dx: float, diffusivity: float, decay_rate: Decimal | float, step: float) -> None:
        current_mass = field_mass(current, dx)
        applied_mass_rate = applied * float(np.sum(source_region)) * dx
        self.source_integral += applied_mass_rate * step
        self.decay_integral += float(decay_rate) * (previous_mass + current_mass) * step / 2
        outward_flux = max(0.0, diffusivity * current[-1] / (dx / 2))
        self.boundary_outflow_integral += outward_flux * step


def receiver_margins(design: FipyReactionDiffusionResponseFiPyDesign, *, final: np.ndarray, x: np.ndarray, dx: float, diffusivity: float, balance: FieldBalance) -> tuple[dict[str, float], tuple[Decimal, ...]]:
    final_mass = float(np.sum(final) * dx)
    boundary_flux = max(0.0, diffusivity * final[-1] / (dx / 2))
    balance_error = abs(
        final_mass
        - (balance.initial_mass + balance.source_integral - balance.decay_integral - balance.boundary_outflow_integral)
    )
    observed = {
        "balance-error": balance_error,
        "boundary-flux": boundary_flux,
        "downstream-mean": float(np.mean(final[x >= 0.75])),
        "field-mass": final_mass,
        "field-maximum": float(np.max(final)),
        "field-minimum": float(np.min(final)),
    }
    margins = (
        as_decimal(float(design.maximum_balance_error) - balance_error),
        as_decimal(float(design.maximum_boundary_flux) - boundary_flux),
        as_decimal(
            min(
                observed["downstream-mean"] - float(design.target_downstream_lower),
                float(design.target_downstream_upper) - observed["downstream-mean"],
            )
        ),
        as_decimal(observed["field-minimum"] + float(design.nonnegativity_tolerance)),
        as_decimal(float(design.maximum_peak_field) - observed["field-maximum"]),
    )
    return observed, margins


def condition_result(*, denominator_id: str, history_id: str, action_id: str, horizon_id: str,
                     requested: float, accepted: float, outside: bool, horizon: float, action_duration: float,
                     source_region_length: float, observed: dict[str, float], margins: tuple[Decimal, ...],
                     stopped: bool, stop_code: str | None) -> tuple[SelectiveDependenceResponseConditionResult, tuple[Decimal, ...]]:
    """Keep failed measurements invalid and unevaluable without synthetic margins."""
    condition_id = f"condition.{denominator_id}.{history_id}.{action_id}.{horizon_id}"
    realized_duration = min(horizon, action_duration)
    action = SelectiveDependenceResponseActionRealization(
        realization_id=f"realization.{condition_id}",
        action_id=action_id,
        requested_value=as_decimal(requested),
        requested_unit="field-amplitude-per-second",
        accepted_value=as_decimal(accepted),
        accepted_unit="field-amplitude-per-second",
        applied_value=as_decimal(accepted),
        applied_unit="field-amplitude-per-second",
        realized_value=as_decimal(accepted * source_region_length * realized_duration),
        realized_unit="field-mass",
        requested_clock=Decimal("0"),
        accepted_clock=Decimal("0"),
        applied_clock=Decimal("0"),
        realized_clock=as_decimal(realized_duration),
        acceptance_state="rejected-to-hold" if outside else "accepted",
    )
    receivers = tuple(
        SelectiveDependenceResponseReceiverObservation(
            observation_id=f"observation.{condition_id}.{receiver_id}",
            receiver_id=receiver_id,
            value=as_decimal(value),
            native_unit={
                "balance-error": "field-mass",
                "boundary-flux": "field-flux",
                "downstream-mean": "field-amplitude",
                "field-mass": "field-mass",
                "field-maximum": "field-amplitude",
                "field-minimum": "field-amplitude",
            }[receiver_id],
            valid=not stopped,
        )
        for receiver_id, value in sorted(observed.items())
    )
    margin_ids = (
        "balance-error-ceiling",
        "boundary-flux-ceiling",
        "downstream-target-band",
        "nonnegativity-tolerance",
        "peak-field-ceiling",
    )
    gate_margins = tuple(
        NamedDecimal(value_id=margin_id, value=value, unit="native-margin")
        for margin_id, value in zip(margin_ids if margins else (), margins, strict=True)
    )
    return (
        SelectiveDependenceResponseConditionResult(
            condition_id=condition_id,
            denominator_id=denominator_id,
            history_id=history_id,
            action_id=action_id,
            horizon_id=horizon_id,
            support_state="outside-support" if outside else "inside-support",
            action=action,
            receivers=receivers,
            gate_margins=gate_margins,
            fibre_admitted=(
                None if stopped else (False if outside else all(value >= 0 for value in margins))
            ),
            disposition=SelectiveDependenceResponseDisposition.UNEVALUABLE,
            stopped=stopped,
            stop_code=stop_code,
        ),
        margins,
    )

def complete_unit_result(design: FipyReactionDiffusionResponseFiPyDesign, *, complete_unit_id: str, phase: SelectiveDependenceResponsePhase, preparation: dict[str, float], raw: dict[tuple[str, str, str], dict[str, tuple[SelectiveDependenceResponseConditionResult, tuple[Decimal, ...]]]]) -> SelectiveDependenceResponseCompleteUnitResult:
    """Assess the entire supplied branch census using one independent unit."""
    conditions = []
    context_decisions = []
    for (denominator_id, history_id, horizon_id), branches in raw.items():
        hold = branches["source-hold"][1]
        active = {
            action_id: margins
            for action_id, (_, margins) in branches.items()
            if action_id not in {"source-hold", "source-outside"}
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
                hold_action_id="source-hold",
                hold_viable=hold_viable,
                disposition=fibre,
            )
        )
        for action_id, (condition, margins) in branches.items():
            if condition.stopped:
                disposition = SelectiveDependenceResponseDisposition.UNEVALUABLE
            elif action_id == "source-outside":
                disposition = SelectiveDependenceResponseDisposition.NONATTEMPT
            elif action_id == "source-hold":
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
            value=as_decimal(value),
            unit="field-preparation-unit",
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
        source_version=design.fipy_version,
        solver_id="fipy-scipy-linear-lu",
        nested_conditions_count_as_units=False,
        outcome_access=access,
    )

def source_qualification(design: FipyReactionDiffusionResponseFiPyDesign, *, units: tuple[SelectiveDependenceResponseCompleteUnitResult, ...], replay: SelectiveDependenceResponseCompleteUnitResult, observed_version: str):
    """Assess supplied excluded-canary records; no native engine is contacted."""
    if not units:
        raise ValueError("FiPy source qualification requires excluded canaries")
    unit = units[0]
    valid = all(not condition.stopped for value in units for condition in value.conditions)
    reset = unit.canonical_bytes() == replay.canonical_bytes()
    balance_ok = all(
        observation.valid and observation.value <= design.maximum_balance_error
        for value in units
        for condition in value.conditions
        for observation in condition.receivers
        if observation.receiver_id == "balance-error"
    )
    actions = {
        condition.action.requested_value for value in units for condition in value.conditions
    }
    version_matches = observed_version == design.fipy_version
    signed_source_observable = any(value < 0 for value in actions) and any(
        value > 0 for value in actions
    )
    realized_integral_observable = all(
        condition.action.realized_unit != condition.action.applied_unit
        for value in units
        for condition in value.conditions
    )
    source_ready = all(
        (
            valid,
            reset,
            balance_ok,
            version_matches,
            signed_source_observable,
            realized_integral_observable,
        )
    )
    panel = build_panel(
        panel_id="panel.fipy.canary",
        target_id=design.target_id,
        complete_units=units,
    )
    qualification = FipyReactionDiffusionResponseFiPySourceQualification(
        qualification_id="qualification.fipy.source",
        design_id=design.design_id,
        observed_fipy_version=observed_version,
        version_matches_design=version_matches,
        equation_constructed=valid,
        signed_source_observable=signed_source_observable,
        realized_integral_observable=realized_integral_observable,
        reset_reproducible=reset,
        balance_qualified=balance_ok,
        source_ready=source_ready,
        canary_panel=ObjectIdentity.from_record(panel.panel_id, panel),
        canary_result_identities=tuple(
            sorted(
                (ObjectIdentity.from_record(value.result_id, value) for value in units),
                key=lambda value: value.object_id,
            )
        ),
        excluded_complete_unit_count=len(units),
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
    )
    return qualification, panel
