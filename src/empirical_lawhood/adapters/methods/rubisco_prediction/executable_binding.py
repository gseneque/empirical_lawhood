# SPDX-License-Identifier: MPL-2.0
"""Executable projections derive from the owning scientific declarations."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

from .extension_bundle import PREDICTION_PHASE_COMPONENTS
from .operation_bindings import NAMESPACE, operation_declarations

EXECUTABLE_BINDING_FACTORIES = tuple(declaration.provider_factory(
    components=PREDICTION_PHASE_COMPONENTS[declaration.manifest().registry_id])
    for declaration in sorted(operation_declarations(), key=lambda value: value.capability_key))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    "executable-contribution." + NAMESPACE, "1.0.0",
    tuple(sorted((factory.binding for factory in EXECUTABLE_BINDING_FACTORIES), key=lambda value: value.binding_id)))
EXECUTABLE_RECORD_TYPES = ()
