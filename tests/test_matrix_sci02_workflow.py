# SPDX-License-Identifier: MPL-2.0
"""Software-only SCI02 controls; these disclosed streams are never study roots."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_bindings as bindings
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as reader
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Design, Sci02Selection
from empirical_lawhood.domains.matrix.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
from empirical_lawhood.domains.matrix.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe, STREAM_RULE
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture


def fixture():
    path = Path(__file__).parents[1] / 'programmes/foundations/emergent-structure/workflows/matrix-programme/scientific-design.example.json'
    original = decode_canonical_bytes(path.read_bytes(), MatrixProgrammeScientificDesign, maximum_bytes=None)
    coordinate, = (c for c in original.e1_coordinates if c.family_id == 'matrix-history.joint-decreasing-coupling')
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype='<c16')
    templates = {'generic_basis': np.asarray([np.kron(p, np.eye(2)) / 2 for p in pauli], dtype='<c16'),
        'force_coefficients': np.stack((np.eye(3), np.eye(3))).astype('<f8') / np.sqrt(6),
        'trace_coefficients': np.ones((2, 3), dtype='<f8') / np.sqrt(6),
        'receiver_coefficients': np.eye(48, dtype='<f8').reshape(48, 2, 2, 3, 4)}
    raw, members = encode_matrix_arrays(templates)
    assay = replace(original.prepared_assay, template_artifact=replace(original.prepared_assay.template_artifact,
        sha256=sha256(raw).hexdigest(), size_bytes=len(raw)), template_members=members)
    design = Sci02Design('design.test.sci02', original.identity, coordinate, assay, original.e1_factor_rule,
        'TEST_ONLY_NO_MOLECULAR_OR_SCIENTIFIC_EVIDENCE', '1' * 64)
    streams = SelectedE4StreamRecipe('streams.test.sci02', '2' * 64, '3' * 64, STREAM_RULE)
    exposure = ObjectIdentity('test.census', 'empirical-lawhood/testing/census', '1.0.0', '4' * 64)
    return Sci02Selection('selection.test.sci02', design, streams, exposure), templates


def test_exact_recipes_and_public_roots_keep_original_prefix_and_no_stream_values():
    selection, _ = fixture()
    original, early, delayed = (selection.design.recipe(r).half_tick_couplings for r in ('ORIGINAL', 'EARLY', 'DELAYED'))
    assert original[:129] == early[:129] == delayed[:129]
    assert early[320:] == (original[-1],) * 193
    assert delayed[128:321] == (original[128],) * 193
    assert original[-1] == early[-1] == delayed[-1]
    root = selection.root('DEV', 0)
    assert decode_canonical_bytes(root.canonical_bytes(), type(root), maximum_bytes=None) == root
    assert b'effective_seed' not in root.canonical_bytes() and b'seed_material_sha256' not in root.canonical_bytes()


def test_shared_compiler_keeps_complete_graph_and_causal_predecessors(tmp_path):
    from tests.test_matrix_later_programme import metadata
    selection, _ = fixture()
    provenance = metadata.__wrapped__(tmp_path)[1].provenance
    draft, _ = bindings.lower(selection, (selection.root('DEV', 0),), provenance, campaign_fixture()[0].campaign,
        draft_id='draft.test.sci02')
    declarations = bindings.operation_declarations()
    registry = CapabilityRegistry('registry.test.sci02', tuple(row.manifest() for row in declarations))
    compiled = compile_recursive_wave(draft=draft, registry=registry, registrations=tuple(row.registration() for row in declarations),
        implementation_commit='a' * 40, output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})
    assert len(compiled.execution_plan.tasks) == 28
    for operation in draft.operations:
        phase = operation.node_id.rsplit('.', 1)[-1]
        links = [link for link in draft.links if link.consumer_node_id == operation.node_id]
        if phase in ('shadow', 'origin', 'refresh'):
            assert not any(link.consumer_input_id.startswith('native-') for link in links)
        if phase == 'completion': assert any(link.consumer_input_id == 'shadow-product' for link in links)
        if phase == 'response-suffix': assert any(link.consumer_input_id == 'refresh-product' for link in links)
    removed = tuple(link for link in draft.links if link.consumer_input_id != 'shadow-product')
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(draft, links=removed), registry=registry,
            registrations=tuple(row.registration() for row in declarations), implementation_commit='a' * 40,
            output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})


@pytest.fixture(scope='module')
def actual_fixture():
    selection, templates = fixture()
    d, root = selection.design, selection.root('DEV', 0)
    streams = tuple((p, s) for p in (0, 1) for s in selection.streams.streams(root.group_id, future=bool(p)))
    preparation = tuple(s for p, s in streams if p == 0)
    prefix = science.acquire_preparation_interval(d, 'ORIGINAL', preparation)
    past = science.project_state(prefix.arrays, tick=64)
    sealed = science.shadow_forecasts(d, past.arrays, templates)
    completion = science.acquire_preparation_interval(d, 'EARLY', preparation, prefix=prefix.arrays, saved=prefix.generators)
    handoff = science.project_state(completion.arrays, tick=256)
    origin = science.origin_models(d, handoff.arrays, sealed.arrays)
    first = science.acquire_response_interval(d, handoff.arrays, sealed.arrays, streams, start=0)
    observed = science.project_checkpoint(d, first.arrays)
    refreshed = science.refresh_models(d, origin.arrays, observed.arrays)
    second = science.acquire_response_interval(d, first.arrays, refreshed.arrays, streams, start=32, saved=first.generators)
    for result in (prefix, past, sealed, completion, handoff, origin, first, observed, refreshed, second):
        encode_matrix_arrays(result.arrays)
    return d, prefix, past, sealed, completion, handoff, origin, observed, refreshed, first, second


def test_complete_cold_readout_uses_no_rng_marcher_or_continuation_producer(actual_fixture, monkeypatch):
    d, prefix, past, sealed, completion, handoff, origin, observed, refreshed, first, second = actual_fixture
    def forbidden(*args, **kwargs): pytest.fail('cold reader entered a producer or RNG')
    monkeypatch.setattr(np.random, 'Generator', forbidden)
    monkeypatch.setattr(science, 'continue_response_window', forbidden)
    monkeypatch.setattr(science, 'propagate_interval', forbidden)
    checks = reader.shadow_checks(d, past.arrays, sealed.arrays)
    result = reader.assess_arm(d, 'EARLY', prefix.arrays, completion.arrays, handoff.arrays, sealed.arrays,
        origin.arrays, observed.arrays, refreshed.arrays, first.arrays, second.arrays)
    assert result.disposition == 'AVAILABLE' and checks
    assert len(result.arrays['input_krylov48.joint_error_curves'][0]) == 49
    assert dict(result.measurements)['assigned'] == 1
    _, members = encode_matrix_arrays({**result.arrays, **{'shadow-control.' + k: v for k, v in checks.items()}})
    assert len(members) <= 256
    reader.instrument_checks(d, past.arrays, sealed.arrays, fixture()[1])
    changed = dict(sealed.arrays)
    changed['source_frame'] = -changed['source_frame']
    with pytest.raises(ValueError, match='chart'):
        reader.instrument_checks(d, past.arrays, changed, fixture()[1])
    for method in ('FULL', 'INPUT_KRYLOV48'):
        np.testing.assert_array_equal(refreshed.arrays['primary.p0.state.' + method.lower() + '_refresh32'][:, :2],
            origin.arrays['primary.state.' + method.lower()][:, :2])


def test_response_continuation_retains_original_noise_position_and_clock(actual_fixture):
    d, _, _, _, _, handoff, _, _, refreshed, first, second = actual_fixture
    for p in (0, 1):
        assert all(s.completed_noise_matrices == 32 for panel, s in first.generators if panel == p)
        assert all(s.completed_noise_matrices == 64 for panel, s in second.generators if panel == p)
    assert first.arrays['branch.primary.p0.a0.hold.ticks'][0] == 256
    assert second.arrays['branch.fine.p0.a0.hold.ticks'][-1] == 640
    changed = dict(second.arrays)
    changed['branch.fine.p0.a0.hold.positions'] = changed['branch.fine.p0.a0.hold.positions'].copy()
    changed['branch.fine.p0.a0.hold.positions'][0, 0, 0, 0, 0] += .1
    with pytest.raises(ValueError, match='endpoint'): reader.joined(first.arrays, changed)
    # A refresh observation cannot contain the rest of a trajectory.
    with pytest.raises(ValueError, match='outside'):
        science.refresh_models(d, refreshed.arrays, handoff.arrays)


def test_original_two_output_native_checkpoint_recovers_without_new_contact(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Product
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
    from empirical_lawhood.execution.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
    from tests.test_matrix_later_programme import metadata
    from tests.test_matrix_parameter_history import publish, object_id
    from tests.runtime_platform.test_native_subwork import _plane
    from tests.matrix_native_invocation_support import prepared_native_store
    provenance = metadata.__wrapped__(tmp_path)[1].provenance
    selection, _ = fixture()
    config = next(c for c in bindings.configs(selection.design, selection.root('DEV', 0), provenance.identity) if c.phase == 'prefix')
    declaration = next(d for d in bindings.operation_declarations() if d.capability_key.endswith('.prefix'))
    plane = _plane(tmp_path / 'native', binary_codecs=MATRIX_STORAGE_CODECS)
    streams = selection.streams.streams(config.root.group_id, future=False)
    records = [(config.config_id, config), (provenance.identity.object_id, provenance),
        (config.design.record_id, config.design), (config.root.record_id, config.root)]
    records += [(pin.object_id, next(s for s in streams if pin.object_id.endswith('.' + s.purpose)))
        for _, pin in bindings.stream_pins(config)]
    manifests = tuple(publish(plane, name, record.SCHEMA, record.canonical_bytes()) for name, record in records)
    def context():
        ports = tuple(plane.open(m, binding=WorkerInputBinding(m.logical.logical_artifact_id, m.materialization.materialization_id,
            m.logical.payload_schema, m.logical.media_type, m.materialization.size_bytes,
            bindings.VISIBILITY, bindings.ACCESS, WorkerInputKind.EXTERNAL), maximum_bytes=m.materialization.size_bytes) for m in manifests)
        outputs = tuple(WorkerOutputPort(config.node_id + '.' + key, schema, profile, media, config.node_id + '.' + key)
            for key, schema, profile, media in (('product', Sci02Product.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'),
                ('arrays', bindings.MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz')))
        return SimpleNamespace(input_ports=ports, output_ports=outputs, task_id=config.node_id,
            config=SimpleNamespace(config_id=config.config_id, content_sha256=config.fingerprint()),
            resource_budget=bindings.BUDGET, permissions=bindings.PERMISSIONS, outcome_access=bindings.ACCESS)
    runner = declaration.provider_factory().runner_factory()
    native, ctx, _ = prepared_native_store(plane, runner=runner, context=context(), manifests=manifests,
        provenance=provenance, execution_plan=object_id('test.sci02.plan'), native_work_preparer=bindings.prepare_native_work,
        run_id='test.sci02.run', attempt_id='test.sci02.run.prefix.attempt-001', visibility=bindings.VISIBILITY, access=bindings.ACCESS)
    result = runner.execute_with_native_subwork(ctx, native)
    raw = next(o.payload for o in result.outputs if o.output_id.endswith('.product'))
    product = decode_canonical_bytes(raw, Sci02Product, maximum_bytes=None)
    assert product.native[0].completion.output_ids == ('arrays', 'checkpoint')
    assert all(state.completed_noise_matrices == 64 for _, state in product.generators)
    def forbidden(*args, **kwargs): pytest.fail('receipt recovery entered a new native acquisition')
    monkeypatch.setattr(bindings, 'acquire', forbidden)
    recovered = runner.execute_with_native_subwork(context(), native)
    assert tuple((o.output_id, o.payload) for o in recovered.outputs) == tuple((o.output_id, o.payload) for o in result.outputs)


def test_inquiry_uses_binary_source_contract_and_does_not_promote_matrix_completion(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_inquiry as inquiry
    from empirical_lawhood.api import recursive_inquiry_evidence as evidence
    from tests.test_matrix_later_programme import metadata
    selection, templates = fixture()
    provenance = metadata.__wrapped__(tmp_path)[1].provenance
    draft, records = bindings.lower(selection, (selection.root('DEV', 0),), provenance, campaign_fixture()[0].campaign,
        draft_id='draft.test.sci02.inquiry')
    raw, _ = encode_matrix_arrays(templates)
    payloads = {}
    for external in draft.external_inputs:
        suffix = '.npz' if external.media_type == 'application/x-npz' else '.json'
        payloads['external-' + sha256(external.input_id.encode()).hexdigest()[:24] + suffix] = (
            raw if suffix == '.npz' else dict(records)[external.input_id].canonical_bytes())
    factories = tuple(d.provider_factory() for d in bindings.operation_declarations())
    monkeypatch.setattr(evidence, 'selected_operation_factories', lambda _: factories)
    meanings = evidence.project_wave_evidence_bindings(draft=draft, payloads=payloads)
    assert len(meanings) == len(draft.external_inputs)
    work = inquiry.inquiry_work_projector(draft, draft.selected_operation_ids[0])
    assert work.scope == inquiry.scope(next(iter(inquiry._wave(draft).values())))
    foreign = ObjectIdentity('claim.molecular.shortcut', 'empirical-lawhood/kernel/claim', '1.0.0', 'a' * 64)
    assert inquiry.inquiry_claim_assessment_projector(draft,
        SimpleNamespace(target=SimpleNamespace(required_claims=(foreign,))), {}) == ()
    assert inquiry.inquiry_outcome_projector(draft, SimpleNamespace(endpoint=work.scope), {'records': {}, 'receipts': {}}) == 'unresolved'
