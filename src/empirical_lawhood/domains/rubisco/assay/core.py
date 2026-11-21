"""Bounded stationary competing-gas assay and independent product reduction.

Adapted from icf-yolo ec4f7ad3c81ffb2d9734babd866f933c794398cc,
adapters/simulators/rubisco_assay_v1/core.py. Concentrations are dissolved
micromolar, time is seconds and products are micromoles per micromole of
activated catalytic sites. Stationary occupancies describe a conditional
ensemble; they are neither sampled trajectories nor elementary binding rates.
The protocol fixes 298.15 K, activation, saturating RuBP and clamped gases.
Supplied macroscopic kinetics do not predict the rates of an unseen protein.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def _positive(value: float, name: str, *, zero: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value):
        raise ValueError(f"{name} must be a finite real scalar")
    if value < 0 or (not zero and value == 0):
        raise ValueError(f"{name} must be {'nonnegative' if zero else 'positive'}")


@dataclass(frozen=True, slots=True)
class Kinetics:
    """kcat,C/O in s^-1 and KC/KO in micromolar, all supplied."""

    kcat_c: float
    kc: float
    kcat_o: float
    ko: float

    def __post_init__(self) -> None:
        for name in ("kcat_c", "kc", "kcat_o", "ko"):
            _positive(getattr(self, name), name)

    @property
    def specificity(self) -> float:
        return (self.kcat_c / self.kc) / (self.kcat_o / self.ko)


@dataclass(frozen=True, slots=True)
class GasQuery:
    co2_um: float
    o2_um: float
    duration_s: float = 1.0

    def __post_init__(self) -> None:
        _positive(self.co2_um, "CO2", zero=True)
        _positive(self.o2_um, "O2", zero=True)
        _positive(self.duration_s, "duration")
        if max(self.co2_um, self.o2_um) > 10000 or self.duration_s > 1000:
            raise ValueError("query exceeds the declared finite assay domain")


@dataclass(frozen=True, slots=True)
class Products:
    pga_per_site: float
    pgly_per_site: float
    duration_s: float
    balance_residual: float

    def __post_init__(self) -> None:
        for name in ("pga_per_site", "pgly_per_site", "balance_residual"):
            _positive(getattr(self, name), name, zero=True)
        _positive(self.duration_s, "duration")
        if self.pga_per_site < self.pgly_per_site:
            raise ValueError("products violate carboxylation/oxygenation stoichiometry")


def execute_assay(parameters: Kinetics, query: GasQuery) -> Products:
    """Solve normalized stationary occupancy, then count both products.

    The three weights are uncommitted, CO2-committed and O2-committed states
    in this macroscopic representation only. The balance solver is distinct
    from the closed-form oracle; both implement the same supplied relation.
    """
    import numpy as np

    c, o = query.co2_um / parameters.kc, query.o2_um / parameters.ko
    if not isfinite(c) or not isfinite(o):
        raise ArithmeticError("supplied kinetics exceed finite occupancy arithmetic")
    matrix = np.array([[1.0, 1.0, 1.0], [-c, 1.0, 0.0], [-o, 0.0, 1.0]])
    rhs = np.array([1.0, 0.0, 0.0])
    occupancy = np.linalg.solve(matrix, rhs)
    if not np.isfinite(occupancy).all() or (occupancy < -1e-12).any():
        raise ArithmeticError("invalid stationary occupancy")
    residual = float(np.max(np.abs(matrix @ occupancy - rhs)))
    carbox = parameters.kcat_c * float(occupancy[1]) * query.duration_s
    oxygen = parameters.kcat_o * float(occupancy[2]) * query.duration_s
    return Products(2 * carbox + oxygen, oxygen, query.duration_s, residual)


def reduce_products(products: Products) -> tuple[float, float]:
    """Infer rates separately from PGA=2*C+O and phosphoglycolate=O."""
    return ((products.pga_per_site - products.pgly_per_site) / (2 * products.duration_s),
            products.pgly_per_site / products.duration_s)


def reference_rates(parameters: Kinetics, query: GasQuery) -> tuple[float, float]:
    """Closed-form check; never called by the product-generating solver."""
    c, o = query.co2_um / parameters.kc, query.o2_um / parameters.ko
    denominator = 1 + c + o
    if not isfinite(denominator):
        raise ArithmeticError("supplied kinetics exceed finite reference arithmetic")
    return (parameters.kcat_c * c / denominator, parameters.kcat_o * o / denominator)


def next_query(previous: GasQuery, observed: Products) -> GasQuery:
    """Frozen rule doubles CO2 if vo/vc>0.1, otherwise halves it.

    This query action preserves O2 and duration. It is not a protein edit or
    evidence of comparative controller value. The observation must belong to
    the preceding query duration; the canonical layer checks its identity.
    """
    if previous.duration_s != observed.duration_s:
        raise ValueError("feedback observation has a different query duration")
    vc, vo = reduce_products(observed)
    if vc <= 0 or previous.co2_um <= 0:
        raise ValueError("feedback needs an evaluable positive carboxylation observation")
    concentration = previous.co2_um * (2 if vo / vc > 0.1 else 0.5)
    if not 1 <= concentration <= 1000:
        raise ValueError("NONATTEMPT: feedback action outside declared CO2 support")
    return GasQuery(concentration, previous.o2_um, previous.duration_s)


def compatible_kinetics(
    *, kcat_c: float, kc_air: float, specificity: float, air_o2_um: float, ko: float,
) -> Kinetics:
    """One member of the nonidentifiable family from three summary values.

    KC=KC,air/(1+airO2/KO); kcat,O=kcat,C*KO/(KC*S). Derived oxygenation is
    not a fourth observation. Alternative KO choices preserve those summaries
    and change off-air gas responses.
    """
    for name, value in (("kcat_c", kcat_c), ("kc_air", kc_air),
                        ("specificity", specificity), ("ko", ko)):
        _positive(value, name)
    _positive(air_o2_um, "air O2", zero=True)
    kc = kc_air / (1 + air_o2_um / ko)
    return Kinetics(kcat_c, kc, kcat_c * ko / (kc * specificity), ko)


def log_sensitivity(parameters: Kinetics, queries: tuple[GasQuery, ...]) -> NDArray[np.float64]:
    """Local Jacobian of log(vc,vo) versus log(kcat,C,KC,kcat,O,KO)."""
    import numpy as np

    if not queries or len(queries) > 16 or any(q.co2_um <= 0 or q.o2_um <= 0 for q in queries):
        raise ValueError("bounded log information requires one to sixteen positive-gas queries")
    rows = []
    for query in queries:
        c, o = query.co2_um / parameters.kc, query.o2_um / parameters.ko
        d = 1 + c + o
        if not isfinite(d):
            raise ArithmeticError("supplied kinetics exceed finite sensitivity arithmetic")
        rows.extend(((1, -1 + c / d, 0, o / d), (0, c / d, 1, -1 + o / d)))
    return np.asarray(rows, dtype=float)


def specificity_energy_scale(ratio: float, temperature_k: float = 298.15) -> float:
    """RT ln(ratio) in kJ/mol, a sensitivity scale rather than a rate bridge."""
    _positive(ratio, "specificity ratio")
    _positive(temperature_k, "temperature")
    return 0.00831446261815324 * temperature_k * log(ratio)
