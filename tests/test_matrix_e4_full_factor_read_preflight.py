# SPDX-License-Identifier: MPL-2.0
"""Actual public DEV compile/input-custody read preflight before any worker.

Original producer I/O is a disclosed fixture seam. All copied inputs, compiler,
authoring, generic DEV input publication and retained graph checks remain real.
No native work, issue, reveal or scientific qualification is produced.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_bindings as owner
from empirical_lawhood.api import matrix_full_factor_derivation as derive,matrix_full_factor_authoring as author,matrix_full_factor_read as reader
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_authoring import implementation_binding,load_authored_wave
from empirical_lawhood.api.recursive_execution import _external_inputs,_retained_plans
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_e4_full_factor_public import ROOT,_copied,_real_plane,_published_secondary,_development_access_seam,selected  # noqa: F401
from tests.test_matrix_e4_full_factor_values import scopes  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401


def test_actual_public_compile_and_consumed_scope_pass_read_preflight_before_worker_entry(selected,tmp_path,monkeypatch):  # noqa: F811
    root=tmp_path/'full-factor-read-preflight'
    plane=_real_plane(root)
    selected,_,_=_published_secondary(selected,plane)
    monkeypatch.setattr(LocalProcessExecutor,'execute',lambda *args,**kwargs:pytest.fail('read preflight entered an executor'))
    access=_development_access_seam(monkeypatch,selected,plane)
    def original(**kwargs):
        kwargs['_consume_original_access'](access,selected.evidence)
        return selected.scope,()
    monkeypatch.setattr(derive,'derive_original_full_factor_scope',original)
    monkeypatch.setattr(author,'authenticate_original_full_factor_scope',lambda **kwargs:())
    spec_path,inputs_path=_copied(selected,root)
    service=ExperimentProgrammeService(ROOT,plane)
    source=implementation_binding(ROOT)
    execution=ExecutionSelection(4,'main-locked',ObjectIdentity.from_record('recursive-member.implementation',source),str(root))
    result=service.derive_inputs(specification_path=spec_path,source_selection_path=inputs_path,metadata_directory=root/'derived',
        output_selection_path=root/'derived'/'sources.json',execution=execution)
    copied=load_experiment_inputs(result.target_specification,result.source_selection_path,artifact_writer=plane)
    directory=root/'authored'
    assert service.author(preparation=result.preparation,output_dir=directory)['status']=='AUTHORED'
    _,draft,_,payloads=load_authored_wave(directory=directory,artifact_writer=plane,lazy_payloads=True)
    _,plan,_=_retained_plans(payloads,draft)
    tasks=reader._graph(result.target_specification,copied.method_inputs,draft,plan)
    assert len(tasks)==2*len(selected.scope.sources)+1
    assert all(row.expected_size_bytes is None for task in plan.tasks for row in task.external_inputs
        if row.logical_artifact_id!=task.capability.config.artifact_id)
    # The ordinary DEV owner publishes and reopens exact input bytes only.
    _external_inputs(plane=plane,plan=plan,draft=draft,payloads=payloads,read_only=False)
    current=_external_inputs(plane=plane,plan=plan,draft=draft,payloads=payloads,read_only=True)
    reference=owner.scope_reference(selected.scope)
    assert reader._scope_input(plane,plan,reference,current_inputs=current)==selected.scope
    # The ordinary public reader supplies this already authenticated tuple.
    # The domain callback must use it without re-enumerating/hash-scanning it.
    from empirical_lawhood.api import recursive_execution
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    instance=decode_canonical_bytes(payloads['experiment-instance.json'],ExperimentInstanceBinding,maximum_bytes=None)
    with monkeypatch.context() as check:
        check.setattr(recursive_execution,'_external_inputs',lambda **kwargs:pytest.fail('domain reader repeated shared external input hashing'))
        observed=[]
        def consume(**kwargs):
            observed.append(kwargs['reconstruct'])
            return kwargs['current_inputs']
        check.setattr(reader,'_replay',consume)
        from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
        for mode in ('off','full'):
            with scientific_reconstruction_operation(mode):
                actual=reader.read_development_result(directory=directory,artifact_writer=plane,specification=result.target_specification,
                    instance=instance,payloads=payloads,report={'status':'SUCCEEDED'},products={'receipts':{},'external_inputs':current},
                    draft=draft,plan=plan)
                assert actual is current
        assert observed==[False,True]
    with pytest.raises(PermissionError,match='actual authored input custody'):
        reader._scope_input(plane,plan,reference)
    scope_task=next(task for task in plan.tasks if any(row.external_input_id==owner.scope_input(reference) for row in task.scientific_inputs))
    scope_edge=next(row for row in scope_task.scientific_inputs if row.external_input_id==owner.scope_input(reference))
    for damage in ('scientific-bound','external-size'):
        if damage=='scientific-bound':
            changed=replace(scope_task,scientific_inputs=tuple(replace(row,maximum_size_bytes=row.maximum_size_bytes-1)
                if row is scope_edge else row for row in scope_task.scientific_inputs))
        else:
            changed=replace(scope_task,external_inputs=tuple(replace(row,expected_size_bytes=1)
                if row.logical_artifact_id==reference.scope.object_id else row for row in scope_task.external_inputs))
        forged=replace(plan,tasks=tuple(changed if task is scope_task else task for task in plan.tasks))
        with pytest.raises(PermissionError,match='external byte/access'):
            reader._graph(result.target_specification,copied.method_inputs,draft,forged)
    scope_input=next(row for row in current if row.logical.logical_artifact_id==reference.scope.object_id)
    path=plane.root.resolve(scope_input.materialization.relative_path,for_write=False)
    original=path.read_bytes()
    monkeypatch.setattr(reader,'authenticate_original_full_factor_reference',
        lambda **kwargs:pytest.fail('damaged consumed scope reached original producer replay'))
    try:
        path.write_bytes(original+b'\n')
        # Count placeholders never stand in for successful receipts: the exact
        # consumed FILE must refuse before original or output receipt replay.
        with pytest.raises((ValueError,PermissionError,RuntimeError)):
            reader._replay(writer=plane,specification=result.target_specification,inputs=copied.method_inputs,
                draft=draft,plan=plan,receipts={task:object() for task in tasks},codecs={},current_inputs=current)
    finally:
        path.write_bytes(original)
