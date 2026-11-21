# SPDX-License-Identifier: MPL-2.0
"""Independent algebraic SCI01 controls; these fixtures are not scientific evidence."""

from dataclasses import replace
from decimal import Decimal as D
from itertools import product
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_read import affine_response, assess_refresh_case, verify_refresh_case
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_records import REFRESH_METHODS, REFRESH_RULE, MatrixRefreshCaseSource, MatrixRefreshMethodAssessment, MatrixRefreshProtocol
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_science import continue_response, evaluate_refresh_case, predict_refresh_case, receiver_matrix, refresh_case_summary, select_refresh_observations
from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_summary import finite_pair_operands, paired_endpoint_rows
from empirical_lawhood.domains.matrix.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
from empirical_lawhood.domains.matrix.matrix_factor_response.science import _block_modes, frame_axes, native_position_lift
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import hermitian_basis
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity


def case_source(index=0, group=0, coordinate=(D('.5'),) * 3, finite=True):
    pin = ObjectIdentity('test.original', 'empirical-lawhood/test/original', '1.0.0', '0' * 64)
    return MatrixRefreshCaseSource(index, f'root.{index}', f'group.{group}', *(pin,) * 6,
        'FINITE' if finite else 'NO_ORIGIN', finite, coordinate, ('panel.a', 'panel.b'))


@pytest.mark.parametrize('dt', (D('.001'), D('.0005')))
@pytest.mark.parametrize('friction', (D(0), D('2.7')))
def test_two_kicks_and_checkpoint_match_independent_affine_map_without_reset(dt, friction):
    origin = np.array([[2., .7], [.7, 9.]])
    refresh = np.array([[12., -.3], [-.3, 3.]])
    basis = np.eye(2)
    force = np.array([[.01, .02, -.03, .015], [.025, -.01, 0., .03]])
    mult = 1 if dt == D('.001') else 2
    frozen = continue_response(origin, basis, force, timestep=dt, friction=friction, native_horizon=128 * mult)
    actual = continue_response(origin, basis, force, timestep=dt, friction=friction,
        native_horizon=128 * mult, refresh_operator=refresh)
    expected = affine_response(origin, refresh, basis, force, timestep=dt, friction=friction)
    np.testing.assert_allclose(actual, expected, rtol=2e-14, atol=1e-18)
    np.testing.assert_array_equal(actual[:, :32 * mult + 1], frozen[:, :32 * mult + 1])
    assert np.linalg.norm(actual[:, 32 * mult]) > 0
    assert not np.array_equal(actual[:, 32 * mult + 1], frozen[:, 32 * mult + 1])
    # The first forced step includes the final force kick as well as the first.
    half = float(dt) / 2
    drift = half * (1 + np.exp(-float(dt * friction)))
    q = drift * half * force
    np.testing.assert_allclose(actual[:, 1, :2], q.T, rtol=1e-15)
    np.testing.assert_allclose(actual[:, 1, 2:], (drift * force - half * origin @ q).T, rtol=1e-15)


def test_frozen_span_retains_omitted_response_and_never_rebuilds_at_refresh():
    origin = np.diag([1., 2., 3.])
    refresh = np.array([[1., 0., 5.], [0., 2., 0.], [5., 0., 3.]])
    basis = np.eye(3)[:, :2]
    force = np.array([[.01] * 4, [.02] * 4, [.03] * 4])
    kwargs = dict(timestep=D('.001'), friction=D(1), native_horizon=128)
    fixed = continue_response(origin, basis, force, refresh_operator=refresh, **kwargs)
    frozen = continue_response(origin, basis, force, **kwargs)
    np.testing.assert_array_equal(fixed, frozen)  # Coupling outside the fixed span stays omitted.
    full = continue_response(origin, np.eye(3), force, refresh_operator=refresh, **kwargs)
    assert np.linalg.norm(full[:, -1, :2] - fixed[:, -1, :2]) > 1e-10


@pytest.fixture(scope='module')
def retained_case():
    from tests.test_matrix_causal_hessian import causal_case
    protocol, causal, frozen = causal_case()
    causal['frame'] = hermitian_basis(4)[4:7].copy()
    for index, role in enumerate(('FACTOR', 'TRACE', 'COMPLEMENT', 'GENERIC')):
        protocol.actions[index].role, protocol.actions[index].action_id = role, f'action.{index}'
    factor = _block_modes([frame_axes(causal['frame'])] * 6)
    forces = np.eye(96)[:, :4] * .01
    receiver = receiver_matrix(frozen['receivers'])
    received = {}
    for view, mult in (('primary', 1), ('fine', 2)):
        h0 = frozen[view + '_hessian']
        numerical = getattr(protocol.public_source.coordinate, view + '_view')
        paths = {}
        for name, basis in (('full_coupled', np.eye(96)), ('factor', factor)):
            states = affine_response(h0, h0, basis, forces, timestep=numerical.timestep, friction=numerical.friction_gamma)
            n = basis.shape[1]
            physical = np.concatenate((states[..., :n] @ basis.T, states[..., n:] @ basis.T), axis=-1)
            frozen[view + '_full_grid_' + name] = physical[:, mult::mult] @ receiver.T
            paths[name] = physical
        count = 128 * mult
        q0 = causal[view + '_positions'][-1]
        # A time-dependent shared baseline distinguishes evaluator information from the checkpoint.
        hold = q0[None] * np.linspace(1., 1.2, count + 1)[:, None, None, None, None]
        for panel in ('panel.a', 'panel.b'):
            for ai, action in enumerate(protocol.actions):
                phase = paths['full_coupled'][ai]
                for sign, coefficient in (('hold', 0), ('plus', 1), ('minus', -1)):
                    stem = f'branch.{view}.{panel}.{action.action_id}.{sign}.'
                    received[stem + 'positions'] = hold + coefficient * np.asarray([native_position_lift(v[:96]) for v in phase])
                    received[stem + 'momenta'] = coefficient * np.asarray([native_position_lift(v[96:]) for v in phase])
                    received[stem + 'ticks'] = np.arange(256 * mult, 256 * mult + count + 1)
                    received[stem + 'alpha_tilde'] = np.broadcast_to(causal[view + '_alpha_tilde'][-1], (count + 1, 2)).copy()
                    received[stem + 'innovations'] = np.zeros((count, 2, 3, 4, 4), dtype='<c16')
    source = case_source()
    observations = select_refresh_observations(protocol, received, panel_ids=source.panel_ids)
    predicted, _ = predict_refresh_case(protocol, causal, frozen, observations, panel_ids=source.panel_ids)
    arrays = evaluate_refresh_case(protocol, predicted, received, panel_ids=source.panel_ids)
    return protocol, causal, frozen, received, source, arrays


def test_complete_reader_reconstructs_states_vectors_and_decision_without_producer(retained_case, monkeypatch):
    protocol, causal, frozen, received, source, arrays = retained_case
    from empirical_lawhood.domains.matrix.matrix_factor_response import refresh_science
    monkeypatch.setattr(refresh_science, 'continue_response', lambda *a, **k: pytest.fail('reader called producer'))
    checks = verify_refresh_case(protocol, causal, frozen, received, arrays, source)
    assert checks and max(checks.values()) <= 1e-10
    independent = assess_refresh_case(source, arrays)
    assert independent.decision == refresh_case_summary(arrays, numerical_usable=True)['H64_method_decision']
    assert len(independent.methods) == 5


@pytest.mark.parametrize('key', ('primary.p0.state.full_refresh32', 'primary.p0.h32',
    'primary.p0.error.input_krylov48_refresh32', 'primary.p0.cross.input_krylov48_refresh32', 'forces'))
def test_independent_reader_refuses_changed_checkpoint_state_operator_error_or_force(retained_case, key):
    protocol, causal, frozen, received, source, arrays = retained_case
    changed = dict(arrays)
    changed[key] = arrays[key].copy()
    changed[key].flat[-1] += .05
    with pytest.raises(ValueError, match='SCI01'):
        verify_refresh_case(protocol, causal, frozen, received, changed, source)


def test_later_HOLD_cannot_change_checkpoint_prediction(retained_case):
    protocol, causal, frozen, received, source, arrays = retained_case
    later = dict(received)
    for key, value in received.items():
        if key.endswith('.positions'):
            mult = 2 if '.fine.' in key else 1
            later[key] = value.copy()
            later[key][32 * mult + 1:] *= 2
    observation = select_refresh_observations(protocol, later, panel_ids=source.panel_ids)
    predicted, _ = predict_refresh_case(protocol, causal, frozen, observation, panel_ids=source.panel_ids)
    for key in predicted:
        np.testing.assert_array_equal(predicted[key], arrays[key])


def test_horizon_gate_does_not_erase_h64_and_cumulative_error_never_resets():
    coarse = (D('.001'),) * 29
    fine = tuple(D('.001') if h <= 64 else D('.002') for h in DENSE_RESPONSE_HORIZONS)
    record = MatrixRefreshMethodAssessment('FULL_REFRESH32', coarse, fine, True)
    assert record.adequate(64) is True and record.adequate(128) is None
    with pytest.raises(ValueError, match='accumulated'):
        replace(record, primary_curve=(D('.005'),) + (D('.001'),) * 28)
    assert decode_canonical_bytes(REFRESH_RULE.canonical_bytes(), type(REFRESH_RULE), maximum_bytes=None) == REFRESH_RULE
    with pytest.raises(ValueError, match='fixed causal'):
        replace(REFRESH_RULE, checkpoint_primary_tick=33)


def test_original_census_preserves_missing_groups_and_nominal_receiver_rule():
    coords = (*product((D('.5'), D(2)), repeat=3), (D(1),) * 3)
    cases = tuple(case_source(9 * group + i, group, coordinate, group < 4)
                  for group in range(16) for i, coordinate in enumerate(coords))
    pin = cases[0].source
    protocol = MatrixRefreshProtocol(pin, pin, pin, 'test.run', cases, 'a' * 64)
    assert decode_canonical_bytes(protocol.canonical_bytes(), MatrixRefreshProtocol, maximum_bytes=None) == protocol
    with pytest.raises(ValueError, match='144/36/108'):
        replace(protocol, cases=cases[:-1])
    changed = (*cases[:8], replace(cases[8], temperature_friction_coupling=(D('.5'),) * 3), *cases[9:])
    with pytest.raises(ValueError, match='nominal receiver'):
        replace(protocol, cases=changed)


def test_original_array_retains_sealed_publication_and_exact_byte_join(tmp_path, monkeypatch):
    from empirical_lawhood.api import matrix_retained_refresh as api, matrix_full_factor_custody as custody
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.science.identity.references import ArtifactIdentity
    from tests.numerical_provenance_fixtures import numerical_plane
    plane = numerical_plane(tmp_path)
    raw = b'explicit software transport seam'
    (tmp_path / 'original.npz').write_bytes(raw)
    artifact = ArtifactIdentity('test.arrays', 'arrays', 'empirical-lawhood/kernel/matrix-array-bundle',
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    operand = SimpleNamespace(array_artifact=artifact, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
    publication = SimpleNamespace(logical=SimpleNamespace(logical_artifact_id=artifact.artifact_id,
        payload_schema=artifact.payload_schema, content_sha256=artifact.sha256,
        outcome_access=OutcomeAccess.EVALUATION_SEALED, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY),
        materialization=SimpleNamespace(size_bytes=len(raw), relative_path='original.npz'))
    current = []
    context = {'writer': plane, 'products': {}, 'plan': None,
        'original_input_access': SimpleNamespace(require_current=lambda: current.append(True))}
    monkeypatch.setattr(custody, '_output', lambda *args, **kwargs: (None, publication))
    def decode(body, selected):
        assert body == raw and selected is operand
        return 'disclosed-decoded-arrays'
    monkeypatch.setattr(api, 'decode_matrix_arrays', decode)
    assert api._arrays(context, case_source(), 'project', operand, (), {}) == 'disclosed-decoded-arrays'
    assert len(current) == 2
    assert publication.logical.outcome_access is OutcomeAccess.EVALUATION_SEALED
    publication.logical.content_sha256 = 'f' * 64
    with pytest.raises(PermissionError, match='array producer'):
        api._arrays(context, case_source(), 'project', operand, (), {})


def test_publication_and_independent_read_keep_complete_mixed_software_census(tmp_path, monkeypatch, retained_case):
    """Exercise real transport/publication; only original custody is an exposed seam."""
    from empirical_lawhood.api import matrix_retained_refresh as api
    from empirical_lawhood.domains.matrix.matrix_factor_response import refresh_science as science
    from empirical_lawhood.storage.retained_analysis import read_retained_analysis
    from tests.numerical_provenance_fixtures import numerical_plane

    project = Path(__file__).resolve().parents[1]
    plane = numerical_plane(tmp_path)
    coords = (*product((D('.5'), D(2)), repeat=3), (D(1),) * 3)
    cases = tuple(case_source(9 * group + i, group, coordinate, group < 4)
        for group in range(16) for i, coordinate in enumerate(coords))
    protocol = MatrixRefreshProtocol(cases[0].source, cases[0].source, cases[0].source,
        'test.run', cases, sha256((project / api.SPECIFICATION_PATH).read_bytes()).hexdigest())
    response_protocol, causal, frozen, received, _, arrays = retained_case
    selected = tuple((case, response_protocol, {phase: SimpleNamespace(arrays=None)
        for phase in ('project', 'mechanical', 'responses')}, {}) for case in cases)
    current_checks = []
    def original_read(directory, writer, consume):
        with writer.read_context() as reading:
            consume(writer=reading, original_input_access=SimpleNamespace(
                require_current=lambda: current_checks.append('current')),
                products={'terminal': None, 'receipts': {}, 'operational_census': {}, 'dispositions': ()},
                plan=SimpleNamespace(tasks=()), run_id='test.run')
        return {'scope': 'EXPOSED_SOFTWARE_ORIGINAL_READER_SEAM'}
    monkeypatch.setattr(api, '_original_read', original_read)
    monkeypatch.setattr(api, '_select_original', lambda context: (selected, (), {}))
    monkeypatch.setattr(api, '_protocol', lambda *args: protocol)
    monkeypatch.setattr(api, '_arrays', lambda context, binding, phase, *args:
        {'project': causal, 'mechanical': frozen, 'responses': received}[phase])
    output = tmp_path / 'artifacts' / 'calculation'
    attempted = []
    def predict(*args, **kwargs):
        read_retained_analysis(directory=output, artifact_writer=plane)
        attempted.append(True)
        if len(attempted) > 1:
            raise science.MechanismUnavailable('EXPOSED_UNAVAILABLE_CONSTRUCTION')
        return arrays, {'scope': 'EXPOSED_NUMERICAL_FIXTURE'}
    monkeypatch.setattr(science, 'predict_refresh_case', predict)
    result = api.run_matrix_retained_refresh(original_directory=tmp_path / 'disclosed-original',
        output_directory=output, project_root=project, artifact_writer=plane)
    calculation = Path(result['calculation_directory'])
    completion = read_retained_analysis(directory=calculation, artifact_writer=plane)
    assert len(attempted) == 36 and len(list(calculation.glob('case-*/summary.json'))) == 144
    assert sum(member.relative_path.endswith('/arrays.npz') for member in completion.members) == 1
    read = api.read_matrix_retained_refresh(original_directory=tmp_path / 'disclosed-original',
        calculation_directory=calculation, assessment_directory=tmp_path / 'artifacts' / 'assessment',
        project_root=project, artifact_writer=plane)
    counts = dict(read['decision_counts'])
    assert counts['NO_ORIGIN'] == 108 and counts['CONSTRUCTION_UNAVAILABLE'] == 35
    assert sum(counts.values()) == 144 and len(current_checks) > 144
    assert read['status'] == 'INDEPENDENT_ASSESSMENT_COMPLETE'
    # The prior protocol is independently authenticated, not reconstructed from the calculation.
    (output / 'specification.md').write_bytes(b'changed protocol')
    with pytest.raises(ValueError, match='member differs'):
        api.read_matrix_retained_refresh(original_directory=tmp_path / 'disclosed-original',
            calculation_directory=calculation, assessment_directory=tmp_path / 'artifacts' / 'refused',
            project_root=project, artifact_writer=plane)


def test_finite_difference_keeps_signed_endpoints_and_refuses_equal_label_different_force(retained_case):
    protocol, _, _, _, source, arrays = retained_case
    low = finite_pair_operands(protocol, source, arrays)
    high = finite_pair_operands(protocol, replace(source, case_index=1), arrays)
    nominal = finite_pair_operands(protocol, replace(source, case_index=8), arrays)
    rows = paired_endpoint_rows(low, high, nominal)
    assert len(rows) == 160 and all(r['status'] == 'MATCHED' for r in rows)
    assert all(r['difference_error'] == 0 for r in rows)
    assert any(r['endpoint_error_low'] > 0 for r in rows)
    for row in rows:
        np.testing.assert_array_equal(np.asarray(row['signed_endpoint_error_high']) - row['signed_endpoint_error_low'], row['signed_difference_error'])
    high['forces'][1, 0, 0, 0, 0] += .1
    rows = paired_endpoint_rows(low, high, nominal)
    assert rows[0]['status'] == 'INCOMPATIBLE_PHYSICAL_FORCE_OR_SCALE'
    assert len(rows) == 81


def test_each_method_keeps_its_own_numerical_gate():
    from empirical_lawhood.domains.matrix.matrix_factor_response.refresh_records import MatrixRefreshCaseAssessment
    methods = tuple(MatrixRefreshMethodAssessment(name, (D('.005'),) * 29, (D('.005'),) * 29, True)
                    for name in REFRESH_METHODS)
    case = MatrixRefreshCaseAssessment(case_source(), methods)
    assert case.decision == 'FROZEN_RESPONSE'
    # A failed structural comparator does not invalidate either full/input-aware comparison.
    methods = (*methods[:-1], replace(methods[-1], fine_curve=(D('.1'),) * 29))
    assert MatrixRefreshCaseAssessment(case_source(), methods).decision == 'FROZEN_RESPONSE'
    assert methods[-1].adequate(64) is None
    methods = (methods[0], replace(methods[1], fine_curve=(D('.1'),) * 29), *methods[2:])
    assert MatrixRefreshCaseAssessment(case_source(), methods).decision == 'FROZEN_RESPONSE'


def test_three_analysis_export_uses_closed_arrays_preserves_missingness_and_rechecks_access(tmp_path, monkeypatch, retained_case):
    """Actual custody/array routes with an explicitly disclosed original-reader seam."""
    import json
    from empirical_lawhood.api import matrix_retained_refresh as original, matrix_refresh_matched as matched
    from empirical_lawhood.domains.matrix.matrix_factor_response import refresh_science as science
    from empirical_lawhood.storage.retained_analysis import read_retained_analysis
    from tests.numerical_provenance_fixtures import numerical_plane

    project = Path(__file__).resolve().parents[1]
    plane = numerical_plane(tmp_path)
    coords = (*product((D('.5'), D(2)), repeat=3), (D(1),) * 3)
    cases = tuple(case_source(9 * group + i, group, coordinate, group < 4)
                  for group in range(16) for i, coordinate in enumerate(coords))
    pin = cases[0].source
    protocol = MatrixRefreshProtocol(pin, pin, pin, 'test.run', cases,
        sha256((project / original.SPECIFICATION_PATH).read_bytes()).hexdigest())
    response_protocol, causal, frozen, received, _, arrays = retained_case
    selected = tuple((case, response_protocol, {phase: SimpleNamespace(arrays=None)
        for phase in ('project', 'mechanical', 'responses')}, {}) for case in cases)
    current = []

    def original_read(directory, writer, consume):
        with writer.read_context() as reading:
            consume(writer=reading, original_input_access=SimpleNamespace(require_current=lambda: current.append(True)),
                products={'terminal': None, 'receipts': {}, 'operational_census': {}, 'dispositions': ()},
                plan=SimpleNamespace(tasks=()), run_id='test.run')
        return {'scope': 'EXPOSED_SOFTWARE_ORIGINAL_READER_SEAM'}

    for owner in (original, matched):
        monkeypatch.setattr(owner, '_original_read', original_read)
        monkeypatch.setattr(owner, '_select_original', lambda context: (selected, (), {}))
        monkeypatch.setattr(owner, '_protocol', lambda *args: protocol)
    monkeypatch.setattr(original, '_arrays', lambda context, binding, phase, *args:
        {'project': causal, 'mechanical': frozen, 'responses': received}[phase])
    attempts = []

    def predict(*args, **kwargs):
        index = len(attempts)
        attempts.append(index)
        if index not in (0, 1, 8):
            raise science.MechanismUnavailable('EXPOSED_UNAVAILABLE_CONSTRUCTION')
        return arrays, {'scope': 'EXPOSED_NUMERICAL_FIXTURE'}

    monkeypatch.setattr(science, 'predict_refresh_case', predict)
    output = tmp_path / 'artifacts' / 'source'
    original.run_matrix_retained_refresh(original_directory=tmp_path / 'original', output_directory=output,
                                         project_root=project, artifact_writer=plane)
    assessment = tmp_path / 'artifacts' / 'assessed'
    original.read_matrix_retained_refresh(original_directory=tmp_path / 'original', calculation_directory=output / 'calculation',
        assessment_directory=assessment, project_root=project, artifact_writer=plane)
    # New analysis must only consume already retained arrays; no producer or original raw trajectory path is permitted.
    monkeypatch.setattr(science, 'predict_refresh_case', lambda *a, **k: pytest.fail('built a prediction or basis'))
    monkeypatch.setattr(original, '_arrays', lambda *a, **k: pytest.fail('reopened a native trajectory'))
    before_access = len(current)
    result = matched.run_matrix_refresh_matched(original_directory=tmp_path / 'original', calculation_directory=output / 'calculation',
        assessment_directory=assessment, output_directory=tmp_path / 'artifacts' / 'matched', project_root=project, artifact_writer=plane)
    assert result['status'] == 'THREE_RETAINED_ANALYSES_COMPLETE'
    assert result['matched_cells'] == 64 and result['unavailable_pairs'] == 63
    assert len(current) > before_access + 144
    destination = Path(result['analysis_directory'])
    completion = read_retained_analysis(directory=destination, artifact_writer=plane)
    assert sum(m.relative_path.endswith('arrays.npz') for m in completion.members) == 3
    summary = json.loads((destination / 'summary.json').read_bytes())
    assert summary['assigned_cases'] == 144 and summary['NO_ORIGIN'] == 108
    assert summary['usable_pairs'] == 1 and summary['unavailable_pairs'] == 63
    assert summary['maximum_normalized_state_reconstruction_residual'] < 1e-10
    assert summary['maximum_native_representation_join_residual'] < 1e-10
    assert len(json.loads((destination / 'representation.json').read_bytes())) == 192
    # A changed source member refuses before another output directory is created.
    (assessment / 'finite-pairs.json').write_text('[]')
    refused = tmp_path / 'artifacts' / 'refused'
    with pytest.raises(ValueError, match='member differs'):
        matched.run_matrix_refresh_matched(original_directory=tmp_path / 'original', calculation_directory=output / 'calculation',
            assessment_directory=assessment, output_directory=refused, project_root=project, artifact_writer=plane)
    assert not refused.exists()
