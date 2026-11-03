# SPDX-License-Identifier: MPL-2.0
"""Literal four-action E4 target controls; no native or qualification evidence."""

from dataclasses import replace
from decimal import Decimal, localcontext
from itertools import product

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, PREDICTORS
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_selection as method
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseLossCell, ScheduledResponseScore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_prepared_assay_method import literal_protocol
from tests.test_matrix_programme_selection import pin


def _protocol_score():
    original_protocol, _ = literal_protocol()
    protocol = replace(original_protocol, protocol_id="protocol.literal.e4-action-census",
        criterion=pin("criterion.literal.e4-action-census", method.MatrixResponseFrontierProtocol.SCHEMA))
    panels = ("panel.literal.common", "panel.literal.independent")
    cells = []
    for view, panel, (action_index, action), (predictor_index, predictor), horizon in product(
            method.VIEWS, panels, enumerate(protocol.actions), enumerate(PREDICTORS), protocol.horizon_steps):
        value = Decimal(action_index + 1) + Decimal(predictor_index) / 10 + Decimal(horizon) / 10000
        value += Decimal(view == "FINE") / 8 + Decimal(panel == panels[-1]) / 100
        cells.append(ScheduledResponseLossCell(view, panel, action.action_id, predictor, horizon,
            None, None, None, None, value))
    cells = tuple(sorted(cells, key=lambda row: row.key))
    with localcontext() as context:
        context.prec = 50
        primary = tuple((Decimal(1) + max(row.normalized_error for row in cells
            if row.view == "PRIMARY" and row.predictor == predictor and row.horizon_tick <= horizon)).ln()
            for predictor, horizon in product(PREDICTORS, protocol.horizon_steps))
    public = protocol.public_source
    control = ScheduledResponseTransitionControl("control.literal.e4-action-census",
        "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", Decimal(0), Decimal(".01"),
        "SATISFIED", 1, 192, (Decimal(0),), ())
    score = ScheduledResponseScore("score.literal.e4-action-census", public.source,
        pin("prefix.literal.e4-action-census", "empirical-lawhood/matrix-scheduled-history/causal-prefix"),
        pin("forecast.literal.e4-action-census", "empirical-lawhood/matrix-scheduled-history/forecast-seal"),
        pin("physical.literal.e4-action-census", "empirical-lawhood/matrix-scheduled-history/response-forecast"),
        pin("responses.literal.e4-action-census", "empirical-lawhood/matrix-scheduled-history/native-responses"),
        public.root.root_id, public.root.independent_group_id, public.root.role.value, protocol.criterion,
        (control,), True, "FINITE", cells, primary, ())
    target = method.ScheduledRevisionTarget("target.literal.e4-action-census", protocol.criterion,
        protocol.horizon_steps, method.VIEWS, "CUMULATIVE_LOG1P_NORMALIZED_RESPONSE_ERROR_ALL15")
    return protocol, target, score


def test_actual_protocol_four_actions_and_all240_cells_reduce_to_original_paired30_targets():
    protocol, target, score = _protocol_score()
    before = score.canonical_bytes()
    assert tuple(action.role for action in protocol.actions) == ACTION_ROLES
    assert len(score.cells) == 2 * 2 * len(ACTION_ROLES) * len(PREDICTORS) * 3 == 240
    actual = method._paired_targets(target, score)
    with localcontext() as context:
        context.prec = 50
        expected = tuple((Decimal(1) + max(row.normalized_error for row in score.cells
            if row.view == view and row.predictor == predictor and row.horizon_tick <= horizon)).ln()
            for view, predictor, horizon in product(method.VIEWS, PREDICTORS, protocol.horizon_steps))
    assert actual == expected and actual[:15] == score.cumulative_log_errors
    assert all(fine > primary for primary, fine in zip(actual[:15], actual[15:], strict=True))
    assert score.canonical_bytes() == before
    assert decode_canonical_bytes(before, ScheduledResponseScore, maximum_bytes=len(before)) == score


@pytest.mark.parametrize("damage", ("missing-action", "extra-action", "missing-cell", "extra-panel"))
def test_missing_or_extra_actual_assay_cells_remain_wholly_unevaluable(damage):
    protocol, target, score = _protocol_score()
    if damage == "missing-action":
        removed = protocol.actions[-1].action_id
        cells = tuple(row for row in score.cells if row.action_id != removed)
        assert len({row.action_id for row in cells}) == 3
    elif damage == "extra-action":
        cells = (*score.cells, *(replace(row, action_id="action.literal.extra") for row in score.cells
            if row.action_id == protocol.actions[-1].action_id))
    elif damage == "missing-cell":
        cells = score.cells[:-1]
    else:
        cells = (*score.cells, *(replace(row, panel_id="panel.literal.extra") for row in score.cells
            if row.panel_id == "panel.literal.common"))
    changed = replace(score, cells=tuple(sorted(cells, key=lambda row: row.key)))
    before = changed.canonical_bytes()
    assert method._paired_targets(target, changed) == (None,) * 30
    assert changed.canonical_bytes() == before
