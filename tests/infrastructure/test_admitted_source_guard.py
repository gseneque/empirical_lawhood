# SPDX-License-Identifier: MPL-2.0
"""Retained source census reuse with fresh original-byte and membership checks."""
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure import source_closure as owner
from tests.infrastructure.test_selected_candidate import candidate_case as candidate_case  # noqa: F401


def test_admitted_installed_guard_reuses_original_identity_without_git_or_capture(candidate_case, monkeypatch):
    case = candidate_case
    admitted = owner.capture_admitted_target_source(case.source)
    monkeypatch.setattr(owner, "_git", lambda *_: pytest.fail("current guard reconstructed a Git source identity"))
    monkeypatch.setattr(owner, "capture_admitted_target_source",
        lambda *_: pytest.fail("current guard recaptured source instead of using its admitted census"))
    checked, original = [], owner._verify_selected_member
    def verify(root, member):
        checked.append(member.relative_path)
        return original(root, member)
    monkeypatch.setattr(owner, "_verify_selected_member", verify)
    assert owner.require_admitted_target_source_current(case.source, admitted) is None
    assert checked == list(admitted.final_source_admission.selected_paths)
    checked.clear()
    assert owner.require_admitted_target_source_current(case.source, admitted) is None
    assert checked == list(admitted.final_source_admission.selected_paths)


@pytest.mark.parametrize("damage", ("source-body", "installed-body", "source-added", "source-missing", "lock"))
def test_admitted_guard_refuses_actual_changed_bytes_or_membership(candidate_case, damage):
    case = candidate_case
    admitted = owner.capture_admitted_target_source(case.source)
    if damage in ("source-body", "installed-body"):
        path = case.source / "src/empirical_lawhood/math.py" if damage == "source-body" else case.package / "math.py"
        raw = path.read_bytes()
        changed = raw.replace(b"7", b"8")
        assert len(changed) == len(raw) and changed != raw
        path.write_bytes(changed)
    elif damage == "source-added":
        (case.source / "src/empirical_lawhood/extra.py").write_bytes(b"EXTRA = 1\n")
    elif damage == "source-missing":
        (case.source / "src/empirical_lawhood/resources/operand.txt").unlink()
    else:
        path = case.source / "uv.lock"
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b"1", b"2"))
    with pytest.raises((PermissionError, ValueError, OSError), match="source|bytes|membership|identity|package member"):
        owner.require_admitted_target_source_current(case.source, admitted)


def test_admitted_guard_refuses_a_different_installed_source_metadata_identity(candidate_case):
    from dataclasses import replace

    case = candidate_case
    admitted = owner.capture_admitted_target_source(case.source)
    foreign = replace(admitted, implementation_commit="d" * 40)
    with pytest.raises(PermissionError, match="identity"):
        owner.require_admitted_target_source_current(Path(case.source), foreign)



def test_admitted_closure_projection_preserves_installed_manifest_without_recapture(candidate_case, monkeypatch):
    case=candidate_case
    expected=owner.capture_target_closure(case.source,"source.installed-current")
    monkeypatch.setattr(owner,"capture_admitted_target_source",lambda *_a,**_kw:pytest.fail("closure recaptured source"))
    observed=owner.capture_target_closure(case.source,"source.installed-current",_admitted_source=expected.source)
    assert observed.closure.canonical_bytes()==expected.closure.canonical_bytes()
    assert observed.manifest.canonical_bytes()==expected.manifest.canonical_bytes()
    assert observed.source.tracked_files is expected.source.tracked_files
    assert (observed.source.implementation_commit, observed.source.implementation_sha256,
        observed.source.source_tree_sha256) == (expected.source.implementation_commit,
            expected.source.implementation_sha256, expected.source.source_tree_sha256)


@pytest.mark.parametrize("damage",("source-body","installed-body","source-added","source-missing","lock"))
def test_closed_installed_source_cannot_project_closure_after_real_mutation(candidate_case,damage):
    case=candidate_case
    source=owner.capture_admitted_target_source(case.source)
    # No live observer/context survives this admission. Reusing its immutable
    # census must still recheck actual source and installed bytes/membership.
    if damage in ("source-body","installed-body"):
        path=(case.source/"src/empirical_lawhood/math.py" if damage=="source-body" else case.package/"math.py")
        raw=path.read_bytes()
        changed=raw.replace(b"7",b"8")
        assert len(changed)==len(raw) and changed!=raw
        path.write_bytes(changed)
    elif damage=="source-added":
        (case.source/"src/empirical_lawhood/extra.py").write_bytes(b"EXTRA = 1\n")
    elif damage=="source-missing":
        (case.source/"src/empirical_lawhood/resources/operand.txt").unlink()
    else:
        path=case.source/"uv.lock"
        path.write_bytes(path.read_bytes().replace(b"1",b"2"))
    with pytest.raises((PermissionError,ValueError,OSError),match="source|bytes|membership|identity|package member"):
        owner.capture_target_closure(case.source,"source.changed",_admitted_source=source)
