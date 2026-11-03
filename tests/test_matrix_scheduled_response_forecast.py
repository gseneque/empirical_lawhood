# SPDX-License-Identifier: MPL-2.0
"""Exposed numerical forecast controls; no acquisition, fit or qualification.

The synthetic causal states are declared test operands, not authenticated
observations. Only the forecast producer is exercised. Cold controls prohibit
native derivatives, contact, acquisition, RNG and eigensolves.
"""

from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.records import (
    ACTION_ROLES, PREDICTORS, MatrixFactorAction, MatrixFactorResponseModel,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history import (
    forecast as public, records as r, response_forecast as f,
    response_records as rr, science,
)
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_factor_confirmation_eligibility import (
    provenance as source_provenance, publish, stock as source_stock,
)
from tests.test_matrix_scheduled_history import scheduled as scheduled_source, with_parents


def blocked(*args, **kwargs):
    raise AssertionError('forecast cold read entered native, acquisition, RNG or eigensolve')


def opaque(name, schema):
    return ObjectIdentity('exposed.forecast.' + name, schema, '1.0.0', 'a' * 64)


def pauli():
    return np.asarray(([[0, 1], [1, 0]], [[0, -1j], [1j, 0]], [[1, 0], [0, -1]]), dtype='<c16')


def causal_record(source, arrays, *, disposition='AVAILABLE'):
    _, operand = science._array_product(source, arrays, role='CAUSAL_STATE',
        artifact_id='exposed.forecast.causal-arrays', producers=(r.identity(source),),
        nonfinite=() if disposition == 'AVAILABLE' else ('frame',))
    return r.ScheduledCausalPrefix('exposed.forecast.causal', r.identity(source),
        opaque('history', r.ScheduledPrefixHistory.SCHEMA),
        opaque('numerical', r.ScheduledNumericalAssessment.SCHEMA),
        opaque('witness', r.ScheduledPrefixWitness.SCHEMA),
        opaque('assessment', r.ScheduledFrameAssessment.SCHEMA), r.identity(source.policy),
        source.root.root, source.policy.cutoff_tick,
        sha256(arrays['frame'].tobytes()).hexdigest() if disposition == 'AVAILABLE' else None,
        disposition, None if disposition == 'AVAILABLE' else 'EXPOSED_SOFTWARE_NONUSE', operand)


@pytest.fixture(scope='module')
def case(tmp_path_factory):
    # Reuse only the existing source-record/publication fixture. No prefix
    # acquisition or alleged qualification occurs in this test owner.
    stock = source_stock.__wrapped__(tmp_path_factory.mktemp('scheduled-forecast'), source_provenance.__wrapped__())
    plane, sources = scheduled_source.__wrapped__(stock)
    old = sources[0]
    policy = replace(old.policy, origin_sector='Y')
    selection = replace(old.specification.selection, prefix_policies=(policy,),
        coordinate_policies=tuple((co, r.identity(policy)) for co, _ in old.specification.selection.coordinate_policies))
    specification = replace(old.specification, selection=selection,
        publication=publish(plane, selection, 'exposed.forecast.selection'))
    source = with_parents(old, specification=specification)
    view = public.ScheduledPublicSource.from_source(source)
    frame = np.asarray([np.kron(p, np.eye(2)) / 2 for p in pauli()], dtype='<c16')
    complement = np.asarray([np.kron(np.eye(2), p) / 2 for p in pauli()], dtype='<c16')
    templates = dict(generic_basis=complement,
        force_coefficients=np.stack((np.eye(3), np.eye(3))).astype('<f8') / np.sqrt(6),
        trace_coefficients=np.ones((2, 3), dtype='<f8') / np.sqrt(6),
        receiver_coefficients=np.eye(48, dtype='<f8').reshape(48, 2, 2, 3, 4))
    raw, members = encode_matrix_arrays(templates)
    instrument = rr.ScheduledResponseArrays('exposed.forecast.templates', 'TEMPLATES', view.source,
        ArtifactIdentity('exposed.forecast.instrument', 'exposed-software-instrument', MATRIX_ARRAY_SCHEMA,
            sha256(raw).hexdigest(), 'application/x-npz', len(raw)), members, (view.source,),
        Access.OUTCOME_BLIND, Visibility.PROSPECTIVE)
    model = MatrixFactorResponseModel('exposed.forecast.mechanical-model', rr.physical_forecast_implementation())
    protocol = rr.ScheduledResponseProtocol(protocol_id='exposed.forecast.protocol', public_source=view,
        criterion=opaque('criterion', 'empirical-lawhood/tests/toy-forecast-target'), mechanical_model=model,
        actions=tuple(MatrixFactorAction('exposed.forecast.action.' + role.lower(), role, D('.01'), 1, D(1)) for role in ACTION_ROLES),
        horizon_steps=(1, 2), receiver_count=48, templates=instrument,
        hessian_difference_step=D('.00001'), generic_gap_minimum=D('1e-10'),
        spectral_gap_minimum=D('1e-10'), radial_norm_minimum=D('1e-10'),
        complement_gram_minimum=D('1e-8'), native_reference_tolerance=D('1e-8'),
        hessian_reference_tolerance=D('1e-5'), weak_response_minimum=D('1e-12'),
        receiver_gram_tolerance=D('1e-10'),
        origin_rule='PRESERVED_DISTINCT_PRIMARY_FINE_CUTOFF_STATES_ORIGIN_FIXED_PRIMARY_Y_FRAME')
    arrays = {'frame': frame}
    for name, multiplier in (('primary', 1), ('fine', 2)):
        ticks = np.arange(multiplier * policy.cutoff_tick + 1, dtype='<i8')
        # Complete distinct Hermitian view states, with a nondegenerate native
        # spectrum. Their construction is deterministic and uses no RNG.
        phase = np.asarray([np.diag([.1, .3, .7, 1.1]) + .03*j*np.eye(4)
            + .01*(j+1)*frame[j % 3] for j in range(6)], dtype='<c16').reshape(2, 3, 4, 4)
        phase += (multiplier - 1) * .002 * np.eye(4)
        arrays[name + '_positions'] = np.repeat(phase[None], len(ticks), axis=0)
        arrays[name + '_momenta'] = np.repeat((.01*phase)[None], len(ticks), axis=0)
        arrays[name + '_ticks'] = ticks
        arrays[name + '_alpha_tilde'] = np.asarray([source.coordinate.couplings(int(t), refinement=multiplier) for t in ticks], dtype='<f8')
    causal = causal_record(source, arrays)
    result_raw, result = f.forecast(protocol, causal, arrays, templates, artifact_id='exposed.forecast.result')
    values = decode_matrix_arrays(result_raw, result.arrays)
    return SimpleNamespace(source=source, protocol=protocol, causal=causal, arrays=arrays,
        templates=templates, raw=result_raw, result=result, retained=values)


def block_cold(monkeypatch):
    import scipy.linalg
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_derivatives, parameter_history_segments, parameter_source
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    for owner, names in ((f, ('_hessian',)), (parameter_derivatives, ('hessian_image',)),
        (parameter_history_segments, ('acquire_parameter_segment',)), (parameter_source, ('acquire_parameter_history',)),
        (ExternalNativeEffectContactStore, ('begin',)), (ExternalNativeSubworkStore, ('begin', 'contact')),
        (np.random, ('Generator', 'PCG64', 'PCG64DXSM', 'default_rng')),
        (np.linalg, ('eigh', 'eigvalsh')), (scipy.linalg, ('eigh', 'eigvalsh'))):
        for name in names:
            monkeypatch.setattr(owner, name, blocked)


def test_actual_forecast_and_cold_exact_witnesses_keep_distinct_views(case, monkeypatch):
    assert case.result.disposition == 'AVAILABLE'
    assert tuple((v, p) for v, p, _, _ in case.result.dispositions) == tuple((v, p) for v in ('PRIMARY', 'FINE') for p in PREDICTORS)
    assert not np.array_equal(case.arrays['primary_positions'][-1], case.arrays['fine_positions'][-1])
    assert case.retained['primary_hessian'].shape == case.retained['fine_hessian'].shape == (96, 96)
    assert case.retained['primary_position_eigenvectors'].shape == (6, 4, 4)
    assert case.retained['fine_hessian_eigenvectors'].shape == (96, 96)
    assert not np.array_equal(case.retained['primary_full_coupled'], case.retained['fine_full_coupled'])
    block_cold(monkeypatch)
    assert f.forecast(case.protocol, case.causal, case.arrays, case.templates,
        artifact_id='exposed.forecast.result', retained=case.retained, raw=case.raw) == (case.raw, case.result)


@pytest.mark.parametrize('defect', ('mutual-hessian-spectrum', 'forces', 'receivers',
    'missing-eigenpair', 'position-eigenpair', 'complement-eigenpair', 'prediction'))
def test_cold_forecast_refuses_changed_complete_witnesses(case, monkeypatch, defect):
    changed = {n: a.copy() for n, a in case.retained.items()}
    if defect == 'mutual-hessian-spectrum':
        changed['primary_hessian'] += np.eye(96)
        changed['primary_hessian_spectrum'] += 1
    elif defect == 'missing-eigenpair':
        del changed['fine_hessian_eigenvectors']
    elif defect == 'position-eigenpair':
        changed['primary_position_eigenvectors'][0, 0, 0] += .1
    elif defect == 'complement-eigenpair':
        changed['complement_eigenvectors'][0, 0] += .1
    else:
        changed[{'forces': 'forces', 'receivers': 'receivers', 'prediction': 'primary_full_coupled'}[defect]].flat[0] += .1
    block_cold(monkeypatch)
    with pytest.raises((ValueError, KeyError)):
        f.forecast(case.protocol, case.causal, case.arrays, case.templates,
            artifact_id='exposed.forecast.result', retained=changed, raw=case.raw)


@pytest.mark.parametrize('defect', ('cutoff', 'schedule', 'fine-clock', 'frame', 'policy'))
def test_public_causal_substitution_refuses_before_derivatives(case, monkeypatch, defect):
    causal = case.causal
    changed = {n: a.copy() for n, a in case.arrays.items()}
    if defect == 'cutoff':
        causal = replace(causal, cutoff_tick=causal.cutoff_tick - 1)
    elif defect == 'schedule':
        changed['primary_alpha_tilde'][-1, 0] += .1
    elif defect == 'fine-clock':
        changed['fine_ticks'][-1] -= 1
    elif defect == 'frame':
        changed['frame'][0, 0, 0] += .1
    else:
        causal = replace(causal, policy=opaque('foreign-policy', r.ScheduledPrefixPolicy.SCHEMA))
    block_cold(monkeypatch)
    with pytest.raises(ValueError):
        f.forecast(case.protocol, causal, changed, case.templates,
            artifact_id='exposed.forecast.result', retained=case.retained, raw=case.raw)


@pytest.mark.parametrize('disposition', ('NO_ORIGIN', 'UNEVALUABLE'))
def test_cold_nonuse_preserves_nan_predictions_without_model_failure(case, monkeypatch, disposition):
    arrays = {n: a.copy() for n, a in case.arrays.items()}
    arrays['frame'][:] = np.nan
    causal = causal_record(case.source, arrays, disposition=disposition)
    block_cold(monkeypatch)
    raw, result = f.forecast(case.protocol, causal, arrays, case.templates, artifact_id='exposed.forecast.nonuse')
    saved = decode_matrix_arrays(raw, result.arrays)
    assert result.disposition == disposition and len(result.dispositions) == 10
    assert all(s == 'UNRESOLVED' for _, _, s, _ in result.dispositions)
    assert all(np.isnan(a).all() for a in saved.values())
    assert f.forecast(case.protocol, causal, arrays, case.templates,
        artifact_id='exposed.forecast.nonuse', retained=saved, raw=raw) == (raw, result)


def test_unresolved_instrument_retains_eigenpairs_for_cold_parity(case, monkeypatch):
    protocol = replace(case.protocol, complement_gram_minimum=D(2))
    raw, result = f.forecast(protocol, case.causal, case.arrays, case.templates, artifact_id='exposed.forecast.unresolved')
    saved = decode_matrix_arrays(raw, result.arrays)
    assert result.disposition == 'INSTRUMENT_UNRESOLVED'
    assert {'complement_spectrum', 'complement_eigenvectors'} <= set(saved)
    assert len(result.dispositions) == 10 and all(s == 'UNRESOLVED' for _, _, s, _ in result.dispositions)
    block_cold(monkeypatch)
    assert f.forecast(protocol, case.causal, case.arrays, case.templates,
        artifact_id='exposed.forecast.unresolved', retained=saved, raw=raw) == (raw, result)


def test_degenerate_predictor_preserves_all_five_methods_and_cold_parity(case, monkeypatch):
    protocol = replace(case.protocol, spectral_gap_minimum=D(100))
    raw, result = f.forecast(protocol, case.causal, case.arrays, case.templates, artifact_id='exposed.forecast.degenerate')
    saved = decode_matrix_arrays(raw, result.arrays)
    assert result.disposition == 'AVAILABLE'
    assert len(result.dispositions) == 10
    assert all(s == 'UNRESOLVED' for _, p, s, _ in result.dispositions if p == 'SPECTRA')
    assert all(np.isnan(saved[v + '_spectra']).all() for v in ('primary', 'fine'))
    assert all(np.isfinite(saved[v + '_full_coupled']).all() for v in ('primary', 'fine'))
    block_cold(monkeypatch)
    assert f.forecast(protocol, case.causal, case.arrays, case.templates,
        artifact_id='exposed.forecast.degenerate', retained=saved, raw=raw) == (raw, result)


# Shared typed custody headers are disclosed software premises. Every branch,
# transition check, physical prediction and score below uses actual equations;
# these controls confer no observation, source or qualification authority.
from tests.test_matrix_selected_e3_e4_workers import (  # noqa: E402,F401
    e4_dense_case, selected_bridge, transfer,
)


def test_dense_forecast_uses_original_witnesses_and_keeps_three_sample_bytes(e4_dense_case, monkeypatch):  # noqa: F811
    c = e4_dense_case
    original_raw, original_bytes = c.original_forecast_raw, c.original_physical.canonical_bytes()
    original = decode_matrix_arrays(original_raw, c.original_physical.arrays)
    dense = decode_matrix_arrays(c.dense_forecast_raw, c.dense_physical.arrays)
    indices = tuple(c.f.secondary_target.observation_horizons.index(horizon) for horizon in c.protocol.horizon_steps)
    expected = {view + '_' + predictor.lower() for view in ('primary', 'fine') for predictor in PREDICTORS}
    assert set(dense) == expected
    assert all(value.shape == (4, 29, 48) for value in dense.values())
    for name, value in dense.items():
        assert value[:, indices, :].tobytes() == original[name].tobytes()
    # Witnesses stay solely in the original archive; cold E4 replay may not
    # calculate a new Hessian, eigensolve, native effect or random draw.
    assert {'primary_hessian', 'fine_hessian', 'complement_eigenvectors'} <= set(original)
    assert {'primary_hessian', 'fine_hessian', 'complement_eigenvectors'}.isdisjoint(dense)
    block_cold(monkeypatch)
    assert f.forecast_e4_dense(c.protocol, c.causal, c.causal_arrays, c.templates,
        target=c.f.secondary_target, secondary=c.f.secondary_readout,
        original_physical=c.original_physical, original_forecast_raw=original_raw,
        artifact_id=c.dense_physical.arrays.array_artifact.artifact_id,
        forecast_id=c.dense_physical.forecast_id, retained=dense, raw=c.dense_forecast_raw) == (
            c.dense_forecast_raw, c.dense_physical)
    assert c.original_forecast_raw == original_raw and c.original_physical.canonical_bytes() == original_bytes
    coordinate = c.source.coordinate
    for step in c.f.secondary_target.observation_horizons:
        assert coordinate.primary_view.timestep * step == coordinate.fine_view.timestep * (2 * step)


def test_amended_seven_method_forecast_seals_all_horizons_and_independent_io_witnesses(e4_dense_case, monkeypatch):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import (
        MatrixIO48Construction, MatrixOriginResponseModel, ORIGIN_RESPONSE_PREDICTORS,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_science import validate_frozen_response_arrays
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_science
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_science import mechanical
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as utility
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_science as utility_science
    from empirical_lawhood.kernel.experimental_design import UnitAllocation

    c = e4_dense_case
    mathematical = replace(c.f.bank.forecast_design.criterion_record,
        protocol_id='exposed.amended.mathematical-protocol', horizon_steps=DENSE_RESPONSE_HORIZONS)
    protocol = replace(c.protocol, protocol_id='exposed.amended.origin-protocol',
        mechanical_model=MatrixOriginResponseModel('exposed.amended.origin-model', rr.physical_forecast_implementation(),
            MatrixIO48Construction('exposed.amended.io48-construction')), horizon_steps=DENSE_RESPONSE_HORIZONS,
        criterion=mathematical.identity)
    assert decode_canonical_bytes(protocol.canonical_bytes(), rr.ScheduledResponseProtocol, maximum_bytes=None) == protocol
    raw, result = mechanical(protocol, c.causal, c.causal_arrays, c.templates, artifact_id='exposed.amended.origin-forecast')
    arrays = decode_matrix_arrays(raw, result.arrays)
    validate_frozen_response_arrays(protocol, arrays, disposition=result.disposition)
    assert f.frozen_member_layout(protocol, result.disposition, members=result.arrays.members) == {
        member.name: (member.dtype, member.shape) for member in result.arrays.members}
    assert tuple((v, p) for v, p, _, _ in result.dispositions) == tuple(
        (v, p) for v in ('PRIMARY', 'FINE') for p in ORIGIN_RESPONSE_PREDICTORS)
    for view, multiplier in (('primary', 1), ('fine', 2)):
        for name in ORIGIN_RESPONSE_PREDICTORS:
            assert arrays[view + '_' + name.lower()].shape == (4, 29, 48)
        assert not arrays[view + '_zero_response'].any()
        assert arrays[view + '_io48_status'].tolist() == [0]
        ranks = arrays[view + '_io48_ranks']
        assert 0 < ranks[-1] <= 48 and ranks[-1] == min(48, ranks[-2])
        assert np.isfinite(arrays[view + '_io48']).all()
        assert arrays[view + '_factor_memory_curve'].shape == (128 * multiplier,)
        assert arrays[view + '_factor_escape_return'].shape == (2,)
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_science import assess_paired_response_arrays
    responses = replace(c.responses, physical_forecast=ObjectIdentity.from_record(result.forecast_id, result),
        protocol=ObjectIdentity.from_record(protocol.protocol_id, protocol))
    observed = assess_paired_response_arrays(c.source, c.causal, c.prefix, c.prefix_arrays, result, arrays,
        protocol, c.panels, responses, c.received, error_forecast=responses.error_forecast, score_id='exposed.amended.score')
    assert observed.numerical_pass and len(observed.controls) == 48
    assert len(observed.cells) == 3248 and len(observed.cumulative_log_errors) == 58
    assert observed.dense.factor_log_targets == observed.cumulative_log_errors
    assert decode_canonical_bytes(observed.canonical_bytes(), rr.ScheduledResponseScore, maximum_bytes=None) == observed
    # Explicit opaque acquisition headers supply no sampling or custody claim.
    # The E2 reduction consumes the actual complete native numerical score.
    def pin(name, kind):
        return ObjectIdentity('exposed.amended.' + name, kind.SCHEMA, kind.VERSION, 'a' * 64)
    specification = utility.NativeUtilitySpecification('exposed.amended.e2', (c.source.root_id,),
        mathematical.identity, utility.NativeAmendedUtilityCriterion('exposed.amended.e2-criterion'))
    acquisition = utility.NativeUtilityAcquisitionSeal('exposed.amended.e2-seal', specification.identity,
        pin('request', utility.NativeUtilityRequest), pin('reservation', r.ScheduledReservation),
        pin('allocation', UnitAllocation), ((observed.root_id, observed.independent_group_id, observed.source),))
    utility_score = utility.NativeUtilityScore(**{field.name: acquisition.identity if field.name == 'acquisition_seal'
        else getattr(observed, field.name) for field in fields(utility.NativeUtilityScore)})
    outcome = utility_science.assess_score(specification, protocol, c.panels, acquisition, utility_score)
    expected_losses = {(view, predictor): max(cell.normalized_error for cell in observed.cells
        if cell.view == view and cell.predictor == predictor)
        for view in ('PRIMARY', 'FINE') for predictor in ('FACTOR', 'GENERIC_SLOW', 'IO48', 'SPECTRA')}
    view_agreement = all(abs(expected_losses['PRIMARY', predictor] - expected_losses['FINE', predictor]) <= D('.0001')
        for predictor in ('FACTOR', 'GENERIC_SLOW', 'IO48', 'SPECTRA'))
    structural = None if not view_agreement else all(expected_losses[view, predictor] - expected_losses[view, 'FACTOR'] > D('.001')
        for view in ('PRIMARY', 'FINE') for predictor in ('GENERIC_SLOW', 'IO48', 'SPECTRA'))
    assert outcome.amended.structural_advantage is structural
    assert outcome.amended.adequacy is all(cell.normalized_error <= D('.01') for cell in observed.cells
        if cell.predictor == 'FACTOR' and cell.horizon_tick <= 32)
    assert outcome.amended.zero_adequacy is all(cell.normalized_error <= D('.01') for cell in observed.cells
        if cell.predictor == 'ZERO_RESPONSE' and cell.horizon_tick <= 32)
    summary = utility_science.summarize(specification, acquisition, (outcome,))
    assert summary.amended.adequacy.events == (outcome.amended.adequacy,)
    assert summary.amended.structural_advantage.events == (structural,)
    assert decode_canonical_bytes(summary.canonical_bytes(), utility.NativeUtilitySummary, maximum_bytes=None) == summary
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import matched_e3_measurement
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import paired_response_view_values
    views, numerical = paired_response_view_values(SimpleNamespace(measurement=matched_e3_measurement()),
        c.source, protocol, c.panels, observed)
    assert numerical == 'SATISFIED' and tuple(view.view_id for view in views) == ('fine', 'primary')
    for view in views:
        assert view.errors == tuple(max(cell.normalized_error for cell in observed.cells
            if cell.view == view.view_id.upper() and cell.predictor == 'FACTOR' and cell.horizon_tick <= horizon)
            for horizon in DENSE_RESPONSE_HORIZONS)
    # The E4 dense products retain this already dense original score. These
    # publication headers are disclosed software operands, not fresh custody.
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import MatrixE4SecondaryReadoutSelection
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.paired_target_reduction import paired_targets
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_secondary_readout as readout
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as selected
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import MATCHED_METHODS
    from tests.test_matrix_selected_protected import unpublished
    target = replace(c.f.secondary_target, mathematical_protocol=mathematical)
    secondary = MatrixE4SecondaryReadoutSelection('exposed.amended.e4-secondary', mathematical.identity, target.identity,
        unpublished(target, 'exposed.amended.target-publication'))
    dense_raw, dense = f.forecast_e4_dense(protocol, c.causal, c.causal_arrays, c.templates,
        target=target, secondary=secondary, original_physical=result, original_forecast_raw=raw,
        artifact_id='exposed.amended.e4-projection-arrays', forecast_id='exposed.amended.e4-projection')
    projected = decode_matrix_arrays(dense_raw, dense.arrays)
    assert len(projected) == 14
    assert all(value.tobytes() == arrays[name].tobytes() for name, value in projected.items())
    dense_score = response_science.score_e4_dense(c.source, protocol, c.panels, target=target, secondary=secondary,
        original_score=observed, original_physical=result, dense_physical=dense, responses=responses,
        original_forecast_raw=raw, dense_forecast_raw=dense_raw, response_raw=c.response_raw,
        score_id='exposed.amended.e4-projection-score')
    assert dense_score.cells == observed.cells and paired_targets(observed, protocol, c.panels) == observed.cumulative_log_errors
    original_case = replace(selected.SelectedE3E4CaseResult.unentered(c.f.programme.cases[0], target_contract='MATCHED_FACTOR58'),
        forecast=observed.error_forecast, score=ObjectIdentity.from_record(observed.score_id, observed),
        paired_log_targets=observed.cumulative_log_errors,
        original_log_points=tuple((method, (D(0),) * 58) for method in MATCHED_METHODS))
    bank_view = SimpleNamespace(response_selection=SimpleNamespace(protocols=(protocol,),
        panels=((original_case.group_id, c.panels),)), forecast_design=SimpleNamespace(criterion_record=mathematical))
    row = readout.dense_e4_functional_rows(bank_view, original_case, observed, dense_score=dense_score, target=target, secondary=secondary)
    assert row.predictors == ORIGIN_RESPONSE_PREDICTORS and len(row.errors) == 406 and all(row.cumulative_complete)
    for view in ('PRIMARY', 'FINE'):
        offset = (('PRIMARY', 'FINE').index(view) * 7) * 29
        assert row.errors[offset:offset + 29] == tuple(max(cell.normalized_error for cell in observed.cells
            if cell.view == view and cell.predictor == 'FACTOR' and cell.horizon_tick <= horizon) for horizon in DENSE_RESPONSE_HORIZONS)
    for record in (dense, dense_score, original_case):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    block_cold(monkeypatch)
    monkeypatch.setattr(np.linalg, 'svd', blocked)
    assert utility_science.assess_score(specification, protocol, c.panels, acquisition, utility_score) == outcome
    assert assess_paired_response_arrays(c.source, c.causal, c.prefix, c.prefix_arrays, result, arrays,
        protocol, c.panels, responses, c.received, error_forecast=responses.error_forecast, score_id=observed.score_id) == observed
    assert mechanical(protocol, c.causal, c.causal_arrays, c.templates,
        artifact_id=result.arrays.array_artifact.artifact_id, retained=arrays, raw=raw) == (raw, result)
    changed = {name: value.copy() for name, value in arrays.items()}
    changed['fine_io48_witness_gramian_c'][0, 0] += 1
    with pytest.raises(ValueError, match='reproof'):
        mechanical(protocol, c.causal, c.causal_arrays, c.templates,
            artifact_id=result.arrays.array_artifact.artifact_id, retained=changed)
    changed = {name: value for name, value in arrays.items() if name != 'primary_zero_response'}
    with pytest.raises(ValueError, match='complete frozen prediction geometry'):
        validate_frozen_response_arrays(protocol, changed, disposition=result.disposition)
    absent, disposition, statuses = f.forecast_response_arrays(protocol, c.causal_arrays, c.templates, disposition='NO_ORIGIN')
    assert disposition == 'NO_ORIGIN' and len(statuses) == 14
    assert all(np.isnan(value).all() for value in absent.values())
    assert len(absent) == 28  # Sampled and full grids cannot invent an unavailable task.


def test_dense_finite_score_uses_all_actual_branches_and_independent_hs24_norms(e4_dense_case, monkeypatch):  # noqa: F811
    from decimal import localcontext

    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census

    c = e4_dense_case
    before = c.original_score.canonical_bytes()
    assert len(c.original_score.controls) == 48
    assert all(control.disposition == 'SATISFIED' for control in c.original_score.controls)
    assert sum(control.denominator_steps for control in c.original_score.controls) == 24 * (128 + 256)
    assert len(c.original_score.cells) == 240 and len(c.original_score.cumulative_log_errors) == 15
    assert len(branch_census(c.protocol, c.panels)) == 48
    frozen = decode_matrix_arrays(c.original_forecast_raw, c.original_physical.arrays)
    dense = decode_matrix_arrays(c.dense_forecast_raw, c.dense_physical.arrays)
    received = decode_matrix_arrays(c.response_raw, c.responses.arrays)
    assert len(received) == 6 + 48 * 5
    block_cold(monkeypatch)
    actual = response_science.score_e4_dense(c.source, c.protocol, c.panels,
        target=c.f.secondary_target, secondary=c.f.secondary_readout, original_score=c.original_score,
        original_physical=c.original_physical, dense_physical=c.dense_physical, responses=c.responses,
        original_forecast_raw=c.original_forecast_raw, dense_forecast_raw=c.dense_forecast_raw,
        response_raw=c.response_raw, score_id=c.dense_score.score_id)
    assert actual == c.dense_score and len(actual.cells) == len({cell.key for cell in actual.cells}) == 2320
    actions = {value.action_id: (index, value) for index, value in enumerate(c.protocol.actions)}
    seen = set()
    for cell in actual.cells:
        action_index, action = actions[cell.action_id]
        multiplier = 1 if cell.view == 'PRIMARY' else 2
        index = c.f.secondary_target.observation_horizons.index(cell.horizon_tick)
        label = cell.view.lower()
        stem = label + '.' + cell.panel_id + '.' + cell.action_id
        odd = np.stack(tuple((received['branch.' + stem + '.plus.' + phase][multiplier * cell.horizon_tick]
            - received['branch.' + stem + '.minus.' + phase][multiplier * cell.horizon_tick]) / 2
            for phase in ('positions', 'momenta')))
        # Independent scalar HS contractions, rather than the producer's
        # einsum/truth cache or its stored scalar error fields.
        observed = np.asarray([np.vdot(receiver, odd).real for receiver in frozen['receivers']])
        predicted = dense[label + '_' + cell.predictor.lower()][action_index, index]
        if not np.isfinite(predicted).all():
            assert cell.position_error_norm is cell.momentum_error_norm is cell.normalized_error is None
            continue
        errors = predicted - observed
        position_norm, momentum_norm = np.linalg.norm(errors[:24]), np.linalg.norm(errors[24:])
        with localcontext() as context:
            context.prec = 60
            duration = c.protocol.public_source.coordinate.primary_view.timestep * cell.horizon_tick
            pulse = c.protocol.public_source.coordinate.primary_view.timestep * min(action.pulse_steps, cell.horizon_tick)
            impulse = action.amplitude * action.force_norm * pulse
            expected = max(position_norm / float(impulse * (duration - pulse / 2)), momentum_norm / float(impulse))
        assert float(cell.position_error_norm) == pytest.approx(position_norm, rel=1e-10, abs=1e-14)
        assert float(cell.momentum_error_norm) == pytest.approx(momentum_norm, rel=1e-10, abs=1e-14)
        assert float(cell.normalized_error) == pytest.approx(expected, rel=1e-9, abs=1e-12)
        seen.add((cell.view, cell.predictor))
    assert {('PRIMARY', 'FACTOR'), ('FINE', 'FACTOR')} <= seen
    by_key = {cell.key: cell for cell in actual.cells}
    for original_cell in c.original_score.cells:
        current = by_key[original_cell.key]
        assert current.normalized_error == original_cell.normalized_error
        if original_cell.signed_errors is not None:
            with localcontext() as context:
                context.prec = 60
                assert current.position_error_norm == sum(value * value for value in original_cell.signed_errors[:24]).sqrt()
                assert current.momentum_error_norm == sum(value * value for value in original_cell.signed_errors[24:]).sqrt()
    assert c.original_score.canonical_bytes() == before


@pytest.mark.parametrize('member', ('original_forecast', 'dense_forecast', 'response'))
def test_dense_score_refuses_changed_actual_archive_bytes(e4_dense_case, member):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_science

    c = e4_dense_case
    arguments = dict(original_forecast_raw=c.original_forecast_raw,
        dense_forecast_raw=c.dense_forecast_raw, response_raw=c.response_raw)
    raw = arguments[member + '_raw']
    arguments[member + '_raw'] = raw[:-1] + bytes((raw[-1] ^ 1,))
    with pytest.raises((ValueError, KeyError)):
        response_science.score_e4_dense(c.source, c.protocol, c.panels,
            target=c.f.secondary_target, secondary=c.f.secondary_readout, original_score=c.original_score,
            original_physical=c.original_physical, dense_physical=c.dense_physical, responses=c.responses,
            score_id=c.dense_score.score_id, **arguments)
