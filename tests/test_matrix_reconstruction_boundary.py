# SPDX-License-Identifier: MPL-2.0
"""Operation routing and current access, without native scientific acquisition."""
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401


@pytest.mark.parametrize('mode,operational', (('off', True), ('full', False)))
def test_public_matrix_read_selects_operational_or_scientific_owner(monkeypatch, mode, operational):
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    plan, context, observed = object(), object(), []
    monkeypatch.setattr(service, '_plan', lambda directory: plan)
    monkeypatch.setattr(service, '_request', lambda *args: None)

    @contextmanager
    def scope(actual, **kwargs):
        assert actual is plan
        yield context

    monkeypatch.setattr(service, '_read_context', scope)
    monkeypatch.setattr(service, '_observe', lambda actual, **kwargs: observed.append(kwargs))
    monkeypatch.setattr(service, '_report', lambda actual, **kwargs: kwargs)
    with scientific_reconstruction_operation(mode):
        report = service.read(directory='/selected/programme')
    assert observed == [{'allow_partial': False, 'operational': operational}]
    assert report == {'allow_partial': False, 'operational': operational}


@pytest.mark.parametrize('pure_output_bytes', (None, 256 * 1024**2))
def test_combined_continuation_publishes_with_owning_writer_inside_read_scope(tmp_path, monkeypatch, pure_output_bytes):
    from pathlib import Path
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.experiment_preparation import prepare_experiment
    from empirical_lawhood.api.matrix_researcher_programme import _publish, PLAN_FILENAME
    from empirical_lawhood.api.composite_experiment_programme import write_experiment_programme_descriptor
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import programme_protocol
    from empirical_lawhood.runtime.experiment_programme import ExperimentProgrammeDescriptor
    from empirical_lawhood.api.retained_e3_evidence import current_e3_evidence
    from tests.test_matrix_programme_preparation_context import _case
    from tests.test_matrix_researcher_programme import ROOT, _execution
    plane, specification, _, profile, _ = _case(tmp_path)
    root = Path(plane.root.contract.canonical_path)
    plan = prepare_experiment(replace(specification, directory='original'), execution=_execution(plane)).programme
    service = ExperimentProgrammeService(ROOT, plane, profile)
    previous = root / 'original'
    _publish(plane, previous / PLAN_FILENAME, plan)
    write_experiment_programme_descriptor(service=service, directory=previous,
        descriptor=ExperimentProgrammeDescriptor('descriptor.' + plan.fingerprint(),
            programme_protocol(plan.specification), plan.specification.identity, plan.identity))

    def derive(actual, **options):
        assert actual.artifact_writer is plane
        assert current_e3_evidence(plane) is not None
        for name in ('specification_path', 'source_selection_path'):
            relative = options[name].relative_to(root).as_posix()
            plane.verify_manifest(plane.read_manifest(relative))
        from empirical_lawhood.api.experiment_preparation import load_experiment_specification
        from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation
        selected = load_experiment_specification(options['specification_path'])
        kind = (source_continuation.MatrixProgrammeSourceContinuationSpecification if pure_output_bytes is None
            else source_continuation.MatrixProgrammeOutputContinuationSpecification)
        assert type(selected) is kind
        if pure_output_bytes is not None:
            assert selected.output_bytes == pure_output_bytes
        raise RuntimeError('reached actual derivation boundary')

    monkeypatch.setattr(ExperimentProgrammeService, 'derive_inputs', derive)
    for name in ('author', 'run'):
        monkeypatch.setattr(ExperimentProgrammeService, name,
            lambda *a, **k: pytest.fail('derivation refusal reached authoring or execution'))
    with pytest.raises(RuntimeError, match='reached actual derivation boundary'):
        service.continue_matrix(predecessor_directory=previous, output_dir=root / 'continued',
            maximum_parallel_tasks=4, confirmed=True, pure_output_bytes=pure_output_bytes)
    assert current_e3_evidence(plane) is None


@pytest.mark.parametrize('refuse_entry', (False, True))
def test_newly_authored_child_reaches_ordinary_entry_without_an_intermediate_status_read(monkeypatch, refuse_entry):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES
    from tests.test_matrix_programme_execution_observation import _complete
    service = MatrixResearchProgrammeService(service=SimpleNamespace(artifact_writer=object()))
    context = SimpleNamespace(bindings={'train': object()},
        observations={phase: _complete(phase) for phase in PHASES if phase != 'train'},
        design=SimpleNamespace(downstream_account='ORIGINAL_E3'))
    calls = []

    def read(*args, **options):
        assert not calls
        calls.append('initial observation')
        return {'state': 'AUTHORING_REQUIRED'}

    def author(*args, **options):
        calls.append('ordinary author')
        return True

    def operate(*args, **options):
        calls.append('ordinary entry')
        if refuse_entry:
            raise PermissionError('fresh entry prerequisite refused')
        return {'status': 'SUCCEEDED', 'read_scope': 'EXECUTION_RECORDS', 'execution_complete': True}

    monkeypatch.setattr(service, '_read_phase', read)
    monkeypatch.setattr(service, '_author_phase', author)
    monkeypatch.setattr(service, '_operate_phase', operate)
    monkeypatch.setattr(service, '_advance_report', lambda actual, dependencies: actual.observations['train'])
    if refuse_entry:
        with pytest.raises(PermissionError, match='fresh entry prerequisite'):
            service._advance(context, mode='run', confirmed=True)
    else:
        assert service._advance(context, mode='run', confirmed=True).execution_complete
    assert calls == ['initial observation', 'ordinary author', 'ordinary entry']


@pytest.fixture
def recorded_controls(actual_issued_current_task_controls):  # noqa: F811
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recovery import build_run_recovery_index
    f = actual_issued_current_task_controls
    package = f.control.package
    index = build_run_recovery_index(f.plan, run_id=package.run_plan_id, wave_id='wave.' + package.package_id,
        authority_identities=tuple(sorted((
            ObjectIdentity.from_record(package.scientific_approval.authorization_id, package.scientific_approval),
            ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority)),
            key=lambda value: value.object_id)))
    ExternalRunRecoveryStore(f.control.service.artifact_plane, minimum_free_bytes=1).freeze(index)
    return f


def test_recorded_issued_controls_preserve_extended_source_and_refuse_incomplete_terminal(recorded_controls):
    from empirical_lawhood.api.recorded_execution_controls import completed_issued_execution
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    f = recorded_controls
    package = f.control.package
    locator = SimpleNamespace(run_id=package.run_plan_id,
        package=ObjectIdentity.from_record(package.package_id, package))
    with f.control.service.artifact_plane.read_context() as writer:
        with pytest.raises(PermissionError, match='complete terminal and receipt census'):
            completed_issued_execution(writer=writer, locator=locator,
                candidate=ObjectIdentity.from_record(package.issued_study.candidate.candidate_id,
                    package.issued_study.candidate),
                terminal=ObjectIdentity.from_record('absent-terminal', f.plan))


def test_retained_evidence_reuses_only_immutable_controls_and_rechecks_reveal(recorded_controls, monkeypatch):
    from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context, current_e3_evidence
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    f = recorded_controls
    plane = f.control.service.artifact_plane
    load = ExternalStudyOperationAuthorityStore.load
    reads = []

    def observed(store, authority_id):
        reads.append(authority_id)
        return load(store, authority_id)

    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', observed)
    with retained_e3_evidence_context(plane) as retained:
        first = retained.producer(f.context.run_id, f.control.reveal.authority_id)
        count = len(reads)
        assert retained.producer(f.context.run_id, f.control.reveal.authority_id) is first
        assert len(reads) > count
        assert first.report['execution_complete'] is False
        assert first.report['new_native_contact_count'] == 0
        assert current_e3_evidence(retained.writer) is retained

        def expired(store, authority_id):
            value = load(store, authority_id)
            return replace(value, expires_at_utc='2026-08-23T20:43:00Z') if authority_id == f.control.reveal.authority_id else value

        with monkeypatch.context() as patch:
            patch.setattr(ExternalStudyOperationAuthorityStore, 'load', expired)
            with pytest.raises(PermissionError):
                retained.producer(f.context.run_id, f.control.reveal.authority_id)
    assert current_e3_evidence(plane) is None
    with pytest.raises(PermissionError, match='escaped'):
        retained.require_access()


def test_retained_evidence_refuses_changed_original_control_at_close(recorded_controls):
    from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context
    f = recorded_controls
    plane = f.control.service.artifact_plane
    consumed = False
    with pytest.raises((ValueError, RuntimeError, OSError)):
        with retained_e3_evidence_context(plane) as retained:
            retained.producer(f.context.run_id, f.control.reveal.authority_id)
            consumed = True
            path = plane.root.resolve('runs/' + f.context.run_id + '/plans/execution-plan.json', for_write=False)
            path.write_bytes(path.read_bytes() + b' ')
    assert consumed


@pytest.fixture
def recorded_output_views(recorded_controls, monkeypatch):
    """Use the real reference plan's codecs; execute no task or Matrix science."""
    from empirical_lawhood.api import recursive_operations
    from empirical_lawhood.adapters.reference_worlds.runtime import ReferenceAdjudicationFixture
    from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
    from tests.runtime_platform.test_recursive_prospective_workflow import Config
    codecs = {kind.SCHEMA: kind for kind in (Config, ReferenceAdjudicationFixture, ScientificAdjudicationRecord)}
    original = recursive_operations.operation_catalog
    # The issued reference fixture uses these declared codecs, independently of
    # the Matrix numerical catalogue. The actual output-registry builder runs.
    def catalog():
        declarations, registrations, installed = original()
        return declarations, registrations, {**installed, **codecs}
    monkeypatch.setattr(recursive_operations, 'operation_catalog', catalog)
    return recorded_controls


def test_registered_output_view_reuses_controls_but_refreshes_current_grants(recorded_output_views, monkeypatch):
    from empirical_lawhood.api import recursive_qualified_parents
    from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context, current_e3_evidence
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    f = recorded_output_views
    packages, grants = [], []
    actual_package = recursive_qualified_parents._actual_package
    actual_grant = ExternalStudyOperationAuthorityStore.load
    def package(*args, **kwargs):
        packages.append(args[1])
        return actual_package(*args, **kwargs)
    def grant(store, authority_id):
        grants.append(authority_id)
        return actual_grant(store, authority_id)
    monkeypatch.setattr(recursive_qualified_parents, '_actual_package', package)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', grant)
    with retained_e3_evidence_context(f.control.service.artifact_plane) as retained:
        producer = retained.producer(f.context.run_id, f.control.reveal.authority_id)
        view = producer.writer
        policy = view.semantic_validations
        assert policy is not retained.writer.semantic_validations
        assert current_e3_evidence(view) is retained
        before = len(grants)
        for _ in range(3):
            with retained_e3_evidence_context(view) as nested:
                assert nested is retained
                assert nested.producer(f.context.run_id, f.control.reveal.authority_id) is producer
                assert producer.writer is view and view.semantic_validations is policy
        assert packages == [f.context.run_id] and len(grants) > before
    assert current_e3_evidence(view) is None
    with pytest.raises(PermissionError, match='escaped'):
        _ = producer.writer


@pytest.mark.parametrize('changed', ('foreign-view', 'registry', 'custom-policy'))
def test_output_control_reuse_rejects_unregistered_or_changed_views(recorded_output_views, monkeypatch, changed):
    from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context, current_e3_evidence
    f = recorded_output_views
    with retained_e3_evidence_context(f.control.service.artifact_plane) as retained:
        producer = retained.producer(f.context.run_id, f.control.reveal.authority_id)
        view = producer.writer
        original = view.semantic_validations
        with monkeypatch.context() as patch:
            if changed == 'foreign-view':
                selected = retained.writer.with_semantic_validation_registry(original)
            elif changed == 'registry':
                patch.setattr(view, 'semantic_validations', replace(original, registry_id='changed.output-policy'))
                selected = view
                assert producer.writer is view  # Retrieval must not renew a changed registration.
            else:
                patch.setitem(vars(view), 'verify_manifest', lambda *_a, **_kw: None)
                selected = view
            assert current_e3_evidence(selected) is None
        assert current_e3_evidence(view) is retained


def test_registered_output_view_refuses_expired_access_before_nested_use(recorded_output_views, monkeypatch):
    from empirical_lawhood.api.retained_e3_evidence import retained_e3_evidence_context
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    f = recorded_output_views
    load = ExternalStudyOperationAuthorityStore.load
    with retained_e3_evidence_context(f.control.service.artifact_plane) as retained:
        view = retained.producer(f.context.run_id, f.control.reveal.authority_id).writer
        def expired(store, authority_id):
            value = load(store, authority_id)
            return replace(value, expires_at_utc='2026-08-23T20:43:00Z') if authority_id == f.control.reveal.authority_id else value
        with monkeypatch.context() as patch:
            patch.setattr(ExternalStudyOperationAuthorityStore, 'load', expired)
            with pytest.raises(PermissionError):
                with retained_e3_evidence_context(view):
                    pytest.fail('expired access reused original controls')
