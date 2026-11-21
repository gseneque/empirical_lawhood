"""Real custody of exposed literal arrays, with numerical engines stubbed."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes
from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import zlib

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_operation as owner
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_selection as selected
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_translation as graph
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_native as native
from empirical_lawhood.domains.rubisco.rubisco_response import periodic_probe_read as retained
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import PeriodicMMSettings
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
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

from tests.runtime_platform.test_native_subwork import _plane,_store
from tests.runtime_platform.test_worker_preflight import _original_task
from tests.rubisco_periodic_fixture import make_periodic_fixture


THREADS=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS',
         'NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','BLIS_NUM_THREADS','OPENMM_CPU_THREADS')


def test_public_authoring_streams_all_six_complete_direct_inputs(fixture,monkeypatch):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import periodic_probe as public
    plane=_plane(fixture.tmp_path/'public-custody')
    project=fixture.tmp_path/'project';project.mkdir()
    destination=Path(plane.root.contract.canonical_path)/'authored'
    observed=[]
    monkeypatch.setattr(recursive_authoring,'implementation_binding',lambda root:fixture.config.implementation)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',lambda **kwargs:fixture.config.provenance)
    def author(**kwargs):
        observed.append(kwargs)
        assert kwargs['project_root']==project and kwargs['output_dir']==destination
        assert kwargs['artifact_writer'] is plane
        assert len(kwargs['input_bindings'])==len(kwargs['draft'].external_inputs)==6
        for identity,path in kwargs['input_bindings']:
            selected_input=next(row for row in kwargs['draft'].external_inputs if row.input_id==identity)
            raw=path.read_bytes()
            manifest=resolve_artifact_sidecar_bytes(plane, path.with_name(path.name + '.manifest.json').read_bytes())
            plane.verify_manifest(manifest)
            assert len(raw)==manifest.materialization.size_bytes==selected_input.maximum_size_bytes
            assert sha256(raw).hexdigest()==manifest.logical.content_sha256==selected_input.expected_content_sha256
            assert manifest.materialization.physical_sha256==manifest.logical.content_sha256
        config_record=decode_canonical_bytes(kwargs['draft'].operations[0].config_payload.encode(),
            owner.PeriodicProbeConfig,maximum_bytes=owner.MAX_CONFIG)
        assert config_record.representation_size_bytes==fixture.model.canonical_size_bytes()
        model_path=dict(kwargs['input_bindings'])['external.periodic-force.native-model']
        assert model_path.read_bytes()==fixture.model.canonical_bytes()
        return {'scope':'EXPOSED_FINAL_SHARED_AUTHOR_STUB','authored_directory':str(destination)}
    monkeypatch.setattr(recursive_authoring,'author_recursive_wave',author)
    result=public.author_periodic_force_probe(selection=fixture.selection,representation=fixture.model,
        raw_topology=fixture.raw_top,raw_coordinates=fixture.raw_xyz,project_root=project,
        work_directory=fixture.workdir,artifact_writer=plane,output_dir=destination)
    assert len(observed)==1 and len(result['native_input_paths'])==6
    assert result['scope']=='EXPOSED_FINAL_SHARED_AUTHOR_STUB'
    assert not fixture.workdir.exists() and not destination.exists()


@pytest.mark.parametrize('change',('changed-source','occupied-inputs','outside-root'))
def test_public_authoring_refuses_source_and_destination_substitution_before_writes(fixture,monkeypatch,change):
    from empirical_lawhood.api import numerical_provenance, recursive_authoring
    from empirical_lawhood.api.domain_composition.rubisco_response import periodic_probe as public
    plane=_plane(fixture.tmp_path/'public-custody')
    project=fixture.tmp_path/'project';project.mkdir()
    destination=Path(plane.root.contract.canonical_path)/'authored'
    topology=fixture.raw_top
    if change=='changed-source':topology+=b'\n'
    elif change=='occupied-inputs':
        inputs=destination.with_name(destination.name+'-native-inputs');inputs.mkdir()
        (inputs/'original.txt').write_bytes(b'ORIGINAL OUTPUT MUST REMAIN EXACT\n')
    else:destination=fixture.tmp_path/'outside-custody'
    before={p.relative_to(fixture.tmp_path).as_posix():p.read_bytes() for p in fixture.tmp_path.rglob('*') if p.is_file()}
    def refuse(*args,**kwargs):pytest.fail('invalid source/destination reached source capture or shared author')
    monkeypatch.setattr(recursive_authoring,'implementation_binding',refuse)
    monkeypatch.setattr(numerical_provenance,'capture_numerical_provenance',refuse)
    monkeypatch.setattr(recursive_authoring,'author_recursive_wave',refuse)
    with pytest.raises(ValueError):
        public.author_periodic_force_probe(selection=fixture.selection,representation=fixture.model,
            raw_topology=topology,raw_coordinates=fixture.raw_xyz,project_root=project,
            work_directory=fixture.workdir,artifact_writer=plane,output_dir=destination)
    after={p.relative_to(fixture.tmp_path).as_posix():p.read_bytes() for p in fixture.tmp_path.rglob('*') if p.is_file()}
    assert after==before and not fixture.workdir.exists()


def engine(directory):
    for name in selected.NUMERIC_PACKAGES:
        child=directory/name;child.mkdir(parents=True)
        (child/'exposed.txt').write_bytes(b'EXPOSED STOCK CONTROL; NOT AN EXECUTABLE ENGINE\n')
    interpreter=Path(sys.executable).resolve()
    return selected.PeriodicNumericEngine('engine.exposed-periodic',str(directory),
        tuple(FileEvidence(p.relative_to(directory).as_posix(),p.stat().st_size,sha256(p.read_bytes()).hexdigest())
              for p in sorted(directory.rglob('*'),key=str) if p.is_file()),str(interpreter),sha256(interpreter.read_bytes()).hexdigest())


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    for name in THREADS:monkeypatch.setenv(name,'1')
    model,path,cell,electronic,raw_top,raw_xyz=make_periodic_fixture()
    stock=engine(tmp_path/'stock')
    selection=selected.prepare_periodic_probe_selection(representation=model,path=path,cell=cell,electronic=electronic,
        molecular=PeriodicMMSettings('settings.exposed-mm','Ewald',D(9),D('1e-6')),engine=stock)
    sources=owner.prepare_raw_sources(selection,raw_top,raw_xyz)
    package=(('src/exposed_periodic_probe.py','4'*64),)
    digest=sha256(canonical_json_bytes(package)).hexdigest()
    implementation=RecursiveImplementationBinding(package,digest,'5'*64,'3'*40,False)
    provenance=NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        '5'*64,package,digest,'3'*40,False)
    workdir=tmp_path/'working'
    config=owner.PeriodicProbeConfig('config.exposed-periodic',selection,sources.identity,
        model.canonical_size_bytes(),sources.canonical_size_bytes(),implementation,str(workdir),provenance)
    selected_fixture=SimpleNamespace(model=model,selection=selection,sources=sources,config=config,stock=stock,
        raw_top=raw_top,raw_xyz=raw_xyz,workdir=workdir,tmp_path=tmp_path,contexts=[])
    yield selected_fixture
    for context in selected_fixture.contexts:
        for port in context.input_ports:port.close()


def custody(fixture, *, owner=owner, task_id=None, runner_type=None, implementation=None, custody_name='custody', density_bytes=None):
    restart = density_bytes is not None
    accelerated = getattr(fixture.config, 'ACCELERATED', False)
    plane=_plane(fixture.tmp_path/custody_name, **({'binary_codecs':(owner.DENSITY_CODEC,)} if restart else {}))
    task_id = (owner.RESTART_CAPABILITY if restart else owner.CAPABILITY) if task_id is None else task_id
    implementation = fixture.config.implementation if implementation is None else implementation
    records=(('config',fixture.config.identity,fixture.config),*owner.native_input_records(fixture.config,fixture.model,fixture.sources))
    manifests=[]
    payloads = [(name,pin,record.canonical_bytes(),'application/json',ArtifactProfile.CANONICAL_JSON) for name,pin,record in records]
    if restart:
        payloads.append(('native-density',fixture.config.seed.density_bytes,density_bytes,
            'application/octet-stream',ArtifactProfile.RAW_SOURCE_BYTES))
    for name,pin,raw,media,profile in payloads:
        written=plane.write(ArtifactWriteRequest(pin.object_id,'inputs/'+name+('.bin' if profile is ArtifactProfile.RAW_SOURCE_BYTES else '.json'),pin.object_schema,
            profile,media,'inputs.exposed','inputs',raw,
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifest=resolve_artifact_sidecar_bytes(plane, plane.root.resolve(written.materialization.relative_path + '.manifest.json', for_write=False).read_bytes())
        manifests.append(manifest)
    manifests=tuple(sorted(manifests,key=lambda m:m.materialization.materialization_id))
    declaration=owner.operation_declaration(**({'restart':True} if restart else {}),
        **({'accelerated':True} if accelerated else {}))
    verified=tuple(sorted((VerifiedArtifactInput(m.logical,m.materialization) for m in manifests),key=lambda r:r.artifact_id))
    bindings=tuple(WorkerInputBinding.from_verified(row,kind=WorkerInputKind.EXTERNAL) for row in verified)
    by_id={m.logical.logical_artifact_id:m for m in manifests}
    def ports():
        return tuple(plane.open(by_id[b.artifact_id],binding=b,maximum_bytes=b.size_bytes) for b in bindings)
    manifest=declaration.manifest()
    context=TaskContext('exposed.periodic',task_id,'exposed.periodic.'+task_id+'.attempt-001',
        CapabilityConfigRef(fixture.config.config_id,fixture.config.SCHEMA,manifest.config_schema_sha256,
            fixture.config.fingerprint(),fixture.config.identity.object_id),bindings,ports(),
        (WorkerOutputPort(task_id+'.product',owner.PeriodicProbeResult.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,'application/json','logical.exposed.periodic-product'),),
        manifest.permissions,OutcomeAccess.DEVELOPMENT_VISIBLE,
        owner.resource_budget(fixture.config) if accelerated else owner.BUDGET,WorkerIsolationProfile.TRUSTED_LOCAL,
        accelerated_compute=accelerated)
    runner=(owner.PeriodicRestartRunner() if restart else owner.PeriodicProbeRunner()) if runner_type is None else runner_type()
    task=_original_task(runner,context,SimpleNamespace(verified_inputs=verified))
    plan=ObjectIdentity('plan.exposed','empirical-lawhood/runtime/development-execution-plan','1.0.0','1'*64)
    contract=prepare_worker_invocation(runner,context,verified,implementation=implementation,
        execution_plan=plan,execution_task=ObjectIdentity.from_record(task.task_id,task),execution_task_record=task,
        native_effect=True,native_work_preparer=owner.prepare_native_work)
    assert contract.native_preparation_error is None
    context=replace(context,prepared_invocation=contract);fixture.contexts.append(context)
    parent=contract.expected_parent_contact;work=contract.native_work
    store=_store(plane,parent,manifests,prepared_invocation=contract)
    store.parent_contacts.begin(parent)
    def fresh_context():
        fresh=replace(context,input_ports=ports());fixture.contexts.append(fresh);return fresh
    return SimpleNamespace(plane=plane,context=context,parent=parent,work=work,store=store,manifests=manifests,
        fresh_context=fresh_context)


@pytest.mark.parametrize('change',('extra','missing','bytes','link','interpreter','threads'))
def test_complete_stock_and_thread_changes_refuse(fixture,monkeypatch,change):
    selected.authenticate_periodic_engine(fixture.stock)
    path=Path(fixture.stock.site_packages)/selected.NUMERIC_PACKAGES[0]/'exposed.txt'
    if change=='extra':(path.parent/'extra').write_bytes(b'X')
    elif change=='missing':path.unlink()
    elif change=='bytes':path.write_bytes(b'changed')
    elif change=='link':path.unlink();path.symlink_to(Path(fixture.stock.site_packages)/selected.NUMERIC_PACKAGES[1]/'exposed.txt')
    elif change=='interpreter':fixture.stock=replace(fixture.stock,interpreter_sha256='0'*64)
    else:monkeypatch.setenv('OPENMM_CPU_THREADS','2')
    with pytest.raises((ValueError,OSError)):selected.authenticate_periodic_engine(fixture.stock)


def test_complete_real_input_custody_authenticates_request_and_every_source(fixture):
    c=custody(fixture)
    assert owner._decode(c.context)==(fixture.config,fixture.model,fixture.sources)
    assert len(c.work.definitions)==len(c.work.rosters)==1
    definition=c.work.definitions[0]
    validate_native_subwork_inputs(c.plane,definition,c.manifests,
        visibility=VisibilityCeiling.DEVELOPMENT_ONLY,access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    assert definition.configuration==owner.selected_request(fixture.config).identity
    assert definition.outputs==owner.probe_outputs()
    assert len(definition.outputs)==6 and len(c.manifests)==7
    assert owner.BUDGET.wall_time_seconds is None and owner.BUDGET.memory_bytes==8*2**30
    assert owner.MAX_MODEL>83_675_322
    for name,pin,size in graph.input_selections(fixture.config):
        actual=next(record for key,_,record in owner.native_input_records(fixture.config,fixture.model,fixture.sources) if key==name)
        assert pin.object_fingerprint==actual.fingerprint() and size==actual.canonical_size_bytes()
    draft=graph.periodic_probe_draft(fixture.config)
    assert draft.development_study.assigned_unit_ids==(owner.UNIT,)
    assert len(draft.operations)==1 and len(draft.external_inputs)==6


@pytest.mark.parametrize('change',('source-bytes','source-size','model-size','missing-port','duplicate-port','changed-provenance'))
def test_direct_model_and_source_substitution_refuses_before_native(fixture,change):
    if change=='source-bytes':
        with pytest.raises(ValueError,match='original selected Amber bytes'):
            owner.prepare_raw_sources(fixture.selection,fixture.raw_top+b'\n',fixture.raw_xyz)
        return
    c=custody(fixture)
    if change in ('source-size','model-size'):
        config=replace(fixture.config,**{('raw_source_size_bytes' if change=='source-size' else 'representation_size_bytes'):1})
        with pytest.raises(ValueError,match='complete original source bytes'):
            owner.native_input_records(config,fixture.model,fixture.sources)
        return
    changed_context=SimpleNamespace(**{row.name:getattr(c.context,row.name) for row in fields(c.context)})
    if change=='missing-port':changed_context.input_ports=c.context.input_ports[:-1]
    elif change=='duplicate-port':changed_context.input_ports=(*c.context.input_ports[:-1],c.context.input_ports[0])
    else:
        changed_context.input_ports=tuple(SimpleNamespace(**{name:getattr(p,name) for name in
            ('kind','media_type','payload_schema','size_bytes','outcome_access','visibility_ceiling','artifact_id')},
            read=lambda _:replace(fixture.config.provenance,observed_git_head='7'*40).canonical_bytes())
            if p.payload_schema==NumericalProducingProvenance.SCHEMA else p for p in c.context.input_ports)
    with pytest.raises(ValueError):owner._decode(changed_context)
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.NOT_ENTERED


@pytest.mark.parametrize('failed',(False,True))
def test_runner_retains_literal_actual_return_failure_cost_and_never_reenters(fixture,monkeypatch,failed):
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry, retain_exposed_source_coordinates
    install_exposed_geometry(monkeypatch)
    c=custody(fixture);calls=[]
    monkeypatch.setattr(owner,'authenticate_periodic_engine',lambda *a,**k:())
    def invoke(**kwargs):
        calls.append('EXPOSED_LITERAL_CALL')
        retain_exposed_source_coordinates(kwargs)
        (kwargs['directory']/'exposed-observation.txt').write_bytes(b'EXPOSED SOFTWARE ARRAY CONTROL\n')
        if failed:raise RuntimeError('exposed deliberate force failure')
        return dict(energy_hartree=-1.234567890123,gradient_hartree_per_bohr=np.arange(249,dtype=np.float64).reshape((83,3)))
    monkeypatch.setattr(native,'execute_periodic_probe',invoke)
    runner=owner.PeriodicProbeRunner()
    first=runner.execute_with_native_subwork(c.context,c.store)
    result=decode_canonical_bytes(first.outputs[0].payload,owner.PeriodicProbeResult,maximum_bytes=owner.MAX_RETURN)
    assert calls==['EXPOSED_LITERAL_CALL']
    for port in c.context.input_ports:
        with pytest.raises((OSError,ValueError)):port.read(0)
    assert result.request.gradient_unit==owner.GRADIENT_UNIT
    assert result.completion.operational_status is (OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED)
    observed=c.store.recover(c.work.definitions[0])
    assert observed.call_entry is not None and observed.call_return is not None
    assert result.completion.cost.cpu_seconds is not None and result.completion.cost.wall_seconds is not None
    assert result.completion.cost.retained_bytes==D(sum(m.materialization.size_bytes for m in observed.outputs))
    assert result.returned.returned is None if failed else result.returned.returned.gradient.shape==(83,3)
    if failed:assert result.completion.omitted_output_ids==('raw.energy','raw.gradient','raw.return')
    monkeypatch.setattr(native,'execute_periodic_probe',lambda **k:pytest.fail('known completed force was replayed'))
    recovered=runner.execute_with_native_subwork(c.fresh_context(),c.store)
    assert recovered.outputs[0].payload==first.outputs[0].payload
    report=retained.read_periodic_probe(config=fixture.config,representation=fixture.model,
        original_result=result,native_subwork=c.store,assessor_source=fixture.model.material.sources[0],
        readout_id='readout.exposed-periodic')
    assert report.original_result==result and report.authenticated_file_count==len(result.returned.files.files)
    assert report.numerical_integrity is None if failed else report.numerical_integrity.disposition=='SATISFIED'
    assert decode_canonical_bytes(report.canonical_bytes(),retained.PeriodicProbeReadout,maximum_bytes=owner.MAX_RETURN)==report
    with pytest.raises(ValueError):replace(result,returned=replace(result.returned,selection=fixture.stock.identity),
        request=replace(result.request,physical_atom_count=82))


def test_unknown_contact_and_observation_failure_cannot_become_known_completion(fixture,monkeypatch):
    c=custody(fixture)
    monkeypatch.setattr(owner,'authenticate_periodic_engine',lambda *a,**k:())
    monkeypatch.setattr(native,'execute_periodic_probe',lambda **k:pytest.fail('unknown contact reentered'))
    c.store.freeze_roster(c.work.rosters[0],definitions=c.work.definitions)
    entry=c.store.begin(c.work.definitions[0]);c.store.contact(entry)
    with pytest.raises(ValueError,match='contacted without exact receipt; no automatic retry'):
        owner.PeriodicProbeRunner().execute_with_native_subwork(c.context,c.store)
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION


def test_unacknowledged_call_observation_retains_unknown_without_retry(fixture,monkeypatch):
    c=custody(fixture)
    monkeypatch.setattr(owner,'authenticate_periodic_engine',lambda *a,**k:())
    calls=[]
    def invoke(**kwargs):calls.append('EXPOSED_LITERAL_CALL');return {'energy_hartree':0.,'gradient_hartree_per_bohr':np.zeros((83,3))}
    monkeypatch.setattr(native,'execute_periodic_probe',invoke)
    def reject(*a,**k):raise OSError('exposed observation publication failure')
    monkeypatch.setattr(c.store,'call_return',reject)
    with pytest.raises(NativeSubworkObservationPublicationError):
        owner.PeriodicProbeRunner().execute_with_native_subwork(c.context,c.store)
    assert calls==['EXPOSED_LITERAL_CALL']
    assert c.store.inspect(c.work.definitions[0]).state is NativeSubworkState.UNKNOWN_COMPLETION


@pytest.mark.parametrize('bad_values',(False,True))
@pytest.mark.parametrize('seeded',(False,True))
def test_real_entry_complete_flat_file_publication_and_retained_read(fixture,monkeypatch,bad_values,seeded):
    from tests.rubisco_exposed_geometry_fixture import install_exposed_geometry
    install_exposed_geometry(monkeypatch)
    import empirical_lawhood.domains.rubisco.rubisco_response as package
    import empirical_lawhood.adapters.rubisco.rubisco_response as native_package
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm as qmmm
    density_bytes = None
    if seeded:
        from tests.test_rubisco_periodic_restart import restart
        config, density_bytes, _ = restart(fixture)
        fixture.config = config
    c=custody(fixture,density_bytes=density_bytes);calls=[]
    monkeypatch.setattr(owner,'authenticate_periodic_engine',lambda *a,**k:())
    for short in ('periodic_mm_remainder','periodic_images','pyscf_periodic_electronic'):
        owner_package = native_package if short == 'pyscf_periodic_electronic' else package
        name=owner_package.__name__+'.'+short
        stub=ModuleType(name)
        monkeypatch.setitem(sys.modules,name,stub);monkeypatch.setattr(owner_package,short,stub,raising=False)
    def build(**kwargs):
        calls.append('EXPOSED_BUILD')
        assert kwargs['output_directory']==kwargs['topology_path'].parent
        for name in ('mm-settings.json','original-mm-parameters.json','mm-assignment.json'):
            (kwargs['output_directory']/name).write_text('{"scope":"EXPOSED_SOFTWARE_STUB"}\n')
        return object(),{},dict(scope='EXPOSED_SOFTWARE_STUB')
    class LiteralOperator:
        def __init__(self,**kwargs):
            self.observe=kwargs['observe'];self.evaluations=0
            self.remainder_audit=self.embedding_audit=dict(scope='EXPOSED_SOFTWARE_STUB')
        def evaluate(self,coordinates,**kwargs):
            assert kwargs == ({'density_seed':fixture.config.seed, 'density_bytes':density_bytes} if seeded else {})
            calls.append('EXPOSED_LITERAL_ARRAYS');self.evaluations+=1
            n,q,m=len(coordinates),len(fixture.selection.path.qm_atom_indices),len(fixture.selection.path.mm_atom_indices)
            gradient=np.arange(n*3,dtype=np.float64).reshape((n,3))*.01
            if bad_values:gradient[42,1]=np.nan
            self.observe(dict(event='return',scope='EXPOSED_SOFTWARE_STUB'))
            return dict(energy_hartree=-12.345,gradient_hartree_per_bohr=gradient,
                embedding_mm_gradient_hartree_per_bohr=np.zeros((m,3)),image_shifts=np.zeros((m,3),dtype=np.int64),
                qm_link_gradient_hartree_per_bohr=np.zeros((q,3)),remainder_gradient_hartree_per_bohr=np.zeros((n,3)),
                bohr_angstrom=.52917721092,gradient_unit=native.GRADIENT_UNIT,scf_converged=True)
    monkeypatch.setattr(qmmm,'build_periodic_amber_system',build)
    monkeypatch.setattr(qmmm,'PeriodicCoupledOperator',LiteralOperator)
    runner = owner.PeriodicRestartRunner() if seeded else owner.PeriodicProbeRunner()
    output=runner.execute_with_native_subwork(c.context,c.store)
    result=decode_canonical_bytes(output.outputs[0].payload,owner.PeriodicProbeResult,maximum_bytes=owner.MAX_RETURN)
    assert calls==['EXPOSED_BUILD','EXPOSED_LITERAL_ARRAYS']
    assert result.completion.operational_status is OperationalStatus.SUCCEEDED
    names={Path(row.relative_path).name for row in result.returned.files.files}
    assert {'original.prmtop','original.inpcrd','original-mm-parameters.json','mm-assignment.json',
            'coupling-audit.json','native-return-metadata.json','gradient_hartree_per_bohr.npy'}<=names
    if seeded:
        assert {'initial-density-seed.json','initial-density.bin'} <= names
    monkeypatch.setattr(native,'execute_periodic_probe',lambda **k:pytest.fail('retained read entered native code'))
    report=retained.read_periodic_probe(config=fixture.config,representation=fixture.model,
        original_result=result,native_subwork=c.store,assessor_source=fixture.model.material.sources[0],
        readout_id='readout.exposed-periodic-complete')
    assert report.numerical_integrity.disposition==('FALSIFIED' if bad_values else 'SATISFIED')
    assert report.numerical_integrity.operands[1].nonfinite_values==int(bad_values)
    assert report.original_result.completion.operational_status is OperationalStatus.SUCCEEDED
    assert report.remaining_requirement_ids==selected.OPEN_REQUIREMENTS
    assert len(calls)==2
    original_iter=c.store.iter_completed_output
    def substituted(definition,key,**kwargs):
        if key=='files.raw':return iter((b'corrupted original archive',))
        return original_iter(definition,key,**kwargs)
    monkeypatch.setattr(c.store,'iter_completed_output',substituted)
    with pytest.raises(zlib.error,match='incorrect header check'):
        retained.read_periodic_probe(config=fixture.config,representation=fixture.model,
            original_result=result,native_subwork=c.store,assessor_source=fixture.model.material.sources[0],
            readout_id='readout.exposed-corrupt-periodic')
    assert len(calls)==2


@pytest.mark.parametrize('threads',(2,8))
def test_selected_multithreading_is_authenticated_without_single_thread_restriction(fixture,monkeypatch,threads):
    stock=replace(fixture.stock,numerical_threads=threads)
    for name in THREADS:monkeypatch.setenv(name,str(threads))
    selected.authenticate_periodic_engine(stock)
    assert decode_canonical_bytes(stock.canonical_bytes(),selected.PeriodicNumericEngine,maximum_bytes=2**20)==stock
    monkeypatch.setenv('OMP_NUM_THREADS',str(threads+1))
    with pytest.raises(ValueError,match='thread count'):selected.authenticate_periodic_engine(stock)


@pytest.mark.parametrize('threads',(1,2,8))
def test_registered_worker_freezes_all_selected_thread_settings(fixture,monkeypatch,threads):
    from empirical_lawhood.execution.local.execution import _select_worker_environment
    from empirical_lawhood.storage.numerical_provenance import worker_numerical_threads
    declaration=owner.operation_declaration()
    selector=declaration.execution_properties.worker_environment_selector
    assert selector is selected.periodic_worker_environment
    assert declaration.registration().worker_environment_selector is selector
    stock=replace(fixture.stock,numerical_threads=threads)
    for name in THREADS:monkeypatch.setenv(name,str(threads))
    frozen=_select_worker_environment(selector,cpu_cores=owner.BUDGET.cpu_cores)
    assert {dict(frozen)[name] for name in THREADS}=={str(threads)}
    assert worker_numerical_threads(frozen,cpu_cores=owner.BUDGET.cpu_cores)==threads
    for name in THREADS:monkeypatch.delenv(name)
    for name,value in frozen:monkeypatch.setenv(name,value)
    selected.authenticate_periodic_engine(stock)


@pytest.mark.parametrize('threads',(0,-1,True,1.5))
def test_invalid_numerical_thread_selections_refuse(fixture,threads):
    with pytest.raises(ValueError,match='thread selection'):replace(fixture.stock,numerical_threads=threads)


@pytest.mark.parametrize('threads',(8,9))
def test_config_checks_thread_selection_against_actual_cpu_allocation(fixture,threads):
    stock=replace(fixture.stock,numerical_threads=threads)
    selection=selected.prepare_periodic_probe_selection(representation=fixture.model,path=fixture.selection.path,
        cell=fixture.selection.cell,electronic=fixture.selection.electronic,molecular=fixture.selection.molecular,
        engine=stock)
    if threads>owner.BUDGET.cpu_cores:
        with pytest.raises(ValueError,match='CPU allocation'):replace(fixture.config,selection=selection)
    else:
        assert replace(fixture.config,selection=selection).selection.engine.numerical_threads==threads
