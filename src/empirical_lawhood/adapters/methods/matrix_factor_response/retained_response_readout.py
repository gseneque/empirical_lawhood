# SPDX-License-Identifier: MPL-2.0
"""Small descriptive projections over authenticated retained response values.

The caller supplies its frozen tolerance and actual finite roster. These pure
helpers reuse the original response-consumer arithmetic without a new criterion,
provider, hypothesis test, calibration or scientific qualification.
"""
from dataclasses import dataclass
from decimal import Decimal, localcontext

from .response_consumer import response_adequacy_values, response_lifetime_values


@dataclass(frozen=True, slots=True)
class AdequacyCell:
    horizon_step: int
    classification: str
    definitely_adequate: bool
    possibly_adequate: bool
    source_disposition: str


def adequacy_cell(horizon, error, *, normalized_tolerance, disposition, known_nonuse=False):
    if (type(normalized_tolerance) is not Decimal or not normalized_tolerance.is_finite()
            or normalized_tolerance < 0):
        raise ValueError("retained readout requires its supplied finite nonnegative frozen tolerance")
    kind, lower, upper = (("KNOWN_NONUSE_INFINITY", Decimal(0), None) if known_nonuse else
        ("FINITE_POINT", error, error) if error is not None else ("UNRESOLVED_INTERVAL", Decimal(0), None))
    classification, definite, possible = response_adequacy_values(kind, lower, upper, normalized_tolerance)
    return AdequacyCell(horizon, classification, definite, possible, disposition)


def failure_detection(cell, predicted, normalized_tolerance):
    if cell.classification == "KNOWN_NONUSE": return "KNOWN_NONUSE"
    if cell.classification not in ("FINITE_ADEQUATE", "FINITE_INADEQUATE"): return "ACTUAL_UNRESOLVED"
    if predicted is None: return "FORECAST_NONUSE"
    failed, flagged = cell.classification == "FINITE_INADEQUATE", predicted > normalized_tolerance
    return (("DETECTED_FAILURE" if flagged else "MISSED_FAILURE") if failed else
        ("FALSE_ALARM" if flagged else "CORRECT_PASS"))


def original_point_units(log_prediction):
    """Display a supplied point; actual adequacy always consumes raw score cells."""
    if log_prediction is None: return None
    with localcontext() as context:
        context.prec = 80
        return log_prediction.exp() - Decimal(1)


def lifetime_readout(cells):
    survival, possible, definite, nonuse, status, dispositions = response_lifetime_values(tuple(cells))
    return {"last_definite_pass": survival, "first_possible_failure": possible,
        "first_definite_failure": definite, "first_nonuse": nonuse,
        "censoring_status": status, "source_dispositions": dispositions}
