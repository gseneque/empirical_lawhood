# SPDX-License-Identifier: MPL-2.0
"""Actual protected declarations through public owners and synthetic authority.

Run this control from a clean frozen source and select pytest's basetemp on the
selected external storage. The original native adapters
and worker Ready/Proceed checks run unchanged. Every original, qualification and
issue grant here is an explicitly exposed software fixture, never fresh E3
scientific evidence or genuine authority.
"""

from contextlib import contextmanager
from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
from empirical_lawhood.api.results import CampaignStatusRequest, ResumeCampaignRequest, RunCampaignRequest
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile
from tests.test_matrix_e3_protected_public_lowering import prepared_case
from tests.runtime_platform.test_recursive_prospective_workflow import _issue_public_handoff

ROOT = Path(__file__).resolve().parents[1]


def _selected_case(directory, design, *, maximum_parallel_tasks=1):
    """Bind producing provenance and an admissible disclosed instrument first."""
    import numpy as np

    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    from tests import test_matrix_e3_protected_source_records as source_literals, test_matrix_scheduled_history as scheduled_literals
    from tests.test_matrix_scheduled_response_forecast import pauli

    provenance = capture_matrix_provenance(project_root=ROOT)
    template = scheduled_literals.parameter_template
    encode = source_literals.encode_matrix_arrays
    # Reuse the declared Pauli-complement instrument and normalizations from
    # the existing AVAILABLE scheduled/response controls. Historical metadata
    # fixtures retain their zero arrays; this public worker control publishes
    # its separate valid originals before any binding or protocol is derived.
    instrument = dict(generic_basis=np.asarray([np.kron(np.eye(2), value) / 2 for value in pauli()], dtype='<c16'),
        force_coefficients=np.stack((np.eye(3), np.eye(3))).astype('<f8') / np.sqrt(6),
        trace_coefficients=np.ones((2, 3), dtype='<f8') / np.sqrt(6),
        receiver_coefficients=np.eye(48, dtype='<f8').reshape(48, 2, 2, 3, 4))

    def publishable_templates(values, **kwargs):
        if {name: (value.dtype.str, value.shape) for name, value in values.items()} != {
                name: (value.dtype.str, value.shape) for name, value in instrument.items()}:
            raise AssertionError('public E3 instrument changes the original declared member/dtype/shape census')
        return encode(instrument, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(scheduled_literals, 'parameter_template',
            lambda: replace(template(), provenance=provenance))
        patch.setattr(source_literals, 'encode_matrix_arrays', publishable_templates)
        if design == 'selected64':
            return prepared_case(directory, selected64=True, maximum_parallel_tasks=maximum_parallel_tasks)
        if design == 'alternative':
            return prepared_case(directory, maximum_parallel_tasks=maximum_parallel_tasks)
        if design != 'small':
            raise ValueError('EL_E3_PUBLIC_DESIGN must be small, alternative or selected64')
        return prepared_case(directory, cal_count=1, eval_count=8, maximum_parallel_tasks=maximum_parallel_tasks)



@dataclass(frozen=True, slots=True)
class _PreparedObservation:
    identity: ObjectIdentity
    native_effect: bool

    @classmethod
    def from_contract(cls, contract):
        return cls(contract.identity, contract.native_effect)


@dataclass(frozen=True, slots=True)
class _ReadyObservation:
    invocation: ObjectIdentity
    ready: bool
    path: Path
    relative_path: str
    size_bytes: int
    sha256: str

    def proof(self):
        from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256

        assert bounded_file_sha256(self.path, maximum_bytes=self.size_bytes) == (self.size_bytes, self.sha256)
        return {'invocation': self.invocation.to_document(), 'ready': self.ready,
            'relative_path': self.relative_path, 'size_bytes': self.size_bytes, 'sha256': self.sha256}


def _retain_ready_record(result, *, path, relative_path):
    raw = result.canonical_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as retained:
        retained.write(raw)
        retained.flush()
        os.fsync(retained.fileno())
    return _ReadyObservation(result.invocation, result.ready, path, relative_path, len(raw), sha256(raw).hexdigest())


@dataclass(frozen=True, slots=True)
class _CompletedChildObservation:
    pid: int
    exitcode: int | None


def _release_dedicated_child(process):
    # This observer runs the dedicated one-child path only. The production
    # executor has already joined it; never close an active/group-reusable child.
    assert not process.is_alive()
    observed = _CompletedChildObservation(process.pid, process.exitcode)
    process.close()
    return observed


class _ObservedProcessContext:
    """Attribute each actual child to its calling observer thread."""

    def __init__(self, context, processes):
        self.context, self.processes = context, processes
        self._local = threading.local()

    @contextmanager
    def capture_children(self):
        assert not hasattr(self._local, 'children'), "nested child observation"
        children = []
        self._local.children = children
        try:
            yield children
        finally:
            del self._local.children

    def Process(self, *args, **kwargs):
        assert hasattr(self._local, 'children'), "child creation lacks its task observation"
        process = self.context.Process(*args, **kwargs)
        self._local.children.append(process)
        return process

    def __getattr__(self, name):
        return getattr(self.context, name)


class _ObservedProcessExecutor(LocalProcessExecutor):
    def __init__(self, root, evidence_directory):
        super().__init__(scratch_root=root)
        self.evidence_directory = evidence_directory
        self.processes, self.contracts, self.ready, self.completed = [], {}, {}, []
        self.source_custody_root, self.source_entries = Path(root.contract.canonical_path), {}
        self._observation_lock, self._source_entry_lock = threading.Lock(), threading.Lock()
        self._context = _ObservedProcessContext(self._context, self.processes)

    def _admit_worker(self, result, contract, *arguments):
        with self._observation_lock:
            assert contract.task_id not in self.ready
            self.ready[contract.task_id] = _retain_ready_record(result,
                path=self.evidence_directory / (contract.task_id + '.json'),
                relative_path='worker-ready/' + contract.task_id + '.json')
            self.contracts[contract.task_id] = _PreparedObservation.from_contract(contract)
        return super()._admit_worker(result, contract, *arguments)

    def _observe_source_entry(self, task_context, prepared_contract):
        # This cache only avoids repeated proof collection. Production entry
        # and every worker retain their separate source/authority admission.
        source_key = (task_context.run_id, prepared_contract.implementation.observed_git_head)
        with self._source_entry_lock:
            if source_key in self.source_entries:
                return
            from tests.current_source_entry_proof import current_source_entry_proof

            self.source_entries[source_key] = current_source_entry_proof(
                self.source_custody_root, task_context, prepared_contract)

    def execute_deadline_free(self, runner, task_context, *, progress_contract, progress_callback,
            native_subwork=None, prepared_contract=None, provenance_requirements=(), native_work_preparer=None, native_entry=None):
        assert prepared_contract is not None
        prepared_contract.validate_context(task_context)
        self._observe_source_entry(task_context, prepared_contract)
        with self._observation_lock:
            assert task_context.task_id not in self.contracts
            self.contracts[task_context.task_id] = _PreparedObservation.from_contract(prepared_contract)
        with self._context.capture_children() as children:
            result = super().execute_deadline_free(runner, task_context,
                progress_contract=progress_contract, progress_callback=progress_callback,
                native_subwork=native_subwork,
                prepared_contract=prepared_contract, provenance_requirements=provenance_requirements,
                native_work_preparer=native_work_preparer, native_entry=native_entry)
        assert len(children) == 1
        child = _release_dedicated_child(children[0])
        assert child.pid != os.getpid()
        with self._observation_lock:
            self.processes.append(child)
            self.completed.append((task_context.task_id, task_context.attempt_id, child.pid))
        return result


def _primary_census(plane, run_id):
    """Include retained native custody as well as ordinary task publications."""
    root = Path(plane.root.contract.canonical_path)
    paths = set()
    for path in (root / 'runs' / run_id / 'receipts').glob('*/*.json'):
        if path.name.endswith('.manifest.json'):
            continue
        receipt = decode_canonical_bytes(path.read_bytes(), CanonicalTaskReceipt, maximum_bytes=1024**2)
        paths.add(path)
        paths.update(root / row.relative_path for row in receipt.output_materializations)
    paths.update(path.with_name(path.name + '.manifest.json') for path in tuple(paths))
    for name in ('native-contacts', 'native-subwork', 'native-subwork-rosters'):
        # Native custody also contains real operational locks and publication
        # batch files. Preserve their exact bytes without inventing sidecars.
        paths.update(path for path in (root / 'runs' / run_id / name).rglob('*') if path.is_file())
    files = {}
    for path in sorted(paths):
        assert path.is_file()
        assert not path.is_symlink()
        raw, stat = path.read_bytes(), path.stat()
        files[path.relative_to(root).as_posix()] = (len(raw), sha256(raw).hexdigest(), stat.st_mtime_ns)
    assert files
    return files


def _file_census(paths, root):
    files = {}
    for path in sorted(paths):
        assert path.is_file() and not path.is_symlink()
        raw, observed = path.read_bytes(), path.stat()
        files[path.relative_to(root).as_posix()] = {
            'size_bytes': len(raw), 'sha256': sha256(raw).hexdigest(),
            'mtime_ns': observed.st_mtime_ns}
    assert files
    return files


def _ready_census(output):
    return _file_census((output / 'worker-ready').glob('*.json'), output)


def _catalog_census(output, catalog):
    return _file_census((path for suffix in ('', '-wal', '-shm')
        if (path := catalog.with_name(catalog.name + suffix)).exists()), output)


def _native_receipt_census(plane, run_id, plan, native_tasks, receipts):
    """Authenticate leaf completions independently of ordinary plan receipts."""
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.kernel.evidence import VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import most_restrictive_outcome_access
    from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster, NativeSubworkState

    selected = tuple(task for task in plan.tasks if task.task_id in native_tasks)
    contacts = ExternalNativeEffectContactStore(plane=plane,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.most_restrictive(
            *(output.visibility_ceiling for task in selected for output in task.outputs)),
        outcome_access=most_restrictive_outcome_access(
            *(task.capability.requested_outcome_access for task in selected),
            *(output.outcome_access for task in selected for output in task.outputs)),
        task_scopes={task.task_id: (
            VisibilityCeiling.most_restrictive(*(output.visibility_ceiling for output in task.outputs)),
            most_restrictive_outcome_access(task.capability.requested_outcome_access,
                *(output.outcome_access for output in task.outputs))) for task in selected})
    root = Path(plane.root.contract.canonical_path)
    observed = {}
    for path in (root / 'runs' / run_id / 'native-subwork-rosters').glob('*/*.json'):
        if path.name.endswith('.manifest.json'):
            continue
        roster = decode_canonical_bytes(path.read_bytes(), NativeSubworkRoster, maximum_bytes=1024**2)
        parent = roster.parent_contact
        assert parent.task_id in native_tasks
        assert parent.execution_plan == contacts.execution_plan
        store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts.for_task(parent.task_id),
            parent_contact=parent)
        assert store.read_roster(parent, roster.roster_id) == roster
        for definition in store.iter_roster_definitions(parent, roster.roster_id):
            inspection = store.inspect(definition)
            assert inspection.state is NativeSubworkState.COMPLETED
            receipt = inspection.receipt
            assert receipt is not None and inspection.completion is not None
            assert receipt.operational_status is inspection.completion.operational_status
            assert receipt.receipt_id not in observed
            observed[receipt.receipt_id] = receipt
    assert observed and len(receipts) == len(observed)
    assert set(observed) == {receipt.receipt_id for receipt in receipts}
    assert all(observed[receipt.receipt_id] == receipt for receipt in receipts)
    return tuple({'receipt_id': receipt.receipt_id, 'task_id': receipt.task_id,
        'status': receipt.operational_status.value, 'reason_codes': receipt.reason_codes,
        'outputs': len(receipt.output_materializations)} for receipt in sorted(receipts, key=lambda row: row.receipt_id))


def _execution(case, handoff, parts, output, *, executor_factory=None, maximum_parallel_tasks=1):
    """Reuse public issue scaffolding with the actual installed provider set."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import (
        EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY,
        EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY,
    )
    from empirical_lawhood.api.execution import CampaignExecutionService
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator
    from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
    from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog
    from empirical_lawhood.infrastructure.study_issue import ExternalIssuedExtensionPayloadSource, ExternalIssuedStudyPublisher
    from empirical_lawhood.runtime.executable_bindings import LayeredCampaignRuntimeProviderResolver
    from empirical_lawhood.runtime.issued_extension_payloads import IssuedExtensionPayloadResolver
    from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry
    from tests.runtime_platform.test_study_issue import _PassthroughSourceInspector

    _, factories, _, plane, _, package, reveal, approval, authorities = parts
    assert factories is EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    package_path = output / 'issued-public-package.json'
    package_path.write_bytes(package.canonical_bytes())
    catalog = output / 'public-catalog.sqlite3'

    def engine_factory():
        engine = create_catalog_engine('sqlite+pysqlite:///' + str(catalog))
        upgrade_catalog(engine)
        return engine

    executor = (executor_factory or _ObservedProcessExecutor)(plane.root, output / "worker-ready")
    service = CampaignExecutionService(repo_root=ROOT, artifact_plane=plane,
        engine_factory=engine_factory, catalog_path=catalog,
        providers=CampaignRuntimeProviderRegistry(()),
        provider_resolver=LayeredCampaignRuntimeProviderResolver(
            precomposed=CampaignRuntimeProviderRegistry(()), factories=factories),
        executable_binding_aggregate=factories.aggregate,
        issued_extension_payload_resolver=IssuedExtensionPayloadResolver(
            source=ExternalIssuedExtensionPayloadSource(ExternalIssuedStudyPublisher(
                artifact_plane=plane, authority_store=authorities, grantee_id='operator.issue-service')),
            codecs=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY),
        executable_platform_ports=handoff.platform_ports, approval_service=approval,
        study_authority_store=authorities, study_source_closure_inspector=_PassthroughSourceInspector(),
        executor=executor, enforce_git_identity=True, maximum_parallel_tasks=maximum_parallel_tasks,
        execution_resource_envelope_coordinator=DurableExecutionResourceEnvelopeCoordinator(
            ExternalExecutionResourceEnvelopeStore(plane.root, artifact_plane=plane)))
    api = EmpiricalLawhoodApi(repo_root=ROOT,
        external_root=Path(plane.root.contract.canonical_path), execution_service=service,
        approval_service=approval, study_authority_store=authorities)
    return SimpleNamespace(service=service, api=api, executor=executor, package=package,
        package_path=package_path, reveal=reveal, catalog=catalog)


def test_original_protected_public_prepare_author_worker_assess_read_and_recover(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.adapters.composition.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as science
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import statistical_task_id
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import bind_protected_e3_experiment_inputs
    from empirical_lawhood.infrastructure.source_closure import capture_target_closure
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    from tests.runtime_platform.test_study_issue import _issue_api_fixture

    design = os.environ.get('EL_E3_PUBLIC_DESIGN', 'small')
    maximum_parallel_tasks = int(os.environ.get('EL_E3_PUBLIC_WORKERS', '1'))
    if maximum_parallel_tasks < 1:
        raise ValueError('public E3 worker count must be positive')
    if 'EL_E3_REQUIRED_MOUNT' in os.environ and maximum_parallel_tasks < 4:
        raise ValueError('future explicitly mounted public E3 runs require at least four workers')
    from tests.matrix_workflow_measurements import WorkflowMeasurements, matrix_observation_callbacks

    measurements = WorkflowMeasurements(tmp_path / 'workflow-phase-measurements.json', monkeypatch,
        selection=design, callbacks=matrix_observation_callbacks())
    case = measurements.call('original_fixture_setup', _selected_case,
        tmp_path / 'originals', design, maximum_parallel_tasks=maximum_parallel_tasks)
    required_mount = Path(os.environ.get('EL_E3_REQUIRED_MOUNT', str(tmp_path)))
    if 'EL_E3_REQUIRED_MOUNT' in os.environ:
        from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot

        case.plane = ExternalArtifactPlane(GuardedExternalRoot(replace(case.plane.root.contract,
            required_mount_path=str(required_mount))), validators=case.plane.validators,
            semantic_validations=case.plane.semantic_validations, custody_limits=case.plane.custody_limits)
        diagnostic = case.plane.root.diagnostic()
        assert diagnostic.read_ready and diagnostic.write_ready, diagnostic
    profile = OperatorStorageProfile('software.e3.public-storage', 'external-filesystem', '1.0.0',
        str(tmp_path / 'originals'), str(required_mount), 'selected', 'scientific-scratch',
        OperatorStorageAccessMode.READ_WRITE, None, None, (), 'strict-mount-contained-no-symlink',
        1, (), maximum_parallel_tasks, False)
    programme = ExperimentProgrammeService(ROOT, case.plane, profile)
    closure = measurements.call('selected_source_capture', capture_target_closure,
        ROOT, case.selection.selection_id + '.prospective.source-closure').closure
    execution = ExecutionSelection(workers=maximum_parallel_tasks, environment_id='main-locked',
        source_snapshot=ObjectIdentity.from_record('recursive-member.implementation', closure),
        output_root=case.plane.root.contract.canonical_path)
    # The selected source binding is produced by the same public input owner
    # exercised in the independent preparation tests.
    resolved = measurements.call('bind_public_inputs', bind_protected_e3_experiment_inputs, case.specification,
        {'protected-selection': case.selection}, files=case.files)
    preparation = measurements.call('prepare', programme.prepare, case.specification,
        scientific_inputs=resolved.scientific_inputs, method_inputs=resolved.method_inputs, execution=execution,
        protocol_bytes=case.candidate_bytes)
    assert preparation.draft is not None
    assert 'matrix.e3.prospective-operation-lowering' not in {row.code for row in preparation.dependencies}
    directory = Path(case.plane.root.contract.canonical_path) / 'public-e3-programme'
    authored = measurements.call('author', programme.author, preparation=preparation, output_dir=directory)
    assert authored['scientific_authority'] == 'NONE' and authored['native_contact'] == 'none'
    selected = measurements.call('cold_load', load_prepared_prospective_experiment, directory=directory, project_root=ROOT,
        storage_profile=profile, artifact_writer=case.plane)
    scaffold_dir = tmp_path / 'synthetic-authority'
    scaffold_dir.mkdir()
    handoff = selected.handoff
    scaffold = _issue_api_fixture(scaffold_dir, standard_fixture=lambda: (
        handoff.authoring.base, handoff.context.resolve_standard(handoff.authoring.base).context))
    scaffold_api, paths, _, custody = scaffold
    parts = (handoff, EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY,
        GENERATED_EXTENSION_BUNDLE_AGGREGATE, case.plane, b'', scaffold_api, paths, custody)
    issued = measurements.call('synthetic_test_issue', _issue_public_handoff, tmp_path, monkeypatch, handoff_parts=parts,
        namespace='software-protected-e3', compiled_candidate=selected.candidate)
    control = measurements.call('execution_composition', _execution, case, handoff, issued, tmp_path, maximum_parallel_tasks=maximum_parallel_tasks)
    assert control.service.maximum_parallel_tasks == profile.maximum_parallel_tasks == maximum_parallel_tasks
    assert control.package.execution_resource_envelope_spec.maximum_parallel_tasks == maximum_parallel_tasks
    programme = ExperimentProgrammeService(ROOT, case.plane, profile,
        prospective_api_factory=lambda **_arguments: control.api)
    preview = measurements.call('unconfirmed_preview', programme.run, directory=directory, maximum_parallel_tasks=maximum_parallel_tasks,
        request=RunCampaignRequest(control.package_path))
    (tmp_path / 'preview-report.json').write_text(json.dumps(preview, sort_keys=True, indent=2) + '\n')
    assert preview['status'] == 'BLOCKED' and not control.executor.contracts, preview
    report = measurements.call('actual_worker_execution_and_assessment', programme.run, directory=directory, maximum_parallel_tasks=maximum_parallel_tasks,
        request=RunCampaignRequest(control.package_path,
        confirmed=True, reveal_authority_id=control.reveal.authority_id))
    (tmp_path / 'run-report.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    assert report['status'] == 'SUCCEEDED', report
    plan = control.service._load_status_execution_plan(control.package.run_plan_id)
    tasks = {task.task_id for task in plan.tasks}
    assert tasks == set(control.executor.contracts) == set(control.executor.ready)
    assert tasks == {task for task, _, _ in control.executor.completed}
    assert all(result.ready for result in control.executor.ready.values())
    assert all(pid != os.getpid() for _, _, pid in control.executor.completed)
    order = {task: index for index, (task, _, _) in enumerate(control.executor.completed)}
    assert all(order[dependency] < order[task.task_id]
        for task in plan.tasks for dependency in task.dependency_task_ids)
    execution_proof = {'parent_pid': os.getpid(), 'fixture_design': design,
        'role_counts': dict(case.allocation.role_counts),
        'source_entries': list(control.executor.source_entries.values()),
        'task_count': len(tasks), 'maximum_parallel_tasks': maximum_parallel_tasks,
        'workers': control.executor.completed,
        'prepared': {key: value.identity.to_document() for key, value in control.executor.contracts.items()},
        'ready': {key: value.proof() for key, value in control.executor.ready.items()}}
    # A later reader/recovery refusal must not discard completed-worker evidence.
    (tmp_path / 'actual-worker-execution-proof.json').write_text(json.dumps(execution_proof, sort_keys=True, indent=2) + '\n')
    before = _primary_census(case.plane, control.package.run_plan_id)
    receipts = []
    root = Path(case.plane.root.contract.canonical_path)
    for path in (root / 'runs' / control.package.run_plan_id / 'receipts').glob('*/*.json'):
        if not path.name.endswith('.manifest.json'):
            receipts.append(decode_canonical_bytes(path.read_bytes(), CanonicalTaskReceipt, maximum_bytes=1024**2))
    ordinary = tuple(row for row in receipts if row.task_id in tasks)
    assert len(ordinary) == len(tasks) and {row.task_id for row in ordinary} == tasks
    native_receipts = _native_receipt_census(case.plane, control.package.run_plan_id, plan,
        {key for key, contract in control.executor.contracts.items() if contract.native_effect},
        tuple(row for row in receipts if row.task_id not in tasks))
    assessment_task = statistical_task_id(case.specification.identity, case.allocation.identity, 'assess')
    assert any(row.task_id == assessment_task for row in receipts)
    (tmp_path / 'primary-census-before-read.json').write_text(json.dumps({
        'primary_census': before, 'native_subwork_receipts': native_receipts}, sort_keys=True, indent=2) + '\n')
    count = len(control.executor.completed)
    ready_before = _ready_census(tmp_path)
    catalog_before = _catalog_census(tmp_path, control.catalog)
    custody_before = {'run_id': control.package.run_plan_id,
        'original_commit': control.package.implementation_commit,
        'primary_census_before': before, 'ready_census_before': ready_before,
        'original_catalogs_before': catalog_before,
        'workers_before_read': tuple(control.executor.completed)}
    (tmp_path / 'recovery-custody-before-read.json').write_text(
        json.dumps(custody_before, sort_keys=True, indent=2) + '\n')
    status = measurements.call('completed_read', programme.read, directory=directory,
        reveal_authority_id=control.reveal.authority_id,
        request=CampaignStatusRequest(control.package.run_plan_id, include_attempt_history=True))
    scientific = status['scientific_result']
    assessment = decode_canonical_record(scientific['assessment'], science.ProtectedE3Assessment)
    assert len(assessment.decisions) == len(case.allocation.unit_ids('evaluation'))
    assert assessment.usable_units <= len(assessment.decisions)
    assert scientific['scientific_status'] == 'UNEVALUABLE'
    assert scientific['training_provenance']['bank_edition'] == 'LEGACY_BANKS'
    assert scientific['training_provenance']['data_origin'] == 'NOT_REESTABLISHED_BY_THIS_READ'
    assert scientific['training_provenance']['units'] == list(case.allocation.unit_ids('train'))
    assert 'models' in scientific['custody']
    assert scientific['denominators']['confirmation']['assigned_units'] == len(assessment.decisions)
    assert scientific['denominators']['confirmation']['usable_units'] == assessment.usable_units
    (tmp_path / 'read-report.json').write_text(json.dumps(status, sort_keys=True, indent=2) + '\n')

    # Recovery owns a private projection; every original catalog and Ready
    # byte is preserved. Any worker dispatch fails this completed-work control.
    class _NeverExecute(LocalProcessExecutor):
        def __init__(self, root, _evidence_directory):
            super().__init__(scratch_root=root)
            self.calls = []

        def execute(self, *args, **kwargs):
            self.calls.append("execute")
            pytest.fail("completed recovery entered an execution worker")

        def execute_deadline_free(self, *args, **kwargs):
            self.calls.append("execute_deadline_free")
            pytest.fail("completed recovery entered a native worker")

    ready_after_read = _ready_census(tmp_path)
    catalog_after_read = _catalog_census(tmp_path, control.catalog)
    primary_after_read = _primary_census(case.plane, control.package.run_plan_id)
    assert ready_after_read == ready_before and catalog_after_read == catalog_before
    assert primary_after_read == before
    custody_after_read = {**custody_before,
        'primary_census_after_read': primary_after_read, 'ready_census_after_read': ready_after_read,
        'original_catalogs_after_read': catalog_after_read,
        'workers_after_read': tuple(control.executor.completed)}
    (tmp_path / 'recovery-custody-after-read.json').write_text(
        json.dumps(custody_after_read, sort_keys=True, indent=2) + '\n')
    recovery_output = tmp_path / 'private-recovery'
    recovery_output.mkdir()
    recovery_control = _execution(case, handoff, issued, recovery_output, executor_factory=_NeverExecute)
    assert recovery_control.package_path.read_bytes() == control.package_path.read_bytes()
    for relative, reference in catalog_before.items():
        original, private = tmp_path / relative, recovery_output / relative
        assert not private.exists()
        private.write_bytes(original.read_bytes())
        assert sha256(private.read_bytes()).hexdigest() == reference['sha256']
    private_before = _catalog_census(recovery_output, recovery_control.catalog)
    recovery_programme = ExperimentProgrammeService(ROOT, case.plane, profile,
        prospective_api_factory=lambda **_arguments: recovery_control.api)
    recovery_control.catalog.unlink()
    for suffix in ('-wal', '-shm'):
        recovery_control.catalog.with_name(recovery_control.catalog.name + suffix).unlink(missing_ok=True)
    assert not recovery_control.catalog.exists()
    recovery_request = ResumeCampaignRequest(control.package.run_plan_id, confirmed=True,
        reveal_authority_id=control.reveal.authority_id)
    recovered = measurements.call('catalog_loss_recovery', recovery_programme.recover, directory=directory, maximum_parallel_tasks=maximum_parallel_tasks, request=recovery_request)
    (tmp_path / 'recover-report.json').write_text(json.dumps(recovered, sort_keys=True, indent=2) + '\n')
    assert status['status'] == recovered['status'] == 'SUCCEEDED', (status, recovered)
    assert len(control.executor.completed) == count
    assert recovery_control.executor.calls == []
    assert recovery_control.catalog.exists()
    assert not (recovery_output / 'worker-ready').exists()
    assert _primary_census(case.plane, control.package.run_plan_id) == before
    ready_after = _ready_census(tmp_path)
    catalog_after = _catalog_census(tmp_path, control.catalog)
    assert ready_after == ready_before and catalog_after == catalog_before
    assert report['programme'] == status['programme'] == recovered['programme']
    custody = {**custody_after_read,
        'claim': 'Completed exposed-worker custody; private recovery forbids all execution',
        'primary_census_after_recover': _primary_census(case.plane, control.package.run_plan_id),
        'ready_census_after_recover': ready_after, 'original_catalogs_after_recover': catalog_after,
        'workers_after_recover': tuple(control.executor.completed),
        'recovery_executor_calls': recovery_control.executor.calls,
        'private_catalog_census_before': private_before,
        'private_catalog_census_after': _catalog_census(recovery_output, recovery_control.catalog),
        'private_catalog_deleted_and_rebuilt': True,
        'private_catalog_path': str(recovery_control.catalog),
        'private_recovery_directory': recovery_output.relative_to(tmp_path).as_posix()}
    (tmp_path / 'recovery-custody-proof.json').write_text(json.dumps(custody, sort_keys=True, indent=2) + '\n')
    proof = {'claim': 'Actual public protected-declaration worker software conformance over exposed originals and synthetic authority',
        'qualification': 'NOT_ESTABLISHED', **execution_proof,
        'assessment': assessment.to_document(), 'primary_census': before,
        'native_subwork_receipts': native_receipts,
        'recovery_repeated_acquisition': False,
        'recovery_custody_proof': 'recovery-custody-proof.json'}
    (tmp_path / 'actual-worker-public-e3-proof.json').write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n')

    measurements.finish()
