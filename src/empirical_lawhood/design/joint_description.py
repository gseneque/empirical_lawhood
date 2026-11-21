# SPDX-License-Identifier: MPL-2.0
"""Editable finite preparation/action/receiver/horizon and description menus."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.joint_description import FAMILIES, MAX_BYTES, PREFIX, exact_identity, finite, finite_json, text
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id

PROTOCOL_ID = "joint-description.development"


def json_text(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class Description(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/description"
    description_id: str
    features: tuple[str, ...]
    model: str
    state_dimension: int
    interface_dimension: int
    memory_dimension: int
    memory_samples: int
    rationale: str
    forecast_work_units: Decimal = Decimal("0")
    forecast_work_unit: str = "normalized-scalar-operation"
    forecast_work_basis: str = "Supplied-feature fixture; declared feature-construction work is zero."

    def __post_init__(self):
        validate_stable_id(self.description_id)
        if (self.model not in ("ridge", "fixed") or type(self.features) is not tuple or not self.features
                or any(type(feature) is not str or not feature.strip() or feature != feature.strip() for feature in self.features)
                or len(set(self.features)) != len(self.features)):
            raise ValueError("description requires a supported model and distinct predictor coordinates")
        if self.model == "fixed" and len(self.features) != 1:
            raise ValueError("fixed physical forecasts expose exactly one pre-outcome prediction")
        if any(type(v) is not int or v < 0 for v in (self.state_dimension, self.interface_dimension,
                self.memory_dimension, self.memory_samples)):
            raise ValueError("description costs and interpretation must be explicit")
        if (self.memory_samples == 0) != (self.memory_dimension == 0):
            raise ValueError("retained memory requires both a per-sample dimension and a sample count")
        text(self.rationale, "description rationale")
        if type(self.forecast_work_units) is not Decimal:
            raise TypeError("authored forecast construction work uses exact Decimal values")
        finite(self.forecast_work_units)
        if self.forecast_work_units < 0:
            raise ValueError("forecast construction work cannot be negative")
        validate_stable_id(self.forecast_work_unit, field_name="forecast work unit")
        text(self.forecast_work_basis, "forecast work estimate basis")


@dataclass(frozen=True, slots=True)
class ReceiverPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/receiver-policy"
    receiver_id: str
    units: str
    target: Decimal
    scale: Decimal
    max_abs_error: Decimal
    weight: Decimal
    safety_lower: Decimal | None = None
    safety_upper: Decimal | None = None

    def __post_init__(self):
        validate_stable_id(self.receiver_id, field_name="receiver")
        text(self.units, "receiver units")
        for value in (self.target, self.scale, self.max_abs_error, self.weight,
                *(() if self.safety_lower is None else (self.safety_lower,)),
                *(() if self.safety_upper is None else (self.safety_upper,))):
            if type(value) is not Decimal:
                raise TypeError("receiver thresholds and scales use exact Decimal values")
            finite(value)
        if self.scale <= 0 or self.max_abs_error <= 0 or self.weight <= 0:
            raise ValueError("receiver scales, tolerances and weights must be positive")
        if self.safety_lower is not None and self.safety_upper is not None and self.safety_lower >= self.safety_upper:
            raise ValueError("safety bounds must form a nonempty interval")


@dataclass(frozen=True, slots=True)
class Economics(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/economics"
    accounting_unit: str = "authored-cost-unit"
    state_price: Decimal = Decimal("0.001")
    interface_price: Decimal = Decimal("0.001")
    memory_price: Decimal = Decimal("0.001")
    compute_price: Decimal = Decimal("0.0001")
    action_price: Decimal = Decimal("0")
    reuse_count: int = 1
    missing_penalty: Decimal = Decimal("1000000")
    safety_penalty: Decimal = Decimal("1000000")
    minimum_coverage: Decimal = Decimal("0.9")
    maximum_control_regret: Decimal = Decimal("1")
    ridge_penalty: Decimal = Decimal("0.001")

    def __post_init__(self):
        text(self.accounting_unit, "economic accounting unit")
        if type(self.reuse_count) is not int or self.reuse_count < 1:
            raise ValueError("explicit cost units and positive reuse count are required")
        for name in ("state_price", "interface_price", "memory_price", "compute_price", "action_price",
                "missing_penalty", "safety_penalty", "minimum_coverage", "maximum_control_regret", "ridge_penalty"):
            value = getattr(self, name)
            if type(value) is not Decimal:
                raise TypeError("economic assumptions use exact Decimal values")
            finite(value)
            if value < 0:
                raise ValueError("economic assumptions must be nonnegative")
        if not 0 < self.minimum_coverage <= 1 or self.missing_penalty <= 0 or self.safety_penalty <= 0 or self.ridge_penalty <= 0:
            raise ValueError("coverage, penalties and regularization must be strictly positive")


@dataclass(frozen=True, slots=True)
class JointSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/specification"
    specification_id: str
    family_id: str
    question: str
    seed: int
    calibration_unit_ids: tuple[str, ...]
    evaluation_unit_ids: tuple[str, ...]
    actions: tuple[Decimal, ...]
    horizons: tuple[Decimal, ...]
    receivers: tuple[ReceiverPolicy, ...]
    descriptions: tuple[Description, ...]
    parameters_json: str
    economics: Economics

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        text(self.question, "scientific question")
        if self.family_id not in FAMILIES or type(self.seed) is not int or not 0 <= self.seed < 2**63:
            raise ValueError("specification requires its family, scientific question and bounded seed")
        for units in (self.calibration_unit_ids, self.evaluation_unit_ids):
            if type(units) is not tuple or len(units) < 2 or len(units) > 4096 or tuple(sorted(set(units))) != units:
                raise ValueError("each independent cohort needs two through 4096 unique sorted roots")
            for unit in units:
                validate_stable_id(unit)
        if set(self.calibration_unit_ids) & set(self.evaluation_unit_ids):
            raise ValueError("calibration and evaluation roots must be disjoint")
        for values in (self.actions, self.horizons):
            if type(values) is not tuple or not values or len(values) > 64:
                raise ValueError("action/horizon menus require bounded immutable coordinates")
            for value in values:
                if type(value) is not Decimal:
                    raise TypeError("authored action/horizon coordinates use Decimal")
                finite(value)
            if tuple(sorted(set(values))) != values:
                raise ValueError("action/horizon menus require sorted unique coordinates")
        if any(h <= 0 for h in self.horizons):
            raise ValueError("horizons must be positive")
        for rows, name, row_type in ((self.receivers, "receiver_id", ReceiverPolicy), (self.descriptions, "description_id", Description)):
            if type(rows) is not tuple or not rows or any(type(row) is not row_type for row in rows):
                raise TypeError("scientific menus require immutable exact receiver/description records")
            if tuple(getattr(r, name) for r in rows) != tuple(sorted({getattr(r, name) for r in rows})):
                raise ValueError("receiver/description menus must be nonempty sorted and unique")
            for row in rows:
                row.__post_init__()
        if len(self.descriptions) < 2 or len(self.descriptions) > 32 or len(self.receivers) > 32:
            raise ValueError("joint-description comparisons need two through 32 descriptions and at most 32 receivers")
        if len({description.forecast_work_unit for description in self.descriptions}) != 1:
            raise ValueError("all compared descriptions require the same authored forecast work unit")
        if len(self.all_unit_ids) * len(self.actions) * len(self.horizons) * len(self.receivers) > 200000:
            raise ValueError("split the study into declared independent replicates below the 200000-row custody bound")
        parameters = finite_json(self.parameters_json)
        if type(parameters) is not dict or json_text(parameters) != self.parameters_json:
            raise ValueError("family parameters must use deterministic finite JSON")
        if len(self.parameters_json.encode("utf-8")) > MAX_BYTES:
            raise ValueError("scientific parameters exceed the bounded configuration payload")
        if type(self.economics) is not Economics:
            raise TypeError("specification requires explicit economic assumptions")
        self.economics.__post_init__()

    @property
    def all_unit_ids(self):
        return tuple(sorted((*self.calibration_unit_ids, *self.evaluation_unit_ids)))

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class SelectedInputs(CanonicalRecord):
    """Copied raw input bytes and operational device; no history compatibility."""
    SCHEMA: ClassVar[str] = PREFIX + "/selected-inputs"
    record_id: str
    specification: ObjectIdentity
    device: str
    archive_json: str | None
    archive_sha256: str | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_identity(self.specification, JointSpecification.SCHEMA)
        if self.device not in ("cpu", "gpu"):
            raise ValueError("select CPU or GPU explicitly")
        if (self.archive_json is None) != (self.archive_sha256 is None):
            raise ValueError("selected archive bytes and their digest are inseparable")
        if self.archive_json is not None:
            finite_json(self.archive_json)
            validate_sha256(self.archive_sha256, field_name="raw input digest")
            if len(self.archive_json.encode("utf-8")) > MAX_BYTES:
                raise ValueError("raw input payload exceeds its bounded custody limit")
            if sha256(self.archive_json.encode()).hexdigest() != self.archive_sha256:
                raise ValueError("selected archive bytes differ from their exact digest")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
