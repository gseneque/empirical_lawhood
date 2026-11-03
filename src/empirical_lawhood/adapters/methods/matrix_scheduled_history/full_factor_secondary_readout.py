# SPDX-License-Identifier: MPL-2.0
"""Exact secondary E4 structural/functional joins over retained original values.

Structural origins stay the original first factor admission. Functional error
horizons stay relative to the actual response cutoff. Their intervals are not
silently equated. No future observation is delivered to a frozen predictor.
"""
from collections import Counter
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import (
    E4_HEADLINE_TOLERANCE, E4_SENSITIVITY_TOLERANCES,
)
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import _moving_state
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import model_predictors, MatrixOriginResponseModel, ORIGIN_RESPONSE_PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import MatrixDenseResponseCell
from empirical_lawhood.adapters.methods.matrix_factor_response.retained_response_readout import (
    AdequacyCell, adequacy_cell, failure_detection, lifetime_readout, original_point_units,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_consumer import response_adequacy_values
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import sampled_pass_count_bounds
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_value

from .full_factor_records import validate_assessment
from .e4_structural_prediction import E4StructuralPredictionCase
from .paired_target_reduction import paired_targets
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_secondary_readout import E4_OBSERVATION_HORIZONS, E4_PRIMARY_TIMESTEP
from .response_records import ScheduledResponseScore, ScheduledResponseLossCell, ScheduledE4DenseResponseCell, ScheduledE4DenseResponseScore, branch_census

HORIZONS = (16, 64, 128)
VIEWS = ("PRIMARY", "FINE")


@dataclass(frozen=True, slots=True)
class OriginalFunctionalRows:
    """Ephemeral small projection; its caller still authenticates real custody."""
    original_case: ObjectIdentity
    source: ObjectIdentity
    root_id: str
    group_id: str
    coordinate: ObjectIdentity
    origin_tick: int
    score: ObjectIdentity | None
    causal_prefix: ObjectIdentity | None
    disposition: str
    errors: tuple
    forecasts: tuple
    observation_horizons: tuple = HORIZONS
    instantaneous_errors: tuple = ()
    original_errors: tuple = ()
    instantaneous_complete: tuple = ()
    cumulative_complete: tuple = ()
    secondary_target: ObjectIdentity | None = None
    secondary_selection: ObjectIdentity | None = None
    dense_score: ObjectIdentity | None = None
    prediction: E4StructuralPredictionCase | None = None
    predictors: tuple = PREDICTORS
    original_observation_horizons: tuple = HORIZONS
    target_contract: str = "PAIRED15"


def original_functional_rows(bank, case, score):
    """Consume one actual original score once, inside the original read lifetime."""
    case.__post_init__()
    protocols = tuple(row for row in bank.response_selection.protocols if row.public_source.root.root_id == case.root_id)
    if len(protocols) != 1: raise ValueError("E4 functional join lacks its exact original root protocol")
    protocol, = protocols
    panels = dict(bank.response_selection.panels)[case.group_id]
    public = protocol.public_source
    horizons = protocol.horizon_steps
    predictors = model_predictors(protocol.mechanical_model)
    if (horizons not in (HORIZONS, E4_OBSERVATION_HORIZONS) or len(panels) != 2 or len(protocol.actions) != 4
            or protocol.receiver_count != 48 or public.source != case.source
            or public.root.independent_group_id != case.group_id
            or protocol.criterion != bank.forecast_design.criterion_record.identity):
        raise ValueError("E4 functional join changes actual source/group/mathematics or nested assay census")
    errors = instantaneous = (None,) * (2 * len(predictors) * len(horizons))
    menus = complete = (False,) * len(errors)
    disposition = "UNKNOWN_CONTACT" if any(row.phase == "responses" and row.disposition == "UNKNOWN" for row in case.native) else "UNAVAILABLE"
    if score is None:
        if case.score is not None: raise PermissionError("E4 functional join omits the actual retained score")
    else:
        if type(score) is not ScheduledResponseScore: raise TypeError("E4 functional join requires the actual original score owner")
        score.__post_init__()
        if (case.score != ObjectIdentity.from_record(score.score_id, score) or score.source != case.source
                or (score.root_id, score.independent_group_id) != (case.root_id, case.group_id)
                or score.error_forecast != case.forecast or score.criterion != protocol.criterion
                or paired_targets(score, protocol, panels) != case.paired_log_targets):
            raise PermissionError("E4 functional join substitutes actual original score/account/case ancestry")
        instantaneous, lower, menus, complete = _error_curves(score.cells, protocol, panels, horizons)
        errors = tuple(value if full and score.numerical_pass and score.disposition in ('FINITE', 'PARTIAL') else None
            for value, full in zip(lower, complete, strict=True))
        if score.disposition in ("FINITE", "PARTIAL"):
            branches = branch_census(protocol, panels)
            if (tuple(row.control_id for row in score.controls) != tuple("control.scheduled." + score.root_id + "." + branch for branch, *_ in branches)
                    or any(row.denominator_steps != (128 if view == "PRIMARY" else 256)
                        or row.denominator_real_coordinates != 192 or row.tolerance != protocol.native_reference_tolerance
                        for row, (_, view, *_rest) in zip(score.controls, branches, strict=True))):
                raise ValueError("E4 functional join loses full original paired native branch controls")
            for control in score.controls: control.__post_init__()
        disposition = score.disposition
    return OriginalFunctionalRows(ObjectIdentity.from_record(case.root_id, case), case.source, case.root_id, case.group_id,
        ObjectIdentity.from_record(public.coordinate.coordinate_id, public.coordinate), public.policy.cutoff_tick,
        case.score, None if score is None else score.causal_prefix, disposition, errors, case.original_log_points,
        observation_horizons=horizons, predictors=predictors, original_observation_horizons=horizons,
        instantaneous_errors=instantaneous, instantaneous_complete=menus, cumulative_complete=complete,
        target_contract=case.target_contract)


def _error_curves(cells, protocol, panels, horizons):
    """Observed nonnegative lower bounds plus exact menu/prefix completeness."""
    cells = tuple(cells)
    predictors = model_predictors(protocol.mechanical_model)
    expected = {(view, panel.panel_id, action.action_id, predictor, horizon) for view in VIEWS
        for panel in panels for action in protocol.actions for predictor in predictors for horizon in horizons}
    kind = (MatrixDenseResponseCell if type(protocol.mechanical_model) is MatrixOriginResponseModel
        else ScheduledResponseLossCell if horizons == HORIZONS else ScheduledE4DenseResponseCell)
    if (any(type(cell) is not kind for cell in cells)
            or len(cells) != len(expected) or {cell.key for cell in cells} != expected):
        raise ValueError('E4 functional join loses complete paired receiver/action/panel/horizon cells')
    by_endpoint = {}
    for cell in cells:
        cell.__post_init__()
        if kind is ScheduledResponseLossCell:
            vectors = cell.actual_odd_responses, cell.signed_errors, cell.absolute_errors, cell.relative_errors
            if (any(values is not None and len(values) != 48 for values in vectors)
                    or cell.normalized_error is not None and any(values is None for values in vectors)):
                raise ValueError('E4 functional join thins complete original receiver vectors')
        by_endpoint.setdefault((cell.view, cell.predictor, cell.horizon_tick), []).append(cell.normalized_error)
    instantaneous, cumulative, menus, prefixes = [], [], [], []
    for view in VIEWS:
        for predictor in predictors:
            maximum, complete = None, True
            for horizon in horizons:
                values = by_endpoint[view, predictor, horizon]
                known = tuple(value for value in values if value is not None)
                point = max(known) if known else None
                menu_complete = len(known) == len(values)
                instantaneous.append(point)
                menus.append(menu_complete)
                complete = complete and menu_complete
                if point is not None:
                    maximum = point if maximum is None else max(maximum, point)
                cumulative.append(maximum)
                prefixes.append(complete)
    return tuple(instantaneous), tuple(cumulative), tuple(menus), tuple(prefixes)


def dense_e4_functional_rows(bank, case, score, *, dense_score, target, secondary):
    """Retain genuine absent cases; a present score requires its dense output.

    The custody caller uses the actual successful scoring receipt's complete
    output roster before this pure projection. A missing/corrupt required output
    of that receipt raises there; it must never be converted to ``None`` here.
    """
    row = original_functional_rows(bank, case, score)
    protocol = next(value for value in bank.response_selection.protocols if value.public_source.root.root_id == case.root_id)
    secondary.validate_target(target)
    target.validate_protocol(protocol)
    horizons = target.observation_horizons
    if score is None:
        # original_functional_rows has already proved case.score is None and
        # derived UNKNOWN_CONTACT/UNAVAILABLE from the actual native census.
        if dense_score is not None:
            raise PermissionError('absent original score case cannot invent a dense score product')
        count = len(VIEWS) * len(row.predictors) * len(horizons)
        instantaneous = errors = (None,) * count
        menus = prefixes = (False,) * count
        dense_pin = None
    else:
        # Includes genuine NO_ORIGIN/UNEVALUABLE/NATIVE_CROSSCHECK_FAILED
        # records: none may hide a missing required new scoring output.
        if type(dense_score) is not ScheduledE4DenseResponseScore:
            raise PermissionError('present original E4 score requires its actual supplemental score output')
        panels = dict(bank.response_selection.panels)[case.group_id]
        dense_score.validate_original(protocol, panels, target, secondary, score)
        instantaneous, errors, menus, prefixes = _error_curves(dense_score.cells, protocol, panels, horizons)
        dense_pin = dense_score.identity
    return replace(row, errors=errors, observation_horizons=horizons,
        instantaneous_errors=instantaneous, original_errors=row.errors,
        instantaneous_complete=menus, cumulative_complete=prefixes,
        secondary_target=target.identity, secondary_selection=secondary.identity, dense_score=dense_pin)


def _dense_adequacy(horizon, lower, complete, tolerance, disposition):
    """Incomplete peers bar pass, but cannot erase an observed failing bound."""
    if disposition == 'NO_ORIGIN':
        return adequacy_cell(horizon, None, normalized_tolerance=tolerance,
            disposition=disposition, known_nonuse=True)
    usable = disposition in ('FINITE', 'PARTIAL')
    if usable and complete:
        return adequacy_cell(horizon, lower, normalized_tolerance=tolerance, disposition='CROSSCHECKED_FINITE')
    # Original numerical failure remains unresolved even if received raw
    # errors exist; raw lower bounds remain visible in the accompanying curve.
    known_lower = lower if usable and lower is not None else Decimal(0)
    classification, definite, possible = response_adequacy_values('UNRESOLVED_INTERVAL', known_lower, None, tolerance)
    return AdequacyCell(horizon, classification, definite, possible, disposition)


def _grid_lifetime(cells):
    cells = tuple(cells)
    if tuple(cell.horizon_step for cell in cells) != E4_OBSERVATION_HORIZONS:
        raise ValueError('E4 useful horizon requires its complete frozen sampled grid')
    result = lifetime_readout(cells)
    failure, passing = result['first_definite_failure'], result['last_definite_pass']
    exact_sample = failure is not None and result['first_possible_failure'] == failure
    censored = result['censoring_status'] == 'RIGHT_CENSORED_AT_LAST_HORIZON'
    passes = tuple(True if cell.definitely_adequate else False
        if cell.classification in ('FINITE_INADEQUATE', 'UNRESOLVED_INADEQUATE') else None for cell in cells)
    lower_count, upper_count = sampled_pass_count_bounds(passes)
    complete = all(cell.classification in ('FINITE_ADEQUATE', 'FINITE_INADEQUATE') for cell in cells)
    with localcontext() as context:
        context.prec = 80
        result.update({'initial_sampled_pass_count': lower_count if lower_count == upper_count else None,
            'initial_sampled_pass_count_lower': lower_count, 'initial_sampled_pass_count_upper': upper_count,
            'sampled_check_count': len(E4_OBSERVATION_HORIZONS), 'sampled_followup_complete': complete,
            'sampled_right_censored': complete and lower_count == len(E4_OBSERVATION_HORIZONS),
            'tau_epsilon_grid': failure if exact_sample else None,
            'tau_epsilon_grid_time': E4_PRIMARY_TIMESTEP * failure if exact_sample else None,
            'definite_failure_by_step': failure,
            'definite_failure_by_time': None if failure is None else E4_PRIMARY_TIMESTEP * failure,
            'last_passing_time': None if passing is None else E4_PRIMARY_TIMESTEP * passing,
            'right_censored_at_step': E4_OBSERVATION_HORIZONS[-1] if censored else None,
            'right_censored_at_time': Decimal('0.128') if censored else None,
            'failure_observation': 'FAILED_BY_FIRST_CHECKED_HORIZON' if failure == 16 and passing is None
                else 'FIRST_SAMPLED_CUMULATIVE_FAILURE' if exact_sample
                else 'FAILED_BY_OBSERVED_HORIZON_EARLIER_SAMPLED_STATUS_UNRESOLVED' if failure is not None else result['censoring_status'],
            'crossing_scope': 'SAMPLED_GRID_ONLY_UNOBSERVED_EXCURSIONS_NOT_EXCLUDED'})
    return result


def _dense_description(row, view, predictor, tolerance):
    offset = (VIEWS.index(view) * len(row.predictors) + row.predictors.index(predictor)) * len(E4_OBSERVATION_HORIZONS)
    stop = offset + len(E4_OBSERVATION_HORIZONS)
    values, complete = row.errors[offset:stop], row.cumulative_complete[offset:stop]
    cells = tuple(_dense_adequacy(horizon, lower, full, tolerance, row.disposition)
        for horizon, lower, full in zip(E4_OBSERVATION_HORIZONS, values, complete, strict=True))
    return {'root_id': row.root_id, 'unit_id': row.group_id, 'coordinate': row.coordinate,
        'description': predictor, 'view': view, 'normalized_tolerance': tolerance,
        'cumulative_error_lower_bounds': values, 'cumulative_prefix_complete': complete,
        'instantaneous_error_lower_bounds': row.instantaneous_errors[offset:stop],
        'instantaneous_menu_complete': row.instantaneous_complete[offset:stop],
        'classifications': tuple(cell.classification for cell in cells),
        'received_error_disposition': row.disposition, **_grid_lifetime(cells)}


def _survival(lifetime, tick, response_origin):
    if lifetime is None: return "UNAVAILABLE"
    if lifetime.origin_tick is None: return "NO_STRUCTURAL_ORIGIN" if lifetime.disposition == "NOT_AT_RISK" else "UNKNOWN"
    if lifetime.origin_tick > response_origin: return "NOT_AT_RISK_AT_RESPONSE_ORIGIN"
    if tick <= lifetime.last_known_survival_tick: return "SURVIVED"
    if lifetime.exit_upper_tick is not None and tick >= lifetime.exit_upper_tick: return "FAILED"
    return "UNKNOWN"


def _failure_order(structural, functional, origin):
    upper = functional["first_definite_failure"]
    if structural is None or structural.exit_upper_tick is None or upper is None:
        return "CENSORED_NONUSE_OR_UNRESOLVED"
    lower = functional["last_definite_pass"] or 0
    if structural.exit_upper_tick <= origin + lower: return "STRUCTURAL_FAILURE_PRECEDES_FUNCTIONAL_INTERVAL"
    if origin + upper <= structural.last_known_survival_tick: return "FUNCTIONAL_FAILURE_PRECEDES_STRUCTURAL_INTERVAL"
    return "OVERLAPPING_INTERVALS_ORDER_UNRESOLVED"


def structural_functional_projection(scope, products, assessments, functional_rows, *, target, secondary):
    """Dense-only E4 response projection joined to the actual3point structure."""
    secondary.validate_target(target)
    scope.__post_init__()
    observation_horizons = target.observation_horizons
    normalized_tolerance = target.normalized_adequacy_tolerance
    target_origin, lineage_scope = target.identity, secondary.lineage_scope
    products = tuple(products); assessments = tuple(assessments); functional_rows = tuple(functional_rows)
    if (len(products) != len(scope.sources) or len(assessments) != len(scope.sources)
            or len(functional_rows) != len(scope.sources)
            or {row.root_id for row in functional_rows} != {row.root_id for row in scope.sources}):
        raise ValueError("E4 secondary join drops or duplicates a complete assigned case")
    by_root = {row.root_id: row for row in functional_rows}
    details, lifetimes, detections, joins = [], [], [], []
    for source, case, product, assessment in zip(scope.sources, scope.original_cases, products, assessments, strict=True):
        validate_assessment(source, product, assessment)
        row = by_root[source.root_id]
        cutoff = next(case.information_cutoff for case in scope.programme.cases if case.root_id == source.root_id)
        if (type(row) is not OriginalFunctionalRows or (row.original_case, row.source, row.group_id, row.coordinate) !=
                (source.original_case, source.source, source.group_id, ObjectIdentity.from_record(source.coordinate.coordinate_id, source.coordinate))
                or row.score != case.score or row.forecasts != case.original_log_points
                or row.observation_horizons != observation_horizons
                or row.target_contract != case.target_contract
                or row.predictors != (ORIGIN_RESPONSE_PREDICTORS if row.target_contract == "MATCHED_FACTOR58" else PREDICTORS)
                or row.original_observation_horizons != (E4_OBSERVATION_HORIZONS if row.target_contract == "MATCHED_FACTOR58" else HORIZONS)
                or row.secondary_target != target.identity or row.secondary_selection != secondary.identity
                or (row.score is None) != (row.dense_score is None)
                or len(row.errors) != len(VIEWS) * len(row.predictors) * len(observation_horizons)
                or (len(row.instantaneous_errors) != len(row.errors) or len(row.original_errors) != 2 * len(row.predictors) * len(row.original_observation_horizons)
                    or len(row.instantaneous_complete) != len(row.errors) or len(row.cumulative_complete) != len(row.errors))
                or any(type(full) is not bool for full in (*row.instantaneous_complete, *row.cumulative_complete))
                or row.score is not None and row.causal_prefix != source.causal_prefix
                or row.disposition in ("FINITE", "PARTIAL") and source.causal_disposition != "AVAILABLE"
                or type(row.origin_tick) is not int or row.origin_tick < 0
                or cutoff.clock_id != source.coordinate.clock_id or cutoff.coordinate != source.coordinate.physical_time(row.origin_tick)
                or (source.coordinate.primary_view.timestep != E4_PRIMARY_TIMESTEP
                    or source.coordinate.fine_view.timestep != Decimal('0.0005'))
                or row.origin_tick + observation_horizons[-1] > source.coordinate.total_ticks
                or any(row.origin_tick + horizon not in source.rule.lattice for horizon in HORIZONS)):
            raise PermissionError("E4 secondary join substitutes exact original case/source/group/coordinate or response clock")
        if row.score is None:
            expected_missing = ('UNKNOWN_CONTACT' if any(native.phase == 'responses' and native.disposition == 'UNKNOWN'
                for native in case.native) else 'UNAVAILABLE')
            if (row.disposition != expected_missing or row.causal_prefix is not None
                    or any(value is not None for value in (*row.errors, *row.instantaneous_errors, *row.original_errors))
                    or any((*row.instantaneous_complete, *row.cumulative_complete))):
                raise PermissionError('absent E4 case changes its actual unresolved native state or invents finite dense observations')
        checked = assessment.witness_pass and assessment.history_numerical_pass is True
        traces = {(trace.view, trace.sector): trace for trace in product.traces}
        for view in VIEWS:
            cells = []
            for horizon in observation_horizons:
                index = (VIEWS.index(view) * len(row.predictors) + row.predictors.index("FACTOR")) * len(observation_horizons) + observation_horizons.index(horizon)
                lower, complete = row.errors[index], row.cumulative_complete[index]
                error = lower if complete and row.disposition in ('FINITE', 'PARTIAL') else None
                cell = _dense_adequacy(horizon, lower, complete, normalized_tolerance, row.disposition)
                cells.append(cell)
                base = {"root_id": source.root_id, "unit_id": source.group_id, "coordinate": row.coordinate,
                    "source": source.identity, "view": view, "horizon": horizon, "response_origin_tick": row.origin_tick,
                    "absolute_tick": row.origin_tick + horizon}
                details.append({**base, "actual_error": error, "observed_error_lower_bound": lower,
                    "cumulative_prefix_complete": complete, "classification": cell.classification,
                    "definitely_adequate": cell.definitely_adequate, "possibly_adequate": cell.possibly_adequate,
                    "source_disposition": cell.source_disposition})
                # Each account retains its own exact original endpoint menu.
                if horizon not in row.original_observation_horizons:
                    continue
                for method, values in row.forecasts:
                    log_point = (values[VIEWS.index(view) * 29 + observation_horizons.index(horizon)]
                        if row.target_contract == 'MATCHED_FACTOR58'
                        else values[PREDICTORS.index('FACTOR') * 3 + HORIZONS.index(horizon)])
                    predicted = original_point_units(log_point)
                    original_index = ((VIEWS.index(view) * len(row.predictors) + row.predictors.index('FACTOR'))
                        * len(row.original_observation_horizons) + row.original_observation_horizons.index(horizon))
                    original_error = row.original_errors[original_index]
                    detection_cell = adequacy_cell(horizon, original_error, normalized_tolerance=normalized_tolerance,
                        disposition='CROSSCHECKED_FINITE' if original_error is not None else row.disposition,
                        known_nonuse=row.disposition == 'NO_ORIGIN')
                    detections.append({**base, "method": method, "raw_log_prediction": log_point,
                        "predicted_error": predicted, "decision": failure_detection(detection_cell, predicted, normalized_tolerance)})
                for sector in source.rule.sectors:
                    trace = traces.get((view, sector))
                    observation = None if trace is None else next((value for value in trace.observations if value.tick == row.origin_tick + horizon), None)
                    moving = None if not checked or observation is None else _moving_state(observation, source.rule)
                    fixed = (None if moving is None or observation.origin_angle_degrees is None else
                        moving and observation.origin_angle_degrees <= source.rule.origin_angle_maximum_degrees)
                    joins.append({**base, "sector": sector, "structural_assessment": assessment.identity,
                        "structural_usable": checked, "observation": observation,
                        "endpoint_moving_state": moving, "endpoint_origin_fixed_state": fixed,
                        "moving_survival": _survival(None if trace is None or not checked else trace.moving_lifetime, row.origin_tick + horizon, row.origin_tick),
                        "origin_fixed_survival": _survival(None if trace is None or not checked else trace.origin_fixed_lifetime, row.origin_tick + horizon, row.origin_tick),
                        "functional_classification": cell.classification})
            functional = _grid_lifetime(cells)
            lifetimes.append({"root_id": source.root_id, "unit_id": source.group_id, "coordinate": row.coordinate,
                "view": view, "response_origin_tick": row.origin_tick, **functional,
                "structural": tuple({"sector": sector,
                    "moving": None if traces.get((view, sector)) is None else traces[view, sector].moving_lifetime,
                    "origin_fixed": None if traces.get((view, sector)) is None else traces[view, sector].origin_fixed_lifetime,
                    "moving_failure_order": _failure_order(None if not checked or traces.get((view, sector)) is None else traces[view, sector].moving_lifetime, functional, row.origin_tick),
                    "origin_fixed_failure_order": _failure_order(None if not checked or traces.get((view, sector)) is None else traces[view, sector].origin_fixed_lifetime, functional, row.origin_tick)}
                    for sector in source.rule.sectors)})
    census = []
    for coordinate in sorted({row.coordinate for row in functional_rows}, key=lambda value: value.object_id):
        roots = {row.root_id for row in functional_rows if row.coordinate == coordinate}
        units = tuple(sorted({row.group_id for row in functional_rows if row.coordinate == coordinate}))
        for view in VIEWS:
            selected = tuple(row for row in lifetimes if row["root_id"] in roots and row["view"] == view)
            patterns = Counter((row["last_definite_pass"], row["first_possible_failure"], row["first_definite_failure"], row["first_nonuse"], row["censoring_status"]) for row in selected)
            census.append({"coordinate": coordinate, "view": view, "assigned_independent_groups": len(units), "groups": units,
                "assigned_cases": len(roots), "lifetime_patterns": tuple({"pattern": key, "count": value} for key, value in sorted(patterns.items(), key=repr)),
                "degenerate_complete_lifetime_labels": len(patterns) == 1 and all(row["censoring_status"] in ("FIRST_FAILURE_ON_LATTICE", "RIGHT_CENSORED_AT_LAST_HORIZON") for row in selected)})
    result = {"scope": "SECONDARY_ORIGINAL_FACTOR_STRUCTURAL_FUNCTIONAL_RETAINED_JOIN",
        "criterion_origin": target_origin, "normalized_tolerance": normalized_tolerance, "target_lineage_scope": lineage_scope,
        "description": "FACTOR", "horizons": observation_horizons, "primary_continuous_error_criterion": "UNCHANGED",
        "structural_origin": "ORIGINAL_FIRST_CAUSAL_ADMISSION_NOT_REANCHORED_TO_RESPONSE_CUTOFF",
        "functional_origin": "ACTUAL_ORIGINAL_RESPONSE_CUTOFF", "failure_order_scope": "OBSERVED_INTERVAL_ORDER_ONLY",
        "standing": "SECONDARY_DESCRIPTIVE_FINITE_DT_NO_NEW_QUALIFICATION_OR_CAUSAL_LIFETIME_CLAIM",
        "sampling_warrant": "NOT_ESTABLISHED_BY_THIS_READOUT", "assigned_independent_groups": len(scope.programme.group_ids),
        "assigned_cases": len(scope.sources),
        "assigned_case_products": tuple({"original_case": row.original_case, "source": row.source,
            "root_id": row.root_id, "unit_id": row.group_id, "original_score": row.score, "dense_score": row.dense_score,
            "functional_disposition": row.disposition, "case_disposition": case.disposition,
            "case_numerical_disposition": case.numerical_disposition, "case_score_disposition": case.score_disposition,
            "reason_codes": case.reason_codes, "native": case.native, "ordinary_receipts": case.ordinary_receipts}
            for row, case in ((by_root[case.root_id], case) for case in scope.original_cases)),
        "nested_views_per_case": 2, "nested_sectors_per_view": len(scope.sources[0].rule.sectors),
        "nested_panels_per_case": 2, "nested_actions_per_panel": 4, "nested_receivers_per_cell": 48,
        "adequacy": tuple(details), "useful_lifetimes": tuple(lifetimes), "failure_detection": tuple(detections),
        "structural_functional_horizons": tuple(joins), "lifetime_pattern_census": tuple(census)}
    result["scope"] = "SECONDARY_E4_DENSE_FACTOR_STRUCTURAL_FUNCTIONAL_RETAINED_JOIN"
    comparisons, sensitivity, other = [], [], []
    tolerances = (E4_HEADLINE_TOLERANCE, *E4_SENSITIVITY_TOLERANCES)
    for row in functional_rows:
        for predictor in row.predictors:
            for tolerance in tolerances:
                paired = tuple(_dense_description(row, view, predictor, tolerance) for view in VIEWS)
                if predictor == 'FACTOR' and tolerance != E4_HEADLINE_TOLERANCE:
                    sensitivity.extend(paired)
                elif predictor != 'FACTOR':
                    other.extend(paired)
                classifications = tuple(value['classifications'] for value in paired)
                comparisons.append({'root_id': row.root_id, 'unit_id': row.group_id,
                    'description': predictor, 'normalized_tolerance': tolerance,
                    'threshold_disagreement_horizons': tuple(horizon for horizon, left, right in zip(
                        observation_horizons, *classifications, strict=True)
                        if (left in ('FINITE_ADEQUATE', 'UNRESOLVED_ADEQUATE') and right in ('FINITE_INADEQUATE', 'UNRESOLVED_INADEQUATE'))
                        or (right in ('FINITE_ADEQUATE', 'UNRESOLVED_ADEQUATE') and left in ('FINITE_INADEQUATE', 'UNRESOLVED_INADEQUATE'))),
                    'unresolved_horizons': tuple(horizon for horizon, left, right in zip(
                        observation_horizons, *classifications, strict=True)
                        if left == 'UNRESOLVED' or right == 'UNRESOLVED'),
                    'known_nonuse_horizons': tuple(horizon for horizon, left, right in zip(
                        observation_horizons, *classifications, strict=True) if 'KNOWN_NONUSE' in (left, right)),
                    'view_lifetimes': tuple((value['view'], value['tau_epsilon_grid'], value['censoring_status']) for value in paired)})
    result.update({'headline_tolerance': E4_HEADLINE_TOLERANCE,
        'sensitivity_tolerances': E4_SENSITIVITY_TOLERANCES,
        'primary_timestep': E4_PRIMARY_TIMESTEP,
        'physical_times': tuple(Decimal('0.' + str(horizon).zfill(3)) for horizon in observation_horizons),
        'structural_observation_horizons': HORIZONS,
        'accuracy_convention': 'PRESPECIFIED_NOMINAL_ACTUATOR_SCALE_NOT_OBSERVED_RESPONSE_RELATIVE_ERROR',
        'normalization': 'MAX_POSITION_MOMENTUM_HS24_ERROR_OVER_NOMINAL_ACTUATOR_SCALE',
        'cumulative_rule': 'WORST_DECLARED_ACTION_PANEL_AND_SAMPLED_PREFIX_STRICT_GREATER_THAN_TOLERANCE',
        'continuum_error_bound': 'NOT_ESTABLISHED_BY_PRIMARY_FINE_AGREEMENT',
        'sensitivity_useful_lifetimes': tuple(sensitivity), 'other_description_readouts': tuple(other),
        'numerical_view_comparisons': tuple(comparisons),
        'headline_error_curves': tuple(_dense_description(row, view, 'FACTOR', E4_HEADLINE_TOLERANCE)
            for row in functional_rows for view in VIEWS)})
    return canonical_value(result)
