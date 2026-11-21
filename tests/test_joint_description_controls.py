"""Guard, calibration and independent-root controls for finite menu inference."""

from decimal import Decimal as D
from dataclasses import replace
import json

import pytest

from empirical_lawhood.design.joint_description import (
    Description, Economics, JointSpecification, ReceiverPolicy,
)
from empirical_lawhood.methods.joint_description import (
    _summary, assess_descriptions, fit_response_laws, forecast_and_choose,
)
from empirical_lawhood.science.joint_description import (
    Calibration, TrialBatch, TrialRow, split_batch,
)


def _spec(*, safety_upper=None, max_error="10"):
    return JointSpecification(
        "fixture-joint-spec", "R20", "finite control test", 5,
        ("calibration-a", "calibration-b"), ("evaluation-a", "evaluation-b"),
        (D(0), D(1)), (D(1),),
        (ReceiverPolicy("receiver", "fixture-unit", D(0), D(1), D(max_error), D(1),
                        safety_upper=safety_upper),),
        (Description("joint", ("joint_prediction",), "fixed", 2, 0, 0, 0, "fixture joint"),
         Description("reduced", ("reduced_prediction",), "fixed", 1, 0, 0, 0, "fixture reduced")),
        "{}", Economics(state_price=D(0), interface_price=D(0), memory_price=D(0),
                         compute_price=D(0), missing_penalty=D(100), safety_penalty=D(1000)),
    )


def _batch(spec, split, predictions, outcomes=(0.0, 1.0)):
    units = spec.calibration_unit_ids if split == "calibration" else spec.evaluation_unit_ids
    rows = []
    for unit in units:
        for action in (0, 1):
            supported = outcomes[action] is not None
            for receiver in spec.receivers:
                rows.append(TrialRow(unit, float(action), 1.0, receiver.receiver_id,
                    (("joint_prediction", predictions[0][action]),
                     ("reduced_prediction", predictions[1][action])), outcomes[action],
                    "supported" if supported else "failed", "" if supported else "fixture-native-failure"))
    return TrialBatch("R20", split, tuple(rows), "independent-test-fixture")


def _fit(spec, predictions, observed=(0.0, 1.0)):
    predictors, outcomes = split_batch(_batch(spec, "calibration", predictions, observed), spec.identity, "fixture-cal")
    calibration = Calibration("fixture-calibration", spec.identity, predictors, outcomes)
    return fit_response_laws(spec, calibration, record_id="fixture-model")


@pytest.mark.numerical(oracle="manual two-action control losses: 1+.36/100 versus 0+1/100")
def test_crossfit_selection_includes_outcome_loss_of_predicted_action():
    spec = _spec()
    # Joint has smaller prediction MSE but chooses the harmful action.
    # Reduced is less accurate in level but chooses the useful action.
    model = _fit(spec, ((0.6, 0.4), (-1.0, 2.0)))
    scores = dict(model.calibration_scores)
    assert float(scores["joint"]) == pytest.approx(1.0036)
    assert float(scores["reduced"]) == pytest.approx(0.01)
    assert model.selected_description == "reduced"


def test_all_predicted_unsafe_actions_produce_no_entry():
    spec = _spec(safety_upper=D(1))
    model = _fit(spec, ((2.0, 3.0), (2.0, 3.0)))
    predictors, _ = split_batch(_batch(spec, "evaluation", ((2.0, 3.0), (2.0, 3.0))), spec.identity, "fixture-eval")
    forecast = forecast_and_choose(spec, model, predictors, record_id="fixture-forecast")
    assert all(action is None for _unit, _horizon, _description, action in forecast.selected_actions)


def test_incomplete_action_menu_cannot_look_like_zero_oracle_regret():
    spec = _spec()
    predictions = ((0.0, 1.0), (0.0, 1.0))
    model = _fit(spec, predictions)
    predictors, outcomes = split_batch(_batch(spec, "evaluation", predictions, (0.0, None)), spec.identity, "fixture-eval")
    forecast = forecast_and_choose(spec, model, predictors, record_id="fixture-forecast")
    assessment = assess_descriptions(spec, model, forecast, outcomes, record_id="fixture-assessment")
    report = json.loads(assessment.result_json)
    for description in report["descriptions"]:
        assert description["control_coverage"] == 1
        assert description["complete_action_menus"] == 0
        assert description["paired_action_panel_regret"]["mean"] == 100
        assert not description["useful_under_authored_thresholds"]


@pytest.mark.numerical(oracle="sample standard error for two independent roots 1 and 3 is exactly 1")
def test_root_summary_has_finite_independent_unit_uncertainty():
    summary = _summary([1.0, 3.0])
    assert summary["independent_roots"] == 2
    assert summary["mean"] == 2
    assert summary["standard_error"] == pytest.approx(1)
    with pytest.raises(ValueError, match="finite"):
        _summary([float("inf"), 3.0])


@pytest.mark.numerical(oracle="same exact predictions and chosen action;100 versus1 authored construction units at0.5 per unit changes cost by49.5")
def test_expensive_fixed_forecast_construction_is_not_hidden_by_one_feature():
    from empirical_lawhood.methods.joint_description import description_cost
    spec = _spec()
    expensive = replace(spec.descriptions[0], forecast_work_units=D(100),
                        forecast_work_unit="fixture-operation", forecast_work_basis="independent fixture estimate")
    cheap = replace(spec.descriptions[1], forecast_work_units=D(1),
                    forecast_work_unit="fixture-operation", forecast_work_basis="independent fixture estimate")
    spec = replace(spec, descriptions=(expensive, cheap),
                   economics=replace(spec.economics, compute_price=D("0.5")))
    assert description_cost(expensive, spec.economics) - description_cost(cheap, spec.economics) == 49.5
    model = _fit(spec, ((0.0, 1.0), (0.0, 1.0)))
    assert model.selected_description == "reduced"


@pytest.mark.numerical(oracle="normalized weighted mean: (.5*1+.5*1)/(.5+.5)=1 at both calibration and evaluation")
def test_normalized_receiver_weights_do_not_divide_prediction_loss_twice():
    spec = _spec(max_error="1")
    spec = replace(spec, receivers=tuple(
        ReceiverPolicy(name, "fixture-unit", D(0), D(1), D(1), D("0.5"))
        for name in ("receiver-a", "receiver-b")))
    predictions = ((1.0, 1.0), (1.0, 1.0))
    model = _fit(spec, predictions, observed=(0.0, 0.0))
    assert dict(model.calibration_scores) == {"joint": D(1), "reduced": D(1)}
    predictors, outcomes = split_batch(_batch(spec, "evaluation", predictions, (0.0, 0.0)), spec.identity, "fixture-eval")
    forecast = forecast_and_choose(spec, model, predictors, record_id="fixture-forecast")
    assessment = assess_descriptions(spec, model, forecast, outcomes, record_id="fixture-assessment")
    assert all(row["all_use_normalized_prediction_loss"]["mean"] == 1.0
               for row in json.loads(assessment.result_json)["descriptions"])


def test_pareto_front_retains_state_vs_construction_work_tradeoff():
    spec = _spec()
    spec = replace(spec, descriptions=(
        replace(spec.descriptions[0], state_dimension=1, forecast_work_units=D(100)),
        replace(spec.descriptions[1], state_dimension=2, forecast_work_units=D(1))))
    predictions = ((0.0, 1.0), (0.0, 1.0))
    model = _fit(spec, predictions)
    predictors, outcomes = split_batch(_batch(spec, "evaluation", predictions), spec.identity, "fixture-eval")
    forecast = forecast_and_choose(spec, model, predictors, record_id="fixture-forecast")
    assessment = assess_descriptions(spec, model, forecast, outcomes, record_id="fixture-assessment")
    report = json.loads(assessment.result_json)
    assert set(report["nondominated_descriptions"]) == {"joint", "reduced"}
    assert "authored_forecast_construction_plus_evaluator_work" in report["nondominated_vector_axes"]
