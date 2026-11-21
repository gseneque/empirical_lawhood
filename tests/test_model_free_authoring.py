# SPDX-License-Identifier: MPL-2.0
"""Synthetic parent-authority and exact-retained-byte authoring controls.

Mocks disclose an authenticated-parent boundary for software tests only. They
do not authenticate real evidence or grant scientific freshness authority.
"""
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import model_free_matrix as api
from empirical_lawhood.domains.matrix.classical_series.arrays import decode_acquisition, encode_acquisition, iter_encoded_bytes
from empirical_lawhood.domains.matrix.model_free import design, experiment
from empirical_lawhood.domains.matrix.model_free.bindings import calculate
from empirical_lawhood.domains.matrix.model_free.records import Product, RootAssignment, Specification, json_text
from empirical_lawhood.domains.matrix.model_free.science import normalise_settings
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


def parent_fixture(tmp_path, monkeypatch, *, parent=None, acquired_payload=None):
    if parent is None:
        settings = normalise_settings({})
        parent = api.specification_for('Disclosed synthetic original source',
            (RootAssignment(10, ('M0',)), RootAssignment(11, ('M0',)), RootAssignment(20, ('M2',))), settings)
    records, outputs, raw_arrays = {}, {}, {}
    parent_dir = tmp_path / 'parent'
    parent_dir.mkdir()
    for config in design.configs_for(parent):
        if config.phase == 'analyse':
            continue
        payload = {'schema': 'matrix-model-free-' + ('acquisition' if config.phase == 'acquire' else 'synthesis') + '.v1',
                   'module': config.module, 'cases': [{'declared_array': [float(i) for i in range(10)]}]}
        if config.phase == 'acquire':
            payload['seed'] = config.assignments[0].seed
            if acquired_payload is not None:
                payload = acquired_payload
        product = Product(config.node_id + '.product', config, json_text(payload))
        if config.phase == 'acquire':
            product, leaves = encode_acquisition(product, artifact_id=config.node_id + '.arrays')
            raw = b''.join(iter_encoded_bytes(product, leaves))
            identity = product.array_artifact
            filename = identity.artifact_id + '.bin'
            (parent_dir / filename).write_bytes(raw)
            raw_arrays[identity.artifact_id] = raw
            outputs[identity.artifact_id] = SimpleNamespace(
                logical=SimpleNamespace(logical_artifact_id=identity.artifact_id, content_sha256=identity.sha256,
                    payload_schema=identity.payload_schema, media_type=identity.media_type),
                materialization=SimpleNamespace(size_bytes=len(raw), physical_sha256=identity.sha256, relative_path=filename))
        records[config.node_id] = {product.record_id: product}
    state = {'active': False, 'guards': 0, 'reads': 0, 'refuse_final': False}
    def guard():
        assert state['active'], 'native bytes escaped their parent verification lifetime'
        state['guards'] += 1
    writer = SimpleNamespace(root=SimpleNamespace(resolve=lambda relative, for_write=False: parent_dir / relative),
                             require_verification_snapshot=guard)
    products = {'records': records, 'outputs': outputs}
    report = {'packet_sha256': 'a' * 64, 'execution_plan_sha256': 'b' * 64, 'producing_code_sha256': 'c' * 64}
    result = {'scientific_completion': 'COMPLETED', 'qualification': 'NOT_ESTABLISHED'}
    payloads = {'experiment-specification.json': parent.canonical_bytes()}
    def reader(parent_directory, parent_service, consumer):
        state['active'], state['reads'] = True, state['reads'] + 1
        try:
            consumer(result=result, payloads=payloads, products=products, artifact_writer=writer, report=report)
            if state['refuse_final']:
                raise PermissionError('synthetic final source revalidation refused')
        finally:
            state['active'] = False
    monkeypatch.setattr(api, '_read_parent', reader)
    from empirical_lawhood.api import recursive_authoring
    source = ObjectIdentity('source.disclosed-fixture', 'empirical-lawhood/test/source', '1.0.0', 'f' * 64)
    monkeypatch.setattr(recursive_authoring, 'implementation_binding', lambda project_root: source)
    from empirical_lawhood.domains.matrix.model_free import science
    monkeypatch.setattr(science, 'acquire_root', lambda *args, **kwargs: pytest.fail('authoring reacquired native work'))
    return SimpleNamespace(parent=parent, products=products, report=report, result=result, state=state,
        service=SimpleNamespace(artifact_writer=writer), parent_dir=parent_dir, raw_arrays=raw_arrays)


def definition(tmp_path, roots, settings, *, name='definition.json'):
    path = tmp_path / name
    path.write_text(json.dumps({'schema': api.DEFINITION_SCHEMA, 'label': 'Disclosed software successor',
        'roots': [{'seed': seed, 'modules': list(modules), 'role': role} for seed, modules, role in roots],
        'settings': settings}))
    return path


def decoded(path):
    return decode_canonical_bytes(path.read_bytes(), Specification, maximum_bytes=None)


def confirmation_settings(fixture):
    """Disclosed decisions and measured-parent seam for software tests only."""
    return normalise_settings({'evidence_scope': 'FRESH_CONFIRMATION',
        'resources': {'memory_bytes': 1024 ** 3, 'wall_time_seconds': 120, 'output_bytes': 1024 ** 2},
        'confirmation': {
            'endpoints': [{'name': 'M0.control_law_consistency', 'practical_effect': '0.1', 'units': 'dimensionless'}],
            'population_target': 'COMPLETE_ASSIGNED_ROOT_POPULATION', 'target_law': 'DECLARED_FINITE_AGE_ROOT_LAW',
            'precision_goal': 'DETECTION_ONLY', 'stopping_rule': 'FIXED_ROOT_CENSUS_AND_PREDECLARED_RECORD_LADDER',
            'independent_verification': ['COMPLETE_ASSIGNED_AND_FAILED_ROOT_CENSUS', 'INDEPENDENT_ANALYSIS_OPERATION'],
            'parent_readout_sha256': sha256(json_text(fixture.result).encode()).hexdigest(),
            'capacity_basis': 'AUTHENTICATED_PARENT_AND_OPERATOR_MEASURED_HOST'}})


def test_confirmation_lineage_is_immutable_and_changes_every_operation_identity(tmp_path, monkeypatch):
    fixture = parent_fixture(tmp_path, monkeypatch)
    settings = confirmation_settings(fixture)
    path = definition(tmp_path, [(100, ('M0',), 'confirmation')], settings)
    destination = tmp_path / 'confirmation'
    result = api.create_successor_inputs(definition_path=path, project_root=tmp_path, output_directory=destination,
        parent_directory=fixture.parent_dir, parent_service=fixture.service)
    successor = decoded(destination / 'specification.json')
    lineage = successor.parent_lineage
    assert fixture.state['reads'] == 1
    assert lineage.parent_specification == fixture.parent.identity
    assert lineage.exposed_seeds == (10, 11, 20)
    assert len(lineage.parent_summaries) == 2
    assert lineage.parent_execution_plan_sha256 == fixture.report['execution_plan_sha256']
    assert lineage.frozen_settings_sha256 == sha256(successor.settings_json.encode()).hexdigest()
    assert result['native_acquisition_performed'] is False
    assert successor.assignments[0].role == 'confirmation'
    assert result['evidence_scope'] == 'PREDECLARED_DEVELOPMENT'
    assert result['declared_population_scope'] == 'FRESH_CONFIRMATION'
    assert result['freshness_claim'] == 'DISJOINT_FROM_DECLARED_PARENT_EXPOSURE'
    assert result['parent_authentication_performed'] is True
    assert result['parent_authentication_time_scope'] == 'THIS_PUBLIC_AUTHORING_INVOCATION_ONLY'
    assert 'DECLARED_LINEAGE_ALONE_IS_NOT_AUTHORITY' in result['parent_authentication_scope']
    assert result['framework_evidence_ceiling'] == 'NON_PROMOTABLE'
    assert not result['global_freshness_established'] and not result['outcome_blind_authority_granted']
    assert successor.settings == normalise_settings(settings)
    changed_settings = normalise_settings(settings)
    changed_settings['response']['minimum_signal'] = '0.002'
    with pytest.raises(ValueError, match='cutoff'):
        replace(successor, settings_json=json_text(changed_settings))
    changed = replace(lineage, parent_readout_sha256='e' * 64)
    different = api.specification_for(successor.study_label, successor.assignments, settings, parent_lineage=changed)
    assert different.fingerprint() != successor.fingerprint()
    assert not {c.node_id for c in design.configs_for(different)} & {c.node_id for c in design.configs_for(successor)}
    # Declaration remains the exposed numerical lifecycle, not a fabricated
    # outcome-blind or molecular qualification authority.
    assert design.scientific_root(successor).access_pair == (design.ACCESS, design.VISIBILITY)


def test_confirmation_cannot_bypass_parent_or_reuse_exposed_roots(tmp_path, monkeypatch):
    fixture = parent_fixture(tmp_path, monkeypatch)
    settings = confirmation_settings(fixture)
    with pytest.raises(ValueError, match='parent lineage'):
        api.specification_for('Missing parent', (RootAssignment(100, ('M0',), 'confirmation'),), settings)
    path = definition(tmp_path, [(10, ('M0',), 'confirmation')], settings)
    with pytest.raises(ValueError, match='exposed development roots'):
        api.create_successor_inputs(definition_path=path, project_root=tmp_path, output_directory=tmp_path / 'invalid',
            parent_directory=fixture.parent_dir, parent_service=fixture.service)
    assert not (tmp_path / 'invalid').exists()
    with pytest.raises(ValueError, match='create_successor_inputs'):
        api.create_inputs(definition_path=path, project_root=tmp_path, output_directory=tmp_path / 'bypass')


def test_final_parent_refusal_never_publishes_a_confirmation(tmp_path, monkeypatch):
    fixture = parent_fixture(tmp_path, monkeypatch)
    fixture.state['refuse_final'] = True
    settings = confirmation_settings(fixture)
    path = definition(tmp_path, [(100, ('M0',), 'confirmation')], settings)
    with pytest.raises(PermissionError, match='final source'):
        api.create_successor_inputs(definition_path=path, project_root=tmp_path, output_directory=tmp_path / 'invalid',
            parent_directory=fixture.parent_dir, parent_service=fixture.service)
    assert not (tmp_path / 'invalid').exists()


def test_final_parent_refusal_leaves_no_executable_reanalysis_selection(tmp_path, monkeypatch):
    fixture = parent_fixture(tmp_path, monkeypatch)
    fixture.state['refuse_final'] = True
    path = definition(tmp_path, [(10, ('M0',), 'development'), (11, ('M0',), 'development')], fixture.parent.settings)
    destination = tmp_path / 'refused-reanalysis'
    with pytest.raises(PermissionError, match='final source'):
        api.create_reanalysis_inputs(definition_path=path, project_root=tmp_path, output_directory=destination,
            parent_directory=fixture.parent_dir, parent_service=fixture.service)
    assert destination.exists() and list(destination.glob('arrays.*.bin'))
    assert not (destination / 'specification.json').exists()
    assert not (destination / 'sources.json').exists()
    assert not fixture.state['active']


def test_narrow_reanalysis_streams_original_arrays_inside_guard_and_retains_census(tmp_path, monkeypatch):
    fixture = parent_fixture(tmp_path, monkeypatch)
    path = definition(tmp_path, [(10, ('M0',), 'development'), (11, ('M0',), 'development')], fixture.parent.settings)
    destination = tmp_path / 'reanalysis'
    api.create_reanalysis_inputs(definition_path=path, project_root=tmp_path, output_directory=destination,
        parent_directory=fixture.parent_dir, parent_service=fixture.service)
    specification = decoded(destination / 'specification.json')
    assert fixture.state['guards'] >= 4 and not fixture.state['active']
    assert {c.phase for c in design.configs_for(specification)} == {'analyse', 'synthesise'}
    assert specification.parent_lineage.parent_assignments == fixture.parent.assignments
    assert specification.parent_lineage.parent_specification == fixture.parent.identity
    assert [r.seed for r in specification.assignments] == [10, 11]
    for row in specification.retained_arrays:
        assert (destination / (row.key + '.bin')).read_bytes() == fixture.raw_arrays[row.identity.artifact_id]
    sources = {row.key: decode_canonical_bytes((destination / (row.key + '.json')).read_bytes(), Product, maximum_bytes=None)
               for row in specification.retained_inputs}
    experiment.bind_inputs(specification, sources)


def test_reanalysis_cannot_select_away_a_failed_or_unwanted_root(tmp_path, monkeypatch):
    fixture = parent_fixture(tmp_path, monkeypatch)
    path = definition(tmp_path, [(10, ('M0',), 'development')], fixture.parent.settings)
    with pytest.raises(ValueError, match='discard assigned'):
        api.create_reanalysis_inputs(definition_path=path, project_root=tmp_path, output_directory=tmp_path / 'invalid',
            parent_directory=fixture.parent_dir, parent_service=fixture.service)
    assert not (tmp_path / 'invalid').exists()


def test_reanalysis_retains_confirmation_role_without_renewing_freshness(tmp_path, monkeypatch):
    development = parent_fixture(tmp_path, monkeypatch)
    settings = confirmation_settings(development)
    roots = [(100, ('M0',), 'confirmation'), (101, ('M0',), 'confirmation')]
    path = definition(tmp_path, roots, settings)
    api.create_successor_inputs(definition_path=path, project_root=tmp_path,
        output_directory=tmp_path / 'confirmation-inputs', parent_directory=development.parent_dir,
        parent_service=development.service)
    confirmation = decoded(tmp_path / 'confirmation-inputs' / 'specification.json')
    replay = tmp_path / 'replay'
    replay.mkdir()
    retained = parent_fixture(replay, monkeypatch, parent=confirmation)
    path = definition(replay, roots, settings)
    destination = replay / 'reanalysis'
    authored = api.create_reanalysis_inputs(definition_path=path, project_root=tmp_path,
        output_directory=destination, parent_directory=retained.parent_dir, parent_service=retained.service)
    specification = decoded(destination / 'specification.json')
    assert specification.assignments == confirmation.assignments
    assert specification.parent_lineage.parent_specification == confirmation.identity
    assert specification.parent_lineage.exposed_seeds == (10, 11, 20, 100, 101)
    assert authored['evidence_scope'] == 'EXPOSED_REANALYSIS'
    assert authored['declared_population_scope'] == 'FRESH_CONFIRMATION'
    assert authored['population_role'] == 'confirmation'
    assert authored['freshness_claim'] == 'EXPOSED_REANALYSIS'
    configs = design.configs_for(specification)
    readout = api.read_result(directory=destination, artifact_writer=retained.service.artifact_writer,
        specification=specification, instance=SimpleNamespace(specification=specification.identity),
        payloads={}, report={'run_id': 'run.disclosed'}, products={}, draft=None,
        plan=SimpleNamespace(tasks=[SimpleNamespace(task_id=c.node_id) for c in configs],
            source_plan=SimpleNamespace(object_id='run.disclosed')), allow_partial=True)
    assert readout['freshness_claim'] == 'EXPOSED_REANALYSIS'
    assert readout['scientific_completion'] == 'DEFERRED'
    assert readout['population_role'] == 'confirmation'
    assert readout['information_cutoff'] == 'DECLARED_PARENT_IDENTITIES_BOUND_IN_SPECIFICATION'
    assert 'parent_authentication_performed' not in readout


def test_m2_rebin_and_history_override_reuses_exact_original_arrays(tmp_path, monkeypatch):
    from empirical_lawhood.domains.matrix.model_free.science import settings_fingerprint
    original = normalise_settings({'memory': {'record_ticks': 16, 'record_length_ladder': [16],
        'lags': [1, 2], 'checkpoint_ticks': [0, 8, 16], 'history_orders': [1], 'observation_dimensions': [1]}})
    parent = api.specification_for('Disclosed retained-array numerical control', (RootAssignment(20, ('M2',)),), original)
    payload = {'schema': 'matrix-model-free-acquisition.v1', 'module': 'M2', 'seed': 20,
        'settings_sha256': settings_fingerprint(original), 'independent_units': 1,
        'status': 'COMPLETED', 'assigned_case_count': len(original['native']['coordinates']),
        'acquisition_seconds': 0., 'evidence_scope': 'EXPOSED_DEVELOPMENT',
        'work_accounting': {'native_force_evaluations': 0, 'native_hessian_actions': 0,
            'native_energy_evaluations': 0, 'wall_seconds': 0., 'counts_are_lower_bounds': False},
        'cases': [{'coordinate': coordinate, 'status': 'COMPLETED',
            'observables': [[(i - 8) / 8, float((-1) ** i), i / 2] for i in range(17)],
            'energies': [1.] * 17, 'physical_timestep': float(original['native']['timestep']),
            'scope': 'DISCLOSED_SYNTHETIC_FINITE_AGE_CONTROL', 'momentum_reset_controls': [],
            'observation': {'direction': 'synthetic fixed chart'}, 'native_force_evaluations': 0}
            for coordinate in original['native']['coordinates']]}
    fixture = parent_fixture(tmp_path, monkeypatch, parent=parent, acquired_payload=payload)
    changed = normalise_settings(original)
    changed['alpha'] = '0.025'
    changed['memory'].update(lags=[1, 3], history_orders=[1, 2], bin_edges=[[-10., -.25, .25, 10.], [-10., 0., 10.], [-100., 0., 100.]])
    path = definition(tmp_path, [(20, ('M2',), 'development')], changed)
    destination = tmp_path / 'rebinned'
    api.create_reanalysis_inputs(definition_path=path, project_root=tmp_path, output_directory=destination,
        parent_directory=fixture.parent_dir, parent_service=fixture.service)
    specification = decoded(destination / 'specification.json')
    assert {c.phase for c in design.configs_for(specification)} == {'analyse', 'synthesise'}
    retained = specification.retained_inputs[0]
    product = decode_canonical_bytes((destination / (retained.key + '.json')).read_bytes(), Product, maximum_bytes=None)
    assert product.config.settings == original and product.config.specification == parent.identity
    binary = (destination / ('arrays.' + retained.key + '.bin')).read_bytes()
    assert binary == fixture.raw_arrays[product.array_artifact.artifact_id]
    acquired = decode_acquisition(product, BytesIO(binary))
    immutable = json_text(acquired)
    config = next(c for c in design.configs_for(specification) if c.phase == 'analyse')
    result = calculate(config, (product,), acquired_payloads={product.identity.object_fingerprint: acquired})
    assert json_text(acquired) == immutable
    assert result.payload['settings_sha256'] == settings_fingerprint(changed)
    assert result.payload['retained_acquisition_settings_sha256'] == settings_fingerprint(original)
    assert result.payload['analysis_settings_changed'] is True
    assert result.payload['assessment_exposure'] == 'EXPOSED_REANALYSIS'
    observations = result.payload['cases'][0]['observations']
    assert {x['history_order'] for x in observations} == {1, 2}
    assert all(set(x['counts']['lags']) == {'1', '3'} for x in observations)
    assert all(x['counts']['alphabet_size'] == 3 for x in observations)
    summary_config = next(c for c in design.configs_for(specification) if c.phase == 'synthesise')
    summary = calculate(summary_config, (result,))
    assert summary.payload['modules']['M2']['assigned_roots'] == 1
    assert summary.payload['modules']['M2']['analysis_menu_scope'] == 'EXPOSED_POST_HOC'
    for row in summary.payload['modules']['M2']['memory']:
        assessment = row['assessment']
        assert assessment['status'] == 'EXPLORATORY_POST_HOC'
        assert assessment['selection_adjusted_coverage'] is False
        assert assessment['task_equivalence_qualified'] is False
        assert assessment['distributional_detection_qualified'] is False
        assert assessment['fixed_menu_calculation']['independent_roots'] == 1
    assert json.loads((destination / 'parent-custody.json').read_text())['interpretation'] == 'EXPOSED_POST_HOC_ANALYSIS'


@pytest.mark.parametrize('section,key,value', [('native', 'timestep', '0.002'), ('memory', 'observation_seed', 99), ('memory', 'stride', 2)])
def test_retained_m2_cannot_change_native_clock_map_or_sampling(tmp_path, monkeypatch, section, key, value):
    fixture = parent_fixture(tmp_path, monkeypatch)
    changed = normalise_settings(fixture.parent.settings)
    changed[section][key] = value
    if (section, key) == ('memory', 'stride'):
        # Keep the proposed analysis internally valid so the original-input
        # guard, rather than an inconsistent derived segment chart, refuses it.
        changed['memory']['segment_boundaries_samples'] = None
    path = definition(tmp_path, [(20, ('M2',), 'development')], changed)
    with pytest.raises(ValueError, match='acquisition setting'):
        api.create_reanalysis_inputs(definition_path=path, project_root=tmp_path, output_directory=tmp_path / 'invalid',
            parent_directory=fixture.parent_dir, parent_service=fixture.service)
    assert not (tmp_path / 'invalid').exists()


def test_changed_reanalysis_must_select_only_m2(tmp_path, monkeypatch):
    fixture = parent_fixture(tmp_path, monkeypatch)
    changed = normalise_settings(fixture.parent.settings)
    changed['alpha'] = '0.025'
    path = definition(tmp_path, [(10, ('M0',), 'development'), (11, ('M0',), 'development'),
        (20, ('M2',), 'development')], changed)
    with pytest.raises(ValueError, match='M2-only'):
        api.create_reanalysis_inputs(definition_path=path, project_root=tmp_path, output_directory=tmp_path / 'invalid',
            parent_directory=fixture.parent_dir, parent_service=fixture.service)


@pytest.mark.parametrize('damage', ['bytes', 'logical-schema', 'physical-digest'])
def test_reanalysis_refuses_changed_original_array_custody(tmp_path, monkeypatch, damage):
    fixture = parent_fixture(tmp_path, monkeypatch)
    manifest = next(iter(fixture.products['outputs'].values()))
    if damage == 'bytes':
        path = fixture.parent_dir / manifest.materialization.relative_path
        raw = bytearray(path.read_bytes())
        raw[-1] ^= 1
        path.write_bytes(raw)
    elif damage == 'logical-schema':
        manifest.logical.payload_schema = 'empirical-lawhood/test/wrong-array'
    else:
        manifest.materialization.physical_sha256 = '0' * 64
    path = definition(tmp_path, [(10, ('M0',), 'development'), (11, ('M0',), 'development')], fixture.parent.settings)
    with pytest.raises(ValueError, match='identity|binary receipt'):
        api.create_reanalysis_inputs(definition_path=path, project_root=tmp_path, output_directory=tmp_path / 'invalid',
            parent_directory=fixture.parent_dir, parent_service=fixture.service)
    assert not (tmp_path / 'invalid' / 'specification.json').exists()


def test_binary_manifest_source_and_allocation_are_scientific_bindings(tmp_path, monkeypatch):
    fixture = parent_fixture(tmp_path, monkeypatch)
    product = next(p for rows in fixture.products['records'].values() for p in rows.values() if p.config.phase == 'acquire')
    bad_source = replace(product.array_manifest.source, object_fingerprint='0' * 64)
    with pytest.raises(ValueError, match='source, allocation'):
        replace(product, array_manifest=replace(product.array_manifest, source=bad_source))
    wrong_allocation = ObjectIdentity.from_record('assignment.root.0000000000000000999', RootAssignment(999, ('M0',)))
    with pytest.raises(ValueError, match='source, allocation'):
        replace(product, array_manifest=replace(product.array_manifest, allocation=wrong_allocation))


def test_parent_callback_uses_runtime_signature_and_current_guard(tmp_path, monkeypatch):
    # Test the actual _read_parent callback rather than the fixture replacement.
    original_reader = api._read_parent
    fixture = parent_fixture(tmp_path, monkeypatch)
    state = {'active': False, 'consumer_calls': 0}
    from empirical_lawhood.api import recursive_execution
    def underlying(**kwargs):
        state['active'] = True
        try:
            callback = kwargs['_scientific_consumer']
            callback(directory=tmp_path, artifact_writer=fixture.service.artifact_writer,
                payloads={'experiment-specification.json': fixture.parent.canonical_bytes()},
                report={}, products=fixture.products, draft=object(), plan=object(), allow_partial=False)
        finally:
            state['active'] = False
        return {}, ()
    monkeypatch.setattr(recursive_execution, '_read_recursive_wave_with_retained_roots', underlying)
    monkeypatch.setattr(api, '_instance', lambda payloads: SimpleNamespace(specification=fixture.parent.identity))
    def read_result(**kwargs):
        assert state['active']
        assert kwargs['specification'] == fixture.parent
        return {'scientific_completion': 'COMPLETED'}
    monkeypatch.setattr(api, 'read_result', read_result)
    def consumer(**kwargs):
        assert state['active'] and kwargs['result']['scientific_completion'] == 'COMPLETED'
        state['consumer_calls'] += 1
    original_reader(tmp_path, fixture.service, consumer)
    assert state['consumer_calls'] == 1 and not state['active']


@pytest.mark.parametrize('damage', ('missing-selection', 'missing-ceiling', 'wrong-parent', 'wrong-units'))
def test_confirmation_requires_complete_scientific_choices_and_measured_parent(tmp_path, monkeypatch, damage):
    fixture = parent_fixture(tmp_path, monkeypatch)
    settings = confirmation_settings(fixture)
    if damage == 'missing-selection':
        settings['confirmation'] = None
    elif damage == 'missing-ceiling':
        settings['resources']['output_bytes'] = None
    elif damage == 'wrong-parent':
        settings['confirmation']['parent_readout_sha256'] = '0' * 64
    else:
        settings['confirmation']['endpoints'][0]['units'] = 'joule'
    path = definition(tmp_path, [(100, ('M0',), 'confirmation')], settings)
    with pytest.raises(ValueError):
        api.create_successor_inputs(definition_path=path, project_root=tmp_path,
            output_directory=tmp_path / 'invalid-freeze', parent_directory=fixture.parent_dir,
            parent_service=fixture.service)
    assert not (tmp_path / 'invalid-freeze').exists()
    assert fixture.state['reads'] == int(damage == 'wrong-parent')


def test_programme_error_allocation_cannot_overspend_or_drop_a_module():
    with pytest.raises(ValueError, match='sum to at most one'):
        normalise_settings({'inference': {'module_alpha_weights': {f'M{i}': '0.2' for i in range(8)}}})
    with pytest.raises(ValueError, match='complete M0-M7'):
        normalise_settings({'inference': {'module_alpha_weights': {'M2': '1'}}})


def population_benchmark_fixture(tmp_path, monkeypatch):
    settings = normalise_settings({'population': {'frame_size': 4, 'audit_size': 2, 'mode': 'reveal_all'}})
    parent = api.specification_for('Synthetic revealed benchmark; no native evidence',
        tuple(RootAssignment(seed, ('M1', 'M5')) for seed in range(1, 5)), settings)
    fixture = parent_fixture(tmp_path, monkeypatch, parent=parent)
    summaries = []
    for values in fixture.products['records'].values():
        for key, product in values.items():
            if product.config.phase != 'synthesise' or product.config.module != 'M5':
                continue
            comparison = {'status': 'ESTIMATED', 'full_frame_benchmark': {'status': 'ENUMERATED'}}
            rows = [{'coordinate': coordinate['id'], 'recipe': recipe, 'full_frame_mean': 1.,
                'estimator_comparison': comparison} for coordinate in settings['native']['coordinates']
                for recipe in settings['native']['preparation_arms']]
            contrasts = [{'coordinate': row['coordinate'], 'recipe': row['recipe'],
                'estimator_comparison': comparison} for row in rows if row['recipe'] != 'baseline']
            body = {'schema': 'matrix-model-free-synthesis.v1', 'module': 'M5',
                'modules': {'M5': {'assigned_roots': 4, 'acquisition_mode': 'reveal_all',
                    'finite_population': rows, 'paired_finite_population_contrasts': contrasts}}}
            values[key] = replace(product, payload_json=json_text(body))
            summaries.append((values, key))
    return fixture, summaries[0]


def test_sparse_deployment_authenticates_benchmark_before_freezing_new_root_frame(tmp_path, monkeypatch):
    fixture, _ = population_benchmark_fixture(tmp_path, monkeypatch)
    settings = normalise_settings(fixture.parent.settings)
    settings['population']['mode'] = 'sparse'
    path = definition(tmp_path, [(seed, ('M1', 'M5'), 'development') for seed in range(101, 105)], settings)
    with pytest.raises(ValueError, match='create_population_deployment_inputs'):
        api.create_inputs(definition_path=path, project_root=tmp_path, output_directory=tmp_path / 'bypass')
    result = api.create_population_deployment_inputs(definition_path=path, project_root=tmp_path,
        output_directory=tmp_path / 'deployment', parent_directory=fixture.parent_dir, parent_service=fixture.service)
    selected = decoded(tmp_path / 'deployment' / 'specification.json')
    assert fixture.state['reads'] == 1
    assert selected.parent_lineage.purpose == 'population-deployment'
    assert selected.parent_lineage.exposed_seeds == (1, 2, 3, 4)
    assert sum(root.audit_selected for root in selected.assignments) == 2
    assert result['native_acquisition_performed'] is False


@pytest.mark.parametrize('damage', ('dropped-row', 'dropped-contrast', 'failed-member', 'old-root', 'changed-target'))
def test_sparse_deployment_refuses_incomplete_or_changed_benchmark(tmp_path, monkeypatch, damage):
    fixture, (values, key) = population_benchmark_fixture(tmp_path, monkeypatch)
    body = values[key].payload
    benchmark = body['modules']['M5']
    if damage == 'dropped-row':
        benchmark['finite_population'].pop()
    elif damage == 'dropped-contrast':
        benchmark['paired_finite_population_contrasts'].pop()
    elif damage == 'failed-member':
        benchmark['finite_population'][0]['full_frame_mean'] = None
    values[key] = replace(values[key], payload_json=json_text(body))
    settings = normalise_settings(fixture.parent.settings)
    settings['population']['mode'] = 'sparse'
    if damage == 'changed-target':
        settings['population']['receiver_seed'] += 1
    seeds = range(1, 5) if damage == 'old-root' else range(101, 105)
    path = definition(tmp_path, [(seed, ('M1', 'M5'), 'development') for seed in seeds], settings)
    with pytest.raises(ValueError):
        api.create_population_deployment_inputs(definition_path=path, project_root=tmp_path,
            output_directory=tmp_path / 'invalid-deployment', parent_directory=fixture.parent_dir, parent_service=fixture.service)
    assert not (tmp_path / 'invalid-deployment').exists()


def test_final_parent_refusal_never_publishes_sparse_deployment(tmp_path, monkeypatch):
    fixture, _ = population_benchmark_fixture(tmp_path, monkeypatch)
    fixture.state['refuse_final'] = True
    settings = normalise_settings(fixture.parent.settings)
    settings['population']['mode'] = 'sparse'
    path = definition(tmp_path, [(seed, ('M1', 'M5'), 'development') for seed in range(101, 105)], settings)
    with pytest.raises(PermissionError, match='final source'):
        api.create_population_deployment_inputs(definition_path=path, project_root=tmp_path,
            output_directory=tmp_path / 'invalid-deployment', parent_directory=fixture.parent_dir, parent_service=fixture.service)
    assert not (tmp_path / 'invalid-deployment').exists()


def test_memory_confirmation_refuses_impossible_equivalence_but_reports_detection_precision():
    from empirical_lawhood.domains.matrix.model_free.confirmation import validate_confirmation

    settings = normalise_settings({'evidence_scope': 'FRESH_CONFIRMATION',
        'resources': {'memory_bytes': 1024 ** 3, 'wall_time_seconds': 120, 'output_bytes': 1024 ** 2},
        'memory': {'protocol_age_ticks': [8192]},
        'confirmation': {
            'endpoints': [{'name': 'M2.finite_history_receiver_error', 'practical_effect': '0.1', 'units': 'declared-receiver-units'}],
            'population_target': 'COMPLETE_ASSIGNED_ROOT_POPULATION', 'target_law': 'DECLARED_FINITE_AGE_ROOT_LAW',
            'precision_goal': 'DETECTION_ONLY', 'stopping_rule': 'FIXED_ROOT_CENSUS_AND_PREDECLARED_RECORD_LADDER',
            'independent_verification': ['COMPLETE_ASSIGNED_AND_FAILED_ROOT_CENSUS', 'INDEPENDENT_ANALYSIS_OPERATION',
                                         'SEGMENT_AND_PROTOCOL_AGE_DIAGNOSTICS'],
            'parent_readout_sha256': '0' * 64, 'capacity_basis': 'AUTHENTICATED_PARENT_AND_OPERATOR_MEASURED_HOST'}})
    assignments = tuple(RootAssignment(seed, ('M2',), 'confirmation') for seed in range(1000, 1080))
    result = validate_confirmation(settings, assignments)
    feasibility = result['memory_family_feasibility']
    assert len(feasibility['rows']) == 6
    assert feasibility['all_selected_menus_pass_necessary_condition'] is False
    assert feasibility['rows'][0]['root_probability_halfwidth'] > result['optimistic_single_event_halfwidth']['M2']
    assert result['power_established'] is False and result['parent_evidence_bound'] is False
    settings['confirmation']['precision_goal'] = 'TASK_EQUIVALENCE_IF_CERTIFIED'
    with pytest.raises(ValueError, match='impossible under the declared all-cell root bound'):
        validate_confirmation(settings, assignments)


@pytest.mark.parametrize('name,units,section,key,effect', [
    ('M1.assigned_service_gain', 'probability-difference', 'formation', 'probability_gain_margin', '0.1'),
    ('M2.finite_history_receiver_error', 'declared-receiver-units', 'memory', 'tolerance', '0.1'),
    ('M3.assigned_adequacy_gain', 'probability-difference', 'formation', 'probability_gain_margin', '0.1'),
    ('M4.destination_receiver_bound', 'declared-resolvent-receiver-units', 'response', 'certificate_tolerance', '0.01'),
])
def test_confirmation_effect_binds_the_implemented_receiver_threshold(tmp_path, monkeypatch, name, units, section, key, effect):
    from empirical_lawhood.domains.matrix.model_free.confirmation import validate_confirmation

    settings = confirmation_settings(parent_fixture(tmp_path, monkeypatch))
    settings['memory']['protocol_age_ticks'] = [8192]
    settings['confirmation']['independent_verification'] += [
        'SEGMENT_AND_PROTOCOL_AGE_DIAGNOSTICS', 'COUPLED_H_H2_H4', 'WITHHELD_FUTURE_SUFFIX']
    endpoint = {'name': name, 'practical_effect': effect + '0', 'units': units}
    settings['confirmation']['endpoints'] = [endpoint]
    assignments = (RootAssignment(100, (name.split('.')[0],), 'confirmation'),)
    result = validate_confirmation(settings, assignments)
    assert result['endpoint_effect_roles'][0]['operative_setting'] == section + '.' + key
    assert result['endpoint_effect_roles'][0]['automatic_success_granted'] is False
    endpoint['practical_effect'] = '0.001'
    with pytest.raises(ValueError, match='practical effect must equal its implemented threshold'):
        validate_confirmation(settings, assignments)


def test_confirmation_signed_response_effect_remains_a_precision_target(tmp_path, monkeypatch):
    from empirical_lawhood.domains.matrix.model_free.confirmation import validate_confirmation

    settings = confirmation_settings(parent_fixture(tmp_path, monkeypatch))
    settings['confirmation']['endpoints'] = [{'name': 'M3.signed_response_contrast',
        'practical_effect': '0.001', 'units': 'actuator-normalized-response'}]
    settings['confirmation']['independent_verification'] += ['COUPLED_H_H2_H4', 'WITHHELD_FUTURE_SUFFIX']
    result = validate_confirmation(settings, (RootAssignment(100, ('M3',), 'confirmation'),))
    role = result['endpoint_effect_roles'][0]
    assert role['effect_role'] == 'DECLARED_PRECISION_TARGET_ONLY; NO_IMPLEMENTED_PRACTICAL_EFFECT_DECISION'
    assert role['operative_setting'] is None and role['automatic_success_granted'] is False


def test_memory_confirmation_refuses_missing_time_support_despite_sufficient_root_bound(tmp_path, monkeypatch):
    from empirical_lawhood.domains.matrix.model_free.confirmation import validate_confirmation

    settings = confirmation_settings(parent_fixture(tmp_path, monkeypatch))
    settings['memory'].update(record_ticks=16, record_length_ladder=[16], lags=[4], history_orders=[2],
        observation_dimensions=[1], protocol_age_ticks=[8], checkpoint_ticks=[0, 8, 16], segment_boundaries_samples=None)
    settings['confirmation']['endpoints'] = [{'name': 'M2.finite_history_receiver_error',
        'practical_effect': '0.1', 'units': 'declared-receiver-units'}]
    settings['confirmation']['independent_verification'].append('SEGMENT_AND_PROTOCOL_AGE_DIAGNOSTICS')
    settings = normalise_settings(settings)
    roots = tuple(RootAssignment(seed, ('M2',), 'confirmation') for seed in range(1000, 3000))
    report = validate_confirmation(settings, roots)['memory_family_feasibility']
    assert report['probability_bounds_pass_necessary_condition'] is True
    assert report['all_selected_menus_pass_necessary_condition'] is False
    support = report['temporal_support'][0]
    assert report['record_samples'] == 17 and support['required_history_span_samples'] == 12
    assert support['pooled_complete_anchor_count'] == 5
    assert support['protocol_ages'][0]['complete_anchor_count'] == 0
    settings['confirmation']['precision_goal'] = 'TASK_EQUIVALENCE_IF_CERTIFIED'
    with pytest.raises(ValueError, match='anchor lacks its complete history'):
        validate_confirmation(settings, roots)
    settings['memory']['protocol_age_ticks'] = [16]
    assert validate_confirmation(settings, roots)['memory_family_feasibility']['all_selected_histories_have_temporal_support'] is True
    # The general development normalizer still permits a longer requested
    # history alongside a supported shorter history; confirmation reports it.
    settings['memory'].update(lags=[8], history_orders=[1, 2])
    settings['confirmation']['precision_goal'] = 'DETECTION_ONLY'
    settings = normalise_settings(settings)
    report = validate_confirmation(settings, roots)['memory_family_feasibility']
    assert report['temporal_support'][1]['pooled_complete_anchor_count'] == 0
    assert report['all_selected_histories_have_temporal_support'] is False
