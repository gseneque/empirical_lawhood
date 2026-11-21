"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from typing import Sequence
from empirical_lawhood.adapters.simulators.quantum_trajectory_preparation_qualification.checkpoint import trajectory_from_bytes, trajectory_to_bytes
from empirical_lawhood.domains.quantum.trajectory_preparation_qualification.joint_inference import PreparedObservation
from empirical_lawhood.domains.quantum.trajectory_preparation_qualification.schemas import QuantumTrajectoryPreparationQualificationConfig
from empirical_lawhood.domains.quantum.trajectory_preparation_qualification.types import PreparationUnit

from empirical_lawhood.domains.quantum.trajectory_preparation_qualification.acquisition import (
    continue_preparation_trajectory as _science_continue_preparation_trajectory,
    observe_prepared_trajectory as _science_observe_prepared_trajectory,
    simulate_preparation_unit as _science_simulate_preparation_unit,
)

def trajectory_worker(unit: PreparationUnit, *, scientific_seed: int, endpoints: Sequence[float]) -> bytes:
    return trajectory_to_bytes(_science_simulate_preparation_unit(unit, scientific_seed=scientific_seed, endpoints=endpoints))


def continue_trajectory_worker(payload: bytes, *, endpoints: Sequence[float]) -> bytes:
    return trajectory_to_bytes(_science_continue_preparation_trajectory(trajectory_from_bytes(payload), endpoints=endpoints))


def observations_from_trajectory(payload: bytes, unit: PreparationUnit, *, config: QuantumTrajectoryPreparationQualificationConfig) -> tuple[PreparedObservation, ...]:
    return _science_observe_prepared_trajectory(trajectory_from_bytes(payload), unit, config=config)
