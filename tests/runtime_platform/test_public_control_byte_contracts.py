# SPDX-License-Identifier: MPL-2.0
"""Public control capacities over existing tiny, disclosed software records.

Only byte allocations are scaled around real canonical controls. The public
compiler, strict parser and prospective producer execute; source capture uses
the existing synthetic fixture and no worker or scientific array is executed.
"""

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from empirical_lawhood.api import codecs
from empirical_lawhood.api import recursive_prospective_authoring as prospective
from empirical_lawhood.storage.contracts.artifacts import ArtifactCustodyLimits
from tests import test_extension_candidate_codec_dispatch as candidate_fixtures
from tests import test_recursive_prospective_resource_preview as preview_fixtures


selected = candidate_fixtures.selected
candidate_case = candidate_fixtures.candidate_case


def test_closed_definition_uses_observed_bytes_and_optional_operator_bound(candidate_case, tmp_path):
    record = candidate_case.handoff.authoring
    payload = record.canonical_bytes() + b" " * 17
    path = tmp_path / "executable-authoring.json"
    path.write_bytes(payload)
    loaded = codecs.load_executable_study_authoring_materialization(path)
    assert loaded.record == record
    assert loaded.raw_bytes == payload and loaded.byte_count == len(payload)
    assert loaded.raw_materialization_sha256 == sha256(b"application/json\x00" + payload).hexdigest()
    assert codecs.load_registered_authoring(path, root_schemas={record.SCHEMA: type(record)}, maximum_bytes=2**40) == record
    with pytest.raises(codecs.AuthoringCodecError, match="byte limit"):
        codecs.load_registered_authoring(path, root_schemas={record.SCHEMA: type(record)}, maximum_bytes=len(payload)-1)


def test_explicit_parser_node_allowance_is_optional():
    codecs._validate_parsed_structure([1, 2, 3])
    with pytest.raises(codecs.AuthoringCodecError, match="node limit"):
        codecs._validate_parsed_structure([1, 2, 3], maximum_nodes=2)


def test_explicit_local_emission_allowance_is_respected(candidate_case, tmp_path):
    case = candidate_case
    api = candidate_fixtures._api(case, candidate_fixtures._registry(case, primary_maximum=len(case.raw)))
    source = tmp_path / 'input.json'
    source.write_bytes(case.raw)
    payload = b'operational output'
    with pytest.raises(ValueError, match='selected byte allowance'):
        api._emit_local_candidate(draft_path=source, requested_path=Path('refused.json'), payload=payload, maximum_bytes=len(payload)-1)
    assert not (tmp_path / 'refused.json').exists()
    api._emit_local_candidate(draft_path=source, requested_path=Path('observed.json'), payload=payload)
    assert (tmp_path / 'observed.json').read_bytes() == payload


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
        with pytest.raises(ValueError, match=role + ".*selected custody byte allowance"):
            call()
        assert not (destination / "candidate.json").exists()
        assert not (destination / "authored-wave.json").exists()
        assert not (destination / role).exists()
        # Prerequisite input custody and pure compiler scratch may exist. They
        # do not constitute a completed handoff, issue, execution or qualification.
    assert len(observed) == 1
