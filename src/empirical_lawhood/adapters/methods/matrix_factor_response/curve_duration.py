# SPDX-License-Identifier: MPL-2.0
"""Unselected TRAIN-only K medians and one-check headroom diagnostics.

These diagnostics cannot select a penalty or a primary endpoint. A median is
computed separately in each view, using the lower central integer when even.
The held-out labels never enter that calculation.
"""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .matched_response_prediction import matched_duration_error_count
from .response_scoring import MatrixSampledResponseDuration


def _counts(errors):
    if type(errors) is not tuple or len(errors) != 58:
        raise ValueError('median-K diagnostics require the original paired58 targets')
    return tuple(MatrixSampledResponseDuration(errors[start:start + 29], Decimal('.01'), True,
        tuple(value is not None for value in errors[start:start + 29])).count for start in (0, 29))


def _medians(targets):
    if not targets:
        return None, None
    return tuple(sorted(row[index + 2] for row in targets)[(len(targets) - 1) // 2] for index in (0, 1))


@dataclass(frozen=True, slots=True)
class CurveDurationDiagnostic(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/curve-duration-diagnostic'
    # Every target retains row ID, independent group ID, PRIMARY K and FINE K.
    fitting_targets: tuple[tuple[str, str, int, int], ...]
    held_out_targets: tuple[tuple[str, str, int, int], ...]
    median_counts: tuple[int | None, int | None]
    fitting_model_errors: tuple[tuple[str, int | None], ...]
    held_out_model_errors: tuple[tuple[str, int | None], ...]

    def __post_init__(self):
        for targets, errors in ((self.fitting_targets, self.fitting_model_errors),
                (self.held_out_targets, self.held_out_model_errors)):
            if (type(targets) is not tuple or type(errors) is not tuple
                    or tuple(row[0] for row in targets) != tuple(sorted({row[0] for row in targets}))
                    or tuple(row[0] for row in errors) != tuple(row[0] for row in targets)):
                raise ValueError('duration diagnostic changes its complete fitting or held-out row census')
            for row, group, primary, fine in targets:
                validate_stable_id(row)
                validate_stable_id(group)
                if any(type(k) is not int or not 0 <= k <= 29 for k in (primary, fine)):
                    raise ValueError('duration diagnostic invents a complete sampled K')
            for _, count in errors:
                if count is not None and (type(count) is not int or not 0 <= count <= 58):
                    raise ValueError('duration diagnostic changes the paired K-error denominator')
        if ({row[1] for row in self.fitting_targets} & {row[1] for row in self.held_out_targets}
                or type(self.median_counts) is not tuple or self.median_counts != _medians(self.fitting_targets)):
            raise ValueError('median K uses held-out groups or changes the fixed lower-central rule')

    def group_errors(self, *, held_out, median):
        targets = self.held_out_targets if held_out else self.fitting_targets
        model_errors = dict(self.held_out_model_errors if held_out else self.fitting_model_errors)
        rows = {}
        for row, group, primary, fine in targets:
            error = (abs(primary - self.median_counts[0]) + abs(fine - self.median_counts[1])
                if median and self.median_counts[0] is not None else None if median else model_errors[row])
            rows.setdefault(group, []).append(error)
        return tuple((group, None if any(value is None for value in values) else Fraction(sum(values), 58 * len(values)))
            for group, values in sorted(rows.items()))

    def headroom(self, assigned_groups, *, held_out, median):
        """A perfect K predictor can win by one check only on these groups."""
        if type(assigned_groups) is not tuple or assigned_groups != tuple(sorted(set(assigned_groups))):
            raise ValueError('K headroom requires the full assigned partition denominator')
        observed = dict(self.group_errors(held_out=held_out, median=median))
        if set(observed) - set(assigned_groups):
            raise ValueError('K headroom substitutes a group outside its original partition')
        losses = tuple(observed.get(group) for group in assigned_groups)
        return {'assigned_groups': len(assigned_groups), 'observed_groups': sum(value is not None for value in losses),
            'unknown_groups': sum(value is None for value in losses),
            'one_check_opportunities': sum(value is not None and value >= Fraction(1, 29) for value in losses),
            'paired_K_losses': tuple((group, None if value is None else (value.numerator, value.denominator))
                for group, value in zip(assigned_groups, losses, strict=True))}


def duration_diagnostic(fitting_rows, held_out_rows, *, fitting_points, held_out_points):
    def targets(rows):
        values = tuple((row.row_id, row.group_id, *_counts(row.errors)) for row in rows)
        if any(k is None for row in values for k in row[2:]):
            raise ValueError('duration diagnostics require the already selected common complete training groups')
        return values

    def errors(rows, predictions):
        return tuple((row.row_id, None if predictions.get(row.row_id) is None else
            matched_duration_error_count(predictions[row.row_id], row.errors)) for row in rows)

    fitting, held_out = targets(fitting_rows), targets(held_out_rows)
    return CurveDurationDiagnostic(fitting, held_out, _medians(fitting),
        errors(fitting_rows, fitting_points), errors(held_out_rows, held_out_points))


def duration_diagnostic_summary(model):
    """The original assigned folds remain denominators even after exclusions."""
    return {'median_rule': 'PER_VIEW_LOWER_CENTRAL_INTEGER_FITTING_PARTITION_ONLY',
        'selected_for_primary_or_tuning': False,
        'final_TRAIN_median_K': model.duration_diagnostic.median_counts,
        'final_training': tuple((kind, model.duration_diagnostic.headroom(model.training_unit_ids,
            held_out=False, median=median)) for kind, median in (('FITTED_MODEL', False), ('TRAIN_MEDIAN_K', True))),
        'cross_validation': tuple({'penalty': fit.diagnostics.penalty, 'held_out_fold': fit.held_out_fold,
            'fitting_median_K': fit.duration_diagnostic.median_counts,
            'partitions': tuple((partition, kind, fit.duration_diagnostic.headroom(
                tuple(group for group, fold in model.folds if (fold == fit.held_out_fold) == held_out),
                held_out=held_out, median=median)) for partition, held_out in (('FITTING', False), ('HELD_OUT', True))
                for kind, median in (('FITTED_MODEL', False), ('TRAIN_MEDIAN_K', True)))}
            for fit in model.cross_validation)}


def evaluation_median_K(model, assigned_groups, observed_rows, *, coordinate_count=1):
    """Apply the unchanged training medians to a full later root/group roster.

    Rows contain coordinate ID, group ID, paired58 targets and numerical
    usability. No later label can change the fitted medians or denominator.
    """
    from .matched_response_prediction import complete_group_loss_summary

    medians = model.duration_diagnostic.median_counts
    if (type(coordinate_count) is not int or coordinate_count not in (1, 9)
            or type(assigned_groups) is not tuple or assigned_groups != tuple(sorted(set(assigned_groups)))
            or type(observed_rows) is not tuple or len({row[0] for row in observed_rows}) != len(observed_rows)
            or any(row[1] not in assigned_groups or type(row[3]) is not bool for row in observed_rows)):
        raise ValueError('median-K evaluation changes its complete assigned group/coordinate roster')
    by_group = {group: [] for group in assigned_groups}
    for coordinate, group, targets, usable in observed_rows:
        validate_stable_id(coordinate)
        counts = _counts(targets)
        error = None if not usable or any(value is None for value in (*medians, *counts)) else sum(
            abs(left - right) for left, right in zip(medians, counts, strict=True))
        by_group[group].append(error)
    if any(len(rows) > coordinate_count for rows in by_group.values()):
        raise ValueError('median-K evaluation adds an unassigned coordinate')
    values = tuple(None if len(rows) != coordinate_count or any(value is None for value in rows)
        else Fraction(sum(rows), 58 * len(rows)) for rows in by_group.values())
    return {'median_rule': 'PER_VIEW_LOWER_CENTRAL_INTEGER_TRAIN_ONLY', 'median_K': medians,
        'assigned_groups': len(assigned_groups), 'unknown_groups': sum(value is None for value in values),
        'loss_summary': complete_group_loss_summary(values),
        'one_check_oracle_opportunities': sum(value is not None and value >= Fraction(1, 29) for value in values),
        'paired_K_losses': tuple((group, None if value is None else (value.numerator, value.denominator))
            for group, value in zip(assigned_groups, values, strict=True))}
