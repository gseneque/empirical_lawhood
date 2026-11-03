# SPDX-License-Identifier: MPL-2.0
"""Exposed relation arithmetic. No original acquisition or authority is asserted."""
from dataclasses import replace
from decimal import Decimal as D, localcontext
from itertools import product

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import e4_structural_prediction as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import MatchedTrainingRow
from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import MATCHED_FEATURES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


def pin(name):
    return ObjectIdentity('test.relation.' + name, 'empirical-lawhood/testing/disclosed-relation', '1.0.0', 'a' * 64)


def selection():
    return owner.E4MatchedRelationSelection('test.relation.selection', D(1), D('.5'), D('.25'))


def causal(factors, family):
    values = {name: D('.1') for name in MATCHED_FEATURES}
    values.update(zip(('bath-temperature', 'friction', 'cross-gamma'), factors, strict=True))
    values.update((name, D(family == identity)) for name, identity in owner.RELATION_FAMILY_CODING)
    return tuple(sorted(values.items()))


def training():
    rows, folds, originals = [], [], []
    for family_index, family in enumerate(owner.FOUR_FAMILY_PREPARATION_IDS):
        for ordinal in range(4):
            group = 'test.group.%d.%d' % (family_index, ordinal)
            folds.append((group, ordinal % 2))
            for index, ratios in enumerate((*product((D('.5'), D(2)), repeat=3), (D(1),) * 3)):
                factors = tuple(value * nominal for value, nominal in zip(ratios, (D(1), D('.5'), D('.25')), strict=True))
                root = group + '.case.' + str(index)
                values = owner.relation_feature_values(selection(), causal(factors, family), 'AVAILABLE',
                    factor_values=factors, family_id=family)
                rows.append(MatchedTrainingRow(root, group, family, values, (D('.02'),) * 58, ()))
                originals.append(pin(root))
    return tuple(rows), tuple(folds), tuple(originals)


def fit(rows, folds, originals):
    return owner.fit_relation_values(selection(), pin('development'), rows, originals,
        assigned_groups=tuple(group for group, _ in folds), folds=folds, record_id='test.relation.fit')


def test_single_case_log_ratios_keep_exact_grid_geometry_and_fixed_off_grid_curvature():
    selected = selection()
    for ratios in product((D('.5'), D(2)), repeat=3):
        factors = tuple(value * nominal for value, nominal in zip(ratios, (D(1), D('.5'), D('.25')), strict=True))
        values = dict(owner.relation_physical_features(selected, factors, selected.reference_family))
        assert values['q-aggregate'] == 1
        assert abs(values['x-temperature']) == abs(values['x-friction']) == abs(values['x-coupling']) == 1
    values = dict(owner.relation_physical_features(selected, (D(1), D('.5'), D('.25')), selected.reference_family))
    assert all(value == 0 for value in values.values())
    with localcontext() as context:
        context.prec = 60
        x = D('1.125').ln() / D(2).ln()
        off_grid = dict(owner.relation_physical_features(selected, (D('1.125'), D('.5'), D('.25')),
            owner.FOUR_FAMILY_PREPARATION_IDS[1]))
        assert off_grid['x-temperature'] == x and off_grid['q-aggregate'] == x*x/3
        assert off_grid['family-de-anneal'] == 1
    masks = dict(owner.RELATION_METHOD_FEATURES)
    assert len(masks['SR']) == len(masks['BR']) == 26 and len(masks['RELATION_BASE']) == 22
    assert len(masks['PHYSICAL']) == 10 and 'd_lin' in set(masks['SR']) & set(masks['BR'])
    assert not set(owner._REPLACED_CONTEXT[:3]).intersection(masks['SR'])


def test_fits_keep16_independent_groups144_nested_rows_equal_weights_and_no_extra_search():
    rows, folds, originals = training()
    fitted = fit(rows, folds, originals)
    for model in fitted.models:
        assert len(model.training_unit_ids) == len(model.complete_group_ids) == 16
        if model.method_key == 'RAW_DEV_MEDIAN':
            assert not model.fit_attempts
            continue
        assert len(model.fit_attempts) == 5 and model.parameters.diagnostics.penalty == 1
        assert len(model.parameters.diagnostics.row_groups) == 144
        assert {count for _, _, count in model.parameters.diagnostics.row_groups} == {9}
        assert all(denominator == 522 for fold in model.cross_validation for _, _, denominator in fold.group_losses)
    assert decode_canonical_bytes(fitted.canonical_bytes(), type(fitted), maximum_bytes=None) == fitted


def test_common_complete_group_threshold_and_family_fold_support_are_distinct():
    rows, folds, originals = training()
    # Lose one entire group in each family: folds retain 8 and4, both eligible.
    missing = {group for group, _ in folds if group.endswith('.3')}
    reduced = tuple(replace(row, reasons=('UNKNOWN_CONTACT',)) if row.group_id in missing else row for row in rows)
    fitted = fit(reduced, folds, originals)
    assert all(len(model.complete_group_ids) == 12 and not model.prerequisite_reasons for model in fitted.models)
    missing = {group for group, _ in folds if group.startswith('test.group.0.') and group.endswith(('.0', '.2'))}
    failed = fit(tuple(replace(row, reasons=('UNKNOWN_CONTACT',)) if row.group_id in missing else row for row in rows), folds, originals)
    assert all(len(model.complete_group_ids) == 14 and 'INSUFFICIENT_FAMILY_SUPPORT_FOLD_0' in model.prerequisite_reasons
        and model.parameters is None for model in failed.models)


def scoring(group_count):
    with localcontext() as context:
        context.prec = 60
        failure = D('1.02').ln()
    points = tuple((method, ((D(0),) * 28 + (failure,)) * 2 if method == 'BR' else (D(0),) * 58)
        for method in owner.RELATION_METHODS)
    groups = tuple('test.scoring.%02d' % index for index in range(group_count))
    return groups, tuple(owner.E4RelationScoringCase(group + '.case.' + str(index), group,
        pin(group + '.forecast.' + str(index)), pin(group + '.outcome.' + str(index)), points, (D(0),) * 58, ())
        for group in groups for index in range(9))


def test_cal20_uses_whole_group_max522_and_one_unknown_coordinate_makes_bound_vacuous():
    groups, cases = scoring(20)
    result = owner.calibrate_relation_values(cases, assigned_groups=groups)
    assert all(row.rank == 20 and row.radius == 0 for row in result)
    unknown = replace(cases[0], original_outcome=None, errors=(None,) * 58, reasons=('UNKNOWN_CONTACT',))
    result = owner.calibrate_relation_values((unknown, *cases[1:]), assigned_groups=groups)
    assert all(row.rank == 20 and row.radius is None and len(row.scores) == 20 for row in result)
    with pytest.raises(ValueError, match='nine coordinates'):
        owner.calibrate_relation_values(cases[1:], assigned_groups=groups)


def test_conf32_counts_one_nested_group_per_win_and_retains_unknowns():
    groups, cases = scoring(32)
    cases = tuple(replace(row, original_outcome=None, errors=(None,) * 58, reasons=('UNKNOWN_CONTACT',))
        if row.group_id in groups[24:] else row for row in cases)
    decisions = owner.relation_group_decisions(cases, assigned_groups=groups)
    assert sum(row.success for row in decisions) == 24
    assert all(dict(row.duration_error_counts)['BR'] == 18 for row in decisions[:24])
    inference = owner.relation_primary_inference(decisions)
    assert inference.critical_successes == 24 and inference.events == (True,) * 24 + (None,) * 8
    assert inference.tail_numerator * 160 <= inference.tail_denominator


def test_prospective_curve_claim_can_win_without_a_K_win_and_preserves_all_nine_coordinates():
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_prediction import MatchedCurveDecision
    groups, cases = scoring(32)
    with localcontext() as context:
        context.prec = 60
        error = D('.2') * D('1.01').ln()
    points = tuple((method, (error if method == 'BR' else D(0),) * 58) for method in owner.RELATION_METHODS)
    cases = tuple(replace(row, log_points=points, original_outcome=None, errors=(None,) * 58, reasons=('UNKNOWN_CONTACT',))
        if row.group_id in groups[24:] else replace(row, log_points=points) for row in cases)
    decisions = owner.relation_group_decisions(cases, assigned_groups=groups, curve_primary=True)
    assert all(type(row) is MatchedCurveDecision and len(row.root_ids) == 9 for row in decisions)
    assert sum(row.success for row in decisions) == 24
    assert all(row.duration_success is False for row in decisions[:24])
    assert owner.relation_primary_inference(decisions).events == (True,) * 24 + (None,) * 8
    read = owner.relation_loss_readout(cases, decisions)
    assert read['curve_primary']['secondary_one_check_wins'] == 0
    assert decode_canonical_bytes(decisions[0].canonical_bytes(), MatchedCurveDecision, maximum_bytes=None) == decisions[0]


def test_curve_relation_keeps_equal_group_weights_and_two_shared_mechanism_inputs():
    from empirical_lawhood.adapters.methods.matrix_factor_response.curve_contract import MECHANISM_FEATURES, CURVE_RELATION_LOSS_RULE
    from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_fitting import MatchedCurveEstimatorModel
    selected = replace(selection(), loss=CURVE_RELATION_LOSS_RULE)
    rows, folds, originals = training()
    rows = tuple(replace(row, features=tuple(sorted((*row.features, *((name, D('.1')) for name in MECHANISM_FEATURES))))) for row in rows)
    fitted = owner.fit_relation_values(selected, pin('development'), rows, originals,
        assigned_groups=tuple(group for group, _ in folds), folds=folds, record_id='test.curve.relation.fit')
    for model in fitted.models:
        assert type(model) is MatchedCurveEstimatorModel and len(model.complete_group_ids) == 16
        if model.method_key == 'RAW_DEV_MEDIAN':
            continue
        assert len(model.fit_attempts) == 5
        assert {count for _, _, count in model.parameters.diagnostics.row_groups} == {9}
        assert all(len(losses) == 9 for fold in model.cross_validation for _, losses in fold.coordinate_losses)
        if model.method_key in ('SR', 'BR'):
            assert len(model.feature_names) == 28 and set(MECHANISM_FEATURES) <= set(model.feature_names)
    assert decode_canonical_bytes(fitted.canonical_bytes(), type(fitted), maximum_bytes=None) == fitted


def test_paired_target_discrepancy_is_nonuse_for_fit_calibration_and_confirmation():
    rows, folds, originals = training()
    broken = replace(rows[0], errors=(D('.02'),) * 29 + (D('.020100000000000000000000000000001'),) * 29)
    fitted = fit((broken, *rows[1:]), folds, originals)
    assert all(len(model.complete_group_ids) == 15 for model in fitted.models)
    assert all('PAIRED_TARGET_DISCREPANCY' in dict(model.exclusions)[broken.group_id] for model in fitted.models)
    groups, cases = scoring(20)
    broken = replace(cases[0], errors=(D(0),) * 29 + (D('.001'),) * 29)
    calibrations = owner.calibrate_relation_values((broken, *cases[1:]), assigned_groups=groups)
    assert all(row.radius is None and 'PAIRED_TARGET_DISCREPANCY' in row.scores[0][2] for row in calibrations)
    decisions = owner.relation_group_decisions((broken, *cases[1:]), assigned_groups=groups)
    assert not decisions[0].usable and not decisions[0].success
    assert owner.relation_primary_inference(decisions).events[0] is None
    with pytest.raises(ValueError, match='cumulative target'):
        replace(cases[0], errors=(D('.1'), D(0), *((D(0),) * 56)))


def test_both_e4_graphs_require_original_mechanics_before_statistical_accounts():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings, selected_e4_native_bindings
    for graph in (selected_e3_e4_bindings, selected_e4_native_bindings):
        assert graph.PHASES.index('mechanical') < graph.PHASES.index('account')
        assert {'mechanical', 'mechanical-arrays'} <= set(graph.INPUTS['account'])
        assert 'account' not in graph.INPUTS['mechanical']
        for phase in ('continue', 'responses'):
            assert {'mechanical', 'account'} <= set(graph.INPUTS[phase])
        manifests = tuple(row for row in graph.operation_declarations() if row.capability_key.endswith('.account'))
        assert manifests and all(row.capability_version == '3.0.0' for row in manifests)
        assert all({'mechanical', 'mechanical-arrays'} <= {port.port_id for port in row.input_ports} for row in manifests)


def test_uniform_family_draw_keeps_zero_counts_without_balancing_or_reusing_native_material():
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Design
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeFactor
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_population import selected_e4_population_groups
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe, STREAM_RULE
    factors = tuple(ScheduledProgrammeFactor(name, 'LOG', D(1), D(2), D(4)) for name in ('temperature', 'friction', 'coupling'))
    designs = tuple((phase, SelectedE3E4Design('test.design.' + phase.lower(), count, D('.95'), factors, 4,
        'BALANCED_FIXED_FOUR_FAMILY_GROUPS' if phase == 'DEVELOPMENT' else 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW'))
        for phase, count in (('CALIBRATION', 1), ('CONFIRMATION', 3), ('DEVELOPMENT', 16)))
    preparations = tuple(SimpleNamespace(family_id=family) for family in owner.FOUR_FAMILY_PREPARATION_IDS)
    streams = SelectedE4StreamRecipe('test.e4.streams', 'a' * 64, 'b' * 64, STREAM_RULE, 'c' * 64)
    groups = selected_e4_population_groups(namespace='test.e4.iid', population_designs=designs,
        preparations=preparations, streams=streams)
    assert sum(len(assigned) for phase, _, assigned in groups if phase == 'CALIBRATION') == 1
    assert sum(not assigned for phase, _, assigned in groups if phase == 'CALIBRATION') == 3
    assert sum(len(assigned) for phase, _, assigned in groups if phase == 'CONFIRMATION') == 3
    assert all(len(assigned) == 4 for phase, _, assigned in groups if phase == 'DEVELOPMENT')
    assert all(streams.family(group) == family for phase, family, assigned in groups if phase != 'DEVELOPMENT' for group in assigned)
    assert len({group for _, _, assigned in groups for group in assigned}) == 20
    assert groups == selected_e4_population_groups(namespace='test.e4.iid', population_designs=designs,
        preparations=preparations, streams=replace(streams, prefix_seed_material_sha256='d' * 64))
    with pytest.raises(ValueError, match='draw material'):
        selected_e4_population_groups(namespace='test.e4.iid', population_designs=designs,
            preparations=preparations, streams=replace(streams, family_seed_material_sha256=None))
    with pytest.raises(ValueError, match='separate declared random'):
        replace(streams, family_seed_material_sha256=streams.prefix_seed_material_sha256)
