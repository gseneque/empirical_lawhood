# SPDX-License-Identifier: MPL-2.0
"""Finite sharing of already decoded immutable values, never access decisions.

Readers retain their own records and authenticate every selected publication.
This bounded weak index joins those existing lifetimes without keeping a large
scientific body alive after its last consumer releases it.
"""

from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import fields, is_dataclass
from functools import lru_cache
from hashlib import sha256
from threading import RLock
from typing import get_args
from weakref import ref

from .serialization import CanonicalRecord

MAX_SHARED_RECORDS = 4096
MAX_SHARED_RECORD_BYTES = 512 * 1024**2
_current = ContextVar('decoded_record_store', default=None)
_ENCODING_METHODS = tuple((name, getattr(CanonicalRecord, name)) for name in (
    'to_document', 'canonical_bytes', 'canonical_chunks', 'canonical_equals',
    '_encoding', '_is_cacheable', 'fingerprint'))


@lru_cache(maxsize=1024)
def _record_types(record_type):
    """Inspect the closed declared type graph, not a decoded population."""
    from .decoding import record_annotations

    pending, seen, records = [record_type], set(), []
    while pending:
        annotation = pending.pop()
        if annotation in seen:
            continue
        seen.add(annotation)
        if isinstance(annotation, type) and issubclass(annotation, CanonicalRecord):
            if not is_dataclass(annotation):
                return ()
            records.append(annotation)
            annotations = record_annotations(annotation)
            pending.extend(annotations[field.name] for field in fields(annotation))
        else:
            pending.extend(get_args(annotation))
    return tuple(records)


def record_store_key(record_type, digest, size):
    """Bind exact content, all declared record validators and Decimal settings."""
    from . import decoding

    if not isinstance(record_type, type) or not issubclass(record_type, CanonicalRecord):
        return None
    kinds = _record_types(record_type)
    if not kinds or any(getattr(kind, name) is not original
            for kind in kinds for name, original in _ENCODING_METHODS):
        return None
    policy = tuple((kind, kind.SCHEMA, kind.VERSION, kind.__init__, getattr(kind, '__post_init__', None))
        for kind in kinds)
    return (record_type, digest, size, policy, decoding.decimal_context_key(),
        decoding._decode_canonical_bytes, decoding._decode_canonical_document,
        decoding.decode_canonical_record, decoding.validate_document_shape)


class DecodedRecordStore:
    """An eviction-only weak index with an explicit finite owner."""

    def __init__(self, *, maximum_records=MAX_SHARED_RECORDS, maximum_bytes=MAX_SHARED_RECORD_BYTES):
        if (type(maximum_records) is not int or maximum_records <= 0
                or type(maximum_bytes) is not int or maximum_bytes <= 0):
            raise ValueError('decoded record sharing requires positive finite bounds')
        self.maximum_records, self.maximum_bytes = maximum_records, maximum_bytes
        self.active = True
        self.records = OrderedDict()
        self.bytes = 0
        self.hits = self.misses = 0
        self.lock = RLock()

    def get(self, key):
        with self.lock:
            if not self.active or key is None:
                return None
            entry = self.records.get(key)
            record = None if entry is None else entry()
            if record is None:
                self.misses += 1
                return None
            self.hits += 1
            self.records.move_to_end(key)
            return record

    def put(self, key, record):
        if (key is None or type(record) is not key[0] or not record._is_cacheable()
                or record_store_key(type(record), key[1], key[2]) != key):
            return
        size = key[2]
        if size > self.maximum_bytes:
            return

        def released(reference):
            with self.lock:
                if self.records.get(key) is reference:
                    self.records.pop(key)
                    self.bytes -= size

        with self.lock:
            if not self.active:
                return
            if self.records.pop(key, None) is not None:
                self.bytes -= size
            while self.records and (len(self.records) >= self.maximum_records
                    or self.bytes + size > self.maximum_bytes):
                old, _ = self.records.popitem(last=False)
                self.bytes -= old[2]
            self.records[key] = ref(record, released)
            self.bytes += size

    def close(self):
        with self.lock:
            self.active = False
            self.records.clear()
            self.bytes = 0


def current_decoded_record_store():
    store = _current.get()
    return store if store is not None and store.active else None


@contextmanager
def decoded_record_scope():
    """Share exact typed values only within this operation and nested readers."""
    existing = current_decoded_record_store()
    if existing is not None:
        yield existing
        return
    store = DecodedRecordStore()
    token = _current.set(store)
    try:
        yield store
    finally:
        store.close()
        _current.reset(token)


def decode_scoped_canonical_bytes(payload, record_type, *, maximum_bytes):
    """Decode supplied bytes; the caller still owns their access and custody."""
    from .decoding import decode_canonical_bytes
    from .serialization import CanonicalizationError

    store = current_decoded_record_store()
    if store is None:
        return decode_canonical_bytes(payload, record_type, maximum_bytes=maximum_bytes)
    if not isinstance(payload, bytes):
        raise CanonicalizationError('canonical payload must be immutable bytes')
    if maximum_bytes is not None and maximum_bytes <= 0:
        raise ValueError('canonical decode byte limit must be positive')
    if maximum_bytes is not None and len(payload) > maximum_bytes:
        raise CanonicalizationError('canonical payload exceeds its bounded contract')
    key = record_store_key(record_type, sha256(payload).hexdigest(), len(payload))
    record = store.get(key)
    if record is None:
        record = decode_canonical_bytes(payload, record_type, maximum_bytes=maximum_bytes)
        store.put(key, record)
    return record
