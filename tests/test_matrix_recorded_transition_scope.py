# SPDX-License-Identifier: MPL-2.0
"""Publication and retained transition custody use separate live owners."""
from contextlib import contextmanager
from pathlib import Path

import pytest

from empirical_lawhood.api import matrix_programme_recorded_lineage as owner
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_recursive_public_service import _plane


@pytest.mark.parametrize('changed', (False, True))
def test_recorded_transition_keeps_its_snapshot_through_the_caller(changed, tmp_path, monkeypatch):
    plane = _plane(tmp_path / 'artifacts')
    root = Path(plane.root.contract.canonical_path)
    request = ArtifactWriteRequest('transition.control', 'transition/control.json',
        'empirical-lawhood/testing/transition-control', ArtifactProfile.CANONICAL_JSON,
        'application/json', 'transition.control', 'transition',
        b'{"schema":"empirical-lawhood/testing/transition-control","value":{},"version":"1.0.0"}\n',
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
    plane.write(request)
    service = ExperimentProgrammeService(Path(__file__).parents[1], plane, None)
    context = MatrixProgrammeProjectionContext(service, None, None, root, {}, {})
    readers = []

    @contextmanager
    def transition(actual_owner, reading, record):
        assert actual_owner is owner and record is request
        assert reading is not context and reading.bindings is context.bindings
        assert reading.service.artifact_writer is not plane
        reading.writer.require_active_verification_scope()
        reading.writer.verify_manifest(reading.writer.read_manifest(request.relative_path))
        readers.append(reading.writer)
        reading.bindings['observed'] = request.logical_artifact_id
        yield
        reading.writer.require_verification_snapshot()

    monkeypatch.setattr(owner, '_recorded_continuation_context', transition)

    def consume():
        with owner.recorded_continuation_context(owner, context, request):
            assert context.service.artifact_writer is plane
            assert context.bindings == {'observed': request.logical_artifact_id}
            if changed:
                (root / request.relative_path).write_bytes(request.payload + b' ')

    if changed:
        with pytest.raises(ArtifactIdentityConflict):
            consume()
    else:
        consume()
    with pytest.raises(ArtifactIdentityConflict, match='ended'):
        readers[0].require_active_verification_scope()
