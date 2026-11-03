# SPDX-License-Identifier: MPL-2.0
"""Cold discovery derives from the owning scientific declarations."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from .operation_bindings import NAMESPACE, operation_declarations

_BUILT = tuple(bundle(declaration.capability_key.removeprefix(NAMESPACE + "."),
    ExtensionContributionKind.METHOD, declaration.manifest(), (), None,
    namespace=NAMESPACE, maximum_config_bytes=None)
    for declaration in operation_declarations())
COMPONENTS = {contribution.capability_manifests[0].registry_id: components
    for contribution, components in _BUILT}
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
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
