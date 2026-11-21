"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
import importlib
from hashlib import sha256
from io import BytesIO
from typing import Any, Literal
import numpy as np
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity

from empirical_lawhood.domains.matrix.six_matrix_response.observation_order import (
    MatrixObservationOrderAcquisitionDisposition as _science_MatrixObservationOrderAcquisitionDisposition,
    MatrixObservationOrderPairedHistoryRequest as _science_MatrixObservationOrderPairedHistoryRequest,
    MatrixObservationOrderPairedHistoryResult as _science_MatrixObservationOrderPairedHistoryResult,
    MatrixObservationOrderPairedHistorySourceConfig as _science_MatrixObservationOrderPairedHistorySourceConfig,
    OBSERVATION_ORDER_DECODED_HDF5_BYTES as _science_OBSERVATION_ORDER_DECODED_HDF5_BYTES,
    OBSERVATION_ORDER_HDF5_SCHEMA as _science_OBSERVATION_ORDER_HDF5_SCHEMA,
    OBSERVATION_ORDER_MAXIMUM_HDF5_BYTES as _science_OBSERVATION_ORDER_MAXIMUM_HDF5_BYTES,
    _HDF5_CLOCKS,
    _HDF5_FRAMES,
    _HDF5_KEYS,
    _HDF5_UNITS,
    _STATE_SHAPE,
    integrate_observation_order_paired_history as _science_integrate_observation_order_paired_history,
)

def _hdf5(
    config: _science_MatrixObservationOrderPairedHistorySourceConfig,
    request: _science_MatrixObservationOrderPairedHistoryRequest,
    arrays: dict[str, np.ndarray[Any, Any]],
    disposition: _science_MatrixObservationOrderAcquisitionDisposition,
) -> bytes:
    stream = BytesIO()
    h5py = importlib.import_module("h5py")
    with h5py.File(stream, "w", libver="earliest", track_order=False) as handle:
        attrs = {
            "acquisition_group_id": request.slot.acquisition_group_id,
            "compression": "NONE",
            "disposition": disposition.value,
            "history_id": request.slot.history_id,
            "empirical_lawhood_clocks": _HDF5_CLOCKS,
            "empirical_lawhood_frames": _HDF5_FRAMES,
            "empirical_lawhood_keys": _HDF5_KEYS,
            "empirical_lawhood_payload_schema": _science_OBSERVATION_ORDER_HDF5_SCHEMA,
            "empirical_lawhood_units": _HDF5_UNITS,
            "physical_independent_unit_id": request.slot.physical_independent_unit_id,
            "request_fingerprint": request.fingerprint(),
            "source_config_fingerprint": config.fingerprint(),
        }
        for key, value in sorted(attrs.items()):
            encoded = str(value).encode("utf-8")
            handle.attrs.create(key, encoded, dtype=f"S{len(encoded)}")
        for view, count in (("primary", 1025), ("fine", 2049)):
            group = handle.create_group(view, track_order=False)
            group.create_dataset(
                "alpha_tilde", data=arrays[f"{view}_alpha"], track_times=False
            )
            group.create_dataset(
                "momenta", data=arrays[f"{view}_momenta"], track_times=False
            )
            group.create_dataset(
                "positions", data=arrays[f"{view}_positions"], track_times=False
            )
            group.create_dataset(
                "step_index",
                data=np.arange(count, dtype="<i8"),
                track_times=False,
            )
    payload = stream.getvalue()
    if len(payload) > config.maximum_hdf5_bytes:
        raise ValueError("observation order paired HDF5 exceeds its frozen byte bound")
    return payload


def execute_observation_order_paired_history(
    config: _science_MatrixObservationOrderPairedHistorySourceConfig, request: _science_MatrixObservationOrderPairedHistoryRequest
) -> tuple[_science_MatrixObservationOrderPairedHistoryResult, bytes]:
    arrays, disposition, completed_primary, completed_fine, receipts, reasons = _science_integrate_observation_order_paired_history(config, request)
    payload = _hdf5(config, request, arrays, disposition)
    result = _science_MatrixObservationOrderPairedHistoryResult(
        result_id=f"paired-history-result.{request.slot.history_id}",
        request=ObjectIdentity.from_record(request.request_id, request),
        source_config=ObjectIdentity.from_record(config.config_id, config),
        history_id=request.slot.history_id,
        family_id=request.slot.family_id,
        physical_independent_unit_id=request.slot.physical_independent_unit_id,
        acquisition_group_id=request.slot.acquisition_group_id,
        primary_view_id=request.slot.primary_view_id,
        fine_view_id=request.slot.fine_view_id,
        disposition=disposition,
        completed_primary_steps=completed_primary,
        completed_fine_steps=completed_fine,
        hdf5_payload_schema=_science_OBSERVATION_ORDER_HDF5_SCHEMA,
        hdf5_size_bytes=len(payload),
        hdf5_sha256=sha256(payload).hexdigest(),
        decoded_dataset_bytes=_science_OBSERVATION_ORDER_DECODED_HDF5_BYTES,
        seed_receipts=tuple(sorted(receipts)),
        reason_codes=reasons,
        scientific_verdict_constructed=False,
        outcome_access=OutcomeAccess.EVALUATION_SEALED,
    )
    return result, payload


def read_observation_order_paired_history(
    payload: bytes, result: _science_MatrixObservationOrderPairedHistoryResult, view: Literal["primary", "fine"]
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Validate hostile HDF5 structure before returning one bounded view."""

    if (
        len(payload) != result.hdf5_size_bytes
        or sha256(payload).hexdigest() != result.hdf5_sha256
    ):
        raise ValueError("observation order HDF5 custody identity differs")
    if len(payload) > _science_OBSERVATION_ORDER_MAXIMUM_HDF5_BYTES or view not in {"primary", "fine"}:
        raise ValueError("observation order HDF5 request exceeds its bound")
    h5py = importlib.import_module("h5py")
    with h5py.File(BytesIO(payload), "r") as handle:
        if set(handle) != {"fine", "primary"}:
            raise ValueError("observation order HDF5 root inventory differs")
        attrs = {
            key: value.decode("utf-8") if isinstance(value, bytes) else str(value)
            for key, value in handle.attrs.items()
        }
        expected_attrs = {
            "acquisition_group_id": result.acquisition_group_id,
            "compression": "NONE",
            "disposition": result.disposition.value,
            "history_id": result.history_id,
            "empirical_lawhood_clocks": _HDF5_CLOCKS,
            "empirical_lawhood_frames": _HDF5_FRAMES,
            "empirical_lawhood_keys": _HDF5_KEYS,
            "empirical_lawhood_payload_schema": _science_OBSERVATION_ORDER_HDF5_SCHEMA,
            "empirical_lawhood_units": _HDF5_UNITS,
            "physical_independent_unit_id": result.physical_independent_unit_id,
            "request_fingerprint": result.request.object_fingerprint,
            "source_config_fingerprint": result.source_config.object_fingerprint,
        }
        if attrs != expected_attrs:
            raise ValueError("observation order HDF5 metadata differs")
        expected_count = 1025 if view == "primary" else 2049
        group = handle[view]
        if set(group) != {"alpha_tilde", "momenta", "positions", "step_index"}:
            raise ValueError("observation order HDF5 view inventory differs")
        specifications = {
            "alpha_tilde": ((expected_count, 2), np.dtype("<f8")),
            "momenta": ((expected_count, *_STATE_SHAPE), np.dtype("<c16")),
            "positions": ((expected_count, *_STATE_SHAPE), np.dtype("<c16")),
            "step_index": ((expected_count,), np.dtype("<i8")),
        }
        for name, (shape, dtype) in specifications.items():
            dataset = group[name]
            if (
                dataset.shape != shape
                or dataset.dtype != dtype
                or dataset.chunks is not None
                or dataset.compression is not None
            ):
                raise ValueError("observation order HDF5 dataset contract differs")
        if not np.array_equal(
            group["step_index"][:], np.arange(expected_count, dtype="<i8")
        ):
            raise ValueError("observation order HDF5 native step index differs")
        positions = np.asarray(group["positions"][:], dtype="<c16")
        momenta = np.asarray(group["momenta"][:], dtype="<c16")
        alpha = np.asarray(group["alpha_tilde"][:], dtype="<f8")
    return positions, momenta, alpha
