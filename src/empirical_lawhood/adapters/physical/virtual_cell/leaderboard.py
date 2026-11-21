"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from decimal import Decimal
from hashlib import sha256
import json
from typing import cast
from empirical_lawhood.domains.biology.virtual_cell.config import OFFICIAL_FINAL_RANKED_ENTRY_COUNT, OFFICIAL_FINAL_SUMMARY_COMPETITOR_COUNT, OFFICIAL_FINAL_TOP100_SHA256, OFFICIAL_FINAL_TOP100_SIZE_BYTES
from empirical_lawhood.domains.biology.virtual_cell.contracts import LeaderboardEntry, LeaderboardSnapshot, VirtualCellContractError

from empirical_lawhood.domains.biology.virtual_cell.leaderboard_assessment import (
    OFFICIAL_FINAL_TOP100_CAPTURED_AT_UTC as _science_OFFICIAL_FINAL_TOP100_CAPTURED_AT_UTC,
    OFFICIAL_FINAL_TOP100_SOURCE_URL as _science_OFFICIAL_FINAL_TOP100_SOURCE_URL,
    _EXPECTED_FIELDS,
)

def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON number is forbidden: {value}")


def _text(row: dict[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise VirtualCellContractError(f"official leaderboard {field} is invalid")
    # Team/model labels are presentation metadata.  The held API response has
    # two model names with surrounding whitespace; canonical records trim that
    # transport artifact while source_sha256 continues to bind the exact bytes.
    return value.strip()


def decode_official_final_top100(
    payload: bytes,
    *,
    expected_sha256: str = OFFICIAL_FINAL_TOP100_SHA256,
    expected_size_bytes: int = OFFICIAL_FINAL_TOP100_SIZE_BYTES,
    total_ranked_entries: int = OFFICIAL_FINAL_RANKED_ENTRY_COUNT,
    summary_competitor_count: int = OFFICIAL_FINAL_SUMMARY_COMPETITOR_COUNT,
) -> LeaderboardSnapshot:
    """Decode only an exact, full-precision official final top-100 snapshot."""

    if not payload or len(payload) != expected_size_bytes:
        raise VirtualCellContractError("official final top-100 byte count differs")
    observed_sha256 = sha256(payload).hexdigest()
    if observed_sha256 != expected_sha256:
        raise VirtualCellContractError("official final top-100 SHA-256 differs")
    try:
        raw = json.loads(
            payload.decode("utf-8"),
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise VirtualCellContractError("official final top-100 JSON is invalid") from error
    if not isinstance(raw, list) or len(raw) != 100:
        raise VirtualCellContractError("official final leaderboard is not the exact top 100")
    entries = []
    for index, value in enumerate(raw, start=1):
        if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
            raise VirtualCellContractError("official leaderboard row is not an object")
        row = cast(dict[str, object], value)
        if set(row) != _EXPECTED_FIELDS:
            raise VirtualCellContractError("official leaderboard row fields differ")
        rank = row["rank"]
        score = row["scoreAvg"]
        if (
            isinstance(rank, bool)
            or not isinstance(rank, int)
            or rank != index
            or not isinstance(score, Decimal)
            or row["isFinal"] is not True
            or row["status"] != "published"
        ):
            raise VirtualCellContractError("official leaderboard final/rank/score fields differ")
        entries.append(
            LeaderboardEntry(
                rank=rank,
                entry_id=_text(row, "id"),
                team_id=_text(row, "teamId"),
                team_name=_text(row, "teamName"),
                model_name=_text(row, "modelName"),
                score=score,
            )
        )
    return LeaderboardSnapshot(
        snapshot_id="leaderboard.virtual-cell-2025-official-final-top100",
        source_url=_science_OFFICIAL_FINAL_TOP100_SOURCE_URL,
        captured_at_utc=_science_OFFICIAL_FINAL_TOP100_CAPTURED_AT_UTC,
        total_ranked_entries=total_ranked_entries,
        summary_competitor_count=summary_competitor_count,
        entries=tuple(entries),
        full_precision=True,
        complete=False,
        tie_policy=(
            "official API ordinal rank with full-precision score equality reported as an "
            "interval; unpublished ranks remain bounded, never imputed"
        ),
        source_sha256=observed_sha256,
    )
