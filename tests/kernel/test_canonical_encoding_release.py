# SPDX-License-Identifier: MPL-2.0
"""Derived caches can be forgotten without changing scientific bytes or fields."""
from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum
from hashlib import sha256
import json
from types import MappingProxyType
from typing import ClassVar

import pytest

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import CanonicalRecord, release_canonical_encodings


@dataclass(frozen=True, slots=True)
class Node(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/released-encoding'
    text: str
    children: tuple['Node', ...] = ()
    amount: Decimal = Decimal('123456789012345678901234567890.12500')


def independent_bytes(value):
    return (json.dumps(value.to_document(), sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode()


def test_complete_shared_graph_preserves_fields_exact_bytes_size_and_identity():
    leaf = Node('"\\\n\u00e9'*(24*1024))
    parent = Node('parent', (leaf,))
    root = Node('root', (parent, leaf, parent))
    expected = independent_bytes(root)
    assert root.canonical_bytes() == expected
    original_fields = (root.children, parent.children, leaf.text, leaf.amount)
    with localcontext() as context:
        context.prec = 5
        assert release_canonical_encodings(root) == 3
        assert all(not hasattr(row, '_canonical_encoding') for row in (root, parent, leaf))
        assert release_canonical_encodings(root) == 0
        assert root.children is original_fields[0] and parent.children is original_fields[1]
        assert leaf.text is original_fields[2] and leaf.amount is original_fields[3]
        assert root.canonical_bytes() == expected
        assert root.fingerprint() == sha256(expected).hexdigest()
        assert root.canonical_size_bytes() == len(expected)
        assert b''.join(root.canonical_chunks()) == expected
        assert decode_canonical_bytes(expected, Node, maximum_bytes=len(expected)) == root


def test_existing_fragment_reader_survives_cache_release():
    child = Node('x'*(128*1024))
    root = Node('root', (child,)*4)
    expected = root.canonical_bytes()
    fragments = root.canonical_chunks()
    first = next(fragments)
    assert release_canonical_encodings(root) == 2
    assert first+b''.join(fragments) == expected
    assert root.canonical_bytes() == expected


@pytest.mark.parametrize('proxy', [False, True])
def test_uncached_mapping_parent_releases_children_and_still_reflects_mutation(proxy):
    @dataclass(frozen=True)
    class WithMapping(CanonicalRecord):
        SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/released-mapping'
        values: object

    child = Node('original')
    backing = {'child': child}
    root = WithMapping(MappingProxyType(backing) if proxy else backing)
    expected = root.canonical_bytes()
    assert not hasattr(root, '_canonical_encoding')
    assert release_canonical_encodings(root) == 1
    assert root.values['child'] is child
    assert root.canonical_bytes() == expected
    backing['new'] = Node('later')
    assert root.canonical_bytes() == independent_bytes(root) != expected


def test_frozenset_and_enum_members_release_without_encoding_or_field_changes():
    left, right = Node('left'), Node('right')
    class Wrapped(Enum):
        CHILD = left
    values = (frozenset((left, right)), Wrapped.CHILD, left)
    left_expected, right_expected = left.canonical_bytes(), right.canonical_bytes()
    assert release_canonical_encodings(values) == 2
    assert values[1].value is left
    assert left.canonical_bytes() == left_expected and right.canonical_bytes() == right_expected


def test_custom_encoder_is_not_invoked_and_cyclic_mapping_terminates():
    calls = []
    class Custom(Node):
        def canonical_bytes(self):
            calls.append(self.text)
            return b'custom encoding\n'
    child = Node('child')
    custom = Custom('custom', (child,))
    expected = child.canonical_bytes()
    cycle = {'custom': custom}
    cycle['cycle'] = cycle
    assert release_canonical_encodings(cycle) == 1
    assert calls == [] and child.canonical_bytes() == expected
    assert custom.canonical_bytes() == b'custom encoding\n'
    assert calls == ['custom']


def test_nonrecord_leaves_are_not_inspected_or_changed():
    class Opaque:
        def __iter__(self):
            pytest.fail('opaque value was traversed')
    leaf = Opaque()
    assert release_canonical_encodings((None, 'text', Decimal('2.00'), leaf)) == 0
