# SPDX-License-Identifier: MPL-2.0
"""Complete exposed E4 metadata controls; no native work or authority is created."""

from collections import Counter
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.recursive_compiler import (
    DecodedRecursiveConfigInput,
    RecursiveScientificRootContext,
    RecursiveScientificRootPreparationContext,
    validate_recursive_scientific_roots,
)
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer  # noqa: F401 - shared disclosed metadata fixtures


@pytest.fixture(scope="module")
def scientific_inputs(selected_bridge):  # noqa: F811
    """Keep all 32 groups, all nine coordinates each, and all 3,458 nodes."""
    fixture = selected_bridge
    configs, external, links, _, _ = owner.contracts(
        fixture.programme, fixture.bank, fixture.evidence.identity,
        len(fixture.evidence.canonical_bytes()),
        produced_input_parents=fixture.evidence.produced_input_parents,
     secondary_readout=fixture.secondary_readout)
    registrations = {
        value.capability_key.rsplit(".", 1)[-1]: value.registration()
        for value in owner.operation_declarations()
    }
    return dict(
        root=owner.development_root(
            fixture.programme, fixture.bank, "study.selected-e4.scientific-preparation",
            produced_input_parents=fixture.evidence.produced_input_parents,
         secondary_readout=fixture.secondary_readout),
        config_inputs=tuple(
            DecodedRecursiveConfigInput(node, config.config_id, config.canonical_bytes(), config, type(config))
            for node, config in configs
        ),
        registrations_for_node={node: registrations[config.phase] for node, config in configs},
        requirements=(), connections=(), qualifications=(), known_design_inputs=(),
        links=links, external_inputs=external,
    )


def _batch(arguments):
    selected = {}
    for row in arguments["config_inputs"]:
        registration = arguments["registrations_for_node"][row.node_id]
        selected.setdefault(registration.selection.selection_id, set()).update(owner.units(row.record))
    return RecursiveScientificRootPreparationContext(
        arguments["root"], arguments["config_inputs"], arguments["requirements"],
        arguments["connections"], arguments["links"], arguments["external_inputs"],
        arguments["qualifications"], arguments["known_design_inputs"],
        {selection: tuple(sorted(units)) for selection, units in selected.items()},
    )


def _context(arguments, batch, preparation, row):
    registration = arguments["registrations_for_node"][row.node_id]
    return RecursiveScientificRootContext(
        batch.root, row.node_id, registration.stage, registration.outcome_access,
        registration.visibility_ceiling, owner.units(row.record),
        batch.selected_unit_ids_by_selection[registration.selection.selection_id],
        registration.complete_unit_census, batch.requirements, batch.connections,
        batch.qualifications, batch.known_design_inputs, batch.config_inputs,
        batch.links, batch.external_inputs, preparation,
    )


def _with_callbacks(arguments, *, validator, preparer=None):
    return {
        **arguments,
        "registrations_for_node": {
            node: replace(registration, scientific_root_validator=validator,
                scientific_root_preparer=(registration.scientific_root_preparer if preparer is None else preparer))
            for node, registration in arguments["registrations_for_node"].items()
        },
    }


def test_complete_owner_prepares_once_and_validates_every_selected_node(
    scientific_inputs, selected_bridge, monkeypatch,  # noqa: F811
):
    arguments = scientific_inputs
    fixture = selected_bridge
    assert len(arguments["config_inputs"]) == 3458
    assert len(fixture.programme.cases) == len(fixture.bank.sources) == 288
    assert len(fixture.programme.group_ids) == 32
    assert set(Counter(case.independent_group_id for case in fixture.programme.cases).values()) == {9}
    assert len(fixture.bank.reservation.allocation.coordinates) == 36
    assert all(len(root.streams) == 4 for root in fixture.bank.reservation.allocation.roots)

    calls, accepted, prepared_values = Counter(), [], []
    original_contracts, original_root = owner.contracts, owner.development_root

    def counted_contracts(*args, **kwargs):
        calls["contracts"] += 1
        return original_contracts(*args, **kwargs)

    def counted_root(*args, **kwargs):
        calls["development_root"] += 1
        return original_root(*args, **kwargs)

    def prepare(batch):
        calls["preparer"] += 1
        prepared = owner.scientific_root_preparer(batch)
        assert type(prepared) is owner.SelectedE3E4ScientificPreparation
        assert prepared.batch is batch
        assert len(prepared.node_configs) == 3458
        assert prepared.group_ids == fixture.programme.group_ids
        assert not hasattr(prepared, "canonical_bytes")
        with pytest.raises(TypeError):
            prepared.node_configs["foreign.node"] = batch.config_inputs[0].record
        with pytest.raises(TypeError):
            prepared.selected_units_by_phase["entry"] = ()
        prepared_values.append(prepared)
        return prepared

    def validate(config, context):
        assert context.scientific_preparation is prepared_values[0]
        assert owner.scientific_root_validator(config, context) is None
        accepted.append(context.node_id)

    monkeypatch.setattr(owner, "contracts", counted_contracts)
    monkeypatch.setattr(owner, "development_root", counted_root)
    validate_recursive_scientific_roots(**_with_callbacks(arguments, validator=validate, preparer=prepare))
    assert calls == {"contracts": 1, "development_root": 1, "preparer": 1}
    assert accepted == [row.node_id for row in arguments["config_inputs"]]
    assert len(accepted) == len(set(accepted)) == 3458


def _changed_census(arguments, damage):
    changed = dict(arguments)
    rows, links, external = (arguments[name] for name in ("config_inputs", "links", "external_inputs"))
    if damage == "config-remove":
        changed["config_inputs"] = rows[:-1]
    elif damage == "config-add":
        changed["config_inputs"] = (*rows, rows[-1])
    elif damage == "config-substitute":
        index, row = next((index, row) for index, row in enumerate(rows) if row.record.phase == "account")
        protocol = replace(row.record.protocol, protocol_id=row.record.protocol.protocol_id + ".substituted")
        config = replace(row.record, protocol=protocol)
        changed["config_inputs"] = (*rows[:index], replace(row, record=config, payload=config.canonical_bytes()), *rows[index + 1:])
    elif damage == "coordinate-remove":
        row = next(row for row in rows if row.record.phase == "prefix")
        root_id = row.record.source.root_id
        changed["config_inputs"] = tuple(value for value in rows
            if not value.node_id.startswith(owner.NAMESPACE + "." + root_id + "."))
        assert len(changed["config_inputs"]) == len(rows) - 12
    elif damage == "link-remove":
        changed["links"] = links[:-1]
    elif damage == "link-add":
        changed["links"] = (*links, replace(links[-1], edge_id=links[-1].edge_id + ".extra"))
    elif damage == "link-substitute":
        changed["links"] = (*links[:-1], replace(links[-1], edge_id=links[-1].edge_id + ".substituted"))
    elif damage == "external-remove":
        changed["external_inputs"] = external[:-1]
    elif damage == "external-add":
        changed["external_inputs"] = (*external, replace(external[-1], input_id=external[-1].input_id + ".extra"))
    elif damage == "external-substitute":
        changed["external_inputs"] = (*external[:-1], replace(external[-1], logical_artifact_id=external[-1].logical_artifact_id + ".substituted"))
    elif damage == "stream-substitute":
        stream = next(link.external_input_id for link in links if link.consumer_input_id.startswith("streams."))
        changed["external_inputs"] = tuple(replace(value, expected_content_sha256="f" * 64)
            if value.input_id == stream else value for value in external)
        assert changed["external_inputs"] != external
    elif damage == "root-operands":
        changed["root"] = replace(arguments["root"], scientific_operands=arguments["root"].scientific_operands[:-1])
    elif damage == "root-groups":
        changed["root"] = replace(arguments["root"], assigned_unit_ids=arguments["root"].assigned_unit_ids[:-1])
    else:
        raise AssertionError(damage)
    return changed


@pytest.mark.parametrize("damage", (
    "config-remove", "config-add", "config-substitute", "coordinate-remove",
    "link-remove", "link-add", "link-substitute",
    "external-remove", "external-add", "external-substitute", "stream-substitute",
    "root-operands", "root-groups",
))
def test_complete_owner_refuses_census_changes_before_any_node(scientific_inputs, damage):
    accepted = []

    def validate(config, context):
        accepted.append(context.node_id)
        return owner.scientific_root_validator(config, context)

    changed = _changed_census(scientific_inputs, damage)
    with pytest.raises(ValueError, match="graph|census|whole-programme"):
        validate_recursive_scientific_roots(**_with_callbacks(changed, validator=validate))
    assert accepted == []


def test_complete_owner_refuses_a_thinned_selected_group_projection_before_any_node(scientific_inputs):
    arguments = scientific_inputs
    missing_group = arguments["root"].assigned_unit_ids[-1]
    accepted = []

    def without_group(config):
        return tuple(value for value in owner.units(config) if value != missing_group)

    def validate(config, context):
        accepted.append(context.node_id)
        return owner.scientific_root_validator(config, context)

    registrations = {
        node: replace(registration, scientific_root_validator=validate,
            scientific_unit_ids=(without_group if registration.selection.capability_key.endswith(".account")
                else registration.scientific_unit_ids))
        for node, registration in arguments["registrations_for_node"].items()
    }
    with pytest.raises(ValueError, match="whole-group census"):
        validate_recursive_scientific_roots(**{**arguments, "registrations_for_node": registrations})
    assert accepted == []


def test_later_validation_reprepares_and_refuses_changed_inputs(scientific_inputs):
    preparations, accepted = [], []

    def prepare(batch):
        preparations.append(batch)
        return owner.scientific_root_preparer(batch)

    def validate(config, context):
        accepted.append(context.node_id)
        return owner.scientific_root_validator(config, context)

    arguments = _with_callbacks(scientific_inputs, validator=validate, preparer=prepare)
    validate_recursive_scientific_roots(**arguments)
    assert len(accepted) == 3458
    accepted.clear()
    with pytest.raises(ValueError, match="graph|census"):
        validate_recursive_scientific_roots(**_changed_census(arguments, "stream-substitute"))
    assert len(preparations) == 2 and preparations[0] is not preparations[1]
    assert accepted == []


@pytest.fixture(scope="module")
def prepared_inputs(scientific_inputs):
    batch = _batch(scientific_inputs)
    prepared = owner.scientific_root_preparer(batch)
    row = next(row for row in batch.config_inputs if row.record.phase == "prefix")
    return batch, prepared, row, _context(scientific_inputs, batch, prepared, row)


@pytest.mark.parametrize("damage", (
    "no-preparation", "foreign-preparation", "other-invocation", "root", "configs", "links", "external",
    "requirements", "connections", "qualifications", "known-design-inputs",
    "node", "equal-config-copy", "stage", "unit", "selected-units", "native-census", "access", "visibility",
))
def test_direct_node_refuses_foreign_preparation_or_context(prepared_inputs, damage):
    batch, prepared, row, context = prepared_inputs
    config = row.record
    if damage == "no-preparation":
        context = replace(context, scientific_preparation=None)
    elif damage == "foreign-preparation":
        context = replace(context, scientific_preparation=object())
    elif damage == "other-invocation":
        other = replace(batch, config_inputs=tuple(list(batch.config_inputs)))
        context = replace(context, scientific_preparation=owner.scientific_root_preparer(other))
    elif damage == "root":
        context = replace(context, root=replace(batch.root, study_id=batch.root.study_id + ".other"))
    elif damage == "configs":
        context = replace(context, config_inputs=tuple(list(batch.config_inputs)))
    elif damage == "links":
        context = replace(context, links=tuple(list(batch.links)))
    elif damage == "external":
        context = replace(context, external_inputs=tuple(list(batch.external_inputs)))
    elif damage in ("requirements", "connections", "qualifications", "known-design-inputs"):
        # A foreign nonempty global tuple must be refused without interpreting
        # its body or treating it as scientific evidence.
        context = replace(context, **{damage.replace("-", "_"): (batch.root,)})
    elif damage == "node":
        context = replace(context, node_id=next(value.node_id for value in batch.config_inputs if value is not row))
    elif damage == "equal-config-copy":
        config = replace(config)
        assert config == row.record and config is not row.record
    elif damage == "stage":
        context = replace(context, stage=owner.stage("reduce"))
    elif damage == "unit":
        context = replace(context, unit_ids=())
    elif damage == "selected-units":
        context = replace(context, selected_unit_ids=tuple(list(context.selected_unit_ids)))
    elif damage == "native-census":
        context = replace(context, complete_unit_census=False)
    elif damage == "access":
        context = replace(context, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    elif damage == "visibility":
        context = replace(context, visibility_ceiling=VisibilityCeiling.PROSPECTIVE)
    else:
        raise AssertionError(damage)
    with pytest.raises((TypeError, ValueError), match="preparation|prepared invocation|graph|census"):
        owner.scientific_root_validator(config, context)
    assert prepared.batch is batch
