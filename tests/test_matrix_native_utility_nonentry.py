# SPDX-License-Identifier: MPL-2.0
"""Exact E2 nonentry metadata controls; disclosed fixtures confer no qualification."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, branch_census
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from tests.test_matrix_native_utility import utility_case

ROOT = Path(__file__).parents[1]
DEV, EXPOSED = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY


def _pin(name, kind):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, "a" * 64)


def _arrays(source, role, name, members):
    return ScheduledResponseArrays("arrays." + name, role, r.scheduled_identity(source),
        ArtifactIdentity("array." + name, "disclosed-metadata-only-no-array-body", MATRIX_ARRAY_SCHEMA,
            "a" * 64, "application/x-npz", 1), members, (r.scheduled_identity(source),), DEV, EXPOSED)


@pytest.fixture
def metadata(tmp_path):
    case = utility_case(tmp_path)
    source, protocol = case.source, case.request.protocols[0]
    panels = r.panels_for(case.request, source)
    source_pin = r.scheduled_identity(source)
    member = MatrixArrayMember("disclosed", "<i8", (1,), sha256(bytes(8)).hexdigest())
    causal_arrays = r.NativeUtilityArrays("arrays.disclosed-causal", source_pin, "CAUSAL_STATE",
        ArtifactIdentity("array.disclosed-causal", "disclosed-metadata-no-body", MATRIX_ARRAY_SCHEMA,
            "a" * 64, "application/x-npz", 1), (member,), (source_pin,), DEV, EXPOSED)
    causal = r.NativeUtilityCausalPrefix("causal.disclosed-nonentry", source_pin,
        _pin("history.disclosed", r.NativeUtilityPrefixHistory), _pin("numerical.disclosed", r.NativeUtilityNumericalAssessment),
        _pin("witness.disclosed", r.NativeUtilityPrefixWitness), _pin("frames.disclosed", r.NativeUtilityFrameAssessment),
        r.scheduled_identity(source.policy), source.root.root, source.policy.cutoff_tick, None,
        "NO_ORIGIN", "disclosed-unavailable-origin", causal_arrays)
    physical = r.NativeUtilityPhysicalForecast("physical.disclosed-nonentry", source_pin, causal.identity,
        r.identity(protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
        None, _arrays(source, "FORECAST", "disclosed-physical", (member,)), "NO_ORIGIN",
        tuple((view, predictor, "UNRESOLVED", "disclosed-unavailable-instrument")
            for view in ("PRIMARY", "FINE") for predictor in r.PREDICTORS))
    return SimpleNamespace(case=case, source=source, protocol=protocol, panels=panels, causal=causal, physical=physical)


def _nonentry(value, causal_disposition, physical_disposition):
    available = causal_disposition == "AVAILABLE"
    causal = replace(value.causal, disposition=causal_disposition, frame_sha256="b" * 64 if available else None,
        reason=None if available else "disclosed-unavailable-origin")
    physical = replace(value.physical, causal_prefix=causal.identity, frame_sha256=causal.frame_sha256,
        disposition=physical_disposition)
    expected = ("NO_ORIGIN" if causal_disposition == "NO_ORIGIN" else
        "INSTRUMENT_UNRESOLVED" if physical_disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE")
    branches = tuple(row[0] for row in branch_census(value.protocol, value.panels))
    raw_hash = sha256(b"".join(index.to_bytes(8, "little", signed=True) for index in range(len(branches)))).hexdigest()
    arrays = _arrays(value.source, "RESPONSES", "disclosed-unentered", (MatrixArrayMember(
        "unentered_branches", "<i8", (len(branches),), raw_hash),))
    response = r.NativeUtilityResponse("responses.disclosed-nonentry", r.scheduled_identity(value.source), causal.identity,
        physical.identity, value.case.acquisition.identity, r.identity(value.protocol), arrays, branches, (), expected,
        ("complete-paired-branch-slots-not-entered-" + expected.lower(),))
    return causal, physical, response


@pytest.mark.parametrize("causal_disposition,physical_disposition", (("NO_ORIGIN", "NO_ORIGIN"),
    ("UNEVALUABLE", "UNEVALUABLE"), ("AVAILABLE", "INSTRUMENT_UNRESOLVED"),
    ("NO_ORIGIN", "INSTRUMENT_UNRESOLVED")))
def test_exact_e2_nonentry_retains_canonical_bytes_without_array_read_or_rng(metadata, monkeypatch,
        causal_disposition, physical_disposition):
    causal, physical, response = _nonentry(metadata, causal_disposition, physical_disposition)
    def forbidden(*args, **kwargs):
        pytest.fail("pure E2 nonentry validation entered array/native/RNG work")
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", forbidden)
    monkeypatch.setattr(bindings, "execute_parameter_native_work", forbidden)
    monkeypatch.setattr(bindings, "decode_matrix_arrays", forbidden)
    monkeypatch.setattr(bindings.np.random, "default_rng", forbidden)
    original = response.canonical_bytes()
    assert response.validate_nonentry(causal, physical, metadata.protocol, metadata.panels) is response
    assert response.canonical_bytes() == original and len(response.branch_ids) == 48 and response.native == ()


@pytest.mark.parametrize("defect", ("disposition", "reason", "branch-count", "member-count", "member-name",
    "dtype", "shape", "hash", "finite", "causal", "physical", "protocol", "available-future"))
def test_exact_e2_nonentry_refuses_mislabelled_or_thinned_marker_and_available_work(metadata, defect):
    causal, physical, response = _nonentry(metadata, "NO_ORIGIN", "NO_ORIGIN")
    member, = response.arrays.members
    if defect == "disposition":
        response = replace(response, disposition="UNEVALUABLE")
    elif defect == "reason":
        response = replace(response, reason_codes=("wrong-owner-reason",))
    elif defect == "branch-count":
        response = replace(response, branch_ids=response.branch_ids[:-1])
    elif defect == "member-count":
        response = replace(response, arrays=replace(response.arrays, members=(member, replace(member, name="unused.extra"))))
    elif defect in ("member-name", "dtype", "shape", "hash", "finite"):
        changes = {"member-name": {"name": "wrong-marker"}, "dtype": {"dtype": "<f8"},
            "shape": {"shape": (47,)}, "hash": {"sha256": "f" * 64}, "finite": {"finite_required": False}}
        response = replace(response, arrays=replace(response.arrays, members=(replace(member, **changes[defect]),)))
    elif defect in ("causal", "physical", "protocol"):
        field = {"causal": "causal_prefix", "physical": "physical_forecast", "protocol": "protocol"}[defect]
        response = replace(response, **{field: replace(getattr(response, field), object_fingerprint="f" * 64)})
    else:
        causal, physical, response = _nonentry(metadata, "AVAILABLE", "AVAILABLE")
    with pytest.raises(ValueError, match="nonentry"):
        response.validate_nonentry(causal, physical, metadata.protocol, metadata.panels)


def test_actual_e2_worker_calls_shared_nonentry_relation_without_native_future(metadata, monkeypatch):
    causal, physical, _ = _nonentry(metadata, "AVAILABLE", "INSTRUMENT_UNRESOLVED")
    source, request = metadata.source, metadata.case.request
    wire = bindings.NativeUtilityOperationConfig("config.disclosed-nonentry-responses", "responses",
        metadata.case.specification.identity, request.identity,
        next(value for value in request.sources if value.root_id == source.root_id), None,
        r.identity(metadata.protocol), metadata.panels, request.resources.for_operation("responses"),
        (("prefix", _pin("config.disclosed-prefix", bindings.NativeUtilityOperationConfig)),))
    config = bindings._BoundConfiguration(wire, metadata.protocol)
    runner = bindings.NativeUtilityNativeRunner("responses")
    records = dict(history=object(), causal=causal, physical=physical, acquisition=metadata.case.acquisition)
    context = SimpleNamespace(input_ports=(), output_ports=(SimpleNamespace(
        profile=ArtifactProfile.MATRIX_ARRAY_NPZ, logical_artifact_id="array.disclosed-owner-nonentry"),))
    def forbidden(*args, **kwargs):
        pytest.fail("unentered E2 owner called a native producer")
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", forbidden)
    monkeypatch.setattr(bindings, "execute_parameter_native_work", forbidden)
    monkeypatch.setattr(bindings, "_decode", lambda *args, **kwargs: (config, metadata.case.specification, source, records, {}))
    monkeypatch.setattr(bindings, "_native_work", lambda *args, **kwargs: (None, None, None))
    monkeypatch.setattr(runner, "_response_arrays", lambda context: (None, None))
    monkeypatch.setattr(bindings, "_outputs", lambda context, product, **kwargs: product)
    observed = []
    validate = r.NativeUtilityResponse.validate_nonentry
    def checked(self, *args):
        observed.append(self.disposition)
        return validate(self, *args)
    monkeypatch.setattr(r.NativeUtilityResponse, "validate_nonentry", checked)
    response = runner.execute_with_native_subwork(context, SimpleNamespace(parent_contact=None))
    assert observed == ["INSTRUMENT_UNRESOLVED"] and response.native == ()


@pytest.mark.native
def test_actual_closed_public_e2_retains_scored_nonuse_adverse_and_missing_whole_root(tmp_path, monkeypatch):
    """Future mixed public control using the already-disclosed finite000 recipe."""
    from decimal import Decimal
    from threadpoolctl import threadpool_limits
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_custody_records import NativeUtilityCustodyAssessment
    from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.api.recursive_execution import run_recursive_wave
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor, ResourceAdmissionError
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
    from tests.test_matrix_native_training_public_lifecycle import _actual_case
    from tests.test_matrix_native_utility import copied_preparation
    with threadpool_limits(limits=1):
        case = utility_case(tmp_path, original=_actual_case(tmp_path, monkeypatch, training_count=3))
        adverse_root, nonuse_root, refused_root = case.specification.root_ids
        # Literal000 already has an AVAILABLE paired prefix in the retained
        # public TRAIN/E2 controls; keep it for the real finite adverse score.
        # Literal001 retains genuine NO_ORIGIN if present, or the frozen
        # complement threshold forces instrument nonuse. No origin is supplied.
        case.specification = replace(case.specification, criterion=replace(case.specification.criterion,
            maximum_view_discrepancy=Decimal("1e30"), improvement_margin=Decimal("1e30"),
            alpha_numerator=1, alpha_denominator=280))
        case.request = replace(case.request, protocols=tuple(replace(value, complement_gram_minimum=Decimal("1e30"))
            if value.public_source.root.root_id == nonuse_root else value for value in case.request.protocols))
        case.acquisition = r.acquisition_seal(case.specification, case.request)
        prepared = copied_preparation(case, tmp_path / "mixed-copied")
        directory = Path(case.plane.root.contract.canonical_path) / "mixed-closed-e2-authored"
        author_prepared_experiment(preparation=prepared, project_root=ROOT, artifact_writer=case.plane, output_dir=directory)
        execute = LocalProcessExecutor.execute
        def selected_refusal(self, runner, context, **kwargs):
            if context.task_id == owner.task_id(refused_root, "prefix"):
                raise ResourceAdmissionError("disclosed no-contact missing-root control")
            return execute(self, runner, context, **kwargs)
        monkeypatch.setattr(LocalProcessExecutor, "execute", selected_refusal)
        report = run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=case.plane,
            maximum_parallel_tasks=4)
        assert report["status"] == "BLOCKED"
        def forbidden(*args, **kwargs):
            pytest.fail("closed mixed read entered executor/native science")
        monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
        monkeypatch.setattr(bindings, "execute_parameter_native_work", forbidden)
        monkeypatch.setattr(bindings, "execute_paired_response_native_work", forbidden)
        result = ExperimentProgrammeService(ROOT, case.plane).read(directory=directory)["scientific_result"]
        assessment = decode_canonical_bytes(canonical_json_document_bytes(result["assessment"]),
            NativeUtilityCustodyAssessment, maximum_bytes=None)
        actual = {value.root_id: value for value in assessment.outcomes}
        assert set(actual) == {nonuse_root, adverse_root}
        assert not actual[nonuse_root].usable and not actual[nonuse_root].success
        assert actual[adverse_root].usable and not actual[adverse_root].success
        assert tuple(value.root_id for value in assessment.missing_roots) == (refused_root,)
        assert assessment.assigned_units == 3 and assessment.usable_units == 1 and assessment.successes == 0
        assert assessment.tail_numerator == assessment.tail_denominator == 1
        assert result["criterion"]["value"]["alpha_numerator"] == 1
        assert result["criterion"]["value"]["alpha_denominator"] == 280
        assert result["qualification"] == result["sampling_warrant"] == "NOT_ESTABLISHED"
