# SPDX-License-Identifier: MPL-2.0
"""Conditional physical-unit conversion of retained paired activation energies.

These operands are free energies, not electronic single-point energies. Their
source identities and explicit model choices do not establish chemical validity.
No molecular backend, sampling clock or implicit rate is supplied here.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact, identities

# Exact SI definitions. R is formed inside the selected arithmetic context.
BOLTZMANN_J_K = Decimal("1.380649e-23")
PLANCK_J_S = Decimal("6.62607015e-34")
AVOGADRO_MOL = Decimal("6.02214076e23")
RATE_PRECISION = 60


def _pair(values, name, *, positive=False, probability=False):
    if type(values) is not tuple or len(values) != 2:
        raise ValueError(name + " requires the complete ordered WT/mutant pair")
    for value in values:
        validate_decimal(value, field_name=name)
        if positive and value <= 0 or probability and not 0 < value <= 1:
            raise ValueError(name + " is outside its selected positive/probability support")


@dataclass(frozen=True, slots=True)
class PairedActivationRateInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-activation-rate-input"
    input_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    parameter: str
    temperature_k: Decimal
    activation_free_energy_j_mol: tuple[Decimal, Decimal]
    transmission_coefficients: tuple[Decimal, Decimal]
    prefactor_multipliers: tuple[Decimal, Decimal]
    concentration_standard_state_um: Decimal | None
    gas_access: str
    bulk_partition_factors: tuple[Decimal, Decimal] | None
    state_definition: ObjectIdentity
    barrier_evidence: ObjectIdentity
    free_energy_assessment: ObjectIdentity | None
    prefactor_model: ObjectIdentity
    transmission_model: ObjectIdentity
    bulk_access_model: ObjectIdentity | None
    oxygenation_model: ObjectIdentity | None
    dependence_group_id: str
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]
    meaning: str = "CONDITIONAL_ACTIVATION_FREE_ENERGIES_NOT_RAW_ELECTRONIC_ENERGIES"

    def __post_init__(self):
        for name in ("input_id", "dependence_group_id"):
            validate_stable_id(getattr(self, name))
        for value, kind in ((self.case, RubiscoPairedCase), (self.context, RubiscoAssayContext)):
            exact(value, ObjectIdentity)
            if (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("activation input changes its exact paired case or assay type")
        if self.parameter not in PARAMETER_ORDER:
            raise ValueError("activation input changes its kinetic transition")
        validate_decimal(self.temperature_k, field_name="temperature_k", minimum=Decimal(0))
        if self.temperature_k == 0:
            raise ValueError("activation input requires a positive physical temperature")
        _pair(self.activation_free_energy_j_mol, "activation free energies")
        _pair(self.transmission_coefficients, "transmission coefficients", probability=True)
        _pair(self.prefactor_multipliers, "prefactor multipliers", positive=True)
        capture = self.parameter in {"c", "o"}
        if capture:
            if self.gas_access not in {"BULK_ALREADY_INCLUDED", "LOCAL_REQUIRES_ONE_BULK_CONVERSION"}:
                raise ValueError("capture requires an explicit bulk-access convention")
            if self.concentration_standard_state_um is None or self.bulk_access_model is None:
                raise ValueError("capture requires its source standard state and bulk-access model")
            validate_decimal(self.concentration_standard_state_um,
                field_name="concentration_standard_state_um", minimum=Decimal(0))
            if self.concentration_standard_state_um == 0:
                raise ValueError("capture standard state must be positive")
        elif (self.gas_access != "UNIMOLECULAR" or self.concentration_standard_state_um is not None
                or self.bulk_access_model is not None):
            raise ValueError("unimolecular rates cannot acquire a concentration/access correction")
        local = self.gas_access == "LOCAL_REQUIRES_ONE_BULK_CONVERSION"
        if local != (self.bulk_partition_factors is not None):
            raise ValueError("bulk partition must be applied exactly once, only to a local barrier")
        if self.bulk_partition_factors is not None:
            _pair(self.bulk_partition_factors, "bulk partition factors", positive=True)
        if (self.parameter in {"o", "d_o", "r_o"}) != (self.oxygenation_model is not None):
            raise ValueError("oxygenation transitions require their explicit electronic/kinetic assumption")
        identities(self.sources)
        required = {self.case, self.context}
        for name in ("state_definition", "barrier_evidence", "prefactor_model", "transmission_model"):
            value = getattr(self, name)
            exact(value, ObjectIdentity)
            required.add(value)
        for name in ("free_energy_assessment", "bulk_access_model", "oxygenation_model"):
            value = getattr(self, name)
            if value is not None:
                exact(value, ObjectIdentity)
                required.add(value)
        if not required.issubset(self.sources):
            raise ValueError("activation input loses its actual source and model closure")
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        if self.meaning != "CONDITIONAL_ACTIVATION_FREE_ENERGIES_NOT_RAW_ELECTRONIC_ENERGIES":
            raise ValueError("electronic energies cannot alias activation free energies")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.input_id, self)

    @property
    def rate_unit(self):
        return "uM^-1 s^-1" if self.parameter in {"c", "o"} else "s^-1"

    @property
    def remaining_requirements(self):
        prefix = "requirement." + self.input_id
        return tuple(sorted({*self.unresolved_requirement_ids,
            prefix + ".physical-rate-applicability", prefix + ".state-lumping-applicability",
            prefix + ".paired-prefactor-and-transmission-support",
            *(() if self.free_energy_assessment is not None else (prefix + ".free-energy-assessment",))}))


def validate_activation_context(selected, case, context):
    exact(selected, PairedActivationRateInput)
    exact(case, RubiscoPairedCase)
    exact(context, RubiscoAssayContext)
    if (selected.case, selected.context, selected.temperature_k) != (
            case.identity, context.identity, context.temperature_k):
        raise ValueError("activation input substitutes its actual case, context or physical temperature")


@dataclass(frozen=True, slots=True)
class PairedTransitionStateRate(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-transition-state-rate"
    result_id: str
    selected_input: ObjectIdentity
    parameter: str
    wild_type_rate: Decimal
    mutant_rate: Decimal
    rate_unit: str
    dependence_group_id: str
    unresolved_requirement_ids: tuple[str, ...]
    interpretation: str = "CONDITIONAL_TST_MODEL_RATE_NOT_PHYSICAL_OR_BIOLOGICAL_ADMISSION"
    physical_clock_unit: str = "s"
    decimal_precision: int = RATE_PRECISION
    new_native_calls: int = 0

    def __post_init__(self):
        for name in ("result_id", "dependence_group_id"):
            validate_stable_id(getattr(self, name))
        exact(self.selected_input, ObjectIdentity)
        if (self.selected_input.object_schema, self.selected_input.object_version) != (
                PairedActivationRateInput.SCHEMA, PairedActivationRateInput.VERSION):
            raise ValueError("rate result changes its exact retained activation input")
        if self.parameter not in PARAMETER_ORDER or self.rate_unit != (
                "uM^-1 s^-1" if self.parameter in {"c", "o"} else "s^-1"):
            raise ValueError("rate result changes its kinetic transition or units")
        _pair((self.wild_type_rate, self.mutant_rate), "model rates", positive=True)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        if (self.interpretation != "CONDITIONAL_TST_MODEL_RATE_NOT_PHYSICAL_OR_BIOLOGICAL_ADMISSION"
                or self.physical_clock_unit != "s" or type(self.decimal_precision) is not int
                or self.decimal_precision != RATE_PRECISION or type(self.new_native_calls) is not int
                or self.new_native_calls != 0):
            raise ValueError("rate conversion cannot establish native execution or physical qualification")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id, self)


def calculate_transition_state_rate(selected, case, context, *, result_id):
    """Apply a declared Eyring model; preserve paired operands without resampling."""
    validate_activation_context(selected, case, context)
    rates = []
    with localcontext() as arithmetic:
        arithmetic.prec = RATE_PRECISION
        arithmetic.rounding = ROUND_HALF_EVEN
        arithmetic.Emax, arithmetic.Emin = 999999, -999999
        thermal = BOLTZMANN_J_K * selected.temperature_k / PLANCK_J_S
        rt = BOLTZMANN_J_K * AVOGADRO_MOL * selected.temperature_k
        for index in range(2):
            value = (thermal * selected.prefactor_multipliers[index]
                * selected.transmission_coefficients[index]
                * (-selected.activation_free_energy_j_mol[index] / rt).exp())
            if selected.concentration_standard_state_um is not None:
                value /= selected.concentration_standard_state_um
            if selected.bulk_partition_factors is not None:
                value *= selected.bulk_partition_factors[index]
            if not value.is_finite() or value <= 0:
                raise ArithmeticError("TST conversion overflow/underflow cannot become an exact zero rate")
            rates.append(value)
    return PairedTransitionStateRate(result_id, selected.identity, selected.parameter, *rates,
        selected.rate_unit, selected.dependence_group_id, selected.remaining_requirements)
