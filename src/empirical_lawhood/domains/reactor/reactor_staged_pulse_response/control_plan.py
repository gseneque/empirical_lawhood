"One supported local relation at a time enters the existing admission owners."

from dataclasses import dataclass, replace
from decimal import Decimal as D
from functools import lru_cache

from empirical_lawhood.methods.control.finite_gates import bounded_response_gate
from empirical_lawhood.methods.control.local_law_basis import qualified_local_basis
from empirical_lawhood.methods.geometry.services import AdmissionReceiptPlanValidator
from empirical_lawhood.methods.contracts import LawQualificationBatch
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.causal import causal_operands
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_words import CHART
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.native_words import PulseProjection, project_pulse
from empirical_lawhood.domains.reactor.reactor_causal_response.delivery_words import coordinate
from empirical_lawhood.science.response.action_contracts import ActionDeliveryStage
from empirical_lawhood.science.evidence.admission import AdmissionGateKind
from empirical_lawhood.science.response.causal_contracts import ReceiverInterval
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.models.models import ModelSetSpec
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import NamedDecimal
from empirical_lawhood.science.records.status import ScientificStatus
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.design.evidence_geometry import ReceiptAdmissionActionFibre, ReceiptAdmissionPlannedCoordinate, ReceiptAdmissionReceiptProductionPlan, ReceiptAdmissionSupportCell
from empirical_lawhood.design.finite_action_support import support_map_for_plan
from empirical_lawhood.design.geometry import BatchAtlasAssemblyResult
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import Request
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.control_records import ClassicalReadout
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.law_terminal import ClassicalLaw, ClassicalLaws
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.prediction import HORIZON, ClassicalPredictedBound
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.records import ClassicalContext
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.science import staged_pulse_reactor_system


@lru_cache(maxsize=113)
def control_basis(
    report: ClassicalLaw,
) -> tuple[LawQualificationBatch, BatchAtlasAssemblyResult, ModelSetSpec]:
    if (
        report.qualification.scientific_status is not ScientificStatus.SUPPORTED
        or report.qualification.response_law is None
    ):
        raise ValueError("Admission requires this exact individually supported response relation")
    return qualified_local_basis(
        system=staged_pulse_reactor_system(report.payload.recipe.bound.coordinate),
        qualification=report.qualification,
        axis=report.family.axis_map.bindings[0],
        stem=report.payload.stem,
        scope_description="One finite action under its qualified causal history and explicit raw/saturated receiver map.",
        nontransport_description="Other actions, histories, guard windows and methods are separate relations, not alternative models of this action.",
    )


@dataclass(frozen=True)
class ClassicalControlContext:
    report: ClassicalLaw
    causal: ClassicalContext
    request: Request
    policy: str
    predicted: ClassicalPredictedBound
    word: PulseProjection
    plan: ReceiptAdmissionReceiptProductionPlan
    readout: ClassicalReadout


def control_context(
    *,
    laws: ClassicalLaws,
    report: ClassicalLaw,
    causal: ClassicalContext,
    request: Request,
    policy: str,
    predicted: ClassicalPredictedBound,
    producer: ObjectIdentity,
    resource: ObjectIdentity,
    authority: ObjectIdentity,
) -> ClassicalControlContext:
    c = report.payload.recipe.bound.coordinate
    inputs = causal_operands(causal, report.payload.prepared_domain)
    if (
        report not in laws.rows
        or predicted.recipe_id != report.payload.recipe.recipe_id
        or predicted.causal != ObjectIdentity.from_record(causal.record_id, causal)
        or inputs is None
        or causal.context != c.context
        or not predicted.available
    ):
        raise ValueError("Admission lacks the exact qualified causal history or prediction")
    if c.kind == "joint" and causal.predecessor is None:
        raise ValueError("second admission decision lacks its actual first owner receipt")
    batch, atlas, models = control_basis(report)
    law = report.qualification.response_law
    assert law is not None and causal.callback is not None
    stem = f"{causal.root}.{policy.lower()}.{request.request_id.lower()}.{c.kind}.{c.pulse.word_id}"
    readout = ClassicalReadout(
        policy, request, c.kind, ObjectIdentity.from_record(laws.record_id, laws)
    )
    primary = "c2" if c.kind == "joint" else "c1" if c.kind in ("first", "baseline") else "c"
    word = project_pulse(
        inputs.observation,
        inputs.previous,
        c.pulse,
        decision_id=stem,
        history_id=causal.record_id,
        horizon_id=HORIZON,
        guard_s=readout.guard_s,
        receiver_id=primary,
    )
    fibre = ReceiptAdmissionActionFibre(
        f"{stem}.action",
        word.word,
        tuple(o.occurrence_id for o in word.word.occurrences),
        tuple(ActionDeliveryStage),
    )
    member = models.members[0]
    cell = ReceiptAdmissionSupportCell(CHART, CHART, CHART, (word.word.word_id,))
    planned = ReceiptAdmissionPlannedCoordinate(
        f"{stem}.coordinate",
        ObjectIdentity.from_record(member.binding_id, member),
        member.response_law,
        member.qualification_result,
        member.denominator_member_id,
        member.candidate_version_ids[0],
        member.qualification_view_ids,
        ObjectIdentity.from_record(fibre.action_binding_id, fibre),
        ObjectIdentity.from_record(cell.cell_id, cell),
    )
    time = D(causal.callback * 10)
    target = request.second_K if c.kind == "joint" else request.required_K
    assert target is not None
    gates = tuple(
        sorted(
            (
                bounded_response_gate(
                    stem=stem,
                    kind=kind,
                    response_receiver=primary,
                    response_minimum=NamedDecimal("response-minimum", target, "K"),
                    safety_receiver="s",
                    safety_maximum=NamedDecimal("safety-maximum", D("356.2"), "K"),
                    protected_interval=ReceiverInterval(
                        coordinate(time), coordinate(time + readout.guard_s)
                    ),
                    evaluator=law.evaluator,
                )
                for kind in AdmissionGateKind
            ),
            key=lambda g: g.predicate_id,
        )
    )
    system = staged_pulse_reactor_system(c)
    plan = ReceiptAdmissionReceiptProductionPlan(
        f"{stem}.admission",
        atlas.atlas,
        ObjectIdentity.from_record(batch.batch_id, batch),
        models,
        member.denominator_member_id,
        (fibre,),
        (cell,),
        (planned,),
        gates,
        f"{stem}.initial",
        law.relation.horizon,
        (f"{stem}.constraint.reachability",),
        producer,
        producer,
        producer,
        resource,
        resource,
        resource,
        ObjectIdentity.from_record(system.world.world_id, system.world),
        InformationCutoff(f"{stem}.preaction", "reactor-clock", CausalPhase.PRE_ACTION, time),
        OutcomeAccess.OUTCOME_BLIND,
        authority,
        EvidenceCeiling.ADMISSION,
        VisibilityCeiling.PROSPECTIVE,
    )
    plan = replace(
        plan, model_set=replace(models, extensions=(support_map_for_plan(plan).extension,))
    )
    AdmissionReceiptPlanValidator.validate(batch=batch, plan=plan)
    return ClassicalControlContext(
        report, causal, request, policy, predicted, word, plan, readout
    )
