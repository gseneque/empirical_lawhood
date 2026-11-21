# SPDX-License-Identifier: MPL-2.0
"""Small exact records for a complete exposed mass-balance census."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_stable_id


NAMESPACE = "mass-balance"
PREFIX = "empirical-lawhood/" + NAMESPACE
PROTOCOL_ID = NAMESPACE + ".development"
MAX_BYTES = 128 * 1024


def mass(value, maximum=Decimal("1e9")):
    validate_decimal(value, field_name="mass_kg")
    if value < 0 or value > maximum or len(value.as_tuple().digits) > 64 or not -30 <= value.as_tuple().exponent <= 30:
        raise ValueError("starter masses require finite nonnegative kg within the declared decimal bound")


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


@dataclass(frozen=True, slots=True)
class MassScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/scope"
    population_id: str
    source_id: str
    receiver_id: str
    clock_id: str
    units: str = "kg"
    condition: str = "closed-additive-mass"

    def __post_init__(self):
        for value in (self.population_id, self.source_id, self.receiver_id, self.clock_id):
            validate_stable_id(value)
        if self.units != "kg" or self.condition != "closed-additive-mass":
            raise ValueError("starter requires the exact kg unit and closed-additive-mass scope")


@dataclass(frozen=True, slots=True)
class MassObservation(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/observation"
    unit_id: str
    initial_kg: Decimal
    added_kg: Decimal
    final_kg: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        mass(self.initial_kg)
        mass(self.added_kg)
        if self.final_kg is not None:
            mass(self.final_kg)


@dataclass(frozen=True, slots=True)
class MassEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/evidence"
    record_id: str
    scope: MassScope
    independent_unit_ids: tuple[str, ...]
    observations: tuple[MassObservation, ...]
    evidence_scope: str = "EXPOSED_DEVELOPMENT"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.scope) is not MassScope or self.evidence_scope != "EXPOSED_DEVELOPMENT":
            raise ValueError("starter evidence requires its exact exposed scope")
        self.scope.__post_init__()
        require_sorted_unique_strings(self.independent_unit_ids, field_name="independent_unit_ids", allow_empty=False)
        require_sorted_unique_ids(self.observations, attribute="unit_id", field_name="observations")
        if not 1 <= len(self.independent_unit_ids) <= 16 or tuple(row.unit_id for row in self.observations) != self.independent_unit_ids:
            raise ValueError("starter observations must retain the complete one-to-sixteen-unit census")
        for row in self.observations:
            if type(row) is not MassObservation:
                raise TypeError("starter requires exact mass observations")
            row.__post_init__()

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MassPredictor(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/predictor"
    unit_id: str
    initial_kg: Decimal
    added_kg: Decimal

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        mass(self.initial_kg)
        mass(self.added_kg)


@dataclass(frozen=True, slots=True)
class MassOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/outcome"
    unit_id: str
    final_kg: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        if self.final_kg is not None:
            mass(self.final_kg)


def _table(record, row_type):
    validate_stable_id(record.record_id)
    if type(record.scope) is not MassScope or type(record.evidence) is not ObjectIdentity:
        raise TypeError("starter input table requires exact scope and original evidence identity")
    record.scope.__post_init__()
    if (record.evidence.object_schema, record.evidence.object_version) != (MassEvidence.SCHEMA, MassEvidence.VERSION):
        raise ValueError("starter input table changes its original evidence revision")
    require_sorted_unique_ids(record.rows, attribute="unit_id", field_name="rows")
    if not 1 <= len(record.rows) <= 16:
        raise ValueError("starter input table exceeds its declared independent-unit bound")
    for row in record.rows:
        if type(row) is not row_type:
            raise TypeError("starter input table substitutes its exact row role")
        row.__post_init__()


@dataclass(frozen=True, slots=True)
class MassPredictors(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/predictors"
    record_id: str
    scope: MassScope
    evidence: ObjectIdentity
    rows: tuple[MassPredictor, ...]

    def __post_init__(self):
        _table(self, MassPredictor)

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MassOutcomes(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/outcomes"
    record_id: str
    scope: MassScope
    evidence: ObjectIdentity
    rows: tuple[MassOutcome, ...]

    def __post_init__(self):
        _table(self, MassOutcome)

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MassSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/specification"
    specification_id: str
    evidence: ObjectIdentity
    scope: MassScope
    independent_unit_ids: tuple[str, ...]
    tolerance_kg: Decimal
    calculation: str = "initial-plus-added"

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if type(self.scope) is not MassScope or type(self.evidence) is not ObjectIdentity:
            raise TypeError("starter specification requires its exact scope and evidence reference")
        self.scope.__post_init__()
        if (self.evidence.object_schema, self.evidence.object_version) != (MassEvidence.SCHEMA, MassEvidence.VERSION):
            raise ValueError("starter specification changes the supported evidence schema or revision")
        require_sorted_unique_strings(self.independent_unit_ids, field_name="independent_unit_ids", allow_empty=False)
        if len(self.independent_unit_ids) > 16:
            raise ValueError("starter specification exceeds its sixteen-unit bound")
        mass(self.tolerance_kg)
        if self.calculation != "initial-plus-added":
            raise ValueError("unimplemented starter calculation; implement and register its scientific contract first")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MassOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/operation-config"
    config_id: str
    phase: str
    specification: ObjectIdentity
    scope: MassScope
    independent_unit_ids: tuple[str, ...]
    predictors: ObjectIdentity
    outcomes: ObjectIdentity | None
    tolerance_kg: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.phase not in ("predict", "assess") or not self.config_id.endswith("." + self.phase):
            raise ValueError("starter operation requires its code-derived phase and identity")
        if type(self.scope) is not MassScope:
            raise TypeError("starter operation requires its exact scientific scope")
        self.scope.__post_init__()
        require_sorted_unique_strings(self.independent_unit_ids, field_name="independent_unit_ids", allow_empty=False)
        if len(self.independent_unit_ids) > 16:
            raise ValueError("starter operation exceeds its independent-unit bound")
        for reference, kind in ((self.specification, MassSpecification), (self.predictors, MassPredictors)):
            if type(reference) is not ObjectIdentity or (reference.object_schema, reference.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("starter operation changes a required exact input role")
        if self.phase == "predict":
            if self.outcomes is not None or self.tolerance_kg is not None:
                raise ValueError("prediction cannot receive final observations or their assessment selection")
        elif (type(self.outcomes) is not ObjectIdentity or
                (self.outcomes.object_schema, self.outcomes.object_version) != (MassOutcomes.SCHEMA, MassOutcomes.VERSION)):
            raise ValueError("assessment requires its exact original outcome table")
        else:
            mass(self.tolerance_kg)

    @property
    def node_id(self):
        return self.config_id.removeprefix("config.")


@dataclass(frozen=True, slots=True)
class PredictedMass(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/predicted-mass"
    unit_id: str
    final_kg: Decimal

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        mass(self.final_kg, Decimal("2e9"))


def _product(record, row_type, phase):
    validate_stable_id(record.record_id)
    if type(record.config) is not MassOperationConfig or record.config.phase != phase:
        raise ValueError("starter product changes its exact producing configuration")
    record.config.__post_init__()
    if record.record_id != record.config.node_id + ".product":
        raise ValueError("starter product changes its producing operation identity")
    if type(record.rows) is not tuple or tuple(row.unit_id for row in record.rows) != record.config.independent_unit_ids:
        raise ValueError("starter product omits or changes an original independent unit")
    for row in record.rows:
        if type(row) is not row_type:
            raise TypeError("starter product changes its exact row type")
        row.__post_init__()


@dataclass(frozen=True, slots=True)
class MassForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/forecast"
    record_id: str
    config: MassOperationConfig
    rows: tuple[PredictedMass, ...]

    def __post_init__(self):
        _product(self, PredictedMass, "predict")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class MassFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/finding"
    unit_id: str
    predicted_kg: Decimal
    observed_kg: Decimal | None
    absolute_error_kg: Decimal | None
    disposition: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        mass(self.predicted_kg, Decimal("2e9"))
        if self.disposition not in ("SATISFIED", "FALSIFIED", "UNEVALUABLE"):
            raise ValueError("starter finding has an unknown disposition")
        expected_reasons = {"SATISFIED": (), "FALSIFIED": ("MASS_RESIDUAL_EXCEEDS_TOLERANCE",),
                            "UNEVALUABLE": ("FINAL_OBSERVATION_MISSING",)}
        if self.reason_codes != expected_reasons[self.disposition]:
            raise ValueError("starter finding changes its exact disposition reason")
        if self.disposition == "UNEVALUABLE":
            if self.observed_kg is not None or self.absolute_error_kg is not None:
                raise ValueError("missing observations cannot acquire invented values")
        else:
            mass(self.observed_kg)
            mass(self.absolute_error_kg, Decimal("2e9"))


@dataclass(frozen=True, slots=True)
class MassAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/assessment"
    record_id: str
    config: MassOperationConfig
    forecast: ObjectIdentity
    rows: tuple[MassFinding, ...]

    def __post_init__(self):
        _product(self, MassFinding, "assess")
        if type(self.forecast) is not ObjectIdentity or (self.forecast.object_schema, self.forecast.object_version) != (MassForecast.SCHEMA, MassForecast.VERSION):
            raise ValueError("starter assessment requires its exact producing forecast")

    @property
    def identity(self):
        return identity(self)
