# SPDX-License-Identifier: MPL-2.0
"""Cross-reader typed reuse preserves custody, limits and record lifetimes."""

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass, replace
from decimal import localcontext
import gc
import sys
from typing import ClassVar
from weakref import ref

import pytest

from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
from empirical_lawhood.api.selected_e4_bank_recipe import _read_exact_record
from empirical_lawhood.infrastructure.bounded_io import BoundedFileIOError
from empirical_lawhood.infrastructure.canonical_record_read import read_verified_canonical_record
from empirical_lawhood.infrastructure.publication_metadata import read_published_canonical_record
from empirical_lawhood.kernel import decoding
from empirical_lawhood.kernel.decoded_record_store import (
    DecodedRecordStore, current_decoded_record_store, decode_scoped_canonical_bytes,
    decoded_record_scope, record_store_key,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from tests.test_artifact_publication_admission import _plane, _requests


@contextmanager
def _decodes(kind):
    calls = []
    def observe(frame, event, _arg):
        if (event == 'call' and frame.f_code is decoding._decode_canonical_bytes.__code__
                and frame.f_locals['record_type'] is kind):
            calls.append(kind)
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield calls
    finally:
        sys.setprofile(previous)


@dataclass(frozen=True, slots=True)
class Child(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/shared-decode-child'
    count: int

    def __post_init__(self):
        if self.count < 0:
            raise ValueError('negative child')


@dataclass(frozen=True, slots=True)
class Parent(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/shared-decode-parent'
    child: Child


@dataclass(frozen=True, slots=True)
class Mutable(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/shared-decode-mutable'
    values: Mapping[str, int]


def test_three_reader_families_share_content_across_actual_publications(tmp_path, record_property):
    plane = _plane(tmp_path / 'shared')
    first, second = _requests(2)
    second = replace(second, payload=first.payload)
    publications = plane.write_batch((first, second))
    manifests = tuple(plane.read_manifest(value.materialization.relative_path) for value in publications)
    with plane.read_context() as writer, _decodes(ObjectIdentity) as calls:
        reader = CurrentResultPlanReader(writer)
        original = reader.read_control(manifests[0], ObjectIdentity, len(first.payload))
        exact = _read_exact_record(writer, publications[1], ObjectIdentity)
        published = read_published_canonical_record(writer, publications[0], ObjectIdentity)
        supplied = decode_scoped_canonical_bytes(first.payload, ObjectIdentity, maximum_bytes=len(first.payload))
        assert original is exact is published is supplied
        assert len(calls) == 1
        assert current_decoded_record_store().hits >= 3
    with plane.read_context() as writer:
        fresh = read_verified_canonical_record(writer, manifests[0], ObjectIdentity, maximum_bytes=len(first.payload))
        assert fresh == original and fresh is not original
    record_property('cross_reader_work', dict(readers=4, distinct_publications=2, typed_decodes=1))


@pytest.mark.parametrize('damage', ('bytes', 'sibling', 'revoked', 'smaller-limit'))
def test_shared_value_never_replaces_current_publication_or_consumer_checks(tmp_path, damage):
    plane = _plane(tmp_path / 'refusal')
    requests = _requests(2)
    publications = plane.write_batch(requests)
    manifests = tuple(plane.read_manifest(value.materialization.relative_path) for value in publications)
    allowed = True
    def access(_manifest):
        if not allowed:
            raise PermissionError('current access revoked')
    errors = (ValueError, RuntimeError, PermissionError, BoundedFileIOError)
    with pytest.raises(errors):
        with plane.read_context(before_member=access) as writer:
            reader = CurrentResultPlanReader(writer)
            original = reader.read_control(manifests[0], ObjectIdentity, len(requests[0].payload))
            assert original is not None
            if damage == 'revoked':
                allowed = False
            elif damage != 'smaller-limit':
                target = manifests[damage == 'sibling'].materialization.relative_path
                path = plane.root.resolve(target, for_write=False)
                path.write_bytes(b'[' + path.read_bytes()[1:])
            bound = 1 if damage == 'smaller-limit' else len(requests[0].payload)
            reader.read_control(manifests[0], ObjectIdentity, bound)


def test_descendant_validator_decimal_and_lifetime_are_part_of_typed_proof(monkeypatch):
    original = Parent(Child(3))
    raw = original.canonical_bytes()
    with decoded_record_scope(), _decodes(Parent) as calls:
        first = decode_scoped_canonical_bytes(raw, Parent, maximum_bytes=len(raw))
        assert decode_scoped_canonical_bytes(raw, Parent, maximum_bytes=len(raw)) is first
        with localcontext() as context:
            context.prec += 1
            assert decode_scoped_canonical_bytes(raw, Parent, maximum_bytes=len(raw)) is not first
        assert len(calls) == 2
        def reject(_record):
            raise ValueError('changed child validator')
        monkeypatch.setattr(Child, '__post_init__', reject)
        with pytest.raises(ValueError, match='changed child validator'):
            decode_scoped_canonical_bytes(raw, Parent, maximum_bytes=len(raw))


def test_weak_store_does_not_extend_record_lifetime_and_eviction_is_not_refusal():
    store = DecodedRecordStore(maximum_records=1, maximum_bytes=4096)
    first, second = Child(1), Child(2)
    first_key = record_store_key(Child, first.fingerprint(), first.canonical_size_bytes())
    second_key = record_store_key(Child, second.fingerprint(), second.canonical_size_bytes())
    store.put(first_key, first)
    store.put(second_key, second)
    assert store.get(first_key) is None and store.get(second_key) is second
    observed = ref(second)
    del second
    gc.collect()
    assert observed() is None and not store.records and store.bytes == 0
    store.put(first_key, first)
    store.close()
    assert store.get(first_key) is None and not store.records
    too_small = DecodedRecordStore(maximum_bytes=1)
    too_small.put(first_key, first)
    assert not too_small.records


def test_mutable_records_and_custom_encodings_never_enter_shared_store():
    first = Mutable({'value': 1})
    with decoded_record_scope() as store:
        key = record_store_key(Mutable, first.fingerprint(), first.canonical_size_bytes())
        store.put(key, first)
        first.values['value'] = 2
        assert store.get(key) is None and not store.records
    class Custom(Child):
        def canonical_bytes(self):
            return super().canonical_bytes()
    assert record_store_key(Custom, 'a' * 64, 1) is None


def test_exception_expires_shared_scope_even_when_consumer_retains_record():
    raw = Child(1).canonical_bytes()
    with pytest.raises(RuntimeError):
        with decoded_record_scope() as store:
            retained = decode_scoped_canonical_bytes(raw, Child, maximum_bytes=len(raw))
            raise RuntimeError('consumer failed')
    assert not store.active and not store.records and current_decoded_record_store() is None
    with decoded_record_scope():
        assert decode_scoped_canonical_bytes(raw, Child, maximum_bytes=len(raw)) is not retained
