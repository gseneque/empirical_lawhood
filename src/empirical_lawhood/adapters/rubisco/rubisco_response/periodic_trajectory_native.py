# SPDX-License-Identifier: MPL-2.0
"""Original full-reference trajectory files inside the shared native boundary.

The registered operation owns authorization, source authentication and receipts.
Each attempted force has original input coordinates. Returned numerical arrays
are written before the integrator checks them; a complete-frame marker is last.
"""

from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import propagate_reference_trajectory
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import ARRAY_KEYS
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import read_phase_space, validate_trajectory_prototype


def _json(path, value, *, diagnostic=False):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=diagnostic, separators=(',', ':'))
        stream.write('\n')


def _array(path, value):
    import numpy as np
    with path.open('xb') as stream:
        np.save(stream, np.asarray(value), allow_pickle=False)


def record_reference_trajectory(*, operator, directory, initial_angstrom, initial_velocity_nm_per_ps,
                                physical_masses_dalton, settings):
    """Retain every returned force and every complete phase-space frame.

    Files are flat so the existing complete-directory native archive retains
    them without a new packaging or recovery mechanism. There is no retry.
    A capture failure leaves its original partial files and does not advance.
    """
    import numpy as np
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError('trajectory recording requires its selected existing native directory')
    calls = 0
    captured = 0
    latest = None
    with (root/'trajectory-evaluations.jsonl').open('x', buffering=1) as events:
        def observe(row):
            events.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')

        class RecordingOperator:
            def evaluate(self, coordinates):
                nonlocal calls, latest
                calls += 1
                prefix = f'evaluation.{calls:016d}.'
                raw_xyz = np.array(coordinates, dtype='<f8', copy=True)
                _array(root/(prefix+'coordinates-angstrom.npy'), raw_xyz)
                latest = None
                returned = operator.evaluate(coordinates)
                # Original return capture precedes all trajectory validation.
                for key in ('energy_hartree', *ARRAY_KEYS):
                    if key in returned:
                        _array(root/(prefix+key+'.npy'), returned[key])
                _json(root/(prefix+'native-return.json'),
                    {k:v for k, v in returned.items() if k not in ARRAY_KEYS}, diagnostic=True)
                latest = dict(evaluation=calls, prefix=prefix, coordinate_sha256=sha256(raw_xyz.tobytes()).hexdigest(),
                    gradient_sha256=sha256(np.asarray(returned['gradient_hartree_per_bohr'], dtype='<f8').tobytes()).hexdigest(),
                    energy_hartree=float(returned['energy_hartree']))
                return returned

        def capture(frame):
            nonlocal captured
            if (latest is None or frame['evaluation'] != calls or calls != captured + 1
                    or frame['step'] != captured or frame['energy_hartree'] != latest['energy_hartree']
                    or sha256(frame['coordinates_angstrom'].tobytes()).hexdigest() != latest['coordinate_sha256']
                    or sha256(frame['gradient_hartree_per_bohr'].tobytes()).hexdigest() != latest['gradient_sha256']):
                raise ValueError('trajectory frame differs from its original returned force or coordinate bytes')
            prefix = latest['prefix']
            _array(root/(prefix+'velocities-nm-per-ps.npy'), frame['velocities_nm_per_ps'])
            metadata = {k:v for k, v in frame.items() if k not in
                ('coordinates_angstrom', 'velocities_nm_per_ps', 'gradient_hartree_per_bohr')}
            metadata.update(coordinate_sha256=latest['coordinate_sha256'], gradient_sha256=latest['gradient_sha256'],
                velocity_sha256=sha256(frame['velocities_nm_per_ps'].tobytes()).hexdigest())
            pending = root/(prefix+'frame-pending.json')
            _json(pending, metadata)
            pending.rename(root/(prefix+'complete-frame.json'))
            captured += 1

        _, _, summary = propagate_reference_trajectory(operator=RecordingOperator(), initial_angstrom=initial_angstrom,
            initial_velocity_nm_per_ps=initial_velocity_nm_per_ps, physical_masses_dalton=physical_masses_dalton,
            settings=settings, observe=observe, capture=capture)
        if summary['completed_evaluations'] != calls or summary['captured_frames'] != captured:
            raise ValueError('trajectory recording loses an actual force call or complete frame')
        _json(root/'trajectory-summary.json', summary)
        return summary


def execute_reference_trajectory(*, selection, prototype, representation, sources, phase_bytes, directory):
    """Construct one fixed complete coupled operator and retain a physical trace."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
    validate_trajectory_prototype(selection, prototype)
    # This reuses the original complete Amber source/cell/atom authentication.
    original_coordinates(prototype, representation, sources)
    xyz, velocity, masses = read_phase_space(selection, representation, phase_bytes)
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise ValueError('reference trajectory requires its existing fresh absolute native directory')
    for name, raw in (('original.prmtop', sources.topology_utf8.encode('ascii')),
            ('original.inpcrd', sources.coordinates_utf8.encode('ascii')),
            ('initial-phase-space.bin', phase_bytes), ('trajectory-selection.json', selection.canonical_bytes()),
            ('prototype.json', prototype.canonical_bytes())):
        with (root/name).open('xb') as stream:
            stream.write(raw)
    _array(root/'physical-masses-dalton.npy', masses)
    _json(root/'source-bindings.json', dict(selection=selection.identity.to_document(),
        prototype=prototype.identity.to_document(), representation=representation.identity.to_document(),
        phase_source=selection.phase_source.to_document(), phase_arrays=selection.arrays.identity.to_document(),
        raw_phase_space=selection.phase_bytes.to_document(), mass_sha256=selection.mass_sha256,
        density_guess_policy=selection.density_guess_policy, initial_ensemble_admission='UNEVALUABLE'))
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_mm_remainder as coupling, periodic_images as images
    from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_electronic as electronic
    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_qmmm import PeriodicCoupledOperator, build_periodic_amber_system
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_operator_options, accelerated_engine
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import record_gpu_observation
    with (root/'native-observations.jsonl').open('x', buffering=1) as native_log:
        def native_observe(row):
            native_log.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')
            if accelerated_engine(prototype.engine):
                record_gpu_observation(root, row)
        original, scales, assignment = build_periodic_amber_system(representation=representation,
            cell=prototype.cell, settings=prototype.molecular, topology_path=root/'original.prmtop', output_directory=root)
        # Require the actual native masses to be exactly the selected binary64
        # projection, not merely within the force-assignment tolerance.
        from openmm import unit
        actual_masses = tuple(float(original.getParticleMass(i).value_in_unit(unit.dalton))
            for i in range(original.getNumParticles()))
        if actual_masses != tuple(masses):
            raise ValueError('trajectory native system substitutes an original physical mass')
        operator = PeriodicCoupledOperator(representation=representation, selection=prototype.path,
            settings=prototype.electronic, cell=prototype.cell, original_system=original,
            source_scee=scales, coupling=coupling, images=images, electronic=electronic, observe=native_observe,
            reuse_converged_density=selection.density_guess_policy == 'PREVIOUS_SUCCESSFUL_RKS',
            **periodic_operator_options(prototype.engine))
        try:
            _json(root/'coupling-audit.json', dict(original_assignment=assignment,
                remainder=operator.remainder_audit, embedding=operator.embedding_audit))
            summary = record_reference_trajectory(operator=operator, directory=root, initial_angstrom=xyz,
                initial_velocity_nm_per_ps=velocity, physical_masses_dalton=masses, settings=selection.settings)
            if summary['completed_evaluations'] != operator.evaluations:
                raise ValueError('trajectory loses actual complete coupled evaluations')
            return summary
        finally:
            del operator
