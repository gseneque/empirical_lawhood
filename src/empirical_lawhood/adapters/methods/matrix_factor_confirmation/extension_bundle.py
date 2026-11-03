# SPDX-License-Identifier: MPL-2.0
"""Static E1 declarations; prospective science retains its authority boundaries."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind

from .operation_bindings import NAMESPACE, operation_manifests

MANIFESTS = tuple(sorted(operation_manifests(), key=lambda m: m.registry_id))
_BUILT = tuple(bundle(m.capability_key.rsplit('.', 1)[-1], ExtensionContributionKind.METHOD,
    m, (), None, namespace=NAMESPACE, maximum_config_bytes=None) for m in MANIFESTS)
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    'method.matrix-factor-confirmation', '1.0.0', ExtensionContributionKind.METHOD, (), MANIFESTS,
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda r: r.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda r: r.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda r: r.object_id)), (), False, False)


from empirical_lawhood.runtime.experiment_preparation import ExperimentInputConfigurationDeclaration,ExperimentProtocolDeclaration
from .experiment_preparation import (PROTOCOL_ID,E1ConfirmationSpecification,E1ConfirmationSelection,
    bind_inputs,prepare,validate_instance)

EXPERIMENT_PROTOCOL_DECLARATIONS=(ExperimentProtocolDeclaration(PROTOCOL_ID,E1ConfirmationSpecification,prepare,
    'matrix-factor-confirmation',example_paths=('programmes/foundations/emergent-structure/workflows/matrix-factor-confirmation/specification.json',),
    maximum_config_bytes=None,input_record_types=(E1ConfirmationSelection,),bind_inputs=bind_inputs,
    validate_instance=validate_instance,configuration_inputs=(ExperimentInputConfigurationDeclaration(
        'matrix-factor-confirmation-selection',E1ConfirmationSelection,128*1024**2),)),)
