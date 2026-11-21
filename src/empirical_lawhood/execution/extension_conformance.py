# SPDX-License-Identifier: MPL-2.0
"""Finite, explicit extension conformance selections, separate from discovery.

These are trusted developer inputs, not scientific records or grants. Contract
inspection never calls a callback, constructs a provider, or reads a source.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from inspect import Parameter, isfunction, signature
from types import MappingProxyType
from typing import Mapping, get_args, get_origin, get_type_hints

from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.execution import experiment_callbacks as callbacks
from empirical_lawhood.execution import recursive_callbacks
from empirical_lawhood.execution.experiment_preparation import ExperimentProtocolDeclaration, ExperimentRuntimeBinding
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration
from empirical_lawhood.execution.continuing_source import LiveEffectPort, LiveSourceAccess
from empirical_lawhood.storage.contracts.knowledge_store import ScientificTypeDescriptor, ScientificTypeRegistry


class ConformanceProfile(StrEnum):
    DECLARATION = "declaration"
    ORDINARY_DEVELOPMENT = "ordinary-development"
    ISOLATED_NATIVE_CONTRACTS = "isolated-native-contracts"
    RECORD_REVISIONS = "record-revisions"
    CONTINUING_SOURCE_CONTRACTS = "continuing-source-contracts"
    DEPENDENT_ASSESSMENT_CONTRACTS = "dependent-assessment-contracts"
    PORTABLE_CERTIFICATE_READ = "portable-certificate-read"
    KNOWLEDGE_STORE_CONTRACTS = "knowledge-store-contracts"


class ConformanceCall(StrEnum):
    CODEC_ROUNDTRIP = "record.roundtrip"
    PREPARE = "experiment.prepare"
    VALIDATE_INSTANCE = "experiment.validate-instance"
    DEVELOPMENT_READ = "experiment.read-development"
    DEVELOPMENT_COMPLETE = "experiment.complete-development"
    COMPILE = "recursive.compile"
    ASSESS = "recursive.assess"
    OUTPUT_CENSUS = "execution.output-census"
    NATIVE_PREPARE = "execution.prepare-native-work"
    OUTPUT_RECORD_DECODE = "record.decode-selected-output"
    LIVE_APPLICATION = "source.require-application"
    LIVE_EVENT_GAPS = "source.sequence-gaps"
    ACTOR_EVIDENCE = "inquiry.require-actor-evidence"
    ASSESSMENT_CONTRACT = "inquiry.assessment-contract"
    CERTIFICATE_READ = "knowledge.verify-certificate"
    KNOWLEDGE_DEPENDENCIES = "knowledge.dependency-order"


@dataclass(frozen=True, slots=True)
class ConformanceCase:
    """One disclosed invocation of a closed owning call site, never arbitrary code.

    ``expected`` is the complete return value, or the exact exception class name
    when ``refusal_contains`` is selected. Failed cases remain in the report.
    """

    case_id: str
    call: ConformanceCall
    arguments: Mapping[str, object]
    expected: object
    refusal_contains: str | None = None

    def __post_init__(self):
        validate_stable_id(self.case_id)
        if type(self.call) is not ConformanceCall:
            raise TypeError("conformance requires a closed owning call site")
        if not isinstance(self.arguments, Mapping) or any(type(key) is not str for key in self.arguments):
            raise TypeError("conformance arguments require named operands")
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        if self.refusal_contains is not None and (
                type(self.refusal_contains) is not str or not self.refusal_contains
                or self.expected not in ("TypeError", "ValueError", "PermissionError", "SchedulerConsistencyError",
                    "UnsupportedRecordRevision", "AmbiguousRecordRevision")):
            raise ValueError("conformance refusal requires its exact class and nonempty diagnostic")


@dataclass(frozen=True, slots=True)
class ExtensionConformanceSelection:
    namespace: str
    schema_prefix: str
    operations: tuple[RecursiveOperationDeclaration, ...]
    protocols: tuple[ExperimentProtocolDeclaration, ...] = ()
    bindings: tuple[ExperimentRuntimeBinding, ...] = ()
    imported_record_types: tuple[type[CanonicalRecord], ...] = ()
    profile: ConformanceProfile = ConformanceProfile.DECLARATION
    cases: tuple[ConformanceCase, ...] = ()
    unmet_prerequisites: tuple[str, ...] = ()
    source_access: LiveSourceAccess | None = None
    effect_ports: tuple[tuple[str, LiveEffectPort], ...] = ()
    knowledge_types: tuple[ScientificTypeDescriptor, ...] = ()


def _call_shape(contract):
    arguments, keywords = [], {}
    for name, parameter in signature(contract if isfunction(contract) else contract.__call__).parameters.items():
        if name == "self":
            continue
        if parameter.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD):
            arguments.append(object())
        elif parameter.kind is Parameter.KEYWORD_ONLY:
            keywords[name] = object()
        else:
            raise TypeError("callback contract must declare its finite exact parameters")
    return arguments, keywords


def require_callback_signature(callback, contract, *, name):
    """Check the actual call form, including optional keywords, without calling it."""
    try:
        arguments, keywords = _call_shape(contract)
        signature(callback).bind(*arguments, **keywords)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} does not accept {contract.__name__}'s exact call form") from error


def _callback_fields(value, path):
    checked = []
    for name, annotation in get_type_hints(type(value)).items():
        callback = getattr(value, name)
        if callback is None:
            continue
        kinds = get_args(annotation) or (annotation,)
        contracts = tuple(get_origin(kind) or kind for kind in kinds
            if getattr(get_origin(kind) or kind, "__module__", None)
            in (callbacks.__name__, recursive_callbacks.__name__))
        if not contracts:
            continue
        for contract in contracts:
            try:
                require_callback_signature(callback, contract, name=f"{path}.{name}")
                checked.append(f"{path}.{name}:{contract.__name__}")
                break
            except TypeError:
                pass
        else:
            raise TypeError(f"{path}.{name} accepts none of its declared callback call forms")
    return checked


_SERVICE_PROFILES = frozenset((ConformanceProfile.CONTINUING_SOURCE_CONTRACTS,
    ConformanceProfile.PORTABLE_CERTIFICATE_READ, ConformanceProfile.KNOWLEDGE_STORE_CONTRACTS))
_PROFILE_CALLS = {
    ConformanceProfile.CONTINUING_SOURCE_CONTRACTS: (ConformanceCall.LIVE_APPLICATION, ConformanceCall.LIVE_EVENT_GAPS),
    ConformanceProfile.DEPENDENT_ASSESSMENT_CONTRACTS: (ConformanceCall.ACTOR_EVIDENCE,
        ConformanceCall.ASSESSMENT_CONTRACT, ConformanceCall.COMPILE, ConformanceCall.ASSESS),
    ConformanceProfile.PORTABLE_CERTIFICATE_READ: (ConformanceCall.CERTIFICATE_READ,),
    ConformanceProfile.KNOWLEDGE_STORE_CONTRACTS: (ConformanceCall.KNOWLEDGE_DEPENDENCIES,),
}


def _inspect_service_contracts(selection, codec):
    """Inspect selected ports and exact types without contacting any owner."""
    forms = []
    if type(selection.effect_ports) is not tuple or type(selection.knowledge_types) is not tuple:
        raise TypeError("conformance service declarations require exact tuples")
    if selection.profile is ConformanceProfile.CONTINUING_SOURCE_CONTRACTS:
        if selection.source_access is None or not 1 <= len(selection.effect_ports) <= 16:
            raise ValueError("source conformance requires its access owner and finite effect-port census")
        names = set()
        ports = [("access", selection.source_access, LiveSourceAccess, ("require_owner", "require_actor"))]
        for row in selection.effect_ports:
            if type(row) is not tuple or len(row) != 2:
                raise TypeError("source conformance needs named effect ports")
            key, port = row
            validate_stable_id(key)
            if key in names:
                raise ValueError("source conformance repeats an effect port")
            names.add(key)
            ports.append((key, port, LiveEffectPort, ("submit", "observe")))
        for key, port, protocol, methods in ports:
            for name in methods:
                require_callback_signature(getattr(port, name, None), getattr(protocol, name), name=key + "." + name)
                forms.append(key + "." + name + ":" + protocol.__name__)
    elif selection.source_access is not None or selection.effect_ports:
        raise ValueError("source ports require their selected conformance profile")
    if selection.profile is ConformanceProfile.KNOWLEDGE_STORE_CONTRACTS:
        if not selection.knowledge_types:
            raise ValueError("knowledge conformance requires its selected exact type descriptors")
        ScientificTypeRegistry(selection.knowledge_types)
        for descriptor in selection.knowledge_types:
            codec(descriptor.record_type)
            signature(descriptor.dependencies).bind(object())
            forms.append(descriptor.descriptor_id + ".dependencies(record)")
            if descriptor.verify is not None:
                signature(descriptor.verify).bind(object())
                forms.append(descriptor.descriptor_id + ".verify(context)")
    elif selection.knowledge_types:
        raise ValueError("knowledge descriptors require their selected conformance profile")
    for call in _PROFILE_CALLS.get(selection.profile, ()):
        cases = tuple(case for case in selection.cases if case.call is call)
        if not any(case.refusal_contains is None for case in cases) or not any(case.refusal_contains for case in cases):
            raise ValueError("selected profile requires a positive case and explicit refusal for " + call.value)
    return forms


def inspect_extension_contracts(selection: ExtensionConformanceSelection) -> dict:
    """Validate complete selected declarations before any executable fixture.

    Imported codecs require explicit selection. Same-class reuse is permitted;
    conflicting implementations of one exact schema/revision refuse.
    """
    if type(selection) is not ExtensionConformanceSelection:
        raise TypeError("conformance requires its exact typed selection")
    validate_stable_id(selection.namespace)
    if selection.schema_prefix != f"empirical-lawhood/{selection.namespace}/":
        raise ValueError("conformance requires an explicit owned schema prefix")
    if type(selection.profile) is not ConformanceProfile:
        raise ValueError("selected conformance profile is not implemented")
    for name, kind in (("operations", RecursiveOperationDeclaration),
                       ("protocols", ExperimentProtocolDeclaration),
                       ("bindings", ExperimentRuntimeBinding), ("cases", ConformanceCase)):
        values = getattr(selection, name)
        if type(values) is not tuple or any(type(value) is not kind for value in values):
            raise TypeError(f"conformance {name} require their exact typed tuple")
    minimum_operations = 0 if selection.profile in _SERVICE_PROFILES else 1
    if not minimum_operations <= len(selection.operations) <= 64 or len(selection.protocols) > 8 or len(selection.cases) > 32:
        raise ValueError("conformance selection exceeds its finite declaration/case census")
    if len({case.case_id for case in selection.cases}) != len(selection.cases):
        raise ValueError("conformance repeats a case identity")
    if (selection.profile is ConformanceProfile.DECLARATION and selection.cases
            or selection.profile is not ConformanceProfile.DECLARATION and not selection.cases):
        raise ValueError("selected conformance profile has an incompatible executable case census")
    if (type(selection.unmet_prerequisites) is not tuple
            or any(type(value) is not str or not value for value in selection.unmet_prerequisites)):
        raise TypeError("unmet conformance prerequisites must be explicit strings")
    if (type(selection.imported_record_types) is not tuple or any(
            not isinstance(kind, type) or not issubclass(kind, CanonicalRecord)
            for kind in selection.imported_record_types)):
        raise TypeError("imported record contracts require exact canonical types")
    codecs = {}
    def codec(kind):
        key = kind.SCHEMA, kind.VERSION
        if codecs.setdefault(key, kind) is not kind:
            raise ValueError(f"conflicting schema/revision implementation: {key}")
        if not kind.SCHEMA.startswith(selection.schema_prefix) and kind not in selection.imported_record_types:
            raise ValueError(f"record outside owned namespace requires explicit import: {kind.SCHEMA}")

    for kind in selection.imported_record_types:
        codec(kind)
    signatures = _inspect_service_contracts(selection, codec)
    keys = set()
    native_operations = 0
    for operation in selection.operations:
        operation.__post_init__()
        key = operation.capability_key, operation.capability_version
        if not key[0].startswith(selection.namespace + ".") or key in keys:
            raise ValueError("operation repeats or escapes the selected namespace")
        keys.add(key)
        properties = operation.execution_properties
        if properties.requires_network:
            raise ValueError("conformance network contact is not implemented; source contracts are effect-free")
        if properties.native_effect:
            native_operations += 1
            if selection.profile is not ConformanceProfile.ISOLATED_NATIVE_CONTRACTS:
                raise ValueError("native declarations require the isolated-native-contracts profile")
            if properties.native_work_preparer is None or not properties.complete_unit_census:
                raise ValueError("native conformance requires a preparer and complete unit census")
        signature(operation.runner_factory).bind()
        for kind in (operation.config_record_type, *operation.record_codecs.values(), *operation.input_record_types):
            codec(kind)
        for group in (operation, operation.scientific_hooks, operation.inquiry_hooks, operation.execution_properties):
            signatures.extend(_callback_fields(group, operation.capability_key))
    if selection.profile is ConformanceProfile.DEPENDENT_ASSESSMENT_CONTRACTS and not any(
            row.scientific_hooks.assessment_projector is not None
            and row.inquiry_hooks.inquiry_claim_assessment_projector is not None for row in selection.operations):
        raise ValueError("dependent assessment conformance requires its registered assessment and exact-claim projectors")
    if selection.profile is ConformanceProfile.ISOLATED_NATIVE_CONTRACTS and not native_operations:
        raise ValueError("isolated-native-contracts requires a selected native operation")
    if selection.profile is ConformanceProfile.RECORD_REVISIONS:
        from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
        outputs = {(operation.record_codecs[output.payload_schema].SCHEMA,
            operation.record_codecs[output.payload_schema].VERSION)
            for operation in selection.operations for output in operation.outputs
            if output.profile is ArtifactProfile.CANONICAL_JSON}
        families = {schema for schema, version in outputs
            if len({v for s, v in outputs if s == schema}) > 1}
        exercised = {(case.expected.SCHEMA, case.expected.VERSION) for case in selection.cases
            if case.call is ConformanceCall.OUTPUT_RECORD_DECODE and case.refusal_contains is None
            and isinstance(case.expected, CanonicalRecord)}
        if not families or not {(s, v) for s, v in outputs if s in families}.issubset(exercised):
            raise ValueError('record-revisions requires every coexisting output revision through its selected decoder')
        if not any(case.call is ConformanceCall.OUTPUT_RECORD_DECODE and case.refusal_contains
                and case.expected == 'UnsupportedRecordRevision' for case in selection.cases):
            raise ValueError('record-revisions requires an explicit unsupported-producer refusal')

    protocols = {}
    for protocol in selection.protocols:
        protocol.__post_init__()
        if not protocol.protocol_id.startswith(selection.namespace + ".") or protocol.protocol_id in protocols:
            raise ValueError("protocol repeats or escapes the selected namespace")
        if protocol.requires_prospective_runtime_binding or protocol.programme_record_type is not None:
            raise ValueError("base conformance supports only ordinary development protocols")
        protocols[protocol.protocol_id] = protocol
        for kind in (protocol.specification_type, *protocol.input_record_types, *protocol.input_file_record_types):
            codec(kind)
        signatures.extend(_callback_fields(protocol, protocol.protocol_id))
        require_callback_signature(protocol.prepare, callbacks.ExperimentPrepare, name=protocol.protocol_id + ".prepare")
        if protocol.bind_inputs is not None:
            contract = (callbacks.ExperimentLocatedFileInputBinder if protocol.bind_input_locations
                        else callbacks.ExperimentFileInputBinder) if protocol.input_file_record_types or protocol.input_storage_codecs else (
                        callbacks.ExperimentLocatedInputBinder if protocol.bind_input_locations else callbacks.ExperimentInputBinder)
            require_callback_signature(protocol.bind_inputs, contract, name=protocol.protocol_id + ".bind_inputs")
    bindings = {}
    for binding in selection.bindings:
        binding.__post_init__()
        if binding.protocol_id not in protocols or binding.protocol_id in bindings:
            raise ValueError("runtime binding lacks one exact selected protocol owner")
        bindings[binding.protocol_id] = binding
        signatures.extend(_callback_fields(binding, binding.protocol_id))
        if binding.validate_development_read_access is not None:
            require_callback_signature(binding.read_development_result,
                callbacks.AccessibleDevelopmentResultReader, name=binding.protocol_id + ".read_development_result")
    for protocol in protocols.values():
        if protocol.requires_development_runtime_binding and protocol.protocol_id not in bindings:
            raise ValueError("development protocol lacks its declared runtime binding")
        if selection.profile is not ConformanceProfile.DECLARATION and (
                protocol.protocol_id not in bindings or bindings[protocol.protocol_id].read_development_result is None):
            raise ValueError("executable conformance requires its retained scientific reader")
    from empirical_lawhood.execution.recursive_qualified_parents import prior_result_capacity
    return dict(namespace=selection.namespace, profile=selection.profile.value,
        operations=sorted(f"{key}@{version}" for key, version in keys),
        protocols=sorted(protocols), codecs=sorted(f"{schema}@{version}" for schema, version in codecs),
        callback_forms=sorted(signatures), prior_result_capacity=prior_result_capacity(), executed_callbacks=0)
