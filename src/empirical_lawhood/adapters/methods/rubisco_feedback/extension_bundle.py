# SPDX-License-Identifier: MPL-2.0
"""Static Rubisco descriptors without scientific execution or native imports."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind
from .assay_binding import MAX_BYTES, NAMESPACE, assay_declaration

EXTENSION_BUNDLE_CONTRIBUTION, RUBISCO_COMPONENTS = bundle(
    "conditional-assay", ExtensionContributionKind.METHOD, assay_declaration().manifest(), (), None,
    namespace=NAMESPACE, maximum_config_bytes=MAX_BYTES)
