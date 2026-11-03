# SPDX-License-Identifier: MPL-2.0
"""Actual tiny exposed worker/store seams; no scientific bank or credentials.

Protected role labels are hypothetical record controls. These tests intentionally
expose their few states/streams and confer no qualification, issue or fresh use.
The numerical model below is explicit static test metadata, never fitted data.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES, MatrixResponseErrorModel
from empirical_lawhood.adapters.methods.matrix_scheduled_history import commitment as c, forecast as f, operation_bindings as b, records as r, retained, science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.continuation import ScheduledFullHistory
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments, parameter_source
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, CandidateExecutionPlan, ExecutionTask, ExternalInputSpec, PlanLane, ScientificInputRole, ScientificInputSpec
from empirical_lawhood.runtime.capabilities import CapabilityRequirement
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance
from tests.test_matrix_factor_confirmation_eligibility import stock as stock
from tests.test_matrix_response_error_prediction import spec as old_spec
from tests.test_matrix_scheduled_history import scheduled as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex, ScheduledNativeSourceContext

TEST_BUDGET = ResourceBudget(1, 512*1024**2, 0, None, 64*1024**2, 64*1024**2)


def blocked(*args, **kwargs):
    raise AssertionError('cold/software metadata entered a producer, RNG, spectrum or fit')


@pytest.fixture
def bank(scheduled):
    plane, old = scheduled
    first = old[0]
    census_pub = publish(plane, first.allocation.exposure.census, 'software.bindings.original-census')
    audit = c.ScheduledExposureAudit('audit.software.bindings', first.allocation.exposure.census, (), (census_pub,))
    audit_pub = publish(plane, audit, 'software.bindings.original-audit')
    artifact = ArtifactIdentity(audit_pub.logical.logical_artifact_id, 'software-only-actual-audit', audit.SCHEMA,
        audit.fingerprint(), 'application/json', len(audit.canonical_bytes()))
    allocation = replace(first.allocation, exposure=replace(first.allocation.exposure, scheduled_audit=artifact))
    reservation = replace(first.reservation, allocation=allocation, publication=publish(plane, allocation, 'software.bindings.allocation'))
    policies = tuple(replace(p, origin_sector='Y') for p in first.specification.selection.prefix_policies)
    selection = replace(first.specification.selection, reservation=r.identity(reservation), prefix_policies=policies,
        coordinate_policies=tuple((co, r.identity(policies[0])) for co, _ in first.specification.selection.coordinate_policies))
    specification = replace(first.specification, selection=selection, publication=publish(plane, selection, 'software.bindings.selection'))
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification, provenances=first.index.provenances)
    sources = tuple(index.resolve(index.reference(source_id=s.source_id, root_id=s.root_id, provenance=s.reference.provenance)) for s in old)
    training = old_spec.__wrapped__()  # existing pure 256-row metadata fixture
    reservation_pub = publish(plane, reservation, 'software.bindings.reservation')
    training = replace(training, future_regime_reservation=r.identity(reservation),
        future_reservation_publication=c.corpus_artifact(reservation_pub))
    roots = tuple(sorted(row[0] for row in training.roles.rows if row[3] == 'TRAIN'))
    model = MatrixResponseErrorModel('model.software.bindings.static', training.identity,
        ObjectIdentity.from_record(training.roles.record_id, training.roles), training.future_regime_reservation,
        'ALL_ORIGIN', FEATURES, (D(0),)*len(FEATURES), (D(1),)*len(FEATURES), (True,)*len(FEATURES),
        ((D('.5'), *((D(0),)*len(FEATURES))),)*15, roots,
        tuple(ObjectIdentity('feature.static.'+root, 'empirical-lawhood/tests/static-feature', '1.0.0', 'a'*64) for root in roots),
        'b'*64, (len(roots),)*15, ((len(roots)//4,)*4,)*15, ())
    criterion = replace(training.population.policy.protocol, factor_rule=sources[0].policy.factor_rule.identity)
    # One complete calibration matched group, both of its coordinate cases.
    selected = tuple(s.root_id for s in sources if s.root.root.role.value == 'CALIBRATION')
    design = f.ScheduledForecastDesign('design.software.bindings', r.identity(allocation), model,
        publish(plane, model, 'software.bindings.model'), training, publish(plane, training, 'software.bindings.training'),
        criterion, publish(plane, criterion, 'software.bindings.criterion'),
        tuple((root, f.CALIBRATION_POINT) for root in selected), None, None, None, D('.1'),
        tuple(sorted({s.root.root.independent_group_id for s in sources if s.root.root.role.value == 'CALIBRATION'})))
    config = c.ScheduledCommitmentConfig('config.'+c.COMMIT_KEY, reservation, specification, index.provenances, tuple(s.reference for s in sources), selected, audit, audit_pub, design)
    return plane, sources, config


def write(plane, logical_id, payload, schema, *, access=Access.OUTCOME_BLIND, visibility=Visibility.PROSPECTIVE, phase='external'):
    result = plane.write(ArtifactWriteRequest(logical_id, 'software.bindings/'+phase+'/'+logical_id,
        schema, ArtifactProfile.MATRIX_ARRAY_NPZ if schema == science.MATRIX_ARRAY_SCHEMA else ArtifactProfile.CANONICAL_JSON,
        'application/x-npz' if schema == science.MATRIX_ARRAY_SCHEMA else 'application/json', 'software-only-bindings',
        'software.bindings/'+phase, payload, visibility, (), access))
    return retained._manifest(plane, result.materialization.relative_path)


def context(plane, config, role, inputs, dependencies=(), *, budget=TEST_BUDGET):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_bindings import RESPONSE_PHASES
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.calibration_bindings import CALIBRATION_PHASES
    m = next(m for m in b.operation_manifests() if m.capability_key == r.NAMESPACE+'.'+role)
    task = c.COMMIT_KEY if role == 'commit' else r.NAMESPACE+'.'+role if role in ('calibrate', 'calibration-qualify') else r.NAMESPACE+'.'+(config.root_id if hasattr(config, 'root_id') else config.source.root_id)+'.'+role
    config_manifest = write(plane, config.config_id, config.canonical_bytes(), config.SCHEMA, phase=role,
        access=b.phase_access(role), visibility=b.phase_visibility(role))
    inputs = (config_manifest, *inputs)
    deps = {p.materialization_id for receipt in dependencies for p in receipt.output_materializations}
    ports = tuple(sorted((plane.open(VerifiedArtifactInput(v.logical, v.materialization),
        binding=WorkerInputBinding.from_verified(VerifiedArtifactInput(v.logical, v.materialization),
            kind=WorkerInputKind.DEPENDENCY if v.materialization.materialization_id in deps else WorkerInputKind.EXTERNAL),
        maximum_bytes=v.materialization.size_bytes) for v in inputs), key=lambda p: p.artifact_id))
    phase = next(p for p in (*b.PHASES, *RESPONSE_PHASES, *( (*p, False) for p in CALIBRATION_PHASES)) if p[0] == role)
    outputs = [WorkerOutputPort(task+'.product', phase[2].SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'ordinary.'+task+'.product')]
    if phase[4]:
        outputs.append(WorkerOutputPort(task+'.arrays', science.MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', 'ordinary.'+task+'.arrays'))
    if role == 'project':
        outputs.append(WorkerOutputPort(task+'.feature', f.ScheduledForecastFeature.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'ordinary.'+task+'.feature'))
    if role == 'prefix':
        outputs.append(WorkerOutputPort(task+'.checkpoint', r.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'ordinary.'+task+'.checkpoint'))
    cfg = CapabilityConfigRef(config.config_id, config.SCHEMA, m.config_schema_sha256, config.fingerprint(), config.config_id)
    ctx = TaskContext('run.software.bindings', task, 'run.software.bindings.'+task+'.attempt-001', cfg, tuple(p.binding for p in ports), ports,
        tuple(sorted(outputs, key=lambda p: p.output_id)), m.permissions, b.phase_access(role), budget, WorkerIsolationProfile.TRUSTED_LOCAL,
        tuple(sorted((DependencyReceiptBinding(q.receipt_id, q.task_id, tuple(p.materialization_id for p in q.output_materializations
            if p.materialization_id in {i.materialization.materialization_id for i in inputs}))
            for q in dependencies if any(p.materialization_id in {i.materialization.materialization_id for i in inputs}
                for p in q.output_materializations)), key=lambda q: q.receipt_id)))
    return ctx, inputs


def finish(plane, ctx, result, source):
    ports = {p.output_id: p for p in ctx.output_ports}
    manifests = tuple(write(plane, ports[o.output_id].logical_artifact_id, o.payload, ports[o.output_id].payload_schema,
        access=ctx.outcome_access, visibility=b.phase_visibility(ctx.task_id.rsplit('.', 1)[-1]), phase='outputs') for o in result.outputs)
    receipt = CanonicalTaskReceipt('receipt.'+ctx.attempt_id, ctx.run_id, ctx.task_id, ctx.attempt_id,
        source.provenance.observed_git_head, ctx.input_materialization_ids,
        tuple(sorted((m.materialization for m in manifests), key=lambda p: p.materialization_id)),
        tuple(sorted((m.logical for m in manifests), key=lambda p: p.logical_artifact_id)), result.checks, OperationalStatus.SUCCEEDED, ())
    ExternalTaskReceiptStore(plane).commit(receipt, visibility_ceiling=b.phase_visibility(ctx.task_id.rsplit('.', 1)[-1]), outcome_access=ctx.outcome_access)
    return receipt, manifests


def commitment_inputs(config):
    design = config.forecast_design
    rows = ((config.reservation.allocation, config.reservation.publication), (config.specification.selection, config.specification.publication),
        (config.audit, config.audit_publication), (config.audit.census, config.audit.prior_corpus[0]),
        (design.model_record, design.model_publication), (design.training_record, design.training_publication),
        (design.criterion_record, design.criterion_publication))
    return rows+(() if config.response_selection is None else ((config.response_selection, config.response_selection_publication),))


def run_commit(bank):
    plane, sources, config = bank
    inputs = tuple(retained._manifest(plane, pub.materialization.relative_path) for _, pub in commitment_inputs(config))
    inputs += (write(plane, config.forecast_design.design_id, config.forecast_design.canonical_bytes(), config.forecast_design.SCHEMA),)
    inputs += tuple(write(plane, s.source_id, s.reference.canonical_bytes(), s.reference.SCHEMA) for s in sources)
    ctx, manifests = context(plane, config, 'commit', inputs)
    m = next(m for m in b.operation_manifests() if m.capability_key == c.COMMIT_KEY)
    result = c.ScheduledCommitter(m, b.BUDGET).execute(ctx)
    receipt, outputs = finish(plane, ctx, result, sources[0])
    return receipt, outputs, manifests



def shared_manifest(plane, shared):
    return write(plane, shared.config_id, shared.canonical_bytes(), shared.SCHEMA)


def native_context(source, shared, role='prefix'):
    config = r.ScheduledConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.'+role,
        role, source.reference, r.identity(shared))
    return ScheduledNativeSourceContext(source, config, shared)

def run_prefix(bank, source, commit_receipt, commit_outputs, *, plan=None):
    plane, _, shared = bank
    records = (source.reference, source.coordinate, source.provenance, *source.root.streams)
    names = (source.source_id, source.coordinate.coordinate_id, source.provenance.identity.object_id,
        *(source.root.stream_identity(s).object_id for s in source.root.streams))
    inputs = tuple(write(plane, name, value.canonical_bytes(), value.SCHEMA) for name, value in zip(names, records, strict=True))
    inputs += tuple(retained._manifest(plane, pub.materialization.relative_path) for pub in (source.reservation.publication, source.specification.publication))
    config = r.ScheduledConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.prefix', 'prefix', source.reference, r.identity(shared))
    inputs += (shared_manifest(plane, shared),)
    ctx, inputs = context(plane, config, 'prefix', (*inputs, *commit_outputs), (commit_receipt,))
    from tests.matrix_native_invocation_support import prepared_native_store
    plan = plan or actual_plan(bank, source, publish_plan=False)
    pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
    runner = b.ScheduledNativeRunner('prefix')
    native,ctx,_ = prepared_native_store(plane,runner=runner,context=ctx,manifests=inputs,
        provenance=source.provenance,execution_plan=pin,native_work_preparer=b.prepare_native_work,
        task_record=next(t for t in plan.tasks if t.task_id == ctx.task_id),
        visibility=Visibility.PROSPECTIVE,access=Access.OUTCOME_BLIND)
    result = runner.execute_with_native_subwork(ctx, native)
    receipt, outputs = finish(plane, ctx, result, source)
    product = decode_canonical_bytes(next(o.payload for o in result.outputs if o.output_id.endswith('.product')), r.ScheduledPrefixHistory, maximum_bytes=None)
    return product, receipt, outputs, inputs, native


def actual_plan(bank, source, *, publish_plan=True, additional_tasks=()):
    """Original typed software plan, not issue or real source qualification."""
    plane, sources, commit = bank
    roles = ('commit', 'prefix', 'numerical', 'measure', 'check', 'project', 'forecast', 'continue', 'full-numerical')
    tasks = []
    for role in roles:
        phase = next(p for p in b.PHASES if p[0] == role)
        task = c.COMMIT_KEY if role == 'commit' else r.NAMESPACE+'.'+source.root_id+'.'+role
        config = commit if role == 'commit' else f.ScheduledForecastConfig('config.'+task, f.ScheduledPublicSource.from_source(source), commit.forecast_design) if role == 'forecast' else r.ScheduledConfig('config.'+task, role, source.reference, r.identity(commit))
        m = next(m for m in b.operation_manifests() if m.capability_key == r.NAMESPACE+'.'+role)
        external = [('config', config.config_id, config, b.phase_access(role), b.phase_visibility(role))]
        if role == 'commit':
            design = commit.forecast_design
            rows = (('allocation', source.allocation, source.reservation.publication),
                ('selection', source.specification.selection, source.specification.publication),
                ('audit', commit.audit, commit.audit_publication),
                ('model', design.model_record, design.model_publication),
                ('training', design.training_record, design.training_publication),
                ('criterion', design.criterion_record, design.criterion_publication))
            if commit.response_selection is not None:
                rows += (('response-selection', commit.response_selection, commit.response_selection_publication),)
            for record in (commit.audit.census, *commit.audit.prior_scheduled_coordinates):
                pub, = (pub for pub in commit.audit.prior_corpus if
                    (pub.logical.payload_schema, pub.logical.content_sha256) == (record.SCHEMA, record.fingerprint()))
                port = 'prior-census' if record is commit.audit.census else 'prior-coordinates.'+record.coordinate_id
                rows += ((port, record, pub),)
            external += [(port, pub.logical.logical_artifact_id, record, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
                for port, record, pub in rows]
            external += [('source.'+s.root_id, s.source_id, s.reference, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE) for s in sources]
            external += [('forecast-design', design.design_id, design, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)]
        elif role != 'forecast':
            external.append(('source', source.source_id, source.reference, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE))
            external.append(('commitment-config', commit.config_id, commit, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE))
        if role in ('prefix', 'continue'):
            external += [(port, pub.logical.logical_artifact_id, record, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE) for port, record, pub in
                (('allocation', source.allocation, source.reservation.publication), ('selection', source.specification.selection, source.specification.publication))]
            external += [('coordinate', source.coordinate.coordinate_id, source.coordinate, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE),
                ('provenance', source.provenance.identity.object_id, source.provenance, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)]
            external += [('streams.'+s.purpose, source.root.stream_identity(s).object_id, s, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE) for s in source.root.streams]
        if role == 'project':
            external.append(('forecast-design', commit.forecast_design.design_id, commit.forecast_design, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE))
        specs = tuple(sorted((ExternalInputSpec(port, name, v.fingerprint(), v.SCHEMA, 'application/json', len(v.canonical_bytes()), vis, access, None)
            for port, name, v, access, vis in external), key=lambda e: e.input_id))
        outputs = [ArtifactOutputSpec(task+'.product', 'ordinary.'+task+'.product', 'software.bindings/outputs/ordinary.'+task+'.product',
            phase[2].SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', b.phase_visibility(role), (), b.phase_access(role))]
        if phase[4]:
            outputs.append(ArtifactOutputSpec(task+'.arrays', 'ordinary.'+task+'.arrays', 'software.bindings/outputs/ordinary.'+task+'.arrays',
                science.MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', b.phase_visibility(role), (), b.phase_access(role)))
        if role == 'project':
            outputs.append(ArtifactOutputSpec(task+'.feature', 'ordinary.'+task+'.feature', 'software.bindings/outputs/ordinary.'+task+'.feature',
                f.ScheduledForecastFeature.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
        if role == 'prefix':
            outputs.append(ArtifactOutputSpec(task+'.checkpoint', 'ordinary.'+task+'.checkpoint', 'software.bindings/outputs/ordinary.'+task+'.checkpoint',
                r.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
        deps = []
        for port, cls in phase[1]:
            if role == 'commit' or port in ('allocation', 'selection', 'coordinate', 'provenance', 'source', 'commitment-config', 'streams', 'forecast-design'):
                continue
            if port == 'physical-forecast' and commit.response_selection is None:
                continue
            owner = 'prefix' if port.startswith('history') or port == 'checkpoint' else 'project' if port.startswith('causal') or port == 'feature' else 'commit' if port == 'commitment' else port.removesuffix('-arrays')
            producer = c.COMMIT_KEY if owner == 'commit' else r.NAMESPACE+'.'+source.root_id+'.'+owner
            output = 'arrays' if port.endswith('-arrays') else 'feature' if port == 'feature' else 'checkpoint' if port == 'checkpoint' else 'product'
            logical = 'ordinary.'+producer+'.'+output
            deps.append(ScientificInputSpec('edge.'+task+'.'+port, port, ScientificInputRole.HISTORY, producer, producer+'.'+output,
                None, logical, logical, cls.SCHEMA if cls else science.MATRIX_ARRAY_SCHEMA,
                'application/json' if cls else 'application/x-npz', None, b.phase_access(owner), b.phase_visibility(owner),
                BarrierKind.FREEZE if owner in ('commit', 'forecast', 'physical-forecast') else BarrierKind.NONE))
        req = CapabilityRequirement(m.capability_key, m.capability_version, m.kind,
            CapabilityConfigRef(config.config_id, config.SCHEMA, m.config_schema_sha256, config.fingerprint(), config.config_id),
            m.input_schema_ids, m.output_schema_ids, m.permissions, m.maximum_evidence_ceiling, b.phase_access(role), TEST_BUDGET)
        tasks.append(ExecutionTask(task, phase[3], req, m.implementation_sha256, tuple(sorted({d.producer_task_id for d in deps})),
            specs, tuple(sorted(outputs, key=lambda o: o.output_id)), (), BarrierKind.FREEZE if role in ('commit', 'forecast') else BarrierKind.NONE,
            1, ('obligation.software.'+role,), scientific_inputs=tuple(sorted(deps, key=lambda d: d.edge_id))))
    plan = CandidateExecutionPlan('plan.software.bindings.original', PlanLane.PROSPECTIVE,
        ObjectIdentity('run.software.bindings', 'empirical-lawhood/runtime/candidate-run-plan', '1.0.0', '1'*64), '2'*64,
        source.provenance.observed_git_head, tuple(sorted((*tasks, *additional_tasks), key=lambda t: t.task_id)), True,
        candidate=ObjectIdentity('candidate.software.bindings', 'empirical-lawhood/planning/draft-study-candidate', '1.0.0', '3'*64))
    if publish_plan:
        plane.write(ArtifactWriteRequest(plan.execution_plan_id, 'runs/run.software.bindings/plans/execution-plan.json', plan.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', 'software-original-plan', 'runs/run.software.bindings/plans',
            plan.canonical_bytes(), Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    return plan


def test_static_default_descriptors_are_cold_and_worker_forecast_config_has_no_current_noise(bank, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.executable_binding import EXECUTABLE_BINDING_FACTORIES
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.extension_bundle import EXTENSION_BUNDLE_CONTRIBUTION
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(segments, 'acquire_parameter_segment', blocked)
    assert len(EXECUTABLE_BINDING_FACTORIES) == len(EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests) == 38
    assert sum(factory.manifest.capability_key.startswith(r.NAMESPACE+'.')
        for factory in EXECUTABLE_BINDING_FACTORIES) == 19
    assert sum(factory.manifest.capability_key.startswith('matrix-scheduled-history-compact.')
        for factory in EXECUTABLE_BINDING_FACTORIES) == 19
    _, sources, config = bank
    source = next(s for s in sources if s.root_id == config.selected_root_ids[0])
    public = f.ScheduledPublicSource.from_source(source)
    value = f.ScheduledForecastConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.forecast', public, config.forecast_design)
    assert decode_canonical_bytes(value.canonical_bytes(), f.ScheduledForecastConfig, maximum_bytes=None) == value
    raw = value.canonical_bytes()
    assert all(str(s.effective_seed).encode() not in raw and s.digest_sha256.encode() not in raw for s in source.root.streams)
    registration = next(v for v in b.operation_registrations() if v.selection.capability_key.endswith('.forecast'))
    assert {p.port_id for p in registration.input_ports} == {'causal', 'causal-arrays', 'feature'}
    assert registration.barrier.value == 'FREEZE' and registration.native_effect is False


def test_actual_pure_commitment_and_native_prefix_keep_original_and_ordinary_ids_separate(bank):
    plane, sources, config = bank
    c.authenticate_prior_publications(plane, (SimpleNamespace(record=config),))
    commit_receipt, commit_outputs, _ = run_commit(bank)
    source = next(s for s in sources if s.root_id == config.selected_root_ids[0])
    history, receipt, outputs, inputs, native = run_prefix(bank, source, commit_receipt, commit_outputs)
    with pytest.raises(ValueError, match='context'):
        history.validate_source(source)
    history.validate_source(source, native_context=native_context(source, config))
    assert history.arrays.array_artifact.artifact_id != history.checkpoint.prefix_arrays.artifact_id
    ordinary = next(m for m in outputs if m.logical.payload_schema == science.MATRIX_ARRAY_SCHEMA)
    assert ordinary.logical.logical_artifact_id == history.arrays.array_artifact.artifact_id
    assert receipt.input_materialization_ids == tuple(sorted(m.materialization.materialization_id for m in inputs))
    actual = native.recover(history.native.definition)
    assert actual.receipt == history.native.receipt and actual.completion == history.native.completion
    raw = b''.join(native.iter_completed_output(history.native.definition, 'arrays'))
    arrays = science.consume_prefix(source, history.arrays, raw)
    assert science.assess_prefix(source, history, arrays, native_context=native_context(source, config)).numerical_pass
    checkpoint_raw = b''.join(native.iter_completed_output(history.native.definition, 'checkpoint'))
    assert checkpoint_raw == history.checkpoint.canonical_bytes()


def pipeline(bank, *, root_id=None, plan=None, before_continue=None):
    plane, sources, commit = bank
    source = next(s for s in sources if s.root_id == (root_id or commit.selected_root_ids[0]))
    plan = plan or actual_plan(bank, source)
    receipts, outputs, inputs, products = {}, {}, {}, {}
    receipts['commit'], outputs['commit'], inputs['commit'] = run_commit(bank)
    history, receipts['prefix'], outputs['prefix'], inputs['prefix'], _ = run_prefix(bank, source,
        receipts['commit'], outputs['commit'], plan=plan)
    products['prefix'] = history
    source_manifest = write(plane, source.source_id, source.reference.canonical_bytes(), source.reference.SCHEMA)
    shared = shared_manifest(plane, commit)
    design_manifest = write(plane, commit.forecast_design.design_id, commit.forecast_design.canonical_bytes(), commit.forecast_design.SCHEMA)
    for role in ('numerical', 'measure', 'check', 'project', 'forecast', 'continue', 'full-numerical'):
        if role == 'continue' and before_continue is not None:
            before_continue(source, receipts, outputs, inputs, products)
        config = f.ScheduledForecastConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.forecast', f.ScheduledPublicSource.from_source(source), commit.forecast_design) if role == 'forecast' else r.ScheduledConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.'+role, role, source.reference, r.identity(commit))
        selected, dependencies = [], []
        if role != 'forecast':
            selected.extend((source_manifest, shared))
        if role == 'project':
            selected.append(design_manifest)
        if role == 'continue':
            for record, pub in ((source.allocation, source.reservation.publication), (source.specification.selection, source.specification.publication)):
                selected.append(retained._manifest(plane, pub.materialization.relative_path))
            for record, name in ((source.coordinate, source.coordinate.coordinate_id), (source.provenance, source.provenance.identity.object_id),
                    *((s, source.root.stream_identity(s).object_id) for s in source.root.streams)):
                selected.append(write(plane, name, record.canonical_bytes(), record.SCHEMA))
        phase = next(p for p in b.PHASES if p[0] == role)
        for port, _ in phase[1]:
            if port in ('source', 'commitment-config', 'forecast-design', 'allocation', 'selection', 'coordinate', 'provenance', 'streams'):
                continue
            if port == 'physical-forecast' and commit.response_selection is None:
                continue
            owner = 'prefix' if port.startswith('history') or port == 'checkpoint' else 'project' if port.startswith('causal') or port == 'feature' else 'commit' if port == 'commitment' else port.removesuffix('-arrays')
            ending = 'arrays' if port.endswith('-arrays') else 'feature' if port == 'feature' else 'checkpoint' if port == 'checkpoint' else 'product'
            manifest = next(m for m in outputs[owner] if m.logical.logical_artifact_id.endswith('.'+ending))
            selected.append(manifest)
            dependencies.append(receipts[owner])
        ctx, inputs[role] = context(plane, config, role, tuple(selected), tuple(dict.fromkeys(dependencies)))
        if role == 'continue':
            pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
            task = next(t for t in plan.tasks if t.task_id == ctx.task_id)
            from tests.matrix_native_invocation_support import prepared_native_store
            runner = b.ScheduledNativeRunner(role)
            native,ctx,_ = prepared_native_store(plane,runner=runner,context=ctx,manifests=inputs[role],
                provenance=source.provenance,execution_plan=pin,native_work_preparer=b.prepare_native_work,
                task_record=task,visibility=Visibility.PROSPECTIVE,access=Access.EVALUATION_SEALED)
            result = runner.execute_with_native_subwork(ctx, native)
        else:
            result = b.ScheduledRunner(role).execute(ctx)
        receipts[role], outputs[role] = finish(plane, ctx, result, source)
        products[role] = decode_canonical_bytes(next(o.payload for o in result.outputs if o.output_id.endswith('.product')), phase[2], maximum_bytes=None)
    return plane, source, commit, plan, receipts, outputs, inputs, products


def test_actual_point_seal_then_continuation_and_original_cold_store_read(bank, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.retained_bindings import read_history
    snapshots = []
    received = []
    forecast_ports = set()
    original_read = WorkerInputPort.read
    def record_delivered(port, *args, **kwargs):
        raw = original_read(port, *args, **kwargs)
        if id(port) in forecast_ports:
            received.append((port.payload_schema, raw))
        return raw
    monkeypatch.setattr(WorkerInputPort, 'read', record_delivered)
    original_execute = b.ScheduledRunner.execute
    def inspect_forecast_worker(runner, ctx):
        if runner.role == 'forecast':
            # Inspect the actual worker-facing bytes/bindings, including config
            # and dependency metadata, before the real predictor consumes them.
            snapshots.append((ctx.input_bindings, ctx.dependency_receipts))
            forecast_ports.update(id(p) for p in ctx.input_ports)
        try:
            return original_execute(runner, ctx)
        finally:
            if runner.role == 'forecast':
                forecast_ports.clear()
    monkeypatch.setattr(b.ScheduledRunner, 'execute', inspect_forecast_worker)
    plane, source, commit, plan, receipts, outputs, inputs, products = pipeline(bank)
    assert len(snapshots) == 1
    bindings, dependencies = snapshots[0]
    payloads = tuple(received)
    assert len(bindings) == 4
    assert {schema for schema, _ in payloads} == {f.ScheduledForecastConfig.SCHEMA, r.ScheduledCausalPrefix.SCHEMA,
        f.ScheduledForecastFeature.SCHEMA, science.MATRIX_ARRAY_SCHEMA}
    assert {q.task_id for q in dependencies} == {r.NAMESPACE+'.'+source.root_id+'.project'}
    assert all(p.outcome_access is Access.OUTCOME_BLIND and p.visibility_ceiling is Visibility.PROSPECTIVE for p in bindings)
    for schema, received in payloads:
        if schema != science.MATRIX_ARRAY_SCHEMA:
            assert all(str(s.effective_seed).encode() not in received and s.digest_sha256.encode() not in received for s in source.root.streams)
            assert b'completed_noise_matrices' not in received and b'generators' not in received
    delivered = science.decode_matrix_arrays(next(raw for schema, raw in payloads if schema == science.MATRIX_ARRAY_SCHEMA), products['project'].arrays)
    assert all(not name.endswith('innovations') for name in delivered)
    assert delivered['primary_ticks'][-1] == source.policy.cutoff_tick
    assert delivered['fine_ticks'][-1] == 2*source.policy.cutoff_tick
    seal = products['forecast']
    assert seal.scope == f.CALIBRATION_POINT and seal.radius is None and seal.calibration is None
    assert all(value is None for value in seal.log_error_uppers)
    full = products['continue']
    assert type(full) is ScheduledFullHistory and products['full-numerical'].numerical_pass
    # The source has a distinct fine cutoff state. Its complete continuation is
    # exactly the same received source trajectory, not a PRIMARY-start replay.
    expected = parameter_source.acquire_parameter_history(source.coordinate, source.root.streams)
    raw = plane.root.resolve(next(m.materialization.relative_path for m in outputs['continue'] if m.logical.payload_schema == science.MATRIX_ARRAY_SCHEMA), for_write=False).read_bytes()
    actual = science.unpack_native(source, raw)
    assert all(np.array_equal(actual[n], expected[n]) for n in actual)
    assert not np.array_equal(actual['primary_positions'][source.policy.cutoff_tick], actual['fine_positions'][2*source.policy.cutoff_tick])
    monkeypatch.setattr(segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', blocked)
    monkeypatch.setattr(science, 'measure_prefix', blocked)
    monkeypatch.setattr(ExternalNativeEffectContactStore, 'begin', blocked)
    for name in ('begin', 'contact', 'freeze_roster', 'complete', 'publish_output', 'recover'):
        monkeypatch.setattr(ExternalNativeSubworkStore, name, blocked)
    monkeypatch.setattr(ExternalTaskReceiptStore, 'commit', blocked)
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    monkeypatch.setattr(np.linalg, 'eigvalsh', blocked)
    roles = tuple(receipts)
    root = Path(plane.root.contract.canonical_path)
    before = {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob('*') if p.is_file()}
    result = read_history(plane=plane, run_id='run.software.bindings', execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        commitment=commit, root_id=source.root_id, original_inputs=tuple((r, inputs[r]) for r in roles),
        receipt_locators=tuple((r, receipts[r].attempt_id) for r in roles))
    assert all(result[r] == products[r] for r in products)
    assert result['commit'] == c.committed(commit)
    assert before == {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('defect', ('native-id', 'native-hash', 'checkpoint-state', 'foreign-run', 'ordinary-id'))
def test_prefix_original_native_or_ordinary_operand_substitution_refuses(bank, defect):
    _, sources, config = bank
    q, outputs, _ = run_commit(bank)
    source = next(s for s in sources if s.root_id == config.selected_root_ids[0])
    history, _, _, _, _ = run_prefix(bank, source, q, outputs)
    with pytest.raises(ValueError):
        if defect == 'native-id':
            value = replace(history, checkpoint=replace(history.checkpoint, prefix_arrays=replace(history.checkpoint.prefix_arrays, artifact_id='foreign.native-array')))
        elif defect == 'native-hash':
            value = replace(history, checkpoint=replace(history.checkpoint, prefix_arrays=replace(history.checkpoint.prefix_arrays, sha256='f'*64)))
        elif defect == 'checkpoint-state':
            states = (replace(history.checkpoint.generators[0], state=history.checkpoint.generators[0].state+1), *history.checkpoint.generators[1:])
            value = replace(history, checkpoint=replace(history.checkpoint, generators=states))
        elif defect == 'foreign-run':
            evidence = replace(history.native, receipt=replace(history.native.receipt, run_id='foreign.run'))
            value = replace(history, native=evidence)
        else:
            artifact = replace(history.arrays.array_artifact, sha256='f'*64)
            value = replace(history, arrays=replace(history.arrays, array_artifact=artifact))
        value.validate_source(source, native_context=native_context(source, config))


@pytest.mark.parametrize('defect', ('missing-commitment', 'wrong-task', 'cpu2', 'gpu1', 'missing-shared', 'foreign-shared'))
def test_native_decode_refuses_before_any_effect(bank, monkeypatch, defect):
    monkeypatch.setattr(segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(np.random, 'Generator', blocked)
    _, sources, config = bank
    receipt, outputs, _ = run_commit(bank)
    source = next(s for s in sources if s.root_id == config.selected_root_ids[0])
    if defect == 'missing-commitment':
        outputs = ()
    if defect == 'wrong-task':
        receipt = replace(receipt, task_id='foreign.commit')
    # Create only exact typed worker inputs; no Native parent/contact is opened.
    plane = bank[0]
    rows = (source.reference, source.coordinate, source.provenance, *source.root.streams)
    names = (source.source_id, source.coordinate.coordinate_id, source.provenance.identity.object_id,
        *(source.root.stream_identity(s).object_id for s in source.root.streams))
    inputs = tuple(write(plane, n, v.canonical_bytes(), v.SCHEMA) for n, v in zip(names, rows, strict=True))
    inputs += tuple(retained._manifest(plane, p.materialization.relative_path) for p in (source.reservation.publication, source.specification.publication))
    cfg = r.ScheduledConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.prefix', 'prefix', source.reference, r.identity(config))
    inputs += (shared_manifest(plane, config),)
    if defect == 'missing-shared':
        inputs = tuple(value for value in inputs if value.logical.payload_schema != c.ScheduledCommitmentConfig.SCHEMA)
    elif defect == 'foreign-shared':
        foreign = replace(config, forecast_design=replace(config.forecast_design, design_id='design.software.foreign-shared'))
        inputs = tuple(value for value in inputs if value.logical.payload_schema != c.ScheduledCommitmentConfig.SCHEMA)
        inputs += (write(plane, foreign.config_id, foreign.canonical_bytes(), foreign.SCHEMA, phase='foreign-shared'),)
    budget = replace(TEST_BUDGET, cpu_cores=2) if defect == 'cpu2' else replace(TEST_BUDGET, gpu_devices=1) if defect == 'gpu1' else TEST_BUDGET
    ctx, _ = context(plane, cfg, 'prefix', (*inputs, *outputs), (receipt,), budget=budget)
    try:
        with pytest.raises(ValueError):
            b._decode(ctx, 'prefix')
    finally:
        for p in ctx.input_ports:
            p.close()


def test_freeze_from_valid_foreign_shared_design_refuses_before_native_effects(bank, monkeypatch):
    _, sources, shared = bank
    source = next(value for value in sources if value.root_id == shared.selected_root_ids[0])
    foreign = replace(shared, forecast_design=replace(shared.forecast_design,
        design_id='design.software.valid-foreign-freeze'))
    received = c.committed(foreign)
    # Both inputs are valid current records with the same complete source,
    # allocation and audit. Source membership alone cannot bind the freeze.
    assert received.sources == c.committed(shared).sources
    assert received.audit == c.committed(shared).audit
    received.validate_source(source)
    monkeypatch.setattr(segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(np.random, 'Generator', blocked)
    b.require_current_commitment(c.committed(shared), shared)
    with pytest.raises(ValueError, match='actual complete shared'):
        b.require_current_commitment(received, shared)
