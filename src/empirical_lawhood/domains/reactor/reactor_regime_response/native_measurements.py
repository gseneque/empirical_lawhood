"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
import numpy as np
from empirical_lawhood.domains.reactor.reactor_regime_response.config import ROOTS
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode

def _root_assignment(root: str) -> tuple[str, int]:
    found = [(role, seed) for name, role, _, seed in ROOTS if name == root]
    if len(found) != 1:
        raise ValueError("root is outside the frozen regime-response study assignment")
    return found[0]

def _episode(
    root: str,
    key: str,
    causal: dict[str, np.ndarray],
    private: dict[str, np.ndarray],
) -> NativeEpisode | None:
    if f"{key}_observations" not in causal:
        return None
    return NativeEpisode(
        root,
        key,
        0.5 if key.endswith("v1") else 1.0,
        causal[f"{key}_observations"],
        causal[f"{key}_requests"],
        causal[f"{key}_stages"],
        causal[f"{key}_exposure"],
        private[f"{key}_grid"],
        private[f"{key}_callback_cpu"],
        None if len(causal[f"{key}_observations"]) == 2880 else "INCOMPLETE_NATIVE_BATCH",
    )
