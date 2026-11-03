# SPDX-License-Identifier: MPL-2.0
"""Additive cold provider with explicit immutable scientific work meaning."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from .durable_extension_bundle import COMPONENTS
from .durable_operation_bindings import NAMESPACE, operation_declarations

EXECUTABLE_BINDING_FACTORIES = tuple(row.provider_factory(components=COMPONENTS[row.manifest().registry_id])
    for row in operation_declarations())
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution("executable-contribution." + NAMESPACE,
    "1.0.0", tuple(row.binding for row in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
