# SPDX-License-Identifier: MPL-2.0
"""Code-owned retained questions with the complete combined target ancestry."""

from empirical_lawhood.science.identity.authority import AuthorityAction
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry_policy import InquiryOutcomeMap, InquiryQuestionKind, InquiryTarget, RobustInquirySpecification, ScientificOutcomeKind
from empirical_lawhood.domains.rubisco.rubisco_response.adoption import CAPABILITY, adoption_connection, adoption_scope
from empirical_lawhood.domains.rubisco.rubisco_response.adoption_translation import selected_config
from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import selected_configs
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import response_requirement_graph, scientific_scope


def retained_inquiry_specification(draft):
    """Declare a read-only recovery question, without selecting a future policy.

    The shared service authenticates actual products and projects every selected
    attempt and work identity. Remaining scientific requirements are unchanged.
    """
    adopted = draft.selected_operation_ids == (CAPABILITY,)
    if adopted:
        config = selected_config(draft)
        study = config.current_science
        endpoint = adoption_scope(config)
        requirement, connection = adoption_connection(config)
        assessment = draft.operations[0].config_identity
    else:
        configs = selected_configs(draft)
        study = configs["assess"].science
        endpoint = scientific_scope(study)
        assessment = ObjectIdentity.from_record(configs["assess"].config_id, configs["assess"])
    graph = response_requirement_graph(study)
    requirements = graph.requirements + ((requirement,) if adopted else ())
    connections = graph.connections + ((connection,) if adopted else ())
    question_requirement = requirement.requirement_id if adopted else graph.conditional_requirement_id
    target = InquiryTarget("target." + draft.draft_id + ".retained", study.question,
        scientific_scope(study), tuple(sorted({graph.root_requirement_id, question_requirement})),
        tuple(ObjectIdentity.from_record(claim.claim_id, claim) for claim in draft.development_study.claims),
        "Original conditional evidence is retained; the combined milestone needs every declared scientific prerequisite.")
    kinds = (("initial", ScientificOutcomeKind.MISSING),
             ("operational-failure", ScientificOutcomeKind.OPERATIONAL_FAILURE),
             ("scientific-failure", ScientificOutcomeKind.NEGATIVE),
             ("uncertain-contact", ScientificOutcomeKind.UNCERTAIN_CONTACT),
             ("unresolved", ScientificOutcomeKind.UNEVALUABLE),
             ("useful-supply", ScientificOutcomeKind.POSITIVE))
    outcomes = tuple(InquiryOutcomeMap(name, kind, ("hold", "recover") if name == "useful-supply" else ("hold",),
        "Retain the actual conditional finding and complete attempt census; no biological or benefit claim follows.",
        "Exact original completion and remaining requirements; no new acquisition.") for name, kind in kinds)
    return RobustInquirySpecification("inquiry." + draft.draft_id + ".retained",
        "What exact completed conditional work is available for retained use?", (), assessment, endpoint,
        "Replaying a completion, dropping adverse evidence or promoting exposed support changes the scientific question.",
        InquiryQuestionKind.ADOPT if adopted else InquiryQuestionKind.ASSESS, target,
        tuple(sorted(requirements, key=lambda row: row.requirement_id)),
        tuple(sorted(connections, key=lambda row: row.connection_id)), question_requirement, outcomes,
        AuthorityAction.SIMULATION_EXECUTION)
