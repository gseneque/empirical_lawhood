"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
import numpy as np
from empirical_lawhood.domains.reactor.reactor_causal_response.numerical import CausalFeatures, Observation
from empirical_lawhood.domains.reactor.reactor_prepared_feed_qualification.config import FeedQualificationDesign
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode
from empirical_lawhood.domains.reactor.reactor_causal_response.actuator import Actuator

def candidate_features(episode: NativeEpisode, callback: int) -> tuple[np.ndarray, np.ndarray]:
    """Causal prefix only; no native concentrations or post-run truth read here."""
    state = CausalFeatures()
    for row in episode.observations[: callback + 1]:
        state.append(Observation(*map(float, row)))
    previous = (
        (0.0, 316.0) if callback == 0 else tuple(map(float, episode.stages[callback - 1, 2:]))
    )
    observation = Observation(*map(float, episode.observations[callback]))
    projections = Actuator().project(observation, (previous[0], previous[1]))
    return np.asarray([state.features(previous[1], p) for p in projections]), np.asarray(
        [p.requested for p in projections]
    )

def assay_anchors(
    design: FeedQualificationDesign,
    donors: tuple[NativeEpisode, ...],
) -> tuple[tuple[str, int | None, int | None, tuple[int, ...]], ...]:
    "First permitted native preparation prefix; no post-handoff labels participate."
    if len(donors) != 1:
        raise ValueError("prepared feed protocol has exactly one exploration policy")
    donor = donors[0]
    domain = design.atlas.domains[0]
    if not donor.complete:
        return ((domain.domain_id, None, None, ()),)
    state = CausalFeatures()
    for callback, row in enumerate(donor.observations[:601]):
        observation = Observation(*map(float, row))
        state.append(observation)
        previous = (
            (0.0, 316.0)
            if callback == 0
            else (float(donor.stages[callback - 1, 2]), float(donor.stages[callback - 1, 3]))
        )
        if observation.time < 600 or previous[0] > 0.016:
            continue
        projections = Actuator().project(observation, previous)
        selected = tuple(projections[a] for a in domain.actions)
        x = np.asarray([state.features(previous[1], p) for p in selected])
        if (
            domain.proposed_support(x, np.asarray(domain.actions)).all()
            and len({p.delivery_key for p in selected}) == 3
            and selected[0].mean_feed == 0
            and all(p.applied[1] == previous[1] for p in selected)
        ):
            return ((domain.domain_id, 0, callback, domain.actions),)
    return ((domain.domain_id, None, None, ()),)
