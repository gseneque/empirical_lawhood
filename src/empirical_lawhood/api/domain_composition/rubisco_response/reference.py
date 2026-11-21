# SPDX-License-Identifier: MPL-2.0
"""Authenticated retained reference analysis through the existing lifecycle."""

from dataclasses import dataclass

from empirical_lawhood.domains.rubisco.rubisco_response.adoption import CAPABILITY
from empirical_lawhood.domains.rubisco.rubisco_response.adoption_translation import actual_use
from empirical_lawhood.domains.rubisco.rubisco_response.contributions import actual_products
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.reference_supply import ReferenceCostCensus, ReferenceKineticAssessment, assess_reference_supply, profile_reference_costs
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponsePredictions
from empirical_lawhood.api.recursive_execution import read_recursive_wave
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.api.domain_composition.rubisco_response.inquiry import RetainedResponseInquiry, project_retained_response_inquiry


@dataclass(frozen=True, slots=True)
class RetainedReferenceAnalysis:
    retained_report: dict
    study: RubiscoResponseStudy
    predictions: ResponsePredictions
    producing_receipts: tuple[CanonicalTaskReceipt, ...]
    references: tuple[ReferenceKineticAssessment, ...]
    costs: ReferenceCostCensus
    inquiry: RetainedResponseInquiry


def read_reference_analysis(*, directory, information_cutoff, artifact_writer):
    """Authenticate original/current-use custody, then independently reduce it.

    Completed access uses the ordinary original receipt guards. This function
    authorizes no new work, changes no original criterion and starts no worker.
    It requires the exposed retained lane's actual post-outcome cutoff.
    """
    exact(information_cutoff, InformationCutoff)
    if information_cutoff.phase is not CausalPhase.POST_OUTCOME:
        raise ValueError("retained reference analysis requires its post-outcome cutoff")
    if information_cutoff.clock_id != "clock.rubisco.physical-seconds":
        raise ValueError("retained reference analysis changes the declared physical clock")
    report, products, draft, _ = read_recursive_wave(directory=directory, artifact_writer=artifact_writer, include_products=True)
    if draft.selected_operation_ids == (CAPABILITY,):
        config, use, _, _ = actual_use(draft, products)
        if use is None:
            raise ValueError("current-use reference analysis needs the original completed adoption product")
        study, predictions = config.current_science, use.current_prediction
    else:
        configs, records, _ = actual_products(draft, products)
        if records is None:
            raise ValueError("retained reference analysis needs the complete original prediction/assessment custody")
        study, predictions = configs["assess"].science, records["predict"]
    inquiry = project_retained_response_inquiry(directory=directory, information_cutoff=information_cutoff,
                                               artifact_writer=artifact_writer)
    references = tuple(assess_reference_supply(supply, prediction, decision,
        assessment_id="reference." + prediction.fingerprint()[:24] + "." + decision.fingerprint()[:24])
        for supply, prediction, decision in zip(study.supplies, predictions.predictions, study.decisions, strict=True))
    costs = profile_reference_costs(inquiry.state, census_id="reference.costs." + inquiry.state.fingerprint()[:24])
    return RetainedReferenceAnalysis(report, study, predictions,
        tuple(products["receipts"][key] for key in sorted(products["receipts"])), references, costs, inquiry)
