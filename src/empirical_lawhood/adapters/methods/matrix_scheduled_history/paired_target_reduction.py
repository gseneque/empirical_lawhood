# SPDX-License-Identifier: MPL-2.0
"""One exact nested target reduction for both selected E4 acquisition routes."""
from decimal import Decimal, localcontext
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS, ACTION_ROLES


def target_contract(protocol):
    from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel
    return 'MATCHED_FACTOR58' if type(protocol.mechanical_model) is MatrixOriginResponseModel else 'PAIRED15'


def paired_factor_errors(score, protocol, panels):
    """Original-unit targets from every original dense score cell, not log inversion."""
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import paired_response_view_values
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import matched_e3_measurement
    if target_contract(protocol) != 'MATCHED_FACTOR58':
        raise ValueError('paired FACTOR errors require the original matched mechanical target')
    views, _ = paired_response_view_values(SimpleNamespace(measurement=matched_e3_measurement()),
        SimpleNamespace(root_id=protocol.public_source.root.root_id), protocol, panels, score)
    by_view = {view.view_id: view.errors for view in views}
    return tuple(value for view in ('primary', 'fine') for value in by_view[view])


def paired_targets(score, protocol, panels):
    """Exact original paired target, retaining complete action/panel cells."""
    if target_contract(protocol) == 'MATCHED_FACTOR58':
        with localcontext() as context:
            context.prec = 60
            values = tuple(None if value is None else (Decimal(1) + value).ln()
                for value in paired_factor_errors(score, protocol, panels))
        if values != score.cumulative_log_errors:
            raise ValueError('matched E4 targets differ from complete original paired FACTOR score cells')
        return values
    if (score.criterion != protocol.criterion or score.disposition not in ("FINITE", "PARTIAL") or not score.numerical_pass
            or len(protocol.actions) != len(ACTION_ROLES)):
        return (None,) * 30
    expected = {(view, panel.panel_id, action.action_id, predictor, horizon)
        for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions
        for predictor in PREDICTORS for horizon in protocol.horizon_steps}
    if {cell.key for cell in score.cells} != expected or len(score.cells) != len(expected):
        return (None,) * 30
    result = []
    with localcontext() as context:
        context.prec = 50
        for view in ("PRIMARY", "FINE"):
            for predictor in PREDICTORS:
                prior, missing = Decimal(0), False
                for horizon in protocol.horizon_steps:
                    cells = tuple(cell for cell in score.cells if (cell.view, cell.predictor, cell.horizon_tick) == (view, predictor, horizon))
                    values = tuple(cell.normalized_error for cell in cells)
                    missing = missing or any(value is None for value in values)
                    if missing:
                        result.append(None)
                    else:
                        prior = max(prior, (Decimal(1) + max(values)).ln())
                        result.append(prior)
    if tuple(result[:15]) != score.cumulative_log_errors:
        raise ValueError("selected E4 paired targets differ from original PRIMARY fifteen-target reduction")
    return tuple(result)

