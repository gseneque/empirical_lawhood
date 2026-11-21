# SPDX-License-Identifier: MPL-2.0
"""Declared BAOAB Langevin sampling with separate reference and bias forces.

The caller authenticates the material, masses, force operator, bias and initial
phase space. Original force returns and random draws belong in native custody.
This numerical component neither establishes equilibration nor supplies an
unbiased dynamical clock or a free energy. It never retries failed work.
"""

from dataclasses import dataclass
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import math
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rates import AVOGADRO_MOL, BOLTZMANN_J_K


@dataclass(frozen=True, slots=True)
class ReferenceEquilibriumSettings(CanonicalRecord):
    """Sampling selections; a discarded prefix does not prove equilibration."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-equilibrium-settings'
    VERSION: ClassVar[str] = '1.0.0'

    settings_id: str
    dynamics: ReferenceDynamicsSettings
    temperature_kelvin: Decimal
    friction_per_picosecond: Decimal
    random_seed: int
    random_generator: str
    discard_initial_steps: int
    sample_interval_steps: int
    bias_window: ObjectIdentity | None
    bias_convention: ObjectIdentity | None

    def __post_init__(self):
        validate_stable_id(self.settings_id)
        exact(self.dynamics, ReferenceDynamicsSettings)
        for name in ('temperature_kelvin', 'friction_per_picosecond'):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value <= 0 or not math.isfinite(float(value)) or float(value) == 0:
                raise ValueError('equilibrium temperature and friction must be positive representable selections')
        if (type(self.random_seed) is not int or not 0 <= self.random_seed < 2**128
                or self.random_generator != 'NUMPY_PCG64DXSM_STANDARD_NORMAL_FLOAT64'):
            raise ValueError('equilibrium sampling requires an explicit seed and normal generator')
        if (type(self.discard_initial_steps) is not int or not 0 <= self.discard_initial_steps < self.dynamics.steps
                or type(self.sample_interval_steps) is not int or self.sample_interval_steps <= 0
                or self.expected_samples <= 0):
            raise ValueError('equilibrium sampling requires a complete declared prefix and nonempty sample schedule')
        if (self.bias_window is None) != (self.bias_convention is None):
            raise ValueError('equilibrium bias requires both exact window and convention identities')
        if self.bias_window is not None:
            exact(self.bias_window, ObjectIdentity)
            exact(self.bias_convention, ObjectIdentity)
            if (self.bias_window.object_schema != UmbrellaWindow.SCHEMA
                    or self.bias_window.object_version != UmbrellaWindow.VERSION
                    or self.bias_convention.object_schema != ReferenceBiasConvention.SCHEMA
                    or self.bias_convention.object_version != ReferenceBiasConvention.VERSION):
                raise ValueError('equilibrium bias identities have unsupported schemas or revisions')
        damping = float(Fraction(self.friction_per_picosecond)*Fraction(self.dynamics.step_seconds)*10**12)
        thermal = self.thermal_energy_kj_mol
        if (not math.isfinite(damping) or damping <= 0 or not 0 <= math.exp(-damping) < 1
                or not math.isfinite(thermal) or thermal <= 0):
            raise ValueError('equilibrium thermal energy and damping must be numerically resolved')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.settings_id, self)

    @property
    def thermal_energy_kj_mol(self):
        return float(Fraction(BOLTZMANN_J_K)*Fraction(AVOGADRO_MOL)*Fraction(self.temperature_kelvin)/1000)

    @property
    def expected_samples(self):
        return (self.dynamics.steps-self.discard_initial_steps)//self.sample_interval_steps

    def sample_ordinal(self, step):
        if type(step) is not int or not 0 <= step <= self.dynamics.steps:
            raise ValueError('sample labeling requires an actual selected integration step')
        elapsed = step-self.discard_initial_steps
        return elapsed//self.sample_interval_steps if elapsed > 0 and elapsed % self.sample_interval_steps == 0 else None


def propagate_reference_equilibrium(*, operator, bias, initial_angstrom, initial_velocity_nm_per_ps,
                                    physical_masses_dalton, settings, observe, capture_noise, capture):
    """Integrate B(half), A(half), exact OU, A(half), B(half) at natural masses.

    One original reference evaluation starts the trace and each step adds one.
    A bias callback returns only the accepted bias component's explicit units
    and identities; None explicitly selects no bias. Independent copies of
    each standard-normal array reach capture_noise before the next force call.
    Complete synchronized frames also retain that draw and both force parts.
    The original native caller must retain raw returns before validation here.
    """
    import numpy as np

    exact(settings, ReferenceEquilibriumSettings)
    if (not callable(getattr(operator, 'evaluate', None)) or not callable(observe)
            or not callable(capture) or not callable(capture_noise)
            or (bias is None) != (settings.bias_window is None) or bias is not None and not callable(bias)):
        raise ValueError('equilibrium sampling requires its selected reference, bias and original capture callbacks')
    if any(np.iscomplexobj(x) for x in (initial_angstrom, initial_velocity_nm_per_ps, physical_masses_dalton)):
        raise ValueError('equilibrium phase space and masses must be real')
    xyz = np.array(initial_angstrom, dtype='<f8', copy=True)
    velocity = np.array(initial_velocity_nm_per_ps, dtype='<f8', copy=True)
    masses = np.array(physical_masses_dalton, dtype='<f8', copy=True)
    if (xyz.ndim != 2 or xyz.shape[1] != 3 or not len(xyz) or velocity.shape != xyz.shape
            or masses.shape != (len(xyz),) or not np.isfinite(xyz).all() or not np.isfinite(velocity).all()
            or not np.isfinite(masses).all() or np.any(masses <= 0)):
        raise ValueError('equilibrium sampling requires all finite positions, velocities and positive physical masses')
    dt = settings.dynamics.step_picoseconds
    damping = float(Fraction(settings.friction_per_picosecond)*Fraction(settings.dynamics.step_seconds)*10**12)
    decay = math.exp(-damping)
    variance_factor = -math.expm1(-2*damping)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        sigma = np.sqrt(variance_factor*settings.thermal_energy_kj_mol/masses)[:, None]
        initial_kinetic = .5*float(np.sum(masses[:, None]*velocity**2))
    if not np.isfinite(sigma).all() or np.any(sigma <= 0) or not math.isfinite(initial_kinetic):
        raise ValueError('equilibrium thermal velocity or initial kinetic energy is not representable')
    rng = np.random.Generator(np.random.PCG64DXSM(settings.random_seed))
    bohr = .52917721092
    hartree = COULOMB_KJ_NM_PER_MOL_E2/(bohr/10)
    bias_window = settings.bias_window.to_document() if settings.bias_window is not None else None
    bias_convention = settings.bias_convention.to_document() if settings.bias_convention is not None else None
    settings_identity = settings.identity.to_document()
    calls, invocations, returns, completed, noise_draws, retained_noise, frames, samples = (0,)*8
    current_step = 0
    heat_total = 0.

    def evaluate(positions, step):
        nonlocal calls, invocations, returns, completed
        if bias is None:
            bias_energy, bias_gradient = 0., np.zeros_like(positions)
        else:
            supplied = positions.copy()
            returned_bias = bias(supplied)
            if (not np.array_equal(supplied, positions) or returned_bias['window'] != bias_window
                    or returned_bias['convention'] != bias_convention or returned_bias['physical_atoms'] != len(xyz)
                    or returned_bias['reference_energy_included'] is not False
                    or returned_bias['gradient_kind'] != 'ENERGY_DERIVATIVE_NOT_FORCE'):
                raise ValueError('equilibrium bias substitutes selected coordinates, identities or gradient meaning')
            bias_energy = float(returned_bias['energy_kj_mol'])
            raw_bias = returned_bias['gradient_kj_mol_per_angstrom']
            if np.iscomplexobj(raw_bias):
                raise ValueError('equilibrium bias gradient must be real')
            bias_gradient = np.array(raw_bias, dtype='<f8', copy=True)
            if not math.isfinite(bias_energy) or bias_gradient.shape != xyz.shape or not np.isfinite(bias_gradient).all():
                raise ValueError('equilibrium bias is not a complete finite physical energy/gradient')
        calls += 1
        coordinate_sha = sha256(positions.tobytes()).hexdigest()
        observe(dict(event='equilibrium-evaluation-entry', evaluation=calls, step=step,
            sampling_time_seconds=str(settings.dynamics.time_at_step(step)), coordinate_sha256=coordinate_sha))
        supplied = positions.copy()
        invocations += 1
        returned = operator.evaluate(supplied)
        returns += 1
        if not np.array_equal(supplied, positions):
            raise ValueError('equilibrium reference operator changed the supplied coordinates')
        energy = float(returned['energy_hartree'])
        raw_gradient = returned['gradient_hartree_per_bohr']
        if np.iscomplexobj(raw_gradient):
            raise ValueError('equilibrium reference gradient must be real')
        gradient = np.array(raw_gradient, dtype='<f8', copy=True)
        if (returned['gradient_unit'] != GRADIENT_UNIT or returned['bohr_angstrom'] != bohr
                or returned['hartree_kj_mol'] != hartree or gradient.shape != xyz.shape
                or not np.isfinite(gradient).all() or not math.isfinite(energy)):
            raise ValueError('equilibrium reference return changes full gradient census or physical units')
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            acceleration = -(gradient*(10*hartree/bohr) + 10*bias_gradient)/masses[:, None]
        if not np.isfinite(acceleration).all():
            raise ValueError('equilibrium total acceleration is not finite')
        completed += 1
        observe(dict(event='equilibrium-evaluation-return', evaluation=calls, step=step,
            coordinate_sha256=coordinate_sha, reference_energy_hartree=energy, bias_energy_kj_mol=bias_energy,
            reference_gradient_sha256=sha256(gradient.tobytes()).hexdigest(),
            bias_gradient_sha256=sha256(bias_gradient.tobytes()).hexdigest()))
        return energy, gradient, bias_energy, bias_gradient, acceleration

    def retain(step, evaluated, noise, heat):
        nonlocal frames, samples
        energy, gradient, bias_energy, bias_gradient, _ = evaluated
        ordinal = settings.sample_ordinal(step)
        frame = dict(settings=deepcopy(settings_identity), step=step, sampling_time_seconds=str(settings.dynamics.time_at_step(step)),
            evaluation=completed, sample_ordinal=ordinal, coordinates_angstrom=xyz.copy(),
            velocities_nm_per_ps=velocity.copy(), reference_energy_hartree=energy,
            reference_gradient_hartree_per_bohr=gradient.copy(), bias_energy_kj_mol=bias_energy,
            bias_gradient_kj_mol_per_angstrom=bias_gradient.copy(), bias_window=deepcopy(bias_window),
            bias_convention=deepcopy(bias_convention), noise_standard_normal=None if noise is None else noise.copy(),
            noise_draw=step, thermostat_heat_kj_mol=heat, gradient_unit=GRADIENT_UNIT,
            bohr_angstrom=bohr, hartree_kj_mol=hartree)
        capture(frame)
        frames += 1
        samples += ordinal is not None
        observe(dict(event='equilibrium-frame-return', step=step, evaluation=completed, sample_ordinal=ordinal,
            coordinate_sha256=sha256(xyz.tobytes()).hexdigest(), velocity_sha256=sha256(velocity.tobytes()).hexdigest()))

    try:
        evaluated = evaluate(xyz, 0)
        retain(0, evaluated, None, 0.)
        for current_step in range(1, settings.dynamics.steps+1):
            with np.errstate(over='raise', invalid='raise'):
                first_velocity = velocity+.5*dt*evaluated[-1]
                middle_position = xyz+5*dt*first_velocity
            if not np.isfinite(first_velocity).all() or not np.isfinite(middle_position).all():
                raise ValueError('equilibrium first kick or drift is not finite')
            state_before = rng.bit_generator.state
            noise = rng.standard_normal(size=xyz.shape, dtype=np.float64)
            noise_draws += 1
            capture_noise(dict(step=current_step, standard_normal=noise.copy(),
                numpy_version=np.__version__, generator=settings.random_generator,
                state_before=state_before, state_after=rng.bit_generator.state))
            retained_noise += 1
            observe(dict(event='equilibrium-noise-return', step=current_step,
                noise_sha256=sha256(noise.tobytes()).hexdigest()))
            with np.errstate(over='raise', invalid='raise', divide='raise'):
                bath_velocity = decay*first_velocity+sigma*noise
                trial = middle_position+5*dt*bath_velocity
                heat = .5*float(np.sum(masses[:, None]*(bath_velocity-first_velocity)*(bath_velocity+first_velocity)))
            if not np.isfinite(trial).all() or not np.isfinite(bath_velocity).all() or not math.isfinite(heat):
                raise ValueError('equilibrium thermal update or second drift is not finite')
            next_evaluated = evaluate(trial, current_step)
            with np.errstate(over='raise', invalid='raise'):
                next_velocity = bath_velocity+.5*dt*next_evaluated[-1]
                kinetic = .5*float(np.sum(masses[:, None]*next_velocity**2))
            if not np.isfinite(next_velocity).all() or not math.isfinite(kinetic):
                raise ValueError('equilibrium synchronized velocity or kinetic energy is not finite')
            xyz, velocity, evaluated = trial, next_velocity, next_evaluated
            heat_total = math.fsum((heat_total, heat))
            retain(current_step, evaluated, noise, heat)
    except BaseException as error:
        observe(dict(event='equilibrium-error', step=current_step, evaluation_attempts=calls,
            operator_invocations=invocations, operator_returns=returns, completed_evaluations=completed,
            noise_draws=noise_draws, retained_noise_draws=retained_noise, captured_frames=frames,
            captured_sample_frames=samples, error_type=type(error).__name__, error=str(error)))
        raise
    summary = dict(settings=settings.identity.to_document(), algorithm='BAOAB',
        sampling_time_seconds=str(settings.dynamics.time_at_step(settings.dynamics.steps)),
        step_seconds=str(settings.dynamics.step_seconds), completed_steps=settings.dynamics.steps,
        physical_atoms=len(xyz), mass_sha256=sha256(masses.tobytes()).hexdigest(),
        operator_invocations=invocations, operator_returns=returns, completed_evaluations=completed,
        noise_draws=noise_draws, retained_noise_draws=retained_noise, captured_frames=frames,
        captured_sample_frames=samples, selected_sample_frames=settings.expected_samples,
        numpy_version=np.__version__, random_generator=settings.random_generator, random_seed=settings.random_seed,
        temperature_kelvin=str(settings.temperature_kelvin), friction_per_picosecond=str(settings.friction_per_picosecond),
        thermostat='LANGEVIN_EXACT_OU_SPLITTING', thermostat_heat_kj_mol=heat_total,
        bias_window=bias_window, bias_convention=bias_convention, constraints='NONE', mass_repartitioning=False,
        velocity_rescaling=False, coordinate_wrapping=False, physical_rate_clock='NOT_SUPPLIED_BY_EQUILIBRIUM_SAMPLER',
        equilibrium_admission='UNEVALUABLE', step_convergence='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')
    return xyz.copy(), velocity.copy(), summary
