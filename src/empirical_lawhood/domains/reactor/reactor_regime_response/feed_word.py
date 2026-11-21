"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass, replace
from decimal import Decimal as D
from typing import ClassVar
from empirical_lawhood.domains.reactor.reactor_causal_response.numerical import Projection
from empirical_lawhood.domains.reactor.reactor_causal_response.delivery_words import ReactorExposureWordMap
from empirical_lawhood.science.response.action_contracts import ActionOccurrenceGroup, OccurrenceActionWord, ActionWordMode
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.domains.reactor.reactor_regime_response.science import CHART, HORIZON, RECEIVERS

SUPPORT = CHART

RECEIVER = RECEIVERS[1]

def scalar_feed_word(full: ReactorExposureWordMap) -> OccurrenceActionWord:
    """Project only the feed occurrence, retaining all four native stages."""
    selected = tuple(
        occurrence
        for occurrence in full.word.occurrences
        if occurrence.channel.controller_quantity_id == "reactor-feed"
    )
    if not selected or len(selected) * 2 != len(full.word.occurrences):
        raise ValueError("native full profile lacks one feed channel per held interval")
    feed = tuple(
        replace(
            occurrence,
            channel=replace(occurrence.channel, support_contract_id=SUPPORT),
        )
        for occurrence in selected
    )
    allowed = {occurrence.occurrence_id for occurrence in selected}
    groups = tuple(
        ActionOccurrenceGroup(
            group.group_id,
            tuple(member for member in group.members if member.occurrence_id in allowed),
        )
        for group in full.word.groups
    )
    if any(len(group.members) != 1 for group in groups):
        raise ValueError("feed projection lost a held native interval")
    return OccurrenceActionWord(
        f"{full.command.decision_id}.feed.word",
        ActionWordMode.SEQUENTIAL,
        feed,
        groups,
        full.word.ordering_clock_id,
        full.word.ordering_time_unit,
        full.word.ordering_coordinate_frame,
        full.word.ordering_origin,
        SUPPORT,
        full.word.retained_history_id,
        RECEIVER,
        HORIZON,
        tuple(f"{full.command.decision_id}.feed.prefix.{i:02d}" for i in range(len(feed) + 1)),
        full.word.support_status,
        full.word.reason_codes,
    )

@dataclass(frozen=True, slots=True)
class ReactorFeedOnlyWordMap(CanonicalRecord):
    """Scalar law action plus the one unchanged absolute jacket denominator."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-regime-response/reactor-feed-only-word-map'
    full_native: ReactorExposureWordMap
    scalar_word: OccurrenceActionWord
    fixed_jacket_K: D

    def __post_init__(self) -> None:
        if self.scalar_word != scalar_feed_word(self.full_native):
            raise ValueError("scalar feed word differs from the exact full native projection")
        if (
            self.full_native.command.jacket_k != self.fixed_jacket_K
            or self.full_native.accepted[1] != self.fixed_jacket_K
            or self.full_native.applied[1] != self.fixed_jacket_K
            or any(row[3] != self.fixed_jacket_K for row in self.full_native.exposure)
        ):
            raise ValueError("fixed absolute jacket changed across native delivery stages")
        if self.full_native.command.feed_kg_s == 0 and any(
            value.value != 0
            for occurrence in self.scalar_word.occurrences
            for value in (
                occurrence.requested,
                occurrence.accepted,
                occurrence.applied,
                occurrence.realized,
            )
        ):
            raise ValueError("zero-feed reference is not actually all zero")

    @classmethod
    def from_projection(
        cls,
        projection: Projection,
        *,
        decision_id: str,
        history_id: str,
    ) -> ReactorFeedOnlyWordMap:
        full = ReactorExposureWordMap.from_projection(
            projection,
            decision_id=decision_id,
            history_id=history_id,
            horizon_id=HORIZON,
        )
        return cls(full, scalar_feed_word(full), full.command.jacket_k)
