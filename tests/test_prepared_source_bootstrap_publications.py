# SPDX-License-Identifier: MPL-2.0
"""Actual companion metadata handles over explicitly unissued source literals.

No model body is decoded or opened, and no authority/qualification is claimed.
The complete scientific group allocation is retained from the fixture.
"""
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.matrix_prepared_source_experiment import prepared_source_bootstrap_publications
from empirical_lawhood.api.prospective_experiment import RetainedProspectiveExperiment
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.runtime.prospective_experiment import ProspectiveExperimentAssociation, instance_identity, source_filename
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from tests.test_prepared_source_access import source_literals, _selected_case  # noqa: F401
from tests.test_matrix_finite_dt_source_assembly import c_backed_source_case  # noqa: F401
from tests.test_matrix_selected_opportunity import opportunity  # noqa: F401
from tests.test_matrix_selected_protected import confirmation, transfer  # noqa: F401


def _case(tmp_path, source_literals, confirmation, monkeypatch):  # noqa: F811
    from tests.test_matrix_prepared_source import prepared_bank
    from tests.test_recursive_public_service import _draft
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
    c = _selected_case(tmp_path, source_literals, monkeypatch)
    directory = c.plane.root.resolve("retained-source", for_write=True)
    (directory / "experiment").mkdir(parents=True)
    bank, draft = prepared_bank(confirmation), _draft()
    allocation = UnitAllocation("allocation.disclosed.bootstrap-emission", (c.request.prepared_programme,),
        tuple(IndependentUnit(group, c.request.prepared_programme.object_id, "family.disclosed.source",
            ("fine", "primary"), False) for group in bank.group_ids),
        tuple(UnitRoleAssignment(group, "source") for group in bank.group_ids))
    request_pin = ObjectIdentity.from_record("source-request", c.request)
    dev_pin = ObjectIdentity.from_record("development.0", c.development)
    sources = tuple(sorted((c.specification.selection, request_pin, dev_pin), key=lambda row: row.object_id))
    instance = ExperimentInstanceBinding(c.specification.identity, allocation.identity,
        ObjectIdentity.from_record(draft.draft_id, draft),
        ObjectIdentity("projection.disclosed.source-emission", draft.SCHEMA, draft.VERSION, "b" * 64),
        ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign), sources)
    model = c.plane.root.resolve("selection.json", for_write=False).read_bytes()
    records = {"experiment-specification.json": (c.specification.identity, c.specification.canonical_bytes()),
        "experiment-allocation.json": (allocation.identity, allocation.canonical_bytes()),
        "experiment-instance.json": (instance_identity(instance), instance.canonical_bytes()),
        source_filename(c.specification.selection): (c.specification.selection, model),
        source_filename(request_pin): (request_pin, c.request.canonical_bytes()),
        source_filename(dev_pin): (dev_pin, c.development.canonical_bytes())}
    members = tuple(RecursiveWaveMember(name, pin, len(raw)) for name, (pin, raw) in sorted(records.items()))
    association = ProspectiveExperimentAssociation("association.disclosed.source-emission",
        ObjectIdentity("packet.disclosed.source-emission", AuthoredRecursiveWave.SCHEMA, AuthoredRecursiveWave.VERSION, "c" * 64),
        ObjectIdentity("candidate.disclosed.source-emission", ExecutableStudyCandidate.SCHEMA, ExecutableStudyCandidate.VERSION, "d" * 64),
        instance_identity(instance), members)
    records["experiment-association.json"] = association.identity, association.canonical_bytes()
    manifests, originals = [], {}
    for filename, (pin, raw) in sorted(records.items()):
        parents = c.scope.parents if pin == c.specification.selection else ()
        pair = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE if parents else OutcomeAccess.OUTCOME_BLIND,
            declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY if parents else VisibilityCeiling.PROSPECTIVE, parents=parents)
        relative = "retained-source/experiment/" + filename
        publication = c.plane.write(ArtifactWriteRequest("publication.disclosed." + filename.removesuffix(".json"), relative,
            pin.object_schema, ArtifactProfile.CANONICAL_JSON, "application/json", "disclosed.source-emission",
            "retained-source/experiment", raw, pair[1], tuple(row.visibility_ceiling for row in parents), pair[0], lineage_parents=parents))
        manifest = c.plane.read_manifest(relative)
        manifests.append(manifest)
        originals[pin] = publication
    scope = replace(c.scope, issued_specification=c.specification, issued_directory=directory,
        issued_members=frozenset((row.logical, row.materialization) for row in manifests))
    # Only association/instance metadata are consumed by the emitter. These
    # absent science/provider fields prevent mistaking this for a full loader.
    retained = RetainedProspectiveExperiment(association, instance, None, None, None, None, {}, scope)
    return SimpleNamespace(case=c, retained=retained, scope=scope, originals=originals, manifests=manifests,
        allocation=allocation, expected_group_ids=bank.group_ids, source_request=c.request, model=model)


@pytest.mark.parametrize("damage", ("none", "missing-member", "foreign-same-body", "expired"))
def test_emitter_retains_exact_seven_original_handles_without_any_payload_open(tmp_path, source_literals, confirmation, monkeypatch, damage):  # noqa: F811
    import os
    f = _case(tmp_path, source_literals, confirmation, monkeypatch)
    c = f.case
    selected = f.retained
    if damage == "missing-member":
        dev, = (pin for pin in selected.instance.sources if pin.object_id == "development.0")
        selected = replace(selected, association=replace(selected.association,
            members=tuple(row for row in selected.association.members if row.filename != source_filename(dev))))
    elif damage == "foreign-same-body":
        original = c.plane.read_manifest
        def foreign(path, **kwargs):
            actual = original(path, **kwargs)
            if path.endswith(source_filename(c.specification.selection)):
                logical = replace(actual.logical, logical_artifact_id="foreign.source-model.publication")
                physical = replace(actual.materialization, logical_artifact_id=logical.logical_artifact_id)
                return ArtifactManifest(logical, physical)
            return actual
        monkeypatch.setattr(c.plane, "read_manifest", foreign)
    elif damage == "expired":
        from empirical_lawhood.infrastructure import publication_metadata
        original = publication_metadata.read_publication_metadata
        def expires(*args, **kwargs):
            result = original(*args, **kwargs)
            c.clock["current"] = False
            return result
        monkeypatch.setattr(publication_metadata, "read_publication_metadata", expires)
    bodies = {str(c.plane.root.resolve(row.materialization.relative_path, for_write=False)) for row in f.manifests}
    original_open = os.open
    def metadata_only(path, *args, **kwargs):
        if str(path) in bodies:
            pytest.fail("source bootstrap emitter opened a companion/model body")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(os, "open", metadata_only)
    monkeypatch.setattr(c.plane, "verify_manifest", lambda *_a, **_k: pytest.fail("metadata emitter hashed a companion/model body"))
    before_request = f.source_request.canonical_bytes()
    if damage != "none":
        with pytest.raises(PermissionError, match="census|outside|foreign|EXPIRED"):
            prepared_source_bootstrap_publications(writer=c.plane, selected=selected, access=f.scope)
        return
    rows = prepared_source_bootstrap_publications(writer=c.plane, selected=selected, access=f.scope)
    assert len(rows) == 7 and tuple(pin.object_id for pin, _ in rows) == tuple(sorted(pin.object_id for pin, _ in rows))
    assert {pin for pin, _ in rows} == set(f.originals)
    for pin, handle in rows:
        actual = f.originals[pin]
        assert not handle.created
        assert (handle.logical, handle.materialization, handle.manifest_materialization) == (
            actual.logical, actual.materialization, actual.manifest_materialization)
    model = dict(rows)[c.specification.selection]
    assert model.logical.lineage_parents == f.scope.parents
    assert model.logical.content_sha256 == sha256(f.model).hexdigest()
    assert f.source_request.canonical_bytes() == before_request
    assert tuple(value.unit_id for value in f.allocation.units) == f.expected_group_ids
    assert tuple(value.unit_id for value in f.allocation.roles) == f.expected_group_ids
