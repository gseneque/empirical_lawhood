# SPDX-License-Identifier: MPL-2.0
"""Exposed trajectory transport and original-custody controls, not enzyme evidence."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import zlib

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_trajectory_selection as selected
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_trajectory_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_trajectory_translation as graph
from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_trajectory_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_trajectory_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics_assessment import ReferenceTrajectoryCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_assessment import assess_recorded_trajectory, selected_trajectory_member
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.capabilities import CapabilityConfigRef
from empirical_lawhood.execution.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.execution.native_subwork import NativeSubworkState, NativeSubworkObservationPublicationError
from empirical_lawhood.execution.local.execution import prepare_worker_invocation
from empirical_lawhood.execution.local.native_subwork_inputs import validate_native_subwork_inputs

from tests import test_rubisco_periodic_probe_operation as probe
from tests.test_rubisco_periodic_dynamics import AnalyticalOperator
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.runtime_platform.test_worker_preflight import _original_task


fixture = probe.fixture


def trajectory(fixture, *, policy='COLD', criteria=True):
    raw = original_coordinates(fixture.selection, fixture.model, fixture.sources)
    xyz = np.frombuffer(raw, dtype='<f8').reshape((-1, 3)).copy()
    velocity = np.linspace(-.1, .2, xyz.size).reshape(xyz.shape)
    settings = ReferenceDynamicsSettings('settings.exposed.trajectory', D('5e-16'), 3)
    limits = ReferenceTrajectoryCriteria('criteria.exposed.trajectory', D('1e-12'), D('1e-12'), D('1e-8'), None) if criteria else None
    selection, phase = selected.prepare_reference_trajectory(prototype=fixture.selection, representation=fixture.model,
        phase_source=fixture.model.raw_coordinates, initial_angstrom=xyz, initial_velocity_nm_per_ps=velocity,
        settings=settings, criteria=limits, density_guess_policy=policy)
    return owner.config_kind(accelerated=fixture.config.ACCELERATED)('config.exposed.trajectory', fixture.config, selection), phase


def stub_native(fixture, monkeypatch, *, failure=None, bad_mass=False):
    import empirical_lawhood.domains.rubisco.rubisco_response as package
    import empirical_lawhood.adapters.rubisco.rubisco_response as native_package
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm as qmmm
    observed = []
    for short in ('periodic_mm_remainder', 'periodic_images', 'pyscf_periodic_electronic'):
        owner_package = native_package if short == 'pyscf_periodic_electronic' else package
        name = owner_package.__name__+'.'+short
        stub = ModuleType(name)
        monkeypatch.setitem(sys.modules, name, stub)
        monkeypatch.setattr(owner_package, short, stub, raising=False)
    mm = ModuleType('openmm')
    mm.unit = SimpleNamespace(dalton='exposed-dalton')
    monkeypatch.setitem(sys.modules, 'openmm', mm)
    masses = selected.physical_masses(fixture.model)
    if bad_mass:
        masses[7] += 1e-10  # Below the existing MM-force tolerance, still forbidden for the physical clock.

    def build(**kwargs):
        observed.append(('build', kwargs))
        system = SimpleNamespace(getNumParticles=lambda:len(masses),
            getParticleMass=lambda i:SimpleNamespace(value_in_unit=lambda unit:float(masses[i])))
        return system, {}, {'scope':'EXPOSED_SOFTWARE_CONTROL'}

    class Operator(AnalyticalOperator):
        def __init__(self, **kwargs):
            observed.append(('operator', kwargs))
            self.remainder_audit = self.embedding_audit = {'scope':'EXPOSED_SOFTWARE_CONTROL'}
            self.evaluations = 0
            self.observe = kwargs['observe']
            super().__init__(lambda x:(float(np.sum(x)) * .01, np.full_like(x, .01)), failure=failure)

        def evaluate(self, coordinates):
            self.evaluations += 1
            observed.append(('force', coordinates.copy()))
            self.observe(dict(event='entry', evaluation=self.evaluations, scope='EXPOSED_SOFTWARE_CONTROL'))
            result = super().evaluate(coordinates)
            self.observe(dict(event='return', evaluation=self.evaluations, scope='EXPOSED_SOFTWARE_CONTROL'))
            return result

    monkeypatch.setattr(qmmm, 'build_periodic_amber_system', build)
    monkeypatch.setattr(qmmm, 'PeriodicCoupledOperator', Operator)
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k:())
    return observed


def run_body(fixture, config, phase, directory):
    directory.mkdir()
    return native.execute_reference_trajectory(selection=config.selection, prototype=fixture.selection,
        representation=fixture.model, sources=fixture.sources, phase_bytes=phase, directory=directory)


def assess_directory(fixture, config, phase, directory, *, success=True):
    return assess_recorded_trajectory(selection=config.selection, prototype=fixture.selection,
        representation=fixture.model, phase_bytes=phase, native_succeeded=success,
        files=((p.name, p.read_bytes() if selected_trajectory_member(p.name) else None) for p in sorted(directory.iterdir())))


def custody(fixture, config, phase):
    plane = _plane(fixture.tmp_path/'trajectory-custody', binary_codecs=(owner.PHASE_CODEC,))
    records = (('config', config.identity, config), *owner.native_input_records(config, fixture.model, fixture.sources))
    payloads = [(name, pin, record.canonical_bytes(), 'application/json', ArtifactProfile.CANONICAL_JSON) for name, pin, record in records]
    payloads.append(('native-phase', config.selection.phase_bytes, phase, 'application/octet-stream', ArtifactProfile.RAW_SOURCE_BYTES))
    manifests = []
    for name, pin, raw, media, profile in payloads:
        result = plane.write(ArtifactWriteRequest(pin.object_id, 'inputs/'+name+('.bin' if profile is ArtifactProfile.RAW_SOURCE_BYTES else '.json'),
            pin.object_schema, profile, media, 'inputs.exposed.trajectory', 'inputs', raw,
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(resolve_artifact_sidecar_bytes(plane, plane.root.resolve(result.materialization.relative_path + '.manifest.json', for_write=False).read_bytes()))
    manifests = tuple(sorted(manifests, key=lambda r:r.materialization.materialization_id))
    verified = tuple(sorted((VerifiedArtifactInput(m.logical, m.materialization) for m in manifests), key=lambda r:r.artifact_id))
    bindings = tuple(WorkerInputBinding.from_verified(row, kind=WorkerInputKind.EXTERNAL) for row in verified)
    by_id = {m.logical.logical_artifact_id:m for m in manifests}
    def ports():
        return tuple(plane.open(by_id[b.artifact_id], binding=b, maximum_bytes=b.size_bytes) for b in bindings)
    manifest = owner.operation_declaration(accelerated=config.ACCELERATED).manifest()
    context = TaskContext('exposed.trajectory', owner.capability_for(config), 'exposed.trajectory.attempt-001',
        CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config.identity.object_id),
        bindings, ports(), (WorkerOutputPort(owner.capability_for(config)+'.product', owner.ReferenceTrajectoryResult.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'logical.exposed.trajectory-result'),),
        manifest.permissions, OutcomeAccess.DEVELOPMENT_VISIBLE, owner.resource_budget(config), WorkerIsolationProfile.TRUSTED_LOCAL,
        accelerated_compute=config.ACCELERATED)
    runner = owner.operation_declaration(accelerated=config.ACCELERATED).runner_factory()
    task = _original_task(runner, context, SimpleNamespace(verified_inputs=verified))
    contract = prepare_worker_invocation(runner, context, verified, implementation=config.original.implementation,
        execution_plan=ObjectIdentity('plan.exposed.trajectory', 'empirical-lawhood/runtime/development-execution-plan', '1.0.0', '1'*64),
        execution_task=ObjectIdentity.from_record(task.task_id, task), execution_task_record=task,
        native_effect=True, native_work_preparer=owner.prepare_native_work)
    assert contract.native_preparation_error is None
    context = replace(context, prepared_invocation=contract)
    fixture.contexts.append(context)
    store = _store(plane, contract.expected_parent_contact, manifests, prepared_invocation=contract)
    store.parent_contacts.begin(contract.expected_parent_contact)
    def fresh_context():
        fresh = replace(context, input_ports=ports())
        fixture.contexts.append(fresh)
        return fresh
    return SimpleNamespace(plane=plane, context=context, store=store, manifests=manifests,
        work=contract.native_work, fresh_context=fresh_context)


def test_phase_binding_is_complete_canonical_and_keeps_supplied_velocities(fixture):
    before = set(sys.modules)
    config, raw = trajectory(fixture)
    xyz, velocity, masses = selected.read_phase_space(config.selection, fixture.model, raw)
    assert len(raw) == len(fixture.model.atoms) * 48
    np.testing.assert_array_equal(velocity, np.linspace(-.1, .2, xyz.size).reshape(xyz.shape))
    assert tuple(masses) == tuple(float(a.mass_dalton) for a in fixture.model.atoms)
    assert decode_canonical_bytes(config.canonical_bytes(), owner.ReferenceTrajectoryConfig, maximum_bytes=owner.MAX_CONFIG) == config
    assert not {'openmm', 'pyscf'} & (set(sys.modules)-before)
    changed = replace(config.selection.settings, steps=4)
    other, _ = selected.prepare_reference_trajectory(prototype=fixture.selection, representation=fixture.model,
        phase_source=fixture.model.raw_coordinates, initial_angstrom=xyz, initial_velocity_nm_per_ps=velocity,
        settings=changed, criteria=config.selection.criteria, density_guess_policy='COLD')
    assert other.identity.object_id != config.selection.identity.object_id


@pytest.mark.parametrize('change', ('raw-byte', 'short', 'mass', 'member-hash', 'prototype', 'clock', 'scope', 'nonfinite-kinetic'))
def test_phase_and_operator_substitutions_refuse_before_native(fixture, change):
    config, raw = trajectory(fixture)
    selection, model, prototype = config.selection, fixture.model, fixture.selection
    with pytest.raises((ValueError, ArithmeticError)):
        if change == 'raw-byte': raw = bytes((raw[0] ^ 1,))+raw[1:]
        elif change == 'short': raw = raw[:-8]
        elif change == 'mass': model = replace(model, atoms=(replace(model.atoms[0], mass_dalton=D(4)), *model.atoms[1:]))
        elif change == 'member-hash': selection = replace(selection, arrays=replace(selection.arrays,
            members=(replace(selection.arrays.members[0], sha256='0'*64), selection.arrays.members[1])))
        elif change == 'prototype': prototype = replace(prototype, selection_id='selection.substituted')
        elif change == 'clock': selection = replace(selection, settings=replace(selection.settings, step_seconds=D('1e-15')))
        elif change == 'scope': selection = replace(selection, scope='ADMITTED_RATE')
        else:
            xyz, _, _ = selected.read_phase_space(selection, model, raw)
            selection, raw = selected.prepare_reference_trajectory(prototype=prototype, representation=model,
                phase_source=model.raw_coordinates, initial_angstrom=xyz, initial_velocity_nm_per_ps=np.full_like(xyz, 1e300),
                settings=selection.settings, criteria=selection.criteria, density_guess_policy='COLD')
        selected.validate_trajectory_prototype(selection, prototype)
        selected.read_phase_space(selection, model, raw)


@pytest.mark.parametrize('policy', ('COLD', 'PREVIOUS_SUCCESSFUL_RKS'))
def test_complete_native_binding_and_independent_file_read(fixture, monkeypatch, policy):
    # Both policies are explicit exposed controls, not enzyme results.
    if policy == 'PREVIOUS_SUCCESSFUL_RKS':
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
        fixture.selection = prepare_periodic_probe_selection(representation=fixture.model, path=fixture.selection.path,
            cell=fixture.selection.cell, electronic=replace(fixture.selection.electronic, ks_flavour='RKS'),
            molecular=fixture.selection.molecular, engine=fixture.stock)
        fixture.config = replace(fixture.config, selection=fixture.selection)
    config, raw = trajectory(fixture, policy=policy)
    observed = stub_native(fixture, monkeypatch)
    directory = fixture.tmp_path/'native'
    summary = run_body(fixture, config, raw, directory)
    assert [kind for kind, _ in observed] == ['build', 'operator', 'force', 'force', 'force', 'force']
    assert observed[1][1]['reuse_converged_density'] is (policy == 'PREVIOUS_SUCCESSFUL_RKS')
    assert summary['completed_steps'] == 3 and summary['captured_frames'] == 4
    monkeypatch.setattr(native, 'execute_reference_trajectory', lambda **k:pytest.fail('read entered native calculation'))
    report = assess_directory(fixture, config, raw, directory)
    assert report['selected_trace_criteria'] == 'SATISFIED' and report['new_operator_evaluations'] == 0
    assert report['initial_ensemble_admission'] == report['physical_rate_admission'] == 'UNEVALUABLE'
    assert report['retained_force_frames'] == report['recorded_return_metadata'] == 4
    assert D(report['observed_physical_time_seconds']) == D('1.5e-15')


def test_uks_cannot_select_unaccepted_density_reuse(fixture):
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
    fixture.selection = prepare_periodic_probe_selection(representation=fixture.model, path=fixture.selection.path,
        cell=fixture.selection.cell, electronic=replace(fixture.selection.electronic, ks_flavour='UKS'),
        molecular=fixture.selection.molecular, engine=fixture.stock)
    fixture.config = replace(fixture.config, selection=fixture.selection)
    assert fixture.selection.electronic.ks_flavour == 'UKS'
    with pytest.raises(ValueError, match='RKS density'):
        trajectory(fixture, policy='PREVIOUS_SUCCESSFUL_RKS')


def test_actual_native_mass_change_refuses_before_force(fixture, monkeypatch):
    config, raw = trajectory(fixture)
    observed = stub_native(fixture, monkeypatch, bad_mass=True)
    with pytest.raises(ValueError, match='physical mass'):
        run_body(fixture, config, raw, fixture.tmp_path/'native')
    assert [name for name, _ in observed] == ['build']


@pytest.mark.parametrize('failure', ('native', 'nonfinite', 'short', 'unit', 'mutated-input'))
def test_failed_force_keeps_original_input_raw_return_and_valid_prefix(fixture, monkeypatch, failure):
    config, raw = trajectory(fixture)
    observed = stub_native(fixture, monkeypatch, failure=failure)
    directory = fixture.tmp_path/'native'
    with pytest.raises((RuntimeError, ValueError)):
        run_body(fixture, config, raw, directory)
    assert len([kind for kind, _ in observed if kind == 'force']) == 2
    assert (directory/'evaluation.0000000000000002.coordinates-angstrom.npy').exists()
    assert not (directory/'evaluation.0000000000000002.complete-frame.json').exists()
    assert not (directory/'trajectory-summary.json').exists()
    report = assess_directory(fixture, config, raw, directory, success=False)
    assert report['selected_trace_criteria'] == 'UNEVALUABLE' and report['retained_force_frames'] == 1
    assert report['recorded_evaluation_inputs'] == 2 and report['partial_last_evaluation']
    assert report['recorded_return_metadata'] == (1 if failure == 'native' else 2)
    if failure == 'nonfinite':
        assert np.isnan(np.load(directory/'evaluation.0000000000000002.energy_hartree.npy', allow_pickle=False))


@pytest.mark.parametrize('change', ('velocity', 'gradient', 'clock', 'mass', 'initial', 'summary', 'trailing-array', 'missing-frame'))
def test_retained_file_substitutions_refuse_or_falsify(fixture, monkeypatch, change):
    config, raw = trajectory(fixture)
    stub_native(fixture, monkeypatch)
    directory = fixture.tmp_path/'native'
    run_body(fixture, config, raw, directory)
    if change in {'velocity', 'gradient'}:
        suffix = 'velocities-nm-per-ps.npy' if change == 'velocity' else 'gradient_hartree_per_bohr.npy'
        key = 'velocity_sha256' if change == 'velocity' else 'gradient_sha256'
        p = directory/('evaluation.0000000000000002.'+suffix)
        array = np.load(p, allow_pickle=False); array[5, 1] += .1
        with p.open('wb') as stream: np.save(stream, array, allow_pickle=False)
        marker = directory/'evaluation.0000000000000002.complete-frame.json'
        row = json.loads(marker.read_bytes());row[key] = sha256(array.tobytes()).hexdigest();marker.write_text(json.dumps(row))
        report = assess_directory(fixture, config, raw, directory)
        assert report['selected_trace_criteria'] == 'FALSIFIED'
        return
    if change in {'clock', 'summary'}:
        p = directory/('evaluation.0000000000000002.complete-frame.json' if change == 'clock' else 'trajectory-summary.json')
        row = json.loads(p.read_bytes());row['physical_time_seconds'] = '10';p.write_text(json.dumps(row))
    elif change == 'mass':
        p = directory/'physical-masses-dalton.npy';array = np.load(p, allow_pickle=False);array[0] += 1
        with p.open('wb') as stream:np.save(stream, array, allow_pickle=False)
    elif change == 'initial':
        p = directory/'initial-phase-space.bin';data = p.read_bytes();p.write_bytes(data[:-1]+bytes((data[-1] ^ 1,)))
    elif change == 'trailing-array':
        p = directory/'evaluation.0000000000000002.coordinates-angstrom.npy';p.write_bytes(p.read_bytes()+b'undeclared')
    else:(directory/'evaluation.0000000000000002.complete-frame.json').unlink()
    with pytest.raises(ValueError):assess_directory(fixture, config, raw, directory)


@pytest.mark.parametrize('failure', (None, 'native', 'nonfinite'))
def test_real_shared_custody_recovers_without_native_replay_and_reads_prefix(fixture, monkeypatch, failure):
    config, raw = trajectory(fixture)
    observed = stub_native(fixture, monkeypatch, failure=failure)
    c = custody(fixture, config, raw)
    assert len(c.manifests) == 8 and owner.BUDGET.wall_time_seconds is None
    validate_native_subwork_inputs(c.plane, c.work.definitions[0], c.manifests,
        visibility=VisibilityCeiling.DEVELOPMENT_ONLY, access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    draft = graph.reference_trajectory_draft(config)
    assert len(draft.operations) == 1 and len(draft.external_inputs) == 7
    assert owner._decode(c.fresh_context()) == (config, fixture.model, fixture.sources, raw)
    runner = owner.ReferenceTrajectoryRunner()
    returned = runner.execute_with_native_subwork(c.context, c.store)
    result = decode_canonical_bytes(returned.outputs[0].payload, owner.ReferenceTrajectoryResult, maximum_bytes=owner.MAX_RETURN)
    assert result.completion.operational_status is (OperationalStatus.SUCCEEDED if failure is None else OperationalStatus.FAILED)
    assert len([kind for kind, _ in observed if kind == 'force']) == (4 if failure is None else 2)
    completed = c.store.recover(c.work.definitions[0])
    assert completed.call_entry is not None and completed.call_return is not None
    assert result.completion.cost.retained_bytes == D(sum(m.materialization.size_bytes for m in completed.outputs))
    monkeypatch.setattr(native, 'execute_reference_trajectory', lambda **k:pytest.fail('original completed attempt replayed'))
    recovered = runner.execute_with_native_subwork(c.fresh_context(), c.store)
    assert recovered.outputs[0].payload == returned.outputs[0].payload
    report = retained.read_reference_trajectory(config=config, representation=fixture.model, phase_bytes=raw,
        original_result=result, native_subwork=c.store, assessor_source=fixture.model.material.sources[0])
    assert report['assessment_error'] is None and report['new_operator_evaluations'] == 0
    assert report['authenticated_file_count'] == len(result.returned.files.files)
    assert report['assessment']['selected_trace_criteria'] == ('SATISFIED' if failure is None else 'UNEVALUABLE')


@pytest.mark.parametrize('unacknowledged', (False, True))
def test_unknown_original_contact_cannot_be_reentered(fixture, monkeypatch, unacknowledged):
    config, raw = trajectory(fixture)
    stub_native(fixture, monkeypatch)
    c = custody(fixture, config, raw)
    if unacknowledged:
        def reject(*args, **kwargs):raise OSError('exposed original return acknowledgement failure')
        monkeypatch.setattr(c.store, 'call_return', reject)
        with pytest.raises(NativeSubworkObservationPublicationError):
            owner.ReferenceTrajectoryRunner().execute_with_native_subwork(c.context, c.store)
    else:
        c.store.freeze_roster(c.work.rosters[0], definitions=c.work.definitions)
        entry = c.store.begin(c.work.definitions[0]);c.store.contact(entry)
    monkeypatch.setattr(native, 'execute_reference_trajectory', lambda **k:pytest.fail('uncertain native work reentered'))
    with pytest.raises(ValueError):owner.ReferenceTrajectoryRunner().execute_with_native_subwork(c.fresh_context(), c.store)
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION


def test_late_archive_corruption_is_refused_even_after_early_assessment_error(fixture, monkeypatch):
    config, raw = trajectory(fixture)
    stub_native(fixture, monkeypatch)
    original = native.execute_reference_trajectory
    def changed(**kwargs):
        result = original(**kwargs)
        directory = kwargs['directory']
        p = directory/'evaluation.0000000000000001.complete-frame.json'
        row = json.loads(p.read_bytes());row['physical_time_seconds'] = '100';p.write_text(json.dumps(row))
        (directory/'zz-tail.txt').write_bytes(b'original-tail')
        return result
    monkeypatch.setattr(native, 'execute_reference_trajectory', changed)
    c = custody(fixture, config, raw)
    output = owner.ReferenceTrajectoryRunner().execute_with_native_subwork(c.context, c.store)
    result = decode_canonical_bytes(output.outputs[0].payload, owner.ReferenceTrajectoryResult, maximum_bytes=owner.MAX_RETURN)
    original_iter = c.store.iter_completed_output
    archive = b''.join(original_iter(result.definition, 'files.raw'))
    expanded = zlib.decompress(archive, wbits=31)
    assert expanded.endswith(b'original-tail')
    compressor = zlib.compressobj(wbits=31)
    bad = compressor.compress(expanded[:-1]+b'X')+compressor.flush()
    def iter_bad(definition, output_id, **kwargs):
        if output_id == 'files.raw':yield bad
        else:yield from original_iter(definition, output_id, **kwargs)
    monkeypatch.setattr(c.store, 'iter_completed_output', iter_bad)
    with pytest.raises(retained.TrajectoryCustodyError, match='original complete file'):
        retained.read_reference_trajectory(config=config, representation=fixture.model, phase_bytes=raw,
            original_result=result, native_subwork=c.store, assessor_source=fixture.model.material.sources[0])


def test_public_authoring_retains_exact_binary_phase_and_six_canonical_inputs(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import periodic_trajectory as public
    config, raw = trajectory(fixture)
    plane = _plane(fixture.tmp_path/'public-custody', binary_codecs=(owner.PHASE_CODEC,))
    project = fixture.tmp_path/'project';project.mkdir()
    output = Path(plane.root.contract.canonical_path)/'authored'
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **k:fixture.config.provenance)
    observed = []
    def author(**kwargs):
        observed.append(kwargs)
        for key, path in kwargs['input_bindings']:
            row = next(r for r in kwargs['draft'].external_inputs if r.input_id == key)
            manifest = resolve_artifact_sidecar_bytes(plane, path.with_name(path.name + '.manifest.json').read_bytes())
            plane.verify_manifest(manifest)
            assert len(path.read_bytes()) == row.maximum_size_bytes and sha256(path.read_bytes()).hexdigest() == row.expected_content_sha256
            if key.endswith('native-phase'):
                assert path.read_bytes() == raw and manifest.logical.profile is ArtifactProfile.RAW_SOURCE_BYTES
        return {'scope':'EXPOSED_SHARED_AUTHOR_STUB'}
    monkeypatch.setattr(recursive_authoring, 'author_recursive_wave', author)
    result = public.author_reference_trajectory(selection=config.selection, prototype=fixture.selection,
        representation=fixture.model, raw_topology=fixture.raw_top, raw_coordinates=fixture.raw_xyz,
        phase_bytes=raw, project_root=project, work_directory=fixture.workdir, artifact_writer=plane, output_dir=output)
    assert len(observed) == 1 and len(result['native_input_paths']) == 7
    assert not fixture.workdir.exists()


def test_incomplete_frame_marker_preserves_prefix_and_cannot_become_complete(fixture, monkeypatch):
    config, raw = trajectory(fixture)
    observed = stub_native(fixture, monkeypatch)
    original_json = native._json
    def failed_marker(path, value, **kwargs):
        if path.name == 'evaluation.0000000000000002.frame-pending.json':
            path.write_bytes(b'{"partial":')
            raise OSError('exposed partial frame-marker write')
        return original_json(path, value, **kwargs)
    monkeypatch.setattr(native, '_json', failed_marker)
    directory = fixture.tmp_path/'native'
    with pytest.raises(OSError, match='partial frame-marker'):
        run_body(fixture, config, raw, directory)
    assert len([kind for kind, _ in observed if kind == 'force']) == 2
    assert (directory/'evaluation.0000000000000002.frame-pending.json').read_bytes() == b'{"partial":'
    report = assess_directory(fixture, config, raw, directory, success=False)
    assert report['retained_force_frames'] == 1 and report['recorded_return_metadata'] == 2
    assert report['partial_last_evaluation'] and report['selected_trace_criteria'] == 'UNEVALUABLE'


def compile_selected(config, draft):
    from empirical_lawhood.execution.capabilities import CapabilityRegistry
    from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
    declaration = owner.operation_declaration()
    return compile_recursive_wave(draft=draft, registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed.trajectory', (declaration.manifest(),)),
        implementation_commit=config.original.implementation.observed_git_head, output_codecs=declaration.record_codecs)


def test_complete_original_graph_compiles_through_shared_engine(fixture):
    config, _ = trajectory(fixture)
    draft = graph.reference_trajectory_draft(config)
    compiled = compile_selected(config, draft)
    assert compiled.proof is not None and compiled.run_plan is not None
    assert len(compiled.execution_plan.tasks) == 1
    task = compiled.execution_plan.tasks[0]
    assert task.maximum_attempts == 1 and task.capability.requested_resources == owner.BUDGET
    assert draft.operations[0].resource_lock_ids == ('gp-periodic-force-native-worker',)
    assert not fixture.workdir.exists()


@pytest.mark.parametrize('change', ('phase-hash', 'phase-size', 'phase-link', 'root-claim'))
def test_compiler_refuses_changed_source_and_physical_scope(fixture, change):
    config, _ = trajectory(fixture)
    draft = graph.reference_trajectory_draft(config)
    if change in {'phase-hash', 'phase-size'}:
        edits = {'expected_content_sha256':'0'*64} if change == 'phase-hash' else {'maximum_size_bytes':48}
        draft = replace(draft, external_inputs=tuple(replace(row, **edits) if row.input_id.endswith('native-phase')
            else row for row in draft.external_inputs))
    elif change == 'phase-link':
        draft = replace(draft, links=tuple(replace(row, external_input_id='external.reference-trajectory.native-source')
            if row.consumer_input_id == 'native-phase' else row for row in draft.links))
    else:
        draft = replace(draft, development_study=replace(draft.development_study, question='Admit a physical turnover rate'))
    with pytest.raises(ValueError):compile_selected(config, draft)
    assert not fixture.workdir.exists()


@pytest.mark.parametrize('change', ('phase-bytes', 'amber-source', 'occupied-inputs'))
def test_public_authoring_bad_inputs_refuse_before_source_capture_or_writes(fixture, monkeypatch, change):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import periodic_trajectory as public
    config, raw = trajectory(fixture)
    topology = fixture.raw_top
    plane = _plane(fixture.tmp_path/'public-custody', binary_codecs=(owner.PHASE_CODEC,))
    project = fixture.tmp_path/'project';project.mkdir()
    output = Path(plane.root.contract.canonical_path)/'authored'
    if change == 'phase-bytes':raw += b'changed'
    elif change == 'amber-source':topology += b'changed'
    else:
        input_directory = output.with_name(output.name+'-native-inputs');input_directory.mkdir()
        (input_directory/'original').write_bytes(b'preserve original attempted preparation')
    before = {p.relative_to(fixture.tmp_path):p.read_bytes() for p in fixture.tmp_path.rglob('*') if p.is_file()}
    def refuse(*args, **kwargs):pytest.fail('invalid inputs reached source capture or shared authoring')
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', refuse)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', refuse)
    monkeypatch.setattr(recursive_authoring, 'author_recursive_wave', refuse)
    with pytest.raises(ValueError):
        public.author_reference_trajectory(selection=config.selection, prototype=fixture.selection,
            representation=fixture.model, raw_topology=topology, raw_coordinates=fixture.raw_xyz,
            phase_bytes=raw, project_root=project, work_directory=fixture.workdir, artifact_writer=plane, output_dir=output)
    assert before == {p.relative_to(fixture.tmp_path):p.read_bytes() for p in fixture.tmp_path.rglob('*') if p.is_file()}


def test_exact_physical_time_survives_canonical_decimal_spelling(fixture, monkeypatch):
    config, raw = trajectory(fixture)
    config = replace(config, selection=replace(config.selection,
        settings=replace(config.selection.settings, step_seconds=D('5.00e-16'))))
    decoded = decode_canonical_bytes(config.canonical_bytes(), owner.ReferenceTrajectoryConfig, maximum_bytes=owner.MAX_CONFIG)
    assert decoded == config and str(decoded.selection.settings.step_seconds) != str(config.selection.settings.step_seconds)
    stub_native(fixture, monkeypatch)
    directory = fixture.tmp_path/'native'
    run_body(fixture, decoded, raw, directory)
    report = assess_directory(fixture, config, raw, directory)
    assert report['selected_trace_criteria'] == 'SATISFIED' and D(report['observed_physical_time_seconds']) == D('1.500e-15')


def test_complete_trajectory_cannot_omit_original_amber_source_file(fixture, monkeypatch):
    config, raw = trajectory(fixture)
    stub_native(fixture, monkeypatch)
    directory = fixture.tmp_path/'native'
    run_body(fixture, config, raw, directory)
    (directory/'original.prmtop').unlink()
    with pytest.raises(ValueError, match='original input bindings'):
        assess_directory(fixture, config, raw, directory)
