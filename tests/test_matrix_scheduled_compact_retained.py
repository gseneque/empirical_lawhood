# SPDX-License-Identifier: MPL-2.0
"""Cold compact input custody over exposed static software declarations."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import (
    NAMESPACE, ScheduledCompactBank, ScheduledCompactCommitmentConfig,
    compact_identity, compact_native_contract,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.retained_bindings import _shared_inputs, _native, _route
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex, ScheduledNativeSourceContext
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from tests.test_matrix_scheduled_history_bindings import (
    bank as bank, provenance as provenance, scheduled as scheduled, stock as stock, finish, write,
)
from tests.test_matrix_scheduled_compact_workers import compact_prefix_case


def test_compact_retained_route_preserves_subject_and_actual_configuration(bank, monkeypatch):
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments, parameter_source
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore

    def blocked(*args, **kwargs):
        pytest.fail('cold compact route entered a native source or contact')

    monkeypatch.setattr(parameter_history_segments, 'acquire_parameter_segment', blocked)
    monkeypatch.setattr(parameter_source, 'acquire_parameter_history', blocked)
    monkeypatch.setattr(ExternalNativeSubworkStore, 'begin', blocked)
    _, _, original = bank
    shared = ScheduledCompactBank.from_commitment(original)
    declaration = ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', shared)
    root = shared.selected_root_ids[0]
    index = ScheduledSourceIndex.from_shared(reservation=shared.reservation,
        specification=shared.specification, provenances=shared.provenances)
    source = index.resolve(next(s for s in shared.sources if s.root_id == root))
    route = _route(declaration, root, source)
    config = route.config('prefix')
    assert route.namespace == NAMESPACE
    assert route.commitment == original
    assert identity(route.source) == source.reference.identity
    assert compact_identity(config) == compact_native_contract(source, 'prefix', bank=shared)[0]
    assert route.task_id('prefix') == compact_native_contract(source, 'prefix', bank=shared)[1]
    assert route.committed().configuration == compact_identity(declaration)
    foreign = replace(shared, bank_id=shared.bank_id+'.foreign')
    with pytest.raises(ValueError, match='configuration|shared operands'):
        ScheduledNativeSourceContext(source, config, foreign)


@pytest.mark.parametrize('defect', (None, 'missing-bank', 'foreign-bank', 'wrong-source-codec', 'foreign-descriptor'))
def test_compact_cold_inputs_require_actual_shared_bank_and_descriptor(bank, defect):
    plane, _, original = bank
    shared = ScheduledCompactBank.from_commitment(original)
    declaration = ScheduledCompactCommitmentConfig('config.'+NAMESPACE+'.commit', shared)
    route = _route(declaration, shared.selected_root_ids[0])
    records = {'bank': shared, 'source': route.source.reference}
    if defect == 'missing-bank':
        records.pop('bank')
    elif defect == 'foreign-bank':
        records['bank'] = replace(shared, bank_id=shared.bank_id+'.foreign')
    elif defect == 'wrong-source-codec':
        records['source'] = shared.reservation
    elif defect == 'foreign-descriptor':
        records['source'] = next(s for s in shared.sources if s.root_id != route.source.root_id)
    manifests, specs = [], []
    for name, record in records.items():
        logical_id = shared.bank_id if name == 'bank' else route.source.source_id
        manifests.append(write(plane, logical_id, record.canonical_bytes(), record.SCHEMA))
        specs.append(SimpleNamespace(input_id=name, logical_artifact_id=logical_id))
    for manifest in manifests:
        plane.verify_manifest(manifest)
    task = SimpleNamespace(external_inputs=tuple(specs))
    if defect is None:
        _shared_inputs(plane, task, tuple(manifests), route, 'numerical')
    else:
        with pytest.raises(ValueError, match='compact retained'):
            _shared_inputs(plane, task, tuple(manifests), route, 'numerical')


@pytest.mark.parametrize('missing_receipt', (False, True))
def test_actual_compact_native_custody_read_never_repairs_receipts(bank, monkeypatch, missing_receipt):
    """Actual compact prefix custody exercises the shared retained native reader."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledPrefixHistory

    case = compact_prefix_case(bank)
    history = decode_canonical_bytes(next(row.payload for row in case.result.outputs
        if row.output_id.endswith('.product')), ScheduledPrefixHistory, maximum_bytes=None)
    receipt, _ = finish(case.plane, case.context, case.result, case.source)
    root = Path(case.plane.root.contract.canonical_path)
    nested = history.native.receipt
    relative = f'runs/{nested.run_id}/receipts/{nested.task_id}/{nested.attempt_id}.json'
    if missing_receipt:
        for suffix in ('', '.manifest.json'):
            (root / (relative + suffix)).unlink()
    before = {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob('*') if p.is_file()}

    def blocked(*args, **kwargs):
        pytest.fail('compact retained native read entered mutation or recovery')

    monkeypatch.setattr(ExternalNativeEffectContactStore, 'begin', blocked)
    monkeypatch.setattr(ExternalTaskReceiptStore, 'commit', blocked)
    for name in ('begin', 'contact', 'freeze_roster', 'publish_output', 'complete', 'recover'):
        monkeypatch.setattr(ExternalNativeSubworkStore, name, blocked)
    with case.plane.read_context() as reading:
        def read():
            return _native(reading, case.plan, case.task, receipt, case.inputs, history.native,
                access=OutcomeAccess.OUTCOME_BLIND, visibility=VisibilityCeiling.PROSPECTIVE)

        if missing_receipt:
            with pytest.raises(ValueError, match='original nested completion'):
                read()
        else:
            native = read()
            inspected = native.inspect(history.native.definition)
            assert inspected.state is NativeSubworkState.COMPLETED
            assert inspected.receipt == history.native.receipt
            assert inspected.completion == history.native.completion
            raw = b''.join(native.iter_completed_output(history.native.definition, 'arrays'))
            assert sha256(raw).hexdigest() == history.arrays.array_artifact.sha256
    assert before == {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob('*') if p.is_file()}
