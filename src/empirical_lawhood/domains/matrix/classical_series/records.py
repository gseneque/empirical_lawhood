# SPDX-License-Identifier: MPL-2.0
"""Authored choices and exact retained products for the classical matrix series.

The complete root roster has one owner, the specification. Per-root operations
carry only their assigned root. Binary64 numerical payloads have a separate
explicit JSON encoding; canonical identities bind those exact encoded bytes.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.matrix.matrix_array_chunks import ChunkedMatrixArrays, FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, framed_size
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id

NAMESPACE = "matrix-classical-series"
PREFIX = "empirical-lawhood/" + NAMESPACE
PROTOCOL_ID = NAMESPACE + ".development"
PHASES = ("capstone-forecast", "capstone-preparation", "derivations", "e1", "e2", "e3", "e4", "e5", "e6", "sci01", "sci02")
ROLES = ("training", "calibration", "confirmation")
# No arbitrary byte ceiling: the shared custody owner records actual sizes.
MAX_BYTES = None


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON field: " + key)
        result[key] = value
    return result


def json_object(text):
    def invalid(value):
        raise ValueError("nonfinite JSON value: " + value)
    if type(text) is not str:
        raise TypeError("numerical JSON requires text")
    value = json.loads(text, object_pairs_hook=_pairs, parse_constant=invalid)
    if type(value) is not dict:
        raise ValueError("scientific JSON payload must be an object")
    if json_text(value) != text:
        raise ValueError("scientific JSON must use its exact stable encoding")
    return value


def json_text(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def unit_id(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a nonnegative signed 64-bit integer")
    return "root." + str(seed).zfill(19)


@dataclass(frozen=True, slots=True)
class RootAssignment(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/root-assignment"
    seed: int
    role: str

    def __post_init__(self):
        unit_id(self.seed)
        if self.role not in ROLES:
            raise ValueError("root role must be training, calibration or confirmation")

    @property
    def unit_id(self):
        return unit_id(self.seed)


@dataclass(frozen=True, slots=True)
class RetainedInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/retained-input"
    key: str
    identity: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.key)
        if type(self.identity) is not ObjectIdentity:
            raise TypeError("retained input needs its exact original identity")
        if self.identity.object_schema not in (PREFIX + "/acquisition", PREFIX + "/calibration"):
            raise ValueError("only retained acquisition and frozen calibration are reanalysis inputs")
        self.identity.__post_init__()


@dataclass(frozen=True, slots=True)
class RetainedArray(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/retained-array"
    key: str
    identity: ArtifactIdentity

    def __post_init__(self):
        validate_stable_id(self.key)
        if (type(self.identity) is not ArtifactIdentity
                or self.identity.payload_schema != FRAMED_ARRAY_SCHEMA
                or self.identity.media_type != FRAMED_ARRAY_MEDIA):
            raise ValueError("retained native arrays require the exact shared framed transport")
        self.identity.__post_init__()


@dataclass(frozen=True, slots=True)
class SeriesSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/specification"
    specification_id: str
    settings_json: str
    assignments: tuple[RootAssignment, ...]
    study_label: str
    mode: str = "new-development"
    retained_inputs: tuple[RetainedInput, ...] = ()
    evidence_scope: str = "PREDECLARED_DEVELOPMENT"
    retained_arrays: tuple[RetainedArray, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if not self.study_label.strip():
            raise ValueError("a scientific study label is required")
        settings = json_object(self.settings_json)
        phases = settings.get("phases")
        if (type(phases) is not list or not phases or len(set(phases)) != len(phases)
                or set(phases) - set(PHASES)):
            raise ValueError("select implemented classical-series phases explicitly")
        if type(self.assignments) is not tuple or not self.assignments:
            raise ValueError("the complete independent-root roster is required")
        for row in self.assignments:
            if type(row) is not RootAssignment:
                raise TypeError("root assignments require the exact typed record")
            row.__post_init__()
        if tuple(r.seed for r in self.assignments) != tuple(sorted({r.seed for r in self.assignments})):
            raise ValueError("each independent seed has one role; roles must be disjoint and seed-sorted")
        if set(r.role for r in self.assignments) != set(ROLES):
            raise ValueError("declare nonempty TRAIN, CAL and CONF root populations")
        if self.mode not in ("new-development", "reanalysis"):
            raise ValueError("unknown classical-series execution mode")
        expected_scope = "PREDECLARED_DEVELOPMENT" if self.mode == "new-development" else "EXPOSED_REANALYSIS"
        if self.evidence_scope != expected_scope:
            raise ValueError("execution mode changes its explicit evidence scope")
        if type(self.retained_inputs) is not tuple:
            raise TypeError("retained input census must be a tuple")
        for row in self.retained_inputs:
            if type(row) is not RetainedInput:
                raise TypeError("retained input requires exact identity")
            row.__post_init__()
        if tuple(r.key for r in self.retained_inputs) != tuple(sorted({r.key for r in self.retained_inputs})):
            raise ValueError("retained inputs must be uniquely key-sorted")
        if type(self.retained_arrays) is not tuple or any(type(row) is not RetainedArray for row in self.retained_arrays):
            raise TypeError("retained array census needs exact immutable typed entries")
        for row in self.retained_arrays:
            row.__post_init__()
        if tuple(r.key for r in self.retained_arrays) != tuple(sorted({r.key for r in self.retained_arrays})):
            raise ValueError("retained arrays need uniquely sorted keys")
        if self.mode == "new-development" and (self.retained_inputs or self.retained_arrays):
            raise ValueError("new acquisition cannot silently substitute exposed retained products")
        if self.mode == "reanalysis":
            expected = {"calibration"} | {unit_id(r.seed) for r in self.assignments if r.role == "confirmation"}
            if {r.key for r in self.retained_inputs} != expected:
                raise ValueError("reanalysis requires the original frozen calibration and every CONF acquisition")
            if {r.key for r in self.retained_arrays} != {"arrays." + key for key in expected - {"calibration"}}:
                raise ValueError("reanalysis requires every original CONF binary array companion")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)

    @property
    def settings(self):
        return json_object(self.settings_json)

    @property
    def independent_unit_ids(self):
        return tuple(r.unit_id for r in self.assignments)


@dataclass(frozen=True, slots=True)
class SeriesOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/operation-config"
    config_id: str
    phase: str
    specification: ObjectIdentity
    settings_json: str
    assignments: tuple[RootAssignment, ...]
    evidence_scope: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.phase not in ("acquire", "calibrate", "analyse", "summarise", "synthesise") or not self.config_id.endswith("." + self.phase):
            raise ValueError("operation phase and code-derived identity must agree")
        if (type(self.specification) is not ObjectIdentity
                or (self.specification.object_schema, self.specification.object_version) != (SeriesSpecification.SCHEMA, SeriesSpecification.VERSION)):
            raise ValueError("operation requires its original specification identity")
        json_object(self.settings_json)
        if self.evidence_scope not in ("PREDECLARED_DEVELOPMENT", "EXPOSED_REANALYSIS"):
            raise ValueError("operation evidence scope is unsupported")
        if not self.assignments or tuple(r.seed for r in self.assignments) != tuple(sorted({r.seed for r in self.assignments})):
            raise ValueError("operation needs its exact sorted root assignment")
        for row in self.assignments:
            if type(row) is not RootAssignment:
                raise TypeError("operation root must be a typed assignment")
            row.__post_init__()
        if self.phase not in ("calibrate", "synthesise") and len(self.assignments) != 1:
            raise ValueError("native acquisition and analysis are independently recoverable per root")
        if self.phase == "calibrate" and set(r.role for r in self.assignments) != {"training", "calibration"}:
            raise ValueError("calibration cannot receive confirmation roots")
        if self.phase == "synthesise" and any(r.role != "confirmation" for r in self.assignments):
            raise ValueError("population synthesis requires the complete CONF denominator")
        if self.phase == "summarise" and self.assignments[0].role == "confirmation":
            raise ValueError("calibration summaries must not receive CONF roots")
        if self.phase == "analyse" and self.assignments[0].role != "confirmation":
            raise ValueError("primary analysis retains the CONF denominator")

    @property
    def node_id(self):
        return self.config_id.removeprefix("config.")

    @property
    def settings(self):
        return json_object(self.settings_json)


def _product(record, phase, payload_schema):
    if type(record.config) is not SeriesOperationConfig or record.config.phase != phase:
        raise ValueError("result has an incompatible producing operation")
    record.config.__post_init__()
    if record.record_id != record.config.node_id + ".product":
        raise ValueError("result changes its exact producing operation")
    body = json_object(record.payload_json)
    if body.get("schema") != payload_schema:
        raise ValueError("numerical payload schema differs from its typed result")
    if phase not in ("calibrate", "synthesise") and body.get("seed") != record.config.assignments[0].seed:
        raise ValueError("result changes its assigned independent root")
    return body


@dataclass(frozen=True, slots=True)
class Acquisition(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/acquisition"
    record_id: str
    config: SeriesOperationConfig
    payload_json: str
    calibration: ObjectIdentity | None = None
    array_manifest: ChunkedMatrixArrays | None = None
    array_artifact: ArtifactIdentity | None = None

    def __post_init__(self):
        _product(self, "acquire", "classical-series-acquisition.v1")
        if (self.array_manifest is None) != (self.array_artifact is None):
            raise ValueError("array transport requires its exact manifest and complete container")
        if self.array_manifest is not None:
            if type(self.array_manifest) is not ChunkedMatrixArrays or type(self.array_artifact) is not ArtifactIdentity:
                raise TypeError("acquisition requires the shared exact matrix array contracts")
            self.array_manifest.__post_init__()
            if not self.array_manifest.members:
                raise ValueError("classical native acquisition requires its declared physical operand census")
            if (self.array_artifact.payload_schema, self.array_artifact.media_type, self.array_artifact.size_bytes) != (FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA, framed_size(self.array_manifest)):
                raise ValueError("acquisition changes its complete binary array transport")
        role = self.config.assignments[0].role
        if (role == "confirmation") != (self.calibration is not None):
            raise ValueError("CONF acquisition requires its already frozen calibration commitment")
        if self.calibration is not None and self.calibration.object_schema != Calibration.SCHEMA:
            raise ValueError("CONF acquisition changes its frozen calibration type")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def payload(self):
        if self.array_manifest is not None:
            raise ValueError("binary acquisition requires its authenticated array companion")
        return json_object(self.payload_json)

    @property
    def metadata(self):
        return json_object(self.payload_json)


@dataclass(frozen=True, slots=True)
class RootSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/root-summary"
    record_id: str
    config: SeriesOperationConfig
    acquisition: ObjectIdentity
    payload_json: str

    def __post_init__(self):
        _product(self, "summarise", "classical-series-summary.v1")
        if type(self.acquisition) is not ObjectIdentity or self.acquisition.object_schema != Acquisition.SCHEMA:
            raise ValueError("training summary must retain its actual original acquisition")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def payload(self):
        return json_object(self.payload_json)


@dataclass(frozen=True, slots=True)
class Calibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/calibration"
    record_id: str
    config: SeriesOperationConfig
    acquisition_inputs: tuple[ObjectIdentity, ...]
    payload_json: str

    def __post_init__(self):
        _product(self, "calibrate", "classical-series-calibration.v1")
        if len(self.acquisition_inputs) != len(self.config.assignments):
            raise ValueError("calibration loses an assigned TRAIN/CAL root")
        if tuple(p.object_id for p in self.acquisition_inputs) != tuple(sorted({p.object_id for p in self.acquisition_inputs})):
            raise ValueError("calibration inputs require the original sorted complete census")
        for pin in self.acquisition_inputs:
            if type(pin) is not ObjectIdentity or pin.object_schema != RootSummary.SCHEMA:
                raise ValueError("calibration input substitutes an acquired-root summary")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def payload(self):
        return json_object(self.payload_json)


@dataclass(frozen=True, slots=True)
class Analysis(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/analysis"
    record_id: str
    config: SeriesOperationConfig
    acquisition: ObjectIdentity
    calibration: ObjectIdentity
    payload_json: str

    def __post_init__(self):
        _product(self, "analyse", "classical-series-analysis.v1")
        if (type(self.acquisition) is not ObjectIdentity or self.acquisition.object_schema != Acquisition.SCHEMA
                or type(self.calibration) is not ObjectIdentity or self.calibration.object_schema != Calibration.SCHEMA):
            raise ValueError("analysis must retain original acquisition and frozen model identities")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def payload(self):
        return json_object(self.payload_json)


@dataclass(frozen=True, slots=True)
class PopulationSummary(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/population-summary"
    record_id: str
    config: SeriesOperationConfig
    analyses: tuple[ObjectIdentity, ...]
    payload_json: str

    def __post_init__(self):
        _product(self, "synthesise", "classical-series-population-readout.v1")
        if len(self.analyses) != len(self.config.assignments):
            raise ValueError("population summary must retain the complete assigned CONF denominator")
        if tuple(p.object_id for p in self.analyses) != tuple(sorted({p.object_id for p in self.analyses})):
            raise ValueError("population synthesis repeats or reorders a root result")
        if any(type(p) is not ObjectIdentity or p.object_schema != Analysis.SCHEMA for p in self.analyses):
            raise ValueError("population synthesis substitutes original root readouts")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def payload(self):
        return json_object(self.payload_json)
