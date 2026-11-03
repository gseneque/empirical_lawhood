"""Independent typed-plan output denials; no task execution or scientific grant."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api import current_result_custody, preparation_result_access, rc_challenge_results
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier
from empirical_lawhood.infrastructure.artifacts import ArtifactProfileValidatorRegistry, ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactMaterialization, ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, ExternalRootContract, LogicalArtifactIdentity, ReceiptCheck
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile
from empirical_lawhood.runtime.plans import CandidateExecutionPlan


class _DisclosedCustodySupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self, *, custody, resolve_input):
        self.custody, self.resolve_input = custody, resolve_input


def test_unregistered_custody_attribute_does_not_silently_join_scope(actual_issued_current_task_controls):
    from types import SimpleNamespace
    from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    f = actual_issued_current_task_controls
    f.control.service.executable_platform_ports = (ExecutablePlatformPort('foreign.custody-attribute',
        RecursiveOperationInputPort(SimpleNamespace(custody=f.custody, resolve_input=lambda spec: spec))),)
    with current_issued_task_control_scope(f.control.api):
        assert f.custody._control_reader is None


def test_original_parent_scope_reuses_plan_reader_and_expires_with_actual_run(actual_issued_current_task_controls):
    from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    f = actual_issued_current_task_controls
    supplier = _DisclosedCustodySupplier(custody=f.custody, resolve_input=lambda spec: spec)
    f.control.service.executable_platform_ports = (ExecutablePlatformPort('typed.original-parent-scope',
        RecursiveOperationInputPort(supplier)),)
    with current_issued_task_control_scope(f.control.api):
        with f.custody.preparation_scope():
            with f.custody.original_read_scope() as (writer, original):
                assert original.plan_reader is f.custody._control_reader
                actual = original.plan_reader.authenticate_execution_plan(package=f.control.package,
                    issued=f.control.package.issued_study, run_id=f.context.run_id)
                assert actual == f.plan
            with f.custody.original_read_scope() as (same_writer, same_original):
                assert same_writer is writer and same_original is original
    assert f.custody._parent_read_scope is None
    with pytest.raises(ArtifactIdentityConflict, match='scope has ended'):
        original.plan_reader.authenticate_execution_plan(package=f.control.package,
            issued=f.control.package.issued_study, run_id=f.context.run_id)


@pytest.fixture
def frozen_outputs():
    plan = decode_canonical_bytes((Path(__file__).parent / 'fixtures/authoring-execution-plan.json').read_bytes(), CandidateExecutionPlan, maximum_bytes=1024**2)
    task = next(value for value in plan.tasks if value.task_id.endswith('.numerical-evaluate'))
    validators = ArtifactProfileValidatorRegistry()
    logical = tuple(LogicalArtifactIdentity(output.logical_artifact_id, 'a' * 64,
        output.payload_schema, output.profile, output.media_type, output.visibility_ceiling,
        output.parent_visibility_ceilings, output.outcome_access,
        validators.generic_validation(profile=output.profile, payload_schema=output.payload_schema))
        for output in task.outputs)
    physical = tuple(ArtifactMaterialization(f'synthetic.output-{index}', output.logical_artifact_id,
        'synthetic.result-store', output.relative_path, 'a' * 64, 1, 'none')
        for index, output in enumerate(task.outputs))
    attempt = f'{plan.source_plan.object_id}.{task.task_id}.attempt-001'
    receipt = CanonicalTaskReceipt(f'receipt.{attempt}', plan.source_plan.object_id, task.task_id,
        attempt, plan.implementation_commit, (), physical, logical,
        (ReceiptCheck('metadata-contract-only', True, ()),), OperationalStatus.SUCCEEDED, ())
    return plan, receipt, logical[0]


def _join(plan, receipt, logical):
    return current_result_custody.require_current_result_receipt_outputs(
        receipt=receipt, logical=logical, execution_plan=plan,
        capability_prefixes=('rc-ladder-response.',))


def test_complete_typed_output_contract_accepts_without_creating_authority(frozen_outputs):
    plan, receipt, logical = frozen_outputs
    task = _join(plan, receipt, logical)
    assert task.task_id == receipt.task_id and len(task.outputs) == 2


@pytest.mark.parametrize('output_limit', (None, 2, 1))
def test_optional_aggregate_output_budget_preserves_complete_contract(frozen_outputs, output_limit):
    plan, receipt, logical = frozen_outputs
    task = next(value for value in plan.tasks if value.task_id == receipt.task_id)
    resources = replace(task.capability.requested_resources, output_bytes=output_limit)
    task = replace(task, capability=replace(task.capability, requested_resources=resources))
    plan = replace(plan, tasks=tuple(task if value.task_id == task.task_id else value for value in plan.tasks))
    if output_limit == 1:
        with pytest.raises(PermissionError, match='OUTPUT_BYTE_BUDGET_EXCEEDED'):
            _join(plan, receipt, logical)
    else:
        assert _join(plan, receipt, logical) == task
        incomplete = replace(receipt, output_logical_artifacts=receipt.output_logical_artifacts[:1],
                             output_materializations=receipt.output_materializations[:1])
        with pytest.raises(PermissionError, match='COMPLETE_EXECUTION_OUTPUT_CENSUS_REQUIRED'):
            _join(plan, incomplete, logical)


@pytest.mark.parametrize('mutation', ('access', 'visibility', 'media', 'path', 'over-budget'))
def test_supplied_metadata_cannot_replace_frozen_output_contract(frozen_outputs, mutation):
    plan, receipt, logical = frozen_outputs
    if mutation == 'access':
        logical = replace(logical, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    elif mutation == 'visibility':
        logical = replace(logical, visibility_ceiling=VisibilityCeiling.UNBOUND_HISTORICAL)
    elif mutation == 'media':
        logical = replace(logical, media_type='application/json')
    if mutation in ('access', 'visibility', 'media'):
        receipt = replace(receipt, output_logical_artifacts=(logical, *receipt.output_logical_artifacts[1:]))
    elif mutation == 'path':
        receipt = replace(receipt, output_materializations=(replace(receipt.output_materializations[0], relative_path='synthetic/foreign-output.json'), *receipt.output_materializations[1:]))
    else:
        task = next(value for value in plan.tasks if value.task_id == receipt.task_id)
        receipt = replace(receipt, output_materializations=(replace(receipt.output_materializations[0], size_bytes=task.capability.requested_resources.output_bytes + 1), *receipt.output_materializations[1:]))
    with pytest.raises(PermissionError, match='OUTPUT_(CONTRACT_MISMATCH|BYTE_BUDGET_EXCEEDED)'):
        _join(plan, receipt, logical)


@pytest.mark.parametrize('mutation', ('missing-output', 'foreign-output', 'foreign-task', 'foreign-run', 'foreign-implementation'))
def test_wrong_complete_census_or_task_identity_is_refused(frozen_outputs, mutation):
    plan, receipt, logical = frozen_outputs
    if mutation == 'missing-output':
        receipt = replace(receipt, output_logical_artifacts=receipt.output_logical_artifacts[:1], output_materializations=receipt.output_materializations[:1])
    elif mutation == 'foreign-output':
        logical = replace(logical, logical_artifact_id=logical.logical_artifact_id + '.foreign')
        physical = replace(receipt.output_materializations[0], logical_artifact_id=logical.logical_artifact_id)
        receipt = replace(receipt, output_logical_artifacts=tuple(sorted((logical, *receipt.output_logical_artifacts[1:]), key=lambda value:value.logical_artifact_id)), output_materializations=(physical, *receipt.output_materializations[1:]))
    else:
        receipt = replace(receipt, **{'task_id':'synthetic.foreign-task'} if mutation == 'foreign-task' else {'run_id':'synthetic.foreign-run'} if mutation == 'foreign-run' else {'implementation_commit':'b' * 40})
    with pytest.raises(PermissionError, match='(CENSUS_REQUIRED|TASK_MISMATCH)'):
        _join(plan, receipt, logical)


@pytest.mark.parametrize('owner', ('rc', 'preparation'))
def test_unprotected_downgrade_cannot_skip_present_current_control(tmp_path, frozen_outputs, monkeypatch, owner):
    plan, receipt, logical = frozen_outputs
    logical = replace(logical, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    receipt = replace(receipt, output_logical_artifacts=(logical, *receipt.output_logical_artifacts[1:]))
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'synthetic.result-store', 'software-only result denial', str(tmp_path), str(next(parent for parent in tmp_path.parents if parent.is_mount())),
        OperatorStorageProfile.SCHEMA, 1, None, None, (),)))
    # A current control pair exists but its schema is deliberately foreign. The
    # supplied access downgrade must reach that refusal rather than return early.
    plane.write(ArtifactWriteRequest(logical_artifact_id=f'campaign-package.{receipt.run_id}',
        relative_path=f'runs/{receipt.run_id}/plans/campaign-package.json',
        payload_schema=ObjectIdentity.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON,
        media_type='application/json', publication_scope_id='synthetic.foreign-controls',
        publication_scope_relative_root=f'runs/{receipt.run_id}/plans',
        payload=ObjectIdentity('synthetic.foreign-package', ObjectIdentity.SCHEMA, '1.0.0', 'a' * 64).canonical_bytes(),
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE, parent_visibility_ceilings=(),
        outcome_access=OutcomeAccess.OUTCOME_BLIND, minimum_free_bytes=1))

    def forbidden(*args, **kwargs):
        raise AssertionError('invalid current control reached protected payload verification')

    monkeypatch.setattr(plane, 'verify_manifest', forbidden)
    guard = rc_challenge_results._authenticate_result_access if owner == 'rc' else preparation_result_access.authenticate_preparation_result_access
    with pytest.raises(PermissionError, match='UNSUPPORTED_PACKAGE'):
        guard(context=None, receipt=receipt, logical=logical, writer=plane)


def test_exposed_unissued_output_preserves_existing_inspection_contract(tmp_path, frozen_outputs):
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    _, receipt, logical = frozen_outputs
    rows = tuple(replace(value, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, parent_visibility_ceilings=())
        for value in receipt.output_logical_artifacts)
    logical = rows[0]
    receipt = replace(receipt, output_logical_artifacts=rows)
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'synthetic.result-store', 'exposed unissued software output', str(tmp_path), str(next(parent for parent in tmp_path.parents if parent.is_mount())),
        OperatorStorageProfile.SCHEMA, 1, None, None, (),)))
    ExternalTaskReceiptStore(plane, minimum_free_bytes=1).commit(receipt,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    rc_challenge_results._authenticate_result_access(context=None, receipt=receipt, logical=logical, writer=plane)
    assert not (tmp_path / 'runs' / receipt.run_id / 'plans').exists()


@pytest.mark.parametrize('owner', ('rc', 'preparation'))
def test_missing_current_controls_do_not_authorize_supplied_access_downgrade(tmp_path, frozen_outputs, owner):
    _, receipt, logical = frozen_outputs
    logical = replace(logical, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'synthetic.result-store', 'missing current controls denial', str(tmp_path), str(next(parent for parent in tmp_path.parents if parent.is_mount())),
        OperatorStorageProfile.SCHEMA, 1, None, None, (),)))
    guard = rc_challenge_results._authenticate_result_access if owner == 'rc' else preparation_result_access.authenticate_preparation_result_access
    with pytest.raises(PermissionError, match='MISSING_ISSUED_CONTROLS'):
        guard(context=None, receipt=receipt, logical=logical, writer=plane)


def test_concrete_lineage_census_does_not_replace_frozen_access_contract(frozen_outputs):
    plan, receipt, logical = frozen_outputs
    # Concrete runtime parents and compiler scientific-edge parents have
    # distinct order/census contracts. Both retain the same frozen access.
    logical = replace(logical, parent_visibility_ceilings=())
    receipt = replace(receipt, output_logical_artifacts=(logical, *receipt.output_logical_artifacts[1:]))
    assert _join(plan, receipt, logical).task_id == receipt.task_id


def test_exposed_label_cannot_replace_actual_stored_protected_receipt(tmp_path, frozen_outputs, monkeypatch):
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    _, receipt, logical = frozen_outputs
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'synthetic.result-store', 'stored protected receipt downgrade denial', str(tmp_path), str(next(parent for parent in tmp_path.parents if parent.is_mount())),
        OperatorStorageProfile.SCHEMA, 1, None, None, (),)))
    ExternalTaskReceiptStore(plane, minimum_free_bytes=1).commit(receipt,
        visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE, outcome_access=OutcomeAccess.EVALUATION_REVEALED)
    rows = tuple(replace(value, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, parent_visibility_ceilings=())
        for value in receipt.output_logical_artifacts)
    claimed = replace(receipt, output_logical_artifacts=rows)

    original_verify = plane.verify_manifests

    def metadata_only(manifests):
        if any(manifest.logical.payload_schema != CanonicalTaskReceipt.SCHEMA for manifest in manifests):
            raise AssertionError('downgraded receipt reached scientific output verification')
        return original_verify(manifests)

    monkeypatch.setattr(plane, 'verify_manifests', metadata_only)
    with pytest.raises(PermissionError, match='EXACT_EXPOSED_IMPORT_RECEIPT_REQUIRED'):
        rc_challenge_results._authenticate_result_access(context=None, receipt=claimed, logical=rows[0], writer=plane)


@pytest.fixture
def actual_issued_current_task_controls(tmp_path,monkeypatch):
    """Existing small reference issue and actual plan compiler; no worker entry."""
    from types import SimpleNamespace
    from empirical_lawhood.api import execution as execution_owner
    from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
    from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
    from empirical_lawhood.runtime.execution import TaskContext, WorkerIsolationProfile, WorkerOutputPort
    from empirical_lawhood.runtime.plans import BarrierKind
    from tests.runtime_platform.test_recursive_prospective_workflow import (
        _public_issued_handoff_fixture,_run_public_handoff,
    )

    parts=_public_issued_handoff_fixture(tmp_path,monkeypatch)
    control=_run_public_handoff(tmp_path,issued_parts=parts,prepare_only=True)
    runs=[];compile_plan=execution_owner.compile_run_plan
    def capture(**kwargs):
        result=compile_plan(**kwargs);runs.append(result);return result
    with monkeypatch.context() as patch:
        patch.setattr(execution_owner,'compile_run_plan',capture)
        plan=control.service._recompile_rebuild_execution_plan(control.package)
    run,=runs
    control.service._persist_plans(control.package,run,plan,package_name='campaign-package',
        source_plan_name='run-plan',minimum_free_bytes=1)
    task=next(value for value in plan.tasks if value.barrier is not BarrierKind.REVEAL
        and all(output.payload_schema!=ScientificAdjudicationRecord.SCHEMA for output in value.outputs))
    manifest=control.package.registry.resolve(task.capability.capability_key,task.capability.capability_version)
    context=TaskContext(control.package.run_plan_id,task.task_id,'attempt.synthetic.current-control',
        task.capability.config,(),(),tuple(WorkerOutputPort(output.output_id,output.payload_schema,
            output.profile,output.media_type,output.logical_artifact_id) for output in task.outputs),
        task.capability.required_permissions,task.capability.requested_outcome_access,
        task.capability.requested_resources,WorkerIsolationProfile.TRUSTED_LOCAL)
    custody=CurrentIssuedTaskCustody(writer=control.service.artifact_plane,
        reveal_authority_id=control.reveal.authority_id)
    return SimpleNamespace(control=control,plan=plan,context=context,
        runner=SimpleNamespace(manifest=manifest),custody=custody)


def test_current_task_scope_checks_prepared_plan_once_but_replays_current_authority(actual_issued_current_task_controls,monkeypatch):
    from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore, ExternalIssuedStudyPublisher
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort

    f=actual_issued_current_task_controls
    validation_calls=[];validate_plan=current_result_custody._require_prepared_plan_bindings
    task_index_builds=[];index_tasks=current_result_custody._index_execution_tasks
    def counted_index(plan):
        task_index_builds.append(len(plan.tasks));return index_tasks(plan)
    monkeypatch.setattr(current_result_custody,'_index_execution_tasks',counted_index)
    def counted(**kwargs):
        validation_calls.append(kwargs['run_plan'].run_plan_id);return validate_plan(**kwargs)
    monkeypatch.setattr(current_result_custody,'_require_prepared_plan_bindings',counted)
    issued_reads=[];load_issue=ExternalIssuedStudyPublisher._load_executable_study
    def counted_issue(self,issue_id,**options):
        issued_reads.append(issue_id);return load_issue(self,issue_id,**options)
    monkeypatch.setattr(ExternalIssuedStudyPublisher,'_load_executable_study',counted_issue)
    grants=[];load=ExternalStudyOperationAuthorityStore.load
    def observed_grant(self,authority_id):
        grants.append(authority_id);return load(self,authority_id)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore,'load',observed_grant)
    # Reuse the real injected fixture API field; two ports share one custody.
    f.control.service.executable_platform_ports=tuple(ExecutablePlatformPort('synthetic.control-port.'+suffix,
        RecursiveOperationInputPort(_DisclosedCustodySupplier(custody=f.custody,
            resolve_input=lambda spec:pytest.fail('control scope must not consume worker inputs')))) for suffix in ('a','b'))
    with current_issued_task_control_scope(f.control.api):
        assert f.custody.current_task(f.context,f.runner)[1]==f.plan
        assert f.custody.current_task(f.context,f.runner)[1]==f.plan
        assert validation_calls==[f.context.run_id]
        assert task_index_builds==[len(f.plan.tasks)]
        assert issued_reads==[f.control.package.issued_study.issue_id]
        execution_id=f.control.package.execution_authority.authority_id
        assert grants.count(execution_id)==2
        def changed_grant(self,authority_id):
            value=load(self,authority_id)
            return replace(value,expires_at_utc='2026-08-23T20:43:00Z') if authority_id==execution_id else value
        monkeypatch.setattr(ExternalStudyOperationAuthorityStore,'load',changed_grant)
        with pytest.raises(PermissionError,match='current execution grant'):
            f.custody.current_task(f.context,f.runner)
        assert validation_calls==[f.context.run_id]
    assert f.custody._control_reader is None


def test_current_plan_reuse_rejects_changed_controls_and_expired_scope(actual_issued_current_task_controls):
    f=actual_issued_current_task_controls
    plane=f.control.service.artifact_plane
    with pytest.raises(RuntimeError):
        with plane.verification_scope() as static:
            reader=current_result_custody.CurrentResultPlanReader(static)
            actual=reader.authenticate_execution_plan(package=f.control.package,
                issued=f.control.package.issued_study,run_id=f.context.run_id)
            assert actual==f.plan
            assert reader.execution_task(execution_plan=actual,task_id=f.context.task_id).task_id==f.context.task_id
            foreign=replace(actual,implementation_commit='f'*40)
            with pytest.raises(PermissionError,match='AUTHENTICATED_PLAN_REQUIRED'):
                reader.execution_task(execution_plan=foreign,task_id=f.context.task_id)
            with pytest.raises(PermissionError,match='AUTHENTICATED_PLAN_REQUIRED'):
                reader.original_recovery_index(package=f.control.package,execution_plan=foreign)
            path=plane.root.resolve('runs/'+f.context.run_id+'/plans/execution-plan.json',for_write=False)
            path.write_bytes(path.read_bytes()+b' ')
            reader.authenticate_execution_plan(package=f.control.package,
                issued=f.control.package.issued_study,run_id=f.context.run_id)
    with pytest.raises(RuntimeError):
        reader.authenticate_execution_plan(package=f.control.package,
            issued=f.control.package.issued_study,run_id=f.context.run_id)
    with pytest.raises(RuntimeError):
        reader.execution_task(execution_plan=actual,task_id=f.context.task_id)
    with pytest.raises(RuntimeError):
        reader.original_recovery_index(package=f.control.package,execution_plan=actual)


def test_original_index_reuse_stays_bound_to_the_authenticated_plan(actual_issued_current_task_controls,monkeypatch):
    from empirical_lawhood.runtime import recovery
    f=actual_issued_current_task_controls
    builds=[];build=recovery.build_run_recovery_index
    def counted_build(plan,**kwargs):
        builds.append(len(plan.tasks));return build(plan,**kwargs)
    monkeypatch.setattr(recovery,'build_run_recovery_index',counted_build)
    plane=f.control.service.artifact_plane
    with plane.verification_scope() as static:
        reader=current_result_custody.CurrentResultPlanReader(static)
        actual=reader.authenticate_execution_plan(package=f.control.package,
            issued=f.control.package.issued_study,run_id=f.context.run_id)
        original=reader.original_recovery_index(package=f.control.package,execution_plan=actual)
        assert reader.original_recovery_index(package=f.control.package,execution_plan=actual) is original
        assert builds==[len(actual.tasks)]
        assert original.execution_plan==ObjectIdentity.from_record(actual.execution_plan_id,actual)
        assert original.authority_identities==tuple(sorted((
            ObjectIdentity.from_record(f.control.package.scientific_approval.authorization_id,f.control.package.scientific_approval),
            ObjectIdentity.from_record(f.control.package.execution_authority.authority_id,f.control.package.execution_authority)),
            key=lambda row:row.object_id))


def test_direct_api_scheduler_owns_control_lifetime_before_any_worker(actual_issued_current_task_controls,monkeypatch):
    from empirical_lawhood.api import execution as execution_owner
    from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
    from empirical_lawhood.api.results import RunCampaignRequest
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort

    f=actual_issued_current_task_controls
    from empirical_lawhood.infrastructure import source_origin
    # This fixture authors an explicitly synthetic source checkout. Its test
    # stops at the scheduler boundary and establishes no actual-source entry.
    def disclosed_source(root):
        assert root == f.control.service.repo_root
    monkeypatch.setattr(source_origin, 'require_executing_target_source', disclosed_source)
    class Supplier(CurrentIssuedTaskCustodySupplier):
        """Explicit disclosed custody interface; original fixture behavior remains."""
        def __init__(self,original):
            self.original,self.custody=original,f.custody
        def resolve_input(self,spec):
            return self.original.resolve_input(spec)
        def __getattr__(self,name):
            return getattr(self.original,name)
    original_ports=f.control.service.executable_platform_ports
    f.control.service.executable_platform_ports=tuple(replace(platform,
        port=RecursiveOperationInputPort(Supplier(platform.port.supplier))) for platform in original_ports)
    assert tuple(value.port_key for value in f.control.service.executable_platform_ports)==tuple(
        value.port_key for value in original_ports)
    validation_calls=[];validate_plan=current_result_custody._require_prepared_plan_bindings
    def counted(**kwargs):
        validation_calls.append(kwargs['run_plan'].run_plan_id);return validate_plan(**kwargs)
    monkeypatch.setattr(current_result_custody,'_require_prepared_plan_bindings',counted)
    class SchedulerBoundary(BaseException):
        pass
    observed=[]
    def before_workers(scheduler,run_id,plan):
        # This is the actual scheduler entry reached by direct public API execution.
        # Stop before its body can enter any task, executor or native effect.
        assert run_id==f.context.run_id and plan==f.plan
        reader=f.custody._control_reader
        assert reader is not None and f.custody.writer is f.control.service.artifact_plane
        assert f.custody.current_task(f.context,f.runner)[1]==plan
        assert f.custody.current_task(f.context,f.runner)[1]==plan
        assert validation_calls==[run_id]
        with current_issued_task_control_scope(f.control.api):
            assert f.custody._control_reader is reader
        assert f.custody._control_reader is reader
        observed.append(run_id)
        raise SchedulerBoundary()
    monkeypatch.setattr(execution_owner.LocalScheduler,'execute',before_workers)
    assert f.custody._control_reader is None
    with pytest.raises(SchedulerBoundary):
        result=f.control.api.run_campaign(RunCampaignRequest(f.control.package_path,confirmed=True,
            reveal_authority_id=f.control.reveal.authority_id))
        pytest.fail('direct API refused before scheduler boundary: '+repr(result))
    assert observed==[f.context.run_id] and f.control.executor.invocations==0
    assert f.custody._control_reader is None


def test_four_current_parent_preparations_share_plan_validation_and_release_before_child_overlap(actual_issued_current_task_controls, monkeypatch):
    """Actual issued plan/grants; only the post-preparation child is disclosed."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort

    f = actual_issued_current_task_controls
    validations, grants = [], []
    original_validation = current_result_custody._require_prepared_plan_bindings
    original_load = ExternalStudyOperationAuthorityStore.load
    def validate_once(**kwargs):
        validations.append(kwargs["run_plan"].run_plan_id)
        return original_validation(**kwargs)
    def fresh_grant(self, authority_id):
        grants.append(authority_id)
        return original_load(self, authority_id)
    monkeypatch.setattr(current_result_custody, "_require_prepared_plan_bindings", validate_once)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, "load", fresh_grant)
    f.control.service.executable_platform_ports = (ExecutablePlatformPort("disclosed.concurrent-custody",
        RecursiveOperationInputPort(_DisclosedCustodySupplier(custody=f.custody,
            resolve_input=lambda spec: pytest.fail("preparation control consumed a worker input")))),)
    ready, children = Barrier(4), Barrier(4)
    def prepare_then_overlap(index):
        ready.wait(timeout=15)
        with f.custody.preparation_scope():
            assert f.custody.current_task(f.context, f.runner)[1] == f.plan
        # All four returned runners can overlap. Holding the graph lifetime or
        # returned child under the parent lock would deadlock this barrier.
        children.wait(timeout=15)
        return index
    pool = ThreadPoolExecutor(max_workers=4)
    try:
        with current_issued_task_control_scope(f.control.api):
            futures = [pool.submit(prepare_then_overlap, index) for index in range(4)]
            assert [future.result(timeout=30) for future in futures] == list(range(4))
            assert validations == [f.context.run_id]
            assert grants.count(f.control.package.execution_authority.authority_id) == 4
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    assert f.custody._control_reader is None


@pytest.mark.parametrize("route", ("configured", "sampling", "selected", "selected-port", "revision"))
@pytest.mark.parametrize("damage", ("type", "writer", "reveal"))
def test_matrix_shared_custody_refuses_foreign_writer_reveal_or_owner_before_reads(route, damage):
    from types import SimpleNamespace
    from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import runtime as configured
    from empirical_lawhood.api import matrix_sampling_runtime as sampling, matrix_selected_runtime as selected
    from empirical_lawhood.api.matrix_selected_revision_runtime import RevisionRuntimeInputSupplier
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_bindings import ENTRY_ORIGINAL_COMMITMENTS_KEY, operation_declarations
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_workers import SelectedProtectedWorker
    from empirical_lawhood.adapters.methods.matrix_sampling_bindings import MatrixSamplingWorker

    writer = object()
    custody = (object() if damage == "type" else CurrentIssuedTaskCustody(
        writer=object() if damage == "writer" else writer,
        reveal_authority_id="reveal.foreign" if damage == "reveal" else None))
    with pytest.raises(TypeError, match="custody changes"):
        if route == "configured":
            configured.ProtectedE3RuntimeInputSupplier(None, writer=writer, root=None, fit_config=None,
                qualifications=(), selection=None, custody=custody)
        elif route == "selected-port":
            selected.SelectedMatrixRuntimeInputSupplier(None, writer=writer, custody=custody)
        elif route == "revision":
            RevisionRuntimeInputSupplier(None, writer=writer, output_codecs={}, custody=custody)
        else:
            supplier = SimpleNamespace(writer=writer, reveal_authority_id=None, custody=custody)
            if route == "sampling":
                sampling.prepare_matrix_sampling(supplier, SimpleNamespace(), MatrixSamplingWorker("E3"))
            else:
                manifest = next(value for value in operation_declarations() if value.capability_key == ENTRY_ORIGINAL_COMMITMENTS_KEY).manifest()
                selected.prepare_selected_matrix(supplier, SimpleNamespace(), SelectedProtectedWorker("entry", manifest))


@pytest.mark.parametrize("route", ("original", "configured", "sampling", "programme", "selected", "revision"))
def test_matrix_ports_share_actual_current_plan_and_refuse_changed_bytes(actual_issued_current_task_controls, monkeypatch, route):
    """Real issue/grants and compiler; foreign task roles refuse before science.

    Configured fit operands are deliberately absent. The selected and revision
    suppliers are actual installed E5/E6 parents, with no scientific execution
    claimed against this independent reference plan.
    """
    from concurrent.futures import ThreadPoolExecutor
    from decimal import getcontext, localcontext
    from threading import Barrier
    from types import SimpleNamespace
    from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import runtime as configured
    from empirical_lawhood.api.domain_composition.matrix_protected_response import runtime as original
    from empirical_lawhood.api.matrix_sampling_runtime import MatrixSamplingRuntimeInputSupplier
    from empirical_lawhood.api.matrix_scheduled_programme_runtime import ProgrammeRuntimeInputSupplier
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_bindings import ENTRY_ORIGINAL_COMMITMENTS_KEY, operation_declarations
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_workers import SelectedProtectedWorker
    from empirical_lawhood.adapters.methods.matrix_sampling_bindings import MatrixSamplingWorker
    from empirical_lawhood.api.matrix_selected_runtime import SelectedMatrixRuntimeInputSupplier
    from empirical_lawhood.api.matrix_selected_revision_runtime import RevisionRuntimeInputSupplier
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as revision
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_workers import SelectedRevisionWorker
    from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort

    f = actual_issued_current_task_controls
    plane = f.control.service.artifact_plane
    def supplier():
        underlying = SimpleNamespace(resolve_input=lambda spec: pytest.fail("foreign role read scientific input"))
        common = dict(writer=plane, reveal_authority_id=f.custody.reveal_authority_id, custody=f.custody)
        if route in ("original", "configured"):
            owner = original if route == "original" else configured
            return owner.ProtectedE3RuntimeInputSupplier(underlying, root=None, fit_config=None,
                qualifications=(), selection=None, **common)
        if route == "sampling":
            return MatrixSamplingRuntimeInputSupplier(underlying, **common)
        if route == "programme":
            return ProgrammeRuntimeInputSupplier(underlying, output_codecs={}, **common)
        if route == "selected":
            return SelectedMatrixRuntimeInputSupplier(underlying, **common)
        return RevisionRuntimeInputSupplier(underlying, output_codecs={}, **common)
    suppliers = tuple(supplier() for _ in range(2))
    f.control.service.executable_platform_ports = tuple(ExecutablePlatformPort(route + ".control." + str(index),
        RecursiveOperationInputPort(supplier)) for index, supplier in enumerate(suppliers))
    assert suppliers[0].custody is suppliers[1].custody is f.custody
    validations, grants = [], []
    original_validation = current_result_custody._require_prepared_plan_bindings
    original_load = ExternalStudyOperationAuthorityStore.load
    def counted_validation(**kwargs):
        validations.append(kwargs["run_plan"].run_plan_id)
        return original_validation(**kwargs)
    def fresh_grant(self, authority_id):
        grants.append(authority_id)
        return original_load(self, authority_id)
    monkeypatch.setattr(current_result_custody, "_require_prepared_plan_bindings", counted_validation)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, "load", fresh_grant)
    manifest = next(value for value in operation_declarations() if value.capability_key == ENTRY_ORIGINAL_COMMITMENTS_KEY).manifest()
    if route in ("original", "configured"):
        callbacks = ((suppliers[0].prepare_selected_matrix, SelectedProtectedWorker("entry", manifest)),
            (suppliers[1].prepare_matrix_sampling, MatrixSamplingWorker("E3")))
    elif route == "sampling":
        callbacks = tuple((value.prepare_matrix_sampling, MatrixSamplingWorker("E3")) for value in suppliers)
    elif route == "programme":
        from empirical_lawhood.adapters.methods.matrix_scheduled_history import revision_future_bindings as old_future
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration_bindings import ScheduledRevisionCalibrationWorker
        future = old_future.operation_factories()[0].runner_factory()
        callbacks = ((suppliers[0].prepare_revision_future, future),
            (suppliers[1].prepare_revision_calibration, ScheduledRevisionCalibrationWorker()))
    elif route == "selected":
        callbacks = tuple((value.prepare_selected_matrix, SelectedProtectedWorker("entry", manifest)) for value in suppliers)
    else:
        declaration = next(value for value in revision.operation_declarations()
            if value.capability_key == revision.capability_key("entry", "PROTECTED", "2.0.0"))
        callbacks = tuple((value.prepare_selected_revision, SelectedRevisionWorker("entry", "PROTECTED", declaration.manifest()))
            for value in suppliers)
    ready, returned = Barrier(4), Barrier(4)
    decimal_policy = getcontext().copy()
    def prepare(index):
        callback, runner = callbacks[index % 2]
        context = replace(f.context, permissions=runner.manifest.permissions)
        with localcontext(decimal_policy):
            ready.wait(timeout=15)
            with pytest.raises(PermissionError, match="actual current installed task/config/access"):
                callback(context, runner)
        returned.wait(timeout=15)
        return index
    pool = ThreadPoolExecutor(max_workers=4)
    try:
        with pytest.raises(ArtifactIdentityConflict, match="changed"):
            with current_issued_task_control_scope(f.control.api):
                reader = f.custody._control_reader
                assert reader is not None
                futures = [pool.submit(prepare, index) for index in range(4)]
                assert [future.result(timeout=30) for future in futures] == list(range(4))
                assert validations == [f.context.run_id]
                assert grants.count(f.control.package.execution_authority.authority_id) == 4
                assert f.custody.current_task(f.context, f.runner)[1] == f.plan
                assert validations == [f.context.run_id]
                path = plane.root.resolve("runs/" + f.context.run_id + "/plans/execution-plan.json", for_write=False)
                path.write_bytes(path.read_bytes() + b" ")
                f.custody.current_task(f.context, f.runner)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    assert f.custody._control_reader is None
    with pytest.raises(ArtifactIdentityConflict, match="scope has ended"):
        reader.authenticate_execution_plan(package=f.control.package, issued=f.control.package.issued_study,
            run_id=f.context.run_id)
