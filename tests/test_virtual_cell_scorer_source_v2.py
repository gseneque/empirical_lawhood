# SPDX-License-Identifier: MPL-2.0
"""Cold software authentication controls over explicitly selected original assets.

Set VIRTUAL_CELL_SCORER_SUPPORT_ROOT to the retained support directory containing
official-code/. These controls never install or import the optional receiver,
open response data, or confer scientific qualification.
"""

from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import zipfile

import pytest

from empirical_lawhood.adapters.physical.virtual_cell.config import (
    virtual_cell_2025_metric_contract,
)
from empirical_lawhood.adapters.physical.virtual_cell.scorer_source_v2 import (
    SCORER_SOURCE_FILES_V2,
    SOURCE_ARCHIVE_SHA256,
    ScorerSourceUnavailable,
    require_selected_scorer_contract_v2,
)


@pytest.mark.parametrize(
    "change",
    [
        {"scorer_distribution": "caller-scorer"},
        {"scorer_version": "0.6.7"},
        {"scorer_source_sha256": SCORER_SOURCE_FILES_V2[0][2]},
        {"scorer_source_sha256": "1" * 64},
    ],
)
def test_contract_cannot_bless_alternate_scorer_bytes(change):
    contract = virtual_cell_2025_metric_contract()
    require_selected_scorer_contract_v2(contract)
    with pytest.raises(ScorerSourceUnavailable):
        require_selected_scorer_contract_v2(replace(contract, **change))


@pytest.fixture
def pinned_installation(tmp_path):
    selected = os.environ.get("VIRTUAL_CELL_SCORER_SUPPORT_ROOT")
    if not selected:
        pytest.skip("select retained original assets with VIRTUAL_CELL_SCORER_SUPPORT_ROOT")
    root = Path(selected)
    archive = root / "official-code/cell-eval-v0.6.6-source.tar.gz"
    wheel = root / "official-code/pypi/cell-eval-0.6.6/cell_eval-0.6.6-py3-none-any.whl"
    assert archive.stat().st_size == 33122
    assert sha256(archive.read_bytes()).hexdigest() == SOURCE_ARCHIVE_SHA256
    assert sha256(wheel.read_bytes()).hexdigest() == (
        "fcf72a07fb08c696695d678b29b027807460bcf91bce831eb055360d997e29d4"
    )
    expected = {name: (size, digest) for name, size, digest in SCORER_SOURCE_FILES_V2}
    original = {}
    with tarfile.open(archive) as source:
        for member in source.getmembers():
            parts = PurePosixPath(member.name).parts
            if member.isfile() and "cell_eval" in parts:
                name = "/".join(parts[parts.index("cell_eval"):])
                data = source.extractfile(member).read()
                assert name not in original
                original[name] = (len(data), sha256(data).hexdigest())
    assert original == expected and len(original) == 26
    with zipfile.ZipFile(wheel) as installed:
        package = {
            name: (len(installed.read(name)), sha256(installed.read(name)).hexdigest())
            for name in installed.namelist()
            if name.startswith("cell_eval/") and not name.endswith("/")
        }
        assert package == expected
        installed.extractall(tmp_path)
    return tmp_path


_COLD_PREFIX = """
import ast
import importlib.abc
import importlib.util
import importlib._bootstrap_external as bytecode
import os
from pathlib import Path
import py_compile
import sys
from types import ModuleType, SimpleNamespace
from empirical_lawhood.adapters.physical.virtual_cell.config import virtual_cell_2025_metric_contract
from empirical_lawhood.adapters.physical.virtual_cell.scorer_source_v2 import (
    authenticate_installed_scorer_source_v2, ScorerSourceUnavailable)
root = Path(sys.argv[1])
sys.path.insert(0, str(root))
contract = virtual_cell_2025_metric_contract()
def authenticate():
    return authenticate_installed_scorer_source_v2(contract)
def refuse():
    try:
        authenticate()
    except ScorerSourceUnavailable:
        return
    raise AssertionError('altered installation was authenticated')
"""


def _cold(root, script):
    result = subprocess.run(
        [sys.executable, "-c", _COLD_PREFIX + script, str(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.held
def test_cold_original_archive_wheel_and_normal_caches_authenticate(pinned_installation):
    _cold(pinned_installation, """
class ForbidReceiverImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('anndata', 'pdex', 'polars'):
            raise AssertionError('authentication imported optional science: ' + fullname)
sys.meta_path.insert(0, ForbidReceiverImports())
assert len(authenticate().files) == 26
for source in (root / 'cell_eval').rglob('*.py'):
    for mode in py_compile.PycInvalidationMode:
        for optimization in (0, 1, 2):
            py_compile.compile(str(source), dfile='/former/install/' + source.name,
                               optimize=optimization, invalidation_mode=mode, doraise=True)
        assert len(authenticate().files) == 26
assert 'cell_eval' not in sys.modules
""")


@pytest.mark.held
@pytest.mark.parametrize("damage", ["content", "size", "missing", "extra", "symlink"])
def test_cold_source_census_refuses_mutation(pinned_installation, damage):
    _cold(pinned_installation, f"""
source = root / 'cell_eval/__init__.py'
damage = {damage!r}
if damage == 'content':
    data = source.read_bytes()
    source.write_bytes(bytes([data[0] ^ 1]) + data[1:])
elif damage == 'size':
    source.write_bytes(source.read_bytes() + b'\\n')
elif damage == 'missing':
    source.unlink()
elif damage == 'extra':
    (root / 'cell_eval/unowned.py').write_text('pass\\n')
elif damage == 'symlink':
    saved = root / 'saved.py'
    source.rename(saved)
    source.symlink_to(saved)
refuse()
""")


@pytest.mark.held
@pytest.mark.parametrize("damage", ["missing-record", "duplicate-record", "version", "shadow"])
def test_cold_distribution_and_import_origin_refuse_mutation(pinned_installation, damage):
    _cold(pinned_installation, f"""
damage = {damage!r}
metadata = root / 'cell_eval-0.6.6.dist-info'
record = metadata / 'RECORD'
if damage == 'missing-record':
    record.write_text('\\n'.join(row for row in record.read_text().splitlines()
                                if not row.startswith('cell_eval/__init__.py,')))
elif damage == 'duplicate-record':
    first = next(row for row in record.read_text().splitlines()
                 if row.startswith('cell_eval/__init__.py,'))
    record.write_text(record.read_text() + first + '\\n')
elif damage == 'version':
    info = metadata / 'METADATA'
    info.write_text(info.read_text().replace('Version: 0.6.6', 'Version: 0.6.7'))
elif damage == 'shadow':
    shadow = root / 'shadow'
    (shadow / 'cell_eval').mkdir(parents=True)
    (shadow / 'cell_eval/__init__.py').write_text('pass\\n')
    sys.path.insert(0, str(shadow))
refuse()
""")


@pytest.mark.held
@pytest.mark.parametrize("mode", ["timestamp", "unchecked", "checked", "malformed"])
def test_cold_valid_source_cannot_bless_forged_bytecode(pinned_installation, mode):
    _cold(pinned_installation, f"""
source = root / 'cell_eval/__init__.py'
cache = Path(importlib.util.cache_from_source(str(source)))
cache.parent.mkdir()
code = compile('MetricsEvaluator = lambda: None\\n', str(source), 'exec')
mode = {mode!r}
if mode == 'timestamp':
    data = bytecode._code_to_timestamp_pyc(code, int(source.stat().st_mtime), source.stat().st_size)
elif mode == 'malformed':
    data = b'bad cache'
else:
    data = bytecode._code_to_hash_pyc(code, importlib.util.source_hash(source.read_bytes()),
                                      checked=mode == 'checked')
cache.write_bytes(data)
refuse()
assert 'cell_eval' not in sys.modules
""")


@pytest.mark.held
@pytest.mark.parametrize("damage", [None, "function", "wrong-module-path"])
def test_loaded_definitions_must_match_authenticated_module(pinned_installation, damage):
    _cold(pinned_installation, f"""
# Execute the exact original helper module with an explicit AnnData type double.
# No response arrays or official evaluator execute in this software fixture.
path = root / 'cell_eval/utils.py'
module = ModuleType('cell_eval.utils')
module.__file__ = str(path)
anndata = ModuleType('anndata')
anndata.AnnData = object
sys.modules['anndata'] = anndata
exec(compile(path.read_bytes(), str(path), 'exec'), vars(module))
sys.modules[module.__name__] = module
damage = {damage!r}
if damage == 'function':
    exec('def guess_is_lognorm(*args, **kwargs): return True', vars(module))
elif damage == 'wrong-module-path':
    module.__file__ = str(root / 'cell_eval/_baseline.py')
if damage is None:
    assert len(authenticate().files) == 26
else:
    refuse()
""")


@pytest.mark.held
def test_loaded_reexport_cannot_replace_original_receiver(pinned_installation):
    _cold(pinned_installation, """
module = ModuleType('cell_eval')
module.__file__ = str(root / 'cell_eval/__init__.py')
module.__path__ = [str(root / 'cell_eval')]
module.__spec__ = importlib.util.spec_from_file_location('cell_eval', module.__file__,
                    submodule_search_locations=module.__path__)
module.MetricsEvaluator = lambda: None
sys.modules['cell_eval'] = module
refuse()
""")
