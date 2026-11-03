# SPDX-License-Identifier: MPL-2.0
"""Exposed bounded calibration software controls, never scientific credentials."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    programme_bindings as wave_bindings, programme_calibration as owner,
    programme_calibration_bindings as bindings, programme_reduction as reduction,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityRequirement
from empirical_lawhood.runtime.plans import (
    ArtifactOutputSpec, BarrierKind, CandidateExecutionPlan, ExecutionTask, ExternalInputSpec, PlanLane,
    ScientificInputRole, ScientificInputSpec,
)
from tests.test_matrix_scheduled_programme_reduction import declared as declared
from tests.test_recursive_public_service import _plane


def _pin(key, schema, version='1.0.0'):
    return ObjectIdentity(key, schema, version, sha256(key.encode()).hexdigest())


def _publish(plane, record, key, *, sealed=False):
    return plane.write(ArtifactWriteRequest(key, 'inputs/'+key+'.json', record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        'application/json', 'publication.'+key, 'inputs', record.canonical_bytes(), Visibility.PROSPECTIVE, (),
        Access.EVALUATION_SEALED if sealed else Access.OUTCOME_BLIND))


def stored_wave_custody(plane, programme, cases):
    """Closed actual stored bytes around expressly synthetic completion labels.

    No source qualification, issue, authority or native result is fabricated.
    Every locator is absent, so these records can never pass the reveal owner.
    This helper exists for bounded public author/load software tests.
    """
    factories = {f.manifest.capability_key: f for f in wave_bindings.operation_factories()}
    by_root, results, custody, plans = {c.root_id: c for c in cases}, [], [], []
    for wave in programme.waves:
        headers, tasks, rows = {}, [], []
        for root in wave.root_ids:
            old = by_root[root]
            references = []
            for role in ('prefix', 'numerical', 'measure', 'check', 'project', 'forecast', 'continue',
                    'full-numerical', 'physical-forecast', 'responses', 'response-score'):
                task_id = owner.COMPACT_NAMESPACE+'.'+root+'.'+role
                references.append(reduction.ScheduledProgrammeReceiptReference('receipt.synthetic.'+task_id,
                    task_id, ('materialization.synthetic.'+task_id,)))
                headers[task_id] = references[-1]
            rows.append(replace(old, ordinary_receipts=tuple(sorted(references, key=lambda r: r.receipt_id))))
        result = reduction.ScheduledProgrammeWaveResult('result.'+wave.wave_id, programme.identity, wave.wave_id,
            wave.group_ids, wave.root_ids, tuple(rows))
        result_publication = _publish(plane, result, 'scientific.'+wave.wave_id+'.collect.product', sealed=True)
        config = wave_bindings.ScheduledProgrammeWaveCollectorConfig('config.'+wave.wave_id+'.collect', programme.identity,
            programme.bank, wave, _pin('admission.synthetic.'+wave.wave_id, wave_bindings.ScheduledProgrammeWaveAdmission.SCHEMA), programme.mode)
        config_pub = _publish(plane, config, config.config_id)

        def task(task_id, role, *, collector=False):
            factory = factories[owner.NAMESPACE+'.'+role]
            m, registration = factory.manifest, factory.registration
            config_ref = (CapabilityConfigRef(config.config_id, config.SCHEMA, m.config_schema_sha256, config.fingerprint(),
                config_pub.logical.logical_artifact_id) if collector else CapabilityConfigRef('config.'+task_id,
                registration.config_record_type.SCHEMA, m.config_schema_sha256, sha256(task_id.encode()).hexdigest(), 'config.'+task_id))
            req = CapabilityRequirement(m.capability_key, m.capability_version, m.kind, config_ref,
                m.input_schema_ids, m.output_schema_ids, m.permissions, m.maximum_evidence_ceiling,
                m.maximum_outcome_access, m.resource_ceiling)
            if collector:
                external = (ExternalInputSpec('config-source.'+wave.wave_id, config_pub.logical.logical_artifact_id,
                    config.fingerprint(), config.SCHEMA, 'application/json', len(config.canonical_bytes()),
                    Visibility.PROSPECTIVE, Access.OUTCOME_BLIND, None),)
                deps = tuple(sorted((*headers, wave.wave_id+'.open')))
                scientific = tuple(ScientificInputSpec('edge.synthetic.'+producer, 'input.synthetic.'+producer,
                    ScientificInputRole.OUTCOME, producer, producer+'.product', None,
                    'scientific.'+producer+'.product', 'scientific.'+producer+'.product',
                    next(t.outputs[0].payload_schema for t in tasks if t.task_id == producer), 'application/json',
                    owner.MAXIMUM_CALIBRATION_BYTES, Access.OUTCOME_BLIND, Visibility.PROSPECTIVE, BarrierKind.NONE)
                    for producer in deps)
                p = result_publication
                outputs = (ArtifactOutputSpec(task_id+'.product', p.logical.logical_artifact_id,
                    p.materialization.relative_path, p.logical.payload_schema, p.logical.profile, p.logical.media_type,
                    p.logical.visibility_ceiling, (), p.logical.outcome_access),)
            else:
                external, deps, scientific = (), (), ()
                outputs = (ArtifactOutputSpec(task_id+'.product', 'scientific.'+task_id+'.product',
                    'software/'+task_id+'.json', registration.outputs[0].payload_schema,
                    ArtifactProfile.CANONICAL_JSON, 'application/json', Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND),)
            return ExecutionTask(task_id, registration.stage, req, m.implementation_sha256, deps, external,
                outputs, (), registration.barrier, 1, ('obligation.synthetic.'+task_id,), scientific_inputs=scientific)

        tasks.append(task(wave.wave_id+'.open', 'open'))
        for task_id in sorted(headers):
            tasks.append(task(task_id, task_id.rsplit('.', 1)[-1]))
        collector = task(wave.wave_id+'.collect', 'collect', collector=True)
        tasks.append(collector)
        plan = CandidateExecutionPlan('plan.synthetic.'+wave.wave_id, PlanLane.PROSPECTIVE,
            _pin('run-plan.synthetic.'+wave.wave_id, 'empirical-lawhood/runtime/candidate-run-plan'), '2'*64, 'd'*40,
            tuple(sorted(tasks, key=lambda t: t.task_id)), True,
            candidate=_pin('candidate.synthetic.'+wave.wave_id, 'empirical-lawhood/planning/draft-study-candidate'))
        inputs = tuple(sorted((config_pub.materialization.materialization_id,
            *(r.output_materialization_ids[0] for r in headers.values()))))
        receipt = CanonicalTaskReceipt('receipt.synthetic.'+wave.wave_id+'.collect', 'run.synthetic.'+wave.wave_id,
            collector.task_id, 'attempt.synthetic.'+wave.wave_id, plan.implementation_commit, inputs,
            (result_publication.materialization,), (result_publication.logical,),
            (ReceiptCheck('scheduled-original-source-cutoff-census', True, ()),), OperationalStatus.SUCCEEDED, ())
        binding = owner.ScheduledProgrammeWaveCustody('custody.synthetic.'+wave.wave_id, wave.wave_id, result.identity,
            result_publication, receipt, _publish(plane, receipt, receipt.receipt_id),
            ObjectIdentity.from_record(plan.execution_plan_id, plan), _publish(plane, plan, plan.execution_plan_id),
            config, config_pub, collector)
        results.append(result)
        custody.append(binding)
        plans.append(plan)
    return tuple(results), tuple(custody), tuple(plans)


@pytest.fixture(scope='module')
def completed(declared, tmp_path_factory):
    programme, cases = declared
    criterion = ScheduledCalibrationCriterion('synthetic.calibration-criterion', 'unit.synthetic.whole-group', 64,
        Decimal(0), tuple(sorted({c.family_id for c in programme.cases})),
        'COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY')
    programme = replace(programme, calibration_criterion=criterion.identity)
    plane = _plane(tmp_path_factory.mktemp('programme-global-calibration')/'selected')
    results, custody, plans = stored_wave_custody(plane, programme, cases)
    config = owner.ScheduledProgrammeCalibrationConfig('config.'+owner.NAMESPACE+'.calibrate', 'calibrate',
        programme, programme.bank, 'calibration.synthetic.global64', tuple(c.identity for c in custody))
    reduced = reduction.reduce_programme(programme, results, reduction_id=config.calibration_id+'.global-reduction',
        authenticate_wave=lambda result: None)
    model = _pin('model.synthetic', 'empirical-lawhood/matrix-response-error-prediction/model')
    # Use the unchanged scientific model schema, even in this declared fixture.
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import MatrixResponseErrorModel
    model = replace(model, object_schema=MatrixResponseErrorModel.SCHEMA)
    semantic = owner.semantic_calibration(programme, reduced, calibration_id=config.calibration_id,
        model=model, independent_unit_id='unit.synthetic.whole-group')
    evidence = owner.ScheduledProgrammeCalibrationEvidence(config.calibration_id+'.programme-evidence', config, reduced,
        semantic, custody)
    return plane, config, results, custody, plans, semantic, evidence


def test_global_semantics_and_closed_evidence_preserve_actual_receipt_ids_rank62_max135(completed):
    plane, config, results, custody, plans, semantic, evidence = completed
    assert len(semantic.cases) == 576 and len(semantic.group_ids) == 64
    assert evidence.reduction.order_statistic_rank == 62 and evidence.reduction.radius == Decimal('62.08')
    assert semantic.scores[0][1] == Decimal('1.08')
    assert semantic.cases[0].score_receipt_id == 'receipt.synthetic.'+owner.COMPACT_NAMESPACE+'.'+semantic.cases[0].root_id+'.response-score'
    assert semantic.cases[0].score_materialization_id == 'materialization.synthetic.'+owner.COMPACT_NAMESPACE+'.'+semantic.cases[0].root_id+'.response-score'
    assert evidence.reduction.qualification_disposition == 'UNENTERED'
    assert len(evidence.canonical_bytes()) <= owner.MAXIMUM_CALIBRATION_BYTES
    assert decode_canonical_bytes(evidence.canonical_bytes(), owner.ScheduledProgrammeCalibrationEvidence,
        maximum_bytes=owner.MAXIMUM_CALIBRATION_BYTES) == evidence
    for result, binding, plan in zip(results, custody, plans, strict=True):
        assert owner.validate_wave_custody(config.programme, result, binding, plan) == result
    assert owner.authenticate_wave_custody(plane, custody[0]) == (results[0], plans[0])


def test_constructor_and_guarded_authentication_refuse_changed_scope_and_actual_bytes(completed):
    plane, config, results, custody, plans, semantic, evidence = completed
    with pytest.raises(ValueError, match='global64'):
        replace(config, wave_custody=config.wave_custody[:-1])
    with pytest.raises(ValueError, match='wave census'):
        replace(evidence, wave_custody=evidence.wave_custody[::-1])
    with pytest.raises(ValueError, match='wave bytes'):
        replace(evidence, calibration=replace(semantic, criterion=replace(semantic.criterion, object_fingerprint='f'*64)))
    with pytest.raises(ValueError, match='summary/census'):
        owner.validate_wave_custody(config.programme, results[1], custody[0], plans[0])
    original = plane.root.resolve(custody[0].publication.materialization.relative_path, for_write=False)
    raw = original.read_bytes()
    original.write_bytes(raw+b' ')
    try:
        with pytest.raises((ValueError, ArtifactPlaneError), match='byte|hash|size'):
            owner.authenticate_wave_custody(plane, custody[0])
    finally:
        original.write_bytes(raw)


def test_global_factory_discovery_has_two_actual_outputs_and_one_reveal(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail('global calibration static discovery entered numerical science')
    monkeypatch.setattr(np.random, 'Generator', blocked)
    monkeypatch.setattr(np.linalg, 'eigh', blocked)
    calibrate, qualify = bindings.calibration_factories()
    assert calibrate.manifest.capability_key == owner.NAMESPACE+'.calibrate'
    assert {o.output_id for o in calibrate.registration.outputs} == {'product', 'evidence'}
    assert qualify.registration.barrier is BarrierKind.REVEAL
    assert qualify.registration.adjudication_output_id == 'adjudication'
    assert all(not f.registration.native_effect for f in (calibrate, qualify))
    assert all(p.maximum_size_bytes == owner.MAXIMUM_CALIBRATION_BYTES for f in (calibrate, qualify) for p in f.registration.input_ports)


def test_numerical_negative_is_retained_in_secondary_evidence_without_rewriting_legacy_scalar(completed):
    plane, config, results, custody, plans, semantic, evidence = completed
    violated = replace(evidence.reduction.cases[0], numerical_disposition='VIOLATED', reason_codes=('synthetic-prefix-violated',))
    by_root = {c.root_id: c for c in (violated, *evidence.reduction.cases[1:])}
    changed_waves = tuple(replace(w, cases=tuple(by_root[c.root_id] for c in w.cases)) for w in results)
    negative = reduction.reduce_programme(config.programme, changed_waves, reduction_id='reduction.synthetic.negative',
        authenticate_wave=lambda result: None)
    assert negative.numerical_disposition == 'VIOLATED' and negative.group_scores[0][1] is None
    # The historical semantic record remains the exact literal finite response.
    literal = owner.semantic_calibration(config.programme, negative, calibration_id=config.calibration_id,
        model=semantic.model, independent_unit_id=semantic.independent_unit_id)
    assert literal == semantic
    criterion = ScheduledCalibrationCriterion('synthetic.calibration-criterion', semantic.independent_unit_id, 64, Decimal(0),
        semantic.family_ids, 'COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY')
    assert owner.construction_supported(evidence, criterion)
    changed_unit = replace(semantic, independent_unit_id='unit.synthetic.foreign')
    changed_unit_evidence = replace(evidence, calibration=changed_unit)
    assert not owner.construction_supported(changed_unit_evidence, criterion)
    first = changed_waves[0]
    original = custody[0]
    pub = _publish(plane, first, 'scientific.synthetic.negative-wave.product', sealed=True)
    output = replace(original.producer_task.outputs[0], logical_artifact_id=pub.logical.logical_artifact_id,
        relative_path=pub.materialization.relative_path)
    task = replace(original.producer_task, outputs=(output,))
    plan = replace(plans[0], tasks=tuple(task if t.task_id == task.task_id else t for t in plans[0].tasks))
    receipt = replace(original.receipt, output_logical_artifacts=(pub.logical,), output_materializations=(pub.materialization,))
    changed_custody = replace(original, binding_id='custody.synthetic.negative-wave', result=first.identity,
        publication=pub, receipt=receipt, receipt_publication=_publish(plane, receipt, 'receipt.synthetic.negative-wave'),
        producer_task=task, execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        execution_plan_publication=_publish(plane, plan, 'plan.synthetic.negative-wave'))
    changed_bindings = (changed_custody, *custody[1:])
    changed_config = replace(config, wave_custody=tuple(c.identity for c in changed_bindings))
    negative_evidence = owner.ScheduledProgrammeCalibrationEvidence('evidence.synthetic.negative', changed_config,
        negative, literal, changed_bindings)
    assert not owner.construction_supported(negative_evidence, criterion)
    with pytest.raises(ValueError, match='incomplete actual cases'):
        owner.semantic_calibration(config.programme, reduction.reduce_programme(config.programme,
            tuple(replace(w, cases=tuple(reduction.ScheduledProgrammeCaseResult.unentered(c)
                for c in config.programme.cases if c.root_id in w.root_ids)) for w in results),
            reduction_id='reduction.synthetic.unentered', authenticate_wave=lambda result: None),
            calibration_id=config.calibration_id, model=semantic.model, independent_unit_id=semantic.independent_unit_id)
    context = SimpleNamespace(scientific_adjudication_context=None)
    with pytest.raises(ValueError):
        bindings.make_adjudication(context, replace(config, config_id='config.'+owner.NAMESPACE+'.calibration-qualify',
            operation='calibration-qualify'), semantic, evidence, SimpleNamespace())
