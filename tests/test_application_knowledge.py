# SPDX-License-Identifier: MPL-2.0
"""Application controls reuse small disclosed custody fixtures, without acquisition."""

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import application_knowledge as owner
from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, load_application_json, response_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_record
from empirical_lawhood.storage.contracts.knowledge_store import KnowledgeObjectLocator
from tests.test_knowledge_store import ROOT, catalog, census, transfer
from tests.test_knowledge_store import case as case
from tests.test_knowledge_certificates import disclosed as disclosed, produce


def context():
    return ApplicationContext("knowledge", "Disclosed local knowledge control", Path("/selected/python"),
        project_root=ROOT, operator_profile=Path("/selected/target-profile"), catalog_relative_path="new.sqlite3")


@pytest.fixture
def application(case, monkeypatch):
    selected = SimpleNamespace(case=case, profile_revision=1, source_revision=1)
    def storage(ctx, **kwargs):
        source = str(ctx.operator_profile) == "/selected/source-profile"
        profile = SimpleNamespace(to_document=lambda: {"selected": "source" if source else "target",
            "revision": selected.source_revision if source else selected.profile_revision})
        return ROOT, profile, case.original if source else case.b.artifact_writer
    monkeypatch.setattr(owner, "application_storage", storage)
    monkeypatch.setattr(owner, "knowledge_certificate_descriptors", lambda: tuple(case.types.descriptors.values()))
    monkeypatch.setattr(owner, "development_certificate_access", lambda plane: case.guard)
    monkeypatch.setattr(owner, "select_operator_catalog", lambda **k: catalog(case, k["catalog_relative_path"].removesuffix(".sqlite3")))
    return selected


def run(operation, *, selection=None, selected_context=None, **values):
    if selection is not None:
        values["text"] = json.dumps(selection)
    return execute_application(selected_context or context(), ApplicationRequest("knowledge.control", "knowledge", operation,
        tuple(values.items())))


def wire(result):
    assert result.succeeded, result
    return load_application_json(response_bytes(result))["payload"]


def test_initialize_review_binds_profile_context_and_destination_before_any_write(application):
    case = application.case
    destination = Path(case.b.artifact_writer.root.contract.canonical_path) / "new-store"
    selection = {"action": "INITIALIZE", "directory": str(destination), "namespace": "new.store"}
    before = census(case.root)
    review = wire(run("knowledge.review", selection=selection))
    assert census(case.root) == before and not destination.exists()
    application.profile_revision = 2
    changed = run("knowledge.apply", selection=review["selection"], expected_review_sha256=review["review_sha256"])
    assert changed.reason_codes == ("REVIEWED_SELECTION_CHANGED",) and not destination.exists()
    application.profile_revision = 1
    other = {**review["selection"], "directory": str(destination.parent / "substitute")}
    assert run("knowledge.apply", selection=other, expected_review_sha256=review["review_sha256"]).reason_codes == ("REVIEWED_SELECTION_CHANGED",)
    assert not Path(other["directory"]).exists()
    assert wire(run("knowledge.apply", selection=review["selection"], expected_review_sha256=review["review_sha256"]))["status"] == "INITIALIZED"


def test_reviewed_import_uses_original_identity_source_profile_and_current_replica_owner(application):
    case = application.case
    directory, identity = transfer(case)
    selection = {"action": "IMPORT", "directory": str(case.b.directory), "namespace": case.b.namespace,
        "source_profile": "/selected/source-profile", "transfer_directory": str(directory), "resume": False}
    review = wire(run("knowledge.review", selection=selection))
    assert review["selection"]["expected_transfer"] == identity.to_document()
    assert review["review"]["physical_closure"]["objects"] == 2
    assert not (case.b.directory / "imports").exists()
    application.source_revision = 2
    assert run("knowledge.apply", selection=review["selection"], expected_review_sha256=review["review_sha256"]).reason_codes == ("REVIEWED_SELECTION_CHANGED",)
    assert not (case.b.directory / "imports").exists()
    application.source_revision = 1
    imported = wire(run("knowledge.apply", selection=review["selection"], expected_review_sha256=review["review_sha256"]))
    assert imported["status"] == "IMPORTED" and len(imported["locators"]) == 2
    rebuild = wire(run("knowledge.review", selection={"action": "REBUILD", "directory": str(case.b.directory), "namespace": case.b.namespace}))
    assert not catalog(case, "new").database_path.exists()
    assert wire(run("knowledge.apply", selection=rebuild["selection"], expected_review_sha256=rebuild["review_sha256"]))["complete_imports"] == 1
    queried = wire(run("knowledge.query", directory=str(case.b.directory), namespace=case.b.namespace, limit=1))
    assert queried["page"]["total"] == 2 and queried["page"]["returned_count"] == 1
    assert queried["summary"]["selected_imports"] == 1 and "not the whole store" in queried["summary"]["total_scope"]
    locator = queried["page"]["rows"][0]["locator"]
    selected = {"directory": str(case.b.directory), "namespace": case.b.namespace, "locator": locator}
    resolved = wire(run("knowledge.resolve", selection=selected))
    assert resolved["knowledge"]["identity"] == decode_canonical_record(locator, KnowledgeObjectLocator).object_identity.to_document()
    assert resolved["knowledge"]["consumer_admission"] == "NOT_EVALUATED"
    case.access.revoked = True
    partial = wire(run("knowledge.resolve", selection=selected, allow_partial=True))
    assert partial["knowledge"]["scientific_assessment"] == "NOT_VERIFIED"
    assert partial["summary"]["verification_status"] == "ACCESS_REFUSED"
    assert "disclosed current knowledge access revoked" not in json.dumps(partial)
    assert "verification" not in partial["knowledge"]


def test_application_export_keeps_exact_locators_and_refuses_changed_review(application):
    case = application.case
    directory, identity = transfer(case)
    imported = case.b.import_transfer(directory=directory, source_artifact_writer=case.original,
        source_require_access=case.guard, expected_transfer=identity)
    destination = case.b.directory.parent / "export"
    selection = {"action": "EXPORT", "directory": str(case.b.directory), "namespace": case.b.namespace,
        "locators": [row.to_document() for row in imported["locators"]],
        "roots": [row.identity.to_document() for row in case.facts], "output_directory": str(destination)}
    review = wire(run("knowledge.review", selection=selection))
    assert not destination.exists()
    changed = {**review["selection"], "locators": selection["locators"][:1], "roots": [imported["locators"][0].object_identity.to_document()]}
    assert not run("knowledge.apply", selection=changed, expected_review_sha256=review["review_sha256"]).succeeded
    assert not destination.exists()
    report = wire(run("knowledge.apply", selection=review["selection"], expected_review_sha256=review["review_sha256"]))
    assert report["transfer"] == review["selection"]["expected_transfer"]
    assert report["status"] == "VERIFIED_TRANSFER_BYTES"


def test_partial_report_sanitization_keeps_original_custodian_reason():
    notice = {"schema": "original.notice", "version": "1.0.0", "value": {"reason": "Original correction assertion"}}
    report = {"status": "NOT_VERIFIED", "reason": "private transport diagnostic", "notice": notice,
        "nested": {"status": "ACCESS_REFUSED", "reason": "private access diagnostic", "scientific_assessment": "NOT_VERIFIED"}}
    clean = owner._safe_report(report)
    assert clean["notice"] == notice and clean["nested"]["scientific_assessment"] == "NOT_VERIFIED"
    assert "private" not in json.dumps(clean)


def test_certificate_view_preserves_adverse_scope_and_partial_verification(disclosed, monkeypatch):
    from empirical_lawhood.api import knowledge_certificates
    original = produce("adverse", "adverse", disclosed)
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: (ROOT, None, disclosed.plane))
    directory = str(disclosed.root / "adverse")
    result = wire(run("knowledge.certificate", directory=directory))
    assert result["knowledge"] == json.loads(json.dumps(original))
    assert result["summary"]["original_disposition"] == "FALSIFIED"
    assert len(result["knowledge"]["independent_unit_ids"]) == 1 and len(result["knowledge"]["nested_view_ids"]) == 2
    def refuse(**kwargs):
        raise PermissionError("private access-owner diagnostic")
    monkeypatch.setattr(knowledge_certificates, "authenticate_recursive_contribution", refuse)
    partial = wire(run("knowledge.certificate", directory=directory, allow_partial=True))
    assert partial["summary"]["verification_status"] == "ACCESS_REFUSED"
    assert "original_disposition" not in partial["summary"] and "private" not in json.dumps(partial)
    assert partial["knowledge"]["scientific_assessment"] == "NOT_REPLAYED"
    assert partial["knowledge"]["certificate"] == original["certificate"]


def test_changed_certificate_after_projection_refuses_the_entire_view(disclosed, monkeypatch):
    produce("adverse", "adverse", disclosed)
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: (ROOT, None, disclosed.plane))
    before = owner.projection
    path = disclosed.root / "adverse/certificate.json"
    def change(**kwargs):
        result = before(**kwargs)
        path.write_bytes(path.read_bytes().replace(b'"FALSIFIED"', b'"SATISFIED"'))
        return result
    monkeypatch.setattr(owner, "projection", change)
    result = run("knowledge.certificate", directory=str(path.parent))
    assert not result.succeeded and result.payload is None


def test_protected_certificate_refuses_before_payload_read(disclosed, monkeypatch):
    from empirical_lawhood.storage import recursive_custody
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
    produce("adverse", "adverse", disclosed)
    disclosed.plane.write(ArtifactWriteRequest("protected.certificate", "protected/certificate.json",
        KnowledgeAssessmentCertificate.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
        "protected.certificate", "protected", (disclosed.root / "adverse/certificate.json").read_bytes(),
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    monkeypatch.setattr(recursive_custody, "read_exposed_recursive_payload", lambda *a, **k: pytest.fail("protected payload was opened"))
    with pytest.raises(PermissionError, match="exposed development publication"):
        owner._certificate(disclosed.root / "protected", disclosed.plane, False)


def test_protected_selection_and_strict_json_never_reach_mutation(monkeypatch):
    monkeypatch.setattr(owner, "application_storage", lambda *a, **k: pytest.fail("invalid selection opened storage"))
    selected = replace(context(), read_access_paths=(Path("/protected/read-access"),))
    assert run("knowledge.certificate", selected_context=selected, directory="/protected/certificate").reason_codes == ("UNSUPPORTED_ACCESS_SELECTION",)
    assert run("knowledge.review", text='{"action":"IMPORT","action":"EXPORT"}').reason_codes == ("DUPLICATE_FIELD",)


def test_nested_exchange_destinations_cannot_overlap_invocation_or_progress(tmp_path, monkeypatch):
    from empirical_lawhood.api import application, invocation_retention
    from empirical_lawhood.api.application_contracts import ApplicationError
    from empirical_lawhood.api.application_invocation import run_application_invocation
    selected = replace(context(), invocation_root=tmp_path / "invocations", progress_root=tmp_path / "progress")
    invocation = selected.invocation_root / "original-handle"
    monkeypatch.setattr(invocation_retention, "start_attempt", lambda *a, **k: pytest.fail("overlap started an attempt"))
    monkeypatch.setattr(application, "execute_application", lambda *a: pytest.fail("overlap entered its owner"))
    for destination in (invocation / "attempt/export", tmp_path / "progress", invocation.parent):
        selection = {"action": "EXPORT", "directory": str(tmp_path / "original-store"), "output_directory": str(destination)}
        request = ApplicationRequest("overlap", "knowledge", "knowledge.apply", (("text", json.dumps(selection)),))
        with pytest.raises(ApplicationError, match="must be disjoint"):
            run_application_invocation(selected, request, directory=invocation, handle="original-handle")
    assert not invocation.exists()


def test_invocation_retains_selected_locators_without_copying_knowledge_text(tmp_path, monkeypatch):
    from empirical_lawhood.api import application
    from empirical_lawhood.api.application_contracts import application_result
    from empirical_lawhood.api.application_invocation import run_application_invocation
    source = str(tmp_path / "original-store")
    selection = {"directory": source, "namespace": "visible.namespace", "locator": {"private_assertion": "DO_NOT_RETAIN_BODY"}}
    request = ApplicationRequest("metadata", "knowledge", "knowledge.resolve", (("text", json.dumps(selection)),))
    monkeypatch.setattr(application, "execute_application", lambda *a: application_result("knowledge.resolve", {}))
    directory = tmp_path / "invocations/metadata"
    directory.mkdir(parents=True)  # The original dispatch owner creates this claimed invocation first.
    run_application_invocation(context(), request, directory=directory, handle="metadata")
    files = tuple(path for path in directory.rglob("*") if path.is_file())
    assert files and any(b'knowledge.directory' in path.read_bytes() and source.encode() in path.read_bytes() for path in files)
    assert all(b'DO_NOT_RETAIN_BODY' not in path.read_bytes() for path in files)
