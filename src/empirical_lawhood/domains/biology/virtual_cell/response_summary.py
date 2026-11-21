# SPDX-License-Identifier: MPL-2.0
"""In-memory scientific response and nested-cell reservoir contracts."""

from dataclasses import dataclass
import math
import numpy as np
from numpy.typing import NDArray
from empirical_lawhood.science.records.serialization import validate_nonempty
from empirical_lawhood.domains.biology.virtual_cell.contracts import VirtualCellContractError


def _require_positive_integer(value: int, *, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")



@dataclass(frozen=True, slots=True)
class ResponseSummaryArrays:
    """In-memory target/batch sufficient statistics for pure analysis code."""

    group_ids: tuple[str, ...]
    target_ids: tuple[str, ...]
    batch_ids: tuple[str, ...]
    gene_ids: tuple[str, ...]
    normalization: str
    normalization_target_sum: float | None
    cell_counts: NDArray[np.int64]
    means: NDArray[np.float64]
    variances: NDArray[np.float64]

    def __post_init__(self) -> None:
        group_count = len(self.group_ids)
        gene_count = len(self.gene_ids)
        if group_count == 0 or gene_count == 0:
            raise ValueError("response summary cannot be empty")
        if self.normalization not in {"source", "log1p-cp10000", "log1p-fixed-total"}:
            raise ValueError("response summary normalization is unknown")
        if self.normalization == "log1p-fixed-total":
            if (
                self.normalization_target_sum is None
                or not math.isfinite(self.normalization_target_sum)
                or self.normalization_target_sum <= 0
            ):
                raise ValueError("fixed-total response summary lacks a positive target sum")
        elif self.normalization_target_sum is not None:
            raise ValueError("only fixed-total summaries may carry a normalization target")
        if not (
            len(self.target_ids) == len(self.batch_ids) == group_count
            and self.cell_counts.shape == (group_count,)
            and self.means.shape == (group_count, gene_count)
            and self.variances.shape == (group_count, gene_count)
        ):
            raise ValueError("response summary array shapes are inconsistent")
        if (
            len(set(self.group_ids)) != group_count
            or tuple(sorted(self.group_ids)) != self.group_ids
        ):
            raise ValueError("group IDs must be sorted and unique")
        if len(set(self.gene_ids)) != gene_count:
            raise ValueError("gene IDs must be unique")
        if np.any(self.cell_counts <= 0):
            raise ValueError("each response group must contain at least one cell")
        if not np.all(np.isfinite(self.means)) or not np.all(np.isfinite(self.variances)):
            raise ValueError("response summary contains nonfinite values")
        if np.any(self.variances < 0):
            raise ValueError("response variances cannot be negative")



def require_response_summary_support(
    summary: ResponseSummaryArrays,
    *,
    control_label: str,
    minimum_cells_per_target: int,
) -> None:
    """Require frozen cell support and a matched comparator for every target batch."""

    validate_nonempty(control_label, field_name="control_label")
    _require_positive_integer(
        minimum_cells_per_target,
        field_name="minimum_cells_per_target",
    )
    counts: dict[str, int] = {}
    control_batches = set()
    target_batches = set()
    for target_id, batch_id, count in zip(
        summary.target_ids,
        summary.batch_ids,
        summary.cell_counts,
        strict=True,
    ):
        counts[target_id] = counts.get(target_id, 0) + int(count)
        if target_id == control_label:
            control_batches.add(batch_id)
        else:
            target_batches.add(batch_id)
    if control_label not in counts:
        raise VirtualCellContractError("response summary lacks the frozen comparator")
    unsupported = tuple(
        sorted(target_id for target_id, count in counts.items() if count < minimum_cells_per_target)
    )
    if unsupported:
        raise VirtualCellContractError(
            "response summary target cell support is below the frozen minimum: "
            + ",".join(unsupported)
        )
    missing_control_batches = tuple(sorted(target_batches - control_batches))
    if missing_control_batches:
        raise VirtualCellContractError(
            "response summary lacks matched control batches: " + ",".join(missing_control_batches)
        )



@dataclass(frozen=True, slots=True)
class ControlReservoirArrays:
    """Deterministic nested-cell reservoir for prediction-shape compilation.

    Reservoir rows retain their source/batch identities but are never promoted
    to independent preparations.  They supply only an empirical residual shape
    after development-visible normalization.
    """

    row_ids: tuple[str, ...]
    batch_ids: tuple[str, ...]
    gene_ids: tuple[str, ...]
    normalization: str
    normalization_target_sum: float
    values: NDArray[np.float32]

    def __post_init__(self) -> None:
        if not self.row_ids or len(set(self.row_ids)) != len(self.row_ids):
            raise ValueError("control reservoir row IDs must be nonempty and unique")
        if len(self.batch_ids) != len(self.row_ids):
            raise ValueError("control reservoir batch IDs are not row aligned")
        if not self.gene_ids or len(set(self.gene_ids)) != len(self.gene_ids):
            raise ValueError("control reservoir gene IDs must be nonempty and unique")
        if self.normalization != "log1p-fixed-total":
            raise ValueError("control reservoir requires fixed-total log1p normalization")
        if not math.isfinite(self.normalization_target_sum) or self.normalization_target_sum <= 0:
            raise ValueError("control reservoir normalization target is invalid")
        if self.values.shape != (len(self.row_ids), len(self.gene_ids)):
            raise ValueError("control reservoir matrix has the wrong shape")
        if not np.all(np.isfinite(self.values)) or np.any(self.values < 0):
            raise ValueError("control reservoir values must be finite and nonnegative")
        if float(np.max(self.values)) >= 15.0:
            raise ValueError("control reservoir exceeds cell-eval's log1p range")

