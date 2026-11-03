# SPDX-License-Identifier: MPL-2.0
"""Actual receiver observations, without changing persisted metric identities."""

from dataclasses import dataclass
from decimal import Decimal

from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_strings,
    validate_decimal,
)
from .correction_records_v2 import OfficialMetricSetV2

HISTORICAL_METRICS_SCHEMA = (
    "empirical-lawhood/physical/virtual-cell/official-metrics-table"
)


@dataclass(frozen=True, slots=True)
class ReceiverObservation:
    target_ids: tuple[str, ...]
    des: tuple[Decimal, ...]
    pds: tuple[Decimal, ...]
    mae: tuple[Decimal, ...]
    score: CanonicalRecord
    metrics_payload: bytes
    metrics_schema: str
    cell_eval_version: str
    pdex_version: str
    response_outcome_read: bool

    def __post_init__(self):
        require_sorted_unique_strings(
            self.target_ids, field_name="target_ids", allow_empty=False
        )
        for name in ("des", "pds", "mae"):
            values = getattr(self, name)
            if type(values) is not tuple or len(values) != len(self.target_ids):
                raise ValueError("actual receiver changes its complete target census")
            for value in values:
                validate_decimal(value, field_name=name)
        from .analysis import OfficialAggregateScore

        if type(self.score) is not OfficialAggregateScore:
            raise TypeError("actual receiver requires its original score object")
        self.score.__post_init__()
        if (
            type(self.metrics_payload) is not bytes
            or not self.metrics_payload
            or self.metrics_schema
            not in (HISTORICAL_METRICS_SCHEMA, OfficialMetricSetV2.SCHEMA)
            or not self.cell_eval_version
            or not self.pdex_version
            or self.response_outcome_read is not True
        ):
            raise ValueError(
                "actual receiver loses exact payload meaning, versions or outcome acknowledgement"
            )

    @classmethod
    def from_historical_run(cls, run):
        from .evaluation import HistoricalOfficialEvaluatorRun

        if type(run) is not HistoricalOfficialEvaluatorRun:
            raise TypeError(
                "historical observation requires its actual original receiver result"
            )
        run.__post_init__()
        return cls(
            run.target_ids,
            *(
                tuple(Decimal(str(float(value))) for value in vector)
                for vector in (run.des, run.pds, run.mae)
            ),
            run.score,
            run.metrics_arrow,
            HISTORICAL_METRICS_SCHEMA,
            run.cell_eval_version,
            run.pdex_version,
            run.response_outcome_read,
        )

    @classmethod
    def from_v2_run(cls, run):
        from .evaluation import OfficialEvaluatorRunV2

        if (
            type(run) is not OfficialEvaluatorRunV2
            or type(run.metrics) is not OfficialMetricSetV2
        ):
            raise TypeError(
                "corrected observation requires its actual versioned receiver result"
            )
        run.metrics.__post_init__()
        return cls(
            run.metrics.target_ids,
            run.metrics.des,
            run.metrics.pds,
            run.metrics.mae,
            run.score,
            run.metrics_canonical,
            OfficialMetricSetV2.SCHEMA,
            run.cell_eval_version,
            run.pdex_version,
            run.response_outcome_read,
        )


@dataclass(frozen=True, slots=True)
class CandidateValidationObservationV2:
    candidate_id: str
    receiver: ReceiverObservation
    score_standard_error: Decimal

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_stable_id

        validate_stable_id(self.candidate_id)
        if (
            type(self.receiver) is not ReceiverObservation
            or self.receiver.metrics_schema != OfficialMetricSetV2.SCHEMA
        ):
            raise TypeError(
                "corrected candidate cannot masquerade as historical Arrow metrics"
            )
        self.receiver.__post_init__()
        validate_decimal(
            self.score_standard_error,
            field_name="score_standard_error",
            minimum=Decimal(0),
        )

    @property
    def target_ids(self):
        return self.receiver.target_ids

    @property
    def score(self):
        return self.receiver.score

    @property
    def metrics_payload(self):
        return self.receiver.metrics_payload

    @property
    def metrics_schema(self):
        return self.receiver.metrics_schema

    @property
    def cell_eval_version(self):
        return self.receiver.cell_eval_version

    @property
    def pdex_version(self):
        return self.receiver.pdex_version

    @property
    def response_outcome_read(self):
        return self.receiver.response_outcome_read
