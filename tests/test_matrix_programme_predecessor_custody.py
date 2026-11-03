# SPDX-License-Identifier: MPL-2.0
"""Nested predecessor reads share bytes, never access or execution authority."""
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
import sys

import pytest

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
from empirical_lawhood.infrastructure import artifacts
from tests.test_matrix_programme_binding_batch import _case


def _fixture(tmp_path, monkeypatch):
    case = _case(tmp_path / 'artifacts', count=4, shape='shared')
    publications = case.result.publications
    manifests = tuple(case.plane.read_manifest(row.materialization.relative_path) for row in publications)
    state = {'allowed': True, 'access': 0}

    def access(manifest):
        state['access'] += 1
        if not state['allowed']:
            raise PermissionError('exposed predecessor access revoked')

    @contextmanager
    def context(self, depth, *, operation=None):
        # Disclosed scientific-context seam. The actual publication, byte and
        # access owners remain in use across the complete nested read.
        with self.writer.read_context() as reading:
            reading.verify_manifests(manifests, before_member=access)
            if depth:
                child = type(self)(service=self.service, descriptor=self.descriptor)
                read = getattr(child, '_read_context', child._context)
                with read(depth - 1, operation=operation):
                    yield reading
            else:
                yield reading

    monkeypatch.setattr(MatrixResearchProgrammeService, '_context', context)
    service = ExperimentProgrammeService(tmp_path, case.plane)
    owner = MatrixResearchProgrammeService(service=service)
    return case, owner, state


def test_predecessor_chain_validates_shared_publication_once(tmp_path, monkeypatch, record_property):
    case, owner, state = _fixture(tmp_path, monkeypatch)
    counts = Counter()
    physical = artifacts.ExternalArtifactPlane._verify_manifest_snapshot.__code__

    def profile(frame, event, arg):
        if event == 'call' and frame.f_code is physical:
            counts['physical_members'] += 1

    read = getattr(owner, '_read_context', owner._context)
    previous = sys.getprofile()
    sys.setprofile(profile)
    try:
        with read(3):
            pass
    finally:
        sys.setprofile(previous)
    record_property('predecessor_depth', 4)
    record_property('physical_member_validations', counts['physical_members'])
    assert counts['physical_members'] == len(case.result.publications)
    assert state['access'] >= 4 * len(case.result.publications)
    # A later operation must establish its own proof.
    with read(0) as reading:
        assert reading is not owner.writer


@pytest.mark.parametrize('damage', ('body', 'revoked'))
def test_predecessor_lifetime_rejects_late_changes(tmp_path, monkeypatch, damage):
    case, owner, state = _fixture(tmp_path, monkeypatch)
    read = getattr(owner, '_read_context', owner._context)
    with pytest.raises((PermissionError, ValueError, RuntimeError)):
        with read(3):
            if damage == 'body':
                path = case.plane.root.resolve(case.result.publications[0].materialization.relative_path,
                    for_write=False)
                path.write_bytes(b'{}\n')
            else:
                state['allowed'] = False


def test_predecessor_session_does_not_change_execution_service(tmp_path, monkeypatch):
    _, owner, _ = _fixture(tmp_path, monkeypatch)
    original = owner.service
    read = getattr(owner, '_read_context', owner._context)
    with read(1) as reading:
        assert owner.service is original
        assert owner.writer is original.artifact_writer
        assert reading is not owner.writer
    assert replace(original, artifact_writer=owner.writer) == original
    with pytest.raises((PermissionError, ValueError, RuntimeError)):
        reading.require_active_verification_scope()
