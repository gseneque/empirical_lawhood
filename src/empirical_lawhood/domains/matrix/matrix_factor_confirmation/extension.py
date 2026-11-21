# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from empirical_lawhood.domains.matrix.matrix_factor_confirmation.operation_bindings import NAMESPACE, operation_manifests

MANIFESTS = tuple(sorted(operation_manifests(), key=lambda m: m.registry_id))
_BUILT = tuple(bundle(m.capability_key.rsplit('.', 1)[-1], ExtensionContributionKind.METHOD,
    m, (), None, namespace=NAMESPACE, maximum_config_bytes=None) for m in MANIFESTS)
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    'method.matrix-factor-confirmation', '1.0.0', ExtensionContributionKind.METHOD, (), MANIFESTS,
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda r: r.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda r: r.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda r: r.object_id)), (), False, False)


from empirical_lawhood.execution.experiment_preparation import ExperimentInputConfigurationDeclaration, ExperimentProtocolDeclaration
from empirical_lawhood.domains.matrix.matrix_factor_confirmation.experiment_preparation import PROTOCOL_ID, E1ConfirmationSpecification, E1ConfirmationSelection, bind_inputs, prepare, validate_instance

_PROTOCOLS=(ExperimentProtocolDeclaration(PROTOCOL_ID,E1ConfirmationSpecification,prepare,
    'matrix-factor-confirmation',example_paths=('programmes/foundations/emergent-structure/workflows/matrix-factor-confirmation/specification.json',),
    maximum_config_bytes=None,input_record_types=(E1ConfirmationSelection,),bind_inputs=bind_inputs,
    validate_instance=validate_instance,configuration_inputs=(ExperimentInputConfigurationDeclaration(
        'matrix-factor-confirmation-selection',E1ConfirmationSelection,128*1024**2),)),)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


from empirical_lawhood.domains.matrix.matrix_factor_confirmation.operation_bindings import operation_factories


_EXECUTABLE_FACTORIES = tuple(sorted(operation_factories(), key=lambda f: f.binding.binding_id))
_EXECUTABLE_ID = 'executable-contribution.matrix-factor-confirmation'
_EXECUTABLE_VERSION = '1.0.0'
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
    protocols=_PROTOCOLS,
)

__all__ = ['EXTENSION']
