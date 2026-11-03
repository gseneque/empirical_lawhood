# SPDX-License-Identifier: MPL-2.0
"""Bounded authoring reads with exposed original-I/O seams and real custody.

The typed preparation, public authoring hook and artifact checks are real.
The original native reader is explicitly replaced by a literal publication;
these controls acquire no science and establish no scientific qualification.
"""
from dataclasses import replace
from pathlib import Path
import sys

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_bindings as methods
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import scope_reference
from empirical_lawhood.api import matrix_full_factor_access as access_owner
from empirical_lawhood.api import matrix_full_factor_authoring as owner
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
from tests.test_matrix_e4_full_factor_public import (
    ROOT, _development_access_seam, _published_secondary, _real_plane, selected,  # noqa: F401
)
from tests.test_matrix_e4_full_factor_values import scopes  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401


def _control(selected, tmp_path, monkeypatch):  # noqa: F811
    plane = _real_plane(tmp_path / 'exposed-authoring')
    selected, _, _ = _published_secondary(selected, plane)
    root = Path(plane.root.contract.canonical_path)
    reference = scope_reference(selected.scope)
    specification = replace(selected.specification, scope=selected.scope.identity,
        measurement=domain.measurement(selected.scope))
    files = []
    rows = [(methods.scope_input(selected.scope), selected.scope, reference.scope_artifact)]
    rows += [(methods.source_input(source), source, row.source_artifact)
        for source, row in zip(selected.scope.sources, reference.sources, strict=True)]
    assert all(source.full_arrays is None for source in selected.scope.sources)
    for number, (key, record, artifact) in enumerate(rows):
        raw = record.canonical_bytes()
        path = root / f'literal-{number}.json'
        path.write_bytes(raw)
        files.append((key, PreparedExperimentFile(artifact, record.VERSION, path, len(raw))))
    inputs = domain.ScheduledFullFactorFollowupInputs(request=selected.request,
        programme=selected.programme, bank=selected.bank, resources=selected.resources,
        campaign=selected.campaign, reference=reference, scope=selected.scope,
        files=tuple(sorted(files)), original_evidence=selected.evidence)
    execution = ExecutionSelection(workers=1, environment_id='environment.exposed-authoring',
        source_snapshot=ObjectIdentity('source.exposed', ObjectIdentity.SCHEMA, '1.0.0', 'a' * 64),
        output_root=str(root))
    preparation = domain.prepare(specification,
        scientific_inputs={'programme': domain.programme_allocation(selected.programme, selected.bank)},
        execution=execution, method_inputs=inputs)
    assert preparation.executable
    value = ObjectIdentity('original.exposed', ObjectIdentity.SCHEMA, '1.0.0', 'b' * 64)
    request = ArtifactWriteRequest('original.exposed', 'original.json', value.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'original.exposed', '.', value.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE)
    publication = plane.write(request)
    manifest = plane.read_manifest(publication.materialization.relative_path)
    _development_access_seam(monkeypatch, selected, plane)
    original = access_owner.development_original_access
    live = {'allowed': True, 'checks': 0}

    def current(_member):
        live['checks'] += 1
        if not live['allowed']:
            raise PermissionError('exposed grant revoked during authoring')

    def bootstrap(**kwargs):
        kwargs['artifact_writer'].verify_manifest(manifest, before_member=current)
        return original(**kwargs)

    def authenticate(**kwargs):
        kwargs['writer'].verify_manifest(manifest, before_member=current)
        return ()

    monkeypatch.setattr(access_owner, 'development_original_access', bootstrap)
    monkeypatch.setattr(owner, 'authenticate_original_full_factor_scope', authenticate)
    return plane, preparation, manifest, current, live, request


def test_structural_authoring_reuses_complete_publication_only_within_one_call(selected, tmp_path, monkeypatch):  # noqa: F811
    plane, preparation, manifest, _, live, _ = _control(selected, tmp_path, monkeypatch)
    observed = []
    code = ExternalArtifactPlane._verify_manifest_snapshot.__code__

    def observe(frame, event, _arg):
        if event == 'call' and frame.f_code is code and frame.f_locals['manifest'] == manifest:
            observed.append(manifest.materialization.relative_path)

    before = sys.getprofile()
    try:
        sys.setprofile(observe)
        for invocation in (1, 2):
            assert owner.prepare_authoring(preparation, project_root=ROOT, artifact_writer=plane,
                output_dir=Path(plane.root.contract.canonical_path) / 'unentered') == preparation
            assert len(observed) == invocation
    finally:
        sys.setprofile(before)
    assert live['checks'] >= 4
    assert not (Path(plane.root.contract.canonical_path) / 'unentered').exists()


@pytest.mark.parametrize('change', ('body', 'sidecar', 'revoked', 'publication', 'consumer-refusal'))
def test_structural_authoring_keeps_final_byte_access_and_effect_boundaries(selected, tmp_path, monkeypatch, change):  # noqa: F811
    plane, preparation, manifest, current, live, request = _control(selected, tmp_path, monkeypatch)
    root = Path(plane.root.contract.canonical_path)

    def authenticate(*, writer, **kwargs):
        writer.verify_manifest(manifest, before_member=current)
        if change in ('body', 'consumer-refusal'):
            path = root / manifest.materialization.relative_path
            path.write_bytes(path.read_bytes().replace(b'original.exposed', b'original.changed'))
        elif change == 'sidecar':
            path = root / (manifest.materialization.relative_path + '.manifest.json')
            path.write_bytes(path.read_bytes() + b' ')
        elif change == 'revoked':
            live['allowed'] = False
        elif change == 'publication':
            writer.write(replace(request, logical_artifact_id='new.exposed', relative_path='unexpected.json'))
        if change == 'consumer-refusal':
            raise ValueError('exposed consumer refusal after mutation')
        return ()

    monkeypatch.setattr(owner, 'authenticate_original_full_factor_scope', authenticate)
    expected = PermissionError if change == 'revoked' else ArtifactIdentityConflict
    with pytest.raises(expected):
        owner.prepare_authoring(preparation, project_root=ROOT, artifact_writer=plane,
            output_dir=root / 'unentered')
    assert not (root / 'unentered').exists()
    assert not (root / 'unexpected.json').exists()
