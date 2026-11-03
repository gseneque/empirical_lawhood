# SPDX-License-Identifier: MPL-2.0
"""Cold discovery of the shared selected-science decoder and authoring owner."""
from hashlib import sha256
from empirical_lawhood.adapters.composition.discovery import component
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionContributionKind
from empirical_lawhood.runtime.recursive_prospective import RECURSIVE_SELECTION_DECODER_KEY

IMPLEMENTATION = sha256(b"recursive-scientific-authoring-v1:typed-selected-science-preservation").hexdigest()
DECODER = component("scientific-selection", ExtensionComponentKind.CONFIG_DECODER,
                    (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,),
                    IMPLEMENTATION, "recursive")
assert DECODER.component_key == RECURSIVE_SELECTION_DECODER_KEY
AUTHOR = component("scientific-author", ExtensionComponentKind.PROGRAMME_AUTHOR,
                   (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,),
                   IMPLEMENTATION, "recursive")
COMPONENTS = tuple(sorted((DECODER, AUTHOR), key=lambda value: value.registration_id))
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    "extension-contribution.recursive-scientific-authoring", "1.0.0", ExtensionContributionKind.STRUCTURAL,
    (), (), (), (), (), (), (ObjectIdentity.from_record(DECODER.registration_id, DECODER),), (), (),
    (ObjectIdentity.from_record(AUTHOR.registration_id, AUTHOR),), False, False)
