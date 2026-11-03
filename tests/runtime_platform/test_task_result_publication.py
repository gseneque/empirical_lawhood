"""Ordinary result publication controls, without task or native entry.

Contacts and implementation bindings below are disclosed software fixtures.
They neither authenticate historical source/custody nor supply current authority.
Real artifact and receipt stores publish literal negative scientific records.
"""
from copy import copy
from types import SimpleNamespace
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.runtime.recovery import ProtocolRunRecoveryIndex
from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry

from dataclasses import dataclass, fields, replace
from hashlib import sha256
import json
from pathlib import Path
import pytest
from empirical_lawhood.infrastructure import execution as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_task_receipt
from empirical_lawhood.kernel.admission import AdmissionGateKind, AdmissionGateResult, GateStatus
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactSemanticValidationRegistry, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import ExecutionTask, ProtocolExecutionTask
from empirical_lawhood.runtime.providers import CapabilityOutputSemanticContract
from tests.runtime_platform.conftest import protocol_fixture as protocol_fixture
from tests.runtime_platform.support import IMPLEMENTATION_COMMIT
from tests.runtime_platform.test_execution_scheduler import _external_inputs, _plane

@pytest.fixture(autouse=True)
def forbid_task_entry(monkeypatch):

    def forbidden(*_args, **_kwargs):
        pytest.fail('retained publication must not construct a scheduler or enter a worker')
    for cls, names in ((owner.LocalScheduler, ('execute', '_run_attempt', '_begin_native_contact')), (owner.DirectTaskExecutor, ('execute',)), (owner.LocalProcessExecutor, ('execute',))):
        for name in names:
            monkeypatch.setattr(cls, name, forbidden)

@dataclass(frozen=True)
class PublicationCase:
    root: Path
    publisher: owner.LocalScheduler
    task: ExecutionTask
    external_inputs: tuple
    run_id: str
    attempt_id: str
    product: AdmissionGateResult
    result: RunnerResult

def _make_case(root, protocol_fixture, *, status=GateStatus.FAIL):
    root.mkdir(parents=True, exist_ok=True)
    original = next((task for task in protocol_fixture.execution_plan.tasks if task.task_id == 'prepare'))
    assert original.dependency_task_ids == ()
    output = replace(original.outputs[0], logical_artifact_id='artifact.disclosed.retained-admission', relative_path=f'runs/{protocol_fixture.run_plan.run_plan_id}/outputs/retained-admission.json', payload_schema=AdmissionGateResult.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json', visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, parent_visibility_ceilings=(VisibilityCeiling.PROSPECTIVE,), outcome_access=OutcomeAccess.OUTCOME_BLIND)
    task_values = {field.name: getattr(original, field.name) for field in fields(ProtocolExecutionTask)}
    task_values['outputs'] = (output,)
    task_values['capability'] = replace(original.capability, required_output_schema_ids=(AdmissionGateResult.SCHEMA,), requested_resources=replace(original.capability.requested_resources, output_bytes=4096))
    task = ExecutionTask(**task_values, scientific_inputs=())
    contract = CapabilityOutputSemanticContract(capability_key=task.capability.capability_key, capability_version=task.capability.capability_version, capability_implementation_sha256=task.capability_implementation_sha256, payload_schema=AdmissionGateResult.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON, top_level_keys=('schema', 'value', 'version'), value_keys=('constraint_ids', 'evidence_link_ids', 'gate_id', 'kind', 'margin', 'reason_codes', 'status'), record_version=AdmissionGateResult.VERSION)
    semantics = ArtifactSemanticValidationRegistry.from_registrations(registry_id='semantic.disclosed.retained-admission', registrations=(contract.artifact_validation_registration(logical_artifact_id=output.logical_artifact_id, task_id=task.task_id, output_id=output.output_id),))
    plane = _plane(root, semantics)
    inputs = _external_inputs(plane, protocol_fixture).resolve(task.external_input_artifact_ids)
    run_id = protocol_fixture.run_plan.run_plan_id
    product = AdmissionGateResult(gate_id='gate.disclosed.retained', kind=AdmissionGateKind.UNCERTAINTY, status=status, constraint_ids=('constraint.disclosed.radius',), margin=None, reason_codes=('EXPOSED_SOFTWARE_COUNTEREXAMPLE',), evidence_link_ids=())
    plan = replace(protocol_fixture.execution_plan, tasks=tuple((task if row.task_id == task.task_id else row for row in protocol_fixture.execution_plan.tasks)))
    index = ProtocolRunRecoveryIndex.from_execution_plan(plan, run_id=run_id, wave_id='wave.software.publication',
        authority_identities=(ObjectIdentity('authority.disclosed.publication',
            'empirical-lawhood/testing/publication-authority', '1.0.0', 'a' * 64),))
    publisher = owner.LocalScheduler(operational_repository=SimpleNamespace(), artifact_writer=plane, receipt_store=ExternalTaskReceiptStore(plane), recovery_index=index, recovery_store=ExternalRunRecoveryStore(plane), runner_registry=RunnerRegistry((), registry_sha256=plan.registry_sha256), implementation_commit=IMPLEMENTATION_COMMIT, output_semantic_contracts=(contract,), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
    result = RunnerResult(outputs=(TaskOutputPayload(output.output_id, product.canonical_bytes()),), checks=(ReceiptCheck('retained-contract-passed', True, ()),))
    return PublicationCase(root, publisher, task, inputs, run_id, f'{run_id}.{task.task_id}.attempt-001', product, result)

@pytest.fixture
def case(tmp_path, protocol_fixture):
    return _make_case(tmp_path, protocol_fixture)

def _files(root):
    return {str(path.relative_to(root)): (path.stat().st_size, sha256(path.read_bytes()).hexdigest()) for path in root.rglob('*') if path.is_file()}

@pytest.mark.parametrize('status', (GateStatus.FAIL, GateStatus.UNEVALUABLE))
def test_negative_typed_result_has_exact_successful_receipt_and_lineage(tmp_path, protocol_fixture, status):
    case = _make_case(tmp_path, protocol_fixture, status=status)
    publisher = case.publisher
    receipt = _publish(case, case.result, publisher=publisher)
    spec = case.task.outputs[0]
    plane = publisher.artifact_writer
    assert (case.root / spec.relative_path).read_bytes() == case.product.canonical_bytes()
    assert decode_canonical_bytes((case.root / spec.relative_path).read_bytes(), AdmissionGateResult, maximum_bytes=len(case.product.canonical_bytes())) == case.product
    assert json.loads((case.root / spec.relative_path).read_bytes())['value']['status'] == status.value
    manifest = plane.read_manifest(spec.relative_path)
    plane.verify_manifest(manifest)
    assert manifest.logical.content_sha256 == sha256(case.product.canonical_bytes()).hexdigest()
    assert manifest.logical.payload_schema == AdmissionGateResult.SCHEMA
    assert manifest.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert manifest.logical.outcome_access is OutcomeAccess.OUTCOME_BLIND
    expected_parents = tuple(sorted((ArtifactLineageParent(identity=ObjectIdentity.from_record(value.logical.logical_artifact_id, value.logical), visibility_ceiling=value.logical.visibility_ceiling, outcome_access=value.logical.outcome_access) for value in case.external_inputs), key=lambda value: (value.identity.object_id, value.identity.object_schema, value.identity.object_version, value.identity.object_fingerprint)))
    assert manifest.logical.lineage_parents == expected_parents
    assert manifest.publication.publication_scope.publication_scope_id == f'task-output-scope.{case.run_id}.{case.task.task_id}'
    assert manifest.publication.publication_scope.relative_root == f'runs/{case.run_id}'
    contract = next(iter(publisher.output_semantic_contracts.values()))
    assert manifest.logical.semantic_validation == contract.artifact_validation(task_id=case.task.task_id, output_id=spec.output_id)
    expected = CanonicalTaskReceipt(receipt_id=f'receipt.{case.attempt_id}', run_id=case.run_id, task_id=case.task.task_id, attempt_id=case.attempt_id, implementation_commit=IMPLEMENTATION_COMMIT, input_materialization_ids=tuple(sorted((value.materialization.materialization_id for value in case.external_inputs))), output_materializations=(manifest.materialization,), output_logical_artifacts=(manifest.logical,), checks=(ReceiptCheck('execution-assurance-trusted-local', True, ()), ReceiptCheck('retained-contract-passed', True, ())), operational_status=OperationalStatus.SUCCEEDED, reason_codes=())
    path = case.root / ExternalTaskReceiptStore._relative_path(case.run_id, case.task.task_id, case.attempt_id)
    assert receipt == expected
    assert path.read_bytes() == expected.canonical_bytes()
    assert decode_task_receipt(path.read_bytes()) == expected
    assert publisher.receipt_store.read(receipt.run_id, receipt.task_id, receipt.attempt_id) == expected
    assert not any((part in {'events', 'resource-events', 'native-subwork', 'recovery'} for name in _files(case.root) for part in Path(name).parts))

def test_publication_is_idempotent_and_conflicting_result_preserves_all_bytes(case):
    receipt = _publish(case, case.result)
    before = _files(case.root)
    assert _publish(case, case.result) == receipt
    assert _files(case.root) == before
    different = replace(case.product, reason_codes=('ANOTHER_EXPOSED_COUNTEREXAMPLE',))
    result = replace(case.result, outputs=(replace(case.result.outputs[0], payload=different.canonical_bytes()),))
    with pytest.raises(ArtifactIdentityConflict):
        _publish(case, result)
    assert _files(case.root) == before
    changed_checks = replace(case.result, checks=(ReceiptCheck('another-passing-check', True, ()),))
    with pytest.raises(ArtifactIdentityConflict):
        _publish(case, changed_checks)
    assert _files(case.root) == before

def test_receipt_failure_leaves_no_false_completion_and_retry_reuses_exact_output(case):

    class RefusingReceiptStore:

        def commit(self, *_args, **_kwargs):
            raise OSError('disclosed receipt publication interruption')
    refusing = _copy_publisher(case.publisher, receipt_store=RefusingReceiptStore())
    with pytest.raises(OSError, match='receipt publication interruption'):
        _publish(case, case.result, publisher=refusing)
    output = case.root / case.task.outputs[0].relative_path
    assert output.read_bytes() == case.product.canonical_bytes()
    receipt_path = case.root / ExternalTaskReceiptStore._relative_path(case.run_id, case.task.task_id, case.attempt_id)
    assert not receipt_path.exists()
    output_identity = (output.stat().st_ino, output.stat().st_mtime_ns, sha256(output.read_bytes()).hexdigest())
    receipt = _publish(case, case.result)
    assert receipt_path.read_bytes() == receipt.canonical_bytes()
    assert (output.stat().st_ino, output.stat().st_mtime_ns, sha256(output.read_bytes()).hexdigest()) == output_identity

@pytest.mark.parametrize('problem', ('missing-output', 'wrong-port', 'no-checks', 'failed-check', 'noncanonical', 'invalid-utf8', 'nonfinite', 'wrong-schema', 'wrong-version', 'wrong-value-shape'))
def test_bad_result_refuses_before_any_publication(case, problem):
    result = case.result
    document = json.loads(result.outputs[0].payload)
    if problem == 'missing-output':
        result = replace(result, outputs=())
    elif problem == 'wrong-port':
        result = replace(result, outputs=(replace(result.outputs[0], output_id='another.output'),))
    elif problem == 'no-checks':
        result = replace(result, checks=())
    elif problem == 'failed-check':
        result = replace(result, checks=(ReceiptCheck('literal-failed-check', False, ('FAILED',)),))
    else:
        if problem == 'noncanonical':
            raw = json.dumps(document, indent=2).encode()
        elif problem == 'invalid-utf8':
            raw = b'\xff'
        elif problem == 'nonfinite':
            raw = b'{"value":NaN}\n'
        else:
            if problem == 'wrong-schema':
                document['schema'] = 'empirical-lawhood/testing/fixtures/wrong-product'
            elif problem == 'wrong-version':
                document['version'] = '9.0.0'
            elif problem == 'wrong-value-shape':
                del document['value']['reason_codes']
            raw = (json.dumps(document, allow_nan=False, ensure_ascii=True, separators=(',', ':'), sort_keys=True) + '\n').encode('utf-8')
        result = replace(result, outputs=(replace(result.outputs[0], payload=raw),))
    before = _files(case.root)
    with pytest.raises(owner.SchedulerConsistencyError):
        _publish(case, result)
    assert _files(case.root) == before

@pytest.mark.parametrize('problem', ('missing-contract', 'wrong-implementation', 'wrong-record-version'))
def test_semantic_contract_is_mandatory_and_exact(case, problem):
    contract = next(iter(case.publisher.output_semantic_contracts.values()))
    if problem == 'missing-contract':
        contracts = {('another.capability', *contract.key[1:]): contract}
    elif problem == 'wrong-implementation':
        altered = replace(contract, capability_implementation_sha256='0' * 64)
        contracts = {altered.key: altered}
    else:
        altered = replace(contract, record_version='9.0.0')
        contracts = {altered.key: altered}
    publisher = _copy_publisher(case.publisher, output_semantic_contracts=contracts)
    before = _files(case.root)
    with pytest.raises(owner.SchedulerConsistencyError):
        _publish(case, case.result, publisher=publisher)
    assert _files(case.root) == before

@pytest.mark.parametrize('field', ('task_id', 'output_id', 'capability'))
def test_context_substitution_is_rejected_by_shared_semantic_consumer(case, field):
    contract = next(iter(case.publisher.output_semantic_contracts.values()))
    contract = replace(contract, top_level_keys=('capability', 'output_id', 'schema', 'task_id'), value_keys=(), record_version=None, task_id_field='task_id', output_id_field='output_id', capability_key_field='capability')
    publisher = _copy_publisher(case.publisher, output_semantic_contracts={contract.key: contract})
    document = {'schema': contract.payload_schema, 'task_id': case.task.task_id, 'output_id': case.task.outputs[0].output_id, 'capability': case.task.capability.capability_key}
    document[field] = 'substituted.fixture.identity'
    result = replace(case.result, outputs=(replace(case.result.outputs[0], payload=canonical_json_bytes(document)),))
    before = _files(case.root)
    with pytest.raises(owner.SchedulerConsistencyError, match='context binding'):
        _publish(case, result, publisher=publisher)
    assert _files(case.root) == before


def _copy_publisher(publisher, **changes):
    selected = copy(publisher)
    for name, value in changes.items():
        setattr(selected, name, value)
    return selected


def _publish(case, result, *, publisher=None, task=None):
    return owner.publish_runner_result(
        case.publisher if publisher is None else publisher, case.run_id,
        case.task if task is None else task, case.attempt_id, (), case.external_inputs, result,
    )


def test_frozen_output_budget_refuses_before_writes(case):
    task = replace(case.task, capability=replace(case.task.capability,
        requested_resources=replace(case.task.capability.requested_resources,
            output_bytes=len(case.result.outputs[0].payload) - 1)))
    before = _files(case.root)
    with pytest.raises(owner.SchedulerConsistencyError, match="output-byte budget"):
        _publish(case, case.result, task=task)
    assert _files(case.root) == before
