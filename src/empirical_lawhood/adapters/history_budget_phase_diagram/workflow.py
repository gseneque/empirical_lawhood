"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
import secrets
from empirical_lawhood.domains.history.history_budget_phase_diagram.contracts import HistoryBudgetPhaseDiagramConfig, HistoryBudgetPhaseDiagramPhase, HistoryBudgetPhaseDiagramSeedRosterCommitment
from empirical_lawhood.domains.history.history_budget_phase_diagram.runtime_contracts import HistoryBudgetPhaseDiagramSeedRoster

from empirical_lawhood.domains.history.history_budget_phase_diagram.workflow import (
    build_seed_roster as _science_build_seed_roster,
)

def create_seed_roster(config: HistoryBudgetPhaseDiagramConfig, *, injected_seeds: tuple[bytes, ...] | None=None) -> tuple[HistoryBudgetPhaseDiagramSeedRoster, HistoryBudgetPhaseDiagramSeedRosterCommitment]:
    if config.phase is not HistoryBudgetPhaseDiagramPhase.NOMINATION:
        raise ValueError('seed roster creation requires the nomination config')
    seeds = tuple((secrets.token_bytes(32) for _ in config.unit_ids)) if injected_seeds is None else injected_seeds
    return _science_build_seed_roster(config, injected_seeds=seeds)
