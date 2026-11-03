# SPDX-License-Identifier: MPL-2.0
"""Cold literal received-array controls; no native execution or qualification.

The upstream prefix/custody metadata is disclosed fixture metadata. All received
paths below are literal zero arrays, never simulator output or fresh evidence.
The real independent transition reader checks those arrays without a producer.
"""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import FEATURES
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history import forecast as f, records as r, response_forecast as rf, response_records as rr, response_science as science, science as history_science
from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition
from tests.test_matrix_scheduled_response_bindings import (
    response_bank as response_bank, bank as bank, scheduled as scheduled, provenance as provenance, stock as stock,
)
from tests.native_completion_fixtures import literal_completion, receipt_with_completion


def reference(name, kind):
    return ObjectIdentity("literal.response." + name, kind.SCHEMA, kind.VERSION, sha256(("EXPOSED." + name).encode()).hexdigest())


def literal_native_metadata(source):
    """Metadata only; never a real contact, completed source or issue claim."""
    task = "literal.response.upstream"
    parent = NativeEffectContact("literal.response.run", task, "literal.response.attempt",
        ObjectIdentity("literal.response.plan", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64),
        ObjectIdentity(task, "empirical-lawhood/runtime/execution-task", "1.0.0", "b" * 64),
        source.provenance.observed_git_head, ("literal.response.input",), ())
    definition = NativeSubworkDefinition("literal.response.upstream", "literal.response.metadata-only", parent,
        r.identity(source), (r.identity(source),), "c" * 64, "d" * 64, parent.input_materialization_ids, (), ())
    contact = NativeSubworkContact(ObjectIdentity("literal.response.begin", "empirical-lawhood/runtime/native-subwork-begin", "1.0.0", "e" * 64))
    completion = NativeSubworkCompletion(definition.identity, ObjectIdentity.from_record("literal.response.contact", contact),
        OperationalStatus.SUCCEEDED, (), (), (), (), (), InquiryCost(None, None, None),
        "EXPOSED LITERAL METADATA ONLY; NO REAL NATIVE CONTACT OR QUALIFICATION", None, ())
    receipt = CanonicalTaskReceipt("literal.response.receipt", parent.run_id, parent.task_id, parent.attempt_id,
        parent.implementation_commit, parent.input_materialization_ids, (), (), (), OperationalStatus.SUCCEEDED, ())
    receipt = receipt_with_completion(receipt, literal_completion(completion, receipt.task_id,
        visibility=Visibility.PROSPECTIVE, access=Access.OUTCOME_BLIND))
    return r.ScheduledNativeEvidence(definition, completion, receipt)


@pytest.fixture
def response_case(response_bank):  # noqa: F811
    _, sources, commit, _ = response_bank
    source = next(s for s in sources if s.root_id in commit.selected_root_ids)
    protocol, panels = commit.response_selection.validate_source(source)
    prefix_arrays = {view + "_" + phase: np.zeros((1, 2, 3, 4, 4), dtype="<c16")
        for view in ("primary", "fine") for phase in ("positions", "momenta")}
    _, prefix_operand = history_science._array_product(
        source, prefix_arrays, role="PREFIX", artifact_id="literal.response.prefix", producers=(r.identity(source),))
    checkpoint = r.ScheduledCheckpoint("literal.response.checkpoint", r.identity(source), coordinate_identity(source.coordinate),
        source.policy.cutoff_tick, prefix_operand.array_artifact, tuple(segments.ParameterGeneratorState(stream.purpose,
            stream.effective_seed, 0, 1, 0, 0, 0) for stream in source.root.streams))
    metadata = literal_native_metadata(source)
    history = r.ScheduledPrefixHistory("literal.response.history", r.identity(source), prefix_operand, checkpoint, metadata)
    _, causal_operand = history_science._array_product(
        source, prefix_arrays, role="CAUSAL_STATE", artifact_id="literal.response.causal", producers=(r.identity(source),))
    causal = r.ScheduledCausalPrefix("literal.response.causal", r.identity(source), r.identity(history),
        reference("numerical", r.ScheduledNumericalAssessment), reference("witness", r.ScheduledPrefixWitness),
        reference("frame", r.ScheduledFrameAssessment), r.identity(source.policy), source.root.root, source.policy.cutoff_tick,
        "f" * 64, "AVAILABLE", None, causal_operand)
    feature = f.ScheduledForecastFeature("literal.response.feature", r.identity(source), r.identity(causal), source.root_id,
        source.root.root.independent_group_id, f.FAMILY_MAP[source.coordinate.family_id], source.coordinate.clock_id,
        source.coordinate.physical_time(source.policy.cutoff_tick), "f" * 64, "AVAILABLE", tuple((name, D(0)) for name in FEATURES))
    design = commit.forecast_design
    error = f.ScheduledForecastSeal("literal.response.error", r.identity(source), r.identity(causal),
        ObjectIdentity.from_record(design.design_id, design), design.model, protocol.criterion, None, f.CALIBRATION_POINT,
        feature, (D(0),) * 15, (D(0),) * 15, (None,) * 15, None)
    receivers = np.zeros((48, 2, 2, 3, 4, 4), dtype="<c16")
    for phase in range(2):
        for sector in range(2):
            for index in range(3):
                for axis in range(4):
                    receivers[phase * 24 + sector * 12 + index * 4 + axis, phase, sector, index, axis, axis] = 1
    frozen = dict(receivers=receivers, forces=np.zeros((4, 2, 3, 4, 4), dtype="<c16"))
    frozen.update((view + "_" + predictor.lower(), np.zeros((4, 3, 48), dtype="<f8"))
        for view in ("primary", "fine") for predictor in rr.PREDICTORS)
    _, physical_operand = rf.array_product(protocol, frozen, role="FORECAST", artifact_id="literal.response.physical",
        producers=(r.identity(source),), access=Access.OUTCOME_BLIND, visibility=Visibility.PROSPECTIVE)
    physical = rr.ScheduledResponseForecast("literal.response.physical", r.identity(source), r.identity(causal),
        ObjectIdentity.from_record(protocol.protocol_id, protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
        "f" * 64, physical_operand, "AVAILABLE", tuple((view, predictor, "AVAILABLE", None)
            for view in ("PRIMARY", "FINE") for predictor in rr.PREDICTORS))
    horizon = protocol.horizon_steps[-1]
    arrays = {}
    for panel in panels:
        for name, count in (("primary", horizon), ("fine", 2 * horizon), ("bridge", horizon)):
            arrays["noise." + panel.panel_id + "." + name] = np.zeros((count, 2, 3, 4, 4), dtype="<c16")
    for branch, view, panel, _, _ in rr.branch_census(protocol, panels):
        multiplier = 1 if view == "PRIMARY" else 2
        count, start = multiplier * horizon, multiplier * source.policy.cutoff_tick
        values = dict(positions=np.zeros((count + 1, 2, 3, 4, 4), dtype="<c16"),
            momenta=np.zeros((count + 1, 2, 3, 4, 4), dtype="<c16"),
            innovations=arrays["noise." + panel.panel_id + "." + view.lower()], ticks=np.arange(start, start + count + 1, dtype="<i8"),
            alpha_tilde=np.asarray([source.coordinate.couplings(tick, refinement=multiplier) for tick in range(start, start + count + 1)], dtype="<f8"))
        arrays.update(("branch." + branch + "." + name, value) for name, value in values.items())
    _, response_operand = rf.array_product(protocol, arrays, role="RESPONSES", artifact_id="literal.response.responses",
        producers=(r.identity(source),), access=Access.EVALUATION_SEALED, visibility=Visibility.PROSPECTIVE)
    responses = rr.ScheduledResponseNative("literal.response.responses", r.identity(source), r.identity(causal),
        ObjectIdentity.from_record(physical.forecast_id, physical), r.identity(error), ObjectIdentity.from_record(protocol.protocol_id, protocol),
        response_operand, tuple(branch for branch, *_ in rr.branch_census(protocol, panels)), (metadata,), "COMPLETED", ())
    return SimpleNamespace(source=source, causal=causal, history=history, prefix=prefix_arrays, error=error, physical=physical,
        frozen=frozen, protocol=protocol, panels=panels, responses=responses, arrays=arrays)


def assess(case, *, function=None, **changed):
    values = vars(case) | changed
    selected = science.assess_responses if function is None else function
    return selected(*(values[name] for name in ("source", "causal", "history", "prefix", "error", "physical", "frozen", "protocol", "panels", "responses", "arrays")),
        score_id="literal.response.score")


def assess_shared(case, *, error_forecast=None, **changed):
    values = vars(case) | changed
    return science.assess_paired_response_arrays(*(values[name] for name in (
        "source", "causal", "history", "prefix", "physical", "frozen", "protocol", "panels", "responses", "arrays")),
        error_forecast=r.identity(case.error) if error_forecast is None else error_forecast, score_id="literal.response.score")


def variations(case):
    partial = {name: value.copy() if name == "primary_factor" else value for name, value in case.frozen.items()}
    partial["primary_factor"][:] = np.nan
    nonuse_arrays = {"unentered_branches": np.arange(48, dtype="<i8")}
    nonuse = replace(case.responses, native=(), disposition="UNEVALUABLE", reason_codes=("literal-unentered",))
    damaged = dict(case.arrays)
    name = "branch." + case.responses.branch_ids[0] + ".positions"
    damaged[name] = damaged[name].copy()
    damaged[name][1, 0, 0, 0, 0] = 0.125
    return dict(finite={}, partial=dict(frozen=partial), nonuse=dict(responses=nonuse, arrays=nonuse_arrays),
        negative=dict(arrays=damaged),
        no_origin=dict(responses=replace(nonuse, disposition="NO_ORIGIN"), arrays=nonuse_arrays),
        instrument_unresolved=dict(responses=replace(nonuse, disposition="INSTRUMENT_UNRESOLVED"), arrays=nonuse_arrays))


def blocked(*args, **kwargs):
    raise AssertionError("cold literal response check entered a native producer, RNG, eigensolver or fitting")


def forbid_producers(monkeypatch):
    from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_derivatives, parameter_source
    from empirical_lawhood.runtime import experimental_statistics
    for owner, names in ((science, ("native_responses", "panel_innovations", "native_scheduled_branch", "hermitian_noise")),
            (np.random, ("Generator", "PCG64DXSM")), (np.linalg, ("eigh", "eigvalsh")),
            (parameter_derivatives, ("scheduled_force_step",)), (parameter_source, ("acquire_parameter_history",)),
            (segments, ("acquire_parameter_segment",)), (experimental_statistics, ("fit_standardized_ridge",))):
        for name in names:
            monkeypatch.setattr(owner, name, blocked)


@pytest.mark.parametrize("variant", ("finite", "partial", "nonuse", "negative", "no_origin", "instrument_unresolved"))
def test_original_complete_received_array_outputs_without_any_producer(response_case, monkeypatch, variant):
    forbid_producers(monkeypatch)
    result = assess(response_case, **variations(response_case)[variant])
    assert len(result.cells) == 240 and len(result.cumulative_log_errors) == 15
    assert result.disposition == {"finite": "FINITE", "partial": "PARTIAL", "nonuse": "UNEVALUABLE",
        "negative": "NATIVE_CROSSCHECK_FAILED", "no_origin": "NO_ORIGIN", "instrument_unresolved": "INSTRUMENT_UNRESOLVED"}[variant]
    assert len(result.controls) == (48 if variant in ("finite", "partial", "negative") else 0)
    if variant in ("finite", "partial", "negative"):
        assert sum(c.denominator_steps for c in result.controls) == 24 * 128 + 24 * 256
        assert all(c.denominator_real_coordinates == 192 for c in result.controls)
    else:
        assert all(v is None for v in result.cumulative_log_errors)
    assert all(cell.actual_odd_responses is None or len(cell.actual_odd_responses) == 48 for cell in result.cells)
    if variant == "negative":
        assert not result.numerical_pass and any(control.failed_steps for control in result.controls)
        assert all(value is None for value in result.cumulative_log_errors)


@pytest.mark.parametrize("damage", ("old-seal-type", "criterion", "physical", "causal-history", "error-reference", "branches", "array-member", "bridge", "receiver"))
def test_original_refusals_precede_or_retain_complete_received_controls(response_case, monkeypatch, damage):
    forbid_producers(monkeypatch)
    case = response_case
    changed = {}
    if damage == "old-seal-type":
        changed["error"] = SimpleNamespace(**{name: getattr(case.error, name) for name in ("source", "prefix", "criterion")})
    elif damage == "criterion":
        changed["error"] = replace(case.error, criterion=reference("foreign-criterion", r.ScheduledPrefixPolicy))
    elif damage == "physical":
        changed["physical"] = replace(case.physical, causal_prefix=reference("foreign-prefix", r.ScheduledCausalPrefix))
    elif damage == "causal-history":
        changed["causal"] = replace(case.causal, history=reference("foreign-history", r.ScheduledPrefixHistory))
    elif damage == "error-reference":
        changed["responses"] = replace(case.responses, error_forecast=reference("foreign-seal", f.ScheduledForecastSeal))
    elif damage == "branches":
        changed["responses"] = replace(case.responses, branch_ids=case.responses.branch_ids[:-1])
    elif damage == "array-member":
        changed["arrays"] = {name: value for name, value in case.arrays.items() if name != next(iter(case.arrays))}
    elif damage == "bridge":
        arrays = dict(case.arrays)
        name = "noise." + case.panels[0].panel_id + ".bridge"
        arrays[name] = arrays[name].copy()
        arrays[name][0, 0, 0, 0, 0] = 1
        changed["arrays"] = arrays
    else:
        changed["frozen"] = case.frozen | {"receivers": case.frozen["receivers"][:-1]}
    with pytest.raises((ValueError, TypeError)):
        assess(case, **changed)


def test_shared_reader_accepts_explicit_reference_without_any_forecast_qualification(response_case, monkeypatch):
    forbid_producers(monkeypatch)
    case = response_case
    unqualified = ObjectIdentity("literal.response.unqualified", "empirical-lawhood/tests/unqualified-forecast", "1.0.0", "9" * 64)
    nonuse = variations(case)["nonuse"]
    nonuse["responses"] = replace(nonuse["responses"], error_forecast=unqualified)
    result = assess_shared(case, error_forecast=unqualified, **nonuse)
    assert result.error_forecast == unqualified and result.disposition == "UNEVALUABLE"
    assert len(result.cells) == 240 and not result.numerical_pass
    assert not hasattr(result, "qualification")
    with pytest.raises(TypeError):
        assess_shared(case, error_forecast=SimpleNamespace(object_id=unqualified.object_id,
            object_schema=unqualified.object_schema, object_version=unqualified.object_version,
            object_fingerprint=unqualified.object_fingerprint), **nonuse)
    with pytest.raises(ValueError):
        assess_shared(case, **nonuse)


@pytest.mark.parametrize("damage", ("physical-prefix", "causal-history", "response-protocol", "physical-reference"))
def test_shared_reader_retains_common_source_and_dependency_joins(response_case, monkeypatch, damage):
    forbid_producers(monkeypatch)
    case = response_case
    changed = variations(case)["nonuse"]
    if damage == "physical-prefix":
        changed["physical"] = replace(case.physical, causal_prefix=reference("foreign-prefix", r.ScheduledCausalPrefix))
    elif damage == "causal-history":
        changed["causal"] = replace(case.causal, history=reference("foreign-history", r.ScheduledPrefixHistory))
    elif damage == "response-protocol":
        changed["responses"] = replace(changed["responses"], protocol=reference("foreign-protocol", rr.ScheduledResponseProtocol))
    else:
        changed["responses"] = replace(changed["responses"], physical_forecast=reference("foreign-physical", rr.ScheduledResponseForecast))
    with pytest.raises(ValueError, match="original source/prefix/frozen menu/seals"):
        assess_shared(case, **changed)


def test_literal_nonzero_error_uses_two_hs24_phase_norms_and_nominal_impulse(response_case, monkeypatch):
    forbid_producers(monkeypatch)
    case = response_case
    frozen = dict(case.frozen)
    frozen["primary_factor"] = case.frozen["primary_factor"].copy()
    frozen["primary_factor"][..., :24] = 1e-8
    frozen["primary_factor"][..., 24:] = 2e-8
    result = assess_shared(case, frozen=frozen)
    with localcontext() as context:
        context.prec = 60
        for cell in result.cells:
            if cell.view == "PRIMARY" and cell.predictor == "FACTOR":
                action = next(a for a in case.protocol.actions if a.action_id == cell.action_id)
                duration = D("0.001") * cell.horizon_tick
                pulse = D("0.001") * min(16, cell.horizon_tick)
                impulse = D("0.01") * D(1) * pulse
                expected = max((D(24) * D("1e-8") ** 2).sqrt() / (impulse * (duration - pulse / 2)),
                    (D(24) * D("2e-8") ** 2).sqrt() / impulse)
                assert action.force_norm == D(1) and cell.normalized_error == expected
                assert cell.signed_errors == (D("1e-8"),) * 24 + (D("2e-8"),) * 24
                assert cell.relative_errors == (None,) * 48
    assert result.numerical_pass and result.disposition == "FINITE" and len(result.controls) == 48
