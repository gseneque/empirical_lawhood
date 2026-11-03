# SPDX-License-Identifier: MPL-2.0
"""Executable projection derives from the supplied-case assay declaration."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution

from .assay_binding import assay_declaration
from .extension_bundle import RUBISCO_COMPONENTS

EXECUTABLE_BINDING_FACTORIES = (assay_declaration().provider_factory(components=RUBISCO_COMPONENTS),)
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    "executable-contribution.rubisco-feedback", "1.0.0",
    tuple(factory.binding for factory in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
