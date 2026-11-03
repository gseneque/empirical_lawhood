# SPDX-License-Identifier: MPL-2.0
"""Historical launch authority and current reveal over actual software custody.

Synthetic disclosed grants/outputs establish software controls only. No worker,
scientific qualification, acquisition, or production outcome read occurs.
"""

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import current_result_custody as owner
from empirical_lawhood.api import protected_e3_read_custody as protected
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, ReceiptCheck
from tests.runtime_platform.test_recursive_compiler import Config
from tests.test_current_result_custody import actual_issued_current_task_controls as actual_issued_current_task_controls
from tests.test_execution_launch_custody import launched_controls


class LaterClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2030, 1, 1, tzinfo=UTC)


def completed_output(f):
    """Publish one task's exact output census and actual receipt, no execution."""
    f.context = replace(f.context,
        attempt_id=f'{f.context.run_id}.{f.context.task_id}.attempt-001')
    plane = f.control.service.artifact_plane
    task, = (task for task in f.plan.tasks if task.task_id == f.context.task_id)
    artifacts = []
    for output in task.outputs:
        assert output.payload_schema == Config.SCHEMA
        record = Config(f'disclosed.completed.{output.output_id}', 1)
        artifacts.append(plane.write(ArtifactWriteRequest(
            logical_artifact_id=output.logical_artifact_id, relative_path=output.relative_path,
            payload_schema=output.payload_schema, profile=ArtifactProfile.CANONICAL_JSON,
            media_type=output.media_type, publication_scope_id=f'disclosed.output.{task.task_id}',
            publication_scope_relative_root=f'runs/{f.context.run_id}', payload=record.canonical_bytes(),
            visibility_ceiling=output.visibility_ceiling, parent_visibility_ceilings=(),
            outcome_access=output.outcome_access)))
    logical = tuple(sorted((row.logical for row in artifacts), key=lambda row: row.logical_artifact_id))
    physical = tuple(sorted((row.materialization for row in artifacts), key=lambda row: row.materialization_id))
    receipt = CanonicalTaskReceipt(f'receipt.{f.context.attempt_id}', f.context.run_id, task.task_id,
        f.context.attempt_id, f.plan.implementation_commit, (), physical, logical,
        (ReceiptCheck('disclosed.metadata-contract', True, ()),), OperationalStatus.SUCCEEDED, ())
    ExternalTaskReceiptStore(plane, minimum_free_bytes=1).commit(receipt,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return receipt, logical[0]


def later_reveal(f):
    reveal = replace(f.control.reveal, authority_id=f.control.reveal.authority_id + '.later',
        issued_at_utc='2028-01-01T00:00:00Z', expires_at_utc='2031-01-01T00:00:00Z')
    ExternalStudyOperationAuthorityStore(f.control.service.artifact_plane).persist(reveal)
    return reveal


def authenticate(f, receipt, logical):
    return owner.authenticate_current_result_plan_outputs(package=f.control.package,
        issued=f.control.package.issued_study, receipt=receipt, logical=logical,
        writer=f.control.service.artifact_plane, capability_prefixes=('recursive-fixture.',))


def test_completed_read_uses_original_grant_at_launch_and_only_current_reveal_at_access(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    launched = launched_controls(f)
    receipt, logical = completed_output(f)
    reveal = later_reveal(f)
    monkeypatch.setattr(owner, 'datetime', LaterClock)
    assert f.control.package.execution_authority.expires_at_utc < '2030-01-01T00:00:00Z'
    loaded = []
    load = ExternalStudyOperationAuthorityStore.load

    def observed(self, authority_id):
        loaded.append(authority_id)
        return load(self, authority_id)

    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', observed)
    assert authenticate(f, receipt, logical) == f.plan
    assert owner.authenticate_historical_execution_authority(package=f.control.package,
        execution_plan=f.plan, receipt=receipt, writer=launched.plane) == launched.event
    protected.authorize(launched.plane, f.control.package, reveal.authority_id)
    assert loaded.count(f.control.package.execution_authority.authority_id) == 2
    assert loaded[-1] == reveal.authority_id
    assert not any('source' in value or 'retry' in value for value in loaded)
    assert not f.control.executor.invocations


@pytest.mark.parametrize('launch_time', ('2026-08-21T20:43:00Z', '2028-08-23T20:43:00Z'))
def test_original_execution_grant_must_be_effective_at_actual_launch(
        actual_issued_current_task_controls, launch_time, monkeypatch):
    f = actual_issued_current_task_controls
    launched_controls(f, at_utc=launch_time)
    receipt, logical = completed_output(f)
    monkeypatch.setattr(owner, 'datetime', LaterClock)
    with pytest.raises(PermissionError, match='not yet effective|expired'):
        authenticate(f, receipt, logical)


def test_current_reveal_expiry_or_store_refusal_blocks_completed_access(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    launched_controls(f)
    receipt, logical = completed_output(f)
    monkeypatch.setattr(owner, 'datetime', LaterClock)
    assert authenticate(f, receipt, logical) == f.plan
    with pytest.raises(PermissionError, match='expired'):
        protected.authorize(f.control.service.artifact_plane, f.control.package, f.control.reveal.authority_id)
    reveal = later_reveal(f)
    protected.authorize(f.control.service.artifact_plane, f.control.package, reveal.authority_id)
    load = ExternalStudyOperationAuthorityStore.load

    def revoked(self, authority_id):
        if authority_id == reveal.authority_id:
            raise PermissionError('actual current reveal access refused')
        return load(self, authority_id)

    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', revoked)
    with pytest.raises(PermissionError, match='current reveal access refused'):
        protected.authorize(f.control.service.artifact_plane, f.control.package, reveal.authority_id)


def test_historical_execution_store_refusal_and_missing_launch_are_not_package_trust_fallbacks(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    receipt, logical = completed_output(f)
    with pytest.raises((FileNotFoundError, ValueError, ArtifactIdentityConflict)):
        authenticate(f, receipt, logical)
    launched_controls(f)
    load = ExternalStudyOperationAuthorityStore.load

    def refused(self, authority_id):
        if authority_id == f.control.package.execution_authority.authority_id:
            raise PermissionError('original authority custody refused')
        return load(self, authority_id)

    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', refused)
    with pytest.raises(PermissionError, match='original authority custody refused'):
        authenticate(f, receipt, logical)


def test_scoped_reader_reuses_historical_fact_but_not_current_reveal(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    launched_controls(f)
    receipt, logical = completed_output(f)
    reveal = later_reveal(f)
    monkeypatch.setattr(owner, 'datetime', LaterClock)
    event_reads = []
    read = owner.read_execution_launch_event

    def counted(**kwargs):
        event_reads.append((kwargs['task_id'], kwargs['attempt_id']))
        return read(**kwargs)

    monkeypatch.setattr(owner, 'read_execution_launch_event', counted)
    with f.control.service.artifact_plane.verification_scope() as writer:
        reader = owner.CurrentResultPlanReader(writer)
        for _ in range(2):
            assert reader.authenticate(package=f.control.package, issued=f.control.package.issued_study,
                receipt=receipt, logical=logical, capability_prefixes=('recursive-fixture.',)) == f.plan
            protected._current_read_grants(writer, f.control.package, reveal.authority_id)
        assert event_reads == [(receipt.task_id, receipt.attempt_id)]
    with pytest.raises(ArtifactIdentityConflict, match='scope has ended'):
        reader.authenticate(package=f.control.package, issued=f.control.package.issued_study,
            receipt=receipt, logical=logical, capability_prefixes=('recursive-fixture.',))


def test_protected_receipt_history_refuses_before_any_output_payload_contact(
        actual_issued_current_task_controls, monkeypatch):
    f = actual_issued_current_task_controls
    # A real output/receipt alone supplies no authenticated launch history.
    receipt, _ = completed_output(f)
    terminal = SimpleNamespace(attempts=(SimpleNamespace(task_id=receipt.task_id,
        receipt_id=receipt.receipt_id, receipt_sha256=receipt.fingerprint()),))
    plane = f.control.service.artifact_plane
    verify = plane.verify_manifests

    def public_controls_only(manifests):
        if any(row.logical.payload_schema == Config.SCHEMA for row in manifests):
            pytest.fail('missing historical authority contacted scientific output bytes')
        return verify(manifests)

    monkeypatch.setattr(plane, 'verify_manifests', public_controls_only)
    with pytest.raises((FileNotFoundError, ValueError, ArtifactIdentityConflict)):
        protected._completed_task_receipts(plane, f.control.package, f.plan, terminal=terminal,
            expected={receipt.task_id}, capability_prefix='recursive-fixture.')


@pytest.mark.parametrize('original_products', (False, True))
def test_original_e3_rechecks_current_access_after_products_before_return(
        actual_issued_current_task_controls, monkeypatch, original_products):
    from empirical_lawhood.api.domain_composition.matrix_protected_response import scientific_read as reader

    f = actual_issued_current_task_controls
    package = f.control.package
    selected = SimpleNamespace(association=SimpleNamespace(candidate=ObjectIdentity.from_record(
        package.issued_study.candidate.candidate_id, package.issued_study.candidate)),
        implementation=package.issued_study.source_closure,
        projection=SimpleNamespace(tasks=f.plan.tasks))
    specification = SimpleNamespace(identity=ObjectIdentity.from_record('spec.disclosed', Config('spec.disclosed', 1)))
    allocation = SimpleNamespace(identity=ObjectIdentity.from_record('allocation.disclosed', Config('allocation.disclosed', 1)))
    monkeypatch.setattr(reader, '_original_design', lambda selected: (specification, allocation))
    monkeypatch.setattr(reader, '_current_control', lambda **kwargs: package)
    monkeypatch.setattr(reader, 'authenticate_current_execution_plan', lambda **kwargs: f.plan)
    monkeypatch.setattr(reader, '_retained_scientific_writer', lambda package, plan, writer: writer)
    monkeypatch.setattr(reader, '_scientific_projection', lambda *args, **kwargs: {})
    monkeypatch.setattr(reader, 'fitted_training_provenance', lambda *args: {})
    monkeypatch.setattr(reader, 'statistical_task_id', lambda *args, **kwargs: 'task.disclosed')
    monkeypatch.setattr(reader, 'adjudication_task_id', lambda *args, **kwargs: 'adjudication.disclosed')
    products = []

    def product(*args):
        products.append(args[3])
        return object(), {}

    monkeypatch.setattr(reader, '_product', product)
    accesses = []

    def access(*args):
        accesses.append(len(products))
        if products:
            raise PermissionError('current reveal expired during original product access')

    monkeypatch.setattr(reader, '_authorize', access)
    # Supply a canonical terminal with the public identity attribute, without
    # contacting any real product; this isolates the return-boundary control.
    class Terminal(Config):
        @property
        def terminal_event_id(self):
            return self.config_id

    monkeypatch.setattr(reader, '_completed_receipts', lambda *args: ({}, Terminal('terminal.disclosed', 1)))
    with pytest.raises(PermissionError, match='expired during original product access'):
        reader._read_protected_e3_result(selected=selected, artifact_writer=f.control.service.artifact_plane,
            run_id=f.context.run_id, reveal_authority_id='reveal.disclosed',
            include_original_products=original_products)
    assert accesses == [0, 7 if original_products else 5]


@pytest.mark.parametrize('route', ('read', 'bind'))
def test_rc_result_final_access_refusal_prevents_return(monkeypatch, route):
    from empirical_lawhood.api import rc_challenge_results as reader

    state = {'decoded': False, 'accesses': 0}
    receipt = SimpleNamespace(run_id='run.disclosed', task_id='task.disclosed',
        operational_status=OperationalStatus.SUCCEEDED, implementation_commit='a' * 40)
    record = SimpleNamespace(SCHEMA=Config.SCHEMA, fingerprint=lambda: 'b' * 64)

    def decode():
        state['decoded'] = True
        return record

    retained = SimpleNamespace(result_id='result.disclosed', task_receipt=receipt,
        authenticate=lambda writer: None, decode=decode)

    def access(*args, **kwargs):
        state['accesses'] += 1
        if state['decoded']:
            raise PermissionError('current reveal revoked before RC return')

    monkeypatch.setattr(reader, 'authenticate_rc_challenge_result_authority', access)
    monkeypatch.setattr(reader, 'decode_canonical_bytes', lambda *args, **kwargs: retained)
    monkeypatch.setattr(reader, 'RCChallengeRetainedResult', lambda *args: retained)
    with pytest.raises(PermissionError, match='revoked before RC return'):
        if route == 'read':
            reader.read_rc_challenge_result(b'{}', writer=object())
        else:
            reader.bind_rc_challenge_retained_result(result_id='result.disclosed', record_payload=b'{}',
                output_manifest=object(), task_receipt=receipt, receipt_manifest=object(), writer=object())
    assert state['accesses'] == 2


def test_preparation_report_final_access_refusal_prevents_return(monkeypatch):
    from empirical_lawhood.api import preparation_inputs as reader

    state = {'decoded': False, 'accesses': 0}
    receipt = SimpleNamespace(run_id='run.disclosed', task_id='task.disclosed', receipt_id='receipt.disclosed')
    manifest = SimpleNamespace(logical=SimpleNamespace(payload_schema=reader.ConstructedPreparationReport.SCHEMA))
    retained = SimpleNamespace(manifest=manifest, receipt=receipt, result_access=object(), record_payload='{}')
    monkeypatch.setattr(reader, 'ExternalTaskReceiptStore', lambda writer: SimpleNamespace(
        read_by_receipt_id=lambda *args: receipt))

    def decode(*args, **kwargs):
        state['decoded'] = True
        return object()

    def access(*args, **kwargs):
        state['accesses'] += 1
        if state['decoded']:
            raise PermissionError('current reveal revoked before preparation return')

    monkeypatch.setattr(reader, 'decode_canonical_bytes', decode)
    monkeypatch.setattr(reader, 'authenticate_preparation_result_access', access)
    with pytest.raises(PermissionError, match='revoked before preparation return'):
        reader.read_preparation_report(retained, artifact_writer=SimpleNamespace(verify_manifest=lambda manifest: None))
    assert state['accesses'] == 2
