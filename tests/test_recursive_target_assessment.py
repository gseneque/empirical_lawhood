# SPDX-License-Identifier: MPL-2.0
"""Public target assessment from actual exposed material supplier/use receipts.

The independent analytic equations below establish the expected software result.
No physical qualification, new independent unit or native acquisition is claimed.
"""

from dataclasses import replace
from hashlib import sha256
from math import cosh
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execute
from empirical_lawhood.api import recursive_inquiry as service
from empirical_lawhood.api import recursive_inquiry_claims as claim_owner
from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution, export_recursive_contribution
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.science.inquiry.recursive_inquiry import identity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryClaimFinding, InquiryStopScope
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.execution.recursive_inquiry import InquiryStateSources, InquiryWaveSource, WorkBoundInquiryDecisionRequest
from tests.test_recursive_public_service import _plane
from tests.test_robust_inquiry_acceptance import frozen_software_source, input_origins, operands, policy_request, publish_sources
from tests.test_robust_inquiry_service import commit

ROOT = Path(__file__).resolve().parents[1]


def rebind(request, *, specification=None, menu=None, state=None):
    specification = specification or request.specification
    state = replace(state or request.state, specification=identity(specification, specification.specification_id))
    sid, tid = state.specification, identity(state, state.state_id)
    menu = menu or request.menu
    menu = replace(menu, specification=sid, state=tid,
        observation=replace(menu.observation, specification=sid),
        alternatives=tuple(replace(row, specification=sid, state=tid) for row in menu.alternatives),
        frontier=replace(menu.frontier, target=identity(specification.target, specification.target.target_id)))
    return replace(request, specification=specification, state=state, menu=menu,
                   policy=replace(request.policy, specification=sid))


@pytest.fixture(scope="module")
def actual_target(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        frozen_software_source(patch)
        binding, science, inputs = operands("material")
        plane = _plane(tmp_path_factory.mktemp("target-assessment") / "selected")
        root = Path(plane.root.contract.canonical_path)
        supply_draft = binding.policy_supply_draft(*inputs)
        author.author_recursive_wave(draft=supply_draft, origins=input_origins(supply_draft),
            input_bindings=publish_sources(plane, supply_draft, inputs), project_root=ROOT,
            artifact_writer=plane, output_dir=root / "supply")
        report = execute.run_recursive_wave(directory=root / "supply", project_root=ROOT, artifact_writer=plane)
        assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
        _, products, _, _ = execute.read_recursive_wave(directory=root / "supply", artifact_writer=plane, include_products=True)
        supplier = next(record for rows in products["records"].values() for record in rows.values())
        supply_packet = author.load_authored_wave(directory=root / "supply", artifact_writer=plane)[0]
        export_recursive_contribution(directory=root / "supply", project_root=ROOT,
            artifact_writer=plane, output_dir=root / "contribution")
        parent = authenticate_recursive_contribution(directory=root / "contribution", artifact_writer=plane)[2]
        instance = science.compatible_instance(supplier)
        use_draft = binding.assessed_use_draft(supplier, instance, parent=parent)
        author.author_recursive_wave(draft=use_draft, origins=input_origins(use_draft, parent),
            input_bindings=publish_sources(plane, use_draft, (instance,)), contribution_dir=root / "contribution",
            project_root=ROOT, artifact_writer=plane, output_dir=root / "use")
        report = execute.run_recursive_wave(directory=root / "use", project_root=ROOT, artifact_writer=plane)
        assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
        _, products, _, _ = execute.read_recursive_wave(directory=root / "use", artifact_writer=plane, include_products=True)
        assessment = next(record for rows in products["records"].values() for record in rows.values())
        packet = author.load_authored_wave(directory=root / "use", artifact_writer=plane)[0]
        sources = InquiryStateSources((
            InquiryWaveSource("supply", identity(supply_packet, supply_packet.packet_id), True),
            InquiryWaveSource("use", identity(packet, packet.packet_id), True)))
        specification, state, menu, policy = policy_request(binding=binding, source_draft=supply_draft,
            specification_id="inquiry.analytic-target", sources=sources, plane=plane, stage="frontier", parent=parent,
            product={"record": assessment, "draft": use_draft, "outcome": "useful-supply"},
            assessments=products["connection_assessments"])
        physical_request = WorkBoundInquiryDecisionRequest(specification, state, sources, menu, policy,
            use_draft.campaign, use_draft.campaign.decision_rights[0], use_draft.campaign.decision_rights[0].decision_maker_id)
        claim = use_draft.development_study.claims[0]
        requirement = specification.requirements[-1]
        target = replace(specification.target, target_id="target.exposed-material-use", purpose=claim.proposition,
            required_requirement_ids=(requirement.requirement_id,), required_claims=(identity(claim, claim.claim_id),),
            success_condition=claim.estimand)
        specification = replace(specification, target=target, requirements=(requirement,),
            outcomes=tuple(replace(row, alternative_ids=tuple(aid for aid in row.alternative_ids if aid != "close-branch"))
                           for row in specification.outcomes))
        assessment_identity = binding.record_identity(assessment)
        evidence_ids = tuple(row.evidence_id for row in state.stock if row.product == assessment_identity)
        finding = InquiryClaimFinding(identity(claim, claim.claim_id), target.scope, assessment.disposition,
            assessment_identity, evidence_ids, "Independently checked exact analytic use claim; no physical promotion")
        menu = replace(menu, alternatives=tuple(replace(row, requirement_id=requirement.requirement_id,
            local_question_answered=row.alternative_id == "stop-target")
            for row in menu.alternatives if row.alternative_id != "close-branch"),
            frontier=replace(menu.frontier, requirement_findings=menu.frontier.requirement_findings[-1:],
                             claim_findings=(finding,)))
        request = rebind(physical_request, specification=specification, menu=menu)
        yield SimpleNamespace(plane=plane, root=root, request=request, physical_request=physical_request,
                              assessment=assessment, claim=claim)


def test_actual_independent_assessment_satisfies_only_its_exact_analytic_target(actual_target):
    case = actual_target
    # Independent SI response and slab equations, separate from the production
    # fitter, establish the expected numerical result and its complete census.
    from scipy.constants import mu_0
    panel = case.assessment.instance.panel
    assert len(panel.rows) == 20 and len(panel.slab_profile) == 101
    for row in panel.rows:
        expected = -(1 + 4 * float(row.q_over_kf) ** 2) * float(row.realized_A_T[1]) / (mu_0 * 1e-7 ** 2)
        assert float(row.current_density[1]) == pytest.approx(expected, rel=1e-12, abs=1e-100)
    assert float(panel.slab_profile[50][1]) == pytest.approx(1 / cosh(5), rel=1e-12)
    packet, records = commit(case.request, case.plane, case.root / "accepted")
    decision = records["decision.json"]
    assert decision.selected_alternative_id == "stop-target" and decision.stop_scope is InquiryStopScope.TARGET
    assert decision.unresolved_target_claim_ids == decision.unresolved_target_requirement_ids == ()
    projections = claim_owner.project_target_claim_assessments(specification=case.request.specification,
        sources=case.request.sources, menu=case.request.menu, artifact_writer=case.plane)
    assert projections[0].claim_identity == identity(case.claim, case.claim.claim_id)
    assert projections[0].assessment_contract == case.request.specification.distinguishing_assessment
    assert projections[0].independent_unit_ids == ()
    assert projections[0].evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE
    assert service.read_inquiry_decision(directory=case.root / "accepted", artifact_writer=case.plane) == (packet, records)


@pytest.mark.parametrize("defect", ("raw-source", "wrong-claim", "wrong-scope", "falsified-disposition", "physical-target"))
def test_public_commit_refuses_unsupported_target_before_publication(actual_target, defect):
    case, request = actual_target, actual_target.request
    finding = request.menu.frontier.claim_findings[0]
    if defect == "raw-source":
        raw = next(row for row in request.state.stock if row.source_contract is not None
                   and row.scope == request.specification.target.scope
                   and row.product.object_schema != "empirical-lawhood/kernel/requirement-supply-assessment")
        finding = replace(finding, assessment=raw.product, evidence_ids=(raw.evidence_id,))
    elif defect == "wrong-claim":
        altered = replace(case.claim, proposition="A different proposition with the same claim ID")
        claim_identity = identity(altered, altered.claim_id)
        specification = replace(request.specification, target=replace(request.specification.target,
                                                                     required_claims=(claim_identity,)))
        request = rebind(request, specification=specification)
        finding = replace(finding, claim=claim_identity)
    elif defect == "wrong-scope":
        finding = replace(finding, scope=replace(finding.scope, instance_id="another-instance"))
    elif defect == "falsified-disposition":
        finding = replace(finding, disposition=AssessmentDisposition.FALSIFIED)
    else:
        request = case.physical_request
        finding = replace(request.menu.frontier.claim_findings[0], disposition=AssessmentDisposition.SATISFIED,
            assessment=finding.assessment, evidence_ids=finding.evidence_ids)
    request = rebind(request, menu=replace(request.menu,
        frontier=replace(request.menu.frontier, claim_findings=(finding,))))
    destination = case.root / ("refused-" + defect)
    with pytest.raises(ValueError, match="target|independent|scope"):
        commit(request, case.plane, destination)
    assert not destination.exists()


def test_current_read_rejects_old_unassessed_success_and_preserves_archive(actual_target, monkeypatch):
    from empirical_lawhood.design import recursive_inquiry_policy as policy

    case, request = actual_target, actual_target.request
    raw = next(row for row in request.state.stock if row.source_contract is not None
               and row.scope == request.specification.target.scope
               and row.product.object_schema != "empirical-lawhood/kernel/requirement-supply-assessment")
    finding = replace(request.menu.frontier.claim_findings[0], assessment=raw.product, evidence_ids=(raw.evidence_id,))
    request = rebind(request, menu=replace(request.menu, frontier=replace(request.menu.frontier, claim_findings=(finding,))))
    directory = case.root / "legacy-unassessed-success"
    # Model only the previous missing semantic check to retain a literal old
    # packet. Original source, receipt and canonical publication checks run.
    with monkeypatch.context() as patch:
        patch.setattr(claim_owner, "project_target_claim_assessments", lambda **kwargs: ())
        patch.setattr(policy, "_validate_claim_assessments", lambda *args: None)
        packet, records = commit(request, case.plane, directory)
    assert records["decision.json"].unresolved_target_claim_ids == ()
    before = {path: sha256(path.read_bytes()).hexdigest() for path in directory.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="applicable registered independent assessor"):
        service.read_inquiry_decision(directory=directory, artifact_writer=case.plane)
    assert service.read_inquiry_decision(directory=directory, artifact_writer=case.plane,
                                        revalidate_sources=False) == (packet, records)
    assert before == {path: sha256(path.read_bytes()).hexdigest() for path in before}


def test_current_read_requires_the_registered_assessor_again(actual_target, monkeypatch):
    from empirical_lawhood.api import recursive_operations

    case = actual_target
    directory = case.root / "assessor-removal"
    packet, records = commit(case.request, case.plane, directory)
    factories = tuple(replace(factory, inquiry_claim_assessment_projector=None)
                      for factory in recursive_operations.operation_factories())
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: factories)
    with pytest.raises(ValueError, match="applicable registered independent assessor"):
        service.read_inquiry_decision(directory=directory, artifact_writer=case.plane)
    assert service.read_inquiry_decision(directory=directory, artifact_writer=case.plane,
                                        revalidate_sources=False) == (packet, records)
