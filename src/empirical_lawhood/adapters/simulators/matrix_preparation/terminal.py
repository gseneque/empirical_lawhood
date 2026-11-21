"""Authenticated publication and finalizer orchestration for supplied domain plans."""
from empirical_lawhood.methods.contracts import CandidateEvaluatorImplementation
from empirical_lawhood.methods.law_assessment import CandidateFamilyAssembler, LawAssessmentAssembler, QualificationProfileEvaluatorRegistry, ResponseLawQualificationService
from empirical_lawhood.methods.qualification_profiles import QualificationProofOwner
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity, NamedDecimal
from empirical_lawhood.execution.candidate_payloads import CandidatePayloadPlane
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import DEVELOPMENT
from empirical_lawhood.domains.matrix.matrix_preparation.data import ProjectedContext
from empirical_lawhood.domains.matrix.matrix_preparation.family import preparation_candidate_evidence
from empirical_lawhood.adapters.simulators.matrix_preparation.fitting import read_fit
from empirical_lawhood.domains.matrix.matrix_preparation.law import LAW_MAXIMUM_BYTES
from empirical_lawhood.domains.matrix.matrix_preparation.records import PreparationAssessmentConfig, PreparationDescriptionReport, PreparationFitReport, PreparationNumericalSemanticsReport
from empirical_lawhood.domains.matrix.matrix_preparation.terminal import PreparationLawReport, prepare_preparation_qualification

def qualify_preparation_description(*, config: PreparationAssessmentConfig, fit: PreparationFitReport, fit_payload: bytes, fit_artifact: ArtifactIdentity, description: PreparationDescriptionReport, description_artifact_id: str, numerical_semantics: PreparationNumericalSemanticsReport, observed: ProjectedContext, payload_plane: CandidatePayloadPlane, profile_owner: QualificationProofOwner, evaluator_implementation: CandidateEvaluatorImplementation, selector_capability: ObjectIdentity, selector_implementation: ObjectIdentity) -> PreparationLawReport:
    groups = read_fit(fit, fit_payload)
    plan = prepare_preparation_qualification(config=config, fit=fit, fit_payload=fit_payload, fit_artifact=fit_artifact, description=description, description_artifact_id=description_artifact_id, numerical_semantics=numerical_semantics, observed=observed, profile_owner=profile_owner, evaluator_implementation=evaluator_implementation, selector_capability=selector_capability, selector_implementation=selector_implementation, groups=groups)
    report_ref, scope, binding, ledger, implementation, decoder, decoders, profile = (plan.report_ref, plan.scope, plan.binding, plan.ledger, plan.implementation, plan.decoder, plan.decoders, plan.profile)
    assembler = LawAssessmentAssembler(payload_plane, decoders, QualificationProfileEvaluatorRegistry((profile,)))
    assessments = []
    for payload, evaluator, metrics in plan.candidates:
        publication = payload_plane.publish_candidate_payload(payload=payload.canonical_bytes(), evaluator=evaluator, implementation=implementation, decoder_schema=decoder.decoder_schema, decoder_version=decoder.decoder_version, maximum_decode_bytes=LAW_MAXIMUM_BYTES)
        supplied = preparation_candidate_evidence(ledger, binding, payload, publication, metrics, (plan.evidence,))
        assessments.append(assembler.assemble(system=config.system, candidate=supplied, qualification_profile=ObjectIdentity.from_record(profile.profile.profile_id, profile.profile), metrics=tuple((NamedDecimal(f'{supplied.candidate_id}.{v.value_id}', v.value, v.unit) for v in metrics))))
    family = CandidateFamilyAssembler().assemble(ledger, tuple(assessments))
    qualification = ResponseLawQualificationService(payload_plane, decoders).qualify(config.system, report_ref, family)
    return PreparationLawReport(f'{DEVELOPMENT}.law.{fit.context}', fit.context, ObjectIdentity.from_record(config.config_id, config), report_ref, scope, binding, family, qualification)
