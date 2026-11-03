# SPDX-License-Identifier: MPL-2.0
"""Issued raw-dependency replay uses synthetic custody, never real qualification."""

from dataclasses import replace
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_artifact_manifest
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform import test_recursive_prospective_workflow as workflow
from tests.runtime_platform.test_recursive_prospective_parents import _authenticate, _parent_inputs


@pytest.fixture(scope='module')
def raw_parent_fixture(tmp_path_factory):
    from empirical_lawhood.adapters.reference_worlds.runtime import REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE

    positive = replace(REFERENCE_NEGATIVE_ADJUDICATION_FIXTURE,
        fixture_id='fixture.synthetic-raw-parent-supported', scientific_status=ScientificStatus.SUPPORTED,
        admission_status=AdmissionStatus.ADMITTED, reason_codes=('SYNTHETIC_PARENT_SUPPORTED',))
    raw, _ = encode_matrix_arrays({'prepared': np.asarray([1 + 2j, 3 - 4j], dtype='<c16')})
    original_fixture, original_execute = workflow.prospective_fixture, workflow._TypedFixtureRunner.execute

    def with_raw_dependency(**kwargs):
        compiled, authoring, context = original_fixture(**kwargs)
        raw_edges = {(edge.consumer_node_id, edge.consumer_input_id) for edge in compiled.template.graph.edges
                     if edge.producer_node_id == 'prepare'}
        registrations = tuple(replace(registration,
            storage_codecs=MATRIX_STORAGE_CODECS if registration.selection.capability_key == 'recursive-fixture.prepare'
                or any(node == registration.selection.capability_key.removeprefix('recursive-fixture.')
                    for node, _ in raw_edges) else registration.storage_codecs,
            outputs=tuple(replace(output, payload_schema=MATRIX_ARRAY_SCHEMA, profile=ArtifactProfile.MATRIX_ARRAY_NPZ,
                                  media_type='application/x-npz', filename_suffix='.npz')
                          if registration.selection.capability_key == 'recursive-fixture.prepare' else output
                          for output in registration.outputs),
            input_ports=tuple(replace(port, payload_schema=MATRIX_ARRAY_SCHEMA, media_type='application/x-npz')
                              if (registration.selection.capability_key.removeprefix('recursive-fixture.'), port.port_id)
                              in raw_edges else port for port in registration.input_ports))
            for registration in workflow._registrations(compiled))
        registry = replace(compiled.registry, capabilities=tuple(replace(manifest,
            output_schema_ids=(MATRIX_ARRAY_SCHEMA,) if manifest.capability_key == 'recursive-fixture.prepare'
                              else manifest.output_schema_ids,
            input_schema_ids=tuple(sorted({*manifest.input_schema_ids, MATRIX_ARRAY_SCHEMA}))
                if any(node == manifest.capability_key.removeprefix('recursive-fixture.') for node, _ in raw_edges)
                else manifest.input_schema_ids) for manifest in compiled.registry.capabilities))
        compiled = compile_recursive_wave(draft=compiled.draft, registrations=registrations, registry=registry,
            implementation_commit='a' * 40, qualifications=compiled.candidate_context.qualifications,
            known_design_inputs=compiled.candidate_context.known_design_inputs, output_codecs=compiled.output_codecs)
        assert compiled.candidate_report.candidate is not None, compiled.candidate_report.diagnostics
        return compiled, authoring, context

    def produce_raw(self, context):
        if context.task_id != 'prepare':
            return original_execute(self, context)
        for port in context.input_ports:
            port.read(port.size_bytes + 1)
        return RunnerResult(tuple(TaskOutputPayload(output.output_id, raw) for output in context.output_ports),
                            (ReceiptCheck('synthetic-raw-dependency', True, ()),))

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(workflow, 'prospective_fixture', with_raw_dependency)
        monkeypatch.setattr(workflow._TypedFixtureRunner, 'execute', produce_raw)
        fixture = workflow._public_run_handoff_fixture(tmp_path_factory.mktemp('raw-qualified-parent'), monkeypatch,
                                                       sealed_fixture=positive, reveal_terminal=True)
        fixture.raw_dependency_payload = raw
        yield fixture


def _raw_dependency(fixture):
    run_id = fixture.package.run_plan_id
    receipt = ExternalTaskReceiptStore(fixture.plane).read(run_id, 'prepare', f'{run_id}.prepare.attempt-001')
    assert receipt is not None
    logical, = receipt.output_logical_artifacts
    physical, = receipt.output_materializations
    path = fixture.plane.root.resolve(physical.relative_path, for_write=False)
    return receipt, logical, physical, path


def test_issued_parent_replays_raw_dependency_without_canonical_codec(raw_parent_fixture):
    fixture = raw_parent_fixture
    receipt, logical, physical, path = _raw_dependency(fixture)
    sidecar = path.with_name(path.name + '.manifest.json')
    original = sidecar.read_bytes()
    manifest = decode_artifact_manifest(original)
    assert manifest.publication is not None
    assert logical.profile is ArtifactProfile.MATRIX_ARRAY_NPZ
    assert MATRIX_ARRAY_SCHEMA not in fixture.handoff.compilation.output_codecs
    assert logical.content_sha256 == physical.physical_sha256 == sha256(fixture.raw_dependency_payload).hexdigest()
    assert not logical.semantic_validation.top_level_keys and not logical.semantic_validation.value_keys

    parent, = _authenticate(fixture)

    assert parent.execution_plan == fixture.execution_plan
    assert parent.product_payload == fixture.adjudication.canonical_bytes()
    assert parent.adjudication.scientific_status is ScientificStatus.SUPPORTED
    assert sidecar.read_bytes() == original and path.read_bytes() == fixture.raw_dependency_payload
    assert _raw_dependency(fixture)[0] == receipt
    assert fixture.executor.invocations == 5


@pytest.mark.parametrize('damage', ['malformed-npz', 'altered-array', 'missing-publication'])
def test_changed_raw_dependency_refuses_before_qualified_product_read(raw_parent_fixture, monkeypatch, damage):
    from empirical_lawhood.api import recursive_qualified_parents as owner

    fixture = raw_parent_fixture
    _, _, _, path = _raw_dependency(fixture)
    target = path.with_name(path.name + '.manifest.json') if damage == 'missing-publication' else path
    original = target.read_bytes()
    monkeypatch.setattr(owner, '_output_payload', lambda *args: pytest.fail('qualified product read before raw custody'))
    try:
        if damage == 'missing-publication':
            target.unlink()
        elif damage == 'malformed-npz':
            target.write_bytes(b'not an NPZ archive')
        else:
            changed, _ = encode_matrix_arrays({'prepared': np.asarray([1 + 2j, 3 + 4j], dtype='<c16')})
            assert changed != original
            target.write_bytes(changed)
        with pytest.raises((PermissionError, RuntimeError, FileNotFoundError)):
            _authenticate(fixture)
    finally:
        target.write_bytes(original)
    assert fixture.executor.invocations == 5


def test_raw_dependency_still_requires_prior_reveal_before_stream_validation(raw_parent_fixture, monkeypatch):
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    from empirical_lawhood.runtime import artifacts

    fixture = raw_parent_fixture
    original = ExternalStudyOperationAuthorityStore.load

    def load(self, authority_id):
        if authority_id == fixture.reveal.authority_id:
            raise PermissionError('synthetic prior reveal grant unavailable')
        return original(self, authority_id)

    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', load)
    monkeypatch.setattr(artifacts, 'verify_artifact_manifests',
                        lambda *args: pytest.fail('raw dependency streamed before reveal authority'))
    with pytest.raises(PermissionError, match='prior reveal grant'):
        _authenticate(fixture)


def test_raw_dependency_does_not_relax_canonical_output_codecs(raw_parent_fixture):
    from empirical_lawhood.api.recursive_qualified_parents import authenticate_recursive_qualified_parents

    fixture = raw_parent_fixture
    draft, registrations, binding = _parent_inputs(fixture)
    with pytest.raises(PermissionError, match='installed typed scientific codec'):
        authenticate_recursive_qualified_parents(spec_bindings=(binding,), draft=draft,
            artifact_writer=fixture.plane, registrations=registrations, output_codecs={})
