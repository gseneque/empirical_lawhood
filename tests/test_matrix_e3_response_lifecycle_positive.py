# SPDX-License-Identifier: MPL-2.0
"""Executable current AVAILABLE/cold paths with disclosed authored operands.

Initial/admission/native-return metadata are explicitly authored test inputs.
Constant received trajectories are not an integration or qualification: the
unchanged literal independent equations must retain their measured negatives.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_bindings as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_response_records as records
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import science as prefix_science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_bindings, response_forecast
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, NativeSubworkUncertainContact
from tests.test_matrix_e3_response_preparation import case as case, original_case as original_case, forbid_native as forbid_native  # noqa: F401
from tests.test_matrix_e3_response_preparation import close, prepared
from tests.test_matrix_e3_response_records import error_operands, publication, qualification
from tests.test_matrix_scheduled_response_forecast import pauli


def blocked(*args, **kwargs):
    raise AssertionError("literal current lifecycle entered real acquisition/native producer/RNG/eigensolve")


def authored_available(case):
    if hasattr(case, "authored_available_base"):
        result = SimpleNamespace(**vars(case.authored_available_base))
        result.response_lifecycle_counter = getattr(case, "response_lifecycle_counter", 0)
        return result
    result = SimpleNamespace(**vars(case))
    frame = np.asarray([np.kron(matrix, np.eye(2)) / 2 for matrix in pauli()], dtype="<c16")
    complement = np.asarray([np.kron(np.eye(2), matrix) / 2 for matrix in pauli()], dtype="<c16")
    templates = {"generic_basis": complement,
        "force_coefficients": np.stack((np.eye(3), np.eye(3))).astype("<f8") / np.sqrt(6),
        "trace_coefficients": np.ones((2, 3), dtype="<f8") / np.sqrt(6),
        "receiver_coefficients": np.eye(48, dtype="<f8").reshape(48, 2, 2, 3, 4)}
    template_raw, template_operand = response_forecast.array_product(case.protocol, templates, role="TEMPLATES",
        artifact_id="aaa.literal.available.templates", producers=(case.protocol.public_source.source,),
        access=Access.OUTCOME_BLIND, visibility=Visibility.PROSPECTIVE)
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
    template_pub = case.plane.write(ArtifactWriteRequest(template_operand.array_artifact.artifact_id, "available/templates.npz",
        template_operand.array_artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", "literal.available",
        "available", template_raw, Visibility.PROSPECTIVE, (), Access.OUTCOME_BLIND))
    result.protocol = replace(case.protocol, templates=template_operand)
    result.selection = replace(case.selection,
        root_protocols=tuple((root, records._object(result.protocol) if root == case.source.root_id else ref) for root, ref in case.selection.root_protocols),
        template_publications=tuple(sorted((template_pub, *case.selection.template_publications), key=lambda row: row.logical.logical_artifact_id)))
    pub = publication(case, result.selection, "available.selection")
    q = qualification(result.selection, pub, "available.selection")
    result.profile = records.project_protected_e3_response_numerics(result.protocol, provenance=result.selection, publication=pub, qualification=q)
    result.physical_config = replace(case.physical_config, protocol=records._object(result.protocol), numerical_profile=identity(result.profile))
    result.native_config = replace(case.native_config, protocol=records._object(result.protocol), numerical_profile=identity(result.profile),
        response_selection=identity(result.selection))
    native = decode_matrix_arrays(case.native_raw, case.history.arrays)
    causal = {name: value for name, value in native.items() if not name.endswith("innovations")}
    causal["frame"] = frame
    result.causal_raw, arrays = prefix_science._array_product(case.source, causal, role="CAUSAL_STATE", artifact_id="literal.available.causal-arrays",
        producers=(case.causal.source, case.causal.history, case.causal.witness, case.causal.frame_assessment))
    # This is authored admission metadata, never the scientific result of the
    # deliberately negative original prefix controls retained in the fixture.
    result.causal = replace(case.causal, disposition="AVAILABLE", reason=None, frame_sha256=sha256(frame.tobytes()).hexdigest(), arrays=arrays)
    result.models, result.frozen, result.error = error_operands(result, result.causal, available=True)
    case.authored_available_base = SimpleNamespace(**vars(result))
    return result


def literal_response_arrays(case):
    """Complete constant paths, exact actual clocks/couplings, zero paired noise."""
    prefix = decode_matrix_arrays(case.native_raw, case.history.arrays)
    horizon = case.protocol.horizon_steps[-1]
    arrays = {}
    for panel in case.panels:
        for label, count in (("primary", horizon), ("fine", 2*horizon), ("bridge", horizon)):
            arrays["noise." + panel.panel_id + "." + label] = np.zeros((count, 2, 3, 4, 4), dtype="<c16")
    for branch, view, panel, _, _ in branch_census(case.protocol, case.panels):
        multiplier, label = (1, "primary") if view == "PRIMARY" else (2, "fine")
        ticks = np.arange(multiplier*case.source.policy.cutoff_tick, multiplier*(case.source.policy.cutoff_tick+horizon)+1, dtype="<i8")
        for phase in ("positions", "momenta"):
            arrays["branch." + branch + "." + phase] = np.repeat(prefix[label + "_" + phase][-1][None], len(ticks), axis=0)
        arrays["branch." + branch + ".innovations"] = arrays["noise." + panel.panel_id + "." + label]
        arrays["branch." + branch + ".ticks"] = ticks
        arrays["branch." + branch + ".alpha_tilde"] = np.asarray([case.source.coordinate.couplings(int(tick), refinement=multiplier) for tick in ticks], dtype="<f8")
    assert len(arrays) == 246
    return dict(sorted(arrays.items()))


def snapshot(plane):
    root = Path(plane.root.contract.canonical_path)
    return {str(path.relative_to(root)): (sha256(path.read_bytes()).hexdigest(), path.stat().st_size, path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()}


def run(selected, native):
    cursors = tuple(port.cursor() for port in selected.bound.input_ports)
    return selected.runner.execute_with_native_subwork(replace(selected.bound, input_ports=cursors), native)


def test_available_actual_forecast_literal_native_relay_recovery_and_full_independent_negative(case, monkeypatch):  # noqa: F811
    original = case
    case = authored_available(case)
    physical = prepared(case, "physical-forecast")
    produced = physical.runner.execute(physical.bound)
    case.physical_raw = next(row.payload for row in produced.outputs if row.output_id.endswith(".arrays"))
    case.physical = decode_canonical_bytes(next(row.payload for row in produced.outputs if row.output_id.endswith(".product")), owner.ProtectedE3PhysicalForecast, maximum_bytes=None)
    assert case.physical.disposition == "AVAILABLE"
    assert len(case.physical.arrays.members) == 24
    values = literal_response_arrays(case)
    calls = []

    def literal(source, history, prefix, protocol, panels, frozen):
        assert source == case.source and history == case.history and protocol == case.protocol and panels == case.panels
        assert prefix["primary_positions"].shape[0] == 257 and frozen["forces"].shape == (4, 2, 3, 4, 4)
        calls.append("explicit-literal-full246-return")
        return values

    monkeypatch.setattr(response_bindings, "native_responses", literal)
    selected = prepared(case)
    try:
        manifests = tuple(decode_artifact_manifest(selected.plane.root.resolve(row.materialization.relative_path + ".manifest.json", for_write=False).read_bytes())
            for row in selected.verified)
        contacts = ExternalNativeEffectContactStore(plane=selected.plane, execution_plan=selected.parent.execution_plan,
            visibility_ceiling=Visibility.DEVELOPMENT_ONLY, outcome_access=Access.EVALUATION_SEALED)
        contacts.begin(selected.parent)
        native = ExternalNativeSubworkStore(plane=selected.plane, parent_contacts=contacts, parent_contact=selected.parent,
            parent_inputs=manifests, prepared_invocation=selected.contract)
        result = run(selected, native)
        case.response_raw = next(row.payload for row in result.outputs if row.output_id.endswith(".arrays"))
        case.response = decode_canonical_bytes(next(row.payload for row in result.outputs if row.output_id.endswith(".product")), owner.ProtectedE3NativeResponse, maximum_bytes=None)
        assert len(case.response.arrays.members) == len(response_bindings.unpack_native(case.response_raw, case.protocol, case.panels)) == 246
        assert len(case.response.branch_ids) == 48 and len(case.response.native) == 1 and calls == ["explicit-literal-full246-return"]
        before = snapshot(selected.plane)
        monkeypatch.setattr(response_bindings, "native_responses", blocked)
        assert run(selected, native) == result
        assert snapshot(selected.plane) == before
        assert all(port.bytes_read == 0 for port in selected.context.input_ports)
    finally:
        close(selected)
    # Cold consumer receives new leases and cannot rerun any producer/eigensolve.
    monkeypatch.setattr(response_forecast, "_hessian", blocked)
    monkeypatch.setattr(np.linalg, "eigh", blocked)
    score_task = prepared(case, "response-score")
    cold = score_task.runner.execute(score_task.bound)
    score = decode_canonical_bytes(next(row.payload for row in cold.outputs if row.output_id.endswith(".score")), owner.ScheduledResponseScore, maximum_bytes=None)
    outcome = decode_canonical_bytes(next(row.payload for row in cold.outputs if row.output_id.endswith(".outcome")), owner.ProtectedE3PairedOutcome, maximum_bytes=None)
    assert score.disposition == "NATIVE_CROSSCHECK_FAILED" and not score.numerical_pass
    assert len(score.controls) == 48 and all(control.denominator_real_coordinates == 192 for control in score.controls)
    assert len(score.cells) == 240 and all(len(cell.actual_odd_responses) == 48 for cell in score.cells)
    assert all(view.dispositions == ("NUMERICAL_FAILURE",) * 15 for view in outcome.views)
    original.response_lifecycle_counter = case.response_lifecycle_counter


@pytest.mark.parametrize("contacted", (False, True))
def test_available_unfinished_native_contact_keeps_custody_and_cannot_reenter(case, monkeypatch, contacted):  # noqa: F811
    original = case
    case = authored_available(case)
    physical = prepared(case, "physical-forecast")
    produced = physical.runner.execute(physical.bound)
    case.physical_raw = next(row.payload for row in produced.outputs if row.output_id.endswith(".arrays"))
    case.physical = decode_canonical_bytes(next(row.payload for row in produced.outputs if row.output_id.endswith(".product")), owner.ProtectedE3PhysicalForecast, maximum_bytes=None)
    selected = prepared(case)
    original.response_lifecycle_counter = case.response_lifecycle_counter
    try:
        manifests = tuple(decode_artifact_manifest(selected.plane.root.resolve(row.materialization.relative_path + ".manifest.json", for_write=False).read_bytes())
            for row in selected.verified)
        contacts = ExternalNativeEffectContactStore(plane=selected.plane, execution_plan=selected.parent.execution_plan,
            visibility_ceiling=Visibility.DEVELOPMENT_ONLY, outcome_access=Access.EVALUATION_SEALED)
        contacts.begin(selected.parent)
        native = ExternalNativeSubworkStore(plane=selected.plane, parent_contacts=contacts, parent_contact=selected.parent,
            parent_inputs=manifests, prepared_invocation=selected.contract)
        work = selected.contract.native_work
        definition, = work.definitions
        native.freeze_roster(work.rosters[0], definitions=work.definitions)
        entry = native.begin(definition)
        if contacted:
            native.contact(entry)
        before = snapshot(selected.plane)
        monkeypatch.setattr(response_bindings, "native_responses", blocked)
        with pytest.raises(NativeSubworkUncertainContact if contacted else ValueError,
                match="contacted without exact receipt|unreceipted Native contact replay"):
            run(selected, native)
        assert snapshot(selected.plane) == before
        assert native.inspect(definition).state is (NativeSubworkState.UNKNOWN_COMPLETION if contacted else NativeSubworkState.BEGUN)
    finally:
        close(selected)
