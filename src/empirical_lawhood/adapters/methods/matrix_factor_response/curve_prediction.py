# SPDX-License-Identifier: MPL-2.0
"""Prospective continuous-curve comparisons; the retained K claim is unchanged.

This owner consumes received predictions and targets only. The finite decimal
convention is precision 60, round-half-even. Comparisons and group averages use
exact fractions of those reported root losses, so the ambient Decimal context
cannot change an event or an equal-coordinate weight.
"""

from dataclasses import dataclass
from decimal import Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

from .matched_response_prediction import (
    MATCHED_METHODS, complete_group_loss_summary, matched_duration_error_count,
    paired_factor_targets, postprocess_log_points,
)
from .curve_contract import CURVE_LOSS_RULE, CURVE_MARGIN, CURVE_RELATION_METHODS


def reported_loss(value):
    """Precision-60 display only; primary comparisons keep the exact fraction."""
    if value is None:
        return None
    with localcontext() as context:
        context.prec = 60
        context.rounding = ROUND_HALF_EVEN
        return Decimal(value.numerator) / Decimal(value.denominator)


def curve_loss(log_points, observed_errors):
    """One equally weighted PRIMARY29/FINE29 root, normalized by log(1.01)."""
    points = postprocess_log_points(log_points)
    if type(observed_errors) is not tuple or len(observed_errors) != 58:
        raise ValueError('curve loss requires the complete PRIMARY29/FINE29 target order')
    for value in observed_errors:
        if value is not None:
            validate_decimal(value, field_name='curve target', minimum=Decimal(0))
    if any(value is None for value in (*points, *observed_errors)):
        return None
    try:
        with localcontext() as context:
            context.prec = 60
            context.rounding = ROUND_HALF_EVEN
            squared = tuple((point - (Decimal(1) + error).ln()) ** 2
                for point, error in zip(points, observed_errors, strict=True))
            return (sum(squared, Decimal(0)) / 58).sqrt() / Decimal('1.01').ln()
    except DecimalException:
        return None


def group_curve_loss(coordinate_losses):
    """An exact equal-coordinate mean of the declared root losses."""
    if type(coordinate_losses) is not tuple or len(coordinate_losses) not in (1, 9):
        raise ValueError('curve comparisons require one root or all nine group coordinates')
    for loss in coordinate_losses:
        if loss is not None:
            validate_decimal(loss, field_name='coordinate curve loss', minimum=Decimal(0))
    if any(loss is None for loss in coordinate_losses):
        return None
    return sum(map(Fraction, coordinate_losses), Fraction(0)) / len(coordinate_losses)


@dataclass(frozen=True, slots=True)
class MatchedCurveDecision(CanonicalRecord):
    """A separately identified curve-primary decision, retaining the K readout."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/matched-curve-decision'
    unit_id: str
    structural_method: str
    coordinate_count: int
    usable: bool
    success: bool
    # Per-coordinate Decimal losses preserve the averaging and comparison exactly.
    curve_losses: tuple[tuple[str, tuple[Decimal | None, ...]], ...]
    # Sum of paired K errors; the denominator is 58 times coordinate_count.
    duration_error_counts: tuple[tuple[str, int | None], ...]
    reasons: tuple[str, ...]
    coordinate_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        methods = MATCHED_METHODS if self.structural_method == 'S0' else CURVE_RELATION_METHODS
        if (self.structural_method not in ('S0', 'SR') or type(self.coordinate_count) is not int
                or self.coordinate_count not in (1, 9) or self.structural_method == 'S0' and self.coordinate_count != 1
                or type(self.usable) is not bool or type(self.success) is not bool
                or type(self.curve_losses) is not tuple or tuple(method for method, _ in self.curve_losses) != methods
                or type(self.duration_error_counts) is not tuple
                or tuple(method for method, _ in self.duration_error_counts) != methods
                or type(self.coordinate_ids) is not tuple or len(self.coordinate_ids) != self.coordinate_count
                or self.coordinate_ids != tuple(sorted(set(self.coordinate_ids)))
                or type(self.reasons) is not tuple or not self.reasons or self.reasons != tuple(sorted(set(self.reasons)))):
            raise ValueError('curve decision changes its complete method, coordinate or reason census')
        for _, losses in self.curve_losses:
            if type(losses) is not tuple or len(losses) != self.coordinate_count:
                raise ValueError('curve decision drops a coordinate from its equal-weight group')
            group_curve_loss(losses)
        for coordinate in self.coordinate_ids:
            validate_stable_id(coordinate)
        for _, count in self.duration_error_counts:
            if count is not None and (type(count) is not int or not 0 <= count <= 58 * self.coordinate_count):
                raise ValueError('secondary duration readout changes its original paired K denominator')
        if self.usable and any(self.loss(method) is None for method in (self.structural_method, self.baseline_method)):
            raise ValueError('curve decision invents a finite comparison for an unknown root or coordinate')
        if self.success != (self.usable and self.improvement >= CURVE_MARGIN):
            raise ValueError('curve decision changes the inclusive prospective 0.1 margin')

    @property
    def baseline_method(self):
        return 'B0' if self.structural_method == 'S0' else 'BR'

    @property
    def group_id(self):
        return self.unit_id

    @property
    def root_ids(self):
        return self.coordinate_ids

    def loss(self, method):
        return group_curve_loss(dict(self.curve_losses)[method])

    @property
    def improvement(self):
        return self.loss(self.baseline_method) - self.loss(self.structural_method) if self.usable else None

    @property
    def duration_improvement_count(self):
        values = dict(self.duration_error_counts)
        left, right = values[self.baseline_method], values[self.structural_method]
        return left - right if left is not None and right is not None else None

    @property
    def duration_success(self):
        count = self.duration_improvement_count
        return None if count is None else count >= 2 * self.coordinate_count


def curve_decision(unit_id, coordinate_points, coordinate_targets, reasons, *, structural_method='S0', coordinate_ids=None):
    """The caller authenticates whole roots/groups, numerical status and cutoff."""
    if (type(coordinate_points) is not tuple or type(coordinate_targets) is not tuple
            or len(coordinate_points) != len(coordinate_targets) or len(coordinate_points) not in (1, 9)):
        raise ValueError('curve decision requires its complete aligned coordinate census')
    methods = MATCHED_METHODS if structural_method == 'S0' else CURVE_RELATION_METHODS
    if any(tuple(sorted(menu)) != methods for menu in coordinate_points):
        raise ValueError('curve decision changes the originally sealed method menu')
    losses, counts = [], []
    targets_usable = not reasons
    for method in methods:
        losses.append((method, tuple(curve_loss(menu[method], targets) if targets_usable else None
            for menu, targets in zip(coordinate_points, coordinate_targets, strict=True))))
        coordinate_counts = tuple(matched_duration_error_count(menu[method], targets) if targets_usable else None
            for menu, targets in zip(coordinate_points, coordinate_targets, strict=True))
        counts.append((method, None if any(value is None for value in coordinate_counts) else sum(coordinate_counts)))
    baseline = 'B0' if structural_method == 'S0' else 'BR'
    reasons = set(reasons)
    primary = tuple(group_curve_loss(dict(losses)[method]) for method in (baseline, structural_method))
    if any(value is None for value in primary):
        reasons.add('MISSING_PAIRED_CURVE_PREDICTION_OR_TARGET')
    usable = not reasons
    success = usable and primary[0] - primary[1] >= CURVE_MARGIN
    if usable:
        reasons.add('PAIRED_CURVE_SUCCESS' if success else 'PAIRED_CURVE_MARGIN_NOT_MET')
    return MatchedCurveDecision(unit_id, structural_method, len(coordinate_points), usable, success,
        tuple(losses), tuple(counts), tuple(sorted(reasons)), (unit_id,) if coordinate_ids is None else coordinate_ids)


def curve_root_decision(unit_id, points, outcome, reasons):
    return curve_decision(unit_id, (points,), (paired_factor_targets(outcome),), reasons)


def curve_loss_summary(decisions):
    """All paired magnitudes; a win fraction is not a mean-improvement claim."""
    if not decisions or any(type(row) is not MatchedCurveDecision for row in decisions):
        raise TypeError('curve summary requires its separately identified full-roster decisions')
    methods = tuple(method for method, _ in decisions[0].curve_losses)
    if any(tuple(method for method, _ in row.curve_losses) != methods for row in decisions):
        raise ValueError('curve summary mixes model comparisons')
    return {'scope': 'OBSERVED_COMMON_GROUPS_DESCRIPTIVE_NOT_POPULATION_MEAN_INFERENCE',
        'loss_rule': CURVE_LOSS_RULE, 'assigned_groups': len(decisions), 'unknown_groups': sum(not row.usable for row in decisions),
        'paired_conventional_minus_structural': tuple((row.unit_id,
            None if row.improvement is None else (row.improvement.numerator, row.improvement.denominator)) for row in decisions),
        'improvement': complete_group_loss_summary(tuple(row.improvement for row in decisions)),
        'absolute_curve_loss': tuple((method, complete_group_loss_summary(tuple(
            row.loss(method) for row in decisions))) for method in methods),
        'secondary_paired_K_improvement': complete_group_loss_summary(tuple(None if row.duration_improvement_count is None else
            Fraction(row.duration_improvement_count, 58 * row.coordinate_count) for row in decisions)),
        'secondary_absolute_K_loss': tuple((method, complete_group_loss_summary(tuple(None if
            dict(row.duration_error_counts)[method] is None else Fraction(dict(row.duration_error_counts)[method],
                58 * row.coordinate_count) for row in decisions))) for method in methods),
        'secondary_one_check_wins': sum(row.duration_success is True for row in decisions),
        'secondary_one_check_unknown': sum(row.duration_success is None for row in decisions)}
