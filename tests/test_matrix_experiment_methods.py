# SPDX-License-Identifier: MPL-2.0
"""Independent exposed E3 arithmetic, causal graph and public custody controls."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import experiment_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_bindings import BUDGET, NAMESPACE, operation_declarations
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_lowering import lower_exposed_matrix_response_error
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_preparation import prepare_matrix_response_error
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.api import load_authoring
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.test_matrix_experiment_specification import PROTOCOL, alternative, execution, inputs, object_identity, selected


ROOT = Path(__file__).parents[1]


def fixture(*, train_count=12, cal_count=20, eval_count=8, minimum_usable=None, selected64=False):
    specification = replace(selected(), evidence_scope="EXPOSED_CONFORMANCE") if selected64 else alternative()
    counts = {"TRAIN": train_count, "CALIBRATION": cal_count, "EVALUATION": eval_count}
    specification = replace(specification,
        populations=tuple(replace(row, expected_units=counts.get(row.role, row.expected_units)) for row in specification.populations),
        assessment=replace(specification.assessment, minimum_usable_units=eval_count if minimum_usable is None else minimum_usable))
    source_inputs = inputs(specification)
    preview = prepare_matrix_response_error(specification, scientific_inputs=source_inputs, execution=execution(), protocol_bytes=PROTOCOL)
    allocation = preview.allocation
    assert allocation is not None
    sources = {source.object_id: source for source in allocation.sources}
    features, outcomes = [], []
    for role in ("train", "calibration", "evaluation"):
        role_units = tuple(unit for unit in allocation.units if unit.unit_id in allocation.unit_ids(role))
        feature_rows, outcome_rows = [], []
        for index, unit in enumerate(role_units):
            values = {name: Decimal("0.1") + Decimal(index) / 10000 for name in FEATURES}
            values.update({"family-de-anneal": Decimal(1), "family-x-first": Decimal(0), "family-y-first": Decimal(0),
                "cutoff": Decimal("0.256"), "bath-temperature": Decimal(1), "friction": Decimal(1), "cross-gamma": Decimal(1),
                "potential-m": Decimal("0.5"), "alpha-x": Decimal("0.666"), "alpha-y": Decimal("7.333")})
            native, origin = object_identity("native." + unit.unit_id), object_identity("origin." + unit.unit_id)
            evidence = (object_identity("explicit-exposed-measurement." + unit.unit_id),)
            feature_rows.append(science.MatrixE3CausalFeature("feature." + unit.unit_id, unit.unit_id, sources[unit.source_id],
                native, origin, "clock.fixture.matrix-q2", Decimal("0.256"), "a" * 64, "AVAILABLE", tuple(sorted(values.items())), evidence))
            errors = tuple((Decimal("0.08") + Decimal(index) / 100000 + Decimal(description) / 100)
                * factor for description in range(5) for factor in (Decimal("0.1"), Decimal("0.5"), Decimal(1)))
            views = tuple(science.MatrixE3ViewOutcome(view, errors, ("FINITE",) * 15) for view in ("fine", "primary"))
            outcome_rows.append(science.MatrixE3PairedOutcome("outcome." + unit.unit_id, unit.unit_id, sources[unit.source_id],
                native, origin, "clock.fixture.matrix-q2", Decimal("0.256"), "a" * 64, views, "SATISFIED", evidence))
        original_allocation = source_inputs[specification.population(role.upper()).source_key].identity
        features.append(science.MatrixE3FeatureBank("feature-bank." + role, original_allocation, role, tuple(feature_rows)))
        outcomes.append(science.MatrixE3OutcomeBank("outcome-bank." + role, original_allocation, role, tuple(outcome_rows)))
    campaign = replace(load_authoring(ROOT / "tests/fixtures/reference-campaign.json").campaign, budget=BUDGET)
    method_inputs = science.project_method_inputs(specification, allocation, source_inputs,
        science.MatrixE3MethodInputs(campaign, tuple(features), tuple(outcomes)))
    return specification, source_inputs, allocation, method_inputs


def bank(method_inputs, kind, role):
    return next(row for row in getattr(method_inputs, kind) if row.role == role)


def selected_input_records(source_inputs, method_inputs):
    def original(bank):
        if bank.original_bank is None:
            return bank
        reconstructed = replace(bank, record_id=bank.original_bank.object_id, allocation=bank.original_allocation,
            original_bank=None, original_allocation=None)
        assert science.identity(reconstructed) == bank.original_bank
        return reconstructed
    return {**source_inputs, "campaign": method_inputs.campaign,
        **{row.role + "-features": original(row) for row in method_inputs.features},
        **{row.role + "-outcomes": original(row) for row in method_inputs.outcomes}}


def write_source_selection(directory, source_inputs, method_inputs):
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
    directory.mkdir()
    bindings = []
    for index, (key, record) in enumerate(sorted(selected_input_records(source_inputs, method_inputs).items())):
        path = directory / (str(index) + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append(ExperimentInputBinding(key, ObjectIdentity.from_record("fixture.selected." + key, record),
            path.name, len(record.canonical_bytes())))
    selection = ExperimentInputSelection("fixture.public.matrix-source-selection", "matrix.response-error.origin-only", tuple(bindings))
    selection_path = directory / "sources.json"
    selection_path.write_bytes(selection.canonical_bytes())
    return selection_path


def test_edit_only_specification_reuses_the_same_original_source_selection(tmp_path):
    from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
    specification, source_inputs, _, method_inputs = fixture()
    selection_path = write_source_selection(tmp_path / "same-original-sources", source_inputs, method_inputs)
    original_bytes = {path.name: path.read_bytes() for path in selection_path.parent.iterdir()}
    counts = {"TRAIN": 6, "CALIBRATION": 16}
    edited = replace(specification, specification_id="fixture.matrix.e3.edited-selection",
        question=specification.question + " Explicit exposed subset.",
        assessment=replace(specification.assessment, minimum_usable_units=7),
        populations=tuple(replace(population, expected_units=counts[population.role],
            unit_ids=tuple(row.unit_id for row in bank(method_inputs, "features", population.role.lower()).rows[:counts[population.role]]))
            if population.role in counts else population for population in specification.populations))
    resolved = load_experiment_inputs(edited, selection_path)
    preparation = prepare_experiment(edited, scientific_inputs=resolved.scientific_inputs, execution=execution(),
        protocol_bytes=PROTOCOL, method_inputs=resolved.method_inputs)
    assert preparation.executable and not preparation.dependencies
    assert dict(preparation.census.role_counts)["train"] == 6
    assert dict(preparation.census.role_counts)["calibration"] == 16
    assert len(preparation.draft.operations) == 53
    training = next(record for _, record in preparation.input_records if type(record) is science.MatrixE3FeatureBank)
    original = next(row for row in resolved.method_inputs.features if row.role == "train")
    assert training.original_bank == science.identity(original)
    assert training.original_allocation == original.allocation
    assert tuple(row.canonical_bytes() for row in training.rows) == tuple(row.canonical_bytes() for row in original.rows[:6])
    assert original_bytes == {path.name: path.read_bytes() for path in selection_path.parent.iterdir()}
    # An omitted original row remains a refusal even when it lies outside the
    # selected subset; selection never hides source-bank missingness.
    partial = replace(original, rows=original.rows[:-1])
    bad = replace(resolved.method_inputs, features=tuple(partial if row.role == "train" else row for row in resolved.method_inputs.features))
    refused = prepare_experiment(edited, scientific_inputs=resolved.scientific_inputs, execution=execution(),
        protocol_bytes=PROTOCOL, method_inputs=bad)
    assert not refused.executable
    assert "matrix.e3.train-features.invalid" in {row.code for row in refused.dependencies}


def test_closed_input_binding_prepares_complete_and_partial_source_banks():
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_inputs import bind_matrix_response_inputs, input_record_types
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3PreparationSelection
    specification, source_inputs, _, method_inputs = fixture()
    records = selected_input_records(source_inputs, method_inputs)
    assert {*{type(row) for row in records.values()}, ProtectedE3PreparationSelection} == set(input_record_types())
    resolved = bind_matrix_response_inputs(specification, records)
    prepared = prepare_matrix_response_error(specification, scientific_inputs=resolved.scientific_inputs,
        execution=execution(), protocol_bytes=PROTOCOL, method_inputs=resolved.method_inputs)
    assert prepared.draft is not None and not prepared.dependencies
    assert len(prepared.draft.operations) == 61 and len(prepared.input_records) == 60
    expected = {row.input_id: row.expected_content_sha256 for row in prepared.draft.external_inputs}
    assert {key: record.fingerprint() for key, record in prepared.input_records} == expected
    with pytest.raises(TypeError):
        resolved.scientific_inputs["substituted-source"] = next(iter(source_inputs.values()))
    del records["evaluation-outcomes"]
    partial = bind_matrix_response_inputs(specification, records)
    refused = prepare_matrix_response_error(specification, scientific_inputs=partial.scientific_inputs,
        execution=execution(), protocol_bytes=PROTOCOL, method_inputs=partial.method_inputs)
    assert refused.draft is None and refused.input_records == ()
    assert [row.code for row in refused.dependencies] == ["matrix.e3.evaluation-outcomes"]
    assert refused.census.operation_counts == prepared.census.operation_counts


def test_selected64_uses_the_same_bank_binding_and_lowering_as_the_alternative():
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_inputs import bind_matrix_response_inputs
    specification, source_inputs, _, method_inputs = fixture(selected64=True,
        train_count=64, cal_count=64, eval_count=64, minimum_usable=58)
    resolved = bind_matrix_response_inputs(specification, selected_input_records(source_inputs, method_inputs))
    prepared = prepare_matrix_response_error(specification, scientific_inputs=resolved.scientific_inputs,
        execution=execution(), protocol_bytes=PROTOCOL, method_inputs=resolved.method_inputs)
    assert prepared.draft is not None and not prepared.dependencies
    assert dict(prepared.census.role_counts) == {role: 64 for role in
        ("train", "calibration", "evaluation", "transfer_nearby", "transfer_shifted")}
    assert len(prepared.allocation.units) == 320
    assert len(prepared.draft.operations) == 261 and len(prepared.input_records) == 260
    assert dict(prepared.census.output_counts)["calibration-rank"] == 62
    assert dict(prepared.census.output_counts)["minimum-primary-successes"] == 43


def test_missing_campaign_retains_all_bound_banks_and_reports_a_typed_dependency():
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_inputs import bind_matrix_response_inputs
    specification, source_inputs, allocation, method_inputs = fixture()
    records = selected_input_records(source_inputs, method_inputs)
    del records["campaign"]
    resolved = bind_matrix_response_inputs(specification, records)
    assert resolved.method_inputs.campaign is None
    assert tuple(row.rows for row in resolved.method_inputs.features) == tuple(row.rows for row in method_inputs.features)
    assert tuple(row.rows for row in resolved.method_inputs.outcomes) == tuple(row.rows for row in method_inputs.outcomes)
    prepared = prepare_matrix_response_error(specification, scientific_inputs=resolved.scientific_inputs,
        execution=execution(), protocol_bytes=PROTOCOL, method_inputs=resolved.method_inputs)
    assert prepared.allocation == allocation and prepared.draft is None
    assert [row.code for row in prepared.dependencies] == ["matrix.e3.campaign"]
    assert prepared.dependencies[0].kind.value == "EXTERNAL_INPUT"
    assert dict(prepared.census.resolved_role_counts)["evaluation"] == 8
    with pytest.raises(ValueError, match="actual selected campaign"):
        lower_exposed_matrix_response_error(specification, allocation, resolved.method_inputs)


@pytest.mark.parametrize("failure", ("unknown-key", "wrong-type", "role-change", "prospective"))
def test_closed_input_binding_refuses_substituted_keys_types_roles_and_protected_scope(failure):
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_inputs import bind_matrix_response_inputs
    specification, source_inputs, _, method_inputs = fixture()
    records = selected_input_records(source_inputs, method_inputs)
    if failure == "unknown-key":
        records["arbitrary-callback"] = method_inputs.campaign
    elif failure == "wrong-type":
        records["train-features"] = records["train-outcomes"]
    elif failure == "role-change":
        records["train-features"] = records["evaluation-features"]
    else:
        specification = replace(specification, evidence_scope="PROSPECTIVE_REQUIRED")
    with pytest.raises((TypeError, ValueError)):
        bind_matrix_response_inputs(specification, records)


def run_methods(specification, allocation, method_inputs):
    models = science.fit_models(specification, allocation, bank(method_inputs, "features", "train"),
        bank(method_inputs, "outcomes", "train"), record_id="models.fixture.matrix-e3")
    fitted = science.freeze(specification, allocation, models, record_id="freeze.fixture.model")
    cal_forecasts = tuple(science.forecast(specification, allocation, models, fitted, feature, role="calibration",
        record_id="forecast." + feature.unit_id) for feature in bank(method_inputs, "features", "calibration").rows)
    cal_outcomes = tuple(science.observe(forecast, outcome, record_id="observed." + outcome.unit_id)
        for forecast, outcome in zip(cal_forecasts, bank(method_inputs, "outcomes", "calibration").rows, strict=True))
    calibration = science.calibrate(specification, allocation, models, fitted, cal_forecasts, cal_outcomes, record_id="calibration.fixture.matrix-e3")
    calibrated = science.freeze(specification, allocation, models, record_id="freeze.fixture.calibrated", model_freeze=fitted, calibration=calibration)
    eval_forecasts = tuple(science.forecast(specification, allocation, models, calibrated, feature, role="evaluation",
        record_id="forecast." + feature.unit_id, calibration=calibration) for feature in bank(method_inputs, "features", "evaluation").rows)
    eval_outcomes = tuple(science.observe(forecast, outcome, record_id="observed." + outcome.unit_id)
        for forecast, outcome in zip(eval_forecasts, bank(method_inputs, "outcomes", "evaluation").rows, strict=True))
    assessed = science.evaluate(specification, allocation, calibrated, eval_forecasts, eval_outcomes, record_id="assessment.fixture.matrix-e3")
    return models, fitted, cal_forecasts, calibration, calibrated, eval_forecasts, assessed


def test_raw_median_fits_original_units_before_log_representation():
    specification, _, allocation, method_inputs = fixture(train_count=2)
    original = bank(method_inputs, "outcomes", "train")
    rows = tuple(replace(row, views=tuple(replace(view, errors=(Decimal(value),) * 15) for view in row.views))
        for row, value in zip(original.rows, (0, 3), strict=True))
    outcomes = replace(original, rows=rows)
    models = science.fit_models(specification, allocation, bank(method_inputs, "features", "train"), outcomes, record_id="models.fixture.raw-median")
    median = next(model for model in models.models if model.method_key == "RAW_TRAIN_MEDIAN")
    # The arithmetic midpoint is1.5; averaging log1p then inverting gives1.
    assert median.raw_constants == (Decimal("1.5"),) * 15
    assert median.feature_names == () and median.finite_counts == (2,) * 15
    assert specification.methods[1].fit_scale == "RAW_NORMALIZED"
    assert specification.methods[1].estimation_rule == "MEDIAN_EVEN_ARITHMETIC_MIDPOINT"


def test_complete_methods_keep_models_frozen_and_source_omissions():
    specification, _, allocation, method_inputs = fixture()
    models, fitted, _, calibration, calibrated, _, assessment = run_methods(specification, allocation, method_inputs)
    assert models.models[2].feature_names == tuple(sorted(name for block in ("CONTEXT", "SPECTRAL") for name in science.FEATURE_BLOCKS[block]))
    assert all(model.training_unit_ids == allocation.unit_ids("train") for model in models.models)
    assert calibration.rank == 20 and calibration.target_view == "MAX_PAIRED_VIEWS"
    assert calibration.models == science.identity(models) and calibration.model_freeze == science.identity(fitted)
    assert calibrated.models == science.identity(models) and calibrated.model_freeze == science.identity(fitted)
    assert len(assessment.decisions) == 8 and len(assessment.coverage) == 8
    assert all(len(row.comparisons) == 4 for row in assessment.decisions)
    assert assessment.qualification == "NOT_ESTABLISHED"
    assert decode_canonical_bytes(assessment.canonical_bytes(), science.MatrixE3Assessment, maximum_bytes=None) == assessment
    original_bytes = models.canonical_bytes()
    changed = replace(bank(method_inputs, "outcomes", "calibration"), rows=tuple(replace(row,
        numerical_disposition="VIOLATED") for row in bank(method_inputs, "outcomes", "calibration").rows))
    changed_inputs = replace(method_inputs, outcomes=tuple(changed if row.role == "calibration" else row for row in method_inputs.outcomes))
    changed_models, _, _, changed_calibration, _, _, _ = run_methods(specification, allocation, changed_inputs)
    assert changed_models.canonical_bytes() == original_bytes
    assert all(score is None for _, score, _ in changed_calibration.scores)
    assert changed_calibration.radius_kind == "INFINITE"


@pytest.mark.parametrize("target_view", ("PRIMARY", "MAX_PAIRED_VIEWS"))
def test_calibration_selected_view_matches_independent_max15_log_oracle(target_view):
    specification, _, allocation, method_inputs = fixture()
    specification = replace(specification, calibration_target_view=target_view)
    # Rebind the records to the new immutable allocation identity produced by
    # specification preparation; there is no unchanged scientific-instance claim.
    source_inputs = inputs(specification)
    allocation = prepare_matrix_response_error(specification, scientific_inputs=source_inputs, execution=execution(), protocol_bytes=PROTOCOL).allocation
    method_inputs = replace(method_inputs,
        features=tuple(replace(row, allocation=allocation.identity) for row in method_inputs.features),
        outcomes=tuple(replace(row, allocation=allocation.identity) for row in method_inputs.outcomes))
    calibration_bank = bank(method_inputs, "outcomes", "calibration")
    changed_rows = tuple(replace(row, views=(replace(row.views[0], errors=tuple(value + Decimal("0.00005") for value in row.views[0].errors)), row.views[1]))
        for row in calibration_bank.rows)
    changed_bank = replace(calibration_bank, rows=changed_rows)
    method_inputs = replace(method_inputs, outcomes=tuple(changed_bank if row.role == "calibration" else row for row in method_inputs.outcomes))
    _, _, forecasts, calibration, _, _, _ = run_methods(specification, allocation, method_inputs)
    expected = []
    with localcontext() as context:
        context.prec = 50
        for forecast, outcome in zip(forecasts, changed_rows, strict=True):
            points = dict(forecast.log_points)["SPECTRAL_RIDGE"]
            labels = outcome.view("primary").errors if target_view == "PRIMARY" else tuple(max(primary, fine)
                for primary, fine in zip(outcome.view("primary").errors, outcome.view("fine").errors, strict=True))
            expected.append(max(max(Decimal(0), (Decimal(1)+label).ln()-point) for label, point in zip(labels, points, strict=True)))
    assert tuple(score for _, score, _ in calibration.scores) == tuple(expected)
    assert calibration.radius == max(expected)


def test_rank62_preserves_three_infinite_scores_and_explicit_bound_kind():
    specification, _, allocation, method_inputs = fixture(cal_count=64)
    original = bank(method_inputs, "outcomes", "calibration")
    invalid = replace(original, rows=tuple(replace(row, numerical_disposition="VIOLATED") if index < 3 else row
        for index, row in enumerate(original.rows)))
    method_inputs = replace(method_inputs, outcomes=tuple(invalid if row.role == "calibration" else row for row in method_inputs.outcomes))
    _, _, _, calibration, _, forecasts, assessment = run_methods(specification, allocation, method_inputs)
    assert len(calibration.scores) == 64 and sum(score is None for _, score, _ in calibration.scores) == 3
    assert calibration.rank == 62 and calibration.radius is None and calibration.radius_kind == "INFINITE"
    assert all(forecast.radius_kind == "INFINITE" for forecast in forecasts)
    assert all(kind == "INFINITE" for _, kind in assessment.coverage_bound_kinds)
    assert all(all(value is None for value in slacks) for _, _, slacks in assessment.coverage)


def test_future_changes_leave_identical_pre_future_forecasts_and_complete_failures():
    specification, _, allocation, method_inputs = fixture()
    before = run_methods(specification, allocation, method_inputs)
    original = bank(method_inputs, "outcomes", "evaluation")
    unknown = replace(original.rows[0], views=tuple(replace(view, errors=(None,) * 15, dispositions=("UNKNOWN_CONTACT",) * 15)
        for view in original.rows[0].views), numerical_disposition="UNEVALUABLE")
    invalid = replace(original, rows=(unknown, *original.rows[1:]))
    changed_inputs = replace(method_inputs, outcomes=tuple(invalid if row.role == "evaluation" else row for row in method_inputs.outcomes))
    after = run_methods(specification, allocation, changed_inputs)
    assert tuple(row.canonical_bytes() for row in before[5]) == tuple(row.canonical_bytes() for row in after[5])
    assert before[0].canonical_bytes() == after[0].canonical_bytes()
    result = after[6]
    assert len(result.decisions) == 8 and result.usable_units == 7
    assert not result.decisions[0].success and "UNKNOWN_CONTACT" in result.decisions[0].reasons
    assert all(value is None for _, _, value in result.decisions[0].comparisons)


def test_declarations_lower_complete_graph_and_refuse_future_port_bypass():
    specification, source_inputs, allocation, method_inputs = fixture()
    lowered = lower_exposed_matrix_response_error(specification, allocation, method_inputs)
    prepared = prepare_matrix_response_error(specification, scientific_inputs=source_inputs, execution=execution(),
        protocol_bytes=PROTOCOL, method_inputs=method_inputs)
    assert not prepared.dependencies and prepared.draft == lowered.draft
    assert len(lowered.draft.operations) == 5 + 2 * (20 + 8)
    assert dict(prepared.census.operation_counts) == {"fit": 1, "freeze": 2, "forecast": 28, "observe": 28, "calibrate": 1, "evaluate": 1}
    assert prepared.census.native_effect_count == 0
    declarations = operation_declarations()
    from empirical_lawhood.runtime.plans import BarrierKind, ScientificStage
    exposed_evaluation = next(row for row in declarations if row.capability_key == NAMESPACE + ".evaluate")
    assert exposed_evaluation.stage is ScientificStage.FALSIFY
    assert exposed_evaluation.execution_properties.barrier is BarrierKind.NONE
    assert all(row.execution_properties.barrier not in (BarrierKind.REVEAL, BarrierKind.AUTHORITY) for row in declarations)
    assert all(row.evidence_ceiling.value == "NON_PROMOTABLE" for row in declarations)
    assert all(row.provenance_requirements[0].requirement_id == "matrix-response-study.selected-numerical-profile.v1" for row in declarations)
    registry = CapabilityRegistry("registry.fixture.parameterized-e3", tuple(sorted((row.manifest() for row in declarations), key=lambda row: row.registry_id)))
    registrations = tuple(row.registration() for row in declarations)
    codecs = {schema: kind for row in declarations for schema, kind in row.record_codecs.items()}
    compiled = compile_recursive_wave(draft=lowered.draft, registrations=registrations, registry=registry,
        implementation_commit="a" * 40, output_codecs=codecs)
    assert len(compiled.execution_plan.tasks) == len(lowered.draft.operations)
    observation = next(row for row in lowered.draft.operations if row.selection.capability_key == NAMESPACE + ".observe")
    links = tuple(row for row in lowered.draft.links if not (row.consumer_node_id == observation.node_id and row.consumer_input_id == "forecast"))
    with pytest.raises(ValueError, match="input|forecast|phase|dependency"):
        compile_recursive_wave(draft=replace(lowered.draft, links=links), registrations=registrations, registry=registry,
            implementation_commit="a" * 40, output_codecs=codecs)
    forecast_node = next(row.node_id for row in lowered.draft.operations if row.selection.capability_key == NAMESPACE + ".forecast")
    outcome_edge = next(row for row in lowered.draft.links if row.consumer_input_id == "outcome")
    from empirical_lawhood.planning.recursive_authoring import RecursiveInputLink
    leaked = RecursiveInputLink("edge.fixture.illicit-future", forecast_node, "outcome", external_input_id=outcome_edge.external_input_id, scientific_role="OUTCOME")
    with pytest.raises(ValueError, match="undeclared|input|phase"):
        compile_recursive_wave(draft=replace(lowered.draft, links=tuple(sorted((*lowered.draft.links, leaked), key=lambda row: row.edge_id))),
            registrations=registrations, registry=registry, implementation_commit="a" * 40, output_codecs=codecs)


def test_original_long_unit_identity_remains_exact_with_bounded_public_task_ids():
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_bindings import MatrixE3OperationConfig, node_id
    specification, _, allocation, _ = fixture()
    long_unit = "unit.original." + "a" * 1024
    node = node_id(specification.identity, "forecast", mode="calibration", unit_id=long_unit)
    config = MatrixE3OperationConfig("config." + node, "forecast", specification.identity, allocation.identity,
        (("calibration", 20), ("evaluation", 8)), "calibration", long_unit)
    assert len(node) <= 110 and config.unit_id == long_unit
    assert node != node_id(specification.identity, "forecast", mode="evaluation", unit_id=long_unit)
    assert node != node_id(specification.identity, "forecast", mode="calibration", unit_id=long_unit + "b")
    assert decode_canonical_bytes(config.canonical_bytes(), MatrixE3OperationConfig, maximum_bytes=None) == config


def test_shared_lookup_preserves_original_first_middle_last_and_missing_units():
    _, _, allocation, _ = fixture()
    original = allocation.canonical_bytes()
    for index in (0, len(allocation.units) // 2, len(allocation.units) - 1):
        expected = allocation.units[index]
        assert allocation.unit(expected.unit_id) == expected
    assert allocation.unit("fixture.unit.absent") is None
    assert allocation.canonical_bytes() == original


def test_instance_association_accepts_exact_graph_and_rejects_another_valid_experiment():
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_preparation import validate_matrix_response_instance
    specification, source_inputs, allocation, method_inputs = fixture()
    prepared = prepare_matrix_response_error(specification, scientific_inputs=source_inputs, execution=execution(),
        protocol_bytes=PROTOCOL, method_inputs=method_inputs)
    assert validate_matrix_response_instance(specification=specification, allocation=allocation,
        draft=prepared.draft, source_records=()) is None
    other_specification, other_inputs, other_allocation, other_methods = fixture(cal_count=21, eval_count=9)
    other = prepare_matrix_response_error(other_specification, scientific_inputs=other_inputs, execution=execution(),
        protocol_bytes=PROTOCOL, method_inputs=other_methods)
    assert not other.dependencies and validate_matrix_response_instance(specification=other_specification,
        allocation=other_allocation, draft=other.draft, source_records=()) is None
    with pytest.raises(ValueError, match="sidecar|root|census|operands"):
        validate_matrix_response_instance(specification=specification, allocation=allocation,
            draft=other.draft, source_records=())


@pytest.mark.parametrize("failure", ("config-allocation", "external-specification", "external-allocation", "forecast-future-link", "partial-selection", "root-units"))
def test_instance_association_refuses_valid_typed_graph_binding_substitutions(failure):
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_bindings import MatrixE3OperationConfig
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_preparation import validate_matrix_response_instance
    specification, source_inputs, allocation, method_inputs = fixture()
    prepared = prepare_matrix_response_error(specification, scientific_inputs=source_inputs, execution=execution(),
        protocol_bytes=PROTOCOL, method_inputs=method_inputs)
    draft = prepared.draft
    if failure == "config-allocation":
        operation = draft.operations[0]
        config = decode_canonical_bytes(operation.config_payload.encode(), MatrixE3OperationConfig, maximum_bytes=None)
        changed = replace(config, allocation=replace(allocation.identity, object_fingerprint="f" * 64))
        operations = tuple(replace(row, config_payload=changed.canonical_bytes().decode()) if row == operation else row for row in draft.operations)
        draft = replace(draft, operations=operations)
    elif failure.startswith("external-"):
        from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_lowering import external_id
        target = external_id(specification.identity, failure.removeprefix("external-"))
        draft = replace(draft, external_inputs=tuple(replace(row, expected_content_sha256="f" * 64)
            if row.input_id == target else row for row in draft.external_inputs))
    elif failure == "forecast-future-link":
        forecast = next(row for row in draft.operations if row.selection.capability_key == NAMESPACE + ".forecast")
        future = next(row for row in draft.links if row.consumer_input_id == "outcome")
        draft = replace(draft, links=tuple(replace(row, external_input_id=future.external_input_id, scientific_role="OUTCOME")
            if row.consumer_node_id == forecast.node_id and row.consumer_input_id == "feature" else row for row in draft.links))
    elif failure == "partial-selection":
        draft = replace(draft, selected_operation_ids=draft.selected_operation_ids[:-1])
    else:
        draft = replace(draft, development_study=replace(draft.development_study,
            assigned_unit_ids=draft.development_study.assigned_unit_ids[:-1]))
    draft.__post_init__()  # Schema validity alone must not establish association.
    with pytest.raises(ValueError):
        validate_matrix_response_instance(specification=specification, allocation=allocation,
            draft=draft, source_records=())


def test_incomplete_source_bank_reports_dependency_without_fitting(monkeypatch):
    specification, source_inputs, _, method_inputs = fixture()
    selected_bank = bank(method_inputs, "outcomes", "evaluation")
    partial = replace(selected_bank, rows=selected_bank.rows[:-1])
    method_inputs = replace(method_inputs, outcomes=tuple(partial if row.role == "evaluation" else row for row in method_inputs.outcomes))
    monkeypatch.setattr(science.numerical, "fit_standardized_ridge", lambda *args, **kwargs: pytest.fail("preparation fitted a model"))
    prepared = prepare_matrix_response_error(specification, scientific_inputs=source_inputs, execution=execution(), protocol_bytes=PROTOCOL, method_inputs=method_inputs)
    assert not prepared.executable and prepared.draft is None
    assert "matrix.e3.evaluation-outcomes.invalid" in {row.code for row in prepared.dependencies}


@pytest.mark.parametrize("field", ("algorithm", "opportunity_baseline", "strong_conventional_baseline", "success", "formal_family"))
def test_rehashed_protocol_semantic_changes_refuse_before_lowering(field):
    specification, source_inputs, _, method_inputs = fixture()
    document = json.loads(PROTOCOL)
    section = "prediction" if field in ("algorithm", "opportunity_baseline", "strong_conventional_baseline") else "primary_criterion"
    document[section][field] = "changed scientific selection"
    raw = (json.dumps(document, indent=2) + "\n").encode()
    changed = replace(specification, protocol_sha256=sha256(raw).hexdigest())
    prepared = prepare_matrix_response_error(changed, scientific_inputs=source_inputs, execution=execution(), protocol_bytes=raw, method_inputs=method_inputs)
    assert not prepared.executable and prepared.draft is None
    assert any(field in row.detail for row in prepared.dependencies)


def test_selected_criterion_uses_strict_margin_each_baseline_each_view_and_full_n64():
    # Forecast points are an independently specified exposed scalar oracle;
    # this does not fit to or acquire any real response data.
    specification, _, allocation, method_inputs = fixture(eval_count=64, minimum_usable=58)
    _, _, _, calibration, frozen, forecasts, _ = run_methods(specification, allocation, method_inputs)
    with localcontext() as context:
        context.prec = 50
        candidate = (Decimal(1) + Decimal("0.08")).ln()
        baseline = (Decimal(1) + Decimal("0.081")).ln()
    forced = tuple(replace(forecast, log_points=tuple((method, (candidate if method == "SPECTRAL_RIDGE" else baseline,) * 15)
        for method in science.METHODS)) for forecast in forecasts)
    original = bank(method_inputs, "outcomes", "evaluation")
    rows = tuple(replace(row, views=tuple(replace(view, errors=((Decimal("0.08") if index < 43 else Decimal("0.082")),) * 15)
        for view in row.views)) for index, row in enumerate(original.rows))
    observed = tuple(science.observe(forecast, row, record_id="forced.observed." + row.unit_id) for forecast, row in zip(forced, rows, strict=True))
    result = science.evaluate(specification, allocation, frozen, forced, observed, record_id="forced.assessment")
    assert len(result.decisions) == 64 and result.successes == 43 and result.usable_units == 64
    assert result.criterion_met
    assert Fraction(result.binomial_tail_numerator, result.binomial_tail_denominator) == Fraction(75141910203168229, 18446744073709551616)
    failing = replace(rows[0], numerical_disposition="VIOLATED")
    observed = (science.observe(forced[0], failing, record_id="forced.observed.failed"), *observed[1:])
    result = science.evaluate(specification, allocation, frozen, forced, observed, record_id="forced.assessment.failed")
    assert result.successes == 42 and not result.criterion_met
    assert calibration.models == frozen.models
    invalid_usable = tuple(science.observe(forecast, replace(row, numerical_disposition="VIOLATED") if index >= 57 else row,
        record_id="usable.observed." + row.unit_id) for index, (forecast, row) in enumerate(zip(forced, rows, strict=True)))
    result = science.evaluate(specification, allocation, frozen, forced, invalid_usable, record_id="forced.assessment.usability")
    assert result.successes == 43 and result.usable_units == 57 and not result.criterion_met


@pytest.mark.parametrize("failure", ("tie", "one-baseline", "one-view"))
def test_primary_comparison_requires_strict_margin_for_each_baseline_in_both_views(failure):
    specification, _, allocation, method_inputs = fixture()
    _, _, _, _, frozen, forecasts, _ = run_methods(specification, allocation, method_inputs)
    with localcontext() as context:
        context.prec = 50
        margin_point = (Decimal(1) + Decimal("0.0002")).ln()
        stronger_point = (Decimal(1) + Decimal("0.001")).ln()
    forced = tuple(replace(forecast, log_points=(
        ("ALL_ORIGIN_RIDGE", ((margin_point if failure == "tie" else Decimal(0) if failure == "one-baseline" else stronger_point),) * 15),
        ("RAW_TRAIN_MEDIAN", (stronger_point,) * 15), ("SPECTRAL_RIDGE", (Decimal(0),) * 15))) for forecast in forecasts)
    rows = tuple(replace(row, views=tuple(replace(view, errors=((
        Decimal("0.000425") if view.view_id == "fine" else Decimal("0.000375")) if failure == "one-view" else Decimal(0),) * 15)
        for view in row.views)) for row in bank(method_inputs, "outcomes", "evaluation").rows)
    # Both numerical labels remain inside0.0001; PRIMARY improves by0.00025
    # while FINE improves by only0.00015. One successful view cannot rescue it.
    observed = tuple(science.observe(forecast, row, record_id="margin.observed." + row.unit_id)
        for forecast, row in zip(forced, rows, strict=True))
    result = science.evaluate(specification, allocation, frozen, forced, observed, record_id="margin.assessment")
    assert result.successes == 0 and not result.criterion_met
    if failure == "tie":
        assert all(row.comparisons[0][2] == Decimal("0.0002") for row in result.decisions)
        assert all(row.usable for row in result.decisions)
    elif failure == "one-view":
        assert all(row.usable for row in result.decisions)
        assert all(row.comparisons[0][2] == Decimal("0.00015") and row.comparisons[1][2] == Decimal("0.00025") for row in result.decisions)


@pytest.mark.parametrize("selected64", (False, True), ids=("alternative12-20-8", "selected64"))
def test_actual_public_default_author_run_read_and_completed_recovery(tmp_path, monkeypatch, selected64):
    from empirical_lawhood.api import recursive_authoring as author, recursive_execution as execute
    from empirical_lawhood.api.recursive_operations import operation_factories
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.infrastructure import execution as execution_boundary
    from empirical_lawhood.api.experiment_preparation import author_prepared_experiment, load_experiment_inputs, prepare_experiment
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from tests.test_recursive_public_service import _plane
    specification, source_inputs, _, method_inputs = fixture(selected64=selected64,
        train_count=64 if selected64 else 12, cal_count=64 if selected64 else 20,
        eval_count=64 if selected64 else 8, minimum_usable=58 if selected64 else 8)
    installed = tuple(factory for factory in operation_factories() if factory.manifest.capability_key.startswith(NAMESPACE + "."))
    assert len(installed) == 6, "coordinator must install owning declarations before public-route acceptance"
    snapshot = author.implementation_binding(ROOT)
    failures = []
    diagnose = execution_boundary.operational_failure_diagnostic
    def retain_failure(error, **kwargs):
        failures.append((type(error).__name__, str(error)))
        return diagnose(error, **kwargs)
    monkeypatch.setattr(execution_boundary, "operational_failure_diagnostic", retain_failure)
    selection_path = write_source_selection(tmp_path / "explicit-inputs", source_inputs, method_inputs)
    resolved = load_experiment_inputs(specification, selection_path)
    plane = _plane(tmp_path / "guarded")
    directory = Path(plane.root.contract.canonical_path) / "authored"
    selected_execution = replace(execution(), source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", snapshot),
        output_root=plane.root.contract.canonical_path)
    prepared = prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs, execution=selected_execution,
        protocol_bytes=PROTOCOL, method_inputs=resolved.method_inputs)
    authored = author_prepared_experiment(preparation=prepared, project_root=ROOT, artifact_writer=plane, output_dir=directory)
    expected_tasks = 261 if selected64 else 61
    assert authored["task_count"] == expected_tasks and authored["native_contact"] == "none"
    report = execute.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane)
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0, failures[:1]
    assert report["scientific_authority"] == "NONE" and report["qualification"] == "NOT_ESTABLISHED"
    retained, products, _, _ = execute.read_recursive_wave(directory=directory, artifact_writer=plane,
        terminal_product_format="references", include_products=True)
    assert retained["status"] == "SUCCEEDED" and len(products["receipts"]) == expected_tasks
    finding = next(record for records in products["records"].values() for record in records.values() if type(record) is science.MatrixE3Assessment)
    assert len(finding.decisions) == (64 if selected64 else 8) and finding.qualification == "NOT_ESTABLISHED"
    monkeypatch.setattr(LocalProcessExecutor, "execute", lambda *args, **kwargs: pytest.fail("completed E3 method was reexecuted"))
    recovered = execute.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane)
    assert recovered["status"] == "SUCCEEDED" and recovered["new_native_contact_count"] == 0
