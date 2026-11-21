# SPDX-License-Identifier: MPL-2.0
"""Independent-root and missingness controls; no scientific qualification."""
from fractions import Fraction
import pytest

from empirical_lawhood.domains.matrix.classical_series.aggregate import aggregate_readouts, event_summary


def _row(seed, *, gain=False, harm=False, status="PAIRED_CONFIRMATION"):
    return {"schema":"classical-series-analysis.v1", "seed":seed,
        "census":{"independent_units":1}, "native_seconds":2., "analysis_seconds":1.,
        "stages":{"e5":{"status":status,"nominee":"x-first","gain":gain,"harm":harm},
            "sci01":{"assigned_cells":1000,"evaluable_cells":1000,
                "endpoint_improvement_contrast_reversals":999,"census":[]}}}


@pytest.mark.numerical(oracle="Exact paired fair-coin tail for eight positive discordances: 1/2^8")
def test_paired_eight_gains_keep_exact_tail_and_whole_root_denominator():
    result = aggregate_readouts([_row(i,gain=True) for i in range(8)],assigned_seeds=range(8))
    paired = result["paired_preparation"]
    assert paired["complete_pair_discordance_tail"]["numerator"] == 1
    assert paired["complete_pair_discordance_tail"]["denominator"] == 256
    assert paired["net_gain_fraction_completion_bounds"] == [1.,1.]
    assert result["assigned_confirmation_roots"] == 8
    assert result["signed_error_accounting"]["assigned_nested_cells"] == 8000
    assert result["signed_error_accounting"]["nested_cell_inferential_sample_size"] is False
    assert result["timing"]["complete_programme_cost"] is None
    assert result["actual_native_work_avoided"] == 0


@pytest.mark.numerical(oracle="Clopper-Pearson zero-success and all-success limits plus conservative unknown completions")
def test_all_unknown_keeps_the_whole_unit_interval():
    result = event_summary({1:None,2:None,3:None})
    assert result["population_interval_over_missing_completions"] == [0.,1.]
    assert result["assigned_success_fraction_lower"] == 0.
    assert result["assigned_success_fraction_upper"] == 1.
    assert result["complete_case_interval"] is None


def test_missing_readout_and_nonnomination_remain_unknown_and_paid_work_is_not_zero():
    result = aggregate_readouts([_row(1,gain=True),_row(2,status="NOT_ENTERED")],assigned_seeds=[1,2,3])
    assert result["missing_readout_seeds"] == [3]
    paired = result["paired_preparation"]
    assert paired["unknown_or_not_entered"] == 2
    assert paired["net_gain_fraction_completion_bounds"] == [-1/3,1.]
    # Worst completion: one gain and two harms, P(Bin(3,1/2)>=1)=7/8.
    assert paired["worst_completion_discordance_tail"] == {"numerator":7,"denominator":8,"value":.875}
    assert result["timing"]["missing_native_timing_roots"] == 1


def test_forecast_denominator_keeps_an_unavailable_root_and_nested_coordinates():
    row = _row(1)
    row["stages"]["e3"] = {"coordinates":[{"coordinate":{"id":"T1.125"},"models":{
        "baseline":{"status":"FINITE","admitted":True,"delivered_service":True,"false_admission":False,"covered":True,"point_absolute_error":.5},
        "structure":{"status":"FINITE","admitted":True,"delivered_service":True,"false_admission":False,"covered":True,"point_absolute_error":.1}}}]}
    result = aggregate_readouts([row],assigned_seeds=[1,2],win_margin="0.1")
    win = next(r for r in result["forecast_and_transfer"] if r["event"] == "margin_win")
    assert (win["assigned_roots"],win["successes"],win["unknown"]) == (2,1,1)
    assert win["conservative_assigned_upper_tail"]["value"] == .75


@pytest.mark.parametrize("rows,seeds", (([_row(1),_row(1)],[1]), ([_row(2)],[1]), ([],[1,1])))
def test_duplicate_or_substituted_roots_refuse(rows,seeds):
    with pytest.raises(ValueError,match="duplicat|unique|outside"):
        aggregate_readouts(rows,assigned_seeds=seeds)


def test_a_single_confirmation_cannot_change_its_nominated_preparation():
    one,two = _row(1),_row(2)
    two["stages"]["e5"]["nominee"] = "y-first"
    with pytest.raises(ValueError,match="nominees"):
        aggregate_readouts([one,two],assigned_seeds=[1,2])


def test_invalid_event_cannot_masquerade_as_boolean():
    with pytest.raises(TypeError,match="True, False or None"):
        event_summary({1:1})
    result = event_summary({1:True,2:False},alpha=Fraction(1,20))
    assert result["population_interval_over_missing_completions"][0] < .5
    assert result["population_interval_over_missing_completions"][1] > .5


def test_true_capstone_connections_keep_nested_requests_and_unknown_futures_separate():
    row = _row(1)
    row["stages"]["capstone-forecast"] = {"coefficient_refits_on_confirmation":0,
        "cases":[{"coordinate":{"id":"nominal"},"arm":"baseline","tasks":[
            {"task_id":"one","admitted":True,"delivered_service":True,"false_admission":False,"covered":True},
            {"task_id":"two","admitted":True,"delivered_service":None,"false_admission":None,"covered":None}]}]}
    row["stages"]["capstone-preparation"] = {"coefficient_refits_on_confirmation":0,
        "cases":[],"comparisons":[{"coordinate":{"id":"nominal"},"nominee":"x-first",
            "complete_pair":True,"gain":True,"harm":False,"same_complete_package":True}]}
    result = aggregate_readouts([row],assigned_seeds=[1,2])
    whole = next(x for x in result["capstone_connections"] if x["task"]=="ALL_ASSIGNED_TASKS")
    assert (whole["assigned_roots"],whole["successes"],whole["unknown"]) == (2,0,2)
    gain = next(x for x in result["capstone_preparation_gains"] if x["event"]=="gain")
    assert (gain["successes"],gain["unknown"]) == (1,1)
    assert result["forecast_and_transfer"] == []


def test_capstone_refit_cannot_be_aggregated_as_unchanged_reuse():
    row = _row(1)
    row["stages"]["capstone-preparation"] = {"coefficient_refits_on_confirmation":1}
    with pytest.raises(ValueError,match="frozen"):
        aggregate_readouts([row],assigned_seeds=[1])


def test_unavailable_case_does_not_disappear_from_structural_or_mechanical_tables():
    row = _row(1)
    row["stages"]["e1"] = {"cases":[{"coordinate":"nominal","arm":"baseline","traces":[]}]}
    row["stages"]["e2"] = {"method_menu":["FULL","FACTOR"],"cases":[
        {"coordinate":{"id":"nominal"},"arm":"baseline","status":"UNAVAILABLE"}]}
    result = aggregate_readouts([row],assigned_seeds=[1,2])
    assert len(result["structural_events"]) == 8
    assert len(result["mechanical_adequacy"]) == 4
    for cell in result["structural_events"]+result["mechanical_adequacy"]:
        assert cell["unknown"] == 2 and cell["assigned_roots"] == 2
        assert cell["population_interval_over_missing_completions"] == [0.,1.]


def test_authored_settings_preserve_cells_when_every_root_readout_is_missing():
    settings={"phases":["e1","e2","e3","capstone-forecast","capstone-preparation"]}
    result = aggregate_readouts([],assigned_seeds=[1,2],scientific_settings=settings)
    assert result["cell_census_source"] == "AUTHORED_SETTINGS_AND_ORIGINAL_READOUTS"
    assert len(result["structural_events"]) == 8
    assert len(result["mechanical_adequacy"]) == 18
    assert len(result["forecast_and_transfer"]) == 9
    assert len(result["capstone_connections"]) == 18
    for name in ("structural_events","mechanical_adequacy","forecast_and_transfer","capstone_connections"):
        assert all(cell["unknown"] == 2 for cell in result[name])


def _relation_row(seed):
    row=_row(seed)
    def coordinate(identity,training):
        return {'coordinate':{'id':identity},'training_coordinate':training,'target':.2,
            'models':{kind:{'status':'FINITE','admitted':True,'delivered_service':False,
                'false_admission':True,'covered':False,'actual_adequate':False,
                'coverage_inherited':training,'unresolved_admitted_future':False}
                for kind in ('baseline','structure')}}
    relation={'status':'FROZEN_RELATION_EVALUATED','refits_on_confirmation':0,
        'package_sha256':'a'*64,'training_coordinates':['nominal'],
        'coverage_transported_to_new_coordinates':False,
        'coordinates':[coordinate('nominal',True),coordinate('transfer',False)]}
    row['stages']['e4']={'parameter_relation':relation}
    row['stages']['e6']={'parameter_relation':relation}
    return row


def test_relation_census_counts_each_assigned_root_once_and_separates_transfer():
    first=_relation_row(1); second=_relation_row(2)
    second['stages']['e4']['parameter_relation']['coordinates'][0]['models']['structure'].pop('covered')
    result=aggregate_readouts([first,second],assigned_seeds=[1,2,3])['parameter_relations']
    assert result['assigned_confirmation_roots']==3
    assert result['available_relation_roots']==2
    assert len(result['training_frame'])==10 and len(result['transfer_coordinates'])==10
    coverage=next(r for r in result['training_frame'] if r['account']=='structure' and r['event']=='covered')
    assert (coverage['assigned_roots'],coverage['failures'],coverage['unknown'])==(3,1,2)
    false=next(r for r in result['transfer_coordinates'] if r['account']=='structure' and r['event']=='false_admission')
    assert (false['successes'],false['unknown'])==(2,1)
    whole=next(r for r in result['simultaneous_training_frame'] if r['account']=='structure' and r['event']=='all_training_coordinates_covered')
    assert (whole['failures'],whole['unknown'])==(1,2)
    assert any(c['reason']=='MISSING_RELATION_ACCOUNT_OR_EVENT' and c['seed']==2 for c in result['unavailable_cells'])
    assert not result['coverage_transported_to_new_coordinates']


def test_relation_missing_whole_field_and_readout_remain_typed_unavailable():
    result=aggregate_readouts([_relation_row(1),_row(2)],assigned_seeds=[1,2,3])['parameter_relations']
    assert result['root_census'][1]=={'seed':2,'status':'UNAVAILABLE','reason':'MISSING_PARAMETER_RELATION_FIELD'}
    assert result['root_census'][2]=={'seed':3,'status':'UNAVAILABLE','reason':'MISSING_CONFIRMATION_READOUT'}
    assert all(c['assigned_roots']==3 and c['unknown']==2 for c in result['training_frame'])


def test_relation_authored_frame_is_preserved_when_every_confirmation_is_missing():
    settings={'phases':['e4','e6'],'relation_training_coordinates':['nominal'],
        'coordinates':[{'id':'nominal','temperature':'1','friction':'1','cross_coupling':'1'},
                       {'id':'held','temperature':'1.125','friction':'1','cross_coupling':'1'}]}
    result=aggregate_readouts([],assigned_seeds=[1,2],scientific_settings=settings)['parameter_relations']
    assert len(result['training_frame'])==10 and len(result['transfer_coordinates'])==10
    assert all(c['unknown']==2 for c in result['training_frame']+result['transfer_coordinates'])
    assert all(c['unknown']==2 for c in result['simultaneous_training_frame'])


def test_relation_cannot_pool_changed_packages_or_transport_calibration_coverage():
    first,second=_relation_row(1),_relation_row(2)
    second['stages']['e4']['parameter_relation']['package_sha256']='b'*64
    with pytest.raises(ValueError,match='different fitted'):
        aggregate_readouts([first,second],assigned_seeds=[1,2])
    first['stages']['e4']['parameter_relation']['coordinates'][1]['models']['baseline']['coverage_inherited']=True
    with pytest.raises(ValueError,match='inherited'):
        aggregate_readouts([first],assigned_seeds=[1])
