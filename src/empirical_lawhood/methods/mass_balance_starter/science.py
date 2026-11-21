# SPDX-License-Identifier: MPL-2.0
"""An editable prediction and a separate falsifier using final observations."""

from dataclasses import replace
from decimal import localcontext

from empirical_lawhood.methods.mass_balance_starter.records import MassAssessment, MassFinding, MassForecast, MassOutcomes, MassPredictors, PredictedMass


def predict_final_mass(initial_kg, added_kg):
    """The contributor's calculation. It receives no final observation."""
    with localcontext() as context:
        context.prec = 100
        return initial_kg + added_kg


def predict(config, predictors):
    if type(predictors) is not MassPredictors or config.phase != "predict":
        raise TypeError("prediction requires the exact predictor role")
    if (predictors.identity != config.predictors or predictors.scope != config.scope
            or tuple(row.unit_id for row in predictors.rows) != config.independent_unit_ids):
        raise ValueError("prediction changes original input identity, scope or independent-unit census")
    return MassForecast(config.node_id + ".product", config,
        tuple(PredictedMass(row.unit_id, predict_final_mass(row.initial_kg, row.added_kg)) for row in predictors.rows))


def prediction_config(config):
    return replace(config, config_id=config.config_id.removesuffix(".assess") + ".predict",
                   phase="predict", outcomes=None, tolerance_kg=None)


def assess(config, forecast, outcomes):
    """Use independent final observations; do not rerun the prediction model."""
    if type(forecast) is not MassForecast or type(outcomes) is not MassOutcomes or config.phase != "assess":
        raise TypeError("assessment requires its exact forecast and final-observation roles")
    if (forecast.config != prediction_config(config) or outcomes.identity != config.outcomes
            or outcomes.scope != config.scope or tuple(row.unit_id for row in outcomes.rows) != config.independent_unit_ids):
        raise ValueError("assessment changes its original predictor, outcome identity, scope or census")
    findings = []
    for prediction, outcome in zip(forecast.rows, outcomes.rows, strict=True):
        error, disposition, reasons = None, "UNEVALUABLE", ("FINAL_OBSERVATION_MISSING",)
        if outcome.final_kg is not None:
            with localcontext() as context:
                context.prec = 100
                error = abs(outcome.final_kg - prediction.final_kg)
            disposition = "SATISFIED" if error <= config.tolerance_kg else "FALSIFIED"
            reasons = () if disposition == "SATISFIED" else ("MASS_RESIDUAL_EXCEEDS_TOLERANCE",)
        findings.append(MassFinding(prediction.unit_id, prediction.final_kg, outcome.final_kg, error, disposition, reasons))
    return MassAssessment(config.node_id + ".product", config, forecast.identity, tuple(findings))
