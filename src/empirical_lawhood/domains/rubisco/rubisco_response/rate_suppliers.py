# SPDX-License-Identifier: MPL-2.0
"""Rate-supplier meanings and exact missing premises beside retained supports.

A source reference establishes which assumption was selected, not its truth.
These metadata joins neither infer physical rates from barriers nor admit a
rate supplier. Existing kernel clocks retain native-to-physical-time meaning.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.science.models.time import ClockSpec, ClockTransport, ClockTransportAvailability
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.rate_contracts import ParameterEvidenceLedger


@dataclass(frozen=True, slots=True)
class RateSupplierSemantics(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/rate-supplier-semantics"
    supplier_id: str
    ledger: ObjectIdentity
    parameter: str
    method: ObjectIdentity
    context: ObjectIdentity
    temperature_k: Decimal
    state_meanings: ObjectIdentity | None
    source_clock: ClockSpec | None
    clock_transport: ClockTransport | None
    source_concentration_standard_state_um: Decimal | None
    standard_state_evidence: ObjectIdentity | None
    gas_access: str
    bulk_access_assessment: ObjectIdentity | None
    paired_activation_free_energy: ObjectIdentity | None
    paired_prefactor_model: ObjectIdentity | None
    paired_transmission_model: ObjectIdentity | None
    reverse_commitment: str
    reverse_commitment_assessment: ObjectIdentity | None
    state_lumping_assessment: ObjectIdentity | None
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.supplier_id)
        if self.parameter not in PARAMETER_ORDER:
            raise ValueError("supplier changes its selected kinetic parameter")
        for row in (self.ledger, self.method, self.context):
            exact(row, ObjectIdentity)
        if self.ledger.object_schema != ParameterEvidenceLedger.SCHEMA or self.context.object_schema != RubiscoAssayContext.SCHEMA:
            raise ValueError("supplier changes its exact rate-ledger or assay record type")
        validate_decimal(self.temperature_k, field_name="temperature_k", minimum=Decimal(0))
        if self.temperature_k == 0:
            raise ValueError("supplier needs a positive selected temperature")
        required = {self.ledger, self.context, self.method}
        for name in ("state_meanings", "standard_state_evidence", "bulk_access_assessment",
                     "paired_activation_free_energy", "paired_prefactor_model", "paired_transmission_model",
                     "reverse_commitment_assessment", "state_lumping_assessment"):
            row = getattr(self, name)
            if row is not None:
                exact(row, ObjectIdentity)
                required.add(row)
        if self.source_clock is not None:
            exact(self.source_clock, ClockSpec)
            required.add(ObjectIdentity.from_record(self.source_clock.clock_id, self.source_clock))
        if self.clock_transport is not None:
            exact(self.clock_transport, ClockTransport)
            transport = self.clock_transport
            if self.source_clock is None or (
                    transport.source_clock_id, transport.source_time_unit, transport.source_coordinate_frame) != (
                    self.source_clock.clock_id, self.source_clock.time_unit, self.source_clock.coordinate_frame):
                raise ValueError("supplier clock transport substitutes its actual native clock")
            if transport.target_clock_id != "clock.rubisco.physical-seconds" or transport.target_time_unit != "s":
                raise ValueError("supplier clock transport does not reach the selected physical seconds")
            required.add(ObjectIdentity.from_record(transport.transport_id, transport))
        standard = self.source_concentration_standard_state_um
        if (standard is None) != (self.standard_state_evidence is None):
            raise ValueError("supplier concentration standard state requires its exact source")
        if standard is not None:
            validate_decimal(standard, field_name="source_concentration_standard_state_um", minimum=Decimal(0))
            if standard == 0:
                raise ValueError("supplier concentration standard state must be positive")
        if self.gas_access not in {"UNIMOLECULAR", "BULK_ALREADY_INCLUDED", "LOCAL_REQUIRES_ONE_BULK_CONVERSION", "UNRESOLVED"}:
            raise ValueError("supplier gas access must state whether bulk conversion is already included")
        capture = self.parameter in {"c", "o"}
        if (self.gas_access == "UNIMOLECULAR") == capture:
            raise ValueError("supplier changes unimolecular versus gas-capture meaning")
        if not capture and (standard is not None or self.bulk_access_assessment is not None):
            raise ValueError("unimolecular supplier cannot acquire a gas standard-state multiplier")
        reverse = self.parameter in {"b", "d_c", "d_o"}
        if self.reverse_commitment not in {"NOT_REVERSE", "FIXED_ZERO_ASSUMPTION", "SOURCE_SUPPORTED_REVERSE", "UNRESOLVED"}:
            raise ValueError("supplier must retain reverse commitment or its explicit missing premise")
        if (self.reverse_commitment == "NOT_REVERSE") == reverse:
            raise ValueError("supplier changes whether the selected transition is a reverse edge")
        identities(self.sources)
        if not required.issubset(self.sources):
            raise ValueError("supplier semantics drop a selected source or complete clock record")
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.supplier_id, self)


def _supplier_metadata_requirements(ledger, context, binding, selected):
    prefix = "requirement." + ledger.ledger_id + "." + binding.parameter
    required = set()
    if selected is None:
        return (prefix + ".supplier-semantics",)
    exact(selected, RateSupplierSemantics)
    if (selected.ledger, selected.parameter, selected.context, selected.temperature_k) != (
            ledger.identity, binding.parameter, context.identity, context.temperature_k):
        raise ValueError("supplier substitutes the actual paired ledger, parameter, context or temperature")
    required.update(selected.unresolved_requirement_ids)
    if selected.state_meanings is None:
        required.add(prefix + ".physical-state-meanings")
    if selected.source_clock is None:
        required.add(prefix + ".physical-clock")
    elif selected.source_clock.time_unit != "s":
        if selected.clock_transport is None or selected.clock_transport.availability is ClockTransportAvailability.UNAVAILABLE:
            required.add(prefix + ".native-to-physical-clock")
    transport = selected.clock_transport
    if transport is not None and (transport.tolerance != 0
            or transport.valid_source_lower is not None or transport.valid_source_upper is not None):
        required.add(prefix + ".clock-domain-and-error-assessment")
    if selected.state_lumping_assessment is None:
        required.add(prefix + ".effective-state-lumping")
    if binding.parameter in {"c", "o"}:
        if selected.source_concentration_standard_state_um is None:
            required.add(prefix + ".concentration-standard-state")
        if selected.gas_access == "UNRESOLVED" or selected.bulk_access_assessment is None:
            required.add(prefix + ".bulk-access-once")
    if binding.supplier_route == "FREE_ENERGY_AND_DYNAMICS":
        for name, value in (("paired-activation-free-energy", selected.paired_activation_free_energy),
                            ("paired-prefactor", selected.paired_prefactor_model),
                            ("paired-transmission", selected.paired_transmission_model)):
            if value is None:
                required.add(prefix + "." + name)
    if binding.parameter in {"b", "d_c", "d_o"}:
        if selected.reverse_commitment == "UNRESOLVED" or selected.reverse_commitment_assessment is None:
            required.add(prefix + ".reverse-commitment")
        if selected.reverse_commitment == "FIXED_ZERO_ASSUMPTION" and (
                binding.wild_type_bounds != (Decimal(0), Decimal(0)) or binding.mutant_bounds != (Decimal(0), Decimal(0))):
            raise ValueError("fixed-zero reverse commitment cannot hide positive or unidentified support")
    return tuple(sorted(required))


def _scientific_requirements(ledger, metadata):
    required = {name for _, rows in metadata for name in rows}
    for binding in ledger.bindings:
        prefix = "requirement." + ledger.ledger_id + "." + binding.parameter
        required.update(binding.unresolved_requirement_ids)
        required.add(prefix + ".supplier-physical-applicability")
        if binding.evidence_kind in {"UNIDENTIFIED", "IMPOSED_ASSUMPTION"}:
            required.add(prefix + ".independent-rate-support")
        elif not binding.assessments:
            required.add(prefix + ".independent-rate-assessment")
        if binding.mutation_dependence in {"UNIDENTIFIED", "IMPOSED_INVARIANT"}:
            required.add(prefix + ".mutation-dependence-support")
    return tuple(sorted(required))


@dataclass(frozen=True, slots=True)
class RateSupplierCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/rate-supplier-census"
    census_id: str
    ledger: ParameterEvidenceLedger
    context: RubiscoAssayContext
    semantics: tuple[RateSupplierSemantics | None, ...]
    metadata_requirements: tuple[tuple[str, tuple[str, ...]], ...]
    unresolved_requirement_ids: tuple[str, ...]
    scientific_admission: A = A.UNEVALUABLE

    def __post_init__(self):
        validate_stable_id(self.census_id)
        exact(self.ledger, ParameterEvidenceLedger)
        exact(self.context, RubiscoAssayContext)
        if self.ledger.context != self.context.identity:
            raise ValueError("supplier census changes its exact assay context")
        if type(self.semantics) is not tuple or len(self.semantics) != len(PARAMETER_ORDER):
            raise ValueError("supplier census drops a selected rate, including missing suppliers")
        expected = tuple((binding.parameter, _supplier_metadata_requirements(self.ledger, self.context, binding, selected))
            for binding, selected in zip(self.ledger.bindings, self.semantics, strict=True))
        if self.metadata_requirements != expected or self.unresolved_requirement_ids != _scientific_requirements(self.ledger, expected):
            raise ValueError("supplier census prunes missing scientific/semantic requirements")
        if self.scientific_admission is not A.UNEVALUABLE:
            raise ValueError("complete supplier metadata cannot establish physical rate applicability")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.census_id, self)

    @property
    def metadata_complete(self):
        return not any(rows for _, rows in self.metadata_requirements)


def assess_rate_suppliers(ledger, context, semantics=(), *, census_id):
    """Complete every original rate slot, using None for actual absent semantics."""
    exact(ledger, ParameterEvidenceLedger)
    exact(context, RubiscoAssayContext)
    if type(semantics) is not tuple:
        raise ValueError("supplier selection must be an immutable supplied census")
    for row in semantics:
        exact(row, RateSupplierSemantics)
    if len({row.parameter for row in semantics}) != len(semantics):
        raise ValueError("supplier census repeats a parameter binding")
    by_parameter = {row.parameter: row for row in semantics}
    selected = tuple(by_parameter.get(parameter) for parameter in PARAMETER_ORDER)
    metadata = tuple((binding.parameter, _supplier_metadata_requirements(ledger, context, binding, row))
                     for binding, row in zip(ledger.bindings, selected, strict=True))
    return RateSupplierCensus(census_id, ledger, context, selected, metadata, _scientific_requirements(ledger, metadata))
