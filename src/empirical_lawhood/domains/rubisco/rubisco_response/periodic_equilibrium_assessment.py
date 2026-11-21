# SPDX-License-Identifier: MPL-2.0
"""Independent BAOAB recurrence checks on original frames and realized noise.

No force, bias evaluator or random generator is called. The native reader owns
authentication of the original arrays and their selected source. A valid trace
does not establish Gaussian-stream provenance, equilibration, effective sample
size, timestep convergence, chemical applicability or a physical rate.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import math
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium import ReferenceEquilibriumSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rates import AVOGADRO_MOL, BOLTZMANN_J_K


@dataclass(frozen=True, slots=True)
class ReferenceEquilibriumCriteria(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-equilibrium-criteria'
    VERSION: ClassVar[str] = '1.0.0'

    criteria_id: str
    maximum_position_recurrence_error_nm: Decimal
    maximum_velocity_recurrence_error_nm_ps: Decimal
    maximum_heat_reconstruction_error_kj_mol: Decimal

    def __post_init__(self):
        validate_stable_id(self.criteria_id)
        for name in ('maximum_position_recurrence_error_nm', 'maximum_velocity_recurrence_error_nm_ps',
                     'maximum_heat_reconstruction_error_kj_mol'):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if not math.isfinite(float(value)):
                raise ValueError('equilibrium trace criteria must be finite numerical limits')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.criteria_id, self)


_KEYS = frozenset(('settings', 'step', 'sampling_time_seconds', 'evaluation', 'sample_ordinal',
    'coordinates_angstrom', 'velocities_nm_per_ps', 'reference_energy_hartree',
    'reference_gradient_hartree_per_bohr', 'bias_energy_kj_mol', 'bias_gradient_kj_mol_per_angstrom',
    'bias_window', 'bias_convention', 'noise_standard_normal', 'noise_draw', 'thermostat_heat_kj_mol',
    'gradient_unit', 'bohr_angstrom', 'hartree_kj_mol'))


def assess_reference_equilibrium_frames(frames, *, initial_angstrom, initial_velocity_nm_per_ps,
                                       physical_masses_dalton, settings, criteria=None):
    """Check closed-form stochastic position/velocity recurrences in one pass.

    This reducer uses the two adjacent original total forces and realized
    noise, independently of the producer's sequence of half-steps. Thermostat
    energy exchange is reconstructed; conservation of total energy or momentum
    is not imposed on thermostatted sampling. An intact prefix remains partial.
    """
    import numpy as np

    exact(settings, ReferenceEquilibriumSettings)
    if criteria is not None:
        exact(criteria, ReferenceEquilibriumCriteria)
    if any(np.iscomplexobj(x) for x in (initial_angstrom, initial_velocity_nm_per_ps, physical_masses_dalton)):
        raise ValueError('equilibrium assessment requires real initial phase space and masses')
    initial = np.array(initial_angstrom, dtype='<f8', copy=True)
    initial_velocity = np.array(initial_velocity_nm_per_ps, dtype='<f8', copy=True)
    masses = np.array(physical_masses_dalton, dtype='<f8', copy=True)
    if (initial.ndim != 2 or initial.shape[1] != 3 or not len(initial) or initial_velocity.shape != initial.shape
            or masses.shape != (len(initial),) or not np.isfinite(initial).all() or not np.isfinite(initial_velocity).all()
            or not np.isfinite(masses).all() or np.any(masses <= 0)):
        raise ValueError('equilibrium assessment requires complete finite original phase space and positive masses')
    dt = float(Fraction(settings.dynamics.step_seconds)*10**12)
    damping = float(Fraction(settings.friction_per_picosecond)*Fraction(settings.dynamics.step_seconds)*10**12)
    decay = math.exp(-damping)
    thermal = float(Fraction(BOLTZMANN_J_K)*Fraction(AVOGADRO_MOL)*Fraction(settings.temperature_kelvin)/1000)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        sigma = np.sqrt(-math.expm1(-2*damping)*thermal/masses)[:, None]
    if not np.isfinite(sigma).all() or np.any(sigma <= 0):
        raise ValueError('equilibrium assessment thermal velocity is not representable')
    hartree = COULOMB_KJ_NM_PER_MOL_E2/(.52917721092/10)
    window = settings.bias_window.to_document() if settings.bias_window is not None else None
    convention = settings.bias_convention.to_document() if settings.bias_convention is not None else None
    settings_identity = settings.identity.to_document()
    count, samples = 0, 0
    position_error, velocity_error, heat_error, observed_heat = (0.,)*4
    previous, last_time = None, None
    coordinate_sha, velocity_sha = None, None
    for frame in frames:
        step = count
        if (type(frame) is not dict or set(frame) != _KEYS or frame['settings'] != settings_identity or step > settings.dynamics.steps
                or type(frame['step']) is not int or frame['step'] != step
                or type(frame['evaluation']) is not int or frame['evaluation'] != step+1
                or type(frame['noise_draw']) is not int or frame['noise_draw'] != step
                or type(frame['sampling_time_seconds']) is not str
                or Fraction(frame['sampling_time_seconds']) != step*Fraction(settings.dynamics.step_seconds)):
            raise ValueError('equilibrium frame substitutes the ordered evaluation/noise census or exact sampling clock')
        offset = step-settings.discard_initial_steps
        ordinal = offset//settings.sample_interval_steps if offset > 0 and offset % settings.sample_interval_steps == 0 else None
        if (frame['sample_ordinal'] != ordinal or type(frame['sample_ordinal']) is not type(ordinal)
                or frame['bias_window'] != window or frame['bias_convention'] != convention):
            raise ValueError('equilibrium frame substitutes the sample schedule or selected bias identities')
        xyz, velocity, gradient, bias_gradient = (np.asarray(frame[key]) for key in
            ('coordinates_angstrom', 'velocities_nm_per_ps', 'reference_gradient_hartree_per_bohr',
             'bias_gradient_kj_mol_per_angstrom'))
        if any(array.shape != initial.shape or array.dtype.kind != 'f' or array.dtype.itemsize != 8
               or not np.isfinite(array).all() for array in (xyz, velocity, gradient, bias_gradient)):
            raise ValueError('equilibrium frame requires every finite binary64 original physical array')
        if (any(type(frame[key]) is not float or not math.isfinite(frame[key]) for key in
                ('reference_energy_hartree', 'bias_energy_kj_mol', 'thermostat_heat_kj_mol', 'bohr_angstrom', 'hartree_kj_mol'))
                or frame['gradient_unit'] != GRADIENT_UNIT or frame['bohr_angstrom'] != .52917721092
                or frame['hartree_kj_mol'] != hartree):
            raise ValueError('equilibrium frame substitutes finite energies or physical units')
        if window is None and (frame['bias_energy_kj_mol'] != 0 or np.any(bias_gradient != 0)):
            raise ValueError('unbiased equilibrium selection received a bias contribution')
        noise = frame['noise_standard_normal']
        if step == 0:
            if (not np.array_equal(xyz, initial) or not np.array_equal(velocity, initial_velocity)
                    or noise is not None or frame['thermostat_heat_kj_mol'] != 0):
                raise ValueError('equilibrium frame changes original phase space or invents initial thermal noise')
        else:
            noise = np.asarray(noise)
            if noise.shape != initial.shape or noise.dtype.kind != 'f' or noise.dtype.itemsize != 8 or not np.isfinite(noise).all():
                raise ValueError('equilibrium frame omits the complete realized thermal-noise array')
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            position = np.array(xyz/10, dtype='<f8', copy=True)
            force = -(gradient*(hartree/(.52917721092/10)) + 10*bias_gradient)
            if previous is not None:
                old_position, old_velocity, old_force = previous
                kick = dt*old_force/(2*masses[:, None])
                noise_velocity = sigma*noise
                position_residual = position-old_position-.5*dt*((1+decay)*(old_velocity+kick)+noise_velocity)
                velocity_residual = (velocity-decay*old_velocity
                    -dt*(decay*old_force+force)/(2*masses[:, None])-noise_velocity)
                before_bath = old_velocity+kick
                after_bath = decay*(old_velocity+kick)+noise_velocity
                reconstructed_heat = .5*float(np.sum(masses[:, None]*(after_bath-before_bath)*(after_bath+before_bath)))
                if not math.isfinite(reconstructed_heat):
                    raise ValueError('equilibrium assessment reconstructed nonfinite thermostat heat')
                position_error = max(position_error, float(np.max(np.abs(position_residual))))
                velocity_error = max(velocity_error, float(np.max(np.abs(velocity_residual))))
                heat_error = max(heat_error, abs(reconstructed_heat-frame['thermostat_heat_kj_mol']))
        if not np.isfinite(force).all():
            raise ValueError('equilibrium assessment reconstructed a nonfinite physical force')
        observed_heat = math.fsum((observed_heat, frame['thermostat_heat_kj_mol']))
        previous = position, np.array(velocity, dtype='<f8', copy=True), np.array(force, dtype='<f8', copy=True)
        coordinate_sha = sha256(np.asarray(xyz, dtype='<f8').tobytes()).hexdigest()
        velocity_sha = sha256(np.asarray(velocity, dtype='<f8').tobytes()).hexdigest()
        last_time = frame['sampling_time_seconds']
        count += 1
        samples += ordinal is not None
    complete = count == settings.dynamics.steps+1
    findings = set()
    disposition = 'UNEVALUABLE'
    if not complete:
        findings.add('selected-sampling-horizon-incomplete')
    if criteria is not None and count:
        for measured, limit, reason in (
            (position_error, criteria.maximum_position_recurrence_error_nm, 'position-recurrence-exceeds-selection'),
            (velocity_error, criteria.maximum_velocity_recurrence_error_nm_ps, 'velocity-recurrence-exceeds-selection'),
            (heat_error, criteria.maximum_heat_reconstruction_error_kj_mol, 'thermostat-heat-exceeds-selection')):
            if Decimal.from_float(measured) > limit:
                findings.add(reason)
        if findings-{'selected-sampling-horizon-incomplete'}:
            disposition = 'FALSIFIED'
        elif complete:
            disposition = 'SATISFIED'
    return dict(settings=settings.identity.to_document(), criteria=criteria.identity.to_document() if criteria else None,
        mass_sha256=sha256(masses.tobytes()).hexdigest(), physical_atoms=len(initial),
        initial_coordinate_sha256=sha256(initial.tobytes()).hexdigest(),
        initial_velocity_sha256=sha256(initial_velocity.tobytes()).hexdigest(),
        final_coordinate_sha256=coordinate_sha, final_velocity_sha256=velocity_sha,
        retained_frames=count, retained_noise_draws=max(0, count-1), selected_steps=settings.dynamics.steps,
        retained_sample_frames=samples, selected_sample_frames=settings.expected_samples,
        selected_sampling_horizon_complete=complete, observed_sampling_time_seconds=last_time,
        maximum_position_recurrence_error_nm=position_error if count > 1 else None,
        maximum_velocity_recurrence_error_nm_ps=velocity_error if count > 1 else None,
        maximum_heat_reconstruction_error_kj_mol=heat_error if count > 1 else None,
        thermostat_heat_kj_mol=observed_heat if count else None, selected_trace_criteria=disposition,
        findings=tuple(sorted(findings)), new_operator_evaluations=0, new_bias_evaluations=0,
        random_stream_provenance='NOT_TESTED_BY_MECHANICS_REDUCER', step_convergence='UNEVALUABLE',
        force_accuracy='UNEVALUABLE', bias_energy_consistency='NOT_TESTED_BY_MECHANICS_REDUCER',
        equilibrium_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')
