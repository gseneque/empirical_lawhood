"""Native acquisition, external-format translation and custody integration."""

from typing import Any
from empirical_lawhood.methods.control.prepared_forecast import freeze_forecast_request
from empirical_lawhood.methods.control.publication import ControlPublicationSession, ControlPublisher
from empirical_lawhood.methods.law_assessment import CandidatePayloadReader
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.frozen_records import UndeliverableSession
from empirical_lawhood.domains.reactor.reactor_prefix_response.batch_design import ReactorBatchSource
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.storage.contracts.canonical_record_archive import CanonicalRecordArchive
from empirical_lawhood.execution.controller_runtime import CommitmentDisposition, DeliveryControllerTickReceipt
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import ARMS, BASE, LOCAL_REQUESTS, MENUS, PAIR_REQUESTS, SEQUENCES, Request
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.control_owner import assess_candidate, rank_and_commit
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.law_evaluator import ClassicalLawEvaluator, registration
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.law_terminal import ClassicalLaws
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prospective_plan import ReactorStagedPulseResponseProspectivePlan
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prediction import ClassicalPredictedBound, ClassicalPredictionSeal
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.records import ClassicalContext, ClassicalPreparation

from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.frozen_records import (
    ClassicalFrozenRoot as _science_ClassicalFrozenRoot,
    ClassicalFrozenStage as _science_ClassicalFrozenStage,
)

def freeze_stage(
    *,
    laws: ClassicalLaws,
    plan: ReactorStagedPulseResponseProspectivePlan,
    causal: ClassicalContext,
    policy: str,
    request: Request,
    kind: str,
    source: ReactorBatchSource,
    publisher: ControlPublisher,
    reader: CandidatePayloadReader,
    control: Any,
    checkpoint: ObjectIdentity,
    causal_artifact: ArtifactIdentity,
    causal_receipt: CanonicalTaskReceipt | DeliveryControllerTickReceipt,
    expected_predictions: tuple[ClassicalPredictedBound, ...] = (),
) -> _science_ClassicalFrozenStage:
    use_plan = plan.use(policy, request, kind)

    def refused(reason: str) -> _science_ClassicalFrozenStage:
        return _science_ClassicalFrozenStage(
            policy,
            request,
            kind,
            causal,
            None,
            None,
            None,
            None,
            None,
            (),
            None,
            None,
            None,
            (reason,),
        )

    if use_plan.plan is None or not next(
        yes for root, yes, _ in use_plan.assigned if root == causal.root
    ):
        return refused("LOCAL_LAW_OR_CAUSAL_PREREQUISITE_NONENTRY")
    arm = (
        policy
        if policy in ARMS
        else "EL_SERVICE_MENU"
        if policy in MENUS
        else "EL_SEQUENCE_RELATION"
    )
    fixed = dict(laws.operands.nomination.fixed_seconds).get(request.request_id)
    reports = tuple(
        r
        for r in laws.rows
        if r.payload.recipe.recipe_id in laws.qualified
        and r.payload.recipe.arm == arm
        and r.payload.recipe.bound.coordinate.kind == kind
        and (
            kind != "local"
            or (
                r.payload.recipe.bound.coordinate.context,
                r.payload.recipe.bound.coordinate.horizon_s,
            )
            == (request.context, request.horizon_s)
        )
        and (policy != "BASE" or r.payload.recipe.bound.coordinate.pulse in BASE)
        and (
            policy != "FIXED_SEQUENCE"
            or kind != "joint"
            or r.payload.recipe.bound.coordinate.pulse == fixed
        )
    )
    candidates = []
    for report in reports:
        predicted = ClassicalLawEvaluator(
            registration(report.candidate.payload_publication.implementation),
            source,
            causal,
            report.payload,
        ).prediction
        if expected_predictions and predicted != next(
            p for p in expected_predictions if p.recipe_id == report.payload.recipe.recipe_id
        ):
            raise ValueError("initial commitment changes its outcome-blind forecast seal")
        if not predicted.available:
            continue
        candidates.append(
            assess_candidate(
                laws=laws,
                report=report,
                causal=causal,
                request=request,
                policy=policy,
                predicted=predicted,
                source=source,
                publisher=publisher,
                reader=reader,
                session=UndeliverableSession(),
                authority=control.authority,
                resources=control.resources,
                evaluation=use_plan.plan,
            )
        )
    if not candidates:
        return refused("NO_AVAILABLE_CAUSAL_PREDICTION")
    proposal, prepared = rank_and_commit(tuple(candidates), publisher, commit_nonattempt=True)
    assert prepared is not None
    candidate = prepared.candidate
    lock = freeze_forecast_request(
        prefix_id=f"{causal.root}.{policy.lower()}.{request.request_id.lower()}.{kind}.prepared",
        policy_id=f"{policy.lower()}.{request.request_id.lower()}",
        root=causal.root,
        compiled=prepared.compiled,
        commitment=prepared.commitment,
        task=candidate.task,
        audit_forecasts=(),
        checkpoint=checkpoint,
        causal_receipt=causal_receipt,
        causal_artifact=causal_artifact,
        issued_study=control.issued_study,
        evaluation=use_plan.plan,
        store=control.open_prepared_store(),
        occurred_at_utc=(
            control.decision_clock(
                causal.root, f"{policy.lower()}.{request.request_id.lower()}.{kind}"
            )
            if isinstance(causal_receipt, DeliveryControllerTickReceipt)
            else control.freeze_clock(causal.root)
        ),
        causal_link=candidate.link if isinstance(causal_receipt, DeliveryControllerTickReceipt) else None,
    )
    return _science_ClassicalFrozenStage(
        policy,
        request,
        kind,
        causal,
        candidate.context.predicted,
        candidate.context.word,
        prepared.compiled,
        prepared.commitment,
        candidate.task,
        candidate.forecasts,
        proposal,
        lock,
        candidate.link,
        ()
        if prepared.commitment.disposition is not CommitmentDisposition.NONATTEMPT
        else ("OWNED_ADMISSION_NONATTEMPT",),
    )

def freeze_root(
    *,
    laws: ClassicalLaws,
    preparation: ClassicalPreparation,
    seal: ClassicalPredictionSeal,
    plan: ReactorStagedPulseResponseProspectivePlan,
    source: ReactorBatchSource,
    publisher: ControlPublisher,
    reader: CandidatePayloadReader,
    control: Any,
    causal_receipt: CanonicalTaskReceipt,
    causal_artifact: ArtifactIdentity,
) -> _science_ClassicalFrozenRoot:
    parent = ObjectIdentity.from_record(preparation.record_id, preparation)
    if (
        seal.preparation != parent
        or plan.laws != ObjectIdentity.from_record(laws.record_id, laws)
        or causal_artifact.sha256 != preparation.fingerprint()
    ):
        raise ValueError("freeze changes the exact causal preparation or qualified parent")
    publisher = ControlPublicationSession(publisher, maximum_records=8192)
    block = plan.block
    stages = []
    for policy in ARMS if block == "base-menu-comparison" else MENUS if block == "expanded-menu-comparison" else SEQUENCES:
        for request in LOCAL_REQUESTS if block != "staged-sequence-comparison" else PAIR_REQUESTS:
            kind = "local" if block != "staged-sequence-comparison" else "baseline" if policy == "ONE_PULSE" else "first"
            causal = next(
                c
                for c in preparation.contexts
                if c.context == (request.context if kind == "local" else "early")
            )
            stage = freeze_stage(
                laws=laws,
                plan=plan,
                causal=causal,
                policy=policy,
                request=request,
                kind=kind,
                source=source,
                publisher=publisher,
                reader=reader,
                control=control,
                checkpoint=parent,
                causal_artifact=causal_artifact,
                causal_receipt=causal_receipt,
                expected_predictions=seal.predictions,
            )
            stages.append(CanonicalRecordArchive.pack(stage.record_id, stage))
    return _science_ClassicalFrozenRoot(
        preparation.root,
        parent,
        ObjectIdentity.from_record(seal.record_id, seal),
        ObjectIdentity.from_record(plan.record_id, plan),
        tuple(stages),
    )
