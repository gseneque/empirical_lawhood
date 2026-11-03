# SPDX-License-Identifier: MPL-2.0
"""Pure original-E3 bound transport challenges; never fit or calibrate E6."""
from collections import Counter
from collections.abc import Mapping
from decimal import Decimal, localcontext
from fractions import Fraction

from empirical_lawhood.adapters.methods.matrix_factor_response.e3_numerical_methods import log_error, original_units
from empirical_lawhood.adapters.methods.matrix_factor_response.retained_response_readout import adequacy_cell, failure_detection, lifetime_readout
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation, identity as scheduled_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase
from empirical_lawhood.runtime.experimental_statistics import binomial_upper_tail

from .e6_transport_records import (
    METHODS, TRANSFER_ROLES, MATCHED_CALIBRATION_METHOD, MATCHED_ADMISSION_RULE, MATCHED_METHODS, MATCHED_STANDING,
    MatrixE6EmpiricalTransportAssessment, MatrixE6EmpiricalTransportPolicy,
    MatrixE6FrozenCalibrationProjection, MatrixE6TransportComparison, MatrixE6TransportDecision,
    MatrixE6TransportEndpointOutcome, MatrixE6TransportLifetime, MatrixE6TransportManifest, MatrixE6TransportRootOutcome,
)
from .functional_case_reduction import _prepared_score_views
from .prepared_point import MatrixPreparedPublicSource
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_prefix import identity
from .prepared_response_science import MatrixPreparedResponseReadout
from .selected_package import selected_frozen_package_types
from .selected_point import MatrixSelectedPointForecast, forecast_selected_point
from .selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme
from .selected_public import calibration_identity, package_identity
from .records import MatrixFunctionalCriterion


def _endpoint_order(measurement):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import ConfiguredE3Measurement
    if type(measurement) is ConfiguredE3Measurement:
        return measurement.forecast_endpoints
    return tuple((description, horizon) for description in measurement.descriptions for horizon in measurement.horizons)


def validate_e6_transport_criterion(criterion, candidate):
    """Reject incompatible expanded-E6 selections before publication effects."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import FAMILY_IDS
    if type(criterion) is not MatrixFunctionalCriterion or type(candidate) not in (
            MatrixResponseErrorSpecification, ConfiguredProtectedE3Specification):
        raise TypeError("E6 criterion requires its actual original selected candidate and typed rule")
    criterion.__post_init__()
    candidate.__post_init__()
    assessment = candidate.assessment
    family = getattr(assessment, "comparison_ids", FAMILY_IDS)
    if (criterion.family_slots != family or criterion.alpha != assessment.alpha
            or criterion.is_matched != getattr(candidate.measurement, 'is_matched', False)
            or criterion.null_probability != assessment.null_probability
            or Fraction(criterion.familywise_alpha_numerator, criterion.familywise_alpha_denominator) != assessment.alpha * len(family)
            or (criterion.predictor, criterion.horizon_tick) not in _endpoint_order(candidate.measurement)
            or candidate.calibration_target_view != "MAX_PAIRED_VIEWS"
            or max(criterion.minimum_usable_groups, criterion.minimum_admitted_groups) >
                min(candidate.population(role).expected_units for role in TRANSFER_ROLES)):
        raise ValueError("E6 criterion changes original family, alpha, null, endpoint, paired target or usable census")


def _availability(value):
    if (type(value) is not tuple or len(value) != 2 or type(value[0]) is not ObjectIdentity
            or type(value[1]) is not AvailabilitySpec):
        raise TypeError("E6 policy requires exact published availability identity and original record")
    pin, record = value
    record.__post_init__()
    if (ObjectIdentity.from_record(pin.object_id, record) != pin or record.phase is not CausalPhase.PREPARATION
            or record.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or record.available_at is None or record.available_at < 0):
        raise ValueError("E6 policy changes its actual pre-TRAIN blind availability")
    return pin


def build_e6_transport_policy(*, record_id, candidate_specification, future_reservation,
        future_response_selections, availability, criterion):
    """Project authenticated pre-TRAIN declarations into a seedless frozen rule.

    Callers authenticate publications. This method checks the complete exact
    reservation/selector join and copies no stream keys, panels or outcomes.
    """
    candidate_specification.__post_init__()
    validate_e6_transport_criterion(criterion, candidate_specification)
    if type(future_reservation) is not ScheduledReservation:
        raise TypeError("E6 policy requires its exact original future reservation")
    future_reservation.__post_init__()
    roles = ("CALIBRATION", "EVALUATION", *TRANSFER_ROLES)
    if (type(future_response_selections) is not tuple
            or tuple(role for role, _ in future_response_selections) != roles
            or any(type(value) is not ScheduledResponseSelection for _, value in future_response_selections)):
        raise ValueError("E6 policy needs all four exact original future role selections")
    measurement = candidate_specification.measurement
    endpoints = _endpoint_order(measurement)
    allocation = future_reservation.allocation
    originals = {row.root.root_id: row for row in allocation.roots}
    assigned_roots, assigned_groups, assigned_sources, roster = set(), set(), set(), []
    role_coordinates = dict(getattr(candidate_specification, "role_coordinates", ()))
    role_kinds = {"CALIBRATION": MatrixProgrammeRole.CALIBRATION, "EVALUATION": MatrixProgrammeRole.CONFIRMATION,
        "TRANSFER_NEARBY": MatrixProgrammeRole.WITHHELD_TRANSFER, "TRANSFER_SHIFTED": MatrixProgrammeRole.WITHHELD_TRANSFER}
    for role, selection in future_response_selections:
        selection.validate_allocation(allocation)
        population = candidate_specification.population(role)
        groups = {protocol.public_source.root.independent_group_id for protocol in selection.protocols}
        if (len(selection.protocols) != len(groups)
                or len(groups) != population.expected_units
                or population.unit_ids is not None and groups != set(population.unit_ids)
                or assigned_groups.intersection(groups)
                or {group for group, _ in selection.panels} != groups):
            raise ValueError("E6 policy drops, overlaps or substitutes original independent role roots")
        assigned_groups.update(groups)
        for protocol in selection.protocols:
            public = protocol.public_source
            root = originals.get(public.root.root_id)
            if (root is None or public.root != root.root or public.root.role is not role_kinds[role]
                    or public.root.root_id in assigned_roots or public.source in assigned_sources
                    or public.reservation != scheduled_identity(future_reservation) or public.allocation != scheduled_identity(allocation)
                    or role_coordinates and coordinate_identity(public.coordinate) != role_coordinates[role]
                    or protocol.horizon_steps != measurement.horizons or protocol.receiver_count != measurement.receiver_count
                    or public.policy.cutoff_tick != measurement.origin_tick
                    or public.coordinate.primary_view.timestep != measurement.primary_timestep
                    or public.coordinate.fine_view.timestep != measurement.fine_timestep):
                raise ValueError("E6 policy substitutes original reserved root/source, clock or complete endpoint assay")
            assigned_roots.add(public.root.root_id)
            assigned_sources.add(public.source)
            if role in TRANSFER_ROLES:
                roster.append((role, public.root.regime_id, public.root.root_id, public.root.independent_group_id, public.source))
    if assigned_roots != set(originals):
        raise ValueError("E6 policy omits an original reserved future root")
    return MatrixE6EmpiricalTransportPolicy(record_id, candidate_specification.identity, scheduled_identity(future_reservation),
        tuple((role, selection.identity) for role, selection in future_response_selections), _availability(availability),
        criterion, endpoints, candidate_specification.calibration_alpha, tuple(sorted(roster, key=lambda row: (row[0], row[2]))),
        **({'calibration_method': MATCHED_CALIBRATION_METHOD, 'admission_rule': MATCHED_ADMISSION_RULE,
            'comparator_methods': MATCHED_METHODS, 'standing': MATCHED_STANDING} if criterion.is_matched else {}))


def validate_e6_transport_policy(policy, *, candidate_specification, future_reservation,
        future_response_selections, availability, criterion=None):
    if type(policy) is not MatrixE6EmpiricalTransportPolicy:
        raise TypeError("E6 requires its actual frozen empirical transport policy")
    expected = build_e6_transport_policy(record_id=policy.record_id, candidate_specification=candidate_specification,
        future_reservation=future_reservation, future_response_selections=future_response_selections,
        availability=availability, criterion=policy.criterion if criterion is None else criterion)
    if policy != expected:
        raise ValueError("E6 policy changes exact pre-TRAIN original declarations")


def validate_e6_transport_scope(policy, programme):
    """Join later prepared sources to every original pre-TRAIN seedless row."""
    if type(policy) is not MatrixE6EmpiricalTransportPolicy or type(programme) not in (
            MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme):
        raise TypeError("E6 transport scope needs its exact original selected programme and policy")
    policy.__post_init__()
    programme.__post_init__()
    package = programme.point_design.package
    validate_e6_transport_criterion(policy.criterion, package.specification)
    if (programme.phase != "E6_TRANSFER" or programme.nomination is not None
            or programme.criterion != policy.criterion or package.specification.identity != policy.candidate_specification
            or scheduled_identity(programme.sources.closure.reservation) != policy.future_reservation
            or package.prefit.reservation != policy.future_reservation
            or _endpoint_order(package.specification.measurement) != policy.endpoint_order
            or package.specification.calibration_alpha != policy.calibration_alpha):
        raise ValueError("E6 transport changes frozen criterion, original candidate/reservation or calibration target")
    by_group = {row[3]: row for row in policy.regime_roster}
    actual = []
    for arm, source in programme.sources.source_arms():
        original = source.original
        row = by_group.get(original.root.independent_group_id)
        if row is None or arm != programme.sources.hold_arm_id:
            raise ValueError("E6 transport introduces an unassigned root or non-HOLD preparation")
        actual.append((row[0], original.root.regime_id, original.root.root_id,
            original.root.independent_group_id, original.source))
    if tuple(sorted(actual, key=lambda row: (row[0], row[2]))) != policy.regime_roster:
        raise ValueError("E6 transport thins or substitutes the complete original root/source/regime roster")
    for role in TRANSFER_ROLES:
        groups = tuple(sorted(row[3] for row in policy.regime_roster if row[0] == role))
        if groups != package.allocation.unit_ids(role.lower()) or len(groups) != programme.point_design.expected_groups:
            raise ValueError("E6 transport changes its exact original separate reserved role census")


def project_e6_frozen_calibration(policy, package, *, record_id):
    """Copy only an actual checked ORIGINAL_E3 radius, never any E6 outcome."""
    if type(policy) is not MatrixE6EmpiricalTransportPolicy or type(package) not in selected_frozen_package_types():
        raise TypeError("E6 radius projection requires the complete actual original frozen package")
    policy.__post_init__()
    package.__post_init__()
    if (package.specification.identity != policy.candidate_specification or package.prefit.reservation != policy.future_reservation
            or package.specification.calibration_alpha != policy.calibration_alpha
            or _endpoint_order(package.specification.measurement) != policy.endpoint_order):
        raise ValueError("E6 radius projection changes original pre-TRAIN candidate or calibration scope")
    calibration = package.calibration
    return MatrixE6FrozenCalibrationProjection(record_id, policy.identity, package.identity, package.specification.identity,
        package.allocation.identity, identity(package.models), identity(package.model_freeze), identity(calibration),
        identity(package.calibrated_freeze), package.allocation.unit_ids("calibration"), policy.calibration_alpha,
        calibration.rank, "INFINITE" if calibration.radius is None else "FINITE", calibration.radius, policy.endpoint_order)


def validate_e6_calibration_projection(projection, policy, package):
    if type(projection) is not MatrixE6FrozenCalibrationProjection or projection != project_e6_frozen_calibration(
            policy, package, record_id=projection.record_id):
        raise ValueError("E6 substitutes its exact original finite/infinite radius or frozen ancestry")


def validate_e6_public_calibration_projection(projection, policy, package):
    """Check seedless joins only; the parent independently reopens original CAL."""
    projection.__post_init__()
    policy.__post_init__()
    if (projection.policy != policy.identity or projection.package != package_identity(package)
            or projection.specification != package.specification.identity or projection.allocation != package.allocation.identity
            or projection.models != identity(package.models) or projection.model_freeze != identity(package.model_freeze)
            or projection.calibration != calibration_identity(package)
            or projection.calibrated_freeze != identity(package.calibrated_freeze)
            or projection.calibration_unit_ids != package.allocation.unit_ids("calibration")
            or projection.calibration_alpha != policy.calibration_alpha or projection.endpoint_order != policy.endpoint_order):
        raise ValueError("E6 seedless projection changes exact original package/CAL/freeze ancestry")


def decide_e6_transport(policy, projection, point, *, source, record_id):
    """Causal admission only: no native future, score, outcome or RNG operand."""
    if (type(policy) is not MatrixE6EmpiricalTransportPolicy or type(projection) is not MatrixE6FrozenCalibrationProjection
            or type(point) is not MatrixSelectedPointForecast or type(source) is not MatrixPreparedPublicSource):
        raise TypeError("E6 decision requires exact seedless policy, original radius and causal point")
    for value in (policy, projection, point, source):
        value.__post_init__()
    root = source.original.root
    rows = tuple(row for row in policy.regime_roster if row[2] == root.root_id)
    if (len(rows) != 1 or rows[0][1:] != (root.regime_id, root.root_id, root.independent_group_id, source.original.source)
            or point.feature.public_source != source or point.package != projection.package
            or point.original_calibration != projection.calibration or projection.policy != policy.identity
            or projection.specification != policy.candidate_specification or projection.endpoint_order != policy.endpoint_order
            or projection.calibration_alpha != policy.calibration_alpha):
        raise ValueError("E6 decision substitutes original source/root, point/prefix or frozen calibration")
    points = dict(point.log_points)["SPECTRAL_RIDGE"]
    if len(points) != len(policy.endpoint_order):
        raise ValueError("E6 decision drops original endpoint predictions")
    if projection.radius_kind == "FINITE":
        with localcontext() as context:
            context.prec = 50
            log_uppers = tuple(None if value is None else value + projection.radius for value in points)
            uppers = tuple(None if value is None else original_units(value) for value in log_uppers)
    else:
        log_uppers = uppers = (None,) * len(points)
    index = policy.endpoint_order.index((policy.criterion.predictor, policy.criterion.horizon_tick))
    eligible = point.feature.disposition == "AVAILABLE" and all(value is not None for value in points)
    admitted = eligible and projection.radius_kind == "FINITE" and uppers[index] <= policy.criterion.normalized_error_maximum
    reasons = ["EMPIRICAL_BOUND_ADMISSION" if admitted else "INFINITE_ORIGINAL_RADIUS" if projection.radius_kind == "INFINITE"
        else "CAUSAL_FEATURE_OR_POINT_UNAVAILABLE" if not eligible else "PRIMARY_UPPER_EXCEEDS_FROZEN_TOLERANCE"]
    # Both declared E6 roles are outside the original CAL/EVAL population.
    # This orthogonal support flag never prevents an empirical challenge.
    reasons.append("OUTSIDE_ORIGINAL_CALIBRATED_POPULATION")
    return MatrixE6TransportDecision(record_id, policy.identity, projection.identity, source.source, source.original.source,
        root.root_id, root.independent_group_id, root.regime_id, identity(point), point.feature.prefix,
        source.original.coordinate.physical_time(source.original.policy.cutoff_tick), False, point.feature.disposition,
        projection.radius_kind, log_uppers, uppers, "ADMIT" if admitted else "ABSTAIN", tuple(sorted(reasons)))


def _endpoints(policy, decision, point, source, readout, protocol, panels):
    if readout is not None:
        _prepared_score_views(policy.criterion, source, readout, protocol=protocol, panels=panels)
    output = []
    for index, (description, horizon) in enumerate(policy.endpoint_order):
        errors, discrepancy = {}, False
        selected = {view: () if readout is None else tuple(sorted((row for row in readout.cells
            if row.view == view and row.predictor == description and row.horizon_tick <= horizon), key=lambda row: row.key[1:]))
            for view in ("PRIMARY", "FINE")}
        if readout is not None:
            discrepancy = any(left.normalized_error is not None and right.normalized_error is not None
                and abs(Fraction(left.normalized_error) - Fraction(right.normalized_error)) > Fraction(policy.criterion.paired_view_discrepancy_maximum)
                for left, right in zip(selected["PRIMARY"], selected["FINE"], strict=True))
        for view in ("PRIMARY", "FINE"):
            rows = selected[view]
            available = (readout is not None and readout.numerical_pass and readout.disposition in ("FINITE", "PARTIAL")
                and not discrepancy and rows and all(row.normalized_error is not None for row in rows))
            errors[view] = max(row.normalized_error for row in rows) if available else None
        paired = None if any(value is None for value in errors.values()) else max(errors.values())
        upper = None if decision is None else decision.error_uppers[index]
        coverage = ("UNAVAILABLE" if paired is None or decision is None else "VACUOUS" if decision.radius_kind == "INFINITE"
            else "UNAVAILABLE" if upper is None else "COVERED" if paired <= upper else "UNCOVERED")
        comparisons, detections = [], []
        menu = {} if point is None else dict(point.log_points)
        for method in METHODS:
            log_point = None if point is None else menu[method][index]
            predicted = None if log_point is None else original_units(log_point)
            values = []
            detection = []
            for view in ("PRIMARY", "FINE"):
                actual = errors[view]
                with localcontext() as context:
                    context.prec = 50
                    values.extend((None if actual is None or predicted is None else abs(actual - predicted),
                        None if actual is None or log_point is None else abs(log_error(actual) - log_point)))
                cell = adequacy_cell(horizon, actual, normalized_tolerance=policy.criterion.normalized_error_maximum,
                    disposition="MISSING" if readout is None else readout.disposition,
                    known_nonuse=readout is not None and readout.disposition == "NO_ORIGIN")
                detection.append(failure_detection(cell, predicted, policy.criterion.normalized_error_maximum))
            comparisons.append((method, *values))
            detections.append((method, *detection))
        output.append(MatrixE6TransportEndpointOutcome(description, horizon, errors["PRIMARY"], errors["FINE"], paired,
            upper, coverage, tuple(comparisons), tuple(detections)))
    return tuple(output)


def _lifetimes(policy, endpoints, point, readout):
    values = []
    menu = None if point is None else dict(point.log_points)
    for description in dict.fromkeys(description for description, _ in policy.endpoint_order):
        rows = tuple(row for row in endpoints if row.description == description)
        for view in ("PRIMARY", "FINE"):
            cells = tuple(adequacy_cell(row.horizon, row.primary_error if view == "PRIMARY" else row.fine_error,
                normalized_tolerance=policy.criterion.normalized_error_maximum,
                disposition="MISSING" if readout is None else readout.disposition,
                known_nonuse=readout is not None and readout.disposition == "NO_ORIGIN") for row in rows)
            actual = lifetime_readout(cells)
            predictions = []
            for method in METHODS:
                first = None
                if menu is not None:
                    for row in rows:
                        index = policy.endpoint_order.index((description, row.horizon))
                        predicted = menu[method][index]
                        if predicted is not None and original_units(predicted) > policy.criterion.normalized_error_maximum:
                            first = row.horizon
                            break
                predictions.append((method, first))
            values.append(MatrixE6TransportLifetime(description, view, actual["last_definite_pass"],
                actual["first_possible_failure"], actual["first_definite_failure"], actual["first_nonuse"],
                actual["censoring_status"], tuple(actual["source_dispositions"]), tuple(predictions)))
    return tuple(values)


def assess_e6_transport(programme, policy, projection, observations, decisions, *, result_id):
    """All assigned roots, fixed original bounds and two unchanged primary slots."""
    if type(programme) is MatrixSelectedProtectedProgramme:
        programme = MatrixSelectedPublicProgramme.from_programme(programme)
    validate_e6_transport_scope(policy, programme)
    validate_e6_public_calibration_projection(projection, policy, programme.point_design.package)
    if not isinstance(observations, Mapping) or not isinstance(decisions, Mapping):
        raise TypeError("E6 assessment requires original received products and separate causal decisions")
    cases = programme.roster.cases
    ids = {case.case_id for case in cases}
    if set(observations) - ids or set(decisions) - ids:
        raise ValueError("E6 assessment receives an unassigned root")
    sources = {"case." + source.source_id: source for _, source in programme.sources.source_arms()}
    outcomes, manifests = [], []
    for case in cases:
        source = sources[case.case_id]
        public = MatrixPreparedPublicSource.from_source(source)
        observation, decision = observations.get(case.case_id), decisions.get(case.case_id)
        point, mechanical, readout = (None, None, None) if observation is None else observation
        if decision is not None:
            decision.__post_init__()
            if (decision.source != source.identity or decision.policy != policy.identity
                    or decision.calibration_projection != projection.identity
                    or (decision.original_source, decision.root_id, decision.independent_group_id, decision.regime_id,
                        decision.cutoff) != (public.original.source, public.original.root.root_id,
                        public.original.root.independent_group_id, public.original.root.regime_id,
                        public.original.coordinate.physical_time(public.original.policy.cutoff_tick))):
                raise ValueError("E6 assessment substitutes a causal decision scope")
        if point is not None:
            if (point != forecast_selected_point(programme.point_design, point.feature, record_id=point.record_id)
                    or point.feature.public_source != public
                    or decision is not None and decision != decide_e6_transport(policy, projection, point, source=public, record_id=decision.record_id)):
                raise ValueError("E6 assessment substitutes actual frozen point or pre-future decision")
        protocol, panels = programme.protocol(source), dict(programme.panels)[case.unit_id]
        if mechanical is not None:
            if type(mechanical) is not MatrixPreparedMechanicalForecast:
                raise TypeError("E6 assessment requires the exact retained mechanical forecast")
            mechanical.__post_init__()
            mechanical.arrays.__post_init__()
            if (mechanical.source != source.identity or mechanical.arrays.source != source.identity
                    or mechanical.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                    or mechanical.arrays.original_protocol != mechanical.original_protocol
                    or mechanical.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)
                    or point is not None and mechanical.causal != point.feature.prefix):
                raise ValueError("E6 assessment substitutes retained mechanical source, protocol, model or causal ancestry")
        if readout is not None:
            if (type(readout) is not MatrixPreparedResponseReadout or mechanical is None or point is None
                    or mechanical.source != source.identity or mechanical.causal != point.feature.prefix
                    or readout.source != source.identity or readout.preparation != mechanical.arrays.preparation
                    or readout.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                    or readout.panels != tuple(panel.identity for panel in panels)
                    or readout.forecast is not None and readout.forecast != mechanical.arrays.identity):
                raise ValueError("E6 assessment changes exact original readout, panel or mechanical ancestry")
            readout.__post_init__()
        endpoints = _endpoints(policy, decision, point, source, readout, protocol, panels)
        primary = endpoints[policy.endpoint_order.index((policy.criterion.predictor, policy.criterion.horizon_tick))]
        state = ("MISSING" if readout is None else "NO_ORIGIN" if readout.disposition == "NO_ORIGIN"
            else "NUMERIC_FAILED" if readout.disposition == "NATIVE_CROSSCHECK_FAILED" else
            "FINITE" if readout.disposition == "FINITE" and primary.paired_error is not None else "OBSERVATION_FAILED")
        admission = "MISSING_DECISION" if decision is None else decision.admission
        functional = primary.paired_error is not None and primary.paired_error <= policy.criterion.normalized_error_maximum
        coverage = ("UNCOVERED" if any(row.coverage == "UNCOVERED" for row in endpoints) else
            "UNAVAILABLE" if any(row.coverage == "UNAVAILABLE" for row in endpoints) else
            "VACUOUS" if all(row.coverage == "VACUOUS" for row in endpoints) else "COVERED")
        delivered = admission == "ADMIT" and state == "FINITE"
        comparison_values = {row[0]: row[1:] for row in primary.comparisons}
        candidate_errors = comparison_values["SPECTRAL_RIDGE"]
        with localcontext() as context:
            context.prec = 50
            improvements = tuple((method, *(None if comparison_values[method][index] is None or candidate_errors[index] is None
                else comparison_values[method][index] - candidate_errors[index] for index in (0, 2))) for method in METHODS[:2])
        beats_both = (None if any(value is None for row in improvements for value in row[1:]) else
            all(value > programme.point_design.package.specification.assessment.improvement_margin for row in improvements for value in row[1:]))
        outcomes.append(MatrixE6TransportRootOutcome(case.case_id, case.unit_id, case.arm_id, public.original.root.regime_id,
            source.identity, None if decision is None else decision.identity, None if point is None else identity(point),
            None if mechanical is None else identity(mechanical), None if readout is None else identity(readout),
            False if decision is None else decision.original_support, admission, state, functional, delivered,
            delivered and functional, admission == "ADMIT" and primary.paired_error is not None and not functional,
            admission == "ADMIT" and primary.paired_error is None, coverage, endpoints, case.preparation_effort,
            tuple(sorted({"OUTSIDE_ORIGINAL_CALIBRATED_POPULATION", "EMPIRICAL_TRANSPORT_ONLY", state,
                *(("PRIMARY_OBSERVED_WITH_INCOMPLETE_MENU",) if state != "FINITE" and primary.paired_error is not None else ()),
                *( () if decision is not None else ("MISSING_CAUSAL_DECISION",))})),
            _lifetimes(policy, endpoints, point, readout), improvements, beats_both))
        manifests.append((case.case_id, None if point is None else identity(point),
            None if mechanical is None else identity(mechanical), None if readout is None else identity(readout),
            None if decision is None else decision.identity))
    outcomes = tuple(outcomes)
    manifest = MatrixE6TransportManifest(result_id + ".received", programme.identity, tuple(manifests))
    comparisons = []
    for role, slot in zip(TRANSFER_ROLES, ("e6.nearby", "e6.shifted"), strict=True):
        groups = tuple(sorted(row[3] for row in policy.regime_roster if row[0] == role))
        rows = tuple(row for row in outcomes if row.unit_id in groups)
        if tuple(sorted(row.unit_id for row in rows)) != groups:
            raise ValueError("E6 assessment drops a complete assigned original regime")
        success, usable, admitted = sum(row.joint_service for row in rows), sum(row.outcome_disposition == "FINITE" for row in rows), sum(row.admission == "ADMIT" for row in rows)
        false, unresolved = sum(row.false_admission_known for row in rows), sum(row.false_admission_unresolved for row in rows)
        probability = binomial_upper_tail(len(groups), success, policy.criterion.null_probability)
        met = (probability <= policy.criterion.alpha and usable >= policy.criterion.minimum_usable_groups
            and admitted >= policy.criterion.minimum_admitted_groups
            and false + unresolved <= policy.criterion.maximum_false_admissions)
        strata = Counter((row.original_support, row.admission, row.outcome_disposition) for row in rows)
        with localcontext() as context:
            context.prec = 80
            effort = None if any(row.preparation_effort is None for row in rows) else sum((row.preparation_effort for row in rows), Decimal(0))
        comparisons.append(MatrixE6TransportComparison(slot, rows[0].regime_id, groups, success, usable, admitted, false, unresolved,
            *(sum(row.whole_menu_coverage == value for row in rows) for value in ("COVERED", "UNCOVERED", "UNAVAILABLE", "VACUOUS")),
            sum(row.functional_reliable for row in rows), sum(row.delivered_service for row in rows),
            probability.numerator, probability.denominator, met,
            tuple((*key, value) for key, value in sorted(strata.items())), effort))
    result = MatrixE6EmpiricalTransportAssessment(result_id, programme.identity, policy.identity, projection.identity,
        package_identity(programme.point_design.package), programme.roster.identity, manifest.identity, policy.criterion,
        tuple(comparisons), outcomes, tuple(slot for slot in policy.criterion.family_slots if slot not in ("e6.nearby", "e6.shifted")))
    return manifest, result
