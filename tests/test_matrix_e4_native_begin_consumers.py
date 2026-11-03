# SPDX-License-Identifier: MPL-2.0
"""Actual E4 DEV worker Ready/BEGIN consumers over existing exposed software keys.

This owner reuses the already disclosed tiny prefix fixture. That fixture really
acquires its exposed prefix. These added cases invoke no continuation/response
solver, native CONTACT, signer, public campaign or qualification. A software-only
parent contact and selected subwork BEGIN are deliberately retained in positive
and late-stop cases. They confer no scientific execution or outcome authority.
Physical producing-checkout and SQL lease mutation are separate acceptance cases;
retiring the actual live creator below is not represented as a SQL lease test.
"""

from dataclasses import replace

import pytest

from empirical_lawhood.infrastructure import execution as lifecycle
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkInputError, NativeSubworkState, NativeSubworkUncertainContact,
)
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from tests.runtime_platform.test_native_subwork import _store
from tests.test_matrix_e4_worker_preflight import (
    invoke, native_case, provenance, ready, scheduled, stock,  # noqa: F401
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner


PHASES = ('prefix', 'continue', 'responses')


def _invocation(case, phase, *, suffix):
    runner, context, contract, inputs = invoke(case, phase, suffix=suffix)
    if phase == 'prefix':
        # The shared fixture already completed a prefix at its original contact.
        # This distinct software run reuses the same disclosed keys without
        # acquiring them, inventing freshness or touching the completed custody.
        context = replace(context, run_id=context.run_id + '.boundary-control',
            attempt_id=context.attempt_id + '.boundary-control', prepared_invocation=None)
        runner = type(runner)(phase, runner.manifest).with_prepared_scope((
            context.run_id, context.task_id, context.input_materialization_ids, contract.execution_plan))
        initial = lifecycle.prepare_worker_invocation(runner, context, inputs,
            implementation=case.implementation, execution_plan=contract.execution_plan,
            execution_task=contract.execution_task, execution_task_record=contract.execution_task_record,
            native_effect=True, provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))
        work = runner.prepare_native_work(replace(context, prepared_invocation=initial),
            expected_parent=initial.expected_parent_contact)
        contract = replace(initial, native_work=work)
        context = replace(context, prepared_invocation=contract)
    return runner, context, contract, inputs


def _ready_store(case, phase, *, suffix):
    runner, context, contract, inputs = _invocation(case, phase, suffix=suffix)
    ready(runner, context, contract)
    manifests = tuple(ArtifactManifest(row.logical, row.materialization) for row in inputs)
    store = _store(case.plane, contract.expected_parent_contact, manifests, prepared_invocation=contract)
    definition, = contract.native_definitions
    roster, = contract.native_work.rosters
    # This is a disclosed custody-only parent contact, not a solver invocation.
    store.parent_contacts.begin(contract.expected_parent_contact)
    store.freeze_roster(roster, definitions=(definition,))
    return runner, context, contract, inputs, store, definition


def _close(context, store=None, parent=None):
    for port in context.input_ports:
        port.close()
    if store is not None:
        store.parent_contacts.retire_live_creator(parent)


@pytest.mark.parametrize('phase', PHASES)
def test_actual_e4_native_ready_reaches_exact_durable_begin_without_native_contact(native_case, phase):  # noqa: F811
    runner, context, contract, inputs, store, definition = _ready_store(
        native_case, phase, suffix='ready-begin')
    try:
        assert definition.parent_contact == contract.expected_parent_contact
        assert len(definition.streams) == (8 if phase == 'responses' else 4)
        assert set(definition.input_materialization_ids) == {row.materialization.materialization_id for row in inputs}
        assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED
        store.begin(definition)
        observed = store.inspect(definition)
        assert observed.state is NativeSubworkState.BEGUN
        assert observed.begin is not None and observed.contact is None
        assert observed.completion is None and observed.receipt is None
        assert store.read_roster(definition.parent_contact, definition.roster_id).subworks == (definition.identity,)
    finally:
        _close(context, store, contract.expected_parent_contact)


@pytest.mark.parametrize('phase', PHASES)
@pytest.mark.parametrize('damage', ('source-body', 'source-sidecar', 'source-marker'))
def test_actual_e4_begin_replays_late_input_publication_damage(native_case, phase, damage):  # noqa: F811
    runner, context, contract, inputs, store, definition = _ready_store(
        native_case, phase, suffix='late-' + damage)
    original = next(row for row in inputs if row.artifact_id.endswith('.source'))
    source_path = native_case.plane.root.resolve(original.materialization.relative_path, for_write=False)
    sidecar = source_path.with_name(source_path.name + '.manifest.json')
    manifest = decode_artifact_manifest(sidecar.read_bytes())
    assert manifest.publication is not None
    target = (source_path if damage == 'source-body' else sidecar if damage == 'source-sidecar' else
        native_case.plane.root.resolve(manifest.publication.commit_marker_relative_path, for_write=False))
    saved = target.read_bytes()
    try:
        # Original custody changes while worker ports retain sealed bytes.
        # BEGIN must independently refuse its fresh read before any contact.
        target.write_bytes(saved[:-1] + bytes((saved[-1] ^ 1,)))
        with pytest.raises(NativeSubworkInputError) as refused:
            store.begin(definition)
        assert refused.value.mismatches
        observed = store.inspect(definition)
        assert observed.state is NativeSubworkState.NOT_ENTERED
        assert observed.begin is None and observed.contact is None
        assert store.parent_contacts.read(context.run_id, context.task_id) == contract.expected_parent_contact
        if damage == 'source-body':
            cursor = next(port for port in context.input_ports if port.artifact_id == original.artifact_id).cursor()
            try:
                assert cursor.read() == saved
            finally:
                cursor.close()
            sealed = lifecycle._worker_preflight(runner, context, contract,
                (MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work)
            assert sealed.ready
    finally:
        target.write_bytes(saved)
        assert target.read_bytes() == saved
        _close(context, store, contract.expected_parent_contact)


@pytest.mark.parametrize('phase', PHASES)
def test_actual_e4_ready_stops_replaced_dependency_receipt_after_preparation(native_case, phase):  # noqa: F811
    runner, context, contract, inputs = _invocation(native_case, phase, suffix='late-dependency')
    try:
        ready(runner, context, contract)
        original = context.dependency_receipts[0]
        substituted = replace(original, receipt_id=original.receipt_id + '.substituted')
        with pytest.raises(ValueError, match='complete worker context'):
            replace(context, dependency_receipts=(substituted, *context.dependency_receipts[1:]))
        changed = replace(context, dependency_receipts=(substituted, *context.dependency_receipts[1:]),
            prepared_invocation=None)
        stopped = lifecycle._worker_preflight(runner, changed, contract,
            (MATRIX_PROVENANCE_REQUIREMENT,), native_work_preparer=owner.prepare_native_work)
        assert not stopped.ready
        assert any(row.operand_id == contract.task_id and 'complete worker context' in row.reason
            for row in stopped.mismatches)
        store = _store(native_case.plane, contract.expected_parent_contact,
            tuple(ArtifactManifest(row.logical, row.materialization) for row in inputs), prepared_invocation=contract)
        assert store.parent_contacts.read(context.run_id, context.task_id) is None
    finally:
        _close(context)


@pytest.mark.parametrize('phase', PHASES)
def test_actual_e4_begin_stops_when_creating_parent_lifetime_ends(native_case, phase):  # noqa: F811
    runner, context, contract, inputs, store, definition = _ready_store(
        native_case, phase, suffix='retired-creator')
    try:
        original = store.parent_contacts.read(context.run_id, context.task_id)
        store.parent_contacts.retire_live_creator(original)
        assert not store.parent_contacts.is_live_creator(original)
        with pytest.raises(NativeSubworkUncertainContact, match='live creating launch'):
            store.begin(definition)
        assert store.parent_contacts.read(context.run_id, context.task_id) == original
        observed = store.inspect(definition)
        assert observed.state is NativeSubworkState.NOT_ENTERED
        assert observed.begin is None and observed.contact is None
    finally:
        _close(context, store, contract.expected_parent_contact)
