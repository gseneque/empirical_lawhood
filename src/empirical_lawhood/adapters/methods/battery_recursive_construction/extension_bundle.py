# SPDX-License-Identifier: MPL-2.0
"""Static shared-engine battery capability discovery without solver imports."""
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from .executable_binding import _DISCOVERY_BUILT, operation_manifests

_CONTRIBUTIONS = tuple(value[0] for value in _DISCOVERY_BUILT)
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    'method.battery-recursive.operations', '1.0.0', ExtensionContributionKind.METHOD,
    (), tuple(sorted(operation_manifests(), key=lambda value: value.registry_id)),
    tuple(sorted((registration for contribution in _CONTRIBUTIONS
                  for registration in contribution.candidate_capability_registrations), key=lambda value: value.registration_id)),
    (), tuple(sorted((registration for contribution in _CONTRIBUTIONS
                      for registration in contribution.profile_registrations), key=lambda value: value.registration_id)),
    tuple(sorted((identity for contribution in _CONTRIBUTIONS for identity in contribution.method_registrations), key=lambda value: value.object_id)),
    (), (),
    tuple(sorted((identity for contribution in _CONTRIBUTIONS for identity in contribution.runtime_providers), key=lambda value: value.object_id)),
    (), False, False)
