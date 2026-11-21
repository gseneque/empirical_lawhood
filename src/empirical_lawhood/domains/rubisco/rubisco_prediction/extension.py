# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from empirical_lawhood.domains.rubisco.rubisco_prediction.operation_bindings import CONFIG_MAX_BYTES, NAMESPACE, operation_declarations

_BUILT = tuple(bundle(declaration.capability_key.removeprefix(NAMESPACE + "."),
    ExtensionContributionKind.METHOD, declaration.manifest(), (), None,
    namespace=NAMESPACE, maximum_config_bytes=CONFIG_MAX_BYTES)
    for declaration in operation_declarations())
PREDICTION_PHASE_COMPONENTS = {contribution.capability_manifests[0].registry_id: components
    for contribution, components in _BUILT}
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    "method." + NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD, (),
    tuple(sorted((manifest for contribution, _ in _BUILT for manifest in contribution.capability_manifests),
        key=lambda value: value.registry_id)),
    tuple(sorted((registration for contribution, _ in _BUILT
        for registration in contribution.candidate_capability_registrations), key=lambda value: value.registration_id)),
    (), tuple(sorted((registration for contribution, _ in _BUILT
        for registration in contribution.profile_registrations), key=lambda value: value.registration_id)),
    (), (), (), tuple(sorted((identity for contribution, _ in _BUILT
        for identity in contribution.runtime_providers), key=lambda value: value.object_id)),
    (), False, False)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.



from empirical_lawhood.domains.rubisco.rubisco_prediction.operation_bindings import NAMESPACE, operation_declarations

_EXECUTABLE_FACTORIES = tuple(declaration.provider_factory(
    components=PREDICTION_PHASE_COMPONENTS[declaration.manifest().registry_id])
    for declaration in sorted(operation_declarations(), key=lambda value: value.capability_key))
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
