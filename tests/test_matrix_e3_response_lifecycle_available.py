# SPDX-License-Identifier: MPL-2.0
"""Exposed current response-worker conformance over a declared causal state.

The AVAILABLE causal state and its support references are authored software
operands. They are not promoted from the retained negative prefix assessment.
The paired future is actually integrated, receipted, independently assessed and
recovered. No source qualification, fresh experiment or issue authority follows.
"""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_records import project_protected_e3_response_numerics
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_forecast, science as prefix_science
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history, parameter_history_segments, parameter_source
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from tests.test_matrix_e3_response_preparation import (
    case as case, error_operands, forbid_native as forbid_native,
    original_case as original_case, prepared,
)
from tests.test_matrix_e3_response_records import publication, qualification
from tests.test_matrix_scheduled_response_forecast import pauli


def blocked(*args, **kwargs):
    raise AssertionError("available response cold check entered acquisition or a producer")


@pytest.fixture(scope="module")
def available(case):
    """A separate finite causal operand; original negative records stay exact."""
    result = SimpleNamespace(**vars(case))
    result.response_lifecycle_counter = 1000
    result.original_negative_bytes = (case.causal.canonical_bytes(), case.numerical.canonical_bytes(), case.frames.canonical_bytes())
    frame = np.asarray([np.kron(p, np.eye(2)) / 2 for p in pauli()], dtype="<c16")
    complement = np.asarray([np.kron(np.eye(2), p) / 2 for p in pauli()], dtype="<c16")
    templates = dict(generic_basis=complement,
        force_coefficients=np.stack((np.eye(3), np.eye(3))).astype("<f8") / np.sqrt(6),
        trace_coefficients=np.ones((2, 3), dtype="<f8") / np.sqrt(6),
        receiver_coefficients=np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4))
    raw, operand = response_forecast.array_product(case.protocol, templates, role="TEMPLATES",
        artifact_id="literal.available.templates", producers=(case.native_config.source.identity,),
        access=Access.OUTCOME_BLIND, visibility=Visibility.PROSPECTIVE)
    template_pub = case.plane.write(ArtifactWriteRequest(operand.array_artifact.artifact_id, "literal/available-templates.npz",
        operand.array_artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "literal-available-response",
        "literal", raw, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    result.protocol = replace(case.protocol, templates=operand)
    result.selection = replace(case.selection, template_publications=(template_pub,), root_protocols=tuple(
        (root, owner._object(result.protocol) if root == case.source.root_id else ref) for root, ref in case.selection.root_protocols))
    selected_pub = publication(case, result.selection, "available-selection")
    result.profile = project_protected_e3_response_numerics(result.protocol, provenance=result.selection,
        publication=selected_pub, qualification=qualification(result.selection, selected_pub, "available-selection"))
    result.physical_config = replace(case.physical_config, protocol=owner._object(result.protocol), numerical_profile=identity(result.profile))
    result.native_config = replace(case.native_config, response_selection=identity(result.selection),
        protocol=owner._object(result.protocol), numerical_profile=identity(result.profile))
    causal_values = dict(decode_matrix_arrays(case.causal_raw, case.causal.arrays))
    causal_values["frame"] = frame
    # These explicit support references name an authored positive control. The
    # actual negative numerical/witness/frame records are never relabelled.
    supports = tuple(ObjectIdentity("literal.available." + name, ref.object_schema, ref.object_version, "a" * 64)
        for name, ref in (("numerical", case.causal.numerical), ("witness", case.causal.witness), ("frames", case.causal.frame_assessment)))
    numerical, witness, frames = supports
    result.causal_raw, operand = prefix_science._array_product(case.source, causal_values, role="CAUSAL_STATE",
        artifact_id="literal.available.causal-arrays", producers=(case.native_config.source.identity, identity(case.history), witness, frames))
    result.causal = replace(case.causal, record_id="causal.literal.available", numerical=numerical, witness=witness,
        frame_assessment=frames, frame_sha256=sha256(frame.tobytes()).hexdigest(), disposition="AVAILABLE", reason=None, arrays=operand)
    result.models, result.frozen, error = error_operands(result, result.causal, available=True)
    result.error = replace(error, feature=replace(error.feature, evidence=tuple(sorted((identity(result.causal), *supports), key=lambda row: row.object_id))))
    result.physical_raw, result.physical = owner.science.forecast_physical(result.physical_config, result.causal,
        specification=result.specification, protocol=result.protocol, numerical_profile=result.profile,
        mathematical_protocol=result.originals.mathematical, projection=result.originals.projection,
        fetch=lambda artifact: {result.causal.arrays.array_artifact.artifact_id: result.causal_raw,
            result.protocol.templates.array_artifact.artifact_id: raw}[artifact.artifact_id], **owner.LIMITS,
        artifact_id="literal.available.physical-arrays", forecast_id="physical.literal.available",
        outcome_access=Access.OUTCOME_BLIND, visibility_ceiling=Visibility.PROSPECTIVE)
    assert result.physical.disposition == "AVAILABLE"
    return result


def test_available_physical_worker_uses_complete_cold_witnesses_and_seedless_ports(available):
    selected = prepared(available, "physical-forecast")
    result = selected.runner.execute(selected.bound)
    payloads = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in result.outputs}
    physical = decode_canonical_bytes(payloads["product"], owner.ProtectedE3PhysicalForecast, maximum_bytes=None)
    assert physical.disposition == "AVAILABLE" and payloads["arrays"] == available.physical_raw
    assert len(physical.arrays.members) == 24 and len(physical.dispositions) == 10
    assert {row[0] for row in selected.rows}.isdisjoint(("manifest", "streams", "history", "models", "error", "allocation"))


def test_actual_complete_paired_future_independent_score_and_recovery_preserve_all_arrays(available, case, monkeypatch):
    # Permit only this declared original pulse controller; prefix acquisition
    # and all whole-source acquisition remain prohibited.
    monkeypatch.undo()
    for module, name in ((parameter_history_segments, "acquire_parameter_segment"),
            (parameter_source, "acquire_parameter_history"), (parameter_history, "advance_parameter_pair")):
        monkeypatch.setattr(module, name, blocked)
    selected = prepared(available)
    manifests = tuple(decode_artifact_manifest(selected.plane.root.resolve(row.materialization.relative_path + ".manifest.json",
        for_write=False).read_bytes()) for row in selected.verified)
    contacts = ExternalNativeEffectContactStore(plane=selected.plane, execution_plan=selected.parent.execution_plan,
        visibility_ceiling=Visibility.DEVELOPMENT_ONLY, outcome_access=Access.EVALUATION_SEALED)
    contacts.begin(selected.parent)
    native = ExternalNativeSubworkStore(plane=selected.plane, parent_contacts=contacts, parent_contact=selected.parent,
        parent_inputs=manifests, prepared_invocation=selected.contract)
    result = selected.runner.execute_with_native_subwork(selected.bound, native)
    payloads = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in result.outputs}
    responses = decode_canonical_bytes(payloads["product"], owner.ProtectedE3NativeResponse, maximum_bytes=None)
    assert responses.disposition == "COMPLETED" and len(responses.native) == 1 and len(responses.branch_ids) == 48
    assert len(responses.arrays.members) == 246
    received = decode_matrix_arrays(payloads["arrays"], responses.arrays)
    assert len(received) == 246
    definition, = selected.contract.native_work.definitions
    completed = native.recover(definition)
    assert completed.state is NativeSubworkState.COMPLETED
    native_bytes = b"".join(native.iter_completed_output(definition, "arrays"))
    assert native_bytes == payloads["arrays"]
    updated = SimpleNamespace(**vars(available))
    updated.response_raw, updated.response = payloads["arrays"], responses
    score_worker = prepared(updated, "response-score")
    available.response_lifecycle_counter = updated.response_lifecycle_counter
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_bindings, response_science
    for module, names in ((response_science, ("native_responses", "panel_innovations")),
            (response_bindings, ("native_responses",)), (response_forecast, ("_hessian",)),
            (np.random, ("Generator", "PCG64DXSM", "default_rng")), (np.linalg, ("eigh", "eigvalsh")),
            (ExternalNativeSubworkStore, ("begin", "contact")), (ExternalNativeEffectContactStore, ("begin",))):
        for name in names:
            monkeypatch.setattr(module, name, blocked)
    score_result = score_worker.runner.execute(score_worker.bound)
    scored = {row.output_id.rsplit(".", 1)[-1]: row.payload for row in score_result.outputs}
    score = decode_canonical_bytes(scored["score"], owner.ScheduledResponseScore, maximum_bytes=None)
    outcome = decode_canonical_bytes(scored["outcome"], owner.ProtectedE3PairedOutcome, maximum_bytes=None)
    assert score.numerical_pass and score.disposition in ("FINITE", "PARTIAL")
    assert len(score.cells) == 240 and len(score.controls) == 48
    assert sum(control.denominator_steps for control in score.controls) == 24 * 128 + 24 * 256
    assert all(control.denominator_real_coordinates == 192 for control in score.controls)
    assert len(outcome.views) == 2 and all(len(view.errors) == 15 for view in outcome.views)
    # Cold recovery uses the same prepared invocation and exact actual native
    # receipt; native entry, producers, RNG and eigensolves now raise.
    replay = replace(selected.bound, input_ports=selected.plane.open_many(selected.verified,
        bindings=selected.bound.input_bindings, maximum_bytes=None))
    recovered = selected.runner.execute_with_native_subwork(replay, native)
    assert {row.output_id.rsplit(".", 1)[-1]: row.payload for row in recovered.outputs} == payloads
    assert (case.causal.canonical_bytes(), case.numerical.canonical_bytes(), case.frames.canonical_bytes()) == available.original_negative_bytes
    evidence = Path(selected.plane.root.contract.canonical_path) / "available-response-conformance.json"
    evidence.write_text(json.dumps({"scope": "exposed software conformance; authored causal state; no scientific qualification",
        "native_definition": definition.fingerprint(), "native_receipt": completed.receipt.fingerprint(),
        "response_sha256": sha256(payloads["arrays"]).hexdigest(), "native_member_count": len(received),
        "branch_count": len(responses.branch_ids), "score_cells": len(score.cells), "native_controls": len(score.controls),
        "native_control_steps": sum(control.denominator_steps for control in score.controls),
        "score_disposition": score.disposition, "recovery_bytes_unchanged": True}, indent=2) + "\n")
