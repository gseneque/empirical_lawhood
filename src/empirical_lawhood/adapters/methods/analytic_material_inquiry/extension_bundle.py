# SPDX-License-Identifier: MPL-2.0
"""Cold discovery descriptors; no source inspection or scientific execution."""
from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from .operation_bindings import MAX_BYTES, NAMESPACE, operation_manifests
_BUILT = tuple(bundle(v.capability_key.removeprefix(NAMESPACE + '.'), ExtensionContributionKind.METHOD,
    v, (), None, namespace=NAMESPACE, maximum_config_bytes=MAX_BYTES) for v in operation_manifests())
COMPONENTS = {v[0].capability_manifests[0].registry_id: tuple(sorted(v[1], key=lambda c: c.registration_id)) for v in _BUILT}
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    'method.' + NAMESPACE, '1.0.0', ExtensionContributionKind.METHOD, (),
    tuple(sorted(operation_manifests(), key=lambda v: v.registry_id)),
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda v: v.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda v: v.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda v: v.object_id)), (), False, False)
