"""Static capability discovery validates records without loading native owners."""

import os
from pathlib import Path
import subprocess
import sys


def test_cold_registry_import_has_no_scientific_or_native_owner_contact():
    root = Path(__file__).resolve().parents[1]
    script = '''
import importlib.abc
import sys
class RefuseImplementationImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        prefixes = (
            'empirical_lawhood.adapters', 'empirical_lawhood.domains',
            'empirical_lawhood.methods', 'empirical_lawhood.api',
            'numpy', 'scipy', 'pyscf', 'cupy', 'torch', 'jax', 'h5py',
        )
        if any(fullname == p or fullname.startswith(p + '.') for p in prefixes):
            raise AssertionError('static discovery loaded an implementation: ' + fullname)
sys.meta_path.insert(0, RefuseImplementationImports())
from empirical_lawhood.execution.generated_extension_bundles import (
    GENERATED_EXTENSION_BUNDLE_AGGREGATE, EXTENSION_BUNDLE_CONTRIBUTIONS,
    EXPECTED_AGGREGATE_FINGERPRINT,
)
assert EXTENSION_BUNDLE_CONTRIBUTIONS
assert GENERATED_EXTENSION_BUNDLE_AGGREGATE.fingerprint() == EXPECTED_AGGREGATE_FINGERPRINT
assert len({c.contribution_id for c in EXTENSION_BUNDLE_CONTRIBUTIONS}) == len(EXTENSION_BUNDLE_CONTRIBUTIONS)
from empirical_lawhood.execution import generated_executable_declarations as executable
assert executable.GENERATED_EXECUTABLE_BINDING_AGGREGATE.fingerprint() == executable.EXPECTED_AGGREGATE_FINGERPRINT
assert executable.GENERATED_EXECUTABLE_BINDING_AGGREGATE.availability
'''
    result = subprocess.run(
        [sys.executable, '-c', script], cwd=root,
        env={**os.environ, 'PYTHONPATH': str(root / 'src'), 'PYTHONDONTWRITEBYTECODE': '1'},
        text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_generated_registry_refuses_a_changed_aggregate_commitment():
    from empirical_lawhood.execution import generated_extension_bundles as registry
    source = Path(registry.__file__).read_text()
    assert registry.EXPECTED_AGGREGATE_FINGERPRINT in source
    corrupted = source.replace(registry.EXPECTED_AGGREGATE_FINGERPRINT, '0' * 64)
    import pytest
    with pytest.raises(RuntimeError, match='fingerprint drifted'):
        exec(compile(corrupted, '<corrupted-static-registry>', 'exec'), {})
