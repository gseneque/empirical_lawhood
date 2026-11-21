# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.domains.rubisco.rubisco_inquiry.operation_bindings import MAX_BYTES, NAMESPACE, operation_manifests
_BUILT = tuple(bundle(v.capability_key.removeprefix(NAMESPACE + '.'), ExtensionContributionKind.METHOD,
    v, (), None, namespace=NAMESPACE, maximum_config_bytes=MAX_BYTES) for v in operation_manifests())
COMPONENTS = {v[0].capability_manifests[0].registry_id: tuple(sorted(v[1], key=lambda c: c.registration_id)) for v in _BUILT}
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    'method.' + NAMESPACE, '1.0.0', ExtensionContributionKind.METHOD, (),
    tuple(sorted(operation_manifests(), key=lambda v: v.registry_id)),
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda v: v.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda v: v.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda v: v.object_id)), (), False, False)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.

from empirical_lawhood.domains.rubisco.rubisco_inquiry.operation_bindings import NAMESPACE, operation_declarations

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
