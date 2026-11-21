"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from typing import Any
import numpy as np
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import TapeController

class WatchedPreparedTape(TapeController):
    """Remember the actual delayed callback seen by the fixed tape."""

    def __init__(self, tape: np.ndarray) -> None:
        super().__init__(tape)
        self.latest: tuple[float, float, float, float] | None = None

    def reset(self, spec: dict[str, Any]) -> None:
        self.latest = None
        super().reset(spec)

    def step(self, t_s: float, y: dict[str, float], dt_s: float) -> tuple[float, float]:
        self.latest = (
            t_s, y["t_reactor_k"], y["t_jacket_k"], y["dosed_kg"]
        )
        return TapeController.step(self, t_s, y, dt_s)
