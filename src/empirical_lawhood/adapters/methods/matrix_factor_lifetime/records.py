"""Strict factor-event rules, complete root roles and finite observed lifetimes.

Thresholds have no defaults: development selects them explicitly. This contract
does not supply a frozen confirmation criterion or scientific authority.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

EXPOSURE = "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
VIEWS = ("PRIMARY", "FINE")


def _int(value, *, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("factor-event integer operand is invalid")


@dataclass(frozen=True, slots=True)
class ScalarClosureSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-lifetime/scalar-closure-spec"
    spec_id: str
    normalization_owner: ArtifactIdentity
    threshold: Decimal

    def __post_init__(self):
        validate_stable_id(self.spec_id)
        validate_decimal(self.threshold, field_name="original scalar closure threshold")
        if self.threshold != Decimal("0.30"):
            raise ValueError("historical scalar closure comparison must preserve its original 0.30 threshold")


@dataclass(frozen=True, slots=True)
class FactorEventSpec(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-lifetime/event-spec"
    spec_id: str
    sectors: tuple[str, ...]
    lattice: tuple[int, ...]
    primary_dt: Decimal
    risk_start_tick: int
    trailing_persistence_ticks: int
    associative_leakage_maximum: Decimal
    lie_leakage_maximum: Decimal
    factor_fit_angle_maximum_degrees: Decimal
    adjacent_angle_maximum_degrees: Decimal
    origin_angle_maximum_degrees: Decimal
    identifiability_relative_gap: Decimal
    identifiability_absolute_fourth: Decimal
    frame_alignment_minimum_overlap: Decimal
    scalar_closure: ScalarClosureSpec | None = None
    exposure: str = EXPOSURE

    def __post_init__(self):
        validate_stable_id(self.spec_id)
        if self.exposure != EXPOSURE or self.sectors not in (("X",), ("Y",), ("X", "Y")):
            raise ValueError("factor-event rule requires an explicit exposed sector menu")
        if len(self.lattice) < 2 or tuple(sorted(set(self.lattice))) != self.lattice:
            raise ValueError("factor-event lattice must be complete and strictly ordered")
        for tick in self.lattice:
            _int(tick)
        stride = self.lattice[1] - self.lattice[0]
        if self.lattice[0] != 0 or any(b-a != stride for a, b in zip(self.lattice, self.lattice[1:], strict=False)):
            raise ValueError("factor population needs one common uniform observation lattice")
        _int(self.risk_start_tick)
        _int(self.trailing_persistence_ticks)
        if self.risk_start_tick not in self.lattice or self.trailing_persistence_ticks % stride:
            raise ValueError("risk cutoff and trailing duration must belong to the common lattice")
        for name in ("primary_dt", "associative_leakage_maximum", "lie_leakage_maximum",
                     "factor_fit_angle_maximum_degrees", "adjacent_angle_maximum_degrees",
                     "origin_angle_maximum_degrees", "identifiability_relative_gap",
                     "identifiability_absolute_fourth", "frame_alignment_minimum_overlap"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if self.primary_dt == 0 or self.frame_alignment_minimum_overlap > 1:
            raise ValueError("factor-event clock or frame overlap is invalid")
        if any(getattr(self, name) > 90 for name in ("factor_fit_angle_maximum_degrees",
                "adjacent_angle_maximum_degrees", "origin_angle_maximum_degrees")):
            raise ValueError("factor-event principal angles must lie within zero and ninety degrees")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.spec_id, self)


@dataclass(frozen=True, slots=True)
class FactorRootRole(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-lifetime/root-role"
    root_id: str
    independent_unit_id: str
    family_id: str
    source: ObjectIdentity
    native_arrays: ArtifactIdentity
    native_result: ArtifactIdentity
    exposure: str = EXPOSURE

    def __post_init__(self):
        for value in (self.root_id, self.independent_unit_id, self.family_id):
            validate_stable_id(value)
        if self.exposure != EXPOSURE:
            raise ValueError("historical exposed factor roots cannot be promoted")


@dataclass(frozen=True, slots=True)
class FactorPopulation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-lifetime/population"
    population_id: str
    roots: tuple[FactorRootRole, ...]
    source_inventory: ArtifactIdentity
    provenance_limitations: tuple[str, ...]
    exposure: str = EXPOSURE

    def __post_init__(self):
        validate_stable_id(self.population_id)
        ids = tuple(r.root_id for r in self.roots)
        if not ids or ids != tuple(sorted(set(ids))) or len({r.independent_unit_id for r in self.roots}) != len(ids):
            raise ValueError("factor population loses whole independent-root roles")
        if self.exposure != EXPOSURE or any(r.exposure != self.exposure for r in self.roots):
            raise ValueError("factor population exposure differs")
        if self.provenance_limitations != tuple(sorted(set(self.provenance_limitations))):
            raise ValueError("factor provenance limitations must be exact and unique")
        for reason in self.provenance_limitations:
            validate_stable_id(reason)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.population_id, self)


@dataclass(frozen=True, slots=True)
class FactorObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-lifetime/observation"
    tick: int
    status: str
    identifiable: bool | None
    raw_admitted: bool | None
    causal_admitted: bool | None
    scalar_closure_pass: bool | None
    associative_leakage: Decimal | None
    lie_leakage: Decimal | None
    factor_fit_angle_degrees: Decimal | None
    adjacent_angle_degrees: Decimal | None
    origin_angle_degrees: Decimal | None
    alignment_ambiguous: bool
    reason: str | None
    scalar_closure_ratio: Decimal | None = None

    def __post_init__(self):
        _int(self.tick)
        if self.status not in ("AVAILABLE", "UNIDENTIFIABLE", "UNAVAILABLE", "NUMERICAL_INVALID"):
            raise ValueError("factor observation has an unknown availability state")
        if type(self.alignment_ambiguous) is not bool:
            raise ValueError("factor alignment ambiguity must be explicit")
        for value in (self.identifiable, self.raw_admitted, self.causal_admitted, self.scalar_closure_pass):
            if value is not None and type(value) is not bool:
                raise ValueError("factor observation flags must remain tri-state")
        if self.scalar_closure_ratio is None:
            if self.scalar_closure_pass is not None:
                raise ValueError("scalar closure comparison lacks its independent numerical operand")
        else:
            validate_decimal(self.scalar_closure_ratio, field_name="scalar closure ratio", minimum=Decimal(0))
            if self.scalar_closure_pass is None:
                raise ValueError("measured scalar closure requires its retained threshold outcome")
        metrics = (self.associative_leakage, self.lie_leakage, self.factor_fit_angle_degrees)
        if self.status == "AVAILABLE":
            if self.identifiable is not True or any(v is None for v in metrics) or self.raw_admitted is None or self.causal_admitted is None or self.reason is not None:
                raise ValueError("available factor observation lacks identification and measured criterion")
        elif self.raw_admitted is not None or self.causal_admitted is not None or any(v is not None for v in metrics) or self.adjacent_angle_degrees is not None or self.origin_angle_degrees is not None or self.reason is None:
            raise ValueError("unknown factor observation must not manufacture a criterion exit")
        if self.status == "UNIDENTIFIABLE" and self.identifiable is not False:
            raise ValueError("unidentifiable factor flag differs")
        for value in (*metrics, self.adjacent_angle_degrees, self.origin_angle_degrees):
            if value is not None:
                validate_decimal(value, field_name="factor metric", minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class FactorLifetime(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-lifetime/lifetime"
    origin_tick: int | None
    onset: str
    disposition: str
    last_known_survival_tick: int | None
    exit_upper_tick: int | None
    unavailable_ticks: tuple[int, ...]

    def __post_init__(self):
        if self.onset not in ("LEFT_PRESENT", "OBSERVED_ADMISSION", "UNRESOLVED_ADMISSION", "NEVER_ADMITTED", "UNKNOWN") or self.disposition not in ("EXIT_INTERVAL", "RIGHT_CENSORED", "UNKNOWN", "NOT_AT_RISK"):
            raise ValueError("factor lifetime loses its admission/censoring semantics")
        for value in (self.origin_tick, self.last_known_survival_tick, self.exit_upper_tick):
            if value is not None:
                _int(value)
        if tuple(sorted(set(self.unavailable_ticks))) != self.unavailable_ticks:
            raise ValueError("factor lifetime unavailable intervals must remain ordered")
        if self.disposition == "NOT_AT_RISK":
            if self.onset != "NEVER_ADMITTED" or self.origin_tick is not None or self.last_known_survival_tick is not None or self.exit_upper_tick is not None:
                raise ValueError("never-admitted root cannot contribute an observed lifetime")
        elif self.origin_tick is None and self.disposition != "UNKNOWN":
            raise ValueError("observed lifetime needs an actual causal origin")
        if self.origin_tick is not None and (self.last_known_survival_tick is None or self.last_known_survival_tick < self.origin_tick):
            raise ValueError("factor lifetime reverses its origin clock")
        if self.disposition == "EXIT_INTERVAL":
            if self.exit_upper_tick is None or self.exit_upper_tick <= self.last_known_survival_tick or self.unavailable_ticks:
                raise ValueError("observed exit must have a complete adjacent interval")
        elif self.exit_upper_tick is not None:
            raise ValueError("censoring or missing observation cannot supply an observed exit")


@dataclass(frozen=True, slots=True)
class FactorTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-lifetime/trace"
    root: FactorRootRole
    rule: ObjectIdentity
    view: str
    sector: str
    observations: tuple[FactorObservation, ...]
    moving_lifetime: FactorLifetime
    origin_fixed_lifetime: FactorLifetime
    diagnostics: ArtifactIdentity | None
    diagnostic_members: tuple[MatrixArrayMember, ...] = ()

    def __post_init__(self):
        if self.view not in VIEWS or self.sector not in ("X", "Y") or self.rule.object_schema != FactorEventSpec.SCHEMA:
            raise ValueError("factor trace changes its rule, sector or numerical view")
        ticks = tuple(x.tick for x in self.observations)
        if not ticks or ticks != tuple(sorted(set(ticks))):
            raise ValueError("factor trace loses its complete observation order")
        members = self.diagnostic_members
        if self.diagnostics is None:
            if members:
                raise ValueError("absent factor diagnostics cannot supply a member manifest")
        elif not members or tuple(m.name for m in members) != tuple(sorted({m.name for m in members})) or sum(m.size_bytes for m in members) > MAXIMUM_MATRIX_ARRAY_BYTES or not 0 < self.diagnostics.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES:
            raise ValueError("factor diagnostics lose their exact bounded scientific array manifest")


@dataclass(frozen=True, slots=True)
class FactorPopulationResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-lifetime/population-result"
    result_id: str
    population: FactorPopulation
    rule: FactorEventSpec
    traces: tuple[FactorTrace, ...]
    producing_provenance: NumericalProducingProvenance
    exposure: str = EXPOSURE

    def __post_init__(self):
        validate_stable_id(self.result_id)
        expected = tuple((r.root_id, view, sector) for r in self.population.roots for view in VIEWS for sector in self.rule.sectors)
        actual = tuple((t.root.root_id, t.view, t.sector) for t in self.traces)
        if actual != expected or self.exposure != EXPOSURE:
            raise ValueError("factor result omits or substitutes the full root/view/sector census")
        for trace in self.traces:
            if trace.root != next(r for r in self.population.roots if r.root_id == trace.root.root_id) or trace.rule != self.rule.identity or tuple(o.tick for o in trace.observations) != self.rule.lattice:
                raise ValueError("factor result changes source, event rule or common population lattice")
