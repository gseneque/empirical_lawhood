"""Independent resistor-chain and linear-observability reference controls.

These oracles import no production generator, observer, evaluator or adapter.
They compare a closed-form circuit solution and independent linear algebra
routes with the supplied operands; production calculations never call them.
"""
from __future__ import annotations
from decimal import Decimal
from itertools import combinations, permutations
from typing import Protocol
import numpy as np
from scipy.linalg import expm, svdvals

class ResistanceChain(Protocol):
    @property
    def left_source_resistance_ohms(self) -> Decimal: ...
    @property
    def right_termination_resistance_ohms(self) -> Decimal: ...
    @property
    def interior_resistances_ohms(self) -> tuple[Decimal, ...]: ...

def _analytic_equilibrium(descriptor: ResistanceChain, amplitude: float) -> np.ndarray:
    left = float(descriptor.left_source_resistance_ohms)
    right = float(descriptor.right_termination_resistance_ohms)
    interior = np.asarray(descriptor.interior_resistances_ohms, dtype=np.float64)
    current = amplitude / (left + float(np.sum(interior)) + right)
    preceding = np.concatenate((np.zeros(1), np.cumsum(interior)))
    return amplitude - current * (left + preceding)

def _brute_matching_rank(support: np.ndarray) -> int:
    rows, columns = support.shape
    for rank in range(min(rows, columns), -1, -1):
        for selected_rows in combinations(range(rows), rank):
            for selected_columns in combinations(range(columns), rank):
                if any(
                    all(
                        support[row, column]
                        for row, column in zip(
                            selected_rows,
                            ordered_columns,
                            strict=True,
                        )
                    )
                    for ordered_columns in permutations(selected_columns)
                ):
                    return rank
    return 0

def _rank_audit(
    state_matrix: np.ndarray, receiver: np.ndarray, *, lag: float,
    maximum_depth: int, error_prefix: str, probe_depths: tuple[int, ...] | None = None,
) -> None:
    inverse = expm(-state_matrix * lag)
    blocks = []
    current = receiver.copy()
    for depth in range(maximum_depth + 1):
        if depth:
            current = current @ inverse
        blocks.append(current.copy())
        if probe_depths is not None and depth not in probe_depths:
            continue
        stack = np.vstack(blocks)
        numpy_values = np.linalg.svd(stack, compute_uv=False)
        scipy_values = svdvals(stack)
        if not np.allclose(numpy_values, scipy_values, atol=1e-10, rtol=1e-11):
            raise ValueError(f"{error_prefix}_CANARY_SVD_AUDIT_FAILED")
        duplicated = np.vstack([receiver] * (depth + 1))
        if np.linalg.matrix_rank(duplicated, tol=1e-12) > 8:
            raise ValueError(f"{error_prefix}_DUPLICATE_PRESENT_CONTROL_FAILED")
        shuffled = np.vstack(tuple(reversed(blocks)))
        if not np.allclose(
            np.linalg.svd(shuffled, compute_uv=False),
            numpy_values,
            atol=1e-10,
            rtol=1e-11,
        ):
            raise ValueError(f"{error_prefix}_SHUFFLED_LAG_CONTROL_FAILED")
