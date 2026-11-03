# SPDX-License-Identifier: MPL-2.0
"""Battery inquiry providers reuse the existing recursive execution owner."""
from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from .extension_bundle import COMPONENTS, OPERATION_DECLARATIONS
from .operation_bindings import NAMESPACE

EXECUTABLE_BINDING_FACTORIES = tuple(row.provider_factory(
    components=COMPONENTS[row.manifest().registry_id]) for row in OPERATION_DECLARATIONS)
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution('executable-contribution.' + NAMESPACE, '1.1.0',
    tuple(sorted((row.binding for row in EXECUTABLE_BINDING_FACTORIES), key=lambda row: row.binding_id)))
EXECUTABLE_RECORD_TYPES = ()
