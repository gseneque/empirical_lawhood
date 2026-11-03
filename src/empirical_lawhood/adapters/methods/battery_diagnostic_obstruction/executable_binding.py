# SPDX-License-Identifier: MPL-2.0
"""Cold executable projections of the owning operation declarations."""
from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from .extension_bundle import COMPONENTS
from .operation_bindings import NAMESPACE, operation_declarations
from .authenticated_operation import operation_declaration

EXECUTABLE_BINDING_FACTORIES = tuple(sorted((row.provider_factory(components=COMPONENTS[row.manifest().registry_id])
    for row in (*operation_declarations(), operation_declaration())), key=lambda row: row.manifest.registry_id))

EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    "executable-contribution." + NAMESPACE,
    "1.0.0",
    tuple(r.binding for r in EXECUTABLE_BINDING_FACTORIES),
)
EXECUTABLE_RECORD_TYPES = ()
