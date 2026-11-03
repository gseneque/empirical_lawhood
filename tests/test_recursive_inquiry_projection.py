# SPDX-License-Identifier: MPL-2.0
"""Projection regressions use authenticated-owner doubles; no worker/native contact."""
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api import recursive_inquiry as service
from empirical_lawhood.kernel.recursive_inquiry import AcquisitionEvent, identity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.recursive_inquiry import InquiryStateSources, InquiryWaveSource
from empirical_lawhood.runtime.execution import TaskBlockReason
from tests.test_recursive_inquiry import cost, episode as episode, obj
from tests.test_recursive_public_service import _plane
from tests.runtime_platform.test_native_effect_facts import selected as selected


@dataclass(frozen=True, slots=True)
class Packet(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/projection-packet"
    packet_id: str
    draft: object
    members: tuple = ()


@pytest.fixture
def custody(tmp_path, monkeypatch, episode):
    plane = _plane(tmp_path / "selected")
    root = Path(plane.root.contract.canonical_path)
    packets, decisions, measurements = {}, {}, {}
    calls = []

    def add_wave(name, *, alias=None):
        packet = packets[alias][0] if alias else Packet("packet." + name, obj("draft." + name))
        run = alias or name
        draft = SimpleNamespace(development_study=SimpleNamespace(assigned_unit_ids=()),
            links=(), selected_operation_ids=(), external_inputs=(), contribution_parents=(), operations=())
        packets[name] = (packet, draft, run)
        return InquiryWaveSource(name, identity(packet, packet.packet_id), True)

    def load(directory, **kwargs):
        packet, draft, _ = packets[Path(directory).relative_to(root).as_posix()]
        return packet, draft, None, {}

    def read_wave(directory, **kwargs):
        name = Path(directory).relative_to(root).as_posix()
        calls.append(name)
        _, draft, run = packets[name]
        return ({"run_id": "run." + run}, {"operational_census": ()}, draft, None)

    def read_decision(directory, **kwargs):
        return None, decisions[Path(directory).relative_to(root).as_posix()]

    from empirical_lawhood.api import recursive_inquiry_evidence
    monkeypatch.setattr(recursive_inquiry_evidence, "project_wave_evidence_bindings", lambda **kwargs: {})
    monkeypatch.setattr(service, "_validate_wave_endpoint", lambda *args: None)
    monkeypatch.setattr(service, "load_authored_wave", load)
    monkeypatch.setattr(service, "read_recursive_wave", read_wave)
    monkeypatch.setattr(service, "read_inquiry_decision", read_decision)
    monkeypatch.setattr(service, "_read", lambda writer, relative, codec: measurements[relative])

    def project(sources):
        return service.project_inquiry_state(specification=episode["specification"], state_id="projected",
            information_cutoff=episode["state"].information_cutoff, sources=sources, artifact_writer=plane)

    def retain(name, state, sources, successor=None):
        # The authentic read owner is doubled here; immutable state/decision content
        # and exact authored packet joins still pass through projection unchanged.
        decision = Packet("decision." + name, obj("decision-draft." + name))
        decision = SimpleNamespace(decision_id="decision." + name, SCHEMA=decision.SCHEMA,
                                  VERSION=decision.VERSION, fingerprint=decision.fingerprint)
        decisions[name] = {"state.json": state, "decision.json": decision, "sources.json": sources}
        if successor:
            decisions[name]["intent.json"] = SimpleNamespace(draft=packets[successor][0].draft)

    return SimpleNamespace(add_wave=add_wave, project=project, retain=retain,
        decisions=decisions, measurements=measurements, packets=packets, calls=calls, plane=plane)


def test_singleton_successor_sources_accumulate_count_and_depth(custody):
    first, second, third = [custody.add_wave(name) for name in ("first", "second", "third")]
    sources1 = InquiryStateSources((first,))
    state1 = custody.project(sources1)
    custody.retain("decision-first", state1, sources1, "second")
    sources2 = InquiryStateSources((second,), previous_decision_paths=("decision-first",))
    state2 = custody.project(sources2)
    custody.retain("decision-second", state2, sources2, "third")
    sources3 = InquiryStateSources((third,), previous_decision_paths=("decision-second",))
    state3 = custody.project(sources3)
    assert [(s.wave_count, s.depth_count) for s in (state1, state2, state3)] == [(1, 1), (2, 2), (3, 3)]
    custody.retain("decision-third", state3, sources3)
    replay = custody.project(InquiryStateSources((third,), previous_decision_paths=("decision-third",)))
    assert (replay.wave_count, replay.depth_count) == (3, 3)


def test_relocated_replay_does_not_doublecount(custody):
    first = custody.add_wave("first")
    moved = custody.add_wave("relocated", alias="first")
    assert custody.project(InquiryStateSources((first, moved))).wave_count == 1


def test_history_cycle_refuses_before_wave_reads(custody):
    source = custody.add_wave("first")
    base = custody.project(InquiryStateSources((source,)))
    custody.retain("cycle", base, InquiryStateSources((source,), previous_decision_paths=("cycle",)))
    custody.calls.clear()
    with pytest.raises(ValueError, match="cycles"):
        custody.project(InquiryStateSources((), previous_decision_paths=("cycle",)))
    assert custody.calls == []


def test_source_and_predecessor_census_has_no_twenty_four_entry_ceiling(custody):
    waves = tuple(custody.add_wave(f"wave-{index:03d}") for index in range(30))
    state = custody.project(InquiryStateSources(waves))
    assert state.wave_count == 30
    previous = ()
    for index, wave in enumerate(waves):
        sources = InquiryStateSources((wave,), previous_decision_paths=previous)
        name = f"decision-{index:03d}"
        custody.retain(name, state, sources)
        previous = (name,)
    cumulative = custody.project(InquiryStateSources((), previous_decision_paths=previous))
    assert cumulative.wave_count == 30
    assert len(cumulative.previous_decisions) == 30
    paths = tuple(f"path-{index:03d}" for index in range(30))
    sources = InquiryStateSources((), measured_event_paths=paths, previous_decision_paths=paths)
    assert len(sources.measured_event_paths) == 30


@pytest.mark.parametrize("changed", [cost("0", "20", "30"), cost(None, "20", "30"), cost("10", "0", "30")])
def test_prior_known_expense_cannot_be_replaced(custody, episode, changed):
    from empirical_lawhood.kernel.recursive_inquiry import InquiryAttempt, InquiryAttemptStatus
    witness = obj("actual-recovery-event")
    attempt = InquiryAttempt("attempt", obj("operation"), InquiryAttemptStatus.FAILED, witness, (), "failed")
    original = AcquisitionEvent("event", "attempt", witness, cost("10", "20", "30"))
    state = replace(episode["state"], stock=(), operational_census=(attempt,), cost_events=(original,))
    custody.retain("prior", state, InquiryStateSources(()))
    custody.measurements["measured"] = replace(original, cost=changed)
    with pytest.raises(ValueError, match="known expense"):
        custody.project(InquiryStateSources((), ("measured",), ("prior",)))
    assert custody.decisions["prior"]["state.json"].cost_events == (original,)


def test_explicit_unknown_refinement_retains_prior_unknown_bytes(custody, episode):
    from empirical_lawhood.kernel.recursive_inquiry import InquiryAttempt, InquiryAttemptStatus
    witness = obj("actual-recovery-event")
    attempt = InquiryAttempt("attempt", obj("operation"), InquiryAttemptStatus.FAILED, witness, (), "failed")
    original = AcquisitionEvent("event", "attempt", witness, cost(None, None, None))
    state = replace(episode["state"], stock=(), operational_census=(attempt,), cost_events=(original,))
    original_bytes = state.canonical_bytes()
    custody.retain("prior", state, InquiryStateSources(()))
    custody.measurements["measured"] = replace(original, cost=cost("10", "20", "30"))
    projected = custody.project(InquiryStateSources((), ("measured",), ("prior",)))
    assert projected.cost_events[0].cost == cost("10", "20", "30")
    assert state.canonical_bytes() == original_bytes
    assert state.cost_events[0].cost.cpu_seconds is None


def test_carried_refinement_requires_immutable_explicit_measurement_provenance(custody, episode):
    from empirical_lawhood.kernel.recursive_inquiry import InquiryAttempt, InquiryAttemptStatus
    witness = obj("actual-recovery-event")
    attempt = InquiryAttempt("attempt", obj("operation"), InquiryAttemptStatus.FAILED, witness, (), "failed")
    original = AcquisitionEvent("event", "attempt", witness, cost(None, None, None))
    state = replace(episode["state"], stock=(), operational_census=(attempt,), cost_events=(original,))
    custody.retain("prior", state, InquiryStateSources(()))
    newer = replace(state, cost_events=(replace(original, cost=cost("1", "2", "3")),))
    custody.retain("newer", newer, InquiryStateSources((), previous_decision_paths=("prior",)))
    with pytest.raises(ValueError, match="provenance"):
        custody.project(InquiryStateSources((), previous_decision_paths=("newer",)))


@pytest.mark.parametrize("operational_status,reason,disposition,expected", [
    ("FAILED", "failure", "FAILED", "FAILED"),
    ("BLOCKED", "missing", "BLOCKED", "BLOCKED"),
    ("FAILED", TaskBlockReason.UNKNOWN_COMPLETION, "FAILED", "UNCERTAIN_CONTACT"),
    ("FAILED", "UNKNOWN_COMPLETION_AFTER_CONTACT", "FAILED", "UNCERTAIN_CONTACT"),
    ("FAILED", "not attempted", "NOT_ATTEMPTED", "NONATTEMPT"),
    ("SUCCEEDED", "", None, "COMPLETED"),
])
def test_projection_retains_nonattempt_and_uncertain_contacts(operational_status, reason, disposition, expected):
    status = service._inquiry_attempt_status(
        {"operational_status": operational_status, "reason_code": reason},
        SimpleNamespace(disposition=disposition))
    assert status.value == expected


@pytest.mark.parametrize("unknown_sibling", (False, True))
def test_current_native_facts_do_not_rewrite_recorded_inquiry_uncertainty(selected, unknown_sibling):
    from empirical_lawhood.infrastructure.native_parent_finalization import inspect_native_parent_return
    from empirical_lawhood.runtime.native_subwork import invoke_native_subwork
    from tests.runtime_platform.test_native_effect_facts import _snapshot

    store, definitions, _bundle, _context, contract = selected
    entry = store.begin(definitions[0]); store.contact(entry)
    invoke_native_subwork(store, entry, lambda: b"disclosed raw return without products")
    if unknown_sibling:
        unknown = store.begin(definitions[1]); store.contact(unknown)
    parent = contract.native_work.expected_parent
    census = dict(task_id=parent.task_id, attempt_id=parent.attempt_id,
        operational_status="BLOCKED", reason_code=TaskBlockReason.UNKNOWN_COMPLETION.value)
    operational = SimpleNamespace(disposition="BLOCKED")
    before = _snapshot(store)
    observed = inspect_native_parent_return(store=store, work=contract.native_work)
    assert service._inquiry_attempt_status(census, operational).value == "UNCERTAIN_CONTACT"
    assert service._inquiry_current_attempt_status(census, operational,
        {parent.attempt_id: observed}).value == ("UNCERTAIN_CONTACT" if unknown_sibling else "BLOCKED")
    # Missing original work never turns the recorded obstruction into certainty.
    assert service._inquiry_current_attempt_status(census, operational, {}).value == "UNCERTAIN_CONTACT"
    assert service._inquiry_attempt_status(census, operational).value == "UNCERTAIN_CONTACT"
    assert observed.pending_publication_definition_ids == (definitions[0].identity,)
    assert _snapshot(store) == before
    with pytest.raises(ValueError, match="substitute.*original attempt"):
        service._inquiry_current_attempt_status(dict(census, task_id="foreign.task"), operational,
            {parent.attempt_id: observed})


def _terminal_nonattempt_wave(custody, episode, monkeypatch, *, block_count=2, failed=False):
    """Project the real custody reader's census, with no fabricated block events."""
    from empirical_lawhood.infrastructure.recursive_custody import _operational_census
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.execution import OperationalFailureClass
    from empirical_lawhood.runtime.recovery import (
        DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent,
        OperationalFailureDiagnostic, RecoveryTerminalAttempt, RecoveryTerminalDisposition,
        TaskRecoveryDisposition, TaskRecoveryEvent,
    )

    source = custody.add_wave("first")
    _, draft, _ = custody.packets["first"]
    draft.selected_operation_ids = ("task",)
    draft.operations = (SimpleNamespace(node_id="task",
        config_identity=episode["specification"].distinguishing_assessment),)
    index_id = ObjectIdentity("index.first", DevelopmentRunRecoveryIndex.SCHEMA, "1.0.0", "a" * 64)
    rows = tuple(RecoveryTerminalAttempt(f"run.first.task.block-{ordinal:03d}", "task", ordinal,
        RecoveryTerminalDisposition.BLOCKED, "resource-lock-unavailable", None, None)
        for ordinal in range(1, block_count + 1))
    events, candidates = {}, ()
    if failed:
        candidate = SimpleNamespace(attempt_id="attempt.first", ordinal=1, event_relative_path="event.first")
        candidates = (candidate,)
        diagnostic = OperationalFailureDiagnostic.create(next(value for value in OperationalFailureClass if value.retryable),
            sanitized_exception_type="RuntimeError", sanitized_message="temporary")
        events["event.first"] = TaskRecoveryEvent("recovery.first", index_id, "run.first", "task",
            candidate.attempt_id, 1, TaskRecoveryDisposition.FAILED, None, None, None, None, (), ("failure.temporary",), diagnostic)
        rows += (RecoveryTerminalAttempt(candidate.attempt_id, "task", block_count + 1,
            RecoveryTerminalDisposition.FAILED, "failure.temporary", None, None),)
    terminal = DevelopmentRunRecoveryTerminalEvent("terminal.first", index_id, "run.first",
        "FAILED" if failed else "BLOCKED", rows, (), ("task",) if failed else (), () if failed else ("task",))
    plan = SimpleNamespace(tasks=(SimpleNamespace(task_id="task", outputs=()),))
    index = SimpleNamespace(run_id="run.first", tasks=(SimpleNamespace(task_id="task", attempts=candidates,
        nonattempt_event_relative_path="nonattempt"),))
    census, recovered, receipts = _operational_census(
        recovery=SimpleNamespace(read_event=lambda _, path: events.get(path)),
        store=SimpleNamespace(plane=custody.plane, read=lambda *args: None), plan=plan, index=index, terminal=terminal)
    products = dict(operational_census=census, attempt_receipts=receipts, recovery_events=recovered,
        terminal=terminal, records={}, connection_assessments=())
    monkeypatch.setattr(service, "read_recursive_wave", lambda **kwargs: ({"run_id": terminal.run_id}, products, draft, plan))
    return source, products, draft


def test_terminal_nonattempts_retain_original_witness_unknown_cost_and_replay_counts(custody, episode, monkeypatch):
    from empirical_lawhood.kernel.recursive_inquiry import InquiryAttemptStatus, summarize_cost

    source, products, _ = _terminal_nonattempt_wave(custody, episode, monkeypatch, failed=True)
    terminal = products["terminal"]
    original_bytes = terminal.canonical_bytes()
    sources = InquiryStateSources((source,))
    state = custody.project(sources)
    attempts = {row.attempt_id: row for row in state.operational_census}
    blocks = tuple(row for row in attempts.values() if row.status is InquiryAttemptStatus.NONATTEMPT)
    assert len(attempts) == 3 and len(blocks) == 2
    assert all(row.receipt == identity(terminal, terminal.terminal_event_id) and not row.products for row in blocks)
    assert attempts["attempt.first"].status is InquiryAttemptStatus.FAILED
    assert attempts["attempt.first"].receipt == identity(products["recovery_events"]["attempt.first"], "recovery.first")
    assert len(state.cost_events) == 3 and summarize_cost(state.cost_events) == cost(None, None, None)
    assert (state.wave_count, state.depth_count) == (1, 1)
    custody.retain("prior", state, sources)
    replay = custody.project(InquiryStateSources((source,), previous_decision_paths=("prior",)))
    assert replay.operational_census == state.operational_census and replay.cost_events == state.cost_events
    assert (replay.wave_count, replay.depth_count) == (1, 1)
    assert tuple(products["recovery_events"]) == ("attempt.first",)
    assert terminal.canonical_bytes() == original_bytes


@pytest.mark.parametrize("failed,expected", [(False, "missing"), (True, "operational_failure")])
def test_terminal_nonattempts_join_robust_outcome_without_masking_entered_failure(custody, episode, monkeypatch, failed, expected):
    from tests.test_recursive_inquiry_policy import policy_case

    source, _, draft = _terminal_nonattempt_wave(custody, episode, monkeypatch, failed=failed)
    specification = policy_case("matrix").specification
    draft.operations[0].config_identity = specification.distinguishing_assessment
    assert service._outcome(specification, InquiryStateSources((source,)), custody.plane) == expected


def test_terminal_nonattempt_cost_measurement_joins_original_terminal(custody, episode, monkeypatch):
    source, products, _ = _terminal_nonattempt_wave(custody, episode, monkeypatch, block_count=1)
    plane = custody.plane
    root = Path(plane.root.contract.canonical_path)
    measured = cost("1", "2", "3")
    event = service.retain_measured_attempt_cost(authoring_directory=root / "first", artifact_writer=plane,
        cpu_seconds=measured.cpu_seconds, wall_seconds=measured.wall_seconds,
        retained_bytes=measured.retained_bytes, output_dir=root / "measurement")
    assert event.receipt == identity(products["terminal"], "terminal.first")
    custody.measurements["measurement/measured-attempt-cost.json"] = event
    state = custody.project(InquiryStateSources((source,), measured_event_paths=("measurement/measured-attempt-cost.json",)))
    assert state.cost_events == (event,) and state.cost_events[0].cost == cost("1", "2", "3")
    assert products["recovery_events"] == {}


@pytest.mark.parametrize("mutation", ["missing-terminal", "missing-marker", "wrong-row", "invented-event", "durable-reason"])
def test_missing_recovery_event_cannot_be_relabelled_as_terminal_nonattempt(custody, episode, monkeypatch, mutation):
    source, products, _ = _terminal_nonattempt_wave(custody, episode, monkeypatch, block_count=1)
    row = products["operational_census"][0]
    if mutation == "missing-terminal":
        products["terminal"] = None
    elif mutation == "missing-marker":
        row["recovery_event_status"] = "MISSING"
    elif mutation == "wrong-row":
        row["ordinal"] = 2
    elif mutation == "invented-event":
        row["recovery_event"] = {"disposition": "NOT_ATTEMPTED"}
    else:
        row["reason_code"] = "dependency-failed"
        terminal = products["terminal"]
        products["terminal"] = replace(terminal, attempts=(replace(terminal.attempts[0], reason_code=row["reason_code"]),))
    with pytest.raises(ValueError, match="original receipt|nonattempt custody"):
        custody.project(InquiryStateSources((source,)))


def test_portable_contribution_ancestry_depth_exceeds_boolean_parent_bound(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_contributions
    from empirical_lawhood.runtime.recursive_handoff import RecursiveParentClosureBinding
    plane = _plane(tmp_path / "selected")
    @dataclass(frozen=True, slots=True)
    class Manifest(CanonicalRecord):
        SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/contribution-manifest"
        contribution_id: str
        predecessors: tuple = ()
    first = Manifest("parent-first")
    second = Manifest("parent-second", (identity(first, first.contribution_id),))
    rows = {"first": first, "second": second}
    def authenticate(directory, artifact_writer):
        name = Path(directory).name
        manifest = rows[name]
        return (None, SimpleNamespace(parent_closure_relative_paths=() if name == "first" else ("first",)),
                manifest, None, None, plane)
    monkeypatch.setattr(recursive_contributions, "authenticate_recursive_contribution", authenticate)
    binding = RecursiveParentClosureBinding("second", obj("transport"), identity(second, second.contribution_id))
    depth = service._inquiry_parent_depth(payloads={"parent-closure.json": binding.canonical_bytes()},
        draft=SimpleNamespace(contribution_parents=(second,)), artifact_writer=plane)
    assert depth == 3


def test_portable_contribution_ancestry_has_no_twenty_four_level_ceiling(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_contributions
    from empirical_lawhood.runtime.recursive_handoff import RecursiveParentClosureBinding
    plane = _plane(tmp_path / "selected")
    @dataclass(frozen=True, slots=True)
    class Manifest(CanonicalRecord):
        SCHEMA: ClassVar[str] = "empirical-lawhood/kernel/contribution-manifest"
        contribution_id: str
        predecessors: tuple = ()
    rows = {}
    for index in range(30):
        name = f"parent-{index:03d}"
        parent = () if index == 0 else (identity(rows[f"parent-{index - 1:03d}"], f"parent-{index - 1:03d}"),)
        rows[name] = Manifest(name, parent)
    def authenticate(directory, artifact_writer):
        name = Path(directory).name
        index = int(name.rsplit("-", 1)[1])
        paths = () if index == 0 else (f"parent-{index - 1:03d}",)
        return None, SimpleNamespace(parent_closure_relative_paths=paths), rows[name], None, None, plane
    monkeypatch.setattr(recursive_contributions, "authenticate_recursive_contribution", authenticate)
    terminal = rows["parent-029"]
    binding = RecursiveParentClosureBinding("parent-029", obj("transport"), identity(terminal, terminal.contribution_id))
    assert service._inquiry_parent_depth(payloads={"parent-closure.json": binding.canonical_bytes()},
        draft=SimpleNamespace(contribution_parents=(terminal,)), artifact_writer=plane) == 31



def test_original_source_scope_roles_and_nested_units_are_retained(custody, episode, monkeypatch):
    from hashlib import sha256
    from empirical_lawhood.api import recursive_inquiry_evidence
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    from empirical_lawhood.runtime.recursive_handoff import RecursiveWaveMember
    from empirical_lawhood.runtime.recursive_inquiry import InquiryEvidenceBinding
    source = custody.add_wave("first")
    packet, draft, run = custody.packets["first"]
    filename = "external-" + sha256(b"operand").hexdigest()[:24] + ".json"
    member = RecursiveWaveMember(filename, obj("source-bytes"), 4)
    packet = replace(packet, members=(member,))
    draft.links = (SimpleNamespace(consumer_node_id="operation", external_input_id="operand"),)
    draft.selected_operation_ids = ("operation",)
    draft.external_inputs = (SimpleNamespace(input_id="operand"),)
    custody.packets["first"] = packet, draft, run
    source = replace(source, packet=identity(packet, packet.packet_id))
    binding = InquiryEvidenceBinding("operand", "a" * 64, episode["specification"].endpoint,
        ContributionRole.RETAINED_ANALYSIS_INPUT, (), ("nested-a", "nested-b"))
    monkeypatch.setattr(recursive_inquiry_evidence, "project_wave_evidence_bindings", lambda **kwargs: {"operand": binding})
    state = custody.project(InquiryStateSources((source,)))
    assert state.stock[0].scope == binding.scope
    assert state.stock[0].role is ContributionRole.RETAINED_ANALYSIS_INPUT
    assert state.stock[0].nested_view_ids == ("nested-a", "nested-b")
    assert state.stock[0].independent_unit_ids == ()
    binding = replace(binding, scope=replace(binding.scope, receiver_id="other-receiver"))
    # Source operands can have different original receivers. Domain endpoint
    # applicability is checked independently; projection never stamps this scope.
    other = custody.project(InquiryStateSources((source,)))
    assert other.stock[0].scope == binding.scope
    assert other.stock[0].scope != episode["specification"].endpoint
