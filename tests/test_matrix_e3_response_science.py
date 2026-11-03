# SPDX-License-Identifier: MPL-2.0
"""Literal current consumers; no native acquisition or qualifying evidence.

The selected256 constant prefix retains its real numerical negative. Finite
cell projection controls below are authored metadata, never received science.
"""

from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal as D
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods import matrix_dataset_readers as datasets
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_science as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast, response_records as rr
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_history_segments, parameter_source
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.test_matrix_e3_response_records import arguments, case as case, completed_metadata


LIMITS = dict(maximum_chunk_bytes=65536, maximum_slice_bytes=1048576)


def blocked(*args, **kwargs):
    raise AssertionError("current response consumer entered a forbidden native/fit/spectral producer")


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    for module, name in ((parameter_history_segments, "acquire_parameter_segment"), (parameter_source, "acquire_parameter_history"),
            (parameter_history, "advance_parameter_pair")):
        monkeypatch.setattr(module, name, blocked)
    for name in ("Generator", "PCG64DXSM", "default_rng"):
        monkeypatch.setattr(np.random, name, blocked)
    monkeypatch.setattr(np.linalg, "eigh", blocked)
    monkeypatch.setattr(response_forecast, "_hessian", blocked)


def context(case, **changes):
    result = dict(prefix_config=case.config, **arguments(case))
    result.update(changes)
    return result


def score_config(case):
    return replace(case.native_config, operation="response-score",
        config_id=case.native_config.config_id.removesuffix("responses") + "response-score")


def public_context(case):
    return dict(specification=case.specification, protocol=case.protocol, numerical_profile=case.profile,
        mathematical_protocol=case.originals.mathematical, projection=case.originals.projection)


def store(case):
    publication = case.selection.template_publications[0]
    port = case.plane.open(VerifiedArtifactInput(publication.logical, publication.materialization), maximum_bytes=None)
    try:
        template = port.read()
    finally:
        port.close()
    return {case.history.arrays.array_artifact.artifact_id: case.native_raw,
        case.causal.arrays.array_artifact.artifact_id: case.causal_raw,
        case.protocol.templates.array_artifact.artifact_id: template,
        case.physical.arrays.array_artifact.artifact_id: case.physical_raw,
        case.response.arrays.array_artifact.artifact_id: case.response_raw}


def byte_fetch(values):
    return lambda artifact: values[artifact.artifact_id]


def test_seedless_physical_nonuse_preserves_original_array_bytes_and_complete_both_views(case):
    raw, record = owner.forecast_physical(case.physical_config, case.causal, **public_context(case), fetch=byte_fetch(store(case)),
        **LIMITS, artifact_id=case.physical.arrays.array_artifact.artifact_id, forecast_id=case.physical.forecast_id,
        outcome_access=case.physical.arrays.outcome_access, visibility_ceiling=case.physical.arrays.visibility_ceiling)
    assert raw == case.physical_raw and record == case.physical
    values = decode_matrix_arrays(raw, record.arrays)
    assert len(values) == 10 and all(value.shape == (4, 3, 48) and np.isnan(value).all() for value in values.values())
    assert record.disposition == "UNEVALUABLE" and all(status == "UNRESOLVED" for _, _, status, _ in record.dispositions)
    assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record


@pytest.mark.parametrize("delivery", ("bytes", "port", "dataset", "reader"))
def test_one_dataset_session_retains_complete_nonuse_score_and_both15_targets(case, monkeypatch, delivery):
    values, entered = store(case), []
    bridges = []
    originals = (case.history.arrays, case.causal.arrays, case.protocol.templates, case.physical.arrays, case.response.arrays)
    if delivery == "bytes":
        fetch = byte_fetch(values)
    elif delivery == "port":
        by_id = {}
        receipt = case.history.native.receipt
        logical = next(row for row in receipt.output_logical_artifacts if row.logical_artifact_id == case.history.arrays.array_artifact.artifact_id)
        physical = next(row for row in receipt.output_materializations if row.logical_artifact_id == logical.logical_artifact_id)
        by_id[logical.logical_artifact_id] = VerifiedArtifactInput(logical, physical)
        template = case.selection.template_publications[0]
        by_id[template.logical.logical_artifact_id] = VerifiedArtifactInput(template.logical, template.materialization)
        for index, original in enumerate((case.causal.arrays, case.physical.arrays, case.response.arrays)):
            artifact = original.array_artifact
            pub = case.plane.write(ArtifactWriteRequest(artifact.artifact_id, "literal/current-array-port-" + str(index) + ".npz",
                artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, artifact.media_type, "literal-array-port", "literal",
                values[artifact.artifact_id], original.visibility_ceiling, (), original.outcome_access))
            by_id[artifact.artifact_id] = VerifiedArtifactInput(pub.logical, pub.materialization)
        fetch = lambda artifact: case.plane.open(by_id[artifact.artifact_id], maximum_bytes=None)
    else:
        by_id = {}
        for original in originals:
            bridge = datasets.bridge_saved_arrays(original, values[original.array_artifact.artifact_id], **LIMITS)
            bridges.append(bridge)
            by_id[original.array_artifact.artifact_id] = bridge if delivery == "dataset" else bridge.reader
        fetch = lambda artifact: by_id[artifact.artifact_id]
    original_context = owner.retained_array_mappings

    @contextmanager
    def one_context(owners, fetch, **limits):
        entered.append(tuple(owners))
        assert len(entered) == 1
        with original_context(owners, fetch, **limits) as mappings:
            yield mappings

    monkeypatch.setattr(owner, "retained_array_mappings", one_context)
    try:
        score = owner.assess_responses(score_config(case), case.native_config, case.response, **context(case), fetch=fetch,
            **LIMITS, score_id="score.literal.current.nonuse")
    finally:
        for bridge in bridges:
            bridge.close()
    assert entered == [originals]
    assert score.disposition == "UNEVALUABLE" and not score.numerical_pass and not score.controls
    assert len(score.cells) == 240 and all(cell.actual_odd_responses is None and cell.normalized_error is None for cell in score.cells)
    assert score.cumulative_log_errors == (None,) * 15
    outcome = owner.project_outcome(score_config(case), case.native_config, case.response, score, **context(case), record_id="outcome.literal.current.nonuse")
    assert tuple(view.view_id for view in outcome.views) == ("fine", "primary")
    assert all(view.errors == (None,) * 15 and view.dispositions == ("NUMERICAL_FAILURE",) * 15 for view in outcome.views)
    assert outcome.numerical_disposition == "UNEVALUABLE"


@pytest.mark.parametrize("damage", ("prefix-config", "prefix-receipt", "wrong-source", "score-config", "frozen", "profile"))
def test_original_prefix_and_current_guards_refuse_before_opening_any_payload(case, damage):
    args, config = context(case), score_config(case)
    with pytest.raises((TypeError, ValueError)):
        if damage == "prefix-config":
            args["prefix_config"] = replace(case.config, record_id="config.matrix-e3-protected.foreign.prefix")
        elif damage == "prefix-receipt":
            history = case.history
            args["history"] = replace(history, native=replace(history.native, receipt=replace(history.native.receipt, task_id="native-subwork.literal.foreign")))
        elif damage == "wrong-source":
            args["source"] = replace(case.source, source_id="source.literal.foreign")
        elif damage == "score-config":
            config = case.native_config
        elif damage == "frozen":
            args["frozen"] = replace(case.frozen, record_id="freeze.literal.foreign")
        else:
            args["numerical_profile"] = replace(case.profile, native_reference_tolerance=case.profile.native_reference_tolerance * 2)
        owner.assess_responses(config, case.native_config, case.response, **args, fetch=blocked, **LIMITS, score_id="score.literal.refused")


def literal_score(case):
    """Complete paired cell/control values authored independently of reducer."""
    response, args, _ = completed_metadata(case)
    controls = tuple(ScheduledResponseTransitionControl("control.scheduled." + case.source.root_id + "." + branch,
        "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", D(0), case.protocol.native_reference_tolerance,
        "SATISFIED", 128 if view == "PRIMARY" else 256, 192, (D(0),) * (128 if view == "PRIMARY" else 256), ())
        for branch, view, *_ in rr.branch_census(case.protocol, case.panels))
    cells = []
    for view in ("PRIMARY", "FINE"):
        for panel_index, panel in enumerate(case.panels):
            for action_index, action in enumerate(case.protocol.actions):
                for predictor_index, predictor in enumerate(case.specification.measurement.descriptions):
                    for horizon_index, horizon in enumerate(case.protocol.horizon_steps):
                        value = D(predictor_index) + D(horizon_index) / 10 + D(panel_index) / 100 + D(action_index) / 1000 + (D("0.0001") if view == "FINE" else 0)
                        cells.append(rr.ScheduledResponseLossCell(view, panel.panel_id, action.action_id, predictor, horizon,
                            (D(1),) * 48, (value,) * 48, (value,) * 48, (value,) * 48, value))
    score = rr.ScheduledResponseScore("score.literal.current.full-cells", response.source, response.causal_prefix, response.error_forecast,
        response.physical_forecast, owner._object(response), case.source.root_id, case.error.feature.unit_id, case.source.root.root.role.value,
        case.protocol.criterion, controls, True, "FINITE", tuple(sorted(cells, key=lambda cell: cell.key)), (D(999),) * 15, ())
    return SimpleNamespace(response=response, args=dict(prefix_config=case.config, **args), score=score)


def test_literal_full240_cells_and48_receivers_reduce_both_views_without_primary_summary(case):
    literal = literal_score(case)
    result = owner.project_outcome(score_config(case), case.native_config, literal.response, literal.score, **literal.args,
        record_id="outcome.literal.current.full-cells")
    for view in result.views:
        assert view.errors == tuple(D(predictor) + D(horizon) / 10 + D("0.013") + (D("0.0001") if view.view_id == "fine" else 0)
            for predictor in range(5) for horizon in range(3))
        assert view.dispositions == ("FINITE",) * 15
    assert len(literal.score.cells) == 240 and len(literal.score.controls) == 48


@pytest.mark.parametrize("damage", ("cell", "receiver", "control", "forecast", "native-response", "root", "nonuse-finite"))
def test_current_target_refuses_denominator_and_exact_evidence_substitution(case, damage):
    literal = literal_score(case)
    response, score, args = literal.response, literal.score, literal.args
    with pytest.raises((TypeError, ValueError)):
        if damage == "cell":
            score = replace(score, cells=score.cells[:-1])
        elif damage == "receiver":
            score = replace(score, cells=(replace(score.cells[0], actual_odd_responses=score.cells[0].actual_odd_responses[:-1]), *score.cells[1:]))
        elif damage == "control":
            score = replace(score, controls=score.controls[:-1])
        elif damage == "forecast":
            score = replace(score, error_forecast=replace(score.error_forecast, object_fingerprint="e" * 64))
        elif damage == "native-response":
            score = replace(score, responses=replace(score.responses, object_fingerprint="e" * 64))
        elif damage == "root":
            score = replace(score, root_id="root.literal.foreign")
        else:
            response, args = case.response, context(case)
            score = replace(score, causal_prefix=response.causal_prefix, physical_forecast=response.physical_forecast,
                error_forecast=response.error_forecast, responses=owner._object(response))
        owner.project_outcome(score_config(case), case.native_config, response, score, **args, record_id="outcome.literal.refused")
