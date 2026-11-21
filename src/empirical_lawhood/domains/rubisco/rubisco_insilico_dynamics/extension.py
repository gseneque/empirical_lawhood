# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import NAMESPACE
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.operation_bindings import operation_manifests
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_operation_bindings import NAMESPACE as DURABLE_NAMESPACE, operation_manifests as durable_manifests

# The durable preparation is part of this extension's one declaration.
_DURABLE_MANIFESTS = durable_manifests()
_DURABLE_BUILT = tuple(bundle("prepare", ExtensionContributionKind.METHOD, row, (), None,
    namespace=DURABLE_NAMESPACE, maximum_config_bytes=None) for row in _DURABLE_MANIFESTS)
DURABLE_COMPONENTS = {row[0].capability_manifests[0].registry_id: tuple(sorted(row[1], key=lambda item: item.registration_id)) for row in _DURABLE_BUILT}
DURABLE_CONTRIBUTION = ExtensionBundleContribution("method." + DURABLE_NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD,
    (), _DURABLE_MANIFESTS, tuple(sorted((value for row, _ in _DURABLE_BUILT for value in row.candidate_capability_registrations), key=lambda row: row.registration_id)),
    (), tuple(sorted((value for row, _ in _DURABLE_BUILT for value in row.profile_registrations), key=lambda row: row.registration_id)),
    (), (), (), tuple(sorted((value for row, _ in _DURABLE_BUILT for value in row.runtime_providers), key=lambda row: row.object_id)), (), False, False)
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.geometry_operation_bindings import NODE as GEOMETRY_NODE, operation_declarations as geometry_declarations

_BUILT = tuple(
    bundle(
        op,
        ExtensionContributionKind.METHOD,
        m,
        (),
        None,
        namespace=NAMESPACE,
        maximum_config_bytes=None,
    )
    for op, m in zip(
        ("assess-preparation", "prepare"), operation_manifests(), strict=True
    )
) + tuple(bundle("reuse-geometry", ExtensionContributionKind.METHOD, row.manifest(), (), None,
    namespace=GEOMETRY_NODE.rsplit(".", 1)[0], maximum_config_bytes=None) for row in geometry_declarations())
COMPONENTS = {
    row[0].capability_manifests[0].registry_id: tuple(
        sorted(row[1], key=lambda r: r.registration_id)
    )
    for row in _BUILT
}
COMPONENTS.update(DURABLE_COMPONENTS)
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    "method." + NAMESPACE,
    "1.0.0",
    ExtensionContributionKind.METHOD,
    (),
    tuple(sorted((*operation_manifests(), *DURABLE_CONTRIBUTION.capability_manifests,
                  *(row.manifest() for row in geometry_declarations())),
                 key=lambda row: row.registry_id)),
    tuple(
        sorted(
            (*tuple(r for row, _ in _BUILT for r in row.candidate_capability_registrations),
             *DURABLE_CONTRIBUTION.candidate_capability_registrations),
            key=lambda r: r.registration_id,
        )
    ),
    (),
    tuple(
        sorted(
            (*tuple(r for row, _ in _BUILT for r in row.profile_registrations),
             *DURABLE_CONTRIBUTION.profile_registrations),
            key=lambda r: r.registration_id,
        )
    ),
    (),
    (),
    (),
    tuple(
        sorted(
            (*tuple(r for row, _ in _BUILT for r in row.runtime_providers),
             *DURABLE_CONTRIBUTION.runtime_providers),
            key=lambda r: r.object_id,
        )
    ),
    (),
    False,
    False,
)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import NAMESPACE
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.operation_bindings import operation_declarations
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_operation_bindings import operation_declarations as durable_declarations
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.geometry_operation_bindings import operation_declarations as geometry_declarations

_EXECUTABLE_FACTORIES = tuple(sorted((row.provider_factory(components=COMPONENTS[row.manifest().registry_id])
    for row in (*operation_declarations(), *durable_declarations(), *geometry_declarations())), key=lambda row: row.binding.binding_id))
_EXECUTABLE_ID = "executable-contribution." + NAMESPACE
_EXECUTABLE_VERSION = "1.0.0"
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
