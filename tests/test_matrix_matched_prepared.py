# SPDX-License-Identifier: MPL-2.0
"""Supplied-noise prepared equations and actual frozen forecasts, without authority."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_forecast, prepared_point
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_response_science as response
from empirical_lawhood.adapters.methods.matrix_experimental_programme.functional_case_reduction import native_functional_case
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixIO48Construction, MatrixOriginResponseModel
from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, MatrixFactorAction
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledResponseArrays, ScheduledResponseProtocol, physical_forecast_implementation,
)
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays, DecodedMatrixArrayInput
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_functional_outcome_reduction import matched_criterion
from tests.test_matrix_prepared_point import available_prepared_operands
from tests.test_matrix_e4_matched_lifecycle import fitted, populations, observations, pin  # noqa: F401
from tests.test_matrix_matched_protected_e3 import original_case, matched_e3_products  # noqa: F401
from tests.test_matrix_selected_e3_e4_bridge import transfer  # noqa: F401


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    f = available_prepared_operands(tmp_path_factory.mktemp('matched-prepared'), future_ticks=160, origin_sector='Y')
    source = f.source
    pauli = np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype='<c16')
    templates = {'generic_basis': np.asarray([np.kron(row, np.eye(2)) / 2 for row in pauli], dtype='<c16'),
        'force_coefficients': np.stack((np.eye(3), np.eye(3))).astype('<f8') / np.sqrt(6),
        'trace_coefficients': np.ones((2, 3), dtype='<f8') / np.sqrt(6),
        'receiver_coefficients': np.eye(48, dtype='<f8').reshape(48, 2, 2, 3, 4)}
    template_raw, members = encode_matrix_arrays(templates)
    operand = ScheduledResponseArrays('templates.matched-prepared', 'TEMPLATES', source.original.source,
        ArtifactIdentity('array.matched-prepared-templates', 'templates', MATRIX_ARRAY_SCHEMA, sha256(template_raw).hexdigest(),
            'application/x-npz', len(template_raw)), members, (source.original.source,),
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    model = MatrixOriginResponseModel('model.matched-prepared', physical_forecast_implementation(),
        MatrixIO48Construction('io48.matched-prepared'))
    protocol = ScheduledResponseProtocol('protocol.matched-prepared', source.original, f.design.original_forecast.criterion, model,
        tuple(MatrixFactorAction('action.matched-prepared.' + role.lower(), role, D('.01'), 16, D(1)) for role in ACTION_ROLES),
        DENSE_RESPONSE_HORIZONS, 48, operand, D('1e-5'), D('1e-10'), D('1e-10'), D('1e-10'), D('1e-8'), D('1e-8'),
        D('1e-5'), D('1e-12'), D('1e-10'), 'PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME')
    mechanical_raw, mechanical = prepared_forecast.forecast(source, protocol, f.causal, f.causal_raw, template_raw,
        artifact_id='array.matched-prepared-mechanical')
    feature = prepared_point.matched_causal_feature(f.public, protocol, f.causal, f.witness, mechanical,
        f.causal_raw, f.diagnostic_raw, mechanical_raw, record_id='feature.matched-prepared')
    assert mechanical.disposition == feature.disposition == 'AVAILABLE'
    group = source.root.root.independent_group_id
    panels = (response.MatrixPreparedResponsePanel('panel.common', group, 'COMMON_NOISE_PANEL', source.root.streams),
        response.MatrixPreparedResponsePanel('panel.independent', group, 'INDEPENDENT_FUTURE', tuple(MatrixHistorySeed(
            purpose, sha256(('literal-dense-' + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES)))
    innovations = {panel.panel_id: {key: np.zeros((steps, 2, 3, 4, 4), dtype='<c16')
        for key, steps in (('primary', 128), ('fine', 256), ('bridge', 128))} for panel in panels}
    operands = (source, f.initial, f.preparation, f.preparation_raw, protocol, panels, mechanical.arrays, mechanical_raw)
    arrays = response.propagate_prepared_responses(*operands, innovations)
    score = response.assess_prepared_responses(*operands, arrays, record_id='readout.matched-prepared')
    return SimpleNamespace(**vars(f), protocol=protocol, template_raw=template_raw, mechanical=mechanical,
        mechanical_raw=mechanical_raw, feature=feature, panels=panels, operands=operands, responses=arrays, score=score)


def test_dense_prepared_feature_mechanics_native_assay_and_cold_replay(native, monkeypatch):
    f = native
    assert f.feature.disposition == 'AVAILABLE' and dict(f.feature.values)['d_lin'] >= 0
    assert f.feature.fine_d_lin is not None
    assay = MatrixPreparedAssayMethod.from_protocol('assay.matched-prepared', f.protocol)
    assert assay.horizon_steps == DENSE_RESPONSE_HORIZONS
    assert f.score.numerical_pass and f.score.dense is not None
    assert len(f.score.cells) == 3248 and len(f.score.cumulative_log_errors) == 58
    assert len(f.score.controls) == 48 and len(f.score.dense.curves) == 14
    def forbidden(*_args, **_kwargs):
        pytest.fail('cold read entered a producer, fitter or eigensolver')
    monkeypatch.setattr(response, 'native_scheduled_branch', forbidden)
    monkeypatch.setattr(np.linalg, 'eigh', forbidden)
    monkeypatch.setattr(np.linalg, 'svd', forbidden)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast
    monkeypatch.setattr(response_forecast, '_hessian', forbidden)
    raw, mechanical = prepared_forecast.forecast(f.source, f.protocol, f.causal, f.causal_raw, f.template_raw,
        artifact_id=f.mechanical.arrays.array_artifact.artifact_id,
        retained_input=DecodedMatrixArrayInput(f.mechanical_raw, f.mechanical.arrays), raw=f.mechanical_raw)
    assert (raw, mechanical) == (f.mechanical_raw, f.mechanical)
    replay = response.assess_prepared_responses(*f.operands, f.responses, record_id=f.score.record_id)
    assert replay == f.score
    case = SimpleNamespace(case_id='case.' + f.source.source_id, unit_id=f.source.root.root.independent_group_id,
        arm_id='hold', preparation_effort=D(8))
    result = native_functional_case(matched_criterion(), case, f.source, replay, protocol=f.protocol, panels=f.panels)
    assert result.response_adequacy in (True, False, None) and not result.conditional_admission
    assert result.response_adequacy_meaning == 'SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK'
    assert decode_canonical_bytes(f.feature.canonical_bytes(), type(f.feature), maximum_bytes=None) == f.feature
    with pytest.raises(ValueError):
        prepared_point.matched_causal_feature(f.public, f.protocol, f.causal, f.witness, f.mechanical,
            f.causal_raw, f.diagnostic_raw[:-1], f.mechanical_raw, record_id='feature.damaged')
    with pytest.raises(ValueError, match='handoff'):
        prepared_point.matched_causal_feature(f.public, f.protocol, f.causal, replace(f.witness,
            record_id='witness.foreign'), f.mechanical, f.causal_raw, f.diagnostic_raw, f.mechanical_raw, record_id='feature.foreign')


def test_frozen_matched_handoff_retains_e3_references_vacuous_cal_and_native_adequacy(native, fitted, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as methods
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import RELATION_SCORE_RULE
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4PointModels, forecast_revision_prepared
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionSelectedPackage, MatrixRevisionPreparedProgramme
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import _case
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_secondary_readout import prepared_secondary_projection
    f, population = native, fitted.populations
    cal = population.calibration
    reduction, data, forecasts = observations(cal, population.calibration_bank, export=fitted.export, missing_groups=cal.group_ids[:1])
    spec = p.SelectedE4CalibrationSpecification('test.prepared.cal-spec', population.development.identity, cal.identity,
        fitted.nomination.identity, fitted.frozen.identity, D('.05'), RELATION_SCORE_RULE)
    calibrated = methods.calibrate_revision_public(spec, fitted.export, cal, population.calibration_bank,
        reduction, data, forecasts, record_id='test.prepared.calibration')
    calibration = p.SelectedE4PublicCalibration.from_calibration(calibrated, record_id='test.prepared.public-calibration')
    payload = SelectedE4PointModels.from_models(fitted.export.models, record_id='test.prepared.models')
    package = MatrixRevisionSelectedPackage('test.prepared.package', payload, pin('test.prepared.disclosed-nomination',
        methods.SelectedE4DownstreamNomination), calibrated.identity, calibration, population.development_bank.forecast_design.package)
    feature = prepared_point.matched_causal_feature(f.public, f.protocol, f.causal, f.witness, f.mechanical,
        f.causal_raw, f.diagnostic_raw, f.mechanical_raw, record_id='feature.matched-prepared.selected',
        curve_primary=payload.relation_fit.selection.is_curve_primary)
    monkeypatch.setattr(np.linalg, 'svd', lambda *_a, **_k: pytest.fail('prepared prediction refit the original accounts'))
    point = forecast_revision_prepared(payload, f.public, f.causal, nomination=package.nomination,
        original_calibration=calibrated.identity, record_id='test.prepared.point', feature=feature,
        calibration=calibration, reference_package=package.reference_package)
    assert point.disposition == 'PREDICTED' and len(point.revision_predictions) == 58
    assert tuple(method for method, _ in point.reference_points) == ('B0', 'S0')
    original = dict(package.reference_package.predict(values=feature.values, disposition=feature.disposition))
    assert all(values == original[method] for method, values in point.reference_points)
    assert all(policy.bound_kind == 'INFINITE' and policy.admissions == (False,) * 29 for policy in point.policies)
    assert decode_canonical_bytes(point.canonical_bytes(), type(point), maximum_bytes=None) == point
    case = SimpleNamespace(case_id='case.' + f.source.source_id, unit_id=f.source.root.root.independent_group_id,
        arm_id='hold', preparation_effort=D(8))
    programme = SimpleNamespace(criterion=matched_criterion(), selected_package=package,
        identity=pin('test.prepared.disclosed-programme', MatrixRevisionPreparedProgramme),
        panels=((case.unit_id, f.panels),), protocol=lambda _source: f.protocol,
        roster=SimpleNamespace(cases=(case,)), source_arms=lambda: (('hold', f.source),),
        arms=(('hold', f.source.recipe),), hold_arm_id='hold')
    assessment = _case(programme, case, f.source, (point, f.mechanical, f.score))
    assert assessment.reference_points == point.reference_points
    assert not assessment.functional.conditional_admission
    assert len(assessment.reference_duration_error_counts) == 2
    assert decode_canonical_bytes(assessment.canonical_bytes(), type(assessment), maximum_bytes=None) == assessment
    report = prepared_secondary_projection(programme, {case.case_id: (point, f.mechanical, f.score)}, (('declared', (case.unit_id,)),))
    assert report['external_delivered_task'] == 'NOT_SELECTED'
    assert {row['method'] for row in report['cases'][0]['prediction_losses']} == {'B0', 'S0', 'BR', 'SR', 'PHYSICAL', 'RELATION_BASE', 'RAW_DEV_MEDIAN'}
    missing = _case(programme, case, f.source, None)
    assert missing.functional.response_adequacy is None and all(value is None for _, value in missing.reference_duration_error_counts)
    pending = _case(programme, case, f.source, (point, f.mechanical, None))
    assert pending.functional.disposition == 'MISSING' and pending.readout is None
    assert pending.policies == point.policies and pending.reference_points == point.reference_points
    partial = prepared_secondary_projection(programme, {case.case_id: (point, f.mechanical, None)}, (('declared', (case.unit_id,)),))
    assert partial['cases'][0]['readout_disposition'] == 'MISSING'
    assert len(partial['admission_risks']) == 58
    assert all(row['assigned_units'] == 1 for row in partial['admission_risks'])
    assert all(summary['unavailable_groups'] == 1 for _, summary in partial['prediction_loss_summaries'][0]['absolute_duration_loss'])
    changed = replace(point, reference_points=tuple((method, (D('.2'),) * 58) for method, _ in point.reference_points))
    with pytest.raises(ValueError, match='substitutes fitted predictions'):
        _case(programme, case, f.source, (changed, f.mechanical, f.score))
    with pytest.raises(ValueError, match='handoff'):
        forecast_revision_prepared(payload, f.public, f.causal, nomination=package.nomination,
            original_calibration=calibrated.identity, record_id='test.prepared.foreign-feature',
            feature=replace(feature, source=replace(feature.source, object_fingerprint='f' * 64)),
            calibration=calibration, reference_package=package.reference_package)
    # Disclosed post-custody API seam: actual raw mathematical reproof, without
    # claiming that these placeholders establish receipts or current authority.
    from empirical_lawhood.api import matrix_selected_scientific_read as reader
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as bindings
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_future as future
    programme.phase = 'E6_TRANSFER'
    tasks = {future.node_id(f.source, phase): SimpleNamespace(task_id=future.node_id(f.source, phase), phase=phase,
        capability=SimpleNamespace(capability_key=bindings.capability_key(phase, 'PROTECTED', bindings.phase_version(phase)),
            capability_version=bindings.phase_version(phase))) for phase in ('point', 'response-score', 'responses', 'mechanical')}
    def configuration(_writer, _run, task, _kinds, **_kwargs):
        return SimpleNamespace(phase=task.phase, programme=programme.identity, public_source=f.public,
            selected_package=package.identity if task.phase == 'point' else package, source=f.source, protocol=f.protocol)
    monkeypatch.setattr(reader, '_configuration', configuration)
    monkeypatch.setattr(reader, '_consumed', lambda _w, _r, _t, _c, name, _k, **_kw:
        {'causal': f.causal, 'witness': f.witness, 'mechanical': f.mechanical}[name])
    monkeypatch.setattr(reader, '_consumed_array', lambda _w, _r, _t, _c, name, _o, **_kw:
        {'causal-arrays': f.causal_raw, 'diagnostic-arrays': f.diagnostic_raw, 'mechanical-arrays': f.mechanical_raw}[name])
    monkeypatch.setattr(reader, '_consumed_producer', lambda _t, _c, name, **_kw: tasks[future.node_id(f.source, 'mechanical')]
        if name.startswith('mechanical') else name)
    def external(_writer, _run, task, name, artifact, **_kwargs):
        assert task.phase == 'mechanical' and name == 'templates' and artifact == f.protocol.templates.array_artifact
        return f.template_raw
    monkeypatch.setattr(reader, '_external_array', external)
    receipts = {future.node_id(f.source, 'point'): object()}
    args = (None, 'run.disclosed', programme, f.source, (point, f.mechanical, None), tasks, receipts)
    reader._replay_matched_revision_case(*args, allow_missing_future=True)
    with pytest.raises(PermissionError, match='READOUT_CANNOT_BE_DROPPED'):
        reader._replay_matched_revision_case(*args)
    with pytest.raises(PermissionError, match='POINT_REPROOF_FAILED'):
        reader._replay_matched_revision_case(*args[:4], (changed, f.mechanical, None), *args[5:], allow_missing_future=True)
