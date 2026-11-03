# SPDX-License-Identifier: MPL-2.0
"""Same-call compilation reuse with fresh custody; exposed software inputs only."""

from collections import Counter
from dataclasses import replace
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import prospective_experiment as companion
from empirical_lawhood.api import recursive_prospective_authoring as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalRootUnavailable
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs
from tests import test_prospective_experiment as fixtures
from tests.prospective_source_capture_fixture import synthetic_capture
from tests.test_recursive_prospective_resource_preview import _arguments, _install_fixture_hook


selected = fixtures.selected


def _count_preparation(monkeypatch):
    counts = Counter()
    for name in ("_compile", "_compile_outer_candidate", "validate_declared_recursive_input_payload"):
        original = getattr(owner, name)

        def observed(*args, _name=name, _original=original, **kwargs):
            counts[_name] += 1
            return _original(*args, **kwargs)

        monkeypatch.setattr(owner, name, observed)
    decode = companion.decode_canonical_bytes

    def decoded(raw, kind, **kwargs):
        if kind is ExecutableStudyCandidate:
            counts["companion_full_candidate_decodes"] += 1
        return decode(raw, kind, **kwargs)

    monkeypatch.setattr(companion, "decode_canonical_bytes", decoded)
    return counts


def _public_author(selected, monkeypatch, name, *, after_preview=None):
    composition = dict(composition=selected.composition, api_factory=selected.api_factory,
        candidate_catalog=selected.candidate_catalog)

    def hook(preparation, *, project_root, artifact_writer, output_dir):
        preview = companion.preview_prepared_prospective_experiment_candidate(preparation=preparation,
            design_inputs=RecursiveProspectiveDesignInputs.from_spec(selected.prospective_spec),
            source_configs=(selected.config,), project_root=project_root, artifact_writer=artifact_writer,
            **composition)
        if after_preview is not None:
            preview = after_preview(preview)
        return replace(preparation, prospective_spec=selected.prospective_spec, source_configs=(selected.config,),
            prospective_candidate_preview=preview)

    preparation_owner = _install_fixture_hook(selected, monkeypatch, hook)
    actual_author = companion.author_prepared_prospective_experiment

    def author(**kwargs):
        # Select the fixture's actual compiler catalog, not a compiler stub.
        return actual_author(**kwargs, **composition)

    monkeypatch.setattr(companion, "author_prepared_prospective_experiment", author)
    directory = Path(selected.plane.root.contract.canonical_path) / name
    report = preparation_owner.author_prepared_experiment(preparation=selected.preparation,
        project_root=selected.root / "checkout", artifact_writer=selected.plane, output_dir=directory)
    assert owner._prospective_authoring_invocation.get() is None
    return directory, report


def _same_members(selected, directory):
    original = selected.original.directory
    assert (directory / "authored-wave.json").read_bytes() == (original / "authored-wave.json").read_bytes()
    packet = companion.decode_canonical_bytes((original / "authored-wave.json").read_bytes(),
        owner.AuthoredRecursiveWave, maximum_bytes=None)
    assert len(packet.members) == 14
    for member in packet.members:
        assert (directory / member.filename).read_bytes() == (original / member.filename).read_bytes()
    for name in owner.SOURCE_PROVENANCE_MEMBERS:
        assert (directory / "provenance" / name).read_bytes() == (original / "provenance" / name).read_bytes()


def test_one_public_invocation_compiles_once_and_reuses_exact_authenticated_roots(selected, monkeypatch):
    counts = _count_preparation(monkeypatch)
    directory, report = _public_author(selected, monkeypatch, "same-invocation")
    assert counts["_compile"] == counts["_compile_outer_candidate"] == 1
    assert counts["validate_declared_recursive_input_payload"] > 0
    assert counts["companion_full_candidate_decodes"] == 0
    _same_members(selected, directory / "prospective")
    assert report["scientific_authority"] == "NONE" and report["native_contact"] == "none"
    # An independent later read authenticates and decodes afresh.
    packet, candidate, _ = companion._prospective_roots(directory / "prospective", selected.plane)
    assert candidate.fingerprint() == report["candidate_sha256"]
    assert packet.implementation == selected.preparation.execution.source_snapshot
    assert counts["companion_full_candidate_decodes"] == 1


def test_a_separately_supplied_preview_recompiles_and_retains_identical_members(selected, monkeypatch):
    counts = _count_preparation(monkeypatch)
    preview = owner.preview_recursive_prospective_candidate(
        design_inputs=RecursiveProspectiveDesignInputs.from_spec(selected.prospective_spec), **_arguments(selected))
    first_validations = counts["validate_declared_recursive_input_payload"]
    destination = Path(selected.plane.root.contract.canonical_path) / "separate-preview-invocation"
    owner.author_recursive_prospective(spec=selected.prospective_spec, expected_preview=preview,
        output_dir=destination, **_arguments(selected))
    assert counts["_compile"] == counts["_compile_outer_candidate"] == 2
    assert counts["validate_declared_recursive_input_payload"] == 2 * first_validations
    _same_members(selected, destination)


@pytest.mark.parametrize("damage", ("original-input", "published-input", "source", "publication-access", "preview", "capacity"))
def test_live_preparation_refreshes_input_source_custody_and_current_checks(selected, monkeypatch, damage):
    counts = _count_preparation(monkeypatch)
    directory = Path(selected.plane.root.contract.canonical_path) / ("refused-reuse-" + damage)
    changed_files = []
    original_limits = selected.plane.custody_limits

    def change(preview):
        if damage in ("original-input", "published-input"):
            path = (selected.preparation.input_files[0][1].path if damage == "original-input"
                else _arguments(selected)["input_bindings"][0][1])
            raw = path.read_bytes()
            mode = stat.S_IMODE(path.stat().st_mode)
            changed_files.append((path, raw, mode))
            path.chmod(mode | stat.S_IWUSR)
            path.write_bytes(raw + b" ")
        elif damage == "source":
            monkeypatch.setattr(owner, "capture_target_closure", lambda project_root, closure_id:
                synthetic_capture(closure_id, "d" * 64))
        elif damage == "publication-access":
            from empirical_lawhood.api import recursive_publications

            def denied(**kwargs):
                raise PermissionError("exposed current publication access withdrawn")

            monkeypatch.setattr(recursive_publications, "authenticate_registered_publications", denied)
        elif damage == "preview":
            return replace(preview, candidate=replace(preview.candidate, candidate_id="candidate.substituted"))
        else:
            selected.plane.custody_limits = replace(original_limits, control_record_bytes=1)
        return preview

    try:
        error = {"original-input": BoundedFileIOError, "published-input": ArtifactIdentityConflict,
            "publication-access": PermissionError}.get(damage, ValueError)
        with pytest.raises(error):
            _public_author(selected, monkeypatch, directory.name, after_preview=change)
    finally:
        for path, raw, mode in changed_files:
            path.write_bytes(raw)
            path.chmod(mode)
        selected.plane.custody_limits = original_limits
    assert not (directory / "prospective/authored-wave.json").exists()
    assert not (directory / "experiment").exists()
    assert owner._prospective_authoring_invocation.get() is None
    assert counts["_compile"] == (2 if damage == "preview" else 1)


def test_failed_invocation_discards_preparation_and_next_author_checks_afresh(selected, monkeypatch):
    counts = _count_preparation(monkeypatch)
    with pytest.raises(RuntimeError, match="exposed interruption"):
        with owner._prospective_preparation_scope():
            preview = owner.preview_recursive_prospective_candidate(
                design_inputs=RecursiveProspectiveDesignInputs.from_spec(selected.prospective_spec), **_arguments(selected))
            raise RuntimeError("exposed interruption")
    assert owner._prospective_authoring_invocation.get() is None
    destination = Path(selected.plane.root.contract.canonical_path) / "after-failed-invocation"
    owner.author_recursive_prospective(spec=selected.prospective_spec, expected_preview=preview,
        output_dir=destination, **_arguments(selected))
    assert counts["_compile"] == counts["_compile_outer_candidate"] == 2
    _same_members(selected, destination)


def test_live_reuse_never_retains_original_input_permission(selected, monkeypatch):
    counts = _count_preparation(monkeypatch)
    current = [True]

    def require_current():
        if not current[0]:
            raise PermissionError("exposed original input grant expired")

    access = SimpleNamespace(require_current=require_current)
    destination = Path(selected.plane.root.contract.canonical_path) / "expired-original-input"
    with owner._prospective_preparation_scope():
        preview = owner.preview_recursive_prospective_candidate(
            design_inputs=RecursiveProspectiveDesignInputs.from_spec(selected.prospective_spec),
            original_input_access=access, **_arguments(selected))
        current[0] = False
        with pytest.raises(PermissionError, match="grant expired"):
            owner.author_recursive_prospective(spec=selected.prospective_spec, expected_preview=preview,
                output_dir=destination, original_input_access=access, **_arguments(selected))
    assert counts["_compile"] == 1 and not destination.exists()


@pytest.mark.parametrize("damage", ("candidate", "sidecar", "marker", "ancestor"))
def test_reused_root_objects_do_not_hide_changed_published_custody(selected, monkeypatch, damage):
    original = owner.author_recursive_prospective
    changed = []

    def author(**kwargs):
        result = original(**kwargs)
        directory = kwargs["output_dir"]
        if damage == "ancestor":
            moved = directory.with_name("prospective-original")
            directory.rename(moved)
            directory.symlink_to(moved, target_is_directory=True)
        else:
            relative = (directory / "candidate.json").relative_to(selected.plane.root.contract.canonical_path).as_posix()
            manifest = selected.plane.read_manifest(relative)
            path = (directory / "candidate.json" if damage == "candidate"
                else directory / "candidate.json.manifest.json" if damage == "sidecar"
                else selected.plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False))
            path.write_bytes(path.read_bytes() + b" ")
        changed.append(True)
        return result

    monkeypatch.setattr(owner, "author_recursive_prospective", author)
    directory = Path(selected.plane.root.contract.canonical_path) / ("refused-published-root-" + damage)
    error = {"candidate": ArtifactIdentityConflict, "sidecar": ValueError,
        "marker": ArtifactIdentityConflict, "ancestor": ExternalRootUnavailable}[damage]
    with pytest.raises(error):
        _public_author(selected, monkeypatch, directory.name)
    assert changed == [True] and not (directory / "experiment").exists()
