# SPDX-License-Identifier: MPL-2.0
"""Code-owned operation composition; document values cannot select imports."""


def operation_catalog():
    """Return static typed registrations and manifests, without native imports."""
    from empirical_lawhood.execution.capabilities import CapabilityRegistry

    factories = operation_factories()
    registrations = tuple(sorted((factory.registration for factory in factories),
                                 key=lambda value: value.selection.selection_id))
    manifests = tuple(sorted((factory.manifest for factory in factories),
                             key=lambda value: value.registry_id))
    registry = CapabilityRegistry(registry_id="recursive-inquiry.registered-operations", capabilities=manifests)
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
    from empirical_lawhood.storage.contracts.record_codecs import OperationOutputRecordBinding, RecordCodecCatalog
    codecs = RecordCodecCatalog(
        (kind for factory in factories for kind in factory.output_codecs.values()),
        output_bindings=tuple(OperationOutputRecordBinding(factory.registration.selection,
            output.payload_schema, factory.output_codecs[output.payload_schema].VERSION)
            for factory in factories for output in factory.registration.outputs
            if output.profile is ArtifactProfile.CANONICAL_JSON))
    from empirical_lawhood.storage.contracts.recursive_record_codecs import input_record_type_census
    input_record_type_census(registrations, legacy_codecs=codecs)
    return registrations, registry, codecs


def operation_storage_codecs():
    """Closed code-owned physical contracts from the installed operations."""
    from empirical_lawhood.storage.contracts.recursive_storage_codecs import storage_codec_census

    if operation_factories is not _INSTALLED_OPERATION_FACTORIES:
        return storage_codec_census(tuple(factory.registration for factory in operation_factories()))
    from empirical_lawhood.api.recursive_operation_index import operation_storage_codecs as installed
    return installed()


def development_output_contracts(plan, codecs):
    """Authenticate installed producers and output shapes without changing custody.

    Ordinary development publication may have no issued semantic registration.
    Checking its producer and codec does not add one retrospectively.
    """
    from dataclasses import fields
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
    from empirical_lawhood.execution.plans import DevelopmentExecutionPlan
    from empirical_lawhood.execution.providers import CapabilityOutputSemanticContract
    from empirical_lawhood.storage.contracts.record_codecs import resolve_operation_output_codec

    if type(plan) is not DevelopmentExecutionPlan:
        raise TypeError("development output contracts require the actual development plan")
    from empirical_lawhood.api.recursive_operation_index import UnknownOperationSelection
    try:
        selected_factories = selected_operation_factories(
            f'{task.capability.capability_key}@{task.capability.capability_version}' for task in plan.tasks)
    except UnknownOperationSelection as error:
        raise PermissionError("development read changes the actual installed producer implementation") from error
    factories = {(value.manifest.capability_key, value.manifest.capability_version): value
        for value in selected_factories}
    contracts = {}
    for task in plan.tasks:
        factory = factories.get((task.capability.capability_key, task.capability.capability_version))
        if factory is None or factory.manifest.implementation_sha256 != task.capability_implementation_sha256:
            raise PermissionError("development read changes the actual installed producer implementation")
        for output in task.outputs:
            args = {}
            if output.profile is ArtifactProfile.CANONICAL_JSON:
                kind = resolve_operation_output_codec(codecs, factory.registration.selection, output.payload_schema)
                if kind is not factory.output_codecs.get(output.payload_schema):
                    raise PermissionError("development read lacks the exact original producer's typed codec")
                args = {"top_level_keys": ("schema", "value", "version"),
                    "value_keys": tuple(sorted(value.name for value in fields(kind))), "record_version": kind.VERSION}
            contract = CapabilityOutputSemanticContract.from_manifest(factory.manifest,
                payload_schema=output.payload_schema, profile=output.profile, **args)
            if contracts.setdefault(contract.key, contract) != contract:
                raise PermissionError("development output shapes conflict")
    return tuple(contracts.values())


def operation_runners(*, registry, plan, input_supplier=None):
    """Compose reviewed runners only after selected execution preflight."""
    from empirical_lawhood.execution.execution import RunnerRegistry
    from empirical_lawhood.execution.plans import ProtocolExecutionPlan

    if not isinstance(plan, ProtocolExecutionPlan) or plan.registry_sha256 != registry.fingerprint():
        raise ValueError("runner selection differs from its exact frozen plan and registry")
    selected = {}
    for task in plan.tasks:
        key = task.capability.capability_key, task.capability.capability_version
        if selected.setdefault(key, task.capability_implementation_sha256) != task.capability_implementation_sha256:
            raise ValueError("selected tasks disagree about one operation implementation")
    factories = {}
    for factory in selected_operation_factories(f'{key}@{version}' for key, version in selected):
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
    keys = tuple(sorted(factories, key=lambda key: f'{key[0]}@{key[1]}'))
    for key in keys:
        factory = factories[key]
        runner = factory.runner_factory()
        if runner.manifest != factory.manifest:
            raise ValueError("selected runner changed its exact registered manifest")
        if factory.runner_preparation_factory is not None:
            from empirical_lawhood.execution.execution import ParentPreparedTaskRunner

            runner = factory.runner_preparation_factory(input_supplier, runner)
            if (type(runner) is not ParentPreparedTaskRunner or runner.manifest != factory.manifest
                    or runner.native_effect != factory.registration.native_effect):
                raise ValueError("development preparation changes its installed wrapper or native scope")
        runners.append(runner)
    for runner, key in zip(runners, keys, strict=True):
        if runner.manifest != factories[key].manifest:
            raise ValueError("selected runner changed its exact registered manifest")
    return RunnerRegistry(tuple(runners), registry_sha256=registry.fingerprint())


def operation_factories():
    """Use the existing generated factory aggregate as the registration owner."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.execution.recursive_provider import RecursiveOperationProviderFactory

    registry = EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    return tuple(value for binding_id in registry.binding_ids
                 if isinstance(value := registry.factory(binding_id), RecursiveOperationProviderFactory))


# The full catalogue remains the explicit consistency-checking route. Custom
# composition keeps its previous eager contract rather than adopting stock keys.
_INSTALLED_OPERATION_FACTORIES = operation_factories
_INSTALLED_OPERATION_CATALOG = operation_catalog


def selected_operation_factories(selection_ids):
    selected = frozenset(selection_ids)
    if operation_factories is not _INSTALLED_OPERATION_FACTORIES:
        return tuple(factory for factory in operation_factories()
            if factory.registration.selection.selection_id in selected)
    from empirical_lawhood.api.recursive_operation_index import selected_factories
    return selected_factories(selected)


def operation_record_codecs():
    if operation_factories is not _INSTALLED_OPERATION_FACTORIES:
        return operation_catalog()[2]
    from empirical_lawhood.api.recursive_operation_index import operation_record_codecs as installed
    return installed()


def operation_catalog_for_draft(draft, *, catalog=None):
    """Load the draft's factories with the complete unchanged registry identity."""
    selected_catalog = operation_catalog if catalog is None else catalog
    if (selected_catalog is not _INSTALLED_OPERATION_CATALOG
            or operation_factories is not _INSTALLED_OPERATION_FACTORIES):
        return selected_catalog()
    from empirical_lawhood.api.recursive_operation_index import operation_registry
    factories = selected_operation_factories(op.selection.selection_id for op in draft.operations)
    return (tuple(factory.registration for factory in factories),
        operation_registry(), operation_record_codecs())


def inquiry_selection_scope(draft):
    """Prepare each installed domain selection once for this consumer lifetime.

    The contexts hold only immutable scientific operands. Original reads,
    current access and completion guards remain with their custody owners.
    """
    from contextlib import ExitStack, contextmanager

    @contextmanager
    def selected():
        selections = {operation.selection.selection_id for operation in draft.operations
            if operation.node_id in draft.selected_operation_ids}
        callbacks = tuple(dict.fromkeys(getattr(factory, 'inquiry_selection_scope', None)
            for factory in selected_operation_factories(selections)))
        with ExitStack() as lifetime:
            for callback in callbacks:
                if callback is not None:
                    lifetime.enter_context(callback(draft))
            yield
    return selected()
