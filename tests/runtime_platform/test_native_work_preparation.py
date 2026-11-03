# SPDX-License-Identifier: MPL-2.0
"""PURE domain native-work projections; disclosed fixtures confer no authority."""

from io import BytesIO
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rc_prerequisite_chain import operation_bindings as rc
from empirical_lawhood.adapters.methods.rc_prerequisite_chain import operation_contracts as rc_records, science as rc_science
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerInputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact


def _parent(ports, task_id="exposed.task"):
    return NativeEffectContact("exposed.run", task_id, "exposed.attempt",
        ObjectIdentity("exposed.plan", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity(task_id, "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        "3" * 40, tuple(sorted(port.materialization_id for port in ports)), ())

def _port(name, schema, raw, *, array=False):
    class UnreadArray:
        def read(self, *_args):
            pytest.fail("PURE native preparation read or decoded scientific arrays")
        def close(self):
            pass
    return WorkerInputPort(WorkerInputBinding(name, "materialization." + name, schema,
        "application/x-npz" if array else "application/json", len(raw), VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE, WorkerInputKind.EXTERNAL), UnreadArray() if array else BytesIO(raw))

def test_rc_ordinary_preparation_projects_original_unit_slot_without_calculation(monkeypatch):
    config = rc_science.default_chain_config()
    selected = rc_records.RCSourceOperationConfig("exposed.rc.source", config, config.units[0].unit_id)
    runner = next(row for row in rc.build_runners() if row.config_type is rc_records.RCSourceOperationConfig)
    port = _port(selected.config_id, selected.SCHEMA, selected.canonical_bytes())
    ref = CapabilityConfigRef(selected.config_id, selected.SCHEMA, runner.manifest.config_schema_sha256,
        selected.fingerprint(), selected.config_id)
    context = SimpleNamespace(input_ports=(port,), config=ref)
    parent = _parent(context.input_ports)
    monkeypatch.setattr(rc.operations, "_execute_native_views", lambda *_: pytest.fail("native calculation"))
    work = rc.prepare_native_work(runner=runner, context=context, expected_parent=parent)
    assert work.expected_parent == parent
    assert work.scientific_unit_ids == rc.scientific_unit_ids(selected)
    assert work.native_effect_slot_ids == rc.native_effect_slot_ids(selected)
    assert work.definitions == work.rosters == ()
    installed = next(row for row in rc.operation_registrations() if row.config_record_type is selected.__class__)
    assert installed.native_work_preparer is rc.prepare_native_work
