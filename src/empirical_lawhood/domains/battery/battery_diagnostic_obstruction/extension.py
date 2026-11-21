# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.execution.experiment_preparation import ExperimentProtocolDeclaration
from empirical_lawhood.domains.battery.battery_diagnostic_obstruction.authenticated_operation import operation_declaration
from empirical_lawhood.domains.battery.battery_diagnostic_obstruction.experiment_preparation import bind_obstruction_experiment_inputs, input_record_types, prepare_obstruction_experiment, validate_obstruction_experiment_instance
from empirical_lawhood.domains.battery.battery_diagnostic_obstruction.experiment_specification import ObstructionExperimentSpecification, PROTOCOL_ID
from empirical_lawhood.domains.battery.battery_diagnostic_obstruction.operation_bindings import NAMESPACE, operation_manifests

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
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
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

_PROTOCOLS = (ExperimentProtocolDeclaration(
    PROTOCOL_ID, ObstructionExperimentSpecification, prepare_obstruction_experiment,
    "battery-obstruction-experiment", maximum_config_bytes=1024**2,
    input_record_types=input_record_types(), bind_inputs=bind_obstruction_experiment_inputs,
    validate_instance=validate_obstruction_experiment_instance, bind_input_locations=True),)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.

from empirical_lawhood.domains.battery.battery_diagnostic_obstruction.operation_bindings import NAMESPACE, operation_declarations
from empirical_lawhood.domains.battery.battery_diagnostic_obstruction.authenticated_operation import operation_declaration

_EXECUTABLE_FACTORIES = tuple(sorted((row.provider_factory(components=COMPONENTS[row.manifest().registry_id])
    for row in (*operation_declarations(), operation_declaration())), key=lambda row: row.manifest.registry_id))

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
