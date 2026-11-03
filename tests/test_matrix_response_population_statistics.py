# SPDX-License-Identifier: MPL-2.0
"""Exposed metadata-only denominator controls, no native science or warrant."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.records import ACTION_ROLES, PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_contracts import (
    MatrixResponseOriginSelection, MatrixResponsePopulationPolicy,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import (
    MatrixResponseActionScale, MatrixResponseFrontierCell, MatrixResponseFrontierProtocol,
    MatrixResponseHorizonLoss, MatrixResponseRootFrontier,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import (
    HORIZONS, ROOT_IDS, STRATA, WARRANT, MatrixResponsePopulationStatistics,
    MatrixResponsePopulationStatisticsSpec, population_statistics, query_statistics,
    root_loss_bounds,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity


def obj(name):
    return ObjectIdentity('software.statistics.' + name, 'empirical-lawhood/tests/' + name, '1.0.0', 'a' * 64)


def artifact(name):
    return ArtifactIdentity('software.statistics.' + name, 'exposed-software-only',
        'empirical-lawhood/tests/uninterpreted', 'b' * 64, 'application/json', 1)


@pytest.fixture(scope='module')
def spec():
    protocol = MatrixResponseFrontierProtocol('software.statistics.protocol', obj('factor-rule'), D('.001'),
        HORIZONS, tuple(MatrixResponseActionScale(role, D('.01'), D(1), 16) for role in ACTION_ROLES), D('1e-12'))
    policy = MatrixResponsePopulationPolicy('software.statistics.policy', obj('population'), obj('supplier'),
        artifact('case'), protocol, ROOT_IDS)
    selections = []
    for i, root in enumerate(ROOT_IDS):
        selected = i % 64 < (40, 64, 37, 45)[i // 64]
        selections.append(MatrixResponseOriginSelection('selection.' + root, policy.identity, root,
            f'unit.cc1-grr-c2.h{i:03d}', STRATA[i // 64], artifact('trace.' + str(i)),
            artifact('diagnostics.' + str(i)) if selected else None,
            'SELECTED' if selected else 'NO_CAUSAL_ORIGIN', 16 if selected else None,
            D('.016') if selected else None, ('exposed-software-selection',)))
    return MatrixResponsePopulationStatisticsSpec('software.statistics.spec', policy, tuple(selections),
        artifact('selections'), artifact('allocation'))


def frontier(spec, *, native_pass=True, unresolved=False):
    selection = spec.selections[0]
    panels = (('software.common', 'COMMON_NOISE_PANEL'), ('software.independent', 'INDEPENDENT_FUTURE'))
    actions = tuple(('software.' + role.lower(), role) for role in ACTION_ROLES)
    scales = {a.role: a for a in spec.policy.protocol.action_scales}
    cells = []
    for panel, role in panels:
        for action, action_role in actions:
            for j, horizon in enumerate(HORIZONS, start=1):
                qscale, _ = scales[action_role].scales(D('.001'), horizon)
                for predictor in PREDICTORS:
                    missing = unresolved and predictor == 'SPECTRA' and horizon >= 64
                    cells.append(MatrixResponseFrontierCell(panel, role, action, action_role, horizon,
                        predictor, None if missing else qscale * j, None if missing else D(0),
                        None if missing else D(j), 0, 0))
    losses = tuple(MatrixResponseHorizonLoss(predictor, horizon,
        None if unresolved and predictor == 'SPECTRA' and horizon >= 64 else D(j))
        for predictor in PREDICTORS for j, horizon in enumerate(HORIZONS, start=1))
    return MatrixResponseRootFrontier('software.statistics.frontier', spec.policy.protocol.identity,
        selection.root_id, selection.independent_group_id, selection.family_id, obj('source'),
        'MEASURED_DEVELOPMENT', obj('origin'), obj('assessment'), obj('metric'), None,
        panels, actions, HORIZONS, tuple(sorted(cells, key=lambda c: c.key)), losses, native_pass)


def report(spec, *, measured=None, refusal=False):
    batches = []
    for selection in spec.selections:
        if measured is not None and selection.root_id == measured.root_id:
            batches.append(root_loss_bounds(spec, selection, measured))
        elif refusal and selection.disposition == 'SELECTED':
            batches.append(root_loss_bounds(spec, selection, disposition='REFUSED', evidence=(obj('refusal'),)))
        else:
            batches.append(root_loss_bounds(spec, selection))
    return population_statistics(spec, batches, report_id='software.statistics.report')


def test_missing_roots_keep_all_256_denominator_and_partial_envelopes(spec):
    result = report(spec)
    assert len(result.bounds) == 256 * 15 and len(result.stratum_cdfs) == 60
    query = query_statistics(result, D('1e100'))
    assert all(r['requested_roots'] == 256 and r['empirical_lower_count'] == 0
        and r['empirical_upper_count'] == 186 for r in query['finite_roster_mixture'])
    assert all(r['requested_roots'] == 64 for r in query['strata'])
    assert {r['empirical_upper_count'] for r in query['strata']} == {40, 64, 37, 45}
    assert result.sampling_warrant == WARRANT and result.qualification == 'NOT_ESTABLISHED'
    assert not result.conditional_radii


def test_all_refusal_is_zero_supplied_use_without_infinite_decimal_or_fake_success(spec):
    result = report(spec, refusal=True)
    assert all(b.lower_loss is None and b.upper_loss is None for b in result.bounds)
    query = query_statistics(result, D('1e100'))
    assert all(r['empirical_lower_count'] == r['empirical_upper_count'] == 0 for r in query['strata'])
    assert len(query['factor_comparator_cdf_differences']) == 60
    assert all(r['empirical_difference_lower_count'] == r['empirical_difference_upper_count'] == 0
        and r['sampling_warrant'] == WARRANT for r in query['factor_comparator_cdf_differences'])
    assert result.admission == 'UNASSESSED'
    with pytest.raises(ValueError, match='nonentry|evidence'):
        root_loss_bounds(spec, spec.selections[0], disposition='REFUSED')


def test_single_complete_measured_root_does_not_become_100_percent_coverage(spec):
    result = report(spec, measured=frontier(spec))
    at_one = query_statistics(result, D(1))['finite_roster_mixture']
    assert next(r for r in at_one if (r['predictor'], r['horizon_step']) == ('FACTOR', 16))['empirical_lower_count'] == 1
    assert next(r for r in at_one if (r['predictor'], r['horizon_step']) == ('FACTOR', 64))['empirical_lower_count'] == 0
    high = query_statistics(result, D(3))['finite_roster_mixture']
    assert all(r['empirical_lower_count'] == 1 and r['empirical_upper_count'] == 186
        and r['requested_roots'] == 256 for r in high)


def test_unresolved_comparator_preserves_known_prior_lower_bound_without_lifetime_imputation(spec):
    bounds = root_loss_bounds(spec, spec.selections[0], frontier(spec, unresolved=True))
    spectral = tuple(b for b in bounds if b.predictor == 'SPECTRA')
    assert spectral[0].bound_kind == 'FINITE_POINT'
    assert tuple((b.lower_loss, b.upper_loss) for b in spectral) == ((D(1), D(1)), (D(1), None), (D(1), None))
    assert spectral[1].disposition == spectral[2].disposition == 'MEASUREMENT_UNRESOLVED'


def test_native_crosscheck_failure_is_nonuse_not_measured_model_error(spec):
    retained = frontier(spec, native_pass=False)
    bounds = root_loss_bounds(spec, spec.selections[0], retained)
    assert not retained.native_reference_pass and all(b.disposition == 'NATIVE_CROSSCHECK_FAILED' for b in bounds)
    assert all(b.bound_kind == 'KNOWN_NONUSE_INFINITY' for b in bounds)
    assert retained.horizon_losses[0].cumulative_loss == D(1)


@pytest.mark.parametrize('defect', ('root', 'stratum', 'group', 'counts', 'warrant', 'qualification'))
def test_complete_report_refuses_denominator_lineage_or_warrant_substitution(spec, defect):
    result = report(spec)
    with pytest.raises(ValueError):
        if defect == 'root':
            replace(result, bounds=result.bounds[:-15])
        elif defect == 'stratum':
            replace(result, bounds=(replace(result.bounds[0], stratum_id=STRATA[1]), *result.bounds[1:]))
        elif defect == 'group':
            replace(result, bounds=(replace(result.bounds[0], independent_group_id='software.other'), *result.bounds[1:]))
        elif defect == 'counts':
            replace(result, stratum_cdfs=result.stratum_cdfs[:-1])
        elif defect == 'warrant':
            replace(result, sampling_warrant='SATISFIED')
        else:
            replace(result, qualification='SATISFIED')


def test_thinned_panels_and_changed_metric_cannot_create_finite_coverage(spec):
    retained = frontier(spec)
    # Retain a self-consistent thinned menu that the old record can express;
    # the protocol's complete panel-role census must still refuse it.
    with pytest.raises(ValueError):
        root_loss_bounds(spec, spec.selections[0], replace(retained, panel_census=retained.panel_census[:1],
            cells=tuple(c for c in retained.cells if c.panel_id == retained.panel_census[0][0])))
    changed = replace(retained, cells=tuple(replace(c, position_error=c.position_error / 2) for c in retained.cells))
    with pytest.raises(ValueError, match='metric loss'):
        root_loss_bounds(spec, spec.selections[0], changed)


def test_explicit_unknown_or_nonentry_requires_evidence_missing_result_is_unavailable(spec):
    selection = spec.selections[0]
    assert {b.disposition for b in root_loss_bounds(spec, selection)} == {'UNAVAILABLE'}
    for disposition in ('UNKNOWN_CONTACT', 'NOT_ENTERED'):
        with pytest.raises(ValueError, match='evidence'):
            root_loss_bounds(spec, selection, disposition=disposition)
        rows = root_loss_bounds(spec, selection, disposition=disposition, evidence=(obj('contact-census'),))
        assert all(b.lower_loss == 0 and b.upper_loss is None and b.disposition == disposition for b in rows)


def test_conditional_formula_cannot_promote_assumptions_and_alpha_is_not_error_tolerance(spec):
    narrow = report(replace(spec, alpha=D('.05')))
    wider = report(replace(spec, alpha=D('.01')))
    assert wider.conditional_radii[0][1] > narrow.conditional_radii[0][1]
    assert all(r.sampling_warrant == WARRANT and r.admission == 'UNASSESSED' for r in (narrow, wider))
    assert query_statistics(narrow, D('.01'))['tolerance'] == D('.01')
    assert query_statistics(narrow, D('.05'))['tolerance'] == D('.05')
    query = query_statistics(narrow, D('.05'))
    assert all(r['conditional_formula_band'] is not None and r['sampling_warrant'] == WARRANT
        for r in query['finite_roster_mixture'])
    assert all(r['conditional_formula_difference_band'][0] <= 0 <= r['conditional_formula_difference_band'][1]
        for r in query['factor_comparator_cdf_differences'])
    with pytest.raises(ValueError, match='warrant'):
        replace(spec, sampling_warrant='FIXED_MAP_IID_SATISFIED')


def test_canonical_complete_report_roundtrip_preserves_decimal_spelling_and_all_outcomes(spec):
    result = report(spec, measured=frontier(spec))
    assert decode_canonical_bytes(result.canonical_bytes(), MatrixResponsePopulationStatistics, maximum_bytes=None) == result
    row = result.bounds[0]
    with pytest.raises(ValueError):
        replace(row, lower_loss=D('Infinity'), upper_loss=D('Infinity'))
    with pytest.raises(ValueError):
        replace(spec, selections=spec.selections[:-1])


def test_partial_bounds_cannot_drop_prior_measured_failure_or_become_infinite_finite_values(spec):
    result = report(spec, measured=frontier(spec, unresolved=True))
    rows = list(result.bounds)
    index = next(i for i, b in enumerate(rows) if b.root_id == ROOT_IDS[0]
        and b.predictor == 'SPECTRA' and b.horizon_step == 64)
    rows[index] = replace(rows[index], lower_loss=D(0))
    with pytest.raises(ValueError):
        population_statistics(spec, (tuple(rows),), report_id='software.statistics.bad-lower')


def test_conditional_formula_remains_unassessed_on_all_refusal_not_qualification(spec):
    result = report(replace(spec, alpha=D('.05')), refusal=True)
    query = query_statistics(result, D('1e100'))
    assert all(r['empirical_lower_count'] == r['empirical_upper_count'] == 0
        and r['conditional_formula_band'][0] == 0 for r in query['strata'])
    assert result.qualification == 'NOT_ESTABLISHED' and result.sampling_warrant == WARRANT


def test_wrong_original_roster_or_source_policy_refuses(spec):
    with pytest.raises(ValueError, match='original|roster'):
        replace(spec, selections=(replace(spec.selections[0], independent_group_id=spec.selections[1].independent_group_id),
            *spec.selections[1:]))
    with pytest.raises(ValueError, match='original'):
        replace(spec, selections=(replace(spec.selections[0], policy=replace(spec.policy, policy_id='software.other').identity),
            *spec.selections[1:]))


