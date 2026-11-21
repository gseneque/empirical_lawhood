# SPDX-License-Identifier: MPL-2.0
"""Read original response custody and assess retained biological source support."""

from dataclasses import dataclass

from empirical_lawhood.domains.rubisco.rubisco_response.biological_sources import read_exposed_biological_sources
from empirical_lawhood.domains.rubisco.rubisco_response.biological_support import PredictiveSupportAssessment, assess_predictive_support, selection_from_study
from empirical_lawhood.api.domain_composition.rubisco_response.reference import RetainedReferenceAnalysis, read_reference_analysis


@dataclass(frozen=True, slots=True)
class RetainedBiologicalAnalysis:
    reference: RetainedReferenceAnalysis
    biological_support: PredictiveSupportAssessment


def read_biological_analysis(*, directory, information_cutoff, artifact_writer,
                             source_audit=None, nomination_dossier=None, nomination_receipt=None):
    """Use the ordinary original-product and post-outcome access guards; start no work.

    Source inputs, when selected, must be the complete retained audit and its
    original nomination dossier/receipt. Missing inputs remain named gaps.
    """
    inputs = (source_audit, nomination_dossier, nomination_receipt)
    if any(row is not None for row in inputs) and any(row is None for row in inputs):
        raise ValueError("biological source selection needs its complete original audit, nomination and receipt")
    reference = read_reference_analysis(directory=directory, information_cutoff=information_cutoff,
                                        artifact_writer=artifact_writer)
    sources = None if source_audit is None else read_exposed_biological_sources(*inputs,
        evidence_id="biology.sources." + source_audit.fingerprint()[:24])
    selection = selection_from_study(reference.study)
    result = assess_predictive_support(selection, sources,
        assessment_id="biology.assessment." + selection.fingerprint()[:24])
    return RetainedBiologicalAnalysis(reference, result)
