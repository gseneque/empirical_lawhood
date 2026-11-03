# SPDX-License-Identifier: MPL-2.0
"""Exposed declared observation controls, never scientific battery acquisition."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, durable_roster as dr
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc, preparation_science as ps
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_native as base, segmented_observation_contracts as oc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_observation_native as native, segmented_science as ss
from empirical_lawhood.adapters.methods.battery_refined_inquiry.source_derived_preparation import supply_source_roots, assess_source_roots
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkUncertainContact
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.test_battery_durable_graph import stock as old_stock_fixture
from tests.test_battery_segmented_native import custody as old_custody_fixture, exposed_backend, selected as selected_fixture

selected = selected_fixture


@pytest.fixture(scope="module")
def observation():
    old = old_stock_fixture.__wrapped__()
    entries = dr.entry_dispositions(old.roster, old.uncertain)
    choices = tuple(index for index, config in enumerate(old.roster.configurations) if config.component_view == "oregan-spme")
    index = next((i for i in choices if entries[i].state == "HOLD_UNCERTAIN_PRIOR_PRIMITIVE"), choices[0])
    preparation = supply_source_roots(c.identity(old.source), "ORegan2022")
    return oc.freeze_observation(old.roster, old.uncertain, index, preparation, assess_source_roots(preparation))


def _custody(tmp_path, selected, observation, method_index, *, selected_abi_payload=None):
    tmp_path.mkdir()
    old = old_custody_fixture.__wrapped__(tmp_path, selected, N(param=D(60)))
    config = observation.configurations[method_index]
    protocol = pc.PreparationProtocol("protocol.observation-exposed." + str(method_index), c.identity(config),
        c.identity(config.source), old.provenance.identity, "ORegan2022", "SPMe", 30, 40,
        config.initial_temperature_k, ps.PREPARATION_SOURCE_MEMBERS)
    abi_payload, resource_payload = selected_abi_payload or b'{"exposed_abi":true}\n', b'{"exposed_resource":true}\n'
    abi = ObjectIdentity("source.exposed.abi", oc.RAW_SOURCE_SCHEMA, "1.0.0", sha256(abi_payload).hexdigest())
    resource_source = ObjectIdentity("source.exposed.resources", oc.RAW_SOURCE_SCHEMA, "1.0.0", sha256(resource_payload).hexdigest())
    resources = oc.ObservationResourceSnapshot("resources.exposed", "2026-10-11T11:00:00+00:00",
        ObjectIdentity("root.exposed", "empirical-lawhood/development/exposed-artifact-root", "1.0.0", "8" * 64), 1000000, 1000000, resource_source)
    declaration = oc.ObservationEntryDeclaration("entry.exposed.observation." + str(method_index),
        ss.identity(observation, "observation_id"), method_index, old.provenance, abi, resources)
    plane = _plane(tmp_path / "observation-root")
    records = ((config.config_id, config), (config.source.source_id, config.source), (protocol.protocol_id, protocol),
        (old.provenance.identity.object_id, old.provenance), (config.preparation.preparation_id, config.preparation),
        (config.preparation_assessment.assessment_id, config.preparation_assessment), (config.method.method_id, config.method),
        (observation.observation_id, observation), (observation.original_selection.roster_id, observation.original_selection),
        (observation.uncertain_work.record_id, observation.uncertain_work), (declaration.declaration_id, declaration), (resources.snapshot_id, resources))
    manifests = []
    for name, record in records:
        result = plane.write(ArtifactWriteRequest(name, "inputs/" + name + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.observation.inputs", "inputs", record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(decode_artifact_manifest(plane.root.resolve(result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
    for source, payload in ((abi, abi_payload), (resource_source, resource_payload)):
        result = plane.write(ArtifactWriteRequest(source.object_id, "inputs/" + source.object_id + ".json", source.object_schema,
            ArtifactProfile.RAW_SOURCE_BYTES, "text/plain", "exposed.observation.inputs", "inputs", payload,
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(decode_artifact_manifest(plane.root.resolve(result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
    manifests = tuple(sorted(manifests, key=lambda row: row.materialization.materialization_id))
    parent = NativeEffectContact("exposed.observation", "battery.observation", "exposed.observation.effect",
        old.store.parent_contact.execution_plan,
        replace(old.store.parent_contact.execution_task, object_id="battery.observation"), old.provenance.observed_git_head,
        tuple(row.materialization.materialization_id for row in manifests), ())
    store = _store(plane, parent, manifests)
    store.parent_contacts.begin(parent)
    definition = native.build_observation_definition(observation, method_index, protocol, old.provenance, store,
        declaration, parent.input_materialization_ids)
    native.freeze_observation_roster(store, (definition,))
    return N(config=config, protocol=protocol, provenance=old.provenance, observation=observation, method_index=method_index,
        definition=definition, store=store, plane=plane, inputs=manifests, declaration=declaration,
        abi_payload=abi_payload, resource_payload=resource_payload)


def _acquire(custody, *, original_inputs=True):
    return native.acquire_observation(custody.observation, custody.method_index, protocol=custody.protocol,
        provenance=custody.provenance, definition=custody.definition, native_subwork=custody.store,
        entry_declaration=custody.declaration, abi_payload=custody.abi_payload if original_inputs else None,
        resource_payload=custody.resource_payload if original_inputs else None, inputs=custody.inputs)


def test_declaration_keeps_all_three_methods_old_unknown_and_full_forecast_separate(observation):
    assert len(observation.configurations) == 3 and tuple(row.method.maximum_segment_horizon_s for row in observation.configurations) == (D(60), D(30), D(15))
    assert all(row.method.maximum_model_clock_s == 180000 and row.method.target_charge_ah == D("2.5") for row in observation.configurations)
    assert observation.uncertain_work.forecast_count is observation.uncertain_work.initializer_count is observation.uncertain_work.charging_segment_count is None
    assert observation.original_entry_disposition.scientific_authority == "NONE"
    assert not observation.full_forecast_completed and not observation.physical_qualification
    assert decode_canonical_bytes(observation.canonical_bytes(), type(observation), maximum_bytes=None) == observation
    for damage in ({"minimum_observation_clock_s": D(15)}, {"fresh_physical_units": 1}, {"full_forecast_completed": True},
            {"configurations": observation.configurations[:2]}, {"selected_qualification_slot": True}):
        with pytest.raises(ValueError):
            replace(observation, **damage)


@pytest.mark.parametrize("method_index,expected_calls,expected_clock,expected", (
    (0, 1, D(60), "OBSERVATION_WINDOW_COMPLETED"),
    (1, 3, D("60.25"), "OBSERVATION_WINDOW_COMPLETED"),
    (2, 3, D("30.25"), "PHYSICAL_TERMINATION_BEFORE_OBSERVATION_WINDOW")))
def test_actual_complete_windows_or_early_physical_return_keep_exact_outcomes(observation, selected, tmp_path, monkeypatch, method_index, expected_calls, expected_clock, expected):
    custody = _custody(tmp_path / "selected", selected, observation, method_index)
    _, _, effects = exposed_backend(custody, monkeypatch)
    monkeypatch.setattr(native, "build_runtime", base.build_runtime)
    monkeypatch.setattr(native, "_validate_selected_source_inputs", lambda *_: None)
    monkeypatch.setattr(native, "_validate_entry_sources", lambda *_: None)  # Explicit exposed fake engine; no real qualification.
    result = _acquire(custody)
    observed = native.observation_result(observation, method_index, result, custody.definition, custody.declaration)
    assert observed.disposition == expected and observed.actual_last_model_clock_s == expected_clock
    assert observed.observed_native_calls == len(effects) == expected_calls
    assert result.trace.native_initializer_contacts == 0 and not observed.full_forecast_completed and not observed.physical_qualification
    assert observed.original_entry_disposition == observation.original_entry_disposition
    assert decode_canonical_bytes(observed.canonical_bytes(), type(observed), maximum_bytes=None) == observed
    assert result.trace.disposition in {"SERVICE_TERMINATED", "TARGET_REACHED"}
    assert len(result.inspection.outputs) == len(native.observation_outputs()) == 12
    assessment = oc.assess_observation_preparation(observed)
    assert not assessment.full_forecast_completed and not assessment.physical_qualification
    assert decode_canonical_bytes(assessment.canonical_bytes(), type(assessment), maximum_bytes=None) == assessment
    recovered = _acquire(custody, original_inputs=False)
    assert recovered.recovered and len(effects) == expected_calls and recovered.trace is None
    with pytest.raises(ValueError, match="original authenticated"):
        native.observation_result(observation, method_index, recovered, custody.definition, custody.declaration)
    with pytest.raises(ValueError):
        replace(observed, disposition="OBSERVATION_WINDOW_COMPLETED", actual_last_model_clock_s=D(180000))


def test_absent_or_changed_entry_operands_refuse_before_any_new_contact(observation, selected, tmp_path):
    custody = _custody(tmp_path / "selected", selected, observation, 0)
    with pytest.raises(ValueError, match="authenticated ABI/resource"):
        _acquire(custody, original_inputs=False)
    assert custody.store.inspect(custody.definition).begin is None
    with pytest.raises(ValueError, match="authenticated ABI/resource"):
        native._validate_entry_sources(custody.declaration, b'{"changed":true}\n', custody.resource_payload)
    with pytest.raises(ValueError):
        replace(custody.declaration, authorised_scope="FULL_FORECAST")


def test_unknown_observation_contact_never_automatically_replays(observation, selected, tmp_path, monkeypatch):
    custody = _custody(tmp_path / "selected", selected, observation, 0)
    entry = custody.store.begin(custody.definition, custody.inputs)
    custody.store.contact(entry)
    monkeypatch.setattr(native, "_validate_entry_sources", lambda *_: pytest.fail("unknown contact must refuse before fresh entry checks"))
    with pytest.raises(NativeSubworkUncertainContact):
        _acquire(custody)


@pytest.mark.parametrize("backend_damage", ("raises", "malformed", "nan"))
def test_observation_adverse_returns_keep_original_custody_and_missing_counts(observation, selected, tmp_path, monkeypatch, backend_damage):
    custody = _custody(tmp_path / "selected", selected, observation, 0)
    options = {"fail_at": 1} if backend_damage == "raises" else {"malformed": True} if backend_damage == "malformed" else {"bad_bits": 0x7ff8000000001234}
    _, _, effects = exposed_backend(custody, monkeypatch, **options)
    monkeypatch.setattr(native, "build_runtime", base.build_runtime)
    monkeypatch.setattr(native, "_validate_selected_source_inputs", lambda *_: None)
    monkeypatch.setattr(native, "_validate_entry_sources", lambda *_: None)  # Explicit exposed engine, not actual ABI qualification.
    result = _acquire(custody)
    observed = native.observation_result(observation, 0, result, custody.definition, custody.declaration)
    assert observed.disposition == "TECHNICAL_FAILURE" and observed.observed_native_calls == len(effects) == 1
    assert result.inspection.receipt.operational_status.value == "FAILED"
    assessment = oc.assess_observation_preparation(observed)
    assert not assessment.full_forecast_completed and not assessment.physical_qualification
    child = custody.store.resolve_completed_definition(result.trace.segments[0].native_definition)
    inspection = custody.store.recover(child)
    schemas = tuple(row.logical.payload_schema for row in inspection.outputs)
    assert (base.RawReturnedSegment.SCHEMA in schemas) == (backend_damage != "raises")
    assert base.FullStateSegment.SCHEMA not in schemas
    recovered = _acquire(custody, original_inputs=False)
    assert recovered.recovered and len(effects) == 1


def _exposed_entry_sources(tmp_path, declaration, monkeypatch):
    """Portable guard inputs with explicit exposed files; no native imports."""
    packages = {"numpy": "2.4.6", "scipy": "1.17.1", "casadi": "3.7.2", "pybammsolvers": "0.8.2", "pybamm": "26.6.2.0", "python-flint": "0.8.0"}
    requested, loaded = [], []
    for name in ("numpy", "scipy", "casadi", "pybammsolvers", "pybammsolvers.idaklu", "pybamm"):
        path = tmp_path / (name.replace(".", "/") + "/__init__.py")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"# EXPOSED ABI guard control; no native acquisition\n")
        row = {"path": str(path), "resolved_path": str(path.resolve()), "size_bytes": path.stat().st_size, "sha256": sha256(path.read_bytes()).hexdigest()}
        loaded.append({"module": name, **row})
        requested.append({"module": name, "file": str(path), "version": packages.get(name, "")})
    interpreter_path = Path(sys.executable)
    interpreter = {"path": str(interpreter_path), "resolved_path": str(interpreter_path.resolve()), "size_bytes": interpreter_path.stat().st_size, "sha256": sha256(interpreter_path.read_bytes()).hexdigest()}
    mapped = [interpreter]
    maps = "0-1 r-xp 0 0 0 " + str(interpreter_path) + "\n"
    abi = {"schema": "empirical-lawhood/development/battery-selected-abi-import-smoke", "status": "IMPORTS_RETURNED",
        "python": "3.11.14", "package_versions": packages, "network_attempts": [], "environment_sync": False,
        "native_scientific_models_constructed": 0, "native_scientific_builds": 0, "native_scientific_solves": 0,
        "scope": "ACTUAL_SELECTED_LOCKED_ABI_IMPORT_ENGINEERING;NOT_NATIVE_SCIENTIFIC_ENTRY_OR_QUALIFICATION",
        "prefix": sys.prefix, "interpreter": interpreter, "requested_imports": requested,
        "selected_environment": {key: os.environ.get(key) for key in ("OPENBLAS_CORETYPE", "NPY_DISABLE_CPU_FEATURES", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")},
        "loaded_module_files": loaded, "mapped_file_bindings": mapped, "process_maps": maps, "process_maps_sha256": sha256(maps.encode()).hexdigest()}
    capacity = {"schema": "empirical-lawhood/development/battery-host-resource-observation", "actual_host": True,
        "observed_utc": declaration.resources.observed_utc, "declared_storage_root": declaration.resources.declared_storage_root.to_document(),
        "storage_available_bytes": declaration.resources.storage_available_bytes, "memory_available_bytes": declaration.resources.memory_available_bytes}
    monkeypatch.setattr(native.importlib.metadata, "version", lambda name: packages[name])
    monkeypatch.setattr(native.importlib.metadata, "distribution", lambda name: N(locate_file=lambda relative: tmp_path / relative))
    return abi, capacity


def _bound_entry(declaration, abi, capacity):
    abi_payload, resource_payload = json.dumps(abi, sort_keys=True).encode(), json.dumps(capacity, sort_keys=True).encode()
    return replace(declaration,
        abi_import_report=replace(declaration.abi_import_report, object_fingerprint=sha256(abi_payload).hexdigest()),
        resources=replace(declaration.resources, evidence=replace(declaration.resources.evidence, object_fingerprint=sha256(resource_payload).hexdigest()))), abi_payload, resource_payload


def test_entry_guard_recomputes_complete_original_source_and_resource_products(observation, selected, tmp_path, monkeypatch):
    custody = _custody(tmp_path / "selected", selected, observation, 0)
    abi, capacity = _exposed_entry_sources(tmp_path / "exposed-files", custody.declaration, monkeypatch)
    bound = _bound_entry(custody.declaration, abi, capacity)
    native._validate_entry_sources(*bound)
    # Each damaged report has a matching physical digest; its scientific and
    # environmental operands must still refuse, not merely pass a hash check.
    for damage in ({"network_attempts": ["exposed forbidden contact"]}, {"native_scientific_solves": True},
            {"requested_imports": abi["requested_imports"][:-1]}, {"mapped_file_bindings": []},
            {"prefix": "exposed foreign interpreter"}, {"process_maps_sha256": "a" * 64},
            {"selected_environment": {}}, {"loaded_module_files": abi["loaded_module_files"][:-1]}):
        with pytest.raises(ValueError):
            native._validate_entry_sources(*_bound_entry(custody.declaration, {**abi, **damage}, capacity))
    for damage in ({"actual_host": False}, {"memory_available_bytes": 1}, {"declared_storage_root": {}}, {"observed_utc": "2026-10-12T11:00:00+00:00"}):
        with pytest.raises(ValueError):
            native._validate_entry_sources(*_bound_entry(custody.declaration, abi, {**capacity, **damage}))
    changed_path = Path(abi["loaded_module_files"][0]["path"])
    changed_path.write_bytes(b"# original qualified bytes changed\n")
    with pytest.raises(ValueError, match="unavailable or changed|bytes have changed"):
        native._validate_entry_sources(*bound)


@pytest.mark.native
def test_unloaded_parameter_source_mutation_refuses_before_begin_contact_or_import(observation, selected, tmp_path, monkeypatch):
    # Copy exact selected source bytes as inert exposed fixtures. No installed
    # source is edited and no parameter/native module is imported.
    root = tmp_path / "source-copy"
    pybamm_root, scipy_root = root / "pybamm", root / "scipy"
    config = observation.configurations[0]
    for member, _ in set((*config.source.source_members, *ps.PREPARATION_SOURCE_MEMBERS)):
        stock = "scipy" if member.startswith("scipy/") else "pybamm"
        relative = member.removeprefix("scipy/") if stock == "scipy" else member
        installed = Path(native.importlib.metadata.distribution(stock).locate_file(stock + "/" + relative))
        target = (scipy_root if stock == "scipy" else pybamm_root) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(installed.read_bytes())
    payload = json.dumps({"requested_imports": [{"module": "pybamm", "file": str(pybamm_root / "__init__.py")},
        {"module": "scipy", "file": str(scipy_root / "__init__.py")}]}).encode()
    custody = _custody(tmp_path / "selected", selected, observation, 0, selected_abi_payload=payload)
    native._validate_selected_source_inputs(config, custody.protocol, payload)
    unloaded = pybamm_root / "input/parameters/lithium_ion/ORegan2022.py"
    unloaded.write_bytes(unloaded.read_bytes() + b"\n# EXPOSED changed unloaded parameter source\n")
    monkeypatch.setattr(native, "_validate_entry_sources", lambda *_: None)  # Isolate scientific-pin gate with explicit exposed ABI fixture.
    with pytest.raises(ValueError, match="scientific source pin changed before contact"):
        _acquire(custody)
    assert custody.store.inspect(custody.definition).begin is None


def test_resource_snapshots_do_not_become_bounds_or_effect_authority():
    source = ObjectIdentity("source.resources", oc.RAW_SOURCE_SCHEMA, "1.0.0", "a" * 64)
    record = oc.ObservationResourceSnapshot("resources.test", "2026-10-11T11:00:00+00:00", source, 100, 100, source)
    for damage in ({"memory_available_bytes": 0}, {"storage_available_bytes": True}, {"scope": "FULL_FORECAST_MEMORY_QUALIFIED"}):
        with pytest.raises(ValueError):
            replace(record, **damage)


def test_observation_native_owner_import_is_inert():
    result = subprocess.run((sys.executable, "-c", "import sys; import empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_observation_native; assert 'pybamm' not in sys.modules; assert 'numpy' not in sys.modules"),
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
