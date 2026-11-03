# SPDX-License-Identifier: MPL-2.0
"""Import-only operational environment proof; no worker/native science claim."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import prepared_native as owner
from empirical_lawhood.runtime.prepared_native_invocation import PreparedWorkerEnvironment

PROBE = '''
import hashlib,json,os,pathlib,sys,sysconfig
before=dict(os.environ)
expected=str(pathlib.Path(sysconfig.get_path("purelib"))/"casadi")
assert before["CASADIPATH"]==expected and before["PYBAMM_DISABLE_TELEMETRY"]=="true"
import pybamm
current=dict(os.environ)
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
print(json.dumps({"before_sha256":digest(before),"after_sha256":digest(current),
    "added_keys":sorted(set(current)-set(before)),"removed_keys":sorted(set(before)-set(current)),
    "changed_keys":sorted(key for key in before.keys() & current.keys() if before[key]!=current[key]),
    "interpreter":sys.executable,"prefix":sys.prefix,"pybamm_version":pybamm.__version__,"casadipath":expected},sort_keys=True))
'''


@pytest.mark.native
def test_actual_selected_interpreter_pybamm_import_preserves_complete_preselected_environment(tmp_path):
    before_parent = 'pybamm' in sys.modules
    declared = dict(os.environ, LANG='C.UTF-8', LC_ALL='C.UTF-8', KMP_DUPLICATE_LIB_OK='True',
        PYBAMM_DISABLE_TELEMETRY='true', PYTHONDONTWRITEBYTECODE='1')
    declared.pop('CASADIPATH', None)
    selected = owner.native_worker_environment(declared)
    expected_sha = sha256(json.dumps(selected, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    completed = subprocess.run((sys.executable, '-B', '-c', PROBE), env=selected, capture_output=True, text=True,
        check=True, timeout=60)
    observed = json.loads(completed.stdout)
    assert observed['before_sha256'] == observed['after_sha256'] == expected_sha
    assert observed['added_keys'] == observed['removed_keys'] == observed['changed_keys'] == []
    assert Path(observed['interpreter']).absolute() == Path(sys.executable).absolute()
    assert observed['prefix'] == sys.prefix and observed['casadipath'] == owner.expected_casadi_path()
    assert ('pybamm' in sys.modules) == before_parent
    (tmp_path/'actual-import-only-environment.json').write_text(json.dumps(observed, sort_keys=True, indent=2)+'\n')


@pytest.mark.parametrize('selected_value,actual_value', ((None, 'expected'), ('wrong', 'wrong'), ('expected', 'wrong')))
def test_missing_wrong_or_changed_native_setting_refuses_before_import(monkeypatch, selected_value, actual_value):
    expected = owner.expected_casadi_path()
    selected = {} if selected_value is None else {'CASADIPATH': expected if selected_value == 'expected' else '/tmp/incorrect-selected-casadi'}
    monkeypatch.setenv('CASADIPATH', expected if actual_value == 'expected' else '/tmp/incorrect-selected-casadi')
    before = 'pybamm' in sys.modules
    prepared = PreparedWorkerEnvironment(str(Path(sys.executable).absolute()), sha256(Path(sys.executable).read_bytes()).hexdigest(),
        str(Path(sys.prefix).absolute()), tuple(sorted(selected.items())))
    with pytest.raises(ValueError, match='ENVIRONMENT: select CASADIPATH=.*before worker preparation'):
        owner.require_native_worker_environment(prepared)
    assert ('pybamm' in sys.modules) == before


def test_explicit_wrong_caller_value_is_preserved_then_refused(monkeypatch):
    original = {'CASADIPATH': '/tmp/incorrect-selected-casadi', 'OMP_NUM_THREADS': '1'}
    selected = owner.native_worker_environment(original)
    assert selected == original and selected is not original
    monkeypatch.setenv('CASADIPATH', selected['CASADIPATH'])
    prepared = PreparedWorkerEnvironment(str(Path(sys.executable).absolute()), sha256(Path(sys.executable).read_bytes()).hexdigest(),
        str(Path(sys.prefix).absolute()), tuple(sorted(selected.items())))
    with pytest.raises(ValueError, match='ENVIRONMENT: select CASADIPATH='):
        owner.require_native_worker_environment(prepared)
