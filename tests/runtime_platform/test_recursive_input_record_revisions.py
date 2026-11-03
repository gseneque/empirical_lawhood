# SPDX-License-Identifier: MPL-2.0
"""Exact old/new input revisions without global output aliases or native entry."""

from dataclasses import dataclass, replace
from decimal import Decimal
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_record_codecs import (
    input_record_type_census, resolve_recursive_input_codec, validate_input_record_types,
)
from tests.runtime_platform.test_recursive_compiler import fixture


@dataclass(frozen=True, slots=True)
class Earlier(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/revisioned-scientific-input'
    record_id: str
    value: int


@dataclass(frozen=True, slots=True)
class Current(CanonicalRecord):
    SCHEMA: ClassVar[str] = Earlier.SCHEMA
    VERSION: ClassVar[str] = '1.1.0'
    record_id: str
    value: int
    uncertainty: Decimal


@dataclass(frozen=True, slots=True)
class ForeignMeaning(CanonicalRecord):
    SCHEMA: ClassVar[str] = Earlier.SCHEMA
    record_id: str
    different_meaning: str


def _selected(types=(Earlier, Current), *, second_types=None):
    draft, registrations, _ = fixture()
    original = registrations[0]
    registration = replace(original, input_ports=(RecursivePortContract('history', Earlier.SCHEMA,
        'application/json', 4096),), input_record_types=types)
    operations = (SimpleNamespace(node_id='consumer-a', selection=registration.selection),)
    links = (SimpleNamespace(consumer_node_id='consumer-a', external_input_id='original-history'),)
    selected = ('consumer-a',)
    result = (registration,)
    if second_types is not None:
        second = replace(registrations[1], input_ports=registration.input_ports, input_record_types=second_types)
        operations += (SimpleNamespace(node_id='consumer-b', selection=second.selection),)
        links += (SimpleNamespace(consumer_node_id='consumer-b', external_input_id='original-history'),)
        selected += ('consumer-b',)
        result += (second,)
    return (SimpleNamespace(operations=operations, links=links, selected_operation_ids=selected),
            SimpleNamespace(input_id='original-history', payload_schema=Earlier.SCHEMA), result)


def _decode(record, *, types=(Earlier, Current), second_types=None, payload=None, fallback=None):
    draft, external, registrations = _selected(types, second_types=second_types)
    raw = record.canonical_bytes() if payload is None else payload
    codec = resolve_recursive_input_codec(draft=draft, external=external, registrations=registrations,
        fallback_codecs={} if fallback is None else fallback, payload=raw)
    return decode_canonical_bytes(raw, codec, maximum_bytes=4096)


@pytest.mark.parametrize('record', (Earlier('original.old', 3), Current('original.current', 3, Decimal('.25'))))
def test_closed_input_revisions_decode_without_entering_global_output_map(record):
    raw = record.canonical_bytes()
    decoded = _decode(record)
    assert type(decoded) is type(record)
    assert decoded.canonical_bytes() == raw
    assert decoded.fingerprint() == record.fingerprint()


def test_strict_legacy_single_codec_remains_supported():
    original = Earlier('original.old', 3)
    assert _decode(original, types=(), fallback={Earlier.SCHEMA: Earlier}) == original


@pytest.mark.parametrize('record_types', ([Earlier], (object,), (Earlier, Earlier), (Current, Earlier), (Earlier, ForeignMeaning)))
def test_invalid_or_ambiguous_declared_codec_census_refuses(record_types):
    with pytest.raises((ValueError, TypeError)):
        validate_input_record_types(record_types)


def test_input_revision_cannot_be_widened_by_a_global_output_codec():
    original = Current('original.current', 3, Decimal('.25'))
    with pytest.raises(ValueError, match='outside'):
        _decode(original, types=(Earlier,), fallback={Current.SCHEMA: Current})


def test_every_consumer_must_accept_the_original_revision():
    original = Current('original.current', 3, Decimal('.25'))
    with pytest.raises(ValueError, match='outside'):
        _decode(original, second_types=(Earlier,))
    assert _decode(original, second_types=(Earlier, Current)) == original


def test_same_schema_and_revision_cannot_have_two_installed_meanings():
    _, _, registrations = _selected((Earlier,), second_types=(ForeignMeaning,))
    with pytest.raises(ValueError, match='disagree'):
        input_record_type_census(registrations, legacy_codecs={})


def test_different_revisions_are_distinct_input_codecs():
    _, _, registrations = _selected((Earlier,), second_types=(Current,))
    assert input_record_type_census(registrations, legacy_codecs={}) == (Earlier, Current)


def test_registration_refuses_unbound_input_codec_schema():
    _, _, registrations = _selected()
    with pytest.raises(ValueError, match='undeclared'):
        replace(registrations[0], input_ports=())


@pytest.mark.parametrize('damage', ('unknown-revision', 'foreign-schema', 'extra-field', 'duplicate-key', 'binary-number'))
def test_envelope_selection_does_not_replace_strict_canonical_decoding(damage):
    original = Earlier('original.old', 3)
    raw = original.canonical_bytes()
    if damage == 'unknown-revision':
        raw = raw.replace(b'1.0.0', b'9.0.0')
    elif damage == 'foreign-schema':
        raw = raw.replace(Earlier.SCHEMA.encode(), b'empirical-lawhood/testing/foreign')
    elif damage == 'extra-field':
        raw = raw.replace(b'"value":3', b'"extra":1,"value":3')
    elif damage == 'duplicate-key':
        raw = raw.replace(b'"value":3', b'"value":3,"value":3')
    else:
        raw = raw.replace(b'"value":3', b'"value":3.0')
    assert raw != original.canonical_bytes()
    with pytest.raises((ValueError, TypeError)):
        _decode(original, payload=raw)
