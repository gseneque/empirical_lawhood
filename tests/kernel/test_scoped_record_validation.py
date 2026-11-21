# SPDX-License-Identifier: MPL-2.0
"""Construction reuse never suppresses new context, mutation or local checks."""
from collections import OrderedDict
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import dataclass, replace
from decimal import Decimal, Inexact, localcontext
import multiprocessing
from typing import ClassVar
from weakref import ref

import pytest

from empirical_lawhood.science.records import decoding
from empirical_lawhood.science.records.decoding import decode_canonical_bytes, record_validation_scope, validate_record_fields
from empirical_lawhood.science.records.serialization import CanonicalRecord, CanonicalizationError


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


def test_unscoped_validation_does_not_construct_an_unused_policy_signature(monkeypatch):
    child = Child(Decimal(1))

    def unexpected_key():
        raise RuntimeError('policy signature')

    monkeypatch.setattr(decoding, 'decimal_context_key', unexpected_key)
    validate_record_fields(child)
    with record_validation_scope(), pytest.raises(RuntimeError, match='policy signature'):
        validate_record_fields(child)
    object.__setattr__(child, 'value', Decimal(-1))
    with pytest.raises(ValueError, match='negative child'):
        validate_record_fields(child)


def test_decimal_signature_tracks_every_setting_and_trap_but_not_sticky_flags():
    with localcontext() as context:
        baseline = decoding.decimal_context_key()
        context.flags[Inexact] = not context.flags[Inexact]
        assert decoding.decimal_context_key() == baseline
        for signal in context.traps:
            original = context.traps[signal]
            context.traps[signal] = not original
            assert decoding.decimal_context_key() != baseline
            context.traps[signal] = original
        for field, value in (('prec', context.prec + 1), ('rounding', 'ROUND_DOWN'),
                ('Emin', context.Emin + 1), ('Emax', context.Emax - 1),
                ('clamp', 1 - context.clamp), ('capitals', 1 - context.capitals)):
            original = getattr(context, field)
            if value == original:
                continue
            setattr(context, field, value)
            assert decoding.decimal_context_key() != baseline
            setattr(context, field, original)
        assert decoding.decimal_context_key() == baseline


def test_copied_closed_context_cannot_reuse_its_intrinsic_proof_or_decode_memo(monkeypatch):
    child = Child(Decimal(1))
    calls = []
    original = Child.__post_init__

    def observed(value):
        calls.append(value)
        original(value)

    monkeypatch.setattr(Child, '__post_init__', observed)
    token = decoding._decoded_validations.set(OrderedDict())
    try:
        with record_validation_scope():
            validate_record_fields(child)
            copied = copy_context()
    finally:
        decoding._decoded_validations.reset(token)
    copied.run(validate_record_fields, child)
    assert len(calls) == 2

    def fresh():
        with record_validation_scope():
            validate_record_fields(child)
            validate_record_fields(child)

    copied.run(fresh)
    assert len(calls) == 3


def test_copied_thread_gets_fresh_intrinsic_proofs_and_keeps_parent_active(monkeypatch):
    child = Child(Decimal(1))
    calls = []
    original = Child.__post_init__

    def observed(value):
        calls.append(value)
        original(value)

    monkeypatch.setattr(Child, '__post_init__', observed)
    token = decoding._decoded_validations.set(OrderedDict())
    try:
        with record_validation_scope():
            validate_record_fields(child)
            parent = decoding._record_validation_lifetime.get()

            def independent():
                validate_record_fields(child)
                with record_validation_scope():
                    current = decoding._record_validation_lifetime.get()
                    assert current is not parent
                    validate_record_fields(child)
                    validate_record_fields(child)

            with ThreadPoolExecutor(max_workers=1) as threads:
                threads.submit(copy_context().run, independent).result(timeout=5)
            assert parent.active
            validate_record_fields(child)
            validate_record_fields(child)
    finally:
        decoding._decoded_validations.reset(token)
    # The child's distinct record-local entry cannot overwrite the parent's
    # decoder memo; that still-owned memo supplies the final parent proof.
    assert len(calls) == 3


@pytest.mark.skipif('fork' not in multiprocessing.get_all_start_methods(), reason='requires fork')
def test_forked_process_gets_fresh_intrinsic_validation_lifetime(monkeypatch):
    child = Child(Decimal(1))
    calls = []
    original = Child.__post_init__

    def observed(value):
        calls.append(value)
        original(value)

    monkeypatch.setattr(Child, '__post_init__', observed)
    context = multiprocessing.get_context('fork')
    receiver, sender = context.Pipe(duplex=False)
    with record_validation_scope():
        validate_record_fields(child)
        parent = decoding._record_validation_lifetime.get()

        def independent():
            try:
                validate_record_fields(child)
                with record_validation_scope():
                    current = decoding._record_validation_lifetime.get()
                    validate_record_fields(child)
                    validate_record_fields(child)
                    sender.send((current is not parent, len(calls)))
            finally:
                sender.close()

        process = context.Process(target=independent)
        process.start()
        sender.close()
        try:
            assert receiver.poll(5)
            assert receiver.recv() == (True, 3)
            process.join(5)
            assert process.exitcode == 0
        finally:
            if process.is_alive():
                process.terminate()
                process.join(5)
            receiver.close()
        assert parent.active
        validate_record_fields(child)
    assert len(calls) == 1
