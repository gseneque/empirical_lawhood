"""Reset-clean complete-unit Cantera execution with stage-resolved actions."""

from __future__ import annotations
from empirical_lawhood.domains.chemistry.chemical_reactor.response_assessment import _preparation, assess_cantera_state, build_cantera_condition, adjudicate_cantera_complete_unit


from decimal import Decimal
from time import monotonic


from empirical_lawhood.methods.selective_dependence_response.analysis import build_panel
from empirical_lawhood.methods.selective_dependence_response.contracts import SelectiveDependenceResponseCompleteUnitResult, SelectiveDependenceResponseConditionResult, SelectiveDependenceResponsePhase, SelectiveDependenceResponseTargetPanel
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity

from empirical_lawhood.methods.selective_dependence_response.preparation_inputs import SelectiveDependenceResponsePreparationInput

from empirical_lawhood.domains.chemistry.chemical_reactor.preparation_inputs import DRAW_VARIABLE_IDS, cantera_preparation_input
from empirical_lawhood.domains.chemistry.chemical_reactor.contracts import CanteraReactionResponseCanteraDesign, CanteraReactionResponseCanteraSourceQualification








def _condition(
    design: CanteraReactionResponseCanteraDesign,
    preparation: dict[str, float],
    *,
    denominator_id: str,
    history_id: str,
    action_id: str,
    horizon_id: str,
) -> tuple[SelectiveDependenceResponseConditionResult, tuple[Decimal, ...]]:
    import cantera as ct

    action_values = {
        "flow-low": float(design.action_multipliers[0]),
        "flow-hold": float(design.action_multipliers[1]),
        "flow-high": float(design.action_multipliers[2]),
        "flow-outside": float(design.outside_action_multiplier),
    }
    requested = action_values[action_id]
    outside = action_id == "flow-outside"
    accepted = 1.0 if outside else requested
    horizon = {"short": float(design.horizon_seconds[0]), "long": float(design.horizon_seconds[1])}[
        horizon_id
    ]
    ua = {
        "heat-loss-low": float(design.heat_transfer_coefficients[0]),
        "heat-loss-high": float(design.heat_transfer_coefficients[1]),
    }[denominator_id] * preparation["heat-transfer-scale"]
    composition = f"CH4:1,O2:{2 / preparation['equivalence-ratio']},N2:{7.52 / preparation['equivalence-ratio']}"
    inlet = ct.Solution("gri30.yaml")
    inlet.TPX = preparation["inlet-temperature"], ct.one_atm, composition
    initial = ct.Solution("gri30.yaml")
    initial_temperature = preparation[
        "hot-checkpoint-seed-temperature"
        if history_id == "hot-checkpoint"
        else "cold-checkpoint-temperature"
    ]
    initial.TPX = initial_temperature, ct.one_atm, composition
    if history_id == "hot-checkpoint":
        initial.equilibrate("HP")
    environment_gas = ct.Solution("gri30.yaml")
    environment_gas.TPX = preparation["bath-temperature"], ct.one_atm, "N2:1"
    upstream = ct.Reservoir(inlet, clone=True)
    downstream = ct.Reservoir(inlet, clone=True)
    environment = ct.Reservoir(environment_gas, clone=True)
    reactor = ct.IdealGasReactor(
        initial,
        energy="on",
        volume=preparation["reactor-volume"],
        clone=True,
    )
    base_mass_flow = reactor.mass / float(design.base_residence_seconds)
    applied_mass_flow = base_mass_flow * accepted
    inlet_controller = ct.MassFlowController(upstream, reactor, mdot=applied_mass_flow)
    ct.PressureController(reactor, downstream, primary=inlet_controller, K=1e-5)
    ct.Wall(reactor, environment, A=1.0, U=ua)
    network = ct.ReactorNet([reactor])
    peak_temperature = reactor.T
    steps = 0
    started = monotonic()
    stopped = False
    stop_code: str | None = None
    margins: tuple[Decimal, ...]
    try:
        while network.time < horizon:
            network.step()
            peak_temperature = max(peak_temperature, reactor.T)
            steps += 1
            if steps > design.maximum_solver_steps:
                raise RuntimeError("solver-step-ceiling")
            if monotonic() - started > float(design.maximum_wall_seconds_per_unit):
                raise RuntimeError("unit-wall-time-ceiling")
        final = reactor.phase
        values, margins = assess_cantera_state(design,
            inlet_ch4=inlet["CH4"].X[0],
            final_methane_mole_fraction=final["CH4"].X[0],
            carbon_monoxide_mole_fraction=final["CO"].X[0],
            elemental_mass_fractions=tuple(final.elemental_mass_fraction(element) for element in range(final.n_elements)),
            peak_temperature=peak_temperature, temperature=reactor.T)
    except Exception as error:  # Cantera failure is a typed scientific outcome.
        stopped = True
        stop_code = f"cantera-{type(error).__name__.lower()}"
        values = {
            "carbon-monoxide": 0.0,
            "element-error": 0.0,
            "methane-conversion": 0.0,
            "peak-temperature": 0.0,
            "temperature": 0.0,
        }
        margins = ()
    return build_cantera_condition(denominator_id=denominator_id, history_id=history_id,
        action_id=action_id, horizon_id=horizon_id, requested=requested, accepted=accepted,
        applied_mass_flow=applied_mass_flow, horizon=horizon, outside=outside, values=values,
        margins=margins, stopped=stopped, stop_code=stop_code)


def execute_cantera_complete_unit(
    design: CanteraReactionResponseCanteraDesign,
    *,
    complete_unit_id: str,
    phase: SelectiveDependenceResponsePhase,
    preparation_input: SelectiveDependenceResponsePreparationInput | None = None,
) -> SelectiveDependenceResponseCompleteUnitResult:
    """Execute the full branch panel while retaining one independent unit."""

    if type(preparation_input) is not SelectiveDependenceResponsePreparationInput:
        raise ValueError("native complete unit requires explicit numerical preparation inputs before solver work")
    preparation_input.validate_context(
        complete_unit_id=complete_unit_id,
        target_id=design.target_id,
        target_design=ObjectIdentity.from_record(design.design_id, design),
        phase=phase.value,
        draw_variable_ids=DRAW_VARIABLE_IDS,
    )
    preparation = _preparation(preparation_input)
    raw: dict[
        tuple[str, str, str], dict[str, tuple[SelectiveDependenceResponseConditionResult, tuple[Decimal, ...]]]
    ] = {}
    for denominator_id in design.denominator_ids:
        for history_id in design.history_ids:
            for horizon_id in design.horizon_ids:
                key = denominator_id, history_id, horizon_id
                raw[key] = {}
                for action_id in design.action_ids:
                    raw[key][action_id] = _condition(
                        design,
                        preparation,
                        denominator_id=denominator_id,
                        history_id=history_id,
                        action_id=action_id,
                        horizon_id=horizon_id,
                    )
    return adjudicate_cantera_complete_unit(design, complete_unit_id=complete_unit_id,
        phase=phase, preparation=preparation, raw=raw)


def qualify_cantera_source(
    design: CanteraReactionResponseCanteraDesign,
    *,
    canary_unit_ids: tuple[str, ...],
) -> tuple[CanteraReactionResponseCanteraSourceQualification, SelectiveDependenceResponseTargetPanel]:
    preparation_inputs = tuple(
        cantera_preparation_input(design, unit_id, SelectiveDependenceResponsePhase.CANARY)
        for unit_id in canary_unit_ids
    )
    import cantera as ct

    units = tuple(
        execute_cantera_complete_unit(
            design,
            complete_unit_id=unit_id,
            phase=SelectiveDependenceResponsePhase.CANARY,
            preparation_input=preparation_input,
        )
        for unit_id, preparation_input in zip(canary_unit_ids, preparation_inputs, strict=True)
    )
    if not units:
        raise ValueError("Cantera source qualification requires excluded canaries")
    unit = units[0]
    replay = execute_cantera_complete_unit(
        design,
        complete_unit_id=unit.complete_unit_id,
        phase=SelectiveDependenceResponsePhase.CANARY,
        preparation_input=cantera_preparation_input(design, unit.complete_unit_id, SelectiveDependenceResponsePhase.CANARY),
    )
    valid = all(not condition.stopped for value in units for condition in value.conditions)
    reset = unit.canonical_bytes() == replay.canonical_bytes()
    mechanism = ct.Solution("gri30.yaml")
    version_matches = ct.__version__ == design.cantera_version
    mechanism_resolved = mechanism.name == design.phase_name
    methane_present = "CH4" in mechanism.species_names
    carbon_monoxide_present = "CO" in mechanism.species_names
    element_ok = all(
        observation.value <= design.maximum_element_error
        for value in units
        for condition in value.conditions
        for observation in condition.receivers
        if observation.receiver_id == "element-error"
    )
    action_stage_observable = all(
        condition.action.realized_unit != condition.action.applied_unit
        for value in units
        for condition in value.conditions
    )
    source_ready = all(
        (
            valid,
            reset,
            element_ok,
            version_matches,
            mechanism_resolved,
            methane_present,
            carbon_monoxide_present,
            action_stage_observable,
        )
    )
    panel = build_panel(
        panel_id="panel.cantera.canary",
        target_id=design.target_id,
        complete_units=units,
    )
    qualification = CanteraReactionResponseCanteraSourceQualification(
        qualification_id="qualification.cantera.source",
        design_id=design.design_id,
        observed_cantera_version=ct.__version__,
        version_matches_design=version_matches,
        mechanism_resolved=mechanism_resolved,
        methane_species_present=methane_present,
        carbon_monoxide_species_present=carbon_monoxide_present,
        energy_enabled=True,
        action_stage_observable=action_stage_observable,
        reset_reproducible=reset,
        elemental_balance_qualified=valid and element_ok,
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


def verify_cantera_source_binding(
    design: CanteraReactionResponseCanteraDesign,
    qualification: CanteraReactionResponseCanteraSourceQualification,
) -> None:
    """Verify source identity without executing or observing a response."""

    import cantera as ct

    mechanism = ct.Solution("gri30.yaml")
    if qualification.design_id != design.design_id:
        raise ValueError("Cantera source qualification binds another design")
    if ct.__version__ != design.cantera_version:
        raise ValueError("Cantera package version drifted after source qualification")
    if mechanism.name != design.phase_name or not {"CH4", "CO"}.issubset(mechanism.species_names):
        raise ValueError("Cantera mechanism identity drifted after source qualification")
    if not qualification.source_ready:
        raise ValueError("Cantera source qualification is not ready")


__all__ = [
    "execute_cantera_complete_unit",
    "qualify_cantera_source",
    "verify_cantera_source_binding",
]
