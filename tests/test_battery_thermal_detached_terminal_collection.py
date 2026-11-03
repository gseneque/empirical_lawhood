# SPDX-License-Identifier: MPL-2.0
"""Portable collection cannot depend on optional native scientific packages."""

from pathlib import Path
import subprocess
import sys


def test_exposed_dae_native_module_collects_without_importing_pybamm():
    selected = Path(__file__).with_name("test_battery_thermal_detached_terminal.py")
    code = """
import importlib.abc
import sys
class RejectNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'pybamm', 'openmm'}:
            raise AssertionError('portable collection imports an optional native package')
sys.meta_path.insert(0, RejectNative())
import pytest
raise SystemExit(pytest.main(['--collect-only', '-q', sys.argv[1]]))
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(selected)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "3 tests collected" in result.stdout
