"""Pure boundary controls for canonical finite-menu investigation records."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.design.joint_description import (
    Description, Economics, JointSpecification, ReceiverPolicy, SelectedInputs,
)
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.joint_description import (
    Assessment, Calibration, FittedReceiver, Forecast, ForecastRow, Model,
    OutcomeRow, Outcomes, PredictorRow, Predictors, TrialBatch, TrialRequest,
    TrialRow, finite_json, split_batch,
)


def _spec():
    return JointSpecification("contract-spec", "R03", "A finite declared question", 7,
        ("cal.a", "cal.b"), ("eval.a", "eval.b"), (D(-1), D(1)), (D(1),),
        (ReceiverPolicy("response", "native-unit", D(0), D(1), D(1), D(1)),),
        (Description("joint", ("x",), "fixed", 2, 0, 0, 0, "joint retained state"),
         Description("local", ("x",), "fixed", 1, 0, 0, 0, "reduced local state")),
        "{}", Economics())


def _tables(spec, split):
    units = spec.calibration_unit_ids if split == "calibration" else spec.evaluation_unit_ids
    batch = TrialBatch(spec.family_id, split, tuple(TrialRow(unit, float(action), 1.0,
        "response", (("x", 2.0),), -3.0) for unit in units for action in spec.actions), "supplied-contract-fixture")
    return split_batch(batch, spec.identity, "contract-" + split)


def _model(spec):
    predictors, outcomes = _tables(spec, "calibration")
    calibration = Calibration("contract-calibration", spec.identity, predictors, outcomes)
    fits = tuple(FittedReceiver(description, "response", ("x",), (D(0), D(1)), (D(0),), (D(1),),
                               "fitted", "fixed declared mechanism") for description in ("joint", "local"))
    return Model("contract-model", spec.identity, calibration.identity, fits,
                 (("joint", D(2)), ("local", D(3))), "joint")


def _forecast(spec):
    model = _model(spec)
    predictors, _ = _tables(spec, "evaluation")
    rows = tuple(sorted((ForecastRow(*row.key, description, D(2), "")
        for row in predictors.rows for description in ("joint", "local")), key=lambda row: row.key))
    selections = tuple((unit, D(1), description, D(1)) for unit in spec.evaluation_unit_ids
                       for description in ("joint", "local"))
    return Forecast("contract-forecast", spec.identity, model.identity, predictors.identity, rows, selections)


def test_request_parameters_are_deeply_detached_and_immutable():
    original = {"nested": {"values": [1.0, 2.0]}}
    request = TrialRequest("R03", 3, ("root",), "calibration", (0.0,), (1.0,), original)
    original["nested"]["values"][0] = 100.0
    assert request.parameters["nested"]["values"] == (1.0, 2.0)
    with pytest.raises(TypeError):
        request.parameters["nested"]["new"] = 1
    with pytest.raises(TypeError):
        request.parameters["nested"]["values"][0] = 9
    with pytest.raises(ValueError, match="finite"):
        replace(request, parameters={"nested": [float("nan")]})


def test_raw_json_transport_preserves_exact_bytes_and_excludes_path():
    raw = '{ "source": [1, 2] }\n'
    request = TrialRequest("R13", 3, ("root",), "calibration", (0.0,), (1.0,), {}, input_json=raw)
    assert request.input_json == raw
    with pytest.raises(ValueError, match="never both"):
        replace(request, input_path=Path("/tmp/declared-input.json"))
    selected = SelectedInputs("contract-selected", _spec().identity, "cpu", raw, sha256(raw.encode()).hexdigest())
    assert selected.archive_json == raw
    with pytest.raises(ValueError, match="digest"):
        replace(selected, archive_json=raw + " ")


@pytest.mark.parametrize("payload", ('{"value":NaN}', '{"value":Infinity}', '{"value":1e999}', '{"value":1,"value":2}'))
def test_nonfinite_or_ambiguous_json_is_rejected(payload):
    with pytest.raises(ValueError):
        finite_json(payload)
    with pytest.raises(ValueError):
        replace(_spec(), parameters_json=payload)


def test_design_rejects_cohort_overlap_mutable_menus_and_wrong_nested_types():
    spec = _spec()
    with pytest.raises(ValueError, match="disjoint"):
        replace(spec, evaluation_unit_ids=spec.calibration_unit_ids)
    with pytest.raises(ValueError):
        replace(spec, actions=[D(-1), D(1)])
    with pytest.raises(TypeError, match="exact"):
        replace(spec, receivers=(spec.descriptions[0],))
    with pytest.raises(ValueError, match="memory"):
        replace(spec.descriptions[0], memory_samples=1)
    with pytest.raises(ValueError):
        replace(spec, parameters_json='{"z": 1}')


def test_canonical_rows_reject_float_nan_negative_horizon_and_mutable_coordinates():
    with pytest.raises(TypeError, match="Decimal"):
        PredictorRow("root", D(0), D(1), "response", (("x", 2.0),))
    with pytest.raises(ValueError, match="finite"):
        ForecastRow("root", D(0), D(1), "response", "joint", D("NaN"), "")
    with pytest.raises(ValueError, match="positive"):
        OutcomeRow("root", D(0), D(0), "response", D(0), "supported", "", D(0), ())
    with pytest.raises(TypeError, match="immutable"):
        TrialRow("root", 0.0, 1.0, "response", [["x", 1.0]], 2.0)
    with pytest.raises(ValueError, match="reason"):
        ForecastRow("root", D(0), D(1), "response", "joint", None, "")


def test_negative_finite_results_are_supported_and_unavailable_census_is_retained():
    row = TrialRow("root", -2.0, 1.0, "response", (("x", 1e200),), -1e200)
    assert row.status == "supported"
    unavailable = replace(row, outcome=None, status="unsupported", reason="no-declared-preparation-support")
    batch = TrialBatch("R03", "evaluation", (unavailable,), "supplied-contract-fixture")
    request = TrialRequest("R03", 3, ("root",), "evaluation", (-2.0,), (1.0,), {})
    batch.validate_census(request, ("response",))
    predictors, outcomes = split_batch(batch, _spec().identity, "contract-census")
    assert len(predictors.rows) == len(outcomes.rows) == 1
    assert outcomes.rows[0].reason == "no-declared-preparation-support"
    assert outcomes.rows[0].outcome is None


def test_canonical_table_rejects_forecast_as_outcome_and_wrong_lineage():
    spec = _spec()
    wrong_row = ForecastRow("root", D(0), D(1), "response", "joint", D(1), "")
    with pytest.raises(TypeError, match="exact row"):
        Outcomes("contract-outcomes", spec.identity, (wrong_row,), "fixture", ())
    wrong_identity = ObjectIdentity("wrong", Predictors.SCHEMA, "1.0.0", "0" * 64)
    with pytest.raises(ValueError, match="schema"):
        Predictors("contract-predictors", wrong_identity,
                   (PredictorRow("root", D(0), D(1), "response", (("x", D(1)),)),), "fixture", ())


def test_calibration_requires_exact_matched_source_and_complete_table_join():
    spec = _spec()
    predictors, outcomes = _tables(spec, "calibration")
    with pytest.raises(ValueError, match="censuses"):
        Calibration("contract-calibration", spec.identity, predictors, replace(outcomes, rows=outcomes.rows[:-1]))
    with pytest.raises(ValueError, match="provenance"):
        Calibration("contract-calibration", spec.identity, predictors, replace(outcomes, source_kind="another-source"))
    with pytest.raises(TypeError, match="exact"):
        Calibration("contract-calibration", spec.identity, outcomes, outcomes)


def test_model_keeps_unavailable_fits_but_rejects_zero_scales_and_missing_scores():
    model = _model(_spec())
    unavailable = replace(model.fits[0], coefficients=(), center=(), scale=(), status="unavailable", reason="no-calibration-support")
    assert replace(model, fits=(unavailable, model.fits[1])).fits[0].status == "unavailable"
    with pytest.raises(ValueError, match="positive"):
        replace(model.fits[0], scale=(D(0),))
    with pytest.raises(ValueError, match="scores"):
        replace(model, calibration_scores=(("joint", D(2)),))
    with pytest.raises(ValueError, match="selected"):
        replace(model, selected_description="nonexistent")


def test_forecast_builds_and_requires_complete_rows_and_control_selections():
    forecast = _forecast(_spec())
    assert len(forecast.rows) == 8
    assert forecast.fingerprint()
    with pytest.raises(ValueError, match="omit"):
        replace(forecast, rows=forecast.rows[:-1])
    with pytest.raises(ValueError, match="omit"):
        replace(forecast, selected_actions=forecast.selected_actions[:-1])
    selected = (*forecast.selected_actions[:-1], (*forecast.selected_actions[-1][:3], D(2)))
    with pytest.raises(ValueError, match="absent"):
        replace(forecast, selected_actions=selected)
    assert all(action is None for *_, action in replace(forecast,
        selected_actions=tuple((*row[:3], None) for row in forecast.selected_actions)).selected_actions)


def test_assessment_finite_claim_scope_and_canonical_json_are_enforced():
    spec, forecast = _spec(), _forecast(_spec())
    model = _model(spec)
    _, outcomes = _tables(spec, "evaluation")
    valid = '{"claim_scope":"FINITE_AUTHORED_MENU_AND_TASK_FAMILY","value":null}'
    assessment = Assessment("contract-assessment", spec.identity, model.identity, forecast.identity, outcomes.identity, valid)
    assert assessment.fingerprint()
    with pytest.raises(ValueError, match="universal"):
        replace(assessment, result_json='{"claim_scope":"UNIVERSAL"}')
    with pytest.raises(ValueError, match="canonical"):
        replace(assessment, result_json=valid + " ")
    with pytest.raises(ValueError, match="nonfinite"):
        replace(assessment, result_json='{"claim_scope":"FINITE_AUTHORED_MENU_AND_TASK_FAMILY","value":NaN}')


def test_forecast_construction_work_is_explicit_finite_and_comparable():
    spec = _spec()
    with pytest.raises(ValueError, match="negative"):
        replace(spec.descriptions[0], forecast_work_units=D(-1))
    with pytest.raises(TypeError, match="Decimal"):
        replace(spec.descriptions[0], forecast_work_units=1.0)
    with pytest.raises(ValueError, match="same"):
        replace(spec, descriptions=(spec.descriptions[0], replace(spec.descriptions[1], forecast_work_unit="another-operation")))
    from empirical_lawhood.api.joint_description import new_recipe, specification_from_recipe
    recipe = new_recipe("R07")
    authored = specification_from_recipe(recipe)
    assert all(description.forecast_work_units > 0 for description in authored.descriptions)
    assert len({description.forecast_work_unit for description in authored.descriptions}) == 1
    recipe["descriptions"][0].pop("forecast_work_basis")
    with pytest.raises(ValueError, match="contract field"):
        specification_from_recipe(recipe)


def test_all_twenty_two_authored_presets_pass_pure_owner_validation():
    from empirical_lawhood.api.joint_description import new_recipe, specification_from_recipe
    from empirical_lawhood.domains.joint_description_catalogue import family_module
    for number in range(1, 23):
        family = f"R{number:02d}"
        specification = specification_from_recipe(new_recipe(family))
        family_module(family).validate_specification(specification)


def test_matrix_changed_memory_or_horizon_requires_honest_dimensions_and_work():
    import copy
    from empirical_lawhood.api.joint_description import new_recipe, specification_from_recipe
    from empirical_lawhood.domains.matrix.joint_description.experiments import validate_specification
    recipe = new_recipe("R07")
    changed = copy.deepcopy(recipe)
    changed["parameters"]["memory_depth"] = 3
    with pytest.raises(ValueError, match="dimensions"):
        validate_specification(specification_from_recipe(changed))
    changed = copy.deepcopy(recipe)
    changed["horizons"] = [.032, .128]
    with pytest.raises(ValueError, match="budget"):
        validate_specification(specification_from_recipe(changed))
    changed = copy.deepcopy(recipe)
    changed["parameters"]["q"] = 3
    with pytest.raises(ValueError, match="q=2"):
        validate_specification(specification_from_recipe(changed))


def test_native_feature_history_cannot_be_relabelled_as_free_information():
    import copy
    from empirical_lawhood.api.joint_description import new_recipe, specification_from_recipe
    from empirical_lawhood.domains.joint_description_native import validate_specification
    recipe = copy.deepcopy(new_recipe("R13"))
    description = next(row for row in recipe["descriptions"] if row["id"] == "additive")
    description["memory_samples"] = description["memory_dimension"] = 0
    with pytest.raises(ValueError, match="dimensions"):
        validate_specification(specification_from_recipe(recipe))
