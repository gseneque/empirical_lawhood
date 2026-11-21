# SPDX-License-Identifier: MPL-2.0
"""Bounded original sampling reduction with separate force, bias and noise counts.

The outer reader authenticates every archived byte even after assessment fails.
This reducer verifies original operand correspondence and stochastic mechanics;
it does not call the bias evaluator, reference operator or random generator.
"""

from fractions import Fraction
from hashlib import sha256
import math
import re

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_assessment import assess_reference_equilibrium_frames
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import assess_reference_bias_geometry, validate_bias_geometry_criteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import read_equilibrium_phase_space, validate_equilibrium_prototype
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_assessment import _array, _json


FRAME_ARRAYS = {'coordinates-angstrom.npy': 'coordinates_angstrom',
    'velocities-nm-per-ps.npy': 'velocities_nm_per_ps',
    'gradient_hartree_per_bohr.npy': 'reference_gradient_hartree_per_bohr',
    'bias-gradient-kj-mol-per-angstrom.npy': 'bias_gradient_kj_mol_per_angstrom'}
FRAME_SUFFIXES = frozenset((*FRAME_ARRAYS, 'energy_hartree.npy', 'native-return.json', 'complete-frame.json'))
NOISE_SUFFIXES = frozenset(('noise-standard-normal.npy', 'noise-state.json'))
BIAS_SUFFIXES = frozenset(('bias-coordinates-angstrom.npy', 'bias-return.json'))
FIXED_MEMBERS = frozenset(('initial-phase-space.bin', 'equilibrium-selection.json', 'prototype.json',
    'physical-masses-dalton.npy', 'source-bindings.json', 'equilibrium-summary.json'))
_EVALUATION = re.compile(r'evaluation\.([0-9]+)\.(.+)\Z')
_DERIVATIVE = re.compile(r'bias-cv-derivative\.[0-9]{8}\.npy\Z')


def selected_equilibrium_member(name):
    match = _EVALUATION.fullmatch(name)
    return name in FIXED_MEMBERS or match is not None and (match[2] in FRAME_SUFFIXES | NOISE_SUFFIXES | BIAS_SUFFIXES
        or _DERIVATIVE.fullmatch(match[2]) is not None)


def _generator_state(value):
    if (type(value) is not dict or set(value) != {'bit_generator', 'state', 'has_uint32', 'uinteger'}
            or value['bit_generator'] != 'PCG64DXSM' or type(value['state']) is not dict
            or set(value['state']) != {'state', 'inc'}
            or any(type(value['state'][key]) is not int or not 0 <= value['state'][key] < 2**128
                for key in ('state', 'inc')) or value['state']['inc'] % 2 != 1
            or type(value['has_uint32']) is not int or value['has_uint32'] not in (0, 1)
            or type(value['uinteger']) is not int or not 0 <= value['uinteger'] < 2**32):
        raise ValueError('equilibrium noise substitutes its complete recorded generator state')


def assess_recorded_equilibrium(*, selection, prototype, representation, phase_bytes, files, native_succeeded,
                               bias_geometry_criteria=None, sample_consumer=None, frame_consumer=None, verify_random_stream=False):
    """Read original selected arrays once, preserving a failed final prefix."""
    import numpy as np
    validate_equilibrium_prototype(selection, prototype)
    xyz, velocity, masses = read_equilibrium_phase_space(selection, representation, phase_bytes)
    if type(native_succeeded) is not bool:
        raise ValueError('equilibrium read requires the actual original native completion status')
    if sample_consumer is not None and not callable(sample_consumer):
        raise TypeError('equilibrium sample projection requires a bounded callable consumer')
    if frame_consumer is not None and not callable(frame_consumer):
        raise TypeError('equilibrium frame projection requires a bounded callable consumer')
    if type(verify_random_stream) is not bool:
        raise TypeError('original random-stream verification must be explicitly selected')
    replay = np.random.Generator(np.random.PCG64DXSM(selection.settings.random_seed)) if verify_random_stream else None
    shape = xyz.shape
    if bias_geometry_criteria is not None:
        if selection.window is None:
            raise ValueError('bias geometry criteria cannot invent a bias in an unbiased selection')
        validate_bias_geometry_criteria(bias_geometry_criteria, selection.window, selection.convention)
    bias_geometry = dict(criteria=bias_geometry_criteria.identity.to_document() if bias_geometry_criteria else None,
        assessed_frames=0, satisfied_frames=0, falsified_frames=0, unevaluable_frames=0,
        first_falsified_evaluation=None, first_unevaluable_evaluation=None,
        maximum_energy_error_kj_mol=None, maximum_gradient_error_kj_mol_per_angstrom=None,
        maximum_gradient_refinement_error_kj_mol_per_angstrom=None,
        maximum_spectator_gradient_error_kj_mol_per_angstrom=None,
        terms=[dict(cv_index=i, maximum_value_error=None, maximum_displacement_error=None,
            maximum_energy_error_kj_mol=None, maximum_derivative_error_per_angstrom=None,
            maximum_derivative_refinement_error_per_angstrom=None, unresolved_frames=0,
            first_unresolved_evaluation=None, first_unresolved_reason=None)
            for i in range(len(selection.window.cv_kinds))] if selection.window is not None else [])

    def collect_bias_geometry(result, number):
        status = result['selected_bias_geometry_criteria']
        bias_geometry['assessed_frames'] += 1
        bias_geometry[{'SATISFIED':'satisfied_frames', 'FALSIFIED':'falsified_frames', 'UNEVALUABLE':'unevaluable_frames'}[status]] += 1
        for kind in ('falsified', 'unevaluable'):
            if status == kind.upper() and bias_geometry['first_'+kind+'_evaluation'] is None:
                bias_geometry['first_'+kind+'_evaluation'] = number
        def maxima(target, row):
            for key, value in row.items():
                name = 'maximum_'+key
                if name in target and value is not None:
                    target[name] = value if target[name] is None else max(target[name], value)
        maxima(bias_geometry, result)
        for target, term in zip(bias_geometry['terms'], result['terms'], strict=True):
            maxima(target, term)
            if term['unresolved_geometry'] is not None:
                target['unresolved_frames'] += 1
                if target['first_unresolved_evaluation'] is None:
                    target['first_unresolved_evaluation'] = number
                    target['first_unresolved_reason'] = term['unresolved_geometry']
    metadata, seen = {}, set()
    counts = dict(recorded_evaluation_inputs=0, recorded_return_metadata=0,
        recorded_bias_inputs=0, recorded_bias_returns=0, recorded_noise_arrays=0,
        recorded_noise_states=0, complete_frame_markers=0)
    last_group, partial, previous_state, numpy_version = 0, False, None, None
    atom_indices = {atom.atom_id: i for i, atom in enumerate(representation.atoms)}

    def frame_for(number, group):
        nonlocal partial, last_group, previous_state, numpy_version
        if number != last_group+1 or partial:
            raise ValueError('equilibrium archive omits an attempted step or continues after a partial frame')
        last_group = number
        for name, key in (('coordinates-angstrom.npy', 'recorded_evaluation_inputs'),
                ('native-return.json', 'recorded_return_metadata'),
                ('bias-coordinates-angstrom.npy', 'recorded_bias_inputs'), ('bias-return.json', 'recorded_bias_returns'),
                ('noise-standard-normal.npy', 'recorded_noise_arrays'), ('noise-state.json', 'recorded_noise_states')):
            counts[key] += name in group
        if 'complete-frame.json' not in group:
            partial = True
            return None
        expected = set(FRAME_SUFFIXES)
        if number > 1:
            expected.update(NOISE_SUFFIXES)
        if selection.window is not None:
            expected.update(BIAS_SUFFIXES)
            expected.update(f'bias-cv-derivative.{i:08d}.npy' for i in range(len(selection.window.cv_kinds)))
        if set(group) != expected:
            raise ValueError('complete equilibrium frame omits or invents original reference, bias or noise operands')
        row = _json(group['complete-frame.json'])
        fields = {'settings', 'step', 'sampling_time_seconds', 'evaluation', 'sample_ordinal',
            'reference_energy_hartree', 'bias_energy_kj_mol', 'bias_window', 'bias_convention', 'noise_draw',
            'thermostat_heat_kj_mol', 'gradient_unit', 'bohr_angstrom', 'hartree_kj_mol',
            'coordinate_sha256', 'reference_gradient_sha256', 'bias_gradient_sha256', 'noise_sha256', 'velocity_sha256'}
        if type(row) is not dict or set(row) != fields or row['evaluation'] != number:
            raise ValueError('equilibrium frame changes its complete original metadata census')
        arrays = {field: _array(group[name], shape) for name, field in FRAME_ARRAYS.items()}
        for field, key in (('coordinates_angstrom', 'coordinate_sha256'),
                ('velocities_nm_per_ps', 'velocity_sha256'),
                ('reference_gradient_hartree_per_bohr', 'reference_gradient_sha256'),
                ('bias_gradient_kj_mol_per_angstrom', 'bias_gradient_sha256')):
            if sha256(arrays[field].tobytes()).hexdigest() != row.pop(key):
                raise ValueError('equilibrium frame substitutes an original returned array')
        original = _json(group['native-return.json'])
        energy = float(_array(group['energy_hartree.npy'], ()))
        if (type(original) is not dict or row['reference_energy_hartree'] != energy
                or original.get('energy_hartree') != energy or any(original.get(key) != row[key]
                    for key in ('gradient_unit', 'bohr_angstrom', 'hartree_kj_mol'))):
            raise ValueError('equilibrium frame changes original reference energy or units')
        noise_sha = row.pop('noise_sha256')
        noise = None
        if number > 1:
            noise = _array(group['noise-standard-normal.npy'], shape)
            state = _json(group['noise-state.json'])
            if (type(state) is not dict or set(state) != {'step', 'numpy_version', 'generator', 'state_before', 'state_after', 'noise_sha256'}
                    or type(state['step']) is not int or state['step'] != number-1
                    or state['generator'] != selection.settings.random_generator
                    or type(state['numpy_version']) is not str or not state['numpy_version']
                    or state['noise_sha256'] != noise_sha or sha256(noise.tobytes()).hexdigest() != noise_sha):
                raise ValueError('equilibrium frame substitutes its original noise draw or generator identity')
            for key in ('state_before', 'state_after'):
                _generator_state(state[key])
            if replay is not None:
                if replay.bit_generator.state != state['state_before']:
                    raise ValueError('equilibrium noise changes its exact selected seed or draw sequence')
                checked_noise=replay.standard_normal(size=shape,dtype=np.float64)
                if not np.array_equal(checked_noise,noise) or replay.bit_generator.state != state['state_after']:
                    raise ValueError('equilibrium noise differs from the exact original generator draw')
            if previous_state is not None and (previous_state != state['state_before'] or numpy_version != state['numpy_version']):
                raise ValueError('equilibrium noise loses its original continuous generator-state chain')
            previous_state, numpy_version = state['state_after'], state['numpy_version']
        elif noise_sha is not None:
            raise ValueError('equilibrium frame invents an initial thermal draw')
        if selection.window is not None:
            window, convention = selection.window, selection.convention
            supplied = _array(group['bias-coordinates-angstrom.npy'], shape)
            bias = _json(group['bias-return.json'])
            indices = [[atom_indices[atom] for atom in atoms] for atoms in window.cv_atom_ids]
            expected_bias = dict(window=selection.settings.bias_window.to_document(), convention=convention.identity.to_document(),
                physical_model_id=representation.representation_id, physical_atoms=len(xyz),
                cv_units=list(convention.center_units), cv_atom_indices=indices,
                gradient_kind='ENERGY_DERIVATIVE_NOT_FORCE', reference_energy_included=False,
                equilibrium_admission='UNEVALUABLE', rate_admission='UNEVALUABLE')
            if (not np.array_equal(supplied, arrays['coordinates_angstrom']) or type(bias) is not dict
                    or set(bias) != set(expected_bias) | {'cv_values', 'cv_displacements', 'term_energies_kj_mol', 'energy_kj_mol'}
                    or any(type(bias.get(k)) is not type(v) or bias[k] != v for k, v in expected_bias.items())
                    or type(bias['energy_kj_mol']) is not float or bias['energy_kj_mol'] != row['bias_energy_kj_mol']):
                raise ValueError('equilibrium frame changes its original bias identities, coordinates or units')
            ncv = len(window.cv_kinds)
            for key in ('cv_values', 'cv_displacements', 'term_energies_kj_mol'):
                if (type(bias[key]) is not list or len(bias[key]) != ncv
                        or any(type(v) is not float or not math.isfinite(v) for v in bias[key])):
                    raise ValueError('equilibrium frame changes its complete finite bias term census')
            gradient = np.zeros(shape, dtype='<f8')
            term_energies = []
            local_derivatives = []
            for i, atom_rows in enumerate(indices):
                derivative = _array(group[f'bias-cv-derivative.{i:08d}.npy'], (len(atom_rows), 3))
                local_derivatives.append(derivative)
                displacement = bias['cv_values'][i]-float(window.centers[i])
                if window.cv_kinds[i] == 'IMPROPER_DIHEDRAL':
                    displacement = math.atan2(math.sin(displacement), math.cos(displacement))
                constant = float(window.force_constants[i])
                term_energies.append(.5*constant*displacement*displacement)
                gradient[atom_rows] += constant*displacement*derivative
                if displacement != bias['cv_displacements'][i]:
                    raise ValueError('equilibrium frame substitutes selected bias centers or angular convention')
            if (term_energies != bias['term_energies_kj_mol'] or math.fsum(term_energies) != bias['energy_kj_mol']
                    or not np.array_equal(gradient, arrays['bias_gradient_kj_mol_per_angstrom'])):
                raise ValueError('equilibrium frame substitutes the original bias term/gradient decomposition')
            if bias_geometry_criteria is not None:
                result = assess_reference_bias_geometry(window=window, convention=convention,
                    criteria=bias_geometry_criteria, physical_model_id=representation.representation_id,
                    physical_atom_ids=tuple(atom.atom_id for atom in representation.atoms),
                    coordinates_angstrom=arrays['coordinates_angstrom'],
                    cell_vectors_angstrom=np.diag([float(v) for v in prototype.cell.lengths_angstrom]),
                    returned=dict(bias, cv_cartesian_derivatives=tuple(local_derivatives),
                        gradient_kj_mol_per_angstrom=arrays['bias_gradient_kj_mol_per_angstrom']))
                collect_bias_geometry(result, number)
        counts['complete_frame_markers'] += 1
        return dict(row, **arrays, noise_standard_normal=noise)

    def checked_frame(frame):
        # Resume only after the independent mechanics reducer has checked this
        # frame. The outer read still authenticates the complete original archive.
        # A consumer must discard its projection if that complete read fails.
        yield frame
        if frame_consumer is not None:
            frame_consumer(frame)
        if sample_consumer is not None and frame['sample_ordinal'] is not None:
            sample_consumer(frame)

    def frames():
        group, number, previous = {}, None, None
        for name, raw in files:
            if type(name) is not str or previous is not None and name <= previous:
                raise ValueError('equilibrium archive changes its ordered complete file census')
            previous = name
            seen.add(name)
            match = _EVALUATION.fullmatch(name)
            if match is not None:
                current = int(match[1])
                if match[1] != f'{current:016d}' or current <= 0:
                    raise ValueError('equilibrium archive changes its original evaluation numbering')
                if number is not None and current != number:
                    frame = frame_for(number, group)
                    if frame is not None:
                        yield from checked_frame(frame)
                    group = {}
                number = current
                if selected_equilibrium_member(name):
                    if type(raw) is not bytes:
                        raise ValueError('equilibrium archive omits a selected original operand')
                    group[match[2]] = raw
            else:
                if number is not None:
                    frame = frame_for(number, group)
                    if frame is not None:
                        yield from checked_frame(frame)
                    number, group = None, {}
                if name in FIXED_MEMBERS:
                    metadata[name] = raw
        if number is not None:
            frame = frame_for(number, group)
            if frame is not None:
                yield from checked_frame(frame)

    assessed = assess_reference_equilibrium_frames(frames(), initial_angstrom=xyz,
        initial_velocity_nm_per_ps=velocity, physical_masses_dalton=masses,
        settings=selection.settings, criteria=selection.criteria)
    if (not (FIXED_MEMBERS-{'equilibrium-summary.json'}).issubset(metadata)
            or not {'original.prmtop', 'original.inpcrd'}.issubset(seen)):
        raise ValueError('equilibrium archive lacks complete original input bindings')
    if (metadata['initial-phase-space.bin'] != phase_bytes
            or metadata['equilibrium-selection.json'] != selection.canonical_bytes()
            or metadata['prototype.json'] != prototype.canonical_bytes()
            or not np.array_equal(_array(metadata['physical-masses-dalton.npy'], masses.shape), masses)):
        raise ValueError('equilibrium archive changes original phase space, operator or physical masses')
    bindings = _json(metadata['source-bindings.json'])
    expected = dict(selection=selection.identity.to_document(), prototype=prototype.identity.to_document(),
        representation=representation.identity.to_document(), phase_source=selection.phase_source.to_document(),
        phase_arrays=selection.arrays.identity.to_document(), raw_phase_space=selection.phase_bytes.to_document(),
        mass_sha256=selection.mass_sha256, density_guess_policy=selection.density_guess_policy,
        initial_ensemble_admission='UNEVALUABLE')
    if bindings != expected:
        raise ValueError('equilibrium archive substitutes its original source binding')
    summary = metadata.get('equilibrium-summary.json')
    if summary is not None:
        summary = _json(summary)
        settings = selection.settings
        steps = settings.dynamics.steps
        expected_summary = dict(settings=settings.identity.to_document(), algorithm='BAOAB',
            completed_steps=steps, physical_atoms=selection.physical_atom_count, mass_sha256=selection.mass_sha256,
            operator_invocations=steps+1, operator_returns=steps+1, completed_evaluations=steps+1, captured_frames=steps+1,
            noise_draws=steps, retained_noise_draws=steps, captured_sample_frames=settings.expected_samples,
            selected_sample_frames=settings.expected_samples, numpy_version=numpy_version,
            random_generator=settings.random_generator, random_seed=settings.random_seed,
            thermostat='LANGEVIN_EXACT_OU_SPLITTING',
            bias_window=settings.bias_window.to_document() if settings.bias_window else None,
            bias_convention=settings.bias_convention.to_document() if settings.bias_convention else None,
            constraints='NONE', mass_repartitioning=False, velocity_rescaling=False, coordinate_wrapping=False,
            physical_rate_clock='NOT_SUPPLIED_BY_EQUILIBRIUM_SAMPLER', equilibrium_admission='UNEVALUABLE',
            step_convergence='UNEVALUABLE', physical_rate_admission='UNEVALUABLE',
            original_bias_invocations=steps+1 if selection.window is not None else 0)
        if (not assessed['selected_sampling_horizon_complete'] or partial or type(summary) is not dict
                or any(type(summary.get(k)) is not type(v) or summary[k] != v for k, v in expected_summary.items())):
            raise ValueError('equilibrium summary changes its original census, thermostat or scientific scope')
        for key, value in (('step_seconds', settings.dynamics.step_seconds),
                ('sampling_time_seconds', settings.dynamics.time_at_step(steps)),
                ('temperature_kelvin', settings.temperature_kelvin), ('friction_per_picosecond', settings.friction_per_picosecond)):
            if type(summary.get(key)) is not str or Fraction(summary[key]) != Fraction(value):
                raise ValueError('equilibrium summary changes exact sampling time or bath selections')
        if (type(summary.get('thermostat_heat_kj_mol')) is not float
                or summary['thermostat_heat_kj_mol'] != assessed['thermostat_heat_kj_mol']):
            raise ValueError('equilibrium summary substitutes original cumulative thermostat heat')
    if native_succeeded and (summary is None or not assessed['selected_sampling_horizon_complete'] or partial):
        raise ValueError('successful equilibrium return omits its complete selected sampling horizon')
    bias_geometry['selected_bias_geometry_criteria'] = (
        'FALSIFIED' if bias_geometry['falsified_frames'] else
        'SATISFIED' if bias_geometry_criteria is not None and assessed['selected_sampling_horizon_complete']
        and not partial and bias_geometry['satisfied_frames'] == selection.settings.dynamics.steps+1 else 'UNEVALUABLE')
    bias_geometry.update(expected_frames=selection.settings.dynamics.steps+1 if selection.window else 0,
        selected_sampling_horizon_complete=assessed['selected_sampling_horizon_complete'],
        equilibrium_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')
    return dict(assessed, **counts, partial_last_evaluation=partial, native_succeeded=native_succeeded,
        summary_retained=summary is not None, selection=selection.identity.to_document(),
        initial_phase_source=selection.phase_source.to_document(),
        random_state_chain=('COMPLETE_FRAME_DRAWS_REPRODUCED_FROM_SELECTED_SEED' if replay is not None
            else 'RETAINED_CONTINUITY_CHECKED_NOT_STREAM_REGENERATED'),
        bias_operand_correspondence='ORIGINAL_ARRAYS_AND_SELECTED_DECOMPOSITION_CHECKED',
        bias_geometry_accuracy='INDEPENDENT_COORDINATE_AND_TWO_STEP_DERIVATIVE_ASSESSMENT'
            if bias_geometry_criteria is not None else 'NOT_INDEPENDENTLY_ASSESSED_BY_THIS_READER',
        bias_geometry_assessment=bias_geometry)
