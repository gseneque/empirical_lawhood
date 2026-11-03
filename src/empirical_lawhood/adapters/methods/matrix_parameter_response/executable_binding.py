# SPDX-License-Identifier: MPL-2.0
"""Installed parameter-response factories; static reconstruction has no effects."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

from .operation_bindings import operation_factories
from .paired_operation_bindings import operation_factories as paired_factories

EXECUTABLE_BINDING_FACTORIES = tuple(sorted((*operation_factories(), *paired_factories()), key=lambda f: f.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    'executable-contribution.matrix-parameter-response', '1.0.0', tuple(f.binding for f in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
