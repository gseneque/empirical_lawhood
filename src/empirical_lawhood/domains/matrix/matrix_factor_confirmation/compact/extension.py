# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.
from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.execution.experiment_preparation import ExperimentInputConfigurationDeclaration, ExperimentProtocolDeclaration
from empirical_lawhood.domains.matrix.matrix_factor_confirmation.compact_bindings import NAMESPACE, operation_manifests
from empirical_lawhood.domains.matrix.matrix_factor_confirmation.compact_preparation import PROTOCOL_ID, E1CompactExperimentSpecification, E1CompactExperimentSelection, E1CompactExperimentSelectionV2, selection_types, bind_inputs, prepare, validate_instance

MANIFESTS=tuple(sorted(operation_manifests(),key=lambda value:value.registry_id))
_BUILT=tuple(bundle(value.capability_key.rsplit('.',1)[-1],ExtensionContributionKind.METHOD,value,(),None,namespace=NAMESPACE,maximum_config_bytes=None) for value in MANIFESTS)
_DISCOVERY_CONTRIBUTION=ExtensionBundleContribution('method.matrix-factor-confirmation-compact','1.0.0',ExtensionContributionKind.METHOD,(),MANIFESTS,
    tuple(sorted((row for contribution,_ in _BUILT for row in contribution.candidate_capability_registrations),key=lambda value:value.registration_id)),(),
    tuple(sorted((row for contribution,_ in _BUILT for row in contribution.profile_registrations),key=lambda value:value.registration_id)),(),(),(),
    tuple(sorted((row for contribution,_ in _BUILT for row in contribution.runtime_providers),key=lambda value:value.object_id)),(),False,False)
_PROTOCOLS=(ExperimentProtocolDeclaration(PROTOCOL_ID,E1CompactExperimentSpecification,prepare,'matrix-factor-confirmation-compact',
    example_paths=('programmes/foundations/emergent-structure/workflows/matrix-factor-confirmation/compact-specification.json',),maximum_config_bytes=None,input_record_types=selection_types(),bind_inputs=bind_inputs,validate_instance=validate_instance,
    requires_prospective_runtime_binding=True,configuration_inputs=(ExperimentInputConfigurationDeclaration('matrix-factor-confirmation-compact-declarative-selection',E1CompactExperimentSelectionV2,128*1024**2),ExperimentInputConfigurationDeclaration('matrix-factor-confirmation-compact-selection',E1CompactExperimentSelection,128*1024**2),)),)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.
from empirical_lawhood.domains.matrix.matrix_factor_confirmation.compact_bindings import operation_factories

_EXECUTABLE_FACTORIES=tuple(sorted(operation_factories(),key=lambda factory:factory.binding.binding_id))
_EXECUTABLE_ID = 'executable-contribution.matrix-factor-confirmation-compact'
_EXECUTABLE_VERSION = '1.0.0'
_ISSUED_RECORD_TYPES=()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
    protocols=_PROTOCOLS,
)

__all__ = ['EXTENSION']
