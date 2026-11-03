# SPDX-License-Identifier: MPL-2.0
"""Exposed software custody tests; these records confer no scientific authority."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_inquiry as service
from empirical_lawhood.kernel.recursive_inquiry import InquiryOutcomeChoice, identity
from empirical_lawhood.planning.recursive_inquiry import InquiryAction
from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigins
from empirical_lawhood.runtime.recursive_inquiry import InquiryStateSources, InquiryWaveSource
from tests.test_recursive_inquiry import episode as episode, obj
from tests.test_recursive_public_service import _plane

ROOT = Path(__file__).resolve().parents[1]


def test_stop_persists_and_replays_without_export_or_execution(tmp_path, monkeypatch, episode):
    # Concurrent engineering edits are not this software fixture's input.
    # Actual acceptance uses the unpatched producing-source owner after edits settle.
    source = service.implementation_binding(ROOT)
    monkeypatch.setattr(service, "implementation_binding", lambda root: source)
    plane = _plane(tmp_path / "selected")
    specification = replace(episode["specification"], outcome_choices=(InquiryOutcomeChoice("initial", ("stop",)),))
    sources = InquiryStateSources(())
    state = service.project_inquiry_state(specification=specification, state_id="state",
        information_cutoff=episode["state"].information_cutoff, sources=sources, artifact_writer=plane)
    sid, tid = identity(specification, "spec"), identity(state, "state")
    stop = next(a for a in episode["menu"].alternatives if a.action is InquiryAction.STOP)
    menu = replace(episode["menu"], specification=sid, state=tid,
                   alternatives=(replace(stop, specification=sid, state=tid, eligible_outcomes=("initial",)),))
    policy = replace(episode["policy"], specification=sid)
    directory = tmp_path / "selected/decision"
    packet, records = service.commit_inquiry_decision(specification=specification, state=state, sources=sources,
        menu=menu, policy=policy, campaign=episode["campaign"], right=episode["right"], actor_id="actor",
        project_root=ROOT, artifact_writer=plane, output_dir=directory)
    assert records["decision.json"].selected_alternative_id == "stop"
    assert "intent.json" not in records and state.cost_events == ()
    assert service.read_inquiry_decision(directory=directory, artifact_writer=plane) == (packet, records)
    with pytest.raises(ValueError, match="HOLD/STOP"):
        service.author_inquiry_successor(decision_directory=directory, origins=RecursiveInputOrigins(()),
            initial_draft=SimpleNamespace(), project_root=ROOT, artifact_writer=plane,
            output_dir=tmp_path / "selected/forbidden")
    assert not (tmp_path / "selected/forbidden").exists()
    (directory / "state.json").write_bytes(b"{}")
    with pytest.raises((ValueError, RuntimeError, OSError)):
        service.read_inquiry_decision(directory=directory, artifact_writer=plane)


def test_zero_product_failure_uses_selected_domain_projector(tmp_path, monkeypatch, episode):
    from empirical_lawhood.api import recursive_operations
    plane = _plane(tmp_path / "selected")
    calls = []
    def projector(draft, specification, products):
        calls.append(products["operational_census"])
        assert products["records"] == {}
        return "unresolved"
    factory = SimpleNamespace(registration=SimpleNamespace(selection=SimpleNamespace(selection_id="selected")),
                              inquiry_outcome_projector=projector)
    draft = SimpleNamespace(selected_operation_ids=("task",),
        operations=(SimpleNamespace(node_id="task", config_identity=episode["specification"].distinguishing_assessment,
                                    selection=SimpleNamespace(selection_id="selected")),))
    products = {"records": {}, "operational_census": ({"operational_status": "FAILED"},)}
    monkeypatch.setattr(recursive_operations, "operation_factories", lambda: (factory,))
    monkeypatch.setattr(service, "read_recursive_wave", lambda **kwargs: ({}, products, draft, None))
    sources = InquiryStateSources((InquiryWaveSource("wave", obj("packet"), True),))
    assert service._outcome(episode["specification"], sources, plane) == "unresolved"
    assert calls == [products["operational_census"]]


def test_runtime_intent_join_rechecks_origins_configuration_and_capability():
    from empirical_lawhood.planning.study_authoring import CapabilitySelection

    origins = RecursiveInputOrigins(())
    selection = CapabilitySelection("rubisco-inquiry.use", "1.0.0", "a" * 64)
    operation = SimpleNamespace(node_id="task", config_identity=obj("config"),
                                selection=selection)
    class Draft:
        draft_id = "draft"
        selected_operation_ids = ("task",)
        operations = (operation,)
        SCHEMA = "empirical-lawhood/testing/draft"
        VERSION = "1.0.0"
        def fingerprint(self):
            return "a" * 64
    draft = Draft()
    intent = SimpleNamespace(draft=identity(draft, "draft"), configuration=obj("config"),
        capability_id=selection.selection_id, input_origins=identity(origins, "inquiry-input-origins"))
    service._validate_intent_draft(intent, draft, origins)
    for field, value in (("configuration", obj("foreign")), ("capability_id", "foreign"),
                         ("capability_id", "rubisco-inquiry.use@2.0.0"),
                         ("input_origins", obj("foreign"))):
        substituted = SimpleNamespace(**dict(vars(intent), **{field: value}))
        with pytest.raises(ValueError, match="intent substitutes"):
            service._validate_intent_draft(substituted, draft, origins)


def test_actual_versioned_capability_selection_survives_decision_and_intent_join(episode):
    from empirical_lawhood.planning.recursive_inquiry import choose_inquiry, make_successor_intent
    from empirical_lawhood.planning.study_authoring import CapabilitySelection
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.recursive_inquiry import InquirySuccessorIntent

    selection = CapabilitySelection("rubisco-inquiry.use", "1.0.0", "a" * 64)
    menu = replace(episode["menu"], alternatives=tuple(
        replace(row, capability_id=selection.selection_id) if row.action is InquiryAction.ACT else row
        for row in episode["menu"].alternatives))
    decision = choose_inquiry(**dict(episode, menu=menu))
    intent = make_successor_intent(intent_id="intent.versioned", decision=decision,
        specification=episode["specification"], menu=menu)
    assert intent.capability_id == "rubisco-inquiry.use@1.0.0"
    assert decode_canonical_bytes(intent.canonical_bytes(), InquirySuccessorIntent,
                                  maximum_bytes=None) == intent
    selected = next(row for row in menu.alternatives if row.alternative_id == decision.selected_alternative_id)
    for malformed in ("rubisco-inquiry.use@bad", "rubisco-inquiry.use@1.0.0@2.0.0"):
        with pytest.raises(ValueError):
            replace(selected, capability_id=malformed)


@pytest.fixture
def multi_operation_intent(episode):
    """Real canonical RC graph/intent; no authoring or scientific execution."""
    from empirical_lawhood.kernel.recursive_inquiry import InquirySuccessorIntent
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind
    from tests.test_recursive_public_service import _draft

    draft = _draft()
    origins = RecursiveInputOrigins(tuple(RecursiveInputOrigin(row.input_id,
        RecursiveInputOriginKind.SOURCE, row.expected_content_sha256, row.scientific_role)
        for row in draft.external_inputs))
    operation = draft.operations[-1]  # Designation need not be the first node.
    intent = InquirySuccessorIntent("intent.multi", obj("decision"), obj("spec"), obj("state"),
        obj("menu"), obj("policy"), "act", identity(draft, draft.draft_id), operation.config_identity,
        identity(origins, "inquiry-input-origins"), episode["specification"].endpoint,
        operation.selection.selection_id)
    return draft, origins, intent


def test_multi_operation_intent_preserves_exact_canonical_record(multi_operation_intent):
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.recursive_inquiry import InquirySuccessorIntent

    draft, origins, intent = multi_operation_intent
    assert len(draft.selected_operation_ids) > 1
    before = intent.canonical_bytes()
    retained = decode_canonical_bytes(before, InquirySuccessorIntent, maximum_bytes=None)
    service._validate_intent_draft(retained, draft, origins)
    assert retained.canonical_bytes() == before
    assert retained.configuration == draft.operations[-1].config_identity


@pytest.mark.parametrize("part", ("deselected", "ambiguous", "cross-pair", "nondesignated", "origins"))
def test_multi_operation_intent_refuses_selection_and_whole_graph_substitution(multi_operation_intent, part):
    draft, origins, intent = multi_operation_intent
    designated, other = draft.operations[-1], draft.operations[0]
    if part == "deselected":
        draft = replace(draft, selected_operation_ids=tuple(node for node in draft.selected_operation_ids
                        if node != designated.node_id))
        # Even a newly committed whole graph cannot designate a deselected node.
        intent = replace(intent, draft=identity(draft, draft.draft_id))
    elif part == "ambiguous":
        duplicate = replace(other, config_id=designated.config_id,
            config_payload=designated.config_payload, selection=designated.selection)
        draft = replace(draft, operations=(duplicate, *draft.operations[1:]))
        intent = replace(intent, draft=identity(draft, draft.draft_id))
    elif part == "cross-pair":
        assert other.selection.selection_id != designated.selection.selection_id
        intent = replace(intent, capability_id=other.selection.selection_id)
    elif part == "nondesignated":
        changed = replace(other, config_id=other.config_id + ".substituted")
        draft = replace(draft, operations=(changed, *draft.operations[1:]))
        assert draft.operations[-1].config_identity == intent.configuration
    else:
        from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind
        origins = replace(origins, inputs=(RecursiveInputOrigin("external.substituted",
            RecursiveInputOriginKind.SOURCE, "b" * 64, "SOURCE"),))
    with pytest.raises(ValueError, match="intent substitutes"):
        service._validate_intent_draft(intent, draft, origins)


def test_unselected_matching_operation_does_not_make_selected_designation_ambiguous(multi_operation_intent):
    draft, origins, intent = multi_operation_intent
    designated, other = draft.operations[-1], draft.operations[0]
    duplicate = replace(other, config_id=designated.config_id,
        config_payload=designated.config_payload, selection=designated.selection)
    draft = replace(draft, operations=(duplicate, *draft.operations[1:]),
        selected_operation_ids=tuple(node for node in draft.selected_operation_ids if node != other.node_id))
    intent = replace(intent, draft=identity(draft, draft.draft_id))
    service._validate_intent_draft(intent, draft, origins)
