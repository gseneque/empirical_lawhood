# SPDX-License-Identifier: MPL-2.0
"""Exposed software checks for exact protected input facts, not E3 authority.

The small canonical record and finite counter isolate the domain caller and
first body-hash boundaries. They are not fitted E3 products or accepted grants;
the genuine protected producer/native DEV lifecycle remains a separate gate.
"""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.current_task_custody import CurrentDevelopmentTaskCustody
from empirical_lawhood.api.selected_e3_access import SelectedE3OriginalInputAccess
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.runtime_platform.test_recursive_compiler import Config
from tests.test_recursive_public_service import _plane


class _OriginalGuard:
    def __init__(self):
        self.samples = 0
        self.current = True

    def require_current(self):
        self.samples += 1
        if not self.current:
            raise PermissionError("disclosed original access expired")

    def require_member(self, manifest):
        raise PermissionError("unowned protected software member")


def _case(tmp_path, *, compact=False):
    plane = _plane(tmp_path / "exact-owned-inputs")
    record = Config("config.disclosed-selected-entry", 7)
    request = ArtifactWriteRequest("config.disclosed-selected-entry",
        "selected/entry.json", record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "publication.disclosed-selected-entry", "selected",
        record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (),
        OutcomeAccess.EVALUATION_SEALED)
    if compact:
        sibling = Config("config.disclosed-selected-sibling", 11)
        publications = plane.write_compact_batch((request, replace(request,
            logical_artifact_id=sibling.config_id, relative_path="selected/sibling.json",
            payload=sibling.canonical_bytes())))
    else:
        publications = (plane.write(request),)
    publication = publications[0]
    manifest = plane.read_manifest(publication.materialization.relative_path)
    value = VerifiedArtifactInput(manifest.logical, manifest.materialization)
    # The real constructor/complete protected bootstrap is exercised by the
    # installed lifecycle. This isolates its already-authenticated input census.
    custody = object.__new__(CurrentDevelopmentTaskCustody)
    custody.writer = plane
    custody.inputs = {row.logical.logical_artifact_id: VerifiedArtifactInput(row.logical, row.materialization)
        for row in publications}
    custody._original_member_facts = {(row.logical, row.materialization) for row in publications}
    custody.original_input_access = _OriginalGuard()
    custody.access_pair = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY
    custody.plan = SimpleNamespace(tasks=())
    return SimpleNamespace(plane=plane, record=record, manifest=manifest, value=value, custody=custody)


@pytest.mark.parametrize("compact", (False, True))
def test_exact_owned_sealed_control_keeps_its_custody_and_current_guard(tmp_path, compact):
    case = _case(tmp_path, compact=compact)
    with pytest.raises(PermissionError, match="lacks an exact owned protected input"):
        case.custody._manifest(case.value.materialization.relative_path)
    before = case.custody.original_input_access.samples
    manifest = case.custody._manifest(case.value.materialization.relative_path, expected=case.manifest)
    actual = case.custody.control_record(manifest, Config, len(case.record.canonical_bytes()))
    assert actual == case.record
    assert manifest == case.manifest
    assert manifest.logical.outcome_access is OutcomeAccess.EVALUATION_SEALED
    assert manifest.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
    assert case.custody.original_input_access.samples > before


@pytest.mark.parametrize("damage", ("logical-hash", "physical-hash", "width"))
@pytest.mark.parametrize("compact", (False, True))
def test_exact_owned_manifest_refuses_substitution_before_body_hash(tmp_path, monkeypatch, damage, compact):
    case = _case(tmp_path, compact=compact)
    logical, material = case.manifest.logical, case.manifest.materialization
    if damage == "logical-hash":
        logical = replace(logical, content_sha256="f" * 64)
    elif damage == "physical-hash":
        material = replace(material, physical_sha256="f" * 64)
    else:
        material = replace(material, size_bytes=material.size_bytes + 1)
    expected = ArtifactManifest(logical, material)
    monkeypatch.setattr(case.plane, "verify_manifest", lambda *_a, **_kw: pytest.fail("substitution reached body verification"))
    with pytest.raises(PermissionError, match="exact original publication path or development lane"):
        case.custody._manifest(case.manifest.materialization.relative_path, expected=expected)


@pytest.mark.parametrize("compact", (False, True))
def test_foreign_same_pair_publication_is_not_owned_input(tmp_path, monkeypatch, compact):
    case = _case(tmp_path, compact=compact)
    foreign = Config("config.disclosed-foreign-entry", 11)
    publication = case.plane.write(ArtifactWriteRequest(foreign.config_id,
        "foreign/entry.json", foreign.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "publication.disclosed-foreign-entry", "foreign",
        foreign.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (),
        OutcomeAccess.EVALUATION_SEALED))
    manifest = case.plane.read_manifest(publication.materialization.relative_path)
    assert (manifest.logical.outcome_access, manifest.logical.visibility_ceiling) == (
        case.manifest.logical.outcome_access, case.manifest.logical.visibility_ceiling)
    before = case.custody.original_input_access.samples
    from empirical_lawhood.infrastructure import artifacts as storage
    original_open = storage.os.open
    body = case.plane.root.resolve(manifest.materialization.relative_path, for_write=False)
    def guarded_open(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path) == body:
            pytest.fail("foreign protected body was opened")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(storage.os, "open", guarded_open)
    with pytest.raises(PermissionError, match="unowned protected software member"):
        case.custody._manifest(manifest.materialization.relative_path, expected=manifest)
    assert (manifest.logical, manifest.materialization) not in case.custody._original_member_facts
    assert case.custody.original_input_access.samples > before


@pytest.mark.parametrize("compact", (False, True))
def test_exact_owned_fact_does_not_cache_current_permission(tmp_path, monkeypatch, compact):
    case = _case(tmp_path, compact=compact)
    assert case.custody._manifest(case.value.materialization.relative_path, expected=case.manifest) == case.manifest
    case.custody.original_input_access.current = False
    monkeypatch.setattr(case.plane, "verify_manifest", lambda *_a, **_kw: pytest.fail("expired access reached body verification"))
    with pytest.raises(PermissionError, match="disclosed original access expired"):
        case.custody._manifest(case.value.materialization.relative_path, expected=case.manifest)


class _ReachedTypedControlBoundary(Exception):
    pass


@pytest.mark.parametrize("consumer", ("e4-development-entry", "e5-development-design"))
@pytest.mark.parametrize("compact", (False, True))
def test_domain_selected_config_forwards_exact_owned_fact_before_typed_body(tmp_path, monkeypatch, consumer, compact):
    case = _case(tmp_path, compact=compact)
    from empirical_lawhood.api import matrix_selected_e3_e4_runtime as e4
    from empirical_lawhood.api import matrix_selected_opportunity_runtime as e5
    runtime = e4 if consumer == "e4-development-entry" else e5
    key = runtime.owner.NAMESPACE + ".entry" if consumer == "e4-development-entry" else runtime.owner.COMMITTED_DESIGN_KEY
    task = SimpleNamespace(capability=SimpleNamespace(capability_key=key,
        capability_version="2.0.0", config=SimpleNamespace(artifact_id=case.value.artifact_id)))
    plan = SimpleNamespace(tasks=(task,))
    # This exact-class witness tests only constructor dispatch. Its fresh guard
    # is explicit test instrumentation, never an accepted original-product read.
    access = SelectedE3OriginalInputAccess(case.plane, (), (), (), ())
    monkeypatch.setattr(SelectedE3OriginalInputAccess, "require_current",
        lambda _self: case.custody.original_input_access.require_current())
    payloads = SimpleNamespace(original_input_access=access)
    def custody_factory(**values):
        assert values["writer"] is case.plane and values["plan"] is plan
        assert values["payloads"] is payloads and values["original_input_access"] is access
        return case.custody
    monkeypatch.setattr(runtime, "CurrentDevelopmentTaskCustody", custody_factory)
    def control_boundary(manifest, kind, maximum):
        assert manifest == case.manifest
        assert maximum == len(case.record.canonical_bytes())
        expected_kind = (runtime.owner.SelectedE3E4EntryConfig if consumer == "e4-development-entry"
            else runtime.MatrixSelectedOpportunityRootConfigV2)
        assert kind is expected_kind
        raise _ReachedTypedControlBoundary
    monkeypatch.setattr(case.custody, "control_record", control_boundary)
    kind = (runtime.SelectedE3E4DevelopmentRuntimeInputSupplier if consumer == "e4-development-entry"
        else runtime.SelectedOpportunityRuntimeInputSupplier)
    with pytest.raises(_ReachedTypedControlBoundary):
        kind(object(), writer=case.plane, directory=tmp_path, plan=plan, output_codecs={}, payloads=payloads)
    assert case.custody.original_input_access.samples >= 3
