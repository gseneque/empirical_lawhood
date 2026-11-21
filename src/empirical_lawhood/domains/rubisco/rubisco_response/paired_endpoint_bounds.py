# SPDX-License-Identifier: MPL-2.0
"""Exact endpoint contrasts with an unidentified WT waiting-time allocation.

One input is one joint realization of four supplied positive rate contrasts.
Only the WT waiting fraction ranges continuously. No marginal uncertainty is
independently combined, and no absolute or missing microscopic rate is fitted.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact, identities

RATIO_ORDER = ("a", "r_c", "c_over_o", "chi_c_over_chi_o")
SCOPE = "FIXED_JOINT_RATE_RATIOS_CLOSED_WT_WAITING_FRACTION_ENCLOSURE"


def _identity(value, kind):
    exact(value, ObjectIdentity)
    if (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("endpoint contrast changes its exact input record type")


def _positive(value):
    exact(value, Exact)
    if value.fraction <= 0:
        raise ValueError("a missing or zero rate contrast cannot be supplied as positive evidence")


@dataclass(frozen=True, slots=True)
class PairedEffectiveRateRatios(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-effective-rate-ratios"
    input_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    formation_ratio: Exact
    processing_ratio: Exact
    gas_discrimination_ratio: Exact
    branch_commitment_ratio: Exact
    wild_type_formation_wait_fraction: tuple[Exact, Exact]
    ratio_sources: tuple[ObjectIdentity, ...]
    waiting_fraction_evidence: ObjectIdentity | None
    closure_model: ObjectIdentity
    dependence_group_id: str
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]
    interpretation: str = SCOPE

    def __post_init__(self):
        for name in ("input_id", "dependence_group_id"):
            validate_stable_id(getattr(self, name))
        _identity(self.case, RubiscoPairedCase)
        _identity(self.context, RubiscoAssayContext)
        for name in ("formation_ratio", "processing_ratio", "gas_discrimination_ratio", "branch_commitment_ratio"):
            _positive(getattr(self, name))
        if type(self.wild_type_formation_wait_fraction) is not tuple or len(self.wild_type_formation_wait_fraction) != 2:
            raise ValueError("WT waiting allocation needs its complete closed interval")
        for value in self.wild_type_formation_wait_fraction:
            exact(value, Exact)
        lower, upper = (value.fraction for value in self.wild_type_formation_wait_fraction)
        if not 0 <= lower <= upper <= 1:
            raise ValueError("WT waiting fractions must be ordered within [0, 1]")
        if (lower, upper) in ((0, 0), (1, 1)):
            raise ValueError("a limiting waiting fraction alone cannot represent positive finite rates")
        if (lower, upper) != (0, 1) and self.waiting_fraction_evidence is None:
            raise ValueError("narrowed WT waiting allocation requires its source evidence")
        if type(self.ratio_sources) is not tuple or len(self.ratio_sources) != len(RATIO_ORDER):
            raise ValueError("all four joint rate contrasts need their ordered source bindings")
        required = {self.case, self.context}
        for source in (*self.ratio_sources, self.closure_model):
            exact(source, ObjectIdentity)
            required.add(source)
        if self.waiting_fraction_evidence is not None:
            exact(self.waiting_fraction_evidence, ObjectIdentity)
            required.add(self.waiting_fraction_evidence)
        identities(self.sources)
        if not required.issubset(self.sources):
            raise ValueError("endpoint contrast loses its actual source closure")
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        if self.interpretation != SCOPE:
            raise ValueError("fixed joint contrasts cannot become independent uncertain marginals")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.input_id, self)

    @property
    def remaining_requirements(self):
        prefix = "requirement." + self.input_id
        return tuple(sorted({*self.unresolved_requirement_ids,
            prefix + ".paired-rate-contrast-support", prefix + ".closure-and-lumping-applicability",
            prefix + ".biological-applicability"}))


@dataclass(frozen=True, slots=True)
class PairedEndpointEnclosure(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-endpoint-enclosure"
    result_id: str
    selected_input: ObjectIdentity
    turnover_ratio_bounds: tuple[Exact, Exact]
    specificity_ratio: Exact
    dependence_group_id: str
    unresolved_requirement_ids: tuple[str, ...]
    interpretation: str = SCOPE
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.result_id)
        validate_stable_id(self.dependence_group_id)
        _identity(self.selected_input, PairedEffectiveRateRatios)
        if type(self.turnover_ratio_bounds) is not tuple or len(self.turnover_ratio_bounds) != 2:
            raise ValueError("endpoint result drops its complete turnover enclosure")
        for value in (*self.turnover_ratio_bounds, self.specificity_ratio):
            _positive(value)
        if self.turnover_ratio_bounds[0].fraction > self.turnover_ratio_bounds[1].fraction:
            raise ValueError("endpoint result reverses its lower and upper bounds")
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        if (self.interpretation != SCOPE or type(self.new_native_calls) is not int or self.new_native_calls != 0):
            raise ValueError("conditional bounds cannot establish native work or biological qualification")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id, self)


def bound_paired_endpoints(selected, case, context, *, result_id):
    """Enclose the whole selected WT waiting interval, without discretizing it."""
    exact(selected, PairedEffectiveRateRatios)
    exact(case, RubiscoPairedCase)
    exact(context, RubiscoAssayContext)
    if (selected.case, selected.context) != (case.identity, context.identity):
        raise ValueError("endpoint contrast substitutes its actual paired case or assay")
    qa, qr = selected.formation_ratio.fraction, selected.processing_ratio.fraction
    bounds = tuple(sorted(Fraction(1) / (w.fraction / qa + (1 - w.fraction) / qr)
        for w in selected.wild_type_formation_wait_fraction))
    return PairedEndpointEnclosure(result_id, selected.identity,
        tuple(Exact.of(value) for value in bounds),
        Exact.of(selected.gas_discrimination_ratio.fraction * selected.branch_commitment_ratio.fraction),
        selected.dependence_group_id, selected.remaining_requirements)
