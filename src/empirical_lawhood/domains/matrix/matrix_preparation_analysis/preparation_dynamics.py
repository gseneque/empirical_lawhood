"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
import numpy as np
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.six_matrix_response.gradients import SixMatrixParameters, coupling_derivative_density
from empirical_lawhood.domains.matrix.six_matrix_response.model import ComplexArray, SixMatrixState
from empirical_lawhood.domains.matrix.six_matrix_response.preparation_differential import preparation_force_step, preparation_pulse_amplitude
from empirical_lawhood.domains.matrix.six_matrix_response.response_assay import parent_schedule
from empirical_lawhood.domains.matrix.six_matrix_response.response_checkpoint import ResponseGeometryNativeCheckpoint
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import ResponseGeometryNativeGeometrySample, ResponseGeometryNativePassiveObserver, PassiveReadout, _decode, _encode, geometry_sample
from empirical_lawhood.domains.matrix.six_matrix_response.response_dynamics import MEMBER, _view
from empirical_lawhood.domains.matrix.six_matrix_response.shooting import brownian_bridge_split
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import BAOABGradientCache, SixMatrixResponseRNGStreamReceipt, baoab_step_with_hermitian_noise, checkpoint_from_phase_state, derive_rng_stream, hermitian_noise, state_from_checkpoint
from empirical_lawhood.domains.matrix.matrix_preparation.scientific_inputs import preparation_scientific_root_inputs
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import RESPONSE_BUNDLES, CAMPAIGN, NATIVE_SCHEMA, PreparationAction, PreparationDelivery, PreparationRoot, PreparationSourceConfig


NATIVE_MAXIMUM_BYTES = 96 * 1024**2


NATIVE_METADATA = {
    "empirical_lawhood_payload_schema": NATIVE_SCHEMA,
    "empirical_lawhood_units": '{"positions,momenta":"native-reduced","couplings":"native-reduced","geometry,transfer":"dimensionless","ticks":"reference-tick"}',
    "empirical_lawhood_frames": '{"positions":"sector,spatial,row,column;native-Hermitian","mode":"primary-preparent-X;common-to-all-parents-and-views"}',
    "empirical_lawhood_clocks": '{"reference":"dt=0.001","handoff":"landmark+144","inner":"pulse64;endpoint320;cadence16"}',
    "empirical_lawhood_keys": '["root","parent","bundle","amplitude","sign","refinement","ticks"]',
}


@dataclass
class _Branch:
    state: SixMatrixState
    observer: ResponseGeometryNativePassiveObserver
    window: list[ResponseGeometryNativeGeometrySample]
    x_window: list[ComplexArray]

    @classmethod
    def restore(cls, checkpoint: ResponseGeometryNativeCheckpoint) -> _Branch:
        state, _ = state_from_checkpoint(checkpoint.native)
        return cls(
            state,
            ResponseGeometryNativePassiveObserver.restore(checkpoint.passive),
            list(checkpoint.structural_window),
            list(_decode(checkpoint.x_window_base64, (len(checkpoint.structural_window), 3, 4, 4))),
        )


@dataclass(frozen=True)
class _Innovations:
    primary: ComplexArray
    half: ComplexArray
    stream: SixMatrixResponseRNGStreamReceipt
    rng_state: str
    bridge_state: str


def innovation_bundle(
    config: PreparationSourceConfig, root: PreparationRoot, purpose: str, ticks: int
) -> _Innovations:
    """Independent purposes; parent/sign do not enter the paired-noise key."""
    if root not in config.roots or purpose not in ("parent", *RESPONSE_BUNDLES, "prospective-task"):
        raise ValueError("preparation noise purpose/root is outside its exact roster")
    if ticks != (144 if purpose == "parent" else 320):
        raise ValueError("preparation noise bundle changes its fixed native clock")

    def generator(suffix: str) -> tuple[np.random.Generator, SixMatrixResponseRNGStreamReceipt]:
        from empirical_lawhood.domains.matrix.matrix_preparation_analysis.tangent_records import TangentPreparationConfig

        purpose_index = ("parent", *RESPONSE_BUNDLES, "prospective-task").index(purpose)
        scientific_seed = (
            root.preparation_seed(purpose_index=purpose_index, bridge=bool(suffix))
            if type(config) is TangentPreparationConfig
            else preparation_scientific_root_inputs(root.context, root.index).native_seed(
                purpose_index=purpose_index, bridge=bool(suffix)
            )
        )
        return derive_rng_stream(
            seed_root_id=f"{CAMPAIGN}.seed.{config.seed_sha256}",
            stream_index=0,
            derivation_rule_id=f"{CAMPAIGN}.explicit-root-purpose-inputs",
            purpose_id=f"{root.root_id}.{purpose}{suffix}",
            scientific_seed_sha256=scientific_seed,
        )

    rng, stream = generator("")
    bridge, _ = generator(".bridge")
    primary = np.empty((ticks, 2, 3, 4, 4), dtype=np.complex128)
    half = np.empty((2 * ticks, 2, 3, 4, 4), dtype=np.complex128)
    for tick in range(ticks):
        primary[tick] = hermitian_noise(rng=rng, q=2)
        halves = brownian_bridge_split(
            coarse_noise=primary[tick],
            bridge_noise=hermitian_noise(rng=bridge, q=2),
            half_decay=float(np.exp(-0.0005)),
        )
        half[2 * tick], half[2 * tick + 1] = halves
    return _Innovations(
        primary,
        half,
        stream,
        json.dumps(rng.bit_generator.state, sort_keys=True, separators=(",", ":")),
        json.dumps(bridge.bit_generator.state, sort_keys=True, separators=(",", ":")),
    )


def _sample(branch: _Branch, readout: PassiveReadout | None) -> tuple[object, ...]:
    geometry = [
        float("nan") if value is None else float(value)
        for factor in (branch.window[-1].x, branch.window[-1].y)
        for value in (factor.phi, factor.closure_ratio, factor.kernel_ratio)
    ]
    probe, transfer = [float("nan")] * 9, np.full((15, 15), np.nan)
    if readout is not None:
        probe = [
            readout.origin_tick,
            readout.evidence_ready_tick,
            *[
                float("nan") if value is None else value
                for value in (
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
    return (
        branch.window[-1].reference_tick,
        branch.state.positions,
        branch.state.momenta,
        (branch.state.alpha_tilde_x, branch.state.alpha_tilde_y),
        geometry,
        probe,
        transfer,
    )


def _row_arrays(rows):
    return {name: np.asarray([row[index] for row in rows]) for index, name in enumerate(("ticks", "positions", "momenta", "couplings", "geometry", "probe", "transfer"))}


def _unentered(
    occurrence: str, refinement: int, start: int, end: int, reason: str
) -> PreparationDelivery:
    return PreparationDelivery(
        occurrence,
        refinement,
        start,
        end,
        False,
        0,
        0,
        0,
        Decimal(0),
        Decimal(0),
        Decimal(0),
        sha256(occurrence.encode()).hexdigest(),
        "UNENTERED",
        reason,
    )


def _handoff_checkpoint(
    branch: _Branch,
    root: PreparationRoot,
    parent: str,
    refinement: int,
    mode: ComplexArray,
    innovations: _Innovations,
) -> ResponseGeometryNativeCheckpoint:
    rng = np.random.Generator(np.random.PCG64DXSM(0))
    rng.bit_generator.state = json.loads(innovations.rng_state)
    native = checkpoint_from_phase_state(
        checkpoint_id=f"checkpoint.{root.root_id}.{parent}.handoff.r{refinement}",
        request=ObjectIdentity.from_record(root.root_id, root),
        total_steps=(root.handoff + 320) * refinement,
        state=branch.state,
        rng=rng,
        rng_stream=innovations.stream,
        receivers=(),
    )
    return ResponseGeometryNativeCheckpoint(
        native.checkpoint_id,
        native,
        branch.observer.checkpoint(),
        tuple(branch.window),
        _encode(np.asarray(branch.x_window, dtype=np.complex128)),
        _encode(mode),
        parent,
        root.landmark,
        None,
        None,
        innovations.bridge_state,
        (),
    )


def _advance(branch: _Branch, *, root: PreparationRoot, parent: str, refinement: int, mode: ComplexArray, innovations: _Innovations, action: PreparationAction | None, progress: Callable[[int], None] | None):
    arrays = {}
    attributes = {}
    is_parent = action is None
    start, end = (root.landmark, root.handoff) if is_parent else (root.handoff, root.handoff + 320)
    occurrence = f'{root.root_id}.{parent}.parent.r{refinement}' if action is None else f'{action.action_id}.r{refinement}'
    if branch.state.step_index != start * refinement:
        raise ValueError('preparation continuation does not begin at its exact native clock')
    noises = innovations.primary if refinement == 1 else innovations.half
    if len(noises) != (end - start) * refinement:
        raise ValueError('preparation innovation count changes physical time')
    attributes['innovation_sha256'] = sha256(noises.tobytes()).hexdigest()
    attributes['innovation_stream_sha256'] = innovations.stream.fingerprint()
    schedule = parent_schedule(parent=parent, refinement=refinement)[:144 * refinement] if is_parent else None
    rows = [_sample(branch, None)]
    native_positions, native_momenta = ([], [])
    if action is not None and action.retain_native_path:
        native_positions.append(branch.state.positions)
        native_momenta.append(branch.state.momenta)
    view, cache = (_view(refinement), BAOABGradientCache())
    completed, nonzero, impulse, force_work, parent_work = (0, 0, 0.0, 0.0, 0.0)
    trace = sha256(occurrence.encode())
    disposition, reason = ('COMPLETE', None)
    for offset, noise in enumerate(noises):
        before, force = (branch.state, 0.0)
        try:
            with np.errstate(over='raise', invalid='raise', divide='raise'):
                if is_parent:
                    assert schedule is not None
                    alpha = schedule[offset]
                    after = baoab_step_with_hermitian_noise(before, member=MEMBER, numerical_view=view, next_alpha_tilde_x=float(alpha[0]), next_alpha_tilde_y=float(alpha[1]), standardized_noise=noise, gradient_cache=cache)
                    derivatives = coupling_derivative_density(before.positions, SixMatrixParameters(2, 0.5, 0.5, 1.0, before.alpha_tilde_x, before.alpha_tilde_y))
                    next_parent_work = parent_work + abs(derivatives[0] * (after.alpha_tilde_x - before.alpha_tilde_x))
                    next_parent_work += abs(derivatives[1] * (after.alpha_tilde_y - before.alpha_tilde_y))
                    next_force_work = force_work
                else:
                    assert action is not None
                    force = preparation_pulse_amplitude(native_step=before.step_index, invocation_tick=root.handoff, refinement=refinement, sign=action.sign, magnitude=float(action.magnitude))
                    after = preparation_force_step(before, amplitude=force, mode=mode, member=MEMBER, numerical_view=view, standardized_noise=noise, gradient_cache=cache)
                    next_force_work = force_work + force * float(np.vdot(mode, after.positions[0] - before.positions[0]).real)
                    next_parent_work = parent_work
                if not after.finite or not np.isfinite((next_parent_work, next_force_work)).all():
                    raise FloatingPointError('nonfinite native state/work')
                branch.state = after
                completed += 1
                nonzero += int(force != 0)
                impulse += force * float(view.timestep)
                force_work, parent_work = (next_force_work, next_parent_work)
                trace.update(np.asarray((before.step_index, before.alpha_tilde_x, before.alpha_tilde_y, after.alpha_tilde_x, after.alpha_tilde_y, force, force), dtype='<f8').tobytes())
        except (FloatingPointError, np.linalg.LinAlgError):
            disposition, reason = ('NUMERICAL_FAILURE', 'NATIVE_NUMERICAL_FAILURE')
            break
        if native_positions:
            native_positions.append(after.positions)
            native_momenta.append(after.momenta)
        if progress is not None and completed % 1024 == 0:
            progress(completed)
        try:
            with np.errstate(over='raise', invalid='raise', divide='raise'):
                readout = branch.observer.advance(y=after.positions[1], native_step=after.step_index, y_velocity=after.momenta[1])
                if after.step_index % (16 * refinement) == 0:
                    branch.window.append(geometry_sample(state=after, member=MEMBER, refinement=refinement))
                    branch.x_window.append(after.positions[0])
                    branch.window, branch.x_window = (branch.window[-16:], branch.x_window[-16:])
                    rows.append(_sample(branch, readout))
        except (FloatingPointError, np.linalg.LinAlgError):
            disposition, reason = ('OBSERVATION_FAILURE', 'NATIVE_OBSERVER_FAILURE')
            break
    arrays.update(_row_arrays(rows))
    if native_positions:
        arrays['native_positions'] = np.asarray(native_positions)
        arrays['native_momenta'] = np.asarray(native_momenta)
    if progress is not None:
        progress(completed)
    return (PreparationDelivery(occurrence, refinement, start, end, True, completed, 2 * completed, nonzero, Decimal(str(impulse)), Decimal(str(force_work)), Decimal(str(parent_work)), trace.hexdigest(), disposition, reason), arrays, attributes)
