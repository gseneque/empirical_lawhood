# SPDX-License-Identifier: MPL-2.0
"""Cold registration of the additive joint kinetic consumer stages."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.runtime.experiment_preparation import ExperimentProtocolDeclaration

from .operation_bindings import NAMESPACE, operation_declarations
from .experiment_inputs import bind_kinetic_experiment_inputs, input_record_types
from .experiment_preparation import prepare_kinetic_experiment, validate_kinetic_experiment_instance
from .experiment_specification import PROTOCOL_ID, RubiscoKineticExperimentSpecification

_MANIFESTS = tuple(declaration.manifest() for declaration in operation_declarations())
_BUILT = tuple(bundle(m.capability_key.removeprefix(NAMESPACE + "."), ExtensionContributionKind.METHOD,
    m, (), None, namespace=NAMESPACE, maximum_config_bytes=None) for m in _MANIFESTS)
COMPONENTS = {c.capability_manifests[0].registry_id: tuple(sorted(parts, key=lambda row: row.registration_id))
              for c, parts in _BUILT}
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution("method." + NAMESPACE,
    "1.0.0", ExtensionContributionKind.METHOD, (),
    tuple(sorted(_MANIFESTS, key=lambda row: row.registry_id)),
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda row: row.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda row: row.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda row: row.object_id)), (), False, False)

EXPERIMENT_PROTOCOL_DECLARATIONS = (ExperimentProtocolDeclaration(PROTOCOL_ID,
    RubiscoKineticExperimentSpecification, prepare_kinetic_experiment, "rubisco-kinetic-experiment",
    example_paths=("programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/experiment.json",),
    input_record_types=input_record_types(), bind_inputs=bind_kinetic_experiment_inputs,
    validate_instance=validate_kinetic_experiment_instance),)
