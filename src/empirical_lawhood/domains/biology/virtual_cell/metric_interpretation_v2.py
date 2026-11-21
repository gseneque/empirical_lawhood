"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from decimal import Decimal
import numpy as np
from empirical_lawhood.domains.biology.virtual_cell.correction_records_v2 import CORRECTIVE_SOURCE_COMMIT as CORRECTIVE_SOURCE_COMMIT, DES_SOURCE_COLUMN as DES_SOURCE_COLUMN, PDS_SOURCE_COLUMN as PDS_SOURCE_COLUMN, MetricSourceSemantics as MetricSourceSemantics, OfficialMetricGaugeV2 as OfficialMetricGaugeV2, OfficialMetricSetV2 as OfficialMetricSetV2, require_metric_contract_gauge as require_metric_contract_gauge


def metric_set_from_source_columns(*, target_ids, columns, gauge):
    """Interpret source names once, keeping unequal DES/PDS unambiguous."""
    if type(gauge) is not OfficialMetricGaugeV2:
        raise TypeError("current metric interpretation requires the selected v2 gauge")
    if set(columns) != {DES_SOURCE_COLUMN, PDS_SOURCE_COLUMN, "mae"}:
        raise ValueError("official metric source column census differs")
    return OfficialMetricSetV2(
        gauge,
        MetricSourceSemantics.OFFICIAL_SOURCE_COLUMNS,
        None,
        tuple(target_ids),
        *(
            tuple(Decimal(str(value)) for value in columns[name])
            for name in (DES_SOURCE_COLUMN, PDS_SOURCE_COLUMN, "mae")
        ),
    )


def score_source_aggregate(*, columns, gauge, metric_contract):
    """Apply the same source-name interpretation to the evaluator's mean row."""
    require_metric_contract_gauge(gauge=gauge, metric_contract=metric_contract)
    metrics = metric_set_from_source_columns(
        target_ids=("aggregate.mean",),
        columns={name: (value,) for name, value in columns.items()},
        gauge=gauge,
    )
    return score_corrected_metrics(metrics, metric_contract=metric_contract)


def score_corrected_metrics(metrics: OfficialMetricSetV2, *, metric_contract):
    """Reuse the existing independent scalar normalization, with corrected inputs."""
    from empirical_lawhood.domains.biology.virtual_cell.analysis import official_aggregate_score

    if type(metrics) is not OfficialMetricSetV2:
        raise TypeError("corrected scoring requires the versioned metric artifact")
    require_metric_contract_gauge(gauge=metrics.gauge, metric_contract=metric_contract)
    means = {
        name: Decimal(
            str(float(np.mean(np.asarray(getattr(metrics, name), dtype=np.float64))))
        )
        for name in ("des", "pds", "mae")
    }
    return official_aggregate_score(**means, metric_contract=metric_contract)
