# SPDX-License-Identifier: MPL-2.0
"""Explicit bounded64 decoder with the unchanged scientific author factory."""

from empirical_lawhood.adapters.methods.recursive_scientific_authoring.executable_binding import RecursiveScientificAuthorFactory
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
from empirical_lawhood.runtime.executable_bindings import (
    ExecutableBindingContribution, ExecutableBindingRole, ExecutableCapabilityBinding, ExecutableRecordTypeBinding,
)
from empirical_lawhood.runtime.recursive_prospective import large_recursive_selection_decoder_registration

from .extension_bundle import AUTHOR, COMPONENTS, DECODER, IMPLEMENTATION

REGISTRATION = large_recursive_selection_decoder_registration(implementation_sha256=IMPLEMENTATION)
BINDING = ExecutableCapabilityBinding(
    "executable.recursive-scientific-authoring-bounded64", AUTHOR.component_key, "1.0.0", IMPLEMENTATION,
    ExecutableBindingRole.PROGRAMME_AUTHOR, AUTHOR.component_key, "1.0.0", IMPLEMENTATION,
    False, COMPONENTS, (), (ExecutableRecordTypeBinding(RecursiveScientificSelection.SCHEMA, "1.0.0"),),
    (RecursiveScientificSelection.SCHEMA,), (ObjectIdentity.from_record(DECODER.registration_id, DECODER),),
    (REGISTRATION,), (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,),
    (), (), False, False, False, False)

EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    "executable-contribution.recursive-scientific-authoring-bounded64", "1.0.0", (BINDING,))
EXECUTABLE_BINDING_FACTORIES = (RecursiveScientificAuthorFactory(binding=BINDING),)
EXECUTABLE_RECORD_TYPES = ()  # The legacy descriptor remains the canonical record owner.
