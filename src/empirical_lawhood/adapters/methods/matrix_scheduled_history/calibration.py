# SPDX-License-Identifier: MPL-2.0
"""Whole matched-group residuals and strict original sealed-parent semantics.

This reduction fits nothing and grants no credentials. Stock parent custody
replays actual issue/execution/reveal and complete successful receipts before
the code-owned assessor is called. A development or plumbing fixture refuses.
"""

from decimal import Decimal, localcontext

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.recursive_qualified_parents import QualifiedParentEvidence

from .forecast import CALIBRATION_POINT, ScheduledCalibration, ScheduledCalibrationCase, ScheduledForecastSeal, _case_digest
from .records import NAMESPACE, identity
from .response_records import ScheduledResponseScore


def reduce_cases(cases):
    scores = []
    for group in sorted({c.independent_group_id for c in cases}):
        residuals, reasons = [], []
        for case in (c for c in cases if c.independent_group_id == group):
            for loss, point in zip(case.cumulative_log_errors, case.log_error_points, strict=True):
                if loss is None or point is None:
                    reasons.append(case.disposition if loss is None else 'NO_FINITE_PRE_FUTURE_POINT_FORECAST')
                else:
                    with localcontext() as ctx:
                        ctx.prec = 50
                        residuals.append(max(Decimal(0), loss-point))
        scores.append((group, None if reasons else max(residuals),
            tuple(sorted(set(reasons))) if reasons else ('finite-complete-whole-group-max15-residual',)))
    return tuple(scores)


def calibrate(commitment, scores, forecasts, *, custody, calibration_id, sources=None):
    """Every requested CALIBRATION case, including known nonuse and unknown."""
    from .qualification import selected_sources
    sources = selected_sources(commitment, sources=sources)
    if any(s.root.root.role is not MatrixProgrammeRole.CALIBRATION for s in sources):
        raise ValueError('scheduled calibration crosses whole-bank role assignment')
    roots = tuple(s.root_id for s in sources)
    ss, fs = {s.root_id: s for s in scores}, {s.feature.root_id: s for s in forecasts}
    if (len(ss) != len(scores) or len(fs) != len(forecasts) or tuple(sorted(ss)) != roots
            or tuple(sorted(fs)) != roots or set(custody) != set(roots)):
        raise ValueError('scheduled calibration drops/duplicates requested complete matched coordinate cases')
    design, cases = commitment.forecast_design, []
    for source in sources:
        score, seal = ss[source.root_id], fs[source.root_id]
        if (type(score) is not ScheduledResponseScore or type(seal) is not ScheduledForecastSeal
                or score.source != identity(source) or score.independent_group_id != source.root.root.independent_group_id
                or score.role != MatrixProgrammeRole.CALIBRATION.value or score.error_forecast != identity(seal)
                or score.criterion != design.criterion or seal.source != identity(source) or seal.scope != CALIBRATION_POINT
                or seal.design != identity(design) or seal.model != design.model or seal.criterion != design.criterion
                or seal.calibration is not None or seal.radius is not None
                or score.disposition in ('FINITE', 'PARTIAL') and not score.numerical_pass):
            raise ValueError('scheduled calibration substitutes actual pre-future model/criterion/source/score')
        sr, fr, sm, fm = custody[source.root_id]
        cases.append(ScheduledCalibrationCase(source.root_id, score.independent_group_id, identity(source), coordinate_identity(source.coordinate),
            source.coordinate.physical_time(source.policy.cutoff_tick), identity(score), identity(seal), sr, fr, sm, fm,
            score.disposition, score.cumulative_log_errors, seal.log_error_points))
    cases = tuple(cases)
    criterion = commitment.response_selection.calibration_criterion
    return ScheduledCalibration(calibration_id, identity(sources[0].reservation), design.model, design.criterion,
        identity(sources[0].allocation), criterion.identity, criterion.independent_unit_id,
        tuple(sorted({s.coordinate.family_id for s in sources})), cases, tuple(sorted({c.independent_group_id for c in cases})), reduce_cases(cases),
        tuple(sorted((c.score for c in cases), key=lambda o: o.object_id)), _case_digest(cases))


def validate_calibration_sources(commitment, calibration, *, sources=None):
    """Bind every retained calibration case to the frozen original source bank."""
    from .qualification import selected_sources
    sources = selected_sources(commitment, sources=sources)
    criterion = commitment.response_selection.calibration_criterion
    if (calibration.reservation != identity(sources[0].reservation)
            or calibration.allocation != identity(sources[0].allocation)
            or calibration.model != commitment.forecast_design.model
            or calibration.criterion != commitment.forecast_design.criterion
            or calibration.qualification_criterion != criterion.identity
            or calibration.independent_unit_id != criterion.independent_unit_id
            or calibration.family_ids != tuple(sorted({s.coordinate.family_id for s in sources}))
            or calibration.group_ids != tuple(sorted({s.root.root.independent_group_id for s in sources}))
            or tuple(case.root_id for case in calibration.cases) != commitment.selected_root_ids):
        raise ValueError('scheduled calibration changes complete original source/model/criterion/group scope')
    for source, case in zip(sources, calibration.cases, strict=True):
        if (case.source != identity(source) or case.coordinate != coordinate_identity(source.coordinate)
                or case.independent_group_id != source.root.root.independent_group_id
                or case.cutoff != source.coordinate.physical_time(source.policy.cutoff_tick)):
            raise ValueError('scheduled calibration changes original case source/coordinate/cutoff')


def qualified_parent_assessor(*, requirement, connection, contribution, product, parent_evidence):
    """Require actual numerical qualification and the exact sealed complete bank."""
    if type(parent_evidence) is not QualifiedParentEvidence:
        raise PermissionError('scheduled calibration has no stock authenticated original parent evidence')
    c = decode_canonical_bytes(parent_evidence.product_payload, ScheduledCalibration, maximum_bytes=16*1024**2)
    q, plan, producing = parent_evidence.adjudication, parent_evidence.execution_plan, parent_evidence.producing_receipt
    from .calibration_bindings import ScheduledCalibrationConfig
    from .commitment import ScheduledCommitmentConfig
    from .response_selection import ScheduledResponseConfig
    from .forecast import ScheduledForecastConfig
    from .compact_records import (NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactBank,
        ScheduledCompactCalibrationConfig, ScheduledCompactCommitmentConfig, ScheduledCompactForecastConfig,
        ScheduledCompactResponseConfig)
    compact = producing.task_id == COMPACT_NAMESPACE+'.calibrate'
    namespace = COMPACT_NAMESPACE if compact else NAMESPACE
    calibration_schema = ScheduledCompactCalibrationConfig.SCHEMA if compact else ScheduledCalibrationConfig.SCHEMA
    response_schema = ScheduledCompactResponseConfig.SCHEMA if compact else ScheduledResponseConfig.SCHEMA
    forecast_schema = ScheduledCompactForecastConfig.SCHEMA if compact else ScheduledForecastConfig.SCHEMA
    scope = requirement.scope
    if (requirement.condition_role is not ConditionRole.EVIDENTIAL or scope is None or scope != contribution.scope
            or scope.population_id != c.calibration_id or scope.source_config_sha256 != c.fingerprint()
            or connection.consumer_input_id != 'calibration' or connection.evidence_role is not ContributionRole.QUALIFIED_EVIDENTIAL_PARENT
            or not requirement.consumer_operation_id.endswith('.forecast-calibrated')
            or product.record != identity(c) or product.artifact.sha256 != c.fingerprint()
            or product.outcome_access is not OutcomeAccess.EVALUATION_SEALED or product.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
            or q.plumbing_only or q.fixture_scope_id is not None or q.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or parent_evidence.package.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or q.relation != identity(parent_evidence.package.system.relation) or q.independent_unit_id != c.independent_unit_id
            or q.reason_codes != ('scheduled-complete-original-calibration-bank-qualified',)
            or producing.task_id != namespace+'.calibrate'
            or not ({case.score_materialization_id for case in c.cases} | {case.forecast_materialization_id for case in c.cases})
                <= set(producing.input_materialization_ids)):
        raise PermissionError('scheduled calibration parent changes genuine qualification, original full-bank scope or sealed lineage')
    task_ids = {t.task_id for t in plan.tasks}
    from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage
    producing_tasks = tuple(t for t in plan.tasks if t.task_id == producing.task_id)
    qualification_tasks = tuple(t for t in plan.tasks if t.task_id == parent_evidence.qualification_receipt.task_id)
    if len(producing_tasks) != 1 or len(qualification_tasks) != 1:
        raise PermissionError('scheduled calibration omits its exact producing/qualification tasks')
    producing_task, qualification_task = producing_tasks[0], qualification_tasks[0]
    for task, key in ((producing_task, namespace+'.calibrate'), (qualification_task, namespace+'.calibration-qualify')):
        if (task.capability.capability_key != key or task.capability.capability_version != '1.0.0'
                or task.capability.config.config_id != 'config.'+key or task.capability.config.config_schema != calibration_schema):
            raise PermissionError('scheduled calibration changes actual original producing/qualification owner/config')
    bank = None
    shared_commitment = None
    if compact:
        # The custody owner authenticated the issued plan and every actual input
        # manifest. Reconstruct these small configurations from that frozen bank
        # pin and compare canonical hashes; this reads no unprovided bank bytes.
        def bank_pin(task):
            rows = tuple(p for p in task.external_inputs if p.expected_payload_schema == ScheduledCompactBank.SCHEMA)
            if (len(rows) != 1 or rows[0].expected_content_sha256 is None
                    or rows[0].expected_media_type != 'application/json'
                    or rows[0].expected_outcome_access is not OutcomeAccess.OUTCOME_BLIND
                    or rows[0].expected_visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
                raise PermissionError('scheduled compact parent omits its actual frozen shared bank input')
            from empirical_lawhood.kernel.provenance import ObjectIdentity
            return ObjectIdentity(rows[0].logical_artifact_id, ScheduledCompactBank.SCHEMA,
                ScheduledCompactBank.VERSION, rows[0].expected_content_sha256)

        bank = bank_pin(producing_task)
        for task, qualify in ((producing_task, False), (qualification_task, True)):
            config = ScheduledCompactCalibrationConfig('config.'+task.task_id, bank, c.calibration_id, qualify, c.group_ids)
            if bank_pin(task) != bank or task.capability.config.content_sha256 != config.fingerprint():
                raise PermissionError('scheduled compact calibration changes exact frozen bank/group/configuration lineage')
        commit_tasks = tuple(t for t in plan.tasks if t.task_id == namespace+'.commit')
        if (len(commit_tasks) != 1 or bank_pin(commit_tasks[0]) != bank
                or commit_tasks[0].capability.capability_key != namespace+'.commit'
                or commit_tasks[0].capability.capability_version != '1.0.0'
                or commit_tasks[0].capability.config.config_id != 'config.'+namespace+'.commit'
                or commit_tasks[0].capability.config.config_schema != ScheduledCompactCommitmentConfig.SCHEMA
                or set(qualification_task.dependency_task_ids) != {namespace+'.commit', namespace+'.calibrate',
                    *(namespace+'.'+case.root_id+'.full-numerical' for case in c.cases)}):
            raise PermissionError('scheduled compact parent loses its exact shared bank commitment/reveal dependencies')
    else:
        def shared_pin(task):
            rows = tuple(p for p in task.external_inputs if p.expected_payload_schema == ScheduledCommitmentConfig.SCHEMA)
            if (len(rows) != 1 or rows[0].expected_content_sha256 is None
                    or rows[0].expected_media_type != 'application/json'
                    or rows[0].expected_outcome_access is not OutcomeAccess.OUTCOME_BLIND
                    or rows[0].expected_visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
                raise PermissionError('scheduled parent omits its exact current shared commitment input')
            return ObjectIdentity(rows[0].logical_artifact_id, ScheduledCommitmentConfig.SCHEMA,
                ScheduledCommitmentConfig.VERSION, rows[0].expected_content_sha256)

        shared_commitment = shared_pin(producing_task)
        for task, role in ((producing_task, 'calibrate'), (qualification_task, 'calibration-qualify')):
            config = ScheduledCalibrationConfig('config.'+task.task_id, role, shared_commitment, c.calibration_id, c.group_ids)
            if shared_pin(task) != shared_commitment or task.capability.config.content_sha256 != config.fingerprint():
                raise PermissionError('scheduled calibration changes exact shared commitment/group/configuration lineage')
        commit_tasks = tuple(t for t in plan.tasks if t.task_id == namespace+'.commit')
        if (len(commit_tasks) != 1 or commit_tasks[0].capability.config.config_schema != ScheduledCommitmentConfig.SCHEMA
                or commit_tasks[0].capability.config.config_id != shared_commitment.object_id
                or commit_tasks[0].capability.config.content_sha256 != shared_commitment.object_fingerprint
                or commit_tasks[0].capability.capability_key != namespace+'.commit'
                or commit_tasks[0].capability.capability_version != '1.0.0'
                or set(qualification_task.dependency_task_ids) != {namespace+'.commit', namespace+'.calibrate'}):
            raise PermissionError('scheduled parent loses its exact current shared commitment/reveal dependencies')
    expected_producers = {namespace+'.'+case.root_id+'.'+role for case in c.cases for role in ('response-score', 'forecast')} | {namespace+'.commit'}
    if set(producing_task.dependency_task_ids) != expected_producers or qualification_task.stage is not ScientificStage.REVEAL or qualification_task.barrier is not BarrierKind.REVEAL:
        raise PermissionError('scheduled calibration thins original score/point census or separate genuine reveal')
    for case in c.cases:
        score_task = namespace+'.'+case.root_id+'.response-score'
        forecast_task = namespace+'.'+case.root_id+'.forecast'
        if (score_task not in task_ids or forecast_task not in task_ids
                or not case.score_receipt_id.startswith('receipt.') or not case.forecast_receipt_id.startswith('receipt.')):
            raise PermissionError('scheduled calibration lacks actual original CALIBRATION score/point operations')
        score_plan = next(t for t in plan.tasks if t.task_id == score_task)
        forecast_plan = next(t for t in plan.tasks if t.task_id == forecast_task)
        for task, role, schema in ((score_plan, 'response-score', response_schema),
                (forecast_plan, 'forecast', forecast_schema)):
            if (task.capability.capability_key != namespace+'.'+role or task.capability.capability_version != '1.0.0'
                    or task.capability.config.config_schema != schema or task.capability.config.config_id != 'config.'+task.task_id):
                raise PermissionError('scheduled calibration case substitutes exact original phase/config/root owner')
        if compact and bank_pin(score_plan) != bank:
            raise PermissionError('scheduled compact calibration case substitutes its frozen shared bank')
        if not compact and shared_pin(score_plan) != shared_commitment:
            raise PermissionError('scheduled calibration case substitutes its exact current shared commitment')
        if compact:
            from .compact_records import ScheduledCompactConfig
            full_tasks = tuple(t for t in plan.tasks if t.task_id == namespace+'.'+case.root_id+'.full-numerical')
            if len(full_tasks) != 1:
                raise PermissionError('scheduled compact calibration omits an independent full-history assessment')
            full_task = full_tasks[0]
            if (bank_pin(full_task) != bank or full_task.stage is not ScientificStage.FALSIFY
                    or full_task.capability.capability_key != namespace+'.full-numerical'
                    or full_task.capability.capability_version != '1.0.0'
                    or full_task.capability.config.config_schema != ScheduledCompactConfig.SCHEMA
                    or full_task.capability.config.config_id != 'config.'+full_task.task_id
                    or set(full_task.dependency_task_ids) != {namespace+'.'+case.root_id+'.continue'}):
                raise PermissionError('scheduled compact calibration changes independent full-history numerical lineage')
        if (forecast_plan.stage is not ScientificStage.FREEZE or forecast_plan.barrier is not BarrierKind.FREEZE
                or score_plan.stage is not ScientificStage.FALSIFY
                or namespace+'.'+case.root_id+'.responses' not in score_plan.dependency_task_ids
                or forecast_task not in score_plan.dependency_task_ids):
            raise PermissionError('scheduled calibration case loses original pre-future point or independent pulse score')
