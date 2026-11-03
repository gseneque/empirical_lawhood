# SPDX-License-Identifier: MPL-2.0
"""Disclosed small in-memory native/progress controls; no fresh campaign contact."""
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from empirical_lawhood.adapters.methods.matrix_scheduled_history import parameter_native
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.kernel.time import validate_utc_timestamp
from tests.test_matrix_parameter_compact_history import selected
from tests.test_matrix_scheduled_history import prefix_case, scheduled as scheduled  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import stock as stock, provenance as provenance  # noqa: F401


def test_real_segment_progress_preserves_arrays_and_exact_generator_continuation():
    _,allocation,_=selected();coordinate=allocation.coordinates[0];streams=allocation.roots[0].streams
    terminal=states=None
    for start,stop in ((0,3),(3,6),(6,8)):
        expected=segments.acquire_parameter_segment(coordinate,streams,start,stop,
            terminal=terminal,generator_states=states)
        counts=[]
        actual=segments.acquire_parameter_segment(coordinate,streams,start,stop,
            terminal=terminal,generator_states=states,progress=counts.append)
        assert counts==list(range(3,3*(stop-start)+1,3))
        assert actual.generators==expected.generators
        assert all(actual.arrays[name].tobytes()==expected.arrays[name].tobytes() for name in expected.arrays)
        assert all(actual.terminal_arrays[name].tobytes()==expected.terminal_arrays[name].tobytes()
            for name in expected.terminal_arrays)
        terminal,states=actual.terminal_arrays,actual.generators


def test_segment_progress_never_counts_a_failed_or_unexecuted_step(monkeypatch):
    _,allocation,_=selected();coordinate=allocation.coordinates[0];streams=allocation.roots[0].streams
    advance=segments.advance_parameter_pair
    def fail_second(*args,**kwargs):
        if kwargs['coarse_step']==2:raise FloatingPointError('disclosed failed second integration pair')
        return advance(*args,**kwargs)
    monkeypatch.setattr(segments,'advance_parameter_pair',fail_second)
    counts=[]
    with pytest.raises(FloatingPointError,match='failed second'):
        segments.acquire_parameter_segment(coordinate,streams,0,3,progress=counts.append)
    assert counts==[3]


def test_parameter_native_bridge_emits_decimal_actual_work_and_preserves_exact_archives(scheduled):
    plane,sources=scheduled;source=sources[0]
    history,_,_,_,_,expected,_,_=prefix_case(plane,source)
    definition=history.native.definition
    outputs={};events=[];call_observations=[];entry=object();roster=object()
    root=Path(plane.root.contract.canonical_path)
    before={path.relative_to(root):path.read_bytes() for path in root.rglob('*') if path.is_file()}
    class InMemoryCustody:
        # Deliberately no store or real contact: this is disclosed adapter plumbing.
        def recover(self,actual):
            assert actual==definition
            return None
        def inspect(self,actual):
            assert actual==definition
            return SimpleNamespace(state=NativeSubworkState.NOT_ENTERED)
        def freeze_roster(self,actual,*,definitions):
            assert actual is roster and definitions==(definition,)
        def begin(self,actual):
            assert actual==definition
            return entry
        def contact(self,actual):assert actual is entry
        def call_entry(self,actual,*,at_utc):
            assert actual is entry
            call_observations.append(("entry",validate_utc_timestamp(at_utc),None))
        def call_return(self,actual,*,at_utc,error_type=None):
            assert actual is entry
            call_observations.append(("return",validate_utc_timestamp(at_utc),error_type))
        def publish_output(self,actual,name,chunks,**kwargs):
            assert actual is entry
            assert tuple(row[0] for row in call_observations)==("entry","return")
            assert call_observations[-1][2] is None
            raw=b''.join(chunks)
            assert (len(raw),sha256(raw).hexdigest())==(kwargs['expected_size_bytes'],kwargs['expected_physical_sha256'])
            outputs[name]=raw
        def complete(self,actual,**kwargs):
            assert actual is entry
            assert kwargs['consumed_streams']==history.native.completion.consumed_streams
            return SimpleNamespace(state=NativeSubworkState.COMPLETED,receipt=history.native.receipt,
                completion=history.native.completion)
    work=SimpleNamespace(expected_parent=definition.parent_contact,definitions=(definition,),rosters=(roster,))
    raw,arrays,checkpoint,_,_=parameter_native.execute_parameter_native_work(source,work,InMemoryCustody(),
        prefix_only=True,start=0,stop=source.policy.cutoff_tick,progress=SimpleNamespace(advance=events.append))
    assert events==[Decimal(value) for value in range(3,3*source.policy.cutoff_tick+1,3)]
    assert all(type(value) is Decimal for value in events)
    assert raw==expected==outputs['arrays'] and checkpoint.canonical_bytes()==outputs['checkpoint']
    assert arrays['primary_ticks'][-1]==source.policy.cutoff_tick
    assert {path.relative_to(root):path.read_bytes() for path in root.rglob('*') if path.is_file()}==before


def test_completed_parameter_recovery_enters_no_acquisition_or_progress(scheduled,monkeypatch):
    plane,sources=scheduled;source=sources[0]
    history,_,_,_,_,raw,_,_=prefix_case(plane,source)
    definition=history.native.definition
    completed=SimpleNamespace(state=NativeSubworkState.COMPLETED,receipt=history.native.receipt,
        completion=history.native.completion)
    def forbidden(*args,**kwargs):pytest.fail('completed recovery entered native work or emitted new progress')
    monkeypatch.setattr(segments,'acquire_parameter_segment',forbidden)
    class Recovered:
        def recover(self,actual):
            assert actual==definition
            return completed
        def iter_completed_output(self,actual,output):
            assert actual==definition
            yield raw if output=='arrays' else history.checkpoint.canonical_bytes()
        inspect=freeze_roster=begin=contact=call_entry=call_return=complete=forbidden
    work=SimpleNamespace(expected_parent=definition.parent_contact,definitions=(definition,))
    actual,arrays,checkpoint,original,replayed=parameter_native.execute_parameter_native_work(
        source,work,Recovered(),prefix_only=True,start=0,stop=source.policy.cutoff_tick,
        progress=SimpleNamespace(advance=forbidden))
    assert actual==raw and checkpoint==history.checkpoint and original==definition and replayed is completed
    assert arrays['primary_ticks'][-1]==source.policy.cutoff_tick
    assert arrays['fine_ticks'][-1]==2*source.policy.cutoff_tick


@pytest.mark.parametrize('owner_name',('native_utility_bindings','native_training_bindings'))
@pytest.mark.parametrize('phase',('prefix','responses'))
def test_selected_native_facades_forward_the_actual_task_progress_before_any_helper_entry(monkeypatch,owner_name,phase):
    from importlib import import_module
    owner=import_module('empirical_lawhood.adapters.methods.matrix_factor_response.'+owner_name)
    runner_type=owner.NativeUtilityNativeRunner if owner_name=='native_utility_bindings' else owner.NativeTrainingNativeRunner
    progress=object();source=object();work=object();prefix=object();frozen=object()
    config=SimpleNamespace(protocol=object(),panels=(),specification=object())
    records={name:SimpleNamespace(disposition='AVAILABLE') for name in ('history','causal','physical')}
    monkeypatch.setattr(owner,'_decode',lambda *args:(config,None,source,records,{}))
    monkeypatch.setattr(owner,'_native_work',lambda *args:(work,prefix,frozen))
    monkeypatch.setattr(runner_type,'_response_arrays',lambda self,context:(prefix,frozen))
    class Forwarded(Exception):pass
    def stop_at_helper(actual_source,actual_work,_native_subwork,**kwargs):
        assert actual_source is source and actual_work is work and kwargs['progress'] is progress
        raise Forwarded
    source=SimpleNamespace(policy=SimpleNamespace(cutoff_tick=6))
    monkeypatch.setattr(owner,'execute_parameter_native_work' if phase=='prefix' else 'execute_paired_response_native_work',stop_at_helper)
    context=SimpleNamespace(input_ports=(),output_ports=(SimpleNamespace(profile=ArtifactProfile.MATRIX_ARRAY_NPZ,
        logical_artifact_id='disclosed.progress.output'),))
    with pytest.raises(Forwarded):
        runner_type(phase).execute_with_native_subwork(context,SimpleNamespace(parent_contact=object()),progress=progress)
