# SPDX-License-Identifier: MPL-2.0
"""Independent cumulative reading of exact original physical path segments."""

from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import math

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_read import RetainedFirstPassagePath, path_disposition
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import PassageObserver
from empirical_lawhood.domains.rubisco.rubisco_response.physical_path_protocol import complete_horizon, physical_settings, read_physical_path, read_physical_phase, stochastic_path, validate_path_model
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import independent_reference_bias_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import PHASE_SCHEMA
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs


def original_identity(source):
    """An absent return remains its selected configuration, never a result."""
    result = source.original_result
    return ObjectIdentity.from_record(result.result_id, result) if result is not None else source.config.identity


class _ContinuousMechanics:
    """Keep only adjacent frames while checking the whole NVE path recurrence."""

    def __init__(self, masses, settings):
        self.masses, self.dt = masses, float(Fraction(settings.step_seconds)*10**12)
        self.previous = self.previous_position = self.first_energy = self.first_momentum = None
        self.position = self.velocity = self.energy = self.momentum = 0.0

    def consume(self, frame):
        import numpy as np
        xyz, velocity = frame['coordinates_angstrom']/10, frame['velocities_nm_per_ps']
        momentum = self.masses[:, None]*velocity
        force = -frame['gradient_hartree_per_bohr']*(frame['hartree_kj_mol']/(frame['bohr_angstrom']/10))
        potential, kinetic = frame['energy_hartree'], .5*float(np.sum(momentum*velocity))
        total_momentum = np.sum(momentum, axis=0)
        if self.previous is not None:
            old_xyz, old_velocity, old_force = self.previous
            residual = (xyz-old_xyz-self.dt*old_velocity-.5*self.dt**2*old_force/self.masses[:, None]
                if self.previous_position is None else xyz-2*old_xyz+self.previous_position-self.dt**2*old_force/self.masses[:, None])
            velocity_residual = (momentum-self.masses[:, None]*old_velocity-.5*self.dt*(old_force+force))/self.masses[:, None]
            self.position = max(self.position, float(np.max(np.abs(residual))))
            self.velocity = max(self.velocity, float(np.max(np.abs(velocity_residual))))
        if self.first_energy is None:
            self.first_energy, self.first_momentum = (potential, kinetic), total_momentum.copy()
        self.energy = max(self.energy, abs(math.fsum(((potential-self.first_energy[0])*frame['hartree_kj_mol'], kinetic, -self.first_energy[1]))))
        self.momentum = max(self.momentum, float(np.max(np.abs(total_momentum-self.first_momentum))))
        self.previous_position = self.previous[0] if self.previous is not None else None
        self.previous = xyz.copy(), velocity.copy(), force.copy()

    def assess(self, criteria):
        metrics = dict(maximum_position_recurrence_error_nm=self.position, maximum_velocity_recurrence_error_nm_ps=self.velocity,
            maximum_energy_drift_kj_mol=self.energy, maximum_momentum_change_dalton_nm_ps=self.momentum)
        failures = tuple(name for name, value in metrics.items()
            if not math.isfinite(value) or getattr(criteria, name) is not None and Decimal.from_float(value)>getattr(criteria, name))
        return dict(metrics, findings=failures, disposition='FALSIFIED' if failures else 'SATISFIED')


def read_physical_history(*, segments, ensemble, assessor_source,
        maximum_boundary_energy_error_kj_mol, maximum_boundary_gradient_error_kj_mol_per_angstrom):
    """Read complete predecessors and the final original, including failed or absent returns.

    Duplicate boundary frames do not advance time or reset residence history.
    A completed predecessor with an absorbing event cannot have a successor.
    Every native return and cost is retained once per original identity by callers.
    """
    import numpy as np
    if (type(segments) is not tuple or not segments or any(type(s) is not RetainedFirstPassagePath for s in segments)
            or any(s.original_result is None for s in segments[:-1])):
        raise ValueError('physical history needs complete original predecessors and its final selected attempt')
    identities = tuple(original_identity(s) for s in segments)
    if len(set(identities)) != len(identities):
        raise ValueError('physical history repeats an original native segment')
    settings = physical_settings(segments[0].config)
    total = sum(physical_settings(s.config).steps for s in segments)
    combined = ReferenceDynamicsSettings('settings.physical-history.'+sha256(b''.join(p.canonical_bytes() for p in identities)).hexdigest(),
        settings.step_seconds, total)
    observer = PassageObserver(ensemble=ensemble, settings=combined)
    initial_xyz, initial_velocity, masses = read_physical_phase(segments[0].config, segments[0].representation, segments[0].phase_bytes)
    final_xyz, final_velocity = initial_xyz.copy(), initial_velocity.copy()
    final_phase, final_force, final_energy = segments[0].phase_bytes, None, None
    nve = None if stochastic_path(segments[0].config) else _ContinuousMechanics(masses, settings)
    reports, boundaries, points, steps = [], [], [], []
    offset, actual_step = 0, 0
    seeds = set()
    for index, source in enumerate(segments):
        config, current = source.config, physical_settings(source.config)
        validate_path_model(config, ensemble)
        if (config.original.selection.identity != ensemble.prototype or current.step_seconds != settings.step_seconds
                or config.selection.criteria != segments[0].config.selection.criteria
                or config.selection.density_guess_policy != segments[0].config.selection.density_guess_policy):
            raise ValueError('physical history changes its original Hamiltonian, clock or numerical criteria')
        read_physical_phase(config, source.representation, source.phase_bytes)
        if index and (source.phase_bytes != final_phase or config.selection.phase_source != identities[index-1]):
            raise ValueError('physical history resets its full endpoint phase or original predecessor')
        if stochastic_path(config):
            seed = config.selection.settings.random_seed
            if seed in seeds:
                raise ValueError('physical history repeats a previous stochastic stream')
            seeds.add(seed)
        atom_ids = tuple(a.atom_id for a in source.representation.atoms)
        cell = np.diag([float(v) for v in config.original.selection.cell.lengths_angstrom])
        final_local_step = None

        def consume(frame):
            nonlocal final_phase, final_xyz, final_velocity, final_force, final_energy, actual_step, final_local_step
            local_step = frame['step']
            clock = 'sampling_time_seconds' if stochastic_path(config) else 'physical_time_seconds'
            if Fraction(frame[clock]) != local_step*Fraction(settings.step_seconds):
                raise ValueError('physical history changes its retained local clock')
            q = independent_reference_bias_coordinates(window=ensemble.coordinate_window, convention=ensemble.coordinate_convention,
                physical_model_id=source.representation.representation_id, physical_atom_ids=atom_ids,
                coordinates_angstrom=frame['coordinates_angstrom'], cell_vectors_angstrom=cell)
            energy = frame['reference_energy_hartree' if stochastic_path(config) else 'energy_hartree']
            gradient = frame['reference_gradient_hartree_per_bohr' if stochastic_path(config) else 'gradient_hartree_per_bohr']
            if index and local_step == 0:
                boundary_energy = abs(energy-final_energy)*frame['hartree_kj_mol']
                boundary_gradient = float(np.max(np.abs(gradient-final_force)))*frame['hartree_kj_mol']/frame['bohr_angstrom']
                boundaries.append(dict(predecessor=identities[index-1].to_document(), successor=identities[index].to_document(),
                    physical_step=offset, energy_error_kj_mol=boundary_energy, gradient_error_kj_mol_per_angstrom=boundary_gradient,
                    disposition='SATISFIED' if (Decimal.from_float(boundary_energy)<=maximum_boundary_energy_error_kj_mol
                        and Decimal.from_float(boundary_gradient)<=maximum_boundary_gradient_error_kj_mol_per_angstrom) else 'FALSIFIED'))
            else:
                observer.consume(step=offset+local_step, physical_time_seconds=str(combined.time_at_step(offset+local_step)), coordinates=q)
                points.append(q)
                steps.append(offset+local_step)
                if nve is not None:
                    nve.consume(frame)
            final_xyz = np.array(frame['coordinates_angstrom'], dtype='<f8', copy=True)
            final_velocity = np.array(frame['velocities_nm_per_ps'], dtype='<f8', copy=True)
            final_force = np.array(gradient, dtype='<f8', copy=True)
            final_energy = energy
            final_phase = final_xyz.tobytes()+final_velocity.tobytes()
            actual_step, final_local_step = offset+local_step, local_step

        report = None if source.original_result is None else read_physical_path(config=config, representation=source.representation,
            phase_bytes=source.phase_bytes, original_result=source.original_result, native_subwork=source.native_subwork,
            assessor_source=assessor_source, frame_consumer=consume)
        reports.append(report)
        if index < len(segments)-1:
            assessment = None if report is None else report['assessment']
            if (assessment is None or report['native_error'] is not None or report['assessment_error'] is not None
                    or report['gpu_assessment_error'] is not None or assessment['selected_trace_criteria'] != 'SATISFIED'
                    or not complete_horizon(config, assessment) or final_local_step != current.steps
                    or observer.entry_valid is not True or observer.first_event is not None):
                raise ValueError('physical history continues after a missing, failed, invalid or absorbed predecessor')
        offset += current.steps
    disposition = path_disposition(segments[-1].config, reports[-1], observer)
    whole_mechanics = None if nve is None or segments[0].config.selection.criteria is None else nve.assess(segments[0].config.selection.criteria)
    if (any(b['disposition'] != 'SATISFIED' for b in boundaries)
            or whole_mechanics is not None and whole_mechanics['disposition'] != 'SATISFIED'):
        disposition = 'MECHANICS_FALSIFIED'
    phase = ObjectIdentity('phase.physical-history.'+sha256(final_phase).hexdigest(), PHASE_SCHEMA, '1.0.0', sha256(final_phase).hexdigest())
    recheck_original_native_outputs(segments, description='physical path history')
    arrays = dict(coordinates=np.asarray(points, dtype='<f8').reshape((-1, len(ensemble.coordinate_window.cv_kinds))),
        physical_steps=np.asarray(steps, dtype='<i8'))
    for array in arrays.values():
        array.setflags(write=False)
    return dict(history=identities, phase=phase, phase_bytes=final_phase, coordinates=final_xyz, velocities=final_velocity,
        physical_step=actual_step, selected_steps=total, original_reports=tuple(reports), boundaries=tuple(boundaries),
        whole_history_mechanics=whole_mechanics, path_disposition=disposition, passage=observer.finish(), arrays=arrays)
