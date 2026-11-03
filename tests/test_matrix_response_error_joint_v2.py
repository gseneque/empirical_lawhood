# SPDX-License-Identifier: MPL-2.0
"""Exposed software-only joint design/port controls; never fresh qualification."""

from decimal import Decimal as D, localcontext
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import eligibility as p
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import (
    FEATURES, development_roles, fit_error_model,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_joint_v2 import (
    CALIBRATION_ROLE, EVALUATION_ROLE, STRATA, MatrixResponseCausalErrorInputV2,
    MatrixResponseErrorGroupV2, MatrixResponseErrorRolesV2, MatrixResponseJointDesignV2,
    MatrixResponseJointForecastV2, calibrate,
    calibration_radius, causal_input_from_origin, evaluate, forecast, identity, split_rank,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_joint_bindings_v2 import INPUTS, BUDGET, MatrixResponseJointForecastConfigV2, MatrixResponseJointForecastRunnerV2, node_id, operation_factory, operation_registration, selected_manifest, validate_native_forecast_gate
from empirical_lawhood.adapters.methods.matrix_factor_response.records import identity as response_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole as Role
from empirical_lawhood.adapters.methods.matrix_prospective.example import example_source
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import (
    DependencyReceiptBinding, TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort,
    WorkerIsolationProfile, WorkerOutputPort,
)
from tests.test_matrix_factor_response import mechanical_case
from tests.test_matrix_response_frontier import numerical_operands, numerical_origin, bind_numerical_identities, replace
from tests.test_matrix_response_error_prediction import spec as old_spec_fixture, inputs as old_inputs
from tests.test_matrix_factor_confirmation_eligibility import publish, artifact
from tests.test_recursive_public_service import _plane


def obj(name,schema='empirical-lawhood/tests/exposed-fixture'):
    return ObjectIdentity(name,schema,'1.0.0',sha256(name.encode()).hexdigest())


@pytest.fixture(scope='module')
def case(tmp_path_factory):
    plane=_plane(tmp_path_factory.mktemp('joint-v2-exposed')/'plane')
    d,initial,templates,mechanical_model=mechanical_case()
    d=replace(d,horizon_steps=(16,64,128),receiver_count=48,
        actions=tuple(replace(a,amplitude=D('.01'),pulse_steps=16) for a in d.actions))
    templates=templates|{'receiver_coefficients':np.eye(48,dtype='<f8').reshape(48,2,2,3,4)}
    source,origin,past=numerical_operands(d,initial,templates,mechanical_model)
    old=old_spec_fixture.__wrapped__()
    criterion=replace(old.population.policy.protocol,factor_rule=d.rule.identity)
    policy=replace(old.population.policy,protocol=criterion)
    selections=tuple(replace(s,policy=policy.identity) for s in old.population.selections)
    population=replace(old.population,policy=policy,selections=selections)
    old_roles=development_roles(population,record_id=old.roles.record_id)
    from tests.test_matrix_response_error_prediction import publication
    old=replace(old,population=population,roles=old_roles,roles_publication=publication(old_roles))
    train=old_inputs(old,role='TRAIN')
    model=fit_error_model(old,*train,method='ALL_ORIGIN',record_id='fixture.joint.training-model')
    original=example_source()
    from empirical_lawhood.adapters.methods.matrix_factor_response.exposure import (
        MANDATORY_EFFECTIVE_SEEDS, MANDATORY_FLOOR_IDENTITY, MANDATORY_FLOOR_SHA256,
        MatrixConstantPhysicalExclusion,
    )
    facts=(artifact('fixture.joint.audit'),artifact('fixture.joint.bank'))
    regime=p.MatrixFactorRegime(original.protocol.root.regime_id,original.protocol.member,
        original.protocol.view,original.protocol.alpha_x,original.protocol.alpha_y)
    seeds=MANDATORY_EFFECTIVE_SEEDS | {stream.effective_seed
        for root in original.allocation.streams.roots for stream in root.scientific_seeds}
    exposure=p.MatrixFactorExposureCensus('fixture.joint.exposure',MANDATORY_FLOOR_IDENTITY,
        tuple(sorted(seeds)),(original.protocol.root.independent_group_id,),
        (original.protocol.root.regime_id,),(MatrixConstantPhysicalExclusion(*regime.physical_parameters),),(),
        tuple(sorted({'f'*64,MANDATORY_FLOOR_SHA256,*(value.sha256 for value in facts)})),facts)
    roots,groups,regimes=[],[],[]
    for family_index,family in enumerate(STRATA):
        regime_id=f'fixture.joint.regime.f{family_index}'
        regimes.append(p.MatrixFactorRegime(regime_id,d.member,d.view,d.alpha_x,d.alpha_y))
        for role,count in ((CALIBRATION_ROLE,79),(EVALUATION_ROLE,1)):
            for number in range(count):
                root=f'fixture.joint.root.f{family_index}.{role.lower()}.{number:03d}'
                group=f'fixture.joint.group.f{family_index}.{role.lower()}.{number:03d}'
                if family_index==0 and role==EVALUATION_ROLE:
                    root,group=source.root.root_id,source.root.independent_group_id
                streams=tuple(p.MatrixFactorStream(name,name+'.panel',(1<<96)+len(roots)*3+i,kind)
                    for i,(name,kind) in enumerate((('independent','INDEPENDENT_FUTURE'),('paired','COMMON_NOISE_PANEL'),('prefix','PREFIX'))))
                roots.append(p.MatrixFactorRootAllocation(root,group,regime_id,root+'.coordinate',root+'.clock',
                    Role.CALIBRATION if role==CALIBRATION_ROLE else Role.CONFIRMATION,streams))
                groups.append(MatrixResponseErrorGroupV2(group,family,role,(root,)))
    transfer_id='fixture.joint.regime.transfer'
    regimes.append(p.MatrixFactorRegime(transfer_id,d.member,replace(d.view,bath_temperature=D(2)),d.alpha_x,d.alpha_y))
    streams=tuple(p.MatrixFactorStream(name,name+'.panel',(1<<97)+i,kind) for i,(name,kind) in enumerate(
        (('independent','INDEPENDENT_FUTURE'),('paired','COMMON_NOISE_PANEL'),('prefix','PREFIX'))))
    roots.append(p.MatrixFactorRootAllocation('fixture.joint.transfer','fixture.joint.transfer-group',transfer_id,
        'fixture.joint.transfer-coordinate','fixture.joint.transfer-clock',Role.WITHHELD_TRANSFER,streams))
    allocation=p.MatrixFactorAllocation('fixture.joint.allocation',tuple(sorted(roots,key=lambda r:r.root_id)),exposure,
        regimes=tuple(sorted(regimes,key=lambda r:r.regime_id)))
    reservation=p.MatrixAllocationReservation('fixture.joint.reservation',allocation,publish(plane,allocation,'fixture.joint.allocation'))
    reserve_id=ObjectIdentity.from_record(reservation.reservation_id,reservation)
    roles=MatrixResponseErrorRolesV2('fixture.joint.roles',reserve_id,tuple(sorted(groups,key=lambda g:g.independent_group_id)),
        tuple((f,(f'fixture.joint.regime.f{i}',)) for i,f in enumerate(STRATA)))
    design=MatrixResponseJointDesignV2('fixture.joint.design',roles.identity,reserve_id,identity(model),old.identity,criterion.identity)
    roles.validate_reservation(reservation);design.validate_roles(roles)
    result=SimpleNamespace(plane=plane,source=source,origin=origin,past=past,
        training=old,model=model,criterion=criterion,reservation=reservation,roles=roles,design=design)
    # Only literal arithmetic operands have projected PINs. All canonical
    # feature/model/calibration bytes, receipts and substitutions remain real.
    with pytest.MonkeyPatch.context() as patch:
        projected=bind_numerical_identities(patch,source,origin)
        patch.setattr(__name__ + ".response_identity",projected)
        yield result


def feature(case,root,*,refused=False):
    group=next(g for g in case.roles.groups if root in g.root_ids)
    values={name:D(0) for name in FEATURES}
    values.update({'alpha-x':D('.666'),'alpha-y':D('7.333'),'bath-temperature':D(1),'cross-gamma':D(1),
        'friction':D(1),'potential-m':D('.5'),'cutoff':D(0)})
    values.update({'family-'+f.rsplit('.',1)[1]:D(f==group.family_id) for f in STRATA[1:]})
    return MatrixResponseCausalErrorInputV2('feature.'+root,case.design.identity,root,group.independent_group_id,group.family_id,
        response_identity(case.source),response_identity(case.origin),case.source.root.clock_id,D(0),case.origin.frame_sha256,
        'REFUSED' if refused else 'AVAILABLE',() if refused else tuple(sorted(values.items())),(obj('fixture.actual-prefix-custody'),))


def calibration(case,*,unknown=False,refused=False):
    roots=tuple(sorted(r for g in case.roles.groups if g.role==CALIBRATION_ROLE for r in g.root_ids))
    features=tuple(feature(case,r,refused=refused) for r in roots)
    outcomes=tuple((r,(None,)*15 if unknown else tuple(D(j+1) for _ in range(5) for j in range(3)),
        ('UNKNOWN_CONTACT',)*15 if unknown else ('FINITE',)*15) for r in roots)
    return calibrate(case.design,case.roles,case.model,features,outcomes,record_id='fixture.joint.calibration'),features,outcomes


@pytest.fixture(scope='module')
def calibrated(case):
    return calibration(case)[0]


def test_exact_boundary_ranks_and_original16_infinity_without_decimal_rounding(case,calibrated):
    assert split_rank(78,D('.0125'))==79 and split_rank(79,D('.0125'))==79
    assert split_rank(16,D('.05'))==17
    with localcontext() as context:
        context.prec=1
        assert split_rank(79,D('.0125'))==79
    assert all(calibration_radius(calibrated,f)[:2]==(79,79) for f in STRATA)
    rows=tuple(s for s in calibrated.scores if s[1]==STRATA[0])[:16]
    short=replace(calibrated,scores=rows)
    assert calibration_radius(short,STRATA[0],D('.05'))==(16,17,None)
    with pytest.raises(ValueError,match='79'):
        reduced=replace(case.roles,groups=tuple(g for g in case.roles.groups if not g.independent_group_id.endswith('.calibration.078')))
        replace(case.design,roles=reduced.identity).validate_roles(reduced)


def test_complete79_scores_and_unknown_nonuse_infinity_not_dropped(case,calibrated):
    assert len(calibrated.scores)==316 and all(s[2] is not None for s in calibrated.scores)
    unknown,features,outcomes=calibration(case,unknown=True)
    assert len(unknown.scores)==316 and all(s[2] is None for s in unknown.scores)
    assert all(calibration_radius(unknown,f)==(79,79,None) for f in STRATA)
    with pytest.raises(ValueError,match='drops'):
        calibrate(case.design,case.roles,case.model,features[:-1],outcomes,record_id='fixture.thinned')
    with pytest.raises(ValueError,match='thins'):
        bad=(outcomes[0][0],outcomes[0][1][:-1],outcomes[0][2][:-1])
        calibrate(case.design,case.roles,case.model,features,(bad,*outcomes[1:]),record_id='fixture.thinned-endpoint')


def test_exact_roles_reservation_model_criterion_and_exposed_relabel_refusals(case,calibrated):
    group=case.roles.groups[0]
    bad=replace(group,role=EVALUATION_ROLE)
    changed=replace(case.roles,groups=(bad,*case.roles.groups[1:]))
    with pytest.raises(ValueError,match='cross'):
        changed.validate_reservation(case.reservation)
    exposure=replace(case.reservation.allocation.exposure,exposed_independent_groups=tuple(sorted((
        *case.reservation.allocation.exposure.exposed_independent_groups,group.independent_group_id))))
    allocation=replace(case.reservation.allocation,exposure=exposure)
    reserve=p.MatrixAllocationReservation('fixture.exposed-reserve',allocation,publish(case.plane,allocation,'fixture.exposed-allocation'))
    changed=replace(case.roles,reservation=ObjectIdentity.from_record(reserve.reservation_id,reserve))
    with pytest.raises(ValueError,match='exposed'):
        changed.validate_reservation(reserve)
    f=feature(case,case.source.root.root_id)
    with pytest.raises(ValueError,match='model'):
        forecast(case.design,case.roles,replace(case.model,record_id='fixture.changed-model'),calibrated,f,record_id='fixture.changed')
    with pytest.raises(ValueError,match='criterion'):
        replace(case.design,criterion=obj('foreign'))
    with pytest.raises(ValueError,match='family'):
        forecast(case.design,case.roles,case.model,calibrated,replace(f,values=tuple((n,D(1) if n=='family-de-anneal' else v)
            for n,v in f.values)),record_id='fixture.foreign-family')


def test_all_refusal_and_unknown_denominator_never_become_usefulness(case):
    c,_,_=calibration(case,refused=True)
    roots=tuple(sorted(r for g in case.roles.groups if g.role==EVALUATION_ROLE for r in g.root_ids))
    forecasts=tuple(forecast(case.design,case.roles,case.model,c,feature(case,r,refused=True),record_id='forecast.'+r) for r in roots)
    outcomes=tuple((r,(None,)*15,('REFUSED',)*15) for r in roots)
    result=evaluate(case.design,case.roles,forecasts,outcomes,record_id='fixture.all-refusal')
    assert len(result.cells)==60 and all(not row[4] and row[5] is None and row[3]=='NONUSE' for row in result.cells)
    assert result.qualification=='NOT_ESTABLISHED' and result.usefulness.startswith('UNASSESSED')
    with pytest.raises(ValueError,match='drops'):
        evaluate(case.design,case.roles,forecasts[:-1],outcomes,record_id='fixture.dropped')


def port(record,name,*,kind=WorkerInputKind.DEPENDENCY,access=Access.DEVELOPMENT_VISIBLE,visibility=Visibility.DEVELOPMENT_ONLY):
    raw=record.canonical_bytes()
    binding=WorkerInputBinding(name,'materialization.'+name,record.SCHEMA,'application/json',len(raw),visibility,access,kind)
    return WorkerInputPort(binding,BytesIO(raw))


def forecast_context(case,calibration,*,defect=None,protected=False):
    f=feature(case,case.source.root.root_id)
    values=dict(design=case.design,roles=case.roles,reservation=case.reservation,criterion=case.criterion,
        model=case.model,calibration=calibration,feature=f,**{'training-spec':case.training})
    producers=tuple((n,'fixture.producer.'+n) for n,_ in INPUTS)
    config=MatrixResponseJointForecastConfigV2('config.'+node_id(f.root_id,protected),case.design.identity,
        f.root_id,f.independent_group_id,f.family_id,f.source,producers,protected)
    access=Access.OUTCOME_BLIND if protected else Access.DEVELOPMENT_VISIBLE
    visibility=Visibility.PROSPECTIVE if protected else Visibility.DEVELOPMENT_ONLY
    if defect=='criterion':values['criterion']=replace(case.criterion,protocol_id='fixture.foreign-criterion')
    if defect=='role':values['roles']=replace(case.roles,record_id='fixture.foreign-roles')
    ports=[port(config,'config',kind=WorkerInputKind.EXTERNAL,access=access,visibility=visibility)]
    receipts=[]
    for name,_ in INPUTS:
        selected=port(values[name],name,access=access,visibility=visibility)
        producer='fixture.foreign-producer.'+name if defect==name else 'fixture.producer.'+name
        ports.append(selected);receipts.append(DependencyReceiptBinding('receipt.'+name,producer,(selected.materialization_id,)))
    output=WorkerOutputPort('forecast',MatrixResponseJointForecastV2.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json','fixture.output.forecast')
    m=selected_manifest(protected)
    ports.sort(key=lambda p:p.artifact_id)
    context=TaskContext('run.fixture',''+node_id(f.root_id,protected),'attempt.fixture',
        CapabilityConfigRef(config.config_id,config.SCHEMA,sha256(config.SCHEMA.encode()).hexdigest(),config.fingerprint(),'config'),
        tuple(p.binding for p in ports),tuple(ports),(output,),m.permissions,access,BUDGET,WorkerIsolationProfile.TRUSTED_LOCAL,
        tuple(sorted(receipts,key=lambda r:r.receipt_id)))
    return context,config


@pytest.mark.parametrize('protected',(False,True))
def test_actual_path_free_freeze_provider_with_complete_receipt_bound_operands(case,calibrated,protected):
    context,_=forecast_context(case,calibrated,protected=protected)
    result=MatrixResponseJointForecastRunnerV2(protected).execute(context)
    forecast_record=decode_canonical_bytes(result.outputs[0].payload,MatrixResponseJointForecastV2,maximum_bytes=None)
    assert len(forecast_record.log_error_uppers)==15 and all(v is not None for v in forecast_record.log_error_uppers)
    assert forecast_record.qualification=='NOT_ESTABLISHED'
    assert operation_registration(protected).barrier.value=='FREEZE'
    assert not operation_registration(protected).native_effect
    assert operation_factory(protected).registration==operation_registration(protected)


@pytest.mark.parametrize('defect',tuple(n for n,_ in INPUTS)+('criterion','role'))
def test_actual_freeze_provider_refuses_missing_receipt_or_changed_exact_operands(case,calibrated,defect):
    context,_=forecast_context(case,calibrated,defect=defect)
    with pytest.raises(ValueError):
        MatrixResponseJointForecastRunnerV2().execute(context)


def test_forecast_gate_checks_receipt_and_disclosed_numerical_clock_frame_cutoff(case,calibrated):
    """Literal numerical joins only; no source authentication or native-entry authority."""
    result=forecast(case.design,case.roles,case.model,calibrated,feature(case,case.source.root.root_id),record_id='forecast.fixture')
    p0=port(result,'forecast')
    receipt=DependencyReceiptBinding('receipt.forecast',node_id(case.source.root.root_id),(p0.materialization_id,))
    context=SimpleNamespace(dependency_receipts=(receipt,))
    proof=validate_native_forecast_gate(context,p0,design=case.design,criterion=case.criterion,
        source=case.source,origin=case.origin,expected_forecast_task_id=receipt.task_id)
    assert proof['receipt_id']==receipt.receipt_id
    for field,value in (('clock_id','clock.foreign'),('frame_sha256','f'*64),('cutoff',D('.001'))):
        changed=replace(result,feature=replace(result.feature,**{field:value}))
        with pytest.raises(ValueError,match='substitutes'):
            validate_native_forecast_gate(context,port(changed,'forecast'),design=case.design,criterion=case.criterion,
                source=case.source,origin=case.origin,expected_forecast_task_id=receipt.task_id)
    with pytest.raises(ValueError,match='receipt'):
        validate_native_forecast_gate(SimpleNamespace(dependency_receipts=()),port(result,'forecast'),
            design=case.design,criterion=case.criterion,source=case.source,origin=case.origin,expected_forecast_task_id=receipt.task_id)
    with pytest.raises(ValueError,match='typed'):
        validate_native_forecast_gate(context,port(result,'forecast',kind=WorkerInputKind.EXTERNAL),design=case.design,
            criterion=case.criterion,source=case.source,origin=case.origin,expected_forecast_task_id=receipt.task_id,protected=True)


def test_causal_projection_refuses_incomplete_window_without_future_or_rng(case,monkeypatch):
    monkeypatch.setattr(np.random,'default_rng',lambda *a,**k:pytest.fail('feature projection drew a stream'))
    monkeypatch.setattr('empirical_lawhood.adapters.simulators.six_matrix_response.factor_response.native_factor_response_branch',lambda *a,**k:pytest.fail('feature projection entered future'))
    result=causal_input_from_origin(case.design,case.roles,case.source,case.origin,case.past,record_id='fixture.projected')
    assert result.disposition=='REFUSED' and not result.values  # origin0 has no trailing interval
    assert result.source==response_identity(case.source) and result.origin==response_identity(case.origin)


def test_causal_projection_complete_window_is_available_and_future_free(case,monkeypatch):
    source=case.source
    d=replace(source.design,origin_tick=48,rule=replace(source.design.rule,lattice=(0,16,32,48,64),risk_start_tick=48))
    source=replace(source,design=d)
    past={name:np.repeat(case.past[name][:1],49,axis=0) for name in ('positions','momenta')}
    # Explicit supplied fixture prefix: no simulator or stream is entered.
    past.update({name:case.past[name].copy() for name in ('frame','forces','receivers')})
    origin=numerical_origin(source,past,artifact_id='fixture.joint.complete-prefix')
    projected=bind_numerical_identities(monkeypatch,source,origin)
    monkeypatch.setattr(__name__ + ".response_identity",projected)
    monkeypatch.setattr(np.random,'default_rng',lambda *a,**k:pytest.fail('feature projection drew a stream'))
    monkeypatch.setattr('empirical_lawhood.adapters.simulators.six_matrix_response.factor_response.native_factor_response_branch',lambda *a,**k:pytest.fail('feature projection entered future'))
    first=causal_input_from_origin(case.design,case.roles,source,origin,past,record_id='fixture.available')
    assert first.disposition=='AVAILABLE' and dict(first.values)['trailing-angle'] >= 0
