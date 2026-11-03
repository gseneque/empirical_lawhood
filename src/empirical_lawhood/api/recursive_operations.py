# SPDX-License-Identifier: MPL-2.0
"""Code-owned operation composition; document values cannot select imports."""


def operation_catalog():
    """Return static typed registrations and manifests, without native imports."""
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry

    factories = operation_factories()
    registrations = tuple(sorted((factory.registration for factory in factories),
                                 key=lambda value: value.selection.selection_id))
    manifests = tuple(sorted((factory.manifest for factory in factories),
                             key=lambda value: value.registry_id))
    registry = CapabilityRegistry(registry_id="recursive-inquiry.registered-operations", capabilities=manifests)
    codecs = {}
    for factory in factories:
        for schema, codec in factory.output_codecs.items():
            if schema in codecs and codecs[schema] is not codec:
                raise ValueError("registered recursive factories disagree on a strict output codec")
            codecs[schema] = codec
    from empirical_lawhood.runtime.recursive_record_codecs import input_record_type_census
    input_record_type_census(registrations, legacy_codecs=codecs)
    return registrations, registry, codecs


def operation_storage_codecs():
    """Closed code-owned physical contracts from the installed operations."""
    from empirical_lawhood.runtime.recursive_storage_codecs import storage_codec_census

    return storage_codec_census(tuple(factory.registration for factory in operation_factories()))


def development_output_contracts(plan, codecs):
    """Authenticate installed producers and output shapes without changing custody.

    Ordinary development publication may have no issued semantic registration.
    Checking its producer and codec does not add one retrospectively.
    """
    from dataclasses import fields
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
    from empirical_lawhood.runtime.providers import CapabilityOutputSemanticContract

    if type(plan) is not DevelopmentExecutionPlan:
        raise TypeError("development output contracts require the actual development plan")
    factories = {(value.manifest.capability_key, value.manifest.capability_version): value
        for value in operation_factories()}
    contracts = {}
    for task in plan.tasks:
        factory = factories.get((task.capability.capability_key, task.capability.capability_version))
        if factory is None or factory.manifest.implementation_sha256 != task.capability_implementation_sha256:
            raise PermissionError("development read changes the actual installed producer implementation")
        for output in task.outputs:
            args = {}
            if output.profile is ArtifactProfile.CANONICAL_JSON:
                kind = codecs.get(output.payload_schema)
                if kind is None or kind.SCHEMA != output.payload_schema:
                    raise PermissionError("development read lacks the exact original typed codec")
                args = {"top_level_keys": ("schema", "value", "version"),
                    "value_keys": tuple(sorted(value.name for value in fields(kind))), "record_version": kind.VERSION}
            contract = CapabilityOutputSemanticContract.from_manifest(factory.manifest,
                payload_schema=output.payload_schema, profile=output.profile, **args)
            if contracts.setdefault(contract.key, contract) != contract:
                raise PermissionError("development output shapes conflict")
    return tuple(contracts.values())


def operation_runners(*, registry, plan, input_supplier=None):
    """Compose reviewed runners only after selected execution preflight."""
    from empirical_lawhood.runtime.execution import RunnerRegistry
    from empirical_lawhood.runtime.plans import ProtocolExecutionPlan

    if not isinstance(plan, ProtocolExecutionPlan) or plan.registry_sha256 != registry.fingerprint():
        raise ValueError("runner selection differs from its exact frozen plan and registry")
    selected = {}
    for task in plan.tasks:
        key = task.capability.capability_key, task.capability.capability_version
        if selected.setdefault(key, task.capability_implementation_sha256) != task.capability_implementation_sha256:
            raise ValueError("selected tasks disagree about one operation implementation")
    factories = {}
    for factory in operation_factories():
        key = factory.manifest.capability_key, factory.manifest.capability_version
        if key not in selected:
            continue
        if (key in factories or factory.manifest != registry.resolve(*key)
                or factory.manifest.implementation_sha256 != selected[key]):
            raise ValueError("selected operation differs from its frozen factory and registry")
        factories[key] = factory
    if set(factories) != set(selected):
        raise ValueError("selected operation lacks its installed executable factory")
    if input_supplier is None and any(factory.runner_preparation_factory is not None for factory in factories.values()):
        raise PermissionError("selected operation requires its actual parent input/custody supplier")
    runners = []
    for key in sorted(factories):
        factory = factories[key]
        runner = factory.runner_factory()
        if runner.manifest != factory.manifest:
            raise ValueError("selected runner changed its exact registered manifest")
        if factory.runner_preparation_factory is not None:
            from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner

            runner = factory.runner_preparation_factory(input_supplier, runner)
            if (type(runner) is not ParentPreparedTaskRunner or runner.manifest != factory.manifest
                    or runner.native_effect != factory.registration.native_effect):
                raise ValueError("development preparation changes its installed wrapper or native scope")
        runners.append(runner)
    for runner, key in zip(runners, sorted(factories), strict=True):
        if runner.manifest != factories[key].manifest:
            raise ValueError("selected runner changed its exact registered manifest")
    return RunnerRegistry(tuple(runners), registry_sha256=registry.fingerprint())


def operation_factories():
    """Use the existing generated factory aggregate as the registration owner."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProviderFactory

    registry = EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    return tuple(value for binding_id in registry.binding_ids
                 if isinstance(value := registry.factory(binding_id), RecursiveOperationProviderFactory))
