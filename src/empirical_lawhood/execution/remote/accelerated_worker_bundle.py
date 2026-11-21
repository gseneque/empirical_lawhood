# SPDX-License-Identifier: MPL-2.0
"""Render an offline worker installation from an authenticated wheel bundle.

The upstream package installers own installation. The enclosing deployment
authenticates every transferred byte before this script can run.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import shlex

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.serialization import validate_relative_locator, validate_sha256
from empirical_lawhood.execution.remote.worker_profiles import hosted_worker_profile


@dataclass(frozen=True, slots=True)
class WorkerBundle:
    base_image: str
    source_image_sha256: str
    source_lock_sha256: str
    source_lock: str
    requirements: str
    wheels: str
    uv_wheel: str
    system_package: str
    installed_versions: dict[str, str]

    def __post_init__(self):
        if re.fullmatch(r'docker:[A-Za-z0-9_./:-]+@sha256:[0-9a-f]{64}', self.base_image) is None:
            raise ValueError('worker bundle requires its exact public base image')
        for value in (self.source_image_sha256, self.source_lock_sha256):
            validate_sha256(value, field_name='worker bundle source')
        for value in (self.requirements, self.wheels, self.uv_wheel, self.system_package, self.source_lock):
            validate_relative_locator(value)
        if (not self.uv_wheel.endswith('.whl') or not self.system_package.endswith('.deb')
                or type(self.installed_versions) is not dict or not self.installed_versions
                or any(type(k) is not str or re.fullmatch(r'[a-z0-9-]+', k) is None
                    or type(v) is not str or re.fullmatch(r'[A-Za-z0-9.+!-]+', v) is None
                    for k, v in self.installed_versions.items())):
            raise ValueError('worker bundle requires exact package and installed-version selections')

    def require_capabilities(self, numerical_backend):
        """Validate the exact selected environment without probing any native device."""
        profile = hosted_worker_profile(numerical_backend)
        profile.validate_versions(self.installed_versions)
        return profile

    @classmethod
    def read(cls, path):
        document = json.loads(read_bounded_bytes(Path(path), maximum_bytes=128*1024))
        if type(document) is not dict or document.pop('version', None) != '1.0.0':
            raise ValueError('unsupported worker bundle revision')
        return cls(**document)

    def validate_files(self, root):
        root = Path(root)
        for value in (self.requirements, self.uv_wheel, self.system_package, self.source_lock):
            path = root/value
            if not path.is_file() or path.resolve(strict=True) != path:
                raise ValueError('worker bundle lacks an ordinary selected installation input')
        if sha256(read_bounded_bytes(root/self.source_lock, maximum_bytes=16*2**20)).hexdigest() != self.source_lock_sha256:
            raise ValueError('worker bundle substitutes its exact original dependency lock')
        wheelhouse = root/self.wheels
        if not wheelhouse.is_dir() or wheelhouse.resolve(strict=True) != wheelhouse:
            raise ValueError('worker bundle lacks its selected wheel directory')


@dataclass(frozen=True, slots=True)
class RetainedWorkerBundle:
    """An exact subtree of a previously sealed payload, verified before reuse."""

    remote_root: str
    original_manifest_sha256: str
    bundle: WorkerBundle
    files: tuple

    @classmethod
    def read(cls, path, *, payload_root):
        from dataclasses import replace
        from empirical_lawhood.storage.transfer_files import normalized_absolute_path as _absolute, portable_relative_path as _relative, read_transfer_manifest as _read_transfer_manifest
        document = json.loads(read_bounded_bytes(Path(path), maximum_bytes=128*1024))
        if (type(document) is not dict or set(document) != {'version', 'remote_root', 'original_manifest',
                'original_manifest_sha256', 'original_prefix', 'bundle_specification'}
                or document['version'] != '1.0.0'):
            raise ValueError('unsupported retained worker bundle selection')
        root = Path(payload_root)
        _absolute(document['remote_root'])
        for name in ('original_manifest', 'original_prefix', 'bundle_specification'):
            _relative(document[name])
        _, original = _read_transfer_manifest(root/document['original_manifest'],
            expected_sha256=document['original_manifest_sha256'])
        prefix = document['original_prefix']+'/'
        files = tuple(replace(row, relative_path=row.relative_path[len(prefix):])
            for row in original if row.relative_path.startswith(prefix))
        by_name = {row.relative_path: row for row in files}
        specification = root/document['bundle_specification']
        raw = read_bounded_bytes(specification, maximum_bytes=128*1024)
        if 'worker-bundle.json' not in by_name or (
                len(raw), sha256(raw).hexdigest()) != (by_name['worker-bundle.json'].size_bytes,
                    by_name['worker-bundle.json'].sha256):
            raise ValueError('retained bundle specification differs from its original sealed bytes')
        bundle = WorkerBundle.read(specification)
        for name in (bundle.source_lock, bundle.requirements, bundle.uv_wheel, bundle.system_package):
            if name not in by_name:
                raise ValueError('retained bundle omits a required installer operand')
        if by_name[bundle.source_lock].sha256 != bundle.source_lock_sha256:
            raise ValueError('retained bundle changes its original dependency lock')
        if not any(row.relative_path.startswith(bundle.wheels+'/') for row in files):
            raise ValueError('retained bundle lacks the original wheel census')
        return cls(document['remote_root'], document['original_manifest_sha256'], bundle, files)

    def verification_script(self):
        """Stdlib-only bootstrap check, available before the worker is installed."""
        rows = [row.to_mapping() for row in self.files]
        return '''# Generated by the retained worker-bundle owner; no provider contact.
from hashlib import sha256
from pathlib import Path
import json, os, stat
root = Path(REMOTE_ROOT)
expected = {row['relative_path']: row for row in json.loads(FILE_CENSUS)}
if not root.is_absolute() or root.resolve(strict=True) != root or root.is_symlink() or not root.is_dir():
    raise ValueError('retained worker bundle root is redirected or absent')
seen = set()
for path in root.rglob('*'):
    info = path.lstat()
    if path.is_symlink() or path.resolve(strict=True) != path:
        raise ValueError('retained bundle contains a linked or redirected member')
    if path.is_dir():
        continue
    name = path.relative_to(root).as_posix()
    if name not in expected or not stat.S_ISREG(info.st_mode):
        raise ValueError('retained bundle changes its original complete file census')
    row = expected[name]
    if info.st_size != row['size_bytes']:
        raise ValueError('retained bundle changes original member size')
    digest = sha256()
    count = 0
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if os.fstat(stream.fileno()) != info:
            raise ValueError('retained bundle changed before read')
        for chunk in iter(lambda: stream.read(1048576), b''):
            count += len(chunk)
            if count > row['size_bytes']:
                raise ValueError('retained bundle exceeds its original size')
            digest.update(chunk)
    after = path.lstat()
    if ((info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns) !=
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)):
        raise ValueError('retained bundle changed during read')
    if count != row['size_bytes'] or digest.hexdigest() != row['sha256']:
        raise ValueError('retained bundle changes original bytes')
    seen.add(name)
if seen != set(expected):
    raise ValueError('retained bundle omits original files')
print('RETAINED_WORKER_BUNDLE_BYTE_VERIFIED_NO_NATIVE')
'''.replace('REMOTE_ROOT', repr(self.remote_root)).replace('FILE_CENSUS', repr(json.dumps(rows, sort_keys=True)))


def render_worker_bootstrap(bundle, *, remote_root, numerical_backend=None):
    """Use the same Python prefix as the accepted image; never contact a registry."""
    if type(bundle) is not WorkerBundle:
        raise TypeError('worker setup requires its authenticated bundle')
    bundle.__post_init__()
    profile = bundle.require_capabilities(numerical_backend)
    paths = {name: str(Path(remote_root)/getattr(bundle, name))
        for name in ('requirements', 'wheels', 'uv_wheel', 'system_package')}
    uv = '/opt/el/tools/bin/uv'
    python = '/opt/el/worker/bin/python'
    expected = json.dumps(bundle.installed_versions, sort_keys=True)
    validate = (
        'import importlib.metadata as m, json; '
        f'expected=json.loads({expected!r}); '
        "actual={d.metadata['Name'].lower().replace('_','-'):d.version for d in m.distributions()}; "
        "assert actual == expected, (actual,expected); "
        # Import checks never select or enumerate a GPU. Actual device admission
        # happens only when the separately authorized native operation is entered.
        + ("import os; os.environ['JAX_PLATFORMS']='cpu'; " if not profile.include_cutensor_path else "")
        + "import " + ", ".join(profile.import_modules)
        + "; print('WORKER_DEPENDENCY_AND_CPU_IMPORT_ACCEPTANCE_ONLY')"
    )
    return '\n'.join((
        'set -eu',
        shlex.join(('python3', '-c', "import sys,platform; assert sys.version_info[:3] == (3,11,14); assert platform.machine() == 'x86_64'")),
        'mkdir -p /opt/el/tmp',
        'export TMPDIR=/opt/el/tmp UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=hardlink PYTHONDONTWRITEBYTECODE=1',
        'test -x /opt/el/tools/bin/python || python3 -m venv /opt/el/tools',
        shlex.join(('/opt/el/tools/bin/pip', 'install', '--no-cache-dir', '--no-index', '--no-deps', paths['uv_wheel'])),
        shlex.join(('dpkg', '--install', paths['system_package'])),
        'test -f /opt/el/worker/pyvenv.cfg || '+shlex.join((uv, 'venv', '--no-python-downloads', '--python', '/usr/local/bin/python3.11', '/opt/el/worker')),
        shlex.join((uv, 'pip', 'sync', '--offline', '--no-cache', '--no-index', '--require-hashes',
            '--find-links', paths['wheels'], '--python', python, paths['requirements'])),
        'find /opt/el/worker/lib/python3.11/site-packages/nvidia -type d -name lib > /etc/ld.so.conf.d/el-cuda.conf',
        *(('echo /opt/el/worker/lib/python3.11/site-packages/cutensor/lib >> /etc/ld.so.conf.d/el-cuda.conf',)
          if profile.include_cutensor_path else ()),
        'ldconfig',
        shlex.join((uv, 'pip', 'check', '--python', python)),
        shlex.join((python, '-c', validate)),
    ))+'\n'
