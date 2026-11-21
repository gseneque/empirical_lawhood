# SPDX-License-Identifier: MPL-2.0
'VirtualCell prediction contracts and pure receiver-specific compilation. Applicability remains the declared marginal receiver; no biological replicate claim.'

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import math
from typing import ClassVar
import numpy as np
from numpy.typing import NDArray
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.domains.biology.virtual_cell.contracts import VirtualCellContractError
from empirical_lawhood.domains.biology.virtual_cell.response_summary import ControlReservoirArrays


CELL_EVAL_LOG1P_MAXIMUM = 14.999


@dataclass(frozen=True, slots=True)
class PredictionTargetAllocation(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/physical/virtual-cell/prediction-target-allocation"
    )

    target_id: str
    recommended_cells: int
    median_umi_per_cell: Decimal
    allocated_cells: int

    def __post_init__(self) -> None:
        if not self.target_id:
            raise ValueError("prediction target ID must be nonempty")
        for count_name, count_value in (
            ("recommended_cells", self.recommended_cells),
            ("allocated_cells", self.allocated_cells),
        ):
            if isinstance(count_value, bool) or count_value <= 0:
                raise ValueError(f"{count_name} must be positive")
        validate_decimal(
            self.median_umi_per_cell,
            field_name="median_umi_per_cell",
            minimum=Decimal("0"),
        )
        if self.median_umi_per_cell == 0:
            raise ValueError("median UMI per cell must be positive")


@dataclass(frozen=True, slots=True)
class PredictionRoster(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/physical/virtual-cell/prediction-roster"

    roster_id: str
    prefix_source_sha256: str
    targets: tuple[PredictionTargetAllocation, ...]
    control_label: str
    control_cells: int
    total_cell_limit: int
    allocation_rule: str

    def __post_init__(self) -> None:
        validate_stable_id(self.roster_id, field_name="roster_id")
        validate_sha256(self.prefix_source_sha256, field_name="prefix_source_sha256")
        require_sorted_unique_ids(
            self.targets, attribute="target_id", field_name="targets"
        )
        if not self.targets or not self.control_label:
            raise ValueError("prediction roster requires targets and a control label")
        if isinstance(self.control_cells, bool) or self.control_cells <= 0:
            raise ValueError("prediction roster requires positive control cells")
        if isinstance(self.total_cell_limit, bool) or self.total_cell_limit <= 0:
            raise ValueError("prediction roster total-cell limit must be positive")
        if self.total_cells != self.total_cell_limit:
            raise ValueError(
                "prediction allocation must exactly fill its frozen cell limit"
            )
        if not self.allocation_rule:
            raise ValueError("prediction allocation rule must be nonempty")

    @property
    def total_cells(self) -> int:
        return self.control_cells + sum(value.allocated_cells for value in self.targets)


@dataclass(frozen=True, slots=True)
class PredictionMeanCompilation:
    target_ids: tuple[str, ...]
    absolute_means: NDArray[np.float64]
    control_mean: NDArray[np.float64]
    clipped_value_count: int
    clipped_value_fraction: float

    def __post_init__(self) -> None:
        if not self.target_ids or len(set(self.target_ids)) != len(self.target_ids):
            raise ValueError("prediction means require unique target IDs")
        if self.absolute_means.ndim != 2 or self.absolute_means.shape[0] != len(
            self.target_ids
        ):
            raise ValueError("absolute prediction means are not target aligned")
        if self.control_mean.shape != (self.absolute_means.shape[1],):
            raise ValueError("control mean is not gene aligned")
        if not np.all(np.isfinite(self.absolute_means)) or np.any(
            self.absolute_means < 0
        ):
            raise ValueError("absolute prediction means must be finite and nonnegative")
        if float(np.max(self.absolute_means)) > CELL_EVAL_LOG1P_MAXIMUM:
            raise ValueError("absolute prediction means exceed cell-eval's log1p range")
        if self.clipped_value_count < 0:
            raise ValueError("clipped value count cannot be negative")
        if not 0 <= self.clipped_value_fraction <= 1:
            raise ValueError("clipped value fraction must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class PredictionH5ADBuildReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/adapters/physical/virtual-cell/prediction-h5-ad-build-receipt"
    )

    receipt_id: str
    roster_sha256: str
    predicted_mean_sha256: str
    control_reservoir_sha256: str
    gene_order_sha256: str
    h5ad_sha256: str
    row_count: int
    gene_count: int
    target_count: int
    control_cell_count: int
    seed: int
    maximum_mean_error: Decimal
    maximum_value: Decimal
    output_dtype: str
    outcome_read: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        for digest_name, digest_value in (
            ("roster_sha256", self.roster_sha256),
            ("predicted_mean_sha256", self.predicted_mean_sha256),
            ("control_reservoir_sha256", self.control_reservoir_sha256),
            ("gene_order_sha256", self.gene_order_sha256),
            ("h5ad_sha256", self.h5ad_sha256),
        ):
            validate_sha256(digest_value, field_name=digest_name)
        for count_name, count_value in (
            ("row_count", self.row_count),
            ("gene_count", self.gene_count),
            ("target_count", self.target_count),
            ("control_cell_count", self.control_cell_count),
        ):
            if isinstance(count_value, bool) or count_value <= 0:
                raise ValueError(f"{count_name} must be positive")
        if isinstance(self.seed, bool) or self.seed < 0:
            raise ValueError("prediction seed must be a nonnegative integer")
        validate_decimal(
            self.maximum_mean_error,
            field_name="maximum_mean_error",
            minimum=Decimal("0"),
        )
        validate_decimal(
            self.maximum_value, field_name="maximum_value", minimum=Decimal("0")
        )
        if self.output_dtype != "float32":
            raise ValueError("the 2025 prediction H5AD must use float32 X")
        if self.outcome_read:
            raise ValueError("prediction H5AD construction cannot read test outcomes")


def compile_absolute_prediction_means(
    *,
    target_ids: tuple[str, ...],
    predicted_deltas: NDArray[np.float64],
    control_reservoir: ControlReservoirArrays,
    maximum_value: float = CELL_EVAL_LOG1P_MAXIMUM,
) -> PredictionMeanCompilation:
    if predicted_deltas.shape != (len(target_ids), len(control_reservoir.gene_ids)):
        raise ValueError("predicted response deltas are not target/gene aligned")
    if not np.all(np.isfinite(predicted_deltas)):
        raise ValueError("predicted response deltas contain nonfinite values")
    if not math.isfinite(maximum_value) or maximum_value <= 0 or maximum_value >= 15:
        raise ValueError("prediction maximum must lie strictly between zero and 15")
    control_mean = np.asarray(
        np.mean(control_reservoir.values, axis=0, dtype=np.float64),
        dtype=np.float64,
    )
    raw = control_mean[None, :] + predicted_deltas
    clipped = np.clip(raw, 0.0, maximum_value)
    clipped_count = int(np.count_nonzero(clipped != raw))
    return PredictionMeanCompilation(
        target_ids=target_ids,
        absolute_means=np.asarray(clipped, dtype=np.float64),
        control_mean=np.asarray(control_mean, dtype=np.float64),
        clipped_value_count=clipped_count,
        clipped_value_fraction=clipped_count / clipped.size,
    )


def _historical_mean_preserving_cells(
    *,
    residual_source: NDArray[np.float64],
    requested_mean: NDArray[np.float64],
    cell_count: int,
    rng: np.random.Generator,
    maximum_value: float,
) -> NDArray[np.float32]:
    sampled = np.asarray(
        residual_source[
            rng.integers(0, residual_source.shape[0], size=cell_count, endpoint=False)
        ],
        dtype=np.float64,
    )
    sampled -= np.mean(sampled, axis=0, keepdims=True)
    positive = np.max(sampled, axis=0)
    negative = -np.min(sampled, axis=0)
    upper_scale = np.divide(
        maximum_value - requested_mean,
        positive,
        out=np.full_like(requested_mean, np.inf),
        where=positive > 0,
    )
    lower_scale = np.divide(
        requested_mean,
        negative,
        out=np.full_like(requested_mean, np.inf),
        where=negative > 0,
    )
    scale = np.minimum(1.0, np.minimum(upper_scale, lower_scale))
    scale = np.maximum(scale, 0.0)
    cells = requested_mean[None, :] + sampled * scale[None, :]
    if np.any(cells < -1e-10) or np.any(cells > maximum_value + 1e-10):
        raise VirtualCellContractError(
            "residual compiler violated its bounded log1p range"
        )
    return np.asarray(np.clip(cells, 0.0, maximum_value), dtype=np.float32)


def allocate_prediction_roster(
    rows: tuple[tuple[str, int, Decimal], ...], *, prefix_source_sha256: str,
    roster_id: str, expected_target_count: int, total_cell_limit: int,
    control_cells: int, minimum_cells_per_target: int,
    control_label: str = "non-targeting",
) -> PredictionRoster:
    """Allocate decoded source recommendations by the exact largest-remainder rule."""
    if len(rows) != expected_target_count:
        raise VirtualCellContractError("perturbation roster target count differs")
    if any(
        isinstance(value, bool) or value <= 0
        for value in (total_cell_limit, control_cells, minimum_cells_per_target)
    ):
        raise ValueError("prediction cell budgets must be positive integers")
    perturbation_budget = total_cell_limit - control_cells
    floor_budget = minimum_cells_per_target * len(rows)
    if perturbation_budget < floor_budget:
        raise ValueError("prediction budget cannot satisfy the per-target floor")
    weights = np.asarray([value[1] for value in rows], dtype=np.float64)
    remaining = perturbation_budget - floor_budget
    shares = weights / float(np.sum(weights)) * remaining
    extras = np.floor(shares).astype(np.int64)
    unallocated = remaining - int(np.sum(extras))
    fractions = shares - extras
    order = sorted(
        range(len(rows)),
        key=lambda index: (-float(fractions[index]), rows[index][0]),
    )
    for index in order[:unallocated]:
        extras[index] += 1
    return PredictionRoster(
        roster_id=roster_id,
        prefix_source_sha256=prefix_source_sha256,
        targets=tuple(
            PredictionTargetAllocation(
                target_id=target,
                recommended_cells=recommended,
                median_umi_per_cell=median,
                allocated_cells=minimum_cells_per_target + int(extras[index]),
            )
            for index, (target, recommended, median) in enumerate(rows)
        ),
        control_label=control_label,
        control_cells=control_cells,
        total_cell_limit=total_cell_limit,
        allocation_rule=(
            "per-target floor then recommended-cell-weighted deterministic largest remainder"
        ),
    )


@dataclass(slots=True)
class HistoricalPredictionPreparation:
    """Explicit original compiler state; rows remain nested numerical views."""
    rng: np.random.Generator
    residual_source: NDArray[np.float64]
    control_values: NDArray[np.float32]
    predicted_means: PredictionMeanCompilation
    maximum_value: float
    maximum_mean_error: float = 0.0

    def compile_target(self, *, target_index: int, allocation: PredictionTargetAllocation) -> NDArray[np.float32]:
        values = _historical_mean_preserving_cells(
            residual_source=self.residual_source,
            requested_mean=self.predicted_means.absolute_means[target_index],
            cell_count=allocation.allocated_cells,
            rng=self.rng,
            maximum_value=self.maximum_value,
        )
        observed = np.mean(values, axis=0, dtype=np.float64)
        error = float(np.max(np.abs(observed - self.predicted_means.absolute_means[target_index])))
        self.maximum_mean_error = max(self.maximum_mean_error, error)
        return values

    def require_mean_preservation(self, mean_tolerance: float) -> None:
        if self.maximum_mean_error > mean_tolerance:
            raise VirtualCellContractError("prediction compiler failed row closure or mean preservation")


def prepare_historical_prediction(
    *, roster: PredictionRoster, gene_ids: tuple[str, ...],
    predicted_means: PredictionMeanCompilation, control_reservoir: ControlReservoirArrays,
    seed: int, mean_tolerance: float, maximum_value: float,
) -> HistoricalPredictionPreparation:
    if gene_ids != control_reservoir.gene_ids:
        raise VirtualCellContractError("prediction and control gene registries differ")
    roster_targets = tuple(value.target_id for value in roster.targets)
    if roster_targets != predicted_means.target_ids:
        raise VirtualCellContractError("prediction means and roster targets differ")
    if predicted_means.absolute_means.shape[1] != len(gene_ids):
        raise VirtualCellContractError("prediction mean gene dimension differs")
    if isinstance(seed, bool) or seed < 0:
        raise ValueError("prediction seed must be a nonnegative integer")
    if not math.isfinite(mean_tolerance) or mean_tolerance < 0:
        raise ValueError("prediction mean tolerance must be finite and nonnegative")
    rng = np.random.default_rng(seed)
    source = np.asarray(control_reservoir.values, dtype=np.float64)
    source_mean = np.mean(source, axis=0, keepdims=True)
    residual_source = source - source_mean
    control_indices = rng.integers(
        0, source.shape[0], size=roster.control_cells, endpoint=False,
    )
    return HistoricalPredictionPreparation(
        rng=rng, residual_source=residual_source,
        control_values=np.asarray(source[control_indices], dtype=np.float32),
        predicted_means=predicted_means, maximum_value=maximum_value,
    )
