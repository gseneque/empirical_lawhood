# SPDX-License-Identifier: MPL-2.0
"""Distinct current-use assessment of original receipted paired predictions."""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, AssessmentPhase, ConditionRole, ContributionRole, RequirementSupplyAssessment, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import validate_unchanged_sources
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import scientific_scope
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment, ResponsePredictions, assess_response_study

CAPABILITY = "rubisco-response.adopt"


def identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


@dataclass(frozen=True, slots=True)
class ResponseAdoptionConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/adoption-config"
    config_id: str
    original_science: RubiscoResponseStudy
    current_science: RubiscoResponseStudy
    parent: ContributionManifest
    prediction: ContributionProduct
    assessment: ContributionProduct
    original_refinement_id: str | None = None
    current_refinement_id: str | None = None

    def __post_init__(self):
        if self.config_id != "config." + CAPABILITY:
            raise ValueError("response adoption changes its installed configuration")
        validate_unchanged_sources(self.original_science, self.current_science)
        if (self.original_science.evidence_scope != "EXPOSED_CONDITIONAL"
                or self.current_science.evidence_scope != "EXPOSED_CONDITIONAL"):
            raise ValueError("retained exposed results cannot become prospective evidence")
        exact(self.parent, ContributionManifest)
        if self.parent.scope != scientific_scope(self.original_science):
            raise ValueError("response adoption changes the original contribution's scientific scope")
        for product, kind, role in (
            (self.prediction, ResponsePredictions, ContributionRole.INSTANCE_PRODUCT),
            (self.assessment, ResponseAssessment, ContributionRole.RETAINED_ANALYSIS_INPUT),
        ):
            exact(product, ContributionProduct)
            if (product not in self.parent.products or product.record.object_schema != kind.SCHEMA
                    or product.record.object_version != kind.VERSION or product.role is not role
                    or product.producing_receipt.object_schema != CanonicalTaskReceipt.SCHEMA
                    or product.producing_receipt.object_version != CanonicalTaskReceipt.VERSION
                    or product.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                    or product.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or product.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                raise ValueError("response adoption changes its exact original product, receipt or exposure")
        if (set(self.parent.products) != {self.prediction, self.assessment}
                or self.prediction.producing_receipt == self.assessment.producing_receipt
                or self.assessment.record not in self.parent.assessments):
            raise ValueError("response adoption needs both separately receipted original products")
        for science, refinement in ((self.original_science, self.original_refinement_id),
                                     (self.current_science, self.current_refinement_id)):
            if refinement is not None and refinement not in science.acceptance.permitted_refinement_ids:
                raise ValueError("response adoption substitutes a finite refinement selection")


def adoption_scope(config):
    return replace(scientific_scope(config.current_science), receiver_id=CAPABILITY,
                   source_config_sha256=config.fingerprint())


def adoption_connection(config):
    requirement = ScientificRequirementSpec(
        "requirement." + config.current_science.study_id + ".retained-use", CAPABILITY, ConditionRole.EVIDENTIAL,
        "Use complete original paired predictions under explicitly selected current criteria",
        "Original receipt-backed paired outcomes retain their exact source, exposure and complete denominator; current use is independently assessed.",
        adoption_scope(config), CAPABILITY,
        "A retained source, original outcome, current criterion or independent assessment is substituted.",
        (ContributionRole.INSTANCE_PRODUCT,))
    connection = ScientificConnectionSpec(
        "connection." + config.current_science.study_id + ".retained-use", requirement.requirement_id,
        None, None, "prediction", CAPABILITY, "claim." + CAPABILITY + "." + config.fingerprint(),
        ContributionRole.INSTANCE_PRODUCT, requirement.falsifier,
        identity(config.parent, "contribution_id"), config.prediction.product_id, "external." + CAPABILITY + ".prediction")
    return requirement, connection


@dataclass(frozen=True, slots=True)
class CurrentResponseUse(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/current-response-use"
    use_id: str
    configuration: ResponseAdoptionConfig
    original_prediction: ResponsePredictions
    original_assessment: ResponseAssessment
    current_prediction: ResponsePredictions
    current_assessment: ResponseAssessment
    new_native_acquisitions: int = 0
    fresh_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.use_id)
        exact(self.configuration, ResponseAdoptionConfig)
        for value, kind in ((self.original_prediction, ResponsePredictions), (self.original_assessment, ResponseAssessment),
                            (self.current_prediction, ResponsePredictions), (self.current_assessment, ResponseAssessment)):
            exact(value, kind)
        config = self.configuration
        if (self.original_prediction.identity != config.prediction.record
                or identity(self.original_assessment, "assessment_id") != config.assessment.record
                or self.original_prediction.study != config.original_science.identity
                or self.original_assessment.study != config.original_science.identity
                or self.original_assessment.predictions != self.original_prediction.identity):
            raise ValueError("current use substitutes an original scientific product")
        if (self.current_prediction.study != config.current_science.identity
                or self.current_prediction.predictions != self.original_prediction.predictions
                or self.current_prediction.prediction_id != self.use_id + ".prediction"
                or self.current_assessment.study != config.current_science.identity
                or self.current_assessment.predictions != self.current_prediction.identity
                or self.current_assessment.assessment_id != self.use_id + ".assessment"):
            raise ValueError("current use changes retained paired records or its distinct current assessment")
        original_expected = assess_response_study(config.original_science, self.original_prediction,
            assessment_id=self.original_assessment.assessment_id, permitted_refinement_id=config.original_refinement_id)
        current_expected = assess_response_study(config.current_science, self.current_prediction,
            assessment_id=self.current_assessment.assessment_id, permitted_refinement_id=config.current_refinement_id)
        if self.original_assessment != original_expected or self.current_assessment != current_expected:
            raise ValueError("current use changes an independent original or current scientific assessment")
        if (type(self.new_native_acquisitions) is not int or self.new_native_acquisitions != 0
                or type(self.fresh_independent_units) is not int or self.fresh_independent_units != 0):
            raise ValueError("current use cannot manufacture acquisition or independent units")

    @property
    def identity(self):
        return identity(self, "use_id")


def assess_retained_response(config, prediction, assessment, *, use_id):
    """Recheck original and current meaning independently; never call a producer."""
    exact(config, ResponseAdoptionConfig)
    exact(prediction, ResponsePredictions)
    exact(assessment, ResponseAssessment)
    if prediction.identity != config.prediction.record or identity(assessment, "assessment_id") != config.assessment.record:
        raise ValueError("response adoption substitutes exact original output bytes")
    original_expected = assess_response_study(config.original_science, prediction,
        assessment_id=assessment.assessment_id, permitted_refinement_id=config.original_refinement_id)
    if assessment != original_expected:
        raise ValueError("response adoption fails independent original-product assessment")
    current_prediction = ResponsePredictions(use_id + ".prediction", config.current_science.identity, prediction.predictions)
    current_assessment = assess_response_study(config.current_science, current_prediction,
        assessment_id=use_id + ".assessment", permitted_refinement_id=config.current_refinement_id)
    return CurrentResponseUse(use_id, config, prediction, assessment, current_prediction, current_assessment)


def adoption_assessments(record, requirement, connection):
    exact(record, CurrentResponseUse)
    if (requirement, connection) != adoption_connection(record.configuration):
        raise ValueError("current-use projection substitutes its exact assessed connection")
    current = record.current_assessment
    valid = (current.complete_case_census and all(row.disposition is AssessmentDisposition.SATISFIED
                                                for row in current.connection_assessments))
    return tuple(RequirementSupplyAssessment(record.use_id + ".connection." + phase.value.lower(),
        identity(requirement, "requirement_id"), identity(connection, "connection_id"), phase,
        AssessmentDisposition.SATISFIED if valid or phase is AssessmentPhase.PROCEDURE else AssessmentDisposition.FALSIFIED,
        record.configuration.current_science.study_id, (record.identity,),
        () if valid or phase is AssessmentPhase.PROCEDURE else ("RETAINED_CURRENT_USE_FAILED",))
        for phase in (AssessmentPhase.PROCEDURE, AssessmentPhase.INSTANCE, AssessmentPhase.ADMISSION, AssessmentPhase.JOINED))
