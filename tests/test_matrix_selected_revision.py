# SPDX-License-Identifier: MPL-2.0
"""Exact selected revision handoff over original in-memory E4 products."""

from dataclasses import replace
from decimal import Decimal

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision as selected
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration import calibrate_revision
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_programme_selection import exposed  # noqa: F401
from tests.test_matrix_revision_calibration import calibrated  # noqa: F401


def adapted(case, *, calibration=None, data=None):
    return selected.adapt_e4_frozen_package(record_id="package.selected-revision-control", development=case.development,
        nomination=case.nomination, frozen=case.frozen, calibration_programme=case.programme,
        calibration=case.result if calibration is None else calibration, reduction=case.reduction,
        data=case.data if data is None else data, forecasts=case.forecasts,
        upstream_fit_unit_ids=case.development.group_ids, selection_unit_ids=case.programme.group_ids)


def test_actual_pair_coefficients_transforms_and_distinct_whole_group_calibration_are_retained(calibrated):  # noqa: F811
    value = adapted(calibrated)
    assert value.calibration.revision_model is calibrated.nomination.revision_model
    assert value.calibration.baseline_model is calibrated.nomination.baseline_model
    assert value.calibration_method == "WHOLE_GROUP_MAX_POSITIVE_PAIRED_LOG_RESIDUAL_NINE_COORDINATES_ALL30"
    assert value.endpoint_order[0] == ("PRIMARY", "FACTOR", 1)
    assert value.endpoint_order[15] == ("FINE", "FACTOR", 1)
    assert value.calibration.rank == 62 and len(value.calibration.group_ids) == 64
    assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
    actual = dict(selected.predict_revision_coordinate(value, calibrated.data.cases[0].coordinate))
    assert actual["REVISION"] == calibrated.forecasts[0].revision_predictions
    assert actual["BASELINE"] == calibrated.forecasts[0].baseline_predictions


def test_non_grid_transfer_coordinate_cannot_silently_receive_center_features(calibrated):  # noqa: F811
    value = adapted(calibrated)
    coordinate = calibrated.data.cases[0].coordinate
    changed = replace(coordinate, primary_view=replace(coordinate.primary_view, bath_temperature=Decimal("1.25")),
        fine_view=replace(coordinate.fine_view, bath_temperature=Decimal("1.25")))
    with pytest.raises(ValueError, match="non-grid point"):
        selected.predict_revision_coordinate(value, changed)


def test_original_infinite_revision_bounds_and_complete_missing_group_census_survive(calibrated):  # noqa: F811
    absent = set(calibrated.programme.group_ids[:3])
    data = replace(calibrated.data, cases=tuple(row for row in calibrated.data.cases
        if row.causal_prefix.root.independent_group_id not in absent))
    result = calibrate_revision(calibrated.specification, calibrated.development, calibrated.nomination,
        calibrated.frozen, calibrated.programme, calibrated.reduction, data, calibrated.forecasts, record_id="calibration.selected-missing")
    value = adapted(calibrated, calibration=result, data=data)
    assert value.calibration.revision_radius is None and value.calibration.baseline_radius is None
    assert {group for group, score in value.calibration.revision_scores if score is None} == absent
    assert len(value.calibration.group_ids) == 64
    assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value


def test_revision_handoff_replays_actual_models_and_assessment_before_accepting(calibrated):  # noqa: F811
    first = calibrated.forecasts[0]
    wrong = replace(first, revision_predictions=tuple(value + Decimal(1) for value in first.revision_predictions))
    with pytest.raises(ValueError, match="prediction"):
        selected.adapt_e4_frozen_package(record_id="package.bad-prediction", development=calibrated.development,
            nomination=calibrated.nomination, frozen=calibrated.frozen, calibration_programme=calibrated.programme,
            calibration=calibrated.result, reduction=calibrated.reduction, data=calibrated.data,
            forecasts=(wrong, *calibrated.forecasts[1:]), upstream_fit_unit_ids=calibrated.development.group_ids,
            selection_unit_ids=calibrated.programme.group_ids)
    value = adapted(calibrated)
    with pytest.raises(ValueError, match="fitted or calibrated"):
        replace(value, upstream_fit_unit_ids=())
    with pytest.raises(TypeError, match="actual calibration"):
        adapted(calibrated, calibration=calibrated.result.identity)
    with pytest.raises(ValueError, match="upstream"):
        value.require_unused_groups(calibrated.development.group_ids)


@pytest.mark.parametrize("phase", selected.DOWNSTREAM_PHASES)
def test_both_revision_radii_remain_carried_without_a_preparation_or_transfer_warrant(calibrated, phase):  # noqa: F811
    value = adapted(calibrated)
    with pytest.raises(ValueError, match=selected.POINT_ONLY):
        selected.require_revision_downstream_calibration(value, phase=phase)
