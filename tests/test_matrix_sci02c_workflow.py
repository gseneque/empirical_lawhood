# SPDX-License-Identifier: MPL-2.0
"""Focused SCI02-C compiler, information-boundary and real-port controls."""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_read as reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Arrays
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CDesign, Sci02CRetainedCase, Sci02CFrozenDescription, Sci02CProduct
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_sci02b_workflow import setup as previous_setup
from tests.test_matrix_sci02_workflow import actual_fixture as actual_fixture


def setup(tmp_path):
    old, selection, cases, provenance = previous_setup(tmp_path)
    study = Sci02CDesign('design.test.sci02c', selection.identity, selection.design, '9' * 64)
    retained = tuple(Sci02CRetainedCase('retained.sci02c.' + c.root.fingerprint(), c.root, c.design, c.original_plan,
        c.original_products, c.original_receipts, replace(c.arrays, array_artifact=replace(c.arrays.array_artifact,
            artifact_id='arrays.sci02c.retained.' + c.root.fingerprint())), c.original_read_sha256) for c in cases)
    d = Decimal
    frozen = Sci02CFrozenDescription('description.test.sci02c', study.identity, tuple(c.root for c in cases),
        tuple(c.identity for c in retained), ((d(0),)*4,)*2, ((d(1),)*4,)*2, (((d(0),)*4,)*3,)*2, ((d(0),)*3,)*2)
    return study, selection, retained, provenance, frozen


def test_complete_compiler_preserves_population_and_seals_reference_after_decision(tmp_path):
    study, selection, cases, provenance, frozen = setup(tmp_path)
    declarations = binding.operation_declarations()
    registry = CapabilityRegistry('registry.test.sci02c', tuple(sorted((d.manifest() for d in declarations), key=lambda m: m.registry_id)))
    kwargs = dict(registry=registry, registrations=tuple(d.registration() for d in declarations), implementation_commit='a' * 40,
        output_codecs={s: t for d in declarations for s, t in d.record_codecs.items()})
    for training in (True, False):
        roots = tuple(selection.root('DEV', i) for i in (range(8) if training else range(8, 16)))
        draft, _ = binding.lower(study, selection, roots, provenance, campaign_fixture()[0].campaign,
            draft_id='draft.test.sci02c.' + ('training' if training else 'calibration'), cases=cases if training else (), model=None if training else frozen)
        compiled = compile_recursive_wave(draft=draft, **kwargs)
        assert len(compiled.execution_plan.tasks) == (9 if training else 233)
        from empirical_lawhood.api.recursive_operations import operation_runners
        runners = operation_runners(registry=registry, plan=compiled.execution_plan, input_supplier=object())
        for task in compiled.execution_plan.tasks:
            assert runners.resolve(task).manifest == registry.resolve(task.capability.capability_key, task.capability.capability_version)
        if not training:
            for op in draft.operations:
                phase = op.node_id.rsplit('.', 1)[-1]
                ports = {l.consumer_input_id for l in draft.links if l.consumer_node_id == op.node_id}
                if phase == 'reference': assert 'decision-product' in ports
                if phase in ('basic', 'history', 'request', 'decision'): assert not any(p.startswith('native-') for p in ports)
                if phase == 'basic': assert not any('history-observation' in p for p in ports)
            bad = replace(draft, links=tuple(l for l in draft.links if l.consumer_input_id != 'decision-product'))
            with pytest.raises(ValueError): compile_recursive_wave(draft=bad, **kwargs)


def test_public_preparation_derives_exact_records_and_marks_training_exposed(tmp_path):
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_experiment as experiment
    from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
    study, selection, cases, provenance, _ = setup(tmp_path)
    campaign = campaign_fixture()[0].campaign
    spec = experiment.Sci02CSpecification('specification.test.sci02c', study.identity, selection.identity, provenance.identity,
        ObjectIdentity.from_record(campaign.campaign_id, campaign), 'TRAINING', tuple(c.identity for c in cases))
    records = {'study': study, 'selection': selection, 'provenance': provenance, 'campaign': campaign,
        **{f'root{i:02d}': c for i, c in enumerate(cases)}}
    files = {f'root{i:02d}-arrays': SimpleNamespace(identity=c.arrays.array_artifact, path=tmp_path / f'{i}.npz') for i,c in enumerate(cases)}
    source = ObjectIdentity('source.test', 'empirical-lawhood/testing/source', '1.0.0', '8' * 64)
    result = experiment.prepare(spec, scientific_inputs={'selection': experiment.allocation_for(selection, 'TRAINING')},
        execution=ExecutionSelection(environment_id='environment.test', source_snapshot=source, output_root=str(tmp_path), workers=4),
        method_inputs=(records, files))
    assert result.executable and all(u.exposed for u in result.allocation.units)
    assert result.census.native_effect_count == 0 and len(result.draft.operations) == 9
    experiment.validate_instance(specification=spec, allocation=result.allocation, draft=result.draft, source_records=result.design_records)


def test_original_observations_feed_independently_checked_history_and_signed_receiver(tmp_path, actual_fixture, monkeypatch):
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as old_read
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_read as previous_read
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    from empirical_lawhood.science.identity.references import ArtifactIdentity
    study, selection, cases, provenance, _ = setup(tmp_path)
    d, _, _, instrument, _, handoff, _, _, _, first, second = actual_fixture
    native = previous_read.native_response(d, handoff.arrays, instrument.arrays, old_read.joined(first.arrays, second.arrays))
    observed = science.project_observations(first.arrays).arrays
    for tick, excluded in ((16, 'h32.'), (32, 'h16.')):
        projected = binding.project_observation(first.arrays, tick).arrays
        assert not any(k.startswith(excluded) or 'innovation' in k for k in projected)
    values = {'instrument.' + key: instrument.arrays[key] for key in ('forces', 'receivers', 'source_frame', 'source_spectrum',
        'source_low', 'complement_spectrum', 'complement_vectors', 'source_factor_admitted')}
    # Same disclosed EARLY fixture for three labels tests transport, not preparation science.
    for recipe in ('original', 'early', 'delayed'):
        for phase, source in (('handoff', handoff.arrays), ('observation', observed), ('assess', {k:v for k,v in native.items() if k.endswith('.native')})):
            values.update({recipe + '.' + phase + '.' + k:v for k,v in source.items()})
    raw, members = encode_matrix_arrays(values)
    artifact = ArtifactIdentity(cases[0].arrays.array_artifact.artifact_id, 'retained-scientific-input', binding.MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    retained = replace(cases[0], arrays=Sci02Arrays(artifact.artifact_id, artifact, members))
    config = binding.make_config(study, (retained.root,), 'diagnose', 'COMMON', provenance.identity, (retained.identity,))
    decoded = dict(decode_matrix_arrays(raw, retained.arrays))
    result = science.diagnose(config, retained, decoded)
    encoded, contract = binding.old._pack(config, result, 'arrays.test.sci02c')
    assert len(contract.members) <= 256
    output = dict(decode_matrix_arrays(encoded, contract))
    product = binding.product(config, {}, result, contract)
    def forbidden(*args, **kwargs): pytest.fail('independent SCI02-C reader entered a producer')
    monkeypatch.setattr(science, 'history_window', forbidden)
    monkeypatch.setattr(science.previous, 'origin_model', forbidden)
    monkeypatch.setattr(np.random, 'Generator', forbidden)
    reader.check_diagnosis(config, retained, decoded, product, output)
    assert np.all(output['native_q'] == 0)
    bad = dict(output)
    key = 'history.original.model.primary.p0.updated'
    bad[key] = bad[key].copy(); bad[key][0, -1, 24] += .001
    with pytest.raises(ValueError, match='affine'):
        reader.check_diagnosis(config, retained, decoded, product, bad)


def test_original_reserved_prefix_checkpoint_recovers_without_new_contact(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_native as native_binding
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
    from empirical_lawhood.execution.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
    from tests.test_matrix_parameter_history import publish, object_id
    from tests.runtime_platform.test_native_subwork import _plane
    from tests.matrix_native_invocation_support import prepared_native_store
    study, selection, _, provenance, frozen = setup(tmp_path)
    config = binding.make_config(study, (selection.root('DEV', 8),), 'prefix', 'COMMON', provenance.identity, model=frozen)
    declaration = next(d for d in binding.operation_declarations() if d.capability_key.endswith('.prefix'))
    plane = _plane(tmp_path / 'native', binary_codecs=MATRIX_STORAGE_CODECS)
    streams = selection.streams.streams(config.root.group_id, future=False)
    records = [(config.config_id, config), (provenance.identity.object_id, provenance),
        (config.design.record_id, config.design), (config.root.record_id, config.root)]
    records += [(pin.object_id, next(s for s in streams if pin.object_id.endswith('.' + s.purpose)))
        for _, pin in binding.stream_pins(config)]
    manifests = tuple(publish(plane, name, record.SCHEMA, record.canonical_bytes()) for name, record in records)
    def context():
        ports = tuple(plane.open(m, binding=WorkerInputBinding(m.logical.logical_artifact_id, m.materialization.materialization_id,
            m.logical.payload_schema, m.logical.media_type, m.materialization.size_bytes,
            binding.VISIBILITY, binding.ACCESS, WorkerInputKind.EXTERNAL), maximum_bytes=m.materialization.size_bytes) for m in manifests)
        outputs = tuple(WorkerOutputPort(config.node_id + '.' + key, schema, profile, media, config.node_id + '.' + key)
            for key, schema, profile, media in (('product', Sci02CProduct.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'),
                ('arrays', binding.MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz')))
        return SimpleNamespace(input_ports=ports, output_ports=outputs, task_id=config.node_id,
            config=SimpleNamespace(config_id=config.config_id, content_sha256=config.fingerprint()),
            resource_budget=binding.BUDGET, permissions=binding.PERMISSIONS, outcome_access=binding.ACCESS)
    runner = declaration.provider_factory().runner_factory()
    native, ctx, _ = prepared_native_store(plane, runner=runner, context=context(), manifests=manifests,
        provenance=provenance, execution_plan=object_id('test.sci02.plan'), native_work_preparer=native_binding.prepare_native_work,
        run_id='test.sci02.run', attempt_id='test.sci02.run.prefix.attempt-001', visibility=binding.VISIBILITY, access=binding.ACCESS)
    result = runner.execute_with_native_subwork(ctx, native)
    raw = next(o.payload for o in result.outputs if o.output_id.endswith('.product'))
    product = decode_canonical_bytes(raw, Sci02CProduct, maximum_bytes=None)
    assert product.native[0].completion.output_ids == ('arrays', 'checkpoint')
    assert all(state.completed_noise_matrices == 64 for _, state in product.generators)
    def forbidden(*args, **kwargs): pytest.fail('receipt recovery entered a new native acquisition')
    monkeypatch.setattr(native_binding, 'acquire', forbidden)
    recovered = runner.execute_with_native_subwork(context(), native)
    assert tuple((o.output_id, o.payload) for o in recovered.outputs) == tuple((o.output_id, o.payload) for o in result.outputs)



def test_hold_only_prefix_and_reference_keep_original_streams_and_consumer_costs(actual_fixture):
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_science as native
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_read as native_read
    from tests.test_matrix_sci02_workflow import fixture
    selection, _ = fixture()
    d, prefix, _, instrument, completion, handoff, _, _, _, _, _ = actual_fixture
    root = selection.root('DEV', 0)
    streams = tuple((p, s) for p in (0, 1) for s in selection.streams.streams(root.group_id, future=bool(p))
        if s.purpose.startswith('autonomous'))
    baseline = native.acquire_baseline(d, handoff.arrays, instrument.arrays, streams)
    costs = {}
    reference = native.acquire_reference(d, handoff.arrays, instrument.arrays, baseline.arrays, streams, baseline.generators,
        observe_cost=lambda k, v: costs.__setitem__(k, v))
    checked = native_read.native_response(d, handoff.arrays, instrument.arrays, reference.arrays, baseline=baseline.arrays)
    assert checked['primary.p0.native'].shape == (4, 64, 48)
    assert len(costs) == 36 and len([k for k in costs if '.a0.' in k]) == 8
    assert all(s.completed_noise_matrices == 64 for _, s in reference.generators)
    assessed = reader.assess_arm(SimpleNamespace(design=d, recipe='EARLY'), {
        'prefix': prefix.arrays, 'completion': completion.arrays, 'handoff': handoff.arrays,
        'instrument': instrument.arrays, 'baseline': baseline.arrays, 'reference': reference.arrays,
        'observation': binding.project_observation(baseline.arrays, 32).arrays})
    assert assessed.disposition == 'AVAILABLE'
    _, members = encode_matrix_arrays(reference.arrays)
    assert len(members) <= 256

