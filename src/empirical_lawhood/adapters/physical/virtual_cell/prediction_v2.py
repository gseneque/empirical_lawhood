# SPDX-License-Identifier: MPL-2.0
"""Selected shared-template-shift v2, adapted from donor 859ed3b1.

Rows are numerical views for the pinned marginal Wilcoxon/global-BH receiver,
not biological replicates or a qualified single-cell generative model. Current
source adaptation is software conformance; donor scientific artifacts are not
relabeled or requalified. Whole-action admission precedes output creation.
"""

from decimal import Decimal
from pathlib import Path

import h5py
import numpy as np
from numpy.typing import NDArray

from empirical_lawhood.science.records.serialization import validate_sha256
from empirical_lawhood.domains.biology.virtual_cell.contracts import VirtualCellContractError
from empirical_lawhood.domains.biology.virtual_cell.correction_records_v2 import SharedTemplateShiftV2BuildReceipt as _SharedTemplateShiftV2BuildReceipt, SharedTemplateShiftV2Selection as _SharedTemplateShiftV2Selection
from empirical_lawhood.domains.biology.virtual_cell.response_summary import ControlReservoirArrays
from empirical_lawhood.domains.biology.virtual_cell.prediction import PredictionRoster
from empirical_lawhood.adapters.physical.virtual_cell.prediction import _array_sha256, _file_sha256, _registry_sha256, _write_dataframe
from empirical_lawhood.domains.biology.virtual_cell import prediction_v2 as scientific


def write_shared_template_shift_v2_prediction_h5ad(
    *,
    path: Path,
    roster: PredictionRoster,
    gene_ids: tuple[str, ...],
    predicted_deltas: NDArray[np.float64],
    control_reservoir: ControlReservoirArrays,
    control_reservoir_sha256: str,
    seed: int,
    selection: _SharedTemplateShiftV2Selection,
) -> _SharedTemplateShiftV2BuildReceipt:
    """Write a receiver-specific v2 H5AD and fail closed before partial output."""

    if path.exists() or path.is_symlink():
        raise VirtualCellContractError("v2 prediction H5AD destination must not already exist")
    validate_sha256(control_reservoir_sha256, field_name="control_reservoir_sha256")
    prepared = scientific.admit_shared_template_shift_v2_prediction(
        roster=roster, gene_ids=gene_ids, predicted_deltas=predicted_deltas,
        control_reservoir=control_reservoir, seed=seed, selection=selection,
    )
    cell_target_ids: list[str] = [roster.control_label] * roster.control_cells
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
            matrix[: roster.control_cells, :] = prepared.control
            offset = roster.control_cells
            # Retain one target population at a time rather than all H5AD rows.
            for index, allocation in enumerate(roster.targets):
                compilation = prepared.compile_target(target_index=index, allocation=allocation)
                stop = offset + allocation.allocated_cells
                matrix[offset:stop, :] = compilation.values
                cell_target_ids.extend(
                    [allocation.target_id] * allocation.allocated_cells
                )
                offset = stop
            if offset != roster.total_cells:
                raise VirtualCellContractError("v2 compiler failed exact row closure")
            obs_index = tuple(f"prediction-cell-{index:06d}" for index in range(offset))
            _write_dataframe(
                handle.create_group("obs"),
                index_values=obs_index,
                columns=(("target_gene", tuple(cell_target_ids)),),
            )
            _write_dataframe(
                handle.create_group("var"), index_values=gene_ids, columns=()
            )
            for name in ("layers", "obsm", "obsp", "uns", "varm", "varp"):
                group = handle.create_group(name)
                group.attrs["encoding-type"] = "dict"
                group.attrs["encoding-version"] = "0.1.0"
    except VirtualCellContractError:
        raise
    except (OSError, TypeError, ValueError) as error:
        raise VirtualCellContractError(
            "v2 prediction H5AD construction failed closed"
        ) from error
    return _SharedTemplateShiftV2BuildReceipt(
        selection_sha256=selection.fingerprint(),
        receipt_id="prediction-h5ad.virtual-cell-2025-shared-template-shift-v2",
        compiler_id="compiler.virtual-cell-2025-shared-template-shift-v2",
        receiver_id="receiver.virtual-cell-2025-pdex-marginal-wilcoxon-v1",
        roster_sha256=roster.fingerprint(),
        predicted_delta_sha256=_array_sha256(prepared.predicted_deltas),
        control_reservoir_sha256=control_reservoir_sha256,
        template_sha256=_array_sha256(np.asarray(prepared.template, dtype=np.float64)),
        gene_order_sha256=_registry_sha256(gene_ids),
        h5ad_sha256=_file_sha256(path),
        row_count=roster.total_cells,
        gene_count=len(gene_ids),
        target_count=len(roster.targets),
        control_cell_count=roster.control_cells,
        seed=seed,
        maximum_null_mean_error=Decimal(str(prepared.maximum_null_error)),
        maximum_action_error=Decimal(str(prepared.maximum_action_error)),
        saturated_value_count=prepared.saturated_count,
        saturated_value_fraction=prepared.saturated_fraction,
        maximum_value=Decimal(str(prepared.maximum_value)),
        output_dtype="float32",
        outcome_read=False,
    )
