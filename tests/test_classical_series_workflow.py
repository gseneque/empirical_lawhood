# SPDX-License-Identifier: MPL-2.0
"""Declared recursive causality, real native freeze, binary custody and reanalysis.

The transport fixtures are explicitly small synthetic operands. The numerical
freeze control below invokes the actual six-Hermitian native implementation.
"""
from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.classical_matrix_series import load_definition, _specification
from empirical_lawhood.domains.matrix.classical_series import design, experiment
from empirical_lawhood.domains.matrix.classical_series.arrays import encode_acquisition, decode_acquisition, iter_encoded_bytes
from empirical_lawhood.domains.matrix.classical_series.bindings import calculate, operation_declarations, prepare_root
from empirical_lawhood.domains.matrix.classical_series.records import Acquisition, RootAssignment, RetainedInput, RetainedArray, json_text
from empirical_lawhood.domains.matrix.classical_series.science import normalise_config
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from empirical_lawhood.execution.experiment_preparation import ExecutionSelection

ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / 'programmes/foundations/emergent-structure/workflows/classical-series'


def small_specification():
    settings = normalise_config(dict(ramp_ticks=4, handoff_tick=4, history_ticks=8,
        horizon_ticks=4, observation_stride=4, pulse_ticks=1, refresh_tick=2,
        persistence_ticks=1, survival_ticks=2, panels=1, actions=['GENERIC'],
        calibration_alpha='0.5', phases=['e1', 'e3', 'e6', 'derivations']))
    assigned = tuple(RootAssignment(seed, role) for seed, role in
        ((101, 'training'), (102, 'training'), (201, 'calibration'), (202, 'calibration'), (301, 'confirmation')))
    return _specification('Small native architecture control; no scientific qualification', assigned, settings)


def test_authored_production_has_complete_independent_roster_and_causal_supplier():
    _, label, assigned, settings = load_definition(WORKFLOW / 'experiment.json')
    spec = _specification(label, assigned, settings)
    configs = design.configs_for(spec)
    assert len(assigned) == 144
    assert {role: sum(r.role == role for r in assigned) for role in ('training', 'calibration', 'confirmation')} == {
        'training': 32, 'calibration': 32, 'confirmation': 80}
    assert len(configs) == 290
    assert len(settings['coordinates']) == 11 and len(settings['preparation_arms']) == 4
    requirements, connections, links, external = design.graph_for(spec, configs)
    assert not external and len(requirements) == len(connections)
    calibration, = (c for c in configs if c.phase == 'calibrate')
    summaries = {c.node_id for c in configs if c.phase == 'summarise'}
    assert {p.producer_node_id for p in links if p.consumer_node_id == calibration.node_id} == summaries
    assert len(summaries) == 64
    for config in configs:
        if config.phase == 'acquire' and config.assignments[0].role == 'confirmation':
            assert [(p.consumer_input_id, p.producer_node_id) for p in links if p.consumer_node_id == config.node_id] == [('calibration', calibration.node_id)]
        if config.phase == 'acquire' and config.assignments[0].role != 'confirmation':
            assert not any(p.consumer_node_id == config.node_id for p in links)
    assert design.budget_for(next(c for c in configs if c.phase == 'acquire')).memory_bytes > 1024**3


def test_editable_definition_refuses_cross_role_reuse(tmp_path):
    value = json.loads((WORKFLOW / 'smoke.json').read_text())
    value['roots']['confirmation'][0] = value['roots']['training'][0]
    path = tmp_path / 'invalid.json'
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='overlap'):
        load_definition(path)


def test_real_compiler_accepts_complete_graph_and_refuses_causal_edge_loss():
    spec = small_specification()
    draft, _ = design.lower(spec, {})
    declarations = operation_declarations()
    options = dict(registry=CapabilityRegistry('registry.classical-series-test', tuple(d.manifest() for d in declarations)),
        registrations=tuple(d.registration() for d in declarations), implementation_commit='a' * 40,
        output_codecs={k: v for d in declarations for k, v in d.record_codecs.items()})
    compilation = compile_recursive_wave(draft=draft, **options)
    assert len(compilation.execution_plan.tasks) == 12
    calibration = next(c for c in design.configs_for(spec) if c.phase == 'calibrate')
    conf = next(c for c in design.configs_for(spec) if c.phase == 'acquire' and c.assignments[0].role == 'confirmation')
    link = next(p for p in draft.links if p.consumer_node_id == conf.node_id and p.producer_node_id == calibration.node_id)
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(draft, links=tuple(p for p in draft.links if p != link)), **options)


def test_once_per_root_preparer_rejects_extra_future_visibility():
    spec = small_specification()
    configs = design.configs_for(spec)
    requirements, connections, links, external = design.graph_for(spec, configs)
    context = SimpleNamespace(config_inputs=tuple(SimpleNamespace(record=c) for c in configs),
        root=design.scientific_root(spec), external_inputs=external, links=links,
        requirements=requirements, connections=connections)
    assert len(prepare_root(context)) == len(configs)
    context.links = links[:-1]
    with pytest.raises(ValueError, match='causal'):
        prepare_root(context)


def sample_transport():
    config = next(c for c in design.configs_for(small_specification()) if c.phase == 'acquire' and c.assignments[0].role == 'training')
    payload = {'schema': 'classical-series-acquisition.v1', 'seed': config.assignments[0].seed,
        'test_fixture': True, 'position': [[0.0, -0.0, 1.125, -7.25] for _ in range(5)],
        'ticks': list(range(19)), 'nested': {'unavailable': None, 'mask': [True, False] * 5}}
    original = Acquisition(config.node_id + '.product', config, json_text(payload))
    encoded, chunks = encode_acquisition(original, artifact_id='artifact.classical-transport-test')
    return original, encoded, b''.join(iter_encoded_bytes(encoded, chunks))


def test_binary_transport_preserves_exact_operands_and_checks_late_corruption():
    original, encoded, raw = sample_transport()
    assert encoded.array_artifact.size_bytes == len(raw)
    assert json_text(decode_acquisition(encoded, BytesIO(raw))) == original.payload_json
    with pytest.raises(ValueError):
        decode_acquisition(encoded, BytesIO(raw[:-1] + bytes([raw[-1] ^ 1])))
    with pytest.raises(ValueError):
        decode_acquisition(encoded, BytesIO(raw[:-17]))


def test_binary_shape_metadata_cannot_duplicate_or_omit_an_operand():
    _, encoded, raw = sample_transport()
    metadata = encoded.metadata
    metadata.pop('position')
    with pytest.raises(ValueError, match='loses'):
        decode_acquisition(replace(encoded, payload_json=json_text(metadata)), BytesIO(raw))


def test_real_native_supplier_stays_sealed_through_wrapper_and_conf_commitment(tmp_path):
    """Actual numerical execution; never a synthetic substitute for a claim."""
    spec = small_specification()
    configs = design.configs_for(spec)
    acquired = {}
    summaries = []
    for config in configs:
        if config.phase == 'acquire' and config.assignments[0].role != 'confirmation':
            acquired[config.assignments[0].seed] = calculate(config, (), None)
    for config in configs:
        if config.phase == 'summarise':
            summaries.append(calculate(config, (acquired[config.assignments[0].seed],), None))
    calibration = calculate(next(c for c in configs if c.phase == 'calibrate'), (), None, summaries=summaries)
    config = next(c for c in configs if c.phase == 'acquire' and c.assignments[0].role == 'confirmation')
    native = calculate(config, (), calibration)
    result = calculate(next(c for c in configs if c.phase == 'analyse'), (native,), calibration)
    assert result.acquisition == native.identity and result.calibration == calibration.identity
    assert native.payload['cases']
    assert all(case.get('status') != 'UNAVAILABLE' for case in native.payload['cases'])
    encoded, chunks = encode_acquisition(native, artifact_id='artifact.classical-reanalysis-test')
    selected = replace(spec, specification_id='specification.classical-retained-test', mode='reanalysis',
        evidence_scope='EXPOSED_REANALYSIS',
        retained_inputs=tuple(sorted((RetainedInput('calibration', calibration.identity),
            RetainedInput(config.assignments[0].unit_id, encoded.identity)), key=lambda p: p.key)),
        retained_arrays=(RetainedArray('arrays.' + config.assignments[0].unit_id, encoded.array_artifact),))
    records = {'calibration': calibration, config.assignments[0].unit_id: encoded}
    experiment.bind_inputs(selected, records)
    physical = tmp_path / 'original-native-arrays.bin'
    physical.write_bytes(b''.join(iter_encoded_bytes(encoded, chunks)))
    key = 'arrays.' + config.assignments[0].unit_id
    bound = experiment.bind_inputs(selected, records,
        files={key: SimpleNamespace(identity=encoded.array_artifact, path=physical)})
    prepared = experiment.prepare(selected, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs,
        execution=ExecutionSelection(1, 'environment.classical-test', spec.identity, str(tmp_path)))
    assert prepared.executable and len(prepared.input_files) == 1
    external = next(p for p in prepared.draft.external_inputs if p.input_id == 'external.' + key)
    assert external.maximum_size_bytes == prepared.input_files[0][1].maximum_bytes == len(physical.read_bytes())
    relabelled = tuple(RootAssignment(100, row.role) if row.seed == 101 else row for row in selected.assignments)
    with pytest.raises(ValueError, match="TRAIN/CAL root allocation"):
        experiment.bind_inputs(replace(selected, assignments=relabelled), records)
    assert {c.phase for c in design.configs_for(selected)} == {'analyse', 'synthesise'}
    changed = selected.settings
    changed['timestep'] = '0.002'
    with pytest.raises(ValueError, match='numerical acquisition'):
        experiment.bind_inputs(replace(selected, settings_json=json_text(changed)), records)
