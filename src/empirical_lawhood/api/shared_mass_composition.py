# SPDX-License-Identifier: MPL-2.0
"""Decode once, validate both owners, and inject one explicit precomposition."""

from dataclasses import dataclass
from hashlib import sha256

from empirical_lawhood.methods.mass_balance_starter.bindings import operation_declarations
from empirical_lawhood.methods.mass_balance_starter.records import MassOperationConfig, MassScope
from empirical_lawhood.methods.mass_balance_starter.science import prediction_config
from empirical_lawhood.methods.shared_mass_reference.consumer import MassAssessmentProvider
from empirical_lawhood.methods.shared_mass_reference.producer import MassForecastProvider
from empirical_lawhood.methods.shared_mass_reference.provider import OperationInputHandle
from empirical_lawhood.methods.shared_mass_reference.service import MassScopeService
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import CompositeCampaignRuntimeProvider, ExecutablePlatformPort
from empirical_lawhood.execution.plans import DevelopmentExecutionPlan
from empirical_lawhood.execution.providers import CampaignRuntimeProviderRegistry
from empirical_lawhood.execution.recursive_provider import RecursiveOperationInputPort, recursive_input_port_key


@dataclass(frozen=True, slots=True)
class SharedMassRuntime:
    """One explicitly owned composition; no data-source or execution authority."""

    service: MassScopeService
    providers: tuple
    provider: CompositeCampaignRuntimeProvider
    precomposed: CampaignRuntimeProviderRegistry


def compose_mass_reference(*, registry, execution_plan, configurations,
                           scope_payload, scope_reference, input_suppliers):
    """Compose the worked two-operation domain after its ordinary source admission.

    The two-operation limit belongs to this example, not to provider composition.
    This pure helper reads no file, invokes no supplier and grants no authority.
    """
    if type(registry) is not CapabilityRegistry or type(execution_plan) is not DevelopmentExecutionPlan:
        raise TypeError('shared mass example requires its exact ordinary registry and development plan')
    registry.__post_init__()
    execution_plan.__post_init__()
    if (type(scope_reference) is not ObjectIdentity
            or (scope_reference.object_schema, scope_reference.object_version) != (MassScope.SCHEMA, MassScope.VERSION)):
        raise ValueError('shared mass configuration requires exactly MassScope@1.0.0')
    if type(scope_payload) is not bytes or len(scope_payload) > 4096:
        raise ValueError('shared mass configuration exceeds its bounded 4096-byte input')
    if sha256(scope_payload).hexdigest() != scope_reference.object_fingerprint:
        raise ValueError('shared mass configuration bytes differ from their selected identity')
    scope = decode_canonical_bytes(scope_payload, MassScope, maximum_bytes=4096)
    service = MassScopeService(scope, scope_reference)
    declarations = operation_declarations()
    if (registry.capabilities != tuple(row.manifest() for row in declarations)
            or execution_plan.registry_sha256 != registry.fingerprint()):
        raise ValueError('shared mass example requires the exact two original registered operations')
    if (type(configurations) is not tuple or len(configurations) != 2
            or any(type(row) is not MassOperationConfig for row in configurations)):
        raise TypeError('shared mass composition requires both original exact operation configurations')
    by_phase = {row.phase:row for row in configurations}
    if set(by_phase) != {'assess', 'predict'} or prediction_config(by_phase['assess']) != by_phase['predict']:
        raise ValueError('shared mass composition changes the original producer/consumer configuration relationship')
    for config in configurations:
        config.__post_init__()
        if config.scope != scope:
            raise ValueError('shared mass configuration changes quantity, kg units, domain, source, receiver or clock')
    configs = {row.node_id:row for row in configurations}
    if set(configs) != {task.task_id for task in execution_plan.tasks}:
        raise ValueError('shared mass composition changes the complete independent task census')
    for task in execution_plan.tasks:
        config = configs[task.task_id]
        if (task.capability.config.config_id != config.config_id
                or task.capability.config.content_sha256 != config.fingerprint()):
            raise ValueError('shared mass composition changes an original planned configuration')
        manifest = registry.resolve('mass-balance.' + config.phase, '1.0.0')
        if ((task.capability.capability_key, task.capability.capability_version,
                task.capability_implementation_sha256) != (manifest.capability_key,
                manifest.capability_version, manifest.implementation_sha256)):
            raise ValueError('shared mass composition changes the exact producer or consumer owner')
    keys = tuple(row.capability_key for row in declarations)
    if (type(input_suppliers) is not tuple or len(input_suppliers) != 2
            or any(type(row) is not tuple or len(row) != 2 for row in input_suppliers)
            or tuple(row[0] for row in input_suppliers) != keys):
        raise ValueError('shared mass composition requires one explicit input supplier per operation owner')
    pin = ObjectIdentity.from_record(execution_plan.execution_plan_id, execution_plan)
    handles = []
    for key, supplier in input_suppliers:
        specs = tuple(spec for task in execution_plan.tasks if task.capability.capability_key == key
            for spec in task.external_inputs)
        handles.append(OperationInputHandle(key, pin, specs, supplier))
    # All configuration/port selections validate before the first provider build.
    providers, bindings = [], []
    for declaration, handle, owner in zip(declarations, handles,
            (MassAssessmentProvider, MassForecastProvider), strict=True):
        factory = declaration.provider_factory()
        port = ExecutablePlatformPort(recursive_input_port_key(factory.registration.selection),
            RecursiveOperationInputPort(handle))
        delegate = factory.build_provider(registry=registry, records=(), platform_ports=(port,))
        providers.append(owner(delegate=delegate, service=service, selection=service.selection, execution_plan=pin))
        bindings.append(factory.binding)
    provider = CompositeCampaignRuntimeProvider(registry=registry, bindings=tuple(bindings), providers=tuple(providers))
    return SharedMassRuntime(service, tuple(providers), provider, CampaignRuntimeProviderRegistry((provider,)))
