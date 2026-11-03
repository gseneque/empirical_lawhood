# SPDX-License-Identifier: MPL-2.0
"""Cold descriptor for the pure adverse diagnostic history owner."""

from empirical_lawhood.adapters.composition.discovery import bundle
from empirical_lawhood.runtime.extension_bundles import (
    ExtensionBundleContribution,
    ExtensionContributionKind,
)
from empirical_lawhood.runtime.experiment_preparation import ExperimentProtocolDeclaration
from .authenticated_operation import operation_declaration
from .experiment_preparation import (
    bind_obstruction_experiment_inputs, input_record_types, prepare_obstruction_experiment,
    validate_obstruction_experiment_instance,
)
from .experiment_specification import ObstructionExperimentSpecification, PROTOCOL_ID
from .operation_bindings import NAMESPACE, operation_manifests

MANIFESTS = (*operation_manifests(), operation_declaration().manifest())
_BUILT = tuple(
    bundle(
        m.capability_key.removeprefix(NAMESPACE + "."),
        ExtensionContributionKind.METHOD,
        m,
        (),
        None,
        namespace=NAMESPACE,
        maximum_config_bytes=None,
    )
    for m in MANIFESTS
)
COMPONENTS = {
    row[0].capability_manifests[0].registry_id: tuple(
        sorted(row[1], key=lambda r: r.registration_id)
    )
    for row in _BUILT
}
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    "method." + NAMESPACE,
    "1.0.0",
    ExtensionContributionKind.METHOD,
    (),
    MANIFESTS,
    tuple(
        sorted(
            (r for row, _ in _BUILT for r in row.candidate_capability_registrations),
            key=lambda r: r.registration_id,
        )
    ),
    (),
    tuple(
        sorted(
            (r for row, _ in _BUILT for r in row.profile_registrations),
            key=lambda r: r.registration_id,
        )
    ),
    (),
    (),
    (),
    tuple(
        sorted(
            (r for row, _ in _BUILT for r in row.runtime_providers),
            key=lambda r: r.object_id,
        )
    ),
    (),
    False,
    False,
)

EXPERIMENT_PROTOCOL_DECLARATIONS = (ExperimentProtocolDeclaration(
    PROTOCOL_ID, ObstructionExperimentSpecification, prepare_obstruction_experiment,
    "battery-obstruction-experiment", maximum_config_bytes=1024**2,
    input_record_types=input_record_types(), bind_inputs=bind_obstruction_experiment_inputs,
    validate_instance=validate_obstruction_experiment_instance, bind_input_locations=True),)
