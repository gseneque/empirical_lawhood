# SPDX-License-Identifier: MPL-2.0
"""Pure actor-only recipe author and separate exact finite-census assessor."""

from empirical_lawhood.design.inquiry_methods import FrozenInquiryProcedure

from empirical_lawhood.methods.assigned_opportunity_assessment.records import NAMESPACE, OpportunityAssessment, OpportunityAuthorInput, finite_enclosure, method, validate_assessment_inputs


def frozen_procedure(config):
    """Reconstruct only the fixed declared recipe, without any outcome or fitting."""
    return FrozenInquiryProcedure(NAMESPACE + ".author.product", config.author, (method("assess"),), config.parameters)


def author(config, actor):
    config.__post_init__()
    if type(actor) is not OpportunityAuthorInput or config.phase != "author":
        raise TypeError("author accepts only its declared actor input")
    actor.__post_init__()
    if (actor.identity != config.author.inputs[0].record or actor.source != config.source
            or actor.availability != config.author.inputs[0].availability
            or actor.requested_threshold != config.parameters[0].value):
        raise ValueError("author substitutes admitted evidence, original source or requested parameters")
    return frozen_procedure(config)


def assess(config, procedure, outcomes):
    config.__post_init__()
    if config.phase != "assess":
        raise ValueError("assessment requires its original assessor operation")
    validate_assessment_inputs(config, procedure, outcomes)
    lo, hi, *_ = finite_enclosure(config.assessment, outcomes.rows)
    return OpportunityAssessment(config.node_id + ".product", config, procedure, outcomes,
                                 (lo.numerator, lo.denominator), (hi.numerator, hi.denominator))
