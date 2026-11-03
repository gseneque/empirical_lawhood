# SPDX-License-Identifier: MPL-2.0
"""Finite path checks retain live volume and directory custody without science."""
from collections import Counter
from pathlib import Path
import sys

import pytest

from empirical_lawhood.infrastructure.artifacts import ExternalRootUnavailable, GuardedExternalRoot
from tests.runtime_platform.test_artifact_verification_scope import _publication


def test_finite_census_shares_root_checks_and_preserves_all_selected_paths(tmp_path):
    plane, manifests = _publication(tmp_path, 8)
    selected = tuple(row.materialization.relative_path for row in manifests) + ('absent/run/receipt.json',)
    checks = Counter()
    code = GuardedExternalRoot._verify.__code__

    def observe(frame, event, argument):
        if event == 'call' and frame.f_code is code:
            checks['root'] += 1

    prior = sys.getprofile()
    sys.setprofile(observe)
    try:
        with plane.root.read_paths(selected) as paths:
            assert tuple(paths) == selected
            assert all(path == Path(plane.root.contract.canonical_path) / relative
                for relative, path in paths.items())
            assert all(paths[row.materialization.relative_path].read_bytes() for row in manifests)
            assert not paths[selected[-1]].exists()
    finally:
        sys.setprofile(prior)
    assert checks == {'root': 2}


@pytest.mark.parametrize('damage', ('parent-link', 'parent-replacement', 'dangling-leaf', 'absent-parent'))
@pytest.mark.parametrize('consumer_refuses', (False, True))
def test_finite_census_refuses_changed_ancestors_and_symlinks_on_return(tmp_path, damage, consumer_refuses):
    plane, manifests = _publication(tmp_path, 1)
    root = Path(plane.root.contract.canonical_path)
    relative = manifests[0].materialization.relative_path
    with pytest.raises(ExternalRootUnavailable):
        with plane.root.read_paths((relative, 'absent/receipt.json')):
            if damage.startswith('parent'):
                (root / 'outputs').rename(root / 'held')
                if damage == 'parent-link':
                    (root / 'outputs').symlink_to('held', target_is_directory=True)
                else:
                    (root / 'outputs').mkdir()
            elif damage == 'dangling-leaf':
                path = root / relative
                path.unlink()
                path.symlink_to('never-present')
            else:
                (root / 'absent').mkdir()
            if consumer_refuses:
                raise ValueError('original consumer refusal')


def test_custom_resolver_keeps_each_selected_boundary(tmp_path, monkeypatch):
    plane, manifests = _publication(tmp_path, 2)
    selected = tuple(row.materialization.relative_path for row in manifests)
    original = plane.root.resolve
    calls = []

    def resolve(relative, **kwargs):
        calls.append(relative)
        return original(relative, **kwargs)

    monkeypatch.setattr(plane.root, 'resolve', resolve)
    with plane.root.read_paths(selected) as paths:
        assert tuple(paths) == selected
    assert calls == [*selected, *selected]


@pytest.mark.parametrize('position', ('parent', 'leaf'))
def test_single_path_refuses_dangling_links_before_access(tmp_path, position):
    plane, _ = _publication(tmp_path, 1)
    root = Path(plane.root.contract.canonical_path)
    (root / 'dangling').symlink_to('never-present', target_is_directory=position == 'parent')
    with pytest.raises(ExternalRootUnavailable, match='symlink'):
        plane.root.resolve('dangling/file' if position == 'parent' else 'dangling', for_write=False)
