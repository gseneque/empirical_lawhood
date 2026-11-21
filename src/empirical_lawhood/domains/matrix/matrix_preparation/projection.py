"""Supplied-array measurement projection and privileged mechanism instruments."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
import numpy as np
import numpy.typing as npt
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import RESPONSE_BUNDLES, PARENTS, READOUTS, PreparationRoot, preparation_actions
from empirical_lawhood.domains.matrix.six_matrix_response.model import SixMatrixState
from empirical_lawhood.domains.matrix.six_matrix_response.preparation_differential import NativeStateDifferential, discrete_secant_step, discrete_tangent_step, scalar_hold_tangent_step
from empirical_lawhood.domains.matrix.six_matrix_response.response_checkpoint import ResponseGeometryNativeCheckpoint
from empirical_lawhood.domains.matrix.six_matrix_response.response_observer import _decode
from empirical_lawhood.domains.matrix.six_matrix_response.response_dynamics import _view
from empirical_lawhood.domains.matrix.six_matrix_response.simulation import state_from_checkpoint
from empirical_lawhood.domains.matrix.matrix_preparation.benchmarks import curvature_quadratic, microscopic_initial, privileged_prediction
from empirical_lawhood.domains.matrix.matrix_preparation.contracts import FEATURES, PROJECTION_SCHEMA, PreparationProjectionReport, PreparationPrivilegedReport, PreparationProspectiveTaskReport


Array = npt.NDArray[Any]


PROJECTION_MAXIMUM_BYTES = 2 * 1024**2


PROJECTION_METADATA = {
    "empirical_lawhood_payload_schema": PROJECTION_SCHEMA,
    "empirical_lawhood_units": '{"responses":"hilbert-schmidt-native","tangent":"receiver-per-unit-force","features":"declared-nine-observable-chart","preservation":"native-X,relative-Y,operator-norm","probability-flags":"1"}',
    "empirical_lawhood_frames": '{"receiver":"primary-preparent-X-mode;common-parents-views","microphysics":"privileged-q2-native-Hermitian"}',
    "empirical_lawhood_clocks": '{"readout":"64,128,192,256,320-reference-ticks-after-handoff","features":"preparent-or-handoff-only","mechanism":"privileged-future-path"}',
    "empirical_lawhood_keys": '["root","refinement","parent","common-response,independent-response-1,independent-response-2,independent-response-3,prospective-task","NEG,HOLD,POS","readout"]',
}


PROJECTION_SHAPES: dict[str, tuple[int, ...]] = {
    "preparent_features": (9,),
    "handoff_features": (5, 9),
    "response": (5, 5, 3, 5),
    "response_path": (5, 5, 3, 21),
    "delivered": (5, 5, 3),
    "contact": (5, 5),
    "preservation": (5, 5, 3),
    "preservation_maxima": (5, 5, 3, 3),
    "parent_work": (5,),
    "privileged_gain": (5, 3, 5),
    "privileged_covariance_minimum": (5,),
    "privileged_symmetry_error": (5,),
    "amplitude_chi": (5, 4, 5),
    "amplitude_even": (5, 4, 5),
    "amplitude_position_error": (5, 4, 5),
    "amplitude_momentum_error": (5, 4, 5),
    "coupled_tangent": (5, 5),
    "scalar_tangent": (5, 5),
    "secant_receiver": (5, 5),
    "secant_position_error": (5, 5),
    "secant_momentum_error": (5, 5),
    "secant_position_norm": (5, 5),
    "secant_momentum_norm": (5, 5),
    "tangent_position_norm": (5, 5),
    "tangent_momentum_norm": (5, 5),
}


_OBSERVABLE_KEYS = (
    "preparent_features",
    "handoff_features",
    "response",
    "response_path",
    "delivered",
    "contact",
    "preservation",
    "preservation_maxima",
    "parent_work",
)


_PROSPECTIVE_TASK_KEYS = (
    "response",
    "response_path",
    "delivered",
    "contact",
    "preservation",
    "preservation_maxima",
)


OBSERVABLE_SHAPES = {
    key: (shape[0], 4, *shape[2:]) if key in _PROSPECTIVE_TASK_KEYS else shape
    for key, shape in PROJECTION_SHAPES.items()
    if key in _OBSERVABLE_KEYS
}


PRIVILEGED_SHAPES = {
    key: shape for key, shape in PROJECTION_SHAPES.items() if key not in _OBSERVABLE_KEYS
}


PROSPECTIVE_TASK_SHAPES = {key: (PROJECTION_SHAPES[key][0], *PROJECTION_SHAPES[key][2:]) for key in _PROSPECTIVE_TASK_KEYS}


@dataclass(frozen=True)
class PreparationProjectionPayloads:
    observable: bytes
    privileged: bytes
    prospective_task: bytes


@dataclass(frozen=True)
class PreparationProjectionReports:
    observable: PreparationProjectionReport
    privileged: PreparationPrivilegedReport
    prospective_task: PreparationProspectiveTaskReport


def observable_features(
    receiver: Array,
    spectra: Array,
    receiver_history: Array,
    radius_history: Array,
    relative_ticks: Array,
    offset_time: float,
) -> Array:
    """Nine permitted scalar/spectral observations; no hidden state/future API."""
    if (
        receiver.shape != (2,)
        or spectra.shape != (4, 3, 4)
        or receiver_history.shape != (16,)
        or radius_history.shape != (16,)
        or not np.array_equal(relative_ticks, np.arange(-240, 1, 16))
    ):
        raise ValueError("observable feature input violates its measurement chart or causal window")
    time = relative_ticks * 0.001
    slope = np.linalg.lstsq(np.column_stack((np.ones(16), time)), radius_history, rcond=None)[0][1]
    acceleration = (
        2
        * np.linalg.lstsq(
            np.column_stack((np.ones(16), time, time * time)), receiver_history, rcond=None
        )[0][2]
    )
    result = np.r_[receiver, np.sum(spectra**2, axis=(1, 2)), slope, acceleration, offset_time]
    if result.shape != (len(FEATURES),) or not np.isfinite(result).all():
        raise ValueError("observable feature is missing or nonfinite")
    return np.asarray(result, dtype=np.float64)


def _observe(checkpoint: ResponseGeometryNativeCheckpoint, mode: Array, landmark: int) -> Array:
    state, _ = state_from_checkpoint(checkpoint.native)
    window = _decode(checkpoint.x_window_base64, (16, 3, 4, 4))
    reference_tick = state.step_index // checkpoint.passive.refinement
    if tuple(g.reference_tick for g in checkpoint.structural_window) != tuple(
        range(reference_tick - 240, reference_tick + 1, 16)
    ):
        raise ValueError("observer is not the exact causal handoff window")
    # This projection is the observation instrument. Downstream estimators
    # receive only its nine outputs, never these hidden native matrices.
    receiver = np.array(
        [np.vdot(mode, state.positions[0]).real, np.vdot(mode, state.momenta[0]).real]
    )
    spectra = np.linalg.eigvalsh(np.concatenate((state.positions, state.momenta)))
    history = np.einsum("tjab,jab->t", window, mode.conj()).real
    radius = np.sum(abs(window) ** 2, axis=(1, 2, 3))
    return observable_features(
        receiver,
        spectra,
        history,
        radius,
        np.arange(-240, 1, 16),
        (reference_tick - landmark) * 0.001,
    )


def preservation(
    action: Mapping[str, Array], hold: Mapping[str, Array], mode: Array
) -> tuple[int, Array]:
    """The original source-qualification/development receiver-preservation quantities, one action at a time."""
    displacement = action["positions"] - hold["positions"]
    projection = np.einsum("jab,sjab->s", mode.conj(), displacement[:, 0]).real
    orthogonal = displacement[:, 0] - projection[:, None, None, None] * mode
    maximum_x = float(np.max(np.linalg.norm(orthogonal.reshape(21, -1), axis=1)))
    maximum_y = float(np.max(np.linalg.norm(displacement[:, 1].reshape(21, -1), axis=1))) / max(
        1, float(np.linalg.norm(hold["positions"][0, 1]))
    )
    maximum_transfer, known = 0.0, True
    for index in range(2, 21):
        tick = int(action["ticks"][index])
        for path in (action, hold):
            row = path["probe"][index]
            known &= bool(
                row[0] == tick - 32
                and row[1] == tick
                and row[8] == 1
                and np.isfinite(path["transfer"][index]).all()
            )
        if known:
            maximum_transfer = max(
                maximum_transfer,
                float(np.linalg.norm(action["transfer"][index] - hold["transfer"][index], 2)),
            )
    maxima = np.array([maximum_x, maximum_y, maximum_transfer if known else np.nan])
    return (
        -1
        if not known
        else int(maximum_x <= 0.125 and maximum_y <= 0.05 and maximum_transfer <= 0.05)
    ), maxima


def _state(
    path: Mapping[str, Array], root: PreparationRoot, refinement: int, offset: int
) -> SixMatrixState:
    return SixMatrixState(
        q=2,
        positions=path["native_positions"][offset],
        momenta=path["native_momenta"][offset],
        step_index=root.handoff * refinement + offset,
        alpha_tilde_x=2 / 3,
        alpha_tilde_y=22 / 3,
    )


def _mechanism(
    arrays: dict[str, Array],
    parent_index: int,
    root: PreparationRoot,
    refinement: int,
    mode: Array,
    paths: Mapping[str, Mapping[str, Array]],
) -> None:
    hold, minus, plus = (paths[f"common-response.a8.{sign}"] for sign in ("hold", "neg", "pos"))
    tangent, secant = NativeStateDifferential.zero(), NativeStateDifferential.zero()
    scalar_position, scalar_momentum = 0.0, 0.0
    previous, previous_minus, previous_plus = (
        _state(path, root, refinement, 0) for path in (hold, minus, plus)
    )
    for offset in range(320 * refinement):
        following, following_minus, following_plus = (
            _state(path, root, refinement, offset + 1) for path in (hold, minus, plus)
        )
        active = float(offset < 64 * refinement)
        tangent = discrete_tangent_step(
            previous,
            following,
            tangent,
            mode=mode,
            numerical_view=_view(refinement),
            force_derivative=active,
        )
        secant = discrete_secant_step(
            previous_minus,
            previous_plus,
            following_minus,
            following_plus,
            secant,
            mode=mode,
            numerical_view=_view(refinement),
            normalized_force=active,
        )
        scalar_position, scalar_momentum = scalar_hold_tangent_step(
            previous,
            following,
            position=scalar_position,
            momentum=scalar_momentum,
            mode=mode,
            numerical_view=_view(refinement),
            force_derivative=active,
        )
        previous, previous_minus, previous_plus = following, following_minus, following_plus
        if offset + 1 not in tuple(j * refinement for j in READOUTS):
            continue
        j = READOUTS.index((offset + 1) // refinement)
        index = (offset + 1) // (16 * refinement)
        arrays["coupled_tangent"][parent_index, j] = tangent.receiver(mode)
        arrays["scalar_tangent"][parent_index, j] = scalar_position
        arrays["secant_receiver"][parent_index, j] = secant.receiver(mode)
        for field in ("positions", "momenta"):
            label = "position" if field == "positions" else "momentum"
            contrast = (getattr(following_plus, field) - getattr(following_minus, field)) / 16
            arrays[f"secant_{label}_error"][parent_index, j] = np.linalg.norm(
                getattr(secant, field) - contrast
            )
            arrays[f"secant_{label}_norm"][parent_index, j] = np.linalg.norm(contrast)
            arrays[f"tangent_{label}_norm"][parent_index, j] = np.linalg.norm(
                getattr(tangent, field)
            )
        for a, (label, magnitude) in enumerate(
            (("a05", 0.5), ("a1", 1.0), ("a2", 2.0), ("a8", 8.0))
        ):
            left, right = paths[f"common-response.{label}.neg"], paths[f"common-response.{label}.pos"]
            for field in ("positions", "momenta"):
                chi = (right[field][index] - left[field][index]) / (2 * magnitude)
                suffix = "position" if field == "positions" else "momentum"
                arrays[f"amplitude_{suffix}_error"][parent_index, a, j] = np.linalg.norm(
                    chi - getattr(tangent, field)
                )
                if field == "positions":
                    arrays["amplitude_chi"][parent_index, a, j] = np.vdot(mode, chi[0]).real
                    even = (right[field][index, 0] + left[field][index, 0]) / 2 - hold[field][
                        index, 0
                    ]
                    arrays["amplitude_even"][parent_index, a, j] = np.vdot(mode, even).real


def project_preparation_records(native, refinement, *, mode, imported_checkpoint, parent_records):
    """Project supplied parent-array bundles; an iterator bounds live native arrays to one parent.

    Native readers supply the fixed census while retaining their own verification lifetime.
    Literal array bundles exercise the same calculations without a file or adapter import.
    """
    arrays = {
        name: np.full(shape, np.nan, dtype=np.float64) for name, shape in PROJECTION_SHAPES.items()
    }
    arrays["delivered"].fill(0)
    arrays["contact"].fill(-1)
    arrays["preservation"].fill(-1)
    failed_mechanisms, failed_benchmarks = [], []
    root = native.root
    deliveries = {d.occurrence_id: d for d in native.deliveries if d.refinement == refinement}
    if imported_checkpoint is not None:
        arrays["preparent_features"] = _observe(imported_checkpoint, mode, root.landmark)
    quadratic = None if mode is None else curvature_quadratic(mode)
    for p, (parent, entry) in enumerate(zip(PARENTS, parent_records, strict=True)):
        checkpoint, paths = entry
        parent_delivery = deliveries[f"{root.root_id}.{parent}.parent.r{refinement}"]
        arrays["parent_work"][p] = float(parent_delivery.absolute_parent_density_work)
        if parent_delivery.disposition != "COMPLETE":
            if root.numerical_semantics:
                failed_mechanisms.append(parent)
            failed_benchmarks.append(parent)
            continue
        if mode is None or checkpoint is None:
            raise ValueError("complete preparation has no observed handoff or common mode")
        arrays["handoff_features"][p] = _observe(checkpoint, mode, root.landmark)
        state, _ = state_from_checkpoint(checkpoint.native)
        for action in (a for a in preparation_actions(root) if a.parent == parent):
            key = action.action_id.rsplit(f".{parent}.", 1)[1]
            delivered = deliveries[f"{action.action_id}.r{refinement}"]
            if delivered.disposition != "COMPLETE":
                continue
            path = paths[key]
            if not np.array_equal(path["positions"][0], state.positions) or not np.array_equal(
                path["momenta"][0], state.momenta
            ):
                raise ValueError("signed probe did not clone its common handoff")
            if action.magnitude == 8:
                b, s = (*RESPONSE_BUNDLES, "prospective-task").index(action.bundle), action.sign + 1
                response = np.einsum(
                    "sijk,ijk->s", path["positions"][:, 0] - state.positions[0], mode.conj()
                ).real
                arrays["response_path"][p, b, s] = response
                arrays["response"][p, b, s] = response[np.asarray(READOUTS) // 16]
                arrays["delivered"][p, b, s] = 1
        for b, bundle in enumerate((*RESPONSE_BUNDLES, "prospective-task")):
            hold = paths.get(f"{bundle}.a8.hold")
            if hold is None:
                continue
            for s, sign in enumerate(("neg", "hold", "pos")):
                action_path = paths.get(f"{bundle}.a8.{sign}")
                if action_path is not None:
                    status, maxima = preservation(action_path, hold, mode)
                    arrays["preservation"][p, b, s], arrays["preservation_maxima"][p, b, s] = (
                        status,
                        maxima,
                    )
            response = arrays["response"][p, b, :, -1]
            if np.isfinite(response).all():
                odd, even = (
                    (response[2] - response[0]) / 2,
                    (response[2] + response[0]) / 2 - response[1],
                )
                free = 8 * (0.064 - np.exp(-0.256) * (1 - np.exp(-0.064)))
                arrays["contact"][p, b] = int(
                    abs(odd) >= 1 / 32 and abs(even) <= 1 / 32 and abs(odd - free) >= 1 / 128
                )
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                benchmark = privileged_prediction(
                    microscopic_initial(state.positions, state.momenta, mode, quadratic),
                    refinement,
                )
                arrays["privileged_gain"][p] = benchmark.gains[
                    :, np.asarray(READOUTS) * refinement
                ]
                arrays["privileged_covariance_minimum"][p] = (
                    benchmark.minimum_covariance_eigenvalue
                )
                arrays["privileged_symmetry_error"][p] = benchmark.symmetry_error
        except (FloatingPointError, np.linalg.LinAlgError):
            failed_benchmarks.append(parent)
        if root.numerical_semantics:
            if (
                not all(
                    f"common-response.{a}.{s}" in paths
                    for a in ("a05", "a1", "a2", "a8")
                    for s in ("neg", "pos")
                )
                or "common-response.a8.hold" not in paths
            ):
                failed_mechanisms.append(parent)
            else:
                try:
                    with np.errstate(over="raise", invalid="raise", divide="raise"):
                        _mechanism(arrays, p, root, refinement, mode, paths)
                except (FloatingPointError, np.linalg.LinAlgError):
                    failed_mechanisms.append(parent)
        del paths, entry
    if any(values.shape != PROJECTION_SHAPES[key] for key, values in arrays.items()):
        raise ValueError("projection changed a frozen array shape")
    return arrays, tuple(sorted(failed_mechanisms)), tuple(sorted(failed_benchmarks))
