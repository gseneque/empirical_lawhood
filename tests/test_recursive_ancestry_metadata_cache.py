# SPDX-License-Identifier: MPL-2.0
"""Cache accounting/lifetime controls; no new scientific qualification."""

from dataclasses import dataclass
from pathlib import Path
import sys
from types import MappingProxyType, SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_contributions as owner
from empirical_lawhood.api.retained_read_metadata import retained_metadata_bytes, copy_metadata_containers
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records import decoded_record_store
from empirical_lawhood.science.records.serialization import _CanonicalRope


def _result(*, physical_bytes=2 * 1024**3, body=None):
    record = ObjectIdentity('exposed.cache-record', 'empirical-lawhood/testing/cache-record', '1.0.0', '0' * 64)
    transport = SimpleNamespace(members=(SimpleNamespace(size_bytes=physical_bytes),))
    report = {'status': 'SUCCEEDED', 'nested': [{'value': 1}]}
    products = {'records': {'task': {'output': record}}, 'body': body}
    return Path('/exposed/contribution'), transport, record, report, products, object(), record


def test_actual_retained_graph_not_external_closure_bytes_controls_admission():
    checks = []
    result = _result()
    with owner.recursive_contribution_read_context() as reading:
        reading.retain('one', result, lambda: checks.append('fresh guard'), reuse_eligible=lambda: True, roots=(result[-1],))
        assert len(reading.entries) == 1
        assert 0 < reading.bytes < 64 * 1024
        assert reading.get('one') == result
        assert checks == ['fresh guard']
    assert reading.bytes == 0 and not reading.entries and not reading.active


def test_pure_policy_invalidation_is_a_cache_miss_with_live_custody_guards():
    checks, eligible = [], True
    with owner.recursive_contribution_read_context() as reading:
        reading.lifetime.callback(checks.append, 'final custody')
        reading.retain('one', _result(), lambda: checks.append('current custody'),
            roots=(), reuse_eligible=lambda: eligible)
        eligible = False
        assert reading.get('one') is None and not reading.entries and reading.bytes == 0
        assert checks == ['current custody']
    assert checks == ['current custody', 'final custody']


def test_cache_copies_caller_projections_and_preserves_exact_typed_objects():
    result = _result()
    with owner.recursive_contribution_read_context() as reading:
        reading.retain('one', result, lambda: None, reuse_eligible=lambda: True, roots=(result[-1],))
        result[3]['nested'][0]['value'] = 99
        result[4]['records'].clear()
        first = reading.get('one')
        assert first[3]['nested'][0]['value'] == 1
        assert first[4]['records']['task']['output'] is result[-1]
        first[3]['nested'].clear()
        first[4]['records'].clear()
        second = reading.get('one')
        assert second[3]['nested'] == [{'value': 1}]
        assert second[4]['records']['task']['output'] is result[-1]
        assert first[5] is second[5] is result[5]


def test_retained_byte_capacity_and_lru_evict_only_metadata(monkeypatch):
    result = _result(body=b'x' * 16_384)
    checks = []
    with owner.recursive_contribution_read_context() as reading:
        monkeypatch.setattr(decoded_record_store, 'MAX_SHARED_RECORD_BYTES', 1024)
        reading.retain('large', result, lambda: None, reuse_eligible=lambda: True, roots=())
        assert not reading.entries
        monkeypatch.setattr(decoded_record_store, 'MAX_SHARED_RECORD_BYTES', 1024**2)
        monkeypatch.setattr(decoded_record_store, 'MAX_SHARED_RECORDS', 1)
        reading.lifetime.callback(checks.append, 'complete original byte guard')
        reading.retain('one', _result(), lambda: None, reuse_eligible=lambda: True, roots=())
        before = reading.bytes
        reading.retain('one', _result(), lambda: None, reuse_eligible=lambda: True, roots=())
        assert reading.bytes == before  # replacement cannot leak the old charge
        reading.retain('two', _result(), lambda: None, reuse_eligible=lambda: True, roots=())
        assert reading.get('one') is None and reading.get('two') is not None
        assert len(reading.entries) == 1 and reading.bytes <= 1024**2
    assert checks == ['complete original byte guard']


def test_graph_counts_shared_canonical_buffers_once_including_inherited_slots():
    record = _result()[-1]
    raw = b'x' * 16_384
    rope = _CanonicalRope((raw, raw), len(raw) * 2)
    object.__setattr__(record, '_canonical_encoding', rope)
    size = retained_metadata_bytes((record, record), maximum_bytes=1024**2)
    assert size is not None and len(raw) < size < 2 * len(raw)
    assert retained_metadata_bytes(record, maximum_bytes=len(raw)) is None


def test_actual_decoded_validation_lifetime_is_counted_without_disabling_cache():
    from empirical_lawhood.science.records.decoding import record_validation_scope
    from empirical_lawhood.science.records.decoded_record_store import decoded_record_scope, decode_scoped_canonical_bytes
    original = _result()[-1]
    with record_validation_scope(), decoded_record_scope():
        record = decode_scoped_canonical_bytes(original.canonical_bytes(), ObjectIdentity, maximum_bytes=None)
        assert hasattr(record, '_canonical_validation')
        size = retained_metadata_bytes(record, maximum_bytes=1024**2)
        assert size is not None and size > sys.getsizeof(record)
        result = _result(body=record)
        with owner.recursive_contribution_read_context() as reading:
            reading.retain('decoded', result, lambda: None, reuse_eligible=lambda: True, roots=(record,))
            assert reading.entries and reading.get('decoded')[4]['body'] is record


def test_mapping_proxy_accounts_for_backing_dictionary_capacity_and_contents():
    mapping = {str(index): index for index in range(30)}
    proxy = MappingProxyType(mapping)
    size = retained_metadata_bytes(proxy, maximum_bytes=1024**2)
    assert size >= sys.getsizeof(proxy) + sys.getsizeof(mapping)
    clone = copy_metadata_containers(proxy)
    mapping['new'] = 'changed original'
    assert 'new' not in clone


def test_graph_bounds_counting_work_and_rejects_unknown_data_without_reading_it():
    class Unknown:
        @property
        def body(self):
            pytest.fail('cache accounting executed a data property')
    assert retained_metadata_bytes(Unknown(), maximum_bytes=1024**2) is None
    assert retained_metadata_bytes(tuple(range(100)), maximum_bytes=1024**2, maximum_objects=10) is None
    deeply_nested = None
    for _ in range(2000):
        deeply_nested = (deeply_nested,)
    assert retained_metadata_bytes(deeply_nested, maximum_bytes=1024**2) is not None


def test_unknown_callable_cannot_hide_mutable_buffers_from_cache_accounting():
    class CallableBuffer:
        def __init__(self):
            self.payload = bytearray(8192)
        def __call__(self):
            return self.payload
    value = CallableBuffer()
    assert retained_metadata_bytes(value, maximum_bytes=1024) is None
    assert retained_metadata_bytes(value, maximum_bytes=1024**2) is None
    result = _result(body=value)
    with owner.recursive_contribution_read_context() as reading:
        reading.retain('callable', result, lambda: None, reuse_eligible=lambda: True, roots=())
        assert not reading.entries


def test_partial_bindings_are_measured_and_snapshot_mutable_arguments():
    from functools import partial
    value = partial(len, bytearray(8192))
    assert retained_metadata_bytes(value, maximum_bytes=1024) is None
    assert retained_metadata_bytes(value, maximum_bytes=1024**2) is not None
    clone = copy_metadata_containers(value)
    value.args[0].append(0)
    assert clone() == 8192 and value() == 8193


def test_callback_policy_snapshots_in_place_mapping_and_partial_keyword_changes():
    from functools import partial
    from empirical_lawhood.api.recursive_inquiry_read import _factory_read_policy
    bindings = {'callback': partial(pow, exp=2), 'codecs': {'one': ObjectIdentity}}
    first = _factory_read_policy(bindings)
    bindings['callback'].keywords['exp'] = 3
    assert _factory_read_policy(bindings) != first
    second = _factory_read_policy(bindings)
    bindings['codecs']['two'] = ObjectIdentity
    assert _factory_read_policy(bindings) != second


def test_generated_frozen_constructor_captures_are_counted_but_mutable_closures_refuse():
    assert ObjectIdentity.__init__.__closure__
    assert retained_metadata_bytes(ObjectIdentity.__init__, maximum_bytes=1024**2) is not None
    mutable = bytearray(8192)
    def captures_mutable():
        return mutable
    assert retained_metadata_bytes(captures_mutable, maximum_bytes=1024**2) is None


def test_tuple_subclasses_with_mutable_children_do_not_enter_snapshot_cache():
    class ExtraTuple(tuple):
        pass
    result = _result(body=ExtraTuple(([1, 2],)))
    with owner.recursive_contribution_read_context() as reading:
        reading.retain('tuple-subclass', result, lambda: None, reuse_eligible=lambda: True, roots=())
        assert not reading.entries


def test_projection_beyond_copy_recursion_capacity_keeps_uncached_route():
    value = None
    for _ in range(2000):
        value = (value,)
    with owner.recursive_contribution_read_context() as reading:
        reading.retain('deep', _result(body=value), lambda: None, reuse_eligible=lambda: True, roots=())
        assert not reading.entries


def test_mutable_dataclass_is_not_admitted_as_an_immutable_cache_projection():
    @dataclass
    class Mutable:
        value: int
    result = _result(body=Mutable(1))
    with owner.recursive_contribution_read_context() as reading:
        reading.retain('mutable', result, lambda: None, reuse_eligible=lambda: True, roots=())
        assert not reading.entries


def test_frozen_metadata_snapshot_includes_nonfield_mutable_attributes():
    @dataclass(frozen=True)
    class ExtraMetadata:
        value: int
    original = ExtraMetadata(1)
    object.__setattr__(original, 'extra', ['original'])
    clone = copy_metadata_containers(original)
    original.extra.append('changed')
    assert clone.extra == ['original']


def test_private_slot_storage_is_counted_and_copied():
    @dataclass(frozen=True)
    class PrivateMetadata:
        __slots__ = ('value', '__extra')
        value: int
    original = PrivateMetadata(1)
    object.__setattr__(original, '_PrivateMetadata__extra', bytearray(8192))
    assert retained_metadata_bytes(original, maximum_bytes=1024) is None
    clone = copy_metadata_containers(original)
    original._PrivateMetadata__extra[0] = 99
    assert clone._PrivateMetadata__extra[0] == 0


def test_forked_process_context_cannot_inherit_live_ancestry_owner(monkeypatch):
    with owner.recursive_contribution_read_context() as original:
        process = original.process
        monkeypatch.setattr(owner.os, 'getpid', lambda: process + 1)
        assert owner._current_contribution_reads() is None
        with pytest.raises(ValueError, match='escaped'):
            original.require_current()
        with owner.recursive_contribution_read_context() as child:
            assert child is not original and child.process == process + 1
        monkeypatch.undo()
