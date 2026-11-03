# SPDX-License-Identifier: MPL-2.0
"""Exact publication membership with in-memory comparison-count falsifiers."""

from dataclasses import replace

import pytest

from empirical_lawhood.runtime.artifacts import ArtifactManifest
from tests.test_artifact_manifest_known_publication import _manifests


class CountedId(str):
    comparisons = 0
    __hash__ = str.__hash__

    def __lt__(self, other):
        type(self).comparisons += 1
        return str.__lt__(self, other)

    def __eq__(self, other):
        type(self).comparisons += 1
        return str.__eq__(self, other)


@pytest.mark.parametrize("count", (16, 256, 1024))
def test_reconstructing_all_members_avoids_quadratic_roster_comparisons(count):
    originals = _manifests(count)
    publication = originals[0].publication
    indexed = replace(publication, members=tuple(
        replace(member, materialization_id=CountedId(member.materialization_id))
        for member in publication.members
    ))
    # String instrumentation changes neither the declared order nor its bytes.
    assert indexed.canonical_bytes() == publication.canonical_bytes()
    CountedId.comparisons = 0
    reconstructed = tuple(ArtifactManifest(row.logical, row.materialization, indexed) for row in originals)
    assert count <= CountedId.comparisons <= count * (count.bit_length() + 2)
    assert all(row.publication is indexed for row in reconstructed)
    assert all((row.logical, row.materialization) == (old.logical, old.materialization)
               for row, old in zip(reconstructed, originals, strict=True))
    assert not hasattr(indexed, "_member_index")


def test_lookup_uses_materialization_order_and_retains_the_exact_original_objects():
    originals = _manifests(64)
    publication = originals[0].publication
    expected = {member.materialization_id: member for member in publication.members}
    for key, member in expected.items():
        assert publication.member_for_materialization(key) is member
    for key in ("a.before", "exposed.materialization.09", "z.after"):
        assert key not in expected
        assert publication.member_for_materialization(key) is None


@pytest.mark.parametrize("field,value", (
    ("physical_sha256", "a" * 64),
    ("relative_path", "outputs/different.json"),
    ("size_bytes", 100),
    ("materialization_id", "exposed.materialization.missing"),
))
def test_matching_id_cannot_hide_a_substituted_materialization(field, value):
    original = _manifests()[0]
    changed = replace(original.materialization, **{field: value})
    with pytest.raises(ValueError, match="does not include"):
        ArtifactManifest(original.logical, changed, original.publication)


def test_matching_id_cannot_hide_substituted_logical_metadata():
    original = _manifests()[0]
    changed = replace(original.logical, content_sha256="a" * 64)
    with pytest.raises(ValueError, match="does not include"):
        ArtifactManifest(changed, original.materialization, original.publication)


def test_unordered_roster_still_refuses_before_lookup():
    publication = _manifests()[0].publication
    with pytest.raises(ValueError, match="sorted"):
        replace(publication, members=tuple(reversed(publication.members)))
