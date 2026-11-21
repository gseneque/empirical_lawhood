# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from empirical_lawhood.domains.rubisco.rubisco_insilico_sampling.operation_bindings import NAMESPACE, OPERATIONS, operation_manifests

_MANIFESTS = operation_manifests()
_BUILT = tuple(bundle(operation, ExtensionContributionKind.METHOD, manifest, (), None,
    namespace=NAMESPACE, maximum_config_bytes=None) for operation, manifest in zip(OPERATIONS, _MANIFESTS, strict=True))
COMPONENTS = {row[0].capability_manifests[0].registry_id: tuple(sorted(row[1], key=lambda item: item.registration_id)) for row in _BUILT}
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution("method." + NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD,
    (), _MANIFESTS, tuple(sorted((item for row, _ in _BUILT for item in row.candidate_capability_registrations), key=lambda item: item.registration_id)),
    (), tuple(sorted((item for row, _ in _BUILT for item in row.profile_registrations), key=lambda item: item.registration_id)), (), (), (),
    tuple(sorted((item for row, _ in _BUILT for item in row.runtime_providers), key=lambda item: item.object_id)), (), False, False)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.



from empirical_lawhood.domains.rubisco.rubisco_insilico_sampling.operation_bindings import NAMESPACE, operation_declarations

_EXECUTABLE_FACTORIES = tuple(sorted((row.provider_factory(components=COMPONENTS[row.manifest().registry_id])
    for row in operation_declarations()), key=lambda row: row.binding.binding_id))
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
