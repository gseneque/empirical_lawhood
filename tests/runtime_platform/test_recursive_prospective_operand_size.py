# SPDX-License-Identifier: MPL-2.0
"""Exact prospective data transport; no source qualification or authority."""

from dataclasses import replace
from hashlib import sha256

import pytest

from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher
from empirical_lawhood.infrastructure.recursive_prospective_inputs import RecursiveContentInputSupplier
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.plans import ExternalInputSpec
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveOperand
from tests.test_recursive_public_service import _plane


def operand(size):
    return RecursiveProspectiveOperand('source.exact', 'a' * 64, size,
        'empirical-lawhood/testing/large-prospective-source', 'application/json',
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)


@pytest.mark.parametrize('size', (True, False, 0, -1, 1.5, '17'))
def test_physical_size_remains_a_strict_positive_integer(size):
    with pytest.raises(ValueError, match='positive exact physical byte size'):
        operand(size)


def test_large_exact_source_round_trips_through_actual_content_address_and_chunk_supplier(tmp_path):
    raw = canonical_json_bytes({'schema': operand(1).payload_schema, 'payload': 'x' * (17 * 1024**2)})
    selected = replace(operand(len(raw)), content_sha256=sha256(raw).hexdigest())
    assert len(raw) > 16 * 1024**2
    assert decode_canonical_bytes(selected.canonical_bytes(), RecursiveProspectiveOperand,
                                  maximum_bytes=4096) == selected
    plane = _plane(tmp_path / 'large-exact-source')
    publication = ExternalCandidateInputPublisher(plane.root).publish(raw, maximum_bytes=selected.size_bytes)
    assert publication.content_sha256 == selected.content_sha256
    supplier = RecursiveContentInputSupplier(root=plane.root, operands=(selected,))
    spec = ExternalInputSpec('input.source', selected.logical_artifact_id, selected.content_sha256,
        selected.payload_schema, selected.media_type, selected.size_bytes,
        selected.visibility_ceiling, selected.outcome_access, None)
    payload = supplier.resolve_input(spec)
    try:
        chunks = tuple(payload.source.chunks(256 * 1024))
        assert all(0 < len(chunk) <= 256 * 1024 for chunk in chunks)
        assert b''.join(chunks) == raw
    finally:
        payload.source.close()
    for changed in (replace(spec, expected_size_bytes=selected.size_bytes - 1),
                    replace(spec, expected_content_sha256='b' * 64)):
        with pytest.raises(ValueError, match='frozen bytes'):
            supplier.resolve_input(changed)


def test_large_reference_cannot_exceed_its_selected_scientific_input_bound():
    from empirical_lawhood.api.recursive_prospective_authoring import _operands
    from tests.runtime_platform.test_recursive_compiler import prospective_fixture
    from types import SimpleNamespace

    compilation, _, _ = prospective_fixture()
    external, = compilation.selected_scientific_projection.external_inputs
    selected = RecursiveProspectiveOperand(external.logical_artifact_id, external.expected_content_sha256,
        17 * 1024**2, external.payload_schema, external.media_type,
        external.outcome_access, external.visibility_ceiling)
    with pytest.raises(ValueError, match='authored scientific input'):
        _operands(SimpleNamespace(external_operands=(selected,)), compilation)
