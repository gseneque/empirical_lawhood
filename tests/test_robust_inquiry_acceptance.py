# SPDX-License-Identifier: MPL-2.0
"""Actual PURE registered waves and independent expected policy decisions.

The original exposed operands remain development evidence. No native worker,
physical qualification or new scientific independent unit is involved.
"""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from math import acosh, cosh, exp, log
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execute
from empirical_lawhood.api import recursive_inquiry as service
from empirical_lawhood.api.recursive_contributions import export_recursive_contribution
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_inquiry import identity
from empirical_lawhood.kernel.recursive_inquiry_policy import (
    InquiryStopScope,
    ScientificOutcomeKind,
)
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.recursive_inquiry import InquiryAction
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.recursive_inquiry import InquiryStateSources, InquiryWaveSource
from tests.test_recursive_public_service import _plane
from tests.test_battery_refined_inquiry import selected as selected
from tests.test_battery_refined_inquiry_binding import stock as stock

ROOT = Path(__file__).resolve().parents[1]
D = Decimal


def input_origins(draft, parent=None):
    from empirical_lawhood.adapters.methods.compact_inquiry_policy import compact_input_origins
    return compact_input_origins(draft, parent)


def frozen_software_source(monkeypatch):
    """Concurrent engineering is excluded from this exposed fixture, explicitly."""
    source = author.implementation_binding(ROOT)
    for module in (author, execute, service):
        monkeypatch.setattr(module, "implementation_binding", lambda root, **kwargs: source)
    from empirical_lawhood.api import matrix_numerical_provenance as provenance
    observed = provenance.capture_matrix_provenance(project_root=ROOT)
    monkeypatch.setattr(provenance, "capture_matrix_provenance", lambda **kwargs: observed)


def operands(domain):
    if domain == "material":
        from empirical_lawhood.adapters.methods.analytic_material_inquiry import policy_binding, science
        from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart import UniformElectronGasAnalyticReferenceConfig
        source = decode_canonical_bytes((ROOT / "programmes/materials/superconductivity/workflows/electron-gas-response/config.json").read_bytes(),
                                        UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None)
        return policy_binding, science, (source,)
    from empirical_lawhood.adapters.methods.rubisco_inquiry import policy_binding, science
    from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import (
        GENBANK_SOURCE_SHA256, WILSON_SOURCE_SHA256, TeParentGenbankInputV1, WilsonArticleInputV1,
    )
    from tests.rubisco_nomination_fixture import source_operands
    retained = source_operands()
    return policy_binding, science, (
        WilsonArticleInputV1("input.exposed-policy.wilson", WILSON_SOURCE_SHA256,
                            retained["macro/source.007--wilson2017-jbc.html"].decode()),
        TeParentGenbankInputV1("input.exposed-policy.te", GENBANK_SOURCE_SHA256,
                              retained["macro/source.008--te-MG000148.gb"].decode()),
    )


def publish_sources(plane, draft, records):
    by_digest = {record.fingerprint(): record for record in records}
    bindings = []
    for external in draft.external_inputs:
        record = by_digest.get(external.expected_content_sha256)
        if record is None:
            continue
        path = f"sources/{draft.draft_id}/{external.input_id}.json"
        plane.write(ArtifactWriteRequest(external.logical_artifact_id, path, record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", draft.draft_id, "sources",
            record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append((external.input_id, plane.root.resolve(path, for_write=False)))
    return tuple(bindings)


def policy_request(*, binding, source_draft, specification_id, sources, plane, stage,
                   next_draft=None, parent=None, previous=None, product=None, assessments=()):
    """Use production adapter builders and the actual public state projector."""
    spec = binding.inquiry_specification(source_draft, specification_id=specification_id,
        stage=stage, parent=parent, previous=None if previous is None else previous["specification.json"],
        assessed_draft=None if product is None else product.get("draft"))
    cutoff = InformationCutoff(f"cutoff.{specification_id}", spec.endpoint.clock_id, CausalPhase.POST_OUTCOME, D(0))
    state = service.project_inquiry_state(specification=spec, state_id=f"state.{specification_id}",
        information_cutoff=cutoff, sources=sources, artifact_writer=plane)
    menu, policy = binding.inquiry_menu(spec, state, stage=stage, next_draft=next_draft, parent=parent,
        record=None if product is None else product["record"], assessments=assessments)
    assert menu.observation.outcome_id == ("initial" if product is None else product["outcome"])
    return spec, state, menu, policy


def commit(plane, directory, request, sources, campaign):
    spec, state, menu, policy = request
    packet, records = service.commit_inquiry_decision(specification=spec, state=state, sources=sources, menu=menu,
        policy=policy, campaign=campaign, right=campaign.decision_rights[0],
        actor_id=campaign.decision_rights[0].decision_maker_id, project_root=ROOT,
        artifact_writer=plane, output_dir=directory)
    assert service.read_inquiry_decision(directory=directory, artifact_writer=plane) == (packet, records)
    return records


def test_legacy_robust_packet_is_readable_history_and_cannot_enter_current_admission(tmp_path, monkeypatch):
    """An exposed v2 custody fixture is never promoted to a current ACT."""
    from empirical_lawhood.planning.recursive_inquiry_policy import choose_robust_inquiry, make_robust_successor_intent
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigins
    from empirical_lawhood.runtime.recursive_handoff import RecursiveWaveMember
    from empirical_lawhood.runtime.recursive_inquiry import RobustInquiryDecisionPacket
    from tests.test_recursive_inquiry_policy import policy_case

    case = policy_case("rubisco")
    plane = _plane(tmp_path / "selected")
    root = Path(plane.root.contract.canonical_path)
    sources = InquiryStateSources(())
    decision = choose_robust_inquiry(decision_id="decision.exposed-v2-archive", specification=case.specification,
        state=case.state, menu=case.menu, policy=case.policy, campaign=case.campaign, right=case.right,
        actor_id=case.actor_id, outcome_id=case.menu.observation.outcome_id)
    assert decision.VERSION == "2.0.0"
    assert next(row.action for row in case.menu.alternatives if row.alternative_id == decision.selected_alternative_id) is InquiryAction.ACT
    records = {"specification.json": case.specification, "state.json": case.state, "sources.json": sources,
        "menu.json": case.menu, "policy.json": case.policy, "campaign.json": case.campaign, "right.json": case.right,
        "decision.json": decision, "implementation.json": service.implementation_binding(ROOT),
        "intent.json": make_robust_successor_intent(intent_id="intent.exposed-v2-archive", decision=decision,
            specification=case.specification, menu=case.menu)}
    members = tuple(RecursiveWaveMember(name, identity(record, "inquiry-member." + name.removesuffix(".json")),
        len(record.canonical_bytes())) for name, record in sorted(records.items()))
    packet = RobustInquiryDecisionPacket("packet.exposed-v2-archive", members)
    directory = root / "archive"
    directory.mkdir()
    for name, record in (*sorted(records.items()), ("inquiry-packet.json", packet)):
        service._publish(plane, directory, name, record, packet.packet_id)
    before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    assert service.read_inquiry_decision(directory=directory, artifact_writer=plane,
        revalidate_sources=False) == (packet, records)
    with pytest.raises(ValueError, match="decision is archival"):
        service.read_inquiry_decision(directory=directory, artifact_writer=plane)
    with pytest.raises(ValueError, match="state is archival"):
        service.commit_inquiry_decision(specification=case.specification, state=case.state, sources=sources,
            menu=case.menu, policy=case.policy, campaign=case.campaign, right=case.right,
            actor_id=case.actor_id, project_root=ROOT, artifact_writer=plane, output_dir=root / "fresh-v2")
    with pytest.raises(ValueError, match="decision is archival"):
        service.author_inquiry_successor(decision_directory=directory, origins=RecursiveInputOrigins(()),
            initial_draft=None, project_root=ROOT, artifact_writer=plane, output_dir=root / "legacy-author")
    from empirical_lawhood.cli.app import app
    from typer.testing import CliRunner
    import json
    monkeypatch.setattr("empirical_lawhood.cli.integrations._storage", lambda: (ROOT, None, plane))
    cli = CliRunner()
    archived = cli.invoke(app, ["campaign", "recursive-inquiry-result", "--decision-dir", str(directory), "--historical"])
    assert archived.exit_code == 0, archived.output
    report = json.loads(archived.stdout)
    assert report["admission_status"] == "HISTORICAL_ARCHIVE"
    assert report["scientific_authority"] == "NONE" and report["qualification"] == "NOT_ESTABLISHED"
    assert report["decision"] == decision.to_document()
    default = cli.invoke(app, ["campaign", "recursive-inquiry-result", "--decision-dir", str(directory)])
    assert default.exit_code != 0 and "decision is archival" in default.output
    assert {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()} == before
    assert not (root / "fresh-v2").exists() and not (root / "legacy-author").exists()


def interrupted_material_fixture(plane, directory, draft, source_bindings):
    """Persist an exposed unknown-worker completion through production custody.

    No worker or native effect is entered. This explicitly recorded interruption
    fixture exercises recovery semantics; it is no historical scientific count.
    """
    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.execution import OperationalAttempt, OperationalFailureClass, TaskAttemptDisposition, TaskBlockReason
    from empirical_lawhood.runtime.recovery import OperationalFailureDiagnostic

    author.author_recursive_wave(draft=draft, origins=input_origins(draft), input_bindings=source_bindings,
        project_root=ROOT, artifact_writer=plane, output_dir=directory)
    packet, retained, _, payloads = author.load_authored_wave(directory=directory, artifact_writer=plane)
    run, plan, index = execute._retained_plans(payloads, retained)
    execute._external_inputs(plane=plane, plan=plan, draft=retained, payloads=payloads, read_only=False)
    execute._provenance(plane=plane, run_id=run.run_plan_id, observed=capture_matrix_provenance(project_root=ROOT))
    recovery = ExternalRunRecoveryStore(plane)
    recovery.freeze(index)
    task = plan.tasks[0]
    candidate = index.tasks[0].attempts[0]
    failure = OperationalFailureDiagnostic.create(OperationalFailureClass.RECOVERY_OBSTRUCTION,
        sanitized_exception_type="RecordedExposedInterruption", sanitized_message="Fixture worker completion is unknown")
    recovery.record_failure(index, task_id=task.task_id, attempt_id=candidate.attempt_id,
        reason_code=TaskBlockReason.UNKNOWN_COMPLETION.value, failure=failure, blocked=True)
    attempt = OperationalAttempt(candidate.attempt_id, run.run_plan_id, task.task_id, 1,
        TaskAttemptDisposition.BLOCKED, TaskBlockReason.UNKNOWN_COMPLETION.value, None, None)
    recovery.record_terminal(index, status=OperationalStatus.BLOCKED, attempts=(attempt,), receipts=())
    assert not tuple(Path(plane.root.contract.canonical_path).glob("runs/*/native-contacts/*.json"))
    return packet


def check_completed_work_and_read_only_reuse(*, plane, root, request, sources, campaign, source_draft, source_bindings, monkeypatch):
    """Actual COMPLETE census defeats omitted menu rows and misleading labels."""
    from empirical_lawhood.kernel.recursive_inquiry_policy import CompletedInquiryWork
    from empirical_lawhood.planning.recursive_inquiry_policy import InquiryAlternativeKind
    from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, LocalProcessExecutor
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigins
    from empirical_lawhood.cli.app import app
    from typer.testing import CliRunner
    import json

    spec, state, menu, policy = request
    binding = next(row for row in state.attempt_work_bindings if row.configuration == source_draft.operations[0].config_identity)
    attempt = next(row for row in state.operational_census if row.attempt_id == binding.attempt_id)
    original = next(row for row in menu.alternatives if row.action is InquiryAction.ACT)
    repeated = replace(original, work=binding.work, successor_draft=identity(source_draft, source_draft.draft_id),
        successor_config=source_draft.operations[0].config_identity,
        input_origins=identity(input_origins(source_draft), "inquiry-input-origins"),
        capability_id=source_draft.operations[0].selection.selection_id)
    assert menu.frontier.completed_work == ()
    for kind in (InquiryAlternativeKind.ACQUIRE, InquiryAlternativeKind.PREREQUISITE, InquiryAlternativeKind.INDEPENDENT_CHECK):
        alternative = replace(repeated, kind=kind,
            parent_requirement_id=spec.target.required_requirement_ids[0] if kind is InquiryAlternativeKind.PREREQUISITE else None)
        altered = replace(menu, alternatives=tuple(alternative if row == original else row for row in menu.alternatives))
        retained = commit(plane, root / ("decision.completed-hold-" + kind.value.lower()),
            (spec, state, altered, policy), sources, campaign)
        assert retained["decision.json"].selected_alternative_id == "hold"
        evaluation = next(row for row in retained["decision.json"].evaluations if row.alternative_id == alternative.alternative_id)
        assert "authenticated-completion-reuse-required" in evaluation.reason_codes and "intent.json" not in retained

    completion = CompletedInquiryWork("completion.actual-exposed-supplier", binding.work,
        attempt.attempt_id, attempt.receipt, attempt.products)
    reused = replace(repeated, kind=InquiryAlternativeKind.REUSE, reuse_completion=completion,
        scientific_question="Recover the exact original completed exposed supplier without new task entry")
    reuse_menu = replace(menu, alternatives=tuple(reused if row == original else row for row in menu.alternatives),
        frontier=replace(menu.frontier, completed_work=(completion,)))
    # Even a real source-only same-work draft cannot replace the exact retained
    # draft in a receipt-recovery promise. Refuse before any decision persists.
    alias = replace(source_draft, draft_id="draft.same-work-recovery-alias")
    author.author_recursive_wave(draft=alias, origins=input_origins(alias), input_bindings=source_bindings,
        project_root=ROOT, artifact_writer=plane, output_dir=root / "alias")
    alias_packet = author.load_authored_wave(directory=root / "alias", artifact_writer=plane)[0]
    alias_sources = replace(sources, waves=tuple(sorted((*sources.waves,
        InquiryWaveSource("alias", identity(alias_packet, alias_packet.packet_id), False)), key=lambda row: row.relative_path)))
    alias_state = service.project_inquiry_state(specification=spec, state_id="state.recovery-alias",
        information_cutoff=state.information_cutoff, sources=alias_sources, artifact_writer=plane)
    alias_id = identity(alias_state, alias_state.state_id)
    alias_alternative = replace(reused, state=alias_id, successor_draft=identity(alias, alias.draft_id))
    alias_menu = replace(reuse_menu, state=alias_id, alternatives=tuple(
        alias_alternative if row.alternative_id == reused.alternative_id else replace(row, state=alias_id)
        for row in reuse_menu.alternatives))
    with pytest.raises(ValueError, match="original task/plan/draft/receipt/work"):
        commit(plane, root / "decision.recovery-alias-refused", (spec, alias_state, alias_menu, policy), alias_sources, campaign)
    assert not (root / "decision.recovery-alias-refused").exists()
    finite_policy = replace(policy, max_operations=len(state.operational_census), max_waves=state.wave_count,
        max_depth=state.depth_count)
    directory = root / "decision.reuse"
    retained = commit(plane, directory, (spec, state, reuse_menu, finite_policy), sources, campaign)
    assert retained["decision.json"].selected_alternative_id == reused.alternative_id
    before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    with monkeypatch.context() as isolated:
        def refuse(*args, **kwargs):
            raise AssertionError("read-only inquiry completion recovery entered an executor")
        isolated.setattr(DirectTaskExecutor, "execute", refuse)
        isolated.setattr(LocalProcessExecutor, "execute", refuse)
        recovered = service.recover_inquiry_completion(decision_directory=directory, artifact_writer=plane)
        original_report, products, _, _ = execute.read_recursive_wave(directory=root / "supplier", artifact_writer=plane,
            include_products=True)
        assert recovered["status"] == "RECOVERED_COMPLETION" and recovered["completion"] == completion.to_document()
        assert recovered["original_operational_census"] == products["operational_census"]
        assert recovered["original_wave_report"] == original_report
        assert recovered["products"] == {key: value.to_document() for key, value in
            products["records"][source_draft.selected_operation_ids[0]].items()}
        assert recovered["task_receipt"] == products["attempt_receipts"][attempt.attempt_id].to_document()
        assert recovered["producing_implementation"] == author.load_authored_wave(
            directory=root / "supplier", artifact_writer=plane)[2].to_document()
        assert recovered["new_native_contact_count"] == recovered["fresh_independent_units"] == 0
        assert recovered["new_operation_count"] == recovered["new_wave_count"] == 0
        assert recovered["read_cpu_seconds"] is recovered["read_wall_seconds"] is recovered["read_peak_rss_bytes"] is None
        isolated.setattr("empirical_lawhood.cli.integrations._storage", lambda: (ROOT, None, plane))
        cli = CliRunner().invoke(app, ["campaign", "recursive-inquiry-result", "--decision-dir", str(directory)])
        assert cli.exit_code == 0, cli.output
        assert json.loads(cli.stdout)["reused_completion"] == json.loads(json.dumps(recovered))
        with pytest.raises(ValueError, match="read-only completion recovery"):
            service.author_inquiry_successor(decision_directory=directory, origins=RecursiveInputOrigins(()),
                initial_draft=source_draft, project_root=ROOT, artifact_writer=plane, output_dir=root / "repeat-refused")
        with pytest.raises(ValueError, match="read-only completion recovery"):
            service._validate_successor_allowances(retained, source_draft)
    assert {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()} == before
    assert not (root / "repeat-refused").exists()


def test_public_projection_blocks_config_rename_and_admits_only_authentic_distinct_work(tmp_path, monkeypatch):
    """Actual API projection/custody, with no policy-forged attempt operation."""
    from empirical_lawhood.kernel.recursive_inquiry import InquiryAttemptStatus, identity
    from empirical_lawhood.kernel.recursive_inquiry_policy import WorkBoundInquiryState
    from empirical_lawhood.planning.recursive_inquiry_policy import choose_robust_inquiry
    from empirical_lawhood.planning.recursive_inquiry_policy import InquiryAlternativeKind
    from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import use_draft

    frozen_software_source(monkeypatch)
    binding, science, records = operands("material")
    plane = _plane(tmp_path / "selected")
    root = Path(plane.root.contract.canonical_path)
    draft = binding.policy_supply_draft(*records)
    source_bindings = publish_sources(plane, draft, records)
    packet = interrupted_material_fixture(plane, root / "interrupted", draft, source_bindings)
    sources = InquiryStateSources((InquiryWaveSource("interrupted", identity(packet, packet.packet_id), True),))
    specification = binding.inquiry_specification(draft, specification_id="inquiry.recorded-uncertainty", stage="origin")
    act_id = "investigate-supplier"
    specification = replace(specification, outcomes=tuple(replace(row, alternative_ids=tuple(sorted((*row.alternative_ids, act_id))))
        if row.kind is ScientificOutcomeKind.UNCERTAIN_CONTACT else row for row in specification.outcomes))
    cutoff = InformationCutoff("cutoff.recorded-uncertainty", specification.endpoint.clock_id, CausalPhase.POST_OUTCOME, D(0))
    state = service.project_inquiry_state(specification=specification, state_id="state.recorded-uncertainty",
        information_cutoff=cutoff, sources=sources, artifact_writer=plane)
    assert type(state) is WorkBoundInquiryState
    attempt = state.operational_census[0]
    assert attempt.operation == draft.operations[0].config_identity
    assert attempt.status is InquiryAttemptStatus.UNCERTAIN_CONTACT and attempt.products == ()
    actual = state.attempt_work_bindings[0]
    assert actual.configuration == attempt.operation and actual.witness == attempt.receipt
    assert actual.work == binding.scientific_work(draft, draft.operations[0].node_id)
    menu, policy = binding.inquiry_menu(specification, state, stage="origin", next_draft=draft)
    menu = replace(menu, observation=replace(menu.observation, outcome_id="uncertain-contact",
        kind=ScientificOutcomeKind.UNCERTAIN_CONTACT, attempt_ids=(attempt.attempt_id,),
        reason="Authenticated exposed recovery witness retains unknown completion"), alternatives=tuple(
            replace(row, eligible_outcomes=(*row.eligible_outcomes, "uncertain-contact"))
            if row.alternative_id == act_id else row for row in menu.alternatives))
    campaign = draft.campaign
    request = (specification, state, menu, policy)
    result = commit(plane, root / "decision.hold", request, sources, campaign)
    assert result["decision.json"].selected_alternative_id == "hold"
    assert result["decision.json"].VERSION == "3.0.0"
    assert "intent.json" not in result
    act = next(row for row in menu.alternatives if row.alternative_id == act_id)
    assert "uncertain-contact-recovery-required" in next(row for row in result["decision.json"].evaluations if row.alternative_id == act_id).reason_codes
    renamed = replace(act, successor_config=replace(act.successor_config, object_id="config.renamed-same-science"))
    renamed_menu = replace(menu, alternatives=tuple(renamed if row == act else row for row in menu.alternatives))
    kwargs = dict(decision_id="decision.renamed", specification=specification, state=state, policy=policy,
        campaign=campaign, right=campaign.decision_rights[0], actor_id=campaign.decision_rights[0].decision_maker_id,
        outcome_id="uncertain-contact")
    assert choose_robust_inquiry(menu=renamed_menu, **kwargs).selected_alternative_id == "hold"
    with pytest.raises(ValueError, match="registered configuration/scientific work"):
        commit(plane, root / "decision.renamed-refused", (specification, state, renamed_menu, policy), sources, campaign)

    # The installed compact config ID has a closed grammar: arbitrary config
    # aliases refuse above. A valid new draft/invocation label still denotes the
    # same registered work and must HOLD through the actual public projector.
    relabelled = binding.policy_supply_draft(*records, draft_id="draft.relabelled-uncertain-supply")
    assert binding.scientific_work(relabelled, relabelled.selected_operation_ids[0]) == actual.work
    author.author_recursive_wave(draft=relabelled, origins=input_origins(relabelled), input_bindings=source_bindings,
        project_root=ROOT, artifact_writer=plane, output_dir=root / "relabelled")
    relabelled_packet = author.load_authored_wave(directory=root / "relabelled", artifact_writer=plane)[0]
    relabelled_sources = replace(sources, waves=(*sources.waves,
        InquiryWaveSource("relabelled", identity(relabelled_packet, relabelled_packet.packet_id), False)))
    relabelled_state = service.project_inquiry_state(specification=specification, state_id="state.relabelled-work",
        information_cutoff=cutoff, sources=relabelled_sources, artifact_writer=plane)
    relabelled_id = identity(relabelled_state, relabelled_state.state_id)
    relabelled_act = replace(act, state=relabelled_id, successor_draft=identity(relabelled, relabelled.draft_id))
    relabelled_menu = replace(menu, state=relabelled_id, alternatives=tuple(
        relabelled_act if row == act else replace(row, state=relabelled_id) for row in menu.alternatives))
    relabelled_result = commit(plane, root / "decision.relabelled-hold",
        (specification, relabelled_state, relabelled_menu, policy), relabelled_sources, campaign)
    assert relabelled_result["decision.json"].selected_alternative_id == "hold"
    assert relabelled_state.operational_census == state.operational_census
    assert relabelled_state.attempt_work_bindings == state.attempt_work_bindings

    # An independently supplied exposed conditional consumer has different
    # registered scientific semantics. Its source-only prospective preparation
    # is declared before a separate ACT; the uncertain supplier is never retried.
    supplier = science.supply(records[0])
    instance = science.compatible_instance(supplier)
    distinct = use_draft(supplier, instance, draft_id="draft.independent-exposed-consumer")
    distinct_bindings = publish_sources(plane, distinct, (supplier, instance))
    author.author_recursive_wave(draft=distinct, origins=input_origins(distinct), input_bindings=distinct_bindings,
        project_root=ROOT, artifact_writer=plane, output_dir=root / "prospective")
    prospective = author.load_authored_wave(directory=root / "prospective", artifact_writer=plane)[0]
    sources = replace(sources, waves=(*sources.waves, InquiryWaveSource("prospective", identity(prospective, prospective.packet_id), False)))
    state2 = service.project_inquiry_state(specification=specification, state_id="state.distinct-work",
        information_cutoff=cutoff, sources=sources, artifact_writer=plane)
    work = binding.scientific_work(distinct, distinct.operations[0].node_id)
    assert work != actual.work and work.scope == actual.work.scope
    tid = identity(state2, state2.state_id)
    distinct_act = replace(act, state=tid, work=work, successor_draft=identity(distinct, distinct.draft_id),
        successor_config=distinct.operations[0].config_identity,
        input_origins=identity(input_origins(distinct), "inquiry-input-origins"),
        capability_id=distinct.operations[0].selection.selection_id,
        kind=InquiryAlternativeKind.INDEPENDENT_CHECK, supplier=None, parent_requirement_id=None)
    distinct_menu = replace(menu, state=tid, alternatives=tuple(distinct_act if row == act else replace(row, state=tid)
        for row in menu.alternatives))
    same_menu = replace(menu, state=tid, alternatives=tuple(replace(row, state=tid) for row in menu.alternatives))
    with pytest.raises(ValueError, match="eligible frozen choice"):
        service.commit_inquiry_decision(specification=specification, state=state2, sources=sources, menu=same_menu,
            policy=policy, campaign=campaign, right=campaign.decision_rights[0], actor_id=campaign.decision_rights[0].decision_maker_id,
            project_root=ROOT, artifact_writer=plane, output_dir=root / "forged-human-choice", human_choice=act_id,
            human_reason="A label cannot settle uncertain completion")
    separate = service.commit_inquiry_decision(specification=specification, state=state2, sources=sources, menu=distinct_menu,
        policy=policy, campaign=campaign, right=campaign.decision_rights[0], actor_id=campaign.decision_rights[0].decision_maker_id,
        project_root=ROOT, artifact_writer=plane, output_dir=root / "decision.distinct", human_choice=act_id,
        human_reason="Select the separately supplied exposed independent consumer, preserving the uncertain original work")[1]
    assert separate["decision.json"].selected_alternative_id == act_id and separate["decision.json"].human_directed
    assert state2.operational_census == state.operational_census and state2.attempt_work_bindings == state.attempt_work_bindings
    assert not tuple(root.glob("runs/*/native-contacts/*.json"))


def run_exposed_battery_source_gate(stock, directory):
    """Run the installed PURE gate alone, retaining its actual local receipt.

    This explicitly selected software gate does not select the native acquisition
    or the qualification reducer present in the complete domain draft.
    """
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import operation_bindings as owner
    from empirical_lawhood.api.recursive_execution import _external_inputs
    from empirical_lawhood.infrastructure.execution import DirectTaskExecutor, LocalScheduler
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.recursive_custody import read_recursive_products
    from empirical_lawhood.infrastructure.sql import SQLiteOperationalRepository, create_catalog_engine, upgrade_catalog
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile, RunnerRegistry
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex
    from tests.runtime_platform.test_execution_scheduler import StaticExternalInputResolver
    from tests.test_battery_refined_inquiry_binding import compile_stock

    draft, compiled = compile_stock(stock)
    gate_task = next(task for task in compiled.execution_plan.tasks if task.task_id.endswith("validate-policy"))
    plan = replace(compiled.execution_plan, execution_plan_id="execution-plan.exposed-inquiry-gate", tasks=(gate_task,))
    plane = _plane(directory)
    payloads = {row.config_id: row.payload for row in compiled.config_inputs}
    payloads.update({name: record.canonical_bytes() for name, record in (
        ("source", stock.source), ("policy", stock.policy), ("selection", stock.selection), ("diagnostic", stock.diagnostic))})
    inputs = _external_inputs(plane=plane, plan=plan, draft=draft, payloads=payloads, read_only=False)
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=plan.source_plan.object_id,
        wave_id="wave.exposed-inquiry-gate", authority_identities=())
    registry = compiled.registry
    runners = RunnerRegistry((owner.RefinedRunner("validate-policy"),), registry_sha256=registry.fingerprint())
    engine = create_catalog_engine("sqlite+pysqlite:///:memory:")
    upgrade_catalog(engine)
    scheduler = LocalScheduler(operational_repository=SQLiteOperationalRepository(engine), artifact_writer=plane,
        receipt_store=ExternalTaskReceiptStore(plane), recovery_index=index, recovery_store=ExternalRunRecoveryStore(plane),
        runner_registry=runners, implementation_commit=plan.implementation_commit,
        external_input_resolver=StaticExternalInputResolver(inputs), executor=DirectTaskExecutor(), input_port_factory=plane,
        lane=PlanLane.DEVELOPMENT, authorized_barriers=(), assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
    try:
        result = scheduler.execute(index.run_id, plan)
        assert result.status is OperationalStatus.SUCCEEDED
        assert len(result.receipts) == 1
        assert not tuple(Path(plane.root.contract.canonical_path).glob("runs/*/native-contacts/*.json"))
        products = read_recursive_products(plane=plane, plan=plan, index=index, external_inputs=inputs,
                                          output_codecs=owner.output_codecs())
        gate = next(iter(products["records"][gate_task.task_id].values()))
        return gate, result.receipts[0]
    finally:
        engine.dispose()


@pytest.mark.parametrize("kind", (ScientificOutcomeKind.UNEVALUABLE, ScientificOutcomeKind.NEGATIVE))
def test_source_bound_battery_pure_gate_retains_uncertainty_or_negative_without_admission(
        tmp_path, monkeypatch, stock, kind):
    """Actual complete exposed diagnostic operands; no acquisition or qualification."""
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import science as diagnostic_science
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticResult
    from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, native, operation_bindings as owner
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import scope as original_scope
    from empirical_lawhood.kernel.recursive_inquiry import InquiryEvidence
    from tests.test_battery_dfn_precision_diagnostic import config_rows, exposed
    from tests.test_recursive_inquiry_policy import choose, policy_case, rebound

    monkeypatch.setattr(native, "acquire", lambda *_: pytest.fail("policy conformance entered native acquisition"))
    if kind is ScientificOutcomeKind.NEGATIVE:
        # All twelve complete exposed numerical views agree on an adverse
        # voltage endpoint; completed precision diagnosis is not target success.
        traces = []
        for config in config_rows():
            row = exposed(config)
            attempts = tuple(replace(attempt, start_receivers=(attempt.start_receivers[0], D("4.3"), *attempt.start_receivers[2:]),
                end_receivers=(attempt.end_receivers[0], D("4.3"), *attempt.end_receivers[2:])) for attempt in row.charging_attempts)
            traces.append(replace(row, voltage_v=tuple(D("4.3") for _ in row.voltage_v), charging_attempts=attempts,
                                  delivery=replace(row.delivery, applied_voltage_v=D("4.3"))))
        traces = tuple(traces)
        checks = tuple(diagnostic_science.check_trace(row) for row in traces)
        comparisons = diagnostic_science.comparisons(traces)
        diagnostic = DiagnosticResult(stock.diagnostic.product_id, stock.diagnostic.source, stock.diagnostic.prior_supply,
            traces, checks, comparisons, AssessmentDisposition.SATISFIED)
        assert all(row.disposition is AssessmentDisposition.FALSIFIED for row in checks)
        assert all(row.disposition is AssessmentDisposition.SATISFIED for row in comparisons)
        selection = replace(stock.selection, diagnostic=owner.record_identity(diagnostic))
        policy = replace(stock.policy, diagnostic=selection.diagnostic, protocol_sha256=selection.fingerprint())
        source = replace(stock.source, diagnostic=selection.diagnostic, policy=c.identity(policy), protocol_sha256=policy.protocol_sha256)
        stock = SimpleNamespace(source=source, policy=policy, selection=selection, diagnostic=diagnostic)
    gate, receipt = run_exposed_battery_source_gate(stock, tmp_path / "battery-gate")
    assert gate.diagnostic == owner.record_identity(stock.diagnostic)
    assert gate.numerical_adequacy == "NOT_ASSESSED" and gate.scientific_authority == "NONE"
    assert len(stock.diagnostic.traces) == 12 and len(stock.diagnostic.checks) == 12 and len(stock.diagnostic.comparisons) == 9
    assert gate.fingerprint() in {row.content_sha256 for row in receipt.output_logical_artifacts}

    case = policy_case("battery", outcome=kind)
    scope = original_scope(stock.source.original)
    requirements = tuple(replace(row, scope=scope) for row in case.specification.requirements)
    target = replace(case.specification.target, scope=scope)
    specification = replace(case.specification, endpoint=scope, target=target, requirements=requirements,
                            distinguishing_assessment=owner.record_identity(stock.diagnostic.source))
    source_id = owner.record_identity(stock.source.original)
    diagnostic_id = owner.record_identity(stock.diagnostic)
    evidence = (
        InquiryEvidence("evidence.assessment", diagnostic_id, None, scope, case.state.stock[0].role, (), (), source_contract=source_id),
        InquiryEvidence("evidence.gate", owner.record_identity(gate), identity(receipt, receipt.receipt_id), c.scope(stock.source),
            case.state.stock[0].role, (), ()),
        InquiryEvidence("evidence.source", source_id, None, scope, case.state.stock[-1].role, (), (), source_contract=source_id),
    )
    alternatives = tuple(replace(row, scope=scope,
        evidence_needs=tuple(replace(need, scope=scope, product=source_id) for need in row.evidence_needs),
        work=None if row.work is None else replace(row.work, scope=scope, scientific_operands=tuple(sorted(
            (owner.record_identity(value) for value in (stock.source, stock.policy, stock.selection, stock.diagnostic)),
            key=lambda value: value.object_id)),
            observation_contract=specification.distinguishing_assessment)) for row in case.menu.alternatives)
    frontier = replace(case.menu.frontier, target=identity(target, target.target_id),
        requirement_findings=tuple(replace(row, requirement=identity(requirement, requirement.requirement_id))
            for row, requirement in zip(case.menu.frontier.requirement_findings, requirements, strict=True)),
        claim_findings=tuple(replace(row, scope=scope) for row in case.menu.frontier.claim_findings))
    cutoff = replace(case.state.information_cutoff, clock_id=scope.clock_id)
    observation = replace(case.menu.observation, scope=scope, assessment=diagnostic_id, information_cutoff=cutoff,
        assessment_contract=specification.distinguishing_assessment,
        reason="Full twelve-view exposed diagnostic result retains an adverse service endpoint or numerical uncertainty; source-policy consistency supplies no qualification.")
    case = rebound(case, specification=specification, state=replace(case.state, stock=evidence, information_cutoff=cutoff),
        campaign=replace(case.campaign, system_ids=(scope.system_id,), world_ids=(scope.world_id,)),
        menu=replace(case.menu, alternatives=alternatives, frontier=frontier, observation=observation))
    decision = choose(case)
    assert decision.selected_alternative_id == "investigate-prerequisite"
    assert decision.supplied_requirement_ids == ()
    assert decision.unresolved_target_claim_ids and decision.unresolved_target_requirement_ids
    assert "missing-prerequisite" in decision.evaluations[0].reason_codes


@pytest.mark.parametrize("domain", ("material", "rubisco"))
def test_actual_origin_supplier_independent_later_use_and_unmet_application_frontier(tmp_path, monkeypatch, domain):
    frozen_software_source(monkeypatch)
    binding, science, records = operands(domain)
    plane = _plane(tmp_path / "selected")
    root = Path(plane.root.contract.canonical_path)
    source_draft = binding.policy_supply_draft(*records)
    source_bindings = publish_sources(plane, source_draft, records)
    origins = input_origins(source_draft)
    source_dir = root / "origin"
    author.author_recursive_wave(draft=source_draft, origins=origins, input_bindings=source_bindings,
        project_root=ROOT, artifact_writer=plane, output_dir=source_dir)
    source_packet = author.load_authored_wave(directory=source_dir, artifact_writer=plane)[0]
    origin_sources = InquiryStateSources((InquiryWaveSource("origin", identity(source_packet, source_packet.packet_id), False),))
    initial = policy_request(binding=binding, source_draft=source_draft, specification_id="inquiry.origin",
        sources=origin_sources, plane=plane, stage="origin", next_draft=source_draft)
    initial_records = commit(plane, root / "decision.origin", initial, origin_sources, source_draft.campaign)
    assert initial_records["decision.json"].selected_alternative_id == "investigate-supplier"
    assert initial_records["decision.json"].unresolved_target_requirement_ids == tuple(
        row.requirement_id for row in source_draft.requirements)
    supplier_dir = root / "supplier"
    service.author_inquiry_successor(decision_directory=root / "decision.origin", initial_draft=source_draft,
        origins=origins, input_bindings=source_bindings, project_root=ROOT, artifact_writer=plane, output_dir=supplier_dir)
    assert service.run_inquiry_successor(directory=supplier_dir, project_root=ROOT, artifact_writer=plane)["new_native_contact_count"] == 0
    _, supply_products, _, _ = execute.read_recursive_wave(directory=supplier_dir, artifact_writer=plane, include_products=True)
    supplier = next(record for outputs in supply_products["records"].values() for record in outputs.values())
    assert supplier.disposition is AssessmentDisposition.SATISFIED
    export_recursive_contribution(directory=supplier_dir, project_root=ROOT, artifact_writer=plane,
                                  output_dir=root / "contribution")
    from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution
    parent = authenticate_recursive_contribution(directory=root / "contribution", artifact_writer=plane)[2]
    next_draft = service.preview_inquiry_successor(supplier_directory=supplier_dir, artifact_writer=plane)
    assert next_draft == binding.assessed_use_draft(supplier, parent=parent)
    supplier_packet = author.load_authored_wave(directory=supplier_dir, artifact_writer=plane)[0]
    later_sources = InquiryStateSources((InquiryWaveSource("supplier", identity(supplier_packet, supplier_packet.packet_id), True),),
        previous_decision_paths=("decision.origin",))
    supply_result = {"record": supplier, "outcome": "useful-supply"}
    next_request = policy_request(binding=binding, source_draft=source_draft, specification_id="inquiry.later",
        sources=later_sources, plane=plane, stage="later", next_draft=next_draft, parent=parent,
        previous=initial_records, product=supply_result)
    with pytest.raises(ValueError, match="supply/independent-use stage"):
        binding.inquiry_menu(next_request[0], next_request[1], stage="later", next_draft=source_draft,
            record=supplier, parent=parent)
    if domain == "material":
        check_completed_work_and_read_only_reuse(plane=plane, root=root, request=next_request,
            sources=later_sources, campaign=source_draft.campaign, source_draft=source_draft,
            source_bindings=source_bindings, monkeypatch=monkeypatch)
    next_records = commit(plane, root / "decision.later", next_request, later_sources, source_draft.campaign)
    assert next_records["decision.json"].selected_alternative_id == "independently-assess-later-instance"
    assert next_records["decision.json"].supplied_requirement_ids == ()
    candidate = science.compatible_instance(supplier) if domain == "material" else science.authentic_candidate(supplier)
    use_bindings = publish_sources(plane, next_draft, (candidate,))
    use_dir = root / "use"
    service.author_inquiry_successor(decision_directory=root / "decision.later", supplier_directory=supplier_dir,
        origins=input_origins(next_draft, parent), input_bindings=use_bindings, contribution_dir=root / "contribution",
        project_root=ROOT, artifact_writer=plane, output_dir=use_dir)
    report = service.run_inquiry_successor(directory=use_dir, project_root=ROOT, artifact_writer=plane)
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
    _, use_products, retained_draft, _ = execute.read_recursive_wave(directory=use_dir, artifact_writer=plane, include_products=True)
    assessment = next(record for outputs in use_products["records"].values() for record in outputs.values())
    phases = use_products["connection_assessments"]
    assert len(phases) == 4 and len({row.phase for row in phases}) == 4
    # These expected verdicts come from independent scalar equations and native
    # source endpoints, not the policy's producer or evaluator implementation.
    if domain == "material":
        from scipy.constants import mu_0
        assert len(assessment.instance.panel.rows) == 20
        assert len(assessment.instance.panel.slab_profile) == 101
        kernel = 1 / (mu_0 * 1e-7**2)
        for row in assessment.instance.panel.rows:
            expected = -kernel * (1 + 4 * float(row.q_over_kf)**2) * float(row.realized_A_T[1])
            assert abs(float(row.current_density[1]) - expected) <= max(abs(expected) * 1e-12, 1e-100)
        centre = float(assessment.instance.panel.slab_profile[50][1])
        assert abs(centre - 1 / cosh(5)) / centre < 1e-12
        assert abs(1e-6 / (2 * acosh(1 / centre)) - 1e-7) / 1e-7 < 1e-12
        assert assessment.disposition is AssessmentDisposition.SATISFIED
    else:
        assert len(supplier.panel.rows) == 19
        assert abs(float(supplier.forecast.additive_point.turnover_s_inv) - exp(log(6.4) + log(8.8) - log(6.9))) < 1e-12
        assert D("8.1") / D("5.46") > 1 and D("45.5") / D(238) < 1
        assert assessment.disposition is AssessmentDisposition.FALSIFIED
    use_packet = author.load_authored_wave(directory=use_dir, artifact_writer=plane)[0]
    frontier_sources = InquiryStateSources((InquiryWaveSource("use", identity(use_packet, use_packet.packet_id), True),),
        previous_decision_paths=("decision.later",))
    final_request = policy_request(binding=binding, source_draft=source_draft, specification_id="inquiry.frontier",
        sources=frontier_sources, plane=plane, stage="frontier", parent=parent, previous=next_records,
        product={"record": assessment, "draft": retained_draft,
                 "outcome": "useful-supply" if domain == "material" else "scoped-failure"}, assessments=phases)
    final_records = commit(plane, root / "decision.frontier", final_request, frontier_sources, source_draft.campaign)
    decision = final_records["decision.json"]
    assert next(row.action for row in final_records["menu.json"].alternatives
                if row.alternative_id == decision.selected_alternative_id) is InquiryAction.STOP
    assert decision.stop_scope is InquiryStopScope.BRANCH
    assert decision.unresolved_target_requirement_ids and decision.unresolved_target_claim_ids
    assert decision.unentered_requirement_ids == (source_draft.requirements[0].requirement_id,)
    assert bool(decision.supplied_requirement_ids) == (domain == "material")
    if domain == "rubisco":
        joined = next(row for row in phases if row.phase.value == "JOINED")
        assert joined.disposition is AssessmentDisposition.FALSIFIED
    before = {path.relative_to(root): sha256(path.read_bytes()).hexdigest()
              for path in root.rglob("*") if path.is_file() and not path.name.endswith(".lock")}
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    monkeypatch.setattr(LocalProcessExecutor, "execute", lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("completed exposed inquiry was reacquired")))
    assert service.run_inquiry_successor(directory=use_dir, project_root=ROOT, artifact_writer=plane)["new_native_contact_count"] == 0
    assert service.read_inquiry_decision(directory=root / "decision.frontier", artifact_writer=plane)[1] == final_records
    after = {path.relative_to(root): sha256(path.read_bytes()).hexdigest()
             for path in root.rglob("*") if path.is_file() and not path.name.endswith(".lock")}
    assert before == after
    # Complete custody moves without the producing root or another operation.
    relocated = _plane(tmp_path / "relocated")
    destination = Path(relocated.root.contract.canonical_path)
    shutil.copytree(root, destination, dirs_exist_ok=True)
    shutil.rmtree(root)
    assert service.read_inquiry_decision(directory=destination / "decision.frontier", artifact_writer=relocated,
                                        revalidate_sources=False)[1] == final_records
    retained, reread, _, _ = execute.read_recursive_wave(directory=destination / "use",
                                                       artifact_writer=relocated, include_products=True)
    assert retained["new_native_contact_count"] == 0
    assert reread["records"] == use_products["records"]
    assert reread["connection_assessments"] == phases
    relocated_bytes = {path.relative_to(destination): sha256(path.read_bytes()).hexdigest()
                       for path in destination.rglob("*") if path.is_file() and not path.name.endswith(".lock")}
    assert relocated_bytes == before
