# SPDX-License-Identifier: MPL-2.0
'Pure shared-template-shift v2 numerical compilation over supplied arrays. No dataset, evaluator or artifact contact.'

from dataclasses import dataclass
from decimal import Decimal
import math
import numpy as np
from numpy.typing import NDArray
from empirical_lawhood.domains.biology.virtual_cell.contracts import VirtualCellContractError
from empirical_lawhood.domains.biology.virtual_cell.correction_records_v2 import SharedTemplateShiftV2BuildReceipt as SharedTemplateShiftV2BuildReceipt, SharedTemplateShiftV2Selection as SharedTemplateShiftV2Selection
from empirical_lawhood.domains.biology.virtual_cell.response_summary import ControlReservoirArrays
from empirical_lawhood.domains.biology.virtual_cell.prediction import CELL_EVAL_LOG1P_MAXIMUM, PredictionRoster, PredictionTargetAllocation


@dataclass(frozen=True, slots=True)
class SharedTemplateShiftV2Compilation:
    """One receiver-admitted v2 cell-population compilation."""

    values: NDArray[np.float32]
    null_mean: NDArray[np.float64]
    requested_delta: NDArray[np.float64]
    realized_delta: NDArray[np.float64]
    saturated_value_count: int

    def __post_init__(self) -> None:
        gene_count = self.values.shape[1] if self.values.ndim == 2 else 0
        if self.values.ndim != 2 or not self.values.shape[0] or not gene_count:
            raise ValueError("v2 compilation requires a nonempty cell matrix")
        expected = (gene_count,)
        if any(
            value.shape != expected
            for value in (self.null_mean, self.requested_delta, self.realized_delta)
        ):
            raise ValueError("v2 compilation vectors are not gene aligned")
        if not all(
            np.all(np.isfinite(value))
            for value in (
                self.values,
                self.null_mean,
                self.requested_delta,
                self.realized_delta,
            )
        ):
            raise ValueError("v2 compilation contains nonfinite values")
        if self.saturated_value_count < 0:
            raise ValueError("v2 saturation count cannot be negative")


def select_shared_control_template(
    *,
    control_reservoir: ControlReservoirArrays,
    control_cells: int,
    seed: int,
) -> NDArray[np.float32]:
    """Select the sole empirical template used by the qualified compiler."""

    if (
        not isinstance(control_cells, (int, np.integer))
        or isinstance(control_cells, bool)
        or control_cells <= 0
    ):
        raise ValueError("shared-template control cell count must be positive")
    if isinstance(seed, bool) or seed < 0:
        raise ValueError("shared-template seed must be nonnegative")
    rng = np.random.default_rng(seed)
    indices = rng.integers(
        0,
        control_reservoir.values.shape[0],
        size=control_cells,
        endpoint=False,
    )
    template = np.asarray(control_reservoir.values[indices], dtype=np.float32)
    # The reservoir's older range admits values above this compiler's limit.
    shared_template_shift_v2_null_cells(template, cell_count=control_cells)
    return template


def shared_template_shift_v2_null_cells(
    template: NDArray[np.float32],
    *,
    cell_count: int,
) -> NDArray[np.float32]:
    """Compile a count-matched empirical marginal null with copula-rank order.

    Each gene receives evenly spaced order statistics from the one shared
    template.  Those marginal values are assigned according to the ranks of a
    deterministic balanced anchor subset, retaining its empirical copula order.
    At the template row count this reconstructs the template bit for bit.

    This construction is qualified only for the VCC 2025 per-gene marginal
    receiver.  It is not a biological single-cell generative model.
    """

    if template.ndim != 2 or not template.shape[0] or not template.shape[1]:
        raise ValueError("v2 shared template must be a nonempty matrix")
    if template.dtype != np.float32:
        raise ValueError(
            "v2 shared template must retain its selected float32 representation"
        )
    if (
        not isinstance(cell_count, (int, np.integer))
        or isinstance(cell_count, bool)
        or cell_count <= 0
    ):
        raise ValueError("v2 target cell count must be positive")
    if (
        not np.all(np.isfinite(template))
        or np.any(template < 0.0)
        or np.any(template > CELL_EVAL_LOG1P_MAXIMUM)
    ):
        raise ValueError("v2 shared template is outside the VCC log1p receiver range")
    sorted_values = np.sort(np.asarray(template, dtype=np.float32), axis=0)
    return _shared_template_shift_v2_null_cells_prepared(
        template=template,
        sorted_values=sorted_values,
        cell_count=cell_count,
    )


def _shared_template_shift_v2_null_cells_prepared(
    *,
    template: NDArray[np.float32],
    sorted_values: NDArray[np.float32],
    cell_count: int,
) -> NDArray[np.float32]:
    template_rows = template.shape[0]
    if cell_count == template_rows:
        # Preserve original bits even for tied values with different zero signs.
        return np.array(template, dtype=np.float32, copy=True)
    quantile_indices = np.floor(
        (np.arange(cell_count, dtype=np.float64) + 0.5) * template_rows / cell_count
    ).astype(np.int64)
    quantile_indices = np.minimum(quantile_indices, template_rows - 1)
    selected = np.asarray(sorted_values[quantile_indices], dtype=np.float32)
    anchor_indices = np.floor(
        np.arange(cell_count, dtype=np.float64) * template_rows / cell_count
    ).astype(np.int64)
    anchors = np.asarray(template[anchor_indices], dtype=np.float32)
    order = np.argsort(anchors, axis=0, kind="stable")
    values = np.empty_like(selected)
    np.put_along_axis(values, order, selected, axis=0)
    return values


def compile_shared_template_shift_v2_cells(
    *,
    template: NDArray[np.float32],
    requested_delta: NDArray[np.float64],
    cell_count: int,
    mean_tolerance: float = 1e-6,
    maximum_value: float = CELL_EVAL_LOG1P_MAXIMUM,
) -> SharedTemplateShiftV2Compilation:
    """Compile one admitted delta without target-specific null recentering.

    The requested action is relative to the count-specific v2 null population.
    Zero coordinates remain bitwise unchanged.  Nonzero coordinates use the
    same bounded monotone translation as v1, but an out-of-range requested mean
    is rejected before construction instead of silently projected.
    """

    # Validate template shape/range and count before inspecting its gene axis.
    shared_template_shift_v2_null_cells(template, cell_count=cell_count)
    if not math.isfinite(maximum_value) or maximum_value <= 0 or maximum_value >= 15:
        raise ValueError("v2 maximum must lie strictly between zero and 15")
    if np.any(template > maximum_value):
        raise ValueError("v2 null population exceeds the selected output range")
    if not math.isfinite(mean_tolerance) or mean_tolerance < 0:
        raise ValueError("v2 mean tolerance must be finite and nonnegative")
    if requested_delta.shape != (template.shape[1],):
        raise ValueError("v2 requested delta is not gene aligned")
    if not np.all(np.isfinite(requested_delta)):
        raise ValueError("v2 requested delta contains nonfinite values")
    sorted_values = np.sort(np.asarray(template, dtype=np.float32), axis=0)
    return _compile_shared_template_shift_v2_cells_prepared(
        template=template,
        sorted_values=sorted_values,
        requested_delta=requested_delta,
        cell_count=cell_count,
        mean_tolerance=mean_tolerance,
        maximum_value=maximum_value,
    )


def _compile_shared_template_shift_v2_cells_prepared(
    *,
    template: NDArray[np.float32],
    sorted_values: NDArray[np.float32],
    requested_delta: NDArray[np.float64],
    cell_count: int,
    mean_tolerance: float,
    maximum_value: float,
) -> SharedTemplateShiftV2Compilation:
    base = _shared_template_shift_v2_null_cells_prepared(
        template=template,
        sorted_values=sorted_values,
        cell_count=cell_count,
    )
    base64 = np.asarray(base, dtype=np.float64)
    null_mean = np.asarray(np.mean(base64, axis=0, dtype=np.float64), dtype=np.float64)
    requested_mean = null_mean + requested_delta
    if np.any(requested_mean < 0.0) or np.any(requested_mean > maximum_value):
        raise VirtualCellContractError(
            "shared-template-shift-v2 requested delta is outside receiver-admissible bounds"
        )
    active = requested_delta != 0.0
    if not np.any(active):
        return SharedTemplateShiftV2Compilation(
            values=base,
            null_mean=null_mean,
            requested_delta=np.asarray(requested_delta, dtype=np.float64),
            realized_delta=np.zeros_like(requested_delta, dtype=np.float64),
            saturated_value_count=0,
        )

    active_base = base64[:, active]
    active_requested_mean = requested_mean[active]
    lower = -np.max(active_base, axis=0)
    upper = maximum_value - np.min(active_base, axis=0)
    for _ in range(64):
        midpoint = (lower + upper) / 2.0
        realized = np.mean(
            np.clip(active_base + midpoint[None, :], 0.0, maximum_value),
            axis=0,
            dtype=np.float64,
        )
        lower = np.where(realized < active_requested_mean, midpoint, lower)
        upper = np.where(realized >= active_requested_mean, midpoint, upper)
    shift = (lower + upper) / 2.0
    raw = active_base + shift[None, :]
    shifted = np.clip(raw, 0.0, maximum_value)
    values64 = base64.copy()
    values64[:, active] = shifted
    values = np.asarray(values64, dtype=np.float32)
    observed = np.mean(values, axis=0, dtype=np.float64)
    realized_delta = np.asarray(observed - null_mean, dtype=np.float64)
    maximum_error = float(np.max(np.abs(realized_delta - requested_delta)))
    if maximum_error > mean_tolerance:
        raise VirtualCellContractError(
            "shared-template-shift-v2 failed action mean closure"
        )
    return SharedTemplateShiftV2Compilation(
        values=values,
        null_mean=null_mean,
        requested_delta=np.asarray(requested_delta, dtype=np.float64),
        realized_delta=realized_delta,
        saturated_value_count=int(np.count_nonzero(raw != shifted)),
    )


@dataclass(frozen=True, slots=True)
class SharedTemplateShiftV2Preparation:
    """Whole-action admission with one retained template, no output side effect."""
    predicted_deltas: NDArray[np.float64]
    template: NDArray[np.float32]
    sorted_template: NDArray[np.float32]
    control: NDArray[np.float32]
    mean_tolerance: float
    maximum_value: float
    maximum_null_error: float
    maximum_action_error: float
    saturated_count: int
    action_values: int

    def compile_target(self, *, target_index: int, allocation: PredictionTargetAllocation) -> SharedTemplateShiftV2Compilation:
        return _compile_shared_template_shift_v2_cells_prepared(
            template=self.template, sorted_values=self.sorted_template,
            requested_delta=self.predicted_deltas[target_index], cell_count=allocation.allocated_cells,
            mean_tolerance=self.mean_tolerance, maximum_value=self.maximum_value,
        )

    @property
    def saturated_fraction(self) -> Decimal:
        return Decimal(self.saturated_count) / Decimal(self.action_values)


def admit_shared_template_shift_v2_prediction(
    *, roster: PredictionRoster, gene_ids: tuple[str, ...],
    predicted_deltas: NDArray[np.float64], control_reservoir: ControlReservoirArrays,
    seed: int, selection: SharedTemplateShiftV2Selection,
) -> SharedTemplateShiftV2Preparation:
    """Validate and assess every target under the selected marginal receiver."""
    if type(selection) is not SharedTemplateShiftV2Selection:
        raise TypeError("v2 writer requires its explicit scientific selection")
    mean_tolerance = float(selection.mean_tolerance)
    maximum_null_mean_error = float(selection.maximum_null_mean_error)
    maximum_value = float(selection.maximum_value)
    predicted_deltas = np.array(predicted_deltas, dtype=np.float64, copy=True)
    if gene_ids != control_reservoir.gene_ids:
        raise VirtualCellContractError(
            "v2 prediction and control gene registries differ"
        )
    target_ids = tuple(value.target_id for value in roster.targets)
    if predicted_deltas.shape != (len(target_ids), len(gene_ids)):
        raise VirtualCellContractError("v2 deltas are not target/gene aligned")
    if not np.all(np.isfinite(predicted_deltas)):
        raise VirtualCellContractError("v2 deltas contain nonfinite values")
    if not math.isfinite(maximum_null_mean_error) or maximum_null_mean_error < 0:
        raise ValueError("v2 null-mean tolerance must be finite and nonnegative")
    template = select_shared_control_template(
        control_reservoir=control_reservoir,
        control_cells=roster.control_cells,
        seed=seed,
    )
    sorted_template = np.sort(np.asarray(template, dtype=np.float32), axis=0)
    control = _shared_template_shift_v2_null_cells_prepared(
        template=template,
        sorted_values=sorted_template,
        cell_count=roster.control_cells,
    )
    control_mean = np.mean(control, axis=0, dtype=np.float64)

    # Admission is completed for the whole action before the destination exists.
    maximum_null_error = 0.0
    maximum_action_error = 0.0
    saturated_count = 0
    for index, allocation in enumerate(roster.targets):
        compilation = _compile_shared_template_shift_v2_cells_prepared(
            template=template,
            sorted_values=sorted_template,
            requested_delta=predicted_deltas[index],
            cell_count=allocation.allocated_cells,
            mean_tolerance=mean_tolerance,
            maximum_value=maximum_value,
        )
        null_error = float(np.max(np.abs(compilation.null_mean - control_mean)))
        action_error = float(
            np.max(np.abs(compilation.realized_delta - compilation.requested_delta))
        )
        maximum_null_error = max(maximum_null_error, null_error)
        maximum_action_error = max(maximum_action_error, action_error)
        saturated_count += compilation.saturated_value_count
    if maximum_null_error > maximum_null_mean_error:
        raise VirtualCellContractError(
            "v2 null population exceeds its receiver error bound"
        )

    return SharedTemplateShiftV2Preparation(
        predicted_deltas=predicted_deltas, template=template,
        sorted_template=sorted_template, control=control,
        mean_tolerance=mean_tolerance, maximum_value=maximum_value,
        maximum_null_error=maximum_null_error, maximum_action_error=maximum_action_error,
        saturated_count=saturated_count,
        action_values=sum(value.allocated_cells for value in roster.targets) * len(gene_ids),
    )
