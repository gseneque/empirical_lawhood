# SPDX-License-Identifier: MPL-2.0
"""Real canonical source companions with explicitly selected custody allowances.

The captures are disclosed literal metadata. No Git/source capture, native
provider, scientific arrays, issue or execution occurs in these controls.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_prospective_authoring as owner
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits
from tests.prospective_source_capture_fixture import synthetic_capture
from tests.test_prospective_source_admission import companions
from tests import test_recursive_prospective_resource_preview as preview_fixtures


selected = preview_fixtures.selected


def _writer(writes, maximum=None):
    return SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path="/guarded")),
        write=writes.append, custody_limits=ArtifactCustodyLimits(control_record_bytes=maximum))


@pytest.mark.parametrize("extra", (0, 1), ids=("exact-bound", "bound-plus-one"))
def test_real_publisher_preflights_both_companions_before_either_write(extra):
    capture = synthetic_capture("source.capacity", "a" * 64, clean=False)
    _, payloads, _ = companions(capture)
    expected = tuple(payloads["provenance/" + name] for name in owner.SOURCE_PROVENANCE_MEMBERS)
    # The second genuine companion is larger: its refusal must leave no first
    # publication, rather than a plausible partial source-provenance directory.
    assert len(expected[1]) > len(expected[0])
    writes = []
    def publish():
        owner._publish_source_provenance(captured=capture, destination=Path("/guarded/prospective"),
            artifact_writer=_writer(writes, len(expected[1]) - extra))
    if extra:
        with pytest.raises(ValueError, match=r"source-observation\.json.*selected custody byte allowance"):
            publish()
        assert writes == []
    else:
        publish()
        assert tuple(row.payload for row in writes) == expected
        assert tuple(row.relative_path for row in writes) == tuple(
            "prospective/provenance/" + name for name in owner.SOURCE_PROVENANCE_MEMBERS)
        assert all(row.visibility_ceiling is owner.VisibilityCeiling.PROSPECTIVE
            and row.outcome_access is owner.OutcomeAccess.OUTCOME_BLIND for row in writes)


def test_real_publisher_names_oversized_manifest_and_publishes_nothing():
    capture = synthetic_capture("source.capacity", "a" * 64)
    writes = []
    with pytest.raises(ValueError, match=r"selected-source-manifest\.json.*selected custody byte allowance"):
        owner._publish_source_provenance(captured=capture, destination=Path("/guarded/prospective"),
            artifact_writer=_writer(writes, len(capture.manifest.canonical_bytes()) - 1))
    assert writes == []


@pytest.mark.parametrize("extra", (0, 1), ids=("exact-bound", "bound-plus-one"))
def test_real_capture_preflights_original_companion_bytes(monkeypatch, extra):
    capture = synthetic_capture("source.capacity", "a" * 64)
    _, payloads, _ = companions(capture)
    monkeypatch.setattr(owner, "capture_target_closure", lambda *_args: capture)
    writer = _writer([], max(map(len, payloads.values())) - extra)
    if extra:
        with pytest.raises(ValueError, match=r"source-observation\.json.*selected custody byte allowance"):
            owner._capture_prospective_source(Path("/uncaptured"), capture.closure.source_closure_id, artifact_writer=writer)
    else:
        result = owner._capture_prospective_source(Path("/uncaptured"), capture.closure.source_closure_id, artifact_writer=writer)
        assert result is capture
        assert companions(result)[1] == payloads


def test_actual_author_refuses_companion_capacity_before_compile_or_any_write(selected, monkeypatch):  # noqa: F811
    spec = selected.prospective_spec
    capture = synthetic_capture(spec.spec_id + ".source-closure", "a" * 64)
    _, payloads, _ = companions(capture)
    monkeypatch.setattr(owner, "capture_target_closure", lambda *_args: capture)
    monkeypatch.setattr(selected.plane, "custody_limits",
        ArtifactCustodyLimits(control_record_bytes=max(map(len, payloads.values())) - 1))
    def deny(*_args, **_kwargs):
        pytest.fail("oversized source companions reached compile or publication")
    monkeypatch.setattr(owner, "_compile", deny)
    monkeypatch.setattr(owner, "_compile_outer_candidate", deny)
    monkeypatch.setattr(selected.plane, "write", deny)
    destination = selected.plane.root.resolve("source-companion-capacity-refusal", for_write=True)
    with pytest.raises(ValueError, match=r"source-observation\.json.*selected custody byte allowance"):
        owner.author_recursive_prospective(spec=spec, output_dir=destination,
            **preview_fixtures._arguments(selected))
    assert not (destination / "candidate.json").exists()
    assert not (destination / "authored-wave.json").exists()


@pytest.mark.parametrize("allowed", (True, False), ids=("selected-budget", "before-plan-read"))
def test_retained_plan_reader_observes_the_same_selected_allowance(selected, monkeypatch, allowed):  # noqa: F811
    directory = selected.original.directory
    name = "preissue-execution-plan.json"
    size = (directory / name).stat().st_size
    maximum = max(size, (directory / "preissue-run-plan.json").stat().st_size) if allowed else size - 1
    monkeypatch.setattr(selected.plane, "custody_limits", ArtifactCustodyLimits(control_record_bytes=maximum))
    reads = []
    original = owner.read_bounded_bytes
    def observe(path, **kwargs):
        reads.append(Path(path).name)
        return original(path, **kwargs)
    monkeypatch.setattr(owner, "read_bounded_bytes", observe)
    with selected.plane.verification_scope() as reader:
        def load():
            return owner._load_recursive_prospective_members(directory=directory,
                root=selected.root / "checkout", storage_profile=object(), artifact_writer=reader)
        if allowed:
            result = load()
            assert result[2][name] == (directory / name).read_bytes()
        else:
            with pytest.raises(ValueError, match=name + ".*selected custody runtime-plan byte allowance"):
                load()
            assert name not in reads
