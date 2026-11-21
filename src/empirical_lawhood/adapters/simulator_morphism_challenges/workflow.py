"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
import secrets
from empirical_lawhood.domains.history.simulator_morphism_challenges.contracts import SimulatorMorphismChallengeConfig, SimulatorMorphismChallengePhase, SimulatorMorphismChallengeSeedRosterCommitment
from empirical_lawhood.domains.history.simulator_morphism_challenges.runtime_contracts import SimulatorMorphismChallengeSeedRoster

from empirical_lawhood.domains.history.simulator_morphism_challenges.workflow import (
    build_seed_roster as _science_build_seed_roster,
)

def create_seed_roster(config: SimulatorMorphismChallengeConfig, *, injected_seeds: tuple[bytes, ...] | None=None) -> tuple[SimulatorMorphismChallengeSeedRoster, SimulatorMorphismChallengeSeedRosterCommitment]:
    if config.phase is not SimulatorMorphismChallengePhase.NOMINATION:
        raise ValueError('seed roster creation requires the nomination config')
    seeds = tuple((secrets.token_bytes(32) for _ in config.unit_ids)) if injected_seeds is None else injected_seeds
    return _science_build_seed_roster(config, injected_seeds=seeds)
