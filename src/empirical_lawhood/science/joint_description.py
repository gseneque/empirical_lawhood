# SPDX-License-Identifier: MPL-2.0
"""Substrate-independent observations for finite joint-description experiments.

Runtime trials use finite machine numbers at the numerical boundary. Persisted
scientific products use Decimal and strict canonical records. Predictor records
have no field capable of carrying outcomes or evaluator-only diagnostics.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id

PREFIX = "empirical-lawhood/joint-description"
FAMILIES = tuple(f"R{i:02d}" for i in range(1, 23))
MAX_BYTES = 64 * 1024**2
# Calibration, predictor and outcome products span many independently bounded roots.
MAX_COHORT_BYTES = 128 * 1024**2


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError("joint-description quantities must be finite numbers")
    try:
        valid = math.isfinite(float(value))
    except (ValueError, OverflowError):
        valid = False
    if not valid:
        raise ValueError("joint-description quantities must be finite machine numbers")
    return value


def pairs(values):
    if type(values) is not tuple or any(type(pair) is not tuple or len(pair) != 2 for pair in values):
        raise TypeError("named numerical coordinates require immutable two-item tuples")
    if any(type(key) is not str or not key.strip() for key, _ in values):
        raise ValueError("a scientific coordinate requires a nonempty name")
    if tuple(key for key, _ in values) != tuple(sorted({key for key, _ in values})):
        raise ValueError("named numerical coordinates must be unique and sorted")
    for key, value in values:
        finite(value)


def text(value, label, *, allow_empty=False):
    if type(value) is not str or (not allow_empty and not value.strip()) or value != value.strip():
        raise ValueError(f"{label} must be {'possibly empty' if allow_empty else 'nonempty'} trimmed text")


def exact_identity(value, schema=None):
    if type(value) is not ObjectIdentity:
        raise TypeError("scientific lineage requires an exact ObjectIdentity")
    value.__post_init__()
    if schema is not None and value.object_schema != schema:
        raise ValueError("scientific lineage names a different record schema")


def exact_decimal(value):
    if type(value) is not Decimal:
        raise TypeError("retained numerical values use exact Decimal values")
    finite(value)


def coordinates(unit_id, action, horizon, receiver_id, *, retained):
    validate_stable_id(unit_id, field_name="independent unit")
    validate_stable_id(receiver_id, field_name="receiver")
    for value in (action, horizon):
        exact_decimal(value) if retained else finite(value)
    if horizon <= 0:
        raise ValueError("trial horizons must be positive")


def finite_json(payload):
    """Parse exact supplied JSON, rejecting nonfinite and ambiguous object keys."""
    if type(payload) is not str:
        raise TypeError("JSON content must be an immutable string")
    def reject(value):
        raise ValueError(f"nonfinite JSON constant {value}")
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result
    value = json.loads(payload, parse_constant=reject, object_pairs_hook=unique)
    def check(item):
        if isinstance(item, dict):
            for child in item.values():
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)
        elif type(item) in (int, float):
            finite(item)
    check(value)
    return value


def _frozen_parameter(value):
    if isinstance(value, Mapping):
        if any(type(key) is not str or not key for key in value):
            raise ValueError("scientific parameter names must be nonempty strings")
        return MappingProxyType({key: _frozen_parameter(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_frozen_parameter(item) for item in value)
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float, Decimal):
        finite(value)
        return value
    raise TypeError("scientific parameters require finite JSON-like immutable values")


def source_metadata(source_kind, provenance):
    text(source_kind, "source kind")
    if type(provenance) is not tuple or any(type(value) is not str or not value.strip() for value in provenance):
        raise TypeError("source provenance requires immutable nonempty text entries")


@dataclass(frozen=True, slots=True)
class TrialRequest:
    family_id: str
    seed: int
    unit_ids: tuple[str, ...]
    split: str
    actions: tuple[float, ...]
    horizons: tuple[float, ...]
    parameters: Mapping[str, object]
    input_path: Path | None = None
    device: str = "cpu"
    input_json: str | None = None

    def __post_init__(self):
        if self.family_id not in FAMILIES or self.split not in ("calibration", "evaluation"):
            raise ValueError("unknown family or scientific split")
        if type(self.seed) is not int or not 0 <= self.seed < 2**63:
            raise ValueError("seed must be a nonnegative signed-64-bit integer")
        if type(self.unit_ids) is not tuple or not self.unit_ids or tuple(sorted(set(self.unit_ids))) != self.unit_ids:
            raise ValueError("the complete independent-unit census must be sorted and unique")
        for unit in self.unit_ids:
            validate_stable_id(unit, field_name="independent unit")
        for values in (self.actions, self.horizons):
            if type(values) is not tuple or not values or len(set(values)) != len(values):
                raise ValueError("action and horizon menus must be nonempty and unique")
            for value in values:
                finite(value)
        if any(h <= 0 for h in self.horizons) or self.device not in ("cpu", "gpu"):
            raise ValueError("positive horizons and an explicit CPU/GPU selection are required")
        if not isinstance(self.parameters, Mapping):
            raise TypeError("scientific parameters require a mapping")
        object.__setattr__(self, "parameters", _frozen_parameter(self.parameters))
        if self.input_path is not None and not isinstance(self.input_path, Path):
            raise TypeError("raw-input paths require pathlib.Path")
        if self.input_path is not None and self.input_json is not None:
            raise ValueError("select either an input path or exact input JSON, never both")
        if self.input_json is not None:
            finite_json(self.input_json)


@dataclass(frozen=True, slots=True)
class TrialRow:
    unit_id: str
    action: float
    horizon: float
    receiver_id: str
    features: tuple[tuple[str, float], ...]
    outcome: float | None
    status: str = "supported"
    reason: str = ""
    work_units: float = 0.0
    diagnostics: tuple[tuple[str, float], ...] = ()

    def __post_init__(self):
        coordinates(self.unit_id, self.action, self.horizon, self.receiver_id, retained=False)
        finite(self.work_units)
        if self.work_units < 0:
            raise ValueError("trial horizon/work units are invalid")
        pairs(self.features); pairs(self.diagnostics)
        if self.outcome is not None:
            finite(self.outcome)
        if self.status not in ("supported", "unsupported", "failed"):
            raise ValueError("unknown trial disposition")
        if self.status == "supported" and self.outcome is None:
            raise ValueError("supported trial requires its observed receiver")
        if self.status != "supported" and not self.reason:
            raise ValueError("unavailable trials retain their explicit reason")
        text(self.reason, "trial reason", allow_empty=True)

    @property
    def key(self):
        return self.unit_id, self.action, self.horizon, self.receiver_id


@dataclass(frozen=True, slots=True)
class TrialBatch:
    family_id: str
    split: str
    rows: tuple[TrialRow, ...]
    source_kind: str
    provenance: tuple[str, ...] = ()

    def __post_init__(self):
        if self.family_id not in FAMILIES or self.split not in ("calibration", "evaluation"):
            raise ValueError("trial batch requires its scientific family, split and source kind")
        source_metadata(self.source_kind, self.provenance)
        if type(self.rows) is not tuple or not self.rows or any(type(row) is not TrialRow for row in self.rows):
            raise ValueError("trial batch requires exact nonempty rows")
        if len({row.key for row in self.rows}) != len(self.rows):
            raise ValueError("trial batch repeats an action/horizon/receiver within an independent unit")
        for row in self.rows:
            row.__post_init__()

    def validate_census(self, request, receivers):
        if type(request) is not TrialRequest:
            raise TypeError("trial census requires its exact authored request")
        request.__post_init__()
        if type(receivers) is not tuple or not receivers or len(set(receivers)) != len(receivers):
            raise ValueError("receiver census must be immutable, nonempty and distinct")
        expected = {(u, float(a), float(h), r) for u in request.unit_ids
                    for a in request.actions for h in request.horizons for r in receivers}
        if self.family_id != request.family_id or self.split != request.split or {r.key for r in self.rows} != expected:
            raise ValueError("trial producer changed the complete authored Cartesian census")


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


def decimal(value):
    finite(value)
    return Decimal(str(value))


@dataclass(frozen=True, slots=True)
class PredictorRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/predictor-row"
    unit_id: str
    action: Decimal
    horizon: Decimal
    receiver_id: str
    features: tuple[tuple[str, Decimal], ...]

    def __post_init__(self):
        coordinates(self.unit_id, self.action, self.horizon, self.receiver_id, retained=True)
        pairs(self.features)
        if any(type(value) is not Decimal for _, value in self.features):
            raise TypeError("retained features use Decimal")

    @property
    def key(self):
        return self.unit_id, self.action, self.horizon, self.receiver_id


@dataclass(frozen=True, slots=True)
class OutcomeRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/outcome-row"
    unit_id: str
    action: Decimal
    horizon: Decimal
    receiver_id: str
    outcome: Decimal | None
    status: str
    reason: str
    work_units: Decimal
    diagnostics: tuple[tuple[str, Decimal], ...]

    def __post_init__(self):
        coordinates(self.unit_id, self.action, self.horizon, self.receiver_id, retained=True)
        exact_decimal(self.work_units)
        if self.work_units < 0:
            raise ValueError("retained acquisition work cannot be negative")
        if self.outcome is not None:
            exact_decimal(self.outcome)
        if self.status not in ("supported", "unsupported", "failed"):
            raise ValueError("unknown outcome disposition")
        if self.status == "supported" and self.outcome is None:
            raise ValueError("supported outcome is absent")
        if self.status != "supported" and not self.reason:
            raise ValueError("unavailable outcome needs a reason")
        text(self.reason, "outcome reason", allow_empty=True)
        pairs(self.diagnostics)
        for _, value in self.diagnostics:
            exact_decimal(value)

    @property
    def key(self):
        return self.unit_id, self.action, self.horizon, self.receiver_id


def table(record, row_type):
    validate_stable_id(record.record_id)
    exact_identity(record.specification, PREFIX + "/specification")
    if type(record.rows) is not tuple or not record.rows or any(type(row) is not row_type for row in record.rows):
        raise TypeError("scientific tables require an immutable nonempty exact row census")
    for row in record.rows:
        row.__post_init__()
    if len({r.key for r in record.rows}) != len(record.rows):
        raise ValueError("scientific table must preserve a nonempty unique census")
    if tuple(sorted(record.rows, key=lambda r: r.key)) != record.rows:
        raise ValueError("scientific table rows must be canonically ordered")


@dataclass(frozen=True, slots=True)
class Predictors(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/predictors"
    record_id: str
    specification: ObjectIdentity
    rows: tuple[PredictorRow, ...]
    source_kind: str
    provenance: tuple[str, ...]

    def __post_init__(self):
        table(self, PredictorRow)
        source_metadata(self.source_kind, self.provenance)

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class Outcomes(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/outcomes"
    record_id: str
    specification: ObjectIdentity
    rows: tuple[OutcomeRow, ...]
    source_kind: str
    provenance: tuple[str, ...]

    def __post_init__(self):
        table(self, OutcomeRow)
        source_metadata(self.source_kind, self.provenance)

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class Calibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/calibration"
    record_id: str
    specification: ObjectIdentity
    predictors: Predictors
    outcomes: Outcomes

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_identity(self.specification, PREFIX + "/specification")
        if type(self.predictors) is not Predictors or type(self.outcomes) is not Outcomes:
            raise TypeError("calibration requires exact predictor and outcome records")
        self.predictors.__post_init__()
        self.outcomes.__post_init__()
        if self.predictors.specification != self.specification or self.outcomes.specification != self.specification:
            raise ValueError("calibration changed its authored specification")
        if tuple(r.key for r in self.predictors.rows) != tuple(r.key for r in self.outcomes.rows):
            raise ValueError("calibration predictors and outcomes have different censuses")
        if (self.predictors.source_kind, self.predictors.provenance) != (self.outcomes.source_kind, self.outcomes.provenance):
            raise ValueError("calibration predictors and outcomes substituted their source provenance")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class FittedReceiver(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/fitted-receiver"
    description_id: str
    receiver_id: str
    feature_names: tuple[str, ...]
    coefficients: tuple[Decimal, ...]
    center: tuple[Decimal, ...]
    scale: tuple[Decimal, ...]
    status: str
    reason: str

    def __post_init__(self):
        validate_stable_id(self.description_id, field_name="description")
        validate_stable_id(self.receiver_id, field_name="receiver")
        if (type(self.feature_names) is not tuple or not self.feature_names
                or any(type(name) is not str or not name for name in self.feature_names)
                or len(set(self.feature_names)) != len(self.feature_names)):
            raise ValueError("fitted receiver requires an immutable distinct feature layout")
        if any(type(values) is not tuple for values in (self.coefficients, self.center, self.scale)):
            raise TypeError("fitted numerical arrays must be immutable tuples")
        if self.status not in ("fitted", "unavailable"):
            raise ValueError("unknown fitted-model disposition")
        if self.status == "fitted" and (len(self.coefficients) != len(self.feature_names) + 1
                or len(self.center) != len(self.feature_names) or len(self.scale) != len(self.feature_names)):
            raise ValueError("fitted coefficients do not match the declared feature layout")
        for value in (*self.coefficients, *self.center, *self.scale):
            exact_decimal(value)
        if self.status == "fitted" and any(value <= 0 for value in self.scale):
            raise ValueError("fitted feature scales must be strictly positive")
        text(self.reason, "fit reason", allow_empty=self.status == "fitted")
        if self.status == "unavailable" and any((self.coefficients, self.center, self.scale)):
            raise ValueError("an unavailable fit cannot retain active numerical coefficients")


@dataclass(frozen=True, slots=True)
class Model(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/model"
    record_id: str
    specification: ObjectIdentity
    calibration: ObjectIdentity
    fits: tuple[FittedReceiver, ...]
    calibration_scores: tuple[tuple[str, Decimal], ...]
    selected_description: str
    selection_scope: str = "CALIBRATION_ROOT_CROSSFIT_ONLY"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_identity(self.specification, PREFIX + "/specification")
        exact_identity(self.calibration, Calibration.SCHEMA)
        if self.selection_scope != "CALIBRATION_ROOT_CROSSFIT_ONLY":
            raise ValueError("model selection cannot access evaluation outcomes")
        if type(self.fits) is not tuple or not self.fits or any(type(row) is not FittedReceiver for row in self.fits):
            raise TypeError("model requires immutable exact fitted-receiver records")
        keys = tuple((r.description_id, r.receiver_id) for r in self.fits)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("model description/receiver census must be sorted and unique")
        for row in self.fits:
            row.__post_init__()
        descriptions = {r.description_id for r in self.fits}
        receivers = {r.receiver_id for r in self.fits}
        if set(keys) != {(d, r) for d in descriptions for r in receivers}:
            raise ValueError("model omits a description/receiver fit disposition")
        pairs(self.calibration_scores)
        for _, value in self.calibration_scores:
            exact_decimal(value)
        if {d for d, _ in self.calibration_scores} != descriptions or self.selected_description not in descriptions:
            raise ValueError("model scores and selected description must match its complete fit census")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class ForecastRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/forecast-row"
    unit_id: str
    action: Decimal
    horizon: Decimal
    receiver_id: str
    description_id: str
    prediction: Decimal | None
    reason: str

    def __post_init__(self):
        coordinates(self.unit_id, self.action, self.horizon, self.receiver_id, retained=True)
        validate_stable_id(self.description_id, field_name="description")
        if self.prediction is not None:
            exact_decimal(self.prediction)
        text(self.reason, "forecast reason", allow_empty=self.prediction is not None)

    @property
    def key(self):
        return self.unit_id, self.action, self.horizon, self.receiver_id, self.description_id


@dataclass(frozen=True, slots=True)
class Forecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/forecast"
    record_id: str
    specification: ObjectIdentity
    model: ObjectIdentity
    predictors: ObjectIdentity
    rows: tuple[ForecastRow, ...]
    selected_actions: tuple[tuple[str, Decimal, str, Decimal | None], ...]

    def __post_init__(self):
        table(self, ForecastRow)
        exact_identity(self.model, Model.SCHEMA)
        exact_identity(self.predictors, Predictors.SCHEMA)
        if (type(self.selected_actions) is not tuple or not self.selected_actions
                or any(type(row) is not tuple or len(row) != 4 for row in self.selected_actions)):
            raise TypeError("forecast requires an immutable complete control-selection census")
        keys = tuple((u, h, d) for u, h, d, _ in self.selected_actions)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("forecast control selections must be sorted and unique")
        expected = {(r.unit_id, r.horizon, r.description_id) for r in self.rows}
        if set(keys) != expected:
            raise ValueError("forecast control selections omit or add a forecast population cell")
        grouped = {}
        for row in self.rows:
            grouped.setdefault((row.unit_id, row.horizon, row.description_id), []).append(row)
        panel = {(r.action, r.receiver_id) for r in self.rows}
        if any({(r.action, r.receiver_id) for r in rows} != panel for rows in grouped.values()):
            raise ValueError("forecast omitted a declared action/receiver within a population cell")
        for unit, horizon, description, action in self.selected_actions:
            validate_stable_id(unit); validate_stable_id(description); exact_decimal(horizon)
            if action is not None:
                exact_decimal(action)
                selected = [r for r in grouped[unit, horizon, description] if r.action == action]
                if not selected or any(r.prediction is None for r in selected):
                    raise ValueError("control choice is absent from its finite fully predicted action panel")

    @property
    def identity(self):
        return identity(self)


@dataclass(frozen=True, slots=True)
class Assessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/assessment"
    record_id: str
    specification: ObjectIdentity
    model: ObjectIdentity
    forecast: ObjectIdentity
    outcomes: ObjectIdentity
    result_json: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_identity(self.specification, PREFIX + "/specification")
        exact_identity(self.model, Model.SCHEMA)
        exact_identity(self.forecast, Forecast.SCHEMA)
        exact_identity(self.outcomes, Outcomes.SCHEMA)
        value = finite_json(self.result_json)
        if type(value) is not dict or value.get("claim_scope") != "FINITE_AUTHORED_MENU_AND_TASK_FAMILY":
            raise ValueError("assessment cannot claim universal minimality")
        if json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) != self.result_json:
            raise ValueError("assessment result requires canonical finite JSON")

    @property
    def identity(self):
        return identity(self)


def split_batch(batch, specification, prefix):
    if type(batch) is not TrialBatch:
        raise TypeError("only an exact complete runtime batch can be split for scientific custody")
    batch.__post_init__()
    exact_identity(specification, PREFIX + "/specification")
    validate_stable_id(prefix)
    rows = tuple(sorted(batch.rows, key=lambda r: r.key))
    predictors = Predictors(prefix + ".predictors", specification,
        tuple(PredictorRow(r.unit_id, decimal(r.action), decimal(r.horizon), r.receiver_id,
            tuple((k, decimal(v)) for k, v in r.features)) for r in rows), batch.source_kind, batch.provenance)
    outcomes = Outcomes(prefix + ".outcomes", specification,
        tuple(OutcomeRow(r.unit_id, decimal(r.action), decimal(r.horizon), r.receiver_id,
            None if r.outcome is None else decimal(r.outcome), r.status, r.reason, decimal(r.work_units),
            tuple((k, decimal(v)) for k, v in r.diagnostics)) for r in rows), batch.source_kind, batch.provenance)
    return predictors, outcomes
