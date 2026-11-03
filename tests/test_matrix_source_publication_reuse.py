# SPDX-License-Identifier: MPL-2.0
"""Actual immutable metadata transport controls, without scientific qualification."""
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_source_runtime as owner
from empirical_lawhood.api.matrix_source_input_assembly import publish_source_input_record
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, derived_outcome_access, lineage_parent_sort_key
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from tests.test_recursive_public_service import _plane


def published(plane):
    value = InformationCutoff("cutoff.publication-reuse-control", "clock.publication-reuse-control",
        CausalPhase.PREPARATION, Decimal(0))
    result, observed = publish_source_input_record(writer=plane, prefix="control", namespace="publication-reuse",
        name="cutoff", record=value)
    return value, result, observed


def test_source_publisher_replays_stable_read_observation_without_changing_write_result(tmp_path):
    plane = _plane(tmp_path / "custody")
    value, first, observed = published(plane)
    _, second, replay = published(plane)
    assert first.created and not second.created
    assert not observed.created and observed.canonical_bytes() == replay.canonical_bytes()
    assert first.logical == observed.logical and first.materialization == observed.materialization
    with pytest.raises(ArtifactIdentityConflict):
        publish_source_input_record(writer=plane, prefix="control", namespace="publication-reuse", name="cutoff",
            record=replace(value, coordinate=Decimal(1)))


@pytest.mark.parametrize('access,visibility', (
    (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY),
    (OutcomeAccess.EVALUATION_REVEALED, VisibilityCeiling.OUTCOME_VISIBLE),
))
def test_source_publisher_preserves_actual_produced_parent_access_and_exact_retry(tmp_path, access, visibility):
    from empirical_lawhood.api.selected_e4_bank_recipe import _read_exact_record
    plane = _plane(tmp_path / 'produced-custody')
    value = InformationCutoff('cutoff.actual-produced-parent', 'clock.actual-produced-parent', CausalPhase.PREPARATION, Decimal(0))
    parents = tuple(sorted((ArtifactLineageParent(ObjectIdentity('original.actual-produced-parent',
        'empirical-lawhood/testing/disclosed-produced-parent', '1.0.0', 'a' * 64), visibility, access),
        ArtifactLineageParent(ObjectIdentity('original.actual-blind-parent',
            'empirical-lawhood/testing/disclosed-blind-parent', '1.0.0', 'b' * 64),
            VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)), key=lineage_parent_sort_key))
    first, observed = publish_source_input_record(writer=plane, prefix='produced', namespace='produced-source',
        name='cutoff', record=value, lineage_parents=parents)
    second, repeated = publish_source_input_record(writer=plane, prefix='produced', namespace='produced-source',
        name='cutoff', record=value, lineage_parents=parents)
    expected = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(parent.outcome_access for parent in parents))
    ceilings = tuple(parent.visibility_ceiling for parent in parents)
    assert first.created and not second.created
    assert observed.canonical_bytes() == repeated.canonical_bytes()
    assert observed.logical.lineage_parents == parents
    assert observed.logical.parent_visibility_ceilings == ceilings
    assert observed.logical.outcome_access is expected
    assert observed.logical.visibility_ceiling is inherited_visibility(ceilings, expected)
    assert plane.root.resolve(observed.materialization.relative_path, for_write=False).read_bytes() == value.canonical_bytes()
    assert _read_exact_record(plane, observed, type(value)) == value


@pytest.mark.parametrize("explicit", (True, False))
def test_source_publication_lookup_reads_only_missing_unique_original_inputs(tmp_path, monkeypatch, explicit):
    plane = _plane(tmp_path / "custody")
    value, _, observed = published(plane)
    pin = ObjectIdentity.from_record(value.cutoff_id, value)
    monkeypatch.setattr(owner, "matrix_source_publication_references", lambda *args: (pin,))
    import empirical_lawhood.infrastructure.provider_input_custody as locations
    calls = []
    def location(writer, run_id, logical_id):
        calls.append(logical_id)
        assert logical_id == observed.logical.logical_artifact_id
        return observed.materialization.relative_path, None, None
    monkeypatch.setattr(locations, "provider_input_location", location)
    external = SimpleNamespace(logical_artifact_id=observed.logical.logical_artifact_id,
        expected_payload_schema=value.SCHEMA, expected_content_sha256=value.fingerprint())
    irrelevant = SimpleNamespace(logical_artifact_id="unrelated.large-bank",
        expected_payload_schema="empirical-lawhood/testing/unrelated", expected_content_sha256="a" * 64)
    plan = SimpleNamespace(tasks=tuple(SimpleNamespace(external_inputs=(irrelevant, external)) for _ in range(9)))
    selection = SimpleNamespace(metadata_publications=((pin, observed),) if explicit else (),
        verification=SimpleNamespace(identity=pin) if explicit else SimpleNamespace(identity=ObjectIdentity(
            "unrelated.verification", "empirical-lawhood/testing/unrelated", "1.0.0", "b" * 64)),
        verification_publication=observed)
    evidence = SimpleNamespace(qualification_config=SimpleNamespace(specification=object()))
    rows = owner.retained_source_publications(writer=plane, package=SimpleNamespace(run_plan_id="run.lookup-control"),
        plan=plan, selection=selection, evidence=evidence, result=object())
    assert rows == ((pin, observed),)
    assert calls == ([] if explicit else [observed.logical.logical_artifact_id])
    if explicit:
        bad = replace(observed, logical=replace(observed.logical, content_sha256="f" * 64))
        selection.metadata_publications = ((pin, bad),)
        selection.verification_publication = bad
        with pytest.raises(PermissionError, match="exact retained metadata identity"):
            owner.retained_source_publications(writer=plane, package=SimpleNamespace(run_plan_id="run.lookup-control"),
                plan=plan, selection=selection, evidence=evidence, result=object())
