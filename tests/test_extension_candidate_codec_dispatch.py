# SPDX-License-Identifier: MPL-2.0
"""Public candidate codec dispatch over unchanged tiny exposed scientific bytes.

Only installed codec subcaps are lowered around the existing real payload.
No large scientific payload, source guard replacement or native task is added.
"""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
from empirical_lawhood.adapters.methods.recursive_scientific_authoring.executable_binding import REGISTRATION
from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded32.executable_binding import REGISTRATION as BOUNDED
from empirical_lawhood.api import facade as owner
from empirical_lawhood.api.results import CompileCandidateRequest, OperationStatus
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalizationError
from tests import test_prospective_experiment as fixtures


selected = fixtures.selected


@pytest.fixture(scope="module")
def candidate_case(selected):
    handoff, factories, discovery, *_ = selected.original_parts
    selection = handoff.compilation.selected_scientific_projection
    raw = selection.canonical_bytes()
    proposal, = handoff.authoring.extension_set.extensions
    assert proposal.payload == ObjectIdentity.from_record(selection.selection_id, selection)
    return SimpleNamespace(selected=selected, handoff=handoff, factories=factories,
        discovery=discovery, selection=selection, raw=raw, proposal=proposal)


def _registry(case, *, primary_maximum=None, additional_changes=None, include_additional=True):
    original = EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
    schema = case.selection.SCHEMA
    primary_maximum = len(case.raw) - 1 if primary_maximum is None else primary_maximum
    primary = tuple(replace(row, maximum_bytes=primary_maximum) if row.record_schema == schema else row
        for row in original.registrations)
    additional = tuple(replace(row, **{"maximum_bytes": len(case.raw), **(additional_changes or {})})
        if row.record_schema == schema else row for row in original.additional_registrations)
    if not include_additional:
        additional = tuple(row for row in additional if row.record_schema != schema)
    return replace(original, registry_id="canonical-codecs.testing.candidate-dispatch",
        registrations=primary, additional_registrations=additional)


def _package(case, registration, **proposal_changes):
    payload = replace(case.proposal.payload, object_schema=registration.payload_schema,
        object_version=registration.payload_version)
    proposal = replace(case.proposal, **{"payload": payload, "decoder_key": registration.decoder_key,
        "decoder_version": registration.decoder_version, "decoder_config_sha256": registration.config_sha256,
        **proposal_changes})
    extension_set = replace(case.handoff.authoring.extension_set, extensions=(proposal,))
    return replace(case.handoff.authoring, extension_set=extension_set)


def _request(tmp_path, package, registration, payload):
    paths = {name: tmp_path / (name + ".json") for name in ("authoring", "decoder", "payload")}
    paths["authoring"].write_bytes(package.canonical_bytes())
    paths["decoder"].write_bytes(registration.canonical_bytes())
    paths["payload"].write_bytes(payload)
    return CompileCandidateRequest(paths["authoring"], (paths["payload"],), (paths["decoder"],))


def _api(case, registry, *, missing_owner=None, external_root=None):
    aggregate = case.factories.aggregate
    if missing_owner == "aggregate":
        aggregate = None
    elif missing_owner == "bounded-binding":
        removed = {row.binding_id for row in aggregate.bindings if row.accepts_issued_decoder_registration(BOUNDED)}
        assert removed
        aggregate = replace(aggregate, bindings=tuple(row for row in aggregate.bindings if row.binding_id not in removed),
            availability=tuple(row for row in aggregate.availability if row.binding is None or row.binding.object_id not in removed))
    return owner.EmpiricalLawhoodApi(repo_root=case.selected.root / "checkout", external_root=external_root,
        candidate_context_provider=case.handoff.context, candidate_capability_catalog=case.handoff.context.catalog,
        extension_bundle_aggregate=case.discovery, executable_binding_aggregate=aggregate,
        study_extension_codec_registry=registry)


def _observe_payload_reads(monkeypatch):
    reads = []
    original = owner.read_bounded_bytes

    def observed(path, *, maximum_bytes):
        reads.append((Path(path).name, maximum_bytes))
        return original(path, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(owner, "read_bounded_bytes", observed)
    return reads


def _invalid_before_payload(api, request, reads):
    result = api.compile_candidate(request)
    assert result.status is OperationStatus.INVALID
    assert result.reason_codes == ("EXTENSION_CANDIDATE_INVALID",)
    assert result.payload is None
    assert reads == []


@pytest.mark.parametrize("registration", (REGISTRATION, BOUNDED), ids=("legacy", "bounded32"))
def test_public_candidate_uses_exact_installed_decoder_and_preserves_canonical_receipt(candidate_case, tmp_path, monkeypatch, registration):
    case = candidate_case
    maximum = len(case.raw)
    registry = _registry(case, primary_maximum=maximum if registration == REGISTRATION else maximum - 1)
    primary_before = registry.registration(case.selection.SCHEMA).canonical_bytes()
    package = _package(case, registration)
    base_before = package.base.canonical_bytes()
    request = _request(tmp_path, package, registration, case.raw)
    reads = _observe_payload_reads(monkeypatch)
    result = _api(case, registry).compile_candidate(request)
    assert result.status is OperationStatus.SUCCEEDED, result
    assert result.payload is not None and result.payload.report.candidate is not None
    assert result.payload.report.candidate.authoring_package == package
    receipt, = result.payload.report.extension_materializations
    proposal, = package.extension_set.extensions
    assert receipt.payload == proposal.payload == ObjectIdentity.from_record(case.selection.selection_id, case.selection)
    assert receipt.proposed_extension == ObjectIdentity.from_record(proposal.extension_id, proposal)
    assert receipt.decoder_registration == ObjectIdentity.from_record(registration.registration_id, registration)
    assert receipt.byte_count == len(case.raw) and receipt.physical_sha256 == sha256(case.raw).hexdigest()
    assert receipt.receipt_id == "extension-materialization." + proposal.extension_id + "." + sha256(case.raw).hexdigest()[:16]
    expected_receipt = {"schema": "empirical-lawhood/runtime/study-extension-materialization-receipt", "version": "1.0.0",
        "value": {"receipt_id": receipt.receipt_id, "extension_id": proposal.extension_id,
            "proposed_extension": ObjectIdentity.from_record(proposal.extension_id, proposal).to_document(),
            "payload": proposal.payload.to_document(), "byte_count": len(case.raw),
            "physical_sha256": sha256(case.raw).hexdigest(),
            "decoder_registration": ObjectIdentity.from_record(registration.registration_id, registration).to_document(),
            "outcome_access": "outcome-blind", "visibility_ceiling": "PROSPECTIVE"}}
    assert receipt.canonical_bytes() == (json.dumps(expected_receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert reads == [("payload.json", maximum)]
    assert package.base.canonical_bytes() == base_before
    assert case.selection.canonical_bytes() == case.raw == request.extension_payload_paths[0].read_bytes()
    assert registry.registration(case.selection.SCHEMA).canonical_bytes() == primary_before


def test_legacy_and_unkeyed_default_never_upgrade_to_the_additional_codec(candidate_case, tmp_path, monkeypatch):
    case = candidate_case
    registry = _registry(case)
    with pytest.raises(CanonicalizationError, match="exceeds its bounded contract"):
        registry.decode(case.raw, expected_schema=case.selection.SCHEMA)
    reads = _observe_payload_reads(monkeypatch)
    request = _request(tmp_path, _package(case, REGISTRATION), REGISTRATION, case.raw)
    _invalid_before_payload(_api(case, registry), request, reads)


@pytest.mark.parametrize("field,value", (
    ("registration_id", "decoder.recursive-scientific-selection-bounded32.forged"),
    ("decoder_key", "recursive.scientific-selection-bounded32.forged"),
    ("decoder_version", "9.0.0"),
    ("payload_schema", "empirical-lawhood/testing/foreign-candidate-science"),
    ("payload_version", "9.0.0"),
    ("config_sha256", "f" * 64),
    ("implementation_sha256", "f" * 64),
    ("maximum_payload_bytes", 33 * 1024**2),
    ("maximum_payload_bytes", 16 * 1024**2),
))
def test_every_changed_full_decoder_identity_refuses_before_payload_read(candidate_case, tmp_path, monkeypatch, field, value):
    case = candidate_case
    changed = replace(BOUNDED, **{field: value})
    # Keep descriptor/proposal scalar joins coherent: installed full ownership
    # must reject this, including registration ID and both cap forgeries.
    request = _request(tmp_path, _package(case, changed), changed, case.raw)
    reads = _observe_payload_reads(monkeypatch)
    _invalid_before_payload(_api(case, _registry(case)), request, reads)


@pytest.mark.parametrize("field,value", (
    ("decoder_key", "decoder.other-proposal"),
    ("decoder_version", "9.0.0"),
    ("decoder_config_sha256", "f" * 64),
    ("object_schema", "empirical-lawhood/testing/foreign-proposal"),
    ("object_version", "9.0.0"),
))
def test_proposal_descriptor_mismatch_refuses_before_payload_read(candidate_case, tmp_path, monkeypatch, field, value):
    case = candidate_case
    changes = {"payload": replace(case.proposal.payload, **{field: value})} if field.startswith("object_") else {field: value}
    request = _request(tmp_path, _package(case, BOUNDED, **changes), BOUNDED, case.raw)
    reads = _observe_payload_reads(monkeypatch)
    _invalid_before_payload(_api(case, _registry(case)), request, reads)


@pytest.mark.parametrize("changes", ({"decoder_implementation_sha256": "f" * 64}, {"maximum_bytes": 32 * 1024**2 + 1}),
    ids=("implementation", "upward-cap"))
def test_additional_codec_must_match_implementation_and_decoder_subcap(candidate_case, tmp_path, monkeypatch, changes):
    case = candidate_case
    request = _request(tmp_path, _package(case, BOUNDED), BOUNDED, case.raw)
    reads = _observe_payload_reads(monkeypatch)
    _invalid_before_payload(_api(case, _registry(case, additional_changes=changes)), request, reads)


@pytest.mark.parametrize("missing_owner", ("aggregate", "bounded-binding"))
def test_larger_codec_requires_its_full_installed_owner(candidate_case, tmp_path, monkeypatch, missing_owner):
    case = candidate_case
    request = _request(tmp_path, _package(case, BOUNDED), BOUNDED, case.raw)
    reads = _observe_payload_reads(monkeypatch)
    _invalid_before_payload(_api(case, _registry(case), missing_owner=missing_owner), request, reads)


@pytest.mark.parametrize("registration", (REGISTRATION, BOUNDED), ids=("legacy", "bounded32"))
def test_declared_size_above_selected_codec_refuses_before_payload_read(candidate_case, tmp_path, monkeypatch, registration):
    case = candidate_case
    request = _request(tmp_path, _package(case, registration, payload_size_bytes=len(case.raw) + 1), registration, case.raw)
    reads = _observe_payload_reads(monkeypatch)
    _invalid_before_payload(_api(case, _registry(case, primary_maximum=len(case.raw))), request, reads)


def test_missing_additional_codec_cannot_enlarge_primary_from_declared_decoder_cap(candidate_case, tmp_path, monkeypatch):
    case = candidate_case
    request = _request(tmp_path, _package(case, BOUNDED), BOUNDED, case.raw)
    reads = _observe_payload_reads(monkeypatch)
    _invalid_before_payload(_api(case, _registry(case, include_additional=False)), request, reads)


@pytest.mark.parametrize("damage", ("oversized", "truncated", "noncanonical", "different-identity"))
def test_payload_bound_canonical_bytes_and_frozen_identity_still_apply(candidate_case, tmp_path, monkeypatch, damage):
    case = candidate_case
    raw = case.raw
    if damage == "oversized":
        raw += b" "
    elif damage == "truncated":
        raw = raw[:-2]
    elif damage == "noncanonical":
        raw = b" " + raw[:-1]
    else:
        old_id = case.selection.selection_id
        changed = replace(case.selection, selection_id=old_id[:-1] + ("x" if old_id[-1] != "x" else "y"))
        raw = changed.canonical_bytes()
        assert len(raw) == len(case.raw)
    request = _request(tmp_path, _package(case, BOUNDED), BOUNDED, raw)
    reads = _observe_payload_reads(monkeypatch)
    result = _api(case, _registry(case)).compile_candidate(request)
    assert result.status is OperationStatus.INVALID
    assert result.reason_codes == ("EXTENSION_CANDIDATE_INVALID",)
    assert reads == [("payload.json", len(case.raw))]
