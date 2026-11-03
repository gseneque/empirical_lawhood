# SPDX-License-Identifier: MPL-2.0
"""Current robust inquiry custody and pre-effect admission, using exposed fixtures."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api import recursive_inquiry as service
from empirical_lawhood.kernel.recursive_inquiry import identity
from empirical_lawhood.kernel.recursive_inquiry_policy import (
    InquiryClaimFinding, InquiryRequirementFinding, ScientificOutcomeKind,
)
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.runtime.recursive_inquiry import (
    InquiryStateSources, WorkBoundInquiryDecisionRequest,
)
from tests.test_recursive_inquiry_policy import policy_case
from tests.test_recursive_public_service import _plane

ROOT = Path(__file__).resolve().parents[1]


def missing_request(plane):
    case = policy_case()
    outcomes = tuple(replace(row, outcome_id="initial" if row.kind is ScientificOutcomeKind.MISSING else row.outcome_id,
                             alternative_ids=("hold",)) for row in case.specification.outcomes)
    outcomes = tuple(sorted(outcomes, key=lambda row: row.outcome_id))
    spec = replace(case.specification, outcomes=outcomes)
    sources = InquiryStateSources(())
    state = service.project_inquiry_state(specification=spec, state_id="state.missing",
        information_cutoff=case.state.information_cutoff, sources=sources, artifact_writer=plane)
    sid, tid = identity(spec, spec.specification_id), identity(state, state.state_id)
    hold = next(row for row in case.menu.alternatives if row.alternative_id == "hold")
    hold = replace(hold, specification=sid, state=tid, eligible_outcomes=tuple(row.outcome_id for row in outcomes))
    frontier = replace(case.menu.frontier,
        requirement_findings=tuple(InquiryRequirementFinding(identity(row, row.requirement_id), None, ())
                                   for row in spec.requirements),
        claim_findings=tuple(InquiryClaimFinding(claim, spec.target.scope, AssessmentDisposition.NOT_ATTEMPTED,
            None, (), "The scientific target has not been investigated.") for claim in spec.target.required_claims),
        completed_work=())
    observation = replace(case.menu.observation, specification=sid, outcome_id="initial",
        kind=ScientificOutcomeKind.MISSING, assessment=None, evidence_ids=(), attempt_ids=())
    menu = replace(case.menu, specification=sid, state=tid, alternatives=(hold,),
                   frontier=frontier, observation=observation)
    policy = replace(case.policy, specification=sid, assumptions=())
    return WorkBoundInquiryDecisionRequest(spec, state, sources, menu, policy, case.campaign, case.right, case.actor_id)


def commit(request, plane, directory):
    from dataclasses import fields
    return service.commit_inquiry_decision(**{field.name: getattr(request, field.name) for field in fields(request)},
        project_root=ROOT, artifact_writer=plane, output_dir=directory)


def test_missing_target_persists_v3_hold_with_unentered_frontier(tmp_path, monkeypatch):
    source = service.implementation_binding(ROOT)
    monkeypatch.setattr(service, "implementation_binding", lambda root: source)
    plane = _plane(tmp_path / "selected")
    request = missing_request(plane)
    raw = request.canonical_bytes()
    assert service.decode_inquiry_decision_request(raw) == request
    directory = tmp_path / "selected/decision"
    packet, records = commit(request, plane, directory)
    assert packet.VERSION == records["decision.json"].VERSION == "3.0.0"
    assert records["state.json"].VERSION == "2.0.0"
    assert records["decision.json"].selected_alternative_id == "hold"
    assert records["decision.json"].unresolved_target_requirement_ids == ("condition", "instrument")
    assert records["decision.json"].unresolved_target_claim_ids == ("claim.target",)
    assert "intent.json" not in records
    assert service.read_inquiry_decision(directory=directory, artifact_writer=plane) == (packet, records)


@pytest.mark.parametrize("defect", ("scope", "inactive", "right-policy", "mixed-version", "observation"))
def test_v3_invalid_operands_refuse_before_publication(tmp_path, monkeypatch, defect):
    source = service.implementation_binding(ROOT)
    monkeypatch.setattr(service, "implementation_binding", lambda root: source)
    plane = _plane(tmp_path / "selected")
    request = missing_request(plane)
    if defect == "scope":
        request = replace(request, campaign=replace(request.campaign, world_ids=("unrelated-world",)))
    elif defect == "inactive":
        request = replace(request, campaign=replace(request.campaign, lifecycle_status=LifecycleStatus.TERMINAL))
    elif defect == "right-policy":
        right = replace(request.right, authority_policy_id="unrelated-policy")
        request = replace(request, right=right, campaign=replace(request.campaign, decision_rights=(right,)))
    elif defect == "mixed-version":
        from empirical_lawhood.planning.recursive_inquiry import InquiryPolicy
        request = replace(request, policy=InquiryPolicy(request.policy.policy_id, request.policy.specification,
            request.policy.max_cost, None, None, None))
    else:
        request = replace(request, menu=replace(request.menu,
            observation=replace(request.menu.observation, outcome_id="negative")))
    directory = tmp_path / "selected/forbidden"
    with pytest.raises(ValueError):
        commit(request, plane, directory)
    assert not directory.exists()


def test_closed_version_dispatch_rejects_unknown_and_duplicate_envelopes(tmp_path):
    request = missing_request(_plane(tmp_path / "selected"))
    raw = request.canonical_bytes()
    with pytest.raises(ValueError):
        service.decode_inquiry_decision_request(raw.replace(b'"version":"3.0.0"}', b'"version":"9.0.0"}', 1))
    with pytest.raises(ValueError):
        service.decode_inquiry_decision_request(b'{"schema":"substitution",' + raw[1:])
