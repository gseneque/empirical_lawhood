from __future__ import annotations

import json
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.methods.effective_law_comparison.analysis import PosthocDocumentSet, execute_analysis
from empirical_lawhood.api.effective_law_comparison import build_authorized_package, build_freeze
from empirical_lawhood.design.posthoc_sources import ParentSourceDefinition, SourceMemberDefinition
from empirical_lawhood.storage.posthoc_sources import qualify_parent_sources
from empirical_lawhood.science.identity.source_exports import IndependentSourceExport, OriginalObjectReference, OriginalArtifactReference
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.storage.contracts.artifacts import ArtifactGenericValidation, ArtifactProfile, LogicalArtifactIdentity, ArtifactMaterialization, ArtifactManifest
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.design.posthoc import POSTHOC_ANALYSIS_IDS, PosthocExecutionAuthorization


def _parent(source_export: IndependentSourceExport | None = None) -> ParentSourceDefinition:
    return ParentSourceDefinition(
        parent_id="sample-parent",
        lane_id="sample-lane",
        study_id="sample-programme",
        target_id="sample-target",
        world_id="sample-world",
        world_kind=WorldKind.NUMERICAL_SIMULATOR,
        independent_unit_id="sample-unit",
        members=(
            SourceMemberDefinition(
                "sample-artifact", "terminal", "inputs/sample.json", source_export
            ),
        ),
        role_ids=("terminal",),
        analysis_ids=("analysis.obstruction-signatures",),
    )


def _current_source(tmp_path, *, write_manifest: bool = True):
    path = tmp_path / "inputs" / "sample.json"
    path.parent.mkdir(exist_ok=True)
    schema = "empirical-lawhood/methods/effective-law-comparison/source-contract-fixture"
    payload = json.dumps({"schema": schema, "version": "1.0.0", "value": {"terminal": "action_response"}}).encode()
    path.write_bytes(payload)
    digest = sha256(payload).hexdigest()
    validator = ArtifactGenericValidation("validator.canonical-json", "1.0.0", "3" * 64, schema, ArtifactProfile.CANONICAL_JSON)
    logical = LogicalArtifactIdentity("sample-artifact", digest, schema, ArtifactProfile.CANONICAL_JSON, "application/json", VisibilityCeiling.OUTCOME_VISIBLE, (), OutcomeAccess.EVALUATION_REVEALED, validator)
    physical = ArtifactMaterialization("sample-materialization", "sample-artifact", "sample-root", "inputs/sample.json", digest, len(payload), "none")
    from empirical_lawhood.storage.contracts.artifact_sidecar import ArtifactManifestReference
    from empirical_lawhood.storage.contracts.artifacts import (
        ArtifactPublicationBinding, ArtifactPublicationCommit, ArtifactPublicationScope,
        artifact_publication_batch_id, artifact_publication_commit_relative_path, artifact_publication_member)
    scope = ArtifactPublicationScope('sample.publication', 'sample-root', 'inputs',
        VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED)
    members = (artifact_publication_member(logical, physical),)
    batch = artifact_publication_batch_id(scope, members)
    commit = ArtifactPublicationCommit(batch, scope, members).canonical_bytes()
    binding = ArtifactPublicationBinding(batch, scope, artifact_publication_commit_relative_path(scope, batch),
        sha256(commit).hexdigest(), len(commit), members)
    manifest = ArtifactManifestReference.from_manifest(ArtifactManifest(logical, physical, binding))
    marker = tmp_path / binding.commit_marker_relative_path
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_bytes(commit)
    if write_manifest:
        path.with_suffix(".json.manifest.json").write_bytes(manifest.canonical_bytes())
    original_schema = "icf-yolo/results/qtsq-closeout/v4"
    export = IndependentSourceExport(
        original_source=OriginalObjectReference("original.sample", original_schema, "1", "a" * 64),
        original_payload_version="1",
        original_artifact=OriginalArtifactReference("original.sample-artifact", "terminal", original_schema, "a" * 64, "application/json", 123),
        original_relative_path="original/sample.json",
        original_task_receipt=OriginalObjectReference("original.sample-receipt", "icf-yolo/runtime/task-receipt/v2", "2", "b" * 64),
        original_manifest_sha256="c" * 64,
        original_publication_commit_sha256="d" * 64,
        original_source_commit="e" * 40,
        interpretation_sha256="f" * 64,
        verified_export=ObjectIdentity("verified.sample-export", "empirical-lawhood/migration/verified-source-export", "1.0.0", "1" * 64),
        target_source=ObjectIdentity("current.sample", schema, "1.0.0", digest),
        target_artifact=ArtifactIdentity("sample-artifact", "terminal", schema, digest, "application/json", len(payload)),
        target_relative_path="inputs/sample.json",
        target_task_receipt=ObjectIdentity("current.sample-receipt", "empirical-lawhood/runtime/canonical-task-receipt", "1.0.0", "2" * 64),
        target_manifest_sha256=manifest.fingerprint(),
        target_publication_commit_sha256=binding.commit_marker_sha256,
        original_physical_unit_ids=("original.sample-unit",),
        target_physical_unit_ids=("sample-unit",),
    )
    return path, payload, export, manifest


def test_explicit_posthoc_source_roster_requires_bound_external_bytes(tmp_path) -> None:
    path, payload, export, manifest = _current_source(tmp_path, write_manifest=False)
    absent = qualify_parent_sources(tmp_path, (_parent(export),))["value"]["parents"][0]
    assert absent["status"] == "PARTIALLY_ELIGIBLE"
    assert "PARENT_RECEIPT_ABSENT" in absent["reason_codes"]

    sidecar = path.with_suffix(".json.manifest.json")
    sidecar.write_bytes(manifest.canonical_bytes())
    qualified = qualify_parent_sources(tmp_path, (_parent(export),))["value"]["parents"][0]
    assert qualified["status"] == "ELIGIBLE"
    assert qualified["members"][0]["content_sha256"] == sha256(payload).hexdigest()

    sidecar.write_bytes(manifest.canonical_bytes() + b" ")
    drifted = qualify_parent_sources(tmp_path, (_parent(export),))["value"]["parents"][0]
    assert drifted["status"] != "ELIGIBLE"
    assert "CURRENT_SOURCE_RECEIPT_CUSTODY_MISMATCH" in drifted["reason_codes"]


def test_partition_sensitive_analysis_requires_explicit_mapping() -> None:
    document = {
        "schema": "empirical-lawhood/methods/effective-law-comparison/source-contract-fixture",
        "version": "1.0.0",
        "value": {"reason_codes": ["POWER_STOP"]},
    }
    with pytest.raises(ValueError, match="parent partition map"):
        execute_analysis("analysis.obstruction-signatures", {"sample-artifact": document}, ("sample-parent",))
    mapped = PosthocDocumentSet(
        {"sample-artifact": document}, {"sample-artifact": "sample-parent"}
    )
    result = execute_analysis("analysis.obstruction-signatures", mapped, ("sample-parent",))
    assert result["value"]["parent_ids"] == ["sample-parent"]


def test_posthoc_freeze_uses_explicit_roster_and_clean_source(tmp_path, monkeypatch) -> None:
    subprocess.run(("git", "init", "-q", str(tmp_path)), check=True)
    _, _, export, _ = _current_source(tmp_path)
    from empirical_lawhood.methods.effective_law_comparison import provider
    monkeypatch.setattr(
        provider,
        "SUPPORTED_INPUT_SCHEMAS",
        tuple(sorted((*provider.SUPPORTED_INPUT_SCHEMAS, export.target_source.object_schema))),
    )
    (tmp_path / "method.py").write_text("METHOD = 'bounded'\n")
    subprocess.run(("git", "add", "."), cwd=tmp_path, check=True)
    subprocess.run(
        ("git", "-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "-qm", "freeze"),
        cwd=tmp_path,
        check=True,
    )
    parent = _parent(export)
    parent = ParentSourceDefinition(
        parent.parent_id,
        parent.lane_id,
        parent.study_id,
        parent.target_id,
        parent.world_id,
        parent.world_kind,
        parent.independent_unit_id,
        parent.members,
        parent.role_ids,
        tuple(sorted(POSTHOC_ANALYSIS_IDS)),
    )
    qualification = qualify_parent_sources(tmp_path, (parent,))
    freeze, closure = build_freeze(
        repository_root=tmp_path,
        qualification=qualification,
        frozen_at_utc="2026-09-28T00:00:00Z",
        parent_sources=(parent,),
        implementation_files=("method.py",),
        plan_sha256=sha256(b"one explicit nonpromotable plan").hexdigest(),
        freeze_id="sample-posthoc.freeze",
    )
    assert len(freeze.analyses) == 9
    assert len(freeze.parents) == 1
    assert closure["value"]["base_commit"] == freeze.implementation_commit
    authority = PosthocExecutionAuthorization(
        authorization_id="sample-posthoc.authorization",
        freeze=ObjectIdentity.from_record(freeze.freeze_id, freeze),
        requested_scope_id="sample-posthoc",
        external_run_root="runs/sample-posthoc",
        requested_budget=ResourceBudget(1, 1024**3, 0, 3600, 1024**2, 1024**2),
        proposer_id="sample-human-proposer",
        approver_id="sample-human-approver",
        authorized_at_utc="2026-09-28T00:00:01Z",
        implementation_commit=freeze.implementation_commit,
        passed_gate_ids=("bounded-source-roster",),
        plan_mutated=False,
        grants_claim_promotion=False,
        nonactuating=True,
    )
    plan, package, registry = build_authorized_package(
        freeze,
        authorization=authority,
        run_root="runs/sample-posthoc",
        package_id="sample-posthoc.package",
    )
    assert len(plan.tasks) == 21
    assert package.authorization == authority
    for task in plan.tasks:
        registry.require(task.capability)
    (tmp_path / "method.py").write_text("METHOD = 'changed'\n")
    with pytest.raises(PermissionError, match="clean source commit"):
        build_freeze(
            repository_root=tmp_path,
            qualification=qualification,
            frozen_at_utc="2026-09-28T00:00:00Z",
            parent_sources=(parent,),
            implementation_files=("method.py",),
            plan_sha256=sha256(b"one explicit nonpromotable plan").hexdigest(),
            freeze_id="sample-posthoc.freeze",
        )


def test_retained_posthoc_reader_preserves_bytes_and_refuses_changed_ancestry(tmp_path):
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.science.records.serialization import canonical_json_bytes
    from empirical_lawhood.science.records.status import OperationalStatus
    from empirical_lawhood.storage.contracts.artifacts import ArtifactSemanticValidation, CanonicalTaskReceipt
    from empirical_lawhood.storage.posthoc_results import EffectiveLawPosthocReadPorts, read_published_task

    implementation = "a" * 64
    resolutions = []
    verifications = []

    class ReadOnlyRoot:
        def resolve(self, relative_path, *, for_write, operation_minimum_free_bytes=0):
            assert for_write is False
            resolutions.append(relative_path)
            return tmp_path / relative_path

    class ReadOnlyPlane:
        def verify(self, materialization):
            verifications.append(materialization.relative_path)
            payload = (tmp_path / materialization.relative_path).read_bytes()
            assert len(payload) == materialization.size_bytes
            if sha256(payload).hexdigest() != materialization.physical_sha256:
                raise ValueError("changed original bytes")

        def verify_manifest(self, manifest):
            self.verify(manifest.materialization)
            sidecar = tmp_path / (manifest.materialization.relative_path + ".manifest.json")
            assert sidecar.read_bytes() == manifest.canonical_bytes()

    def publish_fixture(relative_path, artifact_id, document, *, payload=None):
        payload = canonical_json_bytes(document) if payload is None else payload
        schema = document["schema"]
        generic = ArtifactGenericValidation("validator.canonical-json", "1.0.0", "3" * 64,
            schema, ArtifactProfile.CANONICAL_JSON)
        semantic = ArtifactSemanticValidation(f"posthoc-json.{artifact_id}", "1.0.0", implementation,
            schema, ArtifactProfile.CANONICAL_JSON, ("schema", "value", "version"),
            tuple(sorted(document["value"])))
        logical = LogicalArtifactIdentity(artifact_id, sha256(payload).hexdigest(), schema,
            ArtifactProfile.CANONICAL_JSON, "application/json", VisibilityCeiling.OUTCOME_VISIBLE,
            (), OutcomeAccess.EVALUATION_REVEALED, generic, semantic_validation=semantic)
        physical = ArtifactMaterialization(artifact_id + ".physical", artifact_id, "test.root",
            relative_path, sha256(payload).hexdigest(), len(payload), "none")
        manifest = ArtifactManifest(logical, physical)
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        (tmp_path / (relative_path + ".manifest.json")).write_bytes(manifest.canonical_bytes())
        return manifest

    output_path = "run/outputs/task.one/result.json"
    output = publish_fixture(output_path, "output.one", {
        "schema": "empirical-lawhood/test/posthoc-retained", "version": "1.0.0",
        "value": {"disposition": "UNEVALUABLE"},
    })
    receipt = CanonicalTaskReceipt("receipt.one", "run.one", "task.one", "attempt-001", "b" * 40,
        ("input.original",), (output.materialization,), (output.logical,), (), OperationalStatus.SUCCEEDED, ())
    publish_fixture("run/receipts/task.one/attempt-001.json", "receipt.one",
        json.loads(receipt.canonical_bytes()), payload=receipt.canonical_bytes())
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    ports = EffectiveLawPosthocReadPorts(ReadOnlyRoot(), lambda registry: ReadOnlyPlane(),
        lambda raw: decode_canonical_bytes(raw, ArtifactManifest, maximum_bytes=1024**2),
        lambda raw: decode_canonical_bytes(raw, CanonicalTaskReceipt, maximum_bytes=16 * 1024**2),
        "run", "run.one")
    arguments = dict(ports=ports, task_id="task.one", implementation_commit="b" * 40,
        implementation_sha256=implementation, expected_input_materialization_ids=("input.original",))
    retained = read_published_task(**arguments)
    assert retained.document["value"]["disposition"] == "UNEVALUABLE"
    assert retained.receipt == receipt
    assert retained.result.created is False
    assert verifications and resolutions
    assert before == {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="input closure drifted"):
        read_published_task(**{**arguments, "expected_input_materialization_ids": ("input.substituted",)})
    (tmp_path / output_path).write_bytes(before[Path(output_path)].replace(b"UNEVALUABLE", b"SATISFIED  "))
    with pytest.raises(ValueError, match="changed original bytes"):
        read_published_task(**arguments)


def test_retained_posthoc_reader_refuses_partial_publication_without_writing(tmp_path):
    from empirical_lawhood.storage.posthoc_results import EffectiveLawPosthocReadPorts, read_published_task

    class ReadOnlyRoot:
        def resolve(self, relative_path, *, for_write, operation_minimum_free_bytes=0):
            assert for_write is False
            return tmp_path / relative_path

    def forbidden(*args):
        raise AssertionError("absent or partial publication cannot reach a codec or verifier")

    ports = EffectiveLawPosthocReadPorts(ReadOnlyRoot(), forbidden, forbidden, forbidden, "run", "run.one")
    arguments = dict(ports=ports, task_id="task.one", implementation_commit="b" * 40,
        implementation_sha256="a" * 64, expected_input_materialization_ids=())
    assert read_published_task(**arguments) is None
    output = tmp_path / "run/outputs/task.one/result.json"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"{}")
    with pytest.raises(ValueError, match="partial published state"):
        read_published_task(**arguments)
    assert tuple(path for path in tmp_path.rglob("*") if path.is_file()) == (output,)
