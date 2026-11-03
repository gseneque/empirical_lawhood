# SPDX-License-Identifier: MPL-2.0
"""Sole-checkout reactor lifecycle; synthetic roles cannot qualify science."""
from contextlib import nullcontext
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import pytest
from empirical_lawhood.infrastructure.source_closure import capture_admitted_target_source

ROOT = Path(__file__).resolve().parents[1]


def _source_identity():
    source = capture_admitted_target_source(ROOT)
    return (source.implementation_commit, source.implementation_sha256, source.source_tree_sha256, source.tracked_files)


@pytest.mark.parametrize('mode', ('lifecycle', 'scale', 'exposed'))
def test_public_reactor_issue_execute_reveal_and_recover(tmp_path, mode):
    original_source = _source_identity()
    mount = Path(os.environ.get('EL_TEST_EXTERNAL_MOUNT', '/dev/shm')).resolve(strict=True)
    if not mount.is_mount() or mount == Path('/'):
        raise ValueError('reactor lifecycle requires an actual selected external mount')
    if tmp_path.is_relative_to(mount):
        storage = tmp_path/'reactor-operator'
        storage.mkdir()
        selected = nullcontext(str(storage))
    else:
        if 'EL_TEST_EXTERNAL_MOUNT' in os.environ:
            raise ValueError('select pytest basetemp beneath EL_TEST_EXTERNAL_MOUNT')
        selected = TemporaryDirectory(prefix='empirical-lawhood-reactor-', dir=mount)
    with selected as value:
        storage = Path(value)
        temporary, cache = storage/'scratch/temporary', storage/'scratch/cache'
        temporary.mkdir(parents=True)
        cache.mkdir()
        environment = dict(os.environ, PYTHONPATH=os.pathsep.join((str(ROOT/'src'), str(ROOT))),
            PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(temporary), TMP=str(temporary), TEMP=str(temporary),
            XDG_CACHE_HOME=str(cache), NUMBA_CACHE_DIR=str(cache/'numba'), MPLCONFIGDIR=str(cache/'matplotlib'))
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('reactor_lifecycle_scenario.py')),
            str(ROOT), str(storage/'private-test-trust'), mode, str(storage), str(mount), 'operational/reactor.sqlite3'],
            cwd=storage, env=environment, capture_output=True, text=True, timeout=600)
        assert result.returncode == 0, result.stdout+result.stderr
        expected = {'lifecycle': '21 receipted tasks; same-identity recovery verified',
            'scale': 'realistic census and production member bounds verified',
            'exposed': 'exposed assignment refused base and extension study issue despite contradictory attestations'}[mode]
        assert expected in result.stdout
    assert _source_identity() == original_source
