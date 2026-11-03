# SPDX-License-Identifier: MPL-2.0
"""Actual source metadata and bounded custody; no completion or native claims."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme.completed_source import (
    MatrixCompletedE3InputSource, validate_completed_inputs,
)
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import MatrixProgrammeSourceContinuationSpecification
from empirical_lawhood.api.matrix_programme_source_continuation import _publish_inputs
from empirical_lawhood.api.matrix_researcher_programme import _publish
from empirical_lawhood.infrastructure.matrix_completed_source import original_e3_commitment, original_e3_programme_inputs
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.infrastructure.matrix_retained_training import authenticated_retained_training_source
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from tests.test_matrix_programme_retained_training_continuation import retained_case  # noqa: F401
from tests.test_matrix_programme_source_continuation import metadata_case  # noqa: F401


@pytest.fixture(scope='module')
def completed_case(retained_case):  # noqa: F811
    value = retained_case
    writer = value.case.writer
    root = Path(writer.root.contract.canonical_path)
    predecessor = MatrixProgrammePublishedInput(value.target_plan.identity,
        _publish(writer, root / 'completed-source-original/matrix-programme.json', value.target_plan))
    request = MatrixProgrammeSourceContinuationSpecification('request.disclosed-completed-source',
        predecessor, 'completed-source-target')
    provenance = replace(value.continued.producing_provenance, observed_git_head='e' * 40)
    source = MatrixCompletedE3InputSource('source.disclosed-completed-e3', request.identity,
        value.commitment, value.continued.producing_provenance.identity, provenance.identity)

    def publish(key, record, *, identity=None):
        publication = _publish(writer, root / 'completed-source-target' / (key + '.json'), record)
        return MatrixProgrammePublishedInput(record.identity if identity is None else identity, publication)

    commitment = _publish_inputs(value.continued, provenance, publish,
        record_id='commitments.disclosed-completed-e3', completed_source=source)
    budget = value.case.request.metadata_budget.source_scan_bytes
    with authenticated_programme_inputs(writer=writer, commitment=commitment, maximum_source_bytes=budget) as inputs:
        validate_completed_inputs(value.continued, inputs, source)
    return SimpleNamespace(original=value, writer=writer, commitment=commitment, inputs=inputs,
        source=source, budget=budget)


def test_completed_source_preserves_train_and_original_e3_provenance_in_live_read(completed_case):
    case = completed_case
    source_bytes = case.source.canonical_bytes()
    assert decode_canonical_bytes(source_bytes, MatrixCompletedE3InputSource, maximum_bytes=None) == case.source
    with authenticated_programme_inputs(writer=case.writer, commitment=case.commitment,
            maximum_source_bytes=case.budget) as current:
        assert current.producing_provenance != case.original.continued.producing_provenance
        assert case.original.support in [publication for _, publication in current.commitments.support_files]
        assert original_e3_commitment(case.writer, current, case.commitment) == case.original.commitment
        with original_e3_programme_inputs(writer=case.writer, inputs=current,
                maximum_source_bytes=case.budget) as original:
            assert original == case.original.continued
            with authenticated_retained_training_source(writer=case.writer, inputs=original,
                    maximum_source_bytes=case.budget) as (retained, training):
                assert retained == case.original.lineage
                assert training == case.original.original
    assert case.source.canonical_bytes() == source_bytes


def test_prepared_source_checks_original_train_while_returning_current_future_inputs(completed_case, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_publications
    from empirical_lawhood.api.matrix_prepared_source_runtime import _committed_e4_selections
    case = completed_case
    retained = case.original.lineage
    request = SimpleNamespace(input_commitments=retained.input_commitments,
        identity=retained.export_adoption.request)
    # Only the native request body is a disclosed seam. Actual C/D source
    # publications and all source/lineage joins remain authenticated here.
    observed = []
    monkeypatch.setattr(native_training_publications, 'validate_request_programme_inputs',
        lambda selected, inputs: observed.append((selected, inputs)))
    with _committed_e4_selections(writer=case.writer, commitment=case.commitment,
            request=request, native_training_locator=retained.training_locator,
            maximum_source_bytes=case.budget) as inputs:
        assert inputs == case.inputs
        assert observed == [(request, case.original.original)]


@pytest.mark.parametrize('change', ('original-source', 'target-source', 'folds', 'support', 'chain'))
def test_completed_source_refuses_relabeling_or_changes_to_original_science(completed_case, change):
    case = completed_case
    original, current, source = case.original.continued, case.inputs, case.source
    with pytest.raises((ValueError, PermissionError)):
        if change == 'original-source':
            source = replace(source, original_provenance=case.original.original.producing_provenance.identity)
        elif change == 'target-source':
            source = replace(source, target_provenance=case.original.original.producing_provenance.identity)
        elif change == 'folds':
            group, fold = current.commitments.revision_folds[0]
            current = replace(current, commitments=replace(current.commitments,
                revision_folds=((group, fold + 1), *current.commitments.revision_folds[1:])))
        elif change == 'support':
            current = replace(current, commitments=replace(current.commitments,
                support_files=tuple(row for row in current.commitments.support_files if row[1] != case.original.support)))
        else:
            original = current
        validate_completed_inputs(original, current, source)


@pytest.mark.parametrize('target', ('original', 'source'))
def test_completed_source_keeps_original_bytes_guarded_through_use(completed_case, target):
    case = completed_case
    relative = (case.original.commitment.publication.materialization.relative_path if target == 'original'
        else next(publication.materialization.relative_path for artifact, publication in case.inputs.commitments.support_files
            if artifact == case.source.artifact))
    path = case.writer.root.resolve(relative, for_write=False)
    raw = path.read_bytes()
    try:
        with pytest.raises((ValueError, PermissionError, RuntimeError)):
            with authenticated_programme_inputs(writer=case.writer, commitment=case.commitment,
                    maximum_source_bytes=case.budget):
                path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    finally:
        path.write_bytes(raw)
