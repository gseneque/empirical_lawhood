# SPDX-License-Identifier: MPL-2.0
"""Programme runtime authority controls; no full64 qualification is fabricated.

The retained six-task fixture proves current generic issued-control joins only.
Confirmation records below are explicitly synthetic static declarations. They
never supply genuine programme issue, qualification, source or native authority.
"""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_scheduled_programme_runtime as api
from empirical_lawhood.api import current_task_custody as custody
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import MatrixResponseErrorModel
from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    calibration as legacy_calibration, forecast, programme_calibration_bindings as calibration,
    programme_confirmation as confirmation,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_qualified_parent import ScheduledProgrammeQualifiedParentDeclaration
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole, ScientificConditionScope
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.execution import (
    DependencyReceiptBinding, ParentPreparedTaskRunner, TaskContext, VerifiedArtifactInput, WorkerInputBinding,
    WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort,
)
from empirical_lawhood.runtime.recursive_qualified_parents import RecursiveQualifiedParentBinding
from tests.runtime_platform.test_recursive_prior_execution_replay import sealed_parent_fixture as sealed_parent_fixture
from tests.test_matrix_scheduled_programme_reduction import declared as declared
from tests.runtime_platform.test_native_subwork import _plane


class Unread:
    bytes_read = 0
    def read(self, size=-1):
        pytest.fail('authority/preparation metadata control read an input port')
    def close(self):
        pass


def _context(fixture, task_id='observe'):
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    task = next(t for t in fixture.execution_plan.tasks if t.task_id == task_id)
    run = fixture.package.run_plan_id
    receipts = ExternalTaskReceiptStore(fixture.plane)
    inputs, headers = [], []
    for dependency in task.dependency_task_ids:
        receipt = receipts.read(run, dependency, run+'.'+dependency+'.attempt-001')
        assert receipt is not None
        physical = {p.logical_artifact_id: p for p in receipt.output_materializations}
        inputs.extend((VerifiedArtifactInput(l, physical[l.logical_artifact_id]), WorkerInputKind.DEPENDENCY)
            for l in receipt.output_logical_artifacts)
        headers.append(DependencyReceiptBinding(receipt.receipt_id, dependency,
            tuple(sorted(p.materialization_id for p in receipt.output_materializations))))
    for external in task.external_inputs:
        relative, _, _ = provider_input_location(fixture.plane, run, external.logical_artifact_id)
        m = fixture.plane.read_manifest(relative)
        inputs.append((VerifiedArtifactInput(m.logical, m.materialization), WorkerInputKind.EXTERNAL))
    ports = tuple(sorted((WorkerInputPort(WorkerInputBinding.from_verified(v, kind=kind), Unread())
        for v, kind in inputs), key=lambda p: p.artifact_id))
    context = TaskContext(run, task.task_id, run+'.'+task.task_id+'.attempt-001', task.capability.config,
        tuple(p.binding for p in ports), ports,
        tuple(WorkerOutputPort(o.output_id, o.payload_schema, o.profile, o.media_type, o.logical_artifact_id) for o in task.outputs),
        task.capability.required_permissions, task.capability.requested_outcome_access, task.capability.requested_resources,
        WorkerIsolationProfile.TRUSTED_LOCAL, tuple(sorted(headers, key=lambda r: r.receipt_id)))
    runner = SimpleNamespace(manifest=fixture.package.registry.resolve(task.capability.capability_key, task.capability.capability_version))
    return context, runner, task


def _supplier(fixture, *, reveal=None):
    return api.ProgrammeRuntimeInputSupplier(SimpleNamespace(resolve_input=lambda spec: spec), writer=fixture.plane,
        output_codecs=fixture.handoff.compilation.output_codecs, reveal_authority_id=reveal)


def _block_protected(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail('programme preparation opened protected parent bytes before current authority/refusal')
    monkeypatch.setattr(api, '_output_payload', blocked)
    monkeypatch.setattr(api, 'authenticate_programme_qualified_parent', blocked)
    monkeypatch.setattr(api, '_authenticate_prior_execution', blocked)


def test_supplier_delegates_exact_input_and_runtime_handoff_construction_does_no_preparation(sealed_parent_fixture, monkeypatch):
    fixture = sealed_parent_fixture
    _block_protected(monkeypatch)
    spec, payload, calls = object(), object(), []
    delegate = SimpleNamespace(resolve_input=lambda value: calls.append(value) or payload)
    supplier = api.ProgrammeRuntimeInputSupplier(delegate, writer=fixture.plane,
        output_codecs=fixture.handoff.compilation.output_codecs)
    assert supplier.resolve_input(spec) is payload and calls == [spec]
    monkeypatch.setattr(api.ProgrammeRuntimeInputSupplier, '_current',
        lambda *args: pytest.fail('handoff construction authenticated or prepared runtime authority'))
    bound = api.bind_programme_runtime_handoff(fixture.handoff, writer=fixture.plane)
    assert tuple(p.port_key for p in bound.platform_ports) == tuple(p.port_key for p in fixture.handoff.platform_ports)
    assert all(type(p.port.supplier) is api.ProgrammeRuntimeInputSupplier for p in bound.platform_ports)
    assert all(p.port.supplier.supplier is old.port.supplier for p, old in zip(bound.platform_ports, fixture.handoff.platform_ports, strict=True))
    assert fixture.executor.invocations == 6


def test_actual_six_task_current_package_and_inputs_authenticate_without_port_reads(sealed_parent_fixture):
    fixture = sealed_parent_fixture
    context, runner, task = _context(fixture)
    supplier = _supplier(fixture)
    assert supplier._current(context, runner) == (fixture.package, fixture.execution_plan, task)
    receipts, controls = supplier._inputs(context, task)
    assert receipts == {} and set(controls) == {p.logical_artifact_id for p in task.external_inputs}
    assert all(p.bytes_read == 0 for p in context.input_ports) and fixture.executor.invocations == 6


def test_shared_custody_authenticates_actual_task_controls_and_rechecks_current_grant(sealed_parent_fixture, monkeypatch):
    """Reusing one service must not retain authority after the stored grant disappears."""
    from tests.runtime_platform.test_recursive_compiler import Config
    fixture = sealed_parent_fixture
    context, runner, task = _context(fixture)
    selected = custody.CurrentIssuedTaskCustody(writer=fixture.plane)
    assert selected.current_task(context, runner) == (fixture.package, fixture.execution_plan, task)
    receipts, controls = selected.task_inputs(context, task)
    assert receipts == {}
    assert selected.control_record(controls[context.config.artifact_id], Config, 4096,
        expected_outcome_access=Access.EVALUATION_SEALED) == Config('config.synthetic.observe', 3)
    actual = ExternalStudyOperationAuthorityStore.load

    def absent(self, key):
        if key == fixture.package.execution_authority.authority_id:
            raise FileNotFoundError('actual current execution grant removed')
        return actual(self, key)

    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', absent)
    with pytest.raises(FileNotFoundError, match='grant removed'):
        selected.current_task(context, runner)
    assert all(p.bytes_read == 0 for p in context.input_ports) and fixture.executor.invocations == 6


def test_current_input_materialization_substitution_refuses_exact_bindings(sealed_parent_fixture):
    fixture = sealed_parent_fixture
    context, _, task = _context(fixture)
    ports = tuple(WorkerInputPort(replace(p.binding, materialization_id='materialization.foreign') if i == 0 else p.binding,
        Unread()) for i, p in enumerate(context.input_ports))
    changed = replace(context, input_ports=ports, input_bindings=tuple(p.binding for p in ports))
    with pytest.raises(PermissionError, match='complete actual current task input bindings'):
        _supplier(fixture)._inputs(changed, task)
    assert all(p.bytes_read == 0 for p in ports) and fixture.executor.invocations == 6


def test_metadata_input_rule_accepts_selected_subset_of_actual_multioutput_receipt(tmp_path, monkeypatch):
    """Pure selection control; this dummy plan is not a current issued programme."""
    from tests.runtime_platform.test_recursive_prior_native_replay import _blocked_progress, _stored
    from empirical_lawhood.runtime.plans import BarrierKind, ScientificInputRole, ScientificInputSpec
    _blocked_progress(monkeypatch)
    fixture = _stored(tmp_path)
    inspection = fixture.inspections[0]
    receipt, = (inspection.receipt,)
    selected, = inspection.outputs
    edge = ScientificInputSpec('edge.synthetic.selected-native-output', 'selected-output', ScientificInputRole.HISTORY,
        receipt.task_id, receipt.task_id+'.dummy', None, selected.logical.logical_artifact_id,
        selected.logical.logical_artifact_id, selected.logical.payload_schema, selected.logical.media_type, 4096,
        selected.logical.outcome_access, selected.logical.visibility_ceiling, BarrierKind.NONE)
    task = replace(fixture.native, task_id='consumer.synthetic', dependency_task_ids=(receipt.task_id,),
        external_inputs=(), scientific_inputs=(edge,))
    port = WorkerInputPort(WorkerInputBinding.from_verified(VerifiedArtifactInput(selected.logical, selected.materialization),
        kind=WorkerInputKind.DEPENDENCY), Unread())
    header = DependencyReceiptBinding(receipt.receipt_id, receipt.task_id, (port.materialization_id,))
    context = TaskContext(fixture.binding.run_id, task.task_id, 'attempt.synthetic.consumer', task.capability.config,
        (port.binding,), (port,), (), task.capability.required_permissions, task.capability.requested_outcome_access,
        task.capability.requested_resources, WorkerIsolationProfile.TRUSTED_LOCAL, (header,))
    supplier = api.ProgrammeRuntimeInputSupplier(SimpleNamespace(resolve_input=lambda spec: spec), writer=fixture.plane, output_codecs={})
    receipts, controls = supplier._inputs(context, task)
    assert receipts == {receipt.task_id: receipt} and controls == {} and port.bytes_read == 0
    all_outputs = tuple(sorted(p.materialization_id for p in receipt.output_materializations))
    assert len(all_outputs) == 2
    physical = {p.logical_artifact_id: p for p in receipt.output_materializations}
    all_ports = tuple(sorted((WorkerInputPort(WorkerInputBinding.from_verified(VerifiedArtifactInput(l, physical[l.logical_artifact_id]),
        kind=WorkerInputKind.DEPENDENCY), Unread()) for l in receipt.output_logical_artifacts), key=lambda p: p.artifact_id))
    expanded = replace(context, input_ports=all_ports, input_bindings=tuple(p.binding for p in all_ports),
        dependency_receipts=(replace(header, output_materialization_ids=all_outputs),))
    with pytest.raises(PermissionError, match='selected actual dependency outputs'):
        supplier._inputs(expanded, task)


@pytest.mark.parametrize('mutation', ('wrong-context', 'permissions', 'task', 'config', 'access', 'resources', 'outputs'))
def test_foreign_current_context_refuses_before_protected_reads(sealed_parent_fixture, monkeypatch, mutation):
    fixture = sealed_parent_fixture
    context, runner, _ = _context(fixture)
    _block_protected(monkeypatch)
    if mutation == 'wrong-context':
        context = object()
    elif mutation == 'permissions':
        context = replace(context, permissions=())
    elif mutation == 'task':
        context = replace(context, task_id='task.foreign')
    elif mutation == 'config':
        context = replace(context, config=replace(context.config, content_sha256='0'*64))
    elif mutation == 'access':
        context = replace(context, outcome_access=Access.OUTCOME_BLIND)
    elif mutation == 'resources':
        context = replace(context, resource_budget=replace(context.resource_budget, output_bytes=context.resource_budget.output_bytes+1))
    else:
        context = replace(context, output_ports=())
    with pytest.raises(PermissionError):
        _supplier(fixture)._current(context, runner)
    assert fixture.executor.invocations == 6


@pytest.mark.parametrize('missing', ('package', 'execution', 'reveal'))
def test_missing_current_package_execute_or_reveal_refuses_before_protected_reads(sealed_parent_fixture, monkeypatch, missing):
    fixture = sealed_parent_fixture
    context, runner, _ = _context(fixture)
    _block_protected(monkeypatch)
    if missing == 'package':
        monkeypatch.setattr(custody, '_actual_package', lambda *args: (_ for _ in ()).throw(FileNotFoundError('actual current package absent')))
    elif missing == 'execution':
        actual = ExternalStudyOperationAuthorityStore.load
        def absent(self, key):
            if key == fixture.package.execution_authority.authority_id:
                raise FileNotFoundError('actual current execution grant absent')
            return actual(self, key)
        monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', absent)
    else:
        # Exercise the actual issued REVEAL task with its complete original
        # configuration/ports/permissions. Relabelling observe would correctly
        # refuse at the preceding installed-task guard without testing reveal.
        from empirical_lawhood.runtime.plans import BarrierKind
        context, runner, task = _context(fixture, 'evaluate')
        assert task.barrier is BarrierKind.REVEAL and context.task_id == task.task_id
    with pytest.raises((PermissionError, FileNotFoundError), match='package absent|execution grant absent|reveal grant'):
        _supplier(fixture)._current(context, runner)
    assert fixture.executor.invocations == 6


def test_selected_actual_reveal_does_not_authorize_an_unissued_programme_task(sealed_parent_fixture, monkeypatch):
    fixture = sealed_parent_fixture
    context, runner, _ = _context(fixture)
    _block_protected(monkeypatch)
    with pytest.raises(PermissionError, match='installed task/config/access'):
        _supplier(fixture, reveal=fixture.reveal.authority_id)._current(replace(context, task_id=api.QUALIFY_TASK_ID), runner)
    assert fixture.executor.invocations == 6


def test_wrong_adjudication_context_refuses_before_any_domain_inputs(sealed_parent_fixture, monkeypatch):
    """Injected plan metadata tests refusal order, not a positive global issue."""
    from empirical_lawhood.api.execution import CampaignExecutionService
    fixture = sealed_parent_fixture
    original_context, runner, task = _context(fixture, 'evaluate')
    renamed = replace(task, task_id=api.QUALIFY_TASK_ID)
    plan = replace(fixture.execution_plan, tasks=tuple(sorted((renamed if t.task_id == task.task_id else t
        for t in fixture.execution_plan.tasks), key=lambda t: t.task_id)))
    context = replace(original_context, task_id=api.QUALIFY_TASK_ID, scientific_adjudication_context=None)
    _block_protected(monkeypatch)
    monkeypatch.setattr(custody, 'authenticate_current_execution_plan', lambda **kwargs: plan)
    monkeypatch.setattr(CampaignExecutionService, '_bind_scientific_adjudication',
        lambda *args, **kwargs: SimpleNamespace(context=object()))
    monkeypatch.setattr(api.ProgrammeRuntimeInputSupplier, '_inputs',
        lambda *args: pytest.fail('incorrect adjudication context reached domain input preparation'))
    with pytest.raises(PermissionError, match='genuine global reveal context'):
        _supplier(fixture, reveal=fixture.reveal.authority_id).prepare_programme_task(context, runner)
    assert fixture.executor.invocations == 6


def test_actual_foreign_runtime_role_refuses_before_domain_control_or_outcomes(sealed_parent_fixture, monkeypatch):
    fixture = sealed_parent_fixture
    context, runner, _ = _context(fixture)
    _block_protected(monkeypatch)
    monkeypatch.setattr(api.ProgrammeRuntimeInputSupplier, '_control',
        lambda *args: pytest.fail('foreign runtime role read a domain configuration'))
    with pytest.raises(PermissionError, match='undeclared runtime role'):
        _supplier(fixture).prepare_programme_task(context, runner)
    assert fixture.executor.invocations == 6


def test_candidate_confirmation_and_qualifier_runners_require_preparation_before_port_reads(sealed_parent_fixture):
    fixture = sealed_parent_fixture
    context, _, _ = _context(fixture)
    factory, = confirmation.operation_factories()
    assert factory.manifest.capability_key == confirmation.CAPABILITY_KEY
    raw = factory.runner_factory()
    assert raw.authenticated_parent is None
    context = replace(context, task_id=confirmation.GLOBAL_TASK_ID, permissions=raw.manifest.permissions, outcome_access=Access.OUTCOME_BLIND)
    with pytest.raises(PermissionError, match='prepared runtime authority'):
        raw.execute(context)
    calls = []
    def prepare(*args):
        calls.append(args)
        raise PermissionError('no actual current preparation supplied')
    wrapped = factory.runner_preparation_factory(SimpleNamespace(prepare_programme_task=prepare), raw)
    assert type(wrapped) is ParentPreparedTaskRunner and calls == []
    with pytest.raises(PermissionError, match='PARENT_RUNNER_PREPARATION_REQUIRED'):
        wrapped.execute(context)
    assert calls == []
    qualifier = calibration.ScheduledProgrammeCalibrator('calibration-qualify')
    assert qualifier.verified_custody is None
    context = replace(context, task_id=api.QUALIFY_TASK_ID, permissions=qualifier.manifest.permissions,
        outcome_access=Access.EVALUATOR_REVEAL)
    with pytest.raises(PermissionError, match='parent-side original custody preparation'):
        qualifier.execute(context)
    assert fixture.executor.invocations == 6


def _pin(key, schema, version='1.0.0'):
    return ObjectIdentity(key, schema, version, sha256(key.encode()).hexdigest())


def test_confirmation_static_records_remain_distinct_and_cannot_prepare_runtime(declared, tmp_path):
    """Only typed static fixture records; none are authenticated qualifications."""
    programme, _ = declared
    rows = tuple(forecast.ScheduledCalibrationCase(c.root_id, c.independent_group_id, c.source, c.coordinate,
        c.information_cutoff.coordinate, _pin('score.synthetic.'+c.root_id, 'empirical-lawhood/matrix-scheduled-history/response-score'),
        _pin('forecast.synthetic.'+c.root_id, forecast.ScheduledForecastSeal.SCHEMA),
        'receipt.score.synthetic.'+c.root_id, 'receipt.forecast.synthetic.'+c.root_id,
        'materialization.score.synthetic.'+c.root_id, 'materialization.forecast.synthetic.'+c.root_id,
        'FINITE', (Decimal(1),)*15, (Decimal(0),)*15) for c in programme.cases)
    semantic = forecast.ScheduledCalibration('calibration.synthetic.complete64', programme.reservation,
        _pin('model.synthetic', MatrixResponseErrorModel.SCHEMA), programme.criterion, programme.allocation,
        programme.calibration_criterion, 'unit.synthetic.whole-group', tuple(sorted({c.family_id for c in programme.cases})),
        rows, programme.group_ids, legacy_calibration.reduce_cases(rows),
        tuple(sorted((c.score for c in rows), key=lambda p: p.object_id)), forecast._case_digest(rows))
    plane = _plane(tmp_path/'static-parent')
    pub = plane.write(ArtifactWriteRequest('artifact.synthetic.calibration', 'inputs/static-calibration.json', semantic.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.synthetic.calibration', 'inputs',
        semantic.canonical_bytes(), Visibility.PROSPECTIVE, (), Access.EVALUATION_SEALED))
    scope = ScientificConditionScope('system.synthetic', 'world.synthetic', 'source.synthetic', ('receiver',), ('1',),
        'receiver.synthetic', 'clock.synthetic', 'Synthetic original record scope only',
        source_config_sha256=semantic.fingerprint(), population_id=semantic.calibration_id)
    record = ObjectIdentity.from_record(semantic.calibration_id, semantic)
    producer = _pin('receipt.synthetic.calibrate', CanonicalTaskReceipt.SCHEMA)
    product = ContributionProduct('product.synthetic.calibration', record,
        ArtifactIdentity(pub.logical.logical_artifact_id, 'software-declared-parent', semantic.SCHEMA, semantic.fingerprint(),
            'application/json', len(semantic.canonical_bytes())), producer, ContributionRole.QUALIFIED_EVIDENTIAL_PARENT,
        EvidenceCeiling.RESPONSE, Access.EVALUATION_SEALED, Visibility.PROSPECTIVE)
    adjudication = _pin('adjudication.synthetic', 'empirical-lawhood/runtime/scientific-adjudication-record')
    contribution = ContributionManifest('contribution.synthetic.parent', 'Synthetic parent record closure?',
        'Static software declarations provide no qualification', scope, (product,), (adjudication,), ())
    binding = RecursiveQualifiedParentBinding('binding.synthetic.parent', 'external.synthetic.parent', contribution.contribution_id,
        product.product_id, _pin('issue.synthetic', 'empirical-lawhood/runtime/issued-executable-study-manifest'),
        _pin('execution.synthetic', 'empirical-lawhood/planning/study-operation-authority'),
        _pin('reveal.synthetic', 'empirical-lawhood/planning/study-operation-authority'), 'run.synthetic',
        api.CALIBRATE_TASK_ID, producer.object_id, api.QUALIFY_TASK_ID, 'receipt.synthetic.qualify',
        api.QUALIFY_TASK_ID+'.adjudication', adjudication)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_calibration import ScheduledProgrammeCalibrationEvidence
    declaration = ScheduledProgrammeQualifiedParentDeclaration('declaration.synthetic.parent', record, pub, contribution, binding,
        programme.identity, _pin('evidence.synthetic', ScheduledProgrammeCalibrationEvidence.SCHEMA), semantic.model,
        semantic.criterion, semantic.reservation, semantic.group_ids)
    query = replace(programme, programme_id='programme.synthetic.confirmation', mode='E4_CONFIRMATION',
        cases=tuple(replace(c, role='CONFIRMATION') for c in programme.cases))
    config = confirmation.ScheduledProgrammeConfirmationGlobalConfig(confirmation.CONFIG_ID, query, query.bank, declaration)
    assert config.SCHEMA != api.ScheduledProgrammeCalibrationConfig.SCHEMA
    assert len(config.canonical_bytes()) <= 4*1024**2
    assert decode_canonical_bytes(config.canonical_bytes(), confirmation.ScheduledProgrammeConfirmationGlobalConfig,
        maximum_bytes=4*1024**2) == config
    with pytest.raises(ValueError, match='distinct bounded'):
        replace(config, programme=programme)
    with pytest.raises(ValueError, match='distinct bounded'):
        replace(config, config_id='config.'+api.QUALIFY_TASK_ID)
    with pytest.raises(ValueError, match='sealed parent locators'):
        replace(declaration, group_ids=declaration.group_ids[:-1])
