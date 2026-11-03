"""Exposed pure chart falsifiers; these tests create no native response source."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec, FactorRootRole
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import measure_trace
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.simulators.six_matrix_response.factor_bridge import (
    FactorBridge, FactorBridgeChart, decompose, factor_force, factor_frame_sha256,
    lift, momentum_kick, native_coordinates, norm_matched_complement_force,
    observe, readout, select_factor_bridge,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState, hermitian_part
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes


def artifact(name, raw):
    return ArtifactIdentity(name, 'development', 'empirical-lawhood/test/factor-bridge',
        sha256(raw).hexdigest(), 'application/octet-stream', len(raw))


def event_spec():
    return FactorEventSpec('test.bridge.rule', ('X', 'Y'), (0, 16, 32, 48),
        Decimal('.001'), 16, 16, Decimal('.01'), Decimal('.01'), Decimal('5'),
        Decimal('30'), Decimal('5'), Decimal('1e-10'), Decimal('1e-20'), Decimal('.1'))


def retained_trace(rule, *, positions=None):
    root = FactorRootRole('test.bridge.root', 'test.bridge.unit', 'test.bridge.family',
        ObjectIdentity('test.bridge.source', 'empirical-lawhood/test/source', '1.0.0', 'a'*64),
        artifact('test.bridge.native', b'native'), artifact('test.bridge.result', b'result'))
    if positions is None:
        positions = np.broadcast_to(np.stack((algebra.LEFT, algebra.RIGHT)), (49, 2, 3, 4, 4)).copy()
    record, arrays = measure_trace(rule, root, 'PRIMARY', 'Y', positions)
    raw, members = encode_matrix_arrays(arrays,
        nonfinite_members=('spectrum', 'projector', 'basis', 'factor', 'aligned_factor'))
    return replace(record, diagnostics=artifact('test.bridge.frames', raw), diagnostic_members=members), arrays


@pytest.fixture
def selected():
    rule = event_spec()
    trace, arrays = retained_trace(rule)
    frame = arrays['aligned_factor'][1]
    arguments = dict(chart_id='test.bridge.chart', spec=rule, trace=trace,
        origin_tick=16, cutoff=Decimal('.016'),
        clock=ObjectIdentity('test.bridge.clock', 'empirical-lawhood/test/clock', '1.0.0', 'b'*64),
        origin_native_step=16, frame=frame, expected_frame_sha256=factor_frame_sha256(frame))
    return select_factor_bridge(**arguments), arguments


def native_state(seed=904, step=16):
    rng = np.random.default_rng(seed)
    values = hermitian_part(rng.normal(size=(2, 2, 3, 4, 4)) + 1j*rng.normal(size=(2, 2, 3, 4, 4)))
    return SixMatrixState(2, values[0], values[1], step, 2/3, 22/3)


def phase(state):
    return np.stack((state.positions, state.momenta))


def test_adjoint_projection_and_complete_native_norm(selected):
    bridge, _ = selected
    state = native_state()
    coordinates, retained, complement = decompose(bridge, state, chart=bridge.chart.identity)
    test_coordinates = np.random.default_rng(992).normal(size=(2, 2, 3, 4))
    lifted = lift(bridge, test_coordinates, chart=bridge.chart.identity)
    assert coordinates.shape == (2, 2, 3, 4)
    assert native_coordinates(state).shape == (192,)
    np.testing.assert_allclose(np.vdot(coordinates, test_coordinates), np.vdot(phase(state), lifted).real, atol=1e-12)
    np.testing.assert_allclose(observe(bridge, SixMatrixState(2, retained[0], retained[1], 16, 2/3, 22/3),
        chart=bridge.chart.identity), coordinates, atol=1e-12)
    np.testing.assert_allclose(np.vdot(retained, complement).real, 0, atol=1e-12)
    np.testing.assert_allclose(retained + complement, phase(state), atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(native_coordinates(state)), np.linalg.norm(phase(state)), atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(coordinates)**2 + np.linalg.norm(complement)**2,
        np.linalg.norm(phase(state))**2, atol=1e-12)


def test_trace_order_normalization_and_no_omitted_sector(selected):
    bridge, _ = selected
    amplitudes = np.arange(1., 13.).reshape(2, 2, 3)
    values = amplitudes[..., None, None] * np.eye(4, dtype='<c16') / 2
    state = SixMatrixState(2, values[0], values[1], 16, 2/3, 22/3)
    coordinates, retained, complement = decompose(bridge, state, chart=bridge.chart.identity)
    np.testing.assert_allclose(coordinates[..., 0], amplitudes, atol=1e-12)
    np.testing.assert_allclose(coordinates[..., 1:], 0, atol=1e-12)
    np.testing.assert_allclose(retained, values, atol=1e-12)
    np.testing.assert_allclose(complement, 0, atol=1e-12)
    assert bridge.chart.retained_dimension == 36 + 12
    assert bridge.chart.native_dimension == 192
    assert bridge.chart.phase_order == ('POSITION', 'MOMENTUM')
    assert bridge.chart.sector_order == ('X', 'Y')
    assert bridge.chart.component_order == (0, 1, 2)
    assert bridge.chart.retained_memory == 'ORIGIN_ONLY'


def test_origin_fixed_unitary_covariance_of_observation_action_receiver(selected):
    bridge, _ = selected
    state = native_state()
    rng = np.random.default_rng(708)
    unitary, _ = np.linalg.qr(rng.normal(size=(4, 4)) + 1j*rng.normal(size=(4, 4)))
    transformed_frame = np.asarray(unitary @ bridge.factor_frame @ unitary.conj().T, dtype='<c16')
    transformed = FactorBridge(replace(bridge.chart, chart_id='test.bridge.conjugate',
        frame_sha256=factor_frame_sha256(transformed_frame)), transformed_frame)
    transformed_state = replace(state, positions=unitary @ state.positions @ unitary.conj().T,
        momenta=unitary @ state.momenta @ unitary.conj().T)
    np.testing.assert_allclose(observe(transformed, transformed_state, chart=transformed.chart.identity),
        observe(bridge, state, chart=bridge.chart.identity), atol=1e-12)
    coordinates = rng.normal(size=(2, 2, 3, 4))
    np.testing.assert_allclose(lift(transformed, coordinates, chart=transformed.chart.identity),
        unitary @ lift(bridge, coordinates, chart=bridge.chart.identity) @ unitary.conj().T, atol=1e-12)
    receiver = rng.normal(size=(2, 2, 3, 4))
    np.testing.assert_allclose(readout(transformed, transformed_state, receiver, chart=transformed.chart.identity),
        readout(bridge, state, receiver, chart=bridge.chart.identity), atol=1e-12)
    coefficients = np.zeros((2, 3, 4)); coefficients[..., 1:] = rng.normal(size=(2, 3, 3))
    np.testing.assert_allclose(factor_force(transformed, coefficients, chart=transformed.chart.identity, kind='FACTOR'),
        unitary @ factor_force(bridge, coefficients, chart=bridge.chart.identity, kind='FACTOR') @ unitary.conj().T, atol=1e-12)


def test_both_sector_force_and_full_state_kick_preserve_complement(selected):
    bridge, _ = selected
    coefficients = np.zeros((2, 3, 4)); coefficients[0, 1, 2] = 2.; coefficients[1, 2, 3] = -3.
    force = factor_force(bridge, coefficients, chart=bridge.chart.identity, kind='FACTOR')
    assert np.linalg.norm(force[0]) > 0 and np.linalg.norm(force[1]) > 0
    np.testing.assert_allclose(np.linalg.norm(force), np.linalg.norm(coefficients), atol=1e-12)
    state = native_state()
    kicked = momentum_kick(bridge, state, force, chart=bridge.chart.identity, duration=.001, amplitude=-.4)
    np.testing.assert_array_equal(kicked.positions, state.positions)
    np.testing.assert_allclose(kicked.momenta-state.momenta, -.0004*force, atol=1e-14)
    before = decompose(bridge, state, chart=bridge.chart.identity)[2]
    after = decompose(bridge, kicked, chart=bridge.chart.identity)[2]
    np.testing.assert_allclose(after, before, atol=1e-12)
    assert kicked.step_index == state.step_index and kicked.q == 2
    assert native_coordinates(kicked).shape == (192,)


def test_complement_force_orthogonality_norm_and_covariance(selected):
    bridge, _ = selected
    candidate = native_state().positions
    force = norm_matched_complement_force(bridge, candidate, chart=bridge.chart.identity, norm=3.7)
    np.testing.assert_allclose(np.linalg.norm(force), 3.7, atol=1e-12)
    np.testing.assert_allclose(np.einsum('cab,sjab->sjc', bridge.axes.conj(), force), 0, atol=1e-12)
    np.testing.assert_allclose(np.trace(force, axis1=-2, axis2=-1), 0, atol=1e-12)
    unitary, _ = np.linalg.qr(np.random.default_rng(438).normal(size=(4, 4))+1j*np.random.default_rng(765).normal(size=(4, 4)))
    frame = np.asarray(unitary @ bridge.factor_frame @ unitary.conj().T, dtype='<c16')
    other = FactorBridge(replace(bridge.chart, frame_sha256=factor_frame_sha256(frame)), frame)
    np.testing.assert_allclose(norm_matched_complement_force(other, unitary@candidate@unitary.conj().T,
        chart=other.chart.identity, norm=3.7), unitary@force@unitary.conj().T, atol=1e-12)


def test_trace_force_is_separate_and_receiver_uses_same_native_dual(selected):
    bridge, _ = selected
    coefficients = np.zeros((2, 3, 4)); coefficients[..., 0] = np.arange(1., 7.).reshape(2, 3)
    force = factor_force(bridge, coefficients, chart=bridge.chart.identity, kind='TRACE')
    np.testing.assert_allclose(force, coefficients[..., 0, None, None]*np.eye(4)/2, atol=1e-12)
    with pytest.raises(ValueError, match='separate'):
        factor_force(bridge, coefficients, chart=bridge.chart.identity, kind='FACTOR')
    coefficients[..., 1] = 1
    with pytest.raises(ValueError, match='separate'):
        factor_force(bridge, coefficients, chart=bridge.chart.identity, kind='TRACE')
    receiver = np.random.default_rng(925).normal(size=(2, 2, 3, 4))
    state = native_state()
    native_dual = lift(bridge, receiver, chart=bridge.chart.identity)
    np.testing.assert_allclose(readout(bridge, state, receiver, chart=bridge.chart.identity),
        np.vdot(native_dual, phase(state)).real, atol=1e-12)


def test_matched_signed_actions_share_receiver_and_normalization(selected):
    bridge, _ = selected
    state = native_state()
    coefficients = np.zeros((2, 3, 4)); coefficients[:, :, 2] = 1/np.sqrt(6)
    force = factor_force(bridge, coefficients, chart=bridge.chart.identity, kind='FACTOR')
    receiver = np.zeros((2, 2, 3, 4)); receiver[1] = coefficients
    epsilon, duration = .03, .002
    plus = momentum_kick(bridge, state, force, chart=bridge.chart.identity, duration=duration, amplitude=epsilon)
    minus = momentum_kick(bridge, state, force, chart=bridge.chart.identity, duration=duration, amplitude=-epsilon)
    difference = (readout(bridge, plus, receiver, chart=bridge.chart.identity)
                  - readout(bridge, minus, receiver, chart=bridge.chart.identity))/(2*epsilon)
    np.testing.assert_allclose(np.linalg.norm(force), 1, atol=1e-12)
    np.testing.assert_allclose(difference, duration, atol=1e-12)


def test_future_diagnostics_do_not_change_origin_frame_selection(selected):
    bridge, arguments = selected
    positions = np.broadcast_to(np.stack((algebra.LEFT, algebra.RIGHT)), (49, 2, 3, 4, 4)).copy()
    positions[32:, 1] = 0
    poisoned, arrays = retained_trace(arguments['spec'], positions=positions)
    frame = arrays['aligned_factor'][1]
    altered = select_factor_bridge(**(arguments | dict(trace=poisoned, frame=frame)))
    np.testing.assert_array_equal(altered.factor_frame, bridge.factor_frame)
    np.testing.assert_array_equal(observe(altered, native_state(), chart=altered.chart.identity),
                                  observe(bridge, native_state(), chart=bridge.chart.identity))
    assert altered.chart.cutoff == bridge.chart.cutoff
    # Distinct complete custody artifacts are preserved rather than relabelled.
    assert altered.chart.frame_arrays != bridge.chart.frame_arrays


@pytest.mark.parametrize('change', [dict(origin_tick=0, cutoff=Decimal(0)),
    dict(cutoff=Decimal('.017')), dict(expected_frame_sha256='c'*64)])
def test_unadmitted_origin_cutoff_and_frame_substitution_refuse(selected, change):
    _, arguments = selected
    with pytest.raises(ValueError):
        select_factor_bridge(**(arguments | change))


@pytest.mark.parametrize('failure', ['UNIDENTIFIABLE', 'NUMERICAL_INVALID', 'MISSING_ARTIFACT'])
def test_unavailable_factor_and_absent_diagnostics_refuse(selected, failure):
    _, arguments = selected
    if failure == 'MISSING_ARTIFACT':
        trace = replace(arguments['trace'], diagnostics=None, diagnostic_members=())
    else:
        positions = np.zeros((49, 2, 3, 4, 4), dtype='<c16')
        if failure == 'NUMERICAL_INVALID':
            positions[:] = np.nan
        trace, _ = retained_trace(arguments['spec'], positions=positions)
    with pytest.raises(ValueError, match='unadmitted'):
        select_factor_bridge(**(arguments | dict(trace=trace)))


def test_alignment_ambiguity_refuses_even_structurally_admitted_factor(selected):
    _, arguments = selected
    old = arguments['trace']
    observations = tuple(replace(o, alignment_ambiguous=True) if o.tick == 16 else o for o in old.observations)
    with pytest.raises(ValueError, match='unadmitted'):
        select_factor_bridge(**(arguments | dict(trace=replace(old, observations=observations))))


def test_sealed_chart_and_frame_bytes_refuse_substitution(selected):
    bridge, _ = selected
    state = native_state()
    for change in (dict(cutoff=Decimal('.032')), dict(origin_native_step=32),
                   dict(clock=replace(bridge.chart.clock, object_fingerprint='c'*64)),
                   dict(root=replace(bridge.chart.root, root_id='test.bridge.other-root'))):
        altered = replace(bridge.chart, **change)
        with pytest.raises(ValueError, match='substitutes'):
            observe(bridge, state, chart=altered.identity)
    with pytest.raises(ValueError, match='substituted'):
        FactorBridge(bridge.chart, -bridge.factor_frame)
    with pytest.raises(ValueError, match='substituted'):
        FactorBridge(bridge.chart, bridge.factor_frame*2)


def test_chart_canonical_roundtrip_and_exact_conventions(selected):
    bridge, _ = selected
    raw = canonical_json_bytes(bridge.chart)
    assert decode_canonical_bytes(raw, FactorBridgeChart, maximum_bytes=len(raw)) == bridge.chart
    for change in (dict(native_dimension=96), dict(retained_dimension=36),
                   dict(sector_order=('Y', 'X')), dict(frame_policy='MOVING'),
                   dict(component_order=(1, 0, 2)), dict(retained_memory='FUTURE')):
        with pytest.raises(ValueError, match='convention'):
            replace(bridge.chart, **change)
    with pytest.raises(ValueError, match='precedes'):
        observe(bridge, native_state(step=15), chart=bridge.chart.identity)


def test_bridge_arrays_cannot_be_mutated_and_invalid_operands_refuse(selected):
    bridge, _ = selected
    for values in (bridge.factor_frame, bridge.axes,
                   observe(bridge, native_state(), chart=bridge.chart.identity)):
        assert not values.flags.writeable
        with pytest.raises(ValueError):
            values.setflags(write=True)
    with pytest.raises(ValueError, match='coordinates'):
        lift(bridge, np.zeros(48), chart=bridge.chart.identity)
    with pytest.raises(ValueError, match='complete finite'):
        observe(bridge, None, chart=bridge.chart.identity)
    for candidate in (np.zeros((2, 3, 4, 4), dtype='<c16'),
                      np.broadcast_to(bridge.axes[1], (2, 3, 4, 4)).copy()):
        with pytest.raises(ValueError, match='no resolved'):
            norm_matched_complement_force(bridge, candidate, chart=bridge.chart.identity, norm=1.)
