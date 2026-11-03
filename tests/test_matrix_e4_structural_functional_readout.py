# SPDX-License-Identifier: MPL-2.0
"""Disclosed literal joins: no real native product, source or qualification claim."""
from dataclasses import replace
from decimal import Decimal as D, localcontext
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_secondary_readout as secondary
from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_science as full
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore,ScheduledResponseLossCell,branch_census
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledE4DenseResponseCell, ScheduledE4DenseResponseScore, ScheduledE4DenseMechanicalForecast,
)
from tests.test_matrix_e4_full_factor_public import selected_values, _real_plane
from tests.test_matrix_e4_full_factor_values import scopes,literal_recipe_source_inputs,_analytic_full  # noqa: F401


def pin(name,schema,version='1.0.0'):
    return ObjectIdentity(name,schema,version,'a'*64)


def _literal_norms(protocol,action,horizon,error):
    """Declared arithmetic operands, not measured/native response archives."""
    if error is None:
        return None,None
    with localcontext() as context:
        context.prec=60
        dt=protocol.public_source.coordinate.primary_view.timestep
        duration,pulse=dt*horizon,dt*min(action.pulse_steps,horizon)
        impulse=action.amplitude*action.force_norm*pulse
        return error*impulse*(duration-pulse/2),D(0)


def literal_dense_score(bank,case,score,target,selection,*,overrides=None):
    """Pure record/join controls with literal cells; no forecast or receipt claim."""
    overrides={} if overrides is None else overrides
    protocol=next(row for row in bank.response_selection.protocols if row.public_source.root.root_id==case.root_id)
    panels=dict(bank.response_selection.panels)[case.group_id]
    original_cells={cell.key:cell for cell in score.cells}
    cells=[]
    for view in secondary.VIEWS:
        for panel in panels:
            for action in protocol.actions:
                for predictor in secondary.PREDICTORS:
                    for horizon in target.observation_horizons:
                        if horizon in secondary.HORIZONS:
                            error=original_cells[view,panel.panel_id,action.action_id,predictor,horizon].normalized_error
                        else:
                            error=overrides.get(horizon,D('.005') if horizon<64 else D('.02'))
                        qnorm,pnorm=_literal_norms(protocol,action,horizon,error)
                        cells.append(ScheduledE4DenseResponseCell(view,panel.panel_id,action.action_id,predictor,horizon,
                            qnorm,pnorm,error))
    def archive(name):
        return ArtifactIdentity(name,'disclosed-software-archive',MATRIX_ARRAY_SCHEMA,'a'*64,'application/x-npz',1)
    dense=ScheduledE4DenseResponseScore('dense-score.disclosed.e4.secondary',ObjectIdentity.from_record(score.score_id,score),
        ObjectIdentity('dense-forecast.disclosed',ScheduledE4DenseMechanicalForecast.SCHEMA,ScheduledE4DenseMechanicalForecast.VERSION,'a'*64),
        archive('forecast-archive.disclosed'),score.responses,archive('response-archive.disclosed'),target.identity,selection.identity,
        score.source,score.causal_prefix,ObjectIdentity.from_record(protocol.protocol_id,protocol),protocol.public_source.policy.cutoff_tick,
        score.root_id,score.independent_group_id,score.role,score.numerical_pass,score.disposition,score.reason_codes,
        tuple(sorted(cells,key=lambda row:row.key)))
    dense.validate_original(protocol,panels,target,selection,score)
    return dense


def literal_response(bank,case,values=(D('.005'),D('.02'),D('.03'))):
    protocol=next(row for row in bank.response_selection.protocols if row.public_source.root.root_id==case.root_id)
    panels=dict(bank.response_selection.panels)[case.group_id]
    forecast=pin('forecast.disclosed.e4.secondary',original.SelectedE3E4AccountSeal.SCHEMA,original.SelectedE3E4AccountSeal.VERSION)
    cells=[]
    for view in secondary.VIEWS:
        for panel in panels:
            for action in protocol.actions:
                for predictor in secondary.PREDICTORS:
                    for horizon,error in zip(secondary.HORIZONS,values,strict=True):
                        qnorm,_=_literal_norms(protocol,action,horizon,error)
                        signed=(qnorm,*(D(0),)*47)
                        cells.append(ScheduledResponseLossCell(view,panel.panel_id,action.action_id,predictor,horizon,
                            (D(0),)*48,signed,signed,(None,)*48,error))
    cells=tuple(sorted(cells,key=lambda row:row.key))
    controls=tuple(ScheduledResponseTransitionControl('control.scheduled.'+case.root_id+'.'+branch,
        'SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS',D(0),protocol.native_reference_tolerance,'SATISFIED',
        128 if view=='PRIMARY' else 256,192,(D(0),)*(128 if view=='PRIMARY' else 256),()) for branch,view,*_ in branch_census(protocol,panels))
    with localcontext() as context:
        context.prec=50
        logs=tuple((D(1)+value).ln() for value in values)*5
        points=tuple((method,tuple((D(1)+D('.004' if index==0 else '.04')).ln() for _ in range(15))) for index,method in enumerate(original.METHODS))
    score=ScheduledResponseScore('score.disclosed.e4.secondary',case.source,pin('causal.disclosed',original.SelectedE3E4CausalPrefix.SCHEMA),forecast,
        pin('physical.disclosed','empirical-lawhood/tests/physical'),pin('responses.disclosed','empirical-lawhood/tests/responses'),
        case.root_id,case.group_id,'DEVELOPMENT',protocol.criterion,controls,True,'FINITE',cells,logs,('disclosed-control',))
    case=replace(case,forecast=forecast,score=ObjectIdentity.from_record(score.score_id,score),original_log_points=points,
        paired_log_targets=logs*2,score_disposition='FINITE')
    return case,score


@pytest.fixture(scope='module')
def joined(scopes,literal_recipe_source_inputs,tmp_path_factory):  # noqa: F811
    plane=_real_plane(tmp_path_factory.mktemp('e4-literal-dense-join')/'plane')
    selected=selected_values(scopes,literal_recipe_source_inputs,plane=plane)
    scope=selected.scope
    case,score=literal_response(selected.bank,scope.original_cases[0])
    source,raw=_analytic_full(scope.sources[0],True)
    source=replace(source,causal_disposition='AVAILABLE')
    score=replace(score,causal_prefix=source.causal_prefix)
    case=replace(case,score=ObjectIdentity.from_record(score.score_id,score))
    completed=replace(case.native[0],disposition='COMPLETED',definition=pin('definition.disclosed','empirical-lawhood/runtime/native-subwork-definition'),
        completion=pin('completion.disclosed','empirical-lawhood/runtime/native-subwork-completion'),receipt=pin('receipt.disclosed','empirical-lawhood/runtime/canonical-task-receipt'))
    case=replace(case,native=(completed,*case.native[1:]),full_assessment=source.full_numerical)
    source=replace(source,original_case=ObjectIdentity.from_record(case.root_id,case))
    scope=replace(scope,original_cases=(case,*scope.original_cases[1:]),sources=(source,*scope.sources[1:]))
    products=[];assessments=[];rows=[]
    dense=literal_dense_score(selected.bank,case,score,selected.secondary_target,selected.secondary_readout)
    for index,(source,case) in enumerate(zip(scope.sources,scope.original_cases,strict=True)):
        diagnostic,product=full.measure(source,raw if index==0 else None,artifact_id='diagnostic.disclosed.secondary.'+source.root_id)
        assessment=full.assess(source,product,raw if index==0 else None,diagnostic)
        products.append(product);assessments.append(assessment)
        rows.append(secondary.dense_e4_functional_rows(selected.bank,case,score if index==0 else None,
            dense_score=dense if index==0 else None,target=selected.secondary_target,secondary=selected.secondary_readout))
    return SimpleNamespace(scope=scope,products=tuple(products),assessments=tuple(assessments),rows=tuple(rows),
        score=score,dense=dense,bank=selected.bank,target=selected.secondary_target,selection=selected.secondary_readout)


def project(value,**changes):
    return secondary.structural_functional_projection(changes.get('scope',value.scope),changes.get('products',value.products),
        changes.get('assessments',value.assessments),changes.get('rows',value.rows),target=value.target,secondary=value.selection)


def test_exact_join_keeps_all_groups_and_unavailable_structural_functional_cases(joined):
    before=tuple(row.canonical_bytes() for row in (*joined.scope.original_cases,*joined.products,*joined.assessments))
    result=project(joined)
    n=len(joined.scope.sources)
    assert result['assigned_cases']==n and result['assigned_independent_groups']==len(joined.scope.programme.group_ids)
    assert len(result['adequacy'])==n*58 and len(result['structural_functional_horizons'])==n*12
    root=joined.scope.sources[0].root_id
    assert all(row['last_definite_pass']==60 and row['first_definite_failure']==64 for row in result['useful_lifetimes'] if row['root_id']==root)
    assert all(row['actual_error'] is None for row in result['adequacy'] if row['root_id']!=root)
    joined_rows=tuple(row for row in result['structural_functional_horizons'] if row['root_id']==root)
    assert all(row['observation'] is not None for row in joined_rows)
    assert all(row['structural_usable']==(joined.assessments[0].witness_pass and joined.assessments[0].history_numerical_pass is True) for row in joined_rows)
    assert {row['decision'] for row in result['failure_detection'] if row['root_id']==root}=={'CORRECT_PASS','FALSE_ALARM','MISSED_FAILURE','DETECTED_FAILURE'}
    assert result['structural_origin']=='ORIGINAL_FIRST_CAUSAL_ADMISSION_NOT_REANCHORED_TO_RESPONSE_CUTOFF'
    assert tuple(row.canonical_bytes() for row in (*joined.scope.original_cases,*joined.products,*joined.assessments))==before


@pytest.mark.parametrize('damage',('missing','duplicate','group','source','coordinate','clock','causal','assessment'))
def test_casewise_exact_join_refuses_substitution_without_erasing_denominators(joined,damage):
    rows=joined.rows;kwargs={}
    if damage=='missing':rows=rows[:-1]
    elif damage=='duplicate':rows=(rows[0],*rows[:-1])
    elif damage=='assessment':kwargs['assessments']=(joined.assessments[1],*joined.assessments[1:])
    else:
        row=rows[0]
        row=replace(row,**({'group_id':'group.foreign'} if damage=='group' else {'source':replace(row.source,object_fingerprint='f'*64)} if damage=='source'
            else {'coordinate':replace(row.coordinate,object_fingerprint='f'*64)} if damage=='coordinate' else {'causal_prefix':replace(row.causal_prefix,object_fingerprint='f'*64)} if damage=='causal' else {'origin_tick':row.origin_tick-4}))
        rows=(row,*rows[1:])
    with pytest.raises((ValueError,PermissionError)):
        project(joined,rows=rows,**kwargs)


@pytest.mark.parametrize('damage',('score','forecast','cell','receiver','control'))
def test_original_raw_score_and_complete_nested_cells_are_required(joined,damage):
    case=joined.scope.original_cases[0];score=joined.score
    with pytest.raises((ValueError,PermissionError)):
        if damage=='score':case=replace(case,score=replace(case.score,object_fingerprint='f'*64))
        elif damage=='forecast':score=replace(score,error_forecast=replace(score.error_forecast,object_fingerprint='f'*64))
        elif damage=='cell':score=replace(score,cells=score.cells[:-1])
        elif damage=='receiver':score=replace(score,cells=(replace(score.cells[0],actual_odd_responses=(D(0),)*47),*score.cells[1:]))
        else:score=replace(score,controls=score.controls[:-1])
        if damage not in ('score','forecast'):
            case=replace(case,score=ObjectIdentity.from_record(score.score_id,score))
        secondary.original_functional_rows(joined.bank,case,score)


def test_interval_failure_order_does_not_invent_a_common_origin_or_point_order():
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorLifetime
    functional={'last_definite_pass':16,'first_definite_failure':64}
    origin=128
    assert secondary._failure_order(FactorLifetime(32,'LEFT_PRESENT','EXIT_INTERVAL',80,96,()),functional,origin)=='STRUCTURAL_FAILURE_PRECEDES_FUNCTIONAL_INTERVAL'
    assert secondary._failure_order(FactorLifetime(32,'LEFT_PRESENT','EXIT_INTERVAL',200,208,()),functional,origin)=='FUNCTIONAL_FAILURE_PRECEDES_STRUCTURAL_INTERVAL'
    assert secondary._failure_order(FactorLifetime(32,'LEFT_PRESENT','EXIT_INTERVAL',160,176,()),functional,origin)=='OVERLAPPING_INTERVALS_ORDER_UNRESOLVED'
    assert secondary._failure_order(FactorLifetime(32,'LEFT_PRESENT','UNKNOWN',144,None,(160,)),functional,origin)=='CENSORED_NONUSE_OR_UNRESOLVED'


@pytest.mark.parametrize('error,first_failure,last_pass',((D('.01'),64,60),(D('.02'),20,16)))
def test_dense_cumulative_threshold_is_strict_and_later_recovery_does_not_erase_failure(joined,error,first_failure,last_pass):
    before=joined.score.canonical_bytes()
    case=joined.scope.original_cases[0]
    dense=literal_dense_score(joined.bank,case,joined.score,joined.target,joined.selection,
        overrides={20:error,24:D('.005')})
    row=secondary.dense_e4_functional_rows(joined.bank,case,joined.score,dense_score=dense,
        target=joined.target,secondary=joined.selection)
    result=project(joined,rows=(row,*joined.rows[1:]))
    selected=tuple(value for value in result['useful_lifetimes'] if value['root_id']==case.root_id)
    assert len(selected)==2
    assert all(value['first_definite_failure']==first_failure and value['last_definite_pass']==last_pass
        and value['tau_epsilon_grid']==first_failure for value in selected)
    assert joined.score.canonical_bytes()==before


def test_dense_missing_sample_retains_known_failure_without_inventing_exact_tau(joined):
    case=joined.scope.original_cases[0]
    dense=literal_dense_score(joined.bank,case,joined.score,joined.target,joined.selection,
        overrides={20:None,24:D('.02')})
    row=secondary.dense_e4_functional_rows(joined.bank,case,joined.score,dense_score=dense,
        target=joined.target,secondary=joined.selection)
    result=project(joined,rows=(row,*joined.rows[1:]))
    selected=tuple(value for value in result['useful_lifetimes'] if value['root_id']==case.root_id)
    assert all(value['first_possible_failure']==20 and value['first_definite_failure']==24
        and value['last_definite_pass']==16 and value['tau_epsilon_grid'] is None for value in selected)
    assert result['assigned_cases']==len(joined.scope.sources)


def test_dense_readout_keeps_unobserved_cases_and_refuses_present_score_without_dense_output(joined):
    case=joined.scope.original_cases[0]
    with pytest.raises(PermissionError,match='requires its actual supplemental score'):
        secondary.dense_e4_functional_rows(joined.bank,case,joined.score,dense_score=None,
            target=joined.target,secondary=joined.selection)
    for case,row in zip(joined.scope.original_cases[1:],joined.rows[1:],strict=True):
        assert row.original_case==ObjectIdentity.from_record(case.root_id,case)
        assert row.score is None and row.dense_score is None
        assert len(row.errors)==290 and all(value is None for value in row.errors)
        assert not any(row.cumulative_complete)


def test_dense_followup_censoring_is_sampled_and_first_failure_has_no_earlier_crossing():
    horizons=tuple(range(16,129,4))
    passing=tuple(secondary._dense_adequacy(horizon,D('.01'),True,D('.01'),'FINITE') for horizon in horizons)
    censored=secondary._grid_lifetime(passing)
    assert censored['tau_epsilon_grid'] is None and censored['right_censored_at_step']==128
    assert censored['right_censored_at_time']==D('.128')
    failed=secondary._grid_lifetime(tuple(secondary._dense_adequacy(horizon,D('.02'),True,D('.01'),'FINITE') for horizon in horizons))
    assert failed['tau_epsilon_grid']==16 and failed['last_passing_time'] is None
    assert failed['failure_observation']=='FAILED_BY_FIRST_CHECKED_HORIZON'
    assert failed['crossing_scope']=='SAMPLED_GRID_ONLY_UNOBSERVED_EXCURSIONS_NOT_EXCLUDED'


def test_dense_threshold_disagreement_reports_views_and_all_fixed_sensitivities(joined):
    case = joined.scope.original_cases[0]
    protocol = next(row for row in joined.bank.response_selection.protocols
        if row.public_source.root.root_id == case.root_id)
    actions = {action.action_id: action for action in protocol.actions}
    cells = []
    for cell in joined.dense.cells:
        if cell.view == 'FINE' and cell.horizon_tick == 20:
            qnorm, pnorm = _literal_norms(protocol, actions[cell.action_id], 20, D('.02'))
            cell = replace(cell, position_error_norm=qnorm, momentum_error_norm=pnorm, normalized_error=D('.02'))
        cells.append(cell)
    dense = replace(joined.dense, cells=tuple(cells))
    row = secondary.dense_e4_functional_rows(joined.bank, case, joined.score, dense_score=dense,
        target=joined.target, secondary=joined.selection)
    result = project(joined, rows=(row, *joined.rows[1:]))
    values = tuple(value for value in result['numerical_view_comparisons']
        if value['root_id'] == case.root_id and value['description'] == 'FACTOR')
    assert {D(value['normalized_tolerance']['decimal']) for value in values} == {D('.01'), D('.005'), D('.02'), D('.05')}
    headline = next(value for value in values if D(value['normalized_tolerance']['decimal']) == D('.01'))
    assert headline['threshold_disagreement_horizons'] == list(range(20, 64, 4))
    assert result['continuum_error_bound'] == 'NOT_ESTABLISHED_BY_PRIMARY_FINE_AGREEMENT'
    assert result['structural_observation_horizons'] == [16, 64, 128]


def test_dense_nonuse_and_numerical_failure_never_become_right_censoring():
    horizons = tuple(range(16, 129, 4))
    nonuse = tuple(secondary._dense_adequacy(horizon, None, False, D('.01'), 'NO_ORIGIN') for horizon in horizons)
    failed = tuple(secondary._dense_adequacy(horizon, D(0), True, D('.01'), 'NATIVE_CROSSCHECK_FAILED') for horizon in horizons)
    assert {cell.classification for cell in nonuse} == {'KNOWN_NONUSE'}
    for cells in (nonuse, failed):
        result = secondary._grid_lifetime(cells)
        assert result['tau_epsilon_grid'] is None
        assert result['right_censored_at_step'] is None and result['right_censored_at_time'] is None
