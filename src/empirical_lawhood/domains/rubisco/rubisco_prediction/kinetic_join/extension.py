# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.execution.experiment_preparation import ExperimentProtocolDeclaration

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.operation_bindings import NAMESPACE, operation_declarations
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.experiment_inputs import bind_kinetic_experiment_inputs, input_record_types
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.experiment_preparation import prepare_kinetic_experiment, validate_kinetic_experiment_instance
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.experiment_specification import PROTOCOL_ID, RubiscoKineticExperimentSpecification

_MANIFESTS = tuple(declaration.manifest() for declaration in operation_declarations())
_BUILT = tuple(bundle(m.capability_key.removeprefix(NAMESPACE + "."), ExtensionContributionKind.METHOD,
    m, (), None, namespace=NAMESPACE, maximum_config_bytes=None) for m in _MANIFESTS)
COMPONENTS = {c.capability_manifests[0].registry_id: tuple(sorted(parts, key=lambda row: row.registration_id))
              for c, parts in _BUILT}
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution("method." + NAMESPACE,
    "1.0.0", ExtensionContributionKind.METHOD, (),
    tuple(sorted(_MANIFESTS, key=lambda row: row.registry_id)),
    tuple(sorted((r for c, _ in _BUILT for r in c.candidate_capability_registrations), key=lambda row: row.registration_id)), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.profile_registrations), key=lambda row: row.registration_id)), (), (), (),
    tuple(sorted((r for c, _ in _BUILT for r in c.runtime_providers), key=lambda row: row.object_id)), (), False, False)

_PROTOCOLS = (ExperimentProtocolDeclaration(PROTOCOL_ID,
    RubiscoKineticExperimentSpecification, prepare_kinetic_experiment, "rubisco-kinetic-experiment",
    example_paths=("programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/experiment.json",),
    input_record_types=input_record_types(), bind_inputs=bind_kinetic_experiment_inputs,
    validate_instance=validate_kinetic_experiment_instance),)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.operation_bindings import NAMESPACE, operation_declarations

_EXECUTABLE_FACTORIES = tuple(declaration.provider_factory(
    components=COMPONENTS[declaration.manifest().registry_id]) for declaration in operation_declarations())
_EXECUTABLE_ID = "executable-contribution." + NAMESPACE
_EXECUTABLE_VERSION = "1.0.0"
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
    protocols=_PROTOCOLS,
)

__all__ = ['EXTENSION']
