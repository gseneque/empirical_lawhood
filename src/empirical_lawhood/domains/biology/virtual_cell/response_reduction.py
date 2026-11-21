"""Data-only single-cell reservoir selection and response-moment reduction.

Rows are nested cell views, not independent preparation replicates. Counts,
normalization choice, complete target-by-batch groups and population moments
retain the supplied study's meaning. No HDF5, source access or native engine is
needed to apply these operations to arrays.
"""
from dataclasses import dataclass
import hashlib
import math

import numpy as np
from numpy.typing import NDArray

from empirical_lawhood.domains.biology.virtual_cell.contracts import VirtualCellContractError


def selected_control_rows(*, targets: NDArray[np.str_], batches: NDArray[np.str_],
                          control_label: str, maximum_cells: int, seed: int) -> NDArray[np.int64]:
    control_indices = np.flatnonzero(targets == control_label)
    if control_indices.size == 0:
        raise VirtualCellContractError("H5AD lacks declared comparator cells")
    batch_values = tuple(sorted(set(batches[control_indices].tolist())))
    if maximum_cells < len(batch_values):
        raise VirtualCellContractError("control reservoir is too small to cover observed batches")

    def priority(row: int) -> bytes:
        return hashlib.sha256(f"{seed}:{row}".encode("ascii")).digest()

    chosen: set[int] = set()
    for batch in batch_values:
        candidates = control_indices[batches[control_indices] == batch]
        chosen.add(min((int(value) for value in candidates), key=priority))
    remaining = maximum_cells - len(chosen)
    if remaining > 0:
        candidates = (int(value) for value in control_indices if int(value) not in chosen)
        chosen.update(sorted(candidates, key=priority)[:remaining])
    return np.asarray(sorted(chosen), dtype=np.int64)


def normalization_total(normalization: str, target: float | None) -> float:
    if normalization not in {"source", "log1p-cp10000", "log1p-fixed-total"}:
        raise ValueError("normalization is not supported")
    if normalization == "log1p-fixed-total":
        if target is None or not math.isfinite(target) or target <= 0:
            raise ValueError("fixed-total normalization requires a positive target sum")
        return target
    if target is not None:
        raise ValueError("normalization target sum is only valid for fixed-total mode")
    return 10_000.0


def normalize_control_values(values: np.ndarray, target_sum: float) -> np.ndarray:
    total = float(np.sum(values))
    if total <= 0 or not math.isfinite(total) or not np.all(np.isfinite(values)):
        raise VirtualCellContractError("control row is invalid for normalization")
    result = np.log1p(values * (target_sum / total))
    if not np.all(np.isfinite(result)):
        raise VirtualCellContractError("control row is invalid for normalization")
    return result


def canonical_sparse_row(indices: np.ndarray, data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Coalesce repeated coordinates before applying nonlinear normalization.

    Canonical increasing coordinates keep their original arrays and summation
    order. Noncanonical CSR rows represent the sum of entries at each index.
    """
    if len(indices) <= 1 or np.all(indices[1:] > indices[:-1]):
        return indices, data
    unique, inverse = np.unique(indices, return_inverse=True)
    if len(unique) == len(indices):
        return indices, data
    values = np.zeros(len(unique), dtype=np.float64)
    np.add.at(values, inverse, data)
    return unique, values


@dataclass(slots=True)
class ResponseMomentAccumulator:
    """Bounded array reduction that refuses missing, repeated or reordered rows."""
    pairs: tuple[tuple[str, str], ...]
    group_ids: tuple[str, ...]
    row_groups: np.ndarray
    counts: np.ndarray
    sums: np.ndarray
    squared_sums: np.ndarray
    normalization: str
    target_sum: float
    next_row: int = 0

    @classmethod
    def for_labels(cls, targets, batches, genes: int, normalization: str,
                   normalization_target_sum: float | None):
        pairs = tuple(sorted(set(zip(targets.tolist(), batches.tolist(), strict=True))))
        if not pairs or genes <= 0:
            raise VirtualCellContractError("response reduction requires nonempty rows and genes")
        group_ids = tuple(f"target={target}|batch={batch}" for target, batch in pairs)
        pair_to_index = {pair: index for index, pair in enumerate(pairs)}
        row_groups = np.fromiter((pair_to_index[(target, batch)] for target, batch
                                 in zip(targets.tolist(), batches.tolist(), strict=True)),
                                dtype=np.int64, count=len(targets))
        counts = np.bincount(row_groups, minlength=len(pairs)).astype(np.int64, copy=False)
        sums = np.zeros((len(pairs), genes), dtype=np.float64)
        return cls(pairs, group_ids, row_groups, counts, sums, np.zeros_like(sums),
                   normalization, normalization_total(normalization, normalization_target_sum))

    def _rows(self, start: int, count: int):
        if start != self.next_row or count < 1 or start + count > len(self.row_groups):
            raise VirtualCellContractError("response reduction requires each original row exactly once in order")
        return self.row_groups[start:start + count]

    def add_dense(self, start: int, dense: np.ndarray) -> None:
        if dense.ndim != 2 or dense.shape[1] != self.sums.shape[1]:
            raise VirtualCellContractError("response chunk has another gene census")
        groups = self._rows(start, len(dense))
        if not np.all(np.isfinite(dense)):
            raise VirtualCellContractError("X contains nonfinite development values")
        if self.normalization != "source":
            totals = np.sum(dense, axis=1)
            if np.any(totals <= 0) or not np.all(np.isfinite(totals)):
                raise VirtualCellContractError("count normalization encountered a nonpositive or nonfinite cell total")
            dense = np.log1p(dense * (self.target_sum / totals[:, None]))
        if not np.all(np.isfinite(dense)):
            raise VirtualCellContractError("normalized response contains nonfinite values")
        np.add.at(self.sums, groups, dense)
        np.add.at(self.squared_sums, groups, dense * dense)
        self.next_row += len(dense)

    def add_csr(self, start: int, indptr: np.ndarray, indices: np.ndarray, data: np.ndarray) -> None:
        groups = self._rows(start, len(indptr) - 1)
        if (indptr[0] != 0 or indptr[-1] != len(data) or len(indices) != len(data)
                or np.any(indptr[1:] < indptr[:-1])):
            raise VirtualCellContractError("CSR response chunk has invalid row pointers")
        if np.any(indices < 0) or np.any(indices >= self.sums.shape[1]):
            raise VirtualCellContractError("CSR X contains out-of-range indices")
        if not np.all(np.isfinite(data)):
            raise VirtualCellContractError("X contains nonfinite development values")
        for local_row, group_index in enumerate(groups):
            left, right = int(indptr[local_row]), int(indptr[local_row + 1])
            row_indices, row_data = canonical_sparse_row(indices[left:right], data[left:right])
            if self.normalization != "source":
                total = float(np.sum(row_data))
                if total <= 0 or not math.isfinite(total):
                    raise VirtualCellContractError("count normalization encountered a nonpositive or nonfinite cell total")
                row_data = np.log1p(row_data * (self.target_sum / total))
            if not np.all(np.isfinite(row_data)):
                raise VirtualCellContractError("normalized response contains nonfinite values")
            np.add.at(self.sums[group_index], row_indices, row_data)
            np.add.at(self.squared_sums[group_index], row_indices, row_data * row_data)
        self.next_row += len(groups)

    def finish(self) -> tuple[np.ndarray, np.ndarray]:
        if self.next_row != len(self.row_groups):
            raise VirtualCellContractError("response reduction has an incomplete original-row census")
        means = self.sums / self.counts[:, None]
        variances = np.maximum(self.squared_sums / self.counts[:, None] - means * means, 0.0)
        return means, variances
