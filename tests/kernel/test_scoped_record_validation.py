# SPDX-License-Identifier: MPL-2.0
"""Construction reuse never suppresses new context, mutation or local checks."""
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass, replace
from decimal import Decimal, Inexact, localcontext
from typing import ClassVar
from weakref import ref

import pytest

from empirical_lawhood.kernel import decoding
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, record_validation_scope, validate_record_fields
from empirical_lawhood.kernel.serialization import CanonicalRecord, CanonicalizationError


@dataclass(frozen=True, slots=True)
class Child(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/scoped-child'
    value: Decimal

    def __post_init__(self):
        if +self.value < 0:
            raise ValueError('negative child')


@dataclass(frozen=True, slots=True)
class Parent(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/scoped-parent'
    children: tuple[Child, ...]
    expected: Decimal
    low_precision: bool = False

    def __post_init__(self):
        for child in self.children:
            validate_record_fields(child)
            if child.value != self.expected:
                raise ValueError('wrong operand join')
        if self.low_precision:
            with localcontext() as context:
                context.prec = 3
                context.traps[Inexact] = True
                validate_record_fields(self.children[0])


@dataclass(frozen=True, slots=True)
class MutableChild(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/scoped-mutable-child'
    values: Mapping[str, int]

    def __post_init__(self):
        if self.values['value'] < 0:
            raise ValueError('negative mutable child')


def test_shared_immutable_child_validates_once_per_decode_and_again_after_exit(monkeypatch):
    leaf = Child(Decimal('1.2345'))
    raw = Parent((leaf,) * 12, leaf.value).canonical_bytes()
    calls = []
    original = Child.__post_init__
    original_interner = decoding.ParsedNodeInterner
    interners = []

    def observed_interner():
        value = original_interner()
        interners.append(ref(value))
        return value

    def observed(self):
        assert interners and all(value() is None for value in interners)
        calls.append(self)
        original(self)

    monkeypatch.setattr(decoding, 'ParsedNodeInterner', observed_interner)
    monkeypatch.setattr(Child, '__post_init__', observed)
    result = decode_canonical_bytes(raw, Parent, maximum_bytes=len(raw))
    assert len(calls) == 1
    assert result.canonical_bytes() == raw
    assert decoding._decoded_validations.get() is None
    validate_record_fields(result.children[0])
    assert len(calls) == 2
    object.__setattr__(result.children[0], 'value', Decimal(-1))
    with pytest.raises(ValueError, match='negative child'):
        validate_record_fields(result.children[0])
    with pytest.raises(CanonicalizationError, match='wrong operand join'):
        decode_canonical_bytes(raw.replace(b'"expected":{"decimal":"1.2345"}',
            b'"expected":{"decimal":"2"}'), Parent, maximum_bytes=len(raw))
    with pytest.raises(CanonicalizationError, match='Decimal arithmetic'):
        decode_canonical_bytes(raw.replace(b'"low_precision":false', b'"low_precision":true'),
            Parent, maximum_bytes=len(raw))


def test_mutable_children_are_not_memoized_and_local_memo_is_bounded(monkeypatch):
    original = MutableChild.__post_init__
    calls = []

    def observed(self):
        calls.append(self)
        original(self)

    monkeypatch.setattr(MutableChild, '__post_init__', observed)
    # Mutable mappings have no typed decoder contract. Exercise their local
    # validator directly inside the same finite memo, without widening decoding.
    token = decoding._decoded_validations.set(OrderedDict())
    try:
        mutable = MutableChild({'value': 1})
        validate_record_fields(mutable)
        validate_record_fields(mutable)
        assert not decoding._decoded_validations.get()
        assert len(calls) == 3
        mutable.values['value'] = -1
        with pytest.raises(ValueError, match='negative mutable child'):
            validate_record_fields(mutable)
    finally:
        decoding._decoded_validations.reset(token)
    monkeypatch.setattr(decoding, '_MAX_LOCAL_VALIDATIONS', 1)
    leaf = Child(Decimal(1))
    raw = Parent((leaf,) * 3, leaf.value).canonical_bytes()
    original_remember = decoding._remember_local_validation
    sizes = []

    def remember(*args):
        original_remember(*args)
        sizes.append(len(decoding._decoded_validations.get()))

    monkeypatch.setattr(decoding, '_remember_local_validation', remember)
    assert decode_canonical_bytes(raw, Parent, maximum_bytes=len(raw)).canonical_bytes() == raw
    assert sizes and max(sizes) == 1


def test_finite_operation_reuses_more_than_memo_capacity_but_rechecks_each_parent(monkeypatch):
    children = tuple(Child(Decimal(1)) for _ in range(4200))
    calls = []
    original = Child.__post_init__

    def observed(value):
        calls.append(value)
        original(value)

    monkeypatch.setattr(Child, '__post_init__', observed)
    with record_validation_scope():
        for _ in range(3):
            Parent(children, Decimal(1))
        assert len(calls) == len(children)
        with pytest.raises(ValueError, match='wrong operand join'):
            Parent(children, Decimal(2))
        with pytest.raises(ValueError, match='negative child'):
            replace(children[0], value=Decimal(-1))
    with record_validation_scope():
        Parent(children, Decimal(1))
    assert len(calls) == 2 * len(children) + 1


def test_operation_reuse_keeps_validator_decimal_mutability_and_exception_boundaries(monkeypatch):
    child = Child(Decimal('1.2345'))
    original = Child.__post_init__
    with pytest.raises(RuntimeError, match='consumer'):
        with record_validation_scope():
            validate_record_fields(child)
            with record_validation_scope():
                validate_record_fields(child)
            with localcontext() as context:
                context.prec = 3
                context.traps[Inexact] = True
                with pytest.raises(Inexact):
                    validate_record_fields(child)
            def refused(value):
                raise ValueError('replacement validator')
            monkeypatch.setattr(Child, '__post_init__', refused)
            with pytest.raises(ValueError, match='replacement validator'):
                validate_record_fields(child)
            monkeypatch.setattr(Child, '__post_init__', original)
            mutable = MutableChild({'value': 1})
            validate_record_fields(mutable)
            mutable.values['value'] = -1
            with pytest.raises(ValueError, match='negative mutable'):
                validate_record_fields(mutable)
            raise RuntimeError('consumer')
    assert decoding._record_validation_lifetime.get() is None
    assert not child._canonical_validation[0].active
    object.__setattr__(child, 'value', Decimal(-1))
    with pytest.raises(ValueError, match='negative child'):
        validate_record_fields(child)


def test_validation_lifetime_keeps_no_records_alive():
    @dataclass(frozen=True, slots=True, weakref_slot=True)
    class WeakChild(CanonicalRecord):
        SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/weak-child'
        value: int

        def __post_init__(self):
            if self.value < 0:
                raise ValueError('negative')

    with record_validation_scope():
        child = WeakChild(1)
        validate_record_fields(child)
        reference = ref(child)
        del child
        assert reference() is None
