"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from typing import Callable
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.six_matrix_response.contracts import BetaCouplingRule, SixMatrixResponseModelFamilyMember, SixMatrixResponseNumericalView, MatrixIntegratorKind, MatrixPrecision
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import SixMatrixParameters, coupling_derivative_density
from empirical_lawhood.domains.matrix.six_matrix_response.model import ComplexArray, SixMatrixState, ideal_state
from empirical_lawhood.domains.matrix.six_matrix_response.passive_probe import derive_probe_roster
from empirical_lawhood.domains.matrix.six_matrix_response.response_assay import ResponseGeometryNativeForcePulse, force_step, parent_schedule, select_past_mode
from empirical_lawhood.domains.matrix.six_matrix_response.response_checkpoint import ResponseGeometryNativeCheckpoint
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import ResponseGeometryNativeGeometrySample, ResponseGeometryNativePassiveObserver, PassiveReadout, _decode, _encode, geometry_sample
from empirical_lawhood.domains.matrix.six_matrix_response.response_qualification import ResponseGeometryAssayNativeConfig, ResponseGeometryAssayNativeDelivery, ResponseGeometryAssayNativeRoot, ResponseGeometryAssayNativeSegment, ResponseGeometryAssayNativeViewSegment
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import brownian_bridge_split, traceless_hermitian_basis
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import BAOABGradientCache, SixMatrixResponseRNGStreamReceipt, baoab_step_with_hermitian_noise, checkpoint_from_phase_state, derive_rng_stream, hermitian_noise, state_from_checkpoint


ASSAY_HDF5_SCHEMA = 'empirical-lawhood/simulators/six-matrix-response/assay-native-observations-hdf5'


ASSAY_HDF5_MEDIA_TYPE = "application/x-hdf5"


ASSAY_NATIVE_HDF5_METADATA = {
    "empirical_lawhood_payload_schema": ASSAY_HDF5_SCHEMA,
    "empirical_lawhood_units": '{"couplings":"native-reduced","geometry":"dimensionless","momenta":"native-reduced","positions":"native-reduced","probe":"mixed:reference-ticks,dimensionless,flags","ticks":"reference-tick","transfer":"dimensionless"}',
    "empirical_lawhood_frames": '{"positions":"factor,spatial,matrix-row,matrix-column;unitary-conjugated-native","transfer":"traceless-Hermitian-receiver-basis"}',
    "empirical_lawhood_clocks": '{"probe":"origin-tick,evidence-ready-tick","ticks":"reference-tick=native-step/refinement;dt=0.001"}',
    "empirical_lawhood_keys": '["segment_sha256","refinement","ticks"]',
}


MEMBER = SixMatrixResponseModelFamilyMember(
    "response-geometry.member",
    Decimal("0.5"),
    Decimal("0.5"),
    Decimal(1),
    BetaCouplingRule.PUBLISHED_DETERMINISTIC,
)


def _rng(
    config: ResponseGeometryAssayNativeConfig,
    root: ResponseGeometryAssayNativeRoot,
    purpose: str,
    counter: int = 0,
) -> tuple[np.random.Generator, SixMatrixResponseRNGStreamReceipt]:
    if root not in config.roots or purpose not in {
        "assay.preparation",
        "assay.continuation",
        "assay.bridge",
        "assay.quarter-bridge",
        "assay.covariance",
        "assay.probes",
    }:
        raise ValueError("assay RNG purpose/root is outside the declared roster")
    return derive_rng_stream(
        seed_root_id=f"response-geometry.seed.{config.seed_root_sha256}",
        purpose_id=f"{config.physical_unit_id(root)}.{purpose}",
        stream_index=counter,
        derivation_rule_id="response-geometry.rng.explicit-original-full-seed-pcg64dxsm",
        scientific_seed_sha256=config.scientific_inputs.roots[config.roots.index(root)].native_seed(
            purpose_ordinal=(
                "assay.preparation", "assay.continuation", "assay.bridge", "assay.probes",
                "assay.covariance", "assay.quarter-bridge",
            ).index(purpose),
            counter=counter,
        ),
    )


def _view(refinement: int) -> SixMatrixResponseNumericalView:
    return SixMatrixResponseNumericalView(
        f"response-geometry.view.r{refinement}",
        MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN,
        Decimal("0.001") / refinement,
        "dimensionless-langevin-time",
        Decimal(1),
        Decimal(1),
        MatrixPrecision.COMPLEX128,
        "numpy.pcg64dxsm",
        "1.0.0",
        "response-geometry.rng.explicit-original-full-seed-pcg64dxsm",
        512 * refinement,
    )


def _unitary(config: ResponseGeometryAssayNativeConfig, root: ResponseGeometryAssayNativeRoot, refinement: int) -> ComplexArray:
    if not root.covariance or refinement != 2:
        return np.eye(4, dtype="<c16")
    rng, _ = _rng(config, root, "assay.covariance")
    return np.asarray(
        np.linalg.qr(rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4)))[0], dtype="<c16"
    )


@dataclass
class _Continuation:
    state: SixMatrixState
    rng: np.random.Generator
    stream: SixMatrixResponseRNGStreamReceipt
    bridge: np.random.Generator
    observer: ResponseGeometryNativePassiveObserver
    window: list[ResponseGeometryNativeGeometrySample]
    x_window: list[ComplexArray]
    mode: ComplexArray | None
    pulse: ResponseGeometryNativeForcePulse | None
    invocation_positions: ComplexArray | None


def _start(
    config: ResponseGeometryAssayNativeConfig,
    segment: ResponseGeometryAssayNativeSegment,
    refinement: int,
    previous: ResponseGeometryNativeCheckpoint | None,
    unitary: ComplexArray,
) -> _Continuation:
    root = segment.root
    if previous is None:
        if segment.phase != "prefix":
            raise ValueError("assay continuation lacks its authoritative predecessor checkpoint")
        coupling = 8.0 if root.context == "prepared" else 0.0
        state = ideal_state(
            q=2,
            alpha_tilde_x=coupling,
            alpha_tilde_y=coupling,
            constitution="11" if root.context == "prepared" else "00",
        )
        state = replace(state, positions=unitary @ state.positions @ unitary.conj().T)
        rng, stream = _rng(config, root, "assay.preparation")
        bridge, _ = _rng(config, root, "assay.bridge")
        _, probe_stream = _rng(config, root, "assay.probes")
        roster = derive_probe_roster(
            config_fingerprint=probe_stream.derived_seed_sha256,
            rule_id="response-geometry-assay.probes",
            scientific_seed=int(config.scientific_inputs.roots[config.roots.index(root)].probe_roster_seed_sha256, 16),
        )
        fields = unitary @ roster.fields @ unitary.conj().T
        coordinates = np.einsum("lab,jab->jl", traceless_hermitian_basis(4).conj(), fields).real
        roster = replace(roster, fields=fields, coordinates=coordinates)
        observer = ResponseGeometryNativePassiveObserver(
            roster=roster, y=state.positions[1], y_velocity=state.momenta[1], refinement=refinement
        )
        return _Continuation(
            state,
            rng,
            stream,
            bridge,
            observer,
            [geometry_sample(state=state, member=MEMBER, refinement=refinement)],
            [state.positions[0]],
            None,
            None,
            None,
        )
    if (
        previous.native.step_index != segment.start_tick * refinement
        or previous.passive.refinement != refinement
        or previous.pending_noises_base64
    ):
        raise ValueError("assay segment must restore the exact completed reference-tick boundary")
    state, rng = state_from_checkpoint(previous.native)
    _, stream = _rng(config, root, "assay.continuation")
    if stream != previous.native.rng_stream:
        raise ValueError("assay predecessor RNG role differs from its declared continuation")
    bridge, _ = _rng(config, root, "assay.bridge")
    bridge.bit_generator.state = json.loads(previous.bridge_rng_state_json)
    value = _Continuation(
        state,
        rng,
        stream,
        bridge,
        ResponseGeometryNativePassiveObserver.restore(previous.passive),
        list(previous.structural_window),
        list(_decode(previous.x_window_base64, (len(previous.structural_window), 3, 4, 4))),
        None
        if previous.frozen_mode_base64 is None
        else _decode(previous.frozen_mode_base64, (3, 4, 4)),
        previous.pulse,
        None
        if previous.invocation_positions_base64 is None
        else _decode(previous.invocation_positions_base64, (2, 3, 4, 4)),
    )
    if segment.phase == "inner":
        assert segment.sign is not None
        value.pulse = ResponseGeometryNativeForcePulse(
            f"action.{segment.task_id}", root.assay, segment.sign, segment.start_tick
        )
        value.invocation_positions = state.positions
    elif segment.phase == "resume":
        assert value.pulse is not None and segment.predecessor is not None
        assert segment.sign is not None
        expected = ResponseGeometryNativeForcePulse(
            f"action.{segment.predecessor.task_id}",
            root.assay,
            segment.sign,
            root.landmark_tick + root.invocation_offset,
        )
        if value.pulse != expected:
            raise ValueError("assay resumed pulse occurrence differs from its checkpoint")
    return value


def _checkpoint(
    value: _Continuation, segment: ResponseGeometryAssayNativeSegment, refinement: int
) -> ResponseGeometryNativeCheckpoint:
    native = checkpoint_from_phase_state(
        checkpoint_id=f"checkpoint.{segment.task_id}.r{refinement}.s{value.state.step_index}",
        request=ObjectIdentity.from_record(segment.task_id, segment),
        total_steps=(
            segment.root.landmark_tick + segment.root.invocation_offset + segment.root.horizon_ticks
        )
        * refinement,
        state=value.state,
        rng=value.rng,
        rng_stream=value.stream,
        receivers=(),
    )
    return ResponseGeometryNativeCheckpoint(
        native.checkpoint_id,
        native,
        value.observer.checkpoint(),
        tuple(value.window),
        _encode(np.asarray(value.x_window, dtype="<c16")),
        None if value.mode is None else _encode(value.mode),
        segment.parent,
        None if segment.parent is None else segment.root.landmark_tick,
        value.pulse,
        None if value.invocation_positions is None else _encode(value.invocation_positions),
        json.dumps(value.bridge.bit_generator.state, sort_keys=True, separators=(",", ":")),
        (),
    )


def _innovations(
    value: _Continuation,
    config: ResponseGeometryAssayNativeConfig,
    segment: ResponseGeometryAssayNativeSegment,
    refinement: int,
    tick: int,
    unitary: ComplexArray,
) -> tuple[ComplexArray, ...]:
    if tick == 256:
        value.rng, value.stream = _rng(config, segment.root, "assay.continuation")
    coarse = hermitian_noise(rng=value.rng, q=2)
    bridge = hermitian_noise(rng=value.bridge, q=2)
    halves = brownian_bridge_split(
        coarse_noise=coarse, bridge_noise=bridge, half_decay=float(np.exp(-0.0005))
    )
    noises: tuple[ComplexArray, ...] = (coarse,) if refinement == 1 else halves
    if refinement == 4:
        quarter, _ = _rng(config, segment.root, "assay.quarter-bridge", tick)
        noises = tuple(
            noise
            for half in halves
            for noise in brownian_bridge_split(
                coarse_noise=half,
                bridge_noise=hermitian_noise(rng=quarter, q=2),
                half_decay=float(np.exp(-0.00025)),
            )
        )
    return tuple(np.asarray(unitary @ noise @ unitary.conj().T, dtype="<c16") for noise in noises)


def _sample(
    rows: list[tuple[object, ...]], value: _Continuation, readout: PassiveReadout | None
) -> None:
    sample = value.window[-1]
    metrics = [
        float("nan") if field is None else float(field)
        for factor in (sample.x, sample.y)
        for field in (factor.phi, factor.closure_ratio, factor.kernel_ratio)
    ]
    probe = [float("nan")] * 9
    transfer = np.full((15, 15), np.nan)
    if readout is not None:
        probe = [
            readout.origin_tick,
            readout.evidence_ready_tick,
            *[
                float("nan") if field is None else field
                for field in (
                    readout.geometry_loss,
                    readout.radius_loss,
                    readout.loss_ratio,
                    readout.drift_loss,
                )
            ],
            int(readout.known),
            -1 if readout.passes is None else int(readout.passes),
            int(readout.transfer_resolved),
        ]
        transfer = _decode(readout.propagator_base64, (15, 15), real=True)
    rows.append(
        (
            sample.reference_tick,
            value.state.positions,
            value.state.momenta,
            (value.state.alpha_tilde_x, value.state.alpha_tilde_y),
            metrics,
            probe,
            transfer,
        )
    )


def _run_view(config: ResponseGeometryAssayNativeConfig, segment: ResponseGeometryAssayNativeSegment, refinement: int, previous: ResponseGeometryAssayNativeViewSegment | None, *, progress: Callable[[int], None] | None=None):
    arrays = {}
    trace = sha256(f'{segment.fingerprint()}.r{refinement}'.encode())
    unentered_delivery = ResponseGeometryAssayNativeDelivery(False, 0, 0, 0, Decimal(0), trace.hexdigest(), None)
    if previous is not None and (previous.disposition != 'COMPLETE' or previous.checkpoint is None):
        return (ResponseGeometryAssayNativeViewSegment(refinement, 'UNENTERED', previous.last_completed_native_step, None, 'PREDECESSOR_INCOMPLETE', Decimal(0), Decimal(0), unentered_delivery), arrays)
    if previous is not None and previous.checkpoint is not None and (previous.checkpoint.frozen_mode_base64 is None):
        return (ResponseGeometryAssayNativeViewSegment(refinement, 'UNENTERED', previous.last_completed_native_step, None, 'PAST_MODE_UNRESOLVED', Decimal(0), Decimal(0), unentered_delivery), arrays)
    unitary = _unitary(config, segment.root, refinement)
    arrays['unitary'] = unitary
    value = _start(config, segment, refinement, None if previous is None else previous.checkpoint, unitary)
    view, cache = (_view(refinement), BAOABGradientCache())
    schedule = None if segment.parent is None else parent_schedule(parent=segment.parent, refinement=refinement)
    rows: list[tuple[object, ...]] = []
    _sample(rows, value, None)
    work, density_work = (0.0, 0.0)
    completed_intervals, nonzero_intervals = (0, 0)
    mode_sha256 = None if value.mode is None else sha256(value.mode.tobytes()).hexdigest()
    disposition, reason = ('COMPLETE', None)
    checkpoint = None
    for tick in range(segment.start_tick, segment.end_tick):
        noises = _innovations(value, config, segment, refinement, tick, unitary)
        for noise in noises:
            old = value.state
            force = 0.0
            try:
                with np.errstate(over='raise', invalid='raise', divide='raise'):
                    if value.pulse is not None:
                        assert value.mode is not None
                        state = force_step(old, pulse=value.pulse, mode=value.mode, member=MEMBER, numerical_view=view, standardized_noise=noise, gradient_cache=cache)
                        force = value.pulse.interval_force(native_step=old.step_index, refinement=refinement)
                        next_work = work + force * float(np.vdot(value.mode, state.positions[0] - old.positions[0]).real)
                        next_density_work = density_work
                    else:
                        next_work, next_density_work = (work, density_work)
                        if segment.phase == 'parent':
                            assert schedule is not None
                            offset = old.step_index - segment.start_tick * refinement
                            alpha = schedule[min(offset, len(schedule) - 1)]
                        else:
                            fraction = min(1.0, (old.step_index + 1) / (256 * refinement))
                            initial = 8.0 if segment.root.context == 'prepared' else 0.0
                            alpha = np.asarray((initial + fraction * (2 / 3 - initial), initial + fraction * (22 / 3 - initial)))
                        state = baoab_step_with_hermitian_noise(old, member=MEMBER, numerical_view=view, next_alpha_tilde_x=float(alpha[0]), next_alpha_tilde_y=float(alpha[1]), standardized_noise=noise, gradient_cache=cache)
                        if segment.phase == 'parent':
                            parameters = SixMatrixParameters(2, 0.5, 0.5, 1.0, old.alpha_tilde_x, old.alpha_tilde_y)
                            derivatives = coupling_derivative_density(old.positions, parameters)
                            next_density_work += abs(derivatives[0] * (state.alpha_tilde_x - old.alpha_tilde_x))
                            next_density_work += abs(derivatives[1] * (state.alpha_tilde_y - old.alpha_tilde_y))
                    if not state.finite or not np.isfinite((next_work, next_density_work)).all():
                        raise FloatingPointError('nonfinite native state')
                    value.state = state
                    work, density_work = (next_work, next_density_work)
                    completed_intervals += 1
                    nonzero_intervals += int(force != 0)
                    trace.update(np.asarray((old.step_index, old.alpha_tilde_x, old.alpha_tilde_y, state.alpha_tilde_x, state.alpha_tilde_y, force, force), dtype='<f8').tobytes())
            except (FloatingPointError, np.linalg.LinAlgError):
                disposition, reason = ('NUMERICAL_FAILURE', 'NATIVE_NUMERICAL_FAILURE')
                break
            if progress is not None and completed_intervals % 1024 == 0:
                progress(completed_intervals)
            try:
                with np.errstate(over='raise', invalid='raise', divide='raise'):
                    readout = value.observer.advance(y=state.positions[1], native_step=state.step_index, y_velocity=state.momenta[1])
                    if state.step_index % (16 * refinement) == 0:
                        value.window.append(geometry_sample(state=state, member=MEMBER, refinement=refinement))
                        value.x_window.append(state.positions[0])
                        value.window, value.x_window = (value.window[-16:], value.x_window[-16:])
                        _sample(rows, value, readout)
            except (FloatingPointError, np.linalg.LinAlgError):
                disposition, reason = ('OBSERVATION_FAILURE', 'NATIVE_OBSERVER_FAILURE')
                break
        if reason is not None:
            break
        if (tick + 1) % 512 == 0 and tick + 1 != segment.end_tick:
            intermediate = _checkpoint(value, segment, refinement)
            arrays[f'checkpoint-{tick + 1}'] = np.frombuffer(intermediate.canonical_bytes(), dtype='u1')
    if disposition == 'COMPLETE':
        if segment.phase == 'prefix':
            value.mode = select_past_mode(ticks=tuple((sample.reference_tick for sample in value.window)), observations=np.asarray(value.x_window), cutoff_tick=segment.end_tick)
            if value.mode is not None:
                arrays['shadow_mode'] = value.mode
        checkpoint = _checkpoint(value, segment, refinement)
    for index, name in enumerate(('ticks', 'positions', 'momenta', 'couplings', 'geometry', 'probe', 'transfer')):
        arrays[name] = np.asarray([row[index] for row in rows])
    return (ResponseGeometryAssayNativeViewSegment(refinement, disposition, value.state.step_index, checkpoint, reason, Decimal(str(work)), Decimal(str(density_work)), ResponseGeometryAssayNativeDelivery(True, completed_intervals, 2 * completed_intervals, nonzero_intervals, Decimal(nonzero_intervals * (0 if value.pulse is None else value.pulse.sign * int(value.pulse.amplitude))) * Decimal('0.001') / refinement, trace.hexdigest(), mode_sha256)), arrays)
