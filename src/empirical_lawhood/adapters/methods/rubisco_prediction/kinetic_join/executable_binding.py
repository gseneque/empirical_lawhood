# SPDX-License-Identifier: MPL-2.0
"""Shared recursive factories; no sibling imports or private execution stack."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from .extension_bundle import COMPONENTS
from .operation_bindings import NAMESPACE, operation_declarations

EXECUTABLE_BINDING_FACTORIES = tuple(declaration.provider_factory(
    components=COMPONENTS[declaration.manifest().registry_id]) for declaration in operation_declarations())
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution("executable-contribution." + NAMESPACE,
    "1.0.0", tuple(sorted((f.binding for f in EXECUTABLE_BINDING_FACTORIES), key=lambda row: row.binding_id)))
EXECUTABLE_RECORD_TYPES = ()
