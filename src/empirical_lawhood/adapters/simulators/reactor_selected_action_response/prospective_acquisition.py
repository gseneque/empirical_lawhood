"""Native acquisition, external-format translation and custody integration."""

from typing import Callable
from empirical_lawhood.methods.law_assessment import CandidatePayloadReader
from empirical_lawhood.domains.reactor.reactor_selected_action_response.control_owner import ControlRecordPublisher, prepare_request
from empirical_lawhood.domains.reactor.reactor_selected_action_response.control_prospective_lock import freeze_prepared_request
from empirical_lawhood.domains.reactor.reactor_selected_action_response.control_prospective_plan import ReactorSelectedActionResponseProspectivePlan
from empirical_lawhood.domains.reactor.reactor_selected_action_response.law_terminal import ClassicalLaw
from empirical_lawhood.domains.reactor.reactor_selected_action_response.records import ClassicalCausal, ClassicalDecision, ClassicalPrivate
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode, TapeController
from empirical_lawhood.adapters.simulators.reactor_causal_response.acquisition import acquire_episode
from empirical_lawhood.domains.reactor.reactor_causal_response.design import draw_scenario
from empirical_lawhood.adapters.simulators.reactor_regime_response.committed_branch import acquire_committed_nominal_branch, acquire_committed_refined_replay
from empirical_lawhood.domains.reactor.reactor_regime_response.panel import assay_tape
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorBatchSource
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.controller_evaluation_nested import DurablePreparedExecutionEventStore, ProspectiveEvaluationBindingCoordinator
from empirical_lawhood.execution.controller_runtime import CommitmentDisposition
from empirical_lawhood.domains.reactor.reactor_selected_action_response.native_measurements import donor_episode

from empirical_lawhood.domains.reactor.reactor_selected_action_response.native_acquisition_records import (
    ClassicalRootAcquisition as _science_ClassicalRootAcquisition,
)

class UnboundSession:
    def advance(self, command: object) -> None:
        raise RuntimeError("classical precontact commitment attempted native delivery")

def acquire_prospective_root(
    *,
    source: ReactorBatchSource,
    causal: ClassicalCausal,
    private: ClassicalPrivate,
    assignment: ClassicalDecision,
    report: ClassicalLaw,
    prospective_plan: ReactorSelectedActionResponseProspectivePlan,
    calibration_artifact: ArtifactIdentity,
    publisher: ControlRecordPublisher,
    reader: CandidatePayloadReader,
    authority: ObjectIdentity,
    resources: ObjectIdentity,
    causal_receipt: CanonicalTaskReceipt,
    causal_artifact: ArtifactIdentity,
    issued_study: ObjectIdentity,
    prepared_store: DurablePreparedExecutionEventStore,
    occurred_at_utc: str,
    progress: Callable[[int], None] | None = None,
    acquire: Callable[..., NativeEpisode] = acquire_episode,
) -> _science_ClassicalRootAcquisition:
    root = causal.root
    if (
        causal.role != "prospective"
        or assignment.root != root
        or assignment.causal_preparation
        != ObjectIdentity.from_record(f"{root}.causal-preparation", causal)
        or private.causal_preparation != assignment.causal_preparation
        or source.fingerprint() != causal.source_sha256
        or authority.object_schema != 'empirical-lawhood/planning/study-operation-authority'
    ):
        raise ValueError("classical prospective source or execution authority differs")
    assigned = next(row for row in prospective_plan.assigned_roots if row.root == root)
    if assigned.eligible != assignment.causal_preparation_valid:
        raise ValueError("classical controller use changed its sealed root eligibility")
    if not assigned.eligible:
        return _science_ClassicalRootAcquisition(
            root, (None,), (None,), (None,), (), (None,), 0, assigned.reason_codes
        )
    plan = prospective_plan.plan
    callback = assignment.callback
    assert plan is not None and callback is not None
    scenario = draw_scenario(root, "heldout", causal.seed)
    if assigned.scenario != ObjectIdentity.from_record(scenario.unit_id, scenario):
        raise ValueError("classical controller use native realization differs")
    nominal_base, refined_base = (donor_episode(causal, private, view) for view in (0, 1))
    prepared = prepare_request(
        report=report,
        causal=causal,
        decision=assignment,
        request_K=report.payload.design.request_K,
        publisher=publisher,
        reader=reader,
        session=UnboundSession(),  # type: ignore[arg-type]
        calibration_artifact=calibration_artifact,
        authority=assignment.issue_authority,
        resources=resources,
        evaluation=plan,
    )
    lock = freeze_prepared_request(
        root=root,
        request_index=0,
        prepared=prepared,
        causal=causal,
        causal_receipt=causal_receipt,
        causal_artifact=causal_artifact,
        issued_study=issued_study,
        evaluation=plan,
        store=prepared_store,
        occurred_at_utc=occurred_at_utc,
    )
    coordinator = ProspectiveEvaluationBindingCoordinator(prepared_store=prepared_store)
    calls = 0

    def episode_progress(offset: int) -> Callable[[int], None]:
        def emit(value: int) -> None:
            if progress is not None:
                progress(offset * 2880 + value)

        return emit

    nominal = refined = None
    if prepared.commitment.disposition is CommitmentDisposition.NONATTEMPT:
        tick = prepared.deliver(publisher)
    else:
        nominal, owner = acquire_committed_nominal_branch(
            source=source,
            scenario=scenario,
            base=nominal_base,
            callback=callback,
            request_index=0,
            prepared=prepared,
            publisher=publisher,
            acquire=acquire,
            progress=episode_progress(calls),
        )
        calls += 1
        tick = owner.tick
        refined = acquire_committed_refined_replay(
            source=source,
            scenario=scenario,
            base=nominal_base,
            refined_preparation=refined_base,
            callback=callback,
            feed_kg_s=0.016,
            request_id=f"{root}.request-0",
            acquire=acquire,
            progress=episode_progress(calls),
        )
        calls += 1
    if tick is not None:
        coordinator.store_prepared_delivery(prefix_id=lock.prefix_id, tick=tick)
    chart = []
    for word, feed in enumerate((0.0, 0.016)):
        for view, base in enumerate((nominal_base, refined_base)):
            chart.append(
                acquire(
                    source,
                    scenario,
                    f"{root}.evaluator-word-{word}.view-{view}",
                    TapeController(assay_tape(base, callback, feed)),
                    dt=base.dt,
                    progress=episode_progress(calls),
                )
            )
            calls += 1
    return _science_ClassicalRootAcquisition(
        root, (prepared,), (nominal,), (refined,), tuple(chart), (tick,), calls, (), (lock,)
    )
