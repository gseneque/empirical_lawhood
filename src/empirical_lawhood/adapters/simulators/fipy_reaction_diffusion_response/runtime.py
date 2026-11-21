"""FiPy complete-unit execution for a signed reaction--diffusion field."""

from __future__ import annotations

from decimal import Decimal

import numpy as np

from empirical_lawhood.methods.selective_dependence_response.contracts import SelectiveDependenceResponseCompleteUnitResult, SelectiveDependenceResponseConditionResult, SelectiveDependenceResponsePhase, SelectiveDependenceResponseTargetPanel
from empirical_lawhood.science.identity.provenance import ObjectIdentity

from empirical_lawhood.methods.selective_dependence_response.preparation_inputs import SelectiveDependenceResponsePreparationInput

from empirical_lawhood.domains.chemistry.reaction_diffusion.preparation_inputs import DRAW_VARIABLE_IDS, fipy_preparation_input
from empirical_lawhood.domains.chemistry.reaction_diffusion import response as scientific
from empirical_lawhood.domains.chemistry.reaction_diffusion.contracts import FipyReactionDiffusionResponseFiPyDesign, FipyReactionDiffusionResponseFiPySourceQualification





def _condition(
    design: FipyReactionDiffusionResponseFiPyDesign,
    preparation: dict[str, float],
    *,
    denominator_id: str,
    history_id: str,
    action_id: str,
    horizon_id: str,
) -> tuple[SelectiveDependenceResponseConditionResult, tuple[Decimal, ...]]:
    import fipy as fp  # type: ignore[import-untyped]

    length = float(design.domain_length)
    dx = length / design.mesh_cells
    mesh = fp.Grid1D(nx=design.mesh_cells, dx=dx)
    x = np.asarray(mesh.cellCenters[0], dtype=float)
    values = scientific.initial_field(design, preparation, x=x, history_id=history_id)
    field = fp.CellVariable(mesh=mesh, value=values, hasOld=True)
    field.constrain(0.0, mesh.facesRight)
    source_region = scientific.source_mask(x)
    requested, outside, accepted, diffusivity, horizon = scientific.condition_parameters(
        design, denominator_id=denominator_id, action_id=action_id, horizon_id=horizon_id
    )
    dt = float(design.timestep_seconds)
    action_duration = float(design.action_duration_seconds)
    source = fp.CellVariable(mesh=mesh, value=0.0)
    equation = (
        fp.TransientTerm()
        == fp.DiffusionTerm(coeff=diffusivity) - (float(design.decay_rate) * field) + source
    )
    balance = scientific.FieldBalance(scientific.field_mass(values, dx))
    elapsed = 0.0
    steps = 0
    stopped = False
    stop_code: str | None = None
    margins: tuple[Decimal, ...]
    try:
        while elapsed < horizon - dt / 2:
            step = min(dt, horizon - elapsed)
            field.updateOld()
            applied = accepted if elapsed < action_duration - dt / 2 else 0.0
            source.setValue(applied, where=source_region)
            previous_mass = scientific.field_mass(np.asarray(field.value), dx)
            equation.solve(var=field, dt=step)
            current = np.asarray(field.value, dtype=float)
            balance.observe(
                previous_mass=previous_mass, current=current, applied=applied,
                source_region=source_region, dx=dx, diffusivity=diffusivity,
                decay_rate=design.decay_rate, step=step,
            )
            elapsed += step
            steps += 1
            if steps > design.maximum_solver_steps:
                raise RuntimeError("solver-step-ceiling")
        final = np.asarray(field.value, dtype=float)
        observed, margins = scientific.receiver_margins(
            design, final=final, x=x, dx=dx, diffusivity=diffusivity, balance=balance
        )
    except Exception as error:  # FiPy failure is retained, never imputed.
        stopped = True
        stop_code = f"fipy-{type(error).__name__.lower()}"
        observed = {
            "balance-error": 0.0,
            "boundary-flux": 0.0,
            "downstream-mean": 0.0,
            "field-mass": 0.0,
            "field-maximum": 0.0,
            "field-minimum": 0.0,
        }
        margins = ()
    return scientific.condition_result(
        denominator_id=denominator_id, history_id=history_id, action_id=action_id,
        horizon_id=horizon_id, requested=requested, accepted=accepted, outside=outside,
        horizon=horizon, action_duration=action_duration,
        source_region_length=scientific.field_mass(source_region, dx),
        observed=observed, margins=margins, stopped=stopped, stop_code=stop_code,
    )


def execute_fipy_complete_unit(
    design: FipyReactionDiffusionResponseFiPyDesign,
    *,
    complete_unit_id: str,
    phase: SelectiveDependenceResponsePhase,
    preparation_input: SelectiveDependenceResponsePreparationInput | None = None,
) -> SelectiveDependenceResponseCompleteUnitResult:
    if type(preparation_input) is not SelectiveDependenceResponsePreparationInput:
        raise ValueError("native complete unit requires explicit numerical preparation inputs before solver work")
    preparation_input.validate_context(
        complete_unit_id=complete_unit_id,
        target_id=design.target_id,
        target_design=ObjectIdentity.from_record(design.design_id, design),
        phase=phase.value,
        draw_variable_ids=DRAW_VARIABLE_IDS,
    )
    preparation = scientific.preparation(preparation_input)
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
    return scientific.complete_unit_result(
        design, complete_unit_id=complete_unit_id, phase=phase,
        preparation=preparation, raw=raw,
    )


def qualify_fipy_source(
    design: FipyReactionDiffusionResponseFiPyDesign,
    *,
    canary_unit_ids: tuple[str, ...],
) -> tuple[FipyReactionDiffusionResponseFiPySourceQualification, SelectiveDependenceResponseTargetPanel]:
    preparation_inputs = tuple(
        fipy_preparation_input(design, unit_id, SelectiveDependenceResponsePhase.CANARY)
        for unit_id in canary_unit_ids
    )
    import fipy

    units = tuple(
        execute_fipy_complete_unit(
            design,
            complete_unit_id=unit_id,
            phase=SelectiveDependenceResponsePhase.CANARY,
            preparation_input=preparation_input,
        )
        for unit_id, preparation_input in zip(canary_unit_ids, preparation_inputs, strict=True)
    )
    if not units:
        raise ValueError("FiPy source qualification requires excluded canaries")
    unit = units[0]
    replay = execute_fipy_complete_unit(
        design,
        complete_unit_id=unit.complete_unit_id,
        phase=SelectiveDependenceResponsePhase.CANARY,
        preparation_input=fipy_preparation_input(design, unit.complete_unit_id, SelectiveDependenceResponsePhase.CANARY),
    )
    return scientific.source_qualification(
        design, units=units, replay=replay, observed_version=fipy.__version__
    )


def verify_fipy_source_binding(
    design: FipyReactionDiffusionResponseFiPyDesign,
    qualification: FipyReactionDiffusionResponseFiPySourceQualification,
) -> None:
    """Verify source identity without executing or observing a response."""

    import fipy

    if qualification.design_id != design.design_id:
        raise ValueError("FiPy source qualification binds another design")
    if fipy.__version__ != design.fipy_version:
        raise ValueError("FiPy package version drifted after source qualification")
    if not qualification.source_ready:
        raise ValueError("FiPy source qualification is not ready")


__all__ = [
    "execute_fipy_complete_unit",
    "qualify_fipy_source",
    "verify_fipy_source_binding",
]
