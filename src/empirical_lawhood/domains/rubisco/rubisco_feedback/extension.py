# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.domains.rubisco.rubisco_feedback.assay_binding import MAX_BYTES, NAMESPACE, assay_declaration

_DISCOVERY_CONTRIBUTION, RUBISCO_COMPONENTS = bundle(
    "conditional-assay", ExtensionContributionKind.METHOD, assay_declaration().manifest(), (), None,
    namespace=NAMESPACE, maximum_config_bytes=MAX_BYTES)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


from empirical_lawhood.domains.rubisco.rubisco_feedback.assay_binding import assay_declaration


_EXECUTABLE_FACTORIES = (assay_declaration().provider_factory(components=RUBISCO_COMPONENTS),)
_EXECUTABLE_ID = "executable-contribution.rubisco-feedback"
_EXECUTABLE_VERSION = "1.0.0"
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
