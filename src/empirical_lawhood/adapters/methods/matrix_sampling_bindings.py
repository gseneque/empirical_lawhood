# SPDX-License-Identifier: MPL-2.0
"""Registered follow-on E3/E4 evaluators over retained original evidence.

These operations never replace the closed historical graphs. Parent preparation
reuses current issued-task and prior-execution custody before any protected read.
No source, issue, numerical or sampling authority follows from the input bundle.
"""

from dataclasses import dataclass
from functools import partial
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_adjudication import ProtectedE3SamplingReadout, assess_e3_sampling
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_methods import ProtectedE3Assessment, ProtectedE3FrozenProducts
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import ScheduledFactorialSpecification
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation import (
    ScheduledFactorialConfirmationReadout, ScheduledFactorialSamplingReadout, assess_factorial_sampling,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgramme
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationContext, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner, RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding

from .matrix_sampling_assessment import MatrixSamplingEvidence, MatrixSamplingRequest
from .matrix_source_evidence import MatrixSourcePipelineEvidence


KEYS = {"E3": "matrix-e3-protected.sampling-adjudicate", "E4": "matrix-scheduled-programme.factorial-sampling-adjudicate"}
BUDGET = ResourceBudget(1, None, 0, None, None, None)


def _reference(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class MatrixE3SamplingInputs(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/e3-sampling-inputs"
    record_id: str
    specification: MatrixResponseErrorSpecification
    allocation: UnitAllocation
    assessment: ProtectedE3Assessment
    calibrated_freeze: ProtectedE3FrozenProducts
    model_freeze: ProtectedE3FrozenProducts
    comparison_request: MatrixSamplingRequest
    comparison_evidence: MatrixSamplingEvidence | None
    calibration_requests: tuple[MatrixSamplingRequest, ...] = ()
    calibration_evidence: tuple[MatrixSamplingEvidence | None, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.record_id)
        self.assess()

    def assess(self):
        return assess_e3_sampling(specification=self.specification, allocation=self.allocation, assessment=self.assessment,
            calibrated_freeze=self.calibrated_freeze, model_freeze=self.model_freeze,
            comparison_request=self.comparison_request, comparison_evidence=self.comparison_evidence,
            calibration_requests=self.calibration_requests, calibration_evidence=self.calibration_evidence)

    @property
    def original_products(self):
        return tuple(sorted((_reference(self.assessment), _reference(self.calibrated_freeze), _reference(self.model_freeze)),
            key=lambda value: value.object_id))

    @property
    def unit_ids(self):
        return self.allocation.unit_ids("evaluation")

    @property
    def sampling_pairs(self):
        return ((self.comparison_request, self.comparison_evidence), *zip(self.calibration_requests, self.calibration_evidence, strict=True))


@dataclass(frozen=True, slots=True)
class MatrixE4SamplingInputs(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/e4-sampling-inputs"
    record_id: str
    programme: ScheduledProgramme
    specification: ScheduledFactorialSpecification
    readout: ScheduledFactorialConfirmationReadout
    request: MatrixSamplingRequest
    evidence: MatrixSamplingEvidence | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.readout) is not ScheduledFactorialConfirmationReadout:
            raise TypeError("factorial follow-on requires its actual protected original readout")
        self.readout.__post_init__()
        if (self.readout.programme != self.programme.identity or self.readout.calculation is None
                or self.readout.group_ids != self.programme.group_ids):
            raise ValueError("factorial follow-on requires a complete retained original protected calculation")
        self.assess()

    def assess(self):
        return assess_factorial_sampling(request=self.request, evidence=self.evidence, programme=self.programme,
            specification=self.specification, calculation=self.readout.calculation)

    @property
    def original_products(self):
        return (_reference(self.readout),)

    @property
    def unit_ids(self):
        return self.programme.group_ids

    @property
    def sampling_pairs(self):
        return ((self.request, self.evidence),)


@dataclass(frozen=True, slots=True)
class MatrixSamplingEvidenceCustody(CanonicalRecord):
    """Actual prior issued locators and original publications, never a verdict."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/sampling-evidence-custody"
    record_id: str
    evidence: ObjectIdentity
    qualification_execution: RecursivePriorExecutionBinding
    gate_executions: tuple[RecursivePriorExecutionBinding, ...]
    publications: tuple[tuple[ObjectIdentity, ArtifactWriteResult], ...]
    pipeline: MatrixSourcePipelineEvidence
    pipeline_execution: RecursivePriorExecutionBinding

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.evidence) is not ObjectIdentity or self.evidence.object_schema != MatrixSamplingEvidence.SCHEMA
                or type(self.qualification_execution) is not RecursivePriorExecutionBinding
                or type(self.gate_executions) is not tuple or type(self.publications) is not tuple
                or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not ObjectIdentity
                    for row in self.publications)
                or any(type(value) is not RecursivePriorExecutionBinding for value in self.gate_executions)
                or tuple(value.record.object_id for value in self.gate_executions)
                    != tuple(sorted({value.record.object_id for value in self.gate_executions}))
                or tuple(value.object_id for value, _ in self.publications)
                    != tuple(sorted({value.object_id for value, _ in self.publications}))):
            raise ValueError("sampling custody requires exact unique original source-gate execution and publication locators")
        self.qualification_execution.__post_init__()
        if type(self.pipeline) is not MatrixSourcePipelineEvidence or type(self.pipeline_execution) is not RecursivePriorExecutionBinding:
            raise TypeError("sampling custody requires the actual original qualified/recovered source pipeline")
        self.pipeline.__post_init__()
        self.pipeline_execution.__post_init__()
        for value in self.gate_executions:
            value.__post_init__()
        for reference, publication in self.publications:
            reference.__post_init__()
            if type(publication) is not ArtifactWriteResult:
                raise TypeError("sampling custody requires exact original publication descriptors")
            publication.__post_init__()
            if (reference.object_schema, reference.object_fingerprint) != (
                    publication.logical.payload_schema, publication.logical.content_sha256):
                raise ValueError("sampling custody substitutes an original publication's scientific bytes")


@dataclass(frozen=True, slots=True)
class MatrixSamplingOriginalProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/sampling-original-product"
    prior_execution: RecursivePriorExecutionBinding
    reveal_authority: ObjectIdentity

    def __post_init__(self):
        if (type(self.prior_execution) is not RecursivePriorExecutionBinding or type(self.reveal_authority) is not ObjectIdentity
                or self.reveal_authority.object_schema != "empirical-lawhood/planning/study-operation-authority"):
            raise TypeError("sampling original product requires exact original execution and reveal locators")
        self.prior_execution.__post_init__()
        self.reveal_authority.__post_init__()

    @property
    def issued_study(self):
        return self.prior_execution.issued_study

    @property
    def execution_authority(self):
        return self.prior_execution.execution_authority

    @property
    def record(self):
        return self.prior_execution.record


@dataclass(frozen=True, slots=True)
class MatrixSamplingInvocationCustody(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/sampling-invocation-custody"
    record_id: str
    original_products: tuple[MatrixSamplingOriginalProduct, ...]
    sampling_evidence: tuple[MatrixSamplingEvidenceCustody, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.original_products) is not tuple or type(self.sampling_evidence) is not tuple
                or not self.original_products or any(type(value) is not MatrixSamplingOriginalProduct for value in self.original_products)
                or tuple(value.record.object_id for value in self.original_products)
                    != tuple(sorted({value.record.object_id for value in self.original_products}))
                or any(type(value) is not MatrixSamplingEvidenceCustody for value in self.sampling_evidence)
                or tuple(value.evidence.object_id for value in self.sampling_evidence)
                    != tuple(sorted({value.evidence.object_id for value in self.sampling_evidence}))):
            raise ValueError("sampling invocation loses its exact original-product or evidence custody census")
        for value in (*self.original_products, *self.sampling_evidence):
            value.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixSamplingConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix/sampling-follow-on-config"
    VERSION: ClassVar[str] = "2.0.0"
    config_id: str
    programme: str
    inputs: ObjectIdentity
    custody: ObjectIdentity
    unit_ids: tuple[str, ...]

    def __post_init__(self):
        if (self.programme not in KEYS or type(self.inputs) is not ObjectIdentity or type(self.custody) is not ObjectIdentity
                or self.inputs.object_schema != (MatrixE3SamplingInputs.SCHEMA if self.programme == "E3" else MatrixE4SamplingInputs.SCHEMA)
                or self.custody.object_schema != MatrixSamplingInvocationCustody.SCHEMA
                or self.config_id != "config." + sampling_task_id(self.programme, self.inputs, self.custody)):
            raise ValueError("sampling follow-on config changes its declared scientific inputs or original custody")
        require_sorted_unique_strings(self.unit_ids, field_name="sampling complete independent units", allow_empty=False)


def sampling_task_id(programme, inputs, custody):
    from hashlib import sha256
    from empirical_lawhood.kernel.serialization import canonical_json_bytes

    if programme not in KEYS:
        raise ValueError("sampling follow-on has no selected Matrix programme")
    return KEYS[programme] + "." + sha256(canonical_json_bytes((inputs, custody))).hexdigest()


def sampling_relation_id(config):
    config.__post_init__()
    return "relation." + sampling_task_id(config.programme, config.inputs, config.custody)


def sampling_claim(config, world_id):
    """The sole scientific claim this follow-on evaluator may adjudicate."""
    relation = sampling_relation_id(config)
    comparison = config.programme == "E3"
    return ClaimSpec("claim." + relation, world_id, relation,
        "The fixed E3 whole-root comparison meets its original declared success criterion."
        if comparison else "The seven fixed E4 whole-group contrast tests are assessed within the unchanged twelve-slot family.",
        "Original strict both-baseline/both-view whole-root comparison; no calibration, joint-query coverage or transfer claim."
        if comparison else "Original common-normal whole-group contrasts; five unsupplied cross-phase slots remain unevaluable and three-way interaction descriptive.",
        "unit.matrix-whole-root" if comparison else "unit.matrix-whole-matched-group", None,
        EvidenceCeiling.RESPONSE, OutcomeAccess.EVALUATION_SEALED, VisibilityCeiling.PROSPECTIVE,
        "Scoped retained-result assessment only; source/numerical eligibility, calibration applicability and genuine authority remain separate.",
        ("assumption.matrix-scoped-independent-source-gates",), numerical_view_ids=("fine", "primary"))


def sampling_root_validator(config, context):
    config.__post_init__()
    if (type(context.root) is not StudyDraft or context.root.experiment is None or context.root.system is None
            or context.root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or context.root.experiment.world_id != context.root.system.world.world_id
            or context.root.experiment.relation.relation_id != sampling_relation_id(config)
            or context.root.experiment.claims != (sampling_claim(config, context.root.experiment.world_id),)
            or context.root.experiment.independent_unit_id != sampling_claim(config, context.root.experiment.world_id).physical_independent_unit_id
            or context.node_id != sampling_task_id(config.programme, config.inputs, config.custody)
            or context.stage is not ScientificStage.EVALUATE or context.outcome_access is not OutcomeAccess.EVALUATOR_REVEAL
            or context.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
            or context.unit_ids != config.unit_ids or context.selected_unit_ids != config.unit_ids
            or context.root.evaluation_unit_ids != config.unit_ids or context.complete_unit_census
            or not {config.inputs, config.custody} <= {value.object_identity for value in context.root.design_inputs}):
        raise ValueError("sampling follow-on changes its genuine declared root, complete units or reveal boundary")
    links = tuple(value for value in context.links if value.consumer_node_id == context.node_id)
    if (len(links) != 2 or {value.consumer_input_id for value in links} != {"inputs", "custody"}
            or any(value.producer_node_id is not None or value.external_input_id is None
                or value.scientific_role != "SOURCE" or value.requirement_id is not None or value.connection_id is not None for value in links)):
        raise ValueError("sampling follow-on substitutes its exact retained external input/custody bindings")


class MatrixSamplingWorker:
    def __init__(self, programme, *, prepared_scope=None):
        self.programme = programme
        self.manifest = sampling_declaration(programme).manifest()
        self.prepared_scope = prepared_scope

    def execute(self, context):
        try:
            return self._execute(context)
        finally:
            if type(context) is TaskContext:
                for port in context.input_ports:
                    port.close()

    def _execute(self, context):
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_workers import _read

        if type(context) is not TaskContext or self.prepared_scope is None:
            raise PermissionError("sampling follow-on requires actual parent-side issued/source custody before any input read")
        authority, prepared = context.scientific_adjudication_context, context.prepared_invocation
        if (type(authority) is not ScientificAdjudicationContext or type(prepared) is not PreparedInvocationContract
                or self.prepared_scope != (context.run_id, context.task_id, context.input_materialization_ids, authority.execution_plan)
                or prepared.manifest != self.manifest or prepared.execution_plan != authority.execution_plan or prepared.native_effect
                or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR or authority.plumbing_only
                or authority.fixture_scope_id is not None or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
                or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
                or context.outcome_access is not OutcomeAccess.EVALUATOR_REVEAL or context.permissions != self.manifest.permissions
                or not self.manifest.resource_ceiling.contains(context.resource_budget)):
            raise PermissionError("sampling follow-on loses its actual genuine issued numerical reveal and prepared invocation")
        ports = {port.artifact_id: port for port in context.input_ports}
        contracts = {value.artifact_id: value for value in prepared.inputs}
        config_port = ports.get(context.config.artifact_id)
        if (config_port is None or len(context.input_ports) != 3 or len(ports) != 3
                or len(prepared.inputs) != 3 or set(contracts) != set(ports)
                or any(port.kind is not WorkerInputKind.EXTERNAL for port in context.input_ports)
                or config_port.payload_schema != MatrixSamplingConfig.SCHEMA):
            raise ValueError("sampling follow-on changes its exact config and external input census")
        config = _read(config_port, contracts[config_port.artifact_id], MatrixSamplingConfig)
        if (config.programme != self.programme or context.config.content_sha256 != config.fingerprint()
                or context.config.config_id != config.config_id
                or context.task_id != sampling_task_id(config.programme, config.inputs, config.custody)):
            raise ValueError("sampling follow-on substitutes its actual frozen configuration")
        if authority.relation.object_id != sampling_relation_id(config):
            raise ValueError("sampling follow-on cannot adjudicate a broader calibration, response-use or transfer relation")
        edges = prepared.execution_task_record.scientific_inputs
        if len(edges) != 2 or {edge.consumer_input_id for edge in edges} != {"inputs", "custody"}:
            raise ValueError("sampling follow-on changes its declared complete scientific inputs")
        values = {}
        for edge in edges:
            port = ports[edge.operational_logical_artifact_id]
            kind = MatrixSamplingInvocationCustody if edge.consumer_input_id == "custody" else (
                MatrixE3SamplingInputs if self.programme == "E3" else MatrixE4SamplingInputs)
            if port.payload_schema != kind.SCHEMA or edge.producer_task_id is not None:
                raise ValueError("sampling follow-on substitutes an original scientific input type or producer")
            values[edge.consumer_input_id] = _read(port, contracts[port.artifact_id], kind)
        inputs, custody = values["inputs"], values["custody"]
        if (_reference(inputs) != config.inputs or _reference(custody) != config.custody or inputs.unit_ids != config.unit_ids):
            raise ValueError("sampling follow-on changes its actual retained products, evidence or complete units")
        if (tuple(value.record for value in custody.original_products) != inputs.original_products
                or tuple(value.evidence for value in custody.sampling_evidence) != tuple(sorted(
                    (evidence.identity for _, evidence in inputs.sampling_pairs if evidence is not None), key=lambda value: value.object_id))):
            raise ValueError("sampling follow-on changes its original product or independent evidence custody census")
        product = inputs.assess()
        if self.programme == "E3":
            status = ScientificStatus(product.comparison_status)
            admission = AdmissionStatus.ADMITTED if status is ScientificStatus.SUPPORTED else AdmissionStatus.EMPTY
        else:
            finite = any(scientific != "UNEVALUABLE" for _, _, scientific in product.family_slots)
            status = ScientificStatus.PARTIAL if finite else ScientificStatus.UNEVALUABLE
            admission = AdmissionStatus.PARTIAL if finite else AdmissionStatus.UNEVALUABLE
        if status is ScientificStatus.UNEVALUABLE:
            admission = AdmissionStatus.UNEVALUABLE
        if (len(context.output_ports) != 2 or tuple(value.output_id for value in context.output_ports)
                != (context.task_id + ".adjudication", context.task_id + ".product")):
            raise ValueError("sampling follow-on changes its complete adjudication and scoped result outputs")
        record = ScientificAdjudicationRecord("adjudication." + context.run_id + "." + context.task_id,
            context.run_id, context.task_id, authority.execution_plan, context.input_materialization_ids,
            tuple(sorted(value.logical_artifact_id for value in context.output_ports)), tuple(sorted({
                *context.dependency_receipt_ids, *(value.prior_execution.receipt.object_id for value in custody.original_products),
                *(value.qualification_execution.receipt.object_id for value in custody.sampling_evidence),
                *(value.pipeline_execution.receipt.object_id for value in custody.sampling_evidence),
                *(gate.receipt.object_id for value in custody.sampling_evidence for gate in value.gate_executions)})),
            authority.evidence_world_id, authority.evidence_world_kind, authority.relation, authority.independent_unit_id,
            authority.information_cutoffs, authority.visibility_ceiling, authority.outcome_access,
            AdjudicationEvaluability.UNEVALUABLE if status is ScientificStatus.UNEVALUABLE else AdjudicationEvaluability.EVALUABLE,
            status, admission, product.reason_codes)
        return RunnerResult((TaskOutputPayload(context.task_id + ".adjudication", record.canonical_bytes()),
            TaskOutputPayload(context.task_id + ".product", product.canonical_bytes())),
            (ReceiptCheck("matrix-scoped-sampling-with-original-issued-gate-custody", True, ()),))


def _prepare(supplier, runner):
    return ParentPreparedTaskRunner(runner.manifest, lambda context: supplier.prepare_matrix_sampling(context, runner))


def sampling_declaration(programme):
    if programme not in KEYS:
        raise ValueError("unknown Matrix sampling follow-on programme")
    inputs = MatrixE3SamplingInputs if programme == "E3" else MatrixE4SamplingInputs
    output = ProtectedE3SamplingReadout if programme == "E3" else ScheduledFactorialSamplingReadout
    kinds = (MatrixSamplingConfig, MatrixSamplingInvocationCustody, inputs, output, ScientificAdjudicationRecord)
    return RecursiveOperationDeclaration(KEYS[programme], "2.0.0", KEYS[programme] + ".original-source-gate-scope.v2",
        CapabilityKind.EVALUATOR, MatrixSamplingConfig, ScientificStage.EVALUATE,
        (RecursivePortContract("custody", MatrixSamplingInvocationCustody.SCHEMA, "application/json", None),
         RecursivePortContract("inputs", inputs.SCHEMA, "application/json", None)),
        (OutputTemplate("adjudication", ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
         OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")),
        tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_FROZEN_MODELS, CapabilityPermission.READ_SEALED_OUTCOMES, CapabilityPermission.REVEAL_OUTCOMES))),
        EvidenceCeiling.RESPONSE, OutcomeAccess.EVALUATOR_REVEAL, VisibilityCeiling.OUTCOME_VISIBLE, BUDGET,
        ("exact-named-scientific-premise-and-complete-population", "original-independent-source-gate-and-receipt-custody",
         "separate-comparison-calibration-and-factorial-scope"), partial(MatrixSamplingWorker, programme),
        {kind.SCHEMA: kind for kind in kinds},
        scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda config: config.unit_ids,
            scientific_operand_sha256s=lambda config: tuple(sorted((config.inputs.object_fingerprint, config.custody.object_fingerprint))),
            scientific_root_validator=sampling_root_validator, adjudication_output_id="adjudication"),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.REVEAL, runner_preparation_factory=_prepare),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        input_record_types=tuple(sorted((MatrixSamplingInvocationCustody, inputs), key=lambda kind: (kind.SCHEMA, kind.VERSION))))
