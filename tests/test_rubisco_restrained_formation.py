# SPDX-License-Identifier: MPL-2.0
"""Analytic harmonic partitions and disclosed original-trace transport controls."""

from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction as F

import numpy as np
import pytest
from types import SimpleNamespace

from empirical_lawhood.domains.rubisco.rubisco_response import restrained_formation as owner
from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_records import EquilibriumReweightingSelection, ReweightingTrace
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_transform import AtomicTransformation
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from tests.test_rubisco_equilibrium_reweighting import criteria, ensemble, contrast, pin
from tests import test_rubisco_periodic_equilibrium_acquisition as acquisition


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    # The historical atom-table control intentionally has no hydrogens.
    # Make a separately identified disclosed C/H/O transport fixture, including
    # its actual topology and natural mass; do not bypass the element checks.
    from tests.rubisco_response_molecular_fixture import raw_identity
    from tests.test_rubisco_preparation_integrity import amber_text
    from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.amber_parameters import read_prmtop
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import read_amber_periodic_cell
    original=acquisition.probe.make_periodic_fixture
    def with_hydrogen():
        model,path,_,settings,top,xyz=original()
        atoms=list(model.atoms)
        index=next(i for i,a in enumerate(atoms) if a.atomic_number==6)
        atoms[index]=replace(atoms[index],atomic_number=1,mass_dalton=D('1.008'))
        sections={k:list(v) for k,v in read_prmtop(top.decode('ascii')).items()}
        sections['ATOMIC_NUMBER'][index]=1
        sections['MASS'][index]=D('1.008')
        top=amber_text(sections).encode('ascii')
        pin=raw_identity('exposed.formation.topology',top)
        old_model=model
        model=replace(model,atoms=tuple(atoms),raw_topology=pin,
            arrays=replace(model.arrays,scientific_references=tuple(sorted((pin,model.raw_coordinates),key=lambda p:p.object_id))),
            sources=tuple(sorted((set(model.sources)-{model.raw_topology})|{pin},key=lambda p:p.object_id)))
        cell=read_amber_periodic_cell(model,top,xyz)
        path=replace(path,representation=model.identity,
            qm_formal_charge=sum(model.atoms[i].atomic_number for i in path.qm_atom_indices)%2,
            sources=tuple(sorted((set(path.sources)-{old_model.identity,*old_model.sources})|{model.identity,*model.sources},key=lambda p:p.object_id)))
        return model,path,cell,settings,top,xyz
    monkeypatch.setattr(acquisition.probe,'make_periodic_fixture',with_hydrogen)
    yield from acquisition.fixture.__wrapped__(tmp_path,monkeypatch)


def rational(value):
    return F(value['numerator'],value['denominator'])


def selected(*, coupled=True):
    case=disclosed_supply().case
    window=UmbrellaWindow('window.formation.exposed','model.exposed','REACTANT',
        (('atom.c','atom.h','atom.o'),),('DISTANCE_DIFFERENCE',),(D(0),),(D(4),),0,1,1,1,D('.1'))
    convention=ReferenceBiasConvention('convention.formation.exposed',ObjectIdentity.from_record(window.window_id,window),
        ('ANGSTROM',),('KJ_PER_MOL_PER_ANGSTROM_SQUARED',),'DISTANCE_12_MINUS_DISTANCE_23',
        'SIGNED_ORDERED_TORSION_SHORTEST_ANGULAR_RESTRAINT','ORTHORHOMBIC_MINIMUM_IMAGE_EACH_CONSECUTIVE_BOND')
    ensembles=tuple(ensemble('ensemble.'+name,window=window,convention=convention) for name in ('mutant','wt'))
    nodes=tuple(owner.RestrainedFormationNode('node.'+str(i),center,('trace.wt.'+str(i),),('trace.mutant.'+str(i),))
        for i,center in enumerate((D(-1),D(0),D(1))))
    traces=tuple(ReweightingTrace('trace.'+arm+'.'+str(i),'ensemble.'+arm,
        pin('config.'+arm+'.'+str(i),acquisition.owner.ReferenceEquilibriumConfig.SCHEMA),
        'group.'+str(i) if coupled else 'group.'+arm+'.'+str(i),8,None)
        for arm in ('mutant','wt') for i in range(3))
    eq=EquilibriumReweightingSelection('selection.formation.equilibrium',ensembles,traces,
        (contrast('contrast.formation',*((e,1 if e.ensemble_id.endswith('mutant') else -1) for e in ensembles)),),
        criteria(),pin('dependence.formation'),('Exposed algebra control only.',))
    mapping=AtomicTransformation('mapping.formation',pin('before.formation'),pin('after.formation'),
        'FINITE_SEQUENCE_SUBSTITUTION',case.identity,(),(),(),(),(),(),(),pin('protocol.formation'),(pin('protocol.formation'),))
    return owner.RestrainedFormationSelection('selection.formation',case,eq,nodes,D(4),pin('protocol.formation'),mapping)


def harmonic_samples(selection,*,noise=None):
    # U_WT=2*x^2/2, U_M=2*(x-0.3)^2/2 (kJ/mol), k=4.
    # Exact restrained Gaussian mean: (2*mu+4*s)/(2+4).
    # The Gaussian normalization is independent of s, so its paired integral
    # between -1 and +1 is -2*4/(2+4)*0.3*2 = -0.8 kJ/mol.
    noise=np.zeros(64) if noise is None else noise
    values={}
    for node in selection.nodes:
        s=float(node.center_angstrom)
        for arm,mu in ((node.wt_trace_ids,0),(node.mutant_trace_ids,.3)):
            values[arm[0]]=(2*mu+4*s)/6+noise
    return values


def statistics(selection,values,**changes):
    return owner.restrained_center_statistics(selection=selection,coordinates=values,
        eligible=changes.get('eligible',{t:True for t in values}))


def test_analytic_gaussian_partition_derivative_and_integral():
    selection=selected()
    report=statistics(selection,harmonic_samples(selection))
    assert rational(report['paired_restrained_free_energy_j_mol'])==pytest.approx(-800,abs=1e-10)
    assert report['paired_mean_forces_j_mol_angstrom']==pytest.approx((-400,)*3,abs=1e-10)
    assert tuple(rational(x) for x in report['quadrature_weights_angstrom'])==(F(1,2),F(1),F(1,2))
    assert report['formation_rate_ratio'] is None and report['activation_free_energy_j_mol'] is None
    assert report['physical_rate_admission']=='UNEVALUABLE'
    assert report['selected_receiver_diagnostics']=='UNEVALUABLE'  # zero-variance disclosed samples
    assert decode_canonical_bytes(selection.canonical_bytes(),type(selection),maximum_bytes=2**20)==selection


def test_coupled_draws_preserve_cancellation_but_independent_groups_do_not():
    rng=np.random.Generator(np.random.PCG64DXSM(1981))
    noise=rng.normal(0,.03,256)
    joint=selected()
    first=statistics(joint,harmonic_samples(joint,noise=noise))
    draws=np.asarray([float(rational(x)) for x in first['bootstrap']['joint_paired_integrals_j_mol']])
    assert np.max(abs(draws+800))<1e-10
    independent=selected(coupled=False)
    other=statistics(independent,harmonic_samples(independent,noise=noise))
    second=np.asarray([float(rational(x)) for x in other['bootstrap']['joint_paired_integrals_j_mol']])
    assert np.std(second)>0.1
    assert first['bootstrap']['interpretation']=='CONDITIONAL_BLOCK_BOOTSTRAP_ESTIMATE_NOT_GUARANTEED_COVERAGE'


def test_selected_receiver_drift_is_assessed_separately_from_inherited_mbar_contrasts():
    selection=replace(selected(),maximum_split_integral_disagreement_j_mol=D('1'))
    values=harmonic_samples(selection)
    for node in selection.nodes:
        values[node.mutant_trace_ids[0]][32:]+=.1
    report=statistics(selection,values)
    assert tuple(float(rational(v)) for v in report['split_half_integrals_j_mol'])==pytest.approx((-800,-1600))
    assert float(rational(report['split_half_disagreement_j_mol']))==pytest.approx(800)
    assert ('paired-integral','RECEIVER_SPLIT_INTEGRAL_DISAGREEMENT') in report['reasons']
    unresolved=statistics(selected(),harmonic_samples(selected()))
    assert ('paired-integral','RECEIVER_SPLIT_TOLERANCE_UNSELECTED') in unresolved['reasons']
    assert unresolved['stationarity_scope']=='FINITE_SPLIT_AND_CORRELATION_DIAGNOSTICS_NOT_PROOF_OF_EQUILIBRIUM'


@pytest.mark.parametrize('mode',('missing','failed-prefix','unaligned-group'))
def test_missing_or_failed_arm_never_shrinks_node_or_draw_denominator(mode):
    selection=selected()
    values=harmonic_samples(selection)
    eligibility={t:True for t in values}
    name=selection.nodes[1].mutant_trace_ids[0]
    if mode=='failed-prefix':
        eligibility[name]=False
    else:
        values[name]=values[name][:(0 if mode=='missing' else 3)]
    report=statistics(selection,values,eligible=eligibility)
    assert len(report['node_ids'])==3
    assert report['bootstrap']['failed_replicates']==32
    assert len(report['bootstrap']['joint_paired_integrals_j_mol'])==32
    assert report['selected_receiver_diagnostics']=='UNEVALUABLE'
    if mode!='unaligned-group':
        assert report['paired_restrained_free_energy_j_mol'] is None


def test_reordered_or_repeated_windows_and_marginal_changes_are_refused():
    selection=selected()
    with pytest.raises(ValueError,match='increasing'):
        replace(selection,nodes=tuple(reversed(selection.nodes)))
    with pytest.raises(ValueError,match='denominator'):
        replace(selection,nodes=selection.nodes[:-1])
    with pytest.raises(ValueError,match='measure'):
        replace(selection,measure='CONSTRAINED_CARTESIAN')
    with pytest.raises(ValueError,match='paired atomic'):
        replace(selection,coordinate_correspondence=replace(selection.coordinate_correspondence,case=pin('wrong.case')))
    with pytest.raises(ValueError,match='full trace census'):
        statistics(selection,{})
    values=harmonic_samples(selection)
    values[next(iter(values))]=np.array([1j])
    with pytest.raises(ValueError,match='finite real'):
        statistics(selection,values)


def original_inputs(fixture,monkeypatch,*,acquire=True):
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import paired_case
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_transform import derive_atomic_transformation
    from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_read import RetainedEquilibriumTrace
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import ReferenceBiasGeometryCriteria
    case=paired_case(case_id='case.formation.no-change',parent=fixture.model.material,mutant=fixture.model.material,
        case_role='NO_CHANGE',exposure_group='exposed.formation',sources=fixture.model.material.sources)
    protocol=fixture.model.preparation_protocol
    transform=derive_atomic_transformation(fixture.model,fixture.model,transformation_id='transform.formation.no-change',
        kind='FINITE_SEQUENCE_SUBSTITUTION',common_atoms=tuple((i,i) for i in range(len(fixture.model.atoms))),
        protocol=protocol,sources=(protocol,),case=case)
    base,raw=acquisition.trajectory(fixture)
    xyz,velocities,_=acquisition.selected.read_equilibrium_phase_space(base.selection,fixture.model,raw)
    chosen=tuple(next(i for i,a in enumerate(fixture.model.atoms) if a.atomic_number==z) for z in (6,1,8))
    xyz[list(chosen)]=((-0.9,0,0),(0,0,0),(1.1,.2,0))
    atoms=tuple(fixture.model.atoms[i].atom_id for i in chosen)
    ensembles,traces,sources,nodes=[],[],[],[]
    observed=acquisition.stub_native(fixture,monkeypatch) if acquire else []
    for arm in ('mutant','wt'):
        for index,center in enumerate((D(-1),D(1))):
            name=arm+'.'+str(index)
            window=UmbrellaWindow('window.formation.'+name,fixture.model.representation_id,'REACTANT',
                (atoms,),('DISTANCE_DIFFERENCE',),(center,),(D(4),),3,8,2,91,D('.01'))
            convention=ReferenceBiasConvention('convention.formation.'+name,ObjectIdentity.from_record(window.window_id,window),
                ('ANGSTROM',),('KJ_PER_MOL_PER_ANGSTROM_SQUARED',),'DISTANCE_12_MINUS_DISTANCE_23',
                'SIGNED_ORDERED_TORSION_SHORTEST_ANGULAR_RESTRAINT','ORTHORHOMBIC_MINIMUM_IMAGE_EACH_CONSECUTIVE_BOND')
            settings=replace(base.selection.settings,settings_id='settings.formation.'+name,random_seed=91823+index,
                bias_window=convention.window,bias_convention=convention.identity)
            phase_selection,phase=acquisition.selected.prepare_reference_equilibrium(prototype=fixture.selection,
                representation=fixture.model,phase_source=fixture.model.raw_coordinates,initial_angstrom=xyz,
                initial_velocity_nm_per_ps=velocities,settings=settings,criteria=base.selection.criteria,
                density_guess_policy='COLD',window=window,convention=convention)
            config=replace(base,config_id='config.formation.'+name,selection=phase_selection)
            limits=ReferenceBiasGeometryCriteria('criteria.formation.'+name,convention.identity,D('1e-5'),
                (D('1e-10'),),(D('1e-7'),),(D('1e-7'),),D('1e-9'),D('1e-6'),D('1e-6'))
            traces.append(ReweightingTrace('trace.'+name,'ensemble.'+arm,config.identity,'group.'+str(index),1,limits))
            if index==0:
                ensembles.append(ensemble('ensemble.'+arm,window=window,convention=convention,prototype=fixture.selection.identity))
            original=store=None
            if acquire:
                root=fixture.tmp_path/name
                root.mkdir()
                local=SimpleNamespace(**vars(fixture))
                local.tmp_path=root
                custody=acquisition.custody(local,config,phase)
                returned=acquisition.owner.operation_declaration().runner_factory().execute_with_native_subwork(custody.context,custody.store)
                original=decode_canonical_bytes(returned.outputs[0].payload,acquisition.owner.ReferenceEquilibriumResult,
                    maximum_bytes=acquisition.owner.MAX_RETURN)
                store=custody.store
            sources.append(RetainedEquilibriumTrace('trace.'+name,config,fixture.model,phase,original,store))
    nodes=tuple(owner.RestrainedFormationNode('node.'+str(i),center,('trace.wt.'+str(i),),('trace.mutant.'+str(i),))
        for i,center in enumerate((D(-1),D(1))))
    eq=EquilibriumReweightingSelection('selection.formation.originals',tuple(ensembles),tuple(traces),
        (contrast('contrast.formation.originals',*((e,1 if e.ensemble_id.endswith('mutant') else -1) for e in ensembles)),),
        criteria(),protocol,('Disclosed small-system no-change control; two shared-stream groups.',))
    selection=owner.RestrainedFormationSelection('selection.formation.originals',case,eq,nodes,D(4),protocol,transform)
    return selection,tuple(sources),observed


def test_original_custody_export_and_independent_no_change_read(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import restrained_formation as public
    from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
    from tests.test_recursive_public_service import _plane
    selection,sources,observed=original_inputs(fixture,monkeypatch)
    before=len(observed)
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda _:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    plane=_plane(fixture.tmp_path/'formation-analysis')
    result=public.export_restrained_formation(selection=selection,sources=sources,project_root=fixture.tmp_path,
        artifact_writer=plane,output_relative_path='analysis/formation')
    read=public.read_restrained_formation_export(directory_relative_path='analysis/formation',sources=sources,artifact_writer=plane)
    assert read['report']==result['report']
    assert len(observed)==before
    report=read['report']
    assert report['equilibrium']['assigned_traces']==report['equilibrium']['complete_window_traces']==4
    assert rational(report['formation']['paired_restrained_free_energy_j_mol'])==0
    assert report['formation']['formation_rate_ratio'] is None
    assert report['new_native_calls']==0
    target=plane.root.resolve('analysis/formation/arrays.npz',for_write=False)
    target.write_bytes(target.read_bytes()+b'changed')
    with pytest.raises((ArtifactIdentityConflict,ValueError)):
        public.read_restrained_formation_export(directory_relative_path='analysis/formation',sources=sources,artifact_writer=plane)


def test_preentry_matching_and_absent_originals_retain_both_arms(fixture,monkeypatch):
    selection,sources,_=original_inputs(fixture,monkeypatch,acquire=False)
    owner.validate_restrained_formation_inputs(selection,sources)
    report,_=owner.read_restrained_formation(selection=selection,sources=sources,assessor_source=fixture.config.provenance.identity)
    assert report['equilibrium']['assigned_traces']==4 and report['equilibrium']['supplied_results']==0
    assert report['formation']['paired_restrained_free_energy_j_mol'] is None
    assert report['formation']['bootstrap']['failed_replicates']==32
    with pytest.raises(ValueError,match='stiffness or selected center'):
        owner.validate_restrained_formation_inputs(replace(selection,force_constant_kj_mol_angstrom2=D(5)),sources)
    changed=replace(selection.coordinate_correspondence,changed_parameter_pairs=((0,0),))
    with pytest.raises(ValueError,match='independent finite-change census'):
        owner.validate_restrained_formation_inputs(replace(selection,coordinate_correspondence=changed),sources)
