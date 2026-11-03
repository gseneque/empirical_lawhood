# SPDX-License-Identifier: MPL-2.0
"""Pure source-capture/provenance controls: no Git, files or publications."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_prospective_authoring as owner
from empirical_lawhood.api import prospective_experiment as experiment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_json_document_bytes
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind
from tests.prospective_source_capture_fixture import synthetic_capture


def installed_capture():
    """Literal installed metadata, with no installation, Git or source observation."""
    from empirical_lawhood.infrastructure.selected_candidate import canonical_source_metadata_bytes
    from empirical_lawhood.infrastructure.source_closure import TrackedSourceMember
    from empirical_lawhood.infrastructure.source_policy import InstalledSourceAdmission
    from empirical_lawhood.planning.study_issue import SelectedSourceManifestMember
    original = synthetic_capture('source.installed', 'a' * 64)
    files = tuple(sorted((*original.source.tracked_files,
        TrackedSourceMember('pyproject.toml', '100644', 1, '2' * 64),
        TrackedSourceMember('uv.lock', '100644', 1, '3' * 64)), key=lambda row: row.relative_path))
    manifest = replace(original.manifest, members=tuple(SelectedSourceManifestMember(
        row.relative_path, row.mode, row.size_bytes, row.sha256) for row in files))
    metadata = canonical_source_metadata_bytes(implementation_commit=original.source.implementation_commit,
        implementation_sha256=original.source.implementation_sha256,
        source_tree_sha256=original.source.source_tree_sha256,
        tracked_files=[row.to_mapping() for row in files])
    admission = InstalledSourceAdmission(sha256(metadata).hexdigest(), tuple(row.relative_path for row in files))
    source = replace(original.source, tracked_files=files, source_admission=admission, final_source_admission=admission)
    return replace(original, source=source, manifest=manifest,
        closure=replace(original.closure, clean_worktree=False, exact_source_manifest=manifest.identity))


class MemoryDirectory:
    def __init__(self, names, *, symbolic=False):
        self.names = names
        self.symbolic = symbolic
    def __truediv__(self, name):
        if name == "provenance":
            return self
        return SimpleNamespace(is_symlink=lambda: False, is_file=lambda: name != ".publication-batches",
            is_dir=lambda: name == ".publication-batches", stat=lambda: SimpleNamespace(st_size=0))
    def is_symlink(self):
        return self.symbolic
    def is_dir(self):
        return True
    def iterdir(self):
        return tuple(SimpleNamespace(name=name) for name in self.names)


def companions(capture):
    observation = owner.ProspectiveSourceObservation(capture.closure.source_closure_id + ".source-observation",
        owner._source_reference(capture.closure), capture.manifest.identity,
        canonical_json_bytes(capture.source.to_mapping()).decode())
    payloads = {"provenance/selected-source-manifest.json": capture.manifest.canonical_bytes(),
        "provenance/source-observation.json": observation.canonical_bytes()}
    names = {name for name in owner.SOURCE_PROVENANCE_MEMBERS}
    names.update(name + ".manifest.json" for name in owner.SOURCE_PROVENANCE_MEMBERS)
    return observation, payloads, MemoryDirectory(names)


def test_new_capture_selects_exact_source_and_retains_truthful_raw_status(monkeypatch):
    capture = synthetic_capture("source.exposed", "a"*64, clean=False)
    monkeypatch.setattr(owner, "capture_target_closure", lambda *_args: capture)
    observed = owner._capture_prospective_source(Path("/source"), "source.exposed")
    assert observed == capture
    assert observed.closure.kind is SourceClosureKind.EXACT_SOURCE_CLOSURE
    assert observed.closure.clean_worktree is False


def test_installed_capture_and_cold_companions_keep_exact_metadata_without_git_claims(monkeypatch):
    from empirical_lawhood.infrastructure import selected_candidate
    capture = installed_capture()
    monkeypatch.setattr(owner, 'capture_target_closure', lambda *_args: capture)
    monkeypatch.setattr(selected_candidate, 'installed_candidate',
        lambda **_kwargs: pytest.fail('stored metadata consulted the reader installation'))
    assert owner._capture_prospective_source(Path('/selected/source-data'), capture.closure.source_closure_id) is capture
    observation, payloads, directory = companions(capture)
    owner._load_source_provenance(directory=directory, closure=capture.closure,
        read=lambda name, **_kwargs: payloads[name])
    original_bytes = observation.canonical_bytes()
    assert owner.decode_canonical_bytes(original_bytes, owner.ProspectiveSourceObservation,
        maximum_bytes=len(original_bytes)).canonical_bytes() == original_bytes
    value = json.loads(observation.source_observation_json)
    for key in ('source_admission', 'final_source_admission'):
        assert value[key] == {'policy': 'installed-candidate-v1',
            'source_metadata_sha256': capture.source.source_admission.source_metadata_sha256,
            'selected_paths': [row.relative_path for row in capture.manifest.members],
            'checkout_observed': False, 'observed_checkout_clean': False}
    assert capture.closure.clean_worktree is False


@pytest.mark.parametrize('damage', (
    'unknown-policy', 'mixed-policy', 'raw-status', 'changes', 'local-plan', 'checkout-observed',
    'checkout-integer', 'clean-claim', 'clean-integer', 'metadata-hash', 'final-metadata',
    'reordered-paths', 'duplicate-paths', 'source-identity', 'member-hash', 'symlink-mode', 'missing-lock',
))
def test_installed_observation_refuses_foreign_policy_git_claims_or_build_metadata(damage):
    from empirical_lawhood.infrastructure.selected_candidate import canonical_source_metadata_bytes
    capture = installed_capture()
    observation, _, _ = companions(capture)
    document = json.loads(observation.source_observation_json)
    initial, final = document['source_admission'], document['final_source_admission']
    if damage == 'unknown-policy':
        initial['policy'] = 'installed-candidate-v2'
    elif damage == 'mixed-policy':
        initial.clear()
        initial.update(synthetic_capture('other.source', 'a' * 64).source.source_admission.to_mapping())
    elif damage in ('raw-status', 'changes', 'local-plan'):
        initial[{'raw-status': 'raw_status_sha256', 'changes': 'changes', 'local-plan': 'local_plan'}[damage]] = None
    elif damage in ('checkout-observed', 'checkout-integer', 'clean-claim', 'clean-integer'):
        initial['checkout_observed' if damage.startswith('checkout') else 'observed_checkout_clean'] = (
            0 if damage.endswith('integer') else True)
    elif damage == 'metadata-hash':
        initial['source_metadata_sha256'] = final['source_metadata_sha256'] = 'f' * 64
    elif damage == 'final-metadata':
        final['source_metadata_sha256'] = 'f' * 64
    elif damage in ('reordered-paths', 'duplicate-paths'):
        initial['selected_paths'] = list(reversed(initial['selected_paths'])) if damage == 'reordered-paths' else initial['selected_paths'] * 2
    elif damage == 'source-identity':
        document['implementation_sha256'] = 'f' * 64
    elif damage == 'member-hash':
        document['tracked_files'][0]['sha256'] = 'f' * 64
    else:
        if damage == 'symlink-mode':
            document['tracked_files'][0]['mode'] = '120000'
        else:
            document['tracked_files'] = [row for row in document['tracked_files'] if row['relative_path'] != 'uv.lock']
        digest = sha256(canonical_source_metadata_bytes(implementation_commit=document['implementation_commit'],
            implementation_sha256=document['implementation_sha256'], source_tree_sha256=document['source_tree_sha256'],
            tracked_files=document['tracked_files'])).hexdigest()
        initial['source_metadata_sha256'] = final['source_metadata_sha256'] = digest
    with pytest.raises((ValueError, TypeError)):
        replace(observation, source_observation_json=canonical_json_document_bytes(document).decode())


@pytest.mark.parametrize('damage', ('mixed-type', 'metadata-change', 'false-clean'))
def test_installed_capture_requires_one_unchanged_exact_admission_and_truthful_closure(monkeypatch, damage):
    capture = installed_capture()
    if damage == 'false-clean':
        capture = replace(capture, closure=replace(capture.closure, clean_worktree=True))
    else:
        final = (synthetic_capture('other.source', 'a' * 64).source.source_admission if damage == 'mixed-type'
            else replace(capture.source.final_source_admission, source_metadata_sha256='f' * 64))
        capture = replace(capture, source=replace(capture.source, final_source_admission=final))
    monkeypatch.setattr(owner, 'capture_target_closure', lambda *_args: capture)
    with pytest.raises((ValueError, TypeError, PermissionError)):
        owner._capture_prospective_source(Path('/selected/source-data'), capture.closure.source_closure_id)


def test_retained_exact_closure_does_not_reinterpret_its_original_clean_bit(monkeypatch):
    original = synthetic_capture("source.exposed", "a"*64)
    today = synthetic_capture("source.exposed", "a"*64, clean=False)
    monkeypatch.setattr(owner, "capture_target_closure", lambda *_args: today)
    retained = owner._capture_prospective_source(Path("/source"), "source.exposed", retained_closure=original.closure)
    assert retained.closure == original.closure and retained.closure.clean_worktree is True
    assert retained.source.final_source_admission.observed_checkout_clean is False
    observation, payloads, directory = companions(retained)
    owner._load_source_provenance(directory=directory, closure=original.closure,
        read=lambda name, **_kwargs: payloads[name])
    assert json.loads(observation.source_observation_json)["final_source_admission"]["observed_checkout_clean"] is False


@pytest.mark.parametrize("original_clean", (False, True))
def test_snapshot_only_selection_recovers_only_hash_exact_original_clean_bit(original_clean):
    original = synthetic_capture("source.exposed", "a"*64, clean=original_clean)
    today = synthetic_capture("source.exposed", "a"*64, clean=not original_clean)
    snapshot = ObjectIdentity.from_record("recursive-member.implementation", original.closure)
    selected = experiment._selected_source_closure(today.closure, snapshot)
    assert selected == original.closure
    assert selected.canonical_bytes() == original.closure.canonical_bytes()
    for change in ({"object_id": "different-role"}, {"object_fingerprint": "f"*64},
            {"object_schema": "empirical-lawhood/testing/substituted"}, {"object_version": "2.0.0"}):
        with pytest.raises(ValueError, match="every exact retained"):
            experiment._selected_source_closure(today.closure, replace(snapshot, **change))


def test_capture_refuses_selected_bytes_and_original_manifest_substitution(monkeypatch):
    original = synthetic_capture("source.exposed", "a"*64)
    changed = synthetic_capture("source.exposed", "b"*64)
    monkeypatch.setattr(owner, "capture_target_closure", lambda *_args: changed)
    with pytest.raises(ValueError, match="retained exact selected-source"):
        owner._capture_prospective_source(Path("/source"), "source.exposed", retained_closure=original.closure)
    broken = replace(original, manifest=replace(original.manifest, source_tree_sha256="f"*64))
    monkeypatch.setattr(owner, "capture_target_closure", lambda *_args: broken)
    with pytest.raises(ValueError, match="typed source identity"):
        owner._capture_prospective_source(Path("/source"), "source.exposed")


def test_existing_guarded_writer_receives_separate_operational_companions_only():
    capture = synthetic_capture("source.exposed", "a"*64, clean=False)
    writes = []
    writer = SimpleNamespace(root=SimpleNamespace(contract=SimpleNamespace(canonical_path="/guarded")), write=writes.append)
    owner._publish_source_provenance(captured=capture, destination=Path("/guarded/prospective"), artifact_writer=writer)
    assert len(writes) == 2
    assert tuple(value.relative_path for value in writes) == (
        "prospective/provenance/selected-source-manifest.json", "prospective/provenance/source-observation.json")
    assert all(value.outcome_access is owner.OutcomeAccess.OUTCOME_BLIND for value in writes)
    assert all(value.visibility_ceiling is owner.VisibilityCeiling.PROSPECTIVE for value in writes)


def test_companion_loader_uses_exact_existing_authenticated_read_owner():
    capture = synthetic_capture("source.exposed", "a"*64)
    _, payloads, directory = companions(capture)
    calls = []
    def read(name, *, expected_schema):
        calls.append((name, expected_schema))
        return payloads[name]
    owner._load_source_provenance(directory=directory, closure=capture.closure, read=read)
    assert calls == [("provenance/selected-source-manifest.json", owner.SelectedSourceManifest.SCHEMA),
        ("provenance/source-observation.json", owner.ProspectiveSourceObservation.SCHEMA)]


@pytest.mark.parametrize("change", ("missing", "extra", "symbolic"))
def test_provenance_has_its_own_exact_companion_census(change):
    capture = synthetic_capture("source.exposed", "a"*64)
    _, payloads, directory = companions(capture)
    if change == "missing":
        directory.names.remove("source-observation.json.manifest.json")
    elif change == "extra":
        directory.names.add("additional-scientific-evidence.json")
    else:
        directory.symbolic = True
    with pytest.raises(ValueError, match="separate companion census"):
        owner._load_source_provenance(directory=directory, closure=capture.closure,
            read=lambda name, **_kwargs: payloads[name])


def test_companion_accepts_only_existing_exact_guarded_publication_owner_controls():
    capture = synthetic_capture("source.exposed", "a"*64)
    _, payloads, directory = companions(capture)
    directory.names.add(".publication-batches")
    directory.names.update(".artifact-pair." + sha256((name + "\0" + name + ".manifest.json").encode()).hexdigest()[:24] + ".lock"
        for name in owner.SOURCE_PROVENANCE_MEMBERS)
    owner._load_source_provenance(directory=directory, closure=capture.closure,
        read=lambda name, **_kwargs: payloads[name])
    directory.names.add(".artifact-pair.foreign.lock")
    with pytest.raises(ValueError, match="separate companion census"):
        owner._load_source_provenance(directory=directory, closure=capture.closure,
            read=lambda name, **_kwargs: payloads[name])


@pytest.mark.parametrize("change", ("canonical", "closure", "members", "schema", "version"))
def test_original_provenance_bytes_schema_joins_and_selected_member_census_are_exact(change):
    capture = synthetic_capture("source.exposed", "a"*64)
    observation, payloads, directory = companions(capture)
    if change == "canonical":
        payloads["provenance/source-observation.json"] += b" "
    elif change == "closure":
        payloads["provenance/source-observation.json"] = replace(observation,
            closure=replace(observation.closure, object_fingerprint="f"*64)).canonical_bytes()
    elif change == "members":
        document = json.loads(observation.source_observation_json)
        document["tracked_files"][0]["sha256"] = "f"*64
        payloads["provenance/source-observation.json"] = replace(observation,
            source_observation_json=canonical_json_document_bytes(document).decode()).canonical_bytes()
    else:
        document = json.loads(payloads["provenance/source-observation.json"])
        document[change] = "empirical-lawhood/testing/substitution" if change == "schema" else "2.0.0"
        payloads["provenance/source-observation.json"] = canonical_json_document_bytes(document)
    with pytest.raises(ValueError):
        owner._load_source_provenance(directory=directory, closure=capture.closure,
            read=lambda name, **_kwargs: payloads[name])


def test_original_raw_clean_flag_cannot_be_false_in_operational_disclosure():
    capture = synthetic_capture("source.exposed", "a"*64, clean=False)
    observation, _, _ = companions(capture)
    document = json.loads(observation.source_observation_json)
    document["final_source_admission"]["observed_checkout_clean"] = True
    with pytest.raises(ValueError, match="raw Git cleanliness"):
        replace(observation, source_observation_json=canonical_json_document_bytes(document).decode())


def test_historical_clean_packet_does_not_need_new_companions():
    closure = ImplementationSourceClosure("source.historical", SourceClosureKind.CLEAN_GIT_COMMIT,
        "a"*40, "b"*64, "c"*64, True)
    owner._load_source_provenance(directory=None, closure=closure,
        read=lambda *_args, **_kwargs: pytest.fail("historical packet requested new companions"))
