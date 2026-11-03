# SPDX-License-Identifier: MPL-2.0
"""Invocation-local reuse preserves cold authentication of exposed controls."""
from collections import Counter
import os

import pytest

from empirical_lawhood.api import prospective_experiment as owner
from empirical_lawhood.api import recursive_prospective_authoring as prospective
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
from tests.test_prospective_experiment import _load, selected  # noqa: F401


def test_default_load_reuses_owner_controls_and_matches_custom_boundary(selected, monkeypatch):  # noqa: F811
    reads, decodes = Counter(), Counter()
    original_read, original_decode = owner._read, owner.decode_canonical_bytes

    def read(directory, name, writer, **arguments):
        reads[name] += 1
        return original_read(directory, name, writer, **arguments)

    def decode(raw, kind, **arguments):
        decodes[kind] += 1
        return original_decode(raw, kind, **arguments)

    monkeypatch.setattr(owner, "_read", read)
    monkeypatch.setattr(owner, "decode_canonical_bytes", decode)
    actual = _load(selected)
    controls = {"authored-wave.json", "decoder.json", "implementation.json",
        "candidate.json", "scientific-projection.json"}
    assert all(reads[name] == 0 for name in controls)
    assert decodes[ExecutableStudyCandidate] == 0

    reads.clear()
    decodes.clear()
    custom = _load(selected, handoff_loader=prospective.load_recursive_prospective_handoff)
    assert all(reads[name] == 1 for name in controls)
    assert decodes[ExecutableStudyCandidate] == 1
    for name in ("association", "instance", "candidate", "specification", "allocation"):
        assert getattr(actual, name).canonical_bytes() == getattr(custom, name).canonical_bytes()
    assert actual.design_records == custom.design_records
    assert actual.handoff.projection.canonical_bytes() == custom.handoff.projection.canonical_bytes()


@pytest.mark.parametrize("boundary", ("default", "custom"))
def test_later_invocation_reauthenticates_changed_candidate(selected, monkeypatch, boundary):  # noqa: F811
    previous = _load(selected)
    calls = []

    def cached_loader(**arguments):
        calls.append(arguments["directory"])
        return previous.handoff

    arguments = {} if boundary == "default" else {"handoff_loader": cached_loader}
    path = selected.directory / "prospective/candidate.json"
    raw, metadata = path.read_bytes(), path.stat()
    try:
        # Still valid JSON with unchanged decoded values; exact authenticated
        # bytes must refuse instead of trusting an earlier decoded candidate.
        path.write_bytes(raw + b" ")
        with pytest.raises(ArtifactIdentityConflict, match="artifact verification snapshot exceeds its byte bound"):
            _load(selected, **arguments)
    finally:
        path.write_bytes(raw)
        os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
    assert calls == ([] if boundary == "default" else [selected.directory / "prospective"])


def test_later_default_invocation_rechecks_source_and_preserves_recovery_selection(selected, monkeypatch):  # noqa: F811
    previous = _load(selected)
    calls = []

    class ChangedSourceInspector:
        def __init__(self, root):
            self.root = root

        def observe(self, closure):
            calls.append((self.root, closure))
            raise PermissionError("changed selected source")

    monkeypatch.setattr(prospective, "GitStudySourceClosureInspector", ChangedSourceInspector)
    with pytest.raises(PermissionError, match="changed selected source"):
        _load(selected)
    assert len(calls) == 1 and calls[0][0] == selected.root / "checkout"
    recovered = _load(selected, require_current_source=False)
    assert len(calls) == 1
    assert recovered.candidate.canonical_bytes() == previous.candidate.canonical_bytes()
    assert recovered.association == previous.association
