# SPDX-License-Identifier: MPL-2.0
"""Typed pure calculations on EL's shared execution and custody contracts.

A calculation owns scientific arithmetic and applicability. This module owns
canonical decoding, complete input/output census checks and worker adaptation.
It introduces no scheduler, artifact store, recovery policy or native interface.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, fields
from functools import partial
from types import MappingProxyType

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_nonempty, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.calculations import CalculationRunner
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import (
    RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration,
    RecursiveScientificHooks,
)


def _record_type(value: object) -> None:
    if not isinstance(value, type) or not issubclass(value, CanonicalRecord):
        raise TypeError("calculation ports require a CanonicalRecord type")


@dataclass(frozen=True, slots=True)
class RecordInput:
    """One required typed scientific input, with its actual byte limit.

    Distinct roles use distinct schemas. A calculation needing several values
    of one type declares a canonical collection record for that input role.
    """
    name: str
    record_type: type[CanonicalRecord]
    maximum_bytes: int

    def __post_init__(self) -> None:
        validate_stable_id(self.name)
        if self.name == "config":
            raise ValueError("config is the implicit configuration port")
        _record_type(self.record_type)
        if type(self.maximum_bytes) is not int or self.maximum_bytes < 1:
            raise ValueError("record input requires a positive byte bound")


@dataclass(frozen=True, slots=True)
class RecordOutput:
    """One required original typed result; its output ID is compiler-derived."""
    name: str
    record_type: type[CanonicalRecord]
    maximum_bytes: int

    def __post_init__(self) -> None:
        validate_stable_id(self.name)
        _record_type(self.record_type)
        if type(self.maximum_bytes) is not int or self.maximum_bytes < 1:
            raise ValueError("record output requires a positive byte bound")


@dataclass(frozen=True, slots=True)
class Calculation:
    """A reusable scientific function and its one authoritative operation contract.

    ``calculate(config, inputs)`` receives exact immutable canonical records and
    returns a mapping whose keys are exactly the declared output names. Calling
    this object independently validates the same contracts as its shared worker.
    Optional scientific/inquiry hooks apply only when the calculation uses them.
    """
    capability_key: str
    version: str
    implementation_id: str
    config_type: type[CanonicalRecord]
    inputs: tuple[RecordInput, ...]
    outputs: tuple[RecordOutput, ...]
    calculate: Callable[[CanonicalRecord, Mapping[str, CanonicalRecord]], Mapping[str, CanonicalRecord]]
    resources: ResourceBudget
    applicability: str
    assumptions: tuple[str, ...]
    maximum_config_bytes: int = 1024 * 1024
    kind: CapabilityKind = CapabilityKind.TRANSFORM
    stage: ScientificStage = ScientificStage.TRANSFORM
    permissions: tuple[CapabilityPermission, ...] = (
        CapabilityPermission.READ_DEVELOPMENT,
        CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
        CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
    )
    evidence_ceiling: EvidenceCeiling = EvidenceCeiling.NON_PROMOTABLE
    outcome_access: OutcomeAccess = OutcomeAccess.DEVELOPMENT_VISIBLE
    visibility_ceiling: VisibilityCeiling = VisibilityCeiling.DEVELOPMENT_ONLY
    scientific_hooks: RecursiveScientificHooks = RecursiveScientificHooks()
    inquiry_hooks: RecursiveInquiryHooks = RecursiveInquiryHooks()
    conformance_check_ids: tuple[str, ...] = ()
    _operation: RecursiveOperationDeclaration = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        _record_type(self.config_type)
        validate_nonempty(self.applicability, field_name="applicability")
        if type(self.assumptions) is not tuple:
            raise TypeError("assumptions must be an explicit immutable tuple")
        for assumption in self.assumptions:
            validate_nonempty(assumption, field_name="assumption")
        if not callable(self.calculate):
            raise TypeError("calculation requires a code-owned callable")
        if type(self.resources) is not ResourceBudget:
            raise TypeError("calculation requires its declared resource requirements")
        if type(self.maximum_config_bytes) is not int or self.maximum_config_bytes < 1:
            raise ValueError("calculation configuration requires a positive byte bound")
        for ports, kind, name in ((self.inputs, RecordInput, "inputs"), (self.outputs, RecordOutput, "outputs")):
            if type(ports) is not tuple or any(type(port) is not kind for port in ports):
                raise TypeError(f"calculation {name} require exact immutable port declarations")
            if len({port.name for port in ports}) != len(ports):
                raise ValueError(f"calculation {name} repeat a name")
        if not self.outputs:
            raise ValueError("calculation must declare its complete nonempty result census")
        input_schemas = (self.config_type.SCHEMA, *(port.record_type.SCHEMA for port in self.inputs))
        if len(set(input_schemas)) != len(input_schemas):
            raise ValueError("calculation input roles require distinct schemas; use a typed collection for repeated values")
        codecs = {}
        for kind in (self.config_type, *(port.record_type for port in (*self.inputs, *self.outputs))):
            if codecs.setdefault(kind.SCHEMA, kind) is not kind:
                raise ValueError("calculation substitutes one canonical schema with another record type")
        output_bound = sum(port.maximum_bytes for port in self.outputs)
        if self.resources.output_bytes is not None and output_bound > self.resources.output_bytes:
            raise ValueError("declared result byte bounds exceed the calculation resource ceiling")
        checks = tuple(sorted({"calculation.complete-census", *self.conformance_check_ids}))
        operation = RecursiveOperationDeclaration(
            capability_key=self.capability_key, capability_version=self.version,
            implementation_id=self.implementation_id, kind=self.kind,
            config_record_type=self.config_type, stage=self.stage,
            input_ports=tuple(RecursivePortContract(port.name, port.record_type.SCHEMA,
                "application/json", port.maximum_bytes) for port in sorted(self.inputs, key=lambda p: p.name)),
            outputs=tuple(OutputTemplate(port.name, port.record_type.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                "application/json", ".json") for port in sorted(self.outputs, key=lambda p: p.name)),
            permissions=self.permissions, evidence_ceiling=self.evidence_ceiling,
            outcome_access=self.outcome_access, visibility_ceiling=self.visibility_ceiling,
            resources=self.resources, conformance_check_ids=checks,
            runner_factory=partial(CalculationRunner, self), record_codecs=codecs,
            scientific_hooks=self.scientific_hooks, inquiry_hooks=self.inquiry_hooks,
            execution_properties=RecursiveExecutionProperties(native_effect=False),
        )
        object.__setattr__(self, "_operation", operation)

    def __reduce__(self):
        # Generated descriptors contain mapping proxies and a runner closure.
        # Rebuild those projections from the one declaration in each process.
        return (_restore_calculation, (tuple((member.name, getattr(self, member.name))
            for member in fields(self) if member.init),))

    @property
    def operation(self) -> RecursiveOperationDeclaration:
        """The shared compiler/registration contract; no execution happens here."""
        return self._operation

    def __call__(self, config: CanonicalRecord, inputs: Mapping[str, CanonicalRecord] | None = None) -> Mapping[str, CanonicalRecord]:
        if type(config) is not self.config_type:
            raise TypeError("calculation received another configuration record type")
        _validate_record(config, self.config_type, self.maximum_config_bytes)
        supplied = {} if inputs is None else inputs
        if not isinstance(supplied, Mapping) or set(supplied) != {port.name for port in self.inputs}:
            raise ValueError("calculation input names differ from its complete declared census")
        frozen = {}
        for port in self.inputs:
            value = supplied[port.name]
            _validate_record(value, port.record_type, port.maximum_bytes)
            frozen[port.name] = value
        products = self.calculate(config, MappingProxyType(frozen))
        if not isinstance(products, Mapping) or set(products) != {port.name for port in self.outputs}:
            raise ValueError("calculation result names differ from its complete declared census")
        result = {}
        for port in self.outputs:
            value = products[port.name]
            _validate_record(value, port.record_type, port.maximum_bytes)
            result[port.name] = value
        return MappingProxyType(result)

    def describe(self) -> dict[str, object]:
        """Static applicability and contracts, without reading inputs or running science."""
        return {
            "capability": self.capability_key, "version": self.version,
            "applicability": self.applicability, "assumptions": self.assumptions,
            "config_schema": self.config_type.SCHEMA,
            "inputs": tuple({"name": p.name, "schema": p.record_type.SCHEMA,
                             "maximum_bytes": p.maximum_bytes} for p in self.inputs),
            "outputs": tuple({"name": p.name, "schema": p.record_type.SCHEMA,
                              "maximum_bytes": p.maximum_bytes} for p in self.outputs),
            "native_effect": False, "scientific_execution_performed": False,
        }


def _restore_calculation(arguments):
    return Calculation(**dict(arguments))


def _validate_record(value: object, record_type: type[CanonicalRecord], maximum_bytes: int) -> None:
    if type(value) is not record_type:
        raise TypeError("calculation input or output substitutes its declared exact canonical type")
    if value.canonical_size_bytes() > maximum_bytes:
        raise ValueError("calculation record exceeds its declared byte bound")
    raw = value.canonical_bytes()
    decoded = decode_canonical_bytes(raw, record_type, maximum_bytes=maximum_bytes)
    if decoded != value:
        raise ValueError("calculation record does not round-trip through its strict canonical contract")

