# SPDX-License-Identifier: MPL-2.0
"""Actual journal/publication controls over disclosed software launch events.

No native worker is entered and synthetic fixture grants are not qualification.
"""

from dataclasses import replace
from types import SimpleNamespace
import threading

import pytest

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator, LocalScheduler
from empirical_lawhood.infrastructure.execution_resource_envelopes import (
    ExternalExecutionResourceEnvelopeStore, execution_launch_relative_path, read_execution_launch_event,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeEventKind
from tests.runtime_platform.test_execution_scheduler import _plane
from tests.test_current_result_custody import actual_issued_current_task_controls as actual_issued_current_task_controls


def launched_controls(f, *, at_utc='2026-08-23T20:43:00Z', store=None):
    f.context = replace(f.context,
        attempt_id=f'{f.context.run_id}.{f.context.task_id}.attempt-001')
    plane = f.control.service.artifact_plane
    package = f.control.package
    store = store or ExternalExecutionResourceEnvelopeStore(plane.root, artifact_plane=plane)
    coordinator = DurableExecutionResourceEnvelopeCoordinator(store)
    envelope_id = f'run-resource-envelope.{package.run_plan_id}'
    spec = package.execution_resource_envelope_spec
    cell, = (cell for cell in spec.task_cells if cell.task_id == f.context.task_id)
    coordinator.initialize(envelope_id=envelope_id, spec=spec,
        execution_plan=ObjectIdentity.from_record(f.plan.execution_plan_id, f.plan),
        jit_graph_signature_manifest=package.jit_graph_signature_manifest)
    coordinator.reserve(envelope_id=envelope_id,
        event_id=f'resource-envelope-event.{f.context.attempt_id}.reserve', occurred_at_utc=at_utc,
        cell_id=cell.cell_id, attempt_id=f.context.attempt_id)
    projection = None
    if cell.jit_cell_id is not None:
        projection, = (value for value in package.jit_graph_signature_manifest.cell_projections
            if value.cell_id == cell.jit_cell_id)
    launch = dict(envelope_id=envelope_id,
        event_id=f'resource-envelope-event.{f.context.attempt_id}.launch', occurred_at_utc=at_utc,
        cell_id=cell.cell_id, attempt_id=f.context.attempt_id, jit_projection=projection,
        jit_graph_signature_manifest=package.jit_graph_signature_manifest)
    envelope = coordinator.launch(**launch)
    return SimpleNamespace(plane=plane, store=store, coordinator=coordinator, envelope=envelope,
        event=envelope.events[-1], launch=launch, cell=cell)


def read_launch(f, plane=None, **changes):
    arguments = dict(artifact_plane=f.control.service.artifact_plane if plane is None else plane,
        execution_plan=f.plan, resource_spec=f.control.package.execution_resource_envelope_spec,
        run_id=f.context.run_id, task_id=f.context.task_id, attempt_id=f.context.attempt_id)
    arguments.update(changes)
    return read_execution_launch_event(**arguments)


def test_normal_launch_publishes_exact_primary_bytes_before_return_without_read_replay(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    launched = launched_controls(f)
    path = execution_launch_relative_path(run_id=f.context.run_id,
        task_id=f.context.task_id, attempt_id=f.context.attempt_id)
    assert launched.plane.root.resolve(path, for_write=False).read_bytes() == launched.event.canonical_bytes()
    assert launched.event.canonical_bytes() in launched.store._path(launched.envelope.envelope_id, 'journal').read_bytes()
    assert launched.store.load(launched.envelope.envelope_id) == launched.envelope

    def forbidden(*_args, **_kwargs):
        pytest.fail('bounded completed-read lookup replayed the operational journal')

    monkeypatch.setattr(ExternalExecutionResourceEnvelopeStore, 'load', forbidden)
    monkeypatch.setattr(ExternalExecutionResourceEnvelopeStore, 'current', forbidden)
    monkeypatch.setattr(ExternalExecutionResourceEnvelopeStore, '_read', forbidden)
    assert read_launch(f) == launched.event
    assert not f.control.executor.invocations


def test_retained_publication_reader_reuses_issue_decode_and_keeps_final_byte_guard(
        actual_issued_current_task_controls, monkeypatch):
    from empirical_lawhood.api.protected_e3_read_custody import _publication
    from empirical_lawhood.infrastructure.study_issue import ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore, PROGRAMME_ISSUE_GRANTEE_ID
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    publisher = ExternalIssuedStudyPublisher(artifact_plane=plane,
        authority_store=ExternalStudyOperationAuthorityStore(plane), grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)
    original = ExternalIssuedStudyPublisher._load_executable_study
    calls = []
    def observe(self, issue_id, **options):
        calls.append(issue_id)
        return original(self, issue_id, **options)
    monkeypatch.setattr(ExternalIssuedStudyPublisher, '_load_executable_study', observe)
    with pytest.raises(ArtifactIdentityConflict):
        with publisher.read_context() as reading:
            _publication(plane, f.control.package, publication_reader=reading)
            _publication(plane, f.control.package, publication_reader=reading)
            assert calls == [f.control.package.issued_study.issue_id]
            path = plane.root.resolve('issued-programmes/' + calls[0] + '/executable-study-manifest.json', for_write=False)
            path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ArtifactIdentityConflict, match='ended'):
        reading.load_executable_study(calls[0])
    assert not f.control.executor.invocations


def test_interrupted_derivative_publication_keeps_primary_launch_and_scheduler_adopts_same_event(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    store = ExternalExecutionResourceEnvelopeStore(plane.root, artifact_plane=plane)
    original = store._publish_launch_event
    calls = []

    def interrupted(envelope, event):
        # The primary head and full replay already authenticate this exact event
        # before the derivative writer is contacted.
        assert store._cached[1] == envelope
        assert store._path(envelope.envelope_id, 'head').is_file()
        assert store._path(envelope.envelope_id, 'journal').read_bytes().endswith(event.canonical_bytes())
        calls.append(event)
        raise OSError('disclosed interruption before derivative publication')

    monkeypatch.setattr(store, '_publish_launch_event', interrupted)
    with pytest.raises(OSError, match='disclosed interruption'):
        launched_controls(f, store=store)
    envelope_id = f'run-resource-envelope.{f.context.run_id}'
    committed = store.current(envelope_id)
    assert committed.events[-1] == calls[0]
    assert len(tuple(event for event in committed.events if event.kind is ExecutionResourceEnvelopeEventKind.LAUNCH)) == 1
    with pytest.raises((FileNotFoundError, ValueError, ArtifactIdentityConflict)):
        read_launch(f)
    monkeypatch.setattr(store, '_publish_launch_event', original)
    coordinator = DurableExecutionResourceEnvelopeCoordinator(store)
    # Exercise the real scheduler's same-attempt adoption branch, without a
    # scheduler run, provider, clock call, worker contact, or second launch.
    cell, = (cell for cell in committed.spec.task_cells if cell.task_id == f.context.task_id)
    scheduler = SimpleNamespace(execution_resource_envelope_coordinator=coordinator,
        execution_resource_envelope_id=envelope_id, _resource_envelope_transition_lock=threading.RLock(),
        _resource_envelope_cell_id=lambda task_id: cell.cell_id)
    LocalScheduler._launch_envelope_attempt(scheduler, f.context.task_id, f.context.attempt_id)
    assert read_launch(f) == calls[0]
    assert store.load(envelope_id) == committed
    assert not f.control.executor.invocations


@pytest.mark.parametrize('change', ('run', 'task', 'attempt', 'plan', 'resource'))
def test_launch_publication_refuses_another_run_task_attempt_or_frozen_parent(
        actual_issued_current_task_controls, change):
    f = actual_issued_current_task_controls
    launched_controls(f)
    if change == 'plan':
        changes = dict(execution_plan=replace(f.plan, implementation_commit='f' * 40))
    elif change == 'resource':
        spec = replace(f.control.package.execution_resource_envelope_spec, envelope_spec_id='resource.foreign')
        changes = dict(resource_spec=spec)
    else:
        key = {'run': 'run_id', 'task': 'task_id', 'attempt': 'attempt_id'}[change]
        changes = {key: 'foreign.' + getattr(f.context, key)}
    with pytest.raises((PermissionError, FileNotFoundError, ValueError, ArtifactIdentityConflict)):
        read_launch(f, **changes)


def test_launch_timestamp_cannot_be_substituted_under_original_publication(
        actual_issued_current_task_controls):
    f = actual_issued_current_task_controls
    launched = launched_controls(f)
    changed = replace(launched.event, occurred_at_utc='2026-08-23T20:44:00Z')
    with pytest.raises(PermissionError, match='committed primary event'):
        launched.store._publish_launch_event(launched.envelope, changed)
    relative = execution_launch_relative_path(run_id=f.context.run_id,
        task_id=f.context.task_id, attempt_id=f.context.attempt_id)
    manifest = launched.plane.read_manifest(relative)
    with pytest.raises(ArtifactIdentityConflict):
        launched.plane.write(ArtifactWriteRequest(
            logical_artifact_id=manifest.logical.logical_artifact_id, relative_path=relative,
            payload_schema=changed.SCHEMA, profile=manifest.logical.profile,
            media_type=manifest.logical.media_type,
            publication_scope_id=manifest.publication.publication_scope.publication_scope_id,
            publication_scope_relative_root=manifest.publication.publication_scope.relative_root,
            payload=changed.canonical_bytes(), visibility_ceiling=manifest.logical.visibility_ceiling,
            parent_visibility_ceilings=manifest.logical.parent_visibility_ceilings,
            outcome_access=manifest.logical.outcome_access, lineage_parents=manifest.logical.lineage_parents))
    assert read_launch(f) == launched.event
    path = launched.plane.root.resolve(execution_launch_relative_path(run_id=f.context.run_id,
        task_id=f.context.task_id, attempt_id=f.context.attempt_id), for_write=False)
    path.write_bytes(changed.canonical_bytes())
    with pytest.raises((ArtifactIdentityConflict, ValueError, PermissionError)):
        read_launch(f)


def test_missing_launch_has_no_preparation_time_or_unpublished_journal_fallback(actual_issued_current_task_controls):
    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    store = ExternalExecutionResourceEnvelopeStore(plane.root)
    launched = launched_controls(f, store=store)
    assert launched.store.load(launched.envelope.envelope_id).events[-1] == launched.event
    with pytest.raises((FileNotFoundError, ValueError, ArtifactIdentityConflict)):
        read_launch(f)
    with pytest.raises(PermissionError, match='guarded artifact plane'):
        store.ensure_launch_publication(envelope_id=launched.envelope.envelope_id,
            task_id=f.context.task_id, attempt_id=f.context.attempt_id)


def test_launch_read_refuses_a_valid_publication_with_unrelated_members_before_payload_verification(
        actual_issued_current_task_controls, tmp_path, monkeypatch):
    f = actual_issued_current_task_controls
    launched_controls(f)
    event = read_launch(f)
    relative = execution_launch_relative_path(run_id=f.context.run_id,
        task_id=f.context.task_id, attempt_id=f.context.attempt_id)
    original = f.control.service.artifact_plane.read_manifest(relative)
    root = tmp_path / 'mixed-publication'
    root.mkdir()
    plane = _plane(root)
    request = ArtifactWriteRequest(logical_artifact_id=original.logical.logical_artifact_id,
        relative_path=relative, payload_schema=event.SCHEMA, profile=original.logical.profile,
        media_type=original.logical.media_type,
        publication_scope_id=original.publication.publication_scope.publication_scope_id,
        publication_scope_relative_root=original.publication.publication_scope.relative_root,
        payload=event.canonical_bytes(), visibility_ceiling=original.logical.visibility_ceiling,
        parent_visibility_ceilings=original.logical.parent_visibility_ceilings,
        outcome_access=original.logical.outcome_access, lineage_parents=original.logical.lineage_parents)
    extra = replace(request, logical_artifact_id='unrelated.disclosed.event',
        relative_path=relative.rsplit('/', 1)[0] + '/unrelated.json')
    plane.write_batch((request, extra))

    def forbidden(*args, **kwargs):
        pytest.fail('non-exact launch publication expanded payload verification')

    monkeypatch.setattr(plane, 'verify_manifest', forbidden)
    with pytest.raises(PermissionError, match='exact immutable publication'):
        read_launch(f, plane=plane)
