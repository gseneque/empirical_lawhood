# SPDX-License-Identifier: MPL-2.0
"""Actual checkout admission and invented-byte Git/module refusal controls."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.infrastructure import source_origin
from empirical_lawhood.infrastructure.study_issue import GitStudySourceClosureInspector
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure, SourceClosureKind


ROOT = Path(__file__).resolve().parents[1]
PROBE = """
import json
from pathlib import Path
import sys
from empirical_lawhood.infrastructure.source_closure import capture_target_closure
from empirical_lawhood.infrastructure.source_origin import require_executing_target_source
from empirical_lawhood.infrastructure.study_issue import GitStudySourceClosureInspector
root = Path(sys.argv[1]); require_executing_target_source(root)
captured = capture_target_closure(root, 'synthetic.actual-source-positive')
assert GitStudySourceClosureInspector(root).observe(captured.closure) == captured.closure
print(json.dumps({'root': str(root), 'commit': captured.closure.implementation_commit,
                  'kind': captured.closure.kind.value}))
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def build_synthetic_source_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """Small invented Git operands; no project modules are copied or imported."""
    repo = tmp_path / "invented-source"
    package = repo / "src/empirical_lawhood"
    package.mkdir(parents=True)
    (package / "__init__.py").write_bytes(b"VALUE = 1\n")
    (package / "member.py").write_bytes(b"SYNTHETIC_MEMBER = True\n")
    _git(repo, "init", "--quiet", "--template=")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Invented Git fixture")
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", "-m", "Invented source operands")
    tree = hashlib.sha256(subprocess.check_output([
        "git", "-C", str(repo), "ls-tree", "-r", "-z", "--full-tree", "HEAD",
    ])).hexdigest()
    return repo, _git(repo, "rev-parse", "HEAD"), tree


@pytest.fixture
def source_repo(tmp_path: Path) -> tuple[Path, str, str]:
    return build_synthetic_source_repo(tmp_path)


@pytest.fixture
def source_modules(source_repo, monkeypatch):
    """Explicit module observations for invented Git roots, never real custody."""
    repo, _, _ = source_repo
    modules = {"empirical_lawhood": SimpleNamespace(
        __file__=str(repo / "src/empirical_lawhood/__init__.py"))}
    monkeypatch.setattr(source_origin, "sys", SimpleNamespace(modules=modules))
    return modules


def _observe(repo, commit, tree):
    expected = ImplementationSourceClosure('test.invented-source-closure', SourceClosureKind.CLEAN_GIT_COMMIT,
        commit, '5' * 64, tree, True)
    return GitStudySourceClosureInspector(repo).observe(expected)


def test_actual_cold_package_and_selected_source_are_the_sole_checkout(tmp_path):
    result = subprocess.run([sys.executable, '-c', PROBE, str(ROOT)], cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1'),
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {'root': str(ROOT), 'commit': _git(ROOT, 'rev-parse', 'HEAD'),
        'kind': SourceClosureKind.EXACT_SOURCE_CLOSURE.value}


def test_invented_source_and_same_commit_worktree_are_accepted(source_repo, source_modules, tmp_path):
    repo, commit, tree = source_repo
    assert _observe(repo, commit, tree).implementation_commit == commit
    worktree = tmp_path / 'invented-worktree'
    _git(repo, 'worktree', 'add', '--quiet', '--detach', str(worktree), commit)
    source_modules['empirical_lawhood'].__file__ = str(worktree / 'src/empirical_lawhood/__init__.py')
    assert _observe(worktree, commit, tree).implementation_commit == commit


@pytest.mark.parametrize('mismatch', ('tracked-dirty', 'untracked', 'head', 'tree'))
def test_joint_boundary_reobserves_each_source_identity(source_repo, source_modules, mismatch):
    repo, commit, tree = source_repo
    expected = 'dirty'
    if mismatch == 'tracked-dirty':
        (repo / 'src/empirical_lawhood/__init__.py').write_bytes(b'VALUE = 2\n')
    elif mismatch == 'untracked':
        (repo / 'untracked.txt').write_text('invented untracked member\n')
    elif mismatch == 'head':
        _git(repo, 'commit', '--quiet', '--allow-empty', '-m', 'Changed invented source identity')
        expected = 'commit changed'
    else:
        tree = 'f' * 64
        expected = 'source tree changed'
    with pytest.raises(PermissionError, match=expected):
        _observe(repo, commit, tree)


@pytest.mark.parametrize('origin', ('wheel-layout', 'other-checkout', 'mixed', 'untracked-module'))
def test_inspected_git_cannot_launder_a_different_executing_package(source_repo, source_modules, tmp_path, origin):
    repo, commit, tree = source_repo
    if origin == 'wheel-layout':
        source_modules['empirical_lawhood'].__file__ = str(tmp_path / 'site-packages/empirical_lawhood/__init__.py')
    elif origin == 'other-checkout':
        worktree = tmp_path / 'other-invented-worktree'
        _git(repo, 'worktree', 'add', '--quiet', '--detach', str(worktree), commit)
        source_modules['empirical_lawhood'].__file__ = str(worktree / 'src/empirical_lawhood/__init__.py')
    else:
        extra = (repo / 'src/empirical_lawhood' if origin == 'untracked-module' else tmp_path) / 'origin_probe.py'
        source_modules['empirical_lawhood.origin_probe'] = SimpleNamespace(__file__=str(extra))
    with pytest.raises(PermissionError, match='not the inspected target source tree|outside the inspected target source tree|not tracked'):
        _observe(repo, commit, tree)
