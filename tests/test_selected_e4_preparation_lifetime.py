# SPDX-License-Identifier: MPL-2.0
"""Scheduler-thread preparation lifetime; disclosed scientific admission seams.

The actual storage and finite task-read owners operate on exposed fixtures.
The method operand authenticator is replaced, so this proves no acquisition,
fitting admission or scientific qualification.
"""

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import selected_e4_method_runtime as owner
from empirical_lawhood.api.selected_e3_access import _current_authority_reader, original_e3_authority_read_context
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_development_task_concurrency import _case
from tests.test_matrix_selected_e4_method_workers import fitting_invocation
from tests.test_matrix_selected_e4_methods import (  # noqa: F401
    selected_revision, selected_e4_populations, selected_bridge, transfer, pin,
)
from tests.test_reduced_artifact_verification import _mask_changed_stat


@pytest.mark.parametrize('damage', (None, 'body', 'access'))
def test_scheduler_preparation_owns_one_complete_read_and_final_guard(
        selected_revision, tmp_path, monkeypatch, damage):  # noqa: F811
    case = _case(tmp_path)
    case.plane.maximum_parallel_verifications = 8
    custody = case.custody
    custody.initialize_task_reads()
    runner, context = fitting_invocation(selected_revision)
    runner = runner.with_prepared_scope(None)
    port = next(port for port in context.input_ports if port.artifact_id == context.config.artifact_id)
    raw = port.read(port.size_bytes)
    config = decode_canonical_bytes(raw, owner.owner.SelectedE4MethodConfig, maximum_bytes=None)
    direct = {context.config.artifact_id: SimpleNamespace(materialization=SimpleNamespace(size_bytes=len(raw)))}
    plan = custody.plan
    current = object(), plan, plan.tasks[0]
    calls, readers = [], []
    path = case.plane.root.resolve(case.manifest.materialization.relative_path, for_write=False)

    def current_task(*_):
        calls.append('current')
        if len(calls) == 3:
            if damage == 'body':
                _mask_changed_stat(monkeypatch, path)
                body = path.read_bytes()
                path.write_bytes(b'[' + body[1:])
            elif damage == 'access':
                custody.original_input_access.current = False
        return current

    def operands(*, writer, **_):
        calls.append('operands')
        # ThreadPoolExecutor does not inherit the caller's ContextVars. The
        # supplier must establish its own finite scope around the whole replay.
        assert custody._task_read() is not None, 'revision preparation lost the task read lifetime'
        assert writer is custody.writer
        assert writer._read_verification.context_depth == 1
        assert writer._read_verification.canonical_pool._workers == 8
        assert _current_authority_reader(writer) is not None
        for _ in range(8):
            writer.verify_manifest(writer.read_manifest(case.manifest.materialization.relative_path))
        readers.append(writer)

    monkeypatch.setattr(custody, 'current_task', current_task)
    monkeypatch.setattr(custody, 'task_inputs', lambda *_: ({}, direct))
    monkeypatch.setattr(custody, 'control_record', lambda *_: config)
    custody.inputs = {}
    custody.draft = object()
    monkeypatch.setattr(owner, 'authenticate_selected_e4_development_operands', operands)
    supplier = object.__new__(owner.SelectedE4DevelopmentMethodRuntimeSupplier)
    supplier.writer, supplier.custody, supplier.output_codecs = case.plane, custody, {}

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(supplier.prepare_selected_e4_method, context, runner)
        if damage is None:
            assert future.result().prepared_scope is not None
        else:
            with pytest.raises((ArtifactIdentityConflict, PermissionError)):
                future.result()
    assert calls == ['current', 'operands', 'current']
    assert custody._task_read() is None and custody.writer is case.plane
    for reader in readers:
        with pytest.raises(ArtifactIdentityConflict, match='ended'):
            reader.require_verification_context()


@pytest.mark.parametrize('damage', (False, True))
def test_revision_input_derivation_keeps_one_read_through_observation_projection(tmp_path, monkeypatch, damage):
    """Actual byte lifetime around a disclosed original-result projection."""
    case = _case(tmp_path)
    readers = []
    result = object()

    def derive(*, directory, artifact_writer):
        assert directory == tmp_path
        assert _current_authority_reader(artifact_writer) is not None
        assert getattr(artifact_writer, '_read_verification', None) is not None, 'original result projection lacks a finite read'
        artifact_writer.require_verification_context()
        assert artifact_writer._read_verification.context_depth == 1
        for _ in range(8):
            artifact_writer.verify_manifest(artifact_writer.read_manifest(case.manifest.materialization.relative_path))
        readers.append(artifact_writer)
        if damage:
            path = case.plane.root.resolve(case.manifest.materialization.relative_path, for_write=False)
            _mask_changed_stat(monkeypatch, path)
            raw = path.read_bytes()
            path.write_bytes(b'[' + raw[1:])
        return result

    monkeypatch.setattr(owner, '_complete_selected_e4_revision_inputs_from_acquisition', derive)
    with original_e3_authority_read_context(case.plane):
        if damage:
            with pytest.raises(ArtifactIdentityConflict):
                owner.selected_e4_revision_inputs_from_acquisition(directory=tmp_path,
                    artifact_writer=case.plane, allow_partial=False)
        else:
            assert owner.selected_e4_revision_inputs_from_acquisition(directory=tmp_path,
                artifact_writer=case.plane, allow_partial=False) is result
    assert _current_authority_reader(case.plane) is None
    for reader in readers:
        with pytest.raises(ArtifactIdentityConflict, match='ended'):
            reader.require_verification_context()
