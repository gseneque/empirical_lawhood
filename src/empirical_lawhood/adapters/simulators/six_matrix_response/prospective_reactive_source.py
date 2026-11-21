"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
import importlib
from hashlib import sha256
from io import BytesIO
from typing import Any
import numpy as np
from empirical_lawhood.domains.matrix.six_matrix_response.model import ComplexArray, SixMatrixState, hermiticity_residual
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity

from empirical_lawhood.domains.matrix.six_matrix_response.prospective_reactive_source import (
    ProspectiveReactiveSourceLawRoutingService as _science_ProspectiveReactiveSourceLawRoutingService,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_FUTURE_STEPS as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_FUTURE_STEPS,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_CLOCKS as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_CLOCKS,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_FRAMES as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_FRAMES,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_KEYS as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_KEYS,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_SCHEMA as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_SCHEMA,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_UNITS as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_UNITS,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HOLD_STEPS as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HOLD_STEPS,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_PREPARATION_STEPS as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_PREPARATION_STEPS,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_TARGET_X as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_TARGET_X,
    SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_TARGET_Y as _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_TARGET_Y,
    SixMatrixResponseProspectiveReactiveSourceLawHistoryRequest as _science_SixMatrixResponseProspectiveReactiveSourceLawHistoryRequest,
    SixMatrixResponseProspectiveReactiveSourceLawHistoryResult as _science_SixMatrixResponseProspectiveReactiveSourceLawHistoryResult,
    SixMatrixResponseProspectiveReactiveSourceLawHistoryTerminal as _science_SixMatrixResponseProspectiveReactiveSourceLawHistoryTerminal,
    SixMatrixResponseProspectiveReactiveSourceLawNumericalView as _science_SixMatrixResponseProspectiveReactiveSourceLawNumericalView,
    SixMatrixResponseProspectiveReactiveSourceLawPersistedHistory as _science_SixMatrixResponseProspectiveReactiveSourceLawPersistedHistory,
    SixMatrixResponseProspectiveReactiveSourceLawRouting as _science_SixMatrixResponseProspectiveReactiveSourceLawRouting,
    SixMatrixResponseProspectiveReactiveSourceLawSourceConfig as _science_SixMatrixResponseProspectiveReactiveSourceLawSourceConfig,
    _MATRIX_SHAPE,
    integrate_reactive_source_history as _science_integrate_reactive_source_history,
)

def _h5py() -> Any:
    return importlib.import_module("h5py")


def _hdf5(
    *,
    config: _science_SixMatrixResponseProspectiveReactiveSourceLawSourceConfig,
    request: _science_SixMatrixResponseProspectiveReactiveSourceLawHistoryRequest,
    routing: _science_SixMatrixResponseProspectiveReactiveSourceLawRouting,
    history_states: tuple[SixMatrixState, ...],
    history_noise: ComplexArray,
    routing_states: tuple[SixMatrixState, ...],
    branch_states: tuple[tuple[SixMatrixState, ...], ...],
    branch_noise: ComplexArray,
) -> bytes:
    stream = BytesIO()
    h5py = _h5py()
    positions = np.ascontiguousarray(
        np.stack([value.positions for value in history_states]), dtype="<c16"
    )
    momenta = np.ascontiguousarray(
        np.stack([value.momenta for value in history_states]), dtype="<c16"
    )
    alpha = np.asarray(
        [(value.alpha_tilde_x, value.alpha_tilde_y) for value in history_states], dtype="<f8"
    )
    routing_positions = np.ascontiguousarray(
        np.stack([value.positions for value in routing_states]), dtype="<c16"
    )
    routing_momenta = np.ascontiguousarray(
        np.stack([value.momenta for value in routing_states]), dtype="<c16"
    )
    routing_alpha = np.asarray(
        [(value.alpha_tilde_x, value.alpha_tilde_y) for value in routing_states], dtype="<f8"
    )
    branch_positions = np.ascontiguousarray(
        np.stack([[value.positions for value in path] for path in branch_states])
        if branch_states
        else np.empty(
            (
                0,
                1
                + _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_FUTURE_STEPS
                * (1 if request.numerical_view is _science_SixMatrixResponseProspectiveReactiveSourceLawNumericalView.PRIMARY else 2),
                *_MATRIX_SHAPE,
            ),
            dtype="<c16",
        ),
        dtype="<c16",
    )
    branch_momenta = np.ascontiguousarray(
        np.stack([[value.momenta for value in path] for path in branch_states])
        if branch_states
        else np.empty_like(branch_positions),
        dtype="<c16",
    )
    with h5py.File(stream, "w", libver="earliest", track_order=False) as handle:
        attrs = {
            "empirical_lawhood_clocks": _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_CLOCKS,
            "empirical_lawhood_frames": _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_FRAMES,
            "empirical_lawhood_keys": _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_KEYS,
            "empirical_lawhood_payload_schema": _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_SCHEMA,
            "empirical_lawhood_units": _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_UNITS,
            "source_config_fingerprint": config.fingerprint(),
            "request_fingerprint": request.fingerprint(),
            "routing_fingerprint": routing.fingerprint(),
            "physical_independent_unit_id": request.slot.physical_independent_unit_id,
            "compression": "gzip-1",
        }
        for key, value in sorted(attrs.items()):
            handle.attrs.create(key, str(value).encode(), dtype=f"S{len(str(value).encode())}")
        history = handle.create_group("history", track_order=False)
        routing_group = handle.create_group("routing", track_order=False)
        future = handle.create_group("future", track_order=False)
        kwargs = {
            "compression": "gzip",
            "compression_opts": 1,
            "shuffle": False,
            "track_times": False,
        }
        history.create_dataset("positions", data=positions, **kwargs)
        history.create_dataset("momenta", data=momenta, **kwargs)
        history.create_dataset("alpha_tilde", data=alpha, **kwargs)
        history.create_dataset(
            "innovations", data=np.asarray(history_noise, dtype="<c16"), **kwargs
        )
        history.create_dataset(
            "step_index", data=np.arange(len(history_states), dtype="<i8"), track_times=False
        )
        routing_group.create_dataset("positions", data=routing_positions, **kwargs)
        routing_group.create_dataset("momenta", data=routing_momenta, **kwargs)
        routing_group.create_dataset("alpha_tilde", data=routing_alpha, **kwargs)
        future.create_dataset("positions", data=branch_positions, **kwargs)
        future.create_dataset("momenta", data=branch_momenta, **kwargs)
        future.create_dataset("innovations", data=np.asarray(branch_noise, dtype="<c16"), **kwargs)
        future.create_dataset(
            "checkpoint_step",
            data=np.asarray([value.checkpoint_step for value in routing.branches], dtype="<i8"),
            track_times=False,
        )
        future.create_dataset(
            "future_index",
            data=np.asarray([value.future_index for value in routing.branches], dtype="<i8"),
            track_times=False,
        )
        arm = np.asarray([value.arm.value.encode() for value in routing.branches], dtype="S11")
        future.create_dataset("arm", data=arm, track_times=False)
    return stream.getvalue()


def execute_six_matrix_response_reactive_source_history(
    *,
    config: _science_SixMatrixResponseProspectiveReactiveSourceLawSourceConfig,
    request: _science_SixMatrixResponseProspectiveReactiveSourceLawHistoryRequest,
    routing_service: _science_ProspectiveReactiveSourceLawRoutingService | None,
) -> tuple[_science_SixMatrixResponseProspectiveReactiveSourceLawHistoryResult, bytes]:
    routing, states, innovations, routing_states, branches, branch_noise, reasons = _science_integrate_reactive_source_history(config=config, request=request, routing_service=routing_service)
    payload = _hdf5(
        config=config,
        request=request,
        routing=routing,
        history_states=states,
        history_noise=innovations,
        routing_states=routing_states,
        branch_states=branches,
        branch_noise=branch_noise,
    )
    result = _science_SixMatrixResponseProspectiveReactiveSourceLawHistoryResult(
        result_id=f"history-result.{request.task_id}",
        task_id=request.task_id,
        request=ObjectIdentity.from_record(request.request_id, request),
        neutral_request=ObjectIdentity.from_record(
            request.neutral_request.request_id, request.neutral_request
        ),
        source_config=ObjectIdentity.from_record(config.config_id, config),
        slot_id=request.slot.slot_id,
        history_index=request.slot.history_index,
        family_id=request.slot.family_id,
        physical_independent_unit_id=request.slot.physical_independent_unit_id,
        acquisition_group_id=request.acquisition_group_id,
        scientific_view_id=request.scientific_view_id,
        numerical_view=request.numerical_view,
        routing=routing,
        routing_sha256=routing.fingerprint(),
        history_state_count=len(states),
        branch_count=len(branches),
        terminal=_science_SixMatrixResponseProspectiveReactiveSourceLawHistoryTerminal.COMPLETE,
        hdf5_payload_schema=_science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_SCHEMA,
        hdf5_physical_sha256=sha256(payload).hexdigest(),
        hdf5_size_bytes=len(payload),
        reason_codes=tuple(sorted(reasons)),
        scientific_verdict_constructed=False,
        outcome_access=OutcomeAccess.EVALUATION_SEALED,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
    )
    return result, payload


def decode_six_matrix_response_reactive_source_hdf5(
    payload: bytes, result: _science_SixMatrixResponseProspectiveReactiveSourceLawHistoryResult
) -> _science_SixMatrixResponseProspectiveReactiveSourceLawPersistedHistory:
    """Strictly reconstruct the complete history and future panel."""

    if (
        len(payload) != result.hdf5_size_bytes
        or sha256(payload).hexdigest() != result.hdf5_physical_sha256
    ):
        raise ValueError("matrix response prospective reactive source law HDF5 physical identity differs")
    h5py = _h5py()
    with h5py.File(BytesIO(payload), "r") as handle:
        observed: set[str] = set()
        handle.visit(observed.add)
        expected = {
            "future",
            "future/arm",
            "future/checkpoint_step",
            "future/future_index",
            "future/innovations",
            "future/momenta",
            "future/positions",
            "history",
            "history/alpha_tilde",
            "history/innovations",
            "history/momenta",
            "history/positions",
            "history/step_index",
            "routing",
            "routing/alpha_tilde",
            "routing/momenta",
            "routing/positions",
        }
        if observed != expected:
            raise ValueError("matrix response prospective reactive source law HDF5 inventory differs")
        attrs = {key: bytes(value).rstrip(b"\0").decode() for key, value in handle.attrs.items()}
        if (
            attrs.get("empirical_lawhood_payload_schema") != _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HDF5_SCHEMA
            or attrs.get("routing_fingerprint") != result.routing_sha256
        ):
            raise ValueError("matrix response prospective reactive source law HDF5 custody attributes differ")
        hp = np.asarray(handle["history/positions"], dtype="<c16")
        hm = np.asarray(handle["history/momenta"], dtype="<c16")
        ha = np.asarray(handle["history/alpha_tilde"], dtype="<f8")
        hn = np.asarray(handle["history/innovations"], dtype="<c16")
        hs = np.asarray(handle["history/step_index"], dtype="<i8")
        rp = np.asarray(handle["routing/positions"], dtype="<c16")
        rm = np.asarray(handle["routing/momenta"], dtype="<c16")
        ra = np.asarray(handle["routing/alpha_tilde"], dtype="<f8")
        bp = np.asarray(handle["future/positions"], dtype="<c16")
        bm = np.asarray(handle["future/momenta"], dtype="<c16")
        bn = np.asarray(handle["future/innovations"], dtype="<c16")
        checkpoints = tuple(map(int, np.asarray(handle["future/checkpoint_step"], dtype="<i8")))
        futures = tuple(map(int, np.asarray(handle["future/future_index"], dtype="<i8")))
        arms = tuple(
            bytes(value).rstrip(b"\0").decode() for value in np.asarray(handle["future/arm"])
        )
    multiplier = 1 if result.numerical_view is _science_SixMatrixResponseProspectiveReactiveSourceLawNumericalView.PRIMARY else 2
    if (
        hp.shape != (result.history_state_count, *_MATRIX_SHAPE)
        or hm.shape != hp.shape
        or ha.shape != (result.history_state_count, 2)
        or hn.shape != (result.history_state_count - 1, *_MATRIX_SHAPE)
        or tuple(map(int, hs)) != tuple(range(result.history_state_count))
        or rp.shape != (1 + _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_PREPARATION_STEPS + _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_HOLD_STEPS, *_MATRIX_SHAPE)
        or rm.shape != rp.shape
        or ra.shape != (rp.shape[0], 2)
        or bp.shape != (result.branch_count, 1 + _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_FUTURE_STEPS * multiplier, *_MATRIX_SHAPE)
        or bm.shape != bp.shape
        or bn.shape != (result.branch_count, _science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_FUTURE_STEPS * multiplier, *_MATRIX_SHAPE)
        or tuple((arms[i], checkpoints[i], futures[i]) for i in range(result.branch_count))
        != tuple(
            (value.arm.value, value.checkpoint_step, value.future_index)
            for value in result.routing.branches
        )
        or not all(np.isfinite(value).all() for value in (hp, hm, ha, hn, rp, rm, ra, bp, bm, bn))
        or hermiticity_residual(hp) > 1e-10
        or hermiticity_residual(hm) > 1e-10
    ):
        raise ValueError("matrix response prospective reactive source law HDF5 geometry differs")
    history_states = tuple(
        SixMatrixState(
            q=2,
            positions=hp[i],
            momenta=hm[i],
            step_index=i,
            alpha_tilde_x=float(ha[i, 0]),
            alpha_tilde_y=float(ha[i, 1]),
        )
        for i in range(result.history_state_count)
    )
    branch_states = tuple(
        tuple(
            SixMatrixState(
                q=2,
                positions=bp[j, i],
                momenta=bm[j, i],
                step_index=i,
                alpha_tilde_x=float(_science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_TARGET_X),
                alpha_tilde_y=float(_science_SIX_MATRIX_PROSPECTIVE_SOURCE_LAW_TARGET_Y),
            )
            for i in range(bp.shape[1])
        )
        for j in range(result.branch_count)
    )
    routing_states = tuple(
        SixMatrixState(
            q=2,
            positions=rp[i],
            momenta=rm[i],
            step_index=i,
            alpha_tilde_x=float(ra[i, 0]),
            alpha_tilde_y=float(ra[i, 1]),
        )
        for i in range(rp.shape[0])
    )
    return _science_SixMatrixResponseProspectiveReactiveSourceLawPersistedHistory(result, history_states, hn, routing_states, branch_states, bn)
