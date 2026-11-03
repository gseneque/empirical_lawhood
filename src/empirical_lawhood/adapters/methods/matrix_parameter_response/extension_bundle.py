# SPDX-License-Identifier: MPL-2.0
"""Static declarations for parameter-consistent functional responses."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from .operation_bindings import operation_manifests
from .paired_operation_bindings import operation_manifests as paired_manifests

MANIFESTS = tuple(sorted((*operation_manifests(), *paired_manifests()), key=lambda m: m.registry_id))
_BUILT = tuple(bundle(m.capability_key.rsplit('.', 1)[-1], ExtensionContributionKind.METHOD,
    m, (), None, namespace=m.capability_key.rsplit('.', 1)[0], maximum_config_bytes=None) for m in MANIFESTS)
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    'method.matrix-parameter-response', '1.0.0', ExtensionContributionKind.METHOD, (), MANIFESTS,
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda r: r.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda r: r.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda r: r.object_id)), (), False, False)
