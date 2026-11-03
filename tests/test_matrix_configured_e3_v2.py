# SPDX-License-Identifier: MPL-2.0
"""Configured exposed E3 controls; no protected-native/qualification claim."""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_specification as records
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_inputs as inputs_owner
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_preparation as preparation_owner
from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response import e3_numerical_methods as numerical
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, load_experiment_specification, prepare_experiment
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from tests.test_matrix_experiment_methods import fixture, bank, selected_input_records, run_methods
from tests.test_matrix_experiment_specification import execution

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "matrix.response-error.origin-only.configured-v2"


def configured_case(*, penalty=Decimal("2"), alpha=Decimal("0.2"), margin=Decimal("0.001")):
    legacy, sources, allocation, methods = fixture(train_count=8, cal_count=8, eval_count=8)
    pins = {role: ObjectIdentity("coordinate.disclosed." + role.lower(), MatrixParameterCoordinate.SCHEMA,
        MatrixParameterCoordinate.VERSION, sha256(role.encode()).hexdigest()) for role in records.POPULATION_ROLES}
    estimators = tuple(records.ConfiguredE3Estimator(row.method_key, row.feature_blocks,
        None if row.method_key == "RAW_TRAIN_MEDIAN" else penalty, False,
        fit_scale=row.fit_scale, estimation_rule=row.estimation_rule) for row in legacy.methods)
    specification = records.ConfiguredMatrixResponseErrorSpecification("experiment.configured-e3.disclosed",
        "Disclosed configurable paired source-bank controls", records.ConfiguredE3Protocol("protocol.configured-e3.disclosed", records.ConfiguredE3Measurement(
            primary_description=legacy.measurement.primary_description, primary_horizon=legacy.measurement.primary_horizon,
            target_discrepancy_tolerance=legacy.measurement.target_discrepancy_tolerance)),
        legacy.populations, methods=estimators, assessment=records.ConfiguredE3Assessment(
            improvement_margin=margin, minimum_usable_units=8, null_success_numerator=1, null_success_denominator=2,
            alpha_numerator=1, alpha_denominator=240, comparison_ids=records.FAMILY_IDS), calibration_alpha=alpha,
        role_coordinates=tuple((role, pins[role]) for role in records.POPULATION_ROLES), calibration_target_view="MAX_PAIRED_VIEWS")
    source_by_unit = {feature.unit_id: feature.native_source for block in methods.features for feature in block.rows}
    identities = {pin.object_id: pin for pin in allocation.sources}
    roles = {row.unit_id: row.role.upper() for row in allocation.roles}
    coordinates = records.ConfiguredE3CoordinateCensus("coordinates.configured-e3.disclosed", tuple(
        (unit.unit_id, source_by_unit.get(unit.unit_id, identities[unit.source_id]), pins[roles[unit.unit_id]])
        for unit in allocation.units))
    budget = ResourceBudget(1, 2 * 1024**3, 0, None, 128 * 1024**2, 64 * 1024**2)
    resources = records.ConfiguredE3Resources("resources.configured-e3.disclosed",
        tuple((phase, budget) for phase in records.OPERATIONS))
    selected = {**selected_input_records(sources, methods), "coordinate-census": coordinates, "resources": resources}
    return specification, selected


def prepared_case(**parameters):
    specification, selected = configured_case(**parameters)
    bound = inputs_owner.bind_matrix_response_inputs(specification, selected)
    prepared = prepare_experiment(specification, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=replace(execution(), workers=1))
    assert prepared.executable, tuple((row.code, row.detail) for row in prepared.dependencies)
    feature_banks = tuple(record for _, record in prepared.input_records if type(record) is science.MatrixE3FeatureBank)
    # Complete selected query features/outcomes are individual inputs after lowering.
    projected = science.project_method_inputs(specification, prepared.allocation, bound.scientific_inputs, bound.method_inputs.banks)
    assert feature_banks
    return specification, selected, prepared, projected


def test_v2_roundtrip_and_legacy_parameter_refusals_preserve_original_bytes():
    specification, _ = configured_case()
    assert specification.VERSION == "3.0.0"
    assert decode_canonical_bytes(specification.canonical_bytes(), type(specification), maximum_bytes=None) == specification
    legacy, _, _, _ = fixture()
    before = legacy.canonical_bytes()
    with pytest.raises(ValueError):
        replace(legacy, calibration_alpha=Decimal("0.2"))
    with pytest.raises(ValueError):
        replace(legacy.methods[0], ridge_lambda=Decimal("2"))
    with pytest.raises(ValueError):
        replace(legacy.assessment, improvement_margin=Decimal("0.001"))
    assert before == legacy.canonical_bytes()


@pytest.mark.parametrize("penalty", (Decimal(0), Decimal(-1), Decimal("NaN"), Decimal("Infinity"), Decimal("1e-10000")))
def test_unsupported_or_unrepresentable_penalty_refuses(penalty):
    with pytest.raises(ValueError):
        configured_case(penalty=penalty)


@pytest.mark.parametrize("alpha", (Decimal(0), Decimal(1), Decimal("NaN")))
def test_calibration_alpha_requires_explicit_supported_probability(alpha):
    with pytest.raises(ValueError):
        configured_case(alpha=alpha)


def test_complete_lowering_and_cold_validation_freeze_original_coordinate_and_budget_inputs():
    specification, selected, prepared, _ = prepared_case()
    assert len(prepared.draft.operations) == 37
    assert all(row.selection.capability_key.startswith(bindings.NAMESPACE + ".") for row in prepared.draft.operations)
    preparation_owner.validate_matrix_response_instance(specification=specification, allocation=prepared.allocation,
        draft=prepared.draft, source_records=prepared.design_records)
    registrations = {row.registration().selection.selection_id: row.registration() for row in bindings.operation_declarations()}
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
    for operation in prepared.draft.operations:
        config = decode_recursive_config_input(operation, registrations[operation.selection.selection_id]).record
        assert config.resource_budget == operation.resource_budget == selected["resources"].budget(config.operation)
        assert config.specification == specification.identity and config.specification.object_version == "3.0.0"
        assert config.coordinate_census == ObjectIdentity.from_record(selected["coordinate-census"].record_id, selected["coordinate-census"])
    coordinates = selected["coordinate-census"]
    changed = replace(coordinates, assignments=tuple((unit, source, specification.role_coordinates[-1][1])
        if index == 0 else (unit, source, coordinate) for index, (unit, source, coordinate) in enumerate(coordinates.assignments)))
    with pytest.raises(ValueError):
        preparation_owner.validate_matrix_response_instance(specification=specification, allocation=prepared.allocation,
            draft=prepared.draft, source_records=(("coordinate-census", changed), ("resources", selected["resources"])))


def test_actual_shared_math_consumes_penalty_calibration_alpha_and_strict_margin():
    specification, _, prepared, methods = prepared_case(penalty=Decimal("2"), alpha=Decimal("0.2"))
    models, _, _, calibrated, _, _, assessed = run_methods(specification, prepared.allocation, methods)
    assert models.specification == specification.identity and assessed.specification == specification.identity
    assert calibrated.rank == specification.calibration_rank == 8
    changed = replace(specification, methods=tuple(replace(row, ridge_lambda=Decimal("4"))
        if row.ridge_lambda is not None else row for row in specification.methods), calibration_alpha=Decimal("0.4"))
    changed_models = science.fit_models(changed, prepared.allocation, bank(methods, "features", "train"),
        bank(methods, "outcomes", "train"), record_id="models.configured-e3.other-penalty")
    assert changed_models.models[2].ridge_parameters != models.models[2].ridge_parameters
    assert changed.calibration_rank != calibrated.rank
    outcome = bank(methods, "outcomes", "evaluation").rows[0]
    points = {"ALL_ORIGIN_RIDGE": (Decimal(2),) * 15, "RAW_TRAIN_MEDIAN": (Decimal(2),) * 15,
        "SPECTRAL_RIDGE": tuple(numerical.log_error(value) for value in outcome.view("primary").errors)}
    assert numerical.paired_root_decision(specification, points, outcome, 14, ())[1] is True
    strict = replace(specification, assessment=replace(specification.assessment, improvement_margin=Decimal(10)))
    assert numerical.paired_root_decision(strict, points, outcome, 14, ())[1] is False
    assert numerical.paired_root_decision(strict, points, outcome, 14, ())[0] is True


def _source_file(directory, specification, selected):
    directory.mkdir()
    bindings = []
    for index, (key, record) in enumerate(sorted(selected.items())):
        member = directory / (str(index) + ".json")
        member.write_bytes(record.canonical_bytes())
        bindings.append(ExperimentInputBinding(key, ObjectIdentity.from_record("input.configured." + key, record),
            member.name, len(record.canonical_bytes())))
    selection = ExperimentInputSelection("inputs.configured-e3.disclosed", PROTOCOL, tuple(bindings))
    source = directory / "sources.json"
    source.write_bytes(selection.canonical_bytes())
    specification_path = directory / "specification.json"
    specification_path.write_bytes(specification.canonical_bytes())
    return source, specification_path


def test_actual_public_v2_author_workers_cold_read_and_zero_entry_recovery(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_authoring, recursive_execution
    from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
    from empirical_lawhood.api.configuration import validate_configuration
    from empirical_lawhood.api.recursive_operations import operation_factories
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from tests.test_recursive_public_service import _plane

    specification, selected = configured_case()
    assert len(tuple(row for row in operation_factories() if row.manifest.capability_key.startswith(bindings.NAMESPACE + "."))) == 6
    source, spec_path = _source_file(tmp_path / "source-inputs", specification, selected)
    assert load_experiment_specification(spec_path) == specification
    assert validate_configuration(spec_path, consumer="matrix-response-experiment-v2")["consumer_byte_ready"]
    resolved = load_experiment_inputs(specification, source)
    plane = _plane(tmp_path / "guarded")
    available = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count() or 1
    workers = min(4, available)
    snapshot = recursive_authoring.implementation_binding(ROOT)
    selected_execution = replace(execution(), workers=workers,
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", snapshot),
        output_root=plane.root.contract.canonical_path)
    prepared = prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=selected_execution)
    assert prepared.executable, prepared.dependencies
    directory = Path(plane.root.contract.canonical_path) / "configured"
    authored = author_prepared_experiment(preparation=prepared, project_root=ROOT, artifact_writer=plane, output_dir=directory)
    assert authored["task_count"] == 37
    report = recursive_execution.run_recursive_wave(directory=directory, project_root=ROOT,
        artifact_writer=plane, maximum_parallel_tasks=workers)
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
    retained, products, _, _ = recursive_execution.read_recursive_wave(directory=directory, artifact_writer=plane,
        terminal_product_format="references", include_products=True)
    assert retained["status"] == "SUCCEEDED" and len(products["receipts"]) == 37
    result = next(record for values in products["records"].values() for record in values.values()
        if type(record) is science.MatrixE3Assessment)
    assert result.specification == specification.identity and result.specification.object_version == "3.0.0"
    assert len(result.decisions) == 8 and result.qualification == "NOT_ESTABLISHED"
    for method in ("execute", "execute_deadline_free"):
        monkeypatch.setattr(LocalProcessExecutor, method, lambda *_args, **_kw: pytest.fail("completed V2 reran work"))
    recovered = recursive_execution.run_recursive_wave(directory=directory, project_root=ROOT,
        artifact_writer=plane, maximum_parallel_tasks=workers)
    assert recovered["status"] == "SUCCEEDED" and recovered["new_native_contact_count"] == 0


def test_parameter_support_does_not_advertise_unimplemented_measurement_or_native_authority():
    specification, _ = configured_case()
    with pytest.raises(ValueError):
        replace(specification.protocol.measurement, q=3)
    with pytest.raises(ValueError):
        replace(specification, evidence_scope="PROSPECTIVE_REQUIRED")
    with pytest.raises(ValueError):
        replace(specification, calibration_target_view="UNDECLARED")
    with pytest.raises(ValueError):
        replace(specification, assessment=replace(specification.assessment, comparison_ids=specification.assessment.comparison_ids[:-1]))


def test_missing_selections_and_foreign_coordinate_sources_refuse_before_lowering():
    specification, selected = configured_case()
    partial = dict(selected)
    del partial["resources"]
    bound = inputs_owner.bind_matrix_response_inputs(specification, partial)
    prepared = prepare_experiment(specification, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=replace(execution(), workers=1))
    assert not prepared.executable and "matrix.e3.resources" in {row.code for row in prepared.dependencies}
    census = selected["coordinate-census"]
    unit = next(iter(bank(bound.method_inputs.banks, "features", "train").rows)).unit_id
    changed = replace(census, assignments=tuple((name, replace(source, object_fingerprint="f" * 64), coordinate)
        if name == unit else (name, source, coordinate) for name, source, coordinate in census.assignments))
    selected["coordinate-census"] = changed
    bound = inputs_owner.bind_matrix_response_inputs(specification, selected)
    refused = prepare_experiment(specification, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=replace(execution(), workers=1))
    assert not refused.executable and "matrix.e3.coordinates.invalid" in {row.code for row in refused.dependencies}


def test_installed_v2_operations_require_finite_reservations_without_sidecar_shortcuts():
    _, _, prepared, _ = prepared_case()
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
    operation = prepared.draft.operations[0]
    registration = next(row.registration() for row in bindings.operation_declarations()
        if row.registration().selection == operation.selection)
    config = decode_recursive_config_input(operation, registration).record
    for budget in (replace(config.resource_budget, memory_bytes=None),
                   replace(config.resource_budget, source_scan_bytes=None),
                   replace(config.resource_budget, output_bytes=0)):
        with pytest.raises(ValueError):
            replace(config, resource_budget=budget)


@pytest.mark.parametrize("field,value", (("null_success_numerator", True), ("null_success_denominator", 0),
    ("null_success_numerator", -1), ("null_success_numerator", 3), ("alpha_numerator", False),
    ("alpha_numerator", 0), ("alpha_denominator", 0), ("alpha_numerator", 240)))
def test_assessment_rejects_malformed_exact_probability_operands(field, value):
    specification, _ = configured_case()
    with pytest.raises(ValueError):
        replace(specification.assessment, **{field: value})


def test_assessment_uses_explicit_probabilities_and_retains_complete_programme_slots():
    specification, _ = configured_case()
    assert specification.assessment.comparison_slots == len(records.FAMILY_IDS)
    alternative = replace(specification, assessment=replace(specification.assessment,
        null_success_numerator=1, null_success_denominator=3, alpha_numerator=1, alpha_denominator=120))
    assert alternative.minimum_successes != specification.minimum_successes
    for census in (records.FAMILY_IDS[:-1], (*records.FAMILY_IDS, records.FAMILY_IDS[-1]),
            ("invented.slot", *records.FAMILY_IDS[1:])):
        with pytest.raises(ValueError):
            replace(specification.assessment, comparison_ids=census)
    with pytest.raises(ValueError):
        replace(specification.assessment, alpha_numerator=1, alpha_denominator=2)


def test_explicit_intercept_penalty_changes_actual_fit_and_rejects_nonboolean():
    specification, _, prepared, methods = prepared_case()
    unpenalized = science.fit_models(specification, prepared.allocation, bank(methods, "features", "train"),
        bank(methods, "outcomes", "train"), record_id="models.unpenalized-intercept")
    penalized_spec = replace(specification, methods=tuple(replace(row, penalize_intercept=True)
        if row.ridge_lambda is not None else row for row in specification.methods))
    penalized = science.fit_models(penalized_spec, prepared.allocation, bank(methods, "features", "train"),
        bank(methods, "outcomes", "train"), record_id="models.penalized-intercept")
    assert penalized.models[2].ridge_parameters != unpenalized.models[2].ridge_parameters
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURE_BLOCKS
    assert specification.methods[0].feature_count == sum(len(FEATURE_BLOCKS[block])
        for block in specification.methods[0].feature_blocks)
    with pytest.raises(ValueError):
        replace(specification.methods[0], penalize_intercept=1)
    with pytest.raises(ValueError):
        replace(specification.methods[1], penalize_intercept=True)


def test_supported_primary_endpoint_and_tolerance_reach_original_computation():
    specification, _, prepared, methods = prepared_case()
    selected_measurement = replace(specification.measurement, primary_description="SPECTRA", primary_horizon=16,
        target_discrepancy_tolerance=Decimal("0.01"))
    alternative = replace(specification, protocol=replace(specification.protocol, measurement=selected_measurement))
    products = run_methods(alternative, prepared.allocation, methods)
    assessed = products[-1]
    assert assessed.specification == alternative.identity
    forecasts = products[-2]
    index = science.ENDPOINTS.index((selected_measurement.primary_description, selected_measurement.primary_horizon))
    first = assessed.decisions[0]
    forecast = next(row for row in forecasts if row.feature.unit_id == first.unit_id)
    outcome = next(row for row in bank(methods, "outcomes", "evaluation").rows if row.unit_id == first.unit_id)
    assert first.success == numerical.paired_root_decision(alternative, dict(forecast.log_points), outcome, index,
        numerical.outcome_reasons(alternative, outcome))[1]
    original_outcome = bank(methods, "outcomes", "evaluation").rows[0]
    views = tuple(replace(view, errors=tuple(value + Decimal("0.001") if value is not None else None
        for value in original_outcome.view("primary").errors)) if view.view_id == "fine" else view
        for view in original_outcome.views)
    perturbed = replace(original_outcome, views=views)
    assert "TARGET_VIEW_DISCREPANCY" in numerical.outcome_reasons(specification, perturbed)
    assert "TARGET_VIEW_DISCREPANCY" not in numerical.outcome_reasons(alternative, perturbed)
    for change in ({"primary_horizon": True}, {"primary_horizon": 12}, {"primary_description": "UNKNOWN"},
            {"target_discrepancy_tolerance": Decimal(0)}, {"target_discrepancy_tolerance": Decimal("Infinity")}):
        with pytest.raises(ValueError):
            replace(selected_measurement, **change)


@pytest.mark.parametrize("field", ("cpu_cores", "memory_bytes", "gpu_devices", "wall_time_seconds", "source_scan_bytes", "output_bytes"))
def test_all_configured_integer_resource_operands_refuse_boolean(field):
    specification, selected = configured_case()
    budget = selected["resources"].phase_budgets[0][1]
    # ResourceBudget's historical constructor accepts some booleans; the new
    # configured boundary must independently reject every such operand.
    values = {name: getattr(budget, name) for name in budget.__dataclass_fields__ if name not in {"SCHEMA", "VERSION"}}
    values[field] = False if field == "gpu_devices" else True
    bad = ResourceBudget(**values)
    with pytest.raises(ValueError):
        replace(selected["resources"], phase_budgets=tuple((phase, bad) for phase in records.OPERATIONS))
    del specification


def test_paired15_registered_fixed_geometry_preserves_historical_measurement_bytes():
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseMeasurementSelection

    specification, _ = configured_case()
    selected = specification.protocol.measurement
    before = selected.canonical_bytes()
    legacy = MatrixResponseMeasurementSelection()
    metadata = records.PAIRED15_MEASUREMENT_CAPABILITY.metadata()
    assert metadata['selectable_fields'] == ['primary_description', 'primary_horizon', 'target_discrepancy_tolerance']
    for name, expected in records.PAIRED15_MEASUREMENT_CAPABILITY.fixed_fields:
        if name == 'target_contract':
            assert selected.target_contract == expected == 'PAIRED15'
            continue
        assert type(getattr(selected, name)) is type(getattr(legacy, name))
        assert getattr(selected, name) == getattr(legacy, name) == expected
    assert decode_canonical_bytes(before, type(selected), maximum_bytes=None).canonical_bytes() == before
    changed = replace(selected, primary_description=selected.descriptions[-1], primary_horizon=selected.horizons[-1],
                      target_discrepancy_tolerance=selected.target_discrepancy_tolerance * Decimal(2))
    assert changed != selected and changed.canonical_bytes() != before
    assert selected.canonical_bytes() == before


@pytest.mark.parametrize('field,value', (
    ('q', 3), ('matrix_dimension', 8), ('primary_timestep', Decimal('0.002')),
    ('receiver_count', 24), ('feature_window_ticks', 16), ('action_amplitude', Decimal('0.02')),
))
def test_unsupported_fixed_capability_edits_refuse_before_any_contact(field, value):
    selected = records.ConfiguredE3Measurement(primary_description=records.DESCRIPTIONS[0],
        primary_horizon=records.HORIZONS[0], target_discrepancy_tolerance=Decimal('0.01'))
    with pytest.raises(ValueError, match='capability .* fixes '+field):
        replace(selected, **{field: value})


def test_public_explain_and_config_schema_distinguish_fixed_and_selectable_geometry():
    import json
    from empirical_lawhood.api.configuration_registry import consumer_by_id
    from empirical_lawhood.api.configuration_schemas import generated_resources
    from empirical_lawhood.api.experiment_preparation import experiment_preparation_report

    # Existing cheap configured fixture; metadata exposure needs no fit/native task.
    specification, _ = configured_case()
    prepared = prepare_experiment(specification)
    expected = records.PAIRED15_MEASUREMENT_CAPABILITY.metadata()
    assert experiment_preparation_report(prepared)['configuration_capabilities'] == [expected]
    consumer = consumer_by_id('matrix-response-experiment-v2')
    assert consumer.configuration_capabilities == (records.PAIRED15_MEASUREMENT_CAPABILITY,)
    schema = json.loads(generated_resources()[consumer.consumer+'.schema.json'])
    definitions = tuple(value for value in schema['$defs'].values()
        if value.get('x-capability-contract', {}).get('contract_id') == expected['contract_id'])
    definition, = definitions
    properties = definition['properties']['value']['properties']
    assert properties['q']['const'] == 2 and properties['matrix_dimension']['const'] == 4
    assert properties['primary_timestep']['const'] == {'decimal': '0.001'}
    for name in expected['selectable_fields']:
        assert properties[name]['x-selection'] == 'selectable' and 'const' not in properties[name]
    assert schema['x-configuration-capabilities'] == [expected]


def test_supported_measurement_edits_reach_real_lowered_configs_and_cold_readback():
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input

    specification, selected = configured_case()
    measurement = specification.protocol.measurement
    measurement = replace(measurement, primary_description=measurement.descriptions[-1],
        primary_horizon=measurement.horizons[-1],
        target_discrepancy_tolerance=measurement.target_discrepancy_tolerance * Decimal(2))
    specification = replace(specification, protocol=replace(specification.protocol, measurement=measurement))
    bound = inputs_owner.bind_matrix_response_inputs(specification, selected)
    prepared = prepare_experiment(specification, scientific_inputs=bound.scientific_inputs,
        method_inputs=bound.method_inputs, execution=replace(execution(), workers=1))
    assert prepared.executable
    registrations = {row.registration().selection.selection_id: row.registration()
                     for row in bindings.operation_declarations()}
    for operation in prepared.draft.operations:
        config = decode_recursive_config_input(operation, registrations[operation.selection.selection_id]).record
        assert config.specification == specification.identity
        assert config.resource_budget == operation.resource_budget == selected['resources'].budget(config.operation)
    preparation_owner.validate_matrix_response_instance(specification=specification, allocation=prepared.allocation,
        draft=prepared.draft, source_records=prepared.design_records)
    assert decode_canonical_bytes(specification.canonical_bytes(), type(specification), maximum_bytes=None) == specification
