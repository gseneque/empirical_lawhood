# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.domains.rubisco.rubisco_cycle_constraints.operation_bindings import MAX_BYTES, NAMESPACE, operation_manifests

_BUILT = tuple(bundle(row.capability_key.removeprefix(NAMESPACE + '.'), ExtensionContributionKind.METHOD,
                     row, (), None, namespace=NAMESPACE, maximum_config_bytes=MAX_BYTES) for row in operation_manifests())
COMPONENTS = {row[0].capability_manifests[0].registry_id: tuple(sorted(row[1], key=lambda item: item.registration_id)) for row in _BUILT}
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    'method.' + NAMESPACE, '1.0.0', ExtensionContributionKind.METHOD, (),
    tuple(sorted(operation_manifests(), key=lambda row: row.registry_id)),
    tuple(sorted((value for row, _ in _BUILT for value in row.candidate_capability_registrations), key=lambda row: row.registration_id)), (),
    tuple(sorted((value for row, _ in _BUILT for value in row.profile_registrations), key=lambda row: row.registration_id)), (), (), (),
    tuple(sorted((value for row, _ in _BUILT for value in row.runtime_providers), key=lambda row: row.object_id)), (), False, False)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.

from empirical_lawhood.domains.rubisco.rubisco_cycle_constraints.operation_bindings import NAMESPACE, operation_declarations

_EXECUTABLE_FACTORIES = tuple(declaration.provider_factory(
    components=COMPONENTS[declaration.manifest().registry_id]) for declaration in operation_declarations())
_EXECUTABLE_ID = 'executable-contribution.' + NAMESPACE
_EXECUTABLE_VERSION = '1.0.0'
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
