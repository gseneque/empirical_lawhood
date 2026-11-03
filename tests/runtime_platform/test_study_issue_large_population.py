# SPDX-License-Identifier: MPL-2.0
"""Complete public issue inventories beyond the former 256-member ceiling.

The reference design and accountable-owner/source inspector scaffolding are
existing exposed software fixtures. The additional preparation metadata has
actual canonical bytes, guarded publications and exact qualification records;
its count makes no claim about fresh or independent scientific observations.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

import pytest

from empirical_lawhood.api.facade import EmpiricalLawhoodApi
from empirical_lawhood.api.results import OperationStatus
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.study_issue import ExternalIssuedStudyPublisher
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.candidate_compiler import ContentIdentityPolicy
from tests.approval_support import FixedDecisionClock
from tests.experiment_entry_support import standard_authoring_for_draft
from tests.numerical_provenance_fixtures import numerical_plane
from tests.runtime_platform.test_candidate_compiler import _coverage_for, _fixture
from tests.runtime_platform.test_study_issue import (
    _AuthorityStore,
    _PassthroughSourceInspector,
    _issue_api_fixture,
    _issue_request,
)
from tests.standard_candidate_support import FixedStandardCandidateContextProvider


SOURCE_COUNT = 239  # 18 fixed standard members + 239 qualifications = 257.


@dataclass(frozen=True, slots=True)
class ExposedPreparationMetadata(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/fixtures/reference-source"

    record_id: str
    system: ObjectIdentity
    disclosure: str


def _large_standard_fixture(directory):
    draft, context = _fixture()
    assert draft.system is not None and draft.experiment is not None
    template = context.template(draft.dag_template_key)
    assert template is not None
    system = ObjectIdentity.from_record(draft.system.system_id, draft.system)
    observation = ObjectIdentity.from_record(draft.system.relation.relation_id, draft.system.relation)
    originals = numerical_plane(directory)
    # The test's explicitly selected output directory may be on an external
    # volume. Bind its actual mount instead of the helper's root-volume default.
    mounted = next(parent for parent in (directory.resolve(), *directory.resolve().parents) if parent.is_mount())
    originals = ExternalArtifactPlane(GuardedExternalRoot(replace(
        originals.root.contract, required_mount_path=str(mounted))))
    records = tuple(ExposedPreparationMetadata(
        f"source.issue-population-{index:03d}", system,
        "Exposed preparation metadata; not a fresh scientific observation.",
    ) for index in range(SOURCE_COUNT))
    requests = tuple(ArtifactWriteRequest(
        logical_artifact_id=record.record_id,
        relative_path=f"originals/{record.record_id}.json",
        payload_schema=record.SCHEMA,
        profile=ArtifactProfile.CANONICAL_JSON,
        media_type="application/json",
        publication_scope_id="software.issue-population-originals",
        publication_scope_relative_root="originals",
        payload=record.canonical_bytes(),
        visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
        parent_visibility_ceilings=(),
        outcome_access=OutcomeAccess.OUTCOME_BLIND,
    ) for record in records)
    published = originals.write_batch(requests)
    qualifications, sources, external, edges = [], [], [], []
    original_source = draft.source_materializations[0]
    original_external = template.graph.external_inputs[0]
    original_edge, = (edge for edge in template.graph.edges if edge.external_input_id is not None)
    for index, (record, request, result) in enumerate(zip(records, requests, published, strict=True)):
        raw = originals.root.resolve(result.materialization.relative_path, for_write=False).read_bytes()
        assert raw == record.canonical_bytes()
        assert sha256(raw).hexdigest() == result.materialization.physical_sha256
        materialization = ObjectIdentity.from_record(result.materialization.materialization_id, result.materialization)
        qualification = replace(context.qualifications[0],
            receipt_id=f"qualification.issue-population-{index:03d}", source_id=record.record_id,
            materialization=materialization, content_sha256=sha256(raw).hexdigest(),
            observation_operator=observation)
        qualifications.append(qualification)
        sources.append(replace(original_source, source_id=record.record_id,
            materialization=materialization, content_sha256=qualification.content_sha256,
            source_config_sha256=record.fingerprint(), observation_operator=observation,
            qualification_receipt=ObjectIdentity.from_record(qualification.receipt_id, qualification)))
        external.append(replace(original_external, input_id=record.record_id,
            logical_artifact_id=request.logical_artifact_id,
            content_identity_policy=ContentIdentityPolicy.EXACT_SHA256,
            expected_content_sha256=qualification.content_sha256,
            maximum_size_bytes=len(raw)))
        edges.append(replace(original_edge, edge_id=f"edge.issue-population-{index:03d}.prepare",
            external_input_id=record.record_id, consumer_input_id=f"source-{index:03d}",
            logical_artifact_id=request.logical_artifact_id, maximum_size_bytes=len(raw)))
    graph = replace(template.graph, external_inputs=tuple(external), edges=tuple(sorted(
        (*edges, *(edge for edge in template.graph.edges if edge.external_input_id is None)),
        key=lambda value: value.edge_id)))
    template = replace(template, graph=graph, coverage=_coverage_for(draft.experiment, template.protocol, graph))
    # Preserve the existing design and units; only its complete source inventory
    # changes. The readiness input's materialization now also has actual bytes.
    design_input = replace(draft.design_inputs[0], materialization_sha256=draft.system.fingerprint())
    draft = replace(draft, source_materializations=tuple(sources), design_inputs=(design_input,))
    context = replace(context, templates=(template,), qualifications=tuple(qualifications),
        known_design_inputs=(design_input,))
    authoring, standard = standard_authoring_for_draft(draft, context)
    return authoring, standard, originals, tuple(qualifications)


def _census(directory):
    return {path.relative_to(directory).as_posix():
        (path.stat().st_size, sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in directory.rglob("*") if path.is_file()}


def test_public_standard_issue_preserves_complete_large_inventory_and_atomic_custody(tmp_path):
    authoring, context, originals, qualifications = _large_standard_fixture(tmp_path / "originals")
    original_census = _census(Path(originals.root.contract.canonical_path))
    api, paths, external, authority = _issue_api_fixture(tmp_path,
        standard_fixture=lambda: (authoring, context))
    preview = api.issue_study(_issue_request(paths, confirmed=False))
    assert preview.status is OperationStatus.BLOCKED and preview.payload is not None
    assert not tuple(external.iterdir())
    issued = api.issue_study(_issue_request(paths, confirmed=True))
    assert issued.status is OperationStatus.SUCCEEDED, (issued.reason_codes, issued.errors)
    assert issued.payload is not None and issued.payload.publication_receipt is not None
    manifest, receipt = issued.payload.manifest, issued.payload.publication_receipt
    assert len(manifest.members) == SOURCE_COUNT + 18 == 257
    assert len(receipt.publication.members) == len(manifest.members) + 1 == 258
    assert receipt.declared_member_ids == tuple(member.member_id for member in manifest.members)
    assert manifest.materialization_qualifications == qualifications
    assert manifest.candidate.base_candidate.source_qualification_receipts == tuple(
        ObjectIdentity.from_record(value.receipt_id, value) for value in qualifications)
    assert manifest.authoring_package == authoring
    assert manifest.custody_authority == ObjectIdentity.from_record(authority.authority_id, authority)
    qualified_members = tuple(member for member in manifest.members
        if member.payload_schema == MaterializationQualificationReceipt.SCHEMA)
    assert len(qualified_members) == SOURCE_COUNT
    retained_qualifications = tuple(decode_canonical_bytes(
        (external / member.relative_path).read_bytes(), MaterializationQualificationReceipt,
        maximum_bytes=1024**2) for member in qualified_members)
    assert retained_qualifications == qualifications
    for member in manifest.members:
        raw = (external / member.relative_path).read_bytes()
        assert len(raw) == member.size_bytes and sha256(raw).hexdigest() == member.physical_sha256
    publisher = ExternalIssuedStudyPublisher(
        artifact_plane=ExternalArtifactPlane(api._study_issue_publisher.artifact_plane.root),
        authority_store=_AuthorityStore(authority), grantee_id="operator.issue-service")
    assert publisher.load_study(manifest.issue_id).manifest == manifest
    before = _census(external)
    replay = api.issue_study(_issue_request(paths, confirmed=True))
    assert replay.status is OperationStatus.SUCCEEDED and replay.payload == issued.payload
    assert _census(external) == before
    first_sidecar = publisher.artifact_plane.read_manifest(manifest.members[0].relative_path)
    victim = qualified_members[-1]
    for path, replacement in (
        (external / victim.relative_path, b"corrupted exposed fixture qualification"),
        (external / (victim.relative_path + ".manifest.json"), None),
        (external / receipt.publication.commit_marker_relative_path, b"corrupted publication marker"),
    ):
        original = path.read_bytes()
        if replacement is None:
            path.unlink()
        else:
            path.write_bytes(replacement)
        try:
            with pytest.raises(ArtifactIdentityConflict):
                publisher.artifact_plane.verify_manifest(first_sidecar)
            with pytest.raises(ArtifactIdentityConflict):
                publisher.load_study(manifest.issue_id)
        finally:
            path.write_bytes(original)
    assert publisher.load_study(manifest.issue_id).manifest == manifest
    assert _census(Path(originals.root.contract.canonical_path)) == original_census


def test_public_standard_issue_explicit_finite_member_allowance_refuses_before_publication(tmp_path, caplog):
    authoring, context, _originals, _qualifications = _large_standard_fixture(tmp_path / "originals")
    api, paths, external, authority = _issue_api_fixture(tmp_path,
        standard_fixture=lambda: (authoring, context))
    publisher = ExternalIssuedStudyPublisher(
        artifact_plane=ExternalArtifactPlane(api._study_issue_publisher.artifact_plane.root,
            custody_limits=ArtifactCustodyLimits(publication_members=256)),
        authority_store=_AuthorityStore(authority), grantee_id="operator.issue-service")
    finite = EmpiricalLawhoodApi(repo_root=tmp_path, external_root=external,
        candidate_context_provider=FixedStandardCandidateContextProvider(context),
        study_issue_publisher=publisher, study_source_closure_inspector=_PassthroughSourceInspector(),
        study_issue_clock=FixedDecisionClock(clock_id="clock.large-issue-finite", value="2026-07-24T20:32:00Z"))
    result = finite.issue_study(_issue_request(paths, confirmed=True))
    assert result.status is OperationStatus.FAILED
    assert result.reason_codes == ("PROGRAMME_ISSUE_PUBLICATION_FAILED",)
    assert any(record.exc_info
        and isinstance(record.exc_info[1], ArtifactIdentityConflict)
        and "member-count bound" in str(record.exc_info[1]) for record in caplog.records)
    assert not tuple(external.iterdir())
