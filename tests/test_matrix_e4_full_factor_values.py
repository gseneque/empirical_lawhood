# SPDX-License-Identifier: MPL-2.0
"""Disclosed PURE structural controls: no native work, grant, issue or reveal.

Synthetic output locators below exercise typed value joins only. They cannot
stand in for the existing original wave/receipt/reveal reader in production.
"""
from dataclasses import replace
from hashlib import sha256

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime import science as factor
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import expected_members
from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_records as r, full_factor_science as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as dev
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as protected
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_bank_recipe as recipe, records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history.continuation import ScheduledFullArrays
from empirical_lawhood.adapters.simulators.six_matrix_response.model import ideal_state
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import initial_parameter_state
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays, decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, ExecutionPlan
from tests.test_matrix_factor_lifetime import spec, root
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401
from tests.test_matrix_selected_e3_e4_bridge import disclosed_produced_parents
from tests.test_matrix_selected_protected import unpublished


def pin(name,kind):
    return ObjectIdentity(name,kind.SCHEMA,kind.VERSION,sha256(('DISCLOSED.'+name).encode()).hexdigest())


@pytest.fixture(scope='module')
def scopes(literal_recipe_source_inputs):  # noqa: F811
    f=literal_recipe_source_inputs
    allocation=recipe.recipe_allocation(f.inputs)
    reservation=old.ScheduledReservation('reservation.full-factor.disclosed',allocation,unpublished(allocation,'allocation.full-factor.disclosed'))
    selection=recipe.recipe_selection(f.inputs,reservation)
    specification=old.ScheduledSpecification('specification.full-factor.disclosed',selection,unpublished(selection,'selection.full-factor.disclosed'))
    result={}
    criterion=f.inputs.original_preparation.mathematical_protocol
    parents=disclosed_produced_parents(f.inputs.original_products)
    for phase in ('DEVELOPMENT','CONFIRMATION'):
        _,responses=recipe.recipe_responses(f.inputs,reservation,specification,f.case.provenance,phase)
        bank=recipe.recipe_bank(f.inputs,reservation=reservation,specification=specification,provenance=f.case.provenance,
            criterion_publication=unpublished(criterion,'criterion.full-factor.disclosed'),
            response_publication=unpublished(responses,'responses.full-factor.disclosed.'+phase.lower()),phase=phase)
        programme=recipe.recipe_programme(bank,phase)
        cases=[];sources=[]
        index=bank.source_index()
        for declared,descriptor in zip(programme.cases,bank.sources,strict=True):
            original=dev.SelectedE3E4CaseResult.unentered(declared)
            kind=dev.SelectedE3E4NativeSource
            if phase=='CONFIRMATION':
                coordinate=bank.source(declared.root_id,index=index).coordinate
                original=protected.SelectedE4NativeCaseResult(*(getattr(original,name) for name in (
                    'root_id','source','group_id','disposition','numerical_disposition','score_disposition','paired_log_targets',
                    'original_log_points','forecast','score','full_assessment','ordinary_receipts','native','reason_codes')),
                    None,None,None,coordinate)
                kind=protected.SelectedE4ProtectedNativeSource
            source=kind.from_bank(programme,bank,descriptor,index=index)
            supplied=science.source_from_original(record_id='full-factor.'+declared.root_id,source=source,
                criterion=criterion,case=original,original_products=(),produced_input_parents=parents)
            cases.append(original);sources.append(supplied)
        result[phase]=(programme,tuple(cases),tuple(sources))
    return result


def test_root_free_math_preserves_historical_canonical_trace_and_future_causality():
    rule=spec(risk_start_tick=0,trailing_persistence_ticks=0)
    positions=np.zeros((49,2,3,4,4),dtype='<c16')
    positions[:,1]=algebra.RIGHT
    old_measurements={tick:factor.measure_sector(positions[tick,1],rule) for tick in rule.lattice}
    legacy,_=factor.trace(rule,root(),'PRIMARY','Y',old_measurements)
    values,diagnostics=factor.measure_trace_values(rule,'PRIMARY','Y',positions)
    wrapped,old_diagnostics=factor.measure_trace(rule,root(),'PRIMARY','Y',positions)
    assert wrapped.canonical_bytes()==legacy.canonical_bytes()
    assert values==(legacy.observations,legacy.moving_lifetime,legacy.origin_fixed_lifetime)
    assert all(np.array_equal(diagnostics[name],old_diagnostics[name],equal_nan=True) for name in diagnostics)
    changed=positions.copy();changed[48,1]=0
    later,later_diagnostics=factor.measure_trace_values(rule,'PRIMARY','Y',changed)
    assert later[0][:-1]==values[0][:-1]
    assert np.array_equal(diagnostics['spectrum'][:-1],later_diagnostics['spectrum'][:-1],equal_nan=True)
    assert not np.array_equal(diagnostics['spectrum'][-1],later_diagnostics['spectrum'][-1],equal_nan=True)


@pytest.mark.parametrize('phase',('DEVELOPMENT','CONFIRMATION'))
def test_complete_missing_cases_keep_every_whole_group_and_no_false_check(scopes,phase):
    programme,cases,sources=scopes[phase]
    products=[];assessments=[]
    for source in sources:
        raw,product=science.measure(source,None,artifact_id='diagnostics.'+source.root_id)
        assessment=science.assess(source,product,None,raw)
        assert product.traces==() and assessment.disposition=='HISTORY_UNAVAILABLE' and not assessment.witness_pass
        n=product.requested_traces*product.requested_observations
        assert tuple(len(row.measured_errors) for row in assessment.controls)==(n,15*n,n,n,n,n)
        products.append(product);assessments.append(assessment)
    joined=science.census(programme,cases,sources,products,assessments,record_id='census.disclosed.'+phase.lower())
    assert joined.group_ids==programme.group_ids and len(joined.root_ids)==len(programme.cases)
    assert len(joined.cells)==4*len(programme.cases)
    assert all(row.unavailable_observations==row.requested_observations for row in joined.cells)
    assert decode_canonical_bytes(joined.canonical_bytes(),r.ScheduledFullFactorCensus,maximum_bytes=None)==joined
    for changed in ((sources[:-1],products,assessments),(sources,products[:-1],assessments),
            ((replace(sources[0],group_id='group.changed'),*sources[1:]),products,assessments)):
        with pytest.raises(ValueError,match='census|scope|coordinates'):
            science.census(programme,cases,*changed,record_id='census.refused')


def _disclosed_locator(source,record):
    # A type-correct unissued descriptor, not genuine producing custody.
    publication=unpublished(source,'publication.disclosed.'+record.object_id)
    publication=replace(publication,logical=replace(publication.logical,payload_schema=record.object_schema,
        generic_validation=replace(publication.logical.generic_validation,payload_schema=record.object_schema),
        content_sha256=record.object_fingerprint),materialization=replace(publication.materialization,physical_sha256=record.object_fingerprint))
    receipt=pin('receipt.disclosed.'+record.object_id,CanonicalTaskReceipt)
    if source.original_case.object_schema==dev.SelectedE3E4CaseResult.SCHEMA:
        return protected.SelectedE4DevelopmentProduct(record,'disclosed-original','run.disclosed',
            pin('plan.disclosed',DevelopmentExecutionPlan),'task.disclosed.'+record.object_id,receipt,publication)
    wave=protected.SelectedE4WaveLocator('wave.disclosed','run.disclosed',
        ObjectIdentity('package.disclosed','empirical-lawhood/api/experiment-package','1.0.0','a'*64),
        ObjectIdentity('issue.disclosed','empirical-lawhood/tests/issue','1.0.0','b'*64),
        ObjectIdentity('execution.disclosed','empirical-lawhood/tests/execution','1.0.0','c'*64),
        ObjectIdentity('reveal.disclosed','empirical-lawhood/tests/reveal','1.0.0','d'*64),pin('plan.disclosed',ExecutionPlan))
    return r.ScheduledFullFactorProtectedProduct(record,wave,'task.disclosed.'+record.object_id,receipt,publication)


def _analytic_full(source,numerical_pass):
    """Analytic fields only: these values claim no trajectory/native completion."""
    c=source.coordinate
    arrays={name:np.zeros(shape,dtype=dtype) for name,(dtype,shape) in expected_members(c).items()}
    for view,multiplier in (('primary',1),('fine',2)):
        count=multiplier*c.total_ticks+1
        arrays[view+'_ticks']=np.arange(count,dtype='<i8')
        couplings=np.asarray([c.couplings(tick,refinement=multiplier) for tick in range(count)],dtype='<f8')
        arrays[view+'_alpha_tilde']=couplings
        for index,(x,y) in enumerate(couplings):
            arrays[view+'_positions'][index]=ideal_state(q=2,alpha_tilde_x=x,alpha_tilde_y=y,constitution='11').positions
        arrays[view+'_positions'][0]=initial_parameter_state(c).positions
        arrays[view+'_momenta'][0]=initial_parameter_state(c).momenta
    raw,members=encode_matrix_arrays(arrays)
    artifact=ArtifactIdentity('arrays.disclosed.analytic','disclosed-analytic-only',MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(),'application/x-npz',len(raw))
    is_protected=source.original_case.object_schema==protected.SelectedE4NativeCaseResult.SCHEMA
    history=pin('history.disclosed',protected.SelectedE4ProtectedFullHistory if is_protected else dev.SelectedE3E4FullHistory)
    causal=pin('causal.disclosed',protected.SelectedE4ProtectedCausalPrefix if is_protected else dev.SelectedE3E4CausalPrefix)
    numerical=None if numerical_pass is None else pin('numerical.disclosed',
        protected.SelectedE4ProtectedNumericalAssessment if is_protected else dev.SelectedE3E4NumericalAssessment)
    full=ScheduledFullArrays('full-arrays.disclosed',source.source,artifact,members,(source.source,),
        OutcomeAccess.EVALUATION_SEALED if is_protected else OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.PROSPECTIVE if is_protected else VisibilityCeiling.DEVELOPMENT_ONLY)
    selected=replace(source,source_state='COMPLETED',causal_disposition='NO_ORIGIN',causal_prefix=causal,
        history=history,full_arrays=full,full_numerical=numerical,history_numerical_pass=numerical_pass,
        original_products=tuple(_disclosed_locator(source,pin) for pin in (causal,history,numerical) if pin is not None))
    return selected,raw


@pytest.mark.parametrize('phase',('DEVELOPMENT','CONFIRMATION'))
@pytest.mark.parametrize('numerical_pass,expected',((None,'HISTORY_NUMERICAL_UNASSESSED'),(False,'HISTORY_NUMERICALLY_FAILED')))
def test_no_origin_full_history_is_measured_without_replacing_original_numerical_state(scopes,phase,numerical_pass,expected):
    source,raw=_analytic_full(scopes[phase][2][0],numerical_pass)
    diagnostic,product=science.measure(source,raw,artifact_id='diagnostic.disclosed.analytic')
    assessment=science.assess(source,product,raw,diagnostic)
    assert len(product.traces)==4 and all(len(row.observations)==len(source.rule.lattice) for row in product.traces)
    assert assessment.disposition==expected and assessment.history_numerical_pass is numerical_pass
    assert product.arrays.outcome_access is source.outcome_access
    if phase=='CONFIRMATION':
        assert source.full_arrays.outcome_access is OutcomeAccess.EVALUATION_SEALED
        assert product.arrays.outcome_access is OutcomeAccess.EVALUATION_REVEALED
        assert product.arrays.visibility_ceiling is VisibilityCeiling.OUTCOME_VISIBLE
    assert science.read_retained(source,product,assessment,raw,diagnostic)==assessment
    if phase=='DEVELOPMENT' and numerical_pass is None:
        from empirical_lawhood.api.matrix_retained_replay import replay_full_factor, replay_weight
        from empirical_lawhood.infrastructure.parallel_verification import CanonicalValidationPool
        weight=replay_weight(records=(source,product,assessment),archives=((raw,source.full_arrays),(diagnostic,product.arrays)))
        value=(weight,(source,product,assessment,raw,diagnostic))
        pool=CanonicalValidationPool(2)
        try:
            assert pool.project_ordered(replay_full_factor,(value,value))==(source.root_id,)*2
        finally:pool.close()
    with pytest.raises(ValueError,match='artifact|bytes|original'):
        science.measure(source,raw+b'changed',artifact_id='diagnostic.refused')
    with pytest.raises(ValueError,match='lattice|clock|rule'):
        replace(source,rule=replace(source.rule,lattice=source.rule.lattice[:-1]))
    first=source.original_products[0]
    if phase=='DEVELOPMENT':
        changed=replace(first,execution_plan=pin('plan.foreign',DevelopmentExecutionPlan))
    else:
        changed=replace(first,wave=replace(first.wave,execution_plan=pin('plan.foreign',ExecutionPlan)))
    with pytest.raises(ValueError,match='different waves|authority'):
        replace(source,original_products=(changed,*source.original_products[1:]))


def test_independent_full_history_witness_refuses_forged_stored_operator(scopes):
    source,raw=_analytic_full(scopes['DEVELOPMENT'][2][0],True)
    diagnostic,product=science.measure(source,raw,artifact_id='diagnostic.disclosed.forgery')
    arrays=dict(decode_matrix_arrays(diagnostic,product.arrays))
    name=next(name for name in arrays if name.endswith('_operator'))
    arrays[name]=arrays[name].copy();arrays[name][-1]+=np.eye(15)
    nonfinite=tuple(name for name in arrays if not name.endswith(('_ticks','_available','_identifiable')))
    forged,members=encode_matrix_arrays(arrays,nonfinite_members=nonfinite)
    artifact=replace(product.arrays.array_artifact,sha256=sha256(forged).hexdigest(),size_bytes=len(forged))
    operand=replace(product.arrays,array_artifact=artifact,members=members)
    traces=tuple(replace(trace,diagnostics=artifact,diagnostic_members=members) for trace in product.traces)
    altered=replace(product,arrays=operand,traces=traces)
    assessment=science.assess(source,altered,raw,forged)
    assert not assessment.witness_pass and assessment.disposition=='WITNESS_NOT_ESTABLISHED'
    assert next(row for row in assessment.controls if row.method=='raw-operator').disposition=='VIOLATED'


@pytest.mark.parametrize('history_available', (False, True))
def test_full_factor_diagnostics_retain_sealed_development_ancestry(scopes, history_available):
    """Exposed analytic values exercise inherited labels, never actual access."""
    source = scopes['DEVELOPMENT'][2][0]
    raw = None
    if history_available:
        source, raw = _analytic_full(source, False)
    original_raw, original = science.measure(source, raw, artifact_id='diagnostics.disclosed.ancestry')
    parents = tuple(replace(parent, outcome_access=OutcomeAccess.EVALUATION_SEALED,
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE) for parent in source.produced_input_parents)
    source = replace(source, produced_input_parents=parents)
    assert source.access_pair == (OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.DEVELOPMENT_ONLY)
    diagnostic, product = science.measure(source, raw, artifact_id='diagnostics.disclosed.ancestry')
    assert diagnostic == original_raw and product.scalars == original.scalars
    assert tuple(trace.observations for trace in product.traces) == tuple(trace.observations for trace in original.traces)
    assert (product.arrays.outcome_access, product.arrays.visibility_ceiling) == source.access_pair
    assert product.arrays.producers == source.producers
    assert decode_canonical_bytes(product.canonical_bytes(), r.ScheduledFullFactorProduct,
        maximum_bytes=None) == product
    assessment = science.assess(source, product, raw, diagnostic)
    assert assessment.history_available is history_available
    assert assessment.disposition == ('HISTORY_NUMERICALLY_FAILED' if history_available else 'HISTORY_UNAVAILABLE')
    assert science.read_retained(source, product, assessment, raw, diagnostic) == assessment
    relabelled = replace(product, arrays=replace(product.arrays, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
    with pytest.raises(ValueError, match='complete original source/physical/analysis scope'):
        r.validate_product(source, relabelled)
