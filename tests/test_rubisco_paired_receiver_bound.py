# SPDX-License-Identifier: MPL-2.0
"""Disclosed exact controls; these premises are not molecular evidence."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import json

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact as E
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialSourceDocument
from empirical_lawhood.domains.rubisco.rubisco_response.paired_receiver_bound import ADDED_COSTS, CORRECTIONS, PREMISES, JointErrorVertex, PairedReceiverBoundInput, ReceiverBoundPremise, ReceiverShortcutCost, assess_paired_receiver_bound, bound_paired_receiver, periodic_receiver_omission_coefficient, assess_periodic_receiver_omission_coefficient
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff


def test_periodic_geometric_bound_uses_exact_outward_cell_diagonal():
    # Independent 3-4-12 triangle: box diagonal is exactly 13 angstrom.
    cell=(D(3),D(4),D(12))
    with localcontext() as context:
        context.prec=2
        bound=periodic_receiver_omission_coefficient(cell)
    coefficient=bound['coefficient_j_mol_per_kj_mol_angstrom2_per_angstrom']
    assert F(coefficient['numerator'],coefficient['denominator'])==13000
    assert assess_periodic_receiver_omission_coefficient(cell,bound)['numerical_disposition']=='SATISFIED'
    assert assess_periodic_receiver_omission_coefficient(cell,json.loads(json.dumps(bound)))['numerical_disposition']=='SATISFIED'
    assert bound['activation_correction_bound_j_mol'] is None
    # At opposite limiting geometries xi_W=6.5, xi_M=-6.5, the bare
    # paired difference attains 1000*k*13. No cancellation is presumed.
    assert abs(1000*F(7,2)*(F(13,2)-F(-13,2)))==13000*F(7,2)


def test_geometric_bound_reader_refuses_inward_rounding_and_barrier_promotion():
    cell=(D(1),D(1),D(1))
    bound=periodic_receiver_omission_coefficient(cell)
    diagonal=bound['paired_coordinate_span_upper_angstrom']
    upper=F(diagonal['numerator'],diagonal['denominator'])
    assert upper**2>=3 and (upper-F(1,10**12))**2<3
    assert assess_periodic_receiver_omission_coefficient(cell,bound)['numerical_disposition']=='SATISFIED'
    changed=dict(bound,paired_coordinate_span_upper_angstrom={'numerator':1,'denominator':1})
    assert assess_periodic_receiver_omission_coefficient(cell,changed)['numerical_disposition']=='FALSIFIED'
    changed=dict(bound,formula='abs(Q_k) <= coefficient')
    assert assess_periodic_receiver_omission_coefficient(cell,changed)['numerical_disposition']=='FALSIFIED'
    changed=dict(bound,activation_correction_bound_j_mol={'numerator':0,'denominator':1})
    assert assess_periodic_receiver_omission_coefficient(cell,changed)['numerical_disposition']=='FALSIFIED'


def exposed_input():
    source=InitialSourceDocument('source.receiver.exposed','urn:exposed:receiver',
        'Disclosed software-only premises, costs and errors; not molecular qualification.','MODEL_SPECIFICATION').identity
    now=InformationCutoff('cutoff.receiver.now','clock.receiver',CausalPhase.PRE_ACTION,D(1))
    before=replace(now,cutoff_id='cutoff.receiver.before',coordinate=D(0))
    premises=tuple(ReceiverBoundPremise(p,A.SATISFIED,source,before,'Disclosed premise for software control.') for p in PREMISES)
    costs=ReceiverShortcutCost('cost.receiver',(E.of(10),E.of(20)),
        tuple((c,(E.of(0),E.of(1))) for c in ADDED_COSTS),(source,),'USD_TOTAL_COST')
    # Complete joint errors: two WT, two mutant, six separate corrections.
    vertices=tuple(JointErrorVertex('vertex.'+str(i),tuple(E.of(v) for v in row)) for i,row in enumerate((
        (100,50,101,49,0,0,0,0,0,0),
        (-100,-50,-101,-49,0,0,0,0,0,0))))
    return PairedReceiverBoundInput('input.receiver',source,source,source,('node.0','node.1'),
        (E.of(F(1,2)),E.of(F(1,2))),vertices,E.of(1),'RIGOROUS_BOUND',now,premises,(source,),False,costs,(source,))


def assess(selection):
    result=bound_paired_receiver(selection,result_id='result.receiver')
    return result,assess_paired_receiver_bound(selection,result)


def test_signed_pair_cancellation_and_independent_dual_check():
    selected=exposed_input()
    with localcontext() as ctx:
        ctx.prec=2
        result,report=assess(selected)
    assert tuple(v.fraction for v in result.signed_vertex_errors_j_mol)==(0,0)
    assert result.absolute_error_bound_j_mol.fraction==0
    assert report['shortcut_disposition']=='CONDITIONAL_CANDIDATE_WITHIN_REVIEWED_PREMISES'
    assert report['physical_rate_admission']=='UNEVALUABLE'
    assert decode_canonical_bytes(canonical_json_bytes(selected),PairedReceiverBoundInput,maximum_bytes=2**20)==selected


@pytest.mark.parametrize('coordinate',range(len(CORRECTIONS)))
def test_each_omitted_correction_remains_in_paired_bound(coordinate):
    selected=exposed_input()
    values=list(selected.vertices[0].parameter_errors)
    values[4+coordinate]=E.of(2)
    selected=replace(selected,vertices=(replace(selected.vertices[0],parameter_errors=tuple(values)),))
    result,report=assess(selected)
    assert result.absolute_error_bound_j_mol.fraction==2
    assert 'PAIRED_ERROR_EXCEEDS_SELECTED_TOLERANCE' in report['reason_codes']
    assert report['shortcut_disposition']=='RETAIN_NATIVE_REFERENCE'


@pytest.mark.parametrize('edit,reason',[
    (lambda s:replace(s,vertices=()),'JOINT_ERROR_SET_UNAVAILABLE'),
    (lambda s:replace(s,interpretation='DEVELOPMENT_HEURISTIC'),'HEURISTIC_CANNOT_ADMIT_OMITTED_WORK'),
    (lambda s:replace(s,interpretation='CALIBRATED_BOUND'),'CALIBRATION_HAS_NO_ADMITTED_SIMULTANEOUS_STOPPING_COVERAGE'),
    (lambda s:replace(s,requires_omitted_work_outputs=True),'BOUND_REQUIRES_THE_WORK_IT_CLAIMS_TO_AVOID'),
    (lambda s:replace(s,omitted_work=()),'NO_CONCRETE_OMITTED_WORK_CONTRACT'),
    (lambda s:replace(s,costs=replace(s.costs,avoided_reference_cost=None)),'COMPLETE_NET_WORK_SAVING_UNEVALUABLE'),
    (lambda s:replace(s,costs=replace(s.costs,avoided_reference_cost=(E.of(9),E.of(100)))),
        'COMPLETE_ADDED_COST_NOT_STRICTLY_LESS_THAN_AVOIDED_COST'),
])
def test_unsupported_or_uneconomic_omission_retains_reference(edit,reason):
    _,report=assess(edit(exposed_input()))
    assert reason in report['reason_codes']
    assert report['shortcut_disposition']=='RETAIN_NATIVE_REFERENCE'


@pytest.mark.parametrize('cost_index',range(len(ADDED_COSTS)))
def test_unknown_added_cost_is_not_zero(cost_index):
    selected=exposed_input()
    costs=list(selected.costs.added_costs)
    costs[cost_index]=(costs[cost_index][0],None)
    _,report=assess(replace(selected,costs=replace(selected.costs,added_costs=tuple(costs))))
    assert 'COMPLETE_NET_WORK_SAVING_UNEVALUABLE' in report['reason_codes']


@pytest.mark.parametrize('index',range(len(PREMISES)))
def test_missing_scientific_premise_is_not_math_acceptance(index):
    selected=exposed_input()
    premises=list(selected.premises)
    premises[index]=replace(premises[index],disposition=A.UNEVALUABLE,evidence=None,available_at=None)
    _,report=assess(replace(selected,premises=tuple(premises)))
    assert report['numerical_disposition']=='SATISFIED'
    assert 'UNSUPPORTED_PREMISE.'+PREMISES[index] in report['reason_codes']


@pytest.mark.parametrize('clock,coordinate,phase',[
    ('clock.foreign',D(0),CausalPhase.PRE_ACTION),
    ('clock.receiver',D(2),CausalPhase.PRE_ACTION),
    ('clock.receiver',D(1),CausalPhase.POST_OUTCOME),
])
def test_unavailable_evidence_cannot_justify_stopping(clock,coordinate,phase):
    selected=exposed_input()
    first=selected.premises[0]
    late=replace(first.available_at,clock_id=clock,coordinate=coordinate,phase=phase)
    selected=replace(selected,premises=(replace(first,available_at=late),*selected.premises[1:]))
    _,report=assess(selected)
    assert 'UNAVAILABLE_BEFORE_DECISION.'+PREMISES[0] in report['reason_codes']


def test_independent_assessor_rejects_changed_support_projection():
    selected=exposed_input()
    result,_=assess(selected)
    altered=replace(result,signed_vertex_errors_j_mol=(E.of(1),E.of(0)))
    report=assess_paired_receiver_bound(selected,altered)
    assert report['numerical_disposition']=='FALSIFIED'
    assert report['shortcut_disposition']=='RETAIN_NATIVE_REFERENCE'
    with pytest.raises(ValueError,match='exact selected error problem'):
        assess_paired_receiver_bound(replace(selected,weights_angstrom=(E.of(1),E.of(2))),result)
