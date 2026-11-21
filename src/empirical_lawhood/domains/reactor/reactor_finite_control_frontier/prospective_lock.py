"""Native acquisition, external-format translation and custody integration."""

from decimal import Decimal as D
from typing import Any
from empirical_lawhood.methods.control.prepared_forecast import freeze_forecast_request
from empirical_lawhood.methods.law_assessment import CandidatePayloadReader
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.storage.contracts.canonical_record_archive import CanonicalRecordArchive
from empirical_lawhood.methods.control.publication import ControlPublisher, ControlPublicationSession
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.control_owner import assess_candidate, rank_and_commit
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.causal import causal_operands
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.law_terminal import FrontierLaws
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.prospective_plan import ReactorFiniteControlFrontierProspectivePlan
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierPreparation
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.selection import FrontierPredictionSeal, eligible_el_pulses

from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.frozen_records import (
    FrontierFrozenRoot as _science_FrontierFrozenRoot,
    FrontierFrozenUse as _science_FrontierFrozenUse,
    UndeliverableSession as _science_UndeliverableSession,
)

def freeze_root(
    *,
    laws: FrontierLaws,
    preparation: FrontierPreparation,
    seal: FrontierPredictionSeal,
    plan: ReactorFiniteControlFrontierProspectivePlan,
    publisher: ControlPublisher,
    reader: CandidatePayloadReader,
    control: Any,
    causal_receipt: CanonicalTaskReceipt,
    causal_artifact: ArtifactIdentity,
) -> _science_FrontierFrozenRoot:
    parent = ObjectIdentity.from_record(preparation.record_id, preparation)
    if (
        seal.preparation != parent
        or seal.parent_laws != ObjectIdentity.from_record(laws.record_id, laws)
        or any(seal.development != r.payload.development for r in laws.rows)
        or plan.laws != seal.parent_laws
        or causal_artifact.sha256 != preparation.fingerprint()
    ):
        raise ValueError("Controller use lock changed its sealed parent or qualification source")
    publisher = ControlPublicationSession(publisher, maximum_records=4096)
    uses = []
    store = control.open_prepared_store()
    instant = control.freeze_clock(preparation.root)
    for request, expected in seal.primary:
        if expected is None:
            uses.append(
                _science_FrontierFrozenUse(
                    request, None, None, None, None, (), None, None, ("CAUSAL_NONATTEMPT",)
                )
            )
            continue
        ca = next(c for c in preparation.contexts if c.context == request.context)
        bundle = next(p for p in plan.requests if p.request == request).unpack()
        evaluation = bundle.plan
        if evaluation is None or not next(
            yes for r, yes, _ in bundle.assigned if r == preparation.root
        ):
            raise ValueError("admitted causal choice is missing from its prepared census")
        operands = causal_operands(ca, laws.rows[0].payload.prepared_domain)
        eligible = eligible_el_pulses(
            bounds=tuple(r.payload.bound for r in laws.rows),
            context=request.context,
            horizon=request.horizon_s,
            request=request.request_K,
            budget=request.budget_kg,
            observed_temperature=None
            if operands is None
            else D(repr(operands.observation.temperature)),
            masses={p: mass for c, p, mass, _ in seal.masses if c == request.context},
            qualified=laws.qualified,
        )
        if not eligible or eligible[0] != expected:
            raise ValueError("Admission necessary causal filters disagree with the sealed selector")
        candidates = tuple(
            assess_candidate(
                laws=laws,
                report=report,
                causal=ca,
                request=request,
                publisher=publisher,
                reader=reader,
                session=_science_UndeliverableSession(),
                authority=control.authority,
                resources=control.resources,
                evaluation=evaluation,
            )
            for report in laws.rows
            if report.payload.bound.coordinate.context == request.context
            and report.payload.bound.coordinate.horizon_s == request.horizon_s
            and report.payload.bound.coordinate.coordinate_id in laws.qualified
            and report.payload.bound.coordinate.pulse in eligible
        )
        proposal, prepared = rank_and_commit(candidates, publisher)
        if prepared is None or prepared.candidate.context.word.pulse != expected:
            raise ValueError("independent finite admission owners disagree with the sealed causal choice")
        candidate = prepared.candidate
        lock = freeze_forecast_request(
            prefix_id=f"{preparation.root}.{request.request_id}.prepared",
            policy_id=f"el.{request.request_id}",
            root=preparation.root,
            compiled=prepared.compiled,
            commitment=prepared.commitment,
            task=candidate.task,
            audit_forecasts=candidate.forecasts,
            checkpoint=parent,
            causal_receipt=causal_receipt,
            causal_artifact=causal_artifact,
            issued_study=control.issued_study,
            evaluation=evaluation,
            store=store,
            occurred_at_utc=instant,
        )
        uses.append(
            _science_FrontierFrozenUse(
                request,
                candidate.context.word,
                prepared.compiled,
                prepared.commitment,
                candidate.task,
                candidate.forecasts,
                proposal,
                lock,
                (),
            )
        )
    return _science_FrontierFrozenRoot(
        preparation.root,
        parent,
        ObjectIdentity.from_record(seal.record_id, seal),
        ObjectIdentity.from_record(plan.record_id, plan),
        tuple(
            CanonicalRecordArchive.pack(
                f"{preparation.root}.{u.request.request_id}.frozen-use", u
            )
            for u in uses
        ),
    )
