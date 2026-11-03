# SPDX-License-Identifier: MPL-2.0
"""RECURARCH native input boundary conformance; no scientific effects.

All records and contact metadata are exposed software fixtures. No backend,
native child BEGIN, acquisition or scientific authority is exercised.
"""

from dataclasses import replace

import pytest

from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.native_subwork_inputs import validate_native_subwork_inputs
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_subwork import NativeSubworkInputError, NativeSubworkRoster, NativeSubworkState
from tests.runtime_platform.test_native_subwork import ExposedInput, _selected


def write_record(plane, record, name, *, access=Access.EVALUATION_SEALED, visibility=Visibility.PROSPECTIVE):
    written = plane.write(ArtifactWriteRequest(name, "inputs/" + name + ".json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "publication." + name, "inputs",
        record.canonical_bytes(), visibility, (), access))
    return decode_artifact_manifest(plane.root.resolve(written.materialization.relative_path + ".manifest.json",
        for_write=False).read_bytes())


@pytest.fixture
def mixed(tmp_path):
    original_store, definition, original_inputs = _selected(tmp_path, freeze=False)
    plane = original_store.plane
    inputs = []
    for number, item in enumerate(original_inputs):
        raw = plane.root.resolve(item.materialization.relative_path, for_write=False).read_bytes()
        written = plane.write(ArtifactWriteRequest("mixed." + str(number), "inputs/mixed." + str(number) + ".json",
            item.logical.payload_schema, ArtifactProfile.CANONICAL_JSON, "application/json", "publication.mixed." + str(number),
            "inputs", raw, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
        inputs.append(decode_artifact_manifest(plane.root.resolve(written.materialization.relative_path + ".manifest.json",
            for_write=False).read_bytes()))
    inputs.append(write_record(plane, ExposedInput("coarse.sealed", "exposed-return"), "coarse.sealed"))
    inputs = tuple(inputs)
    parent = replace(definition.parent_contact, run_id="run.mixed-software", task_id="task.mixed-software",
        attempt_id="attempt.mixed-software", execution_task=replace(definition.parent_contact.execution_task,
            object_id="task.mixed-software"),
        input_materialization_ids=tuple(sorted(i.materialization.materialization_id for i in inputs)))
    definition = replace(definition, parent_contact=parent, input_materialization_ids=parent.input_materialization_ids)
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=parent.execution_plan,
        visibility_ceiling=Visibility.PROSPECTIVE, outcome_access=Access.EVALUATION_SEALED)
    contacts.begin(parent)
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent, parent_inputs=inputs)
    store.freeze_roster(NativeSubworkRoster("selected.native-subwork", parent, (definition.identity,)), definitions=(definition,))
    return store, definition, inputs


def test_original_uniform_mode_and_exact_mixed_parent_scopes(mixed):
    store, definition, inputs = mixed
    with pytest.raises(NativeSubworkInputError, match="access boundary"):
        validate_native_subwork_inputs(store.plane, definition, inputs,
            visibility=Visibility.PROSPECTIVE, access=Access.EVALUATION_SEALED)
    validate_native_subwork_inputs(store.plane, definition, inputs,
        visibility=Visibility.PROSPECTIVE, access=Access.EVALUATION_SEALED, frozen_parent_inputs=inputs)


def test_original_no_map_uniform_development_contract_is_unchanged(tmp_path):
    store, definition, inputs = _selected(tmp_path, freeze=False)
    validate_native_subwork_inputs(store.plane, definition, inputs,
        visibility=Visibility.DEVELOPMENT_ONLY, access=Access.DEVELOPMENT_VISIBLE)
    assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize("defect", ("wrong-access", "changed-visibility", "changed-profile", "missing-parent", "extra-parent", "duplicate-parent", "duplicate-input"))
def test_exact_original_manifest_and_parent_denominator_refuse_mutations(mixed, defect):
    store, definition, inputs = mixed
    actual, frozen = list(inputs), list(inputs)
    if defect == "wrong-access":
        actual[0] = replace(actual[0], publication=None,
            logical=replace(actual[0].logical, outcome_access=Access.EVALUATION_SEALED))
    elif defect == "changed-visibility":
        actual[0] = replace(actual[0], publication=None,
            logical=replace(actual[0].logical, visibility_ceiling=Visibility.DEVELOPMENT_ONLY))
    elif defect == "changed-profile":
        actual[0] = replace(actual[0], publication=None,
            logical=replace(actual[0].logical, media_type="application/vnd.changed+json"))
    elif defect == "missing-parent":
        frozen.pop()
    elif defect == "extra-parent":
        frozen.append(write_record(store.plane, ExposedInput("unknown.parent", "exposed-only"), "unknown.parent"))
    elif defect == "duplicate-parent":
        frozen.append(frozen[0])
    else:
        actual.append(actual[0])
    with pytest.raises(NativeSubworkInputError, match="manifest|parent|census"):
        validate_native_subwork_inputs(store.plane, definition, tuple(actual), visibility=Visibility.PROSPECTIVE,
            access=Access.EVALUATION_SEALED, frozen_parent_inputs=tuple(frozen))
    assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize("scope", (Access.EVALUATION_SEALED, Access.OUTCOME_BLIND, Access.DEVELOPMENT_VISIBLE))
def test_unknown_conditional_operand_preserves_uniform_parent_output_scope(mixed, scope):
    store, definition, inputs = mixed
    record = ExposedInput("conditional.source", "exposed-derived-operand")
    extra = write_record(store.plane, record, "conditional.source",
        access=scope, visibility=Visibility.DEVELOPMENT_ONLY if scope is Access.DEVELOPMENT_VISIBLE else Visibility.PROSPECTIVE)
    selected = replace(definition,
        sources=tuple(sorted((*definition.sources, ObjectIdentity.from_record(record.selected_id, record)), key=lambda i:i.object_id)),
        input_materialization_ids=tuple(sorted((*definition.input_materialization_ids, extra.materialization.materialization_id))))
    if scope is Access.EVALUATION_SEALED:
        validate_native_subwork_inputs(store.plane, selected, (*inputs, extra), visibility=Visibility.PROSPECTIVE,
            access=Access.EVALUATION_SEALED, frozen_parent_inputs=inputs)
    else:
        with pytest.raises(NativeSubworkInputError, match="access boundary"):
            validate_native_subwork_inputs(store.plane, selected, (*inputs, extra), visibility=Visibility.PROSPECTIVE,
                access=Access.EVALUATION_SEALED, frozen_parent_inputs=inputs)
    assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED


def test_actual_store_uses_held_scopes_and_refuses_changes_before_begin_or_effects(mixed, monkeypatch):
    store, definition, inputs = mixed
    class QualifiedBeforeBegin(Exception):
        pass
    reached = []
    def stop(selected):
        reached.append(selected.identity)
        raise QualifiedBeforeBegin()
    monkeypatch.setattr(store, "_assert_live_parent", stop)
    with pytest.raises(QualifiedBeforeBegin):
        store.begin(definition)
    assert reached == [definition.identity]
    reached.clear()
    changed = (replace(inputs[0], publication=None,
        logical=replace(inputs[0].logical, outcome_access=Access.EVALUATION_SEALED)), *inputs[1:])
    with pytest.raises(NativeSubworkInputError, match="frozen parent"):
        store.begin(definition, inputs=changed)
    assert not reached
    assert store.inspect(definition).state is NativeSubworkState.NOT_ENTERED
