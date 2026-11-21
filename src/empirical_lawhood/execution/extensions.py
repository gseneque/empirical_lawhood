# SPDX-License-Identifier: MPL-2.0
"""One extension declaration, projected into the existing closed registries.

An extension.py module exports EXTENSION. Generators derive discovery, codecs,
protocols and executable factories from that object. No mutable plugin registry
or import selected by scientific input is introduced.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType

from empirical_lawhood.science.records.serialization import validate_stable_id, validate_semantic_version
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.executable_bindings import ExecutableBindingContribution
from empirical_lawhood.execution.extension_bundles import (
    ExtensionBundleContribution, ExtensionContributionKind, ExtensionProfileRegistration,
)
from empirical_lawhood.execution.experiment_preparation import ExperimentProtocolDeclaration
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration
from empirical_lawhood.execution.workflow_descriptors import WorkflowDeclaration
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration, EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import WorkflowInstallationDeclaration


@dataclass(frozen=True, slots=True)
class ExtensionDeclaration:
    """A scientific extension's authoritative static registration facts.

    Native/source roles are declared on the selected operations. Application
    bindings remain in the application composition layer. Routine pure methods
    need only extension_id, version and their operation declarations.
    """
    extension_id: str
    version: str
    operations: tuple[RecursiveOperationDeclaration, ...]
    kind: ExtensionContributionKind = ExtensionContributionKind.METHOD
    protocols: tuple[ExperimentProtocolDeclaration, ...] = ()
    profiles: tuple[ExtensionProfileRegistration, ...] = ()
    workflows: tuple[WorkflowDeclaration, ...] = ()
    configurations: tuple[ConfigurationDeclaration, ...] = ()
    environments: tuple[EnvironmentDeclaration, ...] = ()
    installations: tuple[WorkflowInstallationDeclaration, ...] = ()

    def __post_init__(self) -> None:
        validate_stable_id(self.extension_id)
        validate_semantic_version(self.version)
        if type(self.kind) is not ExtensionContributionKind:
            raise TypeError("extension kind requires its exact declared role")
        groups = (
            (self.operations, RecursiveOperationDeclaration, "operations", "capability_key"),
            (self.protocols, ExperimentProtocolDeclaration, "protocols", "protocol_id"),
            (self.profiles, ExtensionProfileRegistration, "profiles", "registration_id"),
            (self.workflows, WorkflowDeclaration, "workflows", None),
            (self.configurations, ConfigurationDeclaration, "configurations", "consumer"),
            (self.environments, EnvironmentDeclaration, "environments", "route_id"),
            (self.installations, WorkflowInstallationDeclaration, "installations", None),
        )
        for rows, expected, name, key in groups:
            if type(rows) is not tuple or any(type(row) is not expected for row in rows):
                raise TypeError(f"extension {name} require exact immutable declarations")
            if key is not None and len({getattr(row, key) for row in rows}) != len(rows):
                raise ValueError(f"extension {name} repeat an authoritative owner")
        if not self.operations:
            raise ValueError("scientific extension requires at least one operation")
        # The existing constructors validate capability access and ownership.
        self.discovery
        self.executable

    @property
    def discovery(self) -> ExtensionBundleContribution:
        manifests = tuple(sorted((operation.manifest() for operation in self.operations),
                                 key=lambda manifest: manifest.registry_id))
        registrations = tuple(CandidateCapabilityRegistration(manifest,
            "recursive.provider." + manifest.capability_key, "1.0.0", "application/json", None)
            for manifest in manifests)
        return ExtensionBundleContribution(
            contribution_id=self.kind.value.lower() + "." + self.extension_id,
            contribution_version=self.version, kind=self.kind,
            evidence_profile_registries=(), capability_manifests=manifests,
            candidate_capability_registrations=registrations, dataset_capability_registries=(),
            profile_registrations=tuple(sorted(self.profiles, key=lambda row: row.registration_id)),
            method_registrations=(), config_decoders=(), artifact_validators=(),
            runtime_providers=(), study_authors=(), grants_authority=False, embeds_scientific_payload=False,
        )

    @property
    def factories(self) -> tuple:
        return tuple(operation.provider_factory() for operation in
                     sorted(self.operations, key=lambda operation: operation.capability_key))

    @property
    def executable(self) -> ExecutableBindingContribution:
        return ExecutableBindingContribution("executable-contribution." + self.extension_id,
            self.version, tuple(factory.binding for factory in self.factories))

    @property
    def record_types(self) -> tuple:
        # Issued-payload codecs have their separate exact decoder contracts.
        # Canonical operation input/output codecs are derived by the recursive
        # index from each factory, so they must not be duplicated here.
        return ()


@dataclass(frozen=True, slots=True)
class ExtensionDefinition:
    """Authoritative declaration for heterogeneous native and scientific roles.

    ``discovery`` owns the scientific profiles and capability facts. Factories
    own executable contracts; their binding census is generated here. This form
    supports existing source, protocol compiler and typed decoder roles without
    requiring pure calculation extensions to implement them.
    """
    discovery: ExtensionBundleContribution
    executable_id: str | None = None
    executable_version: str = "1.0.0"
    factories: tuple = ()
    record_types: tuple = ()
    protocols: tuple[ExperimentProtocolDeclaration, ...] = ()
    workflows: tuple[WorkflowDeclaration, ...] = ()
    configurations: tuple[ConfigurationDeclaration, ...] = ()
    environments: tuple[EnvironmentDeclaration, ...] = ()
    installations: tuple[WorkflowInstallationDeclaration, ...] = ()

    def __post_init__(self) -> None:
        if type(self.discovery) is not ExtensionBundleContribution:
            raise TypeError("extension definition requires its exact discovery contract")
        self.discovery.__post_init__()
        if type(self.factories) is not tuple or type(self.record_types) is not tuple:
            raise TypeError("extension factories and issued record types must be immutable tuples")
        if self.executable_id is None:
            if self.factories or self.record_types:
                raise ValueError("executable extension needs its declared executable identity")
        else:
            validate_stable_id(self.executable_id)
            validate_semantic_version(self.executable_version)
            if not self.factories:
                raise ValueError("executable extension requires its complete factory census")
        for values, kind in (
                (self.protocols, ExperimentProtocolDeclaration), (self.workflows, WorkflowDeclaration),
                (self.configurations, ConfigurationDeclaration), (self.environments, EnvironmentDeclaration),
                (self.installations, WorkflowInstallationDeclaration)):
            if type(values) is not tuple or any(type(value) is not kind for value in values):
                raise TypeError("extension facets require their exact immutable declarations")
        self.executable

    @property
    def executable(self) -> ExecutableBindingContribution | None:
        if self.executable_id is None:
            return None
        return ExecutableBindingContribution(self.executable_id, self.executable_version,
            tuple(sorted((factory.binding for factory in self.factories), key=lambda binding: binding.binding_id)))


_PROJECTIONS = {
    "EXTENSION_BUNDLE_CONTRIBUTION": "discovery",
    "EXECUTABLE_BINDING_CONTRIBUTION": "executable",
    "EXECUTABLE_BINDING_FACTORIES": "factories",
    "EXECUTABLE_RECORD_TYPES": "record_types",
    "EXPERIMENT_PROTOCOL_DECLARATIONS": "protocols",
    "WORKFLOW_DECLARATIONS": "workflows",
    "CONFIGURATION_DECLARATIONS": "configurations",
    "ENVIRONMENT_DECLARATIONS": "environments",
    "WORKFLOW_INSTALLATIONS": "installations",
}


def descriptor_projection(module: ModuleType, symbol: str, default=None):
    """Read an exact code-owned descriptor projection for registry generation.

    Existing advanced descriptors may supply their explicit low-level products.
    A unified descriptor cannot also own those facts as module-level products.
    """
    extension = getattr(module, "EXTENSION", None)
    if extension is None:
        if module.__name__.endswith(".extension"):
            raise TypeError(f"{module.__name__}: extension.py requires one EXTENSION declaration")
        return getattr(module, symbol, default)
    if type(extension) not in (ExtensionDeclaration, ExtensionDefinition):
        raise TypeError(f"{module.__name__}: EXTENSION requires an ExtensionDeclaration or ExtensionDefinition")
    if symbol in _PROJECTIONS:
        if hasattr(module, symbol):
            raise ValueError(f"{module.__name__}: {symbol} duplicates EXTENSION ownership")
        return getattr(extension, _PROJECTIONS[symbol])
    return getattr(module, symbol, default)


def projection_expression(module: ModuleType, symbol: str, alias: str) -> tuple[str, ...]:
    """Generate a direct import/reference; execution discovery never scans files."""
    if type(getattr(module, "EXTENSION", None)) in (ExtensionDeclaration, ExtensionDefinition) and symbol in _PROJECTIONS:
        return (f"from {module.__name__} import EXTENSION as {alias}_owner",
                f"{alias} = {alias}_owner.{_PROJECTIONS[symbol]}")
    return (f"from {module.__name__} import {symbol} as {alias}",)
