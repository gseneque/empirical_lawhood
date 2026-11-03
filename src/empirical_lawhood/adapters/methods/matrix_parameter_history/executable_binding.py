# SPDX-License-Identifier: MPL-2.0
"""Installed parameter-history factories; reconstruction has no native effects."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

from .operation_bindings import operation_factories
from .compact_operation_bindings import operation_factories as compact_factories
from .chunked_operation_bindings import operation_factories as chunked_factories


EXECUTABLE_BINDING_FACTORIES = tuple(sorted((*operation_factories(), *compact_factories(), *chunked_factories()), key=lambda f: f.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    'executable-contribution.matrix-parameter-history', '1.0.0',
    tuple(f.binding for f in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
