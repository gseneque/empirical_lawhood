"""Evaluator-only 2025 cell-eval integration and exact aggregate normalization."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import math
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, cast

import h5py  # type: ignore[import-untyped]
import numpy as np
from numpy.typing import NDArray

from .analysis import (
    OfficialAggregateScore,
    VirtualCellAnalysisError,
    official_aggregate_score,
    verify_official_evaluator_versions,
)
from .contracts import MetricContract, VirtualCellContractError
from .metric_correction_v2 import (
    DES_SOURCE_COLUMN,
    PDS_SOURCE_COLUMN,
    OfficialMetricGaugeV2,
    OfficialMetricSetV2,
    metric_set_from_source_columns,
    require_metric_contract_gauge,
    score_source_aggregate,
)

if TYPE_CHECKING:
    import anndata as ad
    import polars as pl


@dataclass(frozen=True, slots=True)
class HistoricalOfficialEvaluatorRun:
    target_ids: tuple[str, ...]
    des: NDArray[np.float64]
    pds: NDArray[np.float64]
    mae: NDArray[np.float64]
    score: OfficialAggregateScore
    metrics_arrow: bytes
    cell_eval_version: str
    pdex_version: str
    profile: str
    control_label: str
    perturbation_column: str
    response_outcome_read: bool

    def __post_init__(self) -> None:
        if tuple(sorted(set(self.target_ids))) != self.target_ids:
            raise ValueError("official evaluator targets must be sorted and unique")
        expected = (len(self.target_ids),)
        if any(values.shape != expected for values in (self.des, self.pds, self.mae)):
            raise ValueError("official evaluator arrays are not target aligned")
        if any(
            not np.all(np.isfinite(values)) for values in (self.des, self.pds, self.mae)
        ):
            raise ValueError("official evaluator arrays contain nonfinite values")
        if (
            self.profile != "vcc"
            or not self.control_label
            or not self.perturbation_column
        ):
            raise ValueError("official evaluator configuration differs from VCC")
        if not self.response_outcome_read:
            raise ValueError(
                "official evaluation must acknowledge its response outcome read"
            )


@dataclass(frozen=True, slots=True)
class OfficialEvaluatorRunV2:
    metrics: OfficialMetricSetV2
    score: OfficialAggregateScore
    cell_eval_version: str
    pdex_version: str
    profile: str
    control_label: str
    perturbation_column: str
    response_outcome_read: bool

    @property
    def metrics_canonical(self):
        return self.metrics.canonical_bytes()


def bootstrap_official_score_standard_error(
    *,
    des: NDArray[np.float64],
    pds: NDArray[np.float64],
    mae: NDArray[np.float64],
    metric_contract: MetricContract,
    resamples: int,
    seed: int,
) -> Decimal:
    """Deterministic target-unit bootstrap SE for the exact aggregate score.

    Calling this function with the same seed for every candidate produces the
    same target-index resamples, preserving the plan's paired target design.
    Cells are never treated as independent units.
    """

    if isinstance(resamples, bool) or resamples <= 1:
        raise ValueError("official-score bootstrap requires at least two resamples")
    if isinstance(seed, bool) or seed < 0:
        raise ValueError("official-score bootstrap seed must be nonnegative")
    expected = des.shape
    if (
        len(expected) != 1
        or expected[0] == 0
        or pds.shape != expected
        or mae.shape != expected
    ):
        raise ValueError(
            "official-score bootstrap arrays must be aligned nonempty vectors"
        )
    if any(not np.all(np.isfinite(values)) for values in (des, pds, mae)):
        raise ValueError("official-score bootstrap arrays contain nonfinite values")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, expected[0], size=(resamples, expected[0]))
    scores = np.empty(resamples, dtype=np.float64)
    for index, target_indices in enumerate(indices):
        score = official_aggregate_score(
            des=Decimal(str(float(np.mean(des[target_indices], dtype=np.float64)))),
            pds=Decimal(str(float(np.mean(pds[target_indices], dtype=np.float64)))),
            mae=Decimal(str(float(np.mean(mae[target_indices], dtype=np.float64)))),
            metric_contract=metric_contract,
        )
        scores[index] = float(score.average_score)
    standard_error = float(np.std(scores, ddof=1))
    if not math.isfinite(standard_error):
        raise VirtualCellAnalysisError(
            "official-score bootstrap standard error is nonfinite"
        )
    return Decimal(str(standard_error))


def read_anndata_h5ad_stream(stream: BinaryIO) -> ad.AnnData:
    """Read one already-authorized seekable H5AD stream without a caller path."""

    import anndata as ad
    from anndata._io.specs import read_elem

    try:
        if not stream.readable() or not stream.seekable():
            raise VirtualCellContractError(
                "evaluator H5AD stream must be readable and seekable"
            )
        stream.seek(0)
        with h5py.File(stream, "r") as handle:
            value = read_elem(handle)
    except VirtualCellContractError:
        raise
    except (OSError, TypeError, ValueError) as error:
        raise VirtualCellContractError("evaluator H5AD stream is invalid") from error
    if not isinstance(value, ad.AnnData):
        raise VirtualCellContractError("evaluator H5AD root is not AnnData")
    return cast(ad.AnnData, value)


def _target_registry(
    adata: ad.AnnData, *, column: str, control_label: str
) -> tuple[str, ...]:
    if column not in adata.obs:
        raise VirtualCellContractError(f"AnnData lacks evaluator column {column}")
    values = tuple(str(value) for value in adata.obs[column])
    if not values or control_label not in values:
        raise VirtualCellContractError("AnnData lacks the declared comparator")
    return tuple(sorted(set(values) - {control_label}))


def _metric_arrays(
    results: pl.DataFrame,
) -> tuple[
    tuple[str, ...],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    expected = {
        "perturbation",
        "overlap_at_N",
        "mae",
        "discrimination_score_l1",
    }
    if set(results.columns) != expected:
        raise VirtualCellAnalysisError("cell-eval VCC per-target column roster differs")
    ordered = results.sort("perturbation")
    target_ids = tuple(str(value) for value in ordered["perturbation"].to_list())
    arrays = tuple(
        np.asarray(ordered[column].to_numpy(), dtype=np.float64)
        for column in (DES_SOURCE_COLUMN, PDS_SOURCE_COLUMN, "mae")
    )
    if tuple(sorted(set(target_ids))) != target_ids:
        raise VirtualCellAnalysisError(
            "cell-eval returned duplicate or unsorted targets"
        )
    if any(not np.all(np.isfinite(value)) for value in arrays):
        raise VirtualCellAnalysisError(
            "cell-eval returned nonfinite per-target metrics"
        )
    return target_ids, arrays[0], arrays[1], arrays[2]


def _aggregate_mean(aggregate: pl.DataFrame, column: str) -> float:
    import polars as pl

    if "statistic" not in aggregate.columns or column not in aggregate.columns:
        raise VirtualCellAnalysisError("cell-eval aggregate table differs")
    row = aggregate.filter(pl.col("statistic") == "mean")
    if row.height != 1:
        raise VirtualCellAnalysisError("cell-eval aggregate table lacks one mean row")
    value = float(row[column][0])
    if not math.isfinite(value):
        raise VirtualCellAnalysisError("cell-eval aggregate mean is nonfinite")
    return value


def evaluate_official_2025_v2(
    *,
    predicted: ad.AnnData,
    real: ad.AnnData,
    metric_contract: MetricContract,
    metric_gauge: OfficialMetricGaugeV2,
    scratch_directory: Path,
    num_threads: int,
    control_label: str = "non-targeting",
    perturbation_column: str = "target_gene",
) -> OfficialEvaluatorRunV2:
    """Produce a separately versioned corrected metric artifact using the pinned evaluator."""

    if type(metric_gauge) is not OfficialMetricGaugeV2:
        raise TypeError(
            "corrected evaluation requires its explicit versioned metric gauge"
        )
    require_metric_contract_gauge(gauge=metric_gauge, metric_contract=metric_contract)
    from cell_eval import MetricsEvaluator

    if isinstance(num_threads, bool) or num_threads <= 0:
        raise ValueError("official evaluator thread count must be positive")
    if scratch_directory.exists() or scratch_directory.is_symlink():
        raise VirtualCellContractError(
            "cell-eval scratch destination must not already exist"
        )
    parent = scratch_directory.parent
    if not parent.is_dir() or parent.is_symlink():
        raise VirtualCellContractError(
            "cell-eval scratch parent must be an authorized directory"
        )
    predicted_targets = _target_registry(
        predicted,
        column=perturbation_column,
        control_label=control_label,
    )
    real_targets = _target_registry(
        real,
        column=perturbation_column,
        control_label=control_label,
    )
    if predicted_targets != real_targets:
        raise VirtualCellContractError(
            "prediction and protected target registries differ"
        )
    if tuple(str(value) for value in predicted.var_names) != tuple(
        str(value) for value in real.var_names
    ):
        raise VirtualCellContractError(
            "prediction and protected gene registries differ"
        )
    cell_eval_version, pdex_version = verify_official_evaluator_versions(
        metric_contract
    )
    scratch_directory.mkdir()
    evaluator = MetricsEvaluator(
        adata_pred=predicted,
        adata_real=real,
        control_pert=control_label,
        pert_col=perturbation_column,
        de_method="wilcoxon",
        num_threads=num_threads,
        batch_size=100,
        outdir=str(scratch_directory),
        allow_discrete=False,
        pdex_kwargs={"tie_correct": True},
    )
    results, aggregate = evaluator.compute(
        profile="vcc",
        write_csv=False,
        break_on_error=True,
    )
    target_ids, des, pds, mae = _metric_arrays(results)
    if target_ids != real_targets:
        raise VirtualCellAnalysisError(
            "cell-eval result targets differ from protected roster"
        )
    score = score_source_aggregate(
        columns={
            name: _aggregate_mean(aggregate, name)
            for name in (DES_SOURCE_COLUMN, PDS_SOURCE_COLUMN, "mae")
        },
        gauge=metric_gauge,
        metric_contract=metric_contract,
    )
    metrics = metric_set_from_source_columns(
        target_ids=target_ids,
        columns={DES_SOURCE_COLUMN: des, PDS_SOURCE_COLUMN: pds, "mae": mae},
        gauge=metric_gauge,
    )
    return OfficialEvaluatorRunV2(
        metrics=metrics,
        score=score,
        cell_eval_version=cell_eval_version,
        pdex_version=pdex_version,
        profile="vcc",
        control_label=control_label,
        perturbation_column=perturbation_column,
        response_outcome_read=True,
    )


def evaluate_official_2025(**_kwargs):
    """Do not publish corrected meanings under original crossed artifact contracts."""
    raise VirtualCellContractError(
        "SOFTWARE: select evaluate_official_2025_v2 and its versioned gauge/output "
        "contracts; original crossed evaluation receipts remain historical"
    )


__all__ = [
    "HistoricalOfficialEvaluatorRun",
    "OfficialEvaluatorRunV2",
    "bootstrap_official_score_standard_error",
    "evaluate_official_2025",
    "evaluate_official_2025_v2",
    "read_anndata_h5ad_stream",
]
