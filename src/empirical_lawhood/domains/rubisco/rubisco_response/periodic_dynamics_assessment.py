# SPDX-License-Identifier: MPL-2.0
"""Independent mechanics checks on retained reference trajectory frames.

This reducer never constructs or calls a force operator. Structural input
changes refuse. Finite numerical violations remain findings. An intact prefix
retains its actual duration and cannot satisfy a complete selected horizon.
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
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT


@dataclass(frozen=True, slots=True)
class ReferenceTrajectoryCriteria(CanonicalRecord):
    """Explicit trace criteria, separate from force or physical-rate accuracy."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-trajectory-criteria'
    VERSION: ClassVar[str] = '1.0.0'

    criteria_id: str
    maximum_position_recurrence_error_nm: Decimal
    maximum_velocity_recurrence_error_nm_ps: Decimal
    maximum_energy_drift_kj_mol: Decimal
    maximum_momentum_change_dalton_nm_ps: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.criteria_id)
        for name in ('maximum_position_recurrence_error_nm', 'maximum_velocity_recurrence_error_nm_ps',
                     'maximum_energy_drift_kj_mol', 'maximum_momentum_change_dalton_nm_ps'):
            value = getattr(self, name)
            if value is None and name == 'maximum_momentum_change_dalton_nm_ps':
                continue
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if not math.isfinite(float(value)):
                raise ValueError('trajectory criteria must be finite numerical limits')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.criteria_id, self)


_FRAME_KEYS = frozenset(('step', 'physical_time_seconds', 'evaluation', 'coordinates_angstrom',
    'velocities_nm_per_ps', 'energy_hartree', 'gradient_hartree_per_bohr', 'gradient_unit',
    'bohr_angstrom', 'hartree_kj_mol'))


def assess_reference_trajectory_frames(frames, *, initial_angstrom, initial_velocity_nm_per_ps,
                                       physical_masses_dalton, settings, criteria=None):
    """Read one ordered complete trace or prefix with bounded live frame memory.

    The caller authenticates the source, original frame bytes and mass census.
    Retained force frames do not count unseen or failed operator invocations.
    The position check uses the central position recurrence after the initial
    interval. The independent momentum update uses the adjacent retained forces.
    Selected trace criteria do not prove step convergence, a qualified initial
    ensemble, a correct potential, state commitment or a physical rate.
    """
    import numpy as np

    exact(settings, ReferenceDynamicsSettings)
    if criteria is not None:
        exact(criteria, ReferenceTrajectoryCriteria)
    initial = np.array(initial_angstrom, dtype='<f8', copy=True)
    initial_velocity = np.array(initial_velocity_nm_per_ps, dtype='<f8', copy=True)
    masses = np.array(physical_masses_dalton, dtype='<f8', copy=True)
    if (initial.ndim != 2 or initial.shape[1] != 3 or not len(initial)
            or initial_velocity.shape != initial.shape or masses.shape != (len(initial),)
            or not np.isfinite(initial).all() or not np.isfinite(initial_velocity).all()
            or not np.isfinite(masses).all() or np.any(masses <= 0)):
        raise ValueError('trajectory assessment requires complete finite original phase space and positive masses')
    dt = float(Fraction(settings.step_seconds) * 10 ** 12)
    expected_hartree = COULOMB_KJ_NM_PER_MOL_E2 / (.52917721092 / 10)
    previous, previous_position = None, None
    first_potential, first_kinetic, first_momentum = None, None, None
    count = 0
    position_error = velocity_error = energy_drift = momentum_change = 0.0
    final_position_sha = final_velocity_sha = None
    last_time = None

    for frame in frames:
        step = count
        if (type(frame) is not dict or set(frame) != _FRAME_KEYS or step > settings.steps
                or type(frame['step']) is not int or frame['step'] != step
                or type(frame['evaluation']) is not int or frame['evaluation'] != step + 1
                or type(frame['physical_time_seconds']) is not str
                or Fraction(frame['physical_time_seconds']) != step * Fraction(settings.step_seconds)):
            raise ValueError('trajectory frame changes its complete ordered force census or exact physical clock')
        xyz = np.asarray(frame['coordinates_angstrom'])
        velocity = np.asarray(frame['velocities_nm_per_ps'])
        gradient = np.asarray(frame['gradient_hartree_per_bohr'])
        if any(array.shape != initial.shape or array.dtype.kind != 'f' or array.dtype.itemsize != 8
               or not np.isfinite(array).all() for array in (xyz, velocity, gradient)):
            raise ValueError('trajectory frame omits a complete finite binary64 physical array')
        if (any(type(frame[key]) is not float for key in ('energy_hartree', 'bohr_angstrom', 'hartree_kj_mol'))
                or frame['gradient_unit'] != GRADIENT_UNIT or frame['bohr_angstrom'] != .52917721092
                or frame['hartree_kj_mol'] != expected_hartree):
            raise ValueError('trajectory frame substitutes the selected physical force units')
        potential = float(frame['energy_hartree'])
        if not math.isfinite(potential):
            raise ValueError('trajectory frame has a nonfinite potential energy')
        if step == 0 and (not np.array_equal(xyz, initial) or not np.array_equal(velocity, initial_velocity)):
            raise ValueError('trajectory frame substitutes its complete selected initial phase space')
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            position_nm = np.array(xyz / 10, dtype='<f8', copy=True)
            momentum = masses[:, None] * velocity
            force = -np.array(gradient, dtype='<f8', copy=True) * (expected_hartree / (.52917721092 / 10))
            kinetic = .5 * float(np.sum(momentum * velocity))
            total_momentum = np.sum(momentum, axis=0)
            if previous is not None:
                if previous_position is None:
                    position_residual = (position_nm - previous[0] - dt * previous[1]
                        - .5 * dt ** 2 * previous[2] / masses[:, None])
                else:
                    position_residual = (position_nm - 2 * previous[0] + previous_position
                        - dt ** 2 * previous[2] / masses[:, None])
                velocity_residual = (momentum - masses[:, None] * previous[1]
                    - .5 * dt * (previous[2] + force)) / masses[:, None]
                position_error = max(position_error, float(np.max(np.abs(position_residual))))
                velocity_error = max(velocity_error, float(np.max(np.abs(velocity_residual))))
        if not math.isfinite(kinetic) or not np.isfinite(total_momentum).all() or not np.isfinite(force).all():
            raise ValueError('trajectory assessment found a nonfinite physical energy, momentum or force')
        if first_potential is None:
            first_potential, first_kinetic, first_momentum = potential, kinetic, total_momentum
        energy_drift = max(energy_drift, abs(math.fsum(((potential - first_potential) * expected_hartree,
            kinetic, -first_kinetic))))
        momentum_change = max(momentum_change, float(np.max(np.abs(total_momentum - first_momentum))))
        previous_position = previous[0] if previous is not None else None
        previous = position_nm, np.array(velocity, dtype='<f8', copy=True), force
        final_position_sha = sha256(np.asarray(xyz, dtype='<f8').tobytes()).hexdigest()
        final_velocity_sha = sha256(np.asarray(velocity, dtype='<f8').tobytes()).hexdigest()
        last_time = frame['physical_time_seconds']
        count += 1

    complete = count == settings.steps + 1
    findings = set()
    disposition = 'UNEVALUABLE'
    if not complete:
        findings.add('selected-physical-horizon-incomplete')
    if criteria is not None and count:
        for measured, limit, reason in (
                (position_error, criteria.maximum_position_recurrence_error_nm, 'position-recurrence-exceeds-selection'),
                (velocity_error, criteria.maximum_velocity_recurrence_error_nm_ps, 'velocity-recurrence-exceeds-selection'),
                (energy_drift, criteria.maximum_energy_drift_kj_mol, 'energy-drift-exceeds-selection'),
                (momentum_change, criteria.maximum_momentum_change_dalton_nm_ps, 'momentum-change-exceeds-selection')):
            if limit is not None and Decimal.from_float(measured) > limit:
                findings.add(reason)
        if findings - {'selected-physical-horizon-incomplete'}:
            disposition = 'FALSIFIED'
        elif complete:
            disposition = 'SATISFIED'
    return dict(settings=settings.identity.to_document(),
        criteria=criteria.identity.to_document() if criteria is not None else None,
        physical_atoms=len(initial), mass_sha256=sha256(masses.tobytes()).hexdigest(),
        initial_coordinate_sha256=sha256(initial.tobytes()).hexdigest(),
        initial_velocity_sha256=sha256(initial_velocity.tobytes()).hexdigest(),
        final_coordinate_sha256=final_position_sha, final_velocity_sha256=final_velocity_sha,
        selected_steps=settings.steps, retained_force_frames=count, completed_steps=max(0, count - 1),
        selected_horizon_complete=complete, observed_physical_time_seconds=last_time,
        maximum_position_recurrence_error_nm=position_error if count > 1 else None,
        maximum_velocity_recurrence_error_nm_ps=velocity_error if count > 1 else None,
        maximum_energy_drift_kj_mol=energy_drift if count else None,
        maximum_momentum_change_dalton_nm_ps=momentum_change if count else None,
        selected_trace_criteria=disposition, findings=tuple(sorted(findings)),
        new_operator_evaluations=0, numerical_step_convergence='UNEVALUABLE',
        initial_ensemble_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')
