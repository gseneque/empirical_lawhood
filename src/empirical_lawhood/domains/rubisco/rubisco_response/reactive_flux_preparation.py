# SPDX-License-Identifier: MPL-2.0
"""Derive complete unbiased shooting phases from original equilibrium frames."""

from fractions import Fraction
from hashlib import sha256
import math

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_read import read_equilibrium_reweighting, validate_reweighting_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_science import thermal_energy
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import evaluate_reference_umbrella_bias
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import assess_reference_bias_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import physical_masses, prepare_reference_trajectory
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_records import PreparedReactiveFlux, PreparedReactiveFluxShot, ReactiveFluxPhaseSource, ReactiveFluxRule
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs, scoped_original_reference


def in_slab(surface, coordinates):
    value = Fraction(float(coordinates[surface.coordinate_axis]))-Fraction(surface.center)
    return -Fraction(surface.half_width) <= value < Fraction(surface.half_width)


def signed_coordinate(surface, coordinates):
    return float(surface.orientation*(Fraction(float(coordinates[surface.coordinate_axis]))-Fraction(surface.center)))


def momentum_draw(*, coordinates_sha256, masses, temperature, seed, pair):
    """An exact seed recipe independent of editable labels or mutation effects.

    Cartesian Maxwell velocities use the existing nm/ps, dalton and kJ/mol
    convention. Antithetic members are nested draws, not independent units.
    No center-of-mass projection, speed rescaling or selected-direction bias
    changes this explicitly unconstrained classical momentum measure.
    """
    import numpy as np
    mass_digest = sha256(masses.tobytes()).hexdigest()
    thermal_value = Fraction(temperature)
    token = sha256(canonical_json_bytes((coordinates_sha256,mass_digest,
        (thermal_value.numerator,thermal_value.denominator),seed,pair))).digest()
    derived_seed = int.from_bytes(token[:16], 'big')
    rng = np.random.Generator(np.random.PCG64DXSM(derived_seed))
    normal = rng.standard_normal(size=(len(masses), 3), dtype=np.float64)
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        velocity = normal*np.sqrt(thermal_energy(temperature)/masses)[:, None]
    if not np.isfinite(velocity).all():
        raise ValueError('selected classical momentum law cannot be represented in native phase units')
    return velocity, dict(seed=derived_seed, normal_sha256=sha256(normal.tobytes()).hexdigest(),
        mass_sha256=mass_digest, numpy_version=np.__version__)


def validate_reactive_flux_preparation(rule, sources):
    exact(rule, ReactiveFluxRule)
    capacity = validate_reweighting_inputs(rule.equilibrium, sources)
    estimated = 0
    ensembles = {e.ensemble_id:e for e in rule.equilibrium.ensembles}
    for trace,source in zip(rule.equilibrium.traces,sources,strict=True):
        n = source.config.selection.settings.expected_samples
        atoms = source.config.selection.physical_atom_count
        dimension = len(ensembles[trace.ensemble_id].coordinate_window.cv_kinds)
        surfaces = sum(s.ensemble_id==trace.ensemble_id for s in rule.surfaces)
        # Worst case: every sample belongs to a slab. Retain coordinates,
        # both momenta and every selected dynamics configuration together.
        estimated += n*(atoms*24+8192+rule.momentum_pairs_per_configuration*2*len(rule.dynamics)*(atoms*48+8192))
        estimated += n*surfaces*(16384+dimension*2048)
        if rule.density_guess_policy == 'PREVIOUS_SUCCESSFUL_RKS' and source.config.original.selection.electronic.ks_flavour != 'RKS':
            raise ValueError('flux preparation cannot select unassessed UKS density continuation')
    if estimated > rule.maximum_preparation_bytes:
        raise ValueError('complete prospective flux phase census exceeds the selected preparation allocation')
    return dict(equilibrium=capacity, worst_case_preparation_bytes=estimated,
        selected_preparation_bytes=rule.maximum_preparation_bytes)


def prepare_reactive_flux(*, rule, sources, assessor_source):
    """Prepare all selected slabs and both physical steps without native entry.

    Every selected original sample is considered. A complete source failure
    produces no successful-subset roster. A missing slab remains visible as
    an empty scientific denominator, never as a zero transition rate.
    """
    import numpy as np
    capacity = validate_reactive_flux_preparation(rule, sources)
    exact(assessor_source, ObjectIdentity)
    ensembles = {e.ensemble_id: e for e in rule.equilibrium.ensembles}
    surfaces = {e: tuple(s for s in rule.surfaces if s.ensemble_id == e) for e in ensembles}
    frames = {}

    def consume(trace, source, frame, coordinates):
        selected = tuple(s for s in surfaces[trace.ensemble_id] if in_slab(s, coordinates))
        if not selected:
            return
        key = (trace.trace_id, frame['sample_ordinal'])
        if key in frames:
            raise ValueError('flux preparation repeats one original equilibrium sample')
        positions = np.asarray(frame['coordinates_angstrom'], dtype='<f8').copy()
        positions.setflags(write=False)
        frames[key] = dict(coordinates_angstrom=positions, coordinates=tuple(coordinates),
            coordinate_sha256=sha256(positions.tobytes()).hexdigest(), step=frame['step'],
            surfaces=selected, trace=trace, source=source)

    original, arrays = read_equilibrium_reweighting(selection=rule.equilibrium, sources=sources,
        assessor_source=assessor_source, sample_consumer=consume)
    complete = original['complete_window_traces'] == len(sources)
    originals = tuple(sorted((scoped_original_reference(s).identity for s in sources
        if s.original_result is not None), key=lambda p:p.object_id))
    shots, phases, geometry = [], {}, {}
    effects = set()
    if complete:
        for (trace_id, ordinal), frame in sorted(frames.items()):
            source, trace = frame['source'], frame['trace']
            ensemble = ensembles[trace.ensemble_id]
            representation = source.representation
            prototype = source.config.original.selection
            positions = frame['coordinates_angstrom']
            atoms = tuple(a.atom_id for a in representation.atoms)
            masses = physical_masses(representation)
            arguments = dict(window=ensemble.coordinate_window, convention=ensemble.coordinate_convention,
                physical_model_id=representation.representation_id, physical_atom_ids=atoms,
                coordinates_angstrom=positions, cell_vectors_angstrom=np.diag([float(x) for x in prototype.cell.lengths_angstrom]))
            returned = evaluate_reference_umbrella_bias(**arguments)
            checked = {}
            for surface in frame['surfaces']:
                criteria = surface.geometry_criteria
                if criteria.identity not in checked:
                    checked[criteria.identity] = assess_reference_bias_geometry(**arguments, criteria=criteria, returned=returned)
                axis = surface.coordinate_axis
                rows = returned['cv_atom_indices'][axis]
                derivatives = surface.orientation*returned['cv_cartesian_derivatives'][axis]
                variance = thermal_energy(ensemble.temperature_kelvin)*float(np.sum(derivatives**2/masses[list(rows), None]))
                positive_speed = math.sqrt(variance/(2*math.pi))*1e13
                if not math.isfinite(positive_speed) or positive_speed <= 0:
                    raise ValueError('flux coordinate has no resolved positive Maxwell flux')
                geometry[(surface.surface_id, trace_id, ordinal)] = dict(
                    coordinate=frame['coordinates'][axis], signed_coordinate=signed_coordinate(surface, frame['coordinates']),
                    analytic_positive_speed_per_second=positive_speed, atom_rows=rows, derivatives=derivatives,
                    derivative_assessment=checked[criteria.identity], coordinate_unit=ensemble.coordinate_convention.center_units[axis])
            for pair in range(rule.momentum_pairs_per_configuration):
                velocity, draw = momentum_draw(coordinates_sha256=frame['coordinate_sha256'], masses=masses,
                    temperature=ensemble.temperature_kelvin, seed=rule.momentum_seed, pair=pair)
                for sign in (-1, 1):
                    actual = sign*velocity
                    seed = ReactiveFluxPhaseSource(rule.identity, scoped_original_reference(source).identity, trace_id,
                        ordinal, frame['step'], frame['coordinate_sha256'], draw['mass_sha256'], pair, sign,
                        draw['seed'], draw['normal_sha256'], sha256(actual.tobytes()).hexdigest(),
                        draw['numpy_version'], ensemble.temperature_kelvin)
                    for dynamics in rule.dynamics:
                        selection, raw = prepare_reference_trajectory(prototype=prototype, representation=representation,
                            phase_source=seed.identity, initial_angstrom=positions, initial_velocity_nm_per_ps=actual,
                            settings=dynamics, criteria=rule.trajectory_criteria, density_guess_policy=rule.density_guess_policy)
                        effect = (prototype.identity, selection.phase_bytes.object_fingerprint,
                            dynamics.step_seconds, dynamics.steps, rule.density_guess_policy)
                        if effect in effects:
                            raise ValueError('flux preparation repeats an identical physical phase and dynamics effect')
                        effects.add(effect)
                        shot_id = 'shot.reactive-flux.'+selection.fingerprint()
                        shot = PreparedReactiveFluxShot(shot_id, seed, selection,
                            tuple(s.surface_id for s in frame['surfaces']))
                        shots.append(shot)
                        phases[shot_id] = raw
    shots = tuple(sorted(shots, key=lambda s:s.shot_id))
    token = sha256(rule.canonical_bytes()+assessor_source.canonical_bytes()
        +canonical_json_bytes((originals, complete))+b''.join(s.canonical_bytes() for s in shots)).hexdigest()
    prepared = PreparedReactiveFlux('preparation.reactive-flux.'+token, rule, assessor_source, originals, complete, shots)
    recheck_original_native_outputs(sources, description='reactive-flux preparation')
    return dict(prepared=prepared, phase_bytes=phases, equilibrium_report=original, equilibrium_arrays=arrays,
        selected_frames=frames, geometry=geometry, capacity=capacity, new_native_calls=0,
        disposition='PREPARED_DIAGNOSTIC_SHOTS' if complete and shots else 'HOLD_INCOMPLETE_OR_EMPTY_SLAB_CENSUS')
