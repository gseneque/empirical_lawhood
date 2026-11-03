# SPDX-License-Identifier: MPL-2.0
"""Disclosed literal all-horizon controls; no native acquisition or qualification."""
from dataclasses import replace
from decimal import Decimal as D, localcontext

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_secondary_readout as science
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import forecast_selected_point
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPublicProgramme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from tests.test_matrix_selected_protected import transfer, confirmation  # noqa: F401
from tests.test_matrix_selected_opportunity import opportunity, literal_observations  # noqa: F401


def projected(programme, observations):
    groups = (("opportunity" if programme.phase == "E5_OPPORTUNITY" else "confirmation",
        tuple(sorted({case.unit_id for case in programme.roster.cases}))),)
    if programme.phase == "E6_TRANSFER":
        allocation = programme.point_design.package.allocation
        groups = tuple((role, allocation.unit_ids(role)) for role in ("transfer_nearby", "transfer_shifted"))
    return science.prepared_secondary_projection(programme, observations, groups)


def changed_values(observations, key, values, *, missing=None, fine=None):
    point, mechanical, score = observations[key]
    cells = []
    for cell in score.cells:
        error = (fine if cell.view == "FINE" and fine is not None else values)[science.HORIZONS.index(cell.horizon_tick)]
        cells.append(replace(cell, normalized_error=error))
    cumulative = []
    for predictor in science.PREDICTORS:
        for horizon in science.HORIZONS:
            raw = tuple(cell.normalized_error for cell in cells if cell.view == "PRIMARY" and cell.predictor == predictor and cell.horizon_tick <= horizon)
            with localcontext() as context:
                context.prec = 50
                cumulative.append(None if any(value is None for value in raw) else (D(1) + max(raw)).ln())
    score = replace(score, cells=tuple(cells), cumulative_log_errors=tuple(cumulative), disposition="PARTIAL" if missing else "FINITE")
    return {**observations, key: (point, mechanical, score)}


@pytest.mark.parametrize("name", ("transfer", "confirmation", "opportunity"))
def test_all_assigned_arms_views_descriptions_and_horizons_use_actual_frozen_criterion(request, name):
    programme = request.getfixturevalue(name)
    observations = literal_observations(programme)
    before = {key: tuple(value.canonical_bytes() for value in row) for key, row in observations.items()}
    result = projected(programme, observations)
    n = len(programme.roster.cases)
    assert len(result["adequacy"]) == n * 2 * 15
    assert len(result["useful_lifetimes"]) == n * 2 * 5
    assert len(result["failure_detection"]) == n * 2 * 15 * 3
    assert result["normalized_tolerance"] == {"decimal": str(programme.criterion.normalized_error_maximum.normalize())}
    assert sum(row["assigned_cases"] for row in result["counts"]) == n
    assert all(row["nested_views_per_case"] == 2 and row["nested_receivers_per_cell"] == 48 for row in result["counts"])
    assert result["point_uncertainty"] == result["admission"] == result["service"] == "UNESTABLISHED"
    assert {key: tuple(value.canonical_bytes() for value in row) for key, row in observations.items()} == before


def test_first_failure_partial_censoring_and_point_nonuse_remain_separate(transfer):  # noqa: F811
    # Literal observations use the actual public point payload identity.
    programme = MatrixSelectedPublicProgramme.from_programme(transfer)
    observations = literal_observations(programme)
    key = next(iter(observations))
    tolerance = programme.criterion.normalized_error_maximum
    observations = changed_values(observations, key, (tolerance / 2, tolerance * 2, None), missing=True)
    point, mechanical, score = observations[key]
    feature = replace(point.feature, disposition="UNAVAILABLE", values=())
    observations[key] = forecast_selected_point(programme.point_design, feature, record_id=point.record_id), mechanical, score
    result = projected(programme, observations)
    selected = tuple(row for row in result["useful_lifetimes"] if row["case_id"] == key)
    assert all(row["last_definite_pass"] == 16 and row["first_definite_failure"] == 64 for row in selected)
    assert all(row["censoring_status"] == "FIRST_FAILURE_ON_LATTICE" for row in selected)
    decisions = tuple(row for row in result["failure_detection"] if row["case_id"] == key)
    assert all(row["decision"] == ("ACTUAL_UNRESOLVED" if row["horizon"] == 128 else "FORECAST_NONUSE") for row in decisions)
    assert all(row["classification"] == "FINITE_ADEQUATE" for row in result["adequacy"] if row["case_id"] == key and row["horizon"] == 16)
    # A later missing sample never rewrites the already observed first failure.
    observations = changed_values(observations, key, (tolerance / 2,) * 3)
    assert all(row["censoring_status"] == "RIGHT_CENSORED_AT_LAST_HORIZON" for row in projected(programme, observations)["useful_lifetimes"] if row["case_id"] == key)


def test_no_origin_missing_and_paired_discrepancy_keep_complete_denominators(transfer):  # noqa: F811
    observations = literal_observations(transfer)
    key = next(iter(observations))
    point, mechanical, score = observations[key]
    source = next(source for _, source in transfer.sources.source_arms() if "case." + source.source_id == key)
    branches = tuple(branch for branch, *_ in branch_census(transfer.protocol(source), dict(transfer.panels)[source.root.root.independent_group_id]))
    cells = tuple(replace(cell, actual_odd_responses=None, signed_errors=None, absolute_errors=None, relative_errors=None, normalized_error=None) for cell in score.cells)
    no_origin = replace(score, forecast=None, controls=(), cells=cells, numerical_pass=False,
        disposition="NO_ORIGIN", cumulative_log_errors=(None,) * 15, unentered_branch_ids=branches)
    observations[key] = point, mechanical, no_origin
    report = projected(transfer, observations)
    assert all(row["censoring_status"] == "KNOWN_NONUSE" and row["first_definite_failure"] is None for row in report["useful_lifetimes"] if row["case_id"] == key)
    observations[key] = None
    report = projected(transfer, observations)
    assert all(row["classification"] == "UNRESOLVED" for row in report["adequacy"] if row["case_id"] == key)
    observations = literal_observations(transfer)
    limit = transfer.criterion.paired_view_discrepancy_maximum
    observations = changed_values(observations, key, (D(0),) * 3, fine=(limit + 1,) * 3)
    report = projected(transfer, observations)
    assert all(row["source_disposition"] == "PAIRED_VIEW_DISCREPANCY" for row in report["adequacy"] if row["case_id"] == key)
    assert sum(row["assigned_cases"] for row in report["counts"]) == len(transfer.roster.cases)


@pytest.mark.parametrize("damage", ("case", "source", "panel", "receiver", "cell"))
def test_exact_terminal_ancestry_and_complete_nested_census_refuse(transfer, damage):  # noqa: F811
    observations = literal_observations(transfer)
    key = next(iter(observations))
    with pytest.raises((ValueError, TypeError)):
        if damage == "case": observations.pop(key)
        else:
            point, mechanical, score = observations[key]
            if damage == "source": score = replace(score, source=replace(score.source, object_fingerprint="f" * 64))
            elif damage == "panel": score = replace(score, panels=(replace(score.panels[0], object_fingerprint="f" * 64), score.panels[1]))
            elif damage == "receiver": score = replace(score, cells=(replace(score.cells[0], actual_odd_responses=(D(0),) * 47), *score.cells[1:]))
            else: score = replace(score, cells=score.cells[:-1])
            observations[key] = point, mechanical, score
        projected(transfer, observations)
