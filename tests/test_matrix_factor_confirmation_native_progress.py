# SPDX-License-Identifier: MPL-2.0
"""Disclosed E1 task-telemetry controls, never issue or qualification evidence.

Only entry/decode/return seams are replaced. The real eight-tick native producer
and framework monotone progress emitter run. No scientific receipt is invented.
"""
from decimal import Decimal
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_bindings,operation_bindings
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_source
from empirical_lawhood.infrastructure.execution import _DirectProgressEmitter
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from tests.test_matrix_factor_confirmation_compact_core import compact_case
from tests.test_matrix_factor_confirmation_history import e1 as e1  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance,stock as stock  # noqa: F401


class ProbeComplete(Exception):
    """Stop before any purported scientific publication or completion receipt."""


def _case(fixture_value,compact):
    if compact:
        _,sources=compact_case(fixture_value)
        return compact_bindings,sources[0],compact_bindings.E1CompactNativeRunner('history')
    return operation_bindings,fixture_value[1][0],operation_bindings.E1NativeRunner('history')


def _decode_seams(monkeypatch,owner,source):
    definition=SimpleNamespace(subwork_id='disclosed.progress-only')
    work=SimpleNamespace(definitions=(definition,),rosters=(object(),))
    monkeypatch.setattr(owner,'_decode',lambda *args:(object(),source,{},()))
    monkeypatch.setattr(owner,'_initial_native_work',lambda *args:work)
    return definition


@pytest.mark.parametrize('compact',(False,True))
@pytest.mark.parametrize('emit',(False,True))
def test_actual_native_ticks_reach_framework_emitter_without_changing_arrays(e1,monkeypatch,compact,emit):  # noqa: F811
    owner,source,runner=_case(e1,compact)
    expected=parameter_source.acquire_parameter_history(source.coordinate,source.root.streams)
    _decode_seams(monkeypatch,owner,source)
    observed=[];entry_events=[];captured=[]
    def begin(definition):
        entry_events.append('begin')
        return object()
    native=SimpleNamespace(parent_contact=object(),recover=lambda definition:None,
        inspect=lambda definition:SimpleNamespace(state=NativeSubworkState.NOT_ENTERED),
        freeze_roster=lambda *args,**kwargs:entry_events.append('freeze'),begin=begin,
        contact=lambda entry:entry_events.append('contact'),
        call_entry=lambda entry,**kwargs:entry_events.append('call-entry'),
        call_return=lambda entry,**kwargs:entry_events.append('call-return'))
    def product(selected,arrays,**kwargs):
        assert selected is source
        captured.append(arrays)
        raise ProbeComplete()
    monkeypatch.setattr(owner.science,'array_product',product)
    with pytest.raises(ProbeComplete):
        runner.execute_with_native_subwork(SimpleNamespace(input_ports=()),native,
            _DirectProgressEmitter(observed.append) if emit else None)
    assert entry_events==['freeze','begin','contact','call-entry','call-return']
    assert observed==([Decimal(3*tick) for tick in range(1,source.coordinate.total_ticks+1)] if emit else [])
    assert len(captured)==1 and captured[0].keys()==expected.keys()
    assert all(np.array_equal(captured[0][name],values,equal_nan=True) for name,values in expected.items())


@pytest.mark.parametrize('compact',(False,True))
def test_completed_native_replay_emits_no_acquisition_progress(e1,monkeypatch,compact):  # noqa: F811
    owner,source,runner=_case(e1,compact)
    _decode_seams(monkeypatch,owner,source)
    observed=[]
    def forbidden(*args,**kwargs):
        pytest.fail('completed replay attempted a native contact or reacquisition')
    native=SimpleNamespace(parent_contact=object(),recover=lambda definition:SimpleNamespace(
        state=NativeSubworkState.COMPLETED,receipt=object(),completion=SimpleNamespace(operational_status=OperationalStatus.SUCCEEDED)),
        iter_completed_output=lambda *args:(b'disclosed-retained-custody-seam',),
        inspect=forbidden,freeze_roster=forbidden,begin=forbidden,contact=forbidden)
    def retained(selected,raw):
        assert selected is source and raw==b'disclosed-retained-custody-seam'
        raise ProbeComplete()
    monkeypatch.setattr(owner,'_retained_values',retained)
    monkeypatch.setattr(parameter_source,'acquire_parameter_history',forbidden)
    with pytest.raises(ProbeComplete):
        runner.execute_with_native_subwork(SimpleNamespace(input_ports=()),native,_DirectProgressEmitter(observed.append))
    assert observed==[]
