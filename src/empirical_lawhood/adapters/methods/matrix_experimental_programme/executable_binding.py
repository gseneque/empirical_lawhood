# SPDX-License-Identifier: MPL-2.0
"""Existing workers execute saved reducers and the prepared opportunity."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

from .operation_bindings import NAMESPACE, operation_declarations
from .prepared_functional_bindings import operation_declarations as prepared_declarations
from .selected_protected_bindings import operation_declarations as selected_declarations
from .selected_opportunity_bindings import operation_declarations as opportunity_declarations
from .selected_revision_bindings import operation_declarations as revision_declarations
from empirical_lawhood.adapters.methods.matrix_source_evidence import source_declarations


EXECUTABLE_BINDING_FACTORIES = tuple(row.provider_factory() for row in sorted(
    (*operation_declarations(), *prepared_declarations(), *selected_declarations(), *opportunity_declarations(), *revision_declarations(), *source_declarations()),
    key=lambda row: (row.capability_key, row.capability_version)))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    "executable-contribution." + NAMESPACE, "1.0.0",
    tuple(row.binding for row in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
