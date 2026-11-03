# SPDX-License-Identifier: MPL-2.0
"""Encoding storage complexity and exact independent byte contracts."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class Nested(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/nested-encoding'
    text: str
    children: tuple['Nested', ...]
    amount: Decimal = Decimal('1.2500')


def _storage(records):
    seen, count, pending = set(), 0, [row._canonical_encoding for row in records]
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, bytes):
            count += len(value)
        else:
            pending.extend(value.parts)
    return count


def test_large_nested_records_share_encoding_storage_without_changing_bytes():
    leaf = Nested('x' * (256 * 1024), ())
    records = [leaf]
    for _ in range(32):
        records.append(Nested('parent', (records[-1],)))
    root = records[-1]
    expected = (json.dumps(root.to_document(), sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()
    assert root.canonical_bytes() == expected
    assert root.fingerprint() == sha256(expected).hexdigest()
    assert decode_canonical_bytes(expected, Nested, maximum_bytes=len(expected)) == root
    # Storage follows the unique large leaf plus small ancestor delimiters,
    # rather than 33 complete copies of the growing canonical document.
    assert _storage(records) < 2 * len(leaf.canonical_bytes())
    before = _storage(records)
    for _ in range(3):
        assert root.canonical_bytes() == expected
        assert root.fingerprint() == sha256(expected).hexdigest()
    assert _storage(records) == before


def test_repeated_large_child_has_one_retained_encoding():
    leaf = Nested('"\\\n\u00e9' * (32 * 1024), ())
    root = Nested('parent', (leaf,) * 16)
    expected = (json.dumps(root.to_document(), sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()
    assert root.canonical_bytes() == expected
    assert root.fingerprint() == sha256(expected).hexdigest()
    assert _storage((root, leaf)) < 2 * len(leaf.canonical_bytes())


def test_encoding_and_exact_comparison_hash_only_requested_record_identities(monkeypatch):
    from empirical_lawhood.kernel import serialization

    leaf = Nested('x' * (128 * 1024), ())
    records = [leaf]
    for _ in range(24):
        records.append(Nested('parent', (records[-1],)))
    root = records[-1]
    expected = (json.dumps(root.to_document(), sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode()
    expected_digest = sha256(expected).hexdigest()
    calls = []
    original = serialization.hashlib.sha256

    def counted(*args, **kwargs):
        calls.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(serialization.hashlib, 'sha256', counted)
    assert root.canonical_bytes() == expected
    assert root.canonical_size_bytes() == len(expected)
    assert root.canonical_equals(expected)
    assert not calls
    assert root.fingerprint() == expected_digest
    assert root.fingerprint() == expected_digest
    assert len(calls) == 1
    assert leaf.fingerprint() == original(leaf.canonical_bytes()).hexdigest()
    assert len(calls) == 2


def test_fragment_size_and_exact_comparison_do_not_flatten(monkeypatch):
    from empirical_lawhood.kernel import serialization

    leaf = Nested('x' * (256 * 1024), ())
    root = Nested('root', (leaf,) * 8)
    expected = root.canonical_bytes()
    # Changing both references preserves the stock-method identity check while
    # proving that size/comparison do not call the materializing method.
    def forbidden(self):
        pytest.fail('size or comparison flattened the canonical document')
    monkeypatch.setattr(CanonicalRecord, 'canonical_bytes', forbidden)
    monkeypatch.setattr(serialization, '_STANDARD_CANONICAL_BYTES', forbidden)
    assert root.canonical_size_bytes() == len(expected)
    assert b''.join(root.canonical_chunks()) == expected
    assert root.canonical_equals(expected)
    for changed in (expected[:-1], expected + b'\n', expected.replace(b'root', b'ROOT')):
        assert not root.canonical_equals(changed)


def test_fragment_methods_preserve_custom_encoding_and_mutable_fields():
    class Custom(Nested):
        def canonical_bytes(self):
            return b'custom encoding\n'
    custom = Custom('ignored', ())
    assert custom.canonical_size_bytes() == len(custom.canonical_bytes())
    assert b''.join(custom.canonical_chunks()) == custom.canonical_bytes()
    assert custom.canonical_equals(custom.canonical_bytes())
    assert custom.fingerprint() == sha256(custom.canonical_bytes()).hexdigest()
    assert custom.fingerprint() == sha256(b'custom encoding\n').hexdigest()

    @dataclass(frozen=True)
    class Mutable(CanonicalRecord):
        SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/mutable-encoding'
        values: dict[str, int]

    value = Mutable({'a': 1})
    original = value.canonical_bytes()
    value.values['new'] = 123
    assert not value.canonical_equals(original)
    assert value.canonical_equals(value.canonical_bytes())
    assert value.canonical_size_bytes() == len(value.canonical_bytes())
