# SPDX-License-Identifier: MPL-2.0
"""Exposed causal arithmetic; supplied curves and prefixes confer no custody."""
from decimal import Decimal as D, localcontext
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import matched_causal_feature_values, MATCHED_FEATURES
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel, MatrixIO48Construction
from empirical_lawhood.adapters.methods.matrix_factor_response.records import MatrixFactorAction, ACTION_ROLES
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import physical_forecast_implementation
from tests.test_matrix_e3_protected_feature import finite_case
from tests.test_matrix_e3_protected_prefix_science import case as prefix_case, forbid_native as forbid_native  # noqa: F401


@pytest.fixture(scope='module')
def operands(prefix_case):  # noqa: F811
    case = finite_case(prefix_case)
    protocol = SimpleNamespace(public_source=ScheduledPublicSource.from_source(case.source),
        mechanical_model=MatrixOriginResponseModel('test.matched.feature-model', physical_forecast_implementation(),
            MatrixIO48Construction('test.matched.io48')),
        horizon_steps=DENSE_RESPONSE_HORIZONS,
        actions=tuple(MatrixFactorAction('test.matched.' + role.lower(), role, D('.01'), 16, D(1)) for role in ACTION_ROLES))
    arrays = {name: value.copy() for name, value in case.values.items()}
    for name, first in (('positions', (6, 4)), ('momenta', (0, 10))):
        arrays['primary_' + name][224] = 0
        arrays['primary_' + name][224, :, 0, 0, 0] = first
    frozen = {view + '_full_grid_' + method: np.zeros((4, 128, 48), dtype='<f8')
        for view in ('primary', 'fine') for method in ('full_coupled', 'factor')}
    frozen['primary_full_grid_full_coupled'][0, :, 24] = 1e-6
    frozen['fine_full_grid_full_coupled'][0, :, 24] = 2e-6
    return case, protocol, arrays, frozen


def evaluate(operands, *, arrays=None, frozen=None):
    case, protocol, causal, forecasts = operands
    return matched_causal_feature_values(protocol, prefix_disposition=case.causal.disposition,
        prefix_frame_sha256=case.causal.frame_sha256, traces=case.witness.traces,
        causal_arrays=causal if arrays is None else arrays, diagnostics=case.diagnostics,
        frozen_arrays=forecasts if frozen is None else frozen)


def test_primary_defect_and_signed_raw_norm_drifts_use_the_original_causal_window(operands):
    disposition, pairs, fine = evaluate(operands)
    assert disposition == 'AVAILABLE' and tuple(name for name, _ in pairs) == MATCHED_FEATURES
    values = dict(pairs)
    assert tuple(values[name] for name in ('position-x-drift', 'position-y-drift', 'momentum-x-drift', 'momentum-y-drift')) == (
        D('-93.75'), D(0), D(375), D('-156.25'))
    with localcontext() as context:
        context.prec = 60
        assert values['d_lin'] == D('1.00625').ln()
        assert fine == D('1.0125').ln()
    # Inter-check diagnostics and unknown future payloads are not features.
    frozen = {name: value.copy() for name, value in operands[3].items()}
    frozen['primary_full_grid_full_coupled'][0, 16, 24] = 100
    frozen['future_hold'] = object()
    assert evaluate(operands, frozen=frozen) == (disposition, pairs, fine)


def test_missing_primary_defect_refuses_both_feature_arms_and_fine_is_only_diagnostic(operands):
    frozen = {name: value.copy() for name, value in operands[3].items()}
    frozen['primary_full_grid_full_coupled'][:, 15] = np.nan
    disposition, values, fine = evaluate(operands, frozen=frozen)
    assert disposition == 'UNAVAILABLE' and not values and fine is not None
    frozen = {name: value.copy() for name, value in operands[3].items()}
    frozen['fine_full_grid_full_coupled'][:, 15] = np.nan
    disposition, values, fine = evaluate(operands, frozen=frozen)
    assert disposition == 'AVAILABLE' and values == evaluate(operands)[1] and fine is None
    arrays = dict(operands[2])
    arrays['primary_ticks'] = np.arange(258, dtype='<i8')
    assert evaluate(operands, arrays=arrays) == ('REFUSED', (), None)
