# SPDX-License-Identifier: MPL-2.0
"""Exact byte identities with one decoder and physical/logical digest pass."""

from hashlib import sha256
from types import SimpleNamespace
import sys

import pytest

from empirical_lawhood.api import matrix_factor_confirmation_compact_read as e1
from empirical_lawhood.api import matrix_full_factor_read as e4
from empirical_lawhood.api import matrix_full_factor_custody as full_custody
from empirical_lawhood.api import protected_e3_read_custody as e3
from empirical_lawhood.api import matrix_selected_e3_e4_read as selected
from empirical_lawhood.api import recursive_qualified_parents as parent
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from tests.runtime_platform.test_artifact_verification_scope import _publication


@pytest.mark.parametrize('owner', (e1, e4, selected))
def test_typed_read_keeps_exact_canonical_refusals_without_rematerializing(owner):
    value = ObjectIdentity('exposed.read-control', ObjectIdentity.SCHEMA, '1.0.0', 'a' * 64)
    raw = value.canonical_bytes()
    def read(body, digest=None):
        if owner is selected:
            return owner._decode_record_bytes((body, digest or sha256(body).hexdigest()), ObjectIdentity)
        return owner._decode(body, ObjectIdentity)
    calls = []
    def observed(frame, event, _):
        if event == 'call' and frame.f_code is CanonicalRecord.canonical_bytes.__code__:
            calls.append(1)
    previous = sys.getprofile()
    sys.setprofile(observed)
    try:
        assert read(raw) == value
    finally:
        sys.setprofile(previous)
    assert not calls
    for changed in (raw + b' ', raw.replace(b'"object_id":', b'"object_id":"duplicate","object_id":')):
        with pytest.raises(ValueError):
            read(changed)
    if owner is selected:
        with pytest.raises(ValueError):
            read(raw, 'f' * 64)


def test_output_payload_hashes_once_and_keeps_current_member_guards(tmp_path, monkeypatch):
    plane, (manifest,) = _publication(tmp_path, 1)
    receipt = SimpleNamespace(output_materializations=(manifest.materialization,))
    hashes, access = [], []
    def digest(raw):
        hashes.append(len(raw))
        return sha256(raw)
    monkeypatch.setattr(parent, 'sha256', digest)
    raw = parent._output_payload(plane, receipt, manifest.logical, manifest.materialization.size_bytes,
        before_member=lambda member: access.append(member))
    assert hashes == [len(raw)] and access[-1] == manifest
    assert len(access) >= 2
    path = plane.root.resolve(manifest.materialization.relative_path, for_write=False)
    path.write_bytes(raw.replace(b'exposed', b'changed', 1))
    with pytest.raises(ArtifactIdentityConflict):
        parent._output_payload(plane, receipt, manifest.logical, manifest.materialization.size_bytes)


@pytest.mark.parametrize('owner', (e3, full_custody))
def test_typed_product_uses_original_published_bytes_and_identity(tmp_path, monkeypatch, owner):
    """Real published body; disclosed receipt metadata, never authority."""
    plane, (manifest,) = _publication(tmp_path, 1)
    receipt = SimpleNamespace(output_materializations=(manifest.materialization,),
        output_logical_artifacts=(manifest.logical,), receipt_id='receipt.exposed.decode',
        SCHEMA='empirical-lawhood/testing/disclosed-receipt', VERSION='1.0.0', fingerprint=lambda: 'a' * 64)
    if owner is e3:
        record, _ = owner.product(plane, None, {'task.exposed': receipt}, 'task.exposed', ObjectIdentity)
    else:
        monkeypatch.setattr(owner, '_output', lambda *args, **kwargs: (receipt, manifest))
        record, _ = owner._record(plane, None, None, 'task.exposed', ObjectIdentity, 'object_id')
    assert record.object_id == 'exposed.subject.0'
    assert record.fingerprint() == manifest.logical.content_sha256
