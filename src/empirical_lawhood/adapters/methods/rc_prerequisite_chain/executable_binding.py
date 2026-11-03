# SPDX-License-Identifier: MPL-2.0
"""Code-owned stateless RC phase factories in the existing executable registry."""
from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from .extension_bundle import OPERATION_DECLARATIONS, RC_PHASE_COMPONENTS

EXECUTABLE_BINDING_FACTORIES = tuple(sorted((row.provider_factory(
    components=tuple(sorted(RC_PHASE_COMPONENTS[row.manifest().registry_id], key=lambda value: value.registration_id)))
    for row in OPERATION_DECLARATIONS), key=lambda value: value.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    "executable-contribution.rc-prerequisite-chain.phases", "1.0.0",
    tuple(row.binding for row in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
