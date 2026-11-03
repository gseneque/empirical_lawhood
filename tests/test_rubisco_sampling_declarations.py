# SPDX-License-Identifier: MPL-2.0
"""Exposed declaration and refusal controls; no molecular engine execution."""

from dataclasses import replace
import os
import subprocess
import sys
from types import SimpleNamespace
import json

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import (
    executable_binding as dynamics, operation_bindings as original)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import DurablePreparationWorker
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse import GeometryReusePlan, GeometryReuseRunner
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_runner import GeometryReuseWorker
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.ordinary_preparation import check_preparation_only_root
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import operation_bindings as sampling
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_preparation_admission import (
    ReusedGeometryChemicalForcePlan, SerializedDurableChemicalForcePlan)
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.control_runner import ChemicalForceRunner
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.nve_runner import NVEControlRunner
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.operation_runner import SamplingOperationWorker
from tests.runtime_platform.test_worker_preflight import _case
from tests.runtime_platform.test_native_subwork import ExposedInput


def test_original_individual_descriptors_preserve_issued_identity():
    expected = {
        "rubisco-insilico-dynamics.assess-preparation": (
            "c863d5afb5f175feb2cdcd25a826c6dadcc804a53ee93dcc7e95907bd640cfab",
            "65c4532c745a6a35035a10d289b3f523be1a4d3ae35c11a906436c4ee4ea4d0b"),
        "rubisco-insilico-dynamics.prepare": (
            "dafe20e09384241020e883cef4f45c52a8800fc0a49f4ff8975273a1bea4d75a",
            "eb8011a65ad651eee85e2a9805a22c91859df7712ab3cdd9c61e10360751f5d1"),
    }
    factories = {row.binding.capability_key: row for row in dynamics.EXECUTABLE_BINDING_FACTORIES}
    for declaration in original.operation_declarations():
        manifest = declaration.manifest()
        assert (manifest.fingerprint(), factories[manifest.capability_key].binding.fingerprint()) == expected[manifest.capability_key]


def test_current_routes_have_explicit_native_preparers_and_closed_historical_inputs():
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_operation_bindings import operation_declarations
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.closed_raw_model_admission import InstanceChemicalForcePlan
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.serialized_nve_custody import SerializedCustodyNVEControlPlan
    declarations = (*original.operation_declarations(), *operation_declarations(), *sampling.operation_declarations())
    for declaration in declarations:
        registration = declaration.registration()
        assert callable(registration.native_work_preparer) is registration.native_effect
        assert registration.native_effect == declaration.execution_properties.native_effect
    assert GeometryReusePlan.VERSION == "1.0.0"
    assert InstanceChemicalForcePlan.VERSION == "1.4.0"
    assert SerializedCustodyNVEControlPlan.VERSION == "1.2.0"
    # The NVE contract admits these immutable originals, not a relabelled 1.4 plan.
    historical = tuple(row for row in sampling.INPUT_RECORD_TYPES if row.SCHEMA == InstanceChemicalForcePlan.SCHEMA)
    assert ReusedGeometryChemicalForcePlan in historical
    assert SerializedDurableChemicalForcePlan in historical
    assert tuple((row.SCHEMA, row.VERSION) for row in sampling.INPUT_RECORD_TYPES) == tuple(sorted(
        {(row.SCHEMA, row.VERSION) for row in sampling.INPUT_RECORD_TYPES}))


@pytest.mark.parametrize("route", ("ordinary", "durable", "geometry", "geometry-inner", "chemical", "nve", "chemical-outer", "nve-outer"))
@pytest.mark.parametrize("bound", (False, True))
def test_current_execute_refuses_missing_complete_specialist_before_science_or_effect(tmp_path, route, bound):
    # This actual sealed-input fixture deliberately has literal exposed source
    # metadata. It tests the early contract guard, not producing readiness.
    _, bundle, _, context, contract, _ = _case(tmp_path, native=True)
    try:
        if bound:
            context = replace(context, prepared_invocation=contract)
        if route == "ordinary":
            call = lambda: original.PreparationRunner("prepare").execute_with_native_subwork(context, None, None)
        elif route == "durable":
            call = lambda: DurablePreparationWorker("prepare").execute_streaming_with_native_subwork(context, None, None)
        elif route == "geometry":
            call = lambda: GeometryReuseWorker("reuse-geometry").execute_streaming_with_native_subwork(context, None, None)
        elif route == "geometry-inner":
            call = lambda: GeometryReuseRunner(None, "", (), (), ()).execute_streaming_with_native_subwork(context, None, None)
        elif route in {"chemical", "nve"}:
            runner = ChemicalForceRunner if route == "chemical" else NVEControlRunner
            call = lambda: runner(None, "", (), (), (), "census").execute_streaming_with_native_subwork(context, None, None)
        else:
            operation = "chemical-force" if route == "chemical-outer" else "nve-control"
            call = lambda: SamplingOperationWorker(operation).execute_streaming_with_native_subwork(context, None, None)
        with pytest.raises(ValueError, match="SOFTWARE:.*(specialist|preparation)"):
            call()
    finally:
        bundle.close()


def test_same_sealed_input_can_be_rechecked_after_live_loader_consumption(tmp_path):
    _, bundle, _, context, _, _ = _case(tmp_path)
    try:
        port, = context.input_ports
        original_bytes = port.read()
        assert len(original_bytes) == port.size_bytes
        assert port.read() == b""
        for _ in range(2):
            cursor = port.cursor()
            try:
                assert cursor.read() == original_bytes
            finally:
                cursor.close()
        assert port.read() == b""
    finally:
        bundle.close()


def test_durable_invocation_canonical_encoder_preserves_original_record_and_definition_arrays(tmp_path):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import _invocation_bytes
    _, bundle, _, _, contract, _ = _case(tmp_path, native=True)
    try:
        records = {name: ExposedInput("exposed." + name, "exact original exposed control")
            for name in ("plan", "source", "nomination", "inventory", "coordinates")}
        selected = contract.native_work.definitions
        raw = _invocation_bytes(SimpleNamespace(source_root="/explicit/exposed-source"), records, selected)
        value = json.loads(raw)
        assert set(value) == {*records, "definitions", "source_root"}
        assert value["definitions"] == [row.canonical_bytes().decode() for row in selected]
        assert all(value[name] == record.canonical_bytes().decode() for name, record in records.items())
        assert raw.endswith(b"\n")
    finally:
        bundle.close()


@pytest.mark.parametrize("member", ("unexpected", ".preparation/started", ".preparation/return.json"))
def test_operational_preparation_metadata_does_not_authorize_uncertain_retry(tmp_path, member):
    root = tmp_path / "selected-work"
    check_preparation_only_root(root)
    (root / ".preparation").mkdir(parents=True)
    (root / ".preparation/invocation.json").write_bytes(b"selected original invocation")
    check_preparation_only_root(root)
    (root / member).write_bytes(b"uncertain actual work")
    with pytest.raises(ValueError, match="receipt-only recovery"):
        check_preparation_only_root(root)


def test_installed_descriptors_stay_cold_and_private_ordinary_bootstrap_is_retired(tmp_path):
    script = r'''
import importlib.abc,sys
class NoScience(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy','openmm','parmed','pdbfixer','pybamm','flint'}:
            raise AssertionError('descriptor entered science: '+fullname)
sys.meta_path.insert(0,NoScience())
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.executable_binding import EXECUTABLE_BINDING_FACTORIES as d
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.executable_binding import EXECUTABLE_BINDING_FACTORIES as s
assert len(d)==4 and len(s)==2
assert not any(name.endswith(('.native','.control_native_entry','.nve_native_entry','.ordinary_native_entry')) for name in sys.modules)
'''
    result = subprocess.run((sys.executable, "-B", "-c", script), env=dict(os.environ), cwd=tmp_path,
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    refused = subprocess.run((sys.executable, "-B", "-m",
        "empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.native",
        "--selected-preparation", str(tmp_path / "never-created")), env=dict(os.environ), cwd=tmp_path,
        capture_output=True, text=True, check=False)
    assert refused.returncode != 0
    assert "historical private bootstrap is retired" in refused.stderr
    assert not (tmp_path / "never-created").exists()
