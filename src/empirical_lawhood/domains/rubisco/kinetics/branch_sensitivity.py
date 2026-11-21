# SPDX-License-Identifier: MPL-2.0
"""Conditional two-channel arithmetic, without a mutation-to-kinetics map.

All energies are declared in kcal/mol. The caller supplies RT, carbon-channel
acceleration and the serial productive-step time fraction; none is inferred
from an electronic descriptor or a measured protein response. Oxygen-channel
arithmetic assumes a Marcus barrier with unchanged prefactor/reorganization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math

ROLE = "CONDITIONAL_HYPOTHESIS_NOT_MUTANT_KINETICS"
MAXIMUM_ABSOLUTE_INPUT = 1e100


def _number(value: float, name: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name} requires an ordinary finite numeric value")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} exceeds the numeric domain") from exc
    if not math.isfinite(number) or abs(number) > MAXIMUM_ABSOLUTE_INPUT:
        raise ValueError(f"{name} exceeds the bounded finite numeric domain")
    if positive and number <= 0:
        raise ValueError(f"{name} must be positive")
    return number


def _result(value: float, name: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{name} is not a representable finite result")
    return value


def _branch(displacement: float) -> str:
    if displacement > 0:
        return "NORMAL"
    return "ACTIVATIONLESS" if displacement == 0 else "INVERTED"


@dataclass(frozen=True, slots=True)
class BranchHypothesisV1:
    """Declared hypothetical operands; no rate or descriptor calibration."""

    carbon_acceleration: float
    initial_dg_kcal_mol: float
    dg_shift_kcal_mol: float
    reorganization_kcal_mol: float
    rt_kcal_mol: float
    productive_step_time_fraction: float
    role: str = field(default=ROLE, init=False)

    def __post_init__(self) -> None:
        for name in (
            "carbon_acceleration", "initial_dg_kcal_mol", "dg_shift_kcal_mol",
            "reorganization_kcal_mol", "rt_kcal_mol", "productive_step_time_fraction",
        ):
            value = _number(getattr(self, name), name, positive=name in {
                "carbon_acceleration", "reorganization_kcal_mol", "rt_kcal_mol",
            })
            object.__setattr__(self, name, value)
        if not 0 <= self.productive_step_time_fraction <= 1:
            raise ValueError("productive_step_time_fraction must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class ClosedShiftIntervalV1:
    """Closed finite endpoints; None denotes the corresponding infinity."""

    lower_kcal_mol: float | None
    upper_kcal_mol: float | None

    def __post_init__(self) -> None:
        for name in ("lower_kcal_mol", "upper_kcal_mol"):
            value = getattr(self, name)
            if value is None:
                continue
            if type(value) not in (int, float):
                raise ValueError("interval endpoints require ordinary finite numbers or None")
            try:
                number = _result(float(value), "interval endpoint")
            except OverflowError as exc:
                raise ValueError("interval endpoint is not representable") from exc
            object.__setattr__(self, name, number)
        if (
            self.lower_kcal_mol is not None and self.upper_kcal_mol is not None
            and self.lower_kcal_mol > self.upper_kcal_mol
        ):
            raise ValueError("closed interval endpoints must be ordered")

    def contains(self, shift_kcal_mol: float) -> bool:
        value = _number(shift_kcal_mol, "shift_kcal_mol")
        return (
            (self.lower_kcal_mol is None or value >= self.lower_kcal_mol)
            and (self.upper_kcal_mol is None or value <= self.upper_kcal_mol)
        )


@dataclass(frozen=True, slots=True)
class SpecificityShiftEnvelopeV1:
    """Complete quadratic solution, including the inverted Marcus branch.

    The nonpositive normal-branch subset answers whether lowering DG can
    preserve specificity while keeping the candidate on the normal branch.
    None means that subset is empty, not that the complete solution is empty.
    """

    discriminant_kcal_mol_squared: float
    quadratic_case: str
    all_branch_intervals: tuple[ClosedShiftIntervalV1, ...]
    normal_branch_interval: ClosedShiftIntervalV1
    normal_branch_nonpositive_interval: ClosedShiftIntervalV1 | None
    initial_branch: str
    role: str = field(default=ROLE, init=False)


@dataclass(frozen=True, slots=True)
class BranchSensitivityV1:
    hypothesis: BranchHypothesisV1
    final_dg_kcal_mol: float
    initial_barrier_kcal_mol: float
    final_barrier_kcal_mol: float
    barrier_shift_kcal_mol: float
    log_carbon_acceleration: float
    log_oxygen_acceleration: float
    log_specificity_ratio: float
    log_turnover_ratio: float
    initial_branch: str
    final_branch: str
    specificity_preserving_shifts: SpecificityShiftEnvelopeV1
    role: str = field(default=ROLE, init=False)


def specificity_preserving_shifts(hypothesis: BranchHypothesisV1) -> SpecificityShiftEnvelopeV1:
    """Solve deltaB >= -RT log(rC), retaining both allowed quadratic rays."""
    if type(hypothesis) is not BranchHypothesisV1:
        raise ValueError("a declared BranchHypothesisV1 is required")
    a = math.fsum((hypothesis.reorganization_kcal_mol, hypothesis.initial_dg_kcal_mol))
    logarithm = math.log(hypothesis.carbon_acceleration)
    square = a * a
    compensation = 4 * hypothesis.reorganization_kcal_mol * hypothesis.rt_kcal_mol * logarithm
    if (a != 0 and square == 0) or (logarithm != 0 and compensation == 0):
        raise ValueError("quadratic operands underflow the representable numeric domain")
    discriminant = _result(math.fsum((square, -compensation)), "quadratic discriminant")
    if discriminant > 0:
        radius = math.sqrt(discriminant)
        # Use conjugates for either cancellation-prone endpoint, retaining
        # the inverted ray even when its endpoint is very near zero.
        lower_ray_end = compensation / (radius - a) if a < 0 else -a - radius
        lower_ray_end = _result(lower_ray_end, "inverted-branch endpoint")
        normal_start = -compensation / (radius + a) if a > 0 else -a + radius
        normal_start = _result(normal_start, "normal-branch endpoint")
        if compensation != 0 and (
            (a < 0 and lower_ray_end == 0) or (a > 0 and normal_start == 0)
        ):
            raise ValueError("quadratic endpoint underflows the representable numeric domain")
        intervals = (
            ClosedShiftIntervalV1(None, lower_ray_end),
            ClosedShiftIntervalV1(normal_start, None),
        )
        case = "POSITIVE_TWO_RAYS"
    else:
        normal_start = -a
        intervals = (ClosedShiftIntervalV1(None, None),)
        case = "ZERO_ALL_REAL" if discriminant == 0 else "NEGATIVE_ALL_REAL"
    normal = ClosedShiftIntervalV1(normal_start, None)
    nonpositive = ClosedShiftIntervalV1(normal_start, 0.0) if normal_start <= 0 else None
    return SpecificityShiftEnvelopeV1(
        discriminant, case, intervals, normal, nonpositive, _branch(a),
    )


def evaluate_branch_hypothesis(hypothesis: BranchHypothesisV1) -> BranchSensitivityV1:
    """Assess conditional log ratios without exponentiating rate ratios.

    Turnover uses serial productive times, distinct from channel specificity:
    total time ratio = 1-f+f/rC. A shared reactive occupancy is not an extra
    specificity multiplier, because it cancels between the two channels.
    """
    if type(hypothesis) is not BranchHypothesisV1:
        raise ValueError("a declared BranchHypothesisV1 is required")
    lam = hypothesis.reorganization_kcal_mol
    shift = hypothesis.dg_shift_kcal_mol
    a = math.fsum((lam, hypothesis.initial_dg_kcal_mol))
    final_dg = _result(math.fsum((hypothesis.initial_dg_kcal_mol, shift)), "final DG")
    final_a = math.fsum((lam, hypothesis.initial_dg_kcal_mol, shift))
    initial_barrier = _result(a * a / (4 * lam), "initial barrier")
    final_barrier = _result(final_a * final_a / (4 * lam), "final barrier")
    factor = math.fsum((2 * lam, 2 * hypothesis.initial_dg_kcal_mol, shift))
    delta_barrier = _result(shift * factor / (4 * lam), "barrier shift")
    if (
        (a != 0 and initial_barrier == 0) or (final_a != 0 and final_barrier == 0)
        or (shift != 0 and factor != 0 and delta_barrier == 0)
    ):
        raise ValueError("barrier arithmetic underflows the representable numeric domain")
    log_carbon = math.log(hypothesis.carbon_acceleration)
    log_oxygen = _result(-delta_barrier / hypothesis.rt_kcal_mol, "log oxygen ratio")
    log_specificity = _result(log_carbon - log_oxygen, "log specificity ratio")
    fraction = hypothesis.productive_step_time_fraction
    if fraction == 0 or log_carbon == 0:
        log_turnover = 0.0
    elif fraction == 1:
        log_turnover = log_carbon
    else:
        # Log-sum-exp keeps tiny rC and f representable without forming 1/rC.
        unchanged, accelerated = math.log1p(-fraction), math.log(fraction) - log_carbon
        largest, smallest = max(unchanged, accelerated), min(unchanged, accelerated)
        log_turnover = -(largest + math.log1p(math.exp(smallest - largest)))
    return BranchSensitivityV1(
        hypothesis, final_dg, initial_barrier, final_barrier, delta_barrier,
        log_carbon, log_oxygen, log_specificity, _result(log_turnover, "log turnover ratio"),
        _branch(a), _branch(final_a), specificity_preserving_shifts(hypothesis),
    )
