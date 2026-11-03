# SPDX-License-Identifier: MPL-2.0
"""E4 public-point parity against real typed cases; exposed software only.

No native worker, signer or scientific campaign runs. The component account is
an exact protected record, with a real compact CAL/CONF configuration. Original
fixture model/calibration metadata are software operands, never source authority.
"""
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import METHODS
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_science as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as programme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource, FAMILY_MAP
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_selected_e4_methods import (
    selected_revision, selected_calibrated, selected_e4_populations, selected_bridge, transfer,  # noqa: F401
)


def _models(fixture):
    return programme.SelectedE4PublicModels.from_products(fixture.programme, fixture.nomination,
        fixture.frozen, record_id='models.public-source-parity')


def _case_menu(fixture, phase):
    selected = getattr(fixture.populations, phase)
    bank = getattr(fixture.populations, phase + '_bank')
    menu = {}
    for case in selected.cases:
        menu.setdefault(case.coordinate, case)
    assert len(menu) == 36  # four families x eight corners plus center
    return selected, bank, tuple(menu.values())


@pytest.mark.parametrize('phase', ('calibration', 'confirmation'))
def test_closed_public_projection_matches_actual_typed_case_bytes_for_every_grid_coordinate(selected_revision, phase):  # noqa: F811
    models = _models(selected_revision)
    selected, bank, cases = _case_menu(selected_revision, phase)
    for case in cases:
        public = ScheduledPublicSource.from_source(bank.source(case.root_id,index=bank.source_index()))
        name = 'forecast.parity.' + phase + '.' + case.root_id
        original = models.forecast(selected, case, record_id=name)
        projected = science._forecast_public_source(models, selected.identity, public, record_id=name)
        assert type(projected) is programme.SelectedE4ForecastSeal
        assert projected.canonical_bytes() == original.canonical_bytes()
        assert projected.source == case.source and projected.cutoff == case.information_cutoff


@pytest.mark.parametrize('phase', ('calibration', 'confirmation'))
def test_actual_typed_account_revision_validator_rejects_changed_seal(selected_calibrated, phase):  # noqa: F811
    f = selected_calibrated.revision
    models = _models(f)
    selected, bank, cases = _case_menu(f, phase)
    case = cases[0]
    source = bank.source(case.root_id,index=bank.source_index())
    decision = programme.SelectedE4PublicRevisionDecision.from_products(f.programme, f.nomination,
        f.frozen, record_id='decision.public-source-parity')
    summary = programme.SelectedE4OriginalCalibrationSummary.from_package(
        f.populations.selected.package, record_id='summary.public-source-parity')
    calibration = None if phase == 'calibration' else programme.SelectedE4PublicCalibration.from_calibration(
        selected_calibrated.result, record_id='calibration.public-source-parity')
    local = native.SelectedE4ProtectedNativeSourceReference.from_bank(selected, bank,
        next(value for value in bank.sources if value.root_id == case.root_id),index=bank.source_index())
    protocol, panels = bank.response_selection.validate_source(source)
    config = owner.SelectedE4ProtectedCompactConfig('config.' + owner.local_node(case.root_id, 'continue'),
        selected.identity, local, protocol, panels, bank.response_selection.identity, 'continue',
        bank.phase, decision, models, calibration, summary)
    prefix = ObjectIdentity('causal.public-source-parity', native.SelectedE4ProtectedCausalPrefix.SCHEMA,
        native.SelectedE4ProtectedCausalPrefix.VERSION, 'a' * 64)
    feature = native.SelectedE4ProtectedFeature('feature.public-source-parity', case.source, prefix,
        case.root_id, case.independent_group_id, FAMILY_MAP[source.coordinate.family_id], source.coordinate.clock_id,
        source.coordinate.physical_time(source.policy.cutoff_tick), 'b' * 64, 'AVAILABLE',
        tuple((name, Decimal(1)) for name in FEATURES))
    reference = models.forecast(selected, case, record_id='revision.' + case.root_id)
    account = native.SelectedE4ProtectedAccountSeal('account.public-source-parity',
        selected.forecast_design, case.source, prefix, feature, summary.original_package, summary.calibration,
        summary, tuple((name, (Decimal(0),) * 15) for name in METHODS), reference, decision.identity,
        None if calibration is None else calibration.identity)
    assert science.validate_revision_account(config, account) == reference
    changed = replace(account, revision=replace(reference,
        revision_predictions=tuple(value + Decimal(1) for value in reference.revision_predictions)))
    with pytest.raises(ValueError, match='actual sealed revision'):
        science.validate_revision_account(config, changed)


@pytest.mark.parametrize('operand', ('models', 'public', 'programme'))
def test_closed_public_forecast_rejects_foreign_operands_without_duck_typing(selected_revision, operand):  # noqa: F811
    selected, bank, cases = _case_menu(selected_revision, 'calibration')
    values = {'models': _models(selected_revision), 'programme': selected.identity,
        'public': ScheduledPublicSource.from_source(bank.source(cases[0].root_id,index=bank.source_index()))}
    # A plausible foreign object still cannot satisfy an exact closed input.
    values[operand] = SimpleNamespace()
    with pytest.raises((TypeError, ValueError)):
        science._forecast_public_source(**values, record_id='forecast.foreign-operand')
