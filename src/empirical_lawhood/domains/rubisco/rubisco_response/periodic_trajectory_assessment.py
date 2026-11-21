# SPDX-License-Identifier: MPL-2.0
"""Independent, bounded-memory reading of original trajectory file operands.

The caller authenticates the complete native archive. This owner reads each
complete frame once and checks the retained original phase space and clock.
It never constructs a force operator or reacquires a missing trajectory frame.
"""

from hashlib import sha256
from fractions import Fraction
import io
import json
import re

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics_assessment import assess_reference_trajectory_frames
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import read_phase_space, validate_trajectory_prototype


FRAME_ARRAYS = {'coordinates-angstrom.npy': 'coordinates_angstrom',
    'velocities-nm-per-ps.npy': 'velocities_nm_per_ps',
    'gradient_hartree_per_bohr.npy': 'gradient_hartree_per_bohr'}
FRAME_SUFFIXES = frozenset((*FRAME_ARRAYS, 'energy_hartree.npy', 'native-return.json', 'complete-frame.json'))
FIXED_MEMBERS = frozenset(('initial-phase-space.bin', 'trajectory-selection.json', 'prototype.json',
    'physical-masses-dalton.npy', 'source-bindings.json', 'trajectory-summary.json'))
_EVALUATION = re.compile(r'evaluation\.([0-9]+)\.(.+)\Z')


def selected_trajectory_member(name):
    match = _EVALUATION.fullmatch(name)
    return name in FIXED_MEMBERS or match is not None and match[2] in FRAME_SUFFIXES


def _json(raw):
    def unique(rows):
        value = {}
        for key, item in rows:
            if key in value:
                raise ValueError('trajectory metadata repeats a key')
            value[key] = item
        return value
    if type(raw) is not bytes or len(raw) > 2**20:
        raise ValueError('trajectory metadata exceeds its bounded original representation')
    return json.loads(raw, object_pairs_hook=unique)


def _array(raw, shape, *, finite=True):
    import numpy as np
    count = 1
    for value in shape:
        count *= value
    if type(raw) is not bytes or not count * 8 < len(raw) <= count * 8 + 1024:
        raise ValueError('trajectory array changes its complete bounded binary64 extent')
    stream = io.BytesIO(raw)
    version = np.lib.format.read_magic(stream)
    if version not in {(1, 0), (2, 0)}:
        raise ValueError('trajectory array changes its original numeric format')
    header = (np.lib.format.read_array_header_1_0 if version == (1, 0)
        else np.lib.format.read_array_header_2_0)(stream, max_header_size=1024)
    actual_shape, fortran, dtype = header
    if actual_shape != shape or fortran or dtype.str != '<f8' or len(raw) - stream.tell() != count * 8:
        raise ValueError('trajectory array changes its original shape, dtype, order or trailing bytes')
    array = np.frombuffer(raw, dtype='<f8', count=count, offset=stream.tell()).reshape(shape)
    if finite and not np.isfinite(array).all():
        raise ValueError('complete trajectory frame contains nonfinite physical values')
    return array


def assess_recorded_trajectory(*, selection, prototype, representation, phase_bytes, files, native_succeeded,
                              frame_consumer=None):
    """Consume ordered file names and selected payloads from complete custody.

    Unselected members have ``None`` payloads but stay in the authenticated
    stream. Files from a failed final force remain a partial last group; their
    absence cannot be interpreted as no native invocation. The owner must drain
    and authenticate the file iterator even when this assessment raises.
    """
    import numpy as np
    validate_trajectory_prototype(selection, prototype)
    xyz, velocity, masses = read_phase_space(selection, representation, phase_bytes)
    if type(native_succeeded) is not bool:
        raise ValueError('trajectory read requires the actual original native completion status')
    if frame_consumer is not None and not callable(frame_consumer):
        raise TypeError('trajectory projection requires a bounded callable consumer')
    shape = xyz.shape
    metadata = {}
    seen = set()
    counts = dict(recorded_evaluation_inputs=0, recorded_return_metadata=0, complete_frame_markers=0)
    last_group = 0
    partial = False

    def frame_for(number, group):
        nonlocal partial, last_group
        if number != last_group + 1 or partial:
            raise ValueError('trajectory archive omits an attempted force or continues after an incomplete frame')
        last_group = number
        if 'coordinates-angstrom.npy' in group:
            counts['recorded_evaluation_inputs'] += 1
        if 'native-return.json' in group:
            counts['recorded_return_metadata'] += 1
        if 'complete-frame.json' not in group:
            partial = True
            return None
        if set(group) != FRAME_SUFFIXES:
            raise ValueError('complete trajectory frame omits original force, coordinate or velocity operands')
        row = _json(group['complete-frame.json'])
        expected = {'step', 'physical_time_seconds', 'evaluation', 'energy_hartree', 'gradient_unit',
            'bohr_angstrom', 'hartree_kj_mol', 'coordinate_sha256', 'gradient_sha256', 'velocity_sha256'}
        if type(row) is not dict or set(row) != expected or row['evaluation'] != number:
            raise ValueError('trajectory frame changes its exact original metadata census')
        arrays = {field:_array(group[name], shape) for name, field in FRAME_ARRAYS.items()}
        for field, key in (('coordinates_angstrom', 'coordinate_sha256'),
                ('velocities_nm_per_ps', 'velocity_sha256'), ('gradient_hartree_per_bohr', 'gradient_sha256')):
            if sha256(arrays[field].tobytes()).hexdigest() != row.pop(key):
                raise ValueError('trajectory frame metadata substitutes an original returned array')
        original = _json(group['native-return.json'])
        energy = float(_array(group['energy_hartree.npy'], ()))
        if (row['energy_hartree'] != energy or type(original) is not dict
                or any(original.get(key) != row[key]
                    for key in ('energy_hartree', 'gradient_unit', 'bohr_angstrom', 'hartree_kj_mol'))):
            raise ValueError('trajectory frame substitutes original returned energy or units')
        counts['complete_frame_markers'] += 1
        return dict(row, **arrays)

    def checked_frame(frame):
        # The mechanics reducer consumes and checks this frame before a derived
        # observer sees it. Its continuation owns copies of the physical state.
        # A consumer must discard projections if the complete archive read fails.
        yield frame
        if frame_consumer is not None:
            frame_consumer(frame)

    def frames():
        group, number, previous = {}, None, None
        for name, raw in files:
            if type(name) is not str or previous is not None and name <= previous:
                raise ValueError('trajectory archive changes its complete ordered file census')
            previous = name
            seen.add(name)
            match = _EVALUATION.fullmatch(name)
            if match is not None:
                current = int(match[1])
                if match[1] != f'{current:016d}' or current <= 0:
                    raise ValueError('trajectory archive changes its original evaluation numbering')
                if number is not None and current != number:
                    frame = frame_for(number, group)
                    if frame is not None:
                        yield from checked_frame(frame)
                    group = {}
                number = current
                if match[2] in FRAME_SUFFIXES:
                    if type(raw) is not bytes:
                        raise ValueError('trajectory archive omits a selected original frame payload')
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

    assessed = assess_reference_trajectory_frames(frames(), initial_angstrom=xyz,
        initial_velocity_nm_per_ps=velocity, physical_masses_dalton=masses,
        settings=selection.settings, criteria=selection.criteria)
    required = FIXED_MEMBERS - {'trajectory-summary.json'}
    if not required.issubset(metadata) or not {'original.prmtop', 'original.inpcrd'}.issubset(seen):
        raise ValueError('trajectory archive lacks its complete original input bindings')
    if (metadata['initial-phase-space.bin'] != phase_bytes
            or metadata['trajectory-selection.json'] != selection.canonical_bytes()
            or metadata['prototype.json'] != prototype.canonical_bytes()
            or not np.array_equal(_array(metadata['physical-masses-dalton.npy'], masses.shape), masses)):
        raise ValueError('trajectory archive changes original selected phase space, operator or physical masses')
    bindings = _json(metadata['source-bindings.json'])
    expected = dict(selection=selection.identity.to_document(), prototype=prototype.identity.to_document(),
        representation=representation.identity.to_document(), phase_source=selection.phase_source.to_document(),
        phase_arrays=selection.arrays.identity.to_document(), raw_phase_space=selection.phase_bytes.to_document(),
        mass_sha256=selection.mass_sha256, density_guess_policy=selection.density_guess_policy,
        initial_ensemble_admission='UNEVALUABLE')
    if bindings != expected:
        raise ValueError('trajectory archive substitutes its original source binding')
    summary = metadata.get('trajectory-summary.json')
    if summary is not None:
        summary = _json(summary)
        expected_summary = dict(settings=selection.settings.identity.to_document(),
            algorithm='VELOCITY_VERLET', physical_clock_id='clock.rubisco.physical-seconds',
            completed_steps=selection.settings.steps,
            physical_atoms=selection.physical_atom_count, mass_sha256=selection.mass_sha256,
            operator_invocations=selection.settings.steps + 1, operator_returns=selection.settings.steps + 1,
            completed_evaluations=selection.settings.steps + 1, captured_frames=selection.settings.steps + 1,
            thermostat='NONE', constraints='NONE', bias='NONE', mass_repartitioning=False,
            velocity_rescaling=False, coordinate_wrapping=False, numerical_accuracy='UNEVALUABLE',
            initial_ensemble_admission='UNEVALUABLE', rate_admission='UNEVALUABLE')
        if (not assessed['selected_horizon_complete'] or partial
                or type(summary) is not dict or any(type(summary.get(k)) is not type(v) or summary[k] != v
                    for k, v in expected_summary.items())):
            raise ValueError('trajectory summary changes its actual complete force census, clock or scientific scope')
        for key, value in (('step_seconds', selection.settings.step_seconds),
                ('physical_time_seconds', selection.settings.time_at_step(selection.settings.steps))):
            if type(summary.get(key)) is not str or Fraction(summary[key]) != Fraction(value):
                raise ValueError('trajectory summary substitutes its exact physical time')
    if native_succeeded and (summary is None or not assessed['selected_horizon_complete'] or partial):
        raise ValueError('successful original trajectory omits its complete selected physical horizon')
    return dict(assessed, **counts, partial_last_evaluation=partial,
        native_succeeded=native_succeeded, summary_retained=summary is not None,
        selection=selection.identity.to_document(), initial_phase_source=selection.phase_source.to_document())
