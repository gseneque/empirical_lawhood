# SPDX-License-Identifier: MPL-2.0
"""Additive durable preparation operands; no native imports or qualification."""

from dataclasses import dataclass
from typing import ClassVar
import json
from pathlib import PurePosixPath

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_sha256, validate_stable_id,
)
from empirical_lawhood.runtime.native_subwork import NativeSubworkState

from . import contracts as historical


def geometry_keys():
    return tuple((construct, view[0]) for construct in historical.CONSTRUCTS
                 for view in historical.JOINT_VIEWS)


def geometry_id(construct, view):
    return "geometry." + construct + "." + view


def model_id(construct, view, parameters):
    return "model." + construct + "." + view + "." + parameters


@dataclass(frozen=True, slots=True)
class DurablePreparationPlan(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-preparation-plan"
    plan_id: str
    source: ObjectIdentity
    nomination: ObjectIdentity
    inventory: ObjectIdentity
    coordinates: ObjectIdentity
    workdir: str
    interpreter_path: str
    interpreter_sha256: str
    tleap_path: str
    tleap_sha256: str
    engine_inventory_sha256: str
    code_sources: tuple[tuple[str, str], ...]
    dependency_lock_sha256: str
    geometry_census: tuple[tuple[str, str], ...] = geometry_keys()
    model_census: tuple[tuple[str, str, str], ...] = historical.model_roster()
    physical_independent_units: int = 0
    attempted_geometry_ids: tuple[str, ...] = tuple(sorted(geometry_id(*key) for key in geometry_keys()))
    attempted_model_ids: tuple[str, ...] = tuple(sorted(model_id(*key) for key in historical.model_roster()))

    def __post_init__(self):
        validate_stable_id(self.plan_id)
        for name in ("interpreter_sha256", "tleap_sha256", "engine_inventory_sha256", "dependency_lock_sha256"):
            validate_sha256(getattr(self, name))
        for name in ("workdir", "interpreter_path", "tleap_path"):
            path = PurePosixPath(getattr(self, name))
            if not path.is_absolute() or ".." in path.parts:
                raise ValueError("durable preparation needs exact absolute selected paths")
        if (self.geometry_census != geometry_keys()
                or self.model_census != historical.model_roster()
                or self.physical_independent_units != 0):
            raise ValueError("durable preparation changes complete 12/24 denominator")
        geometries = {geometry_id(*key) for key in self.geometry_census}
        models = {model_id(*key): geometry_id(*key[:2]) for key in self.model_census}
        if (not self.attempted_geometry_ids
                or self.attempted_geometry_ids != tuple(sorted(set(self.attempted_geometry_ids)))
                or self.attempted_model_ids != tuple(sorted(set(self.attempted_model_ids)))
                or set(self.attempted_geometry_ids) - geometries
                or set(self.attempted_model_ids) - set(models)
                or any(models[key] not in self.attempted_geometry_ids for key in self.attempted_model_ids)):
            raise ValueError("prospective preparation control changes selected unit/geometry dependency")
        if (not self.code_sources or tuple(path for path, _ in self.code_sources)
                != tuple(sorted(set(path for path, _ in self.code_sources)))):
            raise ValueError("durable preparation needs complete sorted source bindings")
        for path, digest in self.code_sources:
            if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
                raise ValueError("selected code source escapes checkout")
            validate_sha256(digest)
        for name in ("source", "nomination", "inventory", "coordinates"):
            if type(getattr(self, name)) is not ObjectIdentity:
                raise ValueError("durable preparation substitutes actual scientific operands")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.plan_id, self)


@dataclass(frozen=True, slots=True)
class DurableNativeCallOperand(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-native-call-operand"
    call_id: str
    plan: ObjectIdentity
    unit: ObjectIdentity
    parent_call: ObjectIdentity | None
    role: str
    requested_json: str
    files: tuple[historical.FileEvidence, ...]

    def __post_init__(self):
        validate_stable_id(self.call_id)
        validate_stable_id(self.role)
        if type(self.plan) is not ObjectIdentity or type(self.unit) is not ObjectIdentity:
            raise ValueError("native call changes plan/unit custody")
        if self.parent_call is not None and type(self.parent_call) is not ObjectIdentity:
            raise ValueError("native call changes actual nested parent")
        if json.dumps(json.loads(self.requested_json), sort_keys=True, separators=(",", ":")) != self.requested_json:
            raise ValueError("native call needs lossless canonical selected operands")
        paths = tuple(row.relative_path for row in self.files)
        if paths != tuple(sorted(set(paths))):
            raise ValueError("native call omits/reorders complete operand file census")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.call_id, self)


@dataclass(frozen=True, slots=True)
class DurableRawFileCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-raw-file-census"
    files: tuple[historical.FileEvidence, ...]

    def __post_init__(self):
        paths = tuple(row.relative_path for row in self.files)
        if paths != tuple(sorted(set(paths))):
            raise ValueError("raw native file census must retain complete exact paths")


@dataclass(frozen=True, slots=True)
class DurableNativeReturnWitness(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-native-return-witness"
    call: ObjectIdentity
    native_returned: bool
    return_type: str | None
    error_text: str | None

    def __post_init__(self):
        if (type(self.native_returned) is not bool
                or self.native_returned != (self.return_type is not None)
                or (self.native_returned and self.error_text is not None)
                or (not self.native_returned and not self.error_text)):
            raise ValueError("native return witness conflates returned object and extraction/interpretation")


@dataclass(frozen=True, slots=True)
class DurableUnitReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-unit-return"
    unit_id: str
    plan: ObjectIdentity
    geometry: ObjectIdentity | None
    geometry_receipt: ObjectIdentity | None
    known_return: bool
    preparation_succeeded: bool
    reason_codes: tuple[str, ...]
    files: tuple[historical.FileEvidence, ...]
    native_calls: tuple[ObjectIdentity, ...]
    error_text: str | None = None
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.unit_id)
        if (type(self.known_return) is not bool or type(self.preparation_succeeded) is not bool
                or not self.known_return or self.physical_independent_units != 0
                or (not self.preparation_succeeded and not self.reason_codes)):
            raise ValueError("unit return cannot manufacture unknown completion or preparation")
        if (self.geometry is None) != (self.geometry_receipt is None):
            raise ValueError("model geometry reuse needs actual complete receipt")
        paths = tuple(row.relative_path for row in self.files)
        if paths != tuple(sorted(set(paths))):
            raise ValueError("unit return changes full actual raw file census")
        if tuple(row.object_id for row in self.native_calls) != tuple(sorted(set(row.object_id for row in self.native_calls))):
            raise ValueError("unit return substitutes actual call denominator")


@dataclass(frozen=True, slots=True)
class DurablePreparationCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/durable-preparation-census"
    plan: ObjectIdentity
    states: tuple[tuple[str, NativeSubworkState], ...]
    physical_independent_units: int = 0

    def __post_init__(self):
        expected = tuple(sorted((*[geometry_id(*key) for key in geometry_keys()],
                                 *[model_id(*key) for key in historical.model_roster()])))
        if tuple(key for key, _ in self.states) != expected or self.physical_independent_units != 0:
            raise ValueError("preparation census drops failed/omitted/unknown 12/24 units")
        if any(type(state) is not NativeSubworkState for _, state in self.states):
            raise ValueError("preparation census changes actual progress state")
