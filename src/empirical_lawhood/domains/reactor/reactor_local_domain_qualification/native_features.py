"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
import numpy as np
from empirical_lawhood.domains.reactor.reactor_causal_response.numerical import CausalFeatures, Observation
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.config import LocalQualificationDesign
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode
from empirical_lawhood.domains.reactor.reactor_causal_response.actuator import Actuator
from empirical_lawhood.domains.reactor.reactor_causal_response.projection import project_episode

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
    design: LocalQualificationDesign,
    donors: tuple[NativeEpisode, ...],
) -> tuple[tuple[str, int | None, int | None, tuple[int, ...]], ...]:
    """Choose earliest causal encounter; same-clock tie uses policy 0, 1, 2."""
    projected: list[tuple[np.ndarray, np.ndarray] | None] = []
    for episode in donors:
        if not episode.complete:
            projected.append(None)
        else:
            projected.append(
                project_episode(
                    tuple(Observation(*map(float, r)) for r in episode.observations),
                    tuple((float(r[0]), float(r[1])) for r in episode.requests),
                )
            )
    result: list[tuple[str, int | None, int | None, tuple[int, ...]]] = []
    for domain in design.atlas.candidates:
        encounters = []
        for policy, projection in enumerate(projected):
            if projection is None:
                continue
            x, actions = projection
            eligible = np.flatnonzero(domain.proposed_support(x, actions))
            # Prefer a real intervention opportunity. This predicate uses only
            # causal observations and known actuator delivery, never responses.
            for callback in eligible:
                # Partition/support coordinates exclude the candidate action.
                # The eligible donor therefore shares its causal context with
                # all measured words; no quadratic prefix reconstruction.
                actions_here = domain.actions
                observation = Observation(*map(float, donors[policy].observations[callback]))
                previous = (
                    (0.0, 316.0)
                    if callback == 0
                    else tuple(map(float, donors[policy].stages[callback - 1, 2:]))
                )
                projections = Actuator().project(observation, (previous[0], previous[1]))
                if len({projections[a].delivery_key for a in actions_here}) < 2:
                    continue
                encounters.append((int(callback), policy, actions_here))
                break
        if encounters:
            chosen_callback, chosen_policy, chosen_actions = min(encounters)
            result.append((domain.domain_id, chosen_policy, chosen_callback, chosen_actions))
        else:
            result.append((domain.domain_id, None, None, ()))
    return tuple(result)
