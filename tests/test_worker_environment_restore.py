# SPDX-License-Identifier: MPL-2.0
"""Separate-prefix restoration mechanics; fixtures are never engine qualification."""

from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

from empirical_lawhood.storage.transfer_files import seal_transfer
from empirical_lawhood.execution.local.worker_environment_restore import restore_worker_environment


def prepare(tmp_path, *, damaged_archive=False):
    base = tmp_path/'base'
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(base)], check=True, capture_output=True)
    (base/'library.so').write_bytes(b'EXPOSED ORIGINAL NONEXECUTABLE LIBRARY')
    payload = tmp_path/'payload'
    payload.mkdir()
    (payload/'replacement.so').write_bytes(b'EXPOSED REPLACEMENT NONEXECUTABLE LIBRARY')
    (payload/'empirical_lawhood-0.3.0-py3-none-any.whl').write_bytes(b'EXPOSED NONEXECUTABLE WHEEL')
    archive = payload/'source.tar.gz'
    with tarfile.open(archive, 'w:gz') as packed:
        info = tarfile.TarInfo('../escape' if damaged_archive else 'source/example.py')
        info.size = len(b'EXPOSED SOURCE\n  ')
        packed.addfile(info, io.BytesIO(b'EXPOSED SOURCE\n  '))
    def pin(name):
        return dict(source=name, sha256=sha256((payload/name).read_bytes()).hexdigest())
    selected = {'version': '1.0.0', 'base_environment': str(base), 'destination': str(tmp_path/'restored'),
        'installer': sys.executable, 'maximum_bytes': 2**20, 'maximum_entries': 1000, 'free_reserve_bytes': 1000,
        'replacements': [{**pin('replacement.so'), 'destination': 'library.so',
            'original_sha256': sha256((base/'library.so').read_bytes()).hexdigest()}],
        'source_distributions': [{**pin('source.tar.gz'), 'destination': str(tmp_path/'source'),
            'maximum_bytes': 1000, 'maximum_entries': 10}],
        'engine_wheel': pin('empirical_lawhood-0.3.0-py3-none-any.whl')}
    (payload/'restore.json').write_text(json.dumps(selected))
    return base, payload, selected


def invoke(tmp_path, payload, run):
    manifest = tmp_path/'manifest.json'
    sealed = seal_transfer(payload, manifest, maximum_bytes=2**20, maximum_files=20)
    return restore_worker_environment(payload/'restore.json', payload_root=payload, manifest_path=manifest,
        expected_sha256=sealed['sha256'], output_directory=tmp_path/'readout', run=run)


def test_distinct_prefix_exact_original_preservation_and_offline_installer_commands(tmp_path):
    base, payload, selected = prepare(tmp_path)
    original = (base/'library.so').read_bytes()
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        if command[1:3] == ['-B', '-c']:
            return subprocess.run(command, **kwargs)
        return subprocess.CompletedProcess(command, 0)
    result = invoke(tmp_path, payload, run)
    assert result['native_calls'] == 0 and result['original_environment_unchanged']
    assert (base/'library.so').read_bytes() == original
    assert (tmp_path/'restored/library.so').read_bytes() == (payload/'replacement.so').read_bytes()
    assert (tmp_path/'source/source/example.py').read_bytes() == b'EXPOSED SOURCE\n  '
    assert '--offline' in calls[1] and '--no-deps' in calls[1] and '--reinstall-package' in calls[1]
    assert str(base/'bin/python') not in calls[1]
    assert Path(selected['destination']) != base


@pytest.mark.parametrize('damage', ['original', 'replacement', 'repeated', 'overlap', 'archive', 'external-link'])
def test_bad_restore_refuses_before_environment_mutation(tmp_path, damage):
    base, payload, selected = prepare(tmp_path, damaged_archive=damage == 'archive')
    if damage == 'original': (base/'library.so').write_bytes(b'CHANGED ORIGINAL')
    if damage == 'replacement': (payload/'replacement.so').write_bytes(b'CHANGED REPLACEMENT')
    if damage == 'repeated': selected['replacements'] *= 2
    if damage == 'overlap': selected['source_distributions'][0]['destination'] = selected['destination']
    if damage == 'external-link': (base/'external-packages').symlink_to(payload, target_is_directory=True)
    (payload/'restore.json').write_text(json.dumps(selected))
    def forbidden(*args, **kwargs):
        pytest.fail('refused restoration called an installer')
    with pytest.raises(ValueError):
        invoke(tmp_path, payload, forbidden)
    assert not (tmp_path/'restored').exists()
    assert not (tmp_path/'readout').exists()


def test_original_mutation_during_installation_refuses_completion_and_keeps_attempt(tmp_path):
    base, payload, _ = prepare(tmp_path)
    def mutate(command, **kwargs):
        (base/'library.so').write_bytes(b'CONCURRENT ORIGINAL CHANGE')
        return subprocess.CompletedProcess(command, 0)
    with pytest.raises(ValueError, match='original worker environment changed'):
        invoke(tmp_path, payload, mutate)
    assert (tmp_path/'readout/command-1.log').exists()
    assert not (tmp_path/'readout/readout.json').exists()
