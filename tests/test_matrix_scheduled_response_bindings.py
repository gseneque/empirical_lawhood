# SPDX-License-Identifier: MPL-2.0
"""Tiny exposed stock pulse/score/calibration seams, no actual bank credentials."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, MatrixFactorResponseModel
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_bindings as rb, response_records as rr, response_science as rs, response_selection as sel
from empirical_lawhood.adapters.methods.matrix_scheduled_history import commitment as c, forecast as f, records as r, retained, science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import operation_bindings as b
from empirical_lawhood.adapters.methods.matrix_scheduled_history.calibration_bindings import CALIBRATION_PHASES, ScheduledCalibrationConfig, ScheduledCalibrator
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays, decode_matrix_arrays
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_record, decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactWriteRequest, ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.plans import ArtifactOutputSpec, BarrierKind, ExecutionTask, ExternalInputSpec, ScientificInputRole, ScientificInputSpec
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_scheduled_history_bindings import bank as bank, scheduled as scheduled, provenance as provenance, stock as stock
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from tests.test_matrix_scheduled_history_bindings import TEST_BUDGET, actual_plan, context, finish, pipeline, write, shared_manifest


def blocked(*args, **kwargs):
    raise AssertionError('cold response entered Native/producer/RNG/eigen/fit')


@pytest.fixture
def response_bank(bank):
    plane, old, commit = bank
    first = old[0]
    coordinates = tuple(replace(coordinate, ramp_ticks=96, autonomous_ticks=40, observation_ticks=tuple(range(137))) for coordinate in first.allocation.coordinates)
    by_id = {co.coordinate_id: co for co in coordinates}
    roots = tuple(replace(row, coordinate=ObjectIdentity.from_record(row.root.coordinate_id, by_id[row.root.coordinate_id])) for row in first.allocation.roots)
    scopes = tuple(replace(scope, coordinates=tuple(ObjectIdentity.from_record(co.object_id, by_id[co.object_id]) for co in scope.coordinates)) for scope in first.allocation.matched_scopes)
    allocation = replace(first.allocation, coordinates=coordinates, roots=roots, matched_scopes=scopes)
    reservation = replace(first.reservation, allocation=allocation, publication=publish(plane, allocation, 'software.response.allocation'))
    selection = replace(first.specification.selection, reservation=r.identity(reservation),
        coordinate_policies=tuple((ObjectIdentity.from_record(co.object_id, by_id[co.object_id]), policy) for co, policy in first.specification.selection.coordinate_policies))
    specification = replace(first.specification, selection=selection, publication=publish(plane, selection, 'software.response.selection'))
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification, provenances=first.index.provenances)
    sources = tuple(index.resolve(index.reference(source_id=source.source_id, root_id=source.root_id, provenance=source.reference.provenance)) for source in old)
    old_design = commit.forecast_design
    reservation_pub = publish(plane, reservation, 'software.response.reservation')
    training = replace(old_design.training_record, future_regime_reservation=r.identity(reservation),
        future_reservation_publication=c.corpus_artifact(reservation_pub))
    model = replace(old_design.model_record, spec=training.identity, reservation=r.identity(reservation))
    design = replace(old_design, allocation=r.identity(allocation), training_record=training, model_record=model,
        training_publication=publish(plane, training, 'software.response.training'),
        model_publication=publish(plane, model, 'software.response.model'))
    selected = tuple(s for s in sources if s.root_id in commit.selected_root_ids)
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype='<c16')
    templates = {'generic_basis': np.asarray([np.kron(np.eye(2), p)/2 for p in pauli], dtype='<c16'),
        'force_coefficients': np.stack((np.eye(3), np.eye(3))).astype('<f8')/np.sqrt(6),
        'trace_coefficients': np.ones((2, 3), dtype='<f8')/np.sqrt(6),
        'receiver_coefficients': np.eye(48, dtype='<f8').reshape(48, 2, 2, 3, 4)}
    raw, members = encode_matrix_arrays(templates)
    publication = plane.write(ArtifactWriteRequest('software.response.templates', 'software.response/templates.npz', science.MATRIX_ARRAY_SCHEMA,
        ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', 'software-response', 'software.response', raw,
        Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    artifact = c.corpus_artifact(publication)
    model = MatrixFactorResponseModel('model.software.response.mechanical', rr.physical_forecast_implementation())
    protocols = []
    for source in selected:
        arrays = rr.ScheduledResponseArrays('templates.'+source.root_id, 'TEMPLATES', r.identity(source), artifact, members, (r.identity(source),), Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
        protocol = rr.ScheduledResponseProtocol('protocol.'+source.root_id, f.ScheduledPublicSource.from_source(source), design.criterion, model,
            tuple(MatrixFactorAction('action.software.'+a.role.lower(), a.role, a.amplitude, a.pulse_steps, a.force_norm) for a in design.criterion_record.action_scales),
            design.criterion_record.horizon_steps, 48, arrays, D('1e-5'), D('1e-10'), D('1e-10'), D('1e-10'),
            D('1e-10'), D('1e-8'), D('1e-5'), D('1e-12'), design.criterion_record.receiver_gram_tolerance,
            'PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME')
        protocols.append(protocol)
    group = selected[0].root.root.independent_group_id
    panels = (rr.ScheduledResponsePanel('panel.common', group, 'COMMON_NOISE_PANEL', 'ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES', selected[0].root.streams),
        rr.ScheduledResponsePanel('panel.independent', group, 'INDEPENDENT_FUTURE', 'FRESH_DECLARED_FUTURE_START_AT_CUTOFF',
            tuple(MatrixHistorySeed(p, sha256(('EXPOSED-SOFTWARE-RESPONSE-'+p).encode()).hexdigest()) for p in HISTORY_PURPOSES)))
    criterion = sel.ScheduledCalibrationCriterion('criterion.software.calibration', 'unit.software.calibration.groups', 1, D(1),
        (selected[0].coordinate.family_id,), 'COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY')
    responses = sel.ScheduledResponseSelection('selection.software.response', ObjectIdentity.from_record(allocation.allocation_id, allocation), tuple(protocols), ((group, panels),), (publication,), criterion)
    responses.validate_allocation(allocation)
    config = replace(commit, reservation=reservation, specification=specification, provenances=index.provenances,
        sources=tuple(source.reference for source in sources), forecast_design=design, response_selection=responses,
        response_selection_publication=publish(plane, responses, 'software.response.original-selection'))
    return plane, sources, config, raw


def stock_plan(response_bank):
    """One immutable original25-task software plan, no issue or source claim."""
    plane, sources, commit, _ = response_bank
    selected = tuple(s for s in sources if s.root_id in commit.selected_root_ids)
    tasks = {}
    for source in selected:
        protocol, panels = commit.response_selection.validate_source(source)
        for role, ports, out, stage, raw in rb.RESPONSE_PHASES[:3]:
            task = r.NAMESPACE+'.'+source.root_id+'.'+role
            config = sel.ScheduledPhysicalForecastConfig('config.'+task, protocol) if role == 'physical-forecast' else sel.ScheduledResponseConfig('config.'+task, role, source.reference, commit.response_selection.identity, r.identity(commit))
            m = next(m for m in b.operation_manifests() if m.capability_key == r.NAMESPACE+'.'+role)
            ext = [ExternalInputSpec('config', config.config_id, config.fingerprint(), config.SCHEMA, 'application/json', len(config.canonical_bytes()), b.phase_visibility(role), b.phase_access(role), None)]
            deps = []
            for port, cls in ports:
                if port == 'templates':
                    a = protocol.templates.array_artifact
                    ext.append(ExternalInputSpec(port, a.artifact_id, a.sha256, a.payload_schema, a.media_type, a.size_bytes, Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None))
                    continue
                records = {'source': (source.source_id, source.reference), 'commitment-config': (commit.config_id, commit), 'allocation': (source.reservation.publication.logical.logical_artifact_id, source.allocation),
                    'selection': (source.specification.publication.logical.logical_artifact_id, source.specification.selection),
                    'response-selection': (commit.response_selection_publication.logical.logical_artifact_id, commit.response_selection),
                    'coordinate': (source.coordinate.coordinate_id, source.coordinate), 'provenance': (source.provenance.identity.object_id, source.provenance)}
                if port in records:
                    name, value = records[port]
                    ext.append(ExternalInputSpec(port, name, value.fingerprint(), value.SCHEMA, 'application/json', len(value.canonical_bytes()), Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None))
                    continue
                if port == 'streams':
                    rows = tuple(('streams.'+s.purpose, source.root.stream_identity(s).object_id, s) for s in source.root.streams)+tuple(('streams.future.'+s.purpose, p.stream_identity(s).object_id, s) for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams)
                    ext.extend(ExternalInputSpec(name, logical_id, value.fingerprint(), value.SCHEMA, 'application/json', len(value.canonical_bytes()), Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None) for name, logical_id, value in rows)
                    continue
                owner = 'prefix' if port.startswith('history') or port == 'checkpoint' else 'project' if port.startswith('causal') else 'forecast' if port == 'error-forecast' else 'commit' if port == 'commitment' else port.removesuffix('-arrays')
                producer = c.COMMIT_KEY if owner == 'commit' else r.NAMESPACE+'.'+source.root_id+'.'+owner
                ending = 'arrays' if port.endswith('-arrays') else 'checkpoint' if port == 'checkpoint' else 'product'
                logical = 'ordinary.'+producer+'.'+ending
                deps.append(ScientificInputSpec('edge.'+task+'.'+port, port, ScientificInputRole.OUTCOME, producer, producer+'.'+ending,
                    None, logical, logical, cls.SCHEMA if cls else science.MATRIX_ARRAY_SCHEMA, 'application/json' if cls else 'application/x-npz',
                    None, b.phase_access(owner), b.phase_visibility(owner), BarrierKind.FREEZE if owner in ('commit', 'forecast', 'physical-forecast') else BarrierKind.NONE))
            outputs = [ArtifactOutputSpec(task+'.product', 'ordinary.'+task+'.product', 'software.bindings/outputs/ordinary.'+task+'.product',
                out.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', b.phase_visibility(role), (), b.phase_access(role))]
            if raw:
                outputs.append(ArtifactOutputSpec(task+'.arrays', 'ordinary.'+task+'.arrays', 'software.bindings/outputs/ordinary.'+task+'.arrays',
                    science.MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', b.phase_visibility(role), (), b.phase_access(role)))
            req = CapabilityRequirement(m.capability_key, m.capability_version, m.kind,
                CapabilityConfigRef(config.config_id, config.SCHEMA, m.config_schema_sha256, config.fingerprint(), config.config_id),
                m.input_schema_ids, m.output_schema_ids, m.permissions, m.maximum_evidence_ceiling, b.phase_access(role), TEST_BUDGET)
            tasks[task] = ExecutionTask(task, stage, req, m.implementation_sha256, tuple(sorted({d.producer_task_id for d in deps})),
                tuple(sorted(ext, key=lambda e: e.input_id)), tuple(sorted(outputs, key=lambda o: o.output_id)), (),
                BarrierKind.FREEZE if role == 'physical-forecast' else BarrierKind.NONE, 1, ('obligation.software.'+role,), scientific_inputs=tuple(sorted(deps, key=lambda d: d.edge_id)))
    plans = tuple(actual_plan((plane, sources, commit), source, publish_plan=False,
        additional_tasks=tuple(task for task in tasks.values() if task.task_id.startswith(r.NAMESPACE+'.'+source.root_id+'.')))
        for source in selected)
    tasks.update((task.task_id, task) for plan in plans for task in plan.tasks)
    for role, ports, out, stage in CALIBRATION_PHASES:
        task, deps = r.NAMESPACE+'.'+role, []
        config = ScheduledCalibrationConfig('config.'+task, role, r.identity(commit), 'calibration.'+commit.response_selection.selection_id,
            tuple(sorted({source.root.root.independent_group_id for source in selected})))
        m = next(m for m in b.operation_manifests() if m.capability_key == task)
        for port, cls in ports:
            if port == 'commitment-config':
                continue
            rows = ((c.COMMIT_KEY, 'commitment'),) if port == 'commitment' else ((r.NAMESPACE+'.calibrate', 'calibration'),) if port == 'calibration' else tuple((r.NAMESPACE+'.'+s.root_id+'.'+('response-score' if port == 'scores' else 'forecast'), port+'.'+s.root_id) for s in selected)
            for producer, name in rows:
                logical = 'ordinary.'+producer+'.product'
                owner = producer.rsplit('.', 1)[-1]
                deps.append(ScientificInputSpec('edge.'+task+'.'+name, name, ScientificInputRole.OUTCOME, producer, producer+'.product',
                    None, logical, logical, cls.SCHEMA, 'application/json', None, b.phase_access(owner), b.phase_visibility(owner),
                    BarrierKind.FREEZE if owner in ('commit', 'forecast') else BarrierKind.NONE))
        output_id = 'adjudication' if role == 'calibration-qualify' else 'product'
        actual_access = Access.EVALUATION_REVEALED if role == 'calibration-qualify' else b.phase_access(role)
        outputs = (ArtifactOutputSpec(task+'.'+output_id, 'ordinary.'+task+'.'+output_id,
            'software.bindings/outputs/ordinary.'+task+'.'+output_id, out.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            'application/json', b.phase_visibility(role), (), actual_access),)
        req = CapabilityRequirement(m.capability_key, m.capability_version, m.kind,
            CapabilityConfigRef(config.config_id, config.SCHEMA, m.config_schema_sha256, config.fingerprint(), config.config_id),
            m.input_schema_ids, m.output_schema_ids, m.permissions, m.maximum_evidence_ceiling, b.phase_access(role), TEST_BUDGET)
        tasks[task] = ExecutionTask(task, stage, req, m.implementation_sha256, tuple(sorted({d.producer_task_id for d in deps})),
            tuple(sorted((ExternalInputSpec('config', config.config_id, config.fingerprint(), config.SCHEMA, 'application/json', len(config.canonical_bytes()), Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None),
                ExternalInputSpec('commitment-config', commit.config_id, commit.fingerprint(), commit.SCHEMA, 'application/json', len(commit.canonical_bytes()), Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None)), key=lambda value: value.input_id)),
            outputs, (), BarrierKind.REVEAL if role == 'calibration-qualify' else BarrierKind.NONE, 1, ('obligation.software.'+role,), scientific_inputs=tuple(sorted(deps, key=lambda d: d.edge_id)))
    plan = replace(plans[0], tasks=tuple(sorted(tasks.values(), key=lambda t: t.task_id)))
    plane.write(ArtifactWriteRequest(plan.execution_plan_id, 'runs/run.software.bindings/plans/execution-plan.json', plan.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'software-original-plan', 'runs/run.software.bindings/plans', plan.canonical_bytes(), Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    return plan


def run_response(response_bank, *, root_id=None, plan=None):
    plane, sources, commit, template_raw = response_bank
    plan = plan or stock_plan(response_bank)
    def before_continue(source, receipts, outputs, original_inputs, products):
        protocol = commit.response_selection.validate_source(source)[0]
        physical_config = sel.ScheduledPhysicalForecastConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.physical-forecast', protocol)
        templates = retained._manifest(plane, commit.response_selection.template_publications[0].materialization.relative_path)
        selected = tuple(m for m in outputs['project'] if m.logical.payload_schema != f.ScheduledForecastFeature.SCHEMA)
        ctx, original_inputs['physical-forecast'] = context(plane, physical_config, 'physical-forecast', (*selected, templates), (receipts['project'],))
        result = rb.ScheduledResponseRunner('physical-forecast').execute(ctx)
        receipts['physical-forecast'], outputs['physical-forecast'] = finish(plane, ctx, result, source)
        products['physical-forecast'] = decode_canonical_bytes(next(o.payload for o in result.outputs if o.output_id.endswith('.product')), rr.ScheduledResponseForecast, maximum_bytes=None)
    data = pipeline((plane, sources, commit), root_id=root_id, plan=plan, before_continue=before_continue)
    _, source, _, _, receipts, outputs, original_inputs, products = data
    protocol, panels = commit.response_selection.validate_source(source)
    for role in ('responses', 'response-score'):
        config = sel.ScheduledResponseConfig('config.'+r.NAMESPACE+'.'+source.root_id+'.'+role, role, source.reference, commit.response_selection.identity, r.identity(commit))
        inputs, deps = [], []
        for port, cls in next(p for p in rb.RESPONSE_PHASES if p[0] == role)[1]:
            if port == 'commitment-config':
                inputs.append(shared_manifest(plane, commit))
            elif port in ('allocation', 'selection', 'response-selection'):
                pub = {'allocation': source.reservation.publication, 'selection': source.specification.publication,
                    'response-selection': commit.response_selection_publication}[port]
                inputs.append(retained._manifest(plane, pub.materialization.relative_path))
            elif port in ('source', 'coordinate', 'provenance'):
                value = {'source': source.reference, 'coordinate': source.coordinate, 'provenance': source.provenance}[port]
                name = source.source_id if port == 'source' else source.coordinate.coordinate_id if port == 'coordinate' else source.provenance.identity.object_id
                inputs.append(write(plane, name, value.canonical_bytes(), value.SCHEMA))
            elif port == 'streams':
                rows = tuple((source.root.stream_identity(s).object_id, s) for s in source.root.streams)+tuple((p.stream_identity(s).object_id, s) for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams)
                inputs.extend(write(plane, name, s.canonical_bytes(), s.SCHEMA) for name, s in rows)
            else:
                owner = 'prefix' if port.startswith('history') or port == 'checkpoint' else 'project' if port == 'causal' else 'forecast' if port == 'error-forecast' else 'commit' if port == 'commitment' else port.removesuffix('-arrays')
                ending = 'arrays' if port.endswith('-arrays') else 'checkpoint' if port == 'checkpoint' else 'product'
                inputs.append(next(m for m in outputs[owner] if m.logical.logical_artifact_id.endswith('.'+ending)))
                deps.append(receipts[owner])
        ctx, manifests = context(plane, config, role, tuple(inputs), tuple(dict.fromkeys(deps)))
        original_inputs[role] = manifests
        if role == 'responses':
            pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
            from tests.matrix_native_invocation_support import prepared_native_store
            runner = rb.ScheduledPulseNativeRunner(role)
            store,ctx,_ = prepared_native_store(plane,runner=runner,context=ctx,manifests=manifests,
                provenance=source.provenance,execution_plan=pin,native_work_preparer=rb.prepare_native_work,
                task_record=next(t for t in plan.tasks if t.task_id == ctx.task_id),
                visibility=Visibility.PROSPECTIVE,access=Access.EVALUATION_SEALED)
            result = runner.execute_with_native_subwork(ctx, store)
        else:
            result = rb.ScheduledResponseRunner(role).execute(ctx)
        receipts[role], outputs[role] = finish(plane, ctx, result, source)
        products[role] = decode_canonical_bytes(next(o.payload for o in result.outputs if o.output_id.endswith('.product')), rr.ScheduledResponseNative if role == 'responses' else rr.ScheduledResponseScore, maximum_bytes=None)
    return data, protocol, panels


def test_actual_stock_pulse_then_full_independent_scores_and_retained_no_effects(response_bank, monkeypatch):
    data, protocol, panels = run_response(response_bank)
    plane, source, commit, _, receipts, outputs, _, products = data
    score = products['response-score']
    assert len(products['responses'].branch_ids) == 48
    assert len(score.cells) == 240 and len(score.cumulative_log_errors) == 15
    if products['responses'].disposition == 'COMPLETED':
        assert len(products['responses'].native) == 1 and len(score.controls) == 48 and score.numerical_pass
        assert sum(c.denominator_steps for c in score.controls) == 24*128+24*256
    else:
        assert not products['responses'].native and all(v is None for v in score.cumulative_log_errors)
    prefix = decode_matrix_arrays(plane.root.resolve(next(m.materialization.relative_path for m in outputs['prefix'] if m.logical.payload_schema == science.MATRIX_ARRAY_SCHEMA), for_write=False).read_bytes(), products['prefix'].arrays)
    frozen = decode_matrix_arrays(plane.root.resolve(next(m.materialization.relative_path for m in outputs['physical-forecast'] if m.logical.payload_schema == science.MATRIX_ARRAY_SCHEMA), for_write=False).read_bytes(), products['physical-forecast'].arrays)
    arrays = decode_matrix_arrays(plane.root.resolve(next(m.materialization.relative_path for m in outputs['responses'] if m.logical.payload_schema == science.MATRIX_ARRAY_SCHEMA), for_write=False).read_bytes(), products['responses'].arrays)
    for owner, names in ((rs, ('native_responses', 'panel_innovations')), (rb, ('native_responses',)),
            (np.random, ('Generator', 'PCG64DXSM')), (np.linalg, ('eigh', 'eigvalsh')),
            (ExternalNativeSubworkStore, ('begin', 'contact', 'freeze_roster', 'publish_output', 'complete', 'recover')),
            (ExternalTaskReceiptStore, ('commit',))):
        for name in names:
            monkeypatch.setattr(owner, name, blocked)
    assert rs.assess_responses(source, products['project'], products['prefix'], prefix, products['forecast'], products['physical-forecast'], frozen,
        protocol, panels, products['responses'], arrays, score_id=score.score_id) == score
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.retained_bindings import read_response
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source, parameter_history_segments, parameter_derivatives
    for owner, names in ((science, ('measure_prefix',)), (response_forecast, ('_hessian',)),
            (parameter_derivatives, ('hessian_image', 'scheduled_force_step')),
            (parameter_source, ('acquire_parameter_history',)), (parameter_history_segments, ('acquire_parameter_segment',)),
            (ExternalNativeEffectContactStore, ('begin',))):
        for name in names:
            monkeypatch.setattr(owner, name, blocked)
    roles = ('commit', 'prefix', 'numerical', 'measure', 'check', 'project', 'forecast', 'physical-forecast',
        'continue', 'full-numerical', 'responses', 'response-score')
    root = Path(plane.root.contract.canonical_path)
    before = {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob('*') if p.is_file()}
    found = read_response(plane=plane, run_id=receipts['prefix'].run_id, execution_plan=ObjectIdentity.from_record(data[3].execution_plan_id, data[3]),
        commitment=commit, root_id=source.root_id, original_inputs=tuple((role, data[6][role]) for role in roles),
        receipt_locators=tuple((role, receipts[role].attempt_id) for role in roles))
    assert found['response-score'] == score and found['responses'] == products['responses']
    assert before == {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob('*') if p.is_file()}


def test_actual_whole_two_coordinate_group_calibration_uses_original_receipted_scores(response_bank):
    plane, _, commit, _ = response_bank
    plan = stock_plan(response_bank)
    assert len(plan.tasks) == 25
    cases = tuple(run_response(response_bank, root_id=root, plan=plan)[0] for root in commit.selected_root_ids)
    config = ScheduledCalibrationConfig('config.'+r.NAMESPACE+'.calibrate', 'calibrate', r.identity(commit), 'calibration.'+commit.response_selection.selection_id,
        tuple(sorted({source.root.root.independent_group_id for source in response_bank[1] if source.root_id in commit.selected_root_ids})))
    inputs = [*cases[0][5]['commit'], shared_manifest(plane, commit)]
    dependencies = [cases[0][4]['commit']]
    for case in cases:
        for role in ('forecast', 'response-score'):
            inputs.extend(case[5][role]); dependencies.append(case[4][role])
    ctx, _ = context(plane, config, 'calibrate', tuple(inputs), tuple(dependencies))
    result = ScheduledCalibrator('calibrate').execute(ctx)
    receipt, outputs = finish(plane, ctx, result, cases[0][1])
    calibration = decode_canonical_bytes(result.outputs[0].payload, f.ScheduledCalibration, maximum_bytes=None)
    assert len(calibration.cases) == 2 and len(calibration.group_ids) == 1
    assert calibration.scores[0][1] is None  # Actual short causal feature is nonuse, never imputed.
    assert all(case.forecast_receipt_id in {q.receipt_id for q in dependencies} and case.score_receipt_id in {q.receipt_id for q in dependencies} for case in calibration.cases)
    assert {case.score_materialization_id for case in calibration.cases} <= set(receipt.input_materialization_ids)
    assert outputs[0].logical.outcome_access is Access.EVALUATION_SEALED
    for name in ('noise.panel.common.primary', 'noise.panel.independent.primary'):
        values = []
        for case in cases:
            response = case[7]['responses']
            if response.disposition == 'COMPLETED':
                manifest = next(m for m in case[5]['responses'] if m.logical.payload_schema == science.MATRIX_ARRAY_SCHEMA)
                values.append(decode_matrix_arrays(plane.root.resolve(manifest.materialization.relative_path, for_write=False).read_bytes(), response.arrays)[name])
        if values:
            assert len(values) == 2 and np.array_equal(*values)


def test_whole_group_calibration_does_not_omit_unavailable_coordinate(response_bank):
    # Pure reduction control complements the actual pulse/score route above.
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.calibration import reduce_cases
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledCalibrationCase
    source = next(s for s in response_bank[1] if s.root_id == response_bank[2].selected_root_ids[0])
    value = ScheduledCalibrationCase(source.root_id, source.root.root.independent_group_id, r.identity(source),
        ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate), D('.006'),
        ObjectIdentity('score.software.cal', rr.ScheduledResponseScore.SCHEMA, '1.0.0', 'a'*64),
        ObjectIdentity('seal.software.cal', f.ScheduledForecastSeal.SCHEMA, '1.0.0', 'b'*64),
        'receipt.software.score', 'receipt.software.forecast', 'materialization.software.score', 'materialization.software.forecast',
        'FINITE', (D(1),)*15, (D('.5'),)*15)
    assert reduce_cases((value,)) == ((source.root.root.independent_group_id, D('.5'), ('finite-complete-whole-group-max15-residual',)),)
    negative = replace(value, root_id=response_bank[2].selected_root_ids[1], disposition='UNEVALUABLE', cumulative_log_errors=(None,)*15)
    assert reduce_cases((value, negative))[0][1] is None


@pytest.mark.parametrize("damage", ("foreign-parent", "missing-coordinate", "common-stream", "history-reuse", "exposed-future", "matched-assay"))
def test_response_selection_pin_keeps_complete_allocation_and_stream_refusals(response_bank, damage):
    """Literal exposed inputs only; full scientific context remains explicit."""
    _, sources, commit, _ = response_bank
    selected = commit.response_selection
    allocation = commit.reservation.allocation
    if damage == "foreign-parent":
        with pytest.raises(ValueError, match="shared allocation"):
            selected.validate_allocation(replace(allocation, allocation_id="allocation.foreign"))
        return
    if damage == "missing-coordinate":
        changed = replace(selected, protocols=selected.protocols[:-1])
        with pytest.raises(ValueError, match="coordinate case"):
            changed.validate_allocation(allocation)
        return
    if damage == "matched-assay":
        first, *others = selected.protocols
        changed = replace(selected, protocols=(replace(first,
            hessian_difference_step=first.hessian_difference_step * 2), *others))
        with pytest.raises(ValueError, match="matched scheduled coordinates"):
            changed.validate_allocation(allocation)
        return
    group, panels = selected.panels[0]
    common = next(panel for panel in panels if panel.role == "COMMON_NOISE_PANEL")
    independent = next(panel for panel in panels if panel.role == "INDEPENDENT_FUTURE")
    if damage == "common-stream":
        changed_panel = replace(common, streams=independent.streams)
        # Preserve internal distinct-stream ownership while changing the exact
        # original paired history menu; the allocation join must refuse it.
        changed_panels = tuple(changed_panel if panel is common else replace(panel,
            streams=tuple(replace(stream, digest_sha256=sha256(("foreign.future." + stream.purpose).encode()).hexdigest())
                for stream in panel.streams)) for panel in panels)
    elif damage == "history-reuse":
        history = next(root for root in allocation.roots if root.root.independent_group_id != group)
        changed_panels = tuple(replace(panel, streams=history.streams) if panel is independent else panel for panel in panels)
    else:
        exposed = next(iter(allocation.exposure.census.effective_seed_exclusions))
        first, *others = independent.streams
        forbidden = replace(first, digest_sha256=f"{exposed:032x}" + "0" * 32)
        changed_panels = tuple(replace(panel, streams=(forbidden, *others)) if panel is independent else panel for panel in panels)
    changed = replace(selected, panels=((group, changed_panels),))
    with pytest.raises(ValueError, match="common panel|exposed/history"):
        changed.validate_allocation(allocation)


def test_response_selection_serializes_only_its_exact_allocation_pin(response_bank):
    """No source body, qualification or fresh acquisition is inferred from a pin."""
    _, sources, commit, _ = response_bank
    selected, allocation = commit.response_selection, commit.reservation.allocation
    source = next(row for row in sources if row.root_id == selected.protocols[0].public_source.root.root_id)
    assert selected.VERSION == "2.0.0"
    assert selected.allocation == r.identity(allocation)
    assert selected.to_document()["value"]["allocation"] == selected.allocation.to_document()
    raw = selected.canonical_bytes()
    assert decode_canonical_bytes(raw, type(selected), maximum_bytes=None) == selected
    selected.validate_allocation(allocation)
    assert selected.validate_source(source) == (selected.protocols[0], dict(selected.panels)[source.root.root.independent_group_id])
    with pytest.raises(TypeError, match="allocation identity"):
        replace(selected, allocation=allocation)
    with pytest.raises(TypeError, match="allocation identity"):
        replace(selected, allocation=replace(selected.allocation, object_version="0.0.0"))
    with pytest.raises(ValueError, match="version"):
        decode_canonical_record({**selected.to_document(), "version": "1.0.0"}, type(selected))
