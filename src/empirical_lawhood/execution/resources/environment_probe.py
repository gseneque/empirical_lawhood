# SPDX-License-Identifier: MPL-2.0
"""Bounded interpreter metadata probes that suppress site and native startup."""

from __future__ import annotations

import json
from pathlib import Path

from empirical_lawhood.storage.bounded_io import bounded_file_sha256
from empirical_lawhood.execution.local.bounded_process import run_bounded_command


# -I ignores user/PYTHONPATH selection. -S prevents .pth and sitecustomize code.
# Distribution metadata is read from the selected interpreter's own site paths.
# In Python 3.11, -S resets a venv's prefix; pyvenv.cfg restores that path as data.
_PROBE_SOURCE = r'''
import builtins, importlib.metadata as metadata, json, os, pathlib, platform, re, sys, sysconfig
blocked = {'brian2','pybamm','cantera','fipy','grid2op','torax','gymtorax','jax','jaxlib',
           'pyscf','openmm','parmed','pdbfixer','cupy','gpu4pyscf','sky'}
original_import = builtins.__import__
def guarded(name,*args,**kwargs):
    if name.split('.')[0] in blocked:
        raise RuntimeError('metadata probe attempted a native module import')
    return original_import(name,*args,**kwargs)
builtins.__import__ = guarded
def normalize(value):
    return re.sub(r'[-_.]+','-',value).lower()
raw = sys.stdin.buffer.read(128 * 1024 + 1)
if len(raw) > 128 * 1024:
    raise ValueError('metadata request exceeds its byte bound')
names = json.loads(raw)
if type(names) is not list or not names or len(names) > 512 or any(type(v) is not str for v in names):
    raise ValueError('metadata request requires a bounded distribution census')
selected = pathlib.Path(sys.argv[1])
root = selected.parent.parent
base = sysconfig.get_paths()
sites = [base['purelib'], base['platlib']]
configuration = root / 'pyvenv.cfg'
if configuration.is_file():
    with configuration.open('rb') as stream:
        config = stream.read(65537)
    if len(config) > 65536:
        raise ValueError('selected venv configuration exceeds its byte bound')
    values = {key.strip().lower(): value.strip().lower() for line in config.decode().splitlines()
              if '=' in line for key, value in (line.split('=', 1),)}
    paths = sysconfig.get_paths(vars={'base':str(root),'platbase':str(root),'installed_base':str(root),'installed_platbase':str(root)})
    sites = [paths['purelib'],paths['platlib']]
    if values.get('include-system-site-packages') == 'true':
        sites.extend((base['purelib'],base['platlib']))
sites = sorted({str(pathlib.Path(path).resolve()) for path in sites})
versions = {normalize(name): [] for name in names}
count = 0
for distribution in metadata.distributions(path=sites):
    count += 1
    if count > 8192:
        raise ValueError('selected environment has an excessive metadata census')
    name = distribution.metadata.get('Name')
    if type(name) is str and normalize(name) in versions:
        version = distribution.version
        if type(version) is not str or len(version) > 128:
            raise ValueError('installed distribution has invalid version metadata')
        versions[normalize(name)].append(version)
print(json.dumps({'python_version': platform.python_version(), 'python_implementation': platform.python_implementation(),
    'system': platform.system(), 'architecture': platform.machine(), 'metadata_paths': sites,
    'distributions': {name: sorted(values) for name,values in versions.items()},
    'site_startup_enabled': False, 'native_modules_loaded': sorted(blocked.intersection(sys.modules))},sort_keys=True))
'''


def inspect_interpreter_metadata(python: Path, distribution_names: tuple[str, ...]) -> dict:
    """Execute only the selected interpreter and stdlib metadata probe."""
    selected = Path(python)
    if not selected.is_absolute() or ".." in selected.parts:
        raise ValueError("environment inspection requires an absolute interpreter path")
    if (type(distribution_names) is not tuple or not 0 < len(distribution_names) <= 512
            or len(set(distribution_names)) != len(distribution_names)
            or any(type(name) is not str or not name or len(name) > 128 for name in distribution_names)):
        raise ValueError("environment inspection requires a bounded unique distribution census")
    resolved = selected.resolve(strict=True)
    before = bounded_file_sha256(resolved, maximum_bytes=512 * 1024**2)
    request = json.dumps(distribution_names).encode()
    result = run_bounded_command((str(selected), "-I", "-S", "-B", "-c", _PROBE_SOURCE, str(selected)),
        input_bytes=request, maximum_input_bytes=128 * 1024, timeout_seconds=30,
        maximum_stdout_bytes=256 * 1024, maximum_stderr_bytes=64 * 1024)
    if result.returncode:
        raise ValueError("selected interpreter metadata probe failed: " + result.stderr.decode(errors="replace")[:4096])
    if selected.resolve(strict=True) != resolved or bounded_file_sha256(resolved, maximum_bytes=before[0]) != before:
        raise ValueError("selected interpreter changed during metadata inspection")
    value = json.loads(result.stdout)
    required = {"python_version", "python_implementation", "system", "architecture", "metadata_paths",
                "distributions", "site_startup_enabled", "native_modules_loaded"}
    if (type(value) is not dict or set(value) != required or value["site_startup_enabled"] is not False
            or value["native_modules_loaded"] != [] or type(value["distributions"]) is not dict
            or set(value["distributions"]) != set(distribution_names)):
        raise ValueError("selected interpreter changed the metadata-only probe contract")
    return {**value, "selected_python": str(selected), "interpreter_file": {
        "resolved_path": str(resolved), "size_bytes": before[0], "sha256": before[1]}}
