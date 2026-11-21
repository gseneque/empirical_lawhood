# SPDX-License-Identifier: MPL-2.0
"""Restore a distinct worker environment from exact retained installation inputs.

This factors the separate-environment pattern used for the Reference PME repair.
It changes no original environment and performs no numerical or scientific task.
"""

from hashlib import sha256
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile

from empirical_lawhood.storage.transfer_files import normalized_absolute_path as _absolute, encode_document as _encode, ordinary_root as _ordinary_root, portable_relative_path as _relative, verify_transfer
from empirical_lawhood.storage.artifact_replication import _durable_bytes
from empirical_lawhood.storage.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.storage.deployment_archive import _tree_census
from empirical_lawhood.science.records.serialization import validate_sha256


def _positive(value):
    if type(value) is not int or value <= 0:
        raise ValueError('environment restoration requires explicit positive capacity bounds')
    return value


def _fresh(path):
    path = Path(_absolute(path))
    if path.resolve(strict=False) != path or path.exists() or not path.parent.is_dir():
        raise ValueError('environment restoration requires fresh ordinary absolute destinations')
    return path


def _source_archive_members(path, selection):
    total, names, members = 0, set(), []
    with tarfile.open(path, mode='r:*') as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or '..' in name.parts or str(name) != member.name or member.name in names
                    or not (member.isdir() or member.isfile()) or 'plans' in name.parts and 'docs' in name.parts):
                raise ValueError('source archive contains a redirected, repeated, special or work-plan member')
            names.add(member.name)
            total += member.size
            if total > selection['maximum_bytes'] or len(names) > selection['maximum_entries']:
                raise ValueError('source archive exceeds its selected expansion allowance')
            members.append(member)
    if not members:
        raise ValueError('source archive is empty')
    return total, members


def restore_worker_environment(selection_path, *, payload_root, manifest_path, expected_sha256, output_directory,
                               run=subprocess.run):
    """Copy to a fresh prefix, apply exact file replacements and install offline.

The enclosing complete payload seal authenticates this editable recipe and all
inputs. Domain source and actual engine admission remain separate prerequisites.
"""
    payload = _ordinary_root(payload_root)
    selected_path = Path(selection_path)
    if (selected_path.resolve(strict=True) != selected_path or not selected_path.is_relative_to(payload)):
        raise ValueError('restoration selection must be an ordinary member of its sealed payload')
    verify_transfer(payload, manifest_path, expected_sha256=expected_sha256)
    raw = read_bounded_bytes(selected_path, maximum_bytes=2**20)
    selected = json.loads(raw)
    if (type(selected) is not dict or set(selected) != {'version', 'base_environment', 'destination', 'installer',
            'maximum_bytes', 'maximum_entries', 'free_reserve_bytes', 'replacements', 'source_distributions', 'engine_wheel'}
            or selected['version'] != '1.0.0'):
        raise ValueError('unsupported worker environment restoration recipe')
    base = _ordinary_root(selected['base_environment'])
    destination = _fresh(selected['destination'])
    output = _fresh(str(output_directory))
    installer = Path(_absolute(selected['installer']))
    if not installer.is_file():
        raise ValueError('selected upstream offline installer is absent')
    for key in ('maximum_bytes', 'maximum_entries', 'free_reserve_bytes'):
        _positive(selected[key])
    before = _tree_census(base, maximum_bytes=selected['maximum_bytes'], maximum_entries=selected['maximum_entries'])
    if not (base/'pyvenv.cfg').is_file() or not (base/'bin/python').exists():
        raise ValueError('base is not the selected Python worker environment')
    before_by_name = {row['path']: row for row in before}
    for row in before:
        if row['kind'] != 'symlink' or re.fullmatch(r'bin/python[0-9.]*', row['path']):
            continue
        # Internal relative links remain internal in the copied prefix. Other
        # external links could make the installer write into original storage.
        target = Path(row['target'])
        if target.is_absolute() or not (base/row['path']).resolve(strict=False).is_relative_to(base):
            raise ValueError('worker contains an external non-interpreter symlink')

    def input_file(row):
        if type(row) is not dict or not {'source', 'sha256'}.issubset(row):
            raise ValueError('restoration requires exact original input bindings')
        path = payload/_relative(row['source'])
        validate_sha256(row['sha256'], field_name='retained installation input')
        if path.resolve(strict=True) != path or not path.is_file():
            raise ValueError('restoration input is not an ordinary payload member')
        if bounded_file_sha256(path, maximum_bytes=selected['maximum_bytes'])[1] != row['sha256']:
            raise ValueError('restoration input changes its original digest')
        return path

    wheel = selected['engine_wheel']
    if set(wheel) != {'source', 'sha256'} or not Path(wheel['source']).name.startswith('empirical_lawhood-') or not wheel['source'].endswith('.whl'):
        raise ValueError('select the exact accepted engine wheel')
    wheel_path = input_file(wheel)
    replacement_destinations = set()
    for row in selected['replacements']:
        if set(row) != {'source', 'sha256', 'destination', 'original_sha256'}:
            raise ValueError('replacement requires original and replacement file bindings')
        input_file(row)
        name = _relative(row['destination'])
        if name in replacement_destinations:
            raise ValueError('restoration repeats a replacement destination')
        replacement_destinations.add(name)
        original = before_by_name.get(name)
        if original is None or original['kind'] != 'regular' or original['sha256'] != row['original_sha256']:
            raise ValueError('replacement does not bind the actual original worker file')
    sources = []
    for row in selected['source_distributions']:
        if set(row) != {'source', 'sha256', 'destination', 'maximum_bytes', 'maximum_entries'}:
            raise ValueError('source restoration requires explicit archive and expansion bounds')
        for key in ('maximum_bytes', 'maximum_entries'):
            _positive(row[key])
        path, target = input_file(row), _fresh(row['destination'])
        size, _ = _source_archive_members(path, row)
        sources.append((row, path, target, size))
    targets = [destination, output, *[target for _, _, target, _ in sources]]
    for i, target in enumerate(targets):
        if any(target.is_relative_to(existing) or existing.is_relative_to(target)
                for existing in (base, payload, *targets[:i])):
            raise ValueError('restoration destinations must be disjoint from original inputs and each other')
    clone_bytes = sum(row.get('bytes', 0) for row in before)
    requirements = [(destination.parent, clone_bytes), *[(target.parent, size) for _, _, target, size in sources]]
    totals = {}
    for parent, amount in requirements:
        device = parent.stat().st_dev
        previous = totals.get(device, (parent, 0))
        totals[device] = parent, previous[1]+amount
    for parent, amount in totals.values():
        if shutil.disk_usage(parent).free < amount+selected['free_reserve_bytes']:
            raise ValueError('restoration does not fit the selected filesystem reserve')

    output.mkdir()
    _durable_bytes(output/'selection.json', raw)
    _durable_bytes(output/'original-environment-census.json', _encode({'root': str(base), 'entries': before}))
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', UV_PYTHON_DOWNLOADS='never')
    # A source import override must not hide which installed prefix is restored.
    environment.pop('PYTHONPATH', None)
    try:
        shutil.copytree(base, destination, symlinks=True)
        copied = _tree_census(destination, maximum_bytes=selected['maximum_bytes'], maximum_entries=selected['maximum_entries'])
        # copytree preserves bytes, modes, times and symlink targets. It can
        # materialize hardlinks, so compare their content contract explicitly.
        def without_links(rows):
            return [{k: v for k, v in row.items() if k != 'hardlink_to'} for row in rows]
        if without_links(copied) != without_links(before):
            raise ValueError('copied worker differs from the complete original environment')
        for row in selected['replacements']:
            target = destination/row['destination']
            target.unlink()
            shutil.copy2(payload/row['source'], target)
        for row, path, target, _ in sources:
            target.mkdir()
            _source_archive_members(path, row)
            with tarfile.open(path, mode='r:*') as archive:
                archive.extractall(target, filter='data')
        commands = [
            [str(destination/'bin/python'), '-B', '-c',
                'import sys; from pathlib import Path; '
                f'assert Path(sys.prefix).resolve() == Path({str(destination)!r})'],
            [str(installer), 'pip', 'install', '--offline', '--no-deps', '--reinstall-package',
                'empirical-lawhood', '--python', str(destination/'bin/python'), str(wheel_path)],
            [str(installer), 'pip', 'check', '--python', str(destination/'bin/python')],
        ]
        for index, command in enumerate(commands):
            _durable_bytes(output/f'command-{index}.json', _encode(command))
            with (output/f'command-{index}.log').open('xb') as stream:
                run(command, env=environment, stdout=stream, stderr=subprocess.STDOUT, check=True)
        for row in selected['replacements']:
            if bounded_file_sha256(destination/row['destination'], maximum_bytes=selected['maximum_bytes'])[1] != row['sha256']:
                raise ValueError('installed environment changed a selected replacement')
        verify_transfer(payload, manifest_path, expected_sha256=expected_sha256)
    finally:
        if _tree_census(base, maximum_bytes=selected['maximum_bytes'], maximum_entries=selected['maximum_entries']) != before:
            raise ValueError('original worker environment changed during restoration')
    result = {'status': 'SEPARATE_WORKER_ENVIRONMENT_RESTORED', 'base_environment': str(base),
        'destination': str(destination), 'cloned_bytes': clone_bytes, 'original_environment_unchanged': True,
        'source_destinations': [str(target) for _, _, target, _ in sources],
        'recipe_sha256': sha256(raw).hexdigest(), 'payload_manifest_sha256': expected_sha256,
        'native_calls': 0, 'remaining_entry_requirements': ['installed-source-acceptance', 'actual-domain-engine-admission']}
    _durable_bytes(output/'readout.json', _encode(result))
    return result
