# SPDX-License-Identifier: MPL-2.0
"""Both version facades retain actual FILE and publication custody checks.

These are only uninterpreted disclosed software bytes. No scientific source,
pre-fit timing, population completeness, issue or qualification is asserted.
"""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_originals, protected_original_publications
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import corpus_artifact
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_recursive_public_service import _plane


@pytest.mark.parametrize('owner', (protected_original_publications, configured_protected_originals))
@pytest.mark.parametrize('kind', ('FILE', 'PUBLICATION'))
def test_shared_original_artifact_keeps_exact_bounds_identity_and_live_bytes(tmp_path, owner, kind):
    plane = _plane(tmp_path / 'actual-selected-root')
    raw = b'disclosed exact original source support'
    publication = plane.write(ArtifactWriteRequest('original.disclosed.custody', 'support/original.txt',
        'empirical-lawhood/source/checksummed-uninterpreted-public-bytes', ArtifactProfile.RAW_SOURCE_BYTES,
        'text/plain', 'control.original.custody', 'support', raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    artifact = corpus_artifact(publication)
    if kind == 'FILE':
        path = plane.root.resolve('originals/exact-selected-copy.txt', for_write=True)
        path.parent.mkdir()
        path.write_bytes(raw)
        custody = ExperimentFileInputBinding('original-support', artifact, '1.0.0', 'originals/exact-selected-copy.txt', len(raw))
    else:
        path = plane.root.resolve(publication.materialization.relative_path, for_write=False)
        custody = publication
    owner._authenticate_artifact(plane, artifact, custody)
    # A same-size copy/manifest is insufficient when the exact original identity
    # differs. This occurs before any native/training loader in both owners.
    with pytest.raises(ValueError, match='substitutes census audit/inventory identity'):
        owner._authenticate_artifact(plane, replace(artifact, artifact_id='foreign.original.identity'), custody)
    path.write_bytes(raw + b'x')
    with pytest.raises((ValueError, RuntimeError)):
        owner._authenticate_artifact(plane, artifact, custody)
    path.write_bytes(raw)
    owner._authenticate_artifact(plane, artifact, custody)
    if kind == 'PUBLICATION':
        manifest_path = plane.root.resolve(publication.materialization.relative_path + '.manifest.json', for_write=False)
        original = manifest_path.read_bytes()
        manifest_path.write_bytes(original + b' ')
        with pytest.raises((ValueError, RuntimeError)):
            owner._authenticate_artifact(plane, artifact, custody)
