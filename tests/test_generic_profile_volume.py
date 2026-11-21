# SPDX-License-Identifier: MPL-2.0
"""Real format validators follow actual extents, not arbitrary payload ceilings."""

from io import BytesIO
import json
from types import SimpleNamespace

import pytest

from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.artifact_validation import ArtifactIdentityConflict, ArtifactProfileValidatorRegistry, validate_jsonl_stream


def test_large_canonical_jsonl_record_retains_sequence_schema_and_exact_extent():
    request = SimpleNamespace(payload_schema='empirical-lawhood/testing/large-jsonl')
    raw = canonical_json_bytes({'schema': request.payload_schema, 'sequence': 0,
        'value': 'x' * (1024**2 + 1), 'version': '1.0.0'})
    assert len(raw) > 1024**2
    validate_jsonl_stream(BytesIO(raw), request, size=len(raw), record_version='1.0.0')
    for changed in (raw[:-1], raw + b'\n', raw.replace(b'"sequence":0', b'"sequence":1')):
        with pytest.raises(ArtifactIdentityConflict):
            validate_jsonl_stream(BytesIO(changed), request, size=len(raw), record_version='1.0.0')
    with pytest.raises(ArtifactIdentityConflict, match='schema'):
        validate_jsonl_stream(BytesIO(raw), SimpleNamespace(payload_schema='foreign'), size=len(raw))


def test_safetensors_sparse_model_exceeds_former_payload_cap_without_heap_population(tmp_path):
    pytest.importorskip('safetensors')
    schema = 'empirical-lawhood/testing/large-safe-model'
    elements = 256 * 1024**2 // 4 + 1
    header = json.dumps({'__metadata__': {'empirical_lawhood_payload_schema': schema},
        'weights': {'dtype': 'F32', 'shape': [elements], 'data_offsets': [0, 4 * elements]}},
        separators=(',', ':')).encode()
    header += b' ' * (-len(header) % 8)
    path = tmp_path / 'large.safetensors'
    with path.open('wb') as handle:
        handle.write(len(header).to_bytes(8, 'little'))
        handle.write(header)
        handle.truncate(8 + len(header) + 4 * elements)
    assert path.stat().st_size > 256 * 1024**2
    ArtifactProfileValidatorRegistry._safetensors_file(path, SimpleNamespace(payload_schema=schema))
    with pytest.raises(ArtifactIdentityConflict, match='schema'):
        ArtifactProfileValidatorRegistry._safetensors_file(path, SimpleNamespace(payload_schema='foreign'))
    with path.open('r+b') as handle:
        handle.write((path.stat().st_size + 1).to_bytes(8, 'little'))
    with pytest.raises(ArtifactIdentityConflict, match='actual byte extent'):
        ArtifactProfileValidatorRegistry._safetensors_file(path, SimpleNamespace(payload_schema=schema))


def test_safetensors_large_metadata_keeps_real_library_and_schema_validation(tmp_path):
    pytest.importorskip('safetensors')
    import numpy as np
    from safetensors.numpy import save

    schema = 'empirical-lawhood/testing/large-safe-header'
    raw = save({'weights': np.array([1.0, 2.0], dtype=np.float32)},
        metadata={'empirical_lawhood_payload_schema': schema, 'description': 'x' * (1024**2 + 1)})
    assert int.from_bytes(raw[:8], 'little') > 1024**2
    request = SimpleNamespace(payload_schema=schema, payload=raw)
    ArtifactProfileValidatorRegistry._safetensors(request)
    path = tmp_path / 'header.safetensors'
    path.write_bytes(raw)
    ArtifactProfileValidatorRegistry._safetensors_file(path, request)
    with pytest.raises(ArtifactIdentityConflict, match='schema'):
        ArtifactProfileValidatorRegistry._safetensors(SimpleNamespace(payload_schema='foreign', payload=raw))


def test_canonical_stream_inspection_reports_actual_chunk_progress():
    from empirical_lawhood.execution.progress import progress_reporting
    from empirical_lawhood.storage.artifact_validation import _CanonicalJsonFileInspector

    schema = 'empirical-lawhood/testing/canonical-progress'
    raw = canonical_json_bytes({'schema': schema, 'value': {'text': 'x' * (2 * 1024**2)}, 'version': '1.0.0'})
    rows, completions = [], []

    class Capture:
        def update(self, **row):
            rows.append(row)

        def step_completed(self, **row):
            completions.append(row)

    with progress_reporting(Capture()):
        header = _CanonicalJsonFileInspector(BytesIO(raw),
            SimpleNamespace(payload_schema=schema, semantic_validation=None), total_bytes=len(raw)).validate()
    assert header.schema == schema
    observed = [row for row in rows if row['phase'] == 'publication.canonical-scan']
    assert len(observed) > 2
    assert observed[0]['done'] == 0 and observed[-1]['done'] == len(raw)
    assert {row['total'] for row in observed} == {len(raw)}
    assert all(row['unit'] == 'bytes' for row in observed)
    assert [row['done'] for row in observed] == sorted(row['done'] for row in observed)
    assert completions[-1]['status'] == 'RETURNED'
