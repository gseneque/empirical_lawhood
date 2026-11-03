# SPDX-License-Identifier: MPL-2.0
"""One installed declaration census over the sole recursive compiler/provider."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from .extension_bundle import COMPONENTS
from .contracts import NAMESPACE
from .operation_bindings import operation_declarations
from .durable_operation_bindings import operation_declarations as durable_declarations
from .geometry_operation_bindings import operation_declarations as geometry_declarations

EXECUTABLE_BINDING_FACTORIES = tuple(sorted((row.provider_factory(components=COMPONENTS[row.manifest().registry_id])
    for row in (*operation_declarations(), *durable_declarations(), *geometry_declarations())), key=lambda row: row.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution("executable-contribution." + NAMESPACE,
    "1.0.0", tuple(row.binding for row in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
