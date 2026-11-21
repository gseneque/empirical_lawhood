# SPDX-License-Identifier: MPL-2.0
"""Bounded exposed integer calculation and explicit operational selections."""

import base64
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import PurePath
from typing import ClassVar

from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract

NAMESPACE = "isolated-native-starter"
PREFIX = "empirical-lawhood/" + NAMESPACE
PROTOCOL_ID = NAMESPACE + ".development"
MAX_CONTROL_BYTES = 64 * 1024
MAX_SOURCE_BYTES = 2 * 1024**2
MAX_RESULT_BYTES = 64 * 1024
MAX_LOG_BYTES = 32 * 1024
UNIT = "unit.isolated-native-starter.exposed-integer-sequence"
FAULTS = ("none", "before-contact", "after-contact", "after-nested-completion", "before-parent-completion")


def absolute(value):
    if type(value) is not str or not PurePath(value).is_absolute() or ".." in PurePath(value).parts:
        raise ValueError("isolated starter requires explicit absolute paths")


def exact_reference(value, kind):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
        raise ValueError("isolated starter changes an exact schema or record revision")


@dataclass(frozen=True, slots=True)
class SquareInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/integer-sequence"
    record_id: str
    last_integer: int
    units: str = "dimensionless-integer"
    evidence_scope: str = "EXPOSED_DEVELOPMENT"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.last_integer) is not int or not 0 <= self.last_integer <= 1024:
            raise ValueError("isolated starter requires zero through 1024 inclusive integers")
        if self.units != "dimensionless-integer" or self.evidence_scope != "EXPOSED_DEVELOPMENT":
            raise ValueError("isolated starter requires its exposed dimensionless integer scope")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class ProcessLog(CanonicalRecord):
    """Exact bounded process bytes, including an empty or non-UTF-8 stream."""

    SCHEMA: ClassVar[str] = PREFIX + "/process-log"
    record_id: str
    stream: str
    content_base64: str
    size_bytes: int
    content_sha256: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_sha256(self.content_sha256)
        if (self.stream not in ("stdout", "stderr") or type(self.size_bytes) is not int
                or not 0 <= self.size_bytes <= MAX_LOG_BYTES or type(self.content_base64) is not str
                or len(self.content_base64) > 4 * ((MAX_LOG_BYTES + 2) // 3)):
            raise ValueError("isolated starter process log exceeds its exact stream or byte contract")
        try:
            raw = base64.b64decode(self.content_base64, validate=True)
        except (ValueError, UnicodeError) as error:
            raise ValueError("isolated starter process log requires exact base64 bytes") from error
        if (base64.b64encode(raw).decode("ascii") != self.content_base64
                or len(raw) != self.size_bytes or sha256(raw).hexdigest() != self.content_sha256):
            raise ValueError("isolated starter process log changes its original complete bytes")

    @classmethod
    def from_bytes(cls, record_id, stream, raw):
        if type(raw) is not bytes or len(raw) > MAX_LOG_BYTES:
            raise ValueError("isolated starter process log requires bounded original bytes")
        return cls(record_id, stream, base64.b64encode(raw).decode("ascii"), len(raw), sha256(raw).hexdigest())

    def original_bytes(self):
        self.__post_init__()
        return base64.b64decode(self.content_base64, validate=True)


@dataclass(frozen=True, slots=True)
class WorkerSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/worker-selection"
    interpreter_path: str
    interpreter_sha256: str
    numpy_version: str
    source_root: str
    package_root: str
    scratch_directory: str
    scratch_contract: ExternalRootContract
    environment: tuple[tuple[str, str], ...]
    fault: str = "none"

    def __post_init__(self):
        for value in (self.interpreter_path, self.source_root, self.package_root, self.scratch_directory):
            absolute(value)
        validate_sha256(self.interpreter_sha256)
        if (type(self.scratch_contract) is not ExternalRootContract
                or not PurePath(self.scratch_directory).is_relative_to(self.scratch_contract.canonical_path)
                or self.scratch_directory == self.scratch_contract.canonical_path):
            raise ValueError("isolated starter scratch must be below its selected guarded root")
        self.scratch_contract.__post_init__()
        if self.numpy_version not in ("2.3.5", "2.4.6"):
            raise ValueError("isolated starter requires a declared locked NumPy profile")
        if self.fault not in FAULTS:
            raise ValueError("isolated starter requires a declared exposed interruption boundary")
        if (type(self.environment) is not tuple or self.environment != tuple(sorted(self.environment))
                or len(dict(self.environment)) != len(self.environment)
                or any(type(k) is not str or type(v) is not str for k, v in self.environment)):
            raise ValueError("isolated starter requires complete sorted worker environment settings")
        values = dict(self.environment)
        if values.get("PYTHONDONTWRITEBYTECODE") != "1" or any(values.get(name) != "1" for name in (
                "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")):
            raise ValueError("isolated starter requires one numerical thread and disabled bytecode writes")


@dataclass(frozen=True, slots=True)
class SquareSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/specification"
    specification_id: str
    operand: ObjectIdentity
    provenance: ObjectIdentity
    worker: WorkerSelection
    calculation: str = "sum-integer-squares"

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        exact_reference(self.operand, SquareInput)
        exact_reference(self.provenance, NumericalProducingProvenance)
        if type(self.worker) is not WorkerSelection:
            raise TypeError("isolated starter requires its exact worker selection")
        self.worker.__post_init__()
        if self.calculation != "sum-integer-squares":
            raise ValueError("unimplemented isolated starter calculation")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class SquareConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/operation-config"
    config_id: str
    specification: SquareSpecification

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if type(self.specification) is not SquareSpecification:
            raise TypeError("isolated starter requires its original complete specification")
        self.specification.__post_init__()
        if self.config_id != "config." + NAMESPACE + "." + self.specification.fingerprint():
            raise ValueError("isolated starter changes its code-derived configuration identity")

    @property
    def node_id(self):
        return self.config_id.removeprefix("config.")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class SquareNativeResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/native-result"
    record_id: str
    configuration: ObjectIdentity
    operand: ObjectIdentity
    last_integer: int
    sum_of_squares: int
    numpy_version: str
    measured_cpu_seconds: Decimal
    measured_wall_seconds: Decimal
    process_lifetime_peak_rss_bytes: int

    def __post_init__(self):
        validate_stable_id(self.record_id)
        exact_reference(self.configuration, SquareConfig)
        exact_reference(self.operand, SquareInput)
        if (type(self.last_integer) is not int or not 0 <= self.last_integer <= 1024
                or type(self.sum_of_squares) is not int or not 0 <= self.sum_of_squares <= 2**63 - 1
                or self.numpy_version not in ("2.3.5", "2.4.6")):
            raise ValueError("isolated starter changes its bounded native return")
        for value in (self.measured_cpu_seconds, self.measured_wall_seconds):
            if type(value) is not Decimal or not value.is_finite() or value < 0:
                raise ValueError("isolated starter requires actual nonnegative measured clocks")
        if type(self.process_lifetime_peak_rss_bytes) is not int or self.process_lifetime_peak_rss_bytes <= 0:
            raise ValueError("isolated starter requires its observed Linux process peak")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class SquareResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/result"
    record_id: str
    config: SquareConfig
    native: SquareNativeResult
    independent_sum: int
    disposition: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.config) is not SquareConfig or type(self.native) is not SquareNativeResult:
            raise TypeError("isolated starter requires its exact original typed products")
        self.config.__post_init__()
        self.native.__post_init__()
        if (self.record_id != self.config.node_id + ".product"
                or self.native.configuration != self.config.identity
                or self.native.operand != self.config.specification.operand
                or self.native.numpy_version != self.config.specification.worker.numpy_version
                or type(self.independent_sum) is not int or not 0 <= self.independent_sum <= 2**63 - 1
                or self.disposition not in ("SATISFIED", "FALSIFIED")):
            raise ValueError("isolated starter changes its original result joins or disposition")
        expected = "SATISFIED" if self.native.sum_of_squares == self.independent_sum else "FALSIFIED"
        if self.disposition != expected:
            raise ValueError("isolated starter changes its comparison disposition")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
