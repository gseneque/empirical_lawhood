# SPDX-License-Identifier: MPL-2.0
"""Closed copied-input publications over disclosed, non-executable records."""
from dataclasses import replace
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
from empirical_lawhood.infrastructure.artifacts import (
    ArtifactIdentityConflict, ExternalArtifactPlane, GuardedExternalRoot,
)
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, ExternalRootContract,
)


def _case(tmp_path, count=4):
    directory = tmp_path / 'selected'
    directory.mkdir()
    mount = next(path for path in directory.parents if path.is_mount())
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        'exposed.input-batch', 'Literal software input publication', str(directory), str(mount),
        'empirical-lawhood/testing/input-batch', 1)))
    parent = ArtifactLineageParent(ObjectIdentity('exposed.parent', ObjectIdentity.SCHEMA, '1.0.0', 'a' * 64),
        VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
    records = tuple((f'input.{index}.json',
        ObjectIdentity(f'exposed.value.{index}', ObjectIdentity.SCHEMA, '1.0.0', 'b' * 64))
        for index in range(count))
    records = tuple((name, record, ObjectIdentity.from_record(f'exposed.input.{index}', record))
        for index, (name, record) in enumerate(records))
    budget = SimpleNamespace(output_bytes=1024**2, memory_bytes=1024**2)
    context = MatrixProgrammeProjectionContext(SimpleNamespace(artifact_writer=plane),
        SimpleNamespace(specification=SimpleNamespace(operations=SimpleNamespace(metadata_budget=budget))),
        SimpleNamespace(commitments=SimpleNamespace(namespace='exposed.input-batch')),
        directory / 'programme', {}, {})
    return context, records, (parent,)


@pytest.mark.parametrize('count', (4, 32))
def test_copied_group_has_one_closed_roster_exact_bytes_and_constant_custody_boundaries(tmp_path, count):
    context, records, parents = _case(tmp_path, count)
    guards = []
    result = context.publish_records('e4.development', records, lineage_parents=parents,
        require_current=lambda: guards.append('current'))
    assert guards == ['current', 'current']
    relatives = {row.materialization.relative_path for row in result}
    batches = set()
    for (name, record, pin), row in zip(records, result, strict=True):
        assert row.logical.logical_artifact_id == pin.object_id
        assert row.logical.content_sha256 == record.fingerprint()
        assert row.logical.lineage_parents == parents
        assert row.logical.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
        assert row.logical.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
        path = context.metadata_directory('e4.development') / name
        assert path.read_bytes() == record.canonical_bytes()
        manifest = context.writer.read_manifest(row.materialization.relative_path)
        context.writer.verify_manifest(manifest)
        assert {member.relative_path for member in manifest.publication.members} == relatives
        batches.add(manifest.publication.publication_batch_id)
    assert len(batches) == 1
    replay = context.publish_records('e4.development', records, lineage_parents=parents)
    assert replay == tuple(replace(row, created=False) for row in result)


def test_existing_singletons_keep_their_original_publications_and_guards(tmp_path):
    context, records, parents = _case(tmp_path)
    original = tuple(context.publish_record('e4.development', name, record,
        identity=pin, lineage_parents=parents) for name, record, pin in records)
    before = tuple(context.writer.read_manifest(row.materialization.relative_path) for row in original)
    guards = []
    actual = context.publish_records('e4.development', records, lineage_parents=parents,
        require_current=lambda: guards.append('current'))
    assert actual == tuple(replace(row, created=False) for row in original)
    assert len(guards) == len(records)
    assert tuple(context.writer.read_manifest(row.materialization.relative_path) for row in actual) == before


def test_custom_single_write_hook_retains_every_original_call(tmp_path, monkeypatch):
    context, records, parents = _case(tmp_path)
    original, calls, guards = ExternalArtifactPlane.write, [], []

    def selected(self, request):
        calls.append(len(guards))
        return original(self, request)

    monkeypatch.setattr(ExternalArtifactPlane, 'write', selected)
    # The legacy hook keeps its per-record bound; it is not forced into a new
    # aggregate materialization or a new resource decision.
    context.plan.specification.operations.metadata_budget.output_bytes = max(
        record.canonical_size_bytes() for _, record, _ in records)
    context.publish_records('e4.development', records, lineage_parents=parents,
        require_current=lambda: guards.append('current'))
    assert calls == list(range(1, len(records) + 1))


@pytest.mark.parametrize('damage', ('bytes', 'access'))
def test_custody_is_current_after_all_copied_inputs_are_constructed_and_before_publication(tmp_path, damage):
    context, records, parents = _case(tmp_path)
    prior = context.writer.write(ArtifactWriteRequest('exposed.prior', 'prior/input.json', ObjectIdentity.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'exposed.prior', 'prior',
        records[0][1].canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    changed, requests = [], []
    prior_path = Path(context.writer.root.contract.canonical_path) / prior.materialization.relative_path

    def observe(frame, event, _value):
        if event == 'return' and frame.f_code is ArtifactWriteRequest.__post_init__.__code__:
            requests.append(True)
            if len(requests) == len(records):
                changed.append(True)
                if damage == 'bytes':
                    prior_path.write_bytes(prior_path.read_bytes() + b' ')

    with pytest.raises((PermissionError, ArtifactIdentityConflict)):
        with context.writer.read_context() as reading:
            reading.verify_manifest(reading.read_manifest(prior.materialization.relative_path))

            def current():
                if changed and damage == 'access':
                    raise PermissionError('exposed grant withdrawn')
                reading.require_verification_snapshot()

            assert sys.getprofile() is None
            sys.setprofile(observe)
            try:
                context.publish_records('e4.development', records,
                    lineage_parents=parents, require_current=current)
            finally:
                sys.setprofile(None)
    assert changed == [True]
    assert not context.metadata_directory('e4.development').exists()


def test_complete_input_group_is_bounded_before_any_publication(tmp_path):
    context, records, parents = _case(tmp_path)
    budget = context.plan.specification.operations.metadata_budget
    budget.output_bytes = max(record.canonical_size_bytes() for _, record, _ in records)
    with pytest.raises(ValueError, match='group exceeds'):
        context.publish_records('e4.development', records, lineage_parents=parents)
    assert not context.directory.exists()
