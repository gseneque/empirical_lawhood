# SPDX-License-Identifier: MPL-2.0
"""Exact TRAIN nonentry metadata controls; disclosed fixtures confer no qualification."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import model_predictors
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays, branch_census
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case

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
    case = fresh_training_metadata_case(tmp_path)
    source, protocol = r.source_for(case.request, case.source.root_id, index=case.source.index), case.request.protocols[0]
    panels = r.panels_for(case.request, source)
    source_pin = r.scheduled_identity(source)
    member = MatrixArrayMember("disclosed", "<i8", (1,), sha256(bytes(8)).hexdigest())
    causal_arrays = r.NativeTrainingArrays("arrays.disclosed-causal", source_pin, "CAUSAL_STATE",
        ArtifactIdentity("array.disclosed-causal", "disclosed-metadata-no-body", MATRIX_ARRAY_SCHEMA,
            "a" * 64, "application/x-npz", 1), (member,), (source_pin,), DEV, EXPOSED)
    causal = r.NativeTrainingCausalPrefix("causal.disclosed-nonentry", source_pin,
        _pin("history.disclosed", r.NativeTrainingPrefixHistory), _pin("numerical.disclosed", r.NativeTrainingNumericalAssessment),
        _pin("witness.disclosed", r.NativeTrainingPrefixWitness), _pin("frames.disclosed", r.NativeTrainingFrameAssessment),
        r.scheduled_identity(source.policy), source.root.root, source.policy.cutoff_tick, None,
        "NO_ORIGIN", "disclosed-unavailable-origin", causal_arrays)
    physical = r.NativeTrainingPhysicalForecast("physical.disclosed-nonentry", source_pin, causal.identity,
        r.identity(protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
        None, _arrays(source, "FORECAST", "disclosed-physical", (member,)), "NO_ORIGIN",
        tuple((view, predictor, "UNRESOLVED", "disclosed-unavailable-instrument")
            for view in ("PRIMARY", "FINE") for predictor in model_predictors(protocol.mechanical_model)))
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
    response = r.NativeTrainingResponse("responses.disclosed-nonentry", r.scheduled_identity(value.source), causal.identity,
        physical.identity, value.case.acquisition.identity, r.identity(value.protocol), arrays, branches, (), expected,
        ("complete-paired-branch-slots-not-entered-" + expected.lower(),))
    return causal, physical, response


@pytest.mark.parametrize("causal_disposition,physical_disposition", (("NO_ORIGIN", "NO_ORIGIN"),
    ("UNEVALUABLE", "UNEVALUABLE"), ("AVAILABLE", "INSTRUMENT_UNRESOLVED"),
    ("NO_ORIGIN", "INSTRUMENT_UNRESOLVED")))
def test_exact_train_nonentry_retains_canonical_bytes_without_array_read_or_rng(metadata, monkeypatch,
        causal_disposition, physical_disposition):
    causal, physical, response = _nonentry(metadata, causal_disposition, physical_disposition)
    def forbidden(*args, **kwargs):
        pytest.fail("pure TRAIN nonentry validation entered array/native/RNG work")
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", forbidden)
    monkeypatch.setattr(bindings, "execute_parameter_native_work", forbidden)
    monkeypatch.setattr(bindings, "decode_matrix_arrays", forbidden)
    monkeypatch.setattr(bindings.np.random, "default_rng", forbidden)
    original = response.canonical_bytes()
    assert response.validate_nonentry(causal, physical, metadata.protocol, metadata.panels) is response
    assert response.canonical_bytes() == original and len(response.branch_ids) == 48 and response.native == ()


@pytest.mark.parametrize("defect", ("disposition", "reason", "branch-count", "member-count", "member-name",
    "dtype", "shape", "hash", "finite", "causal", "physical", "protocol", "available-future"))
def test_exact_train_nonentry_refuses_mislabelled_or_thinned_marker_and_available_work(metadata, defect):
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


@pytest.mark.parametrize("causal_disposition,physical_disposition", (("NO_ORIGIN", "NO_ORIGIN"), ("AVAILABLE", "INSTRUMENT_UNRESOLVED")))
def test_actual_train_worker_calls_shared_nonentry_relation_without_native_future(metadata, monkeypatch, causal_disposition, physical_disposition):
    causal, physical, _ = _nonentry(metadata, causal_disposition, physical_disposition)
    source, request = metadata.source, metadata.case.request
    wire = bindings.NativeTrainingOperationConfig("config.disclosed-nonentry-responses", "responses",
        metadata.case.specification.identity, request.identity,
        next(value for value in request.sources if value.root_id == source.root_id), None,
        r.identity(metadata.protocol), metadata.panels, request.resources.for_operation("responses"),
        (("prefix", _pin("config.disclosed-prefix", bindings.NativeTrainingOperationConfig)),))
    config = bindings._BoundConfiguration(wire, metadata.protocol)
    runner = bindings.NativeTrainingNativeRunner("responses")
    records = dict(history=object(), causal=causal, physical=physical, acquisition=metadata.case.acquisition)
    context = SimpleNamespace(input_ports=(), output_ports=(SimpleNamespace(
        profile=ArtifactProfile.MATRIX_ARRAY_NPZ, logical_artifact_id="array.disclosed-owner-nonentry"),))
    def forbidden(*args, **kwargs):
        pytest.fail("unentered TRAIN owner called a native producer")
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", forbidden)
    monkeypatch.setattr(bindings, "execute_parameter_native_work", forbidden)
    monkeypatch.setattr(bindings, "_decode", lambda *args, **kwargs: (config, metadata.case.specification, source, records, {}))
    monkeypatch.setattr(bindings, "_native_work", lambda *args, **kwargs: (None, None, None))
    monkeypatch.setattr(runner, "_response_arrays", lambda context: (None, None))
    monkeypatch.setattr(bindings, "_outputs", lambda context, product, **kwargs: product)
    observed = []
    validate = r.NativeTrainingResponse.validate_nonentry
    def checked(self, *args):
        observed.append(self.disposition)
        return validate(self, *args)
    monkeypatch.setattr(r.NativeTrainingResponse, "validate_nonentry", checked)
    response = runner.execute_with_native_subwork(context, SimpleNamespace(parent_contact=None))
    assert observed == [physical_disposition] and response.native == ()



@pytest.mark.parametrize("defect", (None, "reason", "hash", "available-future"))
def test_actual_train_score_worker_checks_nonentry_before_arrays_or_score(metadata, monkeypatch, defect):
    causal, physical, response = _nonentry(metadata, "AVAILABLE",
        "AVAILABLE" if defect == "available-future" else "INSTRUMENT_UNRESOLVED")
    if defect == "reason":
        response = replace(response, reason_codes=("resealed-wrong-owner-reason",))
    elif defect == "hash":
        member, = response.arrays.members
        response = replace(response, arrays=replace(response.arrays, members=(replace(member, sha256="f" * 64),)))
    response.canonical_bytes()
    config = SimpleNamespace(protocol=metadata.protocol, panels=metadata.panels, specification=metadata.case.specification.identity)
    records = dict(history=SimpleNamespace(arrays=object()), causal=causal, physical=physical,
        responses=response, acquisition=metadata.case.acquisition, feature=object())
    context = SimpleNamespace(input_ports=(), output_ports=(), task_id="test.response-score")
    monkeypatch.setattr(bindings, "_decode", lambda *args: (config, metadata.case.specification, metadata.source, records, {}))
    events = []
    def values(*args):
        if defect is not None:
            pytest.fail("invalid TRAIN nonentry reached array decoding")
        events.append("arrays")
        return {}
    monkeypatch.setattr(bindings, "_values", values)
    def score(*args):
        if defect is not None:
            pytest.fail("invalid TRAIN nonentry reached score")
        events.append("score")
        return object(), object()
    monkeypatch.setattr(bindings.science, "score", score)
    monkeypatch.setattr(bindings, "_outputs", lambda *args, **kwargs: object())
    def forbidden(*args, **kwargs):
        pytest.fail("pure TRAIN nonentry consumer entered native work")
    monkeypatch.setattr(bindings, "execute_parameter_native_work", forbidden)
    monkeypatch.setattr(bindings, "execute_paired_response_native_work", forbidden)
    if defect is None:
        bindings.NativeTrainingRunner("response-score").execute(context)
        assert events == ["arrays", "arrays", "arrays", "score"]
    else:
        with pytest.raises(ValueError, match="native TRAIN response nonentry changes"):
            bindings.NativeTrainingRunner("response-score").execute(context)
        assert events == []


def test_training_nonentry_rejects_cross_family_operands(metadata, tmp_path):
    from tests.test_matrix_native_utility_nonentry import metadata as utility_metadata
    directory = tmp_path / "separate-e2-metadata"
    directory.mkdir()
    foreign = utility_metadata.__wrapped__(directory)
    causal, physical, response = _nonentry(metadata, "NO_ORIGIN", "NO_ORIGIN")
    with pytest.raises(TypeError, match="exact actual operand"):
        response.validate_nonentry(foreign.causal, physical, metadata.protocol, metadata.panels)
    with pytest.raises(TypeError, match="exact actual operand"):
        response.validate_nonentry(causal, foreign.physical, metadata.protocol, metadata.panels)

@pytest.mark.parametrize("defect", ("reason", "hash", "available-future"))
def test_actual_training_science_rejects_nonentry_before_array_assessment(metadata, monkeypatch, defect):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_science as science
    causal, physical, response = _nonentry(metadata, "AVAILABLE",
        "AVAILABLE" if defect == "available-future" else "INSTRUMENT_UNRESOLVED")
    if defect == "reason":
        response = replace(response, reason_codes=("resealed-wrong-owner-reason",))
    elif defect == "hash":
        member, = response.arrays.members
        response = replace(response, arrays=replace(response.arrays, members=(replace(member, sha256="f" * 64),)))
    def forbidden(*args, **kwargs):
        pytest.fail("invalid TRAIN nonentry reached received-array scoring")
    monkeypatch.setattr(science, "assess_paired_response_arrays", forbidden)
    with pytest.raises(ValueError, match="native TRAIN response nonentry changes"):
        science.score(metadata.case.specification, metadata.source, metadata.protocol, metadata.panels,
            metadata.case.acquisition, object(), causal, physical, response, {}, {}, {}, object())

@pytest.mark.parametrize("partial,status,typed", ((True, "SUCCEEDED", None), (True, "PARTIAL", None),
    (False, "REFUSED", None), (False, "SUCCEEDED", "DEFERRED")))
def test_training_compact_partial_or_refused_read_does_not_open_scientific_products(metadata, partial, status, typed):
    from empirical_lawhood.api.matrix_native_training_read import read_development_result
    class Unreadable:
        def __getattribute__(self, name):
            pytest.fail("deferred TRAIN read touched scientific custody: " + name)
        def __getitem__(self, key):
            pytest.fail("deferred TRAIN read opened scientific payload: " + str(key))
    poison = Unreadable()
    result = read_development_result(directory=poison, artifact_writer=poison,
        specification=metadata.case.specification, instance=poison, payloads=poison,
        report={"status": status, "typed_product_validation": typed}, products=poison,
        draft=poison, plan=poison, allow_partial=partial)
    assert result["scientific_completion"] == result["qualification"] == "NOT_ESTABLISHED"
    assert result["assigned_units"] == 1 and result["new_native_contact_count"] == 0


def test_training_root_read_refuses_a_foreign_source_index_before_opening_products(metadata):
    from empirical_lawhood.api.matrix_native_training_read import _authenticate_root_records
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex

    case = metadata.case
    manifest = case.request.train_manifest
    foreign = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification,
        provenances=(replace(manifest.provenances[0], observed_git_head="f" * 40),))
    original = case.request.canonical_bytes()
    def forbidden(*_args, **_kwargs):
        pytest.fail("foreign TRAIN source index opened a scientific product")
    with pytest.raises(ValueError, match="shared scientific parents"):
        _authenticate_root_records(case.specification, case.request, case.acquisition, metadata.source.root_id,
            {}, None, {}, "run.unread-foreign-source", source_index=foreign, get=forbidden)
    assert case.request.canonical_bytes() == original
