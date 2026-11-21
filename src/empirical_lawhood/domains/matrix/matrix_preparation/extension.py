# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from dataclasses import replace

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionComponentKind, ExtensionContributionKind
from empirical_lawhood.execution.declaration_helpers import bundle, component, manifest
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import DEVELOPMENT
from empirical_lawhood.domains.matrix.matrix_preparation.continuation import PreparationProjectionContinuation
from empirical_lawhood.domains.matrix.matrix_preparation.method_continuation import METHOD_CONTINUATION_ROLES, method_continuation_type
from empirical_lawhood.domains.matrix.matrix_preparation.topology import DATA_OUTPUTS, INPUT_SCHEMAS, METHOD_CONFIG_TYPES, METHOD_ROLES, OUTPUT_MIB, STAGE_SCHEMA, WALL_SECONDS, task_output_schemas


METHOD_CAPABILITIES = tuple(
    manifest(
        role,
        METHOD_CONFIG_TYPES[role],
        CapabilityKind.LAW_IDENTIFIER
        if role == "description"
        else CapabilityKind.NUMERICAL_QUALIFIER
        if role == "numerical-semantics"
        else CapabilityKind.EVALUATOR
        if role == "evaluation"
        else CapabilityKind.TRANSFORM
        if role == "projection"
        else CapabilityKind.ANALYSIS,
        (
            METHOD_CONFIG_TYPES[role].SCHEMA,
            *INPUT_SCHEMAS[role],
            STAGE_SCHEMA,
            *((ObjectIdentity.SCHEMA,) if role == "description" else ()),
        ),
        tuple(task_output_schemas(role).values()),
        EvidenceCeiling.LOCAL_LAW
        if role in ("description", "evaluation")
        else EvidenceCeiling.RESPONSE,
        OutcomeAccess.EVALUATION_REVEALED
        if role == "evaluation"
        else OutcomeAccess.DEVELOPMENT_VISIBLE,
        WALL_SECONDS[role],
        namespace=DEVELOPMENT,
        resources=ResourceBudget(
            1, 2 * 1024**3, 0, WALL_SECONDS[role], 2 * 1024**3, OUTPUT_MIB[role] * 1024**2
        ),
        read_permission=CapabilityPermission.READ_DEVELOPMENT,
        implementation_id="matrix-preparation-projection-with-custodied-native-imports"
        if role == "projection"
        else "matrix-preparation-frozen-observable-and-independent-prospective-task-methods",
        conformance_ids=(
            "exact-root-role-before-artifact-read",
            "no-hidden-or-task-input-to-forecast",
            "separate-description-forecast-task-terminals",
            "shared-law-finalizer",
        ),
    )
    for role in METHOD_ROLES
)

_built = []
for role, capability in zip(METHOD_ROLES, METHOD_CAPABILITIES, strict=True):
    schemas = tuple(schema for _, schema in DATA_OUTPUTS[role])
    contribution, components = bundle(
        role,
        ExtensionContributionKind.METHOD,
        capability,
        (
            METHOD_CONFIG_TYPES[role],
            *((PreparationProjectionContinuation,) if role == "projection" else ()),
            *((method_continuation_type(role),) if role in METHOD_CONTINUATION_ROLES else ()),
        ),
        schemas[0] if schemas else None,
        namespace=DEVELOPMENT,
    )
    extra = tuple(
        component(
            f"{role}.hdf5-validator.{i}",
            ExtensionComponentKind.ARTIFACT_VALIDATOR,
            (schema,),
            ('empirical-lawhood/runtime/artifact-generic-validation',),
            capability.implementation_sha256,
            DEVELOPMENT,
        )
        for i, schema in enumerate(schemas[1:], start=1)
    )
    if extra:
        contribution = replace(
            contribution,
            artifact_validators=tuple(
                sorted(
                    (
                        *contribution.artifact_validators,
                        *(ObjectIdentity.from_record(c.registration_id, c) for c in extra),
                    ),
                    key=lambda r: r.object_id,
                )
            ),
        )
        components = (*components, *extra)
    _built.append((contribution, components))
METHOD_COMPONENTS = tuple(components for _, components in _built)
_contributions = tuple(c for c, _ in _built)
_DISCOVERY_CONTRIBUTION = replace(
    _contributions[0],
    contribution_id=f"extension-contribution.{DEVELOPMENT}.methods",
    capability_manifests=tuple(sorted(METHOD_CAPABILITIES, key=lambda c: c.registry_id)),
    candidate_capability_registrations=tuple(
        sorted(
            (v for c in _contributions for v in c.candidate_capability_registrations),
            key=lambda v: v.manifest.registry_id,
        )
    ),
    profile_registrations=tuple(
        sorted(
            (v for c in _contributions for v in c.profile_registrations),
            key=lambda v: v.registration_id,
        )
    ),
    config_decoders=tuple(
        sorted({v for c in _contributions for v in c.config_decoders}, key=lambda v: v.object_id)
    ),
    artifact_validators=tuple(
        sorted(
            (v for c in _contributions for v in c.artifact_validators), key=lambda v: v.object_id
        )
    ),
    runtime_providers=tuple(
        sorted((v for c in _contributions for v in c.runtime_providers), key=lambda v: v.object_id)
    ),
)


# Executable roles.

from dataclasses import dataclass, replace
from typing import cast

from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.candidate_payloads import CandidatePayloadPlane
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import DEVELOPMENT

from empirical_lawhood.adapters.simulators.matrix_preparation.method_provider import CANDIDATE_PAYLOAD_PORT, PreparationMethodProvider
from empirical_lawhood.domains.matrix.matrix_preparation.topology import METHOD_CONFIG_TYPES, METHOD_ROLES
from empirical_lawhood.domains.matrix.matrix_preparation.continuation import RETAINED_NATIVE_PORT, PreparationProjectionContinuation, PreparationRetainedNativePort
from empirical_lawhood.domains.matrix.matrix_preparation.contracts import PreparationProjectionConfig
from empirical_lawhood.domains.matrix.matrix_preparation.method_continuation import METHOD_CONTINUATION_ROLES, retained_method_port_key, method_continuation_type, METHOD_IMPORT_TYPES, _PreparationMethodImport, PreparationMethodContinuation, PreparationRetainedMethodPort


METHOD_BINDINGS = tuple(
    replace(
        executable(
            capability,
            components,
            (
                METHOD_CONFIG_TYPES[role],
                *((PreparationProjectionContinuation,) if role == "projection" else ()),
                *(
                    (method_continuation_type(role),)
                    if role in METHOD_CONTINUATION_ROLES
                    else ()
                ),
            ),
        ),
        required_issued_payload_schemas=(METHOD_CONFIG_TYPES[role].SCHEMA,),
        required_platform_port_keys=(CANDIDATE_PAYLOAD_PORT, retained_method_port_key(role))
        if role == "description"
        else (RETAINED_NATIVE_PORT,)
        if role == "projection"
        else (retained_method_port_key(role),)
        if role in METHOD_CONTINUATION_ROLES
        else (),
    )
    for role, capability, components in zip(
        METHOD_ROLES, METHOD_CAPABILITIES, METHOD_COMPONENTS, strict=True
    )
)


@dataclass(frozen=True, slots=True)
class PreparationMethodFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(
        self,
        *,
        registry: CapabilityRegistry,
        records: tuple[CanonicalRecord, ...],
        platform_ports: tuple[ExecutablePlatformPort, ...],
    ) -> PreparationMethodProvider:
        index = METHOD_BINDINGS.index(self.binding)
        role = METHOD_ROLES[index]
        configs = tuple(r for r in records if type(r) is METHOD_CONFIG_TYPES[role])
        imports = tuple(r for r in records if isinstance(r, PreparationProjectionContinuation))
        method_imports = tuple(
            r
            for r in records
            if isinstance(r, (PreparationMethodContinuation, _PreparationMethodImport))
        )
        if (
            len(configs) != 1
            or len(imports) > 1
            or len(method_imports) > 1
            or (method_imports and role not in METHOD_CONTINUATION_ROLES)
            or len(records) != 1 + len(imports) + len(method_imports)
            or (imports and role != "projection")
            or tuple(p.port_key for p in platform_ports) != self.binding.required_platform_port_keys
        ):
            raise ValueError(
                "preparation method factory changes its exact config/platform port roster"
            )
        method_sources = None
        if role in METHOD_CONTINUATION_ROLES:
            method_sources = cast(
                PreparationRetainedMethodPort,
                next(
                    p.port
                    for p in platform_ports
                    if p.port_key == retained_method_port_key(role)
                ),
            )
            continuation = method_sources.continuation
            if (continuation is None) != (not method_imports):
                raise ValueError("method retained-input declaration and port disagree")
            if continuation is not None:
                declaration = method_imports[0]
                config_identity = ObjectIdentity.from_record(
                    str(getattr(configs[0], "config_id")), configs[0]
                )
                if role == "description":
                    if declaration != continuation or continuation.assessment != config_identity:
                        raise ValueError("method continuation changed its frozen assessment")
                elif (
                    not isinstance(declaration, _PreparationMethodImport)
                    or declaration.ROLE != role
                    or declaration.continuation
                    != ObjectIdentity.from_record(continuation.config_id, continuation)
                    or declaration.scientific_config != config_identity
                ):
                    raise ValueError("method import differs from its exact issued declaration")
        plane = None
        retained = None
        if role == "projection":
            value = platform_ports[0].port
            if not hasattr(value, "continuation") or not callable(
                getattr(value, "create_source", None)
            ):
                raise TypeError("projection requires its bounded retained-native port")
            retained = cast(PreparationRetainedNativePort, value)
            native_continuation = retained.continuation
            config = cast(PreparationProjectionConfig, configs[0])
            if (native_continuation is None) != (not imports):
                raise ValueError("projection retained-input declaration and port disagree")
            if native_continuation is not None and (
                imports[0].continuation
                != ObjectIdentity.from_record(native_continuation.config_id, native_continuation)
                or imports[0].projection_config
                != ObjectIdentity.from_record(config.config_id, config)
                or config.source_config != native_continuation.source_config
            ):
                raise ValueError("projection native imports differ from their issued identities")
        if role == "description":
            value = platform_ports[0].port
            if not all(
                callable(getattr(value, key, None))
                for key in ("publish_candidate_payload", "read_candidate_payload")
            ):
                raise TypeError(
                    "preparation description requires its bounded candidate publication/read port"
                )
            plane = cast(CandidatePayloadPlane, value)
        return PreparationMethodProvider(
            registry,
            METHOD_CAPABILITIES[index],
            configs[0],
            role,
            plane,
            retained_sources=retained,
            retained_method_sources=method_sources,
        )


_EXECUTABLE_BINDINGS = tuple(sorted(METHOD_BINDINGS, key=lambda b: b.binding_id))
_EXECUTABLE_ID = f"executable-contribution.{DEVELOPMENT}.methods"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = tuple(
    PreparationMethodFactory(b) for b in _EXECUTABLE_BINDINGS
)
_ISSUED_RECORD_TYPES: tuple[type[CanonicalRecord], ...] = tuple(
    sorted(
        set(
            (
                *METHOD_CONFIG_TYPES.values(),
                PreparationProjectionContinuation,
                PreparationMethodContinuation,
                *METHOD_IMPORT_TYPES.values(),
            )
        ),
        key=lambda t: t.SCHEMA,
    )
)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION', 'METHOD_BINDINGS', 'METHOD_CAPABILITIES']

_EXECUTION_CONTRIBUTION = EXTENSION.executable
