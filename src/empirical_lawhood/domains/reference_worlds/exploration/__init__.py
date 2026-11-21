"""Registered substrate-neutral automated exploration capabilities."""

from empirical_lawhood.domains.reference_worlds.exploration.catalog import exploration_catalog_snapshot
from empirical_lawhood.domains.reference_worlds.exploration.detectors import DetectorRegistry, bind_evidence_view, default_detector_registry
from empirical_lawhood.domains.reference_worlds.exploration.execution import AnalysisCoordinateObservation, AutomaticSkeptic, ExplorationWaveInput, ExplorationWaveResult, HypothesisSynthesizer, RegisteredAnalysisExecutor, execute_wave
from empirical_lawhood.domains.reference_worlds.exploration.portfolio import ExplorationPortfolioPlanner, default_portfolio_policy
from empirical_lawhood.domains.reference_worlds.exploration.registry import exploration_capability_keys, exploration_capability_registry
from empirical_lawhood.domains.reference_worlds.exploration.templates import AnalysisProposalFactory, default_template_library

__all__ = [
    "AnalysisProposalFactory",
    "AnalysisCoordinateObservation",
    "AutomaticSkeptic",
    "DetectorRegistry",
    "ExplorationPortfolioPlanner",
    "ExplorationWaveInput",
    "ExplorationWaveResult",
    "HypothesisSynthesizer",
    "RegisteredAnalysisExecutor",
    "bind_evidence_view",
    "default_detector_registry",
    "default_portfolio_policy",
    "default_template_library",
    "exploration_catalog_snapshot",
    "execute_wave",
    'exploration_capability_keys',
    'exploration_capability_registry',
]
