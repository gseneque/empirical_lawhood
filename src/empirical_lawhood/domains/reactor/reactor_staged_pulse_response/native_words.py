"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from dataclasses import dataclass
from decimal import Decimal as D
from typing import ClassVar
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import Pulse
from empirical_lawhood.domains.reactor.reactor_causal_response.numerical import Observation
from empirical_lawhood.domains.reactor.reactor_causal_response.delivery_words import ReactorExposureWordMap
from empirical_lawhood.domains.reactor.reactor_prefix_response.finite_words import feed_action_word, project_feed_commands
from empirical_lawhood.science.response.action_contracts import OccurrenceActionWord
from empirical_lawhood.science.records.serialization import CanonicalRecord


CHART = "reactor-staged-pulse-response-finite-feed-chart"


RECEIVER = "c"




@dataclass(frozen=True, slots=True)
class PulseProjection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-staged-pulse-response/pulse-projection'
    pulse: Pulse
    guard_s: int
    mappings: tuple[ReactorExposureWordMap, ...]
    word: OccurrenceActionWord
    fixed_jacket_K: D

    def __post_init__(self) -> None:
        rates = self.pulse.rates(self.guard_s)
        if (
            self.word.receiver_id not in ("c", "c1", "c2")
            or len(self.mappings) != len(rates)
            or self.word
            != feed_action_word(
                self.mappings,
                word_id=self.word.word_id,
                history_id=self.word.retained_history_id,
                horizon_id=self.word.horizon_id,
                chart_id=CHART,
                receiver_id=self.word.receiver_id,
            )
        ):
            raise ValueError("Staged-pulse word lost its exact native/scalar map")
        start = self.mappings[0].command.time_s
        for i, (m, rate) in enumerate(zip(self.mappings, rates, strict=True)):
            if (
                m.command.time_s != start + 10 * i
                or m.command.feed_kg_s != rate
                or m.command.jacket_k != self.fixed_jacket_K
                or m.accepted[1] != self.fixed_jacket_K
                or m.applied[1] != self.fixed_jacket_K
                or any(e[3] != self.fixed_jacket_K for e in m.exposure)
            ):
                raise ValueError("Staged-pulse word changed its command, clock or fixed jacket")

    @property
    def applied_mass_kg(self) -> D:
        return sum((10 * m.applied[0] for m in self.mappings), D(0))

    @property
    def realized_mass_kg(self) -> D:
        return sum((dt * rate for m in self.mappings for _, dt, rate, _ in m.exposure), D(0))

def project_pulse(
    observation: Observation,
    previous: tuple[float, float],
    pulse: Pulse,
    *,
    decision_id: str,
    history_id: str,
    horizon_id: str,
    guard_s: int = 120,
    receiver_id: str = RECEIVER,
) -> PulseProjection:
    if not 0 <= previous[0] <= 0.016:
        raise ValueError("Staged-pulse pulse is outside its qualified previous-feed chart")
    maps = project_feed_commands(
        observation,
        previous,
        pulse.rates(guard_s),
        decision_id=decision_id,
        history_id=history_id,
        horizon_id=horizon_id,
    )
    word = feed_action_word(
        maps,
        word_id=f"{decision_id}.word",
        history_id=history_id,
        horizon_id=horizon_id,
        chart_id=CHART,
        receiver_id=receiver_id,
    )
    return PulseProjection(pulse, guard_s, maps, word, D(repr(float(previous[1]))))
