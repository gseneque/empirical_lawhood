# SPDX-License-Identifier: MPL-2.0
"""Secondary original-criterion diagnostics from already authenticated E3 products.

No criterion search, fit, calibration, qualification or acquisition occurs here.
The primary continuous-error products retain their original arithmetic/bytes.
"""
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as source_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_value

from . import experiment_methods as endpoints
from .e3_numerical_methods import original_units
from .protected_experiment_methods import ProtectedE3Forecast, ProtectedE3PairedOutcome
from .configured_protected_methods import ConfiguredProtectedE3Forecast, ConfiguredProtectedE3PairedOutcome
from .response_consumer import response_adequacy_values, response_lifetime_values
from .records import SIGNS

HORIZONS = (16, 64, 128)


def _pin(record):
    return ObjectIdentity.from_record(record.record_id, record)


@dataclass(frozen=True, slots=True)
class _Cell:
    horizon_step: int
    classification: str
    definitely_adequate: bool
    possibly_adequate: bool
    source_disposition: str


def _checked_pair(specification, allocation, role, outcome, forecast, score):
    kinds = {ProtectedE3PairedOutcome: ProtectedE3Forecast,
        ConfiguredProtectedE3PairedOutcome: ConfiguredProtectedE3Forecast}
    if (type(outcome) not in kinds or type(forecast) is not kinds[type(outcome)]
            or type(score) is not ScheduledResponseScore):
        raise TypeError("E3 secondary read requires exact original outcome/forecast/score owners")
    for value in (outcome, forecast, score): value.__post_init__()
    public = outcome.feature.public_source
    if (forecast.specification != specification.identity or forecast.allocation != allocation.identity
            or forecast.role != role or outcome.forecast != _pin(forecast) or outcome.feature != forecast.feature
            or score.error_forecast != _pin(forecast) or outcome.original_score != source_identity(score)
            or score.source != public.source or score.causal_prefix != outcome.feature.origin
            or (score.root_id, score.independent_group_id) != (public.root.root_id, outcome.unit_id)
            or score.role != ("CALIBRATION" if role == "calibration" else "CONFIRMATION")
            or outcome.original_cells_sha256 != sha256(canonical_json_bytes(score.cells)).hexdigest()
            or tuple(row.view_id for row in outcome.views) != ("fine", "primary")):
        raise PermissionError("E3 secondary read changes actual consumed source/root/forecast/score ancestry")
    panels = {row.object_id for row in outcome.panels}
    actions = {cell.action_id for cell in score.cells}
    matched = getattr(specification.measurement, 'is_matched', False)
    horizons = specification.measurement.horizons if matched else HORIZONS
    expected = {(view, panel, action, description, horizon)
        for view in ("FINE", "PRIMARY") for panel in panels for action in actions
        for description in specification.measurement.descriptions for horizon in horizons}
    if (len(panels) != 2 or len(actions) != 4 or specification.measurement.horizons != horizons
            or matched != (score.dense is not None)
            or len(score.cells) != len(expected) or {cell.key for cell in score.cells} != expected):
        raise PermissionError("E3 secondary read loses complete original nested paired response cells")
    for cell in score.cells:
        cell.__post_init__()
        if matched:
            continue
        vectors = cell.actual_odd_responses, cell.signed_errors, cell.absolute_errors, cell.relative_errors
        if (any(values is not None and len(values) != specification.measurement.receiver_count for values in vectors)
                or cell.normalized_error is not None and any(values is None for values in vectors)):
            raise PermissionError("E3 secondary read loses complete original receiver vectors")
    if score.disposition in ("FINITE", "PARTIAL"):
        expected_controls = {"control.scheduled." + score.root_id + "." + view.lower() + "." + panel + "." + action + "." + sign:
            128 if view == "PRIMARY" else 256
            for view in ("FINE", "PRIMARY") for panel in panels for action in actions for sign in (value.lower() for value in SIGNS)}
        if (len(score.controls) != len(expected_controls) or {row.control_id for row in score.controls} != set(expected_controls)
                or any(row.denominator_steps != expected_controls[row.control_id] or row.denominator_real_coordinates != 192 for row in score.controls)):
            raise PermissionError("E3 secondary read loses complete original full192 native control denominators")
        for row in score.controls: row.__post_init__()
    numerical = ("SATISFIED" if score.numerical_pass and score.disposition in ("FINITE", "PARTIAL")
        else "VIOLATED" if score.disposition == "NATIVE_CROSSCHECK_FAILED" else "UNEVALUABLE")
    if outcome.numerical_disposition != numerical:
        raise PermissionError("E3 secondary read changes original numerical nonuse")
    for view in outcome.views:
        expected_errors = []
        for description, horizon in (tuple(('FACTOR', tick) for tick in horizons) if matched else endpoints.ENDPOINTS):
            cells = tuple(cell for cell in score.cells if cell.view.lower() == view.view_id
                and cell.predictor == description and cell.horizon_tick <= horizon)
            finite = score.numerical_pass and score.disposition in ("FINITE", "PARTIAL") and all(cell.normalized_error is not None for cell in cells)
            expected_errors.append(max(cell.normalized_error for cell in cells) if finite else None)
        if view.errors != tuple(expected_errors):
            raise PermissionError("E3 secondary read changes actual cumulative paired response errors")


def _observed_cell(horizon, error, *, score, feature, tag, normalized_tolerance):
    if score.disposition == "NO_ORIGIN" or feature.disposition == "NO_CAUSAL_ORIGIN":
        kind, lower, upper, disposition = "KNOWN_NONUSE_INFINITY", Decimal(0), None, "NO_CAUSAL_ORIGIN"
    elif error is not None:
        kind, lower, upper, disposition = "FINITE_POINT", error, error, "CROSSCHECKED_FINITE"
    else:
        kind, lower, upper = "UNRESOLVED_INTERVAL", Decimal(0), None
        disposition = ("UNKNOWN_CONTACT" if "UNKNOWN_CONTACT" in (*score.reason_codes, tag)
            else "UNAVAILABLE" if feature.disposition != "AVAILABLE" or tag == "UNAVAILABLE" else tag)
    classification, definite, possible = response_adequacy_values(kind, lower, upper, normalized_tolerance)
    return _Cell(horizon, classification, definite, possible, disposition)


def _detection(cell, predicted, normalized_tolerance):
    if cell.classification == "KNOWN_NONUSE": return "KNOWN_NONUSE"
    if cell.classification not in ("FINITE_ADEQUATE", "FINITE_INADEQUATE"): return "ACTUAL_UNRESOLVED"
    if predicted is None: return "FORECAST_NONUSE"
    failed = cell.classification == "FINITE_INADEQUATE"
    flagged = predicted > normalized_tolerance
    return ("DETECTED_FAILURE" if flagged else "MISSED_FAILURE") if failed else ("FALSE_ALARM" if flagged else "CORRECT_PASS")


def secondary_response_projection(specification, allocation, rows, *, normalized_tolerance, target_origin):
    """Complete CAL/CONF finite-roster diagnostics; views never add independent units.

    rows are exact (allocated role, paired outcome, original forecast, score).
    The public reader authenticates their original producer/receipt edges first.
    """
    if type(normalized_tolerance) is not Decimal or not normalized_tolerance.is_finite() or normalized_tolerance <= 0:
        raise ValueError("E3 secondary read requires its actual positive frozen target tolerance")
    if type(target_origin) is not ObjectIdentity:
        raise TypeError("E3 secondary read requires the exact authenticated target origin")
    target_origin.__post_init__()
    expected = {(role, unit) for role in ("calibration", "evaluation") for unit in allocation.unit_ids(role)}
    details, lifetimes, detections, seen = [], [], [], set()
    # The API streams one decoded root score at a time. Only these small
    # diagnostics survive the current product lifetime, not another raw census.
    for role, outcome, forecast, score in rows:
        _checked_pair(specification, allocation, role, outcome, forecast, score)
        key = role, outcome.unit_id
        if key not in expected or key in seen:
            raise PermissionError("E3 secondary read drops or duplicates an assigned original independent unit")
        seen.add(key)
        root_id, unit = score.root_id, outcome.unit_id
        for view in outcome.views:
            cells = []
            for horizon in HORIZONS:
                index = endpoints.ENDPOINTS.index(("FACTOR", horizon))
                error, tag = view.errors[index], view.dispositions[index]
                cell = _observed_cell(horizon, error, score=score, feature=outcome.feature, tag=tag, normalized_tolerance=normalized_tolerance)
                cells.append(cell)
                details.append({"role": role, "root_id": root_id, "unit_id": unit, "view": view.view_id,
                    "horizon": horizon, "actual_error": error, "classification": cell.classification,
                    "definitely_adequate": cell.definitely_adequate, "possibly_adequate": cell.possibly_adequate,
                    "source_disposition": cell.source_disposition, "original_outcome_tag": tag})
                for method, values in forecast.log_points:
                    predicted = None if values[index] is None else original_units(values[index])
                    detections.append({"role": role, "root_id": root_id, "unit_id": unit, "view": view.view_id,
                        "horizon": horizon, "method": method, "predicted_error": predicted,
                        "decision": _detection(cell, predicted, normalized_tolerance)})
            survival, possible, definite, nonuse, status, dispositions = response_lifetime_values(tuple(cells))
            lifetimes.append({"role": role, "root_id": root_id, "unit_id": unit, "view": view.view_id,
                "last_definite_pass": survival, "first_possible_failure": possible,
                "first_definite_failure": definite, "first_nonuse": nonuse, "censoring_status": status,
                "source_dispositions": dispositions})
    if seen != expected:
        raise PermissionError("E3 secondary read drops or duplicates an assigned original independent unit")
    details.sort(key=lambda row: (row["role"], row["unit_id"], row["view"], row["horizon"]))
    lifetimes.sort(key=lambda row: (row["role"], row["unit_id"], row["view"]))
    detections.sort(key=lambda row: (row["role"], row["unit_id"], row["view"], row["horizon"], row["method"]))
    histograms = []
    for role in ("calibration", "evaluation"):
        for view in ("fine", "primary"):
            selected = tuple(row for row in lifetimes if row["role"] == role and row["view"] == view)
            patterns = Counter((row["last_definite_pass"], row["first_possible_failure"], row["first_definite_failure"],
                row["first_nonuse"], row["censoring_status"]) for row in selected)
            unresolved = sum(row["censoring_status"] in ("UNKNOWN_CONTACT", "UNAVAILABLE", "UNRESOLVED") for row in selected)
            nonuse = sum(row["censoring_status"] == "KNOWN_NONUSE" for row in selected)
            histograms.append({"role": role, "view": view, "assigned_units": len(selected), "unresolved_units": unresolved, "known_nonuse_units": nonuse,
                "distinct_lifetime_patterns": len(patterns), "degenerate_complete_lifetime_labels": len(patterns) == 1 and unresolved == nonuse == 0,
                "patterns": tuple({"last_definite_pass": key[0], "first_possible_failure": key[1],
                    "first_definite_failure": key[2], "first_nonuse": key[3], "censoring_status": key[4], "count": count}
                    for key, count in sorted(patterns.items(), key=lambda item: repr(item[0])))})
    return canonical_value({"scope": "SECONDARY_ORIGINAL_FACTOR_ADEQUACY_ON_RETAINED_HORIZON_LATTICE",
        "normalized_tolerance": normalized_tolerance, "criterion_origin": target_origin,
        "description": "FACTOR", "horizons": HORIZONS, "primary_continuous_error_criterion": "UNCHANGED",
        "standing": "SECONDARY_DESCRIPTIVE_FINITE_DT_READOUT_NO_NEW_QUALIFICATION",
        "lifetime_inference_scope": "RETAINED_HORIZON_LATTICE_ONLY_NO_NEW_DISCRIMINATION_TEST",
        "sampling_warrant": "NOT_ESTABLISHED_BY_THIS_READOUT",
        "counts": {role: {"assigned_independent_units": len(allocation.unit_ids(role)), "nested_views_per_unit": 2,
            "nested_panels_per_unit": 2, "nested_actions_per_panel": 4, "nested_receivers_per_cell": specification.measurement.receiver_count,
            "nested_horizons": HORIZONS, "units": allocation.unit_ids(role)} for role in ("calibration", "evaluation")},
        "adequacy": tuple(details), "useful_lifetimes": tuple(lifetimes), "failure_detection": tuple(detections),
        "lifetime_pattern_census": tuple(histograms)})
