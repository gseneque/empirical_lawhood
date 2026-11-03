# SPDX-License-Identifier: MPL-2.0
"""Exact inputs admitted through a live ancestor survive the next child BEGIN."""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.adapters.methods.native_subwork_conformance import (
    ExposedDerivedOperand, ExposedNativeSubworkRunner,
)
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput, NativeSubworkRoster, NativeSubworkState
from tests.runtime_platform.test_native_subwork import _process_context, _selected
from tests.runtime_platform.test_native_subwork_completed_relay import pipe


def selected(tmp_path):
    return _selected(tmp_path, extra_outputs=(NativeSubworkOutput("derived.configuration",
        ExposedDerivedOperand.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),))


def test_spawned_grandchild_inherits_exact_already_admitted_parent_inputs(tmp_path):
    store, first, inputs = selected(tmp_path)
    context = _process_context(store, first, inputs)
    try:
        LocalProcessExecutor(scratch_root=store.plane.root).execute(
            ExposedNativeSubworkRunner((first,), (b"FALSIFIED",), "derived-grandchild"),
            context, timeout_seconds=None, native_subwork=store)
    finally:
        for port in context.input_ports:
            port.close()
    child, = store.iter_roster_definitions(first.parent_contact, "conditional.derived-segment")
    grandchild, = store.iter_roster_definitions(first.parent_contact, "conditional.derived-call-operand")
    assert grandchild.input_materialization_ids == child.input_materialization_ids
    assert len(grandchild.input_materialization_ids) == len(first.input_materialization_ids) + 1
    assert store.read_roster(first.parent_contact, grandchild.roster_id).parent_subwork == child.identity
    assert store.recover(grandchild).outputs[0].logical.content_sha256 == sha256(b"FALSIFIED").hexdigest()
    assert store.recover(child).outputs[0].logical.content_sha256 == sha256(b"UNEVALUABLE").hexdigest()


def test_uncompleted_sibling_operands_never_become_global_inputs(tmp_path):
    store, first, inputs = selected(tmp_path)
    progress, service, context = pipe(store, first, inputs, tmp_path)
    try:
        sibling = replace(first, subwork_id="forecast.two")
        entry = progress.begin(first)
        progress.contact(entry)
        operand = ExposedDerivedOperand("exposed.sibling-only", first.parent_contact.task_id, "a" * 64)
        manifest = progress.publish_output(entry, "derived.configuration", (operand.canonical_bytes(),),
            maximum_bytes=len(operand.canonical_bytes()), expected_size_bytes=len(operand.canonical_bytes()),
            expected_physical_sha256=operand.fingerprint())
        sibling_entry = progress.begin(sibling)
        progress.contact(sibling_entry)
        foreign = replace(first, subwork_id="forecast.two.foreign", configuration=operand.identity,
            roster_id="conditional.foreign-sibling", input_materialization_ids=tuple(sorted(
                (*first.input_materialization_ids, manifest.materialization.materialization_id))))
        progress.freeze_roster(NativeSubworkRoster(foreign.roster_id, first.parent_contact,
            (foreign.identity,), sibling.identity), sibling_entry, definitions=(foreign,))
        with pytest.raises(ValueError, match="outside its frozen parent"):
            progress.begin(foreign)
        assert store.inspect(foreign).state is NativeSubworkState.NOT_ENTERED
    finally:
        service.close()
        for port in context.input_ports:
            port.close()
