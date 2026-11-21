# SPDX-License-Identifier: MPL-2.0
"""Parsed-document canonical parity without mutable scientific records."""

from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import json
from typing import ClassVar

import pytest

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.science.records import serialization
from empirical_lawhood.science.records.serialization import CanonicalRecord, CanonicalizationError, canonical_json_bytes, canonical_json_document_bytes
from empirical_lawhood.design.study_issue import SelectedSourceManifest, SelectedSourceManifestMember


@pytest.mark.parametrize('value', ((), {'nested': ({'decimal': '0.00100'}, None, True, 3, 'café')},
    SelectedSourceManifest('manifest.exposed', '1'*40, '2'*64, '3'*64,
        (SelectedSourceManifestMember('src/selected.py', '100644', 4, '4'*64),))))
def test_decoded_json_arrays_retain_exact_original_canonical_bytes(value):
    raw = canonical_json_bytes(value)
    assert canonical_json_document_bytes(json.loads(raw)) == raw


@pytest.mark.parametrize('value', (1.25, float('nan'), {'value': [2.5]}, {1: 'wrong-key'}, Decimal('1'),
    ObjectIdentity('record.exposed', 'empirical-lawhood/testing/exposed', '1.0.0', '1'*64)))
def test_parsed_document_helper_rejects_non_json_and_binary_floats(value):
    with pytest.raises(CanonicalizationError, match='decoded canonical JSON'):
        canonical_json_document_bytes(value)


def test_scientific_serializer_still_refuses_mutable_lists():
    with pytest.raises(CanonicalizationError, match='unsupported canonical value type: list'):
        canonical_json_bytes({'scientific-values': [1, 2]})


def test_api_report_mixed_containers_and_enum_keep_the_same_encoded_json_and_decimal_text():
    report = {'status': OperationalStatus.SUCCEEDED,
        'phases': ({'values': [{'decimal': '0.00500'}, None, True, 3]},)}
    parsed = {'status': 'SUCCEEDED', 'phases': [{'values': [{'decimal': '0.00500'}, None, True, 3]}]}
    assert canonical_json_document_bytes(report) == canonical_json_document_bytes(parsed)
    assert json.loads(canonical_json_document_bytes(report)) == parsed
    assert canonical_json_bytes({'status': OperationalStatus.SUCCEEDED}) == canonical_json_document_bytes(
        {'status': OperationalStatus.SUCCEEDED})


@pytest.mark.parametrize('base, value', ((str, 'text'), (int, 3), (list, [1]),
    (tuple, (1,)), (dict, {'a': 1})))
def test_document_projection_does_not_widen_accepted_container_or_scalar_types(base, value):
    class Custom(base):
        pass

    with pytest.raises(CanonicalizationError, match='decoded canonical JSON'):
        canonical_json_document_bytes({'nested': [Custom(value)]})


def test_document_projection_keeps_unicode_escaping_order_and_enum_container_values():
    class Projection(Enum):
        VALUES = ('café', [None, True, {'z': 2, 'a': '\n'}])

    document = {'z': Projection.VALUES, 'a': {'decimal': '-0.00100'}}
    expected = {'a': {'decimal': '-0.00100'}, 'z': ['café', [None, True, {'a': '\n', 'z': 2}]]}
    raw = (json.dumps(expected, sort_keys=True, ensure_ascii=True,
        separators=(',', ':')) + '\n').encode()
    assert canonical_json_document_bytes(document) == raw
    assert document['z'] is Projection.VALUES


def test_cached_document_metadata_preserves_fresh_containers_and_current_envelope(monkeypatch):
    @dataclass(frozen=True, slots=True)
    class Pair(CanonicalRecord):
        SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/document-pair'
        zeta: ObjectIdentity
        alpha: ObjectIdentity

    identity = ObjectIdentity('record.exposed', 'empirical-lawhood/testing/exposed',
        '1.0.0', '1' * 64)
    record = Pair(identity, identity)
    document = record.to_document()
    again = record.to_document()
    assert list(document['value']) == ['zeta', 'alpha']
    assert document == again
    assert document is not again
    assert document['value']['zeta'] is not document['value']['alpha']
    document['value']['zeta']['value']['object_id'] = 'changed'
    assert record.to_document() == again
    monkeypatch.setattr(Pair, 'SCHEMA', 'not-a-schema')
    with pytest.raises(ValueError, match='invalid schema'):
        record.to_document()
    monkeypatch.setattr(Pair, 'SCHEMA', 'empirical-lawhood/testing/document-pair')
    monkeypatch.setattr(Pair, 'VERSION', 'invalid')
    with pytest.raises(ValueError, match='invalid semantic version'):
        record.to_document()
    monkeypatch.setattr(Pair, 'VERSION', '1.0.0')

    def reject_schema(_schema):
        raise ValueError('changed envelope validator')

    monkeypatch.setattr(serialization, 'validate_schema', reject_schema)
    with pytest.raises(ValueError, match='changed envelope validator'):
        record.to_document()
