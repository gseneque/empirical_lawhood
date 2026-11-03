# SPDX-License-Identifier: MPL-2.0
"""Operational custody selection guards; no scientific or native entry."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


def launcher():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_applied_el_broad_programme.py'
    spec = importlib.util.spec_from_file_location('selected_programme_locations', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selected_locations():
    return launcher().selected_locations


def explicit(tmp_path):
    return SimpleNamespace(label='selected-location', project_root=tmp_path / 'project',
        prior_root=tmp_path / 'original', working_root=tmp_path / 'mount' / 'working',
        logs_root=tmp_path / 'logs', durable_root=tmp_path / 'mount' / 'durable',
        custody_mount=tmp_path / 'mount', custody_filesystem='vfat',
        custody_profile='empirical-lawhood/applied-el/selected-vfat-profile')


@pytest.mark.parametrize('missing', (None, 'working_root', 'logs_root', 'durable_root',
    'custody_mount', 'custody_filesystem', 'custody_profile'))
def test_new_invocation_requires_every_location_before_creating_outputs(tmp_path, missing):
    args = explicit(tmp_path)
    args.project_root.mkdir()
    if missing is None:
        for field in ('working_root', 'logs_root', 'durable_root', 'custody_mount',
                      'custody_filesystem', 'custody_profile'):
            delattr(args, field)
    else:
        setattr(args, missing, None)
    before = set(tmp_path.rglob('*'))
    with pytest.raises(ValueError, match='requires all'):
        launcher().SelectedProgramme(args)
    assert set(tmp_path.rglob('*')) == before


def test_explicit_filesystem_selection_is_cold_and_exact(tmp_path):
    args = explicit(tmp_path)
    assert selected_locations()(args) == (
        args.working_root, args.logs_root, args.durable_root, args.custody_mount,
        ('vfat',), args.custody_profile)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('damage', ('missing', 'relative', 'symlink', 'working-log',
    'working-durable', 'mount-root', 'outside-mount', 'checkout', 'history',
    'filesystem', 'profile'))
def test_bad_selection_refused_before_outputs_are_created(tmp_path, damage):
    args = explicit(tmp_path)
    if damage == 'missing':
        args.logs_root = None
    elif damage == 'relative':
        args.logs_root = Path('relative')
    elif damage == 'symlink':
        real = tmp_path / 'actual'
        real.mkdir()
        alias = tmp_path / 'alias'
        alias.symlink_to(real, target_is_directory=True)
        args.logs_root = alias / 'logs'
    elif damage == 'working-log':
        args.logs_root = args.working_root / 'logs'
    elif damage == 'working-durable':
        args.durable_root = args.working_root
    elif damage == 'mount-root':
        args.working_root = args.custody_mount
    elif damage == 'outside-mount':
        args.working_root = tmp_path / 'outside'
    elif damage == 'checkout':
        args.project_root = args.working_root / 'project'
    elif damage == 'history':
        args.prior_root = args.durable_root / 'original'
    elif damage == 'filesystem':
        args.custody_filesystem = ''
    elif damage == 'profile':
        args.custody_profile = ''
    before = set(tmp_path.rglob('*'))
    with pytest.raises(ValueError):
        selected_locations()(args)
    assert set(tmp_path.rglob('*')) == before


@pytest.mark.parametrize('name', ('broad_programme', 'rubisco_nomination',
    'rubisco_nomination_terminal', 'battery_precision_diagnostic', 'battery_refined_programme'))
@pytest.mark.parametrize('help_selected', (False, True))
def test_cli_locations_and_help_refuse_before_sdk_import_or_directory_creation(name, help_selected):
    path = Path(__file__).resolve().parents[1] / ('scripts/run_applied_el_' + name + '.py')
    probe = '''
import importlib.abc, pathlib, runpy, sys
class NoScientificImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('empirical_lawhood', 'pybamm', 'numpy', 'scipy'):
            raise AssertionError('argument handling imported science: ' + fullname)
sys.meta_path.insert(0, NoScientificImports())
def no_directory(*args, **kwargs):
    raise AssertionError('argument handling created a directory')
pathlib.Path.mkdir = no_directory
path, help_selected = pathlib.Path(sys.argv[1]), sys.argv[2] == 'True'
sys.path.insert(0, str(path.parent))
sys.argv = [str(path), '--help'] if help_selected else [str(path)]
try:
    runpy.run_path(str(path), run_name='__main__')
except SystemExit as error:
    assert error.code == (0 if help_selected else 2), error.code
else:
    raise AssertionError('argument handling unexpectedly returned')
'''
    completed = subprocess.run([sys.executable, '-B', '-c', probe, str(path), str(help_selected)],
        capture_output=True, text=True, check=True)
    text = (completed.stdout if help_selected else
            completed.stderr.split('error: the following arguments are required:', 1)[1])
    for option in ('working-root', 'logs-root', 'durable-root', 'custody-mount',
                   'custody-filesystem', 'custody-profile'):
        assert '--' + option in text
