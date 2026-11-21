# SPDX-License-Identifier: MPL-2.0
"""Complete parameter evidence and joint WT/mutant realizations.

Finite points are a declared support, never an automatic enclosure of a
continuous rate box. Unidentified rates remain unresolved requirements.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER, DissolvedGasQuery, FourStateRates
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import EndpointValues
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_nonempty, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import RubiscoAssayContext, validate_paired_chemical_selection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoPairedCase, exact, identities

TRANSITIONS = {"a": "e0->estar", "b": "estar->e0", "c": "estar+CO2->ec", "d_c": "ec->estar+CO2",
               "d_o": "eo->estar+O2", "o": "estar+O2->eo", "r_c": "ec->e0+carboxylation-products",
               "r_o": "eo->e0+oxygenation-products"}


@dataclass(frozen=True, slots=True)
class RateEvidenceBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/rate-evidence-binding"
    parameter: str
    transition: str
    native_unit: str
    evidence_kind: str
    supplier_route: str
    wild_type_bounds: tuple[Decimal, Decimal] | None
    mutant_bounds: tuple[Decimal, Decimal] | None
    mutation_dependence: str
    dependence_group_id: str
    applicability_limits: tuple[str, ...]
    sources: tuple[ObjectIdentity, ...]
    assessments: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]
    required_relative_accuracy: Decimal | None

    def __post_init__(self):
        if self.parameter not in PARAMETER_ORDER or self.transition != TRANSITIONS[self.parameter]:
            raise ValueError("rate ledger changes the selected physical transition")
        expected = "uM^-1 s^-1" if self.parameter in {"c", "o"} else "s^-1"
        if self.native_unit != expected:
            raise ValueError("rate ledger changes its physical clock or concentration units")
        if self.evidence_kind not in {"MEASURED", "COMPUTED", "DERIVED", "NUISANCE_SUPPORT", "IMPOSED_ASSUMPTION", "UNIDENTIFIED"}:
            raise ValueError("rate ledger must retain its actual evidence interpretation")
        if self.supplier_route not in {"PHYSICAL_TRANSITIONS", "FREE_ENERGY_AND_DYNAMICS", "SOURCE_CONDITIONED", "DISCLOSED_CONTROL", "UNSELECTED"}:
            raise ValueError("rate ledger must select an actual supplier route")
        if self.mutation_dependence not in {"PAIRED_JOINT", "IMPOSED_INVARIANT", "UNIDENTIFIED"}:
            raise ValueError("rate ledger must retain mutation dependence")
        validate_stable_id(self.dependence_group_id)
        require_sorted_unique_strings(self.applicability_limits, field_name="applicability_limits", allow_empty=False)
        for value in self.applicability_limits:
            validate_nonempty(value, field_name="applicability_limits")
        identities(self.sources)
        identities(self.assessments, allow_empty=True)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        for bounds in (self.wild_type_bounds, self.mutant_bounds):
            if bounds is not None:
                if type(bounds) is not tuple or len(bounds) != 2:
                    raise ValueError("rate bounds need exact lower and upper Decimal values")
                for value in bounds:
                    validate_decimal(value, field_name="rate_bound", minimum=Decimal(0))
                if bounds[0] > bounds[1] or self.parameter not in {"b", "d_c", "d_o"} and bounds[0] == 0:
                    raise ValueError("rate bounds have reversed support or unsupported zero")
        if self.evidence_kind == "UNIDENTIFIED":
            if not self.unresolved_requirement_ids or self.wild_type_bounds is not None or self.mutant_bounds is not None:
                raise ValueError("unidentified rate needs its missing requirement without fabricated bounds")
        elif self.wild_type_bounds is None or self.mutant_bounds is None:
            raise ValueError("declared rate support requires both WT and mutant bounds")
        if self.evidence_kind != "UNIDENTIFIED" and self.supplier_route == "UNSELECTED":
            raise ValueError("identified support cannot omit its selected supplier route")
        if (self.evidence_kind not in {"IMPOSED_ASSUMPTION", "UNIDENTIFIED"}
                and not self.assessments and not self.unresolved_requirement_ids):
            raise ValueError("unassessed rate evidence must retain its admission requirement")
        if self.mutation_dependence == "IMPOSED_INVARIANT" and self.wild_type_bounds != self.mutant_bounds:
            raise ValueError("imposed invariance must retain equal marginal supports")
        if self.required_relative_accuracy is not None:
            validate_decimal(self.required_relative_accuracy, field_name="required_relative_accuracy", minimum=Decimal(0))
            if self.required_relative_accuracy == 0:
                raise ValueError("required rate accuracy must be positive")


@dataclass(frozen=True, slots=True)
class ParameterEvidenceLedger(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/parameter-evidence-ledger"
    ledger_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    bindings: tuple[RateEvidenceBinding, ...]
    concentration_standard_state_um: Decimal = Decimal(1)
    interpretation: str = "MARGINAL_BOUNDS_DO_NOT_DEFINE_JOINT_SUPPORT"

    def __post_init__(self):
        validate_stable_id(self.ledger_id)
        for record, kind in ((self.case, RubiscoPairedCase), (self.context, RubiscoAssayContext)):
            exact(record, ObjectIdentity)
            if record.object_schema != kind.SCHEMA or record.object_version != kind.VERSION:
                raise ValueError("rate ledger changes its exact case or context revision")
        if type(self.bindings) is not tuple or tuple(row.parameter for row in self.bindings) != PARAMETER_ORDER:
            raise ValueError("rate ledger must retain every selected kinetic parameter")
        for row in self.bindings:
            exact(row, RateEvidenceBinding)
        if (self.concentration_standard_state_um != Decimal(1)
                or type(self.concentration_standard_state_um) is not Decimal
                or self.interpretation != "MARGINAL_BOUNDS_DO_NOT_DEFINE_JOINT_SUPPORT"):
            raise ValueError("rate ledger cannot change the standard state or invent independence")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.ledger_id, self)

    @property
    def unresolved_requirement_ids(self):
        return tuple(sorted({name for row in self.bindings for name in row.unresolved_requirement_ids}))


@dataclass(frozen=True, slots=True)
class PairedRatePoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-rate-point"
    point_id: str
    wild_type: FourStateRates
    mutant: FourStateRates
    sources: tuple[ObjectIdentity, ...]
    anchor_wild_type: EndpointValues | None = None
    anchor_source: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.point_id)
        for record in (self.wild_type, self.mutant):
            exact(record, FourStateRates)
        identities(self.sources)
        if (self.anchor_wild_type is None) != (self.anchor_source is None):
            raise ValueError("uncertain WT reference needs its exact joint realization and source")
        if self.anchor_wild_type is not None:
            exact(self.anchor_wild_type, EndpointValues)
            exact(self.anchor_source, ObjectIdentity)
            if self.anchor_source not in self.sources:
                raise ValueError("WT reference is absent from joint realization sources")


@dataclass(frozen=True, slots=True)
class PairedRateScenario(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-rate-scenario"
    scenario_id: str
    original_state: str
    ledger: ParameterEvidenceLedger
    points: tuple[PairedRatePoint, ...]
    closure_alternative: str
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.scenario_id)
        exact(self.ledger, ParameterEvidenceLedger)
        validate_nonempty(self.closure_alternative, field_name="closure_alternative")
        identities(self.sources)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        if type(self.points) is not tuple or len(self.points) > 256:
            raise ValueError("scenario joint support exceeds its finite bound")
        require_sorted_unique_ids(self.points, attribute="point_id", field_name="points")
        for point in self.points:
            exact(point, PairedRatePoint)
            for row in self.ledger.bindings:
                for arm in ("wild_type", "mutant"):
                    bounds = getattr(row, arm + "_bounds")
                    if bounds is None or not bounds[0] <= getattr(getattr(point, arm), row.parameter) <= bounds[1]:
                        raise ValueError("joint rate realization lies outside its sourced ledger support")
                if (row.mutation_dependence == "IMPOSED_INVARIANT"
                        and getattr(point.wild_type, row.parameter) != getattr(point.mutant, row.parameter)):
                    raise ValueError("joint rate realization changes an imposed invariant")
        if len({point.anchor_source for point in self.points}) > 1:
            raise ValueError("one scenario region requires a common reference source")
        if self.original_state not in {"AVAILABLE", "UNKNOWN", "FAILED"}:
            raise ValueError("rate scenario must retain its actual completion state")
        if self.original_state != "AVAILABLE" and (self.points or not self.unresolved_requirement_ids):
            raise ValueError("failed or unknown scenario cannot silently acquire point estimates")


@dataclass(frozen=True, slots=True)
class PairedRateSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-rate-supply"
    supply_id: str
    case: RubiscoPairedCase
    context: RubiscoAssayContext
    query: DissolvedGasQuery
    expected_scenario_ids: tuple[str, ...]
    scenarios: tuple[PairedRateScenario, ...]
    shared_sources: tuple[ObjectIdentity, ...]
    prerequisite_requirement_ids: tuple[str, ...]
    biological_predictive_calibration: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.supply_id)
        exact(self.case, RubiscoPairedCase)
        exact(self.context, RubiscoAssayContext)
        exact(self.query, DissolvedGasQuery)
        validate_paired_chemical_selection(self.case, self.context.chemistry)
        require_sorted_unique_strings(self.expected_scenario_ids, field_name="expected_scenario_ids", allow_empty=False)
        if (type(self.scenarios) is not tuple
                or tuple(row.scenario_id for row in self.scenarios) != self.expected_scenario_ids):
            raise ValueError("rate supply drops a selected chemical or closure alternative")
        if len(self.scenarios) > 32 or sum(len(row.points) for row in self.scenarios) > 256:
            raise ValueError("paired rate supply exceeds its bounded scenario or joint-point census")
        for scenario in self.scenarios:
            exact(scenario, PairedRateScenario)
            if (scenario.ledger.case, scenario.ledger.context) != (self.case.identity, self.context.identity):
                raise ValueError("rate scenario changes the exact paired case or assay context")
            if self.case.case_role == "NO_CHANGE" and any(point.wild_type != point.mutant for point in scenario.points):
                raise ValueError("no-change control cannot acquire a finite molecular rate effect")
        identities(self.shared_sources, allow_empty=True)
        require_sorted_unique_strings(self.prerequisite_requirement_ids, field_name="prerequisite_requirement_ids")
        if self.biological_predictive_calibration != "NOT_ESTABLISHED":
            raise ValueError("conditional rate supports cannot grant biological calibration")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.supply_id, self)
