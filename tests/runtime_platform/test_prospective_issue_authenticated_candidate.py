# SPDX-License-Identifier: MPL-2.0
"""Public issue checks for authenticated candidates; all authority is synthetic."""

from dataclasses import replace

import pytest

from empirical_lawhood.api.facade import EmpiricalLawhoodApi
from empirical_lawhood.api.results import OperationStatus
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
from tests.runtime_platform import test_recursive_prospective_workflow as workflow


@pytest.fixture
def authored_candidate(tmp_path, monkeypatch):
    parts = workflow._authored_handoff_fixture(tmp_path, monkeypatch)
    candidate_path = parts[0].directory / "candidate.json"
    payload = candidate_path.read_bytes()
    candidate = decode_canonical_bytes(
        payload, ExecutableStudyCandidate, maximum_bytes=16 * 1024**2
    )
    assert type(candidate) is ExecutableStudyCandidate
    assert candidate.canonical_bytes() == payload

    worker_calls = []

    def deny_execution(*args, **kwargs):
        worker_calls.append(True)
        raise AssertionError("candidate issue must not execute a worker")

    for name in dir(LocalProcessExecutor):
        if name.startswith("execute") and callable(getattr(LocalProcessExecutor, name)):
            monkeypatch.setattr(LocalProcessExecutor, name, deny_execution)

    results = []
    issue_extensions = EmpiricalLawhoodApi.issue_extensions

    def observe_public_issue(self, request):
        result = issue_extensions(self, request)
        results.append(result)
        return result

    monkeypatch.setattr(EmpiricalLawhoodApi, "issue_extensions", observe_public_issue)
    yield parts, candidate, results
    assert candidate_path.read_bytes() == payload
    assert worker_calls == []


def test_supplied_authenticated_candidate_issues_through_public_api(
    tmp_path, monkeypatch, authored_candidate
):
    parts, candidate, results = authored_candidate
    issued = workflow._issue_public_handoff(
        tmp_path,
        monkeypatch,
        handoff_parts=parts,
        namespace="supplied-authenticated-candidate",
        compiled_candidate=candidate,
    )
    package = issued[5]
    assert package.issued_study.candidate == candidate
    assert len(results) == 2
    assert all(result.status is OperationStatus.SUCCEEDED for result in results)
    assert results[0].payload == results[1].payload
    assert results[0].payload.manifest == package.issued_study


def test_supplied_foreign_candidate_is_refused_by_public_issue(
    tmp_path, monkeypatch, authored_candidate
):
    parts, candidate, results = authored_candidate
    foreign = replace(candidate, candidate_id=candidate.candidate_id + ".foreign")
    assert type(foreign) is ExecutableStudyCandidate
    assert foreign.base_candidate == candidate.base_candidate
    assert decode_canonical_bytes(
        foreign.canonical_bytes(), ExecutableStudyCandidate, maximum_bytes=16 * 1024**2
    ) == foreign

    with pytest.raises(AssertionError):
        workflow._issue_public_handoff(
            tmp_path,
            monkeypatch,
            handoff_parts=parts,
            namespace="supplied-foreign-candidate",
            compiled_candidate=foreign,
        )

    assert len(results) == 1
    refused = results[0]
    assert refused.status is OperationStatus.BLOCKED
    assert refused.payload is None
    assert refused.reason_codes == ("PROGRAMME_ISSUE_AUTHORITY_OR_BASE_REPLAY_FAILED",)
    assert tuple(error.message for error in refused.errors) == (
        "operation authority binds another subject",
    )
