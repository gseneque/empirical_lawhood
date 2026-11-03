# SPDX-License-Identifier: MPL-2.0
"""Cold discovery of the shared-engine RC phase capabilities."""
from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from .operation_bindings import MAX_BYTES, NAMESPACE, operation_declarations

OPERATION_DECLARATIONS = operation_declarations()
MANIFESTS = tuple(row.manifest() for row in OPERATION_DECLARATIONS)
_BUILT = tuple(bundle(capability.capability_key.removeprefix(NAMESPACE + "."),
                     ExtensionContributionKind.METHOD, capability, (), None,
                     namespace=NAMESPACE, maximum_config_bytes=MAX_BYTES)
               for capability in MANIFESTS)
EXTENSION_BUNDLE_CONTRIBUTIONS = tuple(value[0] for value in _BUILT)
RC_PHASE_COMPONENTS = {value[0].capability_manifests[0].registry_id: value[1] for value in _BUILT}

EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
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
