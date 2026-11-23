# SPDX-License-Identifier: MPL-2.0
"""Sealed ensemble definitions, acquisition blocks and genuine typed reduction parents."""

from dataclasses import dataclass
import json
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import (
    CanonicalRecord,
    validate_stable_id,
)

PREFIX = "empirical-lawhood/path-ensemble"


def numerical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True)
class PathDesign(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/design"
    family: str
    first_root: int
    development_roots: int
    evaluation_roots: int
    batch_size: int
    parameters_json: str

    def __post_init__(self):
        validate_stable_id(self.family, field_name="family")
        counts = (
            self.first_root,
            self.development_roots,
            self.evaluation_roots,
            self.batch_size,
        )
        if (
            any(type(v) is not int for v in counts)
            or self.first_root < 0
            or min(counts[1:3]) < 2
            or self.batch_size < 1
            or sum(counts[:3]) >= 2**60
        ):
            raise ValueError(
                "path ensembles require disjoint addressable roots and a positive block size"
            )
        if (
            not isinstance(self.parameters, dict)
            or numerical_json(self.parameters) != self.parameters_json
        ):
            raise ValueError(
                "path settings require a single canonical numerical JSON object"
            )

    @property
    def parameters(self):
        return json.loads(self.parameters_json)


@dataclass(frozen=True, slots=True)
class PathSpecification(CanonicalRecord):
    design: PathDesign
    FAMILY: ClassVar[str]
    ISSUED_FORECAST: ClassVar[bool] = False

    @classmethod
    def definition_schema_id(cls) -> str:
        return cls.FAMILY + ".definition.v1"

    def __post_init__(self):
        if self.design.family != self.FAMILY:
            raise ValueError("path design belongs to another physical source")
        self.design.__post_init__()
        self.validate_parameters(self.design.parameters)
        if self.ISSUED_FORECAST:
            splits = self.design.parameters["splits"]
            if sum(splits.values()) != self.design.development_roots:
                raise ValueError(
                    "development, training and calibration must exhaust the assigned roots"
                )

    @property
    def specification_id(self):
        return "specification." + self.FAMILY + "." + self.design.fingerprint()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class PathOperation(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/operation"
    design: PathDesign
    specification: ObjectIdentity
    phase: str
    first: int
    count: int

    def __post_init__(self):
        if (
            self.phase
            not in (
                "develop",
                "freeze",
                "prefix",
                "observe",
                "predict",
                "evaluate",
                "assess",
            )
            or self.count < 1
        ):
            raise ValueError("invalid finite path operation")
        self.design.__post_init__()

    @property
    def node_id(self):
        return f"{self.design.family}.{self.specification.object_fingerprint[:24]}.{self.phase}.{self.first:019d}"

    @property
    def config_id(self):
        return "config." + self.node_id

    @property
    def unit_id(self):
        return f"batch.{self.first:019d}.{self.count:07d}"

    @property
    def acquires(self):
        return self.phase in ("develop", "prefix", "observe", "predict", "evaluate")


@dataclass(frozen=True, slots=True)
class PathProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = PREFIX + "/product"
    config: PathOperation
    parents: tuple[ObjectIdentity, ...]
    measurement_json: str
    arrays: ArtifactIdentity | None

    def __post_init__(self):
        if self.config.acquires != (self.arrays is not None) or tuple(
            p.object_id for p in self.parents
        ) != tuple(sorted({p.object_id for p in self.parents})):
            raise ValueError(
                "path result has mismatched array or original parent census"
            )
        if (
            not isinstance(self.measurement, dict)
            or numerical_json(self.measurement) != self.measurement_json
        ):
            raise ValueError("invalid original path measurement")

    @property
    def measurement(self):
        return json.loads(self.measurement_json)

    @property
    def record_id(self):
        return self.config.node_id + ".product"

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def operations(spec):
    d = spec.design
    starts = (
        ("develop", d.first_root, d.development_roots),
        ("evaluate", d.first_root + d.development_roots, d.evaluation_roots),
    )
    ident = spec.identity
    configs = [
        PathOperation(d, ident, phase, i, min(n - i + first, d.batch_size))
        for phase, first, n in starts
        for i in range(first, first + n, d.batch_size)
    ]
    if spec.ISSUED_FORECAST:
        first, count = starts[1][1:]
        configs.extend(
            PathOperation(d, ident, phase, i, min(first + count - i, d.batch_size))
            for i in range(first, first + count, d.batch_size)
            for phase in ("prefix", "observe", "predict")
        )
    configs.extend(
        PathOperation(d, ident, phase, first, n)
        for phase, first, n in (
            ("freeze", starts[0][1], starts[0][2]),
            ("assess", starts[1][1], starts[1][2]),
        )
    )
    return tuple(sorted(configs, key=lambda c: c.node_id))


def required_parents(config, configs):
    if any(c.phase == "predict" for c in configs):
        whole, matched = {
            "develop": ((), ()),
            "freeze": (("develop",), ()),
            "prefix": (("freeze",), ()),
            "observe": ((), ("prefix",)),
            "predict": (("freeze",), ("observe",)),
            "evaluate": ((), ("prefix", "predict")),
            "assess": (("freeze", "evaluate"), ()),
        }[config.phase]
        return tuple(
            c
            for c in configs
            if c.phase in whole
            or (
                c.phase in matched
                and (c.first, c.count) == (config.first, config.count)
            )
        )
    phases = {
        "develop": (),
        "freeze": ("develop",),
        "evaluate": ("freeze",),
        "assess": ("evaluate", "freeze"),
    }
    return tuple(c for c in configs if c.phase in phases[config.phase])
