# SPDX-License-Identifier: MPL-2.0
"""Exposed authoring conformance; no genuine allocation or scientific fit."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_preparation import prepare_matrix_response_error
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import (
    FAMILIES, MatrixResponseErrorSpecification, selected_deanneal_specification,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection


PROTOCOL = (Path(__file__).parents[1] / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/candidate-design02.json").read_bytes()


def object_identity(name, marker="source"):
    return ObjectIdentity("fixture." + name, "empirical-lawhood/tests/exposed-matrix-source", "1.0.0",
        sha256((name + marker).encode()).hexdigest())


def selected():
    return selected_deanneal_specification(protocol_sha256=sha256(PROTOCOL).hexdigest())


def execution():
    return ExecutionSelection(workers=1, environment_id="fixture.locked-main", source_snapshot=object_identity("implementation"),
        output_root="/explicit/exposed-fixture-output")


def bank(selection, *, count=None, exposed=True, original_role=None, views=("fine", "primary")):
    source = object_identity(selection.source_key)
    count = selection.expected_units if count is None else count
    units = tuple(IndependentUnit("fixture.unit." + selection.role.lower() + f".{i:03}", source.object_id,
        FAMILIES[0], views, exposed) for i in range(count))
    role = selection.role.lower() if original_role is None else original_role
    return UnitAllocation("fixture.allocation." + selection.role.lower(), (source,), units,
        tuple(UnitRoleAssignment(unit.unit_id, role) for unit in units))


def inputs(specification):
    conformance = specification.evidence_scope == "EXPOSED_CONFORMANCE"
    return {population.source_key: bank(population,
        exposed=conformance or population.role == "TRAIN",
        original_role="development" if conformance or population.role == "TRAIN" else None)
        for population in specification.populations}


def prepare(specification, selected_inputs, **changes):
    arguments = dict(scientific_inputs=selected_inputs, execution=execution(), protocol_bytes=PROTOCOL)
    arguments.update(changes)
    return prepare_matrix_response_error(specification, **arguments)


def dependencies(result):
    return {row.code: row for row in result.dependencies}


def alternative():
    specification = selected()
    counts = {"TRAIN": 12, "CALIBRATION": 20, "EVALUATION": 8, "TRANSFER_NEARBY": 2, "TRANSFER_SHIFTED": 2}
    return replace(specification, specification_id="fixture.matrix.e3.alternative",
        populations=tuple(replace(population, expected_units=counts[population.role]) for population in specification.populations),
        assessment=replace(specification.assessment, minimum_usable_units=8), evidence_scope="EXPOSED_CONFORMANCE")


def test_selected_exact_science_and_count_derived_ranks_round_trip():
    specification = selected()
    assert dict((row.role, row.expected_units) for row in specification.populations) == {
        "TRAIN": 64, "CALIBRATION": 64, "EVALUATION": 64, "TRANSFER_NEARBY": 64, "TRANSFER_SHIFTED": 64}
    assert specification.measurement.endpoint_count == 15
    assert specification.measurement.target_discrepancy_tolerance == Decimal("0.0001")
    assert specification.assessment.improvement_margin == Decimal("0.0002")
    assert specification.assessment.minimum_usable_units == 58
    assert specification.calibration_rank == 62
    assert specification.minimum_successes == 43
    assert tuple((method.method_key, method.feature_count) for method in specification.methods) == (
        ("ALL_ORIGIN_RIDGE", 21), ("RAW_TRAIN_MEDIAN", 0), ("SPECTRAL_RIDGE", 13))
    assert decode_canonical_bytes(specification.canonical_bytes(), MatrixResponseErrorSpecification, maximum_bytes=None) == specification


def test_selected64_filters_original_whole_population_without_relabeling_its_bytes():
    # The source-bank projection is explicitly exposed. Protected preparation
    # now requires its complete original-publication carrier and source graph.
    specification = replace(selected(), evidence_scope="EXPOSED_CONFORMANCE")
    selected_inputs = inputs(specification)
    train_selection = specification.population("TRAIN")
    source = object_identity(train_selection.source_key)
    # The selected subset is a new immutable allocation; the source roster and
    # historical identifiers remain unchanged, including the other192 units.
    units = tuple(IndependentUnit(f"unit.cc1-grr-c2.h{i:03}", source.object_id,
        FAMILIES[0] if 64 <= i < 128 else FAMILIES[1], ("fine", "primary"), True) for i in range(256))
    original = UnitAllocation("fixture.original256.source-census", (source,), units,
        tuple(UnitRoleAssignment(unit.unit_id, "development") for unit in units))
    original_bytes = original.canonical_bytes()
    selected_inputs[train_selection.source_key] = original
    result = prepare(specification, selected_inputs)
    assert result.allocation is not None
    assert result.allocation.unit_ids("train") == tuple(f"unit.cc1-grr-c2.h{i:03}" for i in range(64, 128))
    assert original.canonical_bytes() == original_bytes
    assert len(original.units) == 256 and len(result.allocation.units) == 320
    assert result.draft is None and not result.executable and result.census.native_effect_count == 0
    assert {row.kind for row in result.dependencies} == {DependencyKind.EXTERNAL_INPUT}


def test_alternative_specification_uses_same_route_and_derives_complete_census():
    specification = alternative()
    result = prepare(specification, inputs(specification))
    assert result.allocation is not None and len(result.allocation.units) == 44
    assert dict(result.census.role_counts) == dict(result.census.resolved_role_counts) == {
        "train": 12, "calibration": 20, "evaluation": 8, "transfer_nearby": 2, "transfer_shifted": 2}
    assert specification.calibration_rank == 20 and specification.minimum_successes == 8
    assert dict(result.census.output_counts)["point-forecast-endpoints"] == 28 * 15 * 3
    assert {row.kind for row in result.dependencies} == {DependencyKind.EXTERNAL_INPUT}
    complete = replace(selected(), evidence_scope="EXPOSED_CONFORMANCE")
    assert result.allocation.identity != prepare(complete, inputs(complete)).allocation.identity
    assert result.draft is None and not result.executable


def test_missing_inputs_and_execution_choices_report_complete_dependencies_without_assignments():
    specification = selected()
    result = prepare(specification, {}, execution=ExecutionSelection(), protocol_bytes=None)
    findings = dependencies(result)
    assert {"matrix.e3.protocol.0", "matrix.e3.environment", "matrix.e3.source-snapshot", "matrix.e3.output-root",
        "matrix.e3.protected-selection"} <= set(findings)
    assert findings["matrix.e3.protected-selection"].source_key == "protected-selection"
    assert "matrix.e3.prospective-operation-lowering" not in findings
    assert sum(count for _, count in result.census.role_counts) == 320
    assert sum(count for _, count in result.census.resolved_role_counts) == 0
    assert result.allocation is None and result.draft is None


def test_explicit_original_unit_selection_preserves_membership_and_reports_unknown_ids():
    specification = alternative()
    selected_inputs = inputs(specification)
    train = specification.population("TRAIN")
    original = selected_inputs[train.source_key]
    original_bytes = original.canonical_bytes()
    chosen = tuple(unit.unit_id for unit in original.units[:6])
    selected_specification = replace(specification, populations=tuple(replace(row,
        expected_units=6, unit_ids=chosen) if row.role == "TRAIN" else row for row in specification.populations))
    result = prepare(selected_specification, selected_inputs)
    assert result.allocation.unit_ids("train") == chosen
    assert original.canonical_bytes() == original_bytes
    unknown = tuple(sorted((*chosen[:-1], "fixture.unit.not-in-original-source")))
    bad_specification = replace(selected_specification, populations=tuple(replace(row,
        unit_ids=unknown) if row.role == "TRAIN" else row for row in selected_specification.populations))
    refused = prepare(bad_specification, selected_inputs)
    assert refused.allocation is None
    assert train.selection_id + ".unit-selection" in dependencies(refused)
    assert train.selection_id + ".census" in dependencies(refused)
    assert dict(refused.census.resolved_role_counts)["train"] == 5
    wrong_family = replace(selected_specification, populations=tuple(replace(row,
        family_id=FAMILIES[1]) if row.role == "TRAIN" else row for row in selected_specification.populations))
    refused = prepare(wrong_family, selected_inputs)
    assert refused.allocation is None and train.selection_id + ".unit-selection" in dependencies(refused)
    assert dict(refused.census.resolved_role_counts)["train"] == 0


def test_surplus_missing_views_and_exposure_retained_in_invalid_complete_readout():
    specification = replace(selected(), evidence_scope="EXPOSED_CONFORMANCE")
    selected_inputs = inputs(specification)
    cal = specification.population("CALIBRATION")
    selected_inputs[cal.source_key] = bank(cal, count=65, exposed=False, views=("primary",))
    result = prepare(specification, selected_inputs)
    assert dict(result.census.resolved_role_counts)["calibration"] == 65
    assert {cal.selection_id + suffix for suffix in (".census", ".numerical-views", ".exposure")} <= set(dependencies(result))
    assert result.allocation is None


def test_overlapping_unit_and_crossed_roles_refuse_before_any_lowering():
    specification = alternative()
    selected_inputs = inputs(specification)
    train = specification.population("TRAIN")
    cal = specification.population("CALIBRATION")
    supplied = selected_inputs[cal.source_key]
    overlap_id = selected_inputs[train.source_key].units[0].unit_id
    units = tuple(sorted((replace(supplied.units[0], unit_id=overlap_id), *supplied.units[1:]), key=lambda unit: unit.unit_id))
    selected_inputs[cal.source_key] = replace(supplied, units=units,
        roles=tuple(UnitRoleAssignment(unit.unit_id, "evaluation") for unit in units))
    result = prepare(specification, selected_inputs)
    assert cal.selection_id + ".roles" in dependencies(result)
    assert any(code.endswith(".overlap." + overlap_id) for code in dependencies(result))
    assert result.allocation is None and result.draft is None


def test_unachievable_criterion_retains_denominator_as_a_design_dependency():
    specification = alternative()
    specification = replace(specification,
        populations=tuple(replace(population, expected_units=7) if population.role == "EVALUATION" else population
            for population in specification.populations),
        assessment=replace(specification.assessment, minimum_usable_units=7))
    result = prepare(specification, inputs(specification))
    assert specification.minimum_successes == 8
    assert "matrix.e3.evaluation-resolution" in dependencies(result)
    assert dict(result.census.role_counts)["evaluation"] == 7


def test_protocol_hash_mismatch_and_semantic_mutation_remain_distinct_dependencies():
    specification = selected()
    result = prepare(specification, inputs(specification), protocol_bytes=PROTOCOL + b" ")
    assert "SHA256" in dependencies(result)["matrix.e3.protocol.0"].detail
    changed = PROTOCOL.replace(b'"meaningful_paired_improvement": "0.0002"', b'"meaningful_paired_improvement": "0.002"')
    assert changed != PROTOCOL
    changed_specification = replace(specification, protocol_sha256=sha256(changed).hexdigest())
    result = prepare(changed_specification, inputs(changed_specification), protocol_bytes=changed)
    assert "exact primary criterion" in dependencies(result)["matrix.e3.protocol.0"].detail


@pytest.mark.parametrize("action_index", (0, 3))
def test_changed_actuator_normalization_is_reported_before_execution(action_index):
    document = json.loads(PROTOCOL)
    actions = document["target"]["original_mathematical_protocol"]["value"]["action_scales"]
    assert actions[action_index]["value"]["force_norm"] == {"decimal": "1"}
    actions[action_index]["value"]["force_norm"] = {"decimal": "2"}
    changed = json.dumps(document, sort_keys=True).encode()
    specification = replace(selected(), protocol_sha256=sha256(changed).hexdigest())
    result = prepare(specification, inputs(specification), protocol_bytes=changed)
    protocol_dependencies = tuple(row for row in result.dependencies if row.code.startswith("matrix.e3.protocol."))
    assert len(protocol_dependencies) == 1
    assert protocol_dependencies[0].kind is DependencyKind.EXTERNAL_INPUT
    assert protocol_dependencies[0].detail == "prediction protocol changes action menu"
    assert not result.executable and result.draft is None
    # The installed protected graph reports its prospective native census.
    # A planned effect count does not mean preparation entered those effects.
    assert result.census.native_effect_count == 256


@pytest.mark.parametrize("change", ("margin", "view", "ridge", "reserve", "minimum", "roles"))
def test_unsupported_selected_science_refuses_at_specification_boundary(change):
    specification = selected()
    with pytest.raises(ValueError):
        if change == "margin":
            replace(specification.assessment, improvement_margin=Decimal("0.002"))
        elif change == "view":
            replace(specification.measurement, fine_timestep=Decimal("0.00025"))
        elif change == "ridge":
            replace(specification.methods[0], ridge_lambda=Decimal(2))
        elif change == "reserve":
            replace(specification, reserve_before_training_load=False)
        elif change == "minimum":
            replace(specification, assessment=replace(specification.assessment, minimum_usable_units=65))
        else:
            replace(specification, populations=specification.populations[:-1])
