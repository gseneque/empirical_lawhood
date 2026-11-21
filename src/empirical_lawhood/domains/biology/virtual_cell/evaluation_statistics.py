"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import math
import numpy as np
from numpy.typing import NDArray
from empirical_lawhood.domains.biology.virtual_cell.analysis import OfficialAggregateScore, VirtualCellAnalysisError, official_aggregate_score
from empirical_lawhood.domains.biology.virtual_cell.contracts import MetricContract
from empirical_lawhood.domains.biology.virtual_cell.correction_records_v2 import OfficialMetricSetV2


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
