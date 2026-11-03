# SPDX-License-Identifier: MPL-2.0
"""Real stored test grants through retained payload guards; no science claims."""
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from weakref import ref

import pytest

from empirical_lawhood.api import selected_e3_access as owner
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, ArtifactIdentityConflict
from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.recursive_handoff import RecursiveWaveMember
from tests.test_selected_e3_current_access import (
    _actual_original_access, _authority_read_work,
    actual_issued_current_task_controls,  # noqa: F401
)
from tests.test_reduced_artifact_verification import _mask_changed_stat


@dataclass(frozen=True)
class Payload(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/payload-guard-lifetime'
    VERSION: ClassVar[str] = '1.0.0'
    record_id: str
    data: str


@pytest.mark.parametrize('damage', (None, 'grant', 'body'))
def test_payload_checkpoint_owns_one_live_grant_read(actual_issued_current_task_controls,  # noqa: F811
        monkeypatch, damage):
    f = actual_issued_current_task_controls
    original = f.control.service.artifact_plane
    plane = ExternalArtifactPlane(original.root, original.validators, original.semantic_validations,
        custody_limits=original.custody_limits, maximum_parallel_verifications=8)
    # A publication large enough to exercise the actual parallel-read boundary.
    # These are disclosed control records, never completed scientific products.
    records = tuple(Payload('payload.disclosed.' + str(i), 'x' * (600 * 1024)) for i in range(2))
    members = tuple(RecursiveWaveMember(f'member-{i}.json', ObjectIdentity.from_record(record.record_id, record),
        len(record.canonical_bytes())) for i, record in enumerate(records))
    plane.write_batch(tuple(ArtifactWriteRequest(record.record_id, 'guard-lifetime/' + member.filename,
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'control.disclosed',
        'guard-lifetime', record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE) for record, member in zip(records, members, strict=True)))
    root = Path(plane.root.contract.canonical_path)
    expectation = (pytest.raises((ArtifactIdentityConflict, ValueError, PermissionError))
        if damage is not None else nullcontext())
    with expectation:
        with plane.read_context() as reading:
            access = _actual_original_access(f, reading)
            payloads = AuthenticatedRecursivePayloads(plane=reading, directory=root / 'guard-lifetime',
                members=members, original_input_access=access)
            observed = ref(payloads)
            assert payloads._member_preflight() is payloads._member_preflight()
            assert payloads['member-0.json'] == records[0].canonical_bytes()
            if damage is not None:
                relative = (ExternalStudyOperationAuthorityStore._relative_path(f.control.reveal.authority_id)
                    if damage == 'grant' else 'guard-lifetime/member-0.json')
                path = root / relative
                raw = path.read_bytes()
                _mask_changed_stat(monkeypatch, path)
                path.write_bytes(b'[' + raw[1:])
            with _authority_read_work() as work:
                reading.require_full_verification_snapshot()
            # The callback owns one finite grant reader on this caller thread.
            # Every member still rehashes its grants and samples fresh UTC.
            assert work['fresh_grant_loads'] == 2
            assert work['fresh_utc_checks'] == len(members)
            assert owner._current_authority_reader(plane) is None
    del payloads
    if damage is None:
        assert observed() is None
    assert not f.control.executor.invocations
