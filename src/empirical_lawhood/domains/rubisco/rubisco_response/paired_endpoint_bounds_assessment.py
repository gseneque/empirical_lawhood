# SPDX-License-Identifier: MPL-2.0
"""Independent rational checks of retained endpoint enclosures; no producer call."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds import PairedEffectiveRateRatios, PairedEndpointEnclosure


@dataclass(frozen=True, slots=True)
class PairedEndpointEnclosureAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-endpoint-enclosure-assessment"
    assessment_id: str
    selected_input: ObjectIdentity
    retained_result: ObjectIdentity
    bound_balance_residuals: tuple[Exact, Exact]
    specificity_balance_residual: Exact
    numerical_disposition: A
    physical_admission: A = A.UNEVALUABLE
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        for value, kind in ((self.selected_input, PairedEffectiveRateRatios), (self.retained_result, PairedEndpointEnclosure)):
            exact(value, ObjectIdentity)
            if (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("enclosure assessment changes its exact retained operands")
        if type(self.bound_balance_residuals) is not tuple or len(self.bound_balance_residuals) != 2:
            raise ValueError("enclosure assessment drops an extremal balance")
        values = (*self.bound_balance_residuals, self.specificity_balance_residual)
        for value in values:
            exact(value, Exact)
        expected = A.SATISFIED if all(value.fraction == 0 for value in values) else A.FALSIFIED
        if self.numerical_disposition is not expected:
            raise ValueError("enclosure assessment changes its exact numerical finding")
        if (self.physical_admission is not A.UNEVALUABLE or type(self.new_native_calls) is not int
                or self.new_native_calls != 0):
            raise ValueError("algebra cannot establish physical admission or molecular work")


def assess_endpoint_enclosure(selected, result, case, context, *, assessment_id):
    exact(selected, PairedEffectiveRateRatios)
    exact(result, PairedEndpointEnclosure)
    exact(case, RubiscoPairedCase)
    exact(context, RubiscoAssayContext)
    if ((selected.case, selected.context) != (case.identity, context.identity)
            or result.selected_input != selected.identity
            or result.dependence_group_id != selected.dependence_group_id
            or result.unresolved_requirement_ids != selected.remaining_requirements):
        raise ValueError("enclosure assessment changes its pairing, input or remaining requirements")
    qa, qr = selected.formation_ratio.fraction, selected.processing_ratio.fraction
    # The derivative's sign is sign(qa - qr) throughout the positive interval.
    # Thus the two endpoint balances certify the extrema over its continuum.
    fractions = selected.wild_type_formation_wait_fraction
    if qa < qr:
        fractions = tuple(reversed(fractions))
    residuals = tuple(Exact.of(bound.fraction * (w.fraction * qr + (1 - w.fraction) * qa) - qa * qr)
        for bound, w in zip(result.turnover_ratio_bounds, fractions, strict=True))
    specificity = Exact.of(result.specificity_ratio.fraction
        - selected.gas_discrimination_ratio.fraction * selected.branch_commitment_ratio.fraction)
    disposition = A.SATISFIED if all(value.fraction == 0 for value in (*residuals, specificity)) else A.FALSIFIED
    return PairedEndpointEnclosureAssessment(assessment_id, selected.identity, result.identity,
        residuals, specificity, disposition)
