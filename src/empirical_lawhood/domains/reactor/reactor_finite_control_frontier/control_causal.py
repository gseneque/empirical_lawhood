"Finite-control frontier binding to the shared native finite-word causal support construction."

from empirical_lawhood.domains.reactor.reactor_prefix_response.finite_support import finite_feed_causal_binding
from empirical_lawhood.science.identity.provenance import EvidenceLink, ObjectIdentity
from empirical_lawhood.design.controller_study import ControllerActionBinding
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.control_plan import FrontierControlContext
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.science import UNIT


def causal_binding(
    context: FrontierControlContext, evidence: tuple[EvidenceLink, ...]
) -> ControllerActionBinding:
    report = context.report
    law = report.qualification.response_law
    if law is None or not report.operands.qualifies or not evidence:
        raise ValueError("word support lacks its independently qualified parent")
    return finite_feed_causal_binding(
        plan=context.plan,
        law=law,
        word=context.word.word,
        native_mapping=ObjectIdentity.from_record(context.word.word.word_id, context.word),
        views=report.family.axis_map.qualification_view_ids,
        unit=UNIT,
        guard_s=120,
        evidence=evidence,
    )
