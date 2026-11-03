# SPDX-License-Identifier: MPL-2.0
"""Pure precontact falsifiers for actual unit, acquisition and authored-root joins."""

from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.rc_prerequisite_chain import operation_contracts as rc_records
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.operation_bindings import (
    operation_manifests as rc_manifests, operation_registrations as rc_registrations,
    output_codecs as rc_codecs,
)
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import default_chain_config
from empirical_lawhood.adapters.methods.battery_recursive_construction.contracts import BatteryOperation, BatteryOperationConfig
from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import (
    battery_wave_a_draft, battery_wave_b_draft,
)
from empirical_lawhood.adapters.methods.battery_recursive_construction.executable_binding import (
    operation_manifests as battery_manifests,
    operation_registrations as battery_registrations, output_codecs as battery_codecs,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave, project_recursive_assessments


def _compile(draft, *, battery=False, registrations=None):
    manifests, records, codecs = ((battery_manifests, battery_registrations, battery_codecs)
                                  if battery else (rc_manifests, rc_registrations, rc_codecs))
    return compile_recursive_wave(draft=draft, registrations=records() if registrations is None else registrations,
        registry=CapabilityRegistry("review.unit-bindings", tuple(sorted(manifests(), key=lambda value: value.registry_id))),
        implementation_commit="a" * 40, output_codecs=codecs())


def _replace_config(draft, node, record_type, **changes):
    operation = next(value for value in draft.operations if value.node_id == node)
    config = decode_canonical_bytes(operation.config_payload.encode(), record_type, maximum_bytes=16 * 1024**2)
    changed = replace(operation, config_payload=replace(config, **changes).canonical_bytes().decode())
    return replace(draft, operations=tuple(changed if value.node_id == node else value for value in draft.operations))


def _alias(draft, node, record_type, **changes):
    operation = next(value for value in draft.operations if value.node_id == node)
    config = decode_canonical_bytes(operation.config_payload.encode(), record_type, maximum_bytes=16 * 1024**2)
    config = replace(config, config_id=config.config_id + ".alias", **changes)
    alias = replace(operation, node_id=node + ".alias", config_id=config.config_id,
                    config_payload=config.canonical_bytes().decode(), obligation_ids=("obligation.alias",))
    links = tuple(replace(link, edge_id=link.edge_id + ".alias", consumer_node_id=alias.node_id,
                          requirement_id=None, connection_id=None)
                  for link in draft.links if link.consumer_node_id == node)
    return replace(draft, operations=tuple(sorted((*draft.operations, alias), key=lambda value: value.node_id)),
        links=tuple(sorted((*draft.links, *links), key=lambda value: value.edge_id)),
        selected_operation_ids=tuple(sorted((*draft.selected_operation_ids, alias.node_id))))


def _battery_b():
    # Explicit unissued synthetic procedure operands exercise compiler shape.
    # No signer, native solve, public qualification or fresh evidence is claimed.
    from tests.test_battery_recursive_construction import _a_products, _test_manifest
    _, _, procedure = _a_products()
    return battery_wave_b_draft(_test_manifest(procedure), procedure)


@pytest.mark.parametrize("battery", [False, True])
def test_unchanged_scientific_wave_preserves_legitimate_nested_acquisition_slots(battery):
    if battery:
        assert len(_compile(battery_wave_a_draft(), battery=True).execution_plan.tasks) == 11
        assert len(_compile(_battery_b(), battery=True).execution_plan.tasks) == 21
    else:
        config = default_chain_config()
        assert len(_compile(rc_recursive_draft(config)).execution_plan.tasks) == 100
        assert len(_compile(rc_recursive_draft(config, unit_ids=(config.units[0].unit_id,),
                                              include_summary=False)).execution_plan.tasks) == 9


@pytest.mark.parametrize("phase,record_type", [
    ("source", rc_records.RCSourceOperationConfig),
    ("commit", rc_records.RCCommitmentOperationConfig),
])
def test_known_rc_configuration_unit_cannot_replace_selected_independent_unit(phase, record_type):
    config = default_chain_config()
    draft = rc_recursive_draft(config, unit_ids=(config.units[0].unit_id,), include_summary=False)
    changed = _replace_config(draft, "rc.u01." + phase, record_type, unit_id=config.units[1].unit_id)
    with pytest.raises(ValueError, match="scientific units.*study root"):
        _compile(changed)


@pytest.mark.parametrize("phase,record_type", [
    ("source", rc_records.RCSourceOperationConfig),
    ("deliver", rc_records.RCDeliveryOperationConfig),
])
def test_renamed_rc_native_operation_cannot_repeat_same_scientific_acquisition(phase, record_type):
    config = default_chain_config()
    draft = rc_recursive_draft(config, unit_ids=(config.units[0].unit_id,), include_summary=False)
    with pytest.raises(ValueError, match="repeats.*effect slot"):
        _compile(_alias(draft, "rc.u01." + phase, record_type))


def test_closed_rc_graph_omitting_a_whole_unit_cannot_keep_original_root_denominator():
    draft = rc_recursive_draft(default_chain_config())
    operations = tuple(value for value in draft.operations
                       if not value.node_id.startswith("rc.u01.") and value.node_id != "rc.summary")
    selected = {value.node_id for value in operations}
    requirements = tuple(value for value in draft.requirements if value.consumer_operation_id in selected)
    requirement_ids = {value.requirement_id for value in requirements}
    changed = replace(draft, operations=operations, selected_operation_ids=tuple(sorted(selected)),
        requirements=requirements, connections=tuple(value for value in draft.connections
                                                     if value.requirement_id in requirement_ids),
        suppliers=tuple(value for value in draft.suppliers if value.requirement_id in requirement_ids),
        links=tuple(value for value in draft.links if value.consumer_node_id in selected
                    and value.producer_node_id in selected))
    with pytest.raises(ValueError, match="incomplete assigned unit census"):
        _compile(changed)


def test_battery_checkpoint_cannot_acquire_wave_b_under_wave_a_scientific_root():
    changed = _replace_config(battery_wave_a_draft(), "battery.a.early.checkpoint",
                              BatteryOperationConfig, wave="B")
    with pytest.raises(ValueError, match="scientific units.*study root"):
        _compile(changed, battery=True)


@pytest.mark.parametrize("wave,changes", [("A", {}), ("B", {"future_word": "early1"})])
def test_battery_checkpoint_alias_and_unused_future_label_do_not_create_new_native_slot(wave, changes):
    draft = battery_wave_a_draft() if wave == "A" else _battery_b()
    node = next(value.node_id for value in draft.operations if value.selection.capability_key == "battery-recursive.checkpoint")
    with pytest.raises(ValueError, match="repeats.*effect slot"):
        _compile(_alias(draft, node, BatteryOperationConfig, **changes), battery=True)


def test_shared_battery_config_schema_cannot_change_registered_full_operation_to_soc():
    changed = _replace_config(battery_wave_a_draft(), "battery.a.early.full", BatteryOperationConfig,
                              operation=BatteryOperation.SOC)
    with pytest.raises(ValueError, match="registered operation"):
        _compile(changed, battery=True)


def test_battery_source_operand_must_be_explicitly_bound_by_actual_scientific_root():
    draft = battery_wave_a_draft()
    changed = replace(draft, development_study=replace(draft.development_study, scientific_operands=()))
    with pytest.raises(ValueError, match="scientific operands.*study root"):
        _compile(changed, battery=True)


def test_embedded_battery_claim_cannot_change_actual_authored_connection_before_contact():
    draft = battery_wave_a_draft()
    operation = next(value for value in draft.operations if value.node_id == "battery.a.early.assess")
    config = decode_canonical_bytes(operation.config_payload.encode(), BatteryOperationConfig,
                                    maximum_bytes=16 * 1024**2)
    changed = _replace_config(draft, operation.node_id, BatteryOperationConfig,
                              connection=replace(config.connection, claim_id="different.claim"))
    with pytest.raises(ValueError, match="actual authored requirement or connection"):
        _compile(changed, battery=True)


@pytest.mark.parametrize("projection", [lambda _: ["unit.one"], lambda _: ("unit.one", "unit.one"),
                                         lambda _: ("unit two",), lambda _: tuple("unit." + str(n) for n in range(257))])
def test_installed_unit_projection_is_bounded_typed_and_canonical(projection):
    from tests.runtime_platform.test_recursive_compiler import fixture
    draft, registrations, registry = fixture()
    registrations = (replace(registrations[0], scientific_unit_ids=projection), registrations[1])
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
                                implementation_commit="a" * 40)


@pytest.mark.parametrize("field", ["scientific_unit_ids", "native_effect_slot_ids"])
def test_native_registration_missing_scientific_projection_refuses_before_plan(field):
    config = default_chain_config()
    draft = rc_recursive_draft(config, unit_ids=(config.units[0].unit_id,), include_summary=False)
    registrations = tuple(replace(value, **{field: None}) if value.selection.capability_key.endswith(".source")
                          else value for value in rc_registrations())
    with pytest.raises(ValueError, match="lacks code-owned scientific unit and effect slot"):
        _compile(draft, registrations=registrations)


def test_independent_acquisition_groups_cannot_hide_missing_units_in_global_union():
    from tests.runtime_platform.test_recursive_compiler import fixture
    draft, registrations, registry = fixture()
    draft = replace(draft, development_study=replace(draft.development_study,
                                                    assigned_unit_ids=("unit.one", "unit.two")))
    registrations = tuple(replace(registration, native_effect=True, complete_unit_census=True,
        scientific_unit_ids=(lambda _: ("unit.one",)) if index == 0 else (lambda _: ("unit.two",)),
        native_effect_slot_ids=(lambda _: ("native.source.one",)) if index == 0 else (lambda _: ("native.use.two",)))
        for index, registration in enumerate(registrations))
    with pytest.raises(ValueError, match="incomplete assigned unit census"):
        compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
                                implementation_commit="a" * 40)


@pytest.mark.parametrize("retained", [False, True])
def test_root_validator_joins_exact_peer_design_bytes_before_effects_or_assessment_projection(retained):
    from tests.runtime_platform.test_recursive_compiler import fixture, UseConfig

    draft, registrations, registry = fixture()
    seen = []

    def validate(config, context):
        rows = {row.node_id: row for row in context.config_inputs}
        assert tuple(rows) == draft.selected_operation_ids
        assert rows["source"].record == config
        assert rows["use"].record_type is UseConfig
        for row in rows.values():
            assert row.payload == row.record.canonical_bytes()
            assert row.input_spec.expected_content_sha256 == row.record.fingerprint()
        assert context.links == draft.links
        if rows["use"].record.scalar != config.scalar:
            raise ValueError("FROZEN_PEER_SCIENTIFIC_OPERAND_MISMATCH")
        seen.append(context)

    registrations = (replace(registrations[0], scientific_root_validator=validate), registrations[1])

    def run(value):
        if retained:
            # No assessor output is available: every selected design validator
            # must still run before any scientific projection is considered.
            return project_recursive_assessments(draft=value, registrations=registrations, outputs={})
        return compile_recursive_wave(draft=value, registrations=registrations, registry=registry,
                                      implementation_commit="a" * 40)

    run(draft)
    assert len(seen) == 1
    changed = _replace_config(draft, "use", UseConfig, scalar=9)
    with pytest.raises(ValueError, match="FROZEN_PEER_SCIENTIFIC_OPERAND_MISMATCH"):
        run(changed)
    assert len(seen) == 1


def test_retained_root_context_refuses_unknown_peer_configuration_revision_before_projection():
    from tests.runtime_platform.test_recursive_compiler import fixture

    draft, registrations, _ = fixture()
    use = draft.operations[1]
    changed = replace(draft, operations=(draft.operations[0], replace(use,
        config_payload=use.config_payload.replace('"version":"1.0.0"', '"version":"2.0.0"'))))
    with pytest.raises(ValueError):
        project_recursive_assessments(draft=changed, registrations=registrations, outputs={})
