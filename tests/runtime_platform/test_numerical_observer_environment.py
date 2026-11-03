# SPDX-License-Identifier: MPL-2.0
"""Actual import-only environment observation and unchanged exact-pair guards.

The selected interpreter imports threadpoolctl without engine/native entry.
Pure contact/entry records below are disclosed contract fixtures, never durable
contacts, actual invocation selections or scientific qualification evidence.
"""

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import MappingProxyType

import pytest

from empirical_lawhood.infrastructure.isolated_native_subwork import selected_environment_sha256
from empirical_lawhood.infrastructure.numerical_provenance import numerical_observer_environment, selected_worker_environment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork, PreparedWorkerEnvironment


KMP = "KMP_DUPLICATE_LIB_OK"
PROBE = '''
import hashlib,json,os,sys
before=dict(os.environ)
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
import threadpoolctl
current=dict(os.environ)
print(json.dumps({"before_sha256":digest(before),"after_sha256":digest(current),
    "added_keys":sorted(set(current)-set(before)),"removed_keys":sorted(set(before)-set(current)),
    "changed_keys":sorted(key for key in before.keys() & current.keys() if before[key]!=current[key]),
    "kmp":current.get("KMP_DUPLICATE_LIB_OK"),"interpreter":sys.executable,
    "prefix":sys.prefix,"observer_module":threadpoolctl.__file__},sort_keys=True))
'''


def _full_sha(environment):
    # Independent ordinary JSON oracle for the exact existing transport format.
    return sha256(json.dumps(environment, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _environment():
    # Explicit locale prevents a CPython startup locale coercion from being
    # confused with the observer module's measured import effect.
    environment = dict(os.environ, LANG="C.UTF-8", LC_ALL="C.UTF-8", PYTHONDONTWRITEBYTECODE="1")
    environment.pop(KMP, None)
    return environment


def _observe(environment):
    completed = subprocess.run((sys.executable, "-c", PROBE), env=environment,
        capture_output=True, text=True, check=True, timeout=15)
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def test_actual_selected_interpreter_import_adds_only_the_observed_kmp_default(tmp_path):
    original = _environment()
    observed = _observe(original)
    assert observed["before_sha256"] == _full_sha(original)
    assert observed["added_keys"] == [KMP] and observed["changed_keys"] == observed["removed_keys"] == []
    assert observed["kmp"] == "True"
    selected = numerical_observer_environment(original)
    assert selected == {**original, KMP: "True"} and KMP not in original
    assert observed["after_sha256"] == _full_sha(selected) == selected_environment_sha256(selected)
    assert observed["before_sha256"] != observed["after_sha256"]
    assert Path(observed["interpreter"]).absolute() == Path(sys.executable).absolute()
    assert Path(observed["prefix"]).absolute() == Path(sys.prefix).absolute()
    (tmp_path/"actual-observer-import.json").write_text(json.dumps(observed, indent=2, sort_keys=True)+"\n")


@pytest.mark.parametrize("explicit", ("False", "user-explicit"))
def test_actual_import_and_selection_preserve_an_explicit_caller_value(tmp_path, explicit):
    original = {**_environment(), KMP: explicit}
    selected = numerical_observer_environment(original)
    assert selected == original and selected is not original
    observed = _observe(selected)
    assert observed["kmp"] == explicit
    assert observed["added_keys"] == observed["changed_keys"] == observed["removed_keys"] == []
    assert observed["before_sha256"] == observed["after_sha256"] == _full_sha(original)
    assert selected_environment_sha256(original) == observed["after_sha256"]
    (tmp_path/"actual-explicit-observer-import.json").write_text(json.dumps(observed, indent=2, sort_keys=True)+"\n")


def test_selected_environment_is_import_stable_before_any_child_process():
    selected = numerical_observer_environment(_environment())
    observed = _observe(selected)
    assert observed["before_sha256"] == observed["after_sha256"] == _full_sha(selected)
    assert observed["added_keys"] == observed["changed_keys"] == observed["removed_keys"] == []


@pytest.mark.parametrize("explicit", (None, "False", "0", "caller-value"))
def test_common_worker_setting_selection_preserves_explicit_values_without_mutating_parent(monkeypatch, explicit):
    if explicit is None:
        monkeypatch.delenv(KMP, raising=False)
    else:
        monkeypatch.setenv(KMP, explicit)
    selected = dict(selected_worker_environment())
    assert selected[KMP] == ("True" if explicit is None else explicit)
    assert os.environ.get(KMP) == explicit
    assert selected["OMP_NUM_THREADS"] == selected["OPENBLAS_NUM_THREADS"] == "1"


def test_helper_copies_every_full_environment_key_and_is_idempotent():
    original = {"CUSTOM_EXPLICIT_SCOPE": "unchanged-α", "OMP_NUM_THREADS": "1"}
    selected = numerical_observer_environment(original)
    assert original == {"CUSTOM_EXPLICIT_SCOPE": "unchanged-α", "OMP_NUM_THREADS": "1"}
    assert selected == {**original, KMP: "True"}
    assert numerical_observer_environment(selected) == selected
    assert numerical_observer_environment(selected) is not selected
    assert selected_environment_sha256(selected) == _full_sha(selected)
    assert selected_environment_sha256(dict(reversed(tuple(selected.items())))) == _full_sha(selected)


@pytest.mark.parametrize("invalid", (None, (), MappingProxyType({"a": "b"}), {1: "x"}, {"x": 1}, {"x": True}))
def test_non_exact_or_non_string_environments_refuse(invalid):
    with pytest.raises(ValueError, match="exact string environment"):
        numerical_observer_environment(invalid)


def _ordinary_work(environment):
    """Nonexecuted, nonpublished ordinary-scope pair for the existing guard."""
    def identity(name):
        return ObjectIdentity(name, "empirical-lawhood/testing/observer-contract", "1.0.0", sha256(name.encode()).hexdigest())
    parent = NativeEffectContact("run.observer-contract", "task.observer-contract", "attempt.observer-contract",
        identity("plan.observer-contract"), identity("task.observer-contract"), "a"*40, (), ())
    executable = Path(sys.executable).absolute()
    interpreter_sha = sha256(executable.resolve().read_bytes()).hexdigest()
    worker = PreparedWorkerEnvironment(str(executable), interpreter_sha, str(Path(sys.prefix).absolute()), tuple(sorted(environment.items())))
    selected = IsolatedNativeEntrySelection("selection.observer-contract", str(executable), interpreter_sha,
        "exposed.observer_contract", "enter", "/explicit/nonexecuted/observer-entry.py", "b"*64,
        "/explicit/nonexecuted/invocation.json", "c"*64, _full_sha(environment))
    return PreparedNativeWork(parent, ("unit.observer-contract",), ("slot.observer-contract",),
        isolated_selection=selected, isolated_environment=worker)


@pytest.mark.parametrize("value", (None, "/explicit/selected/casadi", "/explicit/incompatible/casadi"))
def test_casadi_environment_is_selected_only_when_explicit_without_domain_inference(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("CASADIPATH", raising=False)
    else:
        monkeypatch.setenv("CASADIPATH", value)
    selected = dict(selected_worker_environment())
    assert selected.get("CASADIPATH") == value
    # The scientific domain checks compatibility; shared selection preserves
    # explicit bytes and never adopts a later native-import mutation.
    assert os.environ.get("CASADIPATH") == value


@pytest.mark.parametrize("damage", ("changed-kmp", "removed-kmp", "unselected-added-key", "other-thread-limit", "false-environment-hash"))
def test_import_default_selection_does_not_weaken_existing_exact_full_environment_pair(damage):
    selected = numerical_observer_environment({"OMP_NUM_THREADS": "1", "CUSTOM_EXPLICIT_SCOPE": "original"})
    work = _ordinary_work(selected)
    environment = dict(selected)
    entry = work.isolated_selection
    if damage == "changed-kmp":
        environment[KMP] = "False"
    elif damage == "removed-kmp":
        del environment[KMP]
    elif damage == "unselected-added-key":
        environment["UNSELECTED_LATE_DRIFT"] = "not-adopted"
    elif damage == "other-thread-limit":
        environment["OMP_NUM_THREADS"] = "2"
    else:
        entry = replace(entry, environment_sha256="f"*64)
    changed = replace(work.isolated_environment, selected_environment=tuple(sorted(environment.items())))
    with pytest.raises(ValueError, match="exact interpreter/hash/full environment"):
        replace(work, isolated_selection=entry, isolated_environment=changed)
    assert work.isolated_selection.environment_sha256 == _full_sha(selected)
    assert dict(work.isolated_environment.selected_environment) == selected


def test_runtime_pool_order_does_not_change_identity_or_drop_observations(monkeypatch):
    from empirical_lawhood.infrastructure.numerical_provenance import numerical_runtime_observation
    from empirical_lawhood.kernel.serialization import canonical_json_bytes

    # Distinct paths sharing a backend, an unknown field and an exact duplicate
    # all remain part of the census; only list order is nonsemantic.
    pools = [
        {"filepath": "/fixture/z.so", "num_threads": 1, "version": "1", "extra": "preserved"},
        {"filepath": "/fixture/a.so", "num_threads": 1, "version": "2"},
        {"filepath": "/fixture/a.so", "num_threads": 1, "version": "2"},
    ]
    monkeypatch.setattr("threadpoolctl.threadpool_info", lambda: pools)
    first = canonical_json_bytes(numerical_runtime_observation())
    monkeypatch.setattr("threadpoolctl.threadpool_info", lambda: list(reversed(pools)))
    assert canonical_json_bytes(numerical_runtime_observation()) == first
    actual = json.loads(first)["threadpools"]
    assert len(actual) == len(pools)
    assert sorted(map(lambda row: json.dumps(row, sort_keys=True), actual)) == sorted(
        map(lambda row: json.dumps(row, sort_keys=True), pools))
    pools[0] = {**pools[0], "num_threads": 2}
    assert canonical_json_bytes(numerical_runtime_observation()) != first


def test_actual_cold_processes_observe_the_same_complete_numerical_runtime(tmp_path):
    probe = r"""
import json,sys
if sys.argv[1] == "numpy-first":
    import numpy
else:
    from empirical_lawhood.cli.entry import enforce_single_thread_environment
    enforce_single_thread_environment()
    from empirical_lawhood.cli.app import app
# Compare the same loaded engines after the two different entry sequences.
import scipy.linalg
from empirical_lawhood.api.matrix_programme_e2 import assemble_programme_e2
from empirical_lawhood.infrastructure.numerical_provenance import numerical_runtime_observation
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from threadpoolctl import threadpool_info
observed = canonical_json_bytes(numerical_runtime_observation()).decode()
print(json.dumps({"observation": observed, "actual_pools": threadpool_info()}))
"""
    observations = []
    for mode in ("numpy-first", "cli-first"):
        completed = subprocess.run((sys.executable, "-B", "-c", probe, mode), env=_environment(),
            capture_output=True, text=True, check=True, timeout=60)
        assert completed.stderr == ""
        result = json.loads(completed.stdout)
        actual = json.loads(result["observation"])["threadpools"]
        assert sorted(json.dumps(row, sort_keys=True) for row in actual) == sorted(
            json.dumps(row, sort_keys=True) for row in result["actual_pools"])
        assert actual and all(row["num_threads"] == 1 for row in actual)
        observations.append(result["observation"])
        (tmp_path / (mode + ".json")).write_text(json.dumps(result, indent=2) + "\n")
    assert observations[0] == observations[1]
