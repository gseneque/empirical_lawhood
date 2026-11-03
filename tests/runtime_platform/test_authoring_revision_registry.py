# SPDX-License-Identifier: MPL-2.0
"""Closed authoring revisions share the original bounded strict parser."""
from dataclasses import dataclass
import json
from typing import ClassVar

import pytest

from empirical_lawhood.api.codecs import AuthoringCodecError, loads_registered_authoring
from empirical_lawhood.kernel.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class First(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/authoring-revision"
    value: int


@dataclass(frozen=True, slots=True)
class Second(CanonicalRecord):
    SCHEMA: ClassVar[str] = First.SCHEMA
    VERSION: ClassVar[str] = "2.0.0"
    value: int


@pytest.mark.parametrize("kind", (First, Second))
def test_exact_revision_dispatch_preserves_both_canonical_and_editable_bytes(kind):
    selected = kind(7)
    roots = {(record.SCHEMA, record.VERSION): record for record in (First, Second)}
    text = json.dumps(json.loads(selected.canonical_bytes()), indent=2)
    assert loads_registered_authoring(text, media_type="application/json", root_schemas=roots) == selected
    assert loads_registered_authoring(selected.canonical_bytes().decode(), media_type="application/json", root_schemas=roots) == selected


@pytest.mark.parametrize("revision", ("3.0.0", None, {}, []))
def test_unsupported_or_malformed_revision_has_no_fallback(revision):
    document = json.loads(First(7).canonical_bytes())
    document["version"] = revision
    with pytest.raises(AuthoringCodecError):
        loads_registered_authoring(json.dumps(document), media_type="application/json",
            root_schemas={(First.SCHEMA, First.VERSION): First, (Second.SCHEMA, Second.VERSION): Second})


def test_legacy_string_registry_stays_exact_and_mixed_registry_is_refused():
    assert loads_registered_authoring(First(7).canonical_bytes().decode(), media_type="application/json",
        root_schemas={First.SCHEMA: First}) == First(7)
    with pytest.raises(AuthoringCodecError):
        loads_registered_authoring(Second(7).canonical_bytes().decode(), media_type="application/json",
            root_schemas={First.SCHEMA: First})
    with pytest.raises(ValueError, match="ambiguous"):
        loads_registered_authoring(First(7).canonical_bytes().decode(), media_type="application/json",
            root_schemas={First.SCHEMA: First, (Second.SCHEMA, Second.VERSION): Second})
