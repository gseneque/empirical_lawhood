# SPDX-License-Identifier: MPL-2.0
"""Static compact E1 successor; discovery performs no prerequisite reads."""
from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution,ExtensionContributionKind
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputConfigurationDeclaration,ExperimentProtocolDeclaration
from ..compact_bindings import NAMESPACE,operation_manifests
from ..compact_preparation import PROTOCOL_ID,E1CompactExperimentSpecification,E1CompactExperimentSelection,E1CompactExperimentSelectionV2,selection_types,bind_inputs,prepare,validate_instance

MANIFESTS=tuple(sorted(operation_manifests(),key=lambda value:value.registry_id))
_BUILT=tuple(bundle(value.capability_key.rsplit('.',1)[-1],ExtensionContributionKind.METHOD,value,(),None,namespace=NAMESPACE,maximum_config_bytes=None) for value in MANIFESTS)
EXTENSION_BUNDLE_CONTRIBUTION=ExtensionBundleContribution('method.matrix-factor-confirmation-compact','1.0.0',ExtensionContributionKind.METHOD,(),MANIFESTS,
    tuple(sorted((row for contribution,_ in _BUILT for row in contribution.candidate_capability_registrations),key=lambda value:value.registration_id)),(),
    tuple(sorted((row for contribution,_ in _BUILT for row in contribution.profile_registrations),key=lambda value:value.registration_id)),(),(),(),
    tuple(sorted((row for contribution,_ in _BUILT for row in contribution.runtime_providers),key=lambda value:value.object_id)),(),False,False)
EXPERIMENT_PROTOCOL_DECLARATIONS=(ExperimentProtocolDeclaration(PROTOCOL_ID,E1CompactExperimentSpecification,prepare,'matrix-factor-confirmation-compact',
    example_paths=('programmes/foundations/emergent-structure/workflows/matrix-factor-confirmation/compact-specification.json',),maximum_config_bytes=None,input_record_types=selection_types(),bind_inputs=bind_inputs,validate_instance=validate_instance,
    requires_prospective_runtime_binding=True,configuration_inputs=(ExperimentInputConfigurationDeclaration('matrix-factor-confirmation-compact-declarative-selection',E1CompactExperimentSelectionV2,128*1024**2),ExperimentInputConfigurationDeclaration('matrix-factor-confirmation-compact-selection',E1CompactExperimentSelection,128*1024**2),)),)
