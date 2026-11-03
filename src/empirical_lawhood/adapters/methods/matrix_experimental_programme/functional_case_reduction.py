# SPDX-License-Identifier: MPL-2.0
"""Original prepared endpoint arithmetic for separately guarded exact subjects.

Caller-owned guards authenticate scientific source, selection and custody. This
private numerical owner supplies no source eligibility or applicability warrant.
"""

from decimal import Decimal, localcontext
from fractions import Fraction

from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import model_predictors
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import paired_adequacy, validate_dense_score_units
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.kernel.provenance import ObjectIdentity

from .science import MatrixFunctionalCaseResult, _validate_original_score


def _prepared_score_views(criterion, source, score, *, protocol, panels):
    """Validate the original complete paired assay before either reduction."""
    _validate_original_score(score)
    predictors = model_predictors(protocol.mechanical_model)
    expected_cells = {(view, panel.panel_id, action.action_id, predictor, horizon) for view in ("PRIMARY", "FINE")
        for panel in panels for action in protocol.actions for predictor in predictors for horizon in protocol.horizon_steps}
    if {row.key for row in score.cells} != expected_cells or score.dense is None and any(value is not None and len(value) != protocol.receiver_count
            for row in score.cells for value in (row.actual_odd_responses, row.signed_errors, row.absolute_errors, row.relative_errors)):
        raise ValueError("prepared functional readout thins the actual full48 receiver/action/panel/horizon denominator")
    if score.dense is not None:
        validate_dense_score_units(protocol, score)
    if score.controls:
        branches = branch_census(protocol, panels)
        expected_controls = tuple("control.prepared." + source.source_id + "." + branch for branch, *_ in branches)
        if (tuple(row.control_id for row in score.controls) != expected_controls
                or any(row.denominator_steps != (1 if view == "PRIMARY" else 2) * protocol.horizon_steps[-1]
                    or row.denominator_real_coordinates != 192 or row.tolerance != protocol.native_reference_tolerance
                    for row, (_, view, *_rest) in zip(score.controls, branches, strict=True))):
            raise ValueError("prepared functional readout thins its original full48 paired128/256-step native branch controls")
    rows = tuple(row for row in score.cells if row.predictor == criterion.predictor and row.horizon_tick <= criterion.horizon_tick)
    views = {view: tuple(sorted((row for row in rows if row.view == view), key=lambda row: row.key[1:])) for view in ("PRIMARY", "FINE")}
    expected = 8 * (protocol.horizon_steps.index(criterion.horizon_tick) + 1)
    if (any(len(value) != expected for value in views.values()) or
            tuple(row.key[1:] for row in views["PRIMARY"]) != tuple(row.key[1:] for row in views["FINE"])):
        raise ValueError("prepared functional result drops a paired view, panel, action or preceding horizon")
    return rows, views


def sampled_prepared_adequacy(criterion, score, rows, views):
    """Keep a known sampled failure even when another required cell is unknown."""
    discrepancy = any(left.normalized_error is not None and right.normalized_error is not None
        and abs(Fraction(left.normalized_error) - Fraction(right.normalized_error)) > Fraction(criterion.paired_view_discrepancy_maximum)
        for left, right in zip(views["PRIMARY"], views["FINE"], strict=True))
    usable = score.numerical_pass and not discrepancy
    durations = tuple(curve.duration(numerical_usable=usable, tolerance=criterion.normalized_error_maximum)
        for curve in score.dense.curves if curve.predictor == criterion.predictor)
    adequacy = paired_adequacy(durations, criterion.horizon_tick)
    finite = usable and all(row.normalized_error is not None for row in rows)
    return adequacy, max(row.normalized_error for row in rows) if finite else None, finite, discrepancy


def native_functional_case(criterion, case, source, score, *, protocol, panels):
    """A native assay diagnostic independent of point availability or admission.

    The caller authenticates the original source and received publication. This
    separate result does not replace a historical point-conditioned reduction.
    """
    from .prepared_response_science import MatrixPreparedResponseReadout

    reasons = ["NATIVE_FUNCTIONAL_DIAGNOSTIC_ONLY", "NO_POINT_COMPARISON_OR_ADMISSION_CLAIM"]
    if score is None:
        return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "MISSING",
            None, None, None, False, False, None, False, case.preparation_effort,
            tuple(sorted((*reasons, "MISSING_ORIGINAL_NATIVE_READOUT"))),
            response_adequacy_meaning="SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK" if criterion.is_matched else "NOT_SELECTED")
    if type(score) is not MatrixPreparedResponseReadout:
        raise TypeError("native functional diagnostic requires the actual prepared readout")
    score.__post_init__()
    if (score.source != source.identity
            or score.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or score.panels != tuple(panel.identity for panel in panels)):
        raise ValueError("native functional diagnostic substitutes its original source, protocol or panels")
    rows, views = _prepared_score_views(criterion, source, score, protocol=protocol, panels=panels)
    if criterion.is_matched:
        if score.dense is None:
            raise ValueError("matched prepared adequacy requires the original dense native readout")
        adequacy, actual, finite, discrepancy = sampled_prepared_adequacy(criterion, score, rows, views)
        if not finite:
            reasons.append("PREPARED_READOUT_" + score.disposition)
        if discrepancy:
            reasons.append("PAIRED_VIEW_DISCREPANCY")
        return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id,
            "FINITE" if finite else "NONUSE" if score.disposition == "NO_ORIGIN" else "UNEVALUABLE",
            actual, None, None, adequacy is True, False, None, False, case.preparation_effort, tuple(sorted(reasons)),
            response_adequacy=adequacy, response_adequacy_meaning="SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK")
    discrepancy = any(left.normalized_error is not None and right.normalized_error is not None
        and abs(Fraction(left.normalized_error) - Fraction(right.normalized_error)) > Fraction(criterion.paired_view_discrepancy_maximum)
        for left, right in zip(views["PRIMARY"], views["FINE"], strict=True))
    finite = (score.numerical_pass and score.disposition == "FINITE" and not discrepancy
        and all(row.normalized_error is not None for row in rows))
    if not finite:
        reasons.append("PREPARED_READOUT_" + score.disposition)
    if discrepancy:
        reasons.append("PAIRED_VIEW_DISCREPANCY")
    actual = max(row.normalized_error for row in rows) if finite else None
    return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id,
        "FINITE" if finite else "NONUSE" if score.disposition == "NO_ORIGIN" else "UNEVALUABLE",
        actual, None, None, finite and actual <= criterion.normalized_error_maximum,
        False, None, False, case.preparation_effort, tuple(sorted(reasons)))


def _prepared_endpoint(criterion, package, case, source, observation, *, protocol, panels):
    point, score = observation.point, observation.readout
    rows, views = _prepared_score_views(criterion, source, score, protocol=protocol, panels=panels)
    reasons = ["CROSS_PREPARATION_APPLICABILITY_NOT_ASSESSED", "UNBOUNDED_PREPARED_POINT_FORECAST"]
    index = PREDICTORS.index(criterion.predictor) * 3 + (16, 64, 128).index(criterion.horizon_tick)
    predicted, upper = point.log_error_points[index], point.log_error_uppers[index]
    unavailable = (not score.numerical_pass or score.disposition != "FINITE" or point.feature.disposition != "AVAILABLE" or predicted is None
        or any(row.normalized_error is None for row in rows))
    discrepancy = any(left.normalized_error is not None and right.normalized_error is not None
        and abs(Fraction(left.normalized_error) - Fraction(right.normalized_error)) > Fraction(criterion.paired_view_discrepancy_maximum)
        for left, right in zip(views["PRIMARY"], views["FINE"], strict=True))
    if unavailable or discrepancy:
        reasons.extend(("PREPARED_READOUT_" + score.disposition, "PREPARED_FEATURE_" + point.feature.disposition))
        if discrepancy:
            reasons.append("PAIRED_VIEW_DISCREPANCY")
        return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "NONUSE" if score.disposition == "NO_ORIGIN" else "UNEVALUABLE",
            None, predicted, upper, False, False, None, False, case.preparation_effort, tuple(sorted(reasons)))
    actual = max(row.normalized_error for row in rows)
    with localcontext() as context:
        context.prec = 80
        actual_log = (Decimal(1) + actual).ln()
        absolute_error = abs(actual_log - predicted)
    comparator_error = None
    comparator = observation.comparator
    if comparator is None:
        reasons.append("MISSING_ORIGINAL_SAME_INFORMATION_COMPARATOR")
    else:
        if (comparator.package != package.identity or comparator.model != package.component("comparator") or comparator.criterion != point.criterion
                or comparator.feature.source != point.feature.source or comparator.feature.prefix != point.feature.prefix
                or comparator.feature.values != point.feature.values or comparator.feature.cutoff != point.feature.cutoff
                or comparator.feature.family_id != point.feature.family_id or comparator.feature.frame_sha256 != point.feature.frame_sha256):
            raise ValueError("prepared functional result changes the original frozen same-information comparator")
        with localcontext() as context:
            context.prec = 80
            comparator_error = None if comparator.log_error_points[index] is None else abs(actual_log - comparator.log_error_points[index])
    return MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "FINITE", actual, predicted, upper,
        actual <= criterion.normalized_error_maximum, False, None, False, case.preparation_effort, tuple(sorted(reasons)),
        absolute_error, comparator_error, "UNESTABLISHED")
