# SPDX-License-Identifier: MPL-2.0
"""Exposed restart identity, binary transport and original-attempt custody."""

from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

import empirical_lawhood.domains.rubisco.rubisco_response.periodic_density_seed as selected_owner_0
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_translation as graph
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import prepare_periodic_probe_selection
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.native_subwork import NativeSubworkState
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests import test_rubisco_periodic_probe_operation as probe
from tests.runtime_platform.test_native_subwork import _plane


fixture = probe.fixture


def restart(fixture):
    """Synthetic custody only. This literal density is not electronic evidence."""
    source = probe.custody(fixture, custody_name='source-custody')
    original = fixture.config
    density = np.eye(4, dtype='<f8').tobytes()
    digest = sha256(density).hexdigest()
    definition = source.work.definitions[0]
    arrays = ArrayDatasetManifest('arrays.exposed-density', (ArrayDatasetMember('initial-density', '<f8', (4, 4), digest),),
        tuple(sorted({original.selection.identity, original.identity, definition.identity}, key=lambda row:row.object_id)))
    seed = selected_owner_0.PeriodicDensitySeed('seed.exposed-density', original.identity, original.selection,
        original.provenance, definition, FileEvidence('exposed.h5', 10, '7'*64), D('-1'), '8'*64, arrays,
        ObjectIdentity('bytes.exposed-density', selected_owner_0.DENSITY_SCHEMA, '1.0.0', digest))
    values = {field.name:getattr(original, field.name) for field in fields(owner.PeriodicProbeConfig)}
    values.update(config_id='config.exposed-restart', selection=owner.restart_selection(seed, original.selection),
        work_directory=str(fixture.tmp_path/'restart-working'), seed=seed)
    return owner.PeriodicRestartConfig(**values), density, source


def compile_selected(config, draft=None):
    declaration = owner.operation_declaration(restart=True)
    return compile_recursive_wave(draft=draft or graph.periodic_probe_draft(config),
        registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed-restart', (declaration.manifest(),)),
        implementation_commit=config.implementation.observed_git_head, output_codecs=declaration.record_codecs)


def test_new_request_is_distinct_and_original_canonical_contract_is_preserved(fixture):
    original_bytes = fixture.config.canonical_bytes()
    config, raw, source = restart(fixture)
    assert config.canonical_bytes() != original_bytes and fixture.config.canonical_bytes() == original_bytes
    assert owner.selected_request(config).identity != owner.selected_request(fixture.config).identity
    assert config.seed.source_definition == source.work.definitions[0]
    assert config.seed.identity in config.selection.probe.sources
    assert config.seed.density_bytes in owner.operands(config)
    assert decode_canonical_bytes(config.canonical_bytes(), owner.PeriodicRestartConfig, maximum_bytes=owner.MAX_CONFIG) == config
    density = selected_owner_0.read_density_bytes(config.seed, raw)
    assert not density.flags.writeable and np.shares_memory(density, np.frombuffer(raw, dtype='<f8'))
    compiled = compile_selected(config)
    assert compiled.proof is not None and len(compiled.execution_plan.tasks) == 1
    task = compiled.execution_plan.tasks[0]
    assert task.capability.capability_key == owner.RESTART_CAPABILITY
    assert task.maximum_attempts == 1 and task.capability.requested_resources == owner.BUDGET
    assert owner.BUDGET.wall_time_seconds is None and len(graph.native_external_inputs(config)) == 8
    assert not Path(config.work_directory).exists()


@pytest.mark.parametrize('change', ['density-hash', 'density-size', 'density-link', 'seed-link', 'claim'])
def test_compiler_refuses_changed_restart_inputs_and_scope(fixture, change):
    config, _, _ = restart(fixture)
    draft = graph.periodic_probe_draft(config)
    if change == 'claim':
        draft = replace(draft, development_study=replace(draft.development_study, question='The original attempt completed'))
    elif change.endswith('link'):
        name = 'native-density' if change == 'density-link' else 'native-seed'
        draft = replace(draft, links=tuple(row for row in draft.links if row.external_input_id != 'external.periodic-force.'+name))
    else:
        changes = {'expected_content_sha256':'0'*64} if change == 'density-hash' else {'maximum_size_bytes':64}
        draft = replace(draft, external_inputs=tuple(replace(row, **changes) if row.input_id.endswith('.native-density') else row
            for row in draft.external_inputs))
    with pytest.raises(ValueError):
        compile_selected(config, draft)


@pytest.mark.parametrize('change', ['basis', 'charge', 'coordinates', 'mm-settings', 'engine-stock'])
def test_restart_refuses_changes_to_physical_and_numerical_context(fixture, change):
    config, _, _ = restart(fixture)
    prototype = fixture.selection
    if change == 'coordinates':
        coordinates = replace(prototype.coordinates, members=(replace(prototype.coordinates.members[0], sha256='0'*64),))
        other = replace(prototype, coordinates=coordinates,
            sources=tuple(sorted((set(prototype.sources)-{prototype.coordinates.identity})|{coordinates.identity}, key=lambda row:row.object_id)))
    else:
        values = dict(representation=fixture.model, path=prototype.path, cell=prototype.cell,
            electronic=prototype.electronic, molecular=prototype.molecular, engine=prototype.engine)
        if change == 'basis':
            values['electronic'] = replace(prototype.electronic, basis='def2-tzvpd')
        elif change == 'charge':
            values['path'] = replace(prototype.path, qm_formal_charge=prototype.path.qm_formal_charge+2)
        elif change == 'mm-settings':
            values['molecular'] = replace(prototype.molecular, ewald_relative_tolerance=D('1e-7'))
        else:
            values['engine'] = replace(prototype.engine, interpreter_sha256='0'*64)
        other = prepare_periodic_probe_selection(**values)
    with pytest.raises(ValueError, match='changed'):
        owner.restart_selection(config.seed, other)


def test_thread_selection_may_change_within_the_existing_allocation(fixture):
    config, _, _ = restart(fixture)
    prototype = fixture.selection
    engine = replace(prototype.engine, numerical_threads=8)
    other = prepare_periodic_probe_selection(representation=fixture.model, path=prototype.path, cell=prototype.cell,
        electronic=prototype.electronic, molecular=prototype.molecular, engine=engine)
    selected_prototype = owner.restart_selection(config.seed, other)
    changed = replace(config, selection=selected_prototype)
    assert changed.selection.engine.numerical_threads == 8
    assert owner.selected_request(changed).identity != owner.selected_request(config).identity
    with pytest.raises(ValueError, match='CPU allocation'):
        replace(changed, selection=replace(selected_prototype, engine=replace(engine, numerical_threads=9),
            sources=tuple(sorted((set(selected_prototype.sources)-{engine.identity})|{replace(engine, numerical_threads=9).identity}, key=lambda row:row.object_id))))


@pytest.mark.parametrize('change', ['truncated', 'changed', 'nan', 'asymmetric'])
def test_changed_or_invalid_density_refuses(fixture, change):
    config, raw, _ = restart(fixture)
    seed = config.seed
    if change == 'truncated':
        raw = raw[:-8]
    elif change == 'changed':
        raw = raw[:-1]+b'\xff'
    else:
        value = np.eye(4, dtype='<f8')
        value[0, 1] = np.nan if change == 'nan' else .1
        raw = value.tobytes()
        digest = sha256(raw).hexdigest()
        seed = replace(seed, arrays=replace(seed.arrays, members=(replace(seed.arrays.members[0], sha256=digest),)),
            density_bytes=replace(seed.density_bytes, object_fingerprint=digest))
    with pytest.raises(ValueError):
        selected_owner_0.read_density_bytes(seed, raw)


def test_source_attempt_and_seed_cannot_be_relabelled_as_completed(fixture):
    config, _, _ = restart(fixture)
    for changes in ({'scope':'CONVERGED_ORIGINAL_COMPLETION'}, {'source_configuration':fixture.model.identity},
            {'source_definition':replace(config.seed.source_definition, code_sources_sha256='0'*64)}):
        with pytest.raises(ValueError):
            replace(config.seed, **changes)


@pytest.mark.parametrize('failed', [False, True])
def test_distinct_restart_retains_original_unknown_contact_and_does_not_replay(fixture, monkeypatch, failed):
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry, retain_exposed_source_coordinates
    install_exposed_geometry(monkeypatch)
    config, raw, source = restart(fixture)
    source.store.freeze_roster(source.work.rosters[0], definitions=source.work.definitions)
    original_entry = source.store.begin(source.work.definitions[0])
    source.store.contact(original_entry)
    fixture.config = config
    current = probe.custody(fixture, custody_name='restart-custody', density_bytes=raw)
    assert len(current.manifests) == 9
    assert current.work.definitions[0].identity != source.work.definitions[0].identity
    assert config.seed.density_bytes in current.work.definitions[0].sources
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k:())
    calls = []
    def invoke(**kwargs):
        calls.append(kwargs)
        retain_exposed_source_coordinates(kwargs)
        assert kwargs['density_seed'] == config.seed and kwargs['density_bytes'] == raw
        (kwargs['directory']/'initial-density-seed.json').write_bytes(config.seed.canonical_bytes())
        (kwargs['directory']/'initial-density.bin').write_bytes(raw)
        if failed:
            raise ArithmeticError('exposed seeded solver failure')
        return dict(energy_hartree=-2.25, gradient_hartree_per_bohr=np.arange(249, dtype=float).reshape((83, 3)))
    monkeypatch.setattr(native, 'execute_periodic_probe', invoke)
    runner = owner.PeriodicRestartRunner()
    product = runner.execute_with_native_subwork(current.context, current.store)
    result = decode_canonical_bytes(product.outputs[0].payload, owner.PeriodicProbeResult, maximum_bytes=owner.MAX_RETURN)
    assert len(calls) == 1
    assert result.completion.operational_status is (OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED)
    monkeypatch.setattr(native, 'execute_periodic_probe', lambda **k:pytest.fail('completed restart was repeated'))
    assert runner.execute_with_native_subwork(current.fresh_context(), current.store).outputs[0].payload == product.outputs[0].payload
    report = retained.read_periodic_probe(config=config, representation=fixture.model, original_result=result,
        native_subwork=current.store, assessor_source=fixture.model.material.sources[0], readout_id='readout.exposed-restart')
    assert report.numerical_integrity is None if failed else report.numerical_integrity.disposition == 'SATISFIED'
    assert source.store.inspect(source.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION
    with pytest.raises(ValueError, match='contacted without exact receipt'):
        source.store.recover(source.work.definitions[0])


def test_unknown_restart_contact_also_refuses_reentry(fixture, monkeypatch):
    config, raw, _ = restart(fixture)
    fixture.config = config
    current = probe.custody(fixture, custody_name='restart-custody', density_bytes=raw)
    current.store.freeze_roster(current.work.rosters[0], definitions=current.work.definitions)
    entry = current.store.begin(current.work.definitions[0])
    current.store.contact(entry)
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *a, **k:())
    monkeypatch.setattr(native, 'execute_periodic_probe', lambda **k:pytest.fail('uncertain restart contact repeated'))
    with pytest.raises(ValueError, match='contacted without exact receipt'):
        owner.PeriodicRestartRunner().execute_with_native_subwork(current.context, current.store)
    assert current.store.inspect(current.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION


def test_public_author_streams_binary_seed_with_all_original_inputs(fixture, monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import periodic_probe as public
    config, raw, _ = restart(fixture)
    plane = _plane(fixture.tmp_path/'public-custody', binary_codecs=(owner.DENSITY_CODEC,))
    project = fixture.tmp_path/'project'
    project.mkdir()
    destination = Path(plane.root.contract.canonical_path)/'authored'
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda root:config.implementation)
    monkeypatch.setattr(numerical_provenance, 'capture_numerical_provenance', lambda **kwargs:config.provenance)
    observed = []
    def author(**kwargs):
        observed.append(kwargs)
        assert len(kwargs['input_bindings']) == len(kwargs['draft'].external_inputs) == 8
        for identity, path in kwargs['input_bindings']:
            row = next(row for row in kwargs['draft'].external_inputs if row.input_id == identity)
            assert sha256(path.read_bytes()).hexdigest() == row.expected_content_sha256
            assert path.stat().st_size == row.maximum_size_bytes
        assert dict(kwargs['input_bindings'])['external.periodic-force.native-density'].read_bytes() == raw
        compiled_config = decode_canonical_bytes(kwargs['draft'].operations[0].config_payload.encode(),
            owner.PeriodicRestartConfig, maximum_bytes=owner.MAX_CONFIG)
        assert compiled_config.seed == config.seed
        return {'scope':'EXPOSED_SHARED_AUTHOR_CONTROL'}
    monkeypatch.setattr(recursive_authoring, 'author_recursive_wave', author)
    result = public.author_periodic_force_restart(prototype=fixture.selection, seed=config.seed, density_bytes=raw,
        representation=fixture.model, raw_topology=fixture.raw_top, raw_coordinates=fixture.raw_xyz,
        project_root=project, work_directory=Path(config.work_directory), artifact_writer=plane, output_dir=destination)
    assert len(observed) == 1 and len(result['native_input_paths']) == 8
    assert not Path(config.work_directory).exists()
