# SPDX-License-Identifier: MPL-2.0
"""Installed compact E1 factories; no execution or scientific source at import."""
from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from ..compact_bindings import operation_factories

EXECUTABLE_BINDING_FACTORIES=tuple(sorted(operation_factories(),key=lambda factory:factory.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION=ExecutableBindingContribution('executable-contribution.matrix-factor-confirmation-compact','1.0.0',tuple(factory.binding for factory in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES=()
