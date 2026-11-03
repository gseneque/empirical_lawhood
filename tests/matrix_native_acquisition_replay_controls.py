# SPDX-License-Identifier: MPL-2.0
"""Received-record adversaries over the existing disclosed actual native run.

No new task, source/body publication, receipt or native contact is created.
The direct semantic consumer receives canonically resealed records; ordinary
receipt/body rejection is independently owned by the public common reader.
"""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import pytest


def assert_actual_replay_rejects_changed_records(*, case, products, draft, plan, training, monkeypatch):
    from empirical_lawhood.api.matrix_native_acquisition_replay import replay_root
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
    if training:
        from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
        from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as owner
    else:
        from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
        from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
    configs = dict(owner.contracts(case.specification, case.request)[0])
    tasks = {task.task_id: task for task in plan.tasks}
    root_id = case.specification.root_ids[0]  # Existing disclosed literal000 only.
    manifest = case.request.train_manifest if training else case.request.source_manifest
    source_index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    source_index.require_roster(case.request.sources, expected_root_ids=case.specification.root_ids)
    source = r.source_for(case.request, root_id, index=source_index)
    protocol, = (value for value in case.request.protocols if value.public_source.root.root_id == root_id)
    panels = r.panels_for(case.request, source)
    names = {"history": "prefix", "checkpoint": "prefix", "numerical": "numerical", "witness": "measure",
        "frames": "check", "causal": "project", "physical": "physical-forecast", "responses": "responses",
        "score": "response-score", "outcome": "response-score"}
    if training:
        names["feature"] = "feature"
    selected = {}
    for name, phase in names.items():
        label = "checkpoint" if name == "checkpoint" else "score" if name == "score" else "product"
        task = owner.task_id(root_id, phase)
        selected[name] = products["records"][task][task + "." + label]
    arguments = dict(artifact_writer=case.plane, specification=case.specification, request=case.request,
        seal=case.acquisition, source=source, protocol=protocol, panels=panels, configurations=configs,
        products=products, tasks=tasks, plan=plan)
    # Actual score arithmetic may be unavailable or negative. Changing even a
    # reason preserves that science while still testing exact record replay.
    old_score = selected["score"]
    errors = tuple(value + Decimal(1) if value is not None else None for value in old_score.cumulative_log_errors)
    if old_score.dense is not None and errors != old_score.cumulative_log_errors:
        with pytest.raises(ValueError, match='targets'):
            replace(old_score, cumulative_log_errors=errors)
    wrong_score = replace(old_score, cumulative_log_errors=errors) if old_score.dense is None and errors != old_score.cumulative_log_errors else replace(
        old_score, reason_codes=("resealed-changed-score",))
    wrong_outcome = selected["outcome"]
    if training:
        wrong_outcome = replace(wrong_outcome, evidence=tuple(sorted(
            (wrong_score.identity if value == selected["score"].identity else value for value in wrong_outcome.evidence),
            key=lambda value: value.object_id)))
    else:
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_science import assess_score
        wrong_outcome = assess_score(case.specification, protocol, panels, case.acquisition, wrong_score)
    wrong_score.canonical_bytes()
    wrong_outcome.canonical_bytes()
    with pytest.raises(PermissionError, match="score/outcome replayed"):
        replay_root(**arguments, records={**selected, "score": wrong_score, "outcome": wrong_outcome})
    if training:
        feature = selected["feature"]
        assert feature.disposition == "AVAILABLE"
        values = tuple((name, value + Decimal(1) if name == "trace_energy" else value) for name, value in feature.values)
        if values == feature.values:
            name, value = next((name, value) for name, value in feature.values if name != "cutoff" and not name.startswith("family-"))
            values = tuple((key, item + Decimal(1) if key == name else item) for key, item in feature.values)
        wrong_feature = replace(feature, values=values)
        wrong_feature.canonical_bytes()
        with pytest.raises(PermissionError, match="feature values derived"):
            replay_root(**arguments, records={**selected, "feature": wrong_feature})
    # The real stores and exact array descriptors are still used; observe actual
    # decoding counts in one positive semantic replay, with no persistent cache.
    from empirical_lawhood.api import matrix_native_acquisition_replay as replay
    calls = []
    decode = replay.decode_matrix_arrays
    def counted(raw, descriptor):
        calls.append((sha256(raw).hexdigest(), descriptor.fingerprint()))
        return decode(raw, descriptor)
    derived = []
    validate = replay.validate_derived_arrays
    def observed(**kwargs):
        derived.append(kwargs)
        return validate(**kwargs)
    templates = {}
    with monkeypatch.context() as patch:
        patch.setattr(replay, "decode_matrix_arrays", counted)
        patch.setattr(replay, "validate_derived_arrays", observed)
        assert replay_root(**arguments, records=selected, template_arrays=templates) == selected["outcome"]
        assert len(calls) == len(set(calls)) == 6
        # The same full-read pure template cache avoids another decode. All
        # root-native and derived arrays are read/rechecked in the second call.
        assert replay_root(**arguments, records=selected, template_arrays=templates) == selected["outcome"]
    assert len(calls) == 11 and len(templates) == 1
    actual = derived[0]
    causal = selected["causal"]
    wrong_causal = replace(causal, disposition="UNEVALUABLE", frame_sha256=None,
        reason="resealed-suppressed-causal-origin")
    wrong_physical = replace(selected["physical"], causal_prefix=wrong_causal.identity)
    wrong_causal.canonical_bytes()
    wrong_physical.canonical_bytes()
    with pytest.raises(PermissionError, match="actual causal cutoff/origin/nonuse"):
        validate(**{**actual, "records": {**selected, "causal": wrong_causal, "physical": wrong_physical}})
    wrong_physical = replace(selected["physical"],
        disposition="NO_ORIGIN" if selected["physical"].disposition != "NO_ORIGIN" else "UNEVALUABLE")
    wrong_physical.canonical_bytes()
    with pytest.raises(PermissionError, match="physical availability/nonuse"):
        validate(**{**actual, "records": {**selected, "physical": wrong_physical}})
