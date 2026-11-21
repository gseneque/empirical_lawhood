# SPDX-License-Identifier: MPL-2.0
"""Exact authenticated size and schema controls without operational size tiers."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api import recursive_prospective_authoring as owner
from empirical_lawhood.methods.recursive_scientific_authoring.extension import REGISTRATION
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.design.experiment_entry import ExecutableStudyDefinition
from empirical_lawhood.design.recursive_authoring import RecursiveScientificSelection, RecursiveStudyDraft
from empirical_lawhood.design.study_issue import ImplementationSourceClosure
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.candidate_compiler import ExecutableStudyCandidate, ExecutableStudyCompilationReport, StudyTemplate
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.execution_envelope import ExecutionResourceEnvelopeSpec
from empirical_lawhood.execution.plans import CandidateExecutionPlan, CandidateRunPlan
from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.execution.recursive_prospective import RecursiveProspectiveAuthoringSpec
from empirical_lawhood.execution.study_issue import StudyExtensionDecoderRegistration
from tests import test_prospective_experiment as fixtures


MIB = 1024**2
selected = fixtures.selected

CLOSED_MEMBER_PROFILES = (
    ("draft.json", RecursiveStudyDraft),
    ("implementation.json", ImplementationSourceClosure),
    ("recursive-prospective.json", RecursiveProspectiveAuthoringSpec),
    ("authoring.json", ExecutableStudyDefinition),
    ("scientific-projection.json", RecursiveScientificSelection),
    ("decoder.json", StudyExtensionDecoderRegistration),
    ("source-closure.json", ImplementationSourceClosure),
    ("template.json", StudyTemplate),
    ("registry.json", CapabilityRegistry),
    ("resources.json", ExecutionResourceEnvelopeSpec),
    ("candidate-report.json", ExecutableStudyCompilationReport),
    ("candidate.json", ExecutableStudyCandidate),
    ("preissue-run-plan.json", CandidateRunPlan),
    ("preissue-execution-plan.json", CandidateExecutionPlan),
)

def _member(filename, kind, size):
    identity = ObjectIdentity("capacity." + filename.removesuffix(".json"), kind.SCHEMA, kind.VERSION, "a" * 64)
    return RecursiveWaveMember(filename, identity, size)


def test_one_installed_decoder_has_no_arbitrary_byte_tier():
    assert REGISTRATION.decoder_key == "recursive.scientific-selection"
    assert REGISTRATION.maximum_payload_bytes is None
    owner._require_selection_decoder(REGISTRATION)
    for forged in (replace(REGISTRATION, decoder_key=REGISTRATION.decoder_key + ".forged"),
                   replace(REGISTRATION, maximum_payload_bytes=32 * MIB)):
        with pytest.raises(ValueError, match="outside its exact installed allowlist"):
            owner._require_selection_decoder(forged)


@pytest.mark.parametrize("size,filename,kind", [
    *((2**40, filename, kind) for filename, kind in CLOSED_MEMBER_PROFILES),
    *((size, "scientific-projection.json", RecursiveScientificSelection)
      for size in (1, 32 * MIB + 1, 256 * MIB + 1)),
])
def test_closed_member_reads_use_authenticated_observed_size(filename, kind, size):
    member = _member(filename, kind, size)
    assert owner._prospective_member_codec(member, decoder_registration=REGISTRATION) == (kind, size)
    assert owner._prospective_member_codec(member) == (kind, size)
    for bad in (replace(member, identity=replace(member.identity, object_schema="empirical-lawhood/testing/foreign")),
                replace(member, identity=replace(member.identity, object_version="9.0.0"))):
        with pytest.raises(ValueError, match="schema/version"):
            owner._prospective_member_codec(bad)


def test_closed_member_profile_covers_complete_handoff(selected):
    packet = decode_canonical_bytes((selected.original.directory / "authored-wave.json").read_bytes(),
        AuthoredRecursiveWave, maximum_bytes=MIB)
    assert len(CLOSED_MEMBER_PROFILES) == 14
    assert {m.filename for m in packet.members} == {name for name, _ in CLOSED_MEMBER_PROFILES}
    for member in packet.members:
        kind = dict(CLOSED_MEMBER_PROFILES)[member.filename]
        assert owner._prospective_member_codec(member, decoder_registration=REGISTRATION) == (kind, member.size_bytes)


def _publish_decoder_bootstrap_case(selected, tmp_path, *, mutate_decoder):
    """Publish a real closed packet whose decoder selector fails authentication."""
    from tests.test_recursive_public_service import _plane

    plane = _plane(tmp_path / "decoder-selector-custody")
    directory = Path(plane.root.contract.canonical_path) / "selected"
    original = selected.original.directory
    packet = decode_canonical_bytes((original / "authored-wave.json").read_bytes(), AuthoredRecursiveWave, maximum_bytes=MIB)
    payloads = {member.filename: (original / member.filename).read_bytes() for member in packet.members}
    decoder = decode_canonical_bytes(payloads["decoder.json"], type(REGISTRATION), maximum_bytes=MIB)
    if mutate_decoder:
        decoder = replace(decoder, decoder_key=decoder.decoder_key + ".uninstalled", maximum_payload_bytes=32 * MIB)
        payloads["decoder.json"] = decoder.canonical_bytes()
    members = tuple(replace(member,
        identity=(ObjectIdentity.from_record(member.identity.object_id, decoder) if mutate_decoder
            else replace(member.identity, object_fingerprint="f" * 64)),
        size_bytes=len(payloads["decoder.json"])) if member.filename == "decoder.json" else member
        for member in packet.members)
    packet = replace(packet, members=members)
    relative = directory.relative_to(Path(plane.root.contract.canonical_path)).as_posix()
    for member in packet.members:
        plane.write(ArtifactWriteRequest("capacity.bootstrap." + member.filename.removesuffix(".json"),
            relative + "/" + member.filename, member.identity.object_schema, ArtifactProfile.CANONICAL_JSON,
            "application/json", "capacity.bootstrap", relative, payloads[member.filename],
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    plane.write(ArtifactWriteRequest("capacity.bootstrap.packet", relative + "/authored-wave.json", packet.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "capacity.bootstrap", relative, packet.canonical_bytes(),
        VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    return directory, plane
