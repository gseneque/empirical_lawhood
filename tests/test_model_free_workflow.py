# SPDX-License-Identifier: MPL-2.0
"""Focused causal graph, original operand, sampling and empty-census controls."""
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace
import pytest

from empirical_lawhood.api.model_free_matrix import specification_for
from empirical_lawhood.domains.matrix.model_free import design, experiment
from empirical_lawhood.domains.matrix.model_free.bindings import Runner, calculate, operation_declarations, prepare_root
from empirical_lawhood.domains.matrix.model_free.records import OperationConfig, ParentLineage, Product, RootAssignment, Specification, json_text, selection_key
from empirical_lawhood.domains.matrix.model_free.science import normalise_settings
from empirical_lawhood.domains.matrix.classical_series.arrays import encode_acquisition, decode_acquisition, iter_encoded_bytes
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


def specification():
    settings = normalise_settings({'population': {'frame_size': 4, 'audit_size': 2}})
    return specification_for('Exposed software topology control; no scientific qualification', (
        RootAssignment(101, ('M0', 'M1', 'M3', 'M4')),
        RootAssignment(102, ('M2',)), RootAssignment(103, ('M1', 'M6', 'M7')),
        RootAssignment(104, ('M1', 'M5')), RootAssignment(105, ('M1', 'M5')),
        RootAssignment(106, ('M1', 'M5')), RootAssignment(107, ('M1', 'M5'))), settings)


def compilation(draft):
    declarations = operation_declarations()
    return compile_recursive_wave(draft=draft,
        registry=CapabilityRegistry('registry.model-free-control', tuple(d.manifest() for d in declarations)),
        registrations=tuple(d.registration() for d in declarations), implementation_commit='a' * 40,
        output_codecs={k: v for d in declarations for k, v in d.record_codecs.items()})


def test_all_modules_compile_without_artificial_fit_dependencies():
    spec = specification()
    configs = design.configs_for(spec)
    draft, _ = design.lower(spec, {})
    compiled = compilation(draft)
    assert len(compiled.execution_plan.tasks) == 40
    assert {c.phase for c in configs} == {'acquire', 'analyse', 'synthesise'}
    by_id = {c.node_id: c for c in configs}
    for link in draft.links:
        if link.consumer_input_id == 'prerequisites.m1':
            assert by_id[link.consumer_node_id].module in ('M3', 'M5', 'M7')
            assert by_id[link.producer_node_id].module == 'M1'
        if link.consumer_input_id == 'prerequisites.m3':
            assert by_id[link.consumer_node_id].module == 'M4'
    assert sum(r.audit_selected is True for r in spec.assignments) == 2
    assert all(r.inclusion_probability == '0.5' for r in spec.assignments if 'M5' in r.modules)


def test_compiler_refuses_lost_checkpoint_or_future_edge():
    draft, _ = design.lower(specification(), {})
    removed = next(l for l in draft.links if l.consumer_input_id == 'prerequisites.m1')
    with pytest.raises(ValueError):
        compilation(replace(draft, links=tuple(l for l in draft.links if l != removed)))


def test_probability_sample_is_derived_and_cannot_be_renominated():
    spec = specification()
    selected = next(r for r in spec.assignments if r.audit_selected is True)
    damaged = tuple(replace(r, audit_selected=False) if r == selected else r for r in spec.assignments)
    with pytest.raises(ValueError, match='frozen probability'):
        replace(spec, assignments=damaged)
    with pytest.raises(ValueError, match='separate'):
        RootAssignment(1, ('M1', 'M2'))


@pytest.mark.parametrize('damage', ('omitted-choice', 'invalid-support', 'invalid-alpha', 'incomplete-family'))
def test_current_entry_refuses_incomplete_or_invalid_choices_without_rewriting_retained_bytes(monkeypatch, damage):
    from empirical_lawhood.domains.matrix.model_free import science
    spec = specification_for('Exposed declaration-boundary control', (RootAssignment(201, ('M0',)),), {})
    settings = spec.settings
    if damage == 'omitted-choice':
        settings['memory'].pop('minimum_support')
    elif damage == 'invalid-support':
        settings['memory']['minimum_support'] = 0
    elif damage == 'invalid-alpha':
        settings['alpha'] = '1'
    else:
        settings['inference']['module_alpha_weights'].pop('M4')
    retained = replace(spec, settings_json=json_text(settings))
    raw = retained.canonical_bytes()
    # Typed historical decoding establishes exact stored data, not permission
    # to execute the old/incomplete settings under a changed current owner.
    restored = decode_canonical_bytes(raw, Specification, maximum_bytes=None)
    assert restored.canonical_bytes() == raw and restored.identity == retained.identity
    with pytest.raises(ValueError):
        experiment.bind_inputs(restored, {})
    config = next(row for row in design.configs_for(restored) if row.phase == 'acquire')
    with pytest.raises(ValueError):
        prepare_root(SimpleNamespace(config_inputs=(SimpleNamespace(record=config),)))
    port = SimpleNamespace(payload_schema=OperationConfig.SCHEMA, media_type='application/json',
        size_bytes=len(config.canonical_bytes()), decode_canonical_record=lambda *args, **kwargs: config)
    with pytest.raises(ValueError):
        Runner(manifest=None)._calculate(SimpleNamespace(input_ports=(port,)))
    def forbidden(*args, **kwargs):
        pytest.fail('invalid current settings reached scientific acquisition')
    monkeypatch.setattr(science, 'acquire_root', forbidden)
    with pytest.raises(ValueError):
        calculate(config)


def empty_acquisition():
    spec = specification()
    config = next(c for c in design.configs_for(spec) if c.phase == 'acquire' and c.module == 'M0')
    body = {'schema': 'matrix-model-free-acquisition.v1', 'module': 'M0', 'seed': 101,
        'status': 'UNRESOLVED', 'cases': [], 'reason': 'Explicit absent numerical control operands'}
    return Product(config.node_id + '.product', config, json_text(body))


def test_empty_numerical_census_has_exact_authenticated_empty_transport():
    original = empty_acquisition()
    with pytest.raises(ValueError, match='operand census'):
        encode_acquisition(original, artifact_id='artifact.empty-control')
    encoded, leaves = encode_acquisition(original, artifact_id='artifact.empty-control', allow_empty=True)
    raw = b''.join(iter_encoded_bytes(encoded, leaves))
    assert raw == b'' and encoded.array_artifact.size_bytes == 0
    assert json_text(decode_acquisition(encoded, BytesIO(raw))) == original.payload_json
    with pytest.raises(ValueError, match='verification'):
        decode_acquisition(encoded, BytesIO(b'unreceipted-extra-data'))


def test_native_control_uses_real_calculation_and_binary_roundtrip():
    spec = specification()
    config = next(c for c in design.configs_for(spec) if c.phase == 'acquire' and c.module == 'M0')
    product = calculate(config)
    assert product.payload['module'] == 'M0' and product.payload['controls']
    encoded, leaves = encode_acquisition(product, artifact_id='artifact.native-control', allow_empty=True)
    raw = b''.join(iter_encoded_bytes(encoded, leaves))
    assert decode_acquisition(encoded, BytesIO(raw)) == product.payload
    analysis_config = next(c for c in design.configs_for(spec) if c.phase == 'analyse' and c.module == 'M0')
    analysis = calculate(analysis_config, (product,))
    assert analysis.dependencies == (product.identity,)


def test_public_preparation_declares_all_inputs_without_native_contact(tmp_path):
    spec = specification()
    bound = experiment.bind_inputs(spec, {})
    prepared = experiment.prepare(spec, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=ExecutionSelection(1, 'environment.model-free-control', spec.identity, str(tmp_path)))
    assert prepared.executable and len(prepared.draft.operations) == 40
    assert not prepared.input_files and not prepared.input_records


def test_phase_only_reanalysis_has_no_acquisition_or_fit(tmp_path):
    source = specification()
    original = empty_acquisition()
    encoded, leaves = encode_acquisition(original, artifact_id='artifact.retained-empty', allow_empty=True)
    assignment = RootAssignment(101, ('M0',))
    key = selection_key('M0', assignment)
    # Disclosed software fixture only: these immutable pins do not authenticate
    # a real producing run or confer scientific authority.
    summaries = tuple(sorted((Product(c.node_id + '.product', c,
        json_text({'schema': 'matrix-model-free-synthesis.v1', 'module': c.module})).identity
        for c in design.configs_for(source) if c.phase == 'synthesise'), key=lambda p: p.object_id))
    exposed = tuple(r.seed for r in source.assignments)
    lineage = ParentLineage('retained-reanalysis', source.identity, summaries, source.assignments,
        'a' * 64, 'b' * 64, 'c' * 64, 'd' * 64, exposed,
        sha256(json_text({'seeds': list(exposed)}).encode()).hexdigest(),
        sha256(source.settings_json.encode()).hexdigest())
    spec = specification_for('One retained module; original exposed root', (assignment,), original.config.settings,
        mode='reanalysis', records=((key, encoded),), arrays=(('arrays.' + key, encoded.array_artifact),), parent_lineage=lineage)
    bound = experiment.bind_inputs(spec, {key: encoded}, files={'arrays.' + key: SimpleNamespace(identity=encoded.array_artifact, path=tmp_path / 'empty.bin')})
    draft, _ = design.lower(spec, {key: encoded})
    assert {c.phase for c in design.configs_for(spec)} == {'analyse', 'synthesise'}
    assert len(compilation(draft).execution_plan.tasks) == 2
    assert bound.scientific_inputs['allocation'].units[0].unit_id == assignment.unit_id
