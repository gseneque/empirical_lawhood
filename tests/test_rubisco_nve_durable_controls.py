# SPDX-License-Identifier: MPL-2.0
"""Exposed numerical/custody counterexamples, with no molecular entry."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from io import BytesIO
import json
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import directory_census
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import control_contracts as f,nve_contracts as c,nve_roster
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.nve_instrumentation import NVEProgress,retain_checkpoint
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.nve_science import assess_nve,requested_binary64_positions,reduce_return
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_instrumentation import selected_value
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition,NativeSubworkCompletion,NativeSubworkState,NativeSubworkRoster
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import WorkerInputBinding,WorkerInputKind,WorkerInputPort,WorkerOutputPort
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.nve_runner import NVEControlRunner
from tests.test_rubisco_chemical_force_controls import plan as plan,exposed_identity
from tests.test_rubisco_durable_preparation import selected as selected


def full_system(tolerance='0.000001'):
    """Complete exposed serializer-shaped Hamiltonian, never a native supply."""
    return ('<System type="System" version="1">'
        '<PeriodicBoxVectors><A x="2" y="0" z="0"/><B x="0" y="2" z="0"/><C x="0" y="0" z="2"/></PeriodicBoxVectors>'
        '<Particles><Particle mass="1"/><Particle mass="1"/></Particles>'
        '<Constraints><Constraint p1="0" p2="1" d="1"/></Constraints>'
        '<Forces><Force type="NonbondedForce" version="4" forceGroup="0" name="NonbondedForce" method="4" '
        'cutoff="1" useSwitchingFunction="0" switchingDistance="-1" ewaldTolerance="'+tolerance+'" '
        'rfDielectric="78.3" dispersionCorrection="1" exceptionsUsePeriodic="0" includeDirectSpace="1" '
        'alpha="0" nx="0" ny="0" nz="0" ljAlpha="0" ljnx="0" ljny="0" ljnz="0" recipForceGroup="-1">'
        '<GlobalParameters/><ParticleOffsets/><ExceptionOffsets/>'
        '<Particles><Particle q="0.1" sig="0.2" eps="0.3"/><Particle q="-0.1" sig="0.2" eps="0.3"/></Particles>'
        '<Exceptions><Exception p1="0" p2="1" q="-0.01" sig="0.2" eps="0.3"/></Exceptions></Force>'
        '<Force type="HarmonicBondForce" version="2" forceGroup="0" name="HarmonicBondForce" usesPeriodic="0">'
        '<Bonds><Bond p1="0" p2="1" d="1" k="100"/></Bonds></Force></Forces></System>').encode()


def native_text(path,raw):
    return p.NativeTextFile(p.FileEvidence(path,len(raw),sha256(raw).hexdigest()),raw.decode())


def full_state(time='0',steps=0,energy='-1',kinetic='1'):
    return ('<State type="State" version="1" time="'+time+'" stepCount="'+str(steps)+'">'
        '<PeriodicBoxVectors><A x="2" y="0" z="0"/><B x="0" y="2" z="0"/><C x="0" y="0" z="2"/></PeriodicBoxVectors>'
        '<Positions><Position x="0" y="0" z="0"/><Position x="1" y="0" z="0"/></Positions>'
        '<Velocities><Velocity x="0" y="1" z="0"/><Velocity x="0" y="1" z="0"/></Velocities>'
        '<Forces><Force x="1" y="1" z="1"/><Force x="1" y="1" z="1"/></Forces>'
        '<Energies PotentialEnergy="'+energy+'" KineticEnergy="'+kinetic+'"/></State>').encode()


@pytest.fixture
def staged(plan):
    chemical_plan=plan
    key=p.model_roster()[0]
    model=p.ModelAssets('model.exposed.nve',chemical_plan.source,*key,())
    supply=c.RelaxedModelSupply('supply.exposed.relaxed',model,exposed_identity('force-return',f.ChemicalForceReturn),
        exposed_identity('force-assessment',f.ChemicalForceAssessment),
        native_text('old/system.xml',full_system()),
        native_text('old/minimized.xml',full_state()))
    name=f.model_id(key)
    plan=c.NVEControlPlan('config.exposed.nve',chemical_plan,((name,supply.identity,
        exposed_identity('force-definition',NativeSubworkDefinition),exposed_identity('force-completion',NativeSubworkCompletion),
        supply.chemical_return,supply.chemical_assessment),),
        ((*key,'ensemble-01','primary'),),
        p.NATIVE_WORK_ROOT+'/exposed-nve-never-entered',(('src/exposed.py','6'*64),),'7'*64)
    return plan,supply


@pytest.mark.parametrize('field,value',[('full_census',()),('ensembles',()),('integration',()),
    ('numerical_window_picosecond',Decimal('50')),('receiver_cadence_picosecond',Decimal('20')),('selected_cases',())])
def test_fixed_numerical_science_and_full96_are_preserved(staged,field,value):
    plan,_=staged
    with pytest.raises(ValueError):replace(plan,**{field:value})


def test_full97_real_roster_and_full96_unentered_scientific_outcomes(staged,selected):
    plan,_=staged
    sources=(plan.chemical_controls.identity,plan.chemical_controls.source,*(row for parent in plan.admitted_parents for row in parent[1:]))
    rows=nve_roster.definitions(plan,selected.progress.parent_contact,sources=sources,
        input_materialization_ids=selected.progress.parent_contact.input_materialization_ids)
    roster=NativeSubworkRoster('selected.native-subwork',selected.progress.parent_contact,tuple(row.identity for row in rows))
    assert len(roster.subworks)==97
    census=c.NVEControlCensus(plan.identity,tuple((name,NativeSubworkState.NOT_ENTERED) for name in c.unit_ids()))
    assert len(census.states)==96
    result=assess_nve(plan,(),(),current_raw_root='/tmp/exposed-never-entered')
    assert len(result.cases)==96 and len(result.refinements)==48 and result.disposition is A.UNEVALUABLE
    with pytest.raises(ValueError):replace(result,disposition=A.SATISFIED)
    with pytest.raises(ValueError):replace(result,refinements=result.refinements[:-1])


def test_requested_setter_bits_keep_signed_zero_dtype_shape_and_units():
    value=np.array([[0.,-0.,1.]])
    row=dict(unit='nanometer',value=selected_value(value))
    observed=requested_binary64_positions(json.dumps(row).encode())
    np.testing.assert_array_equal(observed.view(np.uint64),value.view(np.uint64))
    row['unit']='angstrom'
    with pytest.raises(ValueError):requested_binary64_positions(json.dumps(row).encode())


@pytest.mark.parametrize('changed',['none','output-prefix','input-bytes'])
def test_real_typed_worker_port_census_is_checked_before_nve_handoff(staged,selected,changed):
    original,_=staged
    source_raw=b'exposed original source bytes'
    source=replace(original.chemical_controls.source,object_fingerprint=sha256(source_raw).hexdigest())
    controls=replace(original.chemical_controls,source=source)
    rows={source.object_id:(source,source_raw),controls.plan_id:(controls.identity,controls.canonical_bytes())}
    parents=[]
    for name,*identities in original.admitted_parents:
        actual=[]
        for identity in identities:
            raw=b'exposed '+identity.object_id.encode()
            current=replace(identity,object_fingerprint=sha256(raw).hexdigest())
            rows[current.object_id]=current,raw
            actual.append(current)
        parents.append((name,*actual))
    plan=replace(original,chemical_controls=controls,admitted_parents=tuple(parents))
    rows[plan.plan_id]=plan.identity,plan.canonical_bytes()
    ports=[]
    for ordinal,(name,(identity,raw)) in enumerate(sorted(rows.items())):
        binding=WorkerInputBinding(name,'exposed.nve.materialized.'+str(ordinal),identity.object_schema,'application/json',len(raw),
            VisibilityCeiling.DEVELOPMENT_ONLY,OutcomeAccess.DEVELOPMENT_VISIBLE,WorkerInputKind.EXTERNAL)
        if changed=='input-bytes' and ordinal==0:raw=raw[::-1]
        ports.append(WorkerInputPort(binding,BytesIO(raw)))
    parent=replace(selected.progress.parent_contact,input_materialization_ids=tuple(sorted(row.materialization_id for row in ports)))
    definitions=nve_roster.definitions(plan,parent,sources=tuple(identity for name,(identity,_) in rows.items() if name!=plan.plan_id),
        input_materialization_ids=parent.input_materialization_ids)
    unit=c.unit_id(plan.selected_cases[0])
    actual_output='exposed.node.'+unit
    output=WorkerOutputPort(actual_output if changed!='output-prefix' else unit,
        'empirical-lawhood/source/capture-assured-uninterpreted-public-bytes',ArtifactProfile.RAW_SOURCE_BYTES,'application/gzip')
    context=SimpleNamespace(task_id=parent.task_id,input_ports=tuple(ports),outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        output_ports=(output,WorkerOutputPort('exposed.node.census',c.NVEControlCensus.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json')))
    environment=tuple(sorted(dict(PYTHONDONTWRITEBYTECODE='1',OPENMM_PLUGIN_DIR='/tmp/exposed-nve-plugins',OPENMM_CPU_THREADS='1',
        OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1').items()))
    runner=NVEControlRunner(plan,'/tmp/exposed-never-entered.json',definitions,environment,((unit,actual_output),),'exposed.node.census')
    if changed=='none':assert runner.validate_context(context,SimpleNamespace(parent_contact=parent))==(unit,)
    else:
        with pytest.raises(ValueError):runner.validate_context(context,SimpleNamespace(parent_contact=parent))


def publish_case(tmp_path,plan,supply,changed,case=None):
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import contracts
    case=plan.selected_cases[0] if case is None else case
    dt,tolerance=next(row[1:] for row in contracts.INTEGRATION if row[0]==case[-1])
    interval_steps=int(Decimal(10)/dt)
    directory=tmp_path/c.unit_id(case)
    directory.mkdir()
    paths={}
    for name,raw in [('system.xml',supply.system.raw_utf8.encode() if case[-1]=='primary' else full_system(str(tolerance))),
        ('integrator.xml',('<Integrator type="VerletIntegrator" version="1" stepSize="'+str(dt)+'" constraintTolerance="'+str(tolerance)+'" integrationForceGroups="-1"/>').encode())]:
        if changed=='step-size' and name=='integrator.xml':raw=raw.replace(b'0.002',b'0.001')
        if name=='system.xml':
            mutations={'particle-mass':(b'<Particle mass="1"/>',b'<Particle mass="2"/>'),
                'force-charge':(b'q="0.1"',b'q="0.2"'),'force-bond':(b'k="100"',b'k="101"'),
                'system-box':(b'<A x="2"',b'<A x="3"'),'extra-system-attribute':(b'<System ',b'<System changed="1" '),
                'ewald-precision':(b'ewaldTolerance="0.000001"',b'ewaldTolerance="0.0000001"'),
                'omitted-force':(b'<Forces>',b'<OmittedForces>')}
            if changed in mutations:raw=raw.replace(*mutations[changed],1)
            if changed=='omitted-force':raw=raw.replace(b'</Forces>',b'</OmittedForces>')
        path=directory/name
        path.write_bytes(raw)
        paths[name]=dict(relative_path=path.relative_to(tmp_path).as_posix(),byte_count=len(raw),sha256=sha256(raw).hexdigest())
    properties=dict(Precision=plan.chemical_controls.platform_precision,DeviceIndex=plan.chemical_controls.device_index,
        DeterministicForces=plan.chemical_controls.deterministic_forces,UseCpuPme=plan.chemical_controls.use_cpu_pme)
    apparatus=dict(system=paths['system.xml'],integrator=paths['integrator.xml'],platform='CUDA',properties=properties,
        force_groups=-1,constraint_tolerance=selected_value(float(tolerance)))
    if changed=='apparatus-platform':apparatus['platform']='CPU'
    if changed=='apparatus-properties':apparatus['properties']={**properties,'Precision':'single'}
    (directory/'apparatus-cuda.json').write_text(json.dumps(apparatus))
    realized=dict(platform='CUDA',actual_properties=properties)
    if changed=='realized-platform':realized['platform']='CPU'
    if changed=='realized-properties':realized['actual_properties']={**properties,'Precision':'single'}
    (directory/'context-realization-000001.json').write_text(json.dumps(realized))
    positions=np.array([[0.,0.,0.],[1.,0.,0.]])
    if changed=='source-point':positions[0,0]=1e-15
    for name,value in [('positions',positions),('box',2*np.eye(3))]:
        (directory/('requested-'+name+'-000001.json')).write_text(json.dumps(dict(unit='nanometer',value=selected_value(value))))
    rows=[]
    controls=[]
    for index in range(11):
        name='initial-full-state' if index==0 else 'nve-state-'+str(index).zfill(2)
        potential=-.996 if changed=='energy' and index==10 else -1.
        kinetic=1.
        if changed=='component-hidden':potential,kinetic=1e16,0. if index==10 else 1.
        if changed=='component-boundary':potential,kinetic=.002 if index==10 else 0.,0.
        if changed=='refinement-zero':potential,kinetic=1e16,0.
        if changed=='refinement-component':potential,kinetic=1e16,.001 if index==10 else 0.
        raw=full_state(str(index*10),index*interval_steps,str(potential),str(kinetic))
        if changed=='state-step' and index==10:raw=raw.replace(b'stepCount="50000"',b'stepCount="49999"')
        if changed=='state-clock' and index==10:raw=raw.replace(b'time="100"',b'time="99"')
        if changed=='missing-velocity' and index==0:raw=raw.replace(b'<Velocities>',b'<OtherVelocities>').replace(b'</Velocities>',b'</OtherVelocities>')
        path=directory/(name+'.xml')
        path.write_bytes(raw)
        checkpoint=directory/('nve-checkpoint-'+str(index).zfill(2)+'.bin')
        checkpoint.write_bytes(b'exposed checkpoint '+str(index).encode())
        def member(path):
            raw=path.read_bytes()
            return dict(relative_path=path.relative_to(tmp_path).as_posix(),byte_count=len(raw),sha256=sha256(raw).hexdigest())
        rows.append(dict(receiver_ordinal=index+1,name=name,steps=index*interval_steps,time_picosecond=str(index*10),
            potential_kj_mol=potential,kinetic_kj_mol=kinetic,total_energy_kj_mol=potential+kinetic,full_state=member(path),checkpoint=member(checkpoint)))
        controls.append(dict(steps=index*interval_steps,time_picosecond=str(index*10),total_energy_kj_mol=potential+kinetic))
    if changed=='missing-progress':rows=rows[:-1]
    (directory/'nve-progress.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    (directory/'numerical-control.json').write_text(json.dumps(dict(atom_count=2,step_size_picosecond=str(dt),receivers=controls,integration_wall_seconds='1')))
    unit_id=c.unit_id(case)
    native=[]
    requests=[('sampling.context',apparatus),
        ('sampling.initialize-thermal-velocities',dict(velocity_seed=17011,temperature_kelvin={'decimal':'298'})),
        ('sampling.verlet-integrator',dict(step_size_picosecond={'decimal':str(dt)})),
        ('sampling.apply-constraint-tolerance',dict(tolerance={'decimal':str(tolerance)})),
        ('sampling.apply-position-constraints',dict(tolerance={'decimal':str(tolerance)})),
        ('sampling.apply-velocity-constraints',dict(tolerance={'decimal':str(tolerance)})),
        *[('sampling.nve-integration',dict(steps=interval_steps,step_size_picosecond={'decimal':str(dt)},physical_time_picosecond=10)) for _ in range(10)]]
    if changed=='seed':requests[1][1]['velocity_seed']=41017
    if changed=='context-system-hash':requests[0]=(requests[0][0],{**apparatus,'system':{**apparatus['system'],'sha256':'1'*64}})
    for ordinal,(role,request) in enumerate(requests):
        native.append(p.NativeCall('exposed.call.'+str(ordinal).zfill(4),None,unit_id,role,json.dumps(request),
            json.dumps(realized) if role=='sampling.context' else '{}',Decimal(0),Decimal(0),'COMPLETED',None,()))
    identities=tuple(ObjectIdentity(row.call_id,NativeSubworkDefinition.SCHEMA,'1.0.0',sha256(row.call_id.encode()).hexdigest()) for row in native)
    returned=c.NVEControlReturn(unit_id,plan.identity,supply.identity,True,2,directory_census(directory,tmp_path).files,identities)
    return returned,tuple(native)


@pytest.mark.parametrize('changed',['none','energy','step-size','source-point','state-step','state-clock','missing-progress','missing-velocity','seed',
    'particle-mass','force-charge','force-bond','system-box','extra-system-attribute','ewald-precision','omitted-force',
    'apparatus-platform','apparatus-properties','realized-platform','realized-properties','context-system-hash'])
def test_actual_full_states_clocks_steps_source_and_denominators_are_independent(staged,tmp_path,changed):
    plan,supply=staged
    returned,native=publish_case(tmp_path,plan,supply,changed)
    if changed not in ('none','energy','missing-velocity','omitted-force'):
        with pytest.raises(ValueError):reduce_return(plan,returned,supply,current_raw_root=tmp_path,native_calls=native)
    else:
        verdict,excursion,reasons,components=reduce_return(plan,returned,supply,current_raw_root=tmp_path,native_calls=native)
        expected=A.SATISFIED if changed=='none' else A.REFUSED if changed=='energy' else A.UNEVALUABLE
        assert verdict is expected and bool(reasons)==(expected is not A.SATISFIED)
        if changed=='none':
            all_outcomes=assess_nve(plan,(returned,),(supply,),current_raw_root=tmp_path,native_calls=((returned.unit_id,native),))
            assert sum(row[1] is A.SATISFIED for row in all_outcomes.cases)==1
            assert all_outcomes.disposition is A.UNEVALUABLE
            with pytest.raises(ValueError):replace(all_outcomes,reported_component_excursions=())


def test_refined_system_changes_only_frozen_ewald_precision():
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.nve_science import join_full_hamiltonian
    admitted=full_system()
    refined=full_system('0.0000001')
    join_full_hamiltonian(refined,admitted,'refined')
    for before,after in ((b'q="0.1"',b'q="0.2"'),(b'<Particle mass="1"/>',b'<Particle mass="2"/>'),
            (b'<A x="2"',b'<A x="3"'),(b'k="100"',b'k="101"')):
        with pytest.raises(ValueError):join_full_hamiltonian(refined.replace(before,after,1),admitted,'refined')


@pytest.mark.parametrize('changed',['component-hidden','component-boundary'])
def test_reported_components_cannot_round_a_precision_miss_to_positive(staged,tmp_path,changed):
    plan,supply=staged
    returned,native=publish_case(tmp_path,plan,supply,changed)
    verdict,old_metric,reasons,supplementary=reduce_return(plan,returned,supply,current_raw_root=tmp_path,native_calls=native)
    assert verdict is A.REFUSED and old_metric<=Decimal('0.001')
    assert supplementary>Fraction(Decimal('0.001'))
    assert 'EXACT_REPORTED_COMPONENT_SUM_PRECISION_FAILED' in reasons
    if changed=='component-hidden':assert old_metric==0 and supplementary==Fraction(1,2)
    assessed=assess_nve(plan,(returned,),(supply,),current_raw_root=tmp_path,native_calls=((returned.unit_id,native),))
    row=next(row for row in assessed.reported_component_excursions if row[0]==returned.unit_id)
    assert row[1:]==supplementary.as_integer_ratio()
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    raw=assessed.canonical_bytes()
    assert decode_canonical_bytes(raw,c.NVEControlAssessment,maximum_bytes=len(raw))==assessed
    assert assessed.VERSION=='1.1.0'
    assert assessed.disposition is A.UNEVALUABLE  # Other95 controls remain unentered.
    forged_cases=tuple((name,A.SATISFIED,value,()) if name==returned.unit_id else (name,status,value,why)
        for name,status,value,why in assessed.cases)
    with pytest.raises(ValueError):replace(assessed,cases=forged_cases)


def test_exact_reported_component_refinement_miss_remains_negative(staged,tmp_path):
    plan,supply=staged
    primary=plan.selected_cases[0]
    refined=(*primary[:-1],'refined')
    plan=replace(plan,selected_cases=(primary,refined))
    left,left_calls=publish_case(tmp_path,plan,supply,'refinement-zero',primary)
    right,right_calls=publish_case(tmp_path,plan,supply,'refinement-component',refined)
    assessed=assess_nve(plan,(left,right),(supply,),current_raw_root=tmp_path,
        native_calls=((left.unit_id,left_calls),(right.unit_id,right_calls)))
    cases={row[0]:row for row in assessed.cases}
    assert cases[left.unit_id][1] is A.SATISFIED and cases[right.unit_id][1] is A.SATISFIED
    assert cases[left.unit_id][2]==cases[right.unit_id][2]==0
    pair_name=left.unit_id.rsplit('.',1)[0]
    pair=next(row for row in assessed.refinements if row[0]==pair_name)
    assert pair[1] is A.REFUSED
    forged_pairs=tuple((name,A.SATISFIED,a,b) if name==pair_name else (name,status,a,b)
        for name,status,a,b in assessed.refinements)
    with pytest.raises(ValueError):replace(assessed,refinements=forged_pairs)


def test_progress_and_checkpoint_bytes_precede_any_further_native_work(tmp_path):
    class Energy(float):
        def value_in_unit(self,unit):return float(self)
        def __add__(self,other):return Energy(float(self)+float(other))
    class Clock:
        unit='picosecond'
        def value_in_unit(self,unit):return 0.
    raw=full_state()
    (tmp_path/'initial-full-state.xml').write_bytes(raw)
    path=tmp_path/'nve-checkpoint-00.bin'
    retained=retain_checkpoint(path,b'exposed original checkpoint')
    assert retained['sha256']==sha256(path.read_bytes()).hexdigest()
    state=SimpleNamespace(getTime=lambda:Clock(),getPotentialEnergy=lambda:Energy(-1.),getKineticEnergy=lambda:Energy(1.))
    progress=NVEProgress(tmp_path,tmp_path,SimpleNamespace(kilojoule_per_mole='exposed unit'))
    progress.record(name='initial-full-state',state=state,steps=0,checkpoint=path)
    assert json.loads((tmp_path/'nve-progress.jsonl').read_text())['receiver_ordinal']==1
    progress.close()
