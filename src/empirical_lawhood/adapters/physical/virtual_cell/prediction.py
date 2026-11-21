"""Deterministic, bounded construction of 2025 prediction H5AD payloads."""

from __future__ import annotations

import csv
from decimal import Decimal
import hashlib
import io
from pathlib import Path

import h5py  # type: ignore[import-untyped]
import numpy as np
from numpy.typing import NDArray

from empirical_lawhood.science.records.serialization import validate_sha256

from empirical_lawhood.domains.biology.virtual_cell.contracts import VirtualCellContractError
from empirical_lawhood.domains.biology.virtual_cell.response_summary import ControlReservoirArrays
from empirical_lawhood.domains.biology.virtual_cell import prediction as scientific
from empirical_lawhood.domains.biology.virtual_cell.prediction import CELL_EVAL_LOG1P_MAXIMUM, PredictionRoster, PredictionMeanCompilation, PredictionH5ADBuildReceipt


MAXIMUM_PERTURBATION_ROSTER_BYTES = 1024**2


def _strict_roster_rows(payload: bytes) -> tuple[tuple[str, int, Decimal], ...]:
    if len(payload) > MAXIMUM_PERTURBATION_ROSTER_BYTES:
        raise VirtualCellContractError("perturbation roster exceeds its byte bound")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VirtualCellContractError("perturbation roster is not UTF-8") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    expected = ("target_gene", "n_cells", "median_umi_per_cell")
    if tuple(reader.fieldnames or ()) != expected:
        raise VirtualCellContractError("perturbation roster header differs")
    rows: list[tuple[str, int, Decimal]] = []
    try:
        for row in reader:
            if set(row) != set(expected):
                raise VirtualCellContractError("perturbation roster row shape differs")
            target = row["target_gene"]
            if not target or target.strip() != target:
                raise VirtualCellContractError("perturbation target is invalid")
            count = int(row["n_cells"])
            median = Decimal(row["median_umi_per_cell"])
            if count <= 0 or not median.is_finite() or median <= 0:
                raise VirtualCellContractError("perturbation roster values are invalid")
            rows.append((target, count, median))
    except (ArithmeticError, TypeError, ValueError) as error:
        raise VirtualCellContractError(
            "perturbation roster numeric value is invalid"
        ) from error
    if not rows or len({value[0] for value in rows}) != len(rows):
        raise VirtualCellContractError("perturbation roster is empty or duplicated")
    return tuple(sorted(rows))


def build_prediction_roster(
    payload: bytes,
    *,
    roster_id: str,
    expected_target_count: int,
    total_cell_limit: int,
    control_cells: int,
    minimum_cells_per_target: int,
    control_label: str = "non-targeting",
) -> PredictionRoster:
    """Allocate the exact H5AD row budget by deterministic largest remainder."""

    rows = _strict_roster_rows(payload)
    return scientific.allocate_prediction_roster(
        rows, prefix_source_sha256=hashlib.sha256(payload).hexdigest(),
        roster_id=roster_id, expected_target_count=expected_target_count,
        total_cell_limit=total_cell_limit, control_cells=control_cells,
        minimum_cells_per_target=minimum_cells_per_target, control_label=control_label,
    )


def _registry_sha256(values: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for value in values:
        payload = value.encode("utf-8")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _array_sha256(values: NDArray[np.float64]) -> str:
    data = np.ascontiguousarray(values, dtype="<f8")
    digest = hashlib.sha256()
    digest.update(str(data.shape).encode("ascii"))
    digest.update(data.tobytes())
    return digest.hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 * 1024**2):
            digest.update(chunk)
    return digest.hexdigest()


def _write_string_array(group: h5py.Group, name: str, values: tuple[str, ...]) -> None:
    dtype = h5py.string_dtype(encoding="utf-8")
    dataset = group.create_dataset(
        name, data=np.asarray(values, dtype=object), dtype=dtype
    )
    dataset.attrs["encoding-type"] = "string-array"
    dataset.attrs["encoding-version"] = "0.2.0"


def _write_dataframe(
    group: h5py.Group,
    *,
    index_values: tuple[str, ...],
    columns: tuple[tuple[str, tuple[str, ...]], ...],
) -> None:
    group.attrs["encoding-type"] = "dataframe"
    group.attrs["encoding-version"] = "0.2.0"
    group.attrs["_index"] = "_index"
    group.attrs["column-order"] = np.asarray(
        [name for name, _values in columns],
        dtype=h5py.string_dtype("utf-8"),
    )
    _write_string_array(group, "_index", index_values)
    for name, values in columns:
        _write_string_array(group, name, values)


def write_historical_mean_preserving_prediction_h5ad(
    *,
    path: Path,
    roster: PredictionRoster,
    gene_ids: tuple[str, ...],
    predicted_means: PredictionMeanCompilation,
    control_reservoir: ControlReservoirArrays,
    control_reservoir_sha256: str,
    seed: int,
    mean_tolerance: float,
    maximum_value: float = CELL_EVAL_LOG1P_MAXIMUM,
) -> PredictionH5ADBuildReceipt:
    """Preservation-only original compiler; this is not the selected v2 method."""

    if path.exists() or path.is_symlink():
        raise VirtualCellContractError(
            "prediction H5AD destination must not already exist"
        )
    validate_sha256(control_reservoir_sha256, field_name="control_reservoir_sha256")
    prepared = scientific.prepare_historical_prediction(
        roster=roster, gene_ids=gene_ids, predicted_means=predicted_means,
        control_reservoir=control_reservoir, seed=seed, mean_tolerance=mean_tolerance,
        maximum_value=maximum_value,
    )
    cell_target_ids: list[str] = []
    try:
        with h5py.File(path, "x") as handle:
            handle.attrs["encoding-type"] = "anndata"
            handle.attrs["encoding-version"] = "0.1.0"
            matrix = handle.create_dataset(
                "X",
                shape=(roster.total_cells, len(gene_ids)),
                dtype=np.float32,
                chunks=(min(256, roster.total_cells), min(2048, len(gene_ids))),
                compression="lzf",
            )
            matrix.attrs["encoding-type"] = "array"
            matrix.attrs["encoding-version"] = "0.2.0"
            offset = 0
            control_values = prepared.control_values
            matrix[offset : offset + roster.control_cells, :] = control_values
            cell_target_ids.extend([roster.control_label] * roster.control_cells)
            offset += roster.control_cells
            for target_index, allocation in enumerate(roster.targets):
                values = prepared.compile_target(target_index=target_index, allocation=allocation)
                matrix[offset : offset + allocation.allocated_cells, :] = values
                cell_target_ids.extend(
                    [allocation.target_id] * allocation.allocated_cells
                )
                offset += allocation.allocated_cells
            if offset != roster.total_cells:
                raise VirtualCellContractError(
                    "prediction compiler failed row closure or mean preservation"
                )
            prepared.require_mean_preservation(mean_tolerance)
            obs_index = tuple(f"prediction-cell-{index:06d}" for index in range(offset))
            _write_dataframe(
                handle.create_group("obs"),
                index_values=obs_index,
                columns=(("target_gene", tuple(cell_target_ids)),),
            )
            _write_dataframe(
                handle.create_group("var"),
                index_values=gene_ids,
                columns=(),
            )
            for name in ("layers", "obsm", "obsp", "uns", "varm", "varp"):
                group = handle.create_group(name)
                group.attrs["encoding-type"] = "dict"
                group.attrs["encoding-version"] = "0.1.0"
    except VirtualCellContractError:
        raise
    except (OSError, TypeError, ValueError) as error:
        raise VirtualCellContractError(
            "prediction H5AD construction failed closed"
        ) from error
    h5ad_sha256 = _file_sha256(path)
    return PredictionH5ADBuildReceipt(
        receipt_id="prediction-h5ad.virtual-cell-2025-tier-l0",
        roster_sha256=roster.fingerprint(),
        predicted_mean_sha256=_array_sha256(predicted_means.absolute_means),
        control_reservoir_sha256=control_reservoir_sha256,
        gene_order_sha256=_registry_sha256(gene_ids),
        h5ad_sha256=h5ad_sha256,
        row_count=roster.total_cells,
        gene_count=len(gene_ids),
        target_count=len(roster.targets),
        control_cell_count=roster.control_cells,
        seed=seed,
        maximum_mean_error=Decimal(str(prepared.maximum_mean_error)),
        maximum_value=Decimal(str(maximum_value)),
        output_dtype="float32",
        outcome_read=False,
    )


__all__ = [
    "MAXIMUM_PERTURBATION_ROSTER_BYTES",
    "build_prediction_roster",
    "write_historical_mean_preserving_prediction_h5ad",
]
