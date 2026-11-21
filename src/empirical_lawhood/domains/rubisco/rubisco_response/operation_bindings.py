# SPDX-License-Identifier: MPL-2.0
"""Cold operation declarations and bounded workers for paired response studies."""

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import ClassVar

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.models.worlds import WorldKind
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract, RecursiveScientificRootPreparationContext, RegisteredProvenanceRequirement
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_join.numerical_runtime import validate_kinetic_producing_provenance
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import validate_unchanged_sources
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.paired_prediction import source_union
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import response_requirement_graph
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment, ResponsePredictions

NAMESPACE = "rubisco-response"
MEDIA = "application/json"
MAX_INPUT_BYTES = 32 * 1024 * 1024
BUDGET = ResourceBudget(1, 512 * 1024 * 1024, 0, 60, 128 * 1024 * 1024, MAX_INPUT_BYTES)
PHASES = (
    ("predict", (("study", RubiscoResponseStudy),), ResponsePredictions, ScientificStage.TRANSFORM),
    ("assess", (("prediction", ResponsePredictions), ("study", RubiscoResponseStudy)), ResponseAssessment, ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class ResponseOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/operation-config"
    config_id: str
    operation: str
    original_study: ObjectIdentity
    science: RubiscoResponseStudy
    permitted_refinement_id: str | None = None

    def __post_init__(self):
        if self.operation not in {row[0] for row in PHASES} or self.config_id != f"config.{NAMESPACE}.{self.operation}":
            raise ValueError("response configuration changes its registered operation")
        exact(self.original_study, ObjectIdentity)
        exact(self.science, RubiscoResponseStudy)
        if (self.original_study.object_schema != RubiscoResponseStudy.SCHEMA
                or self.original_study.object_version != RubiscoResponseStudy.VERSION
                or self.science.evidence_scope != "EXPOSED_CONDITIONAL"):
            raise ValueError("conditional response configuration changes original source or evidence lane")
        if self.permitted_refinement_id is not None and (
                self.operation != "assess" or self.permitted_refinement_id not in self.science.acceptance.permitted_refinement_ids):
            raise ValueError("response configuration changes the frozen finite refinement menu")


def scientific_operands(config):
    graph = response_requirement_graph(config.science)
    return source_union((config.original_study, config.science.identity, graph.identity,
                         config.science.cases.identity, config.science.acceptance.identity, config.science.allocation.identity),
                        tuple(supply.identity for supply in config.science.supplies))


def scientific_operand_sha256s(config):
    return tuple(sorted({record.object_fingerprint for record in scientific_operands(config)}))


def scientific_unit_ids(config):
    return config.science.allocation.unit_ids()


def native_effect_slot_ids(config):
    exact(config, ResponseOperationConfig)
    return ()


def development_root(config, *, study_id):
    graph = response_requirement_graph(config.science)
    views = tuple(sorted({view for unit in config.science.allocation.units for view in unit.numerical_view_ids}))
    claim = ClaimSpec(graph.connections[0].claim_id, "world.rubisco-response.conditional",
        "population.rubisco-response.exposed-analytical", config.science.question,
        "Complete original exposure groups with nested cases, scenarios and paired points; zero independent biological observations.",
        "unit.original-exposure-group", None, EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Conditional mathematics cannot establish biological calibration or the combined prediction and computational-benefit milestone.",
        ("assumption.rubisco-response.conditional-four-state",), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, claim.proposition, config.science.cases.identity,
        claim.world_id, WorldKind.ANALYTIC_REFERENCE, scientific_unit_ids(config), views, (claim,), scientific_operands(config))


@dataclass(frozen=True, slots=True, eq=False)
class ResponseScientificPreparation:
    batch: RecursiveScientificRootPreparationContext
    node_configs: object


def scientific_root_preparer(batch):
    from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import graph_contracts

    if type(batch) is not RecursiveScientificRootPreparationContext or type(batch.root) is not DevelopmentStudySpec:
        raise TypeError("response preparation requires its exact exposed scientific root")
    configs = tuple(row.record for row in batch.config_inputs)
    if len(configs) != 2 or any(type(config) is not ResponseOperationConfig for config in configs):
        raise ValueError("response root omits a registered producer or independent assessor")
    by_phase = {config.operation: config for config in configs}
    if set(by_phase) != {"predict", "assess"}:
        raise ValueError("response root changes the complete operation census")
    base = by_phase["predict"]
    if (by_phase["assess"].science != base.science
            or by_phase["assess"].original_study != base.original_study):
        raise ValueError("response peers change original evidence or selected science")
    requirements, connections, external, links = graph_contracts(base)
    if (batch.root != development_root(base, study_id=batch.root.study_id)
            or batch.requirements != requirements or batch.connections != connections
            or batch.external_inputs != external or batch.links != links
            or tuple(row.node_id for row in batch.config_inputs) != tuple(sorted(f"{NAMESPACE}.{phase}" for phase in by_phase))):
        raise ValueError("response root changes complete inputs, assessed connection or scientific census")
    if any(units != scientific_unit_ids(base) for units in batch.selected_unit_ids_by_selection.values()):
        raise ValueError("response root changes the complete original analytical unit census")
    return ResponseScientificPreparation(batch, MappingProxyType({row.node_id: row.record for row in batch.config_inputs}))


def scientific_root_validator(config, context):
    prepared = context.scientific_preparation
    if type(prepared) is not ResponseScientificPreparation:
        raise ValueError("response root requires its invocation's shared scientific preparation")
    if (prepared.node_configs.get(context.node_id) is not config
            or context.root is not prepared.batch.root or context.config_inputs is not prepared.batch.config_inputs
            or context.links is not prepared.batch.links or context.external_inputs is not prepared.batch.external_inputs
            or context.requirements is not prepared.batch.requirements or context.connections is not prepared.batch.connections
            or context.node_id != f"{NAMESPACE}.{config.operation}"
            or context.stage is not next(row[3] for row in PHASES if row[0] == config.operation)
            or context.unit_ids != scientific_unit_ids(config) or context.selected_unit_ids != scientific_unit_ids(config)
            or context.complete_unit_census or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("response stage substitutes its original source, unit, access or effect scope")


def project_assessments(record, requirement, connection):
    exact(record, ResponseAssessment)
    if (connection not in record.graph.connections or requirement not in record.graph.requirements
            or requirement.requirement_id != record.graph.conditional_requirement_id):
        raise ValueError("response projection changes the exact independently assessed connection")
    evidence = (ObjectIdentity.from_record(record.assessment_id, record),)
    return tuple(replace(row, assessment_id=row.assessment_id + ".projection", evidence=evidence)
                 for row in record.connection_assessments)


def output_codecs():
    return {record.SCHEMA: record for record in (ResponseOperationConfig, RubiscoResponseStudy,
                                                ResponsePredictions, ResponseAssessment)}


class ResponseRunner:
    def __init__(self, role):
        self.phase = next(row for row in PHASES if row[0] == role)
        self.role = role
        self.manifest = next(row.manifest() for row in operation_declarations() if row.capability_key == f"{NAMESPACE}.{role}")

    def execute(self, context):
        try:
            _, inputs, output_type, _ = self.phase
            types = {ResponseOperationConfig.SCHEMA: ResponseOperationConfig, **{kind.SCHEMA: kind for _, kind in inputs}}
            if (context.task_id != f"{NAMESPACE}.{self.role}" or context.permissions != self.manifest.permissions
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or context.resource_budget != BUDGET
                    or len(context.input_ports) != len(types) or {port.payload_schema for port in context.input_ports} != set(types)):
                raise ValueError("response worker changes its exact typed input, resource or access contract")
            ports = {port.payload_schema: port for port in context.input_ports}
            for schema, port in ports.items():
                origin = WorkerInputKind.DEPENDENCY if schema == ResponsePredictions.SCHEMA else WorkerInputKind.EXTERNAL
                if (port.kind is not origin or port.media_type != MEDIA or port.size_bytes > MAX_INPUT_BYTES
                        or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError("response worker changes bounded input or original access meanings")
                if origin is WorkerInputKind.DEPENDENCY:
                    receipts = tuple(row for row in context.dependency_receipts if port.materialization_id in row.output_materialization_ids)
                    if len(receipts) != 1 or receipts[0].task_id != f"{NAMESPACE}.predict":
                        raise ValueError("response assessor lacks its exact original prediction receipt")
            def read(kind):
                port = ports[kind.SCHEMA]
                raw = port.read(MAX_INPUT_BYTES + 1)
                if len(raw) != port.size_bytes:
                    raise ValueError("response materialization differs from its complete authenticated size")
                return decode_canonical_bytes(raw, kind, maximum_bytes=MAX_INPUT_BYTES)
            config = read(ResponseOperationConfig)
            if (config.operation != self.role or config.config_id != context.config.config_id
                    or config.fingerprint() != context.config.content_sha256
                    or ports[ResponseOperationConfig.SCHEMA].artifact_id != context.config.artifact_id):
                raise ValueError("response worker changes its immutable selected configuration")
            original = read(RubiscoResponseStudy)
            if original.identity != config.original_study:
                raise ValueError("response worker substitutes original source bytes")
            validate_unchanged_sources(original, config.science)
            if self.role == "predict":
                from empirical_lawhood.domains.rubisco.rubisco_response.study_science import predict_response_study
                product = predict_response_study(config.science, prediction_id=f"{NAMESPACE}.predict.result")
            else:
                from empirical_lawhood.domains.rubisco.rubisco_response.study_science import assess_response_study
                product = assess_response_study(config.science, read(ResponsePredictions),
                    assessment_id=f"{NAMESPACE}.assess.result", permitted_refinement_id=config.permitted_refinement_id)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != f"{context.task_id}.product"
                    or context.output_ports[0].payload_schema != output_type.SCHEMA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                    or context.output_ports[0].media_type != MEDIA):
                raise ValueError("response worker changes its complete output contract")
            raw = product.canonical_bytes()
            if len(raw) > BUDGET.output_bytes:
                raise ValueError("response output exceeds its declared bounded custody")
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, raw),),
                (ReceiptCheck("complete-conditional-paired-response", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations():
    from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import scientific_work
    from empirical_lawhood.domains.rubisco.rubisco_response.contributions import describe_response_contributions, inquiry_endpoint_validator, inquiry_evidence_projector, inquiry_outcome_projector, inquiry_record_identity, next_wave_builder
    return tuple(RecursiveOperationDeclaration(
        capability_key=f"{NAMESPACE}.{role}", capability_version="1.0.0",
        implementation_id=f"{NAMESPACE}.{role}.complete-source-bound-joint-response-v1",
        kind=CapabilityKind.ANALYSIS if role == "predict" else CapabilityKind.FALSIFIER,
        config_record_type=ResponseOperationConfig, stage=stage,
        input_ports=tuple(RecursivePortContract(name, kind.SCHEMA, MEDIA, MAX_INPUT_BYTES) for name, kind in inputs),
        outputs=(OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json"),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
                                  CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("complete-case-and-scenario-census", "independent-four-state-assessment",
                               "nonempty-joint-support", "original-source-binding"),
        runner_factory=lambda phase=role: ResponseRunner(phase), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_assessments if role == "assess" else None,
            scientific_operand_sha256s=scientific_operand_sha256s, scientific_unit_ids=scientific_unit_ids,
            native_effect_slot_ids=native_effect_slot_ids, scientific_root_preparer=scientific_root_preparer,
            scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_response_contributions,
            inquiry_work_projector=scientific_work, next_wave_builder=next_wave_builder,
            inquiry_outcome_projector=inquiry_outcome_projector, inquiry_evidence_projector=inquiry_evidence_projector,
            inquiry_endpoint_validator=inquiry_endpoint_validator, inquiry_record_identity=inquiry_record_identity),
        execution_properties=RecursiveExecutionProperties(native_effect=False),
        provenance_requirements=(RegisteredProvenanceRequirement(
            "rubisco-response.selected-numerical-profile.v1", validate_kinetic_producing_provenance),))
        for role, inputs, output, stage in PHASES)


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())
