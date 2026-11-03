# SPDX-License-Identifier: MPL-2.0
"""Installed PURE parameter-factor factories; reconstruction has no effects."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

from .operation_bindings import operation_factories


EXECUTABLE_BINDING_FACTORIES = tuple(sorted(operation_factories(), key=lambda f: f.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    'executable-contribution.matrix-parameter-factor', '1.0.0',
    tuple(f.binding for f in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
