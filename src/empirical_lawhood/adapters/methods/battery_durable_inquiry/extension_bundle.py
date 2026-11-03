# SPDX-License-Identifier: MPL-2.0
"""Cold per-forecast descriptors; no scientific input selection or native entry."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from .operation_bindings import NAMESPACE, operation_manifests

_MANIFESTS = tuple(sorted(operation_manifests(), key=lambda row: row.registry_id))
_BUILT = tuple(bundle(row.capability_key.removeprefix(NAMESPACE + "."), ExtensionContributionKind.METHOD,
    row, (), None, namespace=NAMESPACE, maximum_config_bytes=None) for row in _MANIFESTS)
COMPONENTS = {row[0].capability_manifests[0].registry_id: tuple(sorted(row[1], key=lambda item: item.registration_id)) for row in _BUILT}
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution("method." + NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD,
    (), _MANIFESTS, tuple(sorted((value for row, _ in _BUILT for value in row.candidate_capability_registrations), key=lambda row: row.registration_id)),
    (), tuple(sorted((value for row, _ in _BUILT for value in row.profile_registrations), key=lambda row: row.registration_id)),
    (), (), (), tuple(sorted((value for row, _ in _BUILT for value in row.runtime_providers), key=lambda row: row.object_id)), (), False, False)
