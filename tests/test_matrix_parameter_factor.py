"""Exposed parameter-factor conformance; no RNG/acquisition/issue/fit/reveal.

The optional explicit history fixture is a previously closed software native
receipt. Its retained bytes are read, never regenerated or relabelled fresh.
The historical-custody checks are held and optional; the portable gate keeps
the pure missing-source, compiler, provider and algebra controls.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import time
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec, FactorLifetime, ScalarClosureSpec
from empirical_lawhood.adapters.methods.matrix_parameter_factor import independent, science
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.adapters.methods.matrix_parameter_factor.operation_bindings import (
    BUDGET, NAMESPACE, MatrixParameterFactorConfig, development_draft, operation_factories,
    operation_registrations, operands, output_codecs,
)
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    MatrixParameterFactorAssessment, MatrixParameterFactorNumericalDesign, MatrixParameterFactorProduct,
    MatrixParameterFactorSource, MatrixParameterFactorSupply, MatrixParameterScalarContrastSpec,
    MatrixParameterScalarDefinition, allocation_scopes, identity, prefix,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history import science as history_science
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import (
    MatrixParameterHistoryProduct, MatrixParameterHistorySource, MatrixParameterNativeHistory, coordinate_identity,
)
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.infrastructure.execution import LocalScheduler
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.native_subwork import NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_matrix_parameter_history import source as parameter_source


def artifact(record):
    return ArtifactIdentity(identity(record).object_id,'exposed-method',record.SCHEMA,record.fingerprint(),'application/json',len(record.canonical_bytes()))


def case(parameter, supply):
    definition = MatrixParameterScalarDefinition('test.e4.factor.scalar-definition')
    c = parameter.coordinate
    rule = FactorEventSpec('test.e4.factor.rule.'+parameter.root_id,('X','Y'),c.observation_ticks,c.primary_view.timestep,
        256 if c.total_ticks==1024 else 0,32 if c.total_ticks==1024 else 0,D('.05'),D('.05'),D(15),D(15),D(30),D('1e-10'),D('1e-20'),D('.5'),
        ScalarClosureSpec('test.e4.scalar-rule',artifact(definition),D('.30')))
    contrast = MatrixParameterScalarContrastSpec('test.e4.factor.scalar.'+parameter.root_id,coordinate_identity(c),
        ObjectIdentity.from_record(c.member.member_id,c.member),artifact(definition),c.member.beta_rule,c.clock_id)
    design = MatrixParameterFactorNumericalDesign('test.e4.factor.numerical',D('1e-9'),D('1e-9'),D('1e-9'),D('1e-9'),D('1e-9'),D('1e-9'))
    directory = Path(__file__).parents[1]/'src/empirical_lawhood/adapters/methods/matrix_parameter_factor'
    packages = tuple(sorted((p.relative_to(Path(__file__).parents[1]/'src/empirical_lawhood').as_posix(),sha256(p.read_bytes()).hexdigest()) for p in directory.glob('*.py')))
    provenance = NumericalProducingProvenance(parameter.provenance.runtime_observation_json,parameter.provenance.dependency_lock_sha256,
        packages,sha256(canonical_json_bytes(packages)).hexdigest(),parameter.provenance.observed_git_head,False)
    selected = parameter.root.root
    source = MatrixParameterFactorSource('source.test.factor.'+parameter.root_id,ObjectIdentity.from_record(parameter.source_id,parameter),
        ObjectIdentity.from_record(parameter.allocation.allocation_id,parameter.allocation),coordinate_identity(c),identity(supply),rule.identity,
        identity(contrast),identity(definition),identity(design),provenance.identity,parameter.root_id,selected.independent_group_id,c.clock_id,
        allocation_scopes(parameter.allocation),supply.state,None if supply.product is None else supply.product.arrays.array_artifact,supply.product_artifact,
        None if supply.assessment is None else supply.assessment.numerical_pass)
    return source,parameter,supply,rule,contrast,definition,design,provenance


@pytest.fixture(scope='module')
def retained():
    selected = os.environ.get('MATRIX_PARAMETER_FACTOR_EXPOSED_HISTORY')
    if not selected:
        pytest.skip('explicit retained exposed history fixture not selected')
    root = Path(selected)
    original = {str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    parameter = decode_canonical_bytes((root/'inputs/source.test.e4.root').read_bytes(),MatrixParameterHistorySource,maximum_bytes=None)
    directories = tuple((root/'runs/test.e4.run/native-subwork').iterdir())
    assert len(directories)==1
    d = directories[0]
    definition = decode_canonical_bytes((d/'definition.json').read_bytes(),NativeSubworkDefinition,maximum_bytes=None)
    begin = decode_canonical_bytes((d/'begin.json').read_bytes(),NativeSubworkBegin,maximum_bytes=None)
    contact = decode_canonical_bytes((d/'contact.json').read_bytes(),NativeSubworkContact,maximum_bytes=None)
    completion = decode_canonical_bytes((d/'completion.json').read_bytes(),NativeSubworkCompletion,maximum_bytes=None)
    receipt_path, = (root/'runs/test.e4.run/receipts').glob('*/*.attempt-001.json')
    receipt = decode_canonical_bytes(receipt_path.read_bytes(),CanonicalTaskReceipt,maximum_bytes=None)
    manifest = decode_artifact_manifest((d/'outputs/arrays.manifest.json').read_bytes())
    raw = (root/manifest.materialization.relative_path).read_bytes()
    assert len(raw)==manifest.materialization.size_bytes and sha256(raw).hexdigest()==manifest.materialization.physical_sha256
    # Explicit newly authored software postprocessing record from authenticated
    # original native child bytes, not a claim that an original ordinary task
    # published a product or completed. Original native/provenance stay exact.
    from empirical_lawhood.adapters.methods.matrix_parameter_history.operation_bindings import _retained_values
    values = _retained_values(parameter,raw)
    _,operand = history_science.array_product(parameter,values,artifact_id=manifest.logical.logical_artifact_id,raw=raw)
    history = MatrixParameterHistoryProduct('history.exposed-retained-native-child',ObjectIdentity.from_record(parameter.source_id,parameter),
        coordinate_identity(parameter.coordinate),parameter.root_id,parameter.root.root.independent_group_id,parameter.coordinate.clock_id,
        operand,MatrixParameterNativeHistory(definition,completion,receipt),parameter.coordinate.total_ticks,2*parameter.coordinate.total_ticks)
    assessment = history_science.assess(parameter,history,values)
    history_artifact = ArtifactIdentity(history.history_id,'exposed-derived-history',history.SCHEMA,history.fingerprint(),'application/json',len(history.canonical_bytes()))
    supply = MatrixParameterFactorSupply('supply.test.e4.retained-native-child',ObjectIdentity.from_record(parameter.source_id,parameter),
        'COMPLETED',history,assessment,history_artifact,definition,begin,contact,completion,receipt)
    yield case(parameter,supply),raw,root,original
    assert {str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}==original


@pytest.fixture(scope='module')
def scored(retained):
    selected,raw,_,_ = retained
    cpu,wall = time.process_time(),time.monotonic()
    diagnostic,product = science.measure(*selected,raw,artifact_id='test.e4.factor.diagnostics')
    measurement = {'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall}
    cpu,wall = time.process_time(),time.monotonic()
    assessment = independent.assess(*selected,product,raw,diagnostic)
    measurement['assessment_cpu_seconds'] = time.process_time()-cpu
    measurement['assessment_wall_seconds'] = time.monotonic()-wall
    measurement.update(diagnostic_bytes=len(diagnostic),decoded_diagnostic_bytes=sum(m.size_bytes for m in product.arrays.members),
        peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        cost_scope='Exposed retained-native read/scoring and separate assessor; RSS inclusive test process; no new native effects.',
        requested_traces=product.requested_traces,requested_observations=product.requested_observations,
        native_effects=0,fit=0,issue=0,reveal=0)
    if path:=os.environ.get('MATRIX_PARAMETER_FACTOR_COST_PATH'):
        with Path(path).open('x') as f:
            json.dump(measurement,f,sort_keys=True,indent=2);f.write('\n')
    return selected,raw,diagnostic,product,assessment


def absent_case(parameter=None):
    parameter = parameter_source() if parameter is None else parameter
    return case(parameter,MatrixParameterFactorSupply('supply.absent.'+parameter.root_id,ObjectIdentity.from_record(parameter.source_id,parameter),'ABSENT'))


def compile_cases(cases,draft=None):
    factories = operation_factories()
    registry = CapabilityRegistry('registry.test.e4.factor',tuple(sorted((f.manifest for f in factories),key=lambda m:m.registry_id)))
    return compile_recursive_wave(draft=development_draft(cases,draft_id='test.e4.factor') if draft is None else draft,
        registrations=operation_registrations(),registry=registry,implementation_commit=cases[0][1].provenance.observed_git_head,output_codecs=output_codecs())


def test_complete_missing_supply_no_available_traces_and_no_false_assessment():
    selected = absent_case()
    raw,product = science.measure(*selected,None,artifact_id='test.absent.factor.arrays')
    assert product.traces==() and product.requested_traces==4
    assessment = independent.assess(*selected,product,None,raw)
    assert not assessment.numerical_pass and all(c.disposition=='UNASSESSED' for c in assessment.controls)
    n = 4*len(selected[3].lattice)
    assert tuple(len(c.measured_errors) for c in assessment.controls)==(n,15*n,n,n,n,n)
    assert science.root_census(selected[1].allocation,(product,),rules={product.root_id:selected[3]},sources={product.root_id:selected[0]})['independent_groups']==1


def test_actual_two_phase_compiler_and_three_root_provenance_refusals():
    selected = absent_case()
    draft = development_draft((selected,),draft_id='test.e4.factor')
    compiled = compile_cases((selected,),draft)
    assert len(compiled.execution_plan.tasks)==2 and compiled.proof is not None
    for changes in ({'system':ObjectIdentity('test.foreign','empirical-lawhood/tests/foreign','1.0.0','a'*64)},
                    {'world_kind':WorldKind.ANALYTIC_REFERENCE},{'numerical_view_ids':()}):
        root = replace(draft.development_study,**changes)
        changed = replace(draft,development_study=root,campaign=replace(draft.campaign,system_ids=(root.system.object_id,)))
        with pytest.raises(ValueError,match='exact scientific root'):
            compile_cases((selected,),changed)
    with pytest.raises(ValueError,match='census|allocation|unselected supplier'):
        compile_cases((selected,),replace(draft,selected_operation_ids=(draft.selected_operation_ids[0],)))


def test_matched_coordinates_remain_one_group_complete_four_tasks():
    first = parameter_source()
    c = replace(first.coordinate,coordinate_id='test.e4.second-coordinate',member=replace(first.coordinate.member,
        member_id='test.e4.second-member',mass_x=D('.9'),mass_y=D('.9'),cross_coupling_gamma=D('2.2')),
        primary_view=replace(first.coordinate.primary_view,view_id='test.e4.second-primary'),
        fine_view=replace(first.coordinate.fine_view,view_id='test.e4.second-fine'))
    second = replace(first.root,root=replace(first.root.root,root_id='test.e4.second-root',coordinate_id=c.coordinate_id,
        regime_id='test.e4.second-regime'),coordinate=coordinate_identity(c))
    allocation = replace(first.allocation,coordinates=tuple(sorted((first.coordinate,c),key=lambda x:x.coordinate_id)),roots=(first.root,second))
    p1 = replace(first,allocation=allocation)
    p2 = replace(first,allocation=allocation,source_id='source.test.e4.second-root',root_id=second.root.root_id)
    cases = (absent_case(p1),absent_case(p2))
    compiled = compile_cases(cases)
    assert len(compiled.execution_plan.tasks)==4 and len(compiled.draft.development_study.assigned_unit_ids)==1
    products = tuple(science.measure(*c,None,artifact_id='array.'+c[0].root_id)[1] for c in cases)
    census = science.root_census(allocation,products,rules={c[0].root_id:c[3] for c in cases},sources={c[0].root_id:c[0] for c in cases})
    assert census['requested_roots']==2 and census['independent_groups']==1 and len(census['cells'])==8
    with pytest.raises(ValueError,match='omits'):
        science.root_census(allocation,products[:1],rules={c[0].root_id:c[3] for c in cases},sources={c[0].root_id:c[0] for c in cases})


@pytest.mark.held
def test_retained_full_operator_scalar_and_eigenpair_census(scored):
    selected,_,raw,product,assessment = scored
    assert product.requested_traces==4 and product.requested_observations==65 and len(product.scalars)==260
    assert len(product.arrays.members)==40
    assert tuple(len(c.measured_errors) for c in assessment.controls)==(260,3900,260,260,260,260)
    assert assessment.numerical_pass and assessment.admission=='UNASSESSED'
    assert decode_canonical_bytes(product.canonical_bytes(),MatrixParameterFactorProduct,maximum_bytes=None)==product
    assert science.consume_diagnostics(selected[0],selected[3],product,raw)[prefix('PRIMARY','X')+'eigenvectors'].shape==(65,15,15)


@pytest.mark.held
def test_cold_independent_read_with_all_producers_rng_eigensolvers_blocked(scored,monkeypatch):
    selected,native,raw,product,assessment = scored
    def blocked(*args,**kwargs):
        pytest.fail('cold retained factor reading entered a producer/eigensolver/RNG')
    monkeypatch.setattr(science,'measure',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.methods.matrix_parameter_factor.scalar.measure',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.methods.matrix_factor_lifetime.science.measure_trace',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.methods.matrix_factor_lifetime.science.measure_sector',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.simulators.six_matrix_response.parameter_source.acquire_parameter_history',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.simulators.six_matrix_response.simulation.baoab_step_with_hermitian_noise',blocked)
    monkeypatch.setattr(np.linalg,'eigh',blocked)
    monkeypatch.setattr(np.linalg,'eigvalsh',blocked)
    monkeypatch.setattr(np.random,'Generator',blocked)
    assert independent.read_retained(*selected,product,assessment,native,raw)==assessment


def altered(product,arrays):
    nonfinite = tuple(n for n in arrays if not n.endswith(('_ticks','_available','_identifiable')))
    raw,members = encode_matrix_arrays(arrays,nonfinite_members=nonfinite)
    a = replace(product.arrays.array_artifact,sha256=sha256(raw).hexdigest(),size_bytes=len(raw))
    p = replace(product,arrays=replace(product.arrays,array_artifact=a,members=members),
        traces=tuple(replace(t,diagnostics=a,diagnostic_members=members) for t in product.traces))
    return raw,p


@pytest.mark.parametrize('field',('operator','eigenvectors','spectrum'))
@pytest.mark.held
def test_independent_witness_retains_last_eigenpair_and_source_failures(scored,field):
    selected,native,raw,product,_ = scored
    arrays = {k:v.copy() for k,v in science.consume_diagnostics(selected[0],selected[3],product,raw).items()}
    b = prefix('FINE','Y')
    index = int(np.flatnonzero(arrays[b+'available'])[-1])
    if field=='operator':
        arrays[b+field][index]+=np.eye(15)*.01
    elif field=='eigenvectors':
        arrays[b+field][index,:,-1]*=2
    else:
        arrays[b+field][index,-1]+=.01
    changed,p = altered(product,arrays)
    if field=='spectrum':
        # Its identifiability may change: a structural inconsistency correctly
        # refuses before reduction rather than inventing a positive control.
        try:
            assessed = independent.assess(*selected,p,native,changed)
        except ValueError:
            return
    else:
        assessed = independent.assess(*selected,p,native,changed)
    assert not assessed.numerical_pass and any(c.disposition=='VIOLATED' for c in assessed.controls)
    assert len(assessed.controls[1].measured_errors)==3900


@pytest.mark.held
def test_changed_member_clock_and_missing_native_contact_refuse(retained):
    selected,_,_,_ = retained
    source,p,supply,rule,contrast,definition,design,provenance = selected
    for changed in (replace(contrast,member=ObjectIdentity('test.foreign-member',contrast.member.object_schema,'1.0.0','a'*64)),
                    replace(contrast,clock_id='test.foreign-clock')):
        changed_source = replace(source,scalar=identity(changed))
        with pytest.raises(ValueError,match='member|clock'):
            changed_source.validate_operands(p,supply,rule,changed,definition,design,provenance)
    with pytest.raises(ValueError,match='completion|contact'):
        replace(supply,begin=None)
    with pytest.raises(ValueError,match='positive'):
        replace(supply,state='UNKNOWN_COMPLETION')


def worker_context(plane,selected,role,native,*,product=None,diagnostic=None):
    source,_,_,rule,*_ = selected
    config = MatrixParameterFactorConfig(f'config.{NAMESPACE}.{source.root_id}.{role}',role,source,rule)
    values = [config,*operands(*selected).values()]
    if product is not None:
        values.append(product)
    # Original allocation/coordinate/source use their own existing ID fields.
    rows = []
    for v in values:
        name = (v.coordinate_id if hasattr(v,'coordinate_id') else v.allocation_id if hasattr(v,'allocation_id')
            else v.source_id if hasattr(v,'source_id') else v.identity.object_id if isinstance(v,NumericalProducingProvenance) else identity(v).object_id)
        rows.append((name,v.SCHEMA,v.canonical_bytes()))
    if product is not None:
        rows[-1] = ('output.actual.current.measure.product',rows[-1][1],rows[-1][2])
    if native is not None:
        rows.append((source.history_arrays.artifact_id,MATRIX_ARRAY_SCHEMA,native))
    if diagnostic is not None:
        rows.append((product.arrays.array_artifact.artifact_id,MATRIX_ARRAY_SCHEMA,diagnostic))
    ports = []
    for i,(name,schema,raw) in enumerate(rows):
        is_array = schema==MATRIX_ARRAY_SCHEMA
        if is_array and native is not None and name==source.history_arrays.artifact_id:
            # Open the original authenticated software native array publication
            # directly. No second eight-MiB native archive is written here.
            original = Path(os.environ['MATRIX_PARAMETER_FACTOR_EXPOSED_HISTORY'])
            original_plane = _plane(original, binary_codecs=MATRIX_STORAGE_CODECS)
            manifest_path = next((original/'runs/test.e4.run/native-subwork').rglob('outputs/arrays.manifest.json'))
            m = decode_artifact_manifest(manifest_path.read_bytes())
            assert m.logical.logical_artifact_id==name and m.logical.content_sha256==sha256(raw).hexdigest()
            ports.append(original_plane.open(m,binding=WorkerInputBinding(name,m.materialization.materialization_id,schema,m.logical.media_type,
                len(raw),VisibilityCeiling.DEVELOPMENT_ONLY,OutcomeAccess.DEVELOPMENT_VISIBLE,WorkerInputKind.EXTERNAL),maximum_bytes=len(raw)))
            continue
        publication = plane.write(ArtifactWriteRequest(name,f'factor-inputs/{role}/{i}',schema,
            ArtifactProfile.MATRIX_ARRAY_NPZ if is_array else ArtifactProfile.CANONICAL_JSON,
            'application/x-npz' if is_array else 'application/json','test.factor-software','factor-inputs',raw,
            VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        m = decode_artifact_manifest(plane.root.resolve(publication.materialization.relative_path+'.manifest.json',for_write=False).read_bytes())
        ports.append(plane.open(m,binding=WorkerInputBinding(name,m.materialization.materialization_id,schema,m.logical.media_type,
            len(raw),VisibilityCeiling.DEVELOPMENT_ONLY,OutcomeAccess.DEVELOPMENT_VISIBLE,WorkerInputKind.EXTERNAL),maximum_bytes=len(raw)))
    factory = next(f for f in operation_factories() if f.manifest.capability_key.endswith('.'+role))
    outputs = (WorkerOutputPort('test.factor.'+role+'.product',
        MatrixParameterFactorProduct.SCHEMA if role=='measure' else MatrixParameterFactorAssessment.SCHEMA,ArtifactProfile.CANONICAL_JSON,'application/json'),)
    if role=='measure':
        outputs+=(WorkerOutputPort('test.factor.measure.arrays',MATRIX_ARRAY_SCHEMA,ArtifactProfile.MATRIX_ARRAY_NPZ,'application/x-npz','array.test.factor.measure'),)
    ctx = SimpleNamespace(input_ports=tuple(ports),output_ports=outputs,config=SimpleNamespace(content_sha256=config.fingerprint()),
        task_id=f'{NAMESPACE}.{source.root_id}.{role}',resource_budget=BUDGET,permissions=factory.manifest.permissions,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    registry = CapabilityRegistry('registry.test.factor-provider',(factory.manifest,))
    platform = ExecutablePlatformPort(factory.binding.required_platform_port_keys[0],RecursiveOperationInputPort(SimpleNamespace(resolve_input=lambda spec:None)))
    runner = factory.build_provider(registry=registry,records=(),platform_ports=(platform,)).runners(registry)[0]
    return runner,ctx


def test_actual_provider_pure_measure_assess_and_missing_source_no_native(tmp_path):
    selected = absent_case()
    plane = _plane(tmp_path/'pure-provider', binary_codecs=MATRIX_STORAGE_CODECS)
    runner,ctx = worker_context(plane,selected,'measure',None)
    assert not hasattr(runner,'execute_with_native_subwork')
    assert LocalScheduler._native_subwork_progress(SimpleNamespace(),runner,None,()) is None
    result = runner.execute(ctx)
    outputs = {o.output_id:o.payload for o in result.outputs}
    product = decode_canonical_bytes(outputs['test.factor.measure.product'],MatrixParameterFactorProduct,maximum_bytes=None)
    diagnostic = outputs['test.factor.measure.arrays']
    runner,ctx = worker_context(plane,selected,'assess',None,product=product,diagnostic=diagnostic)
    assert not hasattr(runner,'execute_with_native_subwork')
    assert LocalScheduler._native_subwork_progress(SimpleNamespace(),runner,None,()) is None
    result = runner.execute(ctx)
    assessment = decode_canonical_bytes(result.outputs[0].payload,MatrixParameterFactorAssessment,maximum_bytes=None)
    assert not assessment.numerical_pass and assessment.admission=='UNASSESSED'


@pytest.mark.held
def test_actual_complete_cold_provider_reads_original_raw_before_finding(scored,tmp_path,monkeypatch):
    selected,native,raw,product,assessment = scored
    plane = _plane(tmp_path/'complete-assessor', binary_codecs=MATRIX_STORAGE_CODECS)
    runner,ctx = worker_context(plane,selected,'assess',native,product=product,diagnostic=raw)
    def blocked(*args,**kwargs):
        pytest.fail('complete pure provider entered a producer or native path')
    monkeypatch.setattr(science,'measure',blocked)
    monkeypatch.setattr(np.linalg,'eigh',blocked)
    monkeypatch.setattr(np.linalg,'eigvalsh',blocked)
    monkeypatch.setattr(np.random,'Generator',blocked)
    assert LocalScheduler._native_subwork_progress(SimpleNamespace(),runner,None,()) is None
    result = runner.execute(ctx)
    assert decode_canonical_bytes(result.outputs[0].payload,MatrixParameterFactorAssessment,maximum_bytes=None)==assessment


@pytest.mark.parametrize('state',('BEGUN','UNKNOWN_COMPLETION'))
@pytest.mark.held
def test_hypothetical_unknown_source_keeps_all_requested_unavailable_cells(retained,state):
    # Explicit hypothetical metadata guard, not a reassignment of the actual
    # closed fixture's state. Its original completion bytes remain retained.
    selected,_,_,_ = retained
    _,parameter,complete,*_ = selected
    supply = MatrixParameterFactorSupply('supply.test.hypothetical.'+state.lower(),complete.source,state,
        definition=complete.definition,begin=complete.begin,contact=complete.contact if state=='UNKNOWN_COMPLETION' else None)
    current = case(parameter,supply)
    raw,product = science.measure(*current,None,artifact_id='array.test.hypothetical.'+state.lower())
    assessment = independent.assess(*current,product,None,raw)
    assert product.traces==() and product.source_state==state and product.history_numerical_pass is None
    assert len(product.scalars)==260 and all(c.disposition=='UNASSESSED' for c in assessment.controls)


@pytest.mark.held
def test_unreceipted_completion_is_retained_unknown_without_positive_product(retained):
    selected,_,_,_ = retained
    _,parameter,original,*_ = selected
    supply = MatrixParameterFactorSupply('supply.hypothetical.completion-no-receipt',original.source,'UNKNOWN_COMPLETION',
        definition=original.definition,begin=original.begin,contact=original.contact,completion=original.completion)
    assert supply.completion==original.completion and supply.receipt is None and supply.product is None
    current = case(parameter,supply)
    raw,product = science.measure(*current,None,artifact_id='array.hypothetical.completion-no-receipt')
    finding = independent.assess(*current,product,None,raw)
    assert product.source_state=='UNKNOWN_COMPLETION' and product.traces==() and not finding.numerical_pass


@pytest.mark.held
def test_original_native_receipt_and_named_operation_cannot_be_substituted(retained):
    selected,_,_,_ = retained
    _,parameter,supply,*_ = selected
    for field,value in (('run_id','test.foreign-run'),('task_id','test.foreign-task'),('attempt_id','test.foreign-attempt')):
        receipt = replace(supply.receipt,**{field:value})
        with pytest.raises(ValueError,match='native receipt|receipt/completion'):
            native = replace(supply.product.native,receipt=receipt)
            product = replace(supply.product,native=native)
            replace(supply,product=product,product_artifact=replace(supply.product_artifact,sha256=product.fingerprint(),size_bytes=len(product.canonical_bytes())),receipt=receipt)
    definition = replace(supply.definition,operation_id='test.foreign-native-operation')
    hypothetical = MatrixParameterFactorSupply('supply.hypothetical.foreign-operation',supply.source,'BEGUN',
        definition=definition,begin=NativeSubworkBegin(definition.identity))
    with pytest.raises(ValueError,match='named original native'):
        hypothetical.validate_source(parameter)


@pytest.mark.held
def test_root_census_refuses_duplicate_traces_and_rewritten_lifetime(scored):
    selected,_,_,product,_ = scored
    allocation = selected[1].allocation
    args = {'rules':{product.root_id:selected[3]},'sources':{product.root_id:selected[0]}}
    with pytest.raises(ValueError,match='duplicates|omits'):
        science.root_census(allocation,(replace(product,traces=(product.traces[0],)*4),),**args)
    trace = product.traces[0]
    wrong_life = FactorLifetime(None,'UNKNOWN','UNKNOWN',None,None,(selected[3].lattice[-1],))
    assert wrong_life!=trace.moving_lifetime
    with pytest.raises(ValueError,match='lifetime|observations'):
        wrong = replace(trace,moving_lifetime=wrong_life)
        science.root_census(allocation,(replace(product,traces=(wrong,*product.traces[1:])),),**args)
    with pytest.raises(ValueError,match='denominator'):
        science.root_census(allocation,(replace(product,history_numerical_pass=not product.history_numerical_pass),),**args)
    with pytest.raises(ValueError,match='root/source'):
        wrong_family = replace(product,traces=tuple(replace(t,root=replace(t.root,family_id='test.foreign-family')) for t in product.traces))
        science.root_census(allocation,(wrong_family,),**args)


def test_literal_pauli_guard_rejects_orthonormal_nonfactor_chart():
    from empirical_lawhood.adapters.methods.matrix_history_analysis.algebra import BASIS, LEFT
    unitary,_ = np.linalg.qr(np.asarray([[1,2j,3,4],[2,4,1j,3],[3j,1,4,2],[4,3,2,1j]],dtype='<c16'))
    assert independent.pauli_residual(unitary@LEFT@unitary.conj().T)<1e-12
    assert np.allclose(np.einsum('iab,jab->ij',BASIS[:3].conj(),BASIS[:3]),np.eye(3))
    assert independent.pauli_residual(BASIS[:3])>1e-3


@pytest.mark.held
def test_unreceipted_completion_cannot_change_original_output_census(retained):
    selected,_,_,_ = retained
    supply = selected[2]
    completion = replace(supply.completion,output_ids=('undeclared',))
    with pytest.raises(ValueError,match='completion output census'):
        MatrixParameterFactorSupply('supply.hypothetical.bad-unreceipted-completion',supply.source,'UNKNOWN_COMPLETION',
            definition=supply.definition,begin=supply.begin,contact=supply.contact,completion=completion)
