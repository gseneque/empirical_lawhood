# SPDX-License-Identifier: MPL-2.0
"""Small issued metadata controls; no native worker or scientific authority."""
from dataclasses import replace

import pytest

from empirical_lawhood.api.protected_e3_read_custody import _publication
from empirical_lawhood.infrastructure.study_issue import (
    ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore,
    PROGRAMME_ISSUE_GRANTEE_ID,
)
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401


def _publisher(writer):
    return ExternalIssuedStudyPublisher(artifact_plane=writer,
        authority_store=ExternalStudyOperationAuthorityStore(writer),
        grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)


def test_original_publication_releases_duplicate_issued_and_base_bodies(
        actual_issued_current_task_controls, monkeypatch):  # noqa: F811
    from empirical_lawhood.infrastructure import study_issue
    f = actual_issued_current_task_controls
    package = f.control.package
    before = package.canonical_bytes()
    original_decode, decoded = study_issue.decode_canonical_bytes, []

    def decode(payload, kind, **options):
        decoded.append(kind)
        return original_decode(payload, kind, **options)

    monkeypatch.setattr(study_issue, 'decode_canonical_bytes', decode)
    with f.control.service.artifact_plane.read_context() as writer, _publisher(writer).read_context() as publisher:
        _publication(writer, package, publication_reader=publisher)
        published = publisher.load_executable_study(package.issued_study.issue_id)
        base = publisher.load_study(package.issued_study.base.issue_id)
        assert published.manifest is package.issued_study
        assert base.manifest is package.issued_study.base
        assert package.canonical_bytes() == before
        assert type(package.issued_study) not in decoded
        assert type(package.issued_study.base) not in decoded
    with pytest.raises(RuntimeError, match='scope has ended'):
        publisher.load_executable_study(package.issued_study.issue_id)
    assert not f.control.executor.invocations


def test_shared_publication_rejects_a_different_expected_issued_record(
        actual_issued_current_task_controls):  # noqa: F811
    f = actual_issued_current_task_controls
    issued = f.control.package.issued_study
    foreign = replace(issued, issue_id='disclosed.foreign.issue')
    with f.control.service.artifact_plane.read_context() as writer, _publisher(writer).read_context() as publisher:
        with pytest.raises(PermissionError, match='expected issued'):
            publisher.load_executable_study(issued.issue_id, expected_manifest=foreign)
        assert publisher.load_executable_study(issued.issue_id).manifest == issued
    assert not f.control.executor.invocations
