# SPDX-License-Identifier: MPL-2.0
"""Cold descriptor for the observed source-mapping owner."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import (
    ExtensionBundleContribution,
    ExtensionContributionKind,
)
from .contracts import NAMESPACE
from .operation_bindings import operation_manifests
from .durable_extension_bundle import (
    COMPONENTS as DURABLE_COMPONENTS,
    EXTENSION_BUNDLE_CONTRIBUTION as DURABLE_CONTRIBUTION,
)
from .geometry_operation_bindings import NODE as GEOMETRY_NODE, operation_declarations as geometry_declarations

_BUILT = tuple(
    bundle(
        op,
        ExtensionContributionKind.METHOD,
        m,
        (),
        None,
        namespace=NAMESPACE,
        maximum_config_bytes=None,
    )
    for op, m in zip(
        ("assess-preparation", "prepare"), operation_manifests(), strict=True
    )
) + tuple(bundle("reuse-geometry", ExtensionContributionKind.METHOD, row.manifest(), (), None,
    namespace=GEOMETRY_NODE.rsplit(".", 1)[0], maximum_config_bytes=None) for row in geometry_declarations())
COMPONENTS = {
    row[0].capability_manifests[0].registry_id: tuple(
        sorted(row[1], key=lambda r: r.registration_id)
    )
    for row in _BUILT
}
COMPONENTS.update(DURABLE_COMPONENTS)
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    "method." + NAMESPACE,
    "1.0.0",
    ExtensionContributionKind.METHOD,
    (),
    tuple(sorted((*operation_manifests(), *DURABLE_CONTRIBUTION.capability_manifests,
                  *(row.manifest() for row in geometry_declarations())),
                 key=lambda row: row.registry_id)),
    tuple(
        sorted(
            (*tuple(r for row, _ in _BUILT for r in row.candidate_capability_registrations),
             *DURABLE_CONTRIBUTION.candidate_capability_registrations),
            key=lambda r: r.registration_id,
        )
    ),
    (),
    tuple(
        sorted(
            (*tuple(r for row, _ in _BUILT for r in row.profile_registrations),
             *DURABLE_CONTRIBUTION.profile_registrations),
            key=lambda r: r.registration_id,
        )
    ),
    (),
    (),
    (),
    tuple(
        sorted(
            (*tuple(r for row, _ in _BUILT for r in row.runtime_providers),
             *DURABLE_CONTRIBUTION.runtime_providers),
            key=lambda r: r.object_id,
        )
    ),
    (),
    False,
    False,
)
