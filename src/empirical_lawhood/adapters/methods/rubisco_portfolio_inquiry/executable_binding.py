# SPDX-License-Identifier: MPL-2.0
"""Executable projections derive from the owning scientific declarations."""
from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from .extension_bundle import COMPONENTS
from .operation_bindings import NAMESPACE, operation_declarations

EXECUTABLE_BINDING_FACTORIES = tuple(declaration.provider_factory(
    components=COMPONENTS[declaration.manifest().registry_id]) for declaration in operation_declarations())
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution('executable-contribution.' + NAMESPACE,
    '1.0.0', tuple(sorted((f.binding for f in EXECUTABLE_BINDING_FACTORIES), key=lambda v: v.binding_id)))
EXECUTABLE_RECORD_TYPES = ()
