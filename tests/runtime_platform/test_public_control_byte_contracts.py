# SPDX-License-Identifier: MPL-2.0
"""Public control capacities over existing tiny, disclosed software records.

Only byte allocations are scaled around real canonical controls. The public
compiler, strict parser and prospective producer execute; source capture uses
the existing synthetic fixture and no worker or scientific array is executed.
"""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from empirical_lawhood.api import codecs
from empirical_lawhood.api import facade as owner
from empirical_lawhood.api import recursive_prospective_authoring as prospective
from empirical_lawhood.api.results import OperationStatus
from empirical_lawhood.runtime import study_issue
from empirical_lawhood.runtime.artifacts import ArtifactCustodyLimits
from tests import test_extension_candidate_codec_dispatch as candidate_fixtures
from tests import test_recursive_prospective_resource_preview as preview_fixtures


selected = candidate_fixtures.selected
candidate_case = candidate_fixtures.candidate_case


def test_closed_definition_preserves_materialization_and_generic_capacity(candidate_case, tmp_path, monkeypatch):
    record = candidate_case.handoff.authoring
    payload = record.canonical_bytes() + b" " * 17
    path = tmp_path / "executable-authoring.json"
    path.write_bytes(payload)
    assert codecs.MAX_AUTHORING_BYTES == 128 * 1024**2
    assert codecs.MAX_COMPOSED_PROGRAMME_CONTROL_BYTES == 256 * 1024**2
    monkeypatch.setattr(codecs, "MAX_EXECUTABLE_STUDY_AUTHORING_BYTES", len(payload))

    loaded = codecs.load_executable_study_authoring_materialization(path)
    assert loaded.record == record
    assert loaded.raw_bytes == payload and loaded.byte_count == len(payload)
    assert loaded.raw_materialization_sha256 == sha256(b"application/json\x00" + payload).hexdigest()
    assert codecs.load_executable_study_authoring(path).canonical_bytes() == record.canonical_bytes()

    # This explicit smaller generic allocation cannot inherit the closed role.
    with pytest.raises(codecs.AuthoringCodecError, match="byte limit"):
        codecs.load_registered_authoring(path, root_schemas={record.SCHEMA: type(record)},
            maximum_bytes=len(payload) - 1)


@pytest.mark.parametrize("extra", (0, 1), ids=("exact-bound", "bound-plus-one"))
def test_closed_definition_exact_finite_bound(candidate_case, tmp_path, monkeypatch, extra):
    record = candidate_case.handoff.authoring
    payload = record.canonical_bytes()
    path = tmp_path / "executable-authoring.json"
    path.write_bytes(payload)
    monkeypatch.setattr(codecs, "MAX_EXECUTABLE_STUDY_AUTHORING_BYTES", len(payload) - extra)
    if extra:
        with pytest.raises(codecs.AuthoringCodecError, match="byte limit"):
            codecs.load_executable_study_authoring(path)
    else:
        assert codecs.load_executable_study_authoring(path) == record


@pytest.mark.parametrize("damage", ("foreign-root", "wrong-revision", "duplicate-key", "extra-field", "bare-fraction"))
def test_closed_definition_keeps_strict_schema_and_lexical_refusals(candidate_case, tmp_path, damage):
    record = candidate_case.handoff.authoring
    document = json.loads(record.canonical_bytes())
    if damage == "foreign-root":
        document["schema"] = "empirical-lawhood/testing/unregistered-control"
    elif damage == "wrong-revision":
        document["version"] = "99.0.0"
    elif damage == "extra-field":
        document["value"]["undeclared"] = True
    elif damage == "bare-fraction":
        document["value"]["undeclared"] = 0.25
    payload = json.dumps(document).encode()
    if damage == "duplicate-key":
        payload = payload.replace(b'{"schema":', b'{"schema": "duplicate.root", "schema":', 1)
    path = tmp_path / "invalid-authoring.json"
    path.write_bytes(payload)
    with pytest.raises(codecs.AuthoringCodecError):
        codecs.load_executable_study_authoring(path)


def test_closed_definition_keeps_generic_node_guard(candidate_case, tmp_path, monkeypatch):
    path = tmp_path / "executable-authoring.json"
    path.write_bytes(candidate_case.handoff.authoring.canonical_bytes())
    monkeypatch.setattr(codecs, "MAX_AUTHORING_NODES", 1)
    with pytest.raises(codecs.AuthoringCodecError, match="node limit"):
        codecs.load_executable_study_authoring(path)


@pytest.mark.parametrize("allowed", (True, False), ids=("exact-bound", "early-refusal"))
def test_actual_public_compile_obeys_closed_definition_bound(candidate_case, tmp_path, monkeypatch, allowed):
    case = candidate_case
    registration = candidate_fixtures.REGISTRATION
    package = candidate_fixtures._package(case, registration)
    request = candidate_fixtures._request(tmp_path, package, registration, case.raw)
    monkeypatch.setattr(codecs, "MAX_EXECUTABLE_STUDY_AUTHORING_BYTES",
        len(package.canonical_bytes()) - (not allowed))
    reads = candidate_fixtures._observe_payload_reads(monkeypatch)
    result = candidate_fixtures._api(case,
        candidate_fixtures._registry(case, primary_maximum=len(case.raw))).compile_candidate(request)
    if allowed:
        assert result.status is OperationStatus.SUCCEEDED
        assert result.payload.report.candidate.authoring_package == package
        assert result.payload.report.extension_materializations[0].payload == case.proposal.payload
    else:
        assert result.status is OperationStatus.INVALID
        assert result.payload is None
        assert reads == []  # Deny before any extension payload/provider work.


def test_authoring_capacity_refuses_before_input_publication_or_outer_compile(selected, monkeypatch):  # noqa: F811
    monkeypatch.setattr(codecs, "MAX_EXECUTABLE_STUDY_AUTHORING_BYTES", 1)

    def deny(*args, **kwargs):
        pytest.fail("oversized authoring reached publication or outer compilation")

    monkeypatch.setattr(selected.plane, "write", deny)
    monkeypatch.setattr(prospective, "_compile_outer_candidate", deny)
    with pytest.raises(ValueError, match="authoring.json.*public composed-control"):
        prospective.preview_recursive_prospective_candidate(
            design_inputs=prospective.RecursiveProspectiveDesignInputs.from_spec(selected.prospective_spec),
            **preview_fixtures._arguments(selected))


def test_candidate_capacity_refuses_before_closed_handoff_publication(selected, monkeypatch):  # noqa: F811
    destination = selected.plane.root.resolve("public-candidate-capacity-refusal", for_write=True)
    monkeypatch.setattr(study_issue, "MAX_COMPOSED_PROGRAMME_CONTROL_BYTES", 1)
    with pytest.raises(ValueError, match="candidate.json.*public composed-control"):
        prospective.author_recursive_prospective(spec=selected.prospective_spec, output_dir=destination,
            **preview_fixtures._arguments(selected))
    assert not (destination / "candidate.json").exists()
    assert not (destination / "authored-wave.json").exists()
    # Prerequisite input custody and pure compiler scratch may already exist;
    # they are not a completed candidate, issue, execution or qualification.


@pytest.mark.parametrize("role", ("preissue-run-plan.json", "preissue-execution-plan.json"))
@pytest.mark.parametrize("allowed", (True, False), ids=("exact-bound", "early-refusal"))
def test_actual_author_preissue_plan_capacity_preflight(selected, monkeypatch, role, allowed):  # noqa: F811
    """Scale one real rendered role's allocation while executing actual authoring.

    The existing disclosed source fixture and tiny real compiler execute. Only
    the byte allocation for the selected role is scaled at its real consumer;
    the existing helper enforces it and every other role keeps its real limit.
    No worker/provider, issue or scientific response array is executed.
    """
    original = prospective._require_prospective_public_member_capacity
    observed = []

    def selected_role_allocation(name, size_bytes, *, artifact_writer=None):
        if name == role:
            observed.append(size_bytes)
            selected_writer = SimpleNamespace(custody_limits=ArtifactCustodyLimits(
                control_record_bytes=size_bytes - (not allowed)))
            original(name, size_bytes, artifact_writer=selected_writer)
        else:
            original(name, size_bytes, artifact_writer=artifact_writer)

    monkeypatch.setattr(prospective, "_require_prospective_public_member_capacity", selected_role_allocation)
    destination = selected.plane.root.resolve("preissue-capacity-" + role.removesuffix(".json") +
        ("-allowed" if allowed else "-refused"), for_write=True)
    def call():
        return prospective.author_recursive_prospective(spec=selected.prospective_spec,
            output_dir=destination, **preview_fixtures._arguments(selected))
    if allowed:
        result = call()
        assert result["status"] == "AUTHORED_PROSPECTIVE" and result["native_contact"] == "none"
        assert (destination / role).stat().st_size == observed[0]
        assert (destination / "authored-wave.json").is_file()
    else:
        with pytest.raises(ValueError, match=role + ".*selected custody runtime-plan byte allowance"):
            call()
        assert not (destination / "candidate.json").exists()
        assert not (destination / "authored-wave.json").exists()
        assert not (destination / role).exists()
        # Prerequisite input custody and pure compiler scratch may exist. They
        # do not constitute a completed handoff, issue, execution or qualification.
    assert len(observed) == 1


@pytest.mark.parametrize("allowed", (True, False), ids=("exact-composed-bound", "one-byte-over"))
@pytest.mark.parametrize("with_external_root", (True, False), ids=("configured-plane", "local-only"))
def test_actual_public_candidate_emit_uses_closed_control_capacity(candidate_case, tmp_path, monkeypatch, allowed, with_external_root):
    """Scale only byte allocations around the real public compiler/emitter.

    The existing disclosed fixture supplies genuine tiny typed compiler inputs.
    No compiler, candidate, source guard, writer or canonical parser is stubbed;
    no native task or genuine authority is used. The generic emission allocation
    remains smaller, while the closed candidate uses its composed-control role.
    """
    case = candidate_case
    registration = candidate_fixtures.REGISTRATION
    package = candidate_fixtures._package(case, registration)
    request = candidate_fixtures._request(tmp_path, package, registration, case.raw)
    external_root = tmp_path / "scientific-plane" if with_external_root else None
    if external_root is not None:
        external_root.mkdir()
    api = candidate_fixtures._api(case,
        candidate_fixtures._registry(case, primary_maximum=len(case.raw)), external_root=external_root)
    baseline = api.compile_candidate(request)
    assert baseline.status is OperationStatus.SUCCEEDED
    candidate = baseline.payload.report.candidate
    payload = candidate.canonical_bytes()
    generic_limit = len(payload) - 1
    closed_limit = len(payload) - (not allowed)
    assert owner.MAX_COMPOSED_PROGRAMME_CONTROL_BYTES == study_issue.MAX_COMPOSED_PROGRAMME_CONTROL_BYTES == 256 * 1024**2
    monkeypatch.setattr(owner, "MAX_AUTHORING_BYTES", generic_limit)
    monkeypatch.setattr(owner, "MAX_COMPOSED_PROGRAMME_CONTROL_BYTES", closed_limit)
    monkeypatch.setattr(codecs, "MAX_COMPOSED_PROGRAMME_CONTROL_BYTES", closed_limit)

    with pytest.raises(ValueError, match="authoring byte limit"):
        api._emit_local_candidate(draft_path=request.path,
            requested_path=Path("generic-capacity.json"), payload=payload)
    assert not (tmp_path / "generic-capacity.json").exists()

    emitted = tmp_path / "closed-candidate.json"
    emit_request = replace(request, emit_path=Path(emitted.name))
    result = api.compile_candidate(emit_request)
    if allowed:
        assert result.status is OperationStatus.SUCCEEDED
        assert result.payload.local_candidate_emitted
        assert result.payload.local_bytes_written == len(payload)
        assert result.payload.local_candidate_sha256 == sha256(payload).hexdigest()
        assert emitted.read_bytes() == payload == result.payload.report.candidate.canonical_bytes()
        assert codecs.load_standard_study_candidate(emitted) == candidate
        # The larger role does not relax the actual no-replace filesystem gate.
        repeated = api.compile_candidate(emit_request)
        assert repeated.status is OperationStatus.CONFLICT
        assert repeated.reason_codes == ("LOCAL_CANDIDATE_NO_REPLACE",)
        assert emitted.read_bytes() == payload
        if external_root is not None:
            forbidden = api.compile_candidate(replace(request,
                emit_path=Path("scientific-plane/forbidden.json")))
            assert forbidden.status is OperationStatus.INVALID
            assert forbidden.reason_codes == ("EXTENSION_CANDIDATE_INVALID",)
            assert not tuple(external_root.iterdir())
    else:
        assert result.status is OperationStatus.INVALID
        assert result.reason_codes == ("EXTENSION_CANDIDATE_INVALID",)
        assert result.payload is None
        assert not emitted.exists()
    assert not tuple(tmp_path.glob(".closed-candidate.json.*.candidate-tmp"))
