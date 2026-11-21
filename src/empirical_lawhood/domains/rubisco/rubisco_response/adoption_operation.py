# SPDX-License-Identifier: MPL-2.0
"""Bounded retained-input assessor; the shared runtime owns original custody."""

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract, RegisteredProvenanceRequirement
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.numerical_runtime import validate_kinetic_producing_provenance
from empirical_lawhood.domains.rubisco.rubisco_response.adoption import CAPABILITY, CurrentResponseUse, ResponseAdoptionConfig, adoption_assessments, assess_retained_response
from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import BUDGET, MAX_INPUT_BYTES, MEDIA
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment, ResponsePredictions


class ResponseAdoptionRunner:
    def __init__(self):
        self.manifest = operation_declaration().manifest()

    def execute(self, context):
        try:
            kinds = (ResponseAdoptionConfig, ResponsePredictions, ResponseAssessment)
            if (context.task_id != CAPABILITY or context.permissions != self.manifest.permissions
                    or context.resource_budget != BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or len(context.input_ports) != len(kinds)
                    or {port.payload_schema for port in context.input_ports} != {kind.SCHEMA for kind in kinds}):
                raise ValueError("response adoption changes its bounded worker contract")
            ports = {port.payload_schema: port for port in context.input_ports}
            for port in ports.values():
                if (port.kind is not WorkerInputKind.EXTERNAL or port.media_type != MEDIA
                        or port.size_bytes > MAX_INPUT_BYTES or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError("response adoption changes original retained input access or size")

            def read(kind):
                port = ports[kind.SCHEMA]
                raw = port.read(MAX_INPUT_BYTES + 1)
                if len(raw) != port.size_bytes:
                    raise ValueError("response adoption changes complete original input bytes")
                return decode_canonical_bytes(raw, kind, maximum_bytes=MAX_INPUT_BYTES)

            config = read(ResponseAdoptionConfig)
            if (config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256
                    or ports[ResponseAdoptionConfig.SCHEMA].artifact_id != context.config.artifact_id):
                raise ValueError("response adoption substitutes its selected configuration")
            for product in (config.prediction, config.assessment):
                port = ports[product.record.object_schema]
                if port.artifact_id != product.artifact.artifact_id or port.size_bytes != product.artifact.size_bytes:
                    raise ValueError("response adoption substitutes producing artifact ownership")
            result = assess_retained_response(config, read(ResponsePredictions), read(ResponseAssessment),
                                              use_id=CAPABILITY + ".result")
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != CAPABILITY + ".product"
                    or context.output_ports[0].payload_schema != CurrentResponseUse.SCHEMA
                    or context.output_ports[0].media_type != MEDIA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON):
                raise ValueError("response adoption changes its complete output contract")
            raw = result.canonical_bytes()
            if len(raw) > BUDGET.output_bytes:
                raise ValueError("response adoption exceeds its selected output bound")
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, raw),),
                (ReceiptCheck("original-and-current-independent-response-assessment", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration():
    from empirical_lawhood.domains.rubisco.rubisco_response.adoption_translation import describe_contributions, evidence_projector, endpoint_validator, native_effect_slot_ids, next_wave_builder, outcome_projector, record_identity, scientific_operands, scientific_unit_ids, scientific_work, validate_root
    return RecursiveOperationDeclaration(
        capability_key=CAPABILITY, capability_version="1.0.0",
        implementation_id="rubisco-response-original-receipts-and-current-use-assessment-v1",
        kind=CapabilityKind.FALSIFIER, config_record_type=ResponseAdoptionConfig, stage=ScientificStage.FALSIFY,
        input_ports=(RecursivePortContract("assessment", ResponseAssessment.SCHEMA, MEDIA, MAX_INPUT_BYTES),
                     RecursivePortContract("prediction", ResponsePredictions.SCHEMA, MEDIA, MAX_INPUT_BYTES)),
        outputs=(OutputTemplate("product", CurrentResponseUse.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                                  CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("independent-current-criterion-assessment", "original-primary-receipt-closure",
                               "unchanged-paired-evidence-and-exposure", "zero-native-acquisition"),
        runner_factory=ResponseAdoptionRunner,
        record_codecs={kind.SCHEMA: kind for kind in (ResponseAdoptionConfig, CurrentResponseUse, ResponsePredictions, ResponseAssessment)},
        scientific_hooks=RecursiveScientificHooks(assessment_projector=adoption_assessments,
            scientific_operand_sha256s=lambda config: tuple(sorted({row.object_fingerprint for row in scientific_operands(config)})),
            scientific_unit_ids=scientific_unit_ids, native_effect_slot_ids=native_effect_slot_ids,
            scientific_root_validator=validate_root),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions, next_wave_builder=next_wave_builder,
            inquiry_work_projector=scientific_work, inquiry_endpoint_validator=endpoint_validator,
            inquiry_outcome_projector=outcome_projector, inquiry_evidence_projector=evidence_projector,
            inquiry_record_identity=record_identity),
        execution_properties=RecursiveExecutionProperties(native_effect=False),
        provenance_requirements=(RegisteredProvenanceRequirement("rubisco-response.selected-numerical-profile.v1",
                                                                validate_kinetic_producing_provenance),))
