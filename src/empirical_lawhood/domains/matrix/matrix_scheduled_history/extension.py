# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from empirical_lawhood.domains.matrix.matrix_scheduled_history.operation_bindings import NAMESPACE, operation_declarations
from empirical_lawhood.domains.matrix.matrix_scheduled_history.compact_bindings import operation_declarations as compact_declarations

OPERATION_DECLARATIONS = (*operation_declarations(), *compact_declarations())
MANIFESTS = tuple(sorted((row.manifest() for row in OPERATION_DECLARATIONS), key=lambda m: m.registry_id))
_BUILT = tuple(bundle(m.capability_key.rsplit('.', 1)[-1], ExtensionContributionKind.METHOD, m, (), None,
    namespace=m.capability_key.rsplit('.', 1)[0], maximum_config_bytes=None) for m in MANIFESTS)
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution('method.'+NAMESPACE, '1.0.0', ExtensionContributionKind.METHOD,
    (), MANIFESTS, tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda r: r.registration_id)),
    (), tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda r: r.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda r: r.object_id)), (), False, False)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


from empirical_lawhood.domains.matrix.matrix_scheduled_history.operation_bindings import NAMESPACE


_EXECUTABLE_FACTORIES = tuple(sorted((row.provider_factory() for row in OPERATION_DECLARATIONS), key=lambda f: f.binding.binding_id))
_EXECUTABLE_ID = 'executable-contribution.'+NAMESPACE
_EXECUTABLE_VERSION = '1.0.0'
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
