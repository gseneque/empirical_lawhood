# SPDX-License-Identifier: MPL-2.0
"""Original input boundaries retain selected siblings and final outer custody."""
from collections import Counter
from pathlib import Path
import sys

import pytest

from empirical_lawhood.infrastructure import artifacts
from empirical_lawhood.infrastructure.matrix_recorded_inputs import recorded_programme_inputs
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from tests.test_matrix_programme_source_continuation import metadata_case  # noqa: F401


def _history(case, suffix):
    record = ObjectIdentity('unrelated.' + suffix, ObjectIdentity.SCHEMA, '1.0.0', 'a' * 64)
    return case.case.writer.write(ArtifactWriteRequest(record.object_id, 'unrelated/' + suffix + '.json',
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', 'unrelated.' + suffix,
        'unrelated', record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))


def _options(case, writer):
    return dict(writer=writer, commitment=case.commitment,
        maximum_source_bytes=case.case.request.metadata_budget.source_scan_bytes)


def test_recorded_input_return_checks_its_publications_without_unrelated_history(metadata_case):  # noqa: F811
    case = metadata_case
    prior = _history(case, 'separate')
    paths = Counter()
    checkpoint = artifacts.ExternalArtifactPlane._require_verification_snapshot_paths.__code__

    def observe(frame, event, arg):
        if event == 'call' and frame.f_code is checkpoint:
            paths.update(frame.f_locals['snapshots'])

    with case.case.writer.read_context() as reading:
        reading.verify_manifest(reading.read_manifest(prior.materialization.relative_path))
        previous = sys.getprofile()
        try:
            with recorded_programme_inputs(**_options(case, reading)) as inputs:
                assert inputs.scientific_design == case.continued.scientific_design
                sys.setprofile(observe)
        finally:
            sys.setprofile(previous)
        selected = (case.commitment, inputs.commitments.scientific_design)
        root = Path(reading.root.contract.canonical_path)
        expected = set()
        for handle in selected:
            manifest = reading.read_manifest(handle.publication.materialization.relative_path)
            expected.add(root / manifest.publication.commit_marker_relative_path)
            for member in manifest.publication.members:
                expected.update((root / member.relative_path, root / (member.relative_path + '.manifest.json')))
        assert set(paths) == expected
        assert root / prior.materialization.relative_path in reading._read_verification.snapshots
        assert root / prior.materialization.relative_path not in paths
        with pytest.raises(PermissionError, match='escaped'):
            inputs.scientific_design


@pytest.mark.parametrize('damage', ('body', 'sidecar', 'marker', 'revoked'))
def test_recorded_input_return_refuses_changed_selected_custody(metadata_case, damage):  # noqa: F811
    case, allowed, returned = metadata_case, True, False
    plane = case.case.writer
    relative = case.commitment.publication.materialization.relative_path
    if damage == 'sidecar':
        relative += '.manifest.json'
    elif damage == 'marker':
        relative = plane.read_manifest(relative).publication.commit_marker_relative_path
    path = Path(plane.root.contract.canonical_path) / relative
    original = path.read_bytes()

    def access(_manifest):
        if not allowed:
            raise PermissionError('current recorded input access revoked')

    try:
        with pytest.raises((artifacts.ArtifactIdentityConflict, PermissionError)):
            with plane.read_context(before_member=access) as reading:
                with recorded_programme_inputs(**_options(case, reading)):
                    if damage == 'revoked':
                        allowed = False
                    else:
                        path.write_bytes(original + b' ')
                returned = True
        assert not returned
    finally:
        allowed = True
        if damage != 'revoked':
            path.write_bytes(original)


def test_recorded_input_boundary_keeps_unrelated_final_byte_guard(metadata_case):  # noqa: F811
    case = metadata_case
    prior = _history(case, 'changed-after-input')
    path = Path(case.case.writer.root.contract.canonical_path) / prior.materialization.relative_path
    original = path.read_bytes()
    try:
        with pytest.raises(artifacts.ArtifactIdentityConflict):
            with case.case.writer.read_context() as reading:
                reading.verify_manifest(reading.read_manifest(prior.materialization.relative_path))
                with recorded_programme_inputs(**_options(case, reading)):
                    pass
                path.write_bytes(original + b' ')
    finally:
        path.write_bytes(original)
