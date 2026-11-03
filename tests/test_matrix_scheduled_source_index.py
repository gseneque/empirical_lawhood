# SPDX-License-Identifier: MPL-2.0
"""Current source identity and complete-roster guards over exposed inputs."""

from dataclasses import replace
from hashlib import sha256
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import records
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import (
    NAMESPACE, ScheduledCompactBank, ScheduledCompactConfig, compact_identity,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import (
    ScheduledNativeSourceContext, ScheduledSourceIndex,
)
from tests.test_matrix_scheduled_history_bindings import (
    bank as bank, provenance as provenance, scheduled as scheduled, stock as stock,
)


def _index(shared):
    return ScheduledSourceIndex.from_shared(reservation=shared.reservation,
        specification=shared.specification, provenances=shared.provenances)


def test_audit_source_join_keeps_exact_size_and_digest_without_repeated_byte_copies(bank):
    _, sources, config = bank
    audit = config.audit
    raw = audit.canonical_bytes()
    assert audit.fingerprint() == sha256(raw).hexdigest()
    copies = []

    def observe(frame, event, arg):
        if (event == 'call' and frame.f_code is CanonicalRecord.canonical_bytes.__code__
                and frame.f_locals.get('self') is audit):
            copies.append(frame.f_code.co_name)

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        for source in sources:
            audit.validate_source(source)
            records._publication(config.audit_publication, audit)
    finally:
        sys.setprofile(previous)
    assert not copies
    assert audit.canonical_bytes() == raw
    source = sources[0]
    declared = source.allocation.exposure
    for change in ({'size_bytes': len(raw) + 1}, {'sha256': 'f' * 64}):
        # Isolate this pure declaration join. No foreign source is admitted by
        # the actual source-index, custody, access or execution owners.
        changed = SimpleNamespace(allocation=SimpleNamespace(exposure=replace(declared,
            scheduled_audit=replace(declared.scheduled_audit, **change))))
        with pytest.raises(ValueError, match='audit/corpus bytes'):
            audit.validate_source(changed)


@pytest.mark.parametrize('damage', ('missing', 'reordered', 'duplicate', 'stream', 'coordinate', 'group'))
def test_shared_index_requires_complete_exact_root_and_stream_roster(bank, damage):
    shared = ScheduledCompactBank.from_commitment(bank[2])
    index = _index(shared)
    references = shared.sources
    if damage == 'missing':
        changed = references[:-1]
    elif damage == 'reordered':
        changed = tuple(reversed(references))
    elif damage == 'duplicate':
        changed = (*references[:-1], references[0])
    else:
        reference = references[-1]
        root = reference.root
        if damage == 'stream':
            stream = replace(root.streams[0], digest_sha256='b'*64)
            root = replace(root, streams=(stream, *root.streams[1:]))
        elif damage == 'coordinate':
            root = replace(root, coordinate=replace(root.coordinate, object_fingerprint='b'*64))
        else:
            root = replace(root, root=replace(root.root, independent_group_id='group.foreign'))
        changed = (*references[:-1], replace(reference, root=root))
    with pytest.raises(ValueError, match='roster|roots|root|scientific parents'):
        index.require_roster(changed, expected_root_ids=index.root_ids)
    index.require_roster(references, expected_root_ids=index.root_ids)


def test_leaf_serialization_and_native_context_do_not_rebuild_shared_population(bank, monkeypatch):
    shared = ScheduledCompactBank.from_commitment(bank[2])
    index = _index(shared)
    expected = tuple(reference.canonical_bytes() for reference in shared.sources)
    # Materialize exact immutable parent identities before installing the guard.
    bank_pin = compact_identity(shared)
    assert index.reservation_identity == records.identity(shared.reservation)

    def forbidden(*args, **kwargs):
        raise AssertionError('leaf work traversed or serialized the full shared population')

    monkeypatch.setattr(records.ScheduledAllocation, '__post_init__', forbidden)
    monkeypatch.setattr(records.ScheduledReservation, 'canonical_bytes', forbidden)
    monkeypatch.setattr(records.ScheduledSpecification, 'canonical_bytes', forbidden)
    monkeypatch.setattr(ScheduledSourceIndex, 'from_shared', forbidden)
    for reference, raw in zip(shared.sources, expected, strict=True):
        resolved = index.resolve(reference)
        assert reference.canonical_bytes() == raw
        assert records.identity(resolved) == reference.identity
        config = ScheduledCompactConfig('config.'+NAMESPACE+'.'+reference.root_id+'.prefix',
            'prefix', reference, bank_pin)
        context = ScheduledNativeSourceContext(resolved, config, shared)
        contract = context.contract('prefix')
        assert contract[0] == compact_identity(config)
        assert reference.identity in contract[3]
        assert not hasattr(resolved, 'canonical_bytes')
