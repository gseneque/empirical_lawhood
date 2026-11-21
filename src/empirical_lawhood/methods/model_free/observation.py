# SPDX-License-Identifier: MPL-2.0
"""Explicit observation, clock and finite alphabet contracts."""
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class ObservationContract:
    observation_id: str
    variables: tuple[str, ...]
    units: tuple[str, ...]
    bin_edges: tuple[tuple[float, ...], ...]
    sample_interval: float
    protocol_id: str
    clock: str = "physical"
    target_law: str = "finite_record_root_average"
    stationarity_qualified: bool = False
    parity: tuple[int, ...] = ()
    filtering: str = "none"

    def __post_init__(self):
        if not self.observation_id or not self.protocol_id or not self.filtering:
            raise ValueError("observation, protocol and filtering identities are required")
        if not 1 <= len(self.variables) <= 3 or len(set(self.variables)) != len(self.variables):
            raise ValueError("declare one to three distinct instantaneous observables")
        if len(self.units) != len(self.variables) or any(not u for u in self.units):
            raise ValueError("every observable requires its actual unit")
        if len(self.bin_edges) != len(self.variables):
            raise ValueError("every observable requires frozen bin boundaries")
        for edges in self.bin_edges:
            if len(edges) < 2 or any(not math.isfinite(float(x)) for x in edges):
                raise ValueError("bin boundaries must be finite and contain an interval")
            if any(b <= a for a, b in zip(edges, edges[1:])):
                raise ValueError("bin boundaries must increase strictly")
        if not math.isfinite(self.sample_interval) or self.sample_interval <= 0:
            raise ValueError("sample interval must be finite and positive")
        if self.clock not in {"physical", "optimizer", "algorithmic"}:
            raise ValueError("unknown clock")
        if self.target_law not in {"finite_record_root_average", "stationary", "protocol_age"}:
            raise ValueError("unknown probability law")
        if self.target_law == "stationary" and not self.stationarity_qualified:
            raise ValueError("constant controls alone do not qualify stationarity")
        if self.parity and (len(self.parity) != len(self.variables) or any(p not in (-1, 1) for p in self.parity)):
            raise ValueError("time-reversal parity must be declared per observable")

    @property
    def alphabet_size(self):
        return math.prod(len(edges) - 1 for edges in self.bin_edges)

    def require_physical_time(self):
        if self.clock != "physical":
            raise ValueError("optimizer/algorithmic iterations do not establish physical time")


def discretize(values, contract: ObservationContract):
    """Closed final bin, otherwise left-closed bins; no implicit tail clipping.

Nonfinite and out-of-range rows become -1 and are separately counted. Their
mass remains missing in downstream counts and cannot support equivalence.
"""
    if not isinstance(contract, ObservationContract):
        raise TypeError("an ObservationContract is required")
    x = np.asarray(values, dtype=float)
    if x.ndim == 1 and len(contract.variables) == 1:
        x = x[:, None]
    if x.ndim != 2 or x.shape[1] != len(contract.variables):
        raise ValueError("observation dimensions differ from the frozen map")
    finite = np.all(np.isfinite(x), axis=1)
    outside = np.zeros(len(x), dtype=bool)
    codes = np.zeros(len(x), dtype=np.int64)
    for j, edges in enumerate(contract.bin_edges):
        edges = np.asarray(edges)
        radix = len(edges) - 1
        outside |= (x[:, j] < edges[0]) | (x[:, j] > edges[-1])
        digit = np.searchsorted(edges, x[:, j], side="right") - 1
        digit[x[:, j] == edges[-1]] = radix - 1
        codes = codes * radix + np.clip(digit, 0, radix - 1)
    codes[~finite | outside] = -1
    return {
        "symbols": codes.tolist(), "alphabet_size": contract.alphabet_size,
        "observation_id": contract.observation_id, "clock": contract.clock,
        "target_law": contract.target_law, "protocol_id": contract.protocol_id,
        "sample_interval": float(contract.sample_interval),
        "record_length": len(x), "nonfinite_rows": int(np.sum(~finite)),
        "out_of_range_rows": int(np.sum(finite & outside)),
        "missing_rows": int(np.sum(codes < 0)),
    }
