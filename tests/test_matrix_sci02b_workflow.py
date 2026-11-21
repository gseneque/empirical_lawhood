# SPDX-License-Identifier: MPL-2.0
"""Disclosed software controls; no study roots or qualification evidence."""
from dataclasses import replace
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_bindings as binding
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_development as development
from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_science as science
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Arrays
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_records import Sci02BDesign, Sci02BProduct, Sci02BRetainedCase
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_sci02_workflow import fixture
from tests.test_matrix_sci02_workflow import actual_fixture as actual_fixture


def setup(tmp_path):
    from tests.test_matrix_later_programme import metadata
    selection, _ = fixture()
    provenance = metadata.__wrapped__(tmp_path)[1].provenance
    study = Sci02BDesign('design.test.sci02b', selection.identity, selection.design, '5' * 64)
    cases = []
    for i in range(8):
        root = selection.root('DEV', i)
        raw, members = encode_matrix_arrays({'test': np.zeros(1, dtype='<f8')})
        artifact = ArtifactIdentity('arrays.sci02b.retained.' + root.fingerprint(), 'retained-scientific-input',
            binding.MATRIX_ARRAY_SCHEMA, sha256(raw).hexdigest(), 'application/x-npz', len(raw))
        identity = ObjectIdentity('test.original', 'empirical-lawhood/testing/original', '1.0.0', '6' * 64)
        cases.append(Sci02BRetainedCase('retained.sci02b.' + root.fingerprint(), root, selection.design,
            identity, (identity,), (identity,), Sci02Arrays(artifact.artifact_id, artifact, members), '7' * 64))
    return study, selection, tuple(cases), provenance


def test_generic_compiler_keeps_all_17_operations_and_refuses_missing_root(tmp_path):
    study, selection, cases, provenance = setup(tmp_path)
    draft, _ = binding.lower(study, selection, cases, provenance, campaign_fixture()[0].campaign, draft_id='draft.test.sci02b')
    declarations = binding.operation_declarations()
    registry = CapabilityRegistry('registry.test.sci02b', tuple(d.manifest() for d in declarations))
    kwargs = dict(registry=registry, registrations=tuple(d.registration() for d in declarations),
        implementation_commit='a' * 40, output_codecs={schema: kind for d in declarations for schema, kind in d.record_codecs.items()})
    result = compile_recursive_wave(draft=draft, **kwargs)
    assert len(result.execution_plan.tasks) == 17
    assert not any(d.execution_properties.native_effect for d in declarations)
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=replace(draft, links=draft.links[1:]), **kwargs)
    with pytest.raises(ValueError, match='complete'):
        binding.configs(study, tuple(c.root for c in cases[1:]), tuple(c.identity for c in cases[1:]), provenance.identity)


def test_public_preparation_preserves_retained_population_and_has_no_native_census(tmp_path):
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_experiment as experiment
    from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
    study, selection, cases, provenance = setup(tmp_path)
    campaign = campaign_fixture()[0].campaign
    specification = experiment.Sci02BSpecification('specification.test.sci02b', study.identity, selection.identity,
        tuple(c.identity for c in cases), provenance.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign))
    records = {'study': study, 'selection': selection, 'provenance': provenance, 'campaign': campaign,
        **{f'root{i:02d}': c for i, c in enumerate(cases)}}
    files = {f'root{i:02d}-arrays': SimpleNamespace(identity=c.arrays.array_artifact, path=tmp_path / f'root{i:02d}.npz')
        for i, c in enumerate(cases)}
    bound = experiment.bind_inputs(specification, records, files=files)
    source = ObjectIdentity('source.test', 'empirical-lawhood/testing/source', '1.0.0', '8' * 64)
    result = experiment.prepare(specification, scientific_inputs={'selection': experiment.allocation_for(selection)},
        execution=ExecutionSelection(environment_id='environment.test', source_snapshot=source, output_root=str(tmp_path), workers=4),
        method_inputs=(records, files))
    assert result.executable and result.census.native_effect_count == 0
    assert len(result.draft.operations) == 17 and bound is not None
    experiment.validate_instance(specification=specification, allocation=result.allocation, draft=result.draft,
        source_records=result.design_records)


def test_bounded_menu_requires_complete_pair_and_cannot_drop_failed_root(tmp_path):
    from decimal import Decimal
    study, selection, cases, provenance = setup(tmp_path)
    configs = binding.configs(study, tuple(c.root for c in cases), tuple(c.identity for c in cases), provenance.identity)
    products = tuple(Sci02BProduct('product.' + c.node_id, c, (), cases[0].arrays, 'AVAILABLE', (),
        (('primary.joint_success', Decimal(int(c.candidate_dimension == 32 or c.root.ordinal != 3))),))
        for c in configs if c.phase == 'diagnose')
    dimension, selected = development.selection(products)
    assert dimension == 32 and len(selected) == 8
    with pytest.raises(ValueError, match='omits'):
        development.selection(products[1:])
    failed = tuple(replace(p, measurements=(('primary.joint_success', Decimal(0)),)) if p.config.root.ordinal == 3 else p for p in products)
    assert development.selection(failed) == (0, ())


def test_causal_response_model_and_independent_read_refuse_response_substitution(actual_fixture, monkeypatch):
    d, _, _, sealed, _, handoff, _, observation, _, first, second = actual_fixture
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as old_reader
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_read as reader
    origin = science.origin_model(d, handoff.arrays, sealed.arrays, 24)
    result = science.refresh_model(d, origin.arrays, observation.arrays)
    # The complete three-arm diagnosis fits the existing bounded NPZ contract.
    native = {recipe: {f'{v}.p{p}.native': result.arrays[f'{v}.p{p}.updated']
        for v, _ in science.VIEWS for p in (0, 1)} for recipe in ('ORIGINAL', 'EARLY', 'DELAYED')}
    assessment = reader.assess_pair(d, native, {recipe: result.arrays for recipe in native})
    _, members = encode_matrix_arrays({**{recipe.lower() + '.model.' + k: v
        for recipe in native for k, v in result.arrays.items()}, **{'assessment.' + k: v for k, v in assessment.arrays.items()}})
    assert len(members) <= 256
    def forbidden(*args, **kwargs): pytest.fail('independent reader entered the response producer or RNG')
    monkeypatch.setattr(science, 'input_basis', forbidden)
    monkeypatch.setattr(science, 'continue_response_window', forbidden)
    monkeypatch.setattr(np.random, 'Generator', forbidden)
    assert np.isfinite(reader.model_checks(d, handoff.arrays, observation.arrays, result.arrays)).all()
    with pytest.raises(ValueError, match='outside'):
        science.refresh_model(d, origin.arrays, {**observation.arrays, 'future.response': np.zeros(1)})
    bad = dict(result.arrays)
    bad['primary.p0.updated'] = bad['primary.p0.updated'].copy()
    bad['primary.p0.updated'][0, -1, 0] += .1
    with pytest.raises(ValueError, match='affine'):
        reader.model_checks(d, handoff.arrays, observation.arrays, bad)
    joined = old_reader.joined(first.arrays, second.arrays)
    native = reader.native_response(d, handoff.arrays, sealed.arrays, joined)
    assert native['primary.p0.native'].shape == (4, 64, 48)


def test_registered_worker_consumes_real_bounded_ports_and_retains_a_cold_readable_result(tmp_path, actual_fixture):
    from types import SimpleNamespace
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02_read as old_reader
    from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_read as reader
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import decode_matrix_arrays
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
    from empirical_lawhood.execution.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
    from tests.test_matrix_parameter_history import publish
    from tests.runtime_platform.test_native_subwork import _plane
    study, selection, cases, provenance = setup(tmp_path)
    d, _, _, instrument, _, handoff, _, observation, _, first, second = actual_fixture
    native = reader.native_response(d, handoff.arrays, instrument.arrays, old_reader.joined(first.arrays, second.arrays))
    values = {'instrument.' + key: instrument.arrays[key] for key in ('forces', 'receivers', 'source_frame', 'source_spectrum',
        'source_low', 'complement_spectrum', 'complement_vectors', 'source_factor_admitted')}
    # Disclosed transport control: all three arms deliberately use the same
    # test-only EARLY operands. It is not a scientific preparation comparison.
    for recipe in ('original', 'early', 'delayed'):
        for phase, source in (('handoff', handoff.arrays), ('observation', observation.arrays),
                ('assess', {k: v for k, v in native.items() if k.endswith('.native')})):
            values.update({recipe + '.' + phase + '.' + k: v for k, v in source.items()})
    raw, members = encode_matrix_arrays(values)
    old = cases[0]
    artifact = replace(old.arrays.array_artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    retained = replace(old, arrays=replace(old.arrays, array_artifact=artifact, members=members))
    cases = (retained, *cases[1:])
    config = next(c for c in binding.configs(study, tuple(c.root for c in cases), tuple(c.identity for c in cases), provenance.identity)
        if c.phase == 'diagnose' and c.root.ordinal == 0 and c.candidate_dimension == 24)
    plane = _plane(tmp_path / 'bounded-inputs', binary_codecs=MATRIX_STORAGE_CODECS)
    manifests = [publish(plane, value.identity.object_id, value.SCHEMA, value.canonical_bytes()) for value in (config, retained)]
    # Publish the binary operand with its exact registered codec.
    manifests.append(publish(plane, artifact.artifact_id, artifact.payload_schema, raw))
    ports = tuple(plane.open(m, binding=WorkerInputBinding(m.logical.logical_artifact_id, m.materialization.materialization_id,
        m.logical.payload_schema, m.logical.media_type, m.materialization.size_bytes, binding.VISIBILITY, binding.ACCESS,
        WorkerInputKind.EXTERNAL), maximum_bytes=m.materialization.size_bytes) for m in manifests)
    context = SimpleNamespace(input_ports=ports, output_ports=tuple(WorkerOutputPort(config.node_id + '.' + key, schema, profile,
        media, config.node_id + '.' + key) for key, schema, profile, media in (
            ('product', Sci02BProduct.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json'),
            ('arrays', binding.MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz'))),
        task_id=config.node_id, config=SimpleNamespace(config_id=config.config_id, content_sha256=config.fingerprint()),
        resource_budget=binding.BUDGET, permissions=binding.PERMISSIONS, outcome_access=binding.ACCESS)
    declaration = next(d for d in binding.operation_declarations() if d.capability_key.endswith('.diagnose'))
    result = declaration.provider_factory().runner_factory().execute(context)
    product = decode_canonical_bytes(next(p.payload for p in result.outputs if p.output_id.endswith('.product')), Sci02BProduct, maximum_bytes=None)
    arrays = dict(decode_matrix_arrays(next(p.payload for p in result.outputs if p.output_id.endswith('.arrays')), product.arrays))
    development.verify_diagnosis(config, retained, dict(decode_matrix_arrays(raw, retained.arrays)), product, arrays)
    assert product.native == () and dict(product.measurements)['assigned'] == 1
