# SPDX-License-Identifier: MPL-2.0
"""Retained prior issued-execution replay; synthetic authority is software only."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_qualified_parents as owner
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.recovery import RecoveryTerminalDisposition
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from tests.runtime_platform.test_recursive_compiler import Config
from tests.runtime_platform.test_recursive_prospective_parents import (
    _authenticate, _parent_inputs, parent_fixture as parent_fixture,
)


@pytest.fixture(scope='module')
def sealed_parent_fixture(tmp_path_factory):
    """Add a sixth sealed observation before actual software issue and execution.

    The original five-task fixture has only blind/development/revealed outputs.
    Its original bytes are never relabelled. This new task uses the already
    declared evaluation unit and the original blind source, with no native work.
    """
    from tests.runtime_platform import test_recursive_prospective_workflow as workflow
    from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink, RecursiveOperationSpec
    from empirical_lawhood.planning.study_authoring import CapabilitySelection
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
    from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
    from empirical_lawhood.runtime.recursive_compiler import RecursiveOperationRegistration, RecursivePortContract, compile_recursive_wave
    from tests.experiment_entry_support import standard_authoring_for_draft

    original_compile, original_registrations = workflow.prospective_fixture, workflow._registrations
    units = ('unit.eval-01',)
    def validate_observe(config, context):
        if (context.node_id != 'observe' or context.stage is not ScientificStage.ACQUIRE
                or context.unit_ids != units or context.root.evaluation_unit_ids != units
                or set(units) & set(context.root.development_unit_ids)
                or context.outcome_access is not OutcomeAccess.EVALUATION_SEALED
                or context.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                or config != Config('config.synthetic.observe', 3)):
            raise ValueError('synthetic observation changes its actual declared evaluation unit/source stage')
    def registrations(compilation):
        return tuple(replace(r, scientific_unit_ids=lambda config: units, scientific_root_validator=validate_observe)
            if r.selection.capability_key == 'recursive-fixture.observe' else r
            for r in original_registrations(compilation))
    def with_observe(**kwargs):
        compilation, _, _ = original_compile(**kwargs)
        assert compilation.draft.prospective_draft.evaluation_unit_ids == units
        assert not set(units) & set(compilation.draft.prospective_draft.development_unit_ids)
        original = compilation.registry.resolve('recursive-fixture.prepare', '1.0.0')
        manifest = replace(original, capability_key='recursive-fixture.observe', kind=CapabilityKind.OBSERVATION_OPERATOR,
            maximum_outcome_access=OutcomeAccess.EVALUATION_SEALED,
            permissions=tuple(sorted({*original.permissions, CapabilityPermission.READ_SEALED_OUTCOMES})),
            output_schema_ids=(Config.SCHEMA,), implementation_sha256=sha256(b'local synthetic sealed evaluation observation').hexdigest())
        source = compilation.draft.external_inputs[0]
        registration = RecursiveOperationRegistration(CapabilitySelection(manifest.capability_key, manifest.capability_version,
            manifest.implementation_sha256), ScientificStage.ACQUIRE, Config,
            (RecursivePortContract('source', source.payload_schema, source.media_type, source.maximum_size_bytes),),
            (OutputTemplate('observation', Config.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
            manifest.permissions, OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE, manifest.resource_ceiling,
            BarrierKind.NONE, scientific_unit_ids=lambda config: units, scientific_root_validator=validate_observe)
        operation = RecursiveOperationSpec.from_config(node_id='observe', selection=registration.selection,
            config_id='config.synthetic.observe', config=Config('config.synthetic.observe', 3),
            obligation_ids=('synthetic-observe-declared-evaluation-unit',),
            resource_budget=next(o.resource_budget for o in compilation.draft.operations if o.node_id == 'prepare'))
        draft = replace(compilation.draft,
            operations=tuple(sorted((*compilation.draft.operations, operation), key=lambda value: value.node_id)),
            links=tuple(sorted((*compilation.draft.links, RecursiveInputLink('edge.source.observe', 'observe', 'source',
                external_input_id=source.input_id, scientific_role='PREPARED_MEDIUM'),
                RecursiveInputLink('edge.observe.evaluate', 'evaluate', 'input-observe', producer_node_id='observe',
                    producer_output_id='observation', scientific_role='OUTCOME')), key=lambda value: value.edge_id)),
            selected_operation_ids=tuple(sorted((*compilation.draft.selected_operation_ids, 'observe'))))
        registry = replace(compilation.registry, capabilities=tuple(sorted((*compilation.registry.capabilities, manifest),
            key=lambda value: value.registry_id)))
        original_regs = tuple(replace(r, input_ports=tuple(sorted((*r.input_ports,
            RecursivePortContract('input-observe', Config.SCHEMA, 'application/json', 1000)), key=lambda p: p.port_id)))
            if r.selection.capability_key == 'recursive-fixture.evaluate' else r for r in registrations(compilation))
        compiled = compile_recursive_wave(draft=draft, registrations=(*original_regs, registration),
            registry=registry, implementation_commit='a'*40, qualifications=compilation.candidate_context.qualifications,
            known_design_inputs=compilation.candidate_context.known_design_inputs, output_codecs=compilation.output_codecs)
        assert compiled.candidate_report.candidate is not None, compiled.candidate_report.diagnostics
        authoring, context = standard_authoring_for_draft(compiled.candidate_draft, compiled.candidate_context,
            formal_method_capability_key='recursive-fixture.evaluate')
        return compiled, authoring, context

    patch = pytest.MonkeyPatch()
    with patch.context() as monkeypatch:
        monkeypatch.setattr(workflow, 'prospective_fixture', with_observe)
        monkeypatch.setattr(workflow, '_registrations', registrations)
        parts = workflow._public_issued_handoff_fixture(tmp_path_factory.mktemp('sealed-prior-observe'), monkeypatch,
            reveal_terminal=True)
        handoff, factories, discovery, plane, raw, package, reveal, approval, authorities = parts
        # Use the unchanged actual campaign service with a counting test executor.
        # The existing five-task runner helper has an intentionally fixed count.
        from empirical_lawhood.api.execution import CampaignExecutionService
        from empirical_lawhood.api.facade import EmpiricalLawhoodApi
        from empirical_lawhood.api.results import RunCampaignRequest
        from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
        from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator
        from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
        from empirical_lawhood.infrastructure.study_issue import ExternalIssuedExtensionPayloadSource, ExternalIssuedStudyPublisher
        from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog
        from empirical_lawhood.runtime.executable_bindings import LayeredCampaignRuntimeProviderResolver
        from empirical_lawhood.runtime.issued_extension_payloads import IssuedExtensionPayloadResolver
        from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry
        from tests.execution_support import EnforcingTestTaskExecutor
        from tests.runtime_platform.test_study_issue import _PassthroughSourceInspector
        directory = handoff.directory.parent
        package_path = directory/'sealed-observation-package.json'
        package_path.write_bytes(package.canonical_bytes())
        catalog = directory/'sealed-observation-catalog.sqlite3'
        def engine_factory():
            engine = create_catalog_engine('sqlite+pysqlite:///'+str(catalog))
            upgrade_catalog(engine)
            return engine
        class CountingExecutor(EnforcingTestTaskExecutor):
            invocations = 0
            def execute_deadline_free(self, runner, task_context, *, progress_contract, progress_callback,
                    prepared_contract=None, provenance_requirements=(), native_work_preparer=None, native_entry=None):
                self.invocations += 1
                if prepared_contract is not None:
                    prepared_contract.__post_init__()
                    prepared_contract.validate_context(task_context)
                # This in-process service double supplies no child or native
                # conformance. It retains the actual parent preparation checks.
                assert not provenance_requirements and native_work_preparer is None and native_entry is None
                return self._delegate.execute_deadline_free(runner, task_context,
                    progress_contract=progress_contract, progress_callback=progress_callback)
        executor = CountingExecutor()
        service = CampaignExecutionService(repo_root=Path(__file__).resolve().parents[2], artifact_plane=plane,
            engine_factory=engine_factory, catalog_path=catalog, providers=CampaignRuntimeProviderRegistry(()),
            provider_resolver=LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()), factories=factories),
            executable_binding_aggregate=factories.aggregate,
            issued_extension_payload_resolver=IssuedExtensionPayloadResolver(source=ExternalIssuedExtensionPayloadSource(
                ExternalIssuedStudyPublisher(artifact_plane=plane, authority_store=authorities, grantee_id='operator.issue-service')),
                codecs=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY), executable_platform_ports=handoff.platform_ports,
            approval_service=approval, study_authority_store=authorities, study_source_closure_inspector=_PassthroughSourceInspector(),
            executor=executor, enforce_git_identity=False,
            execution_resource_envelope_coordinator=DurableExecutionResourceEnvelopeCoordinator(
                ExternalExecutionResourceEnvelopeStore(plane.root, artifact_plane=plane)))
        api = EmpiricalLawhoodApi(repo_root=directory, external_root=Path(plane.root.contract.canonical_path),
            execution_service=service, approval_service=approval, study_authority_store=authorities)
        result = api.run_campaign(RunCampaignRequest(package_path, confirmed=True, reveal_authority_id=reveal.authority_id))
        assert result.succeeded, (result.reason_codes, result.errors)
        assert executor.invocations == 6
        plan = service._load_status_execution_plan(package.run_plan_id)
        # Let the later old-route control construct its original five tasks.
        monkeypatch.setattr(workflow, 'prospective_fixture', original_compile)
        monkeypatch.setattr(workflow, '_registrations', original_registrations)
        yield SimpleNamespace(handoff=handoff, factories=factories, discovery=discovery, plane=plane, raw=raw,
            package=package, reveal=reveal, executor=executor, execution_plan=plan)


@pytest.fixture(scope='module')
def prior_fixture(sealed_parent_fixture):
    """Select actual ordinary sealed observe bytes from the six-task variant."""
    fixture = sealed_parent_fixture
    run = fixture.package.run_plan_id
    receipt = ExternalTaskReceiptStore(fixture.plane).read(run, 'observe', run+'.observe.attempt-001')
    assert receipt is not None
    logical, = receipt.output_logical_artifacts
    physical, = receipt.output_materializations
    assert logical.outcome_access is OutcomeAccess.EVALUATION_SEALED
    assert logical.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
    raw = fixture.plane.root.resolve(physical.relative_path, for_write=False).read_bytes()
    record = decode_canonical_bytes(raw, Config, maximum_bytes=10_000)
    assert record == Config('product.observe', 3)
    locator = RecursivePriorExecutionBinding('binding.synthetic-prior-observe',
        ObjectIdentity.from_record(fixture.package.issued_study.issue_id, fixture.package.issued_study),
        ObjectIdentity.from_record(fixture.package.execution_authority.authority_id, fixture.package.execution_authority),
        ObjectIdentity.from_record(fixture.package.package_id, fixture.package),
        ObjectIdentity.from_record(fixture.execution_plan.execution_plan_id, fixture.execution_plan), run,
        receipt.task_id, ObjectIdentity.from_record(receipt.receipt_id, receipt), logical.logical_artifact_id,
        ObjectIdentity.from_record(record.config_id, record), record_id_field='config_id')
    return fixture, locator, receipt, logical, physical, raw


def _replay(fixture, binding, *, scope=None, parent=None):
    return owner._authenticate_prior_execution(binding, fixture.plane, fixture.handoff.compilation.output_codecs,
        scope_validator=scope or (lambda **kwargs: None), parent_evidence=parent)


def _block_protected_streams(monkeypatch):
    from empirical_lawhood.runtime import artifacts
    def blocked(*args, **kwargs):
        pytest.fail('protected prior artifact stream before exact scope and complete retained custody')
    monkeypatch.setattr(artifacts, 'verify_artifact_manifests', blocked)
    monkeypatch.setattr(owner, '_output_payload', blocked)


def test_actual_complete_issued_prior_replays_without_any_reexecution(prior_fixture):
    fixture, locator, receipt, logical, physical, raw = prior_fixture
    sentinel, observed = object(), []
    def scope(**kwargs):
        assert kwargs['parent_evidence'] is sentinel
        assert kwargs['binding'] == locator and kwargs['package'] == fixture.package
        assert kwargs['execution_plan'] == fixture.execution_plan
        observed.append(locator.binding_id)
    prior = _replay(fixture, locator, scope=scope, parent=sentinel)
    assert prior.binding == locator and prior.package == fixture.package
    assert prior.execution_plan == fixture.execution_plan
    assert len(prior.receipts) == 6 and receipt in prior.receipts
    assert prior.product.logical == logical and prior.product.materialization == physical
    assert prior.product.payload == raw and prior.additional_products == ()
    assert observed == [locator.binding_id] and fixture.executor.invocations == 6
    assert decode_canonical_bytes(locator.canonical_bytes(), RecursivePriorExecutionBinding,
        maximum_bytes=64*1024) == locator


@pytest.mark.parametrize('field', ('package', 'execution_plan', 'receipt', 'issued_study', 'execution_authority'))
def test_substituted_actual_control_identities_refuse_before_protected_stream(prior_fixture, monkeypatch, field):
    fixture, locator, *_ = prior_fixture
    changed = replace(locator, **{field: replace(getattr(locator, field), object_fingerprint='0'*64)})
    _block_protected_streams(monkeypatch)
    with pytest.raises(PermissionError):
        _replay(fixture, changed)
    assert fixture.executor.invocations == 6


def test_missing_original_dependency_receipt_refuses_before_protected_stream(prior_fixture, monkeypatch):
    fixture, locator, *_ = prior_fixture
    actual = ExternalTaskReceiptStore.read_by_receipt_id
    def missing(self, run, task, receipt):
        return None if task == 'prepare' else actual(self, run, task, receipt)
    monkeypatch.setattr(ExternalTaskReceiptStore, 'read_by_receipt_id', missing)
    _block_protected_streams(monkeypatch)
    with pytest.raises(PermissionError, match='dependency'):
        _replay(fixture, locator)
    assert fixture.executor.invocations == 6


def test_unknown_contact_terminal_cannot_become_complete_receipt_custody(prior_fixture, monkeypatch):
    fixture, locator, *_ = prior_fixture
    actual = ExternalRunRecoveryStore.read_terminal
    def unknown(self, index):
        terminal = actual(self, index)
        assert terminal is not None
        attempts = tuple(replace(row, disposition=RecoveryTerminalDisposition.BLOCKED, reason_code='unknown-contact',
            receipt_id=None, receipt_sha256=None) if row.task_id == 'prepare' else row for row in terminal.attempts)
        return replace(terminal, operational_status='BLOCKED', attempts=attempts,
            completed_task_ids=tuple(t for t in terminal.completed_task_ids if t != 'prepare'), blocked_task_ids=('prepare',))
    monkeypatch.setattr(ExternalRunRecoveryStore, 'read_terminal', unknown)
    _block_protected_streams(monkeypatch)
    with pytest.raises(PermissionError, match='complete successful retained'):
        _replay(fixture, locator)
    assert fixture.executor.invocations == 6


def test_partial_original_receipt_pair_refuses_before_protected_stream(prior_fixture, monkeypatch, tmp_path):
    from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
    fixture, locator, *_ = prior_fixture
    run = fixture.package.run_plan_id
    sidecar = fixture.plane.root.resolve(f'runs/{run}/receipts/prepare/{run}.prepare.attempt-001.json.manifest.json',
        for_write=False)
    retained = tmp_path/'original-prepare-receipt.manifest.json'
    _block_protected_streams(monkeypatch)
    sidecar.rename(retained)
    try:
        with pytest.raises((PermissionError, ArtifactPlaneError), match='partial|dependency'):
            _replay(fixture, locator)
    finally:
        retained.rename(sidecar)
    assert fixture.executor.invocations == 6


@pytest.mark.parametrize('refusal', ('raises', 'false-return'))
def test_pure_scope_validator_refuses_before_complete_receipt_artifact_stream(prior_fixture, monkeypatch, refusal):
    fixture, locator, *_ = prior_fixture
    _block_protected_streams(monkeypatch)
    called = []
    def scope(**kwargs):
        assert kwargs['binding'] == locator and kwargs['execution_plan'] == fixture.execution_plan
        called.append(locator.binding_id)
        if refusal == 'raises':
            raise PermissionError('synthetic global scope refuses prior wave')
        return False
    with pytest.raises(PermissionError, match='scope refuses|return None'):
        _replay(fixture, locator, scope=scope)
    assert called == [locator.binding_id] and fixture.executor.invocations == 6


def test_missing_or_uninstalled_prior_codec_refuses_before_protected_stream(prior_fixture, monkeypatch):
    fixture, locator, *_ = prior_fixture
    _block_protected_streams(monkeypatch)
    with pytest.raises(PermissionError, match='installed sealed'):
        owner._authenticate_prior_execution(locator, fixture.plane, {}, scope_validator=lambda **kwargs: None,
            parent_evidence=None)
    assert fixture.executor.invocations == 6


@pytest.mark.parametrize('mutation', ('renamed-object', 'wrong-id-field'))
def test_actual_decoded_stable_record_id_must_match_locator(prior_fixture, mutation):
    fixture, locator, *_ = prior_fixture
    changed = (replace(locator, record=replace(locator.record, object_id='product.other-observation'))
        if mutation == 'renamed-object' else replace(locator, record_id_field='result_id'))
    with pytest.raises(PermissionError, match='canonical product bytes|stable.*identity|record'):
        _replay(fixture, changed)
    assert fixture.executor.invocations == 6


def test_old_qualified_parent_route_has_empty_prior_callback_and_remains_unchanged(parent_fixture, monkeypatch):
    _, registrations, _ = _parent_inputs(parent_fixture)
    assert all(r.qualified_parent_prior_execution_bindings is None
        and r.qualified_parent_prior_execution_scope_validator is None for r in registrations)
    monkeypatch.setattr(owner, '_authenticate_prior_execution',
        lambda *args, **kwargs: pytest.fail('default-empty old qualified-parent route invoked new prior replay'))
    parent, = _authenticate(parent_fixture)
    assert parent.prior_executions == () and parent.additional_products == ()
    assert parent_fixture.executor.invocations == 5
