# SPDX-License-Identifier: MPL-2.0
"""Finite additive capacity over unchanged, exposed scientific record bytes.

These controls use one existing tiny software fixture. Advertised member sizes
exercise physical carrier limits without manufacturing large scientific data.
No native execution, qualification or genuine authority is established.
"""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from empirical_lawhood.api import recursive_prospective_authoring as owner
from empirical_lawhood.adapters.methods.recursive_scientific_authoring.executable_binding import REGISTRATION
from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded32.executable_binding import REGISTRATION as BOUNDED_REGISTRATION
from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded64.executable_binding import REGISTRATION as LARGE_REGISTRATION
from empirical_lawhood.adapters.methods.recursive_scientific_authoring_draft128.executable_binding import REGISTRATION as EXTENDED_REGISTRATION
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_entry import ExecutableStudyDefinition
from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection, RecursiveStudyDraft
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.candidate_compiler import ExecutableStudyCandidate, ExecutableStudyCompilationReport, StudyTemplate
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeSpec
from empirical_lawhood.runtime.plans import CandidateExecutionPlan, CandidateRunPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec, RecursiveProspectiveDesignInputs
from empirical_lawhood.runtime.recursive_prospective import recursive_selection_proposal
from empirical_lawhood.runtime import recursive_prospective_envelope as envelopes
from empirical_lawhood.runtime.study_issue import StudyExtensionDecoderRegistration
from tests import test_prospective_experiment as fixtures


MIB = 1024**2
selected = fixtures.selected

# This is the complete retained handoff contract, including members whose
# finite allocation is deliberately identical under all installed decoders.
CLOSED_MEMBER_PROFILES = (
    ("draft.json", RecursiveStudyDraft, 16 * MIB, 32 * MIB, 64 * MIB, 128 * MIB),
    ("implementation.json", ImplementationSourceClosure, 16 * MIB, 16 * MIB, 16 * MIB, 16 * MIB),
    ("recursive-prospective.json", RecursiveProspectiveAuthoringSpec, 16 * MIB, 16 * MIB, 16 * MIB, 16 * MIB),
    ("authoring.json", ExecutableStudyDefinition, 16 * MIB, 16 * MIB, 512 * MIB, 512 * MIB),
    ("scientific-projection.json", RecursiveScientificSelection, 16 * MIB, 32 * MIB, 64 * MIB, 64 * MIB),
    ("decoder.json", StudyExtensionDecoderRegistration, 16 * MIB, 16 * MIB, 16 * MIB, 16 * MIB),
    ("source-closure.json", ImplementationSourceClosure, 16 * MIB, 16 * MIB, 16 * MIB, 16 * MIB),
    ("template.json", StudyTemplate, 16 * MIB, 32 * MIB, 64 * MIB, 64 * MIB),
    ("registry.json", CapabilityRegistry, 16 * MIB, 16 * MIB, 16 * MIB, 16 * MIB),
    ("resources.json", ExecutionResourceEnvelopeSpec, 16 * MIB, 16 * MIB, 16 * MIB, 16 * MIB),
    ("candidate-report.json", ExecutableStudyCompilationReport, 64 * MIB, 128 * MIB, 512 * MIB, 512 * MIB),
    ("candidate.json", ExecutableStudyCandidate, 64 * MIB, 64 * MIB, 512 * MIB, 512 * MIB),
    ("preissue-run-plan.json", CandidateRunPlan, 64 * MIB, 64 * MIB, 512 * MIB, 512 * MIB),
    ("preissue-execution-plan.json", CandidateExecutionPlan, 64 * MIB, 64 * MIB, 512 * MIB, 512 * MIB),
)


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":")) + "\n").encode()


def _member(filename, kind, size):
    identity = ObjectIdentity("capacity." + filename.removesuffix(".json"), kind.SCHEMA, kind.VERSION, "a" * 64)
    return RecursiveWaveMember(filename, identity, size)


def test_legacy_decoder_registration_keeps_its_exact_original_canonical_bytes():
    expected = {"schema": "empirical-lawhood/runtime/study-extension-decoder-registration", "version": "1.0.0",
        "value": {"registration_id": "decoder.recursive-scientific-selection",
            "decoder_key": "recursive.scientific-selection", "decoder_version": "1.0.0",
            "payload_schema": "empirical-lawhood/planning/recursive-scientific-selection", "payload_version": "1.0.0",
            "config_sha256": sha256(b"empirical-lawhood/planning/recursive-scientific-selection").hexdigest(),
            "implementation_sha256": sha256(b"recursive-scientific-authoring-v1:typed-selected-science-preservation").hexdigest(),
            "maximum_payload_bytes": 16 * MIB}}
    assert REGISTRATION.canonical_bytes() == _json_bytes(expected)
    assert REGISTRATION.maximum_payload_bytes == 16 * MIB


@pytest.mark.parametrize("registration,fingerprint", (
    (BOUNDED_REGISTRATION, "999137a515012e7e77459048b03b33b07ffd873a32f2623001f9c487f50d8529"),
    (LARGE_REGISTRATION, "f120b56c48189cb7f8d7db30c9d5db7da8548f374c67fda3eb96a01dc63b8836"),
))
def test_existing_bounded_decoders_keep_their_original_canonical_bytes(registration, fingerprint):
    assert sha256(registration.canonical_bytes()).hexdigest() == fingerprint


@pytest.mark.parametrize("filename,kind,maximum", (
    ("draft.json", RecursiveStudyDraft, 16 * MIB),
    ("scientific-projection.json", RecursiveScientificSelection, 16 * MIB),
    ("template.json", StudyTemplate, 16 * MIB),
    ("candidate-report.json", ExecutableStudyCompilationReport, 64 * MIB),
    ("recursive-prospective.json", envelopes.RecursiveProspectiveAuthoringEnvelope, 32 * MIB),
))
def test_legacy_member_bounds_never_upgrade_from_the_advertised_size(filename, kind, maximum):
    member = _member(filename, kind, maximum)
    assert owner._prospective_member_codec(member) == (kind, maximum)
    assert owner._prospective_member_codec(member, decoder_registration=REGISTRATION) == (kind, maximum)
    with pytest.raises(ValueError):
        owner._prospective_member_codec(replace(member, size_bytes=maximum + 1))
    with pytest.raises(ValueError):
        owner._prospective_member_codec(replace(member, size_bytes=maximum + 1), decoder_registration=REGISTRATION)


def test_closed_member_profile_covers_the_complete_original_handoff(selected):
    original = selected.original.directory / "authored-wave.json"
    packet = decode_canonical_bytes(original.read_bytes(), AuthoredRecursiveWave, maximum_bytes=MIB)
    profiles = {filename: (kind, legacy, bounded, large, extended)
        for filename, kind, legacy, bounded, large, extended in CLOSED_MEMBER_PROFILES}
    assert len(CLOSED_MEMBER_PROFILES) == len(profiles) == 14
    assert {member.filename for member in packet.members} == set(profiles)
    for member in packet.members:
        kind, legacy, bounded, large, extended = profiles[member.filename]
        assert owner._prospective_member_codec(member) == (kind, legacy)
        assert owner._prospective_member_codec(member, decoder_registration=REGISTRATION) == (kind, legacy)
        assert owner._prospective_member_codec(member, decoder_registration=BOUNDED_REGISTRATION) == (kind, bounded)
        assert owner._prospective_member_codec(member, decoder_registration=LARGE_REGISTRATION) == (kind, large)
        assert owner._prospective_member_codec(member, decoder_registration=EXTENDED_REGISTRATION) == (kind, extended)


@pytest.mark.parametrize("filename,kind,legacy,bounded,large,extended", CLOSED_MEMBER_PROFILES,
    ids=[row[0] for row in CLOSED_MEMBER_PROFILES])
def test_every_closed_member_keeps_its_exact_finite_profile(filename, kind, legacy, bounded, large, extended):
    for registration, maximum in ((None, legacy), (REGISTRATION, legacy), (BOUNDED_REGISTRATION, bounded),
            (LARGE_REGISTRATION, large), (EXTENDED_REGISTRATION, extended)):
        member = _member(filename, kind, maximum)
        assert owner._prospective_member_codec(member, decoder_registration=registration) == (kind, maximum)
        with pytest.raises(ValueError, match="schema/version or byte allocation"):
            owner._prospective_member_codec(replace(member, size_bytes=maximum + 1), decoder_registration=registration)
        for field, value in (("object_schema", "empirical-lawhood/tests/foreign-member"), ("object_version", "9.0.0")):
            changed = replace(member, identity=replace(member.identity, **{field: value}))
            with pytest.raises(ValueError, match="schema/version or byte allocation"):
                owner._prospective_member_codec(changed, decoder_registration=registration)
        if maximum > legacy:
            with pytest.raises(ValueError, match="schema/version or byte allocation"):
                owner._prospective_member_codec(member)


def test_selected_template_advertised_size_requires_the_exact_bounded_profile():
    # This is the retained selected320 template's measured carrier size. The
    # control advertises bytes only; it creates no scientific payload or claim.
    member = _member("template.json", StudyTemplate, 22_931_304)
    for registration in (None, REGISTRATION):
        with pytest.raises(ValueError, match="schema/version or byte allocation"):
            owner._prospective_member_codec(member, decoder_registration=registration)
    assert owner._prospective_member_codec(member, decoder_registration=BOUNDED_REGISTRATION) == (StudyTemplate, 32 * MIB)
    with pytest.raises(ValueError, match="schema/version or byte allocation"):
        owner._prospective_member_codec(replace(member, size_bytes=32 * MIB + 1), decoder_registration=BOUNDED_REGISTRATION)


@pytest.mark.parametrize("registration", (None, REGISTRATION, BOUNDED_REGISTRATION, LARGE_REGISTRATION, EXTENDED_REGISTRATION),
    ids=("unselected", "legacy", "bounded32", "bounded64", "draft128"))
def test_closed_member_profiles_refuse_an_unknown_filename(registration):
    member = _member("template-copy.json", StudyTemplate, 1)
    with pytest.raises(ValueError, match="outside its closed allowlist"):
        owner._prospective_member_codec(member, decoder_registration=registration)


def test_v2_envelope_preserves_original_specification_and_wrapper_bytes(selected, tmp_path):
    specification = selected.prospective_spec
    original = specification.canonical_bytes()
    envelope = envelopes.RecursiveProspectiveAuthoringEnvelope.from_spec(specification)
    expected = {"schema": "empirical-lawhood/runtime/recursive-prospective-authoring-envelope", "version": "2.0.0",
        "value": {"envelope_id": specification.spec_id + ".operational-envelope",
            "original_spec": json.loads(original),
            "semantic_spec": ObjectIdentity.from_record(specification.spec_id, specification).to_document()}}
    assert envelope.canonical_bytes() == _json_bytes(expected)
    assert envelopes.MAXIMUM_OPERATIONAL_ENVELOPE_BYTES == 32 * MIB
    assert envelope.reconstruct().canonical_bytes() == original
    path = tmp_path / "legacy-v2-envelope.json"
    path.write_bytes(envelope.canonical_bytes())
    assert owner.load_recursive_prospective_envelope(path).canonical_bytes() == original
    for mutation in ("semantic-hash", "inner-spec", "schema", "revision"):
        document = json.loads(envelope.canonical_bytes())
        if mutation == "semantic-hash":
            document["value"]["semantic_spec"]["value"]["object_fingerprint"] = "f" * 64
        elif mutation == "inner-spec":
            document["value"]["original_spec"]["value"]["spec_id"] += ".changed"
        elif mutation == "schema":
            document["schema"] = RecursiveProspectiveAuthoringSpec.SCHEMA
        else:
            document["version"] = "9.0.0"
        path.write_bytes(_json_bytes(document))
        with pytest.raises(ValueError):
            owner.load_recursive_prospective_envelope(path)
    assert specification.canonical_bytes() == original


def test_v2_envelope_does_not_inherit_the_larger_envelope_allocation(selected, monkeypatch):
    envelope = envelopes.RecursiveProspectiveAuthoringEnvelope.from_spec(selected.prospective_spec)
    monkeypatch.setattr(envelopes, "MAXIMUM_OPERATIONAL_ENVELOPE_BYTES", len(envelope.canonical_bytes()) - 1)
    with pytest.raises(ValueError, match="32 MiB allocation"):
        envelopes.RecursiveProspectiveAuthoringEnvelope.from_spec(selected.prospective_spec)


def test_additive_decoder_selects_the_exact_original_scientific_bytes(selected):
    selection = selected.original.compilation.selected_scientific_projection
    original = selection.canonical_bytes()
    original_identity = ObjectIdentity.from_record(selection.selection_id, selection)
    assert BOUNDED_REGISTRATION is not REGISTRATION
    assert BOUNDED_REGISTRATION.registration_id == "decoder.recursive-scientific-selection-bounded32"
    assert BOUNDED_REGISTRATION.decoder_key == "recursive.scientific-selection-bounded32"
    assert BOUNDED_REGISTRATION.decoder_version == "1.0.0"
    assert BOUNDED_REGISTRATION.maximum_payload_bytes == 32 * MIB
    assert BOUNDED_REGISTRATION.payload_schema == REGISTRATION.payload_schema == selection.SCHEMA
    assert BOUNDED_REGISTRATION.payload_version == REGISTRATION.payload_version == selection.VERSION
    assert LARGE_REGISTRATION.registration_id == "decoder.recursive-scientific-selection-bounded64"
    assert LARGE_REGISTRATION.decoder_key == "recursive.scientific-selection-bounded64"
    assert LARGE_REGISTRATION.decoder_version == "1.0.0"
    assert LARGE_REGISTRATION.maximum_payload_bytes == 64 * MIB
    assert LARGE_REGISTRATION.payload_schema == selection.SCHEMA
    assert LARGE_REGISTRATION.payload_version == selection.VERSION
    assert EXTENDED_REGISTRATION.registration_id == "decoder.recursive-scientific-selection-draft128"
    assert EXTENDED_REGISTRATION.decoder_key == "recursive.scientific-selection-draft128"
    assert EXTENDED_REGISTRATION.decoder_version == "1.0.0"
    assert EXTENDED_REGISTRATION.maximum_payload_bytes == 64 * MIB
    assert EXTENDED_REGISTRATION.payload_schema == selection.SCHEMA
    assert EXTENDED_REGISTRATION.payload_version == selection.VERSION
    for registration in (REGISTRATION, BOUNDED_REGISTRATION, LARGE_REGISTRATION, EXTENDED_REGISTRATION):
        proposal = recursive_selection_proposal(selection=selection, registration=registration)
        assert proposal.payload == original_identity
        assert proposal.payload_size_bytes == len(original)
        assert proposal.decoder_key == registration.decoder_key
        assert decode_canonical_bytes(original, RecursiveScientificSelection, maximum_bytes=registration.maximum_payload_bytes) == selection
    assert owner._selection_decoder_registration(selection) == REGISTRATION
    assert selection.canonical_bytes() == original


def test_decoder_selector_honours_measured_capacity_and_refuses_unsupported_science(selected, monkeypatch):
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring import executable_binding as legacy
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded32 import executable_binding as bounded
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_bounded64 import executable_binding as large
    from empirical_lawhood.adapters.methods.recursive_scientific_authoring_draft128 import executable_binding as extended

    selection = selected.original.compilation.selected_scientific_projection
    original = selection.canonical_bytes()
    # Scale only the four installed byte thresholds around these actual small
    # canonical bytes; no fake selection type or large allocation is needed.
    small = replace(REGISTRATION, maximum_payload_bytes=len(original))
    smaller = replace(REGISTRATION, maximum_payload_bytes=len(original) - 1)
    larger = replace(BOUNDED_REGISTRATION, maximum_payload_bytes=len(original))
    largest = replace(LARGE_REGISTRATION, maximum_payload_bytes=len(original))
    expanded = replace(EXTENDED_REGISTRATION, maximum_payload_bytes=len(original))
    monkeypatch.setattr(legacy, "REGISTRATION", small)
    monkeypatch.setattr(bounded, "REGISTRATION", larger)
    monkeypatch.setattr(large, "REGISTRATION", largest)
    monkeypatch.setattr(extended, "REGISTRATION", expanded)
    assert owner._selection_decoder_registration(selection) == small
    monkeypatch.setattr(legacy, "REGISTRATION", smaller)
    assert owner._selection_decoder_registration(selection) == larger
    monkeypatch.setattr(bounded, "REGISTRATION", replace(larger, maximum_payload_bytes=len(original) - 1))
    assert owner._selection_decoder_registration(selection) == largest
    monkeypatch.setattr(large, "REGISTRATION", replace(largest, maximum_payload_bytes=len(original) - 1))
    assert owner._selection_decoder_registration(selection) == expanded
    monkeypatch.setattr(extended, "REGISTRATION", replace(expanded, maximum_payload_bytes=len(original) - 1))
    with pytest.raises(ValueError, match="scientific selection exceeds"):
        owner._selection_decoder_registration(selection)
    with pytest.raises(TypeError, match="exact scientific projection"):
        owner._selection_decoder_registration(object())
    assert selection.canonical_bytes() == original


def test_entered_e3_draft_size_requires_the_additive_128_mib_profile():
    # Measured original public metadata: only the draft exceeds bounded64.
    # These advertised sizes contain no synthetic scientific payload.
    draft = _member("draft.json", RecursiveStudyDraft, 76_511_963)
    for registration in (None, REGISTRATION, BOUNDED_REGISTRATION, LARGE_REGISTRATION):
        with pytest.raises(ValueError, match="draft.json"):
            owner._prospective_member_codec(draft, decoder_registration=registration)
    assert owner._prospective_member_codec(draft, decoder_registration=EXTENDED_REGISTRATION) == (
        RecursiveStudyDraft, 128 * MIB)
    for name, kind, size in (("scientific-projection.json", RecursiveScientificSelection, 65_032_437),
            ("template.json", StudyTemplate, 39_261_499)):
        member = _member(name, kind, size)
        assert owner._prospective_member_codec(member, decoder_registration=LARGE_REGISTRATION) == (kind, 64 * MIB)
        assert owner._prospective_member_codec(member, decoder_registration=EXTENDED_REGISTRATION) == (kind, 64 * MIB)


def test_compilation_selects_extended_profile_when_retained_draft_exceeds_large_capacity(selected, monkeypatch):
    spec = selected.prospective_spec
    original = selected.original.compilation.selected_scientific_projection.canonical_bytes()
    draft_size = len(spec.draft.canonical_bytes())
    template_size = len(selected.original.compilation.template.canonical_bytes())
    monkeypatch.setattr(owner, "MAXIMUM_SPEC_BYTES", min(draft_size, template_size) - 1)
    monkeypatch.setattr(owner, "LARGE_RECURSIVE_SELECTION_MAXIMUM_BYTES", draft_size - 1)
    closure = owner.capture_target_closure(selected.root / "checkout", spec.spec_id + ".source-closure").closure
    compilation, authoring, decoder, _ = owner._compile(spec, closure, composition=selected.composition)
    assert decoder == EXTENDED_REGISTRATION
    assert compilation.selected_scientific_projection.canonical_bytes() == original
    assert authoring.base.draft == compilation.candidate_draft


def test_draft_preflight_enforces_the_largest_installed_bound_before_source_capture(selected, monkeypatch):
    design = RecursiveProspectiveDesignInputs.from_spec(selected.prospective_spec)
    maximum = len(design.draft.canonical_bytes())

    class SourceCaptureReached(Exception):
        pass

    def capture(*_args, **_kwargs):
        raise SourceCaptureReached

    monkeypatch.setattr(owner, "_capture_prospective_source", capture)
    monkeypatch.setattr(owner, "DRAFT128_RECURSIVE_DRAFT_MAXIMUM_BYTES", maximum)
    arguments = dict(design_inputs=design, project_root=selected.root / "checkout", artifact_writer=selected.plane)
    with pytest.raises(SourceCaptureReached):
        owner._prepare_prospective_candidate(**arguments)
    monkeypatch.setattr(owner, "DRAFT128_RECURSIVE_DRAFT_MAXIMUM_BYTES", maximum - 1)
    with pytest.raises(ValueError, match="scientific draft exceeds"):
        owner._prepare_prospective_candidate(**arguments)


def test_compilation_selects_capacity_for_actual_draft_template_and_authoring(selected, monkeypatch):
    spec = selected.prospective_spec
    original = selected.original.compilation.selected_scientific_projection.canonical_bytes()
    draft_size = len(spec.draft.canonical_bytes())
    template_size = len(selected.original.compilation.template.canonical_bytes())
    # Scale only the legacy physical carrier ceiling around real small records.
    # The scientific projection still fits its unchanged decoder allocation.
    monkeypatch.setattr(owner, 'MAXIMUM_SPEC_BYTES', min(draft_size, template_size) - 1)
    closure = owner.capture_target_closure(selected.root / 'checkout', spec.spec_id + '.source-closure').closure
    compilation, authoring, decoder, _ = owner._compile(spec, closure, composition=selected.composition)
    assert decoder == LARGE_REGISTRATION
    assert compilation.selected_scientific_projection.canonical_bytes() == original
    assert authoring.base.draft == compilation.candidate_draft
    for filename, record in (('draft.json', spec.draft), ('template.json', compilation.template),
            ('authoring.json', authoring)):
        member = _member(filename, type(record), len(record.canonical_bytes()))
        assert owner._prospective_member_codec(member, decoder_registration=decoder)[1] == (
            512 * MIB if filename == 'authoring.json' else 64 * MIB)
        with pytest.raises(ValueError, match=filename):
            owner._prospective_member_codec(member, decoder_registration=REGISTRATION)


def test_decoder_selection_preserves_fixed_member_ceiling(selected, monkeypatch):
    compilation = selected.original.compilation
    record = compilation.registry
    monkeypatch.setattr(owner, 'MAXIMUM_SPEC_BYTES', len(record.canonical_bytes()) - 1)
    with pytest.raises(ValueError, match='registry.json'):
        owner._selection_decoder_registration(compilation.selected_scientific_projection,
            retained_records=(('registry.json', record),))


def test_decoder_selection_cannot_admit_a_foreign_retained_member(selected):
    with pytest.raises(ValueError, match='outside its closed allowlist'):
        owner._selection_decoder_registration(selected.original.compilation.selected_scientific_projection,
            retained_records=(('draft-copy.json', selected.prospective_spec.draft),))


@pytest.mark.parametrize("filename,kind,maximum", (
    ("draft.json", RecursiveStudyDraft, 32 * MIB),
    ("scientific-projection.json", RecursiveScientificSelection, 32 * MIB),
    ("template.json", StudyTemplate, 32 * MIB),
    ("candidate-report.json", ExecutableStudyCompilationReport, 128 * MIB),
))
def test_only_the_exact_installed_bounded_decoder_selects_finite_larger_members(filename, kind, maximum):
    member = _member(filename, kind, maximum)
    assert owner._prospective_member_codec(member, decoder_registration=BOUNDED_REGISTRATION) == (kind, maximum)
    with pytest.raises(ValueError):
        owner._prospective_member_codec(member)
    with pytest.raises(ValueError):
        owner._prospective_member_codec(replace(member, size_bytes=maximum + 1), decoder_registration=BOUNDED_REGISTRATION)


@pytest.mark.parametrize("filename,kind,maximum", (
    ("candidate.json", ExecutableStudyCandidate, 64 * MIB),
    ("authoring.json", ExecutableStudyDefinition, 16 * MIB),
    ("resources.json", ExecutionResourceEnvelopeSpec, 16 * MIB),
))
def test_new_profile_does_not_enlarge_unrelated_member_contracts(filename, kind, maximum):
    member = _member(filename, kind, maximum)
    assert owner._prospective_member_codec(member, decoder_registration=BOUNDED_REGISTRATION) == (kind, maximum)
    with pytest.raises(ValueError):
        owner._prospective_member_codec(replace(member, size_bytes=maximum + 1), decoder_registration=BOUNDED_REGISTRATION)


@pytest.mark.parametrize("field,value", (
    ("registration_id", "decoder.recursive-scientific-selection-bounded32.forged"),
    ("decoder_key", "recursive.scientific-selection-bounded32.forged"),
    ("decoder_version", "9.0.0"),
    ("payload_schema", "empirical-lawhood/tests/forged-scientific-selection"),
    ("payload_version", "9.0.0"),
    ("config_sha256", "f" * 64),
    ("implementation_sha256", "f" * 64),
    ("maximum_payload_bytes", 16 * MIB),
    ("maximum_payload_bytes", 33 * MIB),
))
@pytest.mark.parametrize("installed", (BOUNDED_REGISTRATION, LARGE_REGISTRATION, EXTENDED_REGISTRATION),
    ids=("bounded32", "bounded64", "draft128"))
def test_forged_decoder_cannot_select_a_larger_physical_bound(field, value, installed):
    registration = replace(installed, **{field: value})
    assert registration != installed
    for filename, kind in (("draft.json", RecursiveStudyDraft), ("scientific-projection.json", RecursiveScientificSelection),
            ("template.json", StudyTemplate)):
        member = _member(filename, kind, 16 * MIB + 1)
        with pytest.raises(ValueError):
            owner._prospective_member_codec(member, decoder_registration=registration)


@pytest.mark.parametrize("field,value", (
    ("object_schema", "empirical-lawhood/tests/foreign-selection"),
    ("object_version", "9.0.0"),
))
@pytest.mark.parametrize("filename,kind", (("scientific-projection.json", RecursiveScientificSelection), ("template.json", StudyTemplate)))
@pytest.mark.parametrize("registration", (BOUNDED_REGISTRATION, LARGE_REGISTRATION, EXTENDED_REGISTRATION),
    ids=("bounded32", "bounded64", "draft128"))
def test_bounded_profile_still_requires_exact_scientific_member_schema_and_revision(field, value, filename, kind, registration):
    member = _member(filename, kind, 16 * MIB + 1)
    changed = replace(member, identity=replace(member.identity, **{field: value}))
    with pytest.raises(ValueError):
        owner._prospective_member_codec(changed, decoder_registration=registration)


def test_v3_envelope_preserves_exact_v1_spec_and_requires_its_own_revision(selected, monkeypatch):
    spec = selected.prospective_spec
    original = spec.canonical_bytes()
    envelope = envelopes.RecursiveProspectiveAuthoringEnvelopeV3.from_spec(spec)
    assert envelope.SCHEMA == envelopes.RecursiveProspectiveAuthoringEnvelope.SCHEMA
    assert envelope.VERSION == "3.0.0"
    assert envelope.reconstruct().canonical_bytes() == original
    assert envelope.semantic_spec == ObjectIdentity.from_record(spec.spec_id, spec)
    assert envelopes.MAXIMUM_LARGE_OPERATIONAL_ENVELOPE_BYTES == 64 * MIB
    assert decode_canonical_bytes(envelope.canonical_bytes(), type(envelope), maximum_bytes=64 * MIB).reconstruct().canonical_bytes() == original
    for mutation in ("hash", "id", "spec"):
        with pytest.raises(ValueError):
            replace(envelope, **{
                "hash": {"semantic_spec": replace(envelope.semantic_spec, object_fingerprint="f" * 64)},
                "id": {"envelope_id": spec.spec_id + ".operational-envelope"},
                "spec": {"original_spec": replace(spec, spec_id=spec.spec_id + ".changed")},
            }[mutation])
    carrier = _member("recursive-prospective.json", type(envelope), 64 * MIB)
    assert owner._prospective_member_codec(carrier, decoder_registration=BOUNDED_REGISTRATION) == (type(envelope), 64 * MIB)
    with pytest.raises(ValueError):
        owner._prospective_member_codec(carrier)
    with pytest.raises(ValueError):
        owner._prospective_member_codec(replace(carrier, size_bytes=64 * MIB + 1), decoder_registration=BOUNDED_REGISTRATION)
    monkeypatch.setattr(envelopes, "MAXIMUM_LARGE_OPERATIONAL_ENVELOPE_BYTES", len(envelope.canonical_bytes()) - 1)
    with pytest.raises(ValueError, match="64 MiB allocation"):
        envelopes.RecursiveProspectiveAuthoringEnvelopeV3.from_spec(spec)
    assert spec.canonical_bytes() == original


def test_v4_envelope_preserves_exact_spec_and_requires_exact_large_profile(selected, monkeypatch):
    spec = selected.prospective_spec
    original = spec.canonical_bytes()
    envelope = envelopes.RecursiveProspectiveAuthoringEnvelopeV4.from_spec(spec)
    assert envelope.SCHEMA == envelopes.RecursiveProspectiveAuthoringEnvelope.SCHEMA
    assert envelope.VERSION == "4.0.0"
    assert envelopes.MAXIMUM_LARGEST_OPERATIONAL_ENVELOPE_BYTES == 256 * MIB
    assert envelope.semantic_spec == ObjectIdentity.from_record(spec.spec_id, spec)
    assert envelope.reconstruct().canonical_bytes() == original
    assert decode_canonical_bytes(envelope.canonical_bytes(), type(envelope), maximum_bytes=256 * MIB) == envelope
    for mutation in (dict(semantic_spec=replace(envelope.semantic_spec, object_fingerprint="f" * 64)),
            dict(envelope_id=spec.spec_id + ".operational-envelope-v3"),
            dict(original_spec=replace(spec, spec_id=spec.spec_id + ".changed"))):
        with pytest.raises(ValueError):
            replace(envelope, **mutation)
    carrier = _member("recursive-prospective.json", type(envelope), 256 * MIB)
    for registration in (LARGE_REGISTRATION, EXTENDED_REGISTRATION):
        assert owner._prospective_member_codec(carrier, decoder_registration=registration) == (type(envelope), 256 * MIB)
        with pytest.raises(ValueError):
            owner._prospective_member_codec(replace(carrier, size_bytes=256 * MIB + 1), decoder_registration=registration)
    for registration in (None, REGISTRATION, BOUNDED_REGISTRATION):
        with pytest.raises(ValueError):
            owner._prospective_member_codec(carrier, decoder_registration=registration)
    for kind, maximum in ((envelopes.RecursiveProspectiveAuthoringEnvelope, 32 * MIB),
            (envelopes.RecursiveProspectiveAuthoringEnvelopeV3, 64 * MIB)):
        member = _member("recursive-prospective.json", kind, maximum)
        for registration in (LARGE_REGISTRATION, EXTENDED_REGISTRATION):
            assert owner._prospective_member_codec(member, decoder_registration=registration) == (kind, maximum)
            with pytest.raises(ValueError):
                owner._prospective_member_codec(replace(member, size_bytes=maximum + 1), decoder_registration=registration)
    monkeypatch.setattr(envelopes, "MAXIMUM_LARGEST_OPERATIONAL_ENVELOPE_BYTES", len(envelope.canonical_bytes()) - 1)
    with pytest.raises(ValueError):
        envelopes.RecursiveProspectiveAuthoringEnvelopeV4.from_spec(spec)
    assert spec.canonical_bytes() == original


def test_api_chooses_smallest_exact_carrier_and_requires_new_decoder_for_v3(selected, monkeypatch):
    spec = selected.prospective_spec
    original = spec.canonical_bytes()
    for registration in (REGISTRATION, BOUNDED_REGISTRATION, LARGE_REGISTRATION, EXTENDED_REGISTRATION):
        assert owner._stored_prospective_spec(spec, decoder_registration=registration) is spec
    # Scale operational carrier thresholds around an honest tiny specification;
    # its scientific records, identities and bytes remain unchanged.
    monkeypatch.setattr(owner, "MAXIMUM_SPEC_BYTES", len(original) - 1)
    for registration in (REGISTRATION, BOUNDED_REGISTRATION, LARGE_REGISTRATION, EXTENDED_REGISTRATION):
        v2 = owner._stored_prospective_spec(spec, decoder_registration=registration)
        assert type(v2) is envelopes.RecursiveProspectiveAuthoringEnvelope
        assert v2.reconstruct().canonical_bytes() == original
    monkeypatch.setattr(envelopes, "MAXIMUM_OPERATIONAL_ENVELOPE_BYTES", len(original) - 1)
    with pytest.raises(ValueError):
        owner._stored_prospective_spec(spec, decoder_registration=REGISTRATION)
    for registration in (BOUNDED_REGISTRATION, LARGE_REGISTRATION, EXTENDED_REGISTRATION):
        v3 = owner._stored_prospective_spec(spec, decoder_registration=registration)
        assert type(v3) is envelopes.RecursiveProspectiveAuthoringEnvelopeV3
        assert v3.reconstruct().canonical_bytes() == original
    monkeypatch.setattr(envelopes, "MAXIMUM_LARGE_OPERATIONAL_ENVELOPE_BYTES", len(original) - 1)
    with pytest.raises(ValueError):
        owner._stored_prospective_spec(spec, decoder_registration=BOUNDED_REGISTRATION)
    for registration in (LARGE_REGISTRATION, EXTENDED_REGISTRATION):
        v4 = owner._stored_prospective_spec(spec, decoder_registration=registration)
        assert type(v4) is envelopes.RecursiveProspectiveAuthoringEnvelopeV4
        assert v4.reconstruct().canonical_bytes() == original
    for installed in (BOUNDED_REGISTRATION, LARGE_REGISTRATION, EXTENDED_REGISTRATION):
        forged = replace(installed, implementation_sha256="f" * 64)
        with pytest.raises(ValueError):
            owner._stored_prospective_spec(spec, decoder_registration=forged)
    assert spec.canonical_bytes() == original


@pytest.mark.parametrize("kind", (envelopes.RecursiveProspectiveAuthoringEnvelopeV3, envelopes.RecursiveProspectiveAuthoringEnvelopeV4))
def test_standalone_large_carrier_requires_explicit_version_and_never_sniffs_upgrade(selected, tmp_path, monkeypatch, kind):
    original = selected.prospective_spec.canonical_bytes()
    envelope = kind.from_spec(selected.prospective_spec)
    path = tmp_path / "explicit-large-envelope.json"
    path.write_bytes(envelope.canonical_bytes())
    with pytest.raises(ValueError):
        owner.load_recursive_prospective_envelope(path)
    assert owner.load_recursive_prospective_envelope(path, version=kind.VERSION).canonical_bytes() == original
    monkeypatch.setattr(owner, "read_bounded_bytes", lambda *_args, **_kwargs: pytest.fail("uninstalled revision reached I/O"))
    with pytest.raises(ValueError, match="revision is not installed"):
        owner.load_recursive_prospective_envelope(path, version="9.0.0")


def _publish_decoder_bootstrap_case(selected, tmp_path, *, mutate_decoder):
    """Publish a real closed packet whose decoder selector fails authentication."""
    from tests.test_recursive_public_service import _plane

    plane = _plane(tmp_path / "bounded-selector-custody")
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


@pytest.mark.parametrize("mutate_decoder", (False, True), ids=("packet-pin-mismatch", "uninstalled-decoder"))
def test_loader_authenticates_decoder_before_reading_scientific_members(selected, tmp_path, monkeypatch, mutate_decoder):
    directory, plane = _publish_decoder_bootstrap_case(selected, tmp_path, mutate_decoder=mutate_decoder)
    reads = []
    read = owner.read_bounded_bytes

    def observed(path, **kwargs):
        if not Path(path).name.endswith(".manifest.json"):
            reads.append(Path(path).name)
        return read(path, **kwargs)

    monkeypatch.setattr(owner, "read_bounded_bytes", observed)
    with pytest.raises(ValueError):
        owner._load_recursive_prospective_members(directory=directory, root=selected.root / "checkout",
            storage_profile=object(), artifact_writer=plane)
    assert reads == ["authored-wave.json", "decoder.json"]
