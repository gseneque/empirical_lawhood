# SPDX-License-Identifier: MPL-2.0
"""Literal E3 diagnostics and exact consumed joins; no acquired scientific evidence."""
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as legacy
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as configured
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_secondary_readout as science
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_records
from empirical_lawhood.adapters.methods.matrix_factor_response.e3_numerical_methods import log_error
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import MatrixE3ViewOutcome
from empirical_lawhood.adapters.methods.matrix_factor_response.records import SIGNS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_consumer import response_adequacy_values, response_lifetime_values
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore, ScheduledResponseLossCell, ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.api import protected_e3_secondary_read as api
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_e3_protected_methods import causal, reference, source_inputs, stock, scheduled, provenance  # noqa: F401
from tests.test_matrix_configured_protected_e3 import selected as configured_selection, causal as configured_causal


def target():
    # Explicit literal software control. Production must authenticate actual
    # frozen target bytes; this fixture grants no original target provenance.
    return {"normalized_tolerance": D(".01"), "target_origin": reference("target.disclosed.secondary", ScheduledResponseProtocol)}


def disclosed_rows(case, configured_edition=False, *, values=(D(".005"), D(".02"), D(".03")), fine_values=None, missing=None):
    owner = configured if configured_edition else legacy
    forecast_kind = owner.ConfiguredProtectedE3Forecast if configured_edition else owner.ProtectedE3Forecast
    outcome_kind = owner.ConfiguredProtectedE3PairedOutcome if configured_edition else owner.ProtectedE3PairedOutcome
    frozen_kind = owner.ConfiguredProtectedE3FrozenProducts if configured_edition else owner.ProtectedE3FrozenProducts
    models_kind = owner.ConfiguredProtectedE3ModelSet if configured_edition else owner.ProtectedE3ModelSet
    if configured_edition:
        inputs, allocation = configured_selection(case)
        case = SimpleNamespace(**{**vars(case), "inputs": inputs, "allocation": allocation})
    specification, allocation = case.inputs.specification, case.allocation
    rows = []
    for role in ("calibration", "evaluation"):
        for unit in allocation.unit_ids(role):
            source, feature = (configured_causal if configured_edition else causal)(case, unit)
            raw_values = values
            finite = missing is None
            if missing == "NO_CAUSAL_ORIGIN": feature = replace(feature, disposition=missing, values=())
            points = tuple((method.method_key, tuple(log_error(D(".004" if method.method_key == "SPECTRAL_RIDGE" else ".04")) for _ in range(15)))
                for method in specification.methods)
            if feature.disposition != "AVAILABLE": points = tuple((method, (None,) * 15) for method, _ in points)
            forecast = forecast_kind("forecast.disclosed.secondary." + unit, specification.identity, allocation.identity,
                reference("models", models_kind), reference("frozen." + role, frozen_kind), feature, role, points,
                None, "UNCALIBRATED" if role == "calibration" else "INFINITE")
            panels = tuple(reference("panel." + panel + "." + unit, ScheduledResponsePanel) for panel in ("common", "independent"))
            actions = tuple("action.disclosed." + action.lower() for action in specification.measurement.actions)
            cells = []
            for view in ("FINE", "PRIMARY"):
                observed = fine_values if view == "FINE" and fine_values is not None else raw_values
                for panel in panels:
                    for action in actions:
                        for description in specification.measurement.descriptions:
                            for index, horizon in enumerate(science.HORIZONS):
                                vectors = (D(0),) * 48 if finite else None
                                cells.append(ScheduledResponseLossCell(view, panel.object_id, action, description, horizon,
                                    vectors, vectors, vectors, vectors, observed[index] if finite else None))
            cells = tuple(sorted(cells, key=lambda row: row.key))
            controls = tuple(ScheduledResponseTransitionControl("control.scheduled." + source.root_id + "." + view.lower() + "." + panel.object_id + "." + action + "." + sign,
                "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", D(0), D("1e-9"), "SATISFIED",
                128 if view == "PRIMARY" else 256, 192, (D(0),) * (128 if view == "PRIMARY" else 256), ())
                for view in ("FINE", "PRIMARY") for panel in panels for action in actions for sign in (value.lower() for value in SIGNS)) if finite else ()
            score = ScheduledResponseScore("score.disclosed.secondary." + unit, feature.public_source.source, feature.origin,
                science._pin(forecast), reference("physical", protected_prefix_records.ProtectedE3CausalPrefix),
                reference("responses", protected_prefix_records.ProtectedE3CausalPrefix), source.root_id, unit, source.root.root.role.value,
                reference("criterion", ScheduledResponseProtocol), controls, finite, "FINITE" if finite else "NO_ORIGIN" if missing == "NO_CAUSAL_ORIGIN" else "UNEVALUABLE",
                cells, tuple(log_error(value) for value in values) * 5 if finite else (None,) * 15,
                ("UNKNOWN_CONTACT",) if missing == "UNKNOWN_CONTACT" else ("disclosed-secondary-control",))
            views = tuple(MatrixE3ViewOutcome(view, tuple(fine_values if view == "fine" and fine_values is not None else values) * 5 if finite else (None,) * 15,
                ("FINITE" if finite else "UNKNOWN_CONTACT" if missing == "UNKNOWN_CONTACT" else "UNAVAILABLE",) * 15) for view in ("fine", "primary"))
            outcome = outcome_kind("outcome.disclosed.secondary." + unit, feature, science._pin(forecast),
                science.source_identity(score), sha256(canonical_json_bytes(cells)).hexdigest(), reference("protocol." + unit, ScheduledResponseProtocol), panels,
                views, "SATISFIED" if finite else "UNEVALUABLE")
            rows.append((role, outcome, forecast, score))
    return specification, allocation, tuple(rows)


@pytest.mark.parametrize("configured_edition", (False, True))
def test_complete_both_editions_preserve_original_criterion_and_show_degenerate_lifetime(source_inputs, configured_edition):  # noqa: F811
    specification, allocation, rows = disclosed_rows(source_inputs, configured_edition)
    original_bytes = tuple(record.canonical_bytes() for _, *records in rows for record in records)
    result = science.secondary_response_projection(specification, allocation, rows, **target())
    assert result["normalized_tolerance"] == {"decimal": "0.01"}
    assert specification.measurement.target_discrepancy_tolerance != D(".01")
    assert len(result["adequacy"]) == len(rows) * 2 * 3
    assert len(result["failure_detection"]) == len(rows) * 2 * 3 * 3
    assert all(row["last_definite_pass"] == 16 and row["first_definite_failure"] == 64 for row in result["useful_lifetimes"])
    assert all(row["degenerate_complete_lifetime_labels"] and row["distinct_lifetime_patterns"] == 1 for row in result["lifetime_pattern_census"])
    assert {row["decision"] for row in result["failure_detection"]} == {"CORRECT_PASS", "MISSED_FAILURE", "FALSE_ALARM", "DETECTED_FAILURE"}
    for role in ("calibration", "evaluation"):
        assert result["counts"][role]["assigned_independent_units"] == len(allocation.unit_ids(role))
        assert result["counts"][role]["nested_views_per_unit"] == 2
    assert tuple(record.canonical_bytes() for _, *records in rows for record in records) == original_bytes


@pytest.mark.parametrize("missing,status", (("UNKNOWN_CONTACT", "UNKNOWN_CONTACT"), ("NO_CAUSAL_ORIGIN", "KNOWN_NONUSE"), ("UNAVAILABLE", "UNAVAILABLE")))
def test_nonuse_and_unknown_remain_in_every_assigned_denominator(source_inputs, missing, status):  # noqa: F811
    specification, allocation, rows = disclosed_rows(source_inputs, missing=missing)
    result = science.secondary_response_projection(specification, allocation, rows, **target())
    assert len(result["useful_lifetimes"]) == len(rows) * 2
    assert all(row["censoring_status"] == status for row in result["useful_lifetimes"])
    assert all(row["first_definite_failure"] is None for row in result["useful_lifetimes"])
    assert all(row["classification"] != "FINITE_INADEQUATE" for row in result["adequacy"])
    assert all(row["decision"] == ("KNOWN_NONUSE" if missing == "NO_CAUSAL_ORIGIN" else "ACTUAL_UNRESOLVED") for row in result["failure_detection"])


def test_views_can_disagree_and_survival_is_right_censored_without_revising_lattice(source_inputs):  # noqa: F811
    specification, allocation, rows = disclosed_rows(source_inputs, fine_values=(D(".005"),) * 3)
    report = science.secondary_response_projection(specification, allocation, rows, **target())
    assert {row["censoring_status"] for row in report["useful_lifetimes"] if row["view"] == "fine"} == {"RIGHT_CENSORED_AT_LAST_HORIZON"}
    assert {row["first_definite_failure"] for row in report["useful_lifetimes"] if row["view"] == "primary"} == {64}


@pytest.mark.parametrize("damage", ("omission", "duplicate", "forecast", "source", "cells-hash", "paired-values", "receiver", "cell"))
def test_original_input_ancestry_and_complete_cells_cannot_be_republished_away(source_inputs, damage):  # noqa: F811
    specification, allocation, rows = disclosed_rows(source_inputs)
    role, outcome, forecast, score = rows[0]
    if damage == "omission": changed = rows[:-1]
    elif damage == "duplicate": changed = (rows[0], *rows[:-1])
    else:
        if damage == "forecast": forecast = replace(forecast, record_id=forecast.record_id + ".foreign")
        elif damage == "source": score = replace(score, source=replace(score.source, object_fingerprint="f" * 64))
        elif damage == "cells-hash": outcome = replace(outcome, original_cells_sha256="f" * 64)
        elif damage == "paired-values": outcome = replace(outcome, views=tuple(replace(view, errors=(D(1),) * 15) for view in outcome.views))
        else:
            cells = score.cells[:-1] if damage == "cell" else (replace(score.cells[0], actual_odd_responses=(D(0),) * 47), *score.cells[1:])
            score = replace(score, cells=cells)
            outcome = replace(outcome, original_score=science.source_identity(score), original_cells_sha256=sha256(canonical_json_bytes(cells)).hexdigest())
        changed = ((role, outcome, forecast, score), *rows[1:])
    with pytest.raises(PermissionError): science.secondary_response_projection(specification, allocation, changed, **target())


def test_native_adequacy_is_retained_when_original_predictor_has_no_point(source_inputs):  # noqa: F811
    specification, allocation, rows = disclosed_rows(source_inputs)
    role, outcome, forecast, score = rows[0]
    forecast = replace(forecast, log_points=tuple((method, (None,) * 15) for method, _ in forecast.log_points))
    score = replace(score, error_forecast=science._pin(forecast))
    outcome = replace(outcome, forecast=science._pin(forecast), original_score=science.source_identity(score))
    result = science.secondary_response_projection(specification, allocation, ((role, outcome, forecast, score), *rows[1:]), **target())
    assert {row["decision"] for row in result["failure_detection"] if row["unit_id"] == outcome.unit_id} == {"FORECAST_NONUSE"}
    assert {row["classification"] for row in result["adequacy"] if row["unit_id"] == outcome.unit_id} == {"FINITE_ADEQUATE", "FINITE_INADEQUATE"}


def test_exact_retained_interval_math_preserves_boundary_nonuse_and_censoring():
    assert response_adequacy_values("FINITE_POINT", D(".01"), D(".01"), D(".01")) == ("FINITE_ADEQUATE", True, True)
    assert response_adequacy_values("UNRESOLVED_INTERVAL", D(0), None, D(".01")) == ("UNRESOLVED", False, True)
    assert response_adequacy_values("KNOWN_NONUSE_INFINITY", D(0), None, D(".01")) == ("KNOWN_NONUSE", False, False)
    cells = (science._Cell(16, "FINITE_ADEQUATE", True, True, "CROSSCHECKED_FINITE"),
        science._Cell(64, "UNRESOLVED", False, True, "UNKNOWN_CONTACT"),
        science._Cell(128, "FINITE_INADEQUATE", False, False, "CROSSCHECKED_FINITE"))
    assert response_lifetime_values(cells)[:6] == (16, 64, 128, None, "INTERVAL_CENSORED_FAILURE", tuple(row.source_disposition for row in cells))


def consumed_fixture(specification, allocation, rows, owner):
    records, receipts, tasks, terminals = {}, {}, [], {}
    for role, operation in (("calibration", "calibrate"), ("evaluation", "assess")):
        task_id = role + ".statistic"
        edges, inputs, outcomes, forecasts = [], [], [], []
        for selected_role, outcome, forecast, score in rows:
            if selected_role != role: continue
            output_task, forecast_task = "score." + outcome.unit_id, "forecast." + outcome.unit_id
            for task, record, schema, logical in ((output_task, outcome, type(outcome).SCHEMA, "logical.outcome." + outcome.unit_id),
                    (forecast_task, forecast, type(forecast).SCHEMA, "logical.forecast." + outcome.unit_id)):
                physical = SimpleNamespace(logical_artifact_id=logical, materialization_id="material." + logical)
                receipts[task] = SimpleNamespace(output_logical_artifacts=(SimpleNamespace(payload_schema=schema, logical_artifact_id=logical),), output_materializations=(physical,))
                edges.append(SimpleNamespace(payload_schema=schema, producer_task_id=task, operational_logical_artifact_id=logical))
                inputs.append(physical.materialization_id)
                records[task, type(record)] = record
            records[output_task, ScheduledResponseScore] = score
            outcomes.append(science._pin(outcome)); forecasts.append(science._pin(forecast))
        receipts[task_id] = SimpleNamespace(input_materialization_ids=tuple(inputs))
        tasks.append(SimpleNamespace(task_id=task_id, scientific_inputs=tuple(edges)))
        terminals[role] = SimpleNamespace(outcomes=tuple(outcomes), forecasts=tuple(forecasts))
    calls = []
    def product(writer, plan, actual_receipts, task, kind):
        assert actual_receipts is receipts
        calls.append((task, kind))
        return records[task, kind], {"disclosed-product": task}
    def task_id(spec, allocated, operation):
        assert spec == specification.identity and allocated == allocation.identity
        return ("calibration" if operation == "calibrate" else "evaluation") + ".statistic"
    return dict(specification=specification, allocation=allocation, calibration=terminals["calibration"], assessment=terminals["evaluation"],
        writer=object(), plan=SimpleNamespace(tasks=tuple(tasks)), receipts=receipts,
        product_reader=product, statistical_task_id=task_id), calls


@pytest.mark.parametrize("configured_edition", (False, True))
def test_secondary_reader_reuses_one_verified_plan_and_exact_consumed_products(source_inputs, configured_edition):  # noqa: F811
    specification, allocation, rows = disclosed_rows(source_inputs, configured_edition)
    selected, calls = consumed_fixture(specification, allocation, rows, api)
    report, custody = api.read_secondary_response(**selected, configured_edition=configured_edition, **target())
    assert len(custody) == len(rows) and len(calls) == len(rows) * 3
    assert report["primary_continuous_error_criterion"] == "UNCHANGED"
    assert len({id(selected["plan"]) for _ in calls}) == 1
    task = selected["plan"].tasks[0]
    edge = task.scientific_inputs[0]
    original = edge.operational_logical_artifact_id
    edge.operational_logical_artifact_id += ".foreign"
    with pytest.raises(PermissionError, match="consumed typed output"):
        api.read_secondary_response(**selected, configured_edition=configured_edition, **target())
    edge.operational_logical_artifact_id = original
    receipt = selected["receipts"][task.task_id]
    receipt.input_materialization_ids = receipt.input_materialization_ids[1:]
    with pytest.raises(PermissionError, match="consumed parent materialization"):
        api.read_secondary_response(**selected, configured_edition=configured_edition, **target())
