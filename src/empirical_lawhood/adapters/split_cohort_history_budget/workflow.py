"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
import secrets
from empirical_lawhood.domains.history.split_cohort_history_budget.contracts import SplitCohortHistoryBudgetConfig, SplitCohortHistoryBudgetPhase, SplitCohortHistoryBudgetSeedRosterCommitment
from empirical_lawhood.domains.history.split_cohort_history_budget.runtime_contracts import SplitCohortHistoryBudgetSeedRoster

from empirical_lawhood.domains.history.split_cohort_history_budget.workflow import (
    build_seed_roster as _science_build_seed_roster,
)

def create_seed_roster(config: SplitCohortHistoryBudgetConfig, *, injected_seeds: tuple[bytes, ...] | None=None) -> tuple[SplitCohortHistoryBudgetSeedRoster, SplitCohortHistoryBudgetSeedRosterCommitment]:
    if config.phase is not SplitCohortHistoryBudgetPhase.NOMINATION:
        raise ValueError('seed roster creation requires the nomination config')
    seeds = tuple((secrets.token_bytes(32) for _ in config.unit_ids)) if injected_seeds is None else injected_seeds
    return _science_build_seed_roster(config, injected_seeds=seeds)
