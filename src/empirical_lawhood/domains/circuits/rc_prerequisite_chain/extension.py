# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.domains.circuits.rc_prerequisite_chain.operation_bindings import MAX_BYTES, NAMESPACE, operation_declarations

OPERATION_DECLARATIONS = operation_declarations()
MANIFESTS = tuple(row.manifest() for row in OPERATION_DECLARATIONS)
_BUILT = tuple(bundle(capability.capability_key.removeprefix(NAMESPACE + "."),
                     ExtensionContributionKind.METHOD, capability, (), None,
                     namespace=NAMESPACE, maximum_config_bytes=MAX_BYTES)
               for capability in MANIFESTS)
EXTENSION_BUNDLE_CONTRIBUTIONS = tuple(value[0] for value in _BUILT)
RC_PHASE_COMPONENTS = {value[0].capability_manifests[0].registry_id: value[1] for value in _BUILT}

_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    'method.rc-prerequisite-chain.phases', '1.0.0', ExtensionContributionKind.METHOD,
    (), tuple(sorted(MANIFESTS, key=lambda value: value.registry_id)),
    tuple(sorted((registration for contribution in EXTENSION_BUNDLE_CONTRIBUTIONS
                  for registration in contribution.candidate_capability_registrations), key=lambda value: value.registration_id)),
    (), tuple(sorted((registration for contribution in EXTENSION_BUNDLE_CONTRIBUTIONS
                      for registration in contribution.profile_registrations), key=lambda value: value.registration_id)),
    tuple(sorted((identity for contribution in EXTENSION_BUNDLE_CONTRIBUTIONS for identity in contribution.method_registrations), key=lambda value: value.object_id)),
    (), (),
    tuple(sorted((identity for contribution in EXTENSION_BUNDLE_CONTRIBUTIONS for identity in contribution.runtime_providers), key=lambda value: value.object_id)),
    (), False, False)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


_EXECUTABLE_FACTORIES = tuple(sorted((row.provider_factory(
    components=tuple(sorted(RC_PHASE_COMPONENTS[row.manifest().registry_id], key=lambda value: value.registration_id)))
    for row in OPERATION_DECLARATIONS), key=lambda value: value.binding.binding_id))
_EXECUTABLE_ID = "executable-contribution.rc-prerequisite-chain.phases"
_EXECUTABLE_VERSION = "1.0.0"
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
