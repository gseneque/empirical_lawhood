# SPDX-License-Identifier: MPL-2.0
"""Cold declarations for the selected exposed prospective matrix route."""
from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from .operation_bindings import NAMESPACE, operation_declarations

OPERATION_DECLARATIONS = operation_declarations()
MANIFESTS = tuple(sorted((row.manifest() for row in OPERATION_DECLARATIONS), key=lambda m: m.registry_id))
_BUILT = tuple(bundle(m.capability_key.removeprefix(NAMESPACE + "."), ExtensionContributionKind.METHOD,
    m, (), None, namespace=NAMESPACE, maximum_config_bytes=None) for m in MANIFESTS)
COMPONENTS = {c.capability_manifests[0].registry_id: tuple(sorted(parts, key=lambda p: p.registration_id))
              for c, parts in _BUILT}
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    "method." + NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD, (),
    MANIFESTS,
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda r: r.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda r: r.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda r: r.object_id)), (), False, False)
