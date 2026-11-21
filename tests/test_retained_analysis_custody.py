# SPDX-License-Identifier: MPL-2.0
"""Independent mutations of exact retained bytes and durable completion custody."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from hashlib import sha256

import pytest

from empirical_lawhood.storage.retained_analysis import publish_retained_analysis, read_retained_analysis, read_retained_analysis_member

from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.execution.retained_analysis import COMPLETION_FILENAME, RetainedAnalysisMember
from tests.numerical_provenance_fixtures import numerical_plane


def completed(tmp_path):
    plane = numerical_plane(tmp_path)
    directory = tmp_path / "completed"
    directory.mkdir()
    members = []
    for name, raw, schema, media in (("report.json", b'{"schema":"empirical-lawhood/test/analysis","value":{"count":24},"version":"1.0.0"}', "empirical-lawhood/test/analysis", "application/json"),
                                    ("arrays.npz", b"explicit software bytes", "empirical-lawhood/test/arrays", "application/x-npz")):
        (directory / name).write_bytes(raw)
        members.append(RetainedAnalysisMember(name, ArtifactIdentity("test." + name, "test-member", schema, sha256(raw).hexdigest(), media, len(raw))))
    completion = publish_retained_analysis(directory=directory, artifact_writer=plane, completion_id="test.completed", members=tuple(members))
    return plane, directory, completion


def test_fresh_read_and_opened_member_bytes_need_no_catalog(tmp_path):
    plane, directory, expected = completed(tmp_path)
    fresh = numerical_plane(tmp_path)
    actual = read_retained_analysis(directory=directory, artifact_writer=fresh)
    assert actual == expected and actual.scientific_authority == "NONE"
    assert read_retained_analysis_member(actual, "arrays.npz", directory=directory, artifact_writer=fresh, maximum_bytes=64) == b"explicit software bytes"


@pytest.mark.parametrize("changed", ("report.json", "arrays.npz", COMPLETION_FILENAME))
def test_changed_exact_bytes_are_refused(tmp_path, changed):
    plane, directory, _ = completed(tmp_path)
    path = directory / changed
    raw = bytearray(path.read_bytes())
    raw[len(raw)//2] ^= 1
    path.write_bytes(raw)
    with pytest.raises((ValueError, RuntimeError)):
        read_retained_analysis(directory=directory, artifact_writer=plane)


@pytest.mark.parametrize("removed", ("report.json", "arrays.npz", COMPLETION_FILENAME, COMPLETION_FILENAME + ".manifest.json", "commit"))
def test_missing_member_or_durable_publication_is_incomplete(tmp_path, removed):
    plane, directory, _ = completed(tmp_path)
    if removed == "commit":
        manifest = resolve_artifact_sidecar_bytes(plane, (directory / (COMPLETION_FILENAME + '.manifest.json')).read_bytes())
        removed_path = tmp_path / manifest.publication.commit_marker_relative_path
    else:
        removed_path = directory / removed
    removed_path.unlink()
    with pytest.raises((OSError, ValueError, RuntimeError)):
        read_retained_analysis(directory=directory, artifact_writer=plane)


def test_symlink_member_and_oversized_consuming_bound_are_refused(tmp_path):
    plane, directory, completion = completed(tmp_path)
    with pytest.raises(ValueError, match="bounded"):
        read_retained_analysis_member(completion, "arrays.npz", directory=directory, artifact_writer=plane, maximum_bytes=1)
    path = directory / "arrays.npz"
    outside = tmp_path / "other"
    path.rename(outside)
    path.symlink_to(outside)
    with pytest.raises((ValueError, RuntimeError)):
        read_retained_analysis(directory=directory, artifact_writer=plane)


def test_unlimited_consuming_allowance_retains_committed_extent_and_digest(tmp_path):
    plane, directory, completion = completed(tmp_path)
    assert read_retained_analysis_member(completion, "arrays.npz", directory=directory,
        artifact_writer=plane, maximum_bytes=None) == b"explicit software bytes"
    path = directory / "arrays.npz"
    original = path.read_bytes()
    path.write_bytes(original + b"uncommitted suffix")
    with pytest.raises((ValueError, RuntimeError)):
        read_retained_analysis_member(completion, "arrays.npz", directory=directory,
            artifact_writer=plane, maximum_bytes=None)
    path.write_bytes(b"x" * len(original))
    with pytest.raises(ValueError, match="committed completion"):
        read_retained_analysis_member(completion, "arrays.npz", directory=directory,
            artifact_writer=plane, maximum_bytes=None)


@pytest.mark.parametrize("allowance", (-1, True, 4.5, "64"))
def test_invalid_optional_member_allowance_refuses_before_read(tmp_path, allowance):
    plane, directory, completion = completed(tmp_path)
    with pytest.raises(ValueError, match="allowance"):
        read_retained_analysis_member(completion, "arrays.npz", directory=directory,
            artifact_writer=plane, maximum_bytes=allowance)
