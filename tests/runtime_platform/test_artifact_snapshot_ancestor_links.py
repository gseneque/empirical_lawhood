# SPDX-License-Identifier: MPL-2.0
"""Ancestor-link substitutions cannot reuse unchanged leaf inode snapshots."""

from contextlib import nullcontext
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure.artifacts import ExternalRootUnavailable
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.runtime_platform.test_artifact_verification_scope import _publication


def _replace_with_link(root, name):
    directory = root / name
    held = root / (name + "-held")
    directory.rename(held)
    directory.symlink_to(held.name, target_is_directory=True)


@pytest.mark.parametrize("scoped", (False, True))
@pytest.mark.parametrize("plural", (False, True))
@pytest.mark.parametrize("consumer_raises", (False, True))
def test_same_in_root_directory_link_refuses_before_callback_result_escapes(tmp_path, scoped, plural, consumer_raises):
    plane, manifests = _publication(tmp_path)
    root = Path(plane.root.contract.canonical_path)
    observed = {}

    def consume(rows):
        observed.update({name: plane._descriptor_identity((root / name).stat()) for name in rows})
        _replace_with_link(root, "outputs")
        # This is the original gap: nofollow on each LEAF still sees the same
        # inode, bytes and timestamps through a symlink in its parent path.
        assert all(plane._descriptor_identity((root / name).stat(follow_symlinks=False)) == identity
            for name, identity in observed.items())
        if consumer_raises:
            raise RuntimeError("literal consumer refusal after ancestor substitution")
        return "changed custody must not escape"

    with pytest.raises(ExternalRootUnavailable, match="parent contains a symlink|parent is not an ordinary directory"):
        with (plane.verification_scope() if scoped else nullcontext(plane)) as writer:
            if plural:
                writer.verify_manifests_members(manifests, validate_members=consume)
            else:
                writer.verify_manifest_members(manifests[0], validate_members=consume)
    assert observed and (root / "outputs").is_symlink()


def test_scoped_other_prior_publication_link_substitution_refuses_before_new_callback_return(tmp_path):
    plane, first = _publication(tmp_path)
    root = Path(plane.root.contract.canonical_path)
    raw = ObjectIdentity("exposed.later-subject", ObjectIdentity.SCHEMA, "1.0.0", "b" * 64).canonical_bytes()
    result = plane.write(ArtifactWriteRequest("exposed.later-member", "later/member.json", ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.later-batch", "later", raw,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    later = plane.read_manifest(result.materialization.relative_path)
    calls = []

    def consume(rows):
        calls.append(tuple(rows))
        _replace_with_link(root, "outputs")
        return "prior custody substitution must not escape"

    with pytest.raises(ExternalRootUnavailable, match="parent contains a symlink|parent is not an ordinary directory"):
        with plane.verification_scope() as writer:
            writer.verify_manifest(first[0])
            writer.verify_manifests_members((later,), validate_members=consume)
    assert calls == [(later.materialization.relative_path,)]
