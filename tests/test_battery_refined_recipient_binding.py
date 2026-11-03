# SPDX-License-Identifier: MPL-2.0
"""Exposed software fixtures only; native acquisition is replaced by fixture traces."""
from dataclasses import replace
from types import SimpleNamespace as N
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, science, native
from empirical_lawhood.adapters.methods.battery_refined_inquiry import recipient_bindings as owner
from empirical_lawhood.adapters.methods.battery_refined_inquiry.operation_bindings import source_policy_admission, record_identity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, WorkerInputKind, WorkerOutputPort
from tests.test_battery_refined_inquiry import selected as selected, table, exposed
from tests.test_battery_refined_inquiry_binding import stock as stock, Port


@pytest.fixture
def original(stock):
    traces = table((stock.source, stock.policy))
    supply = science.construct_supply(stock.source, stock.policy, science.qualify(stock.source, stock.policy, traces), traces)
    source_gate = source_policy_admission(stock.source, stock.policy, stock.selection, stock.diagnostic)
    return N(stock=stock, supplier=supply, traces=traces, source_gate=source_gate, prior=None, prior_traces=())


def config(original, operation):
    _, phase, _ = owner.parts(operation)
    instance = science.compatible_instance(original.supplier, phase, prior_use=original.prior)
    return owner.RecipientOperationConfig('config.' + owner.node_id(operation), operation,
        original.stock.source, original.stock.policy, original.stock.selection, c.identity(original.stock.diagnostic),
        record_identity(original.source_gate), original.supplier, instance, tuple(c.identity(t) for t in original.traces),
        original.prior, tuple(c.identity(t) for t in original.prior_traces))


def context(original, operation, previous):
    selected = config(original, operation)
    step, phase, count = owner.parts(operation)
    run_id = 'run.exposed-recipient'
    node = owner.node_id(operation)
    values = {name: getattr(selected, name) for name, _ in owner.SMALL_INPUTS}
    if step in ('validate', 'assess'):
        values['source-admission'] = original.source_gate
        values.update(zip(owner.ports('supplier-trace', count), original.traces, strict=True))
        if phase == 'reuse':
            values['prior-use'] = original.prior
            values.update(zip(owner.ports('prior-trace', len(original.prior_traces)), original.prior_traces, strict=True))
    inputs = [Port(selected.config_id, selected, WorkerInputKind.EXTERNAL)]
    inputs += [Port('external.exposed.' + name, values[name], WorkerInputKind.EXTERNAL) for name, _ in owner.external_inputs(operation)]
    receipts = {}
    for name, _, producer, output in owner.dependency_inputs(operation):
        producer_node = owner.node_id(producer)
        port = Port(f'artifact.{run_id}.{producer_node}.{output}', previous[producer][output], WorkerInputKind.DEPENDENCY)
        inputs.append(port)
        receipts.setdefault(producer_node, []).append(port.materialization_id)
    return N(task_id=node, run_id=run_id, input_ports=tuple(inputs), permissions=owner.RecipientRunner(operation).manifest.permissions,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, resource_budget=owner.BUDGET,
        dependency_receipts=tuple(DependencyReceiptBinding('receipt.exposed.' + node, node, tuple(ids)) for node, ids in sorted(receipts.items())),
        config=N(artifact_id=selected.config_id, config_id=selected.config_id, content_sha256=selected.fingerprint()),
        output_ports=tuple(WorkerOutputPort(node + '.' + name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, owner.MEDIA)
                           for name, record in owner.operation_outputs(operation)))


def execute(original, operation, previous):
    ctx = context(original, operation, previous)
    result = owner.RecipientRunner(operation).execute(ctx)
    assert all(p.closed for p in ctx.input_ports)
    outputs = {}
    for payload, (name, record) in zip(result.outputs, owner.operation_outputs(operation), strict=True):
        outputs[name] = decode_canonical_bytes(payload.payload, record, maximum_bytes=None)
    previous[operation] = outputs
    return outputs


def test_cold_registration_complete_ports_and_no_native_import():
    probe = """
import importlib.abc,sys
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0]=='pybamm': raise AssertionError('cold recipient imports native')
sys.meta_path.insert(0,RefuseNative())
from empirical_lawhood.adapters.methods.battery_refined_inquiry import recipient_bindings as b
assert len(b.operation_manifests())==len(b.operation_registrations())==20
assert all(b.RecipientRunner(op).manifest for op in b.OPERATIONS)
assert 'pybamm' not in sys.modules
"""
    subprocess.run([sys.executable, '-c', probe], check=True)
    for phase in ('use', 'reuse'):
        for count in (45, 54):
            choice = f'choose-{phase}-{count}'
            assert sum(record is c.Trace for _, record in owner.operation_inputs(choice)) == 9
            assert all(not name.startswith(('supplier-trace', 'prior-trace', 'trace-')) for name, _ in owner.operation_inputs(choice))
            complete = f'complete-{phase}-{count}'
            assert len(owner.operation_outputs(complete)) == (9 if count == 54 else 6)
            assert ('choice', c.ChoiceCommitment, choice, 'choice') in owner.dependency_inputs(complete)


def expanded_original(original, count):
    if count == 54:
        tighter = replace(next(v for v in original.stock.policy.views if v.view_id == 'dfn-refined'),
                          view_id='dfn-tolerance', rtol=next(v for v in original.stock.policy.views if v.view_id == 'dfn-refined').rtol / 10,
                          atol=next(v for v in original.stock.policy.views if v.view_id == 'dfn-refined').atol / 10)
        selection = replace(original.stock.selection, tolerance_probe=True, views=tuple(sorted((*original.stock.selection.views, tighter), key=lambda v: v.view_id)))
        policy = replace(original.stock.policy, views=selection.views, tolerance_probe=True, protocol_sha256=selection.fingerprint())
        source = replace(original.stock.source, policy=c.identity(policy), protocol_sha256=policy.protocol_sha256)
        selected_stock = N(source=source, policy=policy, selection=selection, diagnostic=original.stock.diagnostic)
        traces = table((source, policy))
        supplier = science.construct_supply(source, policy, science.qualify(source, policy, traces), traces)
        original = N(stock=selected_stock, supplier=supplier, traces=traces, source_gate=source_policy_admission(source, policy, selection, selected_stock.diagnostic), prior=None, prior_traces=())
    return original


@pytest.mark.parametrize('count', (45, 54))
def test_real_pure_reducers_relay_custody_choice_before_remaining_and_actual_reuse(original, monkeypatch, count):
    original = expanded_original(original, count)
    phase_count = 18 if count == 54 else 15
    calls = []
    monkeypatch.setattr(native, 'acquire', lambda cfg: calls.append(cfg) or exposed(cfg))
    previous = {}
    gate = execute(original, f'validate-use-{count}', previous)
    assert calls == []
    assert gate['supplier-product'].canonical_bytes() == original.supplier.canonical_bytes()
    assert gate['source-admission'] == original.source_gate
    assert tuple(gate[name].canonical_bytes() for name in owner.ports('supplier-trace', count)) == tuple(t.canonical_bytes() for t in original.traces)
    execute(original, f'forecast-use-{count}', previous)
    assert len(calls) == 9
    choice = execute(original, f'choose-use-{count}', previous)['choice']
    assert len(calls) == 9 and choice.selected_recipe is not None
    execute(original, f'complete-use-{count}', previous)
    assert len(calls) == phase_count and len({c.identity(row) for row in calls}) == phase_count
    use = execute(original, f'assess-use-{count}', previous)['assessed']
    assert use.assessment.persisted_choice == c.identity(choice)
    assert len(use.assessment.traces) == phase_count
    forecast = previous[f'forecast-use-{count}']
    remaining = previous[f'complete-use-{count}']
    use_traces = tuple(sorted((*forecast.values(), *remaining.values()), key=lambda row: row.trace_id))
    science.validate_assessment(original.supplier, use.assessment, use_traces)
    later = N(**{**vars(original), 'prior': use, 'prior_traces': use_traces})
    for step in owner.STEPS:
        result = execute(later, f'{step}-reuse-{count}', previous)
        if step == 'validate':
            assert result['prior-use'].canonical_bytes() == use.canonical_bytes()
            assert tuple(result[name].canonical_bytes() for name in owner.ports('prior-trace', phase_count)) == tuple(t.canonical_bytes() for t in use_traces)
    reuse = result['assessed']
    assert reuse.supplier == original.supplier and reuse.prior_use == use.assessment
    assert reuse.assessment.instance.prior_use == c.identity(use)
    assert len(calls) == 2 * phase_count


def test_missing_choice_receipt_blocks_native_and_extra_reference_blocks_choice(original, monkeypatch):
    previous = {}
    execute(original, 'validate-use-45', previous)
    monkeypatch.setattr(native, 'acquire', exposed)
    execute(original, 'forecast-use-45', previous)
    execute(original, 'choose-use-45', previous)
    calls = []
    monkeypatch.setattr(native, 'acquire', lambda cfg: calls.append(cfg) or exposed(cfg))
    ctx = context(original, 'complete-use-45', previous)
    ctx.dependency_receipts = tuple(r for r in ctx.dependency_receipts if '.choose-' not in r.task_id)
    with pytest.raises(ValueError, match='receipt-backed'):
        owner.RecipientRunner('complete-use-45').execute(ctx)
    assert calls == [] and all(p.closed for p in ctx.input_ports)
    ctx = context(original, 'choose-use-45', previous)
    ctx.input_ports += (Port('exposed.future-reference', exposed(owner.remaining_configs(config(original, 'choose-use-45'))[0]), WorkerInputKind.EXTERNAL),)
    with pytest.raises(ValueError, match='task/input'):
        owner.RecipientRunner('choose-use-45').execute(ctx)
    assert all(p.closed for p in ctx.input_ports)


def test_self_consistent_compact_cost_forgery_refused_against_actual_raw_supplier(original):
    q = original.supplier.qualification
    forged_q = replace(q, model_cpu_seconds=tuple((model, cpu + 100) for model, cpu in q.model_cpu_seconds))
    forged = replace(original.supplier, qualification=forged_q)
    changed = N(**{**vars(original), 'supplier': forged})
    ctx = context(changed, 'validate-use-45', {})
    with pytest.raises(ValueError, match='actual trace reduction'):
        owner.RecipientRunner('validate-use-45').execute(ctx)
    assert all(p.closed for p in ctx.input_ports)


def test_prior_cost_forgery_and_forecast_ordinal_substitution_refused(original, monkeypatch):
    monkeypatch.setattr(native, 'acquire', exposed)
    previous = {}
    for step in owner.STEPS:
        execute(original, f'{step}-use-45', previous)
    forecasts = previous['forecast-use-45']
    use = previous['assess-use-45']['assessed']
    raw = tuple(sorted((*forecasts.values(), *previous['complete-use-45'].values()), key=lambda row: row.trace_id))
    forged = replace(use, assessment=replace(use.assessment, cpu_seconds=use.assessment.cpu_seconds + 100))
    later = N(**{**vars(original), 'prior': forged, 'prior_traces': raw})
    ctx = context(later, 'validate-reuse-45', {})
    with pytest.raises(ValueError, match='independent full-roster'):
        owner.RecipientRunner('validate-reuse-45').execute(ctx)
    assert all(port.closed for port in ctx.input_ports)
    forecasts['forecast-000'], forecasts['forecast-001'] = forecasts['forecast-001'], forecasts['forecast-000']
    ctx = context(original, 'choose-use-45', previous)
    with pytest.raises(ValueError, match='forecast ordinals'):
        owner.RecipientRunner('choose-use-45').execute(ctx)
    assert all(port.closed for port in ctx.input_ports)


def exposed_parent(original):
    """Unsigned software fixture metadata; not actual supplier qualification."""
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, VisibilityCeiling
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
    rows = []
    for index, record in enumerate((original.supplier, original.source_gate, *original.traces)):
        identity = record_identity(record)
        rows.append(ContributionProduct(f'product.exposed-parent.{index:03d}', identity,
            ArtifactIdentity(f'artifact.exposed-parent.{index:03d}', 'scientific-product', record.SCHEMA,
                             record.fingerprint(), owner.MEDIA, len(record.canonical_bytes())),
            ObjectIdentity('receipt.exposed-parent', 'empirical-lawhood/runtime/task-receipt', '1.0.0', 'b' * 64),
            ContributionRole.DESIGN_OPERAND if type(record) is c.Supply else ContributionRole.RETAINED_ANALYSIS_INPUT,
            EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY))
    return ContributionManifest('contribution.exposed-recipient-parent', owner.QUESTION,
        'Unsigned exposed software metadata only; no actual numerical qualification claim.', c.scope(original.stock.source),
        tuple(sorted(rows, key=lambda row: row.product_id)), (c.identity(original.supplier),), (), ())


@pytest.mark.parametrize('count', (45, 54))
def test_actual_scheduler_canonical_receipts_and_callbacks_rejoin_complete_custody(original, tmp_path, monkeypatch, count):
    """PURE fixture emitters + actual gates/choices/reducers/custody, no native science."""
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import recursive_translation as drafts
    from empirical_lawhood.api.recursive_execution import _external_inputs
    from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, LocalScheduler
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.infrastructure.recursive_custody import read_recursive_products
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityRegistry
    from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
    from tests.test_recursive_public_service import _plane
    from tests.test_battery_refined_inquiry_binding import ExposedTraceEmitter

    monkeypatch.setattr(native, 'acquire', lambda *_: pytest.fail('exposed scheduler entered actual native science'))
    original = expanded_original(original, count)
    phase_count = 18 if count == 54 else 15
    draft = drafts.use_draft(original.supplier, original.source_gate, parent=exposed_parent(original),
                            draft_id='draft.exposed-recipient-custody')
    for phase in ('use', 'reuse'):
        registry = CapabilityRegistry('registry.exposed-recipient', tuple(sorted(owner.operation_manifests(), key=lambda row: row.registry_id)))
        compiled = compile_recursive_wave(draft=draft, registrations=owner.operation_registrations(), registry=registry,
            implementation_commit='1' * 40, output_codecs=owner.output_codecs())
        tasks = {task.task_id: task for task in compiled.execution_plan.tasks}
        choice_node, complete_node = owner.node_id(f'choose-{phase}-{count}'), owner.node_id(f'complete-{phase}-{count}')
        assert choice_node in tasks[complete_node].dependency_task_ids
        # Five old operands, admission and only nine foreground forecasts retain
        # their own census alongside the compiler's explicit configuration edge.
        assert len(tuple(row for row in tasks[choice_node].scientific_inputs if row.consumer_input_id != 'config')) == 15
        configuration, = (row for row in tasks[choice_node].scientific_inputs if row.consumer_input_id == 'config')
        assert configuration.payload_schema == owner.RecipientOperationConfig.SCHEMA
        fixtures, emitters, rewritten = [], [], []
        for task in compiled.execution_plan.tasks:
            operation = task.task_id.removeprefix(owner.NAMESPACE + '.')
            if owner.parts(operation)[0] in ('forecast', 'complete'):
                original_manifest = next(row for row in owner.operation_manifests() if row.capability_key == task.task_id)
                fixture = replace(original_manifest, capability_key='testing.exposed-recipient.' + operation, kind=CapabilityKind.ANALYSIS)
                fixtures.append(fixture)
                native_configs = owner.forecast_configs(config(original, operation)) if operation.startswith('forecast') else owner.remaining_configs(config(original, operation))
                emitters.append(ExposedTraceEmitter(fixture, tuple(exposed(row) for row in native_configs)))
                rewritten.append(replace(task, capability=replace(task.capability, capability_key=fixture.capability_key, kind=CapabilityKind.ANALYSIS),
                                         capability_implementation_sha256=fixture.implementation_sha256))
            else:
                rewritten.append(task)
        registry = CapabilityRegistry('registry.exposed-recipient-pure', tuple(sorted((*owner.operation_manifests(), *fixtures), key=lambda row: row.registry_id)))
        plan = replace(compiled.execution_plan, registry_sha256=registry.fingerprint(), tasks=tuple(rewritten))
        runners = RunnerRegistry(tuple(sorted((*(owner.RecipientRunner(op) for op in owner.OPERATIONS), *emitters), key=lambda row: row.manifest.registry_id)),
            registry_sha256=registry.fingerprint())
        gate_config = config(original, f'validate-{phase}-{count}')
        all_records = {name: getattr(gate_config, name) for name, _ in owner.SMALL_INPUTS}
        all_records['source-admission'] = original.source_gate
        all_records.update(zip(owner.ports('supplier-trace', count), original.traces, strict=True))
        if phase == 'reuse':
            all_records['prior-use'] = original.prior
            all_records.update(zip(owner.ports('prior-trace', phase_count), original.prior_traces, strict=True))
        payloads = {row.config_id: row.payload for row in compiled.config_inputs}
        payloads.update({name: row.canonical_bytes() for name, row in all_records.items()})
        plane = _plane(tmp_path / ('exposed-recipient-custody-' + phase))
        inputs = _external_inputs(plane=plane, plan=plan, draft=draft, payloads=payloads, read_only=False)
        run_id = compiled.run_plan.run_plan_id
        index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run_id, wave_id='wave.exposed-recipient', authority_identities=())
        engine = create_catalog_engine('sqlite+pysqlite:///:memory:')
        upgrade_catalog(engine)
        repository = SQLiteOperationalRepository(engine)
        scheduler = LocalScheduler(operational_repository=repository, artifact_writer=plane, receipt_store=ExternalTaskReceiptStore(plane),
            recovery_index=index, recovery_store=ExternalRunRecoveryStore(plane), runner_registry=runners, implementation_commit='1' * 40,
            external_input_resolver=StaticExternalInputResolver(inputs), executor=DirectTaskExecutor(), input_port_factory=plane,
            lane=PlanLane.DEVELOPMENT, authorized_barriers=(), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
        try:
            result = scheduler.execute(run_id, plan)
            assert result.status is OperationalStatus.SUCCEEDED
            assert len(result.receipts) == 5
            actual = read_recursive_products(plane=plane, plan=plan, index=index, external_inputs=inputs, output_codecs=owner.output_codecs())
            choice_receipt = actual['receipts'][choice_node]
            complete_receipt = actual['receipts'][complete_node]
            assert all(row.materialization_id in complete_receipt.input_materialization_ids for row in choice_receipt.output_materializations)
            manifests = drafts.describe_recipient_contributions(draft, actual)
            assert len(manifests) == 1
            exported = manifests[0]
            assert sum(row.record.object_schema == c.Trace.SCHEMA for row in exported.products) == count + phase_count * (2 if phase == 'reuse' else 1)
            meaning_payloads = {'external-' + sha256(row.input_id.encode()).hexdigest()[:24] + '.json':
                                all_records[row.input_id.rsplit('.', 1)[1]].canonical_bytes() for row in draft.external_inputs}
            assert drafts.recipient_evidence_projector(draft, meaning_payloads, actual)
            _, assessed, _ = drafts._recipient_actual_product(draft, actual)
            for requirement, connection in zip(draft.requirements, draft.connections, strict=True):
                phases = owner.project_recipient_assessments(assessed, requirement, connection)
                assert len(phases) == 4
                assert owner.project_recipient_assessments(original.supplier, requirement, connection) == ()
            successor = drafts.next_wave_builder(draft, exported, actual)
            if phase == 'reuse':
                assert successor is None
            else:
                assert successor is not None
                _, actual_assessed, retained = drafts._recipient_actual_product(draft, actual)
                foreground = retained[owner.node_id(f'forecast-{phase}-{count}')]
                references = retained[complete_node]
                current_raw = tuple(sorted((*foreground.values(), *references.values()), key=lambda row: row.trace_id))
                original = N(**{**vars(original), 'prior': actual_assessed, 'prior_traces': current_raw})
            for damage in ('missing-raw', 'missing-raw-receipt', 'missing-choice-binding'):
                changed = {**actual, 'records': {node: dict(rows) for node, rows in actual['records'].items()}, 'receipts': dict(actual['receipts'])}
                if damage == 'missing-raw':
                    del changed['records'][complete_node][complete_node + '.trace-000']
                elif damage == 'missing-raw-receipt':
                    del changed['receipts'][complete_node]
                else:
                    changed['receipts'][complete_node] = replace(complete_receipt, input_materialization_ids=tuple(
                        row for row in complete_receipt.input_materialization_ids if row != choice_receipt.output_materializations[0].materialization_id))
                with pytest.raises(ValueError):
                    drafts.describe_recipient_contributions(draft, changed)
                with pytest.raises(ValueError):
                    drafts.recipient_evidence_projector(draft, meaning_payloads, changed)
        finally:
            engine.dispose()
        if phase == 'use':
            draft = successor


def test_comparator_choices_use_only_their_own_foregrounds_and_reference_failure_stays_unknown(original):
    cfg = config(original, 'choose-use-45')
    foreground = tuple(exposed(row) for row in owner.forecast_configs(cfg))
    el = science.commit_choice(cfg.supplier, cfg.instance, owner.selected_forecasts(cfg, foreground))
    direct = owner.comparator_choice(cfg, foreground, 'direct-dfn')
    chen = owner.comparator_choice(cfg, foreground, 'chen')
    changed = tuple(replace(row, disposition='TECHNICAL_FAILURE', error_type='ExposedFailure', error_message='software fixture')
                    if row.config.component_view == 'dfn-primary' else row for row in foreground)
    assert science.commit_choice(cfg.supplier, cfg.instance, owner.selected_forecasts(cfg, changed)) == el
    assert owner.comparator_choice(cfg, changed, 'chen') == chen
    assert owner.comparator_choice(cfg, changed, 'direct-dfn').choice.selected_recipe is None
    remaining = tuple(exposed(row) for row in owner.remaining_configs(cfg))
    actual = tuple(sorted((*foreground, *remaining), key=lambda row: row.trace_id))
    evaluated = owner.assess_comparator(cfg, actual, direct)
    owner.validate_comparator_assessment(cfg, evaluated, actual)
    broken = tuple(replace(row, disposition='TECHNICAL_FAILURE', error_type='ExposedFailure', error_message='software fixture')
                   if row.config.component_view == 'dfn-refined' else row for row in actual)
    unresolved = owner.assess_comparator(cfg, broken, direct)
    from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
    assert unresolved.assessment.disposition is AssessmentDisposition.UNEVALUABLE
    with pytest.raises(ValueError, match='complete raw reduction'):
        owner.validate_comparator_assessment(cfg, evaluated, broken)
