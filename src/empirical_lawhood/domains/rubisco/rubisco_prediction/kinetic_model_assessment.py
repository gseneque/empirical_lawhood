# SPDX-License-Identifier: MPL-2.0
"""Independent conservation, flux and endpoint checks over retained outputs.

This owner never invokes the producer, stationary solver or a native backend.
Exact agreement assesses the stated closure, not the enzyme's true mechanism.
"""

from dataclasses import dataclass
from fractions import Fraction as F
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import FourStateResult


@dataclass(frozen=True, slots=True)
class FourStateAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/four-state-assessment"
    assessment_id: str
    result: ObjectIdentity
    disposition: AssessmentDisposition
    checks: tuple[tuple[str, bool], ...]
    reason_codes: tuple[str, ...]
    biological_accuracy: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (type(self.result) is not ObjectIdentity or self.result.object_schema != FourStateResult.SCHEMA
                or self.result.object_version != FourStateResult.VERSION):
            raise ValueError("kinetic assessment changes its retained result")
        self.result.__post_init__()
        if (type(self.checks) is not tuple or tuple(name for name, _ in self.checks) != CHECKS
                or any(type(passed) is not bool for _, passed in self.checks)):
            raise ValueError("kinetic assessment drops an independent check")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        failed = tuple("FAILED_" + name.upper() for name, passed in self.checks if not passed)
        expected = AssessmentDisposition.FALSIFIED if failed else AssessmentDisposition.SATISFIED
        if (self.disposition is not expected or self.reason_codes != failed
                or self.biological_accuracy != "NOT_ESTABLISHED"):
            raise ValueError("kinetic assessment changes its findings or biological evidence ceiling")


CHECKS = ("event-flux", "intrinsic-response", "normalization", "sensitivities", "stationary-balance")


def assess_four_state(result: FourStateResult, *, assessment_id: str) -> FourStateAssessment:
    if type(result) is not FourStateResult:
        raise TypeError("kinetic assessment requires its exact retained product")
    result.__post_init__()
    q = result.rates.fractions
    a, b, c, o = (q[key] for key in ("a", "b", "c", "o"))
    dc, do, rc, ro = (q[key] for key in ("d_c", "d_o", "r_c", "r_o"))
    carbon, oxygen = F(result.query.co2_um), F(result.query.o2_um)
    e0, es, ec, eo = (p.fraction for p in result.populations)
    balance = (
        -a * e0 + b * es + rc * ec + ro * eo,
        a * e0 - (b + c * carbon + o * oxygen) * es + dc * ec + do * eo,
        c * carbon * es - (dc + rc) * ec,
        o * oxygen * es - (do + ro) * eo,
    )
    # Eliminate bound-state populations directly; this is independent of
    # normalized matrix elimination and of the producer's endpoint map.
    capture_c, capture_o = c / (dc + rc), o / (do + ro)
    normalization = 1 + b / a + capture_c * carbon * (1 + rc / a) + capture_o * oxygen * (1 + ro / a)
    expected_c = rc * capture_c * carbon / normalization
    expected_o = ro * capture_o * oxygen / normalization
    intrinsic = result.intrinsic
    vc, vo = 1 / (1 / a + 1 / rc), 1 / (1 / a + 1 / ro)
    efficiency_c = (a / (a + b)) * c * (rc / (rc + dc))
    efficiency_o = (a / (a + b)) * o * (ro / (ro + do))
    kc, ko, specificity = vc / efficiency_c, vo / efficiency_o, efficiency_c / efficiency_o
    derivatives = {
        "a": {"kcat_c": rc**2 / (a + rc)**2, "kc": kc * (1 / (a + b) - 1 / (a + rc)),
              "kcat_o": ro**2 / (a + ro)**2, "ko": ko * (1 / (a + b) - 1 / (a + ro))},
        "b": {"kc": kc / (a + b), "ko": ko / (a + b)},
        "c": {"kc": -kc / c, "specificity": specificity / c},
        "o": {"ko": -ko / o, "specificity": -specificity / o},
        "d_c": {"kc": kc / (dc + rc), "specificity": -specificity / (dc + rc)},
        "d_o": {"ko": ko / (do + ro), "specificity": specificity / (do + ro)},
        "r_c": {"kcat_c": a**2 / (a + rc)**2,
                "kc": kc * (1 / (dc + rc) - 1 / (a + rc)),
                "specificity": specificity * (1 / rc - 1 / (dc + rc))},
        "r_o": {"kcat_o": a**2 / (a + ro)**2,
                "ko": ko * (1 / (do + ro) - 1 / (a + ro)),
                "specificity": specificity * (1 / (do + ro) - 1 / ro)},
    }
    endpoints = {"kcat_c": vc, "kc": kc, "kcat_o": vo, "ko": ko, "specificity": specificity}
    sensitivities_valid = all(
        row.derivative.fraction == derivatives[row.parameter].get(row.endpoint, 0)
        and row.elasticity.fraction == q[row.parameter] * derivatives[row.parameter].get(row.endpoint, 0) / endpoints[row.endpoint]
        for row in result.sensitivities)
    checks = (
        ("event-flux", result.carboxylation_events_per_site_s.fraction == expected_c == rc * ec
         and result.oxygenation_events_per_site_s.fraction == expected_o == ro * eo),
        ("intrinsic-response", intrinsic.kcat_c.fraction == vc and intrinsic.kcat_o.fraction == vo
         and intrinsic.kc.fraction == vc / efficiency_c and intrinsic.ko.fraction == vo / efficiency_o
         and intrinsic.specificity.fraction == efficiency_c / efficiency_o),
        ("normalization", e0 + es + ec + eo == 1),
        ("sensitivities", sensitivities_valid),
        ("stationary-balance", not any(balance)),
    )
    reasons = tuple("FAILED_" + name.upper() for name, passed in checks if not passed)
    return FourStateAssessment(assessment_id, ObjectIdentity.from_record(result.result_id, result),
        AssessmentDisposition.FALSIFIED if reasons else AssessmentDisposition.SATISFIED, checks, reasons)
