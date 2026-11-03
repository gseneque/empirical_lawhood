# SPDX-License-Identifier: MPL-2.0
"""Public metadata checks cannot open any blind or sealed batch payload.

These batches are software fixtures and confer no read or issue authority.
"""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.numerical_provenance_fixtures import numerical_plane


def _requests(access):
    requests = []
    for name in ('selected-member', 'sibling-member'):
        record = ObjectIdentity('software.'+name, ObjectIdentity.SCHEMA, '1.0.0', 'a'*64)
        requests.append(ArtifactWriteRequest(logical_artifact_id=record.object_id,
            relative_path='software/metadata/'+name+'.json', payload_schema=record.SCHEMA,
            profile=ArtifactProfile.CANONICAL_JSON, media_type='application/json',
            publication_scope_id='software.public-metadata', publication_scope_relative_root='software/metadata',
            payload=record.canonical_bytes(), visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
            parent_visibility_ceilings=(), outcome_access=access, minimum_free_bytes=1))
    return tuple(requests)


@pytest.fixture(params=(OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED))
def publication_batch(tmp_path, request):
    plane = numerical_plane(tmp_path / 'software-metadata')
    first, second = plane.write_batch(_requests(request.param))
    return plane, first, second


def _block_payload_access(monkeypatch, plane, publications):
    payloads = {plane.root.resolve(value.materialization.relative_path, for_write=False)
                for value in publications}
    original_open = Path.open

    def metadata_only(path, *args, **kwargs):
        if path in payloads:
            pytest.fail('public metadata inspection opened a batch payload')
        return original_open(path, *args, **kwargs)

    def no_verification(*args, **kwargs):
        pytest.fail('public metadata inspection streamed or verified a batch payload')

    monkeypatch.setattr(Path, 'open', metadata_only)
    monkeypatch.setattr(plane, 'verify_manifest', no_verification)
    monkeypatch.setattr(plane, '_verify_manifest_snapshot', no_verification)
    monkeypatch.setattr(plane, '_stream_identity', no_verification)


def test_batch_metadata_never_opens_either_payload(publication_batch, monkeypatch):
    plane, first, second = publication_batch
    _block_payload_access(monkeypatch, plane, (first, second))
    for publication in (first, second):
        actual = read_publication_metadata(plane, publication)
        assert actual.logical == publication.logical
        assert actual.materialization == publication.materialization
        assert len(actual.publication.members) == 2


@pytest.mark.parametrize('mutation', ('missing-marker', 'corrupt-marker', 'substituted-sibling'))
def test_original_batch_metadata_corruption_is_refused_before_payload_access(
        publication_batch, monkeypatch, mutation):
    plane, first, second = publication_batch
    original = read_publication_metadata(plane, first)
    if mutation == 'substituted-sibling':
        path = plane.root.resolve(second.materialization.relative_path+'.manifest.json', for_write=False)
        value = json.loads(path.read_bytes())
        value['value']['materialization']['value']['physical_sha256'] = 'b'*64
        path.write_text(json.dumps(value)+'\n')
    else:
        path = plane.root.resolve(original.publication.commit_marker_relative_path, for_write=False)
        if mutation == 'missing-marker':
            path.unlink()
        else:
            path.write_bytes(b'{}\n')
    _block_payload_access(monkeypatch, plane, (first, second))
    with pytest.raises((ValueError, FileNotFoundError)):
        read_publication_metadata(plane, first)


def test_publisher_refuses_mixed_evidence_batch_before_staging(tmp_path):
    plane = numerical_plane(tmp_path / 'software-metadata')
    first, second = _requests(OutcomeAccess.OUTCOME_BLIND)
    with pytest.raises(ArtifactIdentityConflict, match='mixes evidence classes'):
        plane.write_batch((first, replace(second, outcome_access=OutcomeAccess.EVALUATION_SEALED)))
    assert not any(plane.root.resolve('software/metadata', for_write=False).glob('*.json'))
