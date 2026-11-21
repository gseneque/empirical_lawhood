"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Final
from empirical_lawhood.domains.biology.virtual_cell.analysis import adjudicate_placement
from empirical_lawhood.domains.biology.virtual_cell.config import OFFICIAL_FINAL_TOP100_SHA256
from empirical_lawhood.domains.biology.virtual_cell.contracts import LeaderboardSnapshot, MetricContract, PlacementAdjudication, PredictionCommitment


OFFICIAL_FINAL_TOP100_SOURCE_URL: Final = "https://virtualcellchallenge.org/2025"


OFFICIAL_FINAL_TOP100_CAPTURED_AT_UTC: Final = "2026-08-06T01:50:57Z"


_EXPECTED_FIELDS: Final = frozenset(
    {
        "deScore",
        "deSpearmanLfcSig",
        "deSpearmanSig",
        "description",
        "errorInfo",
        "id",
        "isFinal",
        "maeScore",
        "modelName",
        "noAbsPertScore",
        "noAbsScoreAvg",
        "organization",
        "pearsonDelta",
        "pertScore",
        "prAuc",
        "rank",
        "scoreAvg",
        "status",
        "submissionCount",
        "submissionDate",
        "teamId",
        "teamMembers",
        "teamName",
    }
)


def adjudicate_official_final_top100(
    *,
    prediction: PredictionCommitment,
    metric_contract: MetricContract,
    candidate_score: Decimal,
    snapshot: LeaderboardSnapshot,
) -> PlacementAdjudication:
    """Adjudicate after scoring while enforcing frozen prediction/metric lineage."""

    if prediction.metric_contract_sha256 != metric_contract.fingerprint():
        raise ValueError("placement metric contract differs from prediction commitment")
    if snapshot.source_sha256 != OFFICIAL_FINAL_TOP100_SHA256:
        raise ValueError("placement snapshot is not the held official final top 100")
    return adjudicate_placement(
        adjudication_id="placement.virtual-cell-2025-official-final",
        prediction_commitment_id=prediction.commitment_id,
        metric_contract_sha256=metric_contract.fingerprint(),
        leaderboard_snapshot_sha256=snapshot.fingerprint(),
        candidate_score=candidate_score,
        snapshot=snapshot,
    )
