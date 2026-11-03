"""Compact allocation exposed conformance; no fresh scientific qualification."""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace
import resource
import shutil
import time
import os
from pathlib import Path

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history import compact_operation_bindings as binding, compact_science
from empirical_lawhood.adapters.methods.matrix_parameter_history.compact_records import (
    MatrixParameterCompactAssessment, MatrixParameterCompactHistory, bind_source, compact_sources,
)
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster, NativeSubworkState
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.test_matrix_parameter_history import progress_store, provider, publish, source


def selected(n=1):
    old = source()
    roots = tuple(replace(old.root,root=replace(old.root.root,root_id=f'test.compact.root.{i:04d}',
        independent_group_id=f'test.compact.group.{i:04d}'),
        streams=tuple(MatrixHistorySeed(p,sha256(f'exposed.compact.{i}.{p}'.encode()).hexdigest()) for p in HISTORY_PURPOSES))
        for i in range(n))
    allocation = replace(old.allocation,roots=roots)
    sources = compact_sources(allocation,old.provenance,old.numerical_design,namespace='source.compact')
    return sources, allocation, old.provenance


def compile_draft(draft,provenance):
    factories = binding.operation_factories()
    registry = CapabilityRegistry('registry.compact.exposed',tuple(sorted((f.manifest for f in factories),key=lambda m:m.registry_id)))
    return compile_recursive_wave(draft=draft,registrations=binding.operation_registrations(),registry=registry,
        implementation_commit=provenance.observed_git_head,output_codecs=binding.output_codecs())


def context(plane,s,a,p,role,*,history=None,raw=None):
    c = next(c for c in a.coordinates if c.coordinate_id == s.coordinate.object_id)
    config = binding.MatrixParameterOperationConfig(f'config.{binding.NAMESPACE}.{s.root_id}.{role}',role,s)
    records = [(config.config_id,config.SCHEMA,config.canonical_bytes()),(s.source_id,s.SCHEMA,s.canonical_bytes()),
        (a.allocation_id,a.SCHEMA,a.canonical_bytes()),(c.coordinate_id,c.SCHEMA,c.canonical_bytes()),
        (p.identity.object_id,p.SCHEMA,p.canonical_bytes())]
    if role == 'history':
        records += [(s.root.stream_identity(stream).object_id,stream.SCHEMA,stream.canonical_bytes()) for stream in s.root.streams]
    else:
        records += [(history.history_id,history.SCHEMA,history.canonical_bytes()),(history.arrays.array_artifact.artifact_id,MATRIX_ARRAY_SCHEMA,raw)]
    def retained_or_publish(name,schema,payload):
        # Reuse the original sidecar identity. Republishing equal bytes with a
        # current validator would try to replace immutable historical metadata.
        from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
        sidecar = plane.root.resolve('inputs/'+name+'.manifest.json',for_write=False)
        if not sidecar.exists():
            return publish(plane,name,schema,payload)
        manifest = decode_artifact_manifest(sidecar.read_bytes())
        plane.verify_manifest(manifest)
        if (manifest.logical.logical_artifact_id != name or manifest.logical.payload_schema != schema
                or manifest.logical.content_sha256 != sha256(payload).hexdigest()
                or manifest.materialization.size_bytes != len(payload)
                or plane.root.resolve(manifest.materialization.relative_path,for_write=False).read_bytes() != payload):
            raise ValueError('retained compact fixture substitutes its actual input bytes or schema')
        return manifest
    manifests = tuple(retained_or_publish(*row) for row in records)
    ports = tuple(plane.open(m,binding=WorkerInputBinding(m.logical.logical_artifact_id,m.materialization.materialization_id,
        m.logical.payload_schema,m.logical.media_type,m.materialization.size_bytes,VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE,WorkerInputKind.EXTERNAL),maximum_bytes=m.materialization.size_bytes) for m in manifests)
    factory = next(f for f in binding.operation_factories() if f.manifest.capability_key.endswith('.'+role))
    product = MatrixParameterCompactHistory if role == 'history' else MatrixParameterCompactAssessment
    outputs = (WorkerOutputPort('compact.'+role+'.product',product.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json'),)
    if role == 'history':
        outputs += (WorkerOutputPort('compact.history.arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz','compact.native-arrays'),)
    ctx = SimpleNamespace(input_ports=ports,output_ports=outputs,config=SimpleNamespace(content_sha256=config.fingerprint()),
        task_id=f'{binding.NAMESPACE}.{s.root_id}.{role}',resource_budget=binding.BUDGET,permissions=factory.manifest.permissions,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return config,ctx,manifests,factory


def test_compact_actual_metadata_growth_and_single_shared_allocation():
    rows = []
    for n in (1,8,32,128):
        start,cpu = time.monotonic(),time.process_time()
        sources,a,p = selected(n)
        draft = binding.development_draft(sources,a,p,draft_id='test.compact.scale')
        raw = draft.canonical_bytes()
        shared = tuple(e for e in draft.external_inputs if e.payload_schema == a.SCHEMA)
        assert len(shared) == 1 and shared[0].expected_content_sha256 == a.fingerprint()
        assert len(draft.operations) == 2*n and len(draft.development_study.assigned_unit_ids) == n
        assert len(draft.external_inputs) == 2+1+5*n
        assert len({len(s.canonical_bytes()) for s in sources}) == 1
        authoring = time.monotonic()-start,time.process_time()-cpu
        compile_start, compile_cpu = time.monotonic(),time.process_time()
        assert len(compile_draft(draft,p).execution_plan.tasks) == 2*n
        rows.append((n,len(raw),len(a.canonical_bytes()),*authoring,time.monotonic()-compile_start,
            time.process_time()-compile_cpu,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    assert rows[-1][1] < 160*rows[0][1]
    print('compact_metadata_scale',rows)


@pytest.mark.parametrize('defect',('missing-root','missing-phase','wrong-system','changed-shared-link','changed-scope','changed-group'))
def test_complete_compiler_refuses_shared_or_census_substitution(defect):
    sources,a,p = selected(2)
    draft = binding.development_draft(sources,a,p,draft_id='test.compact.census')
    if defect == 'missing-root':
        draft = replace(draft,selected_operation_ids=tuple(n for n in draft.selected_operation_ids if sources[1].root_id not in n))
    elif defect == 'missing-phase':
        draft = replace(draft,selected_operation_ids=draft.selected_operation_ids[:-1])
    elif defect == 'wrong-system':
        root = replace(draft.development_study,system=replace(draft.development_study.system,object_fingerprint='f'*64))
        draft = replace(draft,development_study=root)
    elif defect == 'changed-shared-link':
        link = next(l for l in draft.links if l.consumer_input_id == 'allocation')
        draft = replace(draft,links=tuple(replace(l,external_input_id='external.shared.provenance') if l is link else l for l in draft.links))
    else:
        bad = replace(sources[0],allocation_scope_sha256='f'*64) if defect == 'changed-scope' else replace(sources[0],root=replace(sources[0].root,root=replace(sources[0].root.root,independent_group_id='test.compact.changed')))
        with pytest.raises(ValueError):
            binding.development_draft((bad,sources[1]),a,p,draft_id='test.compact.refused')
        return
    with pytest.raises(ValueError):
        compile_draft(draft,p)


def test_compiler_all_roots_and_matched_group_denominator():
    sources,a,p = selected(2)
    draft = binding.development_draft(sources,a,p,draft_id='test.compact.complete')
    compiled = compile_draft(draft,p)
    assert len(compiled.execution_plan.tasks) == 4
    matched = replace(a,roots=(a.roots[0],replace(a.roots[1],root=replace(a.roots[1].root,independent_group_id=a.roots[0].root.independent_group_id),streams=a.roots[0].streams)))
    sources = compact_sources(matched,p,sources[0].numerical_design,namespace='source.compact')
    draft = binding.development_draft(sources,matched,p,draft_id='test.compact.matched')
    assert len(draft.development_study.assigned_unit_ids) == 1 and len(compile_draft(draft,p).execution_plan.tasks) == 4


@pytest.fixture(scope='module')
def completed(tmp_path_factory):
    sources,a,p = selected();s = sources[0]
    retained = os.environ.get('MATRIX_PARAMETER_COMPACT_COMPLETED_FIXTURE')
    plane = _plane(Path(retained) if retained else tmp_path_factory.mktemp('compact-retained')/'original', binary_codecs=MATRIX_STORAGE_CODECS)
    config,ctx,manifests,factory = context(plane,s,a,p,'history')
    bound = bind_source(s,a,a.coordinates[0],p)
    if retained:
        contact = next((Path(retained)/'runs/test.e4.run/native-contacts').glob('*.json'))
        if contact.name.endswith('.manifest.json'):
            contact = next(path for path in contact.parent.glob('*.json') if not path.name.endswith('.manifest.json'))
        parent = decode_canonical_bytes(contact.read_bytes(),NativeEffectContact,maximum_bytes=None)
        store = _store(plane,parent,manifests)
        assert store.recover(binding.native_definition(ctx,config,bound,store)) is not None
    else:
        store,ctx = progress_store(plane,bound,ctx,manifests,factory=factory,
            native_work_preparer=binding.prepare_native_work)
    result = provider(factory).execute_with_native_subwork(ctx,store)
    returned = {o.output_id.rsplit('.',1)[-1]:o.payload for o in result.outputs}
    history = decode_canonical_bytes(returned['product'],MatrixParameterCompactHistory,maximum_bytes=None)
    arrays = compact_science.retained_product(bound,history.arrays,returned['arrays'])
    assessment = compact_science.assess(bound,history,arrays)
    return s,a,p,bound,history,assessment,returned['arrays'],plane,store


def test_actual_supported_native_complete_independent_assessor(completed,tmp_path):
    s,a,p,bound,history,assessment,raw,_,store = completed
    assert history.native.completion.operational_status is OperationalStatus.SUCCEEDED
    assert len(history.native.definition.streams) == 4
    assert len(history.arrays.members) == 11
    assert tuple(c.denominator_steps for c in assessment.controls) == (8,16,8,8)
    assert assessment.numerical_pass and assessment.standing.endswith('NO_FUNCTIONAL_NUMERICAL_ADEQUACY')
    plane = _plane(tmp_path/'assess', binary_codecs=MATRIX_STORAGE_CODECS)
    _,ctx,_,factory = context(plane,s,a,p,'assess',history=history,raw=raw)
    runner = provider(factory)
    assert not hasattr(runner,'execute_with_native_subwork')
    result = runner.execute(ctx)
    assert decode_canonical_bytes(result.outputs[0].payload,MatrixParameterCompactAssessment,maximum_bytes=None) == assessment
    assert store.inspect(history.native.definition).state is NativeSubworkState.COMPLETED
    assert compact_science.read_retained(bound,history,assessment,raw) == assessment


def test_receipt_recovery_relocation_zero_producer_rng_or_reencoding(completed,tmp_path,monkeypatch):
    s,a,p,bound,history,assessment,raw,plane,store = completed
    target = tmp_path/'portable';shutil.copytree(plane.root.contract.canonical_path,target)
    relocated = _plane(target, binary_codecs=MATRIX_STORAGE_CODECS)
    recovered = _store(relocated,store.parent_contact,store.parent_inputs)
    def blocked(*args,**kwargs):
        pytest.fail('completed custody cannot reacquire or reencode')
    monkeypatch.setattr(parameter_source,'acquire_parameter_history',blocked)
    monkeypatch.setattr(binding,'acquire_parameter_history',blocked)
    monkeypatch.setattr(np.random,'Generator',blocked)
    monkeypatch.setattr(compact_science,'encode_matrix_arrays',blocked)
    _,ctx,_,factory = context(relocated,s,a,p,'history')
    result = provider(factory).execute_with_native_subwork(ctx,recovered)
    returned = {o.output_id.rsplit('.',1)[-1]:o.payload for o in result.outputs}
    assert returned['arrays'] == raw
    assert decode_canonical_bytes(returned['product'],MatrixParameterCompactHistory,maximum_bytes=None) == history
    assert compact_science.read_retained(bound,history,assessment,raw) == assessment


@pytest.mark.parametrize('state',('unknown','failed'))
def test_negative_native_custody_never_repeats(tmp_path,monkeypatch,state):
    sources,a,p = selected();s = sources[0]
    plane = _plane(tmp_path/'negative', binary_codecs=MATRIX_STORAGE_CODECS)
    config,ctx,manifests,factory = context(plane,s,a,p,'history')
    bound = bind_source(s,a,a.coordinates[0],p)
    store,ctx = progress_store(plane,bound,ctx,manifests,factory=factory,
        native_work_preparer=binding.prepare_native_work)
    definition = binding.native_definition(ctx,config,bound,store)
    store.freeze_roster(NativeSubworkRoster('selected.native-subwork',store.parent_contact,(definition.identity,)),definitions=(definition,))
    entry = store.begin(definition);store.contact(entry)
    if state == 'failed':
        from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
        from decimal import Decimal
        store.complete(entry,operational_status=OperationalStatus.FAILED,cost=InquiryCost(Decimal(0),Decimal(0),None),
            cost_scope='exposed negative contact fixture',unknown_streams=definition.streams,reason_codes=('exposed-failure',))
    def blocked(*args,**kwargs):
        pytest.fail('negative custody cannot redraw')
    monkeypatch.setattr(binding,'acquire_parameter_history',blocked)
    with pytest.raises(ValueError,match='uncertain|successful|no automatic retry'):
        provider(factory).execute_with_native_subwork(ctx,store)


def test_changed_shared_allocation_and_unsupported_domain_before_effects():
    sources,a,p = selected();s = sources[0]
    with pytest.raises(ValueError,match='shared'):
        bind_source(s,replace(a,allocation_id='test.compact.changed'),a.coordinates[0],p)
    c = replace(a.coordinates[0],primary_view=replace(a.coordinates[0].primary_view,friction_gamma=__import__('decimal').Decimal('1e-18')),
        fine_view=replace(a.coordinates[0].fine_view,friction_gamma=__import__('decimal').Decimal('1e-18')))
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    root = replace(a.roots[0],coordinate=coordinate_identity(c))
    a = replace(a,coordinates=(c,),roots=(root,))
    sources = compact_sources(a,p,s.numerical_design,namespace='source.compact')
    with pytest.raises(ValueError,match='unsupported numerical OU domain'):
        binding.development_draft(sources,a,p,draft_id='test.compact.unsupported')
