"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from hashlib import sha256
import time
import numpy as np
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.methods.target_construct_validation.target_freeze import TargetConstructValidationTargetDesignFreeze
from empirical_lawhood.methods.target_construct_validation.target_records import TargetConstructValidationExecutionPhase, TargetConstructValidationNativeConditionResult, TargetConstructValidationCompleteUnitResult

from empirical_lawhood.domains.chemistry.construct_validation.response import (
    _decimal,
    _seed,
    cantera_construct_parameters as _science_cantera_construct_parameters,
    cantera_construct_result as _science_cantera_construct_result,
    fipy_construct_initial_field as _science_fipy_construct_initial_field,
    fipy_construct_parameters as _science_fipy_construct_parameters,
    fipy_construct_result as _science_fipy_construct_result,
)

def _cantera_condition(
    *,
    unit_id: str,
    denominator_id: str,
    history_id: str,
    action_id: str,
    seed: int,
) -> tuple[TargetConstructValidationNativeConditionResult, str]:
    import cantera as ct  # type: ignore[import-not-found]

    residence, initial_temperature, perturbation, requested_multiplier, accepted_multiplier = _science_cantera_construct_parameters(
        denominator_id=denominator_id, history_id=history_id, action_id=action_id, seed=seed)

    upstream_gas = ct.Solution("gri30.yaml")
    upstream_gas.TPX = 300.0, ct.one_atm, "CH4:0.05,O2:0.21,N2:0.74"
    reactor_gas = ct.Solution("gri30.yaml")
    reactor_gas.TPX = (
        initial_temperature + perturbation,
        ct.one_atm,
        "CO2:0.10,H2O:0.20,N2:0.70",
    )
    upstream = ct.Reservoir(upstream_gas, clone=True)
    reactor = ct.IdealGasReactor(reactor_gas, energy="on", volume=1.0e-3, clone=True)
    downstream = ct.Reservoir(reactor_gas, clone=True)
    base_mdot = reactor.mass / residence
    applied_mdot = accepted_multiplier * base_mdot
    controller = ct.MassFlowController(upstream, reactor, mdot=applied_mdot)
    ct.PressureController(reactor, downstream, primary=controller, K=1.0e-5)
    network = ct.ReactorNet([reactor])
    horizon = 5.0 * residence
    network.advance(horizon)
    realized_mdot = float(controller.mass_flow_rate)
    thermo = reactor.phase
    return _science_cantera_construct_result(unit_id=unit_id, denominator_id=denominator_id,
        history_id=history_id, action_id=action_id, requested_multiplier=requested_multiplier,
        accepted_multiplier=accepted_multiplier, applied_mdot=applied_mdot, realized_mdot=realized_mdot,
        horizon=horizon, co2_mole_fraction=float(thermo["CO2"].X[0]), temperature=float(reactor.T),
        solver_step_count=max(1, int(network.solver_stats.get("steps", 1))), source_version=ct.__version__)


def _fipy_condition(
    *,
    unit_id: str,
    denominator_id: str,
    history_id: str,
    action_id: str,
    seed: int,
) -> tuple[TargetConstructValidationNativeConditionResult, str]:
    import fipy  # type: ignore
    from fipy import (
        CellVariable,
        DiffusionTerm,
        Grid1D,
        ImplicitSourceTerm,
        LinearLUSolver,
        TransientTerm,
    )

    diffusivity, requested_rate, accepted_rate, applied_rate, nx, length = _science_fipy_construct_parameters(
        denominator_id=denominator_id, action_id=action_id, seed=seed)
    mesh = Grid1D(nx=nx, Lx=length)
    x = np.asarray(mesh.cellCenters[0], dtype=float)
    initial = _science_fipy_construct_initial_field(x, history_id)
    field = CellVariable(mesh=mesh, value=initial, hasOld=True)
    field.constrain(0.0, mesh.facesRight)
    source = CellVariable(mesh=mesh, value=0.0)
    equation = TransientTerm() == (
        DiffusionTerm(coeff=diffusivity) - ImplicitSourceTerm(coeff=0.10) + source
    )
    dt = 0.01
    steps = 50
    pulse_steps = 10
    source_mask = x < 0.20
    realized_integral = 0.0
    solver = LinearLUSolver(tolerance=1.0e-10, iterations=1000)
    for step in range(steps):
        field.updateOld()
        source.setValue(applied_rate if step < pulse_steps else 0.0, where=source_mask)
        equation.solve(var=field, dt=dt, solver=solver)
        if step < pulse_steps:
            realized_integral += float(np.sum(np.asarray(source.value) * mesh.cellVolumes)) * dt
    return _science_fipy_construct_result(unit_id=unit_id, denominator_id=denominator_id,
        history_id=history_id, action_id=action_id, values=np.asarray(field.value, dtype=float), x=x,
        diffusivity=diffusivity, length=length, nx=nx, requested_rate=requested_rate,
        accepted_rate=accepted_rate, applied_rate=applied_rate, realized_integral=realized_integral,
        steps=steps, source_version=fipy.__version__)


def execute_complete_unit(
    design: TargetConstructValidationTargetDesignFreeze,
    *,
    phase: TargetConstructValidationExecutionPhase,
    complete_unit_id: str,
) -> TargetConstructValidationCompleteUnitResult:
    rosters = {
        TargetConstructValidationExecutionPhase.CANARY: design.task.canary_unit_ids,
        TargetConstructValidationExecutionPhase.DEVELOPMENT: design.task.development_complete_unit_ids,
        TargetConstructValidationExecutionPhase.EVALUATION: design.task.evaluation_complete_unit_ids,
    }
    if complete_unit_id not in rosters[phase]:
        raise ValueError("complete unit lies outside the frozen phase roster")
    seed = _seed(complete_unit_id)
    started = time.monotonic()
    conditions = []
    versions: set[str] = set()
    runner = _cantera_condition if design.task.package_name == "cantera" else _fipy_condition
    for denominator_id, history_id, action_id in (
        (denominator, history, action)
        for denominator in design.task.denominator_value_ids
        for history in design.task.history_value_ids
        for action in design.task.native_action_value_ids
    ):
        condition, version = runner(
            unit_id=complete_unit_id,
            denominator_id=denominator_id,
            history_id=history_id,
            action_id=action_id,
            seed=seed,
        )
        conditions.append(condition)
        versions.add(version)
    if len(versions) != 1:
        raise ValueError("simulator version changed within a complete unit")
    values = tuple(sorted(conditions, key=lambda value: value.condition_id))
    elapsed = time.monotonic() - started
    return TargetConstructValidationCompleteUnitResult(
        result_id=f"complete-unit-result.{complete_unit_id}",
        target_id=design.task.target_id,
        phase=phase,
        complete_unit_id=complete_unit_id,
        seed=seed,
        target_design=ObjectIdentity.from_record(design.freeze_id, design),
        conditions=values,
        condition_ids_sha256=sha256(
            ("\n".join(value.condition_id for value in values) + "\n").encode("ascii")
        ).hexdigest(),
        elapsed_seconds=_decimal(elapsed),
        simulator_version=next(iter(versions)),
        solver_id=design.task.solver_id,
        generator_response_count=len(values),
        outcome_access=(
            OutcomeAccess.EVALUATION_SEALED
            if phase is TargetConstructValidationExecutionPhase.EVALUATION
            else OutcomeAccess.DEVELOPMENT_VISIBLE
        ),
    )
