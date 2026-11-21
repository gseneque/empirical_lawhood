# SPDX-License-Identifier: MPL-2.0
"""Independent inverse-logarithm checks of retained conditional TST rates."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.transition_state_rates import PairedActivationRateInput, PairedTransitionStateRate, validate_activation_context


@dataclass(frozen=True, slots=True)
class TransitionStateRateAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/transition-state-rate-assessment"
    assessment_id: str
    selected_input: ObjectIdentity
    retained_result: ObjectIdentity
    logarithmic_residuals: tuple[Decimal, Decimal]
    logarithmic_tolerance: Decimal
    disposition: A
    unresolved_requirement_ids: tuple[str, ...]
    physical_admission: A = A.UNEVALUABLE
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        for value, kind in ((self.selected_input, PairedActivationRateInput),
                (self.retained_result, PairedTransitionStateRate)):
            exact(value, ObjectIdentity)
            if (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("rate assessment changes its exact retained input/result type")
        if type(self.logarithmic_residuals) is not tuple or len(self.logarithmic_residuals) != 2:
            raise ValueError("rate assessment drops a paired endpoint")
        for value in self.logarithmic_residuals:
            validate_decimal(value, field_name="logarithmic_residual")
        validate_decimal(self.logarithmic_tolerance, field_name="logarithmic_tolerance", minimum=Decimal(0))
        if self.logarithmic_tolerance != Decimal("1e-50"):
            raise ValueError("rate assessment changes the fixed arithmetic tolerance")
        expected = A.SATISFIED if all(value.copy_abs() <= self.logarithmic_tolerance
            for value in self.logarithmic_residuals) else A.FALSIFIED
        if self.disposition is not expected:
            raise ValueError("rate assessment changes its independent arithmetic disposition")
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        if self.physical_admission is not A.UNEVALUABLE or type(self.new_native_calls) is not int or self.new_native_calls != 0:
            raise ValueError("arithmetic assessment cannot establish physical admission or native work")


def assess_transition_state_rate(selected, retained, case, context, *, assessment_id):
    """Recover the supplied barriers from the rates; never invoke the producer."""
    validate_activation_context(selected, case, context)
    exact(retained, PairedTransitionStateRate)
    if (retained.selected_input, retained.parameter, retained.rate_unit, retained.dependence_group_id,
            retained.unresolved_requirement_ids) != (selected.identity, selected.parameter,
            selected.rate_unit, selected.dependence_group_id, selected.remaining_requirements):
        raise ValueError("rate assessment substitutes retained sources, units, pairing or unresolved requirements")
    residuals = []
    with localcontext() as arithmetic:
        arithmetic.prec = 80
        arithmetic.rounding = ROUND_HALF_EVEN
        arithmetic.Emax, arithmetic.Emin = 999999, -999999
        # Independent inverse calculation from exact SI definitions.
        rt = Decimal("1.380649e-23") * Decimal("6.02214076e23") * selected.temperature_k
        log_thermal = (Decimal("1.380649e-23").ln() + selected.temperature_k.ln()
            - Decimal("6.62607015e-34").ln())
        for index, value in enumerate((retained.wild_type_rate, retained.mutant_rate)):
            residual = (value.ln() - log_thermal - selected.prefactor_multipliers[index].ln()
                - selected.transmission_coefficients[index].ln()
                + selected.activation_free_energy_j_mol[index] / rt)
            if selected.concentration_standard_state_um is not None:
                residual += selected.concentration_standard_state_um.ln()
            if selected.bulk_partition_factors is not None:
                residual -= selected.bulk_partition_factors[index].ln()
            residuals.append(residual)
    tolerance = Decimal("1e-50")
    disposition = A.SATISFIED if all(value.copy_abs() <= tolerance for value in residuals) else A.FALSIFIED
    return TransitionStateRateAssessment(assessment_id, selected.identity, retained.identity,
        tuple(residuals), tolerance, disposition, selected.remaining_requirements)
