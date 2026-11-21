# SPDX-License-Identifier: MPL-2.0
"""Actual shared custody for explicitly exposed analytic software controls."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_control_selection as selected
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.native_subwork import NativeSubworkState
from tests.test_rubisco_periodic_control_compilation import configs_for
from tests import test_rubisco_periodic_probe_operation as probe

fixture = probe.fixture


def custody(fixture, config):
    chosen = SimpleNamespace(**(vars(fixture)|{'config':config}))
    return probe.custody(chosen, owner=owner, task_id=owner.node_id(config),
        runner_type=owner.operation_declaration(accelerated=config.ACCELERATED).runner_factory,
        implementation=config.original.implementation, custody_name='custody.'+str(config.point.ordinal))


def execute(c, monkeypatch, function, *, progress=None):
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry
    install_exposed_geometry(monkeypatch)
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *args, **kwargs:())
    monkeypatch.setattr(native, 'execute_periodic_control', function)
    output = owner.operation_declaration(accelerated=c.context.accelerated_compute).runner_factory().execute_with_native_subwork(c.context, c.store if progress is None else progress)
    return decode_canonical_bytes(output.outputs[0].payload, owner.PeriodicProbeResult, maximum_bytes=owner.MAX_RETURN)


def disclose_point(kwargs):
    """Write explicit software operands; no native engine is used by this stub."""
    root, prototype, point = kwargs['directory'], kwargs['prototype'], kwargs['point']
    raw = native.original_coordinates(prototype, kwargs['representation'], kwargs['sources'])
    xyz = selected.point_coordinates(kwargs['protocol'], point, raw)
    np.save(root/'coordinate-array.npy', xyz, allow_pickle=False)
    for name, record in (('control-protocol.json', kwargs['protocol']), ('control-point.json', point),
            ('selection.json', prototype.path), ('electronic-settings.json', point.electronic),
            ('cell.json', prototype.cell), ('mm-settings.json', point.molecular)):
        (root/name).write_bytes(record.canonical_bytes())
    (root/'original.prmtop').write_text(kwargs['sources'].topology_utf8)
    (root/'original.inpcrd').write_text(kwargs['sources'].coordinates_utf8)
    return xyz


@pytest.mark.parametrize('failed', (False, True))
def test_point_retains_original_return_or_failure_and_never_replays(fixture, monkeypatch, failed):
    configs, raw = configs_for(fixture)
    config = configs[1]
    c = custody(fixture, config)
    assert owner._decode(c.fresh_context()) == (config, fixture.model, fixture.sources)
    assert len(c.context.input_ports) == 9
    calls = []
    def literal(**kwargs):
        calls.append(kwargs['point'])
        disclose_point(kwargs)
        (kwargs['directory']/'exposed-control.txt').write_text('SOFTWARE CONTROL; NO ENZYME EVIDENCE\n')
        if failed:
            raise RuntimeError('deliberate exposed control failure')
        return {'energy_hartree':-3.25, 'gradient_hartree_per_bohr':np.zeros((83, 3))}
    result = execute(c, monkeypatch, literal)
    assert calls == [config.point]
    assert result.completion.operational_status is (OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED)
    assert result.completion.cost.cpu_seconds is not None and result.completion.cost.wall_seconds is not None
    monkeypatch.setattr(native, 'execute_periodic_control', lambda **kwargs:pytest.fail('original point was replayed'))
    output = owner.PeriodicControlRunner().execute_with_native_subwork(c.fresh_context(), c.store)
    assert output.outputs[0].payload == result.canonical_bytes()
    report = retained.read_periodic_control_point(config=config, representation=fixture.model, coordinate_bytes=raw,
        original_result=result, native_subwork=c.store, assessor_source=fixture.model.material.sources[0], readout_id='read.exposed.point')
    assert report.selection == config.point.identity and report.original_result == result
    assert report.numerical_integrity is None if failed else report.numerical_integrity.disposition is A.SATISFIED


def test_unknown_point_contact_refuses_automatic_replay(fixture, monkeypatch):
    configs, _ = configs_for(fixture)
    c = custody(fixture, configs[0])
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *args, **kwargs:())
    monkeypatch.setattr(native, 'execute_periodic_control', lambda **kwargs:pytest.fail('unknown point was repeated'))
    c.store.freeze_roster(c.work.rosters[0], definitions=c.work.definitions)
    entry = c.store.begin(c.work.definitions[0])
    c.store.contact(entry)
    with pytest.raises(ValueError, match='no automatic retry'):
        owner.PeriodicControlRunner().execute_with_native_subwork(c.context, c.store)
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION


def test_returned_point_publication_recovers_full_prefix_without_repeating_calculation(fixture, monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response.periodic_controls import recover_periodic_control_publication
    from empirical_lawhood.storage.native_parent_finalization import completed_native_parent_scope
    from empirical_lawhood.execution.local.native_subwork_ipc import NativeSubworkPipeService, NativeSubworkRequest, PipeNativeSubworkProgress
    configs, coordinate_bytes = configs_for(fixture)
    config = configs[1]
    c = custody(fixture, config)
    calls = []
    def literal(**kwargs):
        calls.append(kwargs['point'])
        disclose_point(kwargs)
        return {'energy_hartree': -3.25, 'gradient_hartree_per_bohr': np.zeros((83, 3))}
    publish = c.store.publish_output
    def interrupted(entry, output_id, chunks, **options):
        if output_id != 'files.raw':
            return publish(entry, output_id, chunks, **options)
        raw = b''.join(chunks)
        assert (len(raw), sha256(raw).hexdigest()) == (
            options['expected_size_bytes'], options['expected_physical_sha256'])
        raise OSError('exposed complete stream publication interruption')
    monkeypatch.setattr(c.store, 'publish_output', interrupted)

    class Connection:
        def __init__(self, service):
            self.service = service

        def send(self, message):
            if type(message) is NativeSubworkRequest:
                self.service.handle(message, self)
            else:
                self.reply = message

        def recv(self):
            return self.reply

    service = NativeSubworkPipeService(c.store, c.context, fixture.tmp_path)
    try:
        with pytest.raises(ValueError, match='publication interruption'):
            execute(c, monkeypatch, literal, progress=PipeNativeSubworkProgress(Connection(service)))
    finally:
        service.close()
    definition, = c.work.definitions
    before = c.store.inspect(definition)
    assert before.call_return is not None and before.receipt is None
    partial, = before.partial_output_records
    assert partial.expected_size_bytes == partial.received_size_bytes > 0
    assert partial.expected_physical_sha256 == partial.received_physical_sha256
    monkeypatch.setattr(native, 'execute_periodic_control', lambda **kwargs: pytest.fail('returned point was replayed'))
    repaired = recover_periodic_control_publication(config=config, definition=definition, native_subwork=c.store)
    assert repaired.partial_output_records == before.partial_output_records and calls == [config.point]
    assert repaired.completion.cost.cpu_seconds is None and repaired.completion.cost.wall_seconds is None
    context = c.fresh_context()
    with completed_native_parent_scope(store=c.store, work=c.work) as (reader, _):
        service = NativeSubworkPipeService(reader, context, fixture.tmp_path, completed_work=c.work)
        try:
            output = owner.PeriodicControlRunner().execute_with_native_subwork(context, PipeNativeSubworkProgress(Connection(service)))
        finally:
            service.close()
    result = decode_canonical_bytes(output.outputs[0].payload, owner.PeriodicProbeResult, maximum_bytes=owner.MAX_RETURN)
    report = retained.read_periodic_control_point(config=config, representation=fixture.model,
        coordinate_bytes=coordinate_bytes, original_result=result, native_subwork=c.store,
        assessor_source=fixture.model.material.sources[0], readout_id='read.exposed.repaired-publication')
    assert report.numerical_integrity.disposition is A.SATISFIED and calls == [config.point]


@pytest.mark.parametrize('variant', ('accurate', 'dense-accurate', 'step-sensitive', 'wrong-gradient', 'missing', 'failed', 'nonfinite', 'comparison-only',
    'refinement-sensitive', 'missing-refinement'))
def test_complete_independent_read_uses_original_arrays_and_preserves_denominators(fixture, monkeypatch, variant):
    configs, raw = configs_for(fixture)
    original = np.frombuffer(raw, dtype='<f8').reshape(83, 3)
    protocol = configs[0].protocol
    if variant == 'dense-accurate':
        protocol = replace(protocol, directions=(selected.PeriodicDerivativeDirection('direction.full',
            'ALL_PHYSICAL_CARTESIAN_SIGNS', sign_seed_sha256='3'*64),))
    if variant != 'comparison-only':
        protocol = replace(protocol, maximum_directional_error_hartree_per_bohr=D('.001') if variant == 'step-sensitive' else D('1e-8'),
            maximum_step_change_hartree_per_bohr=D('1e-8'))
    points = selected.control_points(protocol, raw)
    configs = tuple(owner.PeriodicControlConfig('config.'+point.point_id, fixture.config, protocol, point) for point in points)
    stores, results, calls = {}, [], []
    for config in configs:
        if ((variant == 'missing' and config.point.ordinal == 3)
                or (variant == 'missing-refinement' and config.point.role == 'REFINEMENT')):
            continue
        c = custody(fixture, config)
        def quadratic(**kwargs):
            point = kwargs['point']
            calls.append(point.identity)
            xyz = disclose_point(kwargs)
            (kwargs['directory']/'exposed-control.txt').write_text('EXPOSED QUADRATIC; NO ENZYME\n')
            if variant == 'failed' and point.ordinal == 3:
                raise RuntimeError('original known failed selected point')
            x = (xyz-original)/float(selected.BOHR_ANGSTROM)
            gradient = 2*x+1
            if variant == 'wrong-gradient' and point.ordinal == 0:
                gradient[0, 1] += .1
            if variant == 'nonfinite' and point.ordinal == 3:
                gradient[0, 1] = np.nan
            if variant == 'refinement-sensitive' and point.role == 'REFINEMENT':
                gradient[0, 1] += .1
            energy = float(np.sum(x*x+x))
            if variant == 'step-sensitive':
                energy += float(np.sum(x**3))
                gradient += 3*x*x
            return {'energy_hartree':energy, 'gradient_hartree_per_bohr':gradient}
        result = execute(c, monkeypatch, quadratic)
        stores[result.returned.selection] = c.store
        results.append(result)
    before = len(calls)
    monkeypatch.setattr(native, 'execute_periodic_control', lambda **kwargs:pytest.fail('independent read entered native code'))
    kwargs = dict(configs=configs, representation=fixture.model, coordinate_bytes=raw, original_results=tuple(results),
        native_subwork_for_result=lambda result:stores[result.returned.selection],
        assessor_source=fixture.model.material.sources[0], readout_id='read.exposed.complete-controls')
    report = retained.read_periodic_controls(**kwargs)
    expected = {'accurate':A.SATISFIED, 'dense-accurate':A.SATISFIED,
        'refinement-sensitive':A.SATISFIED, 'missing-refinement':A.SATISFIED,
        'wrong-gradient':A.FALSIFIED, 'step-sensitive':A.FALSIFIED}.get(variant, A.UNEVALUABLE)
    assert report.directional_disposition is expected
    refinement_expected = (A.FALSIFIED if variant in {'wrong-gradient', 'refinement-sensitive'}
        else A.UNEVALUABLE if variant == 'missing-refinement' else A.SATISFIED)
    assert report.refinement_disposition is refinement_expected
    assert report.numerical_disposition is (A.FALSIFIED if A.FALSIFIED in {expected, refinement_expected}
        else A.UNEVALUABLE if A.UNEVALUABLE in {expected, refinement_expected} else A.SATISFIED)
    assert len(report.points) == 6 and len(report.directions) == 2 and len(report.refinements) == 1
    assert len(calls) == before
    if variant == 'missing':
        assert report.points[3].original is None
    elif variant == 'failed':
        assert report.points[3].original.original_result.completion.operational_status is OperationalStatus.FAILED
    elif variant == 'nonfinite':
        assert report.points[3].original.original_result.completion.operational_status is OperationalStatus.SUCCEEDED
        assert report.points[3].original.numerical_integrity.disposition is A.FALSIFIED
    elif variant == 'step-sensitive':
        assert all(row.absolute_error_hartree_per_bohr < D('.001') for row in report.directions)
        assert report.directions[-1].step_change_hartree_per_bohr > D('1e-8')
    else:
        assert all(row.absolute_error_hartree_per_bohr < D('1e-8') for row in report.directions) == (variant != 'wrong-gradient')
    if variant == 'missing-refinement':
        assert report.refinements[0].energy_change_hartree is None
        assert report.refinements[0].maximum_gradient_component_change_hartree_per_bohr is None
    elif variant in {'wrong-gradient', 'refinement-sensitive'}:
        assert report.refinements[0].energy_change_hartree == 0
        assert report.refinements[0].maximum_gradient_component_change_hartree_per_bohr > D('.09')
    else:
        assert report.refinements[0].energy_change_hartree == 0
        assert report.refinements[0].maximum_gradient_component_change_hartree_per_bohr == 0
    assert decode_canonical_bytes(report.canonical_bytes(), retained.PeriodicControlsReadout, maximum_bytes=owner.MAX_RETURN) == report
    with pytest.raises(ValueError, match='repeats or substitutes'):
        retained.read_periodic_controls(**(kwargs|{'original_results':(*results, results[0])}))
    with pytest.raises(ValueError, match='original coordinate bytes'):
        retained.read_periodic_controls(**(kwargs|{'coordinate_bytes':raw[:-1]+bytes([raw[-1]^1])}))


@pytest.mark.parametrize('change', ('coordinates', 'settings', 'source', 'missing-file'))
def test_retained_control_refuses_authentic_but_wrong_actual_numerical_inputs(fixture, monkeypatch, change):
    configs, raw = configs_for(fixture)
    config = configs[1]
    c = custody(fixture, config)
    def wrong_input(**kwargs):
        xyz = disclose_point(kwargs)
        directory = kwargs['directory']
        if change == 'coordinates':
            xyz[0, 1] += .1
            np.save(directory/'coordinate-array.npy', xyz, allow_pickle=False)
        elif change == 'settings':
            (directory/'electronic-settings.json').write_bytes(configs[-1].point.electronic.canonical_bytes())
        elif change == 'source':
            with (directory/'original.inpcrd').open('ab') as stream:
                stream.write(b'\n')
        else:
            (directory/'coordinate-array.npy').unlink()
        return {'energy_hartree':-3.25, 'gradient_hartree_per_bohr':np.zeros((83, 3))}
    result = execute(c, monkeypatch, wrong_input)
    assert result.completion.operational_status is OperationalStatus.SUCCEEDED
    expected = ('successful periodic return omits complete geometry operands' if change == 'missing-file'
                else 'coordinates|input files|inspected member')
    with pytest.raises(ValueError, match=expected):
        retained.read_periodic_control_point(config=config, representation=fixture.model, coordinate_bytes=raw,
            original_result=result, native_subwork=c.store, assessor_source=fixture.model.material.sources[0],
            readout_id='read.exposed.wrong-input')


@pytest.mark.parametrize('ordinal', (0, 1, 5))
@pytest.mark.parametrize('accelerated', (False, True))
def test_actual_control_entry_uses_derived_coordinates_and_exact_untouched_amber_sources(fixture, monkeypatch, ordinal, accelerated):
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_native
    if accelerated:
        from tests.test_rubisco_accelerated_compute import gpu_config
        from tests.test_rubisco_periodic_controls import selected as select
        fixture.config = gpu_config(fixture)
        fixture.selection = fixture.config.selection
        protocol, points, raw = select(fixture)
        config = owner.AcceleratedPeriodicControlConfig('config.'+points[ordinal].point_id, fixture.config, protocol, points[ordinal])
    else:
        configs, raw = configs_for(fixture)
        config = configs[ordinal]
    root = fixture.tmp_path/'entry'
    root.mkdir()
    calls = []
    def record(**kwargs):
        calls.append(kwargs)
        assert kwargs['raw_topology'] == fixture.raw_top and kwargs['raw_coordinates'] == fixture.raw_xyz
        assert kwargs['selection'] == fixture.selection.path and kwargs['cell'] == fixture.selection.cell
        assert kwargs['settings'] == config.point.electronic and kwargs['mm_settings'] == config.point.molecular
        assert kwargs['coordinates'].tobytes() == selected.point_coordinates(config.protocol, config.point, raw).tobytes()
        assert kwargs['coordinate_records'] == (('control-protocol.json', config.protocol), ('control-point.json', config.point))
        assert kwargs['molecular_precision_control'] is (accelerated and ordinal == 0)
        return 'EXPOSED_CAPTURE_OF_ACTUAL_NATIVE_ENTRY_ARGUMENTS'
    monkeypatch.setattr(periodic_probe_native, '_execute_periodic_at_coordinates', record)
    assert native.execute_periodic_control(prototype=fixture.selection, protocol=config.protocol, point=config.point,
        representation=fixture.model, sources=fixture.sources, directory=root) == 'EXPOSED_CAPTURE_OF_ACTUAL_NATIVE_ENTRY_ARGUMENTS'
    assert len(calls) == 1 and not tuple(root.iterdir())
    with pytest.raises(ValueError, match='original selected Amber bytes'):
        native.execute_periodic_control(prototype=fixture.selection, protocol=config.protocol, point=config.point,
            representation=fixture.model, sources=replace(fixture.sources, coordinates_utf8=fixture.sources.coordinates_utf8+'\n'),
            directory=root)
    assert len(calls) == 1


def test_molecular_precision_public_read_authenticates_original_archive_without_replay(fixture, monkeypatch):
    import json
    from empirical_lawhood.api.domain_composition.rubisco_response.periodic_controls import read_periodic_molecular_precision
    from tests.test_rubisco_accelerated_compute import gpu_config
    from tests.test_rubisco_accelerated_traces import apparatus, cost
    from tests.test_rubisco_periodic_controls import selected as select
    from empirical_lawhood.adapters.rubisco.rubisco_response import gpu_periodic_backend
    monkeypatch.setattr(gpu_periodic_backend, 'preflight_gpu_backend', lambda **kwargs:None)
    fixture.config = gpu_config(fixture)
    fixture.selection = fixture.config.selection
    protocol, points, raw = select(fixture)
    config = owner.AcceleratedPeriodicControlConfig('config.'+points[0].point_id, fixture.config, protocol, points[0])
    c = custody(fixture, config)
    def original(**kwargs):
        directory = kwargs['directory']
        disclose_point(kwargs)
        request = dict(version='1.0.0', physical_atom_count=83, coordinate_sha256=points[0].coordinate_sha256,
            remainder_parameter_sha256='b'*64, cuda_properties={'Precision':'double','DeviceIndex':'0','DeterministicForces':'true'},
            scope='SAME_GEOMETRY_COMPLETE_MM_CUDA_REFERENCE', electronic_evaluations=0, matched_pme=[4.5,32,32,32])
        request_bytes = json.dumps(request).encode()
        (directory/'mm-precision-request.json').write_bytes(request_bytes)
        (directory/'mm-precision-completion.json').write_text(json.dumps(dict(version='1.0.0',
            request_sha256=sha256(request_bytes).hexdigest(), platforms=['CUDA','Reference'],
            completed_mm_evaluations=2, electronic_evaluations=0, original_system_unchanged=True,
            wall_seconds={'cuda':1.,'reference':2.})))
        (directory/'coupling-audit.json').write_text(json.dumps(dict(remainder=dict(remainder_parameter_sha256='b'*64))))
        for platform in ('cuda','reference'):
            np.save(directory/('mm-precision-'+platform+'-energy-kj-mol.npy'), np.array(2. if platform=='cuda' else 1.))
            np.save(directory/('mm-precision-'+platform+'-forces-kj-mol-nm.npy'), np.zeros((83,3)))
        rows = apparatus(fixture.selection.engine.device_memory_bytes)+[
            dict(event='entry',evaluation=1),cost(1),dict(event='return',evaluation=1)]
        (directory/'native-observations.jsonl').write_text('\n'.join(json.dumps(row) for row in rows))
        return {'energy_hartree':-3.25, 'gradient_hartree_per_bohr':np.zeros((83,3))}
    result = execute(c, monkeypatch, original)
    monkeypatch.setattr(native, 'execute_periodic_control', lambda **kwargs:pytest.fail('precision reader replayed native work'))
    report = read_periodic_molecular_precision(config=config, representation=fixture.model,
        coordinate_bytes=raw, original_result=result, native_subwork=c.store,
        assessor_source=fixture.model.material.sources[0], readout_id='read.exposed.mm-precision')
    assert report['energy_change_kj_mol'] == 1 and report['maximum_force_change_kj_mol_nm'] == 0
    assert report['new_native_calls'] == 0 and report['original_completion_sha256'] == result.completion.fingerprint()


def test_public_author_streams_shared_inputs_once_and_every_prospective_point(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import periodic_controls as public

    configs, _ = configs_for(fixture)
    plane = probe._plane(fixture.tmp_path/'public-custody')
    project = fixture.tmp_path/'project'
    project.mkdir()
    destination = Path(plane.root.contract.canonical_path)/'authored'
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda root:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **kwargs:fixture.config.provenance)
    observed = []
    def author(**kwargs):
        observed.append(kwargs)
        assert len(kwargs['draft'].operations) == 6
        assert len(kwargs['input_bindings']) == len(kwargs['draft'].external_inputs) == 18
        for key, path in kwargs['input_bindings']:
            selected_input = next(row for row in kwargs['draft'].external_inputs if row.input_id == key)
            manifest = resolve_artifact_sidecar_bytes(plane, path.with_name(path.name + '.manifest.json').read_bytes())
            plane.verify_manifest(manifest)
            raw = path.read_bytes()
            assert len(raw) == manifest.materialization.size_bytes == selected_input.maximum_size_bytes
            assert sha256(raw).hexdigest() == manifest.logical.content_sha256 == selected_input.expected_content_sha256
        return {'scope':'EXPOSED_SHARED_AUTHOR_STUB'}
    monkeypatch.setattr(recursive_authoring, 'author_recursive_wave', author)
    result = public.author_periodic_numerical_controls(protocol=configs[0].protocol, prototype=fixture.selection,
        representation=fixture.model, raw_topology=fixture.raw_top, raw_coordinates=fixture.raw_xyz,
        project_root=project, work_directory=fixture.workdir, artifact_writer=plane, output_dir=destination)
    assert len(observed) == 1 and len(result['point_ids']) == 6 and len(result['native_input_paths']) == 18
    assert not fixture.workdir.exists()
