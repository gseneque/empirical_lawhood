# SPDX-License-Identifier: MPL-2.0
"""Pure source-bound three-corner prediction and post-commit assessment."""

from __future__ import annotations

from empirical_lawhood.adapters.physical.rubisco_kinetics.genbank import NativeTeParentConstructV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import WilsonMutantPanelV1
from empirical_lawhood.kernel.provenance import ObjectIdentity

from . import records as r


def _validate_panel(panel, parent):
    if (type(panel) is not WilsonMutantPanelV1 or type(parent) is not NativeTeParentConstructV1
        or panel.parent != parent or ObjectIdentity.from_record(r.PANEL_ID, panel) != r.panel_identity()
        or ObjectIdentity.from_record(r.PARENT_ID, parent) != r.parent_identity()
        or panel.table.source_sha256 != r.SOURCE_ARTICLE_SHA256
        or parent.source_sha256 != r.DEPOSITED_PARENT_SHA256):
        raise ValueError("Wilson combination preparation needs the exact full native panel and deposited parent")


def wilson_quartet_science(panel: WilsonMutantPanelV1,
                          parent: NativeTeParentConstructV1 | None = None) -> r.CombinationScienceV1:
    if type(panel) is not WilsonMutantPanelV1:
        raise ValueError("Wilson combination preparation needs its typed full source panel")
    parent = panel.parent if parent is None else parent
    _validate_panel(panel, parent)
    by_ordinal = {row.native_table_row.ordinal_0based: row for row in panel.rows}
    roster = tuple(r.CombinationSourceDispositionV1(ObjectIdentity.from_record(row.sample_id, row),
        row.native_table_row.ordinal_0based, row.name,
        next((f"SELECTED_{role}" for role, spec in r.CORNER_SPECS.items()
              if spec[0] == row.native_table_row.ordinal_0based), "SOURCE_CONTEXT_ONLY")) for row in panel.rows)
    corners = tuple(r.CombinationCornerV1(role, ObjectIdentity.from_record(by_ordinal[spec[0]].sample_id, by_ordinal[spec[0]]),
        by_ordinal[spec[0]].name, by_ordinal[spec[0]].te_protein_specification) for role, spec in r.CORNER_SPECS.items())
    return r.CombinationScienceV1(r.PREFIX + ".science", r.panel_identity(), r.parent_identity(), r.PROTOCOL_SHA256, roster, corners)


def prepare_roles(panel: WilsonMutantPanelV1, parent: NativeTeParentConstructV1 | None = None):
    """Retain the full source identity while separating three input roles.

    The preparation sees already exposed source labels. This is software role
    separation, never retrospective creation of unexposed biological evidence.
    The full nineteen-row panel remains the separately retained parent.
    """
    science = wilson_quartet_science(panel, parent)
    identity = ObjectIdentity.from_record(science.science_id, science)
    by_sample = {row.sample_id: row for row in panel.rows}
    def observation(sample):
        row = by_sample[sample]
        return r.CombinationObservationV1(sample, row.endpoint("KCAT_C"), row.endpoint("SPECIFICITY_CO"), row)
    training = r.CombinationTrainingV1(r.PREFIX + ".training", identity, science.source_panel,
                                     tuple(observation(sample) for sample in r.TRAINING_IDS))
    features = r.CombinationFeaturesV1(r.PREFIX + ".features", identity, science.source_panel,
                                      next(corner for corner in science.corners if corner.role == "TARGET"))
    labels = r.CombinationLabelsV1(r.PREFIX + ".labels", identity, science.source_panel, observation(r.TARGET_ID))
    return science, training, features, labels


def predict(science: r.CombinationScienceV1, training: r.CombinationTrainingV1,
            features: r.CombinationFeaturesV1) -> r.CombinationForecastV1:
    """Conventional zero-log-interaction point rule; no target label operand."""
    if (type(science) is not r.CombinationScienceV1 or type(training) is not r.CombinationTrainingV1
        or type(features) is not r.CombinationFeaturesV1):
        raise ValueError("combination prediction requires only frozen science, three training corners and target features")
    identity = ObjectIdentity.from_record(science.science_id, science)
    if (training.science != identity or features.science != identity
        or training.source_panel != science.source_panel or features.source_panel != science.source_panel
        or features.target != next(corner for corner in science.corners if corner.role == "TARGET")):
        raise ValueError("combination prediction changes its exact source/science/target recipe")
    members = {member.source_member.object_id: member.source_member for member in science.source_roster}
    if any(ObjectIdentity.from_record(value.native_row.sample_id, value.native_row) != members.get(value.sample_id)
           for value in training.observations):
        raise ValueError("combination prediction changes a frozen native training projection")
    additive, baseline = r.predicted_points(training)
    return r.CombinationForecastV1(r.PREFIX + ".forecast", identity, training, features, additive, baseline)


def commit(science: r.CombinationScienceV1, forecast: r.CombinationForecastV1) -> r.CombinationCommitmentV1:
    """Freeze both endpoint forecasts and the baseline before label access."""
    if type(forecast) is not r.CombinationForecastV1 or type(science) is not r.CombinationScienceV1:
        raise ValueError("combination commitment requires a complete typed frozen forecast")
    if predict(science, forecast.training, forecast.features) != forecast:
        raise ValueError("combination commitment substitutes the complete frozen prediction")
    return r.CombinationCommitmentV1(r.PREFIX + ".commitment", forecast.science,
        ObjectIdentity.from_record(forecast.forecast_id, forecast), forecast)


def evaluate(science: r.CombinationScienceV1, commitment: r.CombinationCommitmentV1,
             labels: r.CombinationLabelsV1) -> r.CombinationEvaluationV1:
    """Validate commitment completely before inspecting the label role."""
    if type(commitment) is not r.CombinationCommitmentV1 or type(science) is not r.CombinationScienceV1:
        raise ValueError("combination assessment requires its prior typed complete commitment")
    if commit(science, commitment.forecast_product) != commitment:
        raise ValueError("combination assessment substitutes its complete prior commitment")
    if (type(labels) is not r.CombinationLabelsV1 or labels.science != commitment.science
        or labels.source_panel != science.source_panel):
        raise ValueError("combination assessment changes its separate target label/source role")
    target = next(corner for corner in science.corners if corner.role == "TARGET")
    if ObjectIdentity.from_record(labels.target.native_row.sample_id, labels.target.native_row) != target.source_member:
        raise ValueError("combination assessment changes its exact native target projection")
    forecast, observed = commitment.forecast_product, labels.target.point()
    errors = tuple(r.CombinationPointErrorV1(method, point, observed, *r.point_errors(point, observed))
        for method, point in (("CONVENTIONAL_ZERO_LOG_INTERACTION", forecast.additive_point), ("PARENT_NO_CHANGE", forecast.parent_point)))
    return r.CombinationEvaluationV1(r.PREFIX + ".evaluation", commitment.science,
        ObjectIdentity.from_record(commitment.commitment_id, commitment), forecast, labels, errors,
        r.parent_log_contrasts(forecast.additive_point, forecast.parent_point),
        r.parent_log_contrasts(observed, forecast.parent_point), r.parent_log_contrasts(observed, forecast.additive_point),
        r.improves_both(forecast.additive_point, forecast.parent_point), r.improves_both(observed, forecast.parent_point))
