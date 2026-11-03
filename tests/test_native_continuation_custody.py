# SPDX-License-Identifier: MPL-2.0
"""Separate literal-software custody never erases an original uncertain attempt."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuation, NativeContinuationCustodyScope
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster, NativeSubworkState
from tests.runtime_platform.test_native_subwork import _selected, _publish, _complete


def _census(root):
    return {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob('*') if path.is_file()}


def _continued_contacts(original, scope, *, selected_scope=False):
    return ExternalNativeEffectContactStore(plane=original.plane,
        execution_plan=scope.original_contact.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        continuation_scopes=(scope,), task_scopes={scope.task_id: (
            VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)} if selected_scope else None)


@pytest.mark.parametrize('contacted', (False, True))
@pytest.mark.parametrize('selected_scope', (False, True))
def test_explicit_new_attempt_uses_disjoint_raw_custody_and_preserves_original_state(tmp_path, contacted, selected_scope):
    original, definition, inputs = _selected(tmp_path)
    entry = original.begin(definition, inputs)
    if contacted:
        original.contact(entry)
    scope = NativeContinuationCustodyScope(ObjectIdentity('continuation.exposed',
        DevelopmentNativeContinuation.SCHEMA, DevelopmentNativeContinuation.VERSION, 'a' * 64),
        definition.parent_contact, 'synthetic.run.native.parent.continuation.attempt-001')
    root = Path(original.plane.root.contract.canonical_path)
    before = _census(root)
    contacts = _continued_contacts(original, scope, selected_scope=selected_scope)
    parent = scope.expected_contact
    assert contacts.read(parent.run_id, parent.task_id) is None
    with pytest.raises(ValueError, match='separate attempt'):
        contacts.begin(replace(parent, attempt_id='unselected.attempt'))
    contacts.begin(parent)
    with pytest.raises(ValueError, match='already committed'):
        contacts.begin(parent)
    new = replace(definition, parent_contact=parent)
    continued = ExternalNativeSubworkStore(plane=original.plane,
        parent_contacts=contacts.for_task(parent.task_id), parent_contact=parent, parent_inputs=inputs)
    roster = NativeSubworkRoster('selected.native-subwork', parent, (new.identity,))
    continued.freeze_roster(roster, definitions=(new,))
    entered = continued.begin(new, inputs)
    continued.contact(entered)
    output = _publish(continued, entered, b'EXPOSED-SEPARATE-CALL')
    completed = _complete(continued, entered)
    assert output.materialization.relative_path.startswith(scope.relative_root + '/')
    assert continued._receipt_locator(new) == original._receipt_locator(definition)
    assert continued.receipts._relative_path(*continued._receipt_locator(new)) != original.receipts._relative_path(
        *original._receipt_locator(definition))
    assert completed.receipt.task_id == 'native-subwork.' + original._key(definition)
    assert completed.receipt.receipt_id == 'receipt.' + continued._receipt_locator(new)[2]
    assert output.logical.logical_artifact_id == completed.receipt.task_id + '.output.' + new.outputs[0].output_id
    fresh = ExternalNativeSubworkStore(plane=original.plane,
        parent_contacts=_continued_contacts(original, scope, selected_scope=True).for_task(parent.task_id),
        parent_contact=parent, parent_inputs=inputs, completed_only=True)
    assert b''.join(fresh.iter_completed_output(new, new.outputs[0].output_id)) == b'EXPOSED-SEPARATE-CALL'
    assert fresh.read_roster(parent) == roster
    with fresh.plane.read_context() as plane:
        scoped = ExternalNativeSubworkStore(plane=plane, parent_contacts=fresh.parent_contacts,
            parent_contact=parent, parent_inputs=inputs, completed_only=True)
        assert scoped.read_definition(new.identity) == new
        assert tuple(scoped.iter_roster_states(parent)) == ((new.identity, NativeSubworkState.COMPLETED),)
        assert scoped.inspect(new).receipt == completed.receipt
    assert original.parent_contacts.read(parent.run_id, parent.task_id) == definition.parent_contact
    assert original.inspect(definition).state is (
        NativeSubworkState.UNKNOWN_COMPLETION if contacted else NativeSubworkState.BEGUN)
    after = _census(root)
    assert {key: after[key] for key in before} == before
    assert all(key.startswith(scope.relative_root + '/') for key in after.keys() - before.keys())


def test_continuation_scope_cannot_change_input_source_or_original_contact(tmp_path):
    original, definition, _ = _selected(tmp_path)
    scope = NativeContinuationCustodyScope(ObjectIdentity('continuation.exposed',
        DevelopmentNativeContinuation.SCHEMA, DevelopmentNativeContinuation.VERSION, 'a' * 64),
        definition.parent_contact, 'synthetic.run.native.parent.continuation.attempt-001')
    contacts = _continued_contacts(original, scope)
    with pytest.raises(ValueError, match='bound original parent'):
        ExternalNativeSubworkStore(plane=original.plane, parent_contacts=contacts)
    with pytest.raises(ValueError, match='original operands'):
        contacts.begin(replace(scope.expected_contact, input_materialization_ids=()))
    with pytest.raises(ValueError, match='original operands'):
        contacts.begin(replace(scope.expected_contact, implementation_commit='b' * 40))
    original_path = original.plane.root.resolve(original.parent_contacts._path(
        scope.original_contact.run_id, scope.task_id), for_write=False)
    original_path.unlink()
    with pytest.raises(ValueError, match='partial'):
        contacts.begin(scope.expected_contact)
    assert contacts.read(scope.original_contact.run_id, scope.task_id) is None
