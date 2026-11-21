# SPDX-License-Identifier: MPL-2.0
"""Disclosed certificate boundary controls; real installed custody is separate.

These controls use the real artifact writer and domain assessor, with explicit
receipt stand-ins at the already tested contribution authentication boundary.
They neither authenticate a real study nor establish scientific qualification.
"""

from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.methods.assigned_opportunity_assessment import bindings, design, portability
from empirical_lawhood.api import knowledge_certificates as owner
from empirical_lawhood.api import recursive_inquiry, recursive_operations
from empirical_lawhood.api.recursive_inquiry_claims import project_wave_claim_assessments
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate, KnowledgeNoticeKind
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest, LogicalArtifactIdentity
from empirical_lawhood.execution.recursive_handoff import PortableRecursiveContribution, RecursiveClosureMember
from tests.test_assigned_opportunity_assessment import projection_fixture
from tests.test_recursive_public_service import _plane


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class DisclosedReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/knowledge-receipt-stand-in"
    receipt_id: str
    run_id: str
    task_id: str
    operational_status: OperationalStatus
    output_logical_artifacts: tuple[LogicalArtifactIdentity, ...]


@pytest.fixture
def disclosed(tmp_path, monkeypatch):
    plane = _plane(tmp_path / "selected")
    root = Path(plane.root.contract.canonical_path)
    cases, exported = {}, {}
    declarations = bindings.operation_declarations()
    factories = tuple(d.provider_factory() for d in declarations)
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: factories)
    monkeypatch.setattr(recursive_inquiry, "_scientific_product_identity", lambda draft, task, record: bindings.record_identity(record))
    for case in ("positive", "adverse", "unevaluable"):
        draft, products, _ = projection_fixture(case)
        products["outputs"] = {}
        for node, rows in products["records"].items():
            record, = rows.values()
            written = plane.write(ArtifactWriteRequest("logical." + case + "." + node,
                "fixture/" + case + "/" + node + ".json", record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                "application/json", "fixture." + case, "fixture/" + case, record.canonical_bytes(),
                design.VISIBILITY, (), design.ACCESS))
            products["outputs"][written.logical.logical_artifact_id] = written
            products["receipts"][node] = DisclosedReceipt("fixture.receipt." + case + "." + node,
                "fixture.run." + case, node, OperationalStatus.SUCCEEDED, (written.logical,))
        manifest, = portability.describe_contributions(draft, products)
        transport = PortableRecursiveContribution("fixture.transport." + case,
            plane.root.contract.storage_root_id, "wave", "run", ObjectIdentity.from_record(manifest.contribution_id, manifest),
            (RecursiveClosureMember("wave/disclosed.json", 1, "a" * 64),))
        cases[case] = SimpleNamespace(draft=draft, products=products, manifest=manifest, transport=transport,
                                      specification=portability.replay_specification(draft))
    def export(*, directory, output_dir, **kwargs):
        selected = cases[Path(directory).name]
        Path(output_dir).mkdir(parents=True)
        exported[Path(output_dir)] = selected
    def authenticate(*, directory, include_draft=False, **kwargs):
        selected = exported[Path(directory)]
        result = (Path(directory), selected.transport, selected.manifest,
            {"run_id": next(iter(selected.products["receipts"].values())).run_id}, selected.products, plane)
        return (*result, selected.draft) if include_draft else result
    monkeypatch.setattr(owner, "export_recursive_contribution", export)
    monkeypatch.setattr(owner, "authenticate_recursive_contribution", authenticate)
    return SimpleNamespace(plane=plane, root=root, cases=cases, exported=exported, factories=factories)


def produce(case, name, fixture):
    return owner.produce_assessment_certificate(directory=Path(case), output_directory=fixture.root / name,
        specification=fixture.cases[case].specification, project_root=ROOT, artifact_writer=fixture.plane)


@pytest.mark.parametrize("case,disposition", (("positive", "SATISFIED"), ("adverse", "FALSIFIED"), ("unevaluable", "UNEVALUABLE")))
def test_reference_round_trip_preserves_original_findings_census_and_admission_limits(disclosed, case, disposition):
    report = produce(case, case, disclosed)
    certificate = decode_canonical_bytes((disclosed.root / case / "certificate.json").read_bytes(),
                                        KnowledgeAssessmentCertificate, maximum_bytes=owner.MAX_CERTIFICATE_MEMBER_BYTES)
    original = disclosed.cases[case]
    assert certificate.disposition.value == report["original_disposition"] == disposition
    assert len(original.products["records"]["assigned-opportunity.assess"]["assigned-opportunity.assess.product"].outcomes.rows) == 4
    assert len(report["independent_unit_ids"]) == 1 and len(report["nested_view_ids"]) == 2
    assert report["consumer_admission"] == "NOT_EVALUATED" and report["authorship"] == "NOT_ATTESTED"
    assert report["evidence_ceiling"] == "NON_PROMOTABLE" and not report["requalification_performed"]
    assert report["replay_selection_is_original_commitment"] is False
    assert report == owner.verify_assessment_certificate(directory=disclosed.root / case,
        artifact_writer=disclosed.plane, expected_certificate=certificate.identity)
    assert bool(report["remaining_requirements"]) == (case != "positive")


@pytest.mark.parametrize("field", ("subject", "source", "assessment_contract", "method", "contribution", "transport"))
def test_consistently_encoded_outer_substitution_does_not_replace_original_receipt_assessment(disclosed, field):
    produce("positive", "selected", disclosed)
    path = disclosed.root / "selected/certificate.json"
    original = decode_canonical_bytes(path.read_bytes(), KnowledgeAssessmentCertificate,
                                      maximum_bytes=owner.MAX_CERTIFICATE_MEMBER_BYTES)
    # Deliberately bypass publication in this mutation fixture. Exact semantic
    # replay must refuse even when an attacker recomputes outer canonical bytes.
    changed = replace(original, **{field: replace(getattr(original, field), object_fingerprint="f" * 64)})
    path.write_bytes(changed.canonical_bytes())
    with pytest.raises(ValueError, match="certificate"):
        owner.verify_assessment_certificate(directory=path.parent, artifact_writer=disclosed.plane)


@pytest.mark.parametrize("failure,status", ((FileNotFoundError("missing original evidence"), "MISSING_DEPENDENCY"),
    (PermissionError("current evidence restricted"), "ACCESS_REFUSED")))
def test_partial_read_keeps_identity_without_issuing_a_scientific_verdict(disclosed, monkeypatch, failure, status):
    produce("adverse", "selected", disclosed)
    def unavailable(**kwargs):
        raise failure
    monkeypatch.setattr(owner, "authenticate_recursive_contribution", unavailable)
    with pytest.raises(type(failure)):
        owner.verify_assessment_certificate(directory=disclosed.root / "selected", artifact_writer=disclosed.plane)
    report = owner.verify_assessment_certificate(directory=disclosed.root / "selected",
        artifact_writer=disclosed.plane, allow_incomplete=True)
    assert report["status"] == status and report["scientific_assessment"] == "NOT_REPLAYED"
    assert report["certificate"]["value"]["disposition"] == "FALSIFIED"
    assert "original_disposition" not in report and report["consumer_admission"] == "NOT_EVALUATED"


@pytest.mark.parametrize("kind", tuple(KnowledgeNoticeKind))
def test_exact_predecessor_notices_preserve_original_bytes_and_local_assertion_scope(disclosed, kind):
    produce("positive", "old", disclosed)
    produce("adverse", "later", disclosed)
    before = {p: p.read_bytes() for name in ("old", "later") for p in (disclosed.root / name).rglob("*") if p.is_file()}
    successor = None if kind is KnowledgeNoticeKind.WITHDRAWAL else disclosed.root / "later"
    report = owner.produce_certificate_notice(predecessor_directory=disclosed.root / "old",
        successor_directory=successor, kind=kind, publisher_label="fixture.local-custodian",
        reason="Disclosed local correction control; original conflicting outcomes remain visible.",
        output_directory=disclosed.root / "notice", project_root=ROOT, artifact_writer=disclosed.plane)
    from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeCertificateNotice
    notice = decode_canonical_bytes((disclosed.root / "notice/notice.json").read_bytes(), KnowledgeCertificateNotice,
                                    maximum_bytes=owner.MAX_CERTIFICATE_MEMBER_BYTES)
    checked = owner.verify_certificate_notice(directory=disclosed.root / "notice", artifact_writer=disclosed.plane,
        expected_notice=notice.identity, predecessor_directory=disclosed.root / "old", successor_directory=successor)
    assert checked["current_global_status"] == "UNKNOWN" and report["authority_scope"] == "LOCAL_CUSTODIAN_ASSERTION_ONLY"
    assert all(path.read_bytes() == raw for path, raw in before.items())
    with pytest.raises(ValueError, match="certificate|notice"):
        owner.verify_certificate_notice(directory=disclosed.root / "notice", artifact_writer=disclosed.plane,
            expected_notice=notice.identity, predecessor_directory=disclosed.root / "later", successor_directory=successor)


def test_shared_wave_projection_reuses_exact_contract_receipt_and_ceiling_checks(disclosed):
    case = disclosed.cases["adverse"]
    rows = project_wave_claim_assessments(specification=case.specification, draft=case.draft, products=case.products)
    assert len(rows) == 1 and rows[0].disposition.value == "FALSIFIED"
    receipt = case.products["receipts"]["assigned-opportunity.assess"]
    case.products["receipts"]["assigned-opportunity.assess"] = replace(receipt, run_id="foreign.run")
    with pytest.raises(ValueError, match="execution"):
        project_wave_claim_assessments(specification=case.specification, draft=case.draft, products=case.products)
    case.products["receipts"]["assigned-opportunity.assess"] = receipt
    factories = {f.registration.selection: replace(f, inquiry_claim_assessment_projector=None) for f in disclosed.factories}
    assert project_wave_claim_assessments(specification=case.specification, draft=case.draft,
                                         products=case.products, factories=factories) == ()


def test_changed_projection_during_replay_refuses_a_current_verified_report(disclosed, monkeypatch):
    produce("positive", "selected", disclosed)
    project = owner._original_projection
    def changed(*args, **kwargs):
        row, method = project(*args, **kwargs)
        forged = replace(row, independent_unit_ids=("unit.foreign",))
        (disclosed.root / "selected/assessment-projection.json").write_bytes(forged.canonical_bytes())
        return row, method
    monkeypatch.setattr(owner, "_original_projection", changed)
    with pytest.raises(ValueError, match="certificate member"):
        owner.verify_assessment_certificate(directory=disclosed.root / "selected", artifact_writer=disclosed.plane)
