# SPDX-License-Identifier: MPL-2.0
"""Real complete custody and recovery, with expressly exposed numerical callbacks."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import zlib

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response import active_relaxation_translation as graph
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import ActiveRelaxationSettings, MODEL_NAMES, prepare_matched_relaxation_plan
from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.capabilities import CapabilityConfigRef
from empirical_lawhood.execution.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.execution.native_subwork import NativeSubworkState, NativeSubworkObservationPublicationError
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.execution.local.native_subwork_inputs import validate_native_subwork_inputs
from empirical_lawhood.execution.local.execution import prepare_worker_invocation

from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.runtime_platform.test_worker_preflight import _original_task
from tests.rubisco_active_fixture import prepared_control
from tests.test_rubisco_periodic_probe_operation import engine, THREADS


@pytest.fixture(scope='module')
def matched(tmp_path_factory, request):
    directory=tmp_path_factory.mktemp('exposed-active-matched')
    stock=replace(engine(directory/'stock'), numerical_threads=getattr(request, 'param', 1))
    models=tuple(prepared_control(name,stock) for name in MODEL_NAMES)
    plan=prepare_matched_relaxation_plan(models=tuple((m.material,p,s) for m,s,p,*_ in models),
        settings=ActiveRelaxationSettings('settings.exposed.matched-active'))
    return plan,models


@pytest.fixture
def fixture(tmp_path,monkeypatch,matched):
    plan,models=matched
    model,prototype,prepared,raw_top,raw_xyz,coordinates=models[0]
    for name in THREADS:monkeypatch.setenv(name,str(prototype.engine.numerical_threads))
    package=(('src/exposed_active_relaxation.py','4'*64),)
    digest=sha256(canonical_json_bytes(package)).hexdigest()
    implementation=RecursiveImplementationBinding(package,digest,'5'*64,'3'*40,False)
    provenance=NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        '5'*64,package,digest,'3'*40,False)
    sources=owner.prepare_raw_sources(prototype,raw_top,raw_xyz)
    config=owner.ActiveRelaxationConfig('config.exposed.active',plan,MODEL_NAMES[0],prototype,prepared.identity,
        prepared.canonical_size_bytes(),prepared.seeds,model.canonical_size_bytes(),sources.identity,sources.canonical_size_bytes(),
        implementation,str(tmp_path/'working'),provenance)
    result=SimpleNamespace(plan=plan,models=models,model=model,prototype=prototype,prepared=prepared,
        raw_top=raw_top,raw_xyz=raw_xyz,coordinates=coordinates,sources=sources,config=config,tmp_path=tmp_path,contexts=[])
    yield result
    for context in result.contexts:
        for port in context.input_ports:port.close()


def custody(fixture):
    conditional=owner.conditional_configuration(fixture.config)
    capability=owner.capability_for(fixture.config)
    result_kind=owner.ConditionalActiveRelaxationResult if conditional else owner.ActiveRelaxationResult
    plane=_plane(fixture.tmp_path/'custody')
    records=(('config',fixture.config.identity,fixture.config),
        *owner.native_input_records(fixture.config,fixture.model,fixture.prepared,fixture.sources))
    manifests=[]
    for name,pin,record in records:
        written=plane.write(ArtifactWriteRequest(pin.object_id,'inputs/'+name+'.json',record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,'application/json','inputs.exposed.active','inputs',record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(resolve_artifact_sidecar_bytes(plane, plane.root.resolve(written.materialization.relative_path + '.manifest.json', for_write=False).read_bytes()))
    manifests=tuple(sorted(manifests,key=lambda m:m.materialization.materialization_id))
    verified=tuple(sorted((VerifiedArtifactInput(m.logical,m.materialization) for m in manifests),key=lambda r:r.artifact_id))
    bindings=tuple(WorkerInputBinding.from_verified(row,kind=WorkerInputKind.EXTERNAL) for row in verified)
    by_id={m.logical.logical_artifact_id:m for m in manifests}
    def ports():
        return tuple(plane.open(by_id[b.artifact_id],binding=b,maximum_bytes=b.size_bytes) for b in bindings)
    manifest=owner.operation_declaration(conditional=conditional, accelerated=fixture.config.ACCELERATED).manifest()
    context=TaskContext('exposed.active',capability,'exposed.active.'+capability+'.attempt-001',
        CapabilityConfigRef(fixture.config.config_id,fixture.config.SCHEMA,manifest.config_schema_sha256,
            fixture.config.fingerprint(),fixture.config.identity.object_id),bindings,ports(),
        (WorkerOutputPort(capability+'.product',result_kind.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,'application/json','logical.exposed.active-product'),),
        manifest.permissions,OutcomeAccess.DEVELOPMENT_VISIBLE,owner.resource_budget(fixture.config),WorkerIsolationProfile.TRUSTED_LOCAL,
        accelerated_compute=fixture.config.ACCELERATED)
    runner=owner.ActiveRelaxationRunner(conditional=conditional, accelerated=fixture.config.ACCELERATED)
    task=_original_task(runner,context,SimpleNamespace(verified_inputs=verified))
    plan=ObjectIdentity('plan.exposed.active','empirical-lawhood/runtime/development-execution-plan','1.0.0','1'*64)
    contract=prepare_worker_invocation(runner,context,verified,implementation=fixture.config.implementation,
        execution_plan=plan,execution_task=ObjectIdentity.from_record(task.task_id,task),execution_task_record=task,
        native_effect=True,native_work_preparer=owner.prepare_native_work)
    assert contract.native_preparation_error is None
    context=replace(context,prepared_invocation=contract);fixture.contexts.append(context)
    store=_store(plane,contract.expected_parent_contact,manifests,prepared_invocation=contract)
    store.parent_contacts.begin(contract.expected_parent_contact)
    def fresh():
        value=replace(context,input_ports=ports());fixture.contexts.append(value);return value
    return SimpleNamespace(plane=plane,context=context,work=contract.native_work,store=store,manifests=manifests,fresh=fresh)


def test_all_four_materials_and_96_original_states_are_joined_before_native(fixture):
    c=custody(fixture)
    assert owner._decode(c.context)==(fixture.config,fixture.model,fixture.prepared,fixture.sources)
    assert len(c.work.definitions)==96 and len(c.work.rosters)==1
    for definition in (c.work.definitions[0], c.work.definitions[-1]):
        validate_native_subwork_inputs(c.plane,definition,c.manifests,
            visibility=VisibilityCeiling.DEVELOPMENT_ONLY,access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    assert len({d.configuration for d in c.work.definitions})==96
    assert owner.BUDGET.wall_time_seconds is None
    draft=graph.active_relaxation_draft(fixture.config)
    assert draft.development_study.assigned_unit_ids==(owner.UNIT,)
    assert len(draft.development_study.numerical_view_ids)==96
    assert len(draft.external_inputs)==103 and len(draft.operations)==1
    assert len(fixture.plan.members)==4
    for _,_,prepared,*_ in fixture.models:
        assert all(a.disposition=='SATISFIED' for a in prepared.assessments)
    with pytest.raises(ValueError,match='complete four'):
        replace(fixture.plan,members=fixture.plan.members[:-1])
    with pytest.raises(ValueError,match='complete.*denominator|drops'):
        replace(fixture.prepared,seeds=fixture.prepared.seeds[:-1],assessments=fixture.prepared.assessments[:-1])


@pytest.mark.parametrize('changed',('source','size','material','missing-port'))
def test_substitution_refuses_before_any_native_entry(fixture,changed):
    if changed=='source':
        with pytest.raises(ValueError,match='original selected Amber'):
            owner.prepare_raw_sources(fixture.prototype,fixture.raw_top+b'\n',fixture.raw_xyz)
    elif changed=='size':
        with pytest.raises(ValueError,match='complete original'):
            owner.native_input_records(replace(fixture.config,representation_size_bytes=1),fixture.model,fixture.prepared,fixture.sources)
    elif changed=='material':
        with pytest.raises(ValueError,match='matched|complete'):
            owner.native_input_records(fixture.config,fixture.models[1][0],fixture.prepared,fixture.sources)
    else:
        c=custody(fixture)
        with pytest.raises(ValueError,match='worker input ports'):
            owner._decode(replace(c.context,input_ports=c.context.input_ports[:-1]))
        assert all(c.store.inspect(d).state is NativeSubworkState.NOT_ENTERED for d in c.work.definitions)


def test_actual_native_wrapper_retains_full_census_failure_endpoint_checks_and_recovery(fixture,monkeypatch):
    import empirical_lawhood.domains.rubisco.rubisco_response as package
    import empirical_lawhood.adapters.rubisco.rubisco_response as native_package
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm as qmmm
    from empirical_lawhood.domains.rubisco.rubisco_response import molecular_quality
    # This fixture tests complete custody/recovery with synthetic coordinates,
    # not molecular admissibility. Expose that additional software substitution;
    # a separate control below exercises the real pre-native quality refusal.
    monkeypatch.setattr(molecular_quality, 'assess_molecular_geometry',
        lambda *args, **kwargs: dict(findings=[], scope='EXPOSED_SOFTWARE_GEOMETRY_STUB'))
    monkeypatch.setattr(molecular_quality, 'bound_geometry_terms',
        lambda *args, **kwargs: 'EXPOSED_SOFTWARE_TOPOLOGY_STUB')
    c=custody(fixture);builds=[];calls=[]
    monkeypatch.setattr(owner,'authenticate_periodic_engine',lambda *a,**k:None)
    for short in ('periodic_mm_remainder','periodic_images','pyscf_periodic_electronic'):
        owner_package = native_package if short == 'pyscf_periodic_electronic' else package
        stub=ModuleType(owner_package.__name__+'.'+short)
        monkeypatch.setitem(sys.modules,stub.__name__,stub);monkeypatch.setattr(owner_package,short,stub,raising=False)
    def build(**kwargs):
        builds.append('EXPOSED_MM_ASSIGNMENT_STUB')
        if len(builds)==1:
            raise RuntimeError('exposed deliberate construction failure')
        (kwargs['output_directory']/'mm-assignment.json').write_text('{"scope":"EXPOSED_SOFTWARE_STUB"}\n')
        return object(),{},dict(scope='EXPOSED_SOFTWARE_STUB')
    class StationaryOperator:
        def __init__(self,**kwargs):
            assert kwargs['settings'].ks_flavour == 'RKS' and kwargs['reuse_converged_density'] is True
            self.observe=kwargs['observe'];self.evaluations=0
            self.remainder_audit=self.embedding_audit=dict(scope='EXPOSED_SOFTWARE_STUB')
        def evaluate(self,coordinates):
            self.evaluations+=1;calls.append('EXPOSED_ZERO_GRADIENT_CALLBACK')
            for event in ('entry','electronic-return','return'):
                self.observe(dict(event=event,evaluation=self.evaluations,physical_atoms=len(coordinates),
                    converged=True,orbital_gradient_norm=0.,energy_hartree=-1.))
            return dict(energy_hartree=-1.,gradient_hartree_per_bohr=np.zeros_like(coordinates),
                gradient_unit=native.GRADIENT_UNIT,bohr_angstrom=.52917721092,
                hartree_kj_mol=COULOMB_KJ_NM_PER_MOL_E2/(.52917721092/10))
    monkeypatch.setattr(qmmm,'build_periodic_amber_system',build)
    monkeypatch.setattr(qmmm,'PeriodicCoupledOperator',StationaryOperator)
    runner=owner.ActiveRelaxationRunner()
    first=runner.execute_with_native_subwork(c.context,c.store)
    result=decode_canonical_bytes(first.outputs[0].payload,owner.ActiveRelaxationResult,maximum_bytes=64*2**20)
    assert len(builds)==96 and len(calls)==190
    assert len(result.units)==96
    assert sum(u.completion.operational_status is OperationalStatus.FAILED for u in result.units)==1
    for unit in result.units:
        observed=c.store.recover(unit.definition)
        assert observed.call_entry is not None and observed.call_return is not None
        assert unit.completion.cost.retained_bytes==sum(m.materialization.size_bytes for m in observed.outputs)
    def refuse(**kwargs):pytest.fail('original relaxation was replayed')
    monkeypatch.setattr(native,'execute_active_relaxation',refuse)
    second=runner.execute_with_native_subwork(c.fresh(),c.store)
    assert first.outputs[0].payload==second.outputs[0].payload
    report=retained.read_relaxation(config=fixture.config,representation=fixture.model,prepared=fixture.prepared,
        coordinate_bytes=fixture.coordinates,original_result=result,native_subwork=c.store,
        assessor_source=fixture.model.material.sources[0],readout_id='readout.exposed.active')
    assert len(report.endpoints)==96 and sum(r.native_error is not None for r in report.endpoints)==1
    assert all(r.assessment is not None for r in report.endpoints[1:])
    assert all(r.assessment.complete_reference_evaluations==2 for r in report.endpoints[1:])
    assert all(r.assessment.equilibrium_population==r.assessment.chemical_state_admission=='UNEVALUABLE' for r in report.endpoints[1:])
    assert decode_canonical_bytes(report.canonical_bytes(),retained.ActiveRelaxationReadout,maximum_bytes=64*2**20)==report
    with pytest.raises(ValueError,match='all four'):
        retained.assess_matched_readouts(plan=fixture.plan,readouts=(report,))
    relabeled=tuple(replace(report,original_result=replace(result,model_name=name)) for name in MODEL_NAMES)
    with pytest.raises(ValueError,match='shared original plan'):
        retained.assess_matched_readouts(plan=fixture.plan,readouts=relabeled)
    original=c.store.iter_completed_output
    def corrupt(definition,key,**kwargs):
        return iter((b'CORRUPT ORIGINAL ARCHIVE',)) if key=='files.raw' else original(definition,key,**kwargs)
    monkeypatch.setattr(c.store,'iter_completed_output',corrupt)
    with pytest.raises((ValueError,zlib.error)):
        retained.read_relaxation(config=fixture.config,representation=fixture.model,prepared=fixture.prepared,
            coordinate_bytes=fixture.coordinates,original_result=result,native_subwork=c.store,
            assessor_source=fixture.model.material.sources[0],readout_id='readout.exposed.corrupt')
    assert len(calls)==190


def test_invalid_complete_geometry_refuses_before_native_operator_construction(fixture,monkeypatch):
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm as qmmm
    from empirical_lawhood.domains.rubisco.rubisco_response import molecular_quality
    import json
    def refuse(**kwargs):
        pytest.fail('invalid whole-molecule geometry reached native construction')
    monkeypatch.setattr(qmmm, 'build_periodic_amber_system', refuse)
    monkeypatch.setattr(qmmm, 'PeriodicCoupledOperator', refuse)
    # The old fixture explicitly has no physical force assignment. Inject a
    # disclosed impossible 100-A source bond to test the real geometry gate;
    # raw topology binding/conversion is checked independently by small controls.
    terms = molecular_quality.GeometryTerms(tuple(a.atomic_number for a in fixture.model.atoms),
        ((0, 1, 100., 100.),), (), ())
    monkeypatch.setattr(molecular_quality, 'bound_geometry_terms', lambda *a: terms)
    site = fixture.prepared.sites[0]
    seed = next(s for s in fixture.prepared.seeds if s.site == site.identity)
    root = fixture.tmp_path/'native-invalid-geometry'; root.mkdir()
    topology = fixture.tmp_path/'original.prmtop'; topology.write_bytes(fixture.raw_top)
    with pytest.raises(native.InvalidRelaxationGeometry, match='initial whole-molecule quality refused'):
        native.execute_active_relaxation(representation=fixture.model, site=site,
            protocol=fixture.prepared.protocol, seed=seed, prototype=fixture.prototype,
            settings=fixture.plan.settings, coordinate_bytes=fixture.coordinates,
            topology_path=topology, directory=root)
    quality = json.loads((root/'initial-whole-molecule-quality.json').read_text())
    assert quality['disposition'] == 'REJECTED' and quality['findings']
    assert (root/'original.prmtop').read_bytes() == fixture.raw_top
    assert not (root/'native-observations.jsonl').exists()


@pytest.mark.parametrize('entered',(False,True))
def test_unknown_or_unacknowledged_attempt_cannot_be_repeated(fixture,monkeypatch,entered):
    c=custody(fixture);calls=[]
    monkeypatch.setattr(owner,'authenticate_periodic_engine',lambda *a,**k:None)
    def execute(**kwargs):calls.append('EXPOSED_CALL');return {}
    monkeypatch.setattr(native,'execute_active_relaxation',execute)
    if entered:
        def refuse(*a,**k):raise OSError('exposed observation-publication failure')
        monkeypatch.setattr(c.store,'call_return',refuse)
        expected=NativeSubworkObservationPublicationError
    else:
        c.store.freeze_roster(c.work.rosters[0],definitions=c.work.definitions)
        entry=c.store.begin(c.work.definitions[0]);c.store.contact(entry)
        expected=ValueError
    with pytest.raises(expected):owner.ActiveRelaxationRunner().execute_with_native_subwork(c.context,c.store)
    assert len(calls)==int(entered)
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION
    assert all(c.store.inspect(d).state is NativeSubworkState.NOT_ENTERED for d in c.work.definitions[1:])


def test_public_preparation_read_never_reconstructs_and_authenticates_original_bytes(fixture,monkeypatch):
    from empirical_lawhood.api.domain_composition.rubisco_response import active_models as public
    plane=_plane(fixture.tmp_path/'prepared-custody')
    result=public.prepare_active_model(representation=fixture.model,prototype=fixture.prototype,
        coordinate_bytes=fixture.coordinates,protocol=fixture.prepared.protocol,
        output_relative_path='prepared/model.json',artifact_writer=plane)
    def refuse(*a,**k):pytest.fail('retained preparation reconstructed coordinates or a partition')
    monkeypatch.setattr(public,'prepare_catalytic_sites',refuse)
    monkeypatch.setattr(public,'materialize_catalytic_states',refuse)
    observed=public.read_active_model(representation=fixture.model,prototype=fixture.prototype,
        coordinate_bytes=fixture.coordinates,relative_path='prepared/model.json',artifact_writer=plane)
    assert observed==result['preparation'] and len(observed.seeds)==96
    changed=bytearray(fixture.coordinates);changed[-1]^=1
    with pytest.raises(ValueError,match='coordinate array'):
        public.read_active_model(representation=fixture.model,prototype=fixture.prototype,
            coordinate_bytes=bytes(changed),relative_path='prepared/model.json',artifact_writer=plane)


def test_public_author_freezes_all_exact_complete_inputs_without_entering_native(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import active_relaxation as public
    plane=_plane(fixture.tmp_path/'public-custody')
    project=fixture.tmp_path/'project';project.mkdir()
    output=Path(plane.root.contract.canonical_path)/'authored'
    calls=[]
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda root:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **k:fixture.config.provenance)
    def author(**kwargs):
        calls.append(kwargs)
        assert len(kwargs['input_bindings'])==len(kwargs['draft'].external_inputs)==103
        for key,path in kwargs['input_bindings']:
            selected=next(r for r in kwargs['draft'].external_inputs if r.input_id==key)
            manifest=resolve_artifact_sidecar_bytes(plane, path.with_name(path.name + '.manifest.json').read_bytes())
            plane.verify_manifest(manifest)
            assert path.stat().st_size==selected.maximum_size_bytes
            assert sha256(path.read_bytes()).hexdigest()==selected.expected_content_sha256==manifest.logical.content_sha256
        return {'authored_directory':str(output),'scope':'EXPOSED_FINAL_AUTHOR_STUB'}
    monkeypatch.setattr(recursive_authoring,'author_recursive_wave',author)
    result=public.author_active_relaxation(plan=fixture.plan,model_name=fixture.config.model_name,
        prepared=fixture.prepared,prototype=fixture.prototype,representation=fixture.model,
        raw_topology=fixture.raw_top,raw_coordinates=fixture.raw_xyz,project_root=project,
        work_directory=Path(fixture.config.work_directory),artifact_writer=plane,output_dir=output)
    assert len(calls)==1 and len(result['native_input_paths'])==103
    assert not output.exists() and not Path(fixture.config.work_directory).exists()


def compile_selected(fixture,draft=None):
    from empirical_lawhood.execution.capabilities import CapabilityRegistry
    from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
    declaration=owner.operation_declaration(conditional=owner.conditional_configuration(fixture.config))
    return compile_recursive_wave(draft=draft or graph.active_relaxation_draft(fixture.config),
        registrations=(declaration.registration(),),
        registry=CapabilityRegistry('registry.exposed.active-relaxation',(declaration.manifest(),)),
        implementation_commit=fixture.config.implementation.observed_git_head,output_codecs=declaration.record_codecs)


def test_shared_compiler_closes_the_complete_relaxation_question(fixture):
    compiled=compile_selected(fixture)
    assert compiled.proof is not None and compiled.run_plan is not None
    assert len(compiled.execution_plan.tasks)==1
    task=compiled.execution_plan.tasks[0]
    assert task.maximum_attempts==1 and task.capability.requested_resources==owner.BUDGET
    assert task.outputs[0].payload_schema==owner.ActiveRelaxationResult.SCHEMA
    assert not Path(fixture.config.work_directory).exists()


@pytest.mark.parametrize('change',('missing-seed','source-fingerprint','unit-census','question','budget'))
def test_shared_compiler_refuses_changed_complete_scientific_scope(fixture,change):
    draft=graph.active_relaxation_draft(fixture.config)
    if change=='missing-seed':
        key='external.active-relaxation.native-seed.095'
        draft=replace(draft,external_inputs=tuple(r for r in draft.external_inputs if r.input_id!=key),
            links=tuple(r for r in draft.links if r.external_input_id!=key))
    elif change=='source-fingerprint':
        draft=replace(draft,external_inputs=tuple(replace(r,expected_content_sha256='0'*64)
            if r.input_id=='external.active-relaxation.native-source' else r for r in draft.external_inputs))
    elif change=='unit-census':
        draft=replace(draft,development_study=replace(draft.development_study,assigned_unit_ids=('unit.substitute',)))
    elif change=='question':
        draft=replace(draft,development_study=replace(draft.development_study,question='Does I95M improve turnover?'))
    else:
        draft=replace(draft,operations=(replace(draft.operations[0],resource_budget=replace(owner.BUDGET,cpu_cores=9)),))
    with pytest.raises(ValueError):compile_selected(fixture,draft)
    assert not Path(fixture.config.work_directory).exists()


def test_independent_geometry_assessor_detects_proton_water_and_stereo_departures(fixture):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_assessment import endpoint_geometry
    from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import expand_state_coordinates
    site=fixture.prepared.sites[0]
    seed=next(s for s in fixture.prepared.seeds if s.site==site.identity and s.state_label=='reactive-enolate-kcxh-hie'
        and s.water_occupancy=='OCCUPIED')
    original=np.frombuffer(fixture.coordinates,dtype='<f8').reshape(-1,3)
    xyz=expand_state_coordinates(seed,fixture.coordinates)
    protocol=fixture.prepared.protocol
    selected=next(g for g in protocol.graphs if g.identity==seed.graph)
    named={a.label:i for a,i in zip(selected.atoms,site.core_atom_indices,strict=True) if not a.cap}
    def assess(points):
        return endpoint_geometry(representation=fixture.model,site=site,protocol=protocol,seed=seed,
            original=original,final=points,cell=fixture.prototype.cell,settings=fixture.plan.settings)
    findings,nearest,count=assess(xyz)
    assert 'magnesium-water-state-escaped' not in findings and nearest<2.8 and count==79
    displaced=xyz.copy();displaced[named['ligand.HO3']]+=(20,20,20)
    assert 'proton-allocation-escaped' in assess(displaced)[0]
    displaced=xyz.copy()
    water=site.water_atom_indices[site.water_residue_ids.index(site.coordination_water_residue_id)]
    displaced[list(water)]+=(20,20,20)
    assert 'magnesium-water-state-escaped' in assess(displaced)[0]
    inverted=xyz.copy();c=named['ligand.C4'];o=named['ligand.O4']
    normal=np.cross(xyz[named['ligand.C3']]-xyz[c],xyz[named['ligand.C5']]-xyz[c]);normal/=np.linalg.norm(normal)
    inverted[o]-=2*np.dot(inverted[o]-xyz[c],normal)*normal
    assert 'stereocentre-inverted-or-planar' in assess(inverted)[0]
