# SPDX-License-Identifier: MPL-2.0
"""Parsed-document canonical parity without mutable scientific records."""

from decimal import Decimal
import json

import pytest

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.serialization import CanonicalizationError, canonical_json_bytes, canonical_json_document_bytes
from empirical_lawhood.planning.study_issue import SelectedSourceManifest, SelectedSourceManifestMember


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
