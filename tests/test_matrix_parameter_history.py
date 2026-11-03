"""Exposed E4 software conformance; no ROOT programme acquisition or authority."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace
import shutil

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history import independent, science
from empirical_lawhood.adapters.methods.matrix_parameter_history.operation_bindings import (
    BUDGET, NAMESPACE, MatrixParameterOperationConfig, operation_factories,
    development_draft, native_definition, operation_registrations, output_codecs, prepare_native_work,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    MatrixParameterAllocation, MatrixParameterHistoryAssessment, MatrixParameterHistoryProduct,
    MatrixParameterHistorySource, MatrixParameterNumericalDesign, MatrixParameterRoot,
    coordinate_identity, expected_members, identity,
)
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
from empirical_lawhood.adapters.simulators.six_matrix_response.gradients import SixMatrixParameters, reference_action_terms
from empirical_lawhood.adapters.simulators.six_matrix_response.shooting import hermitian_basis
from empirical_lawhood.infrastructure.execution import LocalScheduler, ResourceAdmissionError
from empirical_lawhood.infrastructure.native_subwork_inputs import validate_native_subwork_inputs
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.native_subwork import NativeSubworkInputError, NativeSubworkRoster, NativeSubworkState, NativeSubworkUncertainContact
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
from tests.matrix_native_invocation_support import prepared_native_store
from tests.runtime_platform.test_native_subwork import _plane, _store
from tests.test_matrix_parameter_native import REGIMES, coordinate


def source(regime=REGIMES[1], *, name='test.e4.root', legacy_length=False):
    c = coordinate(regime,dt=D('.001'))
    if legacy_length:
        c = replace(c,ramp_ticks=256,autonomous_ticks=768,observation_ticks=tuple(range(0,1025,16)),
            target_x=D('0.6666666666666666666666666667'),target_y=D('7.333333333333333333333333334'))
    packages = (('exposed-software/e4-native.py','b'*64),)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed-fixture","numpy":"exposed-fixture","scipy":"exposed-fixture","system":"fixture","machine":"fixture","threadpools":[]}',
        'c'*64,packages,sha256(canonical_json_bytes(packages)).hexdigest(),'d'*40,False)
    # Explicit toy inputs, already exposed by this software test. No programme
    # seed derivation or scientific eligibility is claimed.
    streams = tuple(MatrixHistorySeed(p,sha256(('software-only.e4.'+p).encode()).hexdigest()) for p in HISTORY_PURPOSES)
    root = MatrixParameterRoot(MatrixProgrammeRoot(name,'test.e4.group','test.e4.regime',c.coordinate_id,
        MatrixProgrammeRole.DEVELOPMENT,c.clock_id),coordinate_identity(c),streams)
    allocation = MatrixParameterAllocation('test.e4.allocation',(c,),(root,),())
    design = MatrixParameterNumericalDesign('test.e4.numerical',D('1e-8'),D('1e-11'))
    return MatrixParameterHistorySource('source.'+name,allocation,name,provenance,design)


def object_id(name):
    return ObjectIdentity(name,'empirical-lawhood/tests/'+name,'1.0.0','a'*64)


def publish(plane,name,schema,raw):
    array = schema == MATRIX_ARRAY_SCHEMA
    result = plane.write(ArtifactWriteRequest(name,'inputs/'+name,schema,
        ArtifactProfile.MATRIX_ARRAY_NPZ if array else ArtifactProfile.CANONICAL_JSON,
        'application/x-npz' if array else 'application/json','test.e4.software','inputs',raw,
        VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
    return decode_artifact_manifest(plane.root.resolve(result.materialization.relative_path+'.manifest.json',for_write=False).read_bytes())


def provider(factory):
    registry = CapabilityRegistry('registry.test.e4',(factory.manifest,))
    port = ExecutablePlatformPort(factory.binding.required_platform_port_keys[0],
        RecursiveOperationInputPort(SimpleNamespace(resolve_input=lambda spec:None)))
    return factory.build_provider(registry=registry,records=(),platform_ports=(port,)).runners(registry)[0]


def context(plane,source,role,*,history=None,raw=None):
    config = MatrixParameterOperationConfig(f'config.{NAMESPACE}.{source.root_id}.{role}',role,source)
    records = [(config.config_id,config.SCHEMA,config.canonical_bytes()),(source.source_id,source.SCHEMA,source.canonical_bytes())]
    if role == 'history':
        records += [(source.allocation.allocation_id,source.allocation.SCHEMA,source.allocation.canonical_bytes()),
            (source.coordinate.coordinate_id,source.coordinate.SCHEMA,source.coordinate.canonical_bytes()),
            (source.provenance.identity.object_id,source.provenance.SCHEMA,source.provenance.canonical_bytes())]
        records += [(source.root.stream_identity(s).object_id,s.SCHEMA,s.canonical_bytes()) for s in source.root.streams]
    else:
        records += [(history.history_id,history.SCHEMA,history.canonical_bytes()),
            (history.arrays.array_artifact.artifact_id,MATRIX_ARRAY_SCHEMA,raw)]
    manifests = tuple(publish(plane,*row) for row in records)
    ports = tuple(plane.open(m,binding=WorkerInputBinding(m.logical.logical_artifact_id,m.materialization.materialization_id,
        m.logical.payload_schema,m.logical.media_type,m.materialization.size_bytes,VisibilityCeiling.DEVELOPMENT_ONLY,
        OutcomeAccess.DEVELOPMENT_VISIBLE,WorkerInputKind.EXTERNAL),maximum_bytes=m.materialization.size_bytes) for m in manifests)
    factory = next(f for f in operation_factories() if f.manifest.capability_key.endswith('.'+role))
    output_type = MatrixParameterHistoryProduct if role == 'history' else MatrixParameterHistoryAssessment
    outputs = (WorkerOutputPort('test.e4.'+role+'.product',output_type.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json'),)
    if role == 'history':
        outputs += (WorkerOutputPort('test.e4.history.arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz','test.e4.native-arrays'),)
    ctx = SimpleNamespace(input_ports=ports,output_ports=outputs,config=SimpleNamespace(content_sha256=config.fingerprint()),
        task_id=f'{NAMESPACE}.{source.root_id}.{role}',resource_budget=BUDGET,permissions=factory.manifest.permissions,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return config,ctx,manifests,factory


def progress_store(plane,source,ctx,manifests,*,factory,native_work_preparer=prepare_native_work):
    store,ctx,_ = prepared_native_store(plane,runner=provider(factory),context=ctx,manifests=manifests,
        provenance=source.provenance,execution_plan=object_id('test.e4.plan'),
        native_work_preparer=native_work_preparer,run_id='test.e4.run',
        attempt_id='test.e4.run.'+ctx.task_id+'.attempt-001',
        visibility=VisibilityCeiling.DEVELOPMENT_ONLY,access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    return store,ctx


@pytest.fixture(scope='module')
def retained_case(tmp_path_factory):
    # One complete old-length software trajectory: every1025/2049 state row and
    # all1024/2048/1024 innovations are genuinely created under one guarded
    # exposed test receipt. It has no ROOT scientific authority or fresh role.
    s = source(legacy_length=True)
    root = tmp_path_factory.mktemp('e4-retained')
    plane = _plane(root/'original', binary_codecs=MATRIX_STORAGE_CODECS)
    _,ctx,manifests,factory = context(plane,s,'history')
    store,ctx = progress_store(plane,s,ctx,manifests,factory=factory)
    result = provider(factory).execute_with_native_subwork(ctx,store)
    outputs = {o.output_id.rsplit('.',1)[-1]:o.payload for o in result.outputs}
    history = decode_canonical_bytes(outputs['product'],MatrixParameterHistoryProduct,maximum_bytes=None)
    arrays = science.consume_arrays(s,history.arrays,outputs['arrays'])
    assessment = science.assess(s,history,arrays)
    return s,history,assessment,arrays,outputs['arrays'],plane,store,manifests,factory


@pytest.mark.parametrize('regime',REGIMES)
def test_independent_literal_potential_gradient_and_full_paired_steps(regime):
    s = source(regime)
    arrays = parameter_source.acquire_parameter_history(s.coordinate,s.root.streams)
    science.validate_arrays(s,arrays)
    rows = independent.assess_arrays(s.coordinate,arrays,trajectory_tolerance=D('1e-8'),bridge_tolerance=D('1e-11'))
    assert all(r['disposition'] == 'SATISFIED' for r in rows)
    assert tuple(r['denominator_steps'] for r in rows) == (8,16,8,8)
    x = arrays['fine_positions'][5]
    alpha = arrays['fine_alpha_tilde'][5]
    gradient = independent.potential_gradient(x,s.coordinate.member,alpha)
    p = SixMatrixParameters(2,float(s.coordinate.member.mass_x),float(s.coordinate.member.mass_y),
        float(s.coordinate.member.cross_coupling_gamma),*alpha)
    assert independent.potential(x,s.coordinate.member,alpha) == pytest.approx(reference_action_terms(x,p).total,abs=1e-10)
    for sector in range(2):
        for component in range(3):
            for b in hermitian_basis(4):
                direction = np.zeros_like(x);direction[sector,component] = b
                eps = 1e-6
                fd = (independent.potential(x+eps*direction,s.coordinate.member,alpha)
                    -independent.potential(x-eps*direction,s.coordinate.member,alpha))/(2*eps)
                assert fd == pytest.approx(np.vdot(direction,gradient).real,abs=1e-8,rel=1e-6)


def test_full_old_length_bound_source_canonical_census_and_actual_receipt(retained_case):
    s,history,assessment,arrays,raw,_,_,_,_ = retained_case
    assert len(expected_members(s.coordinate)) == len(arrays) == 11
    assert arrays['primary_positions'].shape[0] == 1025 and arrays['fine_positions'].shape[0] == 2049
    assert sum(v.nbytes for v in arrays.values()) == 15808560
    assert tuple((c.denominator_steps,c.denominator_real_coordinates) for c in assessment.controls) == ((1024,192),(2048,192),(1024,192),(1024,96))
    assert assessment.numerical_pass and assessment.standing.endswith('NO_CONTINUUM_BOUND')
    assert history.native.completion.operational_status is OperationalStatus.SUCCEEDED
    assert len(history.native.definition.streams) == 4
    assert decode_canonical_bytes(s.canonical_bytes(),MatrixParameterHistorySource,maximum_bytes=None) == s
    assert decode_canonical_bytes(history.canonical_bytes(),MatrixParameterHistoryProduct,maximum_bytes=None) == history
    assert history.arrays.array_artifact.sha256 == sha256(raw).hexdigest()


def test_actual_factory_qualifies_all_native_operands_before_begin(tmp_path):
    s = source();plane = _plane(tmp_path/'qualify', binary_codecs=MATRIX_STORAGE_CODECS)
    _,ctx,manifests,factory = context(plane,s,'history')
    store,ctx = progress_store(plane,s,ctx,manifests,factory=factory)
    class StopBeforeBegin(Exception):
        pass
    class Qualifier:
        parent_contact = store.parent_contact
        def recover(self,definition):
            return store.recover(definition)
        def inspect(self,definition):
            return store.inspect(definition)
        def freeze_roster(self,roster,*,definitions):
            store.freeze_roster(roster,definitions=definitions)
            assert len(definitions) == 1
            self.definition = definitions[0]
            validate_native_subwork_inputs(plane,self.definition,manifests,visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
                access=OutcomeAccess.DEVELOPMENT_VISIBLE,frozen_parent_inputs=manifests)
            assert store.inspect(self.definition).state is NativeSubworkState.NOT_ENTERED
            raise StopBeforeBegin
        def begin(self,*args):
            pytest.fail('qualification cannot enter a scientific programme')
    q = Qualifier()
    with pytest.raises(StopBeforeBegin):
        provider(factory).execute_with_native_subwork(ctx,q)
    assert set(q.definition.sources) == {identity(s),identity(s.allocation),coordinate_identity(s.coordinate),s.provenance.identity}
    assert len(q.definition.streams) == 4 and len(q.definition.input_materialization_ids) == 9
    with pytest.raises(NativeSubworkInputError):
        validate_native_subwork_inputs(plane,replace(q.definition,sources=tuple(x for x in q.definition.sources if x != s.provenance.identity)),
            manifests,visibility=VisibilityCeiling.DEVELOPMENT_ONLY,access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    with pytest.raises(NativeSubworkInputError):
        validate_native_subwork_inputs(plane,q.definition,manifests[:-1],visibility=VisibilityCeiling.DEVELOPMENT_ONLY,access=OutcomeAccess.DEVELOPMENT_VISIBLE)


def test_actual_pure_provider_scheduler_path_and_complete_finding(retained_case,tmp_path):
    s,history,assessment,_,raw,_,_,_,_ = retained_case
    plane = _plane(tmp_path/'pure', binary_codecs=MATRIX_STORAGE_CODECS)
    _,ctx,_,factory = context(plane,s,'assess',history=history,raw=raw)
    runner = provider(factory)
    assert not factory.registration.native_effect and not hasattr(runner,'execute_with_native_subwork')
    assert LocalScheduler._native_subwork_progress(SimpleNamespace(),runner,None,()) is None
    result = runner.execute(ctx)
    returned = decode_canonical_bytes(result.outputs[0].payload,MatrixParameterHistoryAssessment,maximum_bytes=None)
    assert returned == assessment
    native = next(f for f in operation_factories() if f.registration.native_effect).runner_factory()
    with pytest.raises(ResourceAdmissionError,match='no selected native-effect parent'):
        LocalScheduler._native_subwork_progress(SimpleNamespace(),native,None,())


def test_receipt_only_recovery_cold_relocation_and_independent_reproof(retained_case,tmp_path,monkeypatch):
    s,history,assessment,_,raw,plane,store,_,factory = retained_case
    destination = tmp_path/'portable';shutil.copytree(plane.root.contract.canonical_path,destination)
    relocated = _plane(destination, binary_codecs=MATRIX_STORAGE_CODECS)
    recovered = _store(relocated,store.parent_contact,store.parent_inputs)
    def blocked(*args,**kwargs):
        pytest.fail('retained source reading must not reacquire states or innovations')
    monkeypatch.setattr(parameter_source,'acquire_parameter_history',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.methods.matrix_parameter_history.operation_bindings.acquire_parameter_history',blocked)
    monkeypatch.setattr(np.random,'Generator',blocked)
    _,ctx,_,_ = context(relocated,s,'history')
    result = provider(factory).execute_with_native_subwork(ctx,recovered)
    outputs = {o.output_id.rsplit('.',1)[-1]:o.payload for o in result.outputs}
    assert outputs['arrays'] == raw
    assert decode_canonical_bytes(outputs['product'],MatrixParameterHistoryProduct,maximum_bytes=None) == history
    assert science.read_retained(s,history,assessment,raw) == assessment


@pytest.mark.parametrize('defect',('clock','schedule','member','missing','nonfinite','source','control-denominator'))
def test_source_array_clock_and_control_substitution_refuse(retained_case,defect):
    s,history,assessment,arrays,_,_,_,_,_ = retained_case
    if defect == 'source':
        with pytest.raises(ValueError,match='source'):
            history.validate_source(replace(s,source_id='test.other-source'))
        return
    if defect == 'control-denominator':
        with pytest.raises(ValueError,match='denominator'):
            replace(assessment.controls[0],measured_errors=assessment.controls[0].measured_errors[:-1])
        return
    changed = dict(arrays)
    if defect == 'member':
        with pytest.raises(ValueError,match='source|coordinate'):
            history.validate_source(replace(s,allocation=replace(s.allocation,coordinates=(replace(s.coordinate,target_x=D(1)),))))
        return
    if defect == 'missing':
        changed.pop('bridge_innovations')
    else:
        name = 'primary_ticks' if defect == 'clock' else 'primary_alpha_tilde' if defect == 'schedule' else 'fine_momenta'
        changed[name] = changed[name].copy()
        if defect == 'clock':
            changed[name][-1] = 7
        else:
            changed[name][-1].flat[0] = np.nan if defect == 'nonfinite' else 7
    with pytest.raises(ValueError,match='clock|schedule|finite|member'):
        science.validate_arrays(s,changed)


def test_wrong_innovation_and_state_are_complete_adverse_findings(retained_case):
    s,_,_,arrays,_,_,_,_,_ = retained_case
    changed = dict(arrays)
    changed['fine_momenta'] = changed['fine_momenta'].copy();changed['fine_momenta'][-1,1,2,0,0] += .01
    changed['bridge_innovations'] = changed['bridge_innovations'].copy();changed['bridge_innovations'][17,0,1,0,0] += .1
    rows = independent.assess_arrays(s.coordinate,changed,trajectory_tolerance=s.numerical_design.trajectory_tolerance,bridge_tolerance=s.numerical_design.bridge_tolerance)
    assert rows[1]['disposition'] == rows[2]['disposition'] == 'VIOLATED'
    assert rows[1]['failed_steps'] == (2048,) and rows[2]['failed_steps'] == (18,)
    assert tuple(r['denominator_steps'] for r in rows) == (1024,2048,1024,1024)


def test_complete_allocation_disjointness_matching_and_no_fixed_root_ceiling():
    s = source();a = s.allocation
    second = replace(s.root,root=replace(s.root.root,root_id='test.e4.second',independent_group_id='test.e4.other-group'))
    with pytest.raises(ValueError,match='collide'):
        replace(a,roots=(s.root,second))
    matched = replace(second,root=replace(second.root,independent_group_id=s.root.root.independent_group_id))
    assert len(replace(a,roots=(s.root,matched)).roots) == 2
    with pytest.raises(ValueError,match='exposed'):
        replace(a,prior_effective_seeds=(s.root.streams[0].effective_seed,))
    with pytest.raises(ValueError,match='coordinate'):
        replace(a,coordinates=(replace(s.coordinate,coordinate_id='test.unselected'),))
    # This checks declared multiplicity rather than introducing another bank.
    roots = tuple(replace(s.root,root=replace(s.root.root,root_id=f'test.e4.matched.{i:04d}')) for i in range(129))
    assert len(replace(a,roots=roots).roots) == 129


def test_actual_two_phase_compiler_requires_every_allocated_independent_group():
    first = source()
    streams = tuple(MatrixHistorySeed(p,sha256(('other-exposed-software.e4.'+p).encode()).hexdigest()) for p in HISTORY_PURPOSES)
    second = replace(first.root,root=replace(first.root.root,root_id='test.e4.second',independent_group_id='test.e4.second-group'),streams=streams)
    allocation = replace(first.allocation,roots=(first.root,second))
    sources = (replace(first,allocation=allocation),replace(first,source_id='source.test.e4.second',allocation=allocation,root_id=second.root.root_id))
    draft = development_draft(sources,draft_id='test.e4.whole-two-root')
    factories = operation_factories()
    registry = CapabilityRegistry('registry.test.e4.compiler',tuple(sorted((f.manifest for f in factories),key=lambda m:m.registry_id)))
    compiled = compile_recursive_wave(draft=draft,registrations=operation_registrations(),registry=registry,
        implementation_commit=first.provenance.observed_git_head,output_codecs=output_codecs())
    assert len(compiled.execution_plan.tasks) == 4
    with pytest.raises(ValueError,match='root|census|allocated|unit'):
        compile_recursive_wave(draft=replace(draft,selected_operation_ids=tuple(o for o in draft.selected_operation_ids if second.root.root_id not in o)),
            registrations=operation_registrations(),registry=registry,implementation_commit=first.provenance.observed_git_head,output_codecs=output_codecs())


@pytest.mark.parametrize('variant',('foreign-system','analytic-world','removed-views'))
def test_actual_compiler_refuses_rewritten_scientific_root(variant):
    selected = source()
    draft = development_draft((selected,),draft_id='test.e4.exact-root')
    root = draft.development_study
    if variant == 'foreign-system':
        root = replace(root,system=object_id('test.e4.foreign-system'))
    elif variant == 'analytic-world':
        root = replace(root,world_kind=WorldKind.ANALYTIC_REFERENCE)
    else:
        root = replace(root,numerical_view_ids=())
    # Keep the campaign consistent with the altered root so refusal tests the
    # domain source join, rather than the generic campaign-scope check.
    changed = replace(draft,development_study=root,campaign=replace(draft.campaign,
        system_ids=(root.system.object_id,),world_ids=(root.world_id,)))
    factories = operation_factories()
    registry = CapabilityRegistry('registry.test.e4.exact-root',tuple(sorted((f.manifest for f in factories),key=lambda m:m.registry_id)))
    with pytest.raises(ValueError,match='complete selected scientific root'):
        compile_recursive_wave(draft=changed,registrations=operation_registrations(),registry=registry,
            implementation_commit=selected.provenance.observed_git_head,output_codecs=output_codecs())


def test_actual_default_catalog_compiles_complete_parameter_history_development():
    from empirical_lawhood.api.recursive_operations import operation_catalog

    selected = source()
    draft = development_draft((selected,),draft_id='test.e4.default-catalog')
    registrations,registry,codecs = operation_catalog()
    assert {NAMESPACE+'.history',NAMESPACE+'.assess'}.issubset({r.selection.capability_key for r in registrations})
    compiled = compile_recursive_wave(draft=draft,registrations=registrations,registry=registry,
        implementation_commit=selected.provenance.observed_git_head,output_codecs=codecs)
    assert len(compiled.execution_plan.tasks) == 2
    assert compiled.proof is not None


@pytest.mark.parametrize('state',('uncertain','known-failed'))
def test_actual_uncertain_or_failed_native_receipt_never_repeats(tmp_path,monkeypatch,state):
    s = source();plane = _plane(tmp_path/'negative-contact', binary_codecs=MATRIX_STORAGE_CODECS)
    config,ctx,manifests,factory = context(plane,s,'history')
    store,ctx = progress_store(plane,s,ctx,manifests,factory=factory)
    definition = native_definition(ctx,config,s,store)
    if state == 'uncertain':
        store.freeze_roster(NativeSubworkRoster('selected.native-subwork',store.parent_contact,(definition.identity,)),definitions=(definition,))
        entry = store.begin(definition);store.contact(entry)
        assert store.inspect(definition).state is NativeSubworkState.UNKNOWN_COMPLETION
    else:
        def failure(*args,**kwargs):
            raise ValueError('explicit exposed numerical failure')
        monkeypatch.setattr('empirical_lawhood.adapters.methods.matrix_parameter_history.operation_bindings.acquire_parameter_history',failure)
        with pytest.raises(ValueError,match='exposed numerical failure'):
            provider(factory).execute_with_native_subwork(ctx,store)
        observed = store.inspect(definition)
        assert observed.completion.operational_status is OperationalStatus.FAILED
        assert observed.completion.unknown_streams == definition.streams
        _,ctx,_,_ = context(plane,s,'history')
    def blocked(*args,**kwargs):
        pytest.fail('negative or UNKNOWN contact must not reacquire innovations')
    monkeypatch.setattr('empirical_lawhood.adapters.methods.matrix_parameter_history.operation_bindings.acquire_parameter_history',blocked)
    with pytest.raises((ValueError,NativeSubworkUncertainContact)):
        provider(factory).execute_with_native_subwork(ctx,store)
    assert store.inspect(definition).state is (NativeSubworkState.UNKNOWN_COMPLETION if state == 'uncertain' else NativeSubworkState.COMPLETED)
