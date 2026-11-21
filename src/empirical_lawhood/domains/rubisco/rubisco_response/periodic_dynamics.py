# SPDX-License-Identifier: MPL-2.0
"""Natural-mass, fixed-step dynamics of a complete reference force operator.

The native caller owns the authenticated physical masses, initial ensemble,
operator, resource selection and original-call custody. This numerical seam
adds no thermostat, constraint, bias, mass change or rate interpretation.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import math
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import GRADIENT_UNIT, reference_force_units


def _integer_product(value, multiplier):
    """Multiply an exact decimal by a count without ambient-context rounding."""
    sign, digits, exponent = value.as_tuple()
    coefficient = int(''.join(str(digit) for digit in digits)) * multiplier
    return Decimal((sign, tuple(int(digit) for digit in str(coefficient)), exponent))


@dataclass(frozen=True, slots=True)
class ReferenceDynamicsSettings(CanonicalRecord):
    """A physical observation horizon, never an experiment wall-time limit."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-dynamics-settings'
    VERSION: ClassVar[str] = '1.0.0'

    settings_id: str
    step_seconds: Decimal
    steps: int

    def __post_init__(self):
        validate_stable_id(self.settings_id)
        validate_decimal(self.step_seconds, field_name='step_seconds', minimum=Decimal(0))
        if not 0 < self.step_seconds <= Decimal('5e-16'):
            raise ValueError('reactive reference dynamics requires the selected 0.5 fs step or its refinement')
        if type(self.steps) is not int or self.steps <= 0:
            raise ValueError('reference dynamics requires a positive selected physical step count')
        if not math.isfinite(self.step_picoseconds) or self.step_picoseconds <= 0:
            raise ValueError('the selected physical step is not representable by the numerical integrator')
        if not math.isfinite(float(self.time_at_step(self.steps))):
            raise ValueError('the selected physical observation horizon is not finite in the numerical representation')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.settings_id, self)

    @property
    def step_picoseconds(self):
        sign, digits, exponent = self.step_seconds.as_tuple()
        return float(Decimal((sign, digits, exponent + 12)))

    def time_at_step(self, step):
        if type(step) is not int or not 0 <= step <= self.steps:
            raise ValueError('physical time requires an actual step in the selected observation horizon')
        return _integer_product(self.step_seconds, step)


def propagate_reference_trajectory(*, operator, initial_angstrom, initial_velocity_nm_per_ps,
                                   physical_masses_dalton, settings, observe, capture):
    """Advance all physical atoms with synchronized velocity-Verlet states.

    One fresh complete E/G starts the trajectory. Each selected step uses one
    new complete E/G, and its final force starts the next step. Every frame,
    including step zero, reaches ``capture`` with positions, synchronized
    velocities, energy and the full gradient. The callbacks own durable output.
    A failed force or capture is never retried here.

    Positions remain unwrapped. Forces use the operator's selected fixed cell.
    In OpenMM's nm/ps/dalton/kJ-per-mole convention, acceleration is force/mass
    and kinetic energy is sum(m*v*v)/2. Electronic returns retain their exact
    existing PySCF-Bohr and MM-consistent Hartree conversion.
    """
    import numpy as np
    from empirical_lawhood.methods.electronic_structure.fixed_cell_sampling import velocity_verlet_drift, velocity_verlet_finish

    exact(settings, ReferenceDynamicsSettings)
    settings_identity = settings.identity.to_document()
    xyz = np.array(initial_angstrom, dtype='<f8', copy=True)
    velocity = np.array(initial_velocity_nm_per_ps, dtype='<f8', copy=True)
    masses = np.array(physical_masses_dalton, dtype='<f8', copy=True)
    if (xyz.ndim != 2 or xyz.shape[1] != 3 or not len(xyz)
            or velocity.shape != xyz.shape or masses.shape != (len(xyz),)
            or not np.isfinite(xyz).all() or not np.isfinite(velocity).all()
            or not np.isfinite(masses).all() or np.any(masses <= 0)
            or not callable(observe) or not callable(capture)
            or not callable(getattr(operator, 'evaluate', None))):
        raise ValueError('reference dynamics requires every finite physical position, velocity and positive mass')
    dt = settings.step_picoseconds
    calls, invocations, returns, completed, frames = 0, 0, 0, 0, 0
    units = None
    current_step = 0
    initial_energy = None
    maximum_energy_drift = 0.0
    maximum_momentum_change = 0.0
    with np.errstate(over='raise', invalid='raise'):
        initial_momentum = np.sum(masses[:, None] * velocity, axis=0)
        initial_kinetic = .5 * float(np.sum(masses[:, None] * velocity ** 2))
    if not math.isfinite(initial_kinetic) or not np.isfinite(initial_momentum).all():
        raise ValueError('reference dynamics requires finite initial physical energy and momentum before force entry')
    mass_sha = sha256(masses.tobytes()).hexdigest()

    def evaluate(positions, step):
        nonlocal calls, invocations, returns, completed, units
        calls += 1
        stamp = str(settings.time_at_step(step))
        coordinate_sha = sha256(positions.tobytes()).hexdigest()
        observe(dict(event='trajectory-evaluation-entry', evaluation=calls, step=step,
            physical_time_seconds=stamp, coordinate_sha256=coordinate_sha, physical_atoms=len(xyz)))
        delivered = positions.copy()
        invocations += 1
        returned = operator.evaluate(delivered)
        returns += 1
        if not np.array_equal(delivered, positions):
            raise ValueError('the force operator changed its delivered physical coordinates')
        energy = float(returned['energy_hartree'])
        gradient = np.array(returned['gradient_hartree_per_bohr'], dtype='<f8', copy=True)
        current_units = reference_force_units(returned)
        bohr, hartree = current_units
        if (gradient.shape != xyz.shape or not np.isfinite(gradient).all()
                or not math.isfinite(energy) or units is not None and units != current_units):
            raise ValueError('reference dynamics received an incomplete force or changed physical units')
        units = current_units
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            acceleration = -gradient * (10 * hartree / bohr) / masses[:, None]
        if not np.isfinite(acceleration).all():
            raise ValueError('reference dynamics returned a nonfinite physical acceleration')
        completed += 1
        observe(dict(event='trajectory-evaluation-return', evaluation=calls, step=step,
            physical_time_seconds=stamp, coordinate_sha256=coordinate_sha,
            gradient_sha256=sha256(gradient.tobytes()).hexdigest(), energy_hartree=energy,
            gradient_unit=GRADIENT_UNIT))
        return energy, gradient, acceleration

    def retain(step, energy, gradient):
        nonlocal frames, initial_energy, maximum_energy_drift, maximum_momentum_change
        with np.errstate(over='raise', invalid='raise'):
            kinetic = float(.5 * np.sum(masses[:, None] * velocity ** 2))
            total = energy * units[1] + kinetic
            momentum = np.sum(masses[:, None] * velocity, axis=0)
        if not math.isfinite(total) or not np.isfinite(momentum).all():
            raise ValueError('reference dynamics produced a nonfinite synchronized energy or momentum')
        if initial_energy is None:
            initial_energy = total
        maximum_energy_drift = max(maximum_energy_drift, abs(total - initial_energy))
        maximum_momentum_change = max(maximum_momentum_change,
            float(np.max(np.abs(momentum - initial_momentum))))
        # Capture owns these independent copies. Changing them cannot change
        # the continued numerical state or an input supplied by the caller.
        frame = dict(step=step, physical_time_seconds=str(settings.time_at_step(step)),
            evaluation=completed, coordinates_angstrom=xyz.copy(), velocities_nm_per_ps=velocity.copy(),
            energy_hartree=energy, gradient_hartree_per_bohr=gradient.copy(),
            gradient_unit=GRADIENT_UNIT, bohr_angstrom=units[0], hartree_kj_mol=units[1])
        capture(frame)
        frames += 1
        observe(dict(event='trajectory-frame-return', step=step,
            physical_time_seconds=str(settings.time_at_step(step)), evaluation=completed,
            coordinate_sha256=sha256(xyz.tobytes()).hexdigest(),
            velocity_sha256=sha256(velocity.tobytes()).hexdigest(),
            kinetic_energy_kj_mol=kinetic, total_energy_kj_mol=total))

    try:
        energy, gradient, acceleration = evaluate(xyz, 0)
        retain(0, energy, gradient)
        for current_step in range(1, settings.steps + 1):
            trial, half_velocity = velocity_verlet_drift(xyz, velocity, acceleration, dt)
            energy, gradient, next_acceleration = evaluate(trial, current_step)
            next_velocity = velocity_verlet_finish(half_velocity, next_acceleration, dt)
            xyz, velocity, acceleration = trial, next_velocity, next_acceleration
            retain(current_step, energy, gradient)
    except BaseException as error:
        observe(dict(event='trajectory-error', step=current_step,
            evaluation_attempts=calls, operator_invocations=invocations, operator_returns=returns,
            completed_evaluations=completed, captured_frames=frames,
            error_type=type(error).__name__, error=str(error)))
        raise
    summary = dict(settings=settings_identity, algorithm='VELOCITY_VERLET',
        physical_clock_id='clock.rubisco.physical-seconds', physical_time_seconds=str(settings.time_at_step(settings.steps)),
        step_seconds=str(settings.step_seconds), completed_steps=settings.steps,
        physical_atoms=len(xyz), mass_sha256=mass_sha, operator_invocations=invocations,
        operator_returns=returns, completed_evaluations=completed,
        captured_frames=frames, gradient_unit=GRADIENT_UNIT, bohr_angstrom=units[0], hartree_kj_mol=units[1],
        maximum_absolute_energy_drift_kj_mol=maximum_energy_drift,
        maximum_momentum_component_change_dalton_nm_ps=maximum_momentum_change,
        thermostat='NONE', constraints='NONE', bias='NONE', mass_repartitioning=False,
        velocity_rescaling=False, coordinate_wrapping=False,
        numerical_accuracy='UNEVALUABLE', initial_ensemble_admission='UNEVALUABLE', rate_admission='UNEVALUABLE')
    return xyz.copy(), velocity.copy(), summary
