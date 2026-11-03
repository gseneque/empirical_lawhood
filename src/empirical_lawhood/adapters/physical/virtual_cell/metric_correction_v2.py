# SPDX-License-Identifier: MPL-2.0
"""Explicit corrected metric meaning; historical crossed bytes stay historical.

The source mapping follows donor commit 96bdd9194e0a56a4d27bc6048cbc37816c06be00.
This module performs no evaluator, outcome or artifact access.
"""

from decimal import Decimal
import hashlib

import numpy as np

from .correction_records_v2 import (
    CORRECTIVE_SOURCE_COMMIT as CORRECTIVE_SOURCE_COMMIT,
    DES_SOURCE_COLUMN as DES_SOURCE_COLUMN,
    PDS_SOURCE_COLUMN as PDS_SOURCE_COLUMN,
    MetricSourceSemantics as MetricSourceSemantics,
    OfficialMetricGaugeV2 as OfficialMetricGaugeV2,
    OfficialMetricSetV2 as OfficialMetricSetV2,
    require_metric_contract_gauge as require_metric_contract_gauge,
)


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


def correct_historical_crosswired_metrics(
    payload: bytes, *, gauge: OfficialMetricGaugeV2
):
    """Read only the original Arrow contract and produce a separate v2 record.

    Successor canonical records cannot enter this reader, preventing a second
    swap of an already corrected artifact. Optional Arrow dependencies are
    needed only when this explicitly selected historical reader is invoked.
    """
    if type(gauge) is not OfficialMetricGaugeV2:
        raise TypeError("historical correction requires the selected v2 gauge")
    if payload.lstrip().startswith(b"{"):
        raise ValueError(
            "historical crossed reader refuses successor canonical records"
        )
    from .codecs import decode_official_metrics

    target_ids, old_des, old_pds, mae = decode_official_metrics(payload)
    return OfficialMetricSetV2(
        gauge,
        MetricSourceSemantics.HISTORICAL_CROSSED_V1,
        hashlib.sha256(payload).hexdigest(),
        tuple(target_ids),
        *(
            tuple(Decimal(str(value)) for value in values)
            for values in (old_pds, old_des, mae)
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
    from .analysis import official_aggregate_score

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
