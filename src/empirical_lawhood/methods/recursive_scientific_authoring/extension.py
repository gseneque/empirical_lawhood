# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.
from hashlib import sha256
from empirical_lawhood.execution.declaration_helpers import component
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.recursive_authoring import RecursiveScientificSelection
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionContributionKind
from empirical_lawhood.execution.recursive_prospective import RECURSIVE_SELECTION_DECODER_KEY

IMPLEMENTATION = sha256(b"recursive-scientific-authoring-v2:exact-observed-size:typed-selected-science-preservation").hexdigest()
DECODER = component("scientific-selection", ExtensionComponentKind.CONFIG_DECODER,
                    (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,),
                    IMPLEMENTATION, "recursive")
assert DECODER.component_key == RECURSIVE_SELECTION_DECODER_KEY
AUTHOR = component("scientific-author", ExtensionComponentKind.PROGRAMME_AUTHOR,
                   (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,),
                   IMPLEMENTATION, "recursive")
COMPONENTS = tuple(sorted((DECODER, AUTHOR), key=lambda value: value.registration_id))
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution(
    "extension-contribution.recursive-scientific-authoring", "1.0.0", ExtensionContributionKind.STRUCTURAL,
    (), (), (), (), (), (), (ObjectIdentity.from_record(DECODER.registration_id, DECODER),), (), (),
    (ObjectIdentity.from_record(AUTHOR.registration_id, AUTHOR),), False, False)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.
from dataclasses import dataclass
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.recursive_authoring import RecursiveScientificSelection
from empirical_lawhood.execution.executable_bindings import ExecutableBindingRole, ExecutableCapabilityBinding, ExecutableRecordTypeBinding
from empirical_lawhood.execution.recursive_prospective import recursive_selection_decoder_registration


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


_EXECUTABLE_ID = "executable-contribution.recursive-scientific-authoring"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = (RecursiveScientificAuthorFactory(),)
_ISSUED_RECORD_TYPES = (RecursiveScientificSelection,)


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION', 'REGISTRATION', 'RecursiveScientificAuthorFactory']
