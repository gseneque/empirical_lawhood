# SPDX-License-Identifier: MPL-2.0
"""Allowlisted shared scientific selection decoder; construction grants no authority."""
from dataclasses import dataclass
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
from empirical_lawhood.runtime.executable_bindings import (
    ExecutableBindingContribution, ExecutableBindingRole, ExecutableCapabilityBinding, ExecutableRecordTypeBinding,
)
from empirical_lawhood.runtime.recursive_prospective import recursive_selection_decoder_registration
from .extension_bundle import AUTHOR, COMPONENTS, DECODER, IMPLEMENTATION

REGISTRATION = recursive_selection_decoder_registration(implementation_sha256=IMPLEMENTATION)
BINDING = ExecutableCapabilityBinding(
    "executable.recursive-scientific-authoring", AUTHOR.component_key, "1.0.0", IMPLEMENTATION,
    ExecutableBindingRole.PROGRAMME_AUTHOR, AUTHOR.component_key, "1.0.0", IMPLEMENTATION,
    False, COMPONENTS, (), (ExecutableRecordTypeBinding(RecursiveScientificSelection.SCHEMA, "1.0.0"),),
    (RecursiveScientificSelection.SCHEMA,), (ObjectIdentity.from_record(DECODER.registration_id, DECODER),),
    (REGISTRATION,), (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,),
    (), (), False, False, False, False)


@dataclass(frozen=True, slots=True)
class RecursiveScientificAuthorFactory:
    binding: ExecutableCapabilityBinding = BINDING

    def build_study_author(self, *, records, platform_ports):
        if platform_ports or len(records) != 1 or type(records[0]) is not RecursiveScientificSelection:
            raise ValueError("scientific author requires the exact selected-science operand")
        return records[0]


EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution(
    "executable-contribution.recursive-scientific-authoring", "1.0.0", (BINDING,))
EXECUTABLE_BINDING_FACTORIES = (RecursiveScientificAuthorFactory(),)
EXECUTABLE_RECORD_TYPES = (RecursiveScientificSelection,)
