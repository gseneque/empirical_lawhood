# SPDX-License-Identifier: MPL-2.0
"""All-horizon secondary diagnostics from terminal-consumed E5/E6 products.

Primary functional reductions and canonical bytes are unchanged. Native assay
adequacy survives unavailable point models. No carried calibration radius is a
prepared/transfer warrant; receiver, panel, action and view rows remain nested.
"""
from collections import Counter
from decimal import Decimal, DecimalException, localcontext
from fractions import Fraction

from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.retained_response_readout import (
    adequacy_cell, failure_detection, lifetime_readout, original_point_units,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import SelectedE4RevisionPoint
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_value

from .functional_case_reduction import _prepared_score_views
from .prepared_response_science import MatrixPreparedResponseReadout
from .selected_point import MatrixSelectedPointForecast

HORIZONS = (16, 64, 128)
VIEWS = ("PRIMARY", "FINE")


def _point_rows(point, source, view):
    if point is None: return (("POINT_NOT_SUPPLIED", (None,) * 15),)
    if type(point) is MatrixSelectedPointForecast:
        if point.feature.public_source.source != source.identity:
            raise ValueError("prepared secondary read substitutes the actual original point source")
        return point.log_points
    if type(point) is SelectedE4RevisionPoint:
        if point.source != source.identity:
            raise ValueError("prepared secondary read substitutes the actual revision point source")
        offset = 15 * VIEWS.index(view)
        return (("E4_REVISION", point.revision_predictions[offset:offset + 15]),
            ("E4_BASELINE", point.baseline_predictions[offset:offset + 15]))
    raise TypeError("prepared secondary read requires the actual selected original or revision point")


def _point_disposition(observation):
    if observation is None: return "MISSING"
    point = observation[0]
    return point.feature.disposition if type(point) is MatrixSelectedPointForecast else point.disposition


def _validated_observation(programme, case, source, observation):
    protocol = programme.protocol(source)
    panels = dict(programme.panels)[case.unit_id]
    point, mechanical, score = (None, None, None) if observation is None else observation
    if score is not None:
        if type(score) is not MatrixPreparedResponseReadout:
            raise TypeError("prepared secondary read requires the actual received native readout")
        score.__post_init__()
        if (score.source != source.identity or score.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or score.panels != tuple(panel.identity for panel in panels)
                or mechanical is None or mechanical.source != source.identity
                or score.preparation != mechanical.arrays.preparation
                or score.forecast is not None and score.forecast != mechanical.arrays.identity):
            raise ValueError("prepared secondary read changes original source, protocol, panel or physical prediction ancestry")
        _prepared_score_views(programme.criterion, source, score, protocol=protocol, panels=panels)
    if point is not None:
        point.__post_init__()
        if type(point) is SelectedE4RevisionPoint and point.feature is not None and (
                mechanical is None or point.source != source.identity or point.feature.mechanical != ObjectIdentity.from_record(mechanical.record_id, mechanical)
                or mechanical.source != source.identity or mechanical.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)):
            raise ValueError('matched prepared read changes its original causal point or handoff chart')
    return point, mechanical, score


def prepared_secondary_projection(programme, observations, groups):
    """Project exact already-authenticated terminal inputs; never load a product."""
    criterion = programme.criterion
    criterion.__post_init__()
    if hasattr(programme, "source_arms"):
        rows = programme.source_arms()
    elif hasattr(programme.sources, "source_arms"):
        rows = programme.sources.source_arms()
    else:
        arms = {public.source: arm for arm, public in programme.point_design.sources}
        rows = tuple((arms[source.identity], source) for source in programme.sources.sources)
    sources = {"case." + source.source_id: source for _, source in rows}
    cases = programme.roster.cases
    expected = {case.case_id for case in cases}
    if (len(sources) != len(rows) or set(sources) != expected or set(observations) != expected
            or len(cases) != len(expected)):
        raise ValueError("prepared secondary read drops or duplicates an assigned case")
    assigned = tuple(unit for _, units in groups for unit in units)
    if len(assigned) != len(set(assigned)) or set(assigned) != {case.unit_id for case in cases}:
        raise ValueError("prepared secondary read changes the complete original regime/group partition")
    if criterion.is_matched:
        return _matched_prepared_secondary(programme, observations, groups, sources, cases)
    panels = dict(programme.panels)
    details, lifetimes, detections = [], [], []
    for case in cases:
        source = sources[case.case_id]
        protocol = programme.protocol(source)
        if protocol.horizon_steps != HORIZONS or len(panels[case.unit_id]) != 2:
            raise ValueError("prepared secondary read changes the actual original three horizons or paired panels")
        observation = observations[case.case_id]
        point, mechanical, score = _validated_observation(programme, case, source, observation)
        points = {view: _point_rows(point, source, view) for view in VIEWS}
        for predictor in PREDICTORS:
            view_cells = {view: [] for view in VIEWS}
            for horizon in HORIZONS:
                selected = {} if score is None else {view: tuple(sorted((row for row in score.cells if
                    row.view == view and row.predictor == predictor and row.horizon_tick <= horizon), key=lambda row: row.key[1:])) for view in VIEWS}
                discrepancy = (score is not None and any(left.normalized_error is not None and right.normalized_error is not None
                    and abs(Fraction(left.normalized_error) - Fraction(right.normalized_error)) > Fraction(criterion.paired_view_discrepancy_maximum)
                    for left, right in zip(selected["PRIMARY"], selected["FINE"], strict=True)))
                for view in VIEWS:
                    observed = () if score is None else selected[view]
                    finite = (score is not None and score.numerical_pass and score.disposition in ("FINITE", "PARTIAL")
                        and not discrepancy and bool(observed) and all(row.normalized_error is not None for row in observed))
                    error = max(row.normalized_error for row in observed) if finite else None
                    disposition = ("MISSING" if score is None else "PAIRED_VIEW_DISCREPANCY" if discrepancy else
                        "CROSSCHECKED_FINITE" if finite else score.disposition)
                    cell = adequacy_cell(horizon, error, normalized_tolerance=criterion.normalized_error_maximum,
                        disposition=disposition, known_nonuse=score is not None and score.disposition == "NO_ORIGIN")
                    view_cells[view].append(cell)
                    base = {"case_id": case.case_id, "unit_id": case.unit_id, "arm_id": case.arm_id,
                        "view": view, "description": predictor, "horizon": horizon}
                    details.append({**base, "actual_error": error, "classification": cell.classification,
                        "definitely_adequate": cell.definitely_adequate, "possibly_adequate": cell.possibly_adequate,
                        "source_disposition": cell.source_disposition, "paired_view_discrepancy": discrepancy})
                    index = PREDICTORS.index(predictor) * len(HORIZONS) + HORIZONS.index(horizon)
                    for method, values in points[view]:
                        predicted = original_point_units(values[index])
                        detections.append({**base, "method": method, "raw_log_prediction": values[index],
                            "predicted_error": predicted, "decision": failure_detection(cell, predicted, criterion.normalized_error_maximum)})
            for view, cells in view_cells.items():
                lifetimes.append({"case_id": case.case_id, "unit_id": case.unit_id, "arm_id": case.arm_id,
                    "view": view, "description": predictor, **lifetime_readout(cells)})
    counts = []
    for regime, units in groups:
        for arm in sorted({case.arm_id for case in cases}):
            selected = tuple(case for case in cases if case.unit_id in units and case.arm_id == arm)
            if {case.unit_id for case in selected} != set(units) or len(selected) != len(units):
                raise ValueError("prepared secondary read thins a matched assigned arm/regime")
            ids = {case.case_id for case in selected}
            protocol = programme.protocol(sources[selected[0].case_id])
            counts.append({"regime": regime, "arm_id": arm, "assigned_independent_units": len(units),
                "assigned_cases": len(selected), "units": units, "nested_views_per_case": 2,
                "nested_panels_per_case": 2, "nested_actions_per_panel": len(protocol.actions),
                "nested_receivers_per_cell": protocol.receiver_count,
                "readout_dispositions": dict(Counter("MISSING" if observations[case.case_id] is None else observations[case.case_id][2].disposition for case in selected)),
                "point_dispositions": dict(Counter(_point_disposition(observations[case.case_id]) for case in selected)),
                "adequacy_counts": tuple({"view": view, "description": predictor, "horizon": horizon,
                    "assigned_units": len(units), "classifications": dict(Counter(row["classification"] for row in details
                        if row["case_id"] in ids and (row["view"], row["description"], row["horizon"]) == (view, predictor, horizon)))}
                    for view in VIEWS for predictor in PREDICTORS for horizon in HORIZONS)})
    return canonical_value({"scope": "SECONDARY_ALL15_NATIVE_ADEQUACY_USEFUL_LIFETIME_AND_POINT_FAILURE_DETECTION",
        "criterion": criterion, "programme": programme.identity, "roster": programme.roster.identity,
        "normalized_tolerance": criterion.normalized_error_maximum,
        "paired_view_discrepancy_maximum": criterion.paired_view_discrepancy_maximum,
        "primary_endpoint": {"description": criterion.predictor, "horizon": criterion.horizon_tick, "unchanged": True},
        "standing": "SECONDARY_DESCRIPTIVE_FINITE_DT_NO_NEW_HYPOTHESIS_TEST_OR_QUALIFICATION",
        "lifetime_inference_scope": "CUMULATIVE_ERROR_ON_DECLARED_RETAINED_16_64_128_LATTICE_ONLY",
        "point_uncertainty": "UNESTABLISHED", "admission": "UNESTABLISHED", "service": "UNESTABLISHED",
        "sampling_warrant": "NOT_ESTABLISHED_BY_THIS_READOUT", "counts": tuple(counts),
        "adequacy": tuple(details), "useful_lifetimes": tuple(lifetimes), "failure_detection": tuple(detections),
        "readouts": tuple((case.case_id, None if observations[case.case_id] is None else
            ObjectIdentity.from_record(observations[case.case_id][2].record_id, observations[case.case_id][2])) for case in cases)})


def _matched_prepared_secondary(programme, observations, groups, sources, cases):
    """Same-bank response, amplitude and frozen-policy reports for every arm."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import (
        admission_risk, matched_coverage_values, matched_duration_error_count, original_error_points, complete_group_loss_summary,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import ORIGIN_RESPONSE_PREDICTORS
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS, paired_adequacy
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import RELATION_METHODS, relation_target_reasons
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import TRANSPORT
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import curve_decision, curve_loss, curve_loss_summary
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_duration import evaluation_median_K

    details, by_pair, median_rows = [], {}, {}
    for case in cases:
        source = sources[case.case_id]
        point, mechanical, score = _validated_observation(programme, case, source, observations[case.case_id])
        if score is not None and (score.dense is None or type(point) is not SelectedE4RevisionPoint or point.feature is None):
            raise ValueError("matched prepared report requires its original dense readout and causal revision seal")
        curves = {} if score is None else {(curve.view, curve.predictor): curve for curve in score.dense.curves}
        first_discrepancy = {}
        if score is not None:
            cells = {row.key: row.normalized_error for row in score.cells}
            for row in score.cells:
                if row.view != 'PRIMARY':
                    continue
                other = cells['FINE', *row.key[1:]]
                if (row.normalized_error is not None and other is not None and
                        abs(Fraction(row.normalized_error) - Fraction(other)) > Fraction(programme.criterion.paired_view_discrepancy_maximum)):
                    first_discrepancy[row.predictor] = min(first_discrepancy.get(row.predictor, 129), row.horizon_tick)
        outcomes, durations, discrepancies = {}, [], {}
        for method in ORIGIN_RESPONSE_PREDICTORS:
            discrepant = []
            for horizon in DENSE_RESPONSE_HORIZONS:
                paired = () if score is None else tuple(curves[view, method] for view in VIEWS)
                # One horizon's availability uses only its preceding sampled
                # checks; a later discrepancy cannot erase an earlier result.
                bad = first_discrepancy.get(method, 129) <= horizon
                usable = score is not None and score.numerical_pass and not bad
                measured = tuple(curve.duration(numerical_usable=usable) for curve in paired)
                outcomes[method, horizon] = None if score is None else paired_adequacy(measured, horizon)
                discrepant.append(bad)
            discrepancies[method] = tuple(discrepant)
            for view in VIEWS:
                curve = curves.get((view, method))
                duration = None if curve is None else curve.duration(numerical_usable=score.numerical_pass and not discrepant[-1])
                durations.append({'view': view, 'description': method, 'sampled_adequacy': tuple(
                    None if curve is None else curve.duration(numerical_usable=score.numerical_pass and not discrepant[index]).adequate_through(horizon)
                    for index, horizon in enumerate(DENSE_RESPONSE_HORIZONS)),
                    'K': None if duration is None else duration.count, 'K_bounds': (0, 29) if duration is None else duration.count_bounds,
                    'first_known_failure_tick': None if duration is None else duration.first_known_failure_tick,
                    'first_unknown_tick': DENSE_RESPONSE_HORIZONS[0] if duration is None else duration.first_unknown_tick,
                    'complete_followup': False if duration is None else duration.complete_followup,
                    'right_censored': False if duration is None else duration.right_censored,
                    'full_tick1_through128_curve': curve})
        zero_views = tuple(None if score is None else curves[view, 'ZERO_RESPONSE'].duration(
            numerical_usable=score.numerical_pass and not discrepancies['ZERO_RESPONSE'][DENSE_RESPONSE_HORIZONS.index(64)]).adequate_through(64) for view in VIEWS)
        zero_partition = ('UNRESOLVED' if None in zero_views else 'ZERO_FAILS_BOTH' if zero_views == (False, False)
            else 'SMALL_SIGNAL_ZERO_PASSES_BOTH' if zero_views == (True, True) else 'VIEWS_DISAGREE')
        targets = (None,) * 58 if score is None else tuple(value for view in VIEWS
            for value in curves[view, 'FACTOR'].cumulative_sampled_errors(numerical_usable=score.numerical_pass))
        target_usable = score is not None and score.numerical_pass and not relation_target_reasons(targets)
        points = (tuple((method, (None,) * 58) for method in (*RELATION_METHODS, 'B0', 'S0')) if point is None
            else (*point.relation_points, *point.reference_points))
        errors, coverage = [], []
        for method, values in points:
            try:
                predicted = original_error_points(values)
                projection_reason = None
            except DecimalException:
                predicted, projection_reason = (None,) * 58, 'UNREPRESENTABLE_ORIGINAL_UNIT_PREDICTION'
            available = target_usable and all(value is not None for value in (*targets, *predicted))
            exact_mae = sum((abs(Fraction(a) - Fraction(b)) for a, b in zip(predicted, targets, strict=True)), Fraction(0)) / 58 if available else None
            with localcontext() as context:
                context.prec = 60
                mae = Decimal(exact_mae.numerator) / Decimal(exact_mae.denominator) if available else None
            errors.append({'method': method, 'duration_error_count_over58': matched_duration_error_count(values, targets) if target_usable else None,
                'mean_absolute_error_paired58': mae, 'mean_absolute_error_paired58_exact_ratio':
                    None if exact_mae is None else (exact_mae.numerator, exact_mae.denominator), 'original_unit_projection_reason': projection_reason})
            if programme.criterion.is_curve_primary:
                errors[-1]['normalized_root_curve_rms'] = curve_loss(values, targets) if target_usable else None
        if point is not None:
            coverage = tuple(matched_coverage_values(case.unit_id, policy.method_key, dict(points)[policy.method_key], policy,
                targets, target_usable) for policy in point.policies)
        amplitudes = () if score is None else tuple({'view': row.view, 'panel_id': row.panel_id, 'action_id': row.action_id,
            'contrast': row.contrast, 'horizon_tick': tick,
            **{name: getattr(row, name)[tick] for name in ('position_norms', 'momentum_norms', 'position_minima', 'position_maxima',
                'momentum_minima', 'momentum_maxima', 'complement_position_norms', 'complement_momentum_norms',
                'sector_x_position_norms', 'sector_y_position_norms', 'sector_x_momentum_norms', 'sector_y_momentum_norms', 'normalized_amplitudes')}}
            for row in score.dense.amplitudes for tick in (64, 128))
        detail = {'case_id': case.case_id, 'unit_id': case.unit_id, 'arm_id': case.arm_id,
            'source': source.identity, 'recipe': source.recipe.identity, 'preparation_effort': case.preparation_effort,
            'effort_unit': programme.criterion.effort_unit, 'mechanical': None if mechanical is None else ObjectIdentity.from_record(mechanical.record_id, mechanical),
            'chart_arrays': None if mechanical is None else mechanical.arrays.identity,
            'causal_feature': None if point is None else point.feature, 'readout': None if score is None else ObjectIdentity.from_record(score.record_id, score),
            'point_disposition': _point_disposition(observations[case.case_id]), 'readout_disposition': 'MISSING' if score is None else score.disposition,
            'factor_adequate_through64': outcomes['FACTOR', 64], 'zero_response_through64_by_view': zero_views,
            'zero_response_partition': zero_partition,
            'factor_passes_zero_fails_both': (None if outcomes['FACTOR', 64] is None or None in zero_views
                else outcomes['FACTOR', 64] and zero_views == (False, False)),
            'durations': tuple(durations), 'response_magnitudes': amplitudes, 'prediction_losses': tuple(errors), 'coverage': tuple(coverage),
            'policies': () if point is None else point.policies, 'admission_refusal_reasons': (
                ('MISSING_PRE_FUTURE_POINT',) if point is None else tuple(sorted({
                    *(('CAUSAL_FEATURE_' + point.feature.disposition,) if point.feature.disposition != 'AVAILABLE' else ()),
                    *(policy.method_key + '_BOUND_' + policy.bound_kind for policy in point.policies if policy.bound_kind != 'FINITE')})))}
        if programme.criterion.is_curve_primary:
            detail['curve_comparison'] = curve_decision(case.unit_id,
                ({method: dict(points)[method] for method in RELATION_METHODS},), (targets,),
                () if target_usable else ('NUMERICALLY_UNUSABLE_TARGET',), structural_method='SR', coordinate_ids=(case.case_id,))
            median_rows[case.unit_id, case.arm_id] = (case.case_id, case.unit_id, targets, target_usable)
        details.append(detail)
        by_pair[case.unit_id, case.arm_id] = (detail, outcomes, point, score)
    counts, risks, loss_summaries = [], [], []
    arms = tuple(arm for arm, _ in programme.arms)
    for regime, units in groups:
        for arm in arms:
            values = tuple(by_pair[unit, arm] for unit in units)
            losses = tuple({row['method']: row for row in value[0]['prediction_losses']} for value in values)
            def loss(method, key):
                return tuple(None if row[method][key] is None else Fraction(row[method][key], 58)
                    if key == 'duration_error_count_over58' else Fraction(row[method][key])
                    if key == 'normalized_root_curve_rms' else Fraction(*row[method][key]) for row in losses)
            def difference(left, right, key):
                return tuple(None if a is None or b is None else a - b
                    for a, b in zip(loss(left, key), loss(right, key), strict=True))
            loss_summaries.append({'regime': regime, 'arm_id': arm, 'assigned_group_ids': units,
                'scope': 'OBSERVED_GROUPS_DESCRIPTIVE_NO_POPULATION_MEAN_OR_CAUSAL_MEDIATION_CLAIM',
                'absolute_duration_loss': tuple((method, complete_group_loss_summary(loss(method, 'duration_error_count_over58')))
                    for method in (*RELATION_METHODS, 'B0', 'S0')),
                'mean_absolute_original_error_paired58': tuple((method, complete_group_loss_summary(loss(method, 'mean_absolute_error_paired58_exact_ratio')))
                    for method in (*RELATION_METHODS, 'B0', 'S0')),
                'continuous_differences': tuple({'left_minus_right': (left, right),
                    'duration_loss': complete_group_loss_summary(difference(left, right, 'duration_error_count_over58')),
                    'mean_absolute_original_error': complete_group_loss_summary(difference(left, right, 'mean_absolute_error_paired58_exact_ratio'))}
                    for left, right in (('BR', 'SR'), ('B0', 'S0'), ('S0', 'SR'), ('B0', 'BR')))})
            if programme.criterion.is_curve_primary:
                loss_summaries[-1].update({
                    'curve_comparison': curve_loss_summary(tuple(value[0]['curve_comparison'] for value in values)),
                    'absolute_curve_loss': tuple((method, complete_group_loss_summary(loss(method, 'normalized_root_curve_rms')))
                        for method in (*RELATION_METHODS, 'B0', 'S0')),
                    'paired_curve_differences': tuple({'left_minus_right': (left, right),
                        'loss_summary': complete_group_loss_summary(difference(left, right, 'normalized_root_curve_rms')),
                        'complete_assigned_differences': tuple((unit, None if value is None else (value.numerator, value.denominator))
                            for unit, value in zip(units, difference(left, right, 'normalized_root_curve_rms'), strict=True))}
                        for left, right in (('BR', 'SR'), ('B0', 'S0'), ('S0', 'SR'), ('B0', 'BR'))),
                    'DEV_median_K': evaluation_median_K(programme.selected_package.models.relation_fit.models[0], units,
                        tuple(median_rows[unit, arm] for unit in units))})
            counts.append({'regime': regime, 'arm_id': arm, 'assigned_independent_units': len(units), 'unit_ids': units,
                'adequacy_counts': tuple({'description': method, 'horizon_tick': horizon,
                    'observed_successes': sum(row[1][method, horizon] is True for row in values),
                    'observed_failures': sum(row[1][method, horizon] is False for row in values),
                    'unknown': sum(row[1][method, horizon] is None for row in values)}
                    for method in ORIGIN_RESPONSE_PREDICTORS for horizon in DENSE_RESPONSE_HORIZONS),
                'bound_kinds': tuple({'method': method, 'counts': dict(Counter('UNAVAILABLE' if row[2] is None else
                    next(policy.bound_kind for policy in row[2].policies if policy.method_key == method) for row in values))} for method in ('BR', 'SR'))})
            for method in ('BR', 'SR'):
                for index, horizon in enumerate(DENSE_RESPONSE_HORIZONS):
                    admissions = tuple(None if row[2] is None else next(policy.admissions[index] for policy in row[2].policies
                        if policy.method_key == method) for row in values)
                    adequate = tuple(row[1]['FACTOR', horizon] for row in values)
                    risks.append({'regime': regime, 'arm_id': arm, 'method': method, 'horizon_tick': horizon,
                        'policy_interpretation': TRANSPORT, **admission_risk(units, admissions, adequate)})
    gains = []
    for regime, units in groups:
        for arm in arms:
            if arm == programme.hold_arm_id:
                continue
            partitions = Counter()
            for unit in units:
                baseline, prepared = (by_pair[unit, selected] for selected in (programme.hold_arm_id, arm))
                if baseline[1]['FACTOR', 64] is not False or prepared[1]['FACTOR', 64] is not True:
                    continue
                label = prepared[0]['zero_response_partition']
                partitions[label] += 1
                amplitudes = tuple({row.key: (row.position_norms[64], row.momentum_norms[64]) for row in item[3].dense.amplitudes
                    if row.contrast == 'ODD'} for item in (baseline, prepared))
                if amplitudes[0].keys() != amplitudes[1].keys():
                    raise ValueError("paired amplitude report substitutes a matched panel/action/view")
                pairs = tuple((before, after) for key in sorted(amplitudes[0])
                    for before, after in zip(amplitudes[0][key], amplitudes[1][key], strict=True))
                decrease = (None if any(value is None for pair in pairs for value in pair) else
                    all(after <= before for before, after in pairs) and any(after < before for before, after in pairs))
                gains.append({'regime': regime, 'unit_id': unit, 'arm_id': arm, 'zero_response_partition': label,
                    'paired_magnitudes_decrease_all_views_panels_actions_q_and_p_at64': decrease,
                    'baseline_case': baseline[0]['case_id'], 'prepared_case': prepared[0]['case_id'],
                    'baseline_chart': baseline[0]['chart_arrays'], 'prepared_chart': prepared[0]['chart_arrays'],
                    'interpretation': 'PAIRED_CHANGE_UNDER_STATE_CONDITIONED_ASSAY_NOT_IDENTICAL_PHYSICAL_FORCES'})
            counts.append({'regime': regime, 'arm_id': arm, 'observed_gain_zero_response_partitions': dict(partitions)})
    return canonical_value({'scope': 'MATCHED_SAMPLED_RESPONSE_ADEQUACY_AND_FROZEN_E4_TRANSPORT',
        'programme': programme.identity, 'criterion': programme.criterion, 'horizon_ticks': DENSE_RESPONSE_HORIZONS,
        'primary_response_adequacy_horizon': 64, 'primary_response_adequacy_tolerance': Decimal('.01'),
        'external_delivered_task': 'NOT_SELECTED', 'service_definition': 'ADMISSION_AND_OBSERVED_SAMPLED_RESPONSE_ADEQUACY',
        'calibration_interpretation': TRANSPORT, 'conditional_admission_reliability_guarantee': 'NOT_ESTABLISHED',
        'coupling_interpretation': 'NET_ARM_MARGINAL_DIFFERENCE_GAIN_AND_HARM_FRACTIONS_DEPEND_ON_COMMON_NOISE_COUPLING',
        'quieting_interpretation': 'REQUIRES_OBSERVED_PAIRED_MAGNITUDE_DECREASE_UNDER_EACH_STATE_CONDITIONED_CHART',
        'thermodynamic_cost_claim': 'NOT_SELECTED_EFFORT_PROXY_IS_NOT_WORK_HEAT_OR_ENTROPY',
        'counts': tuple(counts), 'cases': tuple(details), 'observed_gains': tuple(gains), 'admission_risks': tuple(risks),
        'prediction_loss_summaries': tuple(loss_summaries),
        'statistical_completions_are_observed_physical_harms': False,
        'population_benefit_at_least_point_threshold_certified': False,
        'standing': 'DESCRIPTIVE_FROZEN_TRANSPORT_NO_NEW_TESTS_OR_SCIENTIFIC_QUALIFICATION'})
