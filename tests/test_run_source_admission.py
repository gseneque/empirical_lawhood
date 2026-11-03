# SPDX-License-Identifier: MPL-2.0
"""Operational entry controls with bounded synthetic Git and no native work."""

from dataclasses import replace
from hashlib import sha256
import json
import subprocess
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure import run_source_admission as owner
from empirical_lawhood.infrastructure import source_closure
from empirical_lawhood.infrastructure.run_source_admission import RunSourceAdmissionError
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.infrastructure.test_selected_candidate import candidate_case as candidate_case  # noqa: F401


def _git(root, *arguments):
    return subprocess.check_output(("git", *arguments), cwd=root, stderr=subprocess.PIPE).decode().strip()


def _identity(name):
    return ObjectIdentity(name, "empirical-lawhood/testing/source-entry", "1.0.0", "d" * 64)


@pytest.fixture
def entry(tmp_path, monkeypatch):
    project = tmp_path / "synthetic-source"
    project.mkdir()
    _git(project, "init", "--template=")
    members = {
        "src/empirical_lawhood/__init__.py": b"VALUE = 42\n",
        "scripts/run.py": b"VALUE = 42\n",
        "tests/test_selection.py": b"VALUE = 42\n",
        "uv.lock": b"version = 1\n",
        "pyproject.toml": b"[project]\nname = 'source-fixture'\n",
        "README.md": b"Original documentation\n",
    }
    for name, payload in members.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    _git(project, "add", "--", ".")
    _git(project, "-c", "user.name=Software fixture", "-c", "user.email=fixture@example.invalid",
         "commit", "-m", "bounded source fixture")
    custody = tmp_path / "custody"
    custody.mkdir()
    floors = []

    def verify(*, for_write, operation_minimum_free_bytes=0):
        assert for_write
        floors.append(operation_minimum_free_bytes)
        return custody

    guard = SimpleNamespace(verify=verify, contract=SimpleNamespace(storage_root_id="software.source-custody"))
    # The project origin guard has its own real-checkout refusal controls. This
    # bounded fixture isolates only that guard; physical source/blob admission,
    # selected source admission and durable metadata custody remain real.
    monkeypatch.setattr(source_closure, "require_executing_target_source", lambda root: None)
    environment = {"interpreter": "/locked/python", "selected_environment": [["OMP_NUM_THREADS", "1"]]}
    monkeypatch.setattr(owner, "observe_worker_environment", lambda: SimpleNamespace(to_document=lambda: environment))
    monkeypatch.setattr(owner, "numerical_runtime_observation", lambda: {"numpy": "fixture", "threadpools": []})
    return SimpleNamespace(project=project, custody=custody, writer=SimpleNamespace(root=guard),
        commit=_git(project, "rev-parse", "HEAD"), floors=floors, environment=environment)


def _enter(entry, **changes):
    options = {"project_root": entry.project, "artifact_writer": entry.writer,
        "run_id": "run.source-fixture", "expected_commit": entry.commit,
        "invocation": ("software.experiment", "run.source-fixture"),
        "source_bindings": (_identity("original.protocol"), _identity("actual.authority"))}
    return owner.ensure_run_source_entry(**{**options, **changes})


def test_entries_share_exact_candidate_metadata_without_archives_or_reconstruction(entry):
    (entry.project / "WTF.md").write_text("Local operational plan\n")
    (entry.project / "README.md").write_text("Unrelated documentary edit\n")
    first = _enter(entry)
    second = _enter(entry)
    other = _enter(entry, run_id="run.another")
    assert first == second
    assert first.candidate_metadata_path == other.candidate_metadata_path
    assert len(list((entry.custody / "operational/source-candidates").iterdir())) == 1
    assert not list(entry.custody.rglob("*.bundle"))
    assert not list(entry.custody.rglob("*.tar"))
    assert not (entry.custody / "operational/run-source-validation").exists()
    candidate_raw = first.candidate_metadata_path.read_bytes()
    candidate = json.loads(candidate_raw)
    assert sha256(candidate_raw).hexdigest() == first.candidate_metadata_sha256
    assert candidate["implementation_commit"] == entry.commit
    assert {row["relative_path"] for row in candidate["tracked_files"]} >= {
        "src/empirical_lawhood/__init__.py", "tests/test_selection.py", "uv.lock"}
    payload = first.receipt_path.read_bytes()
    assert sha256(payload).hexdigest() == first.receipt_sha256
    record = json.loads(payload)
    assert record["candidate"] == {"relative_path": first.candidate_metadata_path.relative_to(entry.custody).as_posix(),
        "sha256": first.candidate_metadata_sha256, "size_bytes": len(candidate_raw),
        "implementation_commit": entry.commit, "implementation_sha256": candidate["implementation_sha256"],
        "source_tree_sha256": candidate["source_tree_sha256"]}
    assert "tracked_files" not in record and "bundle" not in record
    assert record["parent_environment"] == entry.environment
    assert record["dependency_lock_sha256"] == sha256((entry.project / "uv.lock").read_bytes()).hexdigest()
    assert record["source_before"]["observed_checkout_clean"] is False
    assert set(record["source_after"]) == {"policy", "observed_checkout_clean", "observation_sha256"}
    assert {row["value"]["object_id"] for row in record["source_bindings"]} == {"original.protocol", "actual.authority"}
    assert record["scientific_authority"] == "NONE"
    assert 0 < len(payload) < owner._MAX_ENTRY_BYTES and entry.floors[0] > len(candidate_raw)


@pytest.mark.parametrize("path", ("src/empirical_lawhood/__init__.py", "scripts/run.py", "uv.lock", "tests/test_selection.py"))
def test_selected_executable_lock_or_test_drift_refuses_before_packet_creation(entry, path):
    (entry.project / path).write_bytes(b"changed selected operand\n")
    with pytest.raises(PermissionError):
        _enter(entry)
    assert not list(entry.custody.iterdir())


def test_actual_commit_must_match_selected_entry(entry):
    with pytest.raises(RunSourceAdmissionError, match="another actual implementation"):
        _enter(entry, expected_commit="a" * 40)
    assert not list(entry.custody.iterdir())


@pytest.mark.parametrize("damage", ("bad-json", "wrong-census", "symlink"))
def test_retry_refuses_changed_shared_candidate_metadata(entry, damage, tmp_path):
    admitted = _enter(entry)
    path = admitted.candidate_metadata_path
    if damage == "bad-json":
        path.write_bytes(b"{}")
    elif damage == "wrong-census":
        value = json.loads(path.read_bytes())
        value["tracked_files"] = []
        path.write_bytes(owner._json_bytes(value))
    else:
        target = tmp_path / "borrowed-candidate.json"
        path.rename(target)
        path.symlink_to(target)
    with pytest.raises((RunSourceAdmissionError, OSError, ValueError)):
        _enter(entry)


def test_retry_refuses_changed_retained_entry(entry):
    admitted = _enter(entry)
    admitted.receipt_path.write_bytes(b"changed durable entry\n")
    with pytest.raises(RunSourceAdmissionError, match="exact bytes"):
        _enter(entry)


def test_interrupted_candidate_write_never_records_entry(entry, monkeypatch):
    original = owner._write_once

    def fail(path, payload, **kwargs):
        if path.parent.name == "source-candidates":
            path.write_bytes(payload[:12])
            raise OSError("interrupted metadata write")
        return original(path, payload, **kwargs)

    monkeypatch.setattr(owner, "_write_once", fail)
    with pytest.raises(OSError, match="interrupted"):
        _enter(entry)
    assert not (entry.custody / "operational/run-source-entries").exists()
    monkeypatch.setattr(owner, "_write_once", original)
    with pytest.raises(RunSourceAdmissionError, match="exact bytes"):
        _enter(entry)


def test_installed_entry_references_typed_candidate_without_git_or_clean_checkout_claim(candidate_case, tmp_path, monkeypatch):
    case = candidate_case
    custody = tmp_path / "installed-custody"
    custody.mkdir()
    guard = SimpleNamespace(verify=lambda **_kwargs: custody,
        contract=SimpleNamespace(storage_root_id="software.installed-source-custody"))
    environment = {"interpreter": "/locked/python"}
    monkeypatch.setattr(owner, "observe_worker_environment", lambda: SimpleNamespace(to_document=lambda: environment))
    monkeypatch.setattr(owner, "numerical_runtime_observation", lambda: {"software-fixture": True})
    captures, capture = [], owner.capture_admitted_target_source
    def observe(root, **kwargs):
        captures.append(root)
        return capture(root, **kwargs)
    monkeypatch.setattr(owner, "capture_admitted_target_source", observe)
    monkeypatch.setattr(source_closure, "_git", lambda *args, **kwargs: pytest.fail("installed entry used Git"))
    admitted = owner.ensure_run_source_entry(project_root=case.source, artifact_writer=SimpleNamespace(root=guard),
        run_id="run.installed-source-fixture", expected_commit="a" * 40,
        invocation=("software.installed-entry",))
    assert captures == [case.source]
    record = json.loads(admitted.receipt_path.read_bytes())
    assert record["source_before"]["policy"] == "installed-candidate-v1"
    assert record["source_before"]["observed_checkout_clean"] is False
    assert record["source_after"]["observed_checkout_clean"] is False
    assert record["dependency_lock_sha256"] == sha256((case.source / "uv.lock").read_bytes()).hexdigest()


def test_capacity_refusal_has_no_source_packet_or_worker_fallback(entry):
    def refuse(**kwargs):
        raise PermissionError("insufficient selected capacity")

    entry.writer.root.verify = refuse
    with pytest.raises(PermissionError, match="capacity"):
        _enter(entry)
    assert not list(entry.custody.iterdir())


def test_symlinked_operational_directory_refuses(entry, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (entry.custody / "operational").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(RunSourceAdmissionError, match="real canonical"):
        _enter(entry)
    assert not list(elsewhere.iterdir())


@pytest.mark.parametrize("changes", ({"run_id": "../escape"}, {"expected_commit": "HEAD"},
    {"invocation": ()}, {"source_bindings": ("authority-label",)},
    {"source_bindings": (_identity("duplicate"), _identity("duplicate"))}))
def test_untyped_or_ambiguous_entry_selection_refuses_before_source_or_writes(entry, changes, monkeypatch):
    monkeypatch.setattr(owner, "capture_admitted_target_source", lambda *args, **kwargs: pytest.fail("source inspected"))
    with pytest.raises(ValueError, match="exact run"):
        _enter(entry, **changes)
    assert not list(entry.custody.iterdir())


def test_pytest_entry_captures_once_and_authenticates_expanded_test_scope(entry, monkeypatch):
    archives, checked = [], []
    git, verify = source_closure._git, source_closure._verify_selected_member
    def observe_git(root, *arguments):
        if arguments[0] == "archive":
            archives.append(arguments)
        return git(root, *arguments)
    def observe_member(root, member):
        checked.append(member.relative_path)
        return verify(root, member)
    monkeypatch.setattr(source_closure, "_git", observe_git)
    monkeypatch.setattr(source_closure, "_verify_selected_member", observe_member)
    source = owner._capture_source(entry.project)
    assert len(archives) == 1
    assert "tests/test_selection.py" in source.source_admission.selected_paths
    assert source.source_admission.selected_paths == source.final_source_admission.selected_paths
    assert "tests/test_selection.py" in checked
    _enter(entry, _admitted_source=source)
    assert len(archives) == 1
    assert checked.count("tests/test_selection.py") == 2


@pytest.mark.parametrize("path", ("tests/test_selection.py", "README.md"))
def test_reused_entry_checks_new_test_bytes_and_preserves_original_extra_scope(entry, monkeypatch, path):
    source = source_closure.capture_admitted_target_source(entry.project, selected_paths=("README.md",))
    assert "README.md" in source.final_source_admission.selected_paths
    assert "tests/test_selection.py" not in source.final_source_admission.selected_paths
    (entry.project / path).write_bytes(b"changed actual selected bytes\n")
    monkeypatch.setattr(owner, "capture_admitted_target_source", lambda *_a, **_kw: pytest.fail("reused source recaptured"))
    with pytest.raises(PermissionError, match="selected source file type, mode or size"):
        _enter(entry, _admitted_source=source)
    assert not list(entry.custody.iterdir())


def test_reused_entry_retains_fresh_status_and_runtime_without_archive(entry, monkeypatch):
    source = owner._capture_source(entry.project)
    assert source.final_source_admission.observed_checkout_clean is True
    (entry.project / "README.md").write_bytes(b"new unselected documentary status\n")
    monkeypatch.setattr(owner, "capture_admitted_target_source", lambda *_a, **_kw: pytest.fail("reused source recaptured"))
    runtime = []
    monkeypatch.setattr(owner, "numerical_runtime_observation", lambda: runtime.append("fresh") or {"observed": len(runtime)})
    first = _enter(entry, _admitted_source=source)
    first_record = json.loads(first.receipt_path.read_bytes())
    assert first_record["source_before"]["observed_checkout_clean"] is False
    assert first_record["source_after"]["observed_checkout_clean"] is False
    assert first_record["source_before"] != owner._admission_summary(source.source_admission)
    (entry.project / "README.md").write_bytes(b"Original documentation\n")
    second = _enter(entry, _admitted_source=source)
    second_record = json.loads(second.receipt_path.read_bytes())
    assert second_record["source_before"]["observed_checkout_clean"] is True
    assert second_record["source_after"]["observed_checkout_clean"] is True
    assert runtime == ["fresh", "fresh"]
    assert first.candidate_metadata_path == second.candidate_metadata_path
    assert first.receipt_path != second.receipt_path


@pytest.mark.parametrize("damage", ("missing-package", "missing-lock", "changed-scope", "untracked-test"))
def test_reused_entry_cannot_shrink_or_invent_admitted_scope(entry, monkeypatch, damage):
    source = source_closure.capture_admitted_target_source(entry.project)
    scope = source.final_source_admission.selected_paths
    if damage == "changed-scope":
        source = replace(source, source_admission=replace(source.source_admission,
            selected_paths=tuple(sorted((*scope, "README.md")))))
    else:
        removed = {"missing-package": "src/empirical_lawhood/__init__.py", "missing-lock": "uv.lock"}.get(damage)
        selected = (tuple(name for name in scope if name != removed) if removed is not None else
            tuple(sorted((*scope, "tests/not-committed.py"))))
        source = replace(source, source_admission=replace(source.source_admission, selected_paths=selected),
            final_source_admission=replace(source.final_source_admission, selected_paths=selected))
    monkeypatch.setattr(owner, "capture_admitted_target_source", lambda *_a, **_kw: pytest.fail("reused source recaptured"))
    with pytest.raises(PermissionError, match="scope"):
        _enter(entry, _admitted_source=source)
    assert not list(entry.custody.iterdir())


def test_new_closure_uses_current_raw_status_without_recapturing_identity(entry, monkeypatch):
    source = source_closure.capture_admitted_target_source(entry.project)
    assert source.final_source_admission.observed_checkout_clean is True
    monkeypatch.setattr(source_closure, "capture_admitted_target_source",
        lambda *_a, **_kw: pytest.fail("closure reconstructed an admitted source archive"))
    (entry.project / "README.md").write_bytes(b"new unselected documentary bytes\n")
    dirty = source_closure.capture_target_closure(entry.project, "source.new-current-disclosure", _admitted_source=source)
    assert dirty.source.tracked_files is source.tracked_files
    assert dirty.source.final_source_admission.observed_checkout_clean is False
    assert dirty.closure.clean_worktree is False
    (entry.project / "README.md").write_bytes(b"Original documentation\n")
    clean = source_closure.capture_target_closure(entry.project, "source.new-current-disclosure", _admitted_source=source)
    assert clean.source.tracked_files is source.tracked_files
    assert clean.source.final_source_admission.observed_checkout_clean is True
    assert clean.closure.clean_worktree is True
    assert clean.manifest == dirty.manifest
    assert clean.closure.implementation_sha256 == dirty.closure.implementation_sha256
    assert source.final_source_admission.observed_checkout_clean is True
