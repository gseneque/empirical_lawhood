# SPDX-License-Identifier: MPL-2.0
"""Paired30 revision point errors and separate complete functional outcomes.

Raw fitted outputs remain unaltered. An unsupported point model leaves the
independent native functional assay interpretable, without forecasting error
or uncertainty claims. No scientific sampling or applicability is supplied.
"""
from collections.abc import Mapping
from .preparation_records import is_baseline_recipe

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4RevisionPoint, POINT_ONLY, TRANSPORT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import RELATION_METHODS, relation_point_values, relation_target_reasons
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import (
    MatchedCoverage, MatchedForecastPolicy, matched_coverage_values, matched_duration_error_count,
    matched_forecast_policy, postprocess_log_points,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import curve_decision
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id, validate_decimal
from .prepared_prefix import identity
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_response_science import MatrixPreparedResponseReadout
from .science import MatrixFunctionalCaseResult, MatrixFunctionalAssessment, MatrixPreparationNomination, _validate_original_score
from .functional_outcome_reduction import _nominate_functional_cases, _confirmation_comparisons, _transfer_comparisons
from .selected_revision_programme import MatrixRevisionPreparedProgramme


@dataclass(frozen=True, slots=True)
class MatrixRevisionCaseAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-case-assessment"
    VERSION: ClassVar[str] = "2.0.0"
    case_id: str
    point: ObjectIdentity | None
    mechanical: ObjectIdentity | None
    readout: ObjectIdentity | None
    actual_log_targets: tuple[Decimal | None, ...]
    revision_log_predictions: tuple[Decimal | None, ...]
    baseline_log_predictions: tuple[Decimal | None, ...]
    absolute_revision_errors: tuple[Decimal | None, ...]
    absolute_baseline_errors: tuple[Decimal | None, ...]
    functional: MatrixFunctionalCaseResult
    uncertainty_status: str = POINT_ONLY
    relation_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...] = ()
    factor_errors: tuple[Decimal | None, ...] = ()
    prediction_targets_usable: bool | None = None
    policies: tuple[MatchedForecastPolicy, ...] = ()
    coverage: tuple[MatchedCoverage, ...] = ()
    reference_points: tuple[tuple[str, tuple[Decimal | None, ...]], ...] = ()
    reference_duration_error_counts: tuple[tuple[str, int | None], ...] = ()

    def __post_init__(self):
        validate_stable_id(self.case_id)
        if (type(self.functional) is not MatrixFunctionalCaseResult or self.functional.case_id != self.case_id
                or self.uncertainty_status not in (POINT_ONLY, TRANSPORT)):
            raise ValueError("revision case substitutes actual complete functional outcome or invents uncertainty")
        self.functional.__post_init__()
        expected = ((self.point, SelectedE4RevisionPoint), (self.mechanical, MatrixPreparedMechanicalForecast),
            (self.readout, MatrixPreparedResponseReadout))
        partial = self.uncertainty_status == TRANSPORT and self.point is not None and self.mechanical is not None and self.readout is None
        if not partial and any(value is None for value, _ in expected) != all(value is None for value, _ in expected):
            raise ValueError("revision case invents a partial original observation")
        if partial and (self.functional.disposition != 'MISSING' or any(value is not None for value in self.actual_log_targets)):
            raise ValueError('partial matched forecast cannot invent a future observation')
        for value, kind in expected:
            if value is not None and (type(value) is not ObjectIdentity or
                    (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION)):
                raise ValueError("revision case substitutes an original observation identity")
        if self.point is None and (self.functional.disposition != "MISSING" or any(
                value is not None for values in (self.actual_log_targets, self.revision_log_predictions,
                    self.baseline_log_predictions, self.absolute_revision_errors, self.absolute_baseline_errors) for value in values)):
            raise ValueError("revision missing case invents a finite point or assay")
        for values in (self.actual_log_targets, self.revision_log_predictions, self.baseline_log_predictions,
                self.absolute_revision_errors, self.absolute_baseline_errors):
            if type(values) is not tuple or len(values) != (58 if self.uncertainty_status == TRANSPORT else 30):
                raise ValueError("revision case drops its complete original paired endpoints")
            for value in values:
                if value is not None:
                    validate_decimal(value, field_name="revision paired endpoint")
        for actual, revision, baseline, revision_error, baseline_error in zip(self.actual_log_targets,
                self.revision_log_predictions, self.baseline_log_predictions, self.absolute_revision_errors, self.absolute_baseline_errors, strict=True):
            for prediction, error in ((revision, revision_error), (baseline, baseline_error)):
                with localcontext() as context:
                    context.prec = 80
                    expected = None if actual is None or prediction is None else abs(actual - prediction)
                if error != expected:
                    raise ValueError("revision case alters raw paired point-error arithmetic")
        if self.uncertainty_status == TRANSPORT:
            if (tuple(method for method, _ in self.relation_points) != RELATION_METHODS
                    or type(self.factor_errors) is not tuple or len(self.factor_errors) != 58
                    or type(self.prediction_targets_usable) is not bool
                    or tuple(policy.method_key for policy in self.policies) != ("BR", "SR")
                    or tuple(row.method_key for row in self.coverage) != ("BR", "SR")
                    or tuple(method for method, _ in self.reference_points) != ('B0', 'S0')):
                raise ValueError("matched prepared assessment loses all accounts, paired58 targets or original policies")
            for _, points in (*self.relation_points, *self.reference_points):
                if postprocess_log_points(points) != points:
                    raise ValueError("matched prepared assessment changes the pre-future processed predictions")
            for value in self.factor_errors:
                if value is not None:
                    validate_decimal(value, field_name="matched actual FACTOR target", minimum=Decimal(0))
            with localcontext() as context:
                context.prec = 60
                expected = tuple(None if value is None else (Decimal(1) + value).ln() for value in self.factor_errors)
            points = dict(self.relation_points)
            counts = tuple((method, matched_duration_error_count(values, self.factor_errors)
                if self.prediction_targets_usable else None) for method, values in self.relation_points)
            coverage = tuple(matched_coverage_values(self.functional.unit_id, policy.method_key,
                points[policy.method_key], policy, self.factor_errors, self.prediction_targets_usable) for policy in self.policies)
            reference_counts = tuple((method, matched_duration_error_count(values, self.factor_errors)
                if self.prediction_targets_usable else None) for method, values in self.reference_points)
            if (expected != self.actual_log_targets or self.functional.duration_error_counts != counts or self.coverage != coverage
                    or (self.revision_log_predictions, self.baseline_log_predictions) != (points['SR'], points['BR'])
                    or self.reference_duration_error_counts != reference_counts):
                raise ValueError("matched prepared assessment changes exact duration losses, targets or transported coverage")
        elif any((self.relation_points, self.factor_errors, self.prediction_targets_usable is not None, self.policies,
                self.coverage, self.reference_points, self.reference_duration_error_counts)):
            raise ValueError("closed point-only assessment cannot claim matched inference")


@dataclass(frozen=True, slots=True)
class MatrixRevisionManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-programme-manifest"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    programme: ObjectIdentity
    rows: tuple[tuple[str, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.programme.object_schema != MatrixRevisionPreparedProgramme.SCHEMA or not self.rows
                or tuple(row[0] for row in self.rows) != tuple(sorted({row[0] for row in self.rows}))):
            raise ValueError("revision manifest drops an assigned case")
        for _, point, mechanical, readout in self.rows:
            if point is None:
                if (mechanical, readout) != (None, None):
                    raise ValueError("revision manifest invents a partially observed case")
            elif (point.object_schema != SelectedE4RevisionPoint.SCHEMA or mechanical is None
                    or mechanical.object_schema != MatrixPreparedMechanicalForecast.SCHEMA
                    or readout is not None and readout.object_schema != MatrixPreparedResponseReadout.SCHEMA):
                raise ValueError("revision manifest substitutes original numerical product types")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MatrixRevisionProgrammeAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/revision-programme-assessment"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    programme: ObjectIdentity
    manifest: ObjectIdentity
    cases: tuple[MatrixRevisionCaseAssessment, ...]
    functional: MatrixPreparationNomination | MatrixFunctionalAssessment
    uncertainty_status: str = POINT_ONLY

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.programme.object_schema != MatrixRevisionPreparedProgramme.SCHEMA
                or self.manifest.object_schema != MatrixRevisionManifest.SCHEMA
                or type(self.functional) not in (MatrixPreparationNomination, MatrixFunctionalAssessment)
                or type(self.cases) is not tuple or not self.cases
                or tuple(row.case_id for row in self.cases) != tuple(sorted({row.case_id for row in self.cases}))
                or self.uncertainty_status not in (POINT_ONLY, TRANSPORT)
                or any(row.uncertainty_status != self.uncertainty_status for row in self.cases)):
            raise ValueError("revision result changes original complete cases or grants downstream uncertainty")
        for row in (*self.cases, self.functional):
            row.__post_init__()
        if (tuple(row.functional for row in self.cases) != self.functional.cases
                or self.functional.specification != self.programme or self.functional.evidence != self.manifest):
            raise ValueError("revision result drops original functional adverse/nonuse outcomes")


def _case(programme, case, source, observation):
    matched = programme.criterion.is_matched
    none = (None,) * (58 if matched else 30)
    reasons = {"REVISION_DOWNSTREAM_APPLICABILITY_UNESTABLISHED", POINT_ONLY}
    if observation is None:
        row = MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "MISSING", None, None, None,
            False, False, None, False, case.preparation_effort, ("MISSING_ORIGINAL_FORECAST_OR_SCORE",),
            response_adequacy_meaning="SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK" if matched else "NOT_SELECTED",
            duration_error_counts=tuple((method, None) for method in RELATION_METHODS) if matched else ())
        if matched:
            policies = tuple(matched_forecast_policy(method, none, None, calibrated=True) for method in ('BR', 'SR'))
            coverage = tuple(matched_coverage_values(case.unit_id, method, none, policy, none, False)
                for method, policy in zip(('BR', 'SR'), policies, strict=True))
            return MatrixRevisionCaseAssessment(case.case_id, None, None, None, none, none, none, none, none, row,
                TRANSPORT, tuple((method, none) for method in RELATION_METHODS), none, False, policies, coverage,
                tuple((method, none) for method in ('B0', 'S0')), tuple((method, None) for method in ('B0', 'S0')))
        return MatrixRevisionCaseAssessment(case.case_id, None, None, None, none, none, none, none, none, row)
    point, mechanical, readout = observation
    protocol = programme.protocol(source)
    package = programme.selected_package
    if (type(point) is not SelectedE4RevisionPoint or type(mechanical) is not MatrixPreparedMechanicalForecast
            or type(readout) is not MatrixPreparedResponseReadout and not (matched and readout is None) or point.source != source.identity
            or point.recipe != source.recipe.identity or point.models != package.models.identity
            or point.coordinate != ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate)
            or point.cutoff.clock_id != source.coordinate.clock_id
            or point.cutoff.coordinate != source.coordinate.physical_time(source.total_ticks)
            or point.nomination != package.nomination or point.original_calibration != package.original_calibration
            or mechanical.source != source.identity or mechanical.causal != point.causal_prefix
            or mechanical.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or readout is not None and (readout.source != source.identity or readout.original_protocol != mechanical.original_protocol
                or readout.preparation != mechanical.arrays.preparation
                or readout.panels != tuple(row.identity for row in dict(programme.panels)[case.unit_id]))):
        raise ValueError("revision result substitutes actual selected pre-future point/physical/source/readout products")
    for record in (point, mechanical, readout):
        if record is not None:
            record.__post_init__()
    if matched:
        return _matched_case(programme, case, source, protocol, point, mechanical, readout)
    # The worker replays the point against its exact causal record. Here the
    # original coefficient/coordinate/nonuse result is independently repeated.
    predicted = package.models.predict(source.coordinate) if point.disposition in ("PREDICTED", "UNSUPPORTED_DECLARED_GRID") else (point.disposition, none, none)
    if (point.disposition, point.revision_predictions, point.baseline_predictions) != predicted:
        raise ValueError("revision result alters actual raw paired30 fitted model output")
    if readout.forecast is not None and readout.forecast != mechanical.arrays.identity:
        raise ValueError("revision readout substitutes its independently checked physical prediction")
    _validate_original_score(readout)
    panels = dict(programme.panels)[case.unit_id]
    expected_cells = {(view, panel.panel_id, action.action_id, predictor, horizon)
        for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions
        for predictor in PREDICTORS for horizon in protocol.horizon_steps}
    if ({row.key for row in readout.cells} != expected_cells or any(value is not None and len(value) != protocol.receiver_count
            for row in readout.cells for value in (row.actual_odd_responses, row.signed_errors, row.absolute_errors, row.relative_errors))):
        raise ValueError("revision functional readout thins actual full receiver/action/panel/horizon denominator")
    if readout.controls:
        branches = branch_census(protocol, panels)
        expected_controls = tuple("control.prepared." + source.source_id + "." + branch for branch, *_ in branches)
        if (tuple(row.control_id for row in readout.controls) != expected_controls
                or any(row.denominator_steps != (1 if view == "PRIMARY" else 2) * protocol.horizon_steps[-1]
                    or row.denominator_real_coordinates != 192 or row.tolerance != protocol.native_reference_tolerance
                    for row, (_, view, *_rest) in zip(readout.controls, branches, strict=True))):
            raise ValueError("revision functional readout thins original paired native branch controls")
    target = package.models.target
    values = []
    for view in target.numerical_views:
        for predictor in PREDICTORS:
            for horizon in target.horizon_ticks:
                rows = tuple(row for row in readout.cells if row.view == view and row.predictor == predictor and row.horizon_tick <= horizon)
                if not rows or not readout.numerical_pass or readout.disposition not in ("FINITE", "PARTIAL") or any(row.normalized_error is None for row in rows):
                    values.append(None)
                else:
                    with localcontext() as context:
                        context.prec = 50
                        values.append((Decimal(1) + max(row.normalized_error for row in rows)).ln())
    actual = tuple(values)
    errors = []
    for predictions in (point.revision_predictions, point.baseline_predictions):
        with localcontext() as context:
            context.prec = 80
            errors.append(tuple(None if value is None or prediction is None else abs(value - prediction)
                for value, prediction in zip(actual, predictions, strict=True)))
    criterion = programme.criterion
    rows = tuple(row for row in readout.cells if row.predictor == criterion.predictor and row.horizon_tick <= criterion.horizon_tick)
    primary = tuple(sorted((row for row in rows if row.view == "PRIMARY"), key=lambda row: row.key[1:]))
    fine = tuple(sorted((row for row in rows if row.view == "FINE"), key=lambda row: row.key[1:]))
    discrepancy = any(left.normalized_error is not None and right.normalized_error is not None
        and abs(Fraction(left.normalized_error) - Fraction(right.normalized_error)) > Fraction(criterion.paired_view_discrepancy_maximum)
        for left, right in zip(primary, fine, strict=True))
    finite = readout.numerical_pass and readout.disposition == "FINITE" and not discrepancy and all(row.normalized_error is not None for row in rows)
    if point.disposition != "PREDICTED":
        reasons.add("REVISION_POINT_" + point.disposition)
    if discrepancy:
        reasons.add("PAIRED_VIEW_DISCREPANCY")
    index = PREDICTORS.index(criterion.predictor) * len(target.horizon_ticks) + target.horizon_ticks.index(criterion.horizon_tick)
    paired_indices = (index, index + 15)
    actual_error = max(row.normalized_error for row in rows) if finite else None
    selected_error = None if any(errors[0][i] is None for i in paired_indices) else max(errors[0][i] for i in paired_indices)
    baseline_error = None if any(errors[1][i] is None for i in paired_indices) else max(errors[1][i] for i in paired_indices)
    if not finite:
        reasons.add("PREPARED_READOUT_" + readout.disposition)
    functional = MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id,
        "FINITE" if finite else "NONUSE" if readout.disposition == "NO_ORIGIN" else "UNEVALUABLE",
        actual_error, point.revision_predictions[index], None,
        finite and actual_error <= criterion.normalized_error_maximum, False, None, False, case.preparation_effort,
        tuple(sorted(reasons)), selected_error, baseline_error, "UNESTABLISHED")
    return MatrixRevisionCaseAssessment(case.case_id, identity(point), identity(mechanical), identity(readout), actual,
        point.revision_predictions, point.baseline_predictions, errors[0], errors[1], functional)


def _matched_case(programme, case, source, protocol, point, mechanical, readout):
    """Frozen relation replay and actual response adequacy are separate outcomes."""
    from .functional_case_reduction import _prepared_score_views, sampled_prepared_adequacy

    package = programme.selected_package
    if (point.feature is None or point.feature.mechanical != identity(mechanical)
            or point.feature.protocol != mechanical.original_protocol or readout is not None and readout.dense is None
            or point.uncertainty_status != TRANSPORT or point.frozen_calibration != package.frozen_calibration.identity
            or readout is not None and readout.forecast is not None and readout.forecast != mechanical.arrays.identity):
        raise ValueError("matched prepared assessment changes its actual causal/mechanical handoff or frozen CAL")
    points = relation_point_values(package.models.relation_fit, point.feature.values, point.feature.disposition,
        factor_values=(source.coordinate.primary_view.bath_temperature, source.coordinate.primary_view.friction_gamma,
            source.coordinate.member.cross_coupling_gamma), family_id=source.coordinate.family_id)
    radii = (('BR', package.frozen_calibration.baseline_radius), ('SR', package.frozen_calibration.revision_radius))
    policies = tuple(matched_forecast_policy(method, dict(points)[method], radius, calibrated=True) for method, radius in radii)
    reference = dict(package.reference_package.predict(values=point.feature.values, disposition=point.feature.disposition))
    reference_points = tuple((method, reference[method]) for method in ('B0', 'S0'))
    if (point.relation_points != points or point.model_radii != radii or point.policies != policies
            or point.reference_package != package.reference_package.identity or point.reference_points != reference_points):
        raise ValueError("matched prepared assessment substitutes fitted predictions or unchanged E4 model-specific bounds")
    criterion = programme.criterion
    if readout is None:
        adequacy, actual_error, finite, discrepancy = None, None, False, False
        factor_errors = actual = (None,) * 58
    else:
        rows, views = _prepared_score_views(criterion, source, readout, protocol=protocol, panels=dict(programme.panels)[case.unit_id])
        adequacy, actual_error, finite, discrepancy = sampled_prepared_adequacy(criterion, readout, rows, views)
        factor_errors = tuple(value for curve in readout.dense.curves if curve.predictor == 'FACTOR'
            for value in curve.cumulative_sampled_errors(numerical_usable=readout.numerical_pass))
        actual = readout.dense.factor_log_targets
    target_reasons = relation_target_reasons(factor_errors, tolerance=criterion.paired_view_discrepancy_maximum)
    usable = readout is not None and readout.numerical_pass and not target_reasons
    counts = tuple((method, matched_duration_error_count(values, factor_errors) if usable else None) for method, values in points)
    with localcontext() as context:
        context.prec = 80
        errors = tuple(tuple(None if value is None or prediction is None else abs(value - prediction)
            for value, prediction in zip(actual, values, strict=True)) for values in (point.revision_predictions, point.baseline_predictions))
    coverage = tuple(matched_coverage_values(case.unit_id, policy.method_key, dict(points)[policy.method_key], policy, factor_errors, usable)
        for policy in policies)
    index = DENSE_RESPONSE_HORIZONS.index(criterion.horizon_tick)
    sr = next(policy for policy in policies if policy.method_key == 'SR')
    admitted = sr.admissions[index] is True
    def paired_max(values):
        return None if any(values[i] is None for i in (index, index + 29)) else max(values[index], values[index + 29])
    with localcontext() as context:
        context.prec = 60
        upper = paired_max(sr.upper_errors)
        upper = None if upper is None else (Decimal(1) + upper).ln()
    reasons = {TRANSPORT, 'SAMPLED_RESPONSE_ADEQUACY_NOT_EXTERNAL_TASK', *target_reasons}
    if not finite:
        reasons.add('PREPARED_READOUT_' + ('MISSING' if readout is None else readout.disposition))
    if discrepancy:
        reasons.add('PAIRED_VIEW_DISCREPANCY')
    if point.disposition != 'PREDICTED':
        reasons.add('REVISION_POINT_' + point.disposition)
    functional = MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id,
        'FINITE' if finite else 'MISSING' if readout is None else 'NONUSE' if readout.disposition == 'NO_ORIGIN' else 'UNEVALUABLE', actual_error,
        paired_max(point.revision_predictions), upper, adequacy is True, admitted,
        next(row.covered for row in coverage if row.method_key == 'SR'), admitted and adequacy is False,
        case.preparation_effort, tuple(sorted(reasons)), paired_max(errors[0]), paired_max(errors[1]), 'UNESTABLISHED',
        adequacy, 'SAMPLED_FACTOR_RESPONSE_ADEQUACY_THROUGH64_NOT_EXTERNAL_TASK', counts)
    return MatrixRevisionCaseAssessment(case.case_id, identity(point), identity(mechanical), None if readout is None else identity(readout), actual,
        point.revision_predictions, point.baseline_predictions, *errors, functional, TRANSPORT,
        points, factor_errors, usable, policies, coverage, reference_points,
        tuple((method, matched_duration_error_count(values, factor_errors) if usable else None) for method, values in reference_points))


def revision_transfer_regimes(programme, original_allocation):
    """Join semantic roles from original allocation; regime labels carry no role.

    Entry authenticates this unchanged original record. Final workers receive
    its exact bytes from that successful entry, never from a caller selection.
    """
    if (type(programme) is not MatrixRevisionPreparedProgramme or programme.phase != "E6_TRANSFER"
            or type(original_allocation) is not UnitAllocation):
        raise TypeError("revision transfer requires its actual original semantic allocation")
    original_allocation.__post_init__()
    by_regime = {}
    for _, source in programme.source_arms():
        by_regime.setdefault(source.root.root.regime_id, set()).add(source.root.root.independent_group_id)
    regimes = []
    for role in ("transfer_nearby", "transfer_shifted"):
        groups = original_allocation.unit_ids(role)
        names = tuple(name for name, actual in by_regime.items() if actual == set(groups))
        if len(groups) != programme.expected_groups or len(names) != 1:
            raise ValueError("revision transfer substitutes an original complete nearby/shifted role partition")
        regimes.append((names[0], groups))
    if (len(by_regime) != 2 or regimes[0][0] == regimes[1][0]
            or set(regimes[0][1]).intersection(regimes[1][1])):
        raise ValueError("revision transfer overlaps or drops its original separate semantic regimes")
    return tuple(regimes)


def assess_revision_programme(programme, observations, *, result_id, original_allocation=None):
    if type(programme) is not MatrixRevisionPreparedProgramme or not isinstance(observations, Mapping):
        raise TypeError("revision assessment requires its actual complete programme and received observations")
    programme.__post_init__()
    regimes = revision_transfer_regimes(programme, original_allocation) if programme.phase == "E6_TRANSFER" else None
    roster = programme.roster
    if set(observations) - {case.case_id for case in roster.cases}:
        raise ValueError("revision assessment adds an unassigned case")
    sources = {"case." + source.source_id: source for _, source in programme.source_arms()}
    cases = tuple(_case(programme, case, sources[case.case_id], observations.get(case.case_id)) for case in roster.cases)
    manifest = MatrixRevisionManifest(result_id + ".received", programme.identity,
        tuple((row.case_id, row.point, row.mechanical, row.readout) for row in cases))
    functional_cases = tuple(row.functional for row in cases)
    groups = tuple(sorted({case.unit_id for case in roster.cases}))
    if programme.phase == "E5_OPPORTUNITY":
        functional = _nominate_functional_cases(result_id=result_id + ".functional", specification_identity=programme.identity,
            package_identity=programme.selected_package.identity, roster_identity=roster.identity, evidence_identity=manifest.identity,
            group_ids=groups, arm_ids=tuple(arm for arm, _ in programme.arms), hold_arm_id=programme.hold_arm_id,
            criterion=programme.criterion, minimum_recoverable_groups=programme.minimum_recoverable_groups,
            tie_policy=programme.tie_policy, recipes=tuple((arm, recipe.identity) for arm, recipe in programme.arms), cases=functional_cases)
    else:
        if programme.phase == "E5_CONFIRMATION":
            prepared = next(arm for arm, recipe in programme.arms if not is_baseline_recipe(recipe))
            comparisons = _confirmation_comparisons(programme.criterion, groups, prepared, programme.hold_arm_id, functional_cases)
        else:
            curve = programme.criterion.is_matched and programme.selected_package.models.relation_fit.selection.is_curve_primary
            curve_decisions = tuple(curve_decision(row.functional.unit_id, (dict(row.relation_points),), (row.factor_errors,),
                () if row.prediction_targets_usable else ('UNUSABLE_PAIRED_TARGET',), structural_method='SR',
                coordinate_ids=(row.case_id,)) for row in cases) if curve else None
            comparisons = _transfer_comparisons(programme.criterion, regimes, programme.transfer_domain_claims,
                programme.hold_arm_id, functional_cases, curve_decisions=curve_decisions)
        used = {row.comparison_id for row in comparisons}
        functional = MatrixFunctionalAssessment(result_id + ".functional", programme.identity, programme.selected_package.identity,
            roster.identity, manifest.identity, programme.preparation_nomination, comparisons, functional_cases,
            tuple(slot for slot in programme.criterion.family_slots if slot not in used))
    return manifest, MatrixRevisionProgrammeAssessment(result_id, programme.identity, manifest.identity, cases, functional,
        TRANSPORT if programme.criterion.is_matched else POINT_ONLY)
