# SPDX-License-Identifier: MPL-2.0
"""Stock provider reconstruction, without Native/science or source readiness."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

from .operation_bindings import NAMESPACE
from .extension_bundle import OPERATION_DECLARATIONS

EXECUTABLE_BINDING_FACTORIES = tuple(sorted((row.provider_factory() for row in OPERATION_DECLARATIONS), key=lambda f: f.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution('executable-contribution.'+NAMESPACE, '1.0.0',
    tuple(f.binding for f in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
