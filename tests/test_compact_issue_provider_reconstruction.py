# SPDX-License-Identifier: MPL-2.0
"""Public software issue and fresh provider reconstruction, without execution.

The original synthetic authority/source fixture is explicit. This establishes
no genuine authority, acquisition, clean-source qualification or scientific result.
"""

from empirical_lawhood.infrastructure.artifact_sidecars import decode_artifact_sidecar
from empirical_lawhood.runtime.artifact_sidecar import ArtifactManifestReference
from tests.runtime_platform.test_compact_artifact_publication import _census
from tests.runtime_platform.test_recursive_prospective_workflow import (
    _public_issued_handoff_fixture, _run_public_handoff,
)


def test_public_compact_issue_reconstructs_fresh_provider_with_original_authority_and_zero_execution(tmp_path, monkeypatch):
    parts = _public_issued_handoff_fixture(tmp_path, monkeypatch)
    plane, package = parts[3], parts[5]
    control = _run_public_handoff(tmp_path, issued_parts=parts, prepare_only=True)
    for issue_id, filename, logical_prefix in (
        (package.issued_study.base.issue_id, "manifest.json", "issued-manifest"),
        (package.issued_study.issue_id, "executable-study-manifest.json", "issued-executable-study-manifest"),
    ):
        relative = f"issued-programmes/{issue_id}/{filename}"
        raw = plane.root.resolve(relative + ".manifest.json", for_write=False).read_bytes()
        assert type(decode_artifact_sidecar(raw)) is ArtifactManifestReference
        assert plane.read_manifest(relative).logical.logical_artifact_id == f"{logical_prefix}.{issue_id}"
    before = _census(plane)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("provider reconstruction entered worker execution")

    monkeypatch.setattr(control.executor, "execute_deadline_free", forbidden)
    control.service._validate_campaign_authorization(package)
    control.service._validate_issued_execution_authority(package, at_utc="2026-10-16T00:00:00Z")
    first = control.service._resolve_campaign_provider(package, authorization_replayed=True)
    second = control.service._resolve_campaign_provider(package, authorization_replayed=True)
    assert first.reconstruction is not None and first.reconstruction == second.reconstruction
    assert first.reconstruction.scientific_recomputation_count == 0
    assert len(first.provider.runners(package.registry)) == 5
    assert control.executor.invocations == 0
    assert _census(plane) == before
