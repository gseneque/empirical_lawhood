"""Genuine exposed conditional segment receipts and complete cold assessment."""

from dataclasses import replace
from io import BytesIO
from types import SimpleNamespace
from pathlib import Path
import os
import shutil
import resource
import time

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_array_chunks import FRAMED_ARRAY_SCHEMA, FRAMED_ARRAY_MEDIA
from empirical_lawhood.adapters.methods.matrix_parameter_history import chunked_operation_bindings as binding, chunked_science as science
from empirical_lawhood.adapters.methods.matrix_parameter_history.chunked_records import MatrixParameterChunkedSource, MatrixParameterChunkedHistory, bind_source
from empirical_lawhood.adapters.methods.matrix_parameter_history.chunked_control_records import MatrixParameterChunkedAssessmentReport
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, NativeSubworkUncertainContact
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.test_matrix_parameter_compact_history import selected
from tests.test_matrix_parameter_history import progress_store, provider, publish


def selection():
    sources,a,p = selected()
    return MatrixParameterChunkedSource('source.chunked.'+sources[0].root_id,sources[0],3),a,p


def context(plane,s,a,p,role,*,history=None,raw=None):
    c = a.coordinates[0]
    config = binding.MatrixParameterOperationConfig(f'config.{binding.NAMESPACE}.{s.root_id}.{role}',role,s)
    records = [(config.config_id,config.SCHEMA,config.canonical_bytes()),(s.source_id,s.SCHEMA,s.canonical_bytes()),
        (a.allocation_id,a.SCHEMA,a.canonical_bytes()),(c.coordinate_id,c.SCHEMA,c.canonical_bytes()),
        (p.identity.object_id,p.SCHEMA,p.canonical_bytes())]
    if role == 'history':
        records += [(s.root.stream_identity(stream).object_id,stream.SCHEMA,stream.canonical_bytes()) for stream in s.root.streams]
    else:
        records += [(history.history_id,history.SCHEMA,history.canonical_bytes())]
    manifests = []
    for name,schema,payload in records:
        existing = plane.root.resolve('inputs/'+name,for_write=False)
        sidecar = existing.with_name(existing.name+'.manifest.json')
        if existing.exists() and sidecar.exists():
            assert existing.read_bytes() == payload
            manifest = decode_artifact_manifest(sidecar.read_bytes())
            plane.verify_manifest(manifest)
            manifests.append(manifest)
        else:
            manifests.append(publish(plane,name,schema,payload))
    if raw is not None:
        artifact = history.container
        result = plane.write(ArtifactWriteRequest(artifact.artifact_id,'inputs/'+artifact.artifact_id,artifact.payload_schema,
            ArtifactProfile.RAW_SOURCE_BYTES,artifact.media_type,'test.chunked.exposed','inputs',raw,
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        manifests.append(decode_artifact_manifest(plane.root.resolve(result.manifest_materialization.relative_path,for_write=False).read_bytes()))
    manifests = tuple(manifests)
    ports = tuple(plane.open(m,binding=WorkerInputBinding(m.logical.logical_artifact_id,m.materialization.materialization_id,
        m.logical.payload_schema,m.logical.media_type,m.materialization.size_bytes,VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE,WorkerInputKind.EXTERNAL),maximum_bytes=m.materialization.size_bytes) for m in manifests)
    factory = next(f for f in binding.operation_factories() if f.manifest.capability_key.endswith('.'+role))
    product = MatrixParameterChunkedHistory if role == 'history' else MatrixParameterChunkedAssessmentReport
    outputs = (WorkerOutputPort('chunked.'+role+'.product',product.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json'),)
    if role == 'history':
        outputs += (WorkerOutputPort('chunked.history.arrays',FRAMED_ARRAY_SCHEMA,ArtifactProfile.RAW_SOURCE_BYTES,FRAMED_ARRAY_MEDIA,'chunked.history.container'),)
    else:
        outputs += (WorkerOutputPort('chunked.assess.control-arrays',FRAMED_ARRAY_SCHEMA,ArtifactProfile.RAW_SOURCE_BYTES,FRAMED_ARRAY_MEDIA,'chunked.assess.controls'),)
    ctx = SimpleNamespace(input_ports=ports,output_ports=outputs,config=SimpleNamespace(content_sha256=config.fingerprint()),
        task_id=f'{binding.NAMESPACE}.{s.root_id}.{role}',resource_budget=binding.BUDGET,permissions=factory.manifest.permissions,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return config,ctx,manifests,factory


@pytest.fixture(scope='module')
def completed(tmp_path_factory):
    s,a,p = selection()
    retained = os.environ.get('MATRIX_PARAMETER_CHUNKED_COMPLETED_FIXTURE')
    plane = _plane(Path(retained) if retained else tmp_path_factory.mktemp('chunked-retained')/'original',
        binary_codecs=MATRIX_STORAGE_CODECS)
    config,ctx,manifests,factory = context(plane,s,a,p,'history')
    bound = bind_source(s,a,a.coordinates[0],p)
    if retained:
        path = next(path for path in (Path(retained)/'runs/test.e4.run/native-contacts').glob('*.json') if not path.name.endswith('.manifest.json'))
        parent = decode_canonical_bytes(path.read_bytes(),NativeEffectContact,maximum_bytes=None)
        store = _store(plane,parent,manifests)
        assert store.recover(binding.carrier_definition(ctx,config,bound,store)) is not None
    else:
        store,ctx = progress_store(plane,bound,ctx,manifests,factory=factory,
            native_work_preparer=binding.prepare_native_work)
    result = provider(factory).execute_with_native_subwork(ctx,store,progress=manifests)
    product = next(o for o in result.outputs if hasattr(o,'payload'))
    history = decode_canonical_bytes(product.payload,MatrixParameterChunkedHistory,maximum_bytes=None)
    stream = next(o for o in result.outputs if hasattr(o,'source'))
    raw = b''.join(stream.source.chunks(1024))
    assessment = _assess_framed(bound,history,raw)
    return s,a,p,bound,history,assessment,raw,plane,store


def _assess_framed(bound,history,raw):
    sink = BytesIO()
    result = science.assess_framed(bound,history,BytesIO(raw).read,emit_control=sink.write,control_artifact_id='chunked.assess.controls')
    from empirical_lawhood.adapters.methods.matrix_array_chunks import iter_framed_chunk_arrays
    assert len(tuple(iter_framed_chunk_arrays(result.control_arrays,result.control_container,BytesIO(sink.getvalue()).read))) == len(history.segments)
    return result


def test_actual_compiler_shared_sources_complete_segmented_native_scope():
    s,a,p = selection()
    draft = binding.development_draft((s,),a,p,draft_id='test.chunked.actual')
    factories = binding.operation_factories()
    registry = CapabilityRegistry('registry.chunked',tuple(sorted((f.manifest for f in factories),key=lambda m:m.registry_id)))
    compiled = compile_recursive_wave(draft=draft,registrations=binding.operation_registrations(),registry=registry,
        implementation_commit=p.observed_git_head,output_codecs=binding.output_codecs())
    assert len(compiled.execution_plan.tasks) == 2
    arrays = next(o for t in compiled.execution_plan.tasks for o in t.outputs if o.payload_schema == FRAMED_ARRAY_SCHEMA)
    assert arrays.profile is ArtifactProfile.RAW_SOURCE_BYTES


def test_conditional_native_receipts_every_scientific_row_and_pure_assessor(completed,tmp_path):
    s,a,p,bound,history,assessment,raw,_,_ = completed
    assert len(history.segments) == 3 and len(history.arrays.chunks) == 6
    assert tuple(v.checkpoint.previous is None for v in history.segments) == (True,False,False)
    assert tuple(c.denominator_steps for c in assessment.controls) == (8,16,8,8)
    assert assessment.numerical_pass and assessment.standing.endswith('NO_FUNCTIONAL_NUMERICAL_ADEQUACY')
    assert all(v.completion.unknown_streams == () for v in history.segments)
    plane = _plane(tmp_path/'assessor',binary_codecs=MATRIX_STORAGE_CODECS)
    _,ctx,_,factory = context(plane,s,a,p,'assess',history=history,raw=raw)
    assert not hasattr(provider(factory),'execute_with_native_subwork')
    class Emitter:
        def __init__(self):
            self.outputs = {}
        def write(self,name,payload):
            self.outputs.setdefault(name,BytesIO()).write(payload)
    emitter = Emitter()
    provider(factory).execute_streaming(ctx,emitter)
    assert decode_canonical_bytes(emitter.outputs['chunked.assess.product'].getvalue(),MatrixParameterChunkedAssessmentReport,maximum_bytes=None) == assessment
    assert history.carrier.completion.consumed_streams == ()


def test_relocated_completed_native_container_blocks_producer_rng_reencoding(completed,tmp_path,monkeypatch):
    s,a,p,bound,history,assessment,raw,plane,store = completed
    target = tmp_path/'portable';shutil.copytree(plane.root.contract.canonical_path,target)
    relocated = _plane(target,binary_codecs=MATRIX_STORAGE_CODECS);recovered = _store(relocated,store.parent_contact,store.parent_inputs)
    def blocked(*args,**kwargs):
        pytest.fail('completed source cannot acquire/draw/reencode')
    monkeypatch.setattr(binding,'acquire_parameter_segment',blocked)
    monkeypatch.setattr(parameter_history_segments,'acquire_parameter_segment',blocked)
    original_encoder = science.encode_chunk
    def derived_control_encoder(*args,**kwargs):
        if kwargs.get('artifact_id','').startswith('control-array.'):
            return original_encoder(*args,**kwargs)
        blocked()
    monkeypatch.setattr(science,'encode_chunk',derived_control_encoder)
    monkeypatch.setattr(np.random,'Generator',blocked)
    _,ctx,manifests,factory = context(relocated,s,a,p,'history')
    result = provider(factory).execute_with_native_subwork(ctx,recovered,progress=manifests)
    returned = next(o for o in result.outputs if hasattr(o,'payload'))
    assert decode_canonical_bytes(returned.payload,MatrixParameterChunkedHistory,maximum_bytes=None) == history
    stream = next(o for o in result.outputs if hasattr(o,'source'))
    assert b''.join(stream.source.chunks(333)) == raw
    assert _assess_framed(bound,history,raw) == assessment


@pytest.mark.parametrize('defect',('previous','native-parent','stream-cursor','science-denominator','whole-hash','late-container'))
def test_complete_cold_refuses_substitution(completed,defect):
    _,_,_,bound,history,_,raw,_,_ = completed
    if defect == 'late-container':
        with pytest.raises(ValueError):
            _assess_framed(bound,history,raw[:-1])
        return
    if defect == 'whole-hash':
        bad = replace(history,arrays=replace(history.arrays,members=tuple(replace(m,sha256='f'*64) if m.name == 'primary_momenta' else m for m in history.arrays.members)))
        with pytest.raises(ValueError):
            _assess_framed(bound,bad,raw)
        return
    segment = history.segments[1]
    with pytest.raises(ValueError):
        if defect == 'previous':
            bad = replace(segment,checkpoint=replace(segment.checkpoint,previous=replace(segment.checkpoint.previous,object_fingerprint='f'*64)))
        elif defect == 'native-parent':
            bad = replace(segment,receipt=replace(segment.receipt,run_id='run.wrong'))
        elif defect == 'stream-cursor':
            states = segment.checkpoint.generators
            bad = replace(segment,checkpoint=replace(segment.checkpoint,generators=(replace(states[0],completed_noise_matrices=90),*states[1:])))
        else:
            bad = replace(segment,arrays=replace(segment.arrays,intervals=tuple(replace(i,stop=i.stop-1) if i.name == 'primary_ticks' else i for i in segment.arrays.intervals)))
        bad.validate_source(bound,history.segments[0])


def test_interrupted_segment_retains_completed_prefix_never_repeats(tmp_path,monkeypatch):
    s,a,p = selection();plane = _plane(tmp_path/'interrupted',binary_codecs=MATRIX_STORAGE_CODECS)
    config,ctx,manifests,factory = context(plane,s,a,p,'history')
    bound = bind_source(s,a,a.coordinates[0],p)
    store,ctx = progress_store(plane,bound,ctx,manifests,factory=factory,
        native_work_preparer=binding.prepare_native_work)
    original = binding.acquire_parameter_segment
    class Interrupted(Exception):
        pass
    def interrupted(*args,**kwargs):
        if args[2] == 3:
            raise Interrupted('exposed midcourse interruption')
        return original(*args,**kwargs)
    monkeypatch.setattr(binding,'acquire_parameter_segment',interrupted)
    with pytest.raises(Interrupted):
        provider(factory).execute_with_native_subwork(ctx,store,progress=manifests)
    base = binding.carrier_definition(ctx,config,bound,store)
    assert store.inspect(base).state is NativeSubworkState.UNKNOWN_COMPLETION
    first = binding.segment_definition(base,0,None)
    completed,_ = binding._recover_segment(store,first)
    assert completed.checkpoint.stop == 3
    def blocked(*args,**kwargs):
        pytest.fail('unknown carrier cannot repeat completed or uncertain calls')
    monkeypatch.setattr(binding,'acquire_parameter_segment',blocked)
    _,ctx,manifests,_ = context(plane,s,a,p,'history')
    with pytest.raises(NativeSubworkUncertainContact):
        provider(factory).execute_with_native_subwork(ctx,store,progress=manifests)


def test_complete_over4341_history_has_bounded_native_leaves_and_cold_denominators(tmp_path,monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_parameter_history.compact_records import compact_sources
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
    original,a,p = selected()
    c = replace(a.coordinates[0],autonomous_ticks=4996,observation_ticks=(0,5000))
    root = replace(a.roots[0],coordinate=coordinate_identity(c))
    a = replace(a,coordinates=(c,),roots=(root,))
    compact = compact_sources(a,p,original[0].numerical_design,namespace='source.long')[0]
    s = MatrixParameterChunkedSource('source.chunked.long',compact,256)
    bound = bind_source(s,a,c,p)
    retained = os.environ.get('MATRIX_PARAMETER_CHUNKED_LONG_COMPLETED_FIXTURE')
    plane = _plane(Path(retained) if retained else tmp_path/'original',binary_codecs=MATRIX_STORAGE_CODECS)
    config,ctx,manifests,factory = context(plane,s,a,p,'history')
    if retained:
        path = next(path for path in (Path(retained)/'runs/test.e4.run/native-contacts').glob('*.json') if not path.name.endswith('.manifest.json'))
        parent = decode_canonical_bytes(path.read_bytes(),NativeEffectContact,maximum_bytes=None)
        store = _store(plane,parent,manifests)
        assert store.recover(binding.carrier_definition(ctx,config,bound,store)) is not None
    else:
        store,ctx = progress_store(plane,bound,ctx,manifests,factory=factory,
            native_work_preparer=binding.prepare_native_work)
    cpu,wall = time.process_time(),time.monotonic()
    result = provider(factory).execute_with_native_subwork(ctx,store,progress=manifests)
    native_cost = time.monotonic()-wall,time.process_time()-cpu
    history = decode_canonical_bytes(next(o.payload for o in result.outputs if hasattr(o,'payload')),MatrixParameterChunkedHistory,maximum_bytes=None)
    assert len(history.segments) == 20 and len(history.arrays.chunks) == 40
    assert sum(m.size_bytes for m in history.arrays.members if not m.name.startswith('terminal_')) > MAXIMUM_MATRIX_ARRAY_BYTES
    assert max(c.array_artifact.size_bytes for c in history.arrays.chunks) < MAXIMUM_MATRIX_ARRAY_BYTES
    def blocked(*args,**kwargs):
        pytest.fail('complete long source cannot replay producers or streams')
    monkeypatch.setattr(binding,'acquire_parameter_segment',blocked)
    monkeypatch.setattr(np.random,'Generator',blocked)
    stream = next(o.source for o in result.outputs if hasattr(o,'source'))
    cpu,wall = time.process_time(),time.monotonic()
    controls_path = tmp_path/'complete-controls.bin'
    with controls_path.open('wb') as sink:
        returned = science.assess_retained(bound,history,stream.fetch,emit_control=sink.write,control_artifact_id='chunked.assess.long-controls')
    cold_cost = time.monotonic()-wall,time.process_time()-cpu
    assert tuple(c.denominator_steps for c in returned.controls) == (5000,10000,5000,5000)
    assert returned.numerical_pass
    assert sum(c.denominator_steps*c.denominator_real_coordinates for c in returned.controls) == 4320000
    from empirical_lawhood.adapters.methods.matrix_array_chunks import iter_framed_chunk_arrays
    with controls_path.open('rb') as inputs:
        assert sum(v.size for _,arrays in iter_framed_chunk_arrays(returned.control_arrays,returned.control_container,inputs.read) for v in arrays.values()) == 25000
    print('long_segment_cost',{'new_native':not bool(retained),'native_wall_cpu_s':native_cost,'cold_wall_cpu_s':cold_cost,
        'decoded_science_bytes':sum(m.size_bytes for m in history.arrays.members if not m.name.startswith('terminal_')),
        'native_physical_bytes':sum(c.array_artifact.size_bytes for c in history.arrays.chunks),
        'framed_ordinary_bytes':history.container.size_bytes,'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024})


@pytest.mark.parametrize('defect',('source-schema','history-schema','design-schema','allocation','container-schema','container-size','unrelated-producers','summary-count'))
def test_compact_report_refuses_unrelated_control_evidence(completed,defect):
    report = completed[5]
    with pytest.raises(ValueError):
        if defect == 'source-schema':
            replace(report,source=replace(report.source,object_schema='empirical-lawhood/tests/wrong-source'))
        elif defect == 'history-schema':
            replace(report,history=replace(report.history,object_schema='empirical-lawhood/tests/wrong-history'))
        elif defect == 'design-schema':
            replace(report,numerical_design=replace(report.numerical_design,object_schema='empirical-lawhood/tests/wrong-design'))
        elif defect == 'allocation':
            replace(report,allocation=replace(report.allocation,object_fingerprint='f'*64))
        elif defect == 'container-schema':
            replace(report,control_container=replace(report.control_container,payload_schema='empirical-lawhood/tests/wrong-container'))
        elif defect == 'container-size':
            replace(report,control_container=replace(report.control_container,size_bytes=report.control_container.size_bytes+1))
        elif defect == 'unrelated-producers':
            arrays = replace(report.control_arrays,producers=(report.history,))
            replace(report,control_arrays=arrays)
        else:
            controls = (replace(report.controls[0],denominator_steps=report.controls[0].denominator_steps+1),*report.controls[1:])
            replace(report,controls=controls)
