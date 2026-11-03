# SPDX-License-Identifier: MPL-2.0
# ruff: noqa: F811
"""Typed metadata/prehash controls, not a completed source or scientific grant.

The canonical association, instance, allocation and current locator types are
real software records. The model body is intentionally undecodable and must
remain unopened in these controls. Actual full-chain science is a separate gate.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
from empirical_lawhood.api import prepared_source_replay as owner
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft, RecursiveScientificSelection
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from empirical_lawhood.runtime.prospective_experiment import (
    ALLOCATION_FILENAME, ASSOCIATION_FILENAME, INSTANCE_FILENAME, SPECIFICATION_FILENAME,
    ProspectiveExperimentAssociation, instance_identity, source_filename,
)
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_prepared_source_access import source_literals  # noqa: F401
from tests.test_matrix_finite_dt_source_assembly import c_backed_source_case  # noqa: F401
from tests.test_matrix_selected_opportunity import opportunity  # noqa: F401
from tests.test_matrix_selected_protected import confirmation, transfer  # noqa: F401
from tests.test_recursive_public_service import _plane
from tests.runtime_platform.test_recursive_compiler import Config


def _pin(identifier, kind, digest="a" * 64):
    return ObjectIdentity(identifier, kind.SCHEMA, kind.VERSION, digest)


def _case(tmp_path, source_literals, *, directory="original-source", candidate=None, bad_role=False):
    request, development = source_literals
    plane = _plane(tmp_path / "prepared-source-replay")
    raw = canonical_json_document_bytes({"schema": domain.MatrixPreparedSourceQualificationSelection.SCHEMA,
        "version": domain.MatrixPreparedSourceQualificationSelection.VERSION,
        "value": {"disclosed": "NO_MODEL_DECODE_OR_SOURCE_QUALIFICATION"}})
    model = _pin("selection.disclosed-producer-bootstrap", domain.MatrixPreparedSourceQualificationSelection,
        sha256(raw).hexdigest())
    specification = domain.MatrixPreparedSourceQualificationSpecification("spec.disclosed-producer-bootstrap", model, 1)
    allocation = UnitAllocation("allocation.disclosed-producer-bootstrap", (_pin("source.disclosed", Config),),
        (IndependentUnit("unit.disclosed", "source.disclosed", "family.disclosed", ("view.disclosed",), True),),
        (UnitRoleAssignment("unit.disclosed", "metadata-control"),))
    request_pin = ObjectIdentity.from_record("source-request", request)
    development_pin = ObjectIdentity.from_record("development.0", development)
    instance = ExperimentInstanceBinding(specification.identity, allocation.identity,
        _pin("draft.disclosed-producer-bootstrap", RecursiveStudyDraft),
        _pin("projection.disclosed-producer-bootstrap", RecursiveScientificSelection),
        _pin("campaign.disclosed", CampaignSpec, "c" * 64),
        tuple(sorted((model, request_pin, development_pin), key=lambda pin: pin.object_id)))
    data = {SPECIFICATION_FILENAME: (specification.identity, specification.canonical_bytes(), False),
        ALLOCATION_FILENAME: (allocation.identity, allocation.canonical_bytes(), False),
        INSTANCE_FILENAME: (instance_identity(instance), instance.canonical_bytes(), False),
        source_filename(model): (model, raw, True),
        source_filename(request_pin): (request_pin, request.canonical_bytes(), False),
        source_filename(development_pin): (development_pin, development.canonical_bytes(), False)}
    if bad_role:
        name = source_filename(request_pin)
        bad = Config("source-request", 17)
        data[name] = (ObjectIdentity.from_record("source-request", bad), bad.canonical_bytes(), False)
    members = tuple(RecursiveWaveMember(name, pin, len(body)) for name, (pin, body, _) in sorted(data.items()))
    association = ProspectiveExperimentAssociation("association.disclosed-producer-bootstrap",
        _pin("packet.disclosed-producer-bootstrap", AuthoredRecursiveWave),
        candidate or _pin("candidate.disclosed-producer-bootstrap", ExecutableStudyCandidate), instance_identity(instance), members)
    data[ASSOCIATION_FILENAME] = association.identity, association.canonical_bytes(), False
    rows = []
    prefix = directory + "/experiment"
    parent = ArtifactLineageParent(request.original_products[0].record,
        VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.EVALUATION_SEALED)
    for name, (pin, body, model_body) in sorted(data.items()):
        parents = (parent,) if model_body else ()
        publication = plane.write(ArtifactWriteRequest(association.association_id + "." + name.removesuffix(".json"),
            prefix + "/" + name, pin.object_schema, ArtifactProfile.CANONICAL_JSON, "application/json",
            association.association_id, prefix, body,
            VisibilityCeiling.DEVELOPMENT_ONLY if model_body else VisibilityCeiling.PROSPECTIVE,
            tuple(value.visibility_ceiling for value in parents),
            OutcomeAccess.EVALUATION_SEALED if model_body else OutcomeAccess.OUTCOME_BLIND, lineage_parents=parents))
        rows.append((pin, publication))
    return SimpleNamespace(plane=plane, association=association, instance=instance, data=data,
        rows=tuple(sorted(rows, key=lambda row: row[0].object_id)), prefix=prefix, model=model,
        model_path=plane.root.resolve(prefix + "/" + source_filename(model), for_write=False))


def _forbid_companion_bodies(case, monkeypatch, *, extra=()):
    import os
    actual = os.open
    forbidden = {case.plane.root.resolve(case.prefix + "/" + name, for_write=False)
        for name in case.data if name != ASSOCIATION_FILENAME}
    forbidden.update(extra)
    opened = []
    def opening(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path) in forbidden:
            pytest.fail("bootstrap metadata opened a protected/unneeded companion body")
        opened.append(str(path))
        return actual(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", opening)
    return opened


def test_exact_seven_rows_are_partitioned_without_any_companion_body(tmp_path, source_literals, monkeypatch):
    case = _case(tmp_path, source_literals)
    _forbid_companion_bodies(case, monkeypatch)
    scientific, bootstrap = owner.partition_prepared_source_publications(writer=case.plane, publications=case.rows)
    assert scientific == () and bootstrap == case.rows and len(bootstrap) == 7
    model_publication, = (publication for pin, publication in bootstrap if pin == case.model)
    assert model_publication.logical.outcome_access is OutcomeAccess.EVALUATION_SEALED
    assert model_publication.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY


@pytest.mark.parametrize("missing_schema", (domain.MatrixPreparedSourceQualificationSelection.SCHEMA,
    ExperimentInstanceBinding.SCHEMA, UnitAllocation.SCHEMA))
def test_missing_pinned_member_refuses_before_model_body(tmp_path, source_literals, monkeypatch, missing_schema):
    case = _case(tmp_path, source_literals)
    _forbid_companion_bodies(case, monkeypatch)
    rows = tuple(row for row in case.rows if row[0].object_schema != missing_schema)
    with pytest.raises(PermissionError, match="omits an association-pinned"):
        owner.partition_prepared_source_publications(writer=case.plane, publications=rows)


def test_unknown_companion_codec_refuses_before_any_companion_body(tmp_path, source_literals, monkeypatch):
    case = _case(tmp_path, source_literals, bad_role=True)
    _forbid_companion_bodies(case, monkeypatch)
    with pytest.raises(PermissionError, match="undeclared original companion"):
        owner.partition_prepared_source_publications(writer=case.plane, publications=case.rows)


def test_foreign_same_model_bytes_cannot_substitute_companion_publication(tmp_path, source_literals, monkeypatch):
    case = _case(tmp_path, source_literals)
    body = case.data[source_filename(case.model)][1]
    publication = case.plane.write(ArtifactWriteRequest("foreign.same-model-bytes", "foreign/model.json",
        case.model.object_schema, ArtifactProfile.CANONICAL_JSON, "application/json", "foreign", "foreign", body,
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.EVALUATION_SEALED))
    rows = tuple((pin, publication if pin == case.model else original) for pin, original in case.rows)
    _forbid_companion_bodies(case, monkeypatch,
        extra=(case.plane.root.resolve(publication.materialization.relative_path, for_write=False),))
    with pytest.raises(PermissionError, match="exact original companion publication"):
        owner.partition_prepared_source_publications(writer=case.plane, publications=rows)


def test_duplicate_association_is_not_an_alternative_locator(tmp_path, source_literals, monkeypatch):
    case = _case(tmp_path, source_literals)
    other = replace(case.association, association_id="association.foreign-bootstrap")
    publication = case.plane.write(ArtifactWriteRequest("foreign.association", "foreign/experiment-association.json",
        other.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "foreign", "foreign",
        other.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    rows = tuple(sorted((*case.rows, (other.identity, publication)), key=lambda row: row[0].object_id))
    _forbid_companion_bodies(case, monkeypatch,
        extra=(case.plane.root.resolve(publication.materialization.relative_path, for_write=False),))
    with pytest.raises(PermissionError, match="one exact original association"):
        owner.partition_prepared_source_publications(writer=case.plane, publications=rows)


def test_association_control_bound_refuses_before_even_its_body(tmp_path, source_literals, monkeypatch):
    case = _case(tmp_path, source_literals)
    publication, = (publication for pin, publication in case.rows if pin == case.association.identity)
    case.plane.custody_limits = replace(case.plane.custody_limits,
        control_record_bytes=publication.materialization.size_bytes - 1)
    import os
    actual = os.open
    body = case.plane.root.resolve(publication.materialization.relative_path, for_write=False)
    def opening(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path) == body:
            pytest.fail("over-bound association body was opened")
        return actual(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", opening)
    with pytest.raises(PermissionError, match="exact unprivileged locator metadata"):
        owner.partition_prepared_source_publications(writer=case.plane, publications=case.rows)


def _binding(package, plan):
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateEvidence
    return RecursivePriorExecutionBinding("binding.disclosed-source-package-join",
        ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
        ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority),
        ObjectIdentity.from_record(package.package_id, package), ObjectIdentity.from_record(plan.execution_plan_id, plan),
        package.run_plan_id, plan.tasks[0].task_id, _pin("receipt.unexecuted-package-join", CanonicalTaskReceipt),
        "output.unexecuted-package-join", _pin("gate.unexecuted-package-join", ScientificSourceGateEvidence),
        record_id_field="evidence_id")


@pytest.mark.parametrize("damage", ("candidate", "package", "authority"))
def test_actual_package_join_refuses_foreign_association_before_model(tmp_path, source_literals,
        actual_issued_current_task_controls, monkeypatch, damage):
    controls = actual_issued_current_task_controls
    package, plan = controls.control.package, controls.plan
    candidate = ObjectIdentity.from_record(package.issued_study.candidate.candidate_id, package.issued_study.candidate)
    case = _case(tmp_path, source_literals, candidate=candidate)
    binding = _binding(package, plan)
    assert owner._require_associated_package(case.association, package, binding) is None
    _forbid_companion_bodies(case, monkeypatch)
    association = case.association
    if damage == "candidate":
        association = replace(association, candidate=replace(candidate, object_fingerprint="f" * 64))
    elif damage == "package":
        binding = replace(binding, package=replace(binding.package, object_fingerprint="f" * 64))
    else:
        binding = replace(binding, execution_authority=replace(binding.execution_authority, object_fingerprint="f" * 64))
    with pytest.raises(PermissionError, match="actual producing package or candidate"):
        owner._require_associated_package(association, package, binding)


@pytest.mark.parametrize("damage", ("outside-root", "symlink"))
def test_writer_only_parser_keeps_real_directory_admission(tmp_path, monkeypatch, damage):
    from empirical_lawhood.api import recursive_prospective_authoring as parser
    plane = _plane(tmp_path / "writer-root")
    outside = tmp_path / "outside"
    outside.mkdir()
    directory = outside
    if damage == "symlink":
        directory = plane.root.resolve("linked", for_write=True)
        directory.symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(parser, "_prospective_selection_decoder",
        lambda *_args: pytest.fail("unadmitted directory reached packet parsing"))
    with pytest.raises(ValueError, match="outside its selected guarded root|symbolic links"):
        parser._read_recursive_prospective_members(directory=directory, artifact_writer=plane)


def _provenance_case(tmp_path, monkeypatch, *, damage=None):
    from empirical_lawhood.api import selected_prepared_access as access_owner
    from empirical_lawhood.api.recursive_prospective_authoring import ProspectiveSourceObservation
    from empirical_lawhood.planning.study_issue import (
        ImplementationSourceClosure, SelectedSourceManifest, SelectedSourceManifestMember, SourceClosureKind,
    )
    plane = _plane(tmp_path / "closed-source-provenance")
    manifest = SelectedSourceManifest("manifest.disclosed.operational", "a" * 40, "b" * 64, "c" * 64,
        (SelectedSourceManifestMember("README.md", "100644", 1, "d" * 64),))
    closure = ImplementationSourceClosure("closure.disclosed.operational", SourceClosureKind.EXACT_SOURCE_CLOSURE,
        manifest.implementation_commit, manifest.implementation_sha256, manifest.source_tree_sha256, True, manifest.identity)
    if damage == "manifest-pin":
        closure = replace(closure, exact_source_manifest=replace(manifest.identity, object_fingerprint="f" * 64))
    implementation = ObjectIdentity.from_record("recursive-member.implementation", closure)
    draft = Config("draft.disclosed.operational", 2)
    draft_pin = ObjectIdentity.from_record(draft.config_id, draft)
    members = (RecursiveWaveMember("draft.json", draft_pin, len(draft.canonical_bytes())),
        RecursiveWaveMember("implementation.json", implementation, len(closure.canonical_bytes())),
        RecursiveWaveMember("source-closure.json", ObjectIdentity.from_record("recursive-member.source-closure", closure),
            len(closure.canonical_bytes())))
    packet = AuthoredRecursiveWave("packet.disclosed.operational", draft_pin, implementation, members)
    prefix = "selected/prospective"
    packet_publication = plane.write(ArtifactWriteRequest(packet.packet_id + ".authored-wave", prefix + "/authored-wave.json",
        packet.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", packet.packet_id, prefix,
        packet.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    plane.write(ArtifactWriteRequest(packet.packet_id + ".source-closure", prefix + "/source-closure.json",
        closure.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", packet.packet_id, prefix,
        closure.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    # This is a disclosed closed operational body, not selected source admission.
    admission = {"policy": "selected-source-identities-v1", "raw_status_sha256": "e" * 64,
        "observed_checkout_clean": True, "changes": [], "selected_paths": ["README.md"],
        "selected_path_changes": [], "local_plan": None}
    observation = ProspectiveSourceObservation(closure.source_closure_id + ".source-observation",
        ObjectIdentity.from_record(closure.source_closure_id, closure), manifest.identity,
        canonical_json_document_bytes({"implementation_commit": manifest.implementation_commit,
            "implementation_sha256": manifest.implementation_sha256, "source_tree_sha256": manifest.source_tree_sha256,
            "tracked_files": [{"relative_path": "README.md", "mode": "100644", "size_bytes": 1, "sha256": "d" * 64}],
            "source_admission": admission, "final_source_admission": admission}).decode())
    provenance = prefix + "/provenance"
    scope_id = closure.source_closure_id + ".provenance"
    if damage == "scope":
        scope_id = "foreign.disclosed.provenance"
    requests = []
    for name, record in (("selected-source-manifest.json", manifest), ("source-observation.json", observation)):
        if damage == "codec" and name == "source-observation.json":
            record = Config("observation.disclosed.foreign-codec", 3)
        requests.append(ArtifactWriteRequest(scope_id + "." + name.removesuffix(".json"), provenance + "/" + name,
            record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", scope_id, provenance, record.canonical_bytes(),
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    if damage == "sibling":
        plane.write_batch((requests[0], replace(requests[0], logical_artifact_id="foreign.same-pair",
            relative_path=provenance + "/foreign.json")))
        plane.write(requests[1])
    else:
        for request in requests:
            plane.write(request)
    directory = plane.root.resolve("selected", for_write=False)
    scope = access_owner.SelectedPreparedOriginalInputAccess(plane, (), (), (), (), (), (), None,
        issued_directory=directory, issued_members=frozenset(((packet_publication.logical, packet_publication.materialization),)))
    clock = {"current": True, "calls": 0}
    def current(self, **kwargs):
        clock["calls"] += 1
        if not clock["current"]:
            raise PermissionError("DISCLOSED_PROVENANCE_GRANT_EXPIRED")
    monkeypatch.setattr(access_owner.SelectedPreparedOriginalInputAccess, "require_current", current)
    return SimpleNamespace(plane=plane, packet=packet, directory=directory, scope=scope, clock=clock,
        provenance=provenance)


def _forbid_provenance_bodies(case, monkeypatch):
    import os
    actual = os.open
    def opening(path, *args, **kwargs):
        name = Path(path).name
        if name in ("selected-source-manifest.json", "source-observation.json", "foreign.json"):
            pytest.fail("provenance metadata admission opened a body before its original member guard")
        return actual(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", opening)


def test_source_provenance_exact_two_controls_are_bound_without_opening_them(tmp_path, monkeypatch):
    case = _provenance_case(tmp_path, monkeypatch)
    _forbid_provenance_bodies(case, monkeypatch)
    bound = case.scope.bind_source_provenance(packet=case.packet, directory=case.directory)
    assert len(bound.issued_members) == 3
    assert len(case.scope.issued_members) == 1
    assert {Path(material.relative_path).name for _, material in bound.issued_members - case.scope.issued_members} == {
        "selected-source-manifest.json", "source-observation.json"}
    for name in ("selected-source-manifest.json", "source-observation.json"):
        assert bound.require_issued_member(case.plane.read_manifest(case.provenance + "/" + name)) is None
    assert case.clock["calls"] >= 4


@pytest.mark.parametrize("damage", ("manifest-pin", "scope", "codec", "sibling"))
def test_source_provenance_foreign_role_or_publication_refuses_before_body(tmp_path, monkeypatch, damage):
    case = _provenance_case(tmp_path, monkeypatch, damage=damage)
    _forbid_provenance_bodies(case, monkeypatch)
    with pytest.raises(PermissionError, match="closure-pinned|closed publication role"):
        case.scope.bind_source_provenance(packet=case.packet, directory=case.directory)


def test_source_provenance_bound_facts_do_not_admit_unknown_or_expired_members(tmp_path, monkeypatch):
    from empirical_lawhood.runtime.artifacts import ArtifactManifest
    case = _provenance_case(tmp_path, monkeypatch)
    _forbid_provenance_bodies(case, monkeypatch)
    bound = case.scope.bind_source_provenance(packet=case.packet, directory=case.directory)
    actual = case.plane.read_manifest(case.provenance + "/source-observation.json")
    foreign = ArtifactManifest(replace(actual.logical, logical_artifact_id="foreign.same-pair"),
        replace(actual.materialization, logical_artifact_id="foreign.same-pair"))
    with pytest.raises(PermissionError, match="actual producing closure"):
        bound.require_issued_member(foreign)
    case.clock["current"] = False
    with pytest.raises(PermissionError, match="GRANT_EXPIRED"):
        bound.require_issued_member(actual)


@pytest.mark.parametrize("damage", ("unbound-packet", "foreign-directory"))
def test_source_provenance_cannot_attach_controls_to_an_unrelated_bound_scope(tmp_path, monkeypatch, damage):
    case = _provenance_case(tmp_path, monkeypatch)
    _forbid_provenance_bodies(case, monkeypatch)
    scope, directory = case.scope, case.directory
    if damage == "unbound-packet":
        scope = replace(scope, issued_members=frozenset())
    else:
        directory = case.directory / "prospective"
    with pytest.raises(PermissionError, match="already-bound"):
        scope.bind_source_provenance(packet=case.packet, directory=directory)
