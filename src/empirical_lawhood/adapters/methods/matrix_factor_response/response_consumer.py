# SPDX-License-Identifier: MPL-2.0
"""Finite-grid adequacy and useful-horizon arithmetic shared by current readers."""

from fractions import Fraction


def response_lifetime_values(cells):
    """Original finite-lattice interval/nonuse mathematics, without population IDs."""
    survival = None
    for cell in cells:
        if not cell.definitely_adequate:
            break
        survival = cell.horizon_step
    first = lambda predicate: next((cell.horizon_step for cell in cells if predicate(cell)), None)
    nonuse = first(lambda cell: cell.classification == "KNOWN_NONUSE")
    possible = first(lambda cell: not cell.definitely_adequate and cell.classification != "KNOWN_NONUSE")
    definite = first(lambda cell: cell.classification in ("FINITE_INADEQUATE", "UNRESOLVED_INADEQUATE"))
    dispositions = tuple(cell.source_disposition for cell in cells)
    status = ("KNOWN_NONUSE" if nonuse is not None
        else "FIRST_FAILURE_ON_LATTICE" if definite is not None and possible == definite
        else "INTERVAL_CENSORED_FAILURE" if definite is not None
        else "RIGHT_CENSORED_AT_LAST_HORIZON" if all(cell.definitely_adequate for cell in cells)
        else "UNKNOWN_CONTACT" if "UNKNOWN_CONTACT" in dispositions
        else "UNAVAILABLE" if "UNAVAILABLE" in dispositions else "UNRESOLVED")
    return survival, possible, definite, nonuse, status, dispositions



def response_adequacy_values(bound_kind, lower_loss, upper_loss, normalized_tolerance):
    """Original finite/interval/nonuse classification; no fitted criterion."""
    tolerance = Fraction(normalized_tolerance)
    if bound_kind == "KNOWN_NONUSE_INFINITY":
        return "KNOWN_NONUSE", False, False
    lower = upper_loss is not None and Fraction(upper_loss) <= tolerance
    upper = Fraction(lower_loss) <= tolerance
    classification = (("FINITE_ADEQUATE" if lower else "FINITE_INADEQUATE") if bound_kind == "FINITE_POINT"
        else "UNRESOLVED_ADEQUATE" if lower else "UNRESOLVED_INADEQUATE" if not upper else "UNRESOLVED")
    return classification, lower, upper
