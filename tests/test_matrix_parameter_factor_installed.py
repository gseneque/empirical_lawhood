"""Actual default PURE author/run/provider over original exposed native custody.

Earlier pytest factor outputs were pruned. Retain one genuinely new PURE run;
never recreate or relabel their original task returns or native acquisitions.
"""
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import time
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_parameter_factor import science
from empirical_lawhood.adapters.methods.matrix_parameter_factor.operation_bindings import BUDGET, NAMESPACE, development_draft, operands
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorAssessment, MatrixParameterFactorProduct
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
from empirical_lawhood.api.recursive_authoring import author_recursive_wave, load_authored_wave
from empirical_lawhood.api.recursive_execution import _external_inputs, read_recursive_wave, run_recursive_wave
from empirical_lawhood.api.recursive_operations import operation_catalog, operation_factories
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.execution import LocalScheduler
from empirical_lawhood.infrastructure.recursive_custody import iter_exact_custody_file_chunks
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.execution import WorkerInputBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
from empirical_lawhood.runtime.providers import ExternalInputPayload
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
from tests.runtime_platform.test_native_subwork import _plane
from tests.test_matrix_parameter_factor import retained as _retained_fixture

# Optional inspection of original external test custody; not release acceptance.
pytestmark = pytest.mark.held

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def original_retained():
    yield from _retained_fixture.__wrapped__()


@pytest.fixture(scope='module')
def installed_proof_parent():
    value=os.environ.get('MATRIX_PARAMETER_FACTOR_INSTALLED_PROOF')
    if not value:
        pytest.skip('explicit installed PURE proof parent not selected')
    parent=Path(value)
    assert parent.is_absolute() and not parent.exists() and not parent.is_symlink()
    parent.mkdir()
    return parent


def inventory(root):
    return tuple((str(p.relative_to(root)),p.stat().st_size,sha256(p.read_bytes()).hexdigest())
        for p in sorted(root.rglob('*')) if p.is_file())


def pin(p):
    b=p.read_bytes()
    return {'path':str(p),'size_bytes':len(b),'sha256':sha256(b).hexdigest()}


def opened(plane, manifest, *, artifact_id=None,kind=WorkerInputKind.EXTERNAL):
    return plane.open(manifest,binding=WorkerInputBinding(
        manifest.logical.logical_artifact_id if artifact_id is None else artifact_id,
        manifest.materialization.materialization_id,manifest.logical.payload_schema,manifest.logical.media_type,
        manifest.materialization.size_bytes,VisibilityCeiling.DEVELOPMENT_ONLY,OutcomeAccess.DEVELOPMENT_VISIBLE,
        kind),maximum_bytes=manifest.materialization.size_bytes)


def test_installed_default_author_execution_provider_and_exact_refusals(installed_proof_parent,original_retained,monkeypatch):
    proof=installed_proof_parent/'author-run-provider'
    assert not proof.exists()
    proof.mkdir()
    plane=_plane(proof/'custody')
    previous_case,_,original,_=original_retained
    before_native=inventory(original)
    # Actual current analysis provenance is separate from the unchanged
    # explicitly synthetic original native fixture's producing provenance.
    current=capture_matrix_provenance(project_root=ROOT)
    case=(replace(previous_case[0],producing_provenance=current.identity),*previous_case[1:-1],current)
    source,parameter,_,rule,*_=case
    source.validate_operands(*case[1:])
    registrations,registry,codecs=operation_catalog()
    factories=tuple(f for f in operation_factories() if f.manifest.capability_key.startswith(NAMESPACE+'.'))
    assert len(factories)==2 and all(not f.registration.native_effect for f in factories)
    native_manifest_path=next((original/'runs/test.e4.run/native-subwork').rglob('outputs/arrays.manifest.json'))
    native_manifest=decode_artifact_manifest(native_manifest_path.read_bytes())
    native_path=original/native_manifest.materialization.relative_path
    assert (native_manifest.logical.logical_artifact_id,native_manifest.logical.content_sha256)==(source.history_arrays.artifact_id,source.history_arrays.sha256)
    with pytest.raises(ArtifactIdentityConflict,match='binding differs'):
        opened(_plane(original),native_manifest,artifact_id='test.substituted-native-alias')
    draft=development_draft((case,),draft_id='test.matrix-parameter-factor.installed-default')
    compile_args={'registrations':registrations,'registry':registry,'implementation_commit':current.observed_git_head,'output_codecs':codecs}
    compilation=compile_recursive_wave(draft=draft,**compile_args)
    assert len(compilation.execution_plan.tasks)==2 and compilation.proof is not None
    refusals=[]
    for label,change in (('foreign-system',{'system':ObjectIdentity('test.foreign-system','empirical-lawhood/tests/foreign','1.0.0','a'*64)}),
                         ('analytic-world',{'world_kind':WorldKind.ANALYTIC_REFERENCE}),('deleted-views',{'numerical_view_ids':()})):
        root=replace(draft.development_study,**change)
        altered=replace(draft,development_study=root,campaign=replace(draft.campaign,system_ids=(root.system.object_id,)))
        with pytest.raises(ValueError,match='exact scientific root'):
            compile_recursive_wave(draft=altered,**compile_args)
        refusals.append(label)
    with pytest.raises(ValueError,match='typed operands'):
        source.validate_operands(parameter,case[2],rule,case[4],case[5],case[6],replace(current,observed_git_head='a'*40))
    refusals.append('analysis-provenance')
    (proof/'operands').mkdir()
    paths={}
    for name,value in operands(*case).items():
        path=proof/'operands'/name
        path.write_bytes(value.canonical_bytes())
        paths[name]=path
    paths['history-arrays']=native_path
    bindings=tuple(('external.'+source.root_id+'.'+name,path) for name,path in sorted(paths.items()))
    authored=author_recursive_wave(draft=draft,project_root=ROOT,artifact_writer=plane,output_dir=proof/'custody/authored',input_bindings=bindings)
    assert authored['status']=='AUTHORED' and authored['task_count']==2 and authored['native_contact']=='none'
    cpu,wall=time.process_time(),time.monotonic()
    run_report=run_recursive_wave(directory=proof/'custody/authored',project_root=ROOT,artifact_writer=plane,terminal_product_format='references')
    runtime={'wall_seconds':time.monotonic()-wall,'controller_cpu_seconds':time.process_time()-cpu,
        'inclusive_peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
    assert run_report['status']=='SUCCEEDED' and run_report['task_count']==2 and run_report['new_native_contact_count']==0
    assert run_report['native_contact']=='none'

    cold_reproof(proof=proof,output=proof,plane=plane,case=case,draft=draft,original=original,before_native=before_native,factories=factories,registry=registry,authored=authored,run_report=run_report,runtime=runtime,refusals=refusals,monkeypatch=monkeypatch)

def cold_reproof(*,proof,output,plane,case,draft,original,before_native,factories,registry,authored,run_report,runtime,refusals,monkeypatch):
    source,parameter,_,_,*_=case
    current=case[-1]
    native_manifest_path=next((original/'runs/test.e4.run/native-subwork').rglob('outputs/arrays.manifest.json'))
    native_manifest=decode_artifact_manifest(native_manifest_path.read_bytes())
    native_path=original/native_manifest.materialization.relative_path
    with pytest.raises(ArtifactIdentityConflict,match='binding differs'):
        opened(_plane(original),native_manifest,artifact_id='test.substituted-native-alias')
    def blocked(*args,**kwargs):
        pytest.fail('cold installed PURE reproof entered a producer/eigensolver/native/RNG path')
    monkeypatch.setattr(science,'measure',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.methods.matrix_parameter_factor.scalar.measure',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.simulators.six_matrix_response.parameter_source.acquire_parameter_history',blocked)
    monkeypatch.setattr('empirical_lawhood.adapters.simulators.six_matrix_response.simulation.baoab_step_with_hermitian_noise',blocked)
    monkeypatch.setattr(np.linalg,'eigh',blocked)
    monkeypatch.setattr(np.linalg,'eigvalsh',blocked)
    monkeypatch.setattr(np.random,'Generator',blocked)
    cold_report,products,returned,plan=read_recursive_wave(directory=proof/'custody/authored',artifact_writer=plane,include_products=True,terminal_product_format='references')
    assert returned==draft and cold_report['status']=='SUCCEEDED' and len(products['receipts'])==2
    packet,_,_,payloads=load_authored_wave(directory=proof/'custody/authored',artifact_writer=plane,lazy_payloads=True)
    assert packet.fingerprint()==authored['packet_sha256']
    inputs=_external_inputs(plane=plane,plan=plan,draft=draft,payloads=payloads,read_only=True)
    task=next(t for t in plan.tasks if t.capability.capability_key.endswith('.assess'))
    measure_task=next(t for t in plan.tasks if t.capability.capability_key.endswith('.measure'))
    product=next(p for p in products['records'][measure_task.task_id].values() if type(p) is MatrixParameterFactorProduct)
    previous=next(p for p in products['records'][task.task_id].values() if type(p) is MatrixParameterFactorAssessment)
    current_output=next(o for o in measure_task.outputs if o.payload_schema==MatrixParameterFactorProduct.SCHEMA)
    assert current_output.logical_artifact_id!=product.product_id
    assert products['outputs'][current_output.logical_artifact_id].logical.content_sha256==product.fingerprint()
    factory=next(f for f in factories if f.manifest.capability_key.endswith('.assess'))
    by_id={v.logical.logical_artifact_id:v for v in inputs}
    calls=[]
    def supply_input(spec):
        calls.append(spec.logical_artifact_id)
        value=by_id[spec.logical_artifact_id]
        path=plane.root.resolve(value.materialization.relative_path,for_write=False)
        stream=SimpleNamespace(chunks=lambda amount:iter_exact_custody_file_chunks(path,size_bytes=value.materialization.size_bytes,
            expected_sha256=value.materialization.physical_sha256,maximum_chunk_bytes=amount),close=lambda:None)
        return ExternalInputPayload(spec.logical_artifact_id,value.logical.payload_schema,value.logical.profile,value.logical.media_type,
            stream,value.materialization.size_bytes,value.materialization.physical_sha256,max(1,value.materialization.size_bytes),min(65536,max(1,value.materialization.size_bytes)),
            value.logical.visibility_ceiling,value.logical.outcome_access,value.logical.parent_visibility_ceilings,value.logical.lineage_parents,
            value.logical.content_sha256)
    port=ExecutablePlatformPort(factory.binding.required_platform_port_keys[0],RecursiveOperationInputPort(SimpleNamespace(resolve_input=supply_input)))
    provider=factory.build_provider(registry=registry,records=(),platform_ports=(port,))
    supplied=provider.external_inputs(plan)
    for value in supplied:
        assert sha256(b''.join(value.chunks())).hexdigest()==value.source_sha256
        value.close()
    assert calls and len(calls)==len(supplied)
    runner=provider.runners(registry)[0]
    assert not hasattr(runner,'execute_with_native_subwork') and LocalScheduler._native_subwork_progress(SimpleNamespace(),runner,None,()) is None
    external_ids={s.logical_artifact_id for s in task.external_inputs}
    worker_inputs=[opened(plane,by_id[name]) for name in sorted(external_ids)]
    worker_inputs += [opened(plane,products['outputs'][o.logical_artifact_id],kind=WorkerInputKind.DEPENDENCY) for o in measure_task.outputs]
    ctx=SimpleNamespace(input_ports=tuple(worker_inputs),output_ports=tuple(WorkerOutputPort(o.output_id,o.payload_schema,o.profile,o.media_type,o.logical_artifact_id) for o in task.outputs),
        config=task.capability.config,task_id=task.task_id,resource_budget=BUDGET,permissions=task.capability.required_permissions,
        outcome_access=task.capability.requested_outcome_access)
    cpu,wall=time.process_time(),time.monotonic()
    result=runner.execute(ctx)
    reproof_cost={'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall}
    finding=decode_canonical_bytes(result.outputs[0].payload,MatrixParameterFactorAssessment,maximum_bytes=None)
    assert finding==previous and finding.admission=='UNASSESSED' and len(finding.controls)==6 and len(finding.controls[1].measured_errors)==3900
    (output/'independent-cold-assessment.json').write_bytes(finding.canonical_bytes())
    assert inventory(original)==before_native
    record={'schema':'el.matrix.e4.parameter-factor-installed-pure-proof.v2','authoring':authored,'actual_run':run_report,'cold_read':cold_report,
        'installed_factory_bindings':[{'id':f.binding.binding_id,'sha256':f.binding.fingerprint(),'manifest_sha256':f.manifest.fingerprint()} for f in factories],
        'compiler_tasks':2,'root_and_provenance_refusals':refusals,'custody_binding_alias_refusals':['original-native-arrays'],
        'actual_compiler_product_artifact_id':current_output.logical_artifact_id,'internal_product_id':product.product_id,
        'original_native_provenance':parameter.provenance.identity.to_document(),'current_analysis_provenance':current.identity.to_document(),
        'native_original':pin(native_path),'new_independent_cold_assessment':pin(output/'independent-cold-assessment.json'),
        'original_native_inventory_unchanged':True,'run_cost':runtime,'cold_reproof_cost':reproof_cost,'provider_actual_supplied_inputs':len(supplied),
        'producer_native_eigen_rng_calls_during_cold':0,'new_native_effects':0,'issue_fit_reveal':0,
        'prior_pytest_factor_outputs':'PRUNED_DISPOSABLE_NOT_RECREATED_AS_ORIGINAL_RETURNS',
        'scope':'One genuinely new exposed PURE measure/assess through installed default public author/compiler/scheduler and provider cold reproof; no scientific qualification.'}
    (output/'readout.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    return record
