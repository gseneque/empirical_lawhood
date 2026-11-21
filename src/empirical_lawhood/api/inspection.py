# SPDX-License-Identifier: MPL-2.0
"""Compose read-only inspection from static declarations and the operator's selected roots."""
from __future__ import annotations

from importlib import import_module
from pathlib import Path

from empirical_lawhood.api.facade import EmpiricalLawhoodApi
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityProviderFactoryRegistry, GeneratedExecutableBindingAggregate
from empirical_lawhood.execution.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
from empirical_lawhood.execution.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile, resolve_external_root_contract
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.artifacts import GuardedExternalRoot
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
from empirical_lawhood.storage.guarded_catalog import select_operator_catalog


def load_installed_executable_bindings() -> GeneratedExecutableBindingAggregate:
    """Read the declared capability and component availability without loading their implementations."""
    from empirical_lawhood.execution.generated_executable_declarations import GENERATED_EXECUTABLE_BINDING_AGGREGATE

    return GENERATED_EXECUTABLE_BINDING_AGGREGATE


def load_installed_executable_factories() -> ExecutableCapabilityProviderFactoryRegistry:
    """Load the code-owned generated executable root, never a config-selected import."""

    generated = import_module(
        "empirical_lawhood.adapters.composition.generated_executable_bindings"
    )
    aggregate = generated.GENERATED_EXECUTABLE_BINDING_AGGREGATE
    if not isinstance(aggregate, GeneratedExecutableBindingAggregate):
        raise TypeError("generated executable aggregate has another record type")
    factories = generated.EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    if not isinstance(factories, ExecutableCapabilityProviderFactoryRegistry):
        raise TypeError("generated executable factory root has another registry type")
    if factories.aggregate is not aggregate and factories.aggregate != aggregate:
        raise ValueError("generated executable factories differ from their aggregate")
    expected_discovery = ObjectIdentity.from_record(
        GENERATED_EXTENSION_BUNDLE_AGGREGATE.aggregate_id,
        GENERATED_EXTENSION_BUNDLE_AGGREGATE,
    )
    if aggregate.discovery_aggregate != expected_discovery:
        raise ValueError("generated executable root binds another discovery aggregate")
    return factories


def create_inspection_api(
    *,
    repo_root: Path | None = None,
    operator_storage_profile: OperatorStorageProfile | None = None,
    operator_artifact_root_contract: ExternalRootContract | None = None,
    catalog_relative_path: str | None = None,
) -> EmpiricalLawhoodApi:
    """Compose static discovery and local validation without a storage plane."""
    if operator_artifact_root_contract is not None and operator_storage_profile is None:
        raise ValueError("selected inspection root requires its operator profile")

    root = Path.cwd().resolve() if repo_root is None else repo_root.resolve(strict=True)
    storage = (
        None
        if operator_storage_profile is None
        else GuardedExternalRoot(
            resolve_external_root_contract(
                operator_storage_profile,
                repo_root=root,
                home_root=Path.home(),
                for_write=False,
                selected_contract=operator_artifact_root_contract,
            )
        )
    )
    return EmpiricalLawhoodApi(
        repo_root=root,
        project_configured=repo_root is not None,
        catalog_access=select_operator_catalog(profile=operator_storage_profile,
            project_root=root, catalog_relative_path=catalog_relative_path),
        external_root=None if storage is None else Path(storage.contract.canonical_path),
        inspection_storage_root=storage,
        inspection_storage_read_only=(
            operator_storage_profile is not None
            and operator_storage_profile.access_mode is OperatorStorageAccessMode.READ_ONLY
        ),
        extension_bundle_aggregate=GENERATED_EXTENSION_BUNDLE_AGGREGATE,
        executable_binding_loader=load_installed_executable_bindings,
        executable_factory_loader=load_installed_executable_factories,
    )
