"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
import importlib
from hashlib import sha256
from io import BytesIO
from typing import Any
import numpy as np
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_sha256
from empirical_lawhood.domains.matrix.six_matrix_response.model import ComplexArray, SixMatrixState, hermiticity_residual

from empirical_lawhood.domains.matrix.six_matrix_response.reactive_entrance import (
    REACTIVE_ENTRANCE_HDF5_CLOCKS as _science_REACTIVE_ENTRANCE_HDF5_CLOCKS,
    REACTIVE_ENTRANCE_HDF5_FRAMES as _science_REACTIVE_ENTRANCE_HDF5_FRAMES,
    REACTIVE_ENTRANCE_HDF5_KEYS as _science_REACTIVE_ENTRANCE_HDF5_KEYS,
    REACTIVE_ENTRANCE_HDF5_SCHEMA as _science_REACTIVE_ENTRANCE_HDF5_SCHEMA,
    REACTIVE_ENTRANCE_HDF5_UNITS as _science_REACTIVE_ENTRANCE_HDF5_UNITS,
    SixMatrixResponseReactiveEntranceExecutedPrecursor as _science_SixMatrixResponseReactiveEntranceExecutedPrecursor,
    SixMatrixResponseReactiveEntranceNoiseReceipt as _science_SixMatrixResponseReactiveEntranceNoiseReceipt,
    SixMatrixResponseReactiveEntrancePersistedPrecursor as _science_SixMatrixResponseReactiveEntrancePersistedPrecursor,
    SixMatrixResponseReactiveEntrancePrecursorRequest as _science_SixMatrixResponseReactiveEntrancePrecursorRequest,
    SixMatrixResponseReactiveEntrancePrecursorResult as _science_SixMatrixResponseReactiveEntrancePrecursorResult,
    SixMatrixResponseReactiveEntrancePrecursorTerminal as _science_SixMatrixResponseReactiveEntrancePrecursorTerminal,
    SixMatrixResponseReactiveEntranceSourceConfig as _science_SixMatrixResponseReactiveEntranceSourceConfig,
    _phase_space_sha256,
    integrate_reactive_entrance as _science_integrate_reactive_entrance,
)

def _h5py() -> Any:
    try:
        return importlib.import_module("h5py")
    except ImportError as error:  # pragma: no cover - optional dependency guard
        raise RuntimeError("matrix response reactive entrance HDF5 support requires h5py") from error


def _hdf5_payload(
    *,
    request: _science_SixMatrixResponseReactiveEntrancePrecursorRequest,
    config: _science_SixMatrixResponseReactiveEntranceSourceConfig,
    states: tuple[SixMatrixState, ...],
    innovations: ComplexArray,
    noise: _science_SixMatrixResponseReactiveEntranceNoiseReceipt,
) -> bytes:
    h5py = _h5py()
    positions = np.ascontiguousarray(np.stack([value.positions for value in states]), dtype="<c16")
    momenta = np.ascontiguousarray(np.stack([value.momenta for value in states]), dtype="<c16")
    alpha = np.asarray(
        [(value.alpha_tilde_x, value.alpha_tilde_y) for value in states], dtype="<f8"
    )
    steps = np.asarray([value.step_index for value in states], dtype="<i8")
    standardized = np.ascontiguousarray(innovations, dtype="<c16")
    stream = BytesIO()

    def fixed_utf8(target: Any, name: str, value: str) -> None:
        encoded = value.encode("utf-8")
        target.create(name, encoded, dtype=f"S{len(encoded)}")

    with h5py.File(stream, "w", libver="earliest", track_order=False) as handle:
        root_attributes = {
            "acquisition_group_id": request.acquisition_group_id,
            "bridge_seed_sha256": noise.bridge_seed_sha256 or "NONE",
            "checkpoint_sha256": config.checkpoint.combined_state_sha256,
            "coarse_driver_sha256": noise.coarse_driver_sha256,
            "empirical_lawhood_clocks": _science_REACTIVE_ENTRANCE_HDF5_CLOCKS,
            "empirical_lawhood_frames": _science_REACTIVE_ENTRANCE_HDF5_FRAMES,
            "empirical_lawhood_keys": _science_REACTIVE_ENTRANCE_HDF5_KEYS,
            "empirical_lawhood_payload_schema": _science_REACTIVE_ENTRANCE_HDF5_SCHEMA,
            "empirical_lawhood_units": _science_REACTIVE_ENTRANCE_HDF5_UNITS,
            "numerical_member_id": request.numerical_member_id,
            "physical_independent_unit_id": request.slot.physical_independent_unit_id,
            "realized_innovation_sha256": noise.realized_innovation_sha256,
            "request_fingerprint": request.fingerprint(),
            "scientific_view_id": request.scientific_view_id,
            "source_config_fingerprint": config.fingerprint(),
            "source_seed_sha256": noise.source_seed_sha256,
        }
        for name, value in sorted(root_attributes.items()):
            fixed_utf8(handle.attrs, name, value)
        state_group = handle.create_group("state", track_order=False)
        noise_group = handle.create_group("noise", track_order=False)
        dataset_kwargs = {"track_times": False}
        state_group.create_dataset("positions", data=positions, **dataset_kwargs)
        state_group.create_dataset("momenta", data=momenta, **dataset_kwargs)
        state_group.create_dataset("alpha_tilde", data=alpha, **dataset_kwargs)
        state_group.create_dataset("step_index", data=steps, **dataset_kwargs)
        noise_group.create_dataset("standardized", data=standardized, **dataset_kwargs)
    return stream.getvalue()


def execute_six_matrix_response_reactive_entrance_precursor(
    *, config: _science_SixMatrixResponseReactiveEntranceSourceConfig, request: _science_SixMatrixResponseReactiveEntrancePrecursorRequest
) -> _science_SixMatrixResponseReactiveEntranceExecutedPrecursor:
    config_identity, state_tuple, completed, realized_prefix, noise_receipt, reasons = _science_integrate_reactive_entrance(config=config, request=request)
    hdf5 = _hdf5_payload(
        request=request,
        config=config,
        states=state_tuple,
        innovations=realized_prefix,
        noise=noise_receipt,
    )
    initial = state_tuple[0]
    terminal = state_tuple[-1]
    result = _science_SixMatrixResponseReactiveEntrancePrecursorResult(
        result_id=f"precursor-result.{request.request_id}",
        task_id=request.task_id,
        result_output_id=request.result_output_id,
        trajectory_output_id=request.trajectory_output_id,
        request=ObjectIdentity.from_record(request.request_id, request),
        neutral_request=ObjectIdentity.from_record(
            request.neutral_request.request_id,
            request.neutral_request,
        ),
        source_config=config_identity,
        slot_id=request.slot.slot_id,
        slot_index=request.slot.slot_index,
        physical_independent_unit_id=request.slot.physical_independent_unit_id,
        acquisition_group_id=request.acquisition_group_id,
        scientific_view_id=request.scientific_view_id,
        numerical_member_id=request.numerical_member_id,
        numerical_view_kind=request.numerical_view_kind,
        terminal=(
            _science_SixMatrixResponseReactiveEntrancePrecursorTerminal.COMPLETED
            if completed == request.integration_steps and not reasons
            else _science_SixMatrixResponseReactiveEntrancePrecursorTerminal.NUMERICAL_INVALID
        ),
        completed_steps=completed,
        total_steps=request.integration_steps,
        state_count=len(state_tuple),
        initial_positions_sha256=sha256(initial.positions.tobytes()).hexdigest(),
        initial_momenta_sha256=sha256(initial.momenta.tobytes()).hexdigest(),
        terminal_positions_sha256=sha256(terminal.positions.tobytes()).hexdigest(),
        terminal_momenta_sha256=sha256(terminal.momenta.tobytes()).hexdigest(),
        phase_space_sha256=_phase_space_sha256(state_tuple),
        noise=noise_receipt,
        hdf5_payload_schema=_science_REACTIVE_ENTRANCE_HDF5_SCHEMA,
        hdf5_physical_sha256=sha256(hdf5).hexdigest(),
        hdf5_size_bytes=len(hdf5),
        scientific_verdict_constructed=False,
        reason_codes=tuple(sorted(reasons)),
        evidence_ceiling=EvidenceCeiling.MEASUREMENT,
        outcome_access=OutcomeAccess.EVALUATION_SEALED,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        grants_authority=False,
    )
    return _science_SixMatrixResponseReactiveEntranceExecutedPrecursor(
        result=result,
        hdf5_payload=hdf5,
        states=state_tuple,
        innovations=realized_prefix,
    )


def decode_six_matrix_response_reactive_entrance_hdf5(
    *, payload: bytes, result: _science_SixMatrixResponseReactiveEntrancePrecursorResult
) -> _science_SixMatrixResponseReactiveEntrancePersistedPrecursor:
    """Strictly reconstruct one externally persisted precursor path."""

    if (
        len(payload) != result.hdf5_size_bytes
        or sha256(payload).hexdigest() != result.hdf5_physical_sha256
    ):
        raise ValueError("matrix response reactive entrance HDF5 physical identity differs")
    h5py = _h5py()
    with h5py.File(BytesIO(payload), "r") as handle:
        expected_objects = {
            "noise",
            "noise/standardized",
            "state",
            "state/alpha_tilde",
            "state/momenta",
            "state/positions",
            "state/step_index",
        }
        observed: set[str] = set()
        handle.visit(observed.add)
        if observed != expected_objects:
            raise ValueError("matrix response reactive entrance HDF5 object inventory differs")
        expected_attrs = {
            "empirical_lawhood_clocks": _science_REACTIVE_ENTRANCE_HDF5_CLOCKS,
            "empirical_lawhood_frames": _science_REACTIVE_ENTRANCE_HDF5_FRAMES,
            "empirical_lawhood_keys": _science_REACTIVE_ENTRANCE_HDF5_KEYS,
            "empirical_lawhood_payload_schema": _science_REACTIVE_ENTRANCE_HDF5_SCHEMA,
            "empirical_lawhood_units": _science_REACTIVE_ENTRANCE_HDF5_UNITS,
            "request_fingerprint": result.request.object_fingerprint,
            "source_config_fingerprint": result.source_config.object_fingerprint,
            "physical_independent_unit_id": result.physical_independent_unit_id,
            "acquisition_group_id": result.acquisition_group_id,
            "scientific_view_id": result.scientific_view_id,
            "numerical_member_id": result.numerical_member_id,
            "source_seed_sha256": result.noise.source_seed_sha256,
            "bridge_seed_sha256": result.noise.bridge_seed_sha256 or "NONE",
            "coarse_driver_sha256": result.noise.coarse_driver_sha256,
            "realized_innovation_sha256": result.noise.realized_innovation_sha256,
        }
        if set(handle.attrs) != {*expected_attrs, "checkpoint_sha256"}:
            raise ValueError("matrix response reactive entrance HDF5 root attribute inventory differs")
        for name, expected in expected_attrs.items():
            observed = handle.attrs.get(name)
            if isinstance(observed, (bytes, np.bytes_)):
                observed = bytes(observed).rstrip(b"\0").decode("utf-8")
            if str(observed) != expected:
                raise ValueError(f"matrix response reactive entrance HDF5 root attribute differs: {name}")
        checkpoint_sha256 = handle.attrs["checkpoint_sha256"]
        if isinstance(checkpoint_sha256, (bytes, np.bytes_)):
            checkpoint_sha256 = bytes(checkpoint_sha256).rstrip(b"\0").decode("utf-8")
        validate_sha256(str(checkpoint_sha256), field_name="checkpoint_sha256")
        positions = np.asarray(handle["state/positions"], dtype="<c16")
        momenta = np.asarray(handle["state/momenta"], dtype="<c16")
        alpha = np.asarray(handle["state/alpha_tilde"], dtype="<f8")
        steps = np.asarray(handle["state/step_index"], dtype="<i8")
        innovations = np.asarray(handle["noise/standardized"], dtype="<c16")
    expected_state_shape = (result.state_count, 2, 3, 4, 4)
    if (
        positions.shape != expected_state_shape
        or momenta.shape != expected_state_shape
        or alpha.shape != (result.state_count, 2)
        or steps.shape != (result.state_count,)
        or tuple(int(value) for value in steps) != tuple(range(result.state_count))
        or innovations.shape != (result.completed_steps, 2, 3, 4, 4)
        or not all(np.isfinite(value).all() for value in (positions, momenta, alpha, innovations))
        or hermiticity_residual(positions) > 1e-10
        or hermiticity_residual(momenta) > 1e-10
        or hermiticity_residual(innovations) > 1e-10
    ):
        raise ValueError("matrix response reactive entrance HDF5 dataset geometry differs")
    states = tuple(
        SixMatrixState(
            q=2,
            positions=positions[index],
            momenta=momenta[index],
            step_index=int(steps[index]),
            alpha_tilde_x=float(alpha[index, 0]),
            alpha_tilde_y=float(alpha[index, 1]),
        )
        for index in range(result.state_count)
    )
    if (
        sha256(states[0].positions.tobytes()).hexdigest() != result.initial_positions_sha256
        or sha256(states[0].momenta.tobytes()).hexdigest() != result.initial_momenta_sha256
        or sha256(states[-1].positions.tobytes()).hexdigest() != result.terminal_positions_sha256
        or sha256(states[-1].momenta.tobytes()).hexdigest() != result.terminal_momenta_sha256
        or _phase_space_sha256(states) != result.phase_space_sha256
        or sha256(innovations.tobytes()).hexdigest() != result.noise.realized_innovation_sha256
    ):
        raise ValueError("matrix response reactive entrance HDF5 scientific bytes differ from custody")
    return _science_SixMatrixResponseReactiveEntrancePersistedPrecursor(
        result=result,
        states=states,
        innovations=np.ascontiguousarray(innovations, dtype="<c16"),
    )
