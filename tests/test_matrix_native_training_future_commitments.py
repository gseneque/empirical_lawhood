# SPDX-License-Identifier: MPL-2.0
"""Actual metadata publication controls; no TRAIN/native/fit or freshness claim."""
from dataclasses import replace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_future_response_selections
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import corpus_artifact
from empirical_lawhood.infrastructure.artifacts import ArtifactPlaneError
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case


def _selections(case):
    """The actual four selector bodies already published in whole C before TRAIN."""
    return case.future_response_selections


def _declare(case, selections):
    """Publish only explicit adversarial replacements; never rewrite original C.

    The actual programme, clock and E6 policy retain their original publication
    custody. Negative partition controls change candidate selectors, so their
    positive byte support remains real while the scientific join must refuse.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
    baseline = r.future_response_support(case.request)
    selector_rows = {reference: (artifact, publication) for reference, artifact, publication in baseline
        if reference.object_schema == ScheduledResponseSelection.SCHEMA}
    retained = tuple((reference, artifact, publication) for reference, artifact, publication in baseline
        if reference.object_schema != ScheduledResponseSelection.SCHEMA)
    rows = [(artifact, publication) for _, artifact, publication in retained]
    pins = [reference for reference, _, _ in retained]
    for value in selections:
        if value.identity in selector_rows:
            artifact, publication = selector_rows[value.identity]
        else:
            publication = publish(case.plane, value, value.selection_id)
            artifact = corpus_artifact(publication)
        rows.append((artifact, publication));pins.append(value.identity)
    original_artifacts = {artifact for _, artifact, _ in baseline}
    exposure = tuple(row for row in case.request.exposure_support if row[0] not in original_artifacts)
    request = replace(case.request, campaign=replace(case.request.campaign,
        evidence_state=tuple(sorted(pins, key=lambda value: value.object_id))),
        exposure_support=tuple(sorted((*exposure, *rows), key=lambda value: value[0].artifact_id)))
    return request, case.future_availability


def _independent(selection):
    return next(panel for _, panels in selection.panels for panel in panels if panel.role == "INDEPENDENT_FUTURE")


def _replace_streams(selection, streams):
    panel = _independent(selection)
    return replace(selection, selection_id=selection.selection_id + ".changed",
        panels=tuple((group, tuple(replace(value, streams=streams) if value.panel_id == panel.panel_id else value
            for value in panels)) for group, panels in selection.panels))


def test_prior_whole_programme_publications_authenticate_all_seven_inputs_before_train(tmp_path):
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    case = fresh_training_metadata_case(tmp_path)
    original = case.request.canonical_bytes()
    support = r.future_response_support(case.request)
    assert len(support) == 7
    assert sum(reference.object_schema == MatrixProgrammeInputCommitments.SCHEMA for reference, _, _ in support) == 1
    assert case.request.input_commitments.publication in tuple(publication for _, _, publication in support)
    expected = r.validate_future_response_selections(case.request, _selections(case), case.future_availability)
    assert tuple(role for role, _ in expected) == ("CALIBRATION", "EVALUATION", "TRANSFER_NEARBY", "TRANSFER_SHIFTED")
    assert authenticate_future_response_selections(case.plane, case.request) == expected
    r.validate_request(case.specification, case.request)
    assert case.request.canonical_bytes() == original
    assert case.request.VERSION == "3.0.0"
    assert decode_canonical_bytes(original, r.NativeTrainingAcquisitionRequest, maximum_bytes=len(original)).canonical_bytes() == original
    with pytest.raises(TypeError, match="complete pre-acquisition programme commitment"):
        replace(case.request, input_commitments=None)
    with pytest.raises(ValueError, match="whole programme|future selection|availability|policy"):
        r.future_response_support(replace(case.request, campaign=replace(case.request.campaign, evidence_state=())))
    for retired in ("1.0.0", "2.0.0"):
        document = case.request.to_document();document["version"] = retired
        with pytest.raises(ValueError, match="unsupported canonical document version"):
            decode_canonical_bytes(canonical_json_document_bytes(document), r.NativeTrainingAcquisitionRequest, maximum_bytes=None)


def test_declared_future_commitment_cannot_drop_one_publication_or_replace_it_with_a_file_copy(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    request, _ = _declare(case, _selections(case))
    support = r.future_response_support(request)
    assert len(support) == 7
    original = request.canonical_bytes()
    for reference, artifact, publication in support:
        missing = replace(request, exposure_support=tuple(value for value in request.exposure_support if value[0] != artifact))
        with pytest.raises(ValueError, match="every future|commit|custody"):
            r.future_response_support(missing)
        copied = ExperimentFileInputBinding(artifact.artifact_id, artifact, reference.object_version,
            publication.materialization.relative_path, artifact.size_bytes)
        substituted = replace(request, exposure_support=tuple((value, copied if value == artifact else handle)
            for value, handle in request.exposure_support))
        with pytest.raises(ValueError, match="actual blind canonical|FILE"):
            r.future_response_support(substituted)
    assert request.canonical_bytes() == original



@pytest.mark.parametrize("damage", ("duplicate-role", "wrong-allocation", "train-panel", "other-future-role"))
def test_future_response_partition_refuses_exact_role_allocation_or_effective_stream_alias(tmp_path, damage):
    case = fresh_training_metadata_case(tmp_path)
    selections = list(_selections(case))
    if damage == "duplicate-role":
        selections[1] = replace(selections[0], selection_id="responses.disclosed.future.duplicate-role")
    elif damage == "wrong-allocation":
        allocation = case.request.future_manifest.reservation.allocation
        changed = replace(allocation, allocation_id=allocation.allocation_id + ".changed")
        changed_pin = old.identity(changed)
        protocols = tuple(replace(value, public_source=replace(value.public_source, allocation=changed_pin))
            for value in selections[0].protocols)
        selections[0] = replace(selections[0], selection_id=selections[0].selection_id + ".changed",
            allocation=changed_pin, protocols=protocols)
    else:
        streams = (_independent(selections[1]).streams if damage == "other-future-role" else
            next(value.streams for value in case.request.panels if value.role == "INDEPENDENT_FUTURE"))
        selections[0] = _replace_streams(selections[0], streams)
    selections = tuple(sorted(selections, key=lambda value: value.selection_id))
    request, availability = _declare(case, selections)
    with pytest.raises(ValueError, match="role|allocation|overlap|TRAIN"):
        r.validate_future_response_selections(request, selections, availability)


def test_actual_future_publication_byte_mutation_is_refused_before_train_entry(tmp_path):
    case = fresh_training_metadata_case(tmp_path)
    request, _ = _declare(case, _selections(case))
    assert authenticate_future_response_selections(case.plane, request)
    support = r.future_response_support(request)
    assert len(support) == 7
    for _, _, publication in support:
        path = case.plane.root.resolve(publication.materialization.relative_path, for_write=False)
        raw = path.read_bytes()
        try:
            path.write_bytes(b" " + raw[1:])  # Disposable metadata controls only.
            with pytest.raises((ArtifactPlaneError, ValueError, PermissionError)):
                authenticate_future_response_selections(case.plane, request)
        finally:
            path.write_bytes(raw)
    assert authenticate_future_response_selections(case.plane, request)
