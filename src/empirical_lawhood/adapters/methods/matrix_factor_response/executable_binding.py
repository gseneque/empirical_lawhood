# SPDX-License-Identifier: MPL-2.0
"""Installed method factories; no native work occurs during reconstruction."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

from .extension_bundle import COMPONENTS, OPERATION_DECLARATIONS


EXECUTABLE_BINDING_FACTORIES = tuple(sorted((declaration.provider_factory(components=COMPONENTS[declaration.manifest().registry_id])
    for declaration in OPERATION_DECLARATIONS),
    key=lambda factory: factory.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution('executable-contribution.matrix-factor-response',
    '1.0.0', tuple(f.binding for f in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
