# SPDX-License-Identifier: MPL-2.0
"""Cold discovery of the 128 MiB draft and 64 MiB scientific payload profile."""

from hashlib import sha256

from empirical_lawhood.adapters.composition.discovery import component
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionComponentKind, ExtensionContributionKind
from empirical_lawhood.runtime.recursive_prospective import DRAFT128_RECURSIVE_SELECTION_DECODER_KEY, DRAFT128_RECURSIVE_DRAFT_MAXIMUM_BYTES, LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES

IMPLEMENTATION = sha256(
    ("recursive-scientific-authoring-draft128-v1:typed-selected-science-preservation:maximum-canonical-selection-"
        + str(LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES) + ":maximum-draft-"
        + str(DRAFT128_RECURSIVE_DRAFT_MAXIMUM_BYTES)).encode()
).hexdigest()
DECODER = component("scientific-selection-draft128", ExtensionComponentKind.CONFIG_DECODER,
    (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,), IMPLEMENTATION, "recursive")
assert DECODER.component_key == DRAFT128_RECURSIVE_SELECTION_DECODER_KEY
AUTHOR = component("scientific-author-draft128", ExtensionComponentKind.PROGRAMME_AUTHOR,
    (RecursiveScientificSelection.SCHEMA,), (RecursiveScientificSelection.SCHEMA,), IMPLEMENTATION, "recursive")
COMPONENTS = tuple(sorted((DECODER, AUTHOR), key=lambda value: value.registration_id))
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution(
    "extension-contribution.recursive-scientific-authoring-draft128", "1.0.0", ExtensionContributionKind.STRUCTURAL,
    (), (), (), (), (), (), (ObjectIdentity.from_record(DECODER.registration_id, DECODER),), (), (),
    (ObjectIdentity.from_record(AUTHOR.registration_id, AUTHOR),), False, False)
