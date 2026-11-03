# SPDX-License-Identifier: MPL-2.0
"""Cold installed descriptors for current source-bound numerical controls."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from .operation_bindings import NAMESPACE, OPERATIONS, operation_manifests

_MANIFESTS = operation_manifests()
_BUILT = tuple(bundle(operation, ExtensionContributionKind.METHOD, manifest, (), None,
    namespace=NAMESPACE, maximum_config_bytes=None) for operation, manifest in zip(OPERATIONS, _MANIFESTS, strict=True))
COMPONENTS = {row[0].capability_manifests[0].registry_id: tuple(sorted(row[1], key=lambda item: item.registration_id)) for row in _BUILT}
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution("method." + NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD,
    (), _MANIFESTS, tuple(sorted((item for row, _ in _BUILT for item in row.candidate_capability_registrations), key=lambda item: item.registration_id)),
    (), tuple(sorted((item for row, _ in _BUILT for item in row.profile_registrations), key=lambda item: item.registration_id)), (), (), (),
    tuple(sorted((item for row, _ in _BUILT for item in row.runtime_providers), key=lambda item: item.object_id)), (), False, False)
