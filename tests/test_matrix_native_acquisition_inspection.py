# SPDX-License-Identifier: MPL-2.0
"""Pure inspection-policy controls; actual store I/O is covered by existing native lifecycle controls."""
from types import SimpleNamespace
import pytest
from empirical_lawhood.api.matrix_native_acquisition_replay import inspect_native
from empirical_lawhood.runtime.native_subwork import NativeSubworkState


@pytest.mark.parametrize("state", tuple(NativeSubworkState))
def test_nonentry_requires_actual_not_entered_state_without_promoting_uncertainty(state):
    definition = object()
    completion = object()
    observed = SimpleNamespace(state=state, definition=definition, completion=completion, receipt=None)
    calls = []
    def actual(value):
        calls.append(value)
        return observed
    store = SimpleNamespace(inspect=actual)
    # Forensic callers retain the exact uncertain observation, even if an
    # authenticated completion is present without its required nested receipt.
    assert inspect_native(store=store, definition=definition) is observed
    if state is NativeSubworkState.NOT_ENTERED:
        assert inspect_native(store=store, definition=definition, require_nonentry=True) is observed
    else:
        with pytest.raises(PermissionError, match="nonentry contradicts"):
            inspect_native(store=store, definition=definition, require_nonentry=True)
    assert calls == [definition, definition]


@pytest.mark.parametrize("defect", (None, "state", "definition", "completion", "receipt"))
def test_scientific_completed_event_requires_all_exact_actual_store_joins(defect):
    definition, completion, receipt = object(), object(), object()
    event = SimpleNamespace(definition=definition, completion=completion, receipt=receipt)
    observed = SimpleNamespace(state=NativeSubworkState.COMPLETED,
        definition=definition, completion=completion, receipt=receipt)
    if defect == "state":
        observed.state = NativeSubworkState.UNKNOWN_COMPLETION
    elif defect is not None:
        setattr(observed, defect, object())
    store = SimpleNamespace(inspect=lambda value: observed)
    if defect is None:
        assert inspect_native(store=store, definition=definition, event=event) is observed
    else:
        with pytest.raises(PermissionError, match="completed definition/completion/receipt"):
            inspect_native(store=store, definition=definition, event=event)
