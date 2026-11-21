# SPDX-License-Identifier: MPL-2.0
"""Retain reference, bias and thermal-noise operands for original sampling."""

from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium import propagate_reference_equilibrium
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import read_equilibrium_phase_space, selected_bias, validate_equilibrium_prototype
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import ARRAY_KEYS
from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_trajectory_native import _array, _json


def record_reference_equilibrium(*, operator, bias, directory, initial_angstrom,
        initial_velocity_nm_per_ps, physical_masses_dalton, settings, sample_consumer=None):
    """Capture original returns and each draw before its subsequent force call.

    The complete-directory archive includes unsuccessful and partial operands.
    A frame marker follows every required array; no failure is retried. Bias
    calls, electronic calls and thermal draws remain distinct denominators.
    """
    import numpy as np
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError('equilibrium recording requires its existing selected native directory')
    calls, captured, draws, bias_calls = (0,)*4
    latest, latest_bias, latest_noise = None, None, None
    with (root/'equilibrium-evaluations.jsonl').open('x', buffering=1) as events:
        def observe(row):
            events.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')

        def record_bias(coordinates):
            nonlocal bias_calls, latest_bias
            number = calls+1
            prefix = f'evaluation.{number:016d}.'
            latest_bias = None
            raw_xyz = np.array(coordinates, dtype='<f8', copy=True)
            _array(root/(prefix+'bias-coordinates-angstrom.npy'), raw_xyz)
            bias_calls += 1
            observe(dict(event='original-bias-entry', evaluation=number, bias_invocation=bias_calls))
            returned = bias(coordinates)
            # Capture the original bias before the sampler validates it.
            if 'gradient_kj_mol_per_angstrom' in returned:
                _array(root/(prefix+'bias-gradient-kj-mol-per-angstrom.npy'), returned['gradient_kj_mol_per_angstrom'])
            for i, derivative in enumerate(returned.get('cv_cartesian_derivatives', ())):
                _array(root/(prefix+f'bias-cv-derivative.{i:08d}.npy'), derivative)
            _json(root/(prefix+'bias-return.json'), {k:v for k, v in returned.items()
                if k not in ('gradient_kj_mol_per_angstrom', 'cv_cartesian_derivatives')}, diagnostic=True)
            latest_bias = dict(evaluation=number, energy=float(returned['energy_kj_mol']),
                coordinate_sha256=sha256(raw_xyz.tobytes()).hexdigest(),
                gradient_sha256=sha256(np.asarray(returned['gradient_kj_mol_per_angstrom'], dtype='<f8').tobytes()).hexdigest())
            observe(dict(event='original-bias-return', evaluation=number, bias_invocation=bias_calls))
            return returned

        class RecordingOperator:
            def evaluate(self, coordinates):
                nonlocal calls, latest
                calls += 1
                prefix = f'evaluation.{calls:016d}.'
                raw_xyz = np.array(coordinates, dtype='<f8', copy=True)
                _array(root/(prefix+'coordinates-angstrom.npy'), raw_xyz)
                latest = None
                returned = operator.evaluate(coordinates)
                for key in ('energy_hartree', *ARRAY_KEYS):
                    if key in returned:
                        _array(root/(prefix+key+'.npy'), returned[key])
                _json(root/(prefix+'native-return.json'),
                    {k:v for k, v in returned.items() if k not in ARRAY_KEYS}, diagnostic=True)
                latest = dict(evaluation=calls, prefix=prefix,
                    coordinate_sha256=sha256(raw_xyz.tobytes()).hexdigest(),
                    gradient_sha256=sha256(np.asarray(returned['gradient_hartree_per_bohr'], dtype='<f8').tobytes()).hexdigest(),
                    energy_hartree=float(returned['energy_hartree']))
                return returned

        def capture_noise(row):
            nonlocal draws, latest_noise
            number = row['step']+1
            if row['step'] != draws+1 or number != calls+1:
                raise ValueError('equilibrium recording loses the original noise/force order')
            prefix = f'evaluation.{number:016d}.'
            _array(root/(prefix+'noise-standard-normal.npy'), row['standard_normal'])
            digest = sha256(row['standard_normal'].tobytes()).hexdigest()
            metadata = {k:v for k, v in row.items() if k != 'standard_normal'}
            _json(root/(prefix+'noise-state.json'), dict(metadata, noise_sha256=digest))
            latest_noise = dict(step=row['step'], sha256=digest)
            draws += 1

        def capture(frame):
            nonlocal captured
            if (latest is None or frame['evaluation'] != calls or calls != captured+1
                    or frame['step'] != captured or frame['reference_energy_hartree'] != latest['energy_hartree']
                    or sha256(frame['coordinates_angstrom'].tobytes()).hexdigest() != latest['coordinate_sha256']
                    or sha256(frame['reference_gradient_hartree_per_bohr'].tobytes()).hexdigest() != latest['gradient_sha256']):
                raise ValueError('equilibrium frame changes its original returned reference force')
            prefix = latest['prefix']
            bias_sha = sha256(frame['bias_gradient_kj_mol_per_angstrom'].tobytes()).hexdigest()
            if bias is None:
                if frame['bias_energy_kj_mol'] != 0. or np.any(frame['bias_gradient_kj_mol_per_angstrom'] != 0):
                    raise ValueError('equilibrium frame invents an unselected bias')
                _array(root/(prefix+'bias-gradient-kj-mol-per-angstrom.npy'), frame['bias_gradient_kj_mol_per_angstrom'])
            elif (latest_bias is None or latest_bias['evaluation'] != calls
                    or latest_bias['energy'] != frame['bias_energy_kj_mol']
                    or latest_bias['coordinate_sha256'] != latest['coordinate_sha256']
                    or latest_bias['gradient_sha256'] != bias_sha):
                raise ValueError('equilibrium frame changes its original bias return')
            noise_sha = None
            if frame['step']:
                noise_sha = sha256(frame['noise_standard_normal'].tobytes()).hexdigest()
                if latest_noise != dict(step=frame['step'], sha256=noise_sha):
                    raise ValueError('equilibrium frame substitutes its captured original noise')
            elif frame['noise_standard_normal'] is not None:
                raise ValueError('equilibrium frame invents an initial noise draw')
            _array(root/(prefix+'velocities-nm-per-ps.npy'), frame['velocities_nm_per_ps'])
            arrays = ('coordinates_angstrom', 'velocities_nm_per_ps', 'reference_gradient_hartree_per_bohr',
                'bias_gradient_kj_mol_per_angstrom', 'noise_standard_normal')
            metadata = {k:v for k, v in frame.items() if k not in arrays}
            metadata.update(coordinate_sha256=latest['coordinate_sha256'], reference_gradient_sha256=latest['gradient_sha256'],
                bias_gradient_sha256=bias_sha, noise_sha256=noise_sha,
                velocity_sha256=sha256(frame['velocities_nm_per_ps'].tobytes()).hexdigest())
            pending = root/(prefix+'frame-pending.json')
            _json(pending, metadata)
            pending.rename(root/(prefix+'complete-frame.json'))
            captured += 1
            if sample_consumer is not None:
                sample_consumer(frame)

        _, _, summary = propagate_reference_equilibrium(operator=RecordingOperator(),
            bias=record_bias if bias is not None else None, initial_angstrom=initial_angstrom,
            initial_velocity_nm_per_ps=initial_velocity_nm_per_ps, physical_masses_dalton=physical_masses_dalton,
            settings=settings, observe=observe, capture_noise=capture_noise, capture=capture)
        if (summary['completed_evaluations'] != calls or summary['captured_frames'] != captured
                or summary['retained_noise_draws'] != draws or bias_calls != (calls if bias is not None else 0)):
            raise ValueError('equilibrium recording loses an original reference, bias, noise or frame')
        summary = dict(summary, original_bias_invocations=bias_calls)
        _json(root/'equilibrium-summary.json', summary)
        return summary


def execute_reference_equilibrium(*, selection, prototype, representation, sources, phase_bytes, directory):
    """Construct the selected complete reference operator and acquire one trace."""
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
    validate_equilibrium_prototype(selection, prototype)
    original_coordinates(prototype, representation, sources)
    xyz, velocity, masses = read_equilibrium_phase_space(selection, representation, phase_bytes)
    selected_bias(selection, prototype, representation, xyz)
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise ValueError('reference equilibrium requires its existing fresh absolute native directory')
    for name, raw in (('original.prmtop', sources.topology_utf8.encode('ascii')),
            ('original.inpcrd', sources.coordinates_utf8.encode('ascii')),
            ('initial-phase-space.bin', phase_bytes), ('equilibrium-selection.json', selection.canonical_bytes()),
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
        from openmm import unit
        actual_masses = tuple(float(original.getParticleMass(i).value_in_unit(unit.dalton))
            for i in range(original.getNumParticles()))
        if actual_masses != tuple(masses):
            raise ValueError('equilibrium native system substitutes an original physical mass')
        recorder = None
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import ObservedElectronicEquilibriumSelection
        if type(selection) is ObservedElectronicEquilibriumSelection:
            from empirical_lawhood.domains.rubisco.rubisco_response.electronic_observation_native import ElectronicSampleRecorder
            def factory(selected, observe, capture):
                return PeriodicCoupledOperator(representation=representation, selection=selected.path,
                    settings=selected.electronic, cell=selected.cell, original_system=original,
                    source_scee=scales, coupling=coupling, images=images, electronic=electronic,
                    observe=observe, capture_electronic_state=capture,
                    **periodic_operator_options(selected.engine))
            recorder = ElectronicSampleRecorder(selection=selection, prototype=prototype,
                directory=root, operator_factory=factory)
        operator = PeriodicCoupledOperator(representation=representation, selection=prototype.path,
            settings=prototype.electronic, cell=prototype.cell, original_system=original,
            source_scee=scales, coupling=coupling, images=images, electronic=electronic, observe=native_observe,
            reuse_converged_density=selection.density_guess_policy == 'PREVIOUS_SUCCESSFUL_RKS',
            **periodic_operator_options(prototype.engine),
            **({'capture_electronic_state':recorder.capture_for(prototype)} if recorder is not None else {}))
        try:
            _json(root/'coupling-audit.json', dict(original_assignment=assignment,
                remainder=operator.remainder_audit, embedding=operator.embedding_audit))
            bias = (lambda positions: selected_bias(selection, prototype, representation, positions)) if selection.window is not None else None
            summary = record_reference_equilibrium(operator=operator, bias=bias, directory=root,
                initial_angstrom=xyz, initial_velocity_nm_per_ps=velocity,
                physical_masses_dalton=masses, settings=selection.settings,
                **({'sample_consumer':recorder.observe_sample} if recorder is not None else {}))
            if summary['completed_evaluations'] != operator.evaluations:
                raise ValueError('equilibrium sampling loses actual complete coupled evaluations')
            if recorder is not None:
                _json(root/'electronic-observation-summary.json', recorder.summary())
            return summary
        finally:
            del operator
            if recorder is not None:
                recorder.close()
