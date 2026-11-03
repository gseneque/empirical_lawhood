"""Versioned nonauthoritative projection for candidate/final graph drift checks."""

from __future__ import annotations

from empirical_lawhood.kernel.retrospective_prediction_experiments import RetrospectiveExperimentSpec
from empirical_lawhood.planning.study_authoring import RetrospectiveDesignOrigin

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.experiments import ExperimentSpec
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_ids,
    validate_sha256,
    validate_stable_id,
)
from empirical_lawhood.planning.study_authoring import CapabilitySelection, DesignOrigin, SourceMaterializationRef

from .candidate_compiler import CandidateScientificGraph, FrozenConditionalChild, ObligationCoverage, DraftStudyCandidate, StudyCandidate, ExecutableStudyCandidate
from .capabilities import CapabilityRegistry
from .execution_envelope import validate_optional_jit_identities
from .plans import ProtocolExecutionPlan, CandidateExecutionPlan, EnvelopeExecutionPlan, ExecutionPlan, ExecutionTask, ProtocolTemplate, ProtocolRunPlan, RunPlanStep, CandidateRunPlan, EnvelopeRunPlan, RunPlan


@dataclass(frozen=True, slots=True)
class NormalizedScientificGraphProjection(CanonicalRecord):
    """Exact section-4.1.1 science with derived operational IDs excluded."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/normalized-scientific-graph-projection'

    projection_id: str
    system: ObjectIdentity
    candidate_experiment: ExperimentSpec
    campaign: ObjectIdentity
    protocol: ProtocolTemplate
    scientific_graph: CandidateScientificGraph
    obligation_coverage: ObligationCoverage
    design_origin: DesignOrigin
    capability_locks: tuple[CapabilitySelection, ...]
    source_locks: tuple[SourceMaterializationRef, ...]
    source_qualification_receipts: tuple[ObjectIdentity, ...]
    conditional_successor: FrozenConditionalChild | None

    def __post_init__(self) -> None:
        if not isinstance(self, RetrospectiveGraphProjection):
            if type(self.candidate_experiment) is not ExperimentSpec:
                raise ValueError(
                    "NormalizedScientificGraphProjection requires its original candidate_experiment schema"
                )
            if type(self.design_origin) is not DesignOrigin:
                raise ValueError(
                    "NormalizedScientificGraphProjection requires its original design_origin schema"
                )
        validate_stable_id(self.projection_id, field_name="projection_id")
        require_sorted_unique_ids(
            self.capability_locks,
            attribute="selection_id",
            field_name="capability_locks",
        )
        require_sorted_unique_ids(
            self.source_locks,
            attribute="source_id",
            field_name="source_locks",
        )
        require_sorted_unique_ids(
            self.source_qualification_receipts,
            attribute="object_id",
            field_name="source_qualification_receipts",
        )


@dataclass(frozen=True, slots=True)
class ScientificGraphPreservationReceipt(CanonicalRecord):
    """Proof that one authorized lowering retained the issued science exactly."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/scientific-graph-preservation-receipt'

    receipt_id: str
    candidate: ObjectIdentity
    issue_manifest: ObjectIdentity
    package: ObjectIdentity
    scientific_approval: ObjectIdentity
    execution_authority: ObjectIdentity
    run_plan: ObjectIdentity
    execution_plan: ObjectIdentity
    projection: NormalizedScientificGraphProjection
    candidate_projection_sha256: str
    run_plan_projection_sha256: str
    execution_plan_projection_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self, RetrospectiveGraphParity):
            if type(self.projection) is not NormalizedScientificGraphProjection:
                raise ValueError(
                    "ScientificGraphPreservationReceipt requires its original projection schema"
                )
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        for name, value in (
            ("candidate_projection_sha256", self.candidate_projection_sha256),
            ("run_plan_projection_sha256", self.run_plan_projection_sha256),
            ("execution_plan_projection_sha256", self.execution_plan_projection_sha256),
        ):
            validate_sha256(value, field_name=name)
        expected = self.projection.fingerprint()
        if (
            self.candidate_projection_sha256,
            self.run_plan_projection_sha256,
            self.execution_plan_projection_sha256,
        ) != (expected, expected, expected):
            raise ValueError("candidate, run and execution scientific projections drifted")


@dataclass(frozen=True, slots=True)
class EnvelopeGraphPreservationReceipt(CanonicalRecord):
    "Scientific graph preservation proof plus exact extension/envelope identity continuity."

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/envelope-graph-preservation-receipt'

    receipt_id: str
    base: ScientificGraphPreservationReceipt
    issued_extension_set: ObjectIdentity
    execution_envelope_spec: ObjectIdentity

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if (
            self.issued_extension_set.object_schema
            != 'empirical-lawhood/runtime/issued-extension-set'
            or self.execution_envelope_spec.object_schema
            != 'empirical-lawhood/runtime/execution-envelope-spec'
        ):
            raise ValueError("envelope preservation receipt extension/envelope identity is incompatible")


@dataclass(frozen=True, slots=True)
class ResourceGraphPreservationReceipt(CanonicalRecord):
    "Scientific graph preservation plus deadline-free resource/JIT continuity."

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/resource-graph-preservation-receipt'

    receipt_id: str
    base: ScientificGraphPreservationReceipt
    issued_extension_set: ObjectIdentity
    execution_resource_envelope_spec: ObjectIdentity
    predevelopment_jit_signature_census: ObjectIdentity | None
    jit_graph_signature_manifest: ObjectIdentity | None

    def __post_init__(self) -> None:
        if not isinstance(self, RetrospectiveEnvelopeGraphParity):
            if type(self.base) is not ScientificGraphPreservationReceipt:
                raise ValueError("ResourceGraphPreservationReceipt requires its original base schema")
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        expected = (
            'empirical-lawhood/runtime/issued-extension-set',
            'empirical-lawhood/runtime/execution-resource-envelope-spec',
        )
        observed = (
            self.issued_extension_set.object_schema,
            self.execution_resource_envelope_spec.object_schema,
        )
        if observed != expected:
            raise ValueError("resource preservation receipt resource identity is incompatible")
        validate_optional_jit_identities(
            self.predevelopment_jit_signature_census, self.jit_graph_signature_manifest
        )


def normalized_candidate_projection(
    candidate: (DraftStudyCandidate | StudyCandidate | ExecutableStudyCandidate),
) -> NormalizedScientificGraphProjection:
    candidate_root = candidate
    candidate = (
        candidate.base_candidate.base_candidate
        if isinstance(candidate, ExecutableStudyCandidate)
        else candidate.base_candidate
        if isinstance(candidate, StudyCandidate)
        else candidate
    )
    record_type_normalizedscientificgraphprojection: type[NormalizedScientificGraphProjection] = (
        RetrospectiveGraphProjection
        if isinstance(candidate.experiment, RetrospectiveExperimentSpec)
        else NormalizedScientificGraphProjection
    )
    return record_type_normalizedscientificgraphprojection(
        projection_id=f"scientific-graph.{candidate_root.candidate_id}",
        system=ObjectIdentity.from_record(candidate.system.system_id, candidate.system),
        candidate_experiment=candidate.experiment,
        campaign=ObjectIdentity.from_record(
            candidate.campaign.campaign_id,
            candidate.campaign,
        ),
        protocol=candidate.protocol,
        scientific_graph=candidate.scientific_graph,
        obligation_coverage=candidate.obligation_coverage,
        design_origin=candidate.design_origin,
        capability_locks=candidate.capability_locks,
        source_locks=candidate.source_locks,
        source_qualification_receipts=candidate.source_qualification_receipts,
        conditional_successor=candidate.conditional_successor,
    )


def prove_scientific_graph_parity(
    *,
    candidate: (DraftStudyCandidate | StudyCandidate | ExecutableStudyCandidate),
    issued_candidate: (
        DraftStudyCandidate | StudyCandidate | ExecutableStudyCandidate
    ),
    authorized_experiment: ExperimentSpec,
    scientific_approval: ObjectIdentity,
    issue_manifest: ObjectIdentity,
    package: ObjectIdentity,
    execution_authority: ObjectIdentity,
    run_plan: ProtocolRunPlan,
    execution_plan: ProtocolExecutionPlan,
    registry: CapabilityRegistry,
) -> ScientificGraphPreservationReceipt | EnvelopeGraphPreservationReceipt | ResourceGraphPreservationReceipt:
    """Validate actual plan fields, then bind the identical normalized view."""

    if candidate != issued_candidate:
        raise ValueError("candidate differs from the externally issued candidate")
    candidate_identity = ObjectIdentity.from_record(
        candidate.candidate_id,
        candidate,
    )
    if (
        not isinstance(run_plan, CandidateRunPlan)
        or not isinstance(execution_plan, CandidateExecutionPlan)
        or run_plan.candidate != candidate_identity
        or execution_plan.candidate != candidate_identity
    ):
        raise ValueError("authorized plans lack the exact issued candidate binding")
    has_deadline_bearing_extension_plans = isinstance(run_plan, EnvelopeRunPlan) or isinstance(
        execution_plan, EnvelopeExecutionPlan
    )
    has_deadline_free_extension_plans = isinstance(run_plan, RunPlan) or isinstance(
        execution_plan, ExecutionPlan
    )
    if has_deadline_bearing_extension_plans and has_deadline_free_extension_plans:
        raise ValueError("scientific graph comparison mixes deadline-bearing and deadline-free plans")
    if has_deadline_bearing_extension_plans and not (
        isinstance(run_plan, EnvelopeRunPlan)
        and isinstance(execution_plan, EnvelopeExecutionPlan)
        and run_plan.issued_extension_set == execution_plan.issued_extension_set
        and run_plan.execution_envelope_spec == execution_plan.execution_envelope_spec
    ):
        raise ValueError("extension-bound plans differ on extension/envelope identity")
    if has_deadline_free_extension_plans and not (
        isinstance(run_plan, RunPlan)
        and isinstance(execution_plan, ExecutionPlan)
        and run_plan.issued_extension_set == execution_plan.issued_extension_set
        and run_plan.execution_resource_envelope_spec
        == execution_plan.execution_resource_envelope_spec
        and run_plan.predevelopment_jit_signature_census
        == execution_plan.predevelopment_jit_signature_census
        and run_plan.jit_graph_signature_manifest == execution_plan.jit_graph_signature_manifest
    ):
        raise ValueError("deadline-free plans differ on resource/JIT identity")
    has_extension_plans = has_deadline_bearing_extension_plans or has_deadline_free_extension_plans
    if isinstance(candidate, ExecutableStudyCandidate) != has_extension_plans:
        raise ValueError("candidate and plan executable-extension topology differs")
    base_candidate = (
        candidate.base_candidate.base_candidate
        if isinstance(candidate, ExecutableStudyCandidate)
        else candidate.base_candidate
        if isinstance(candidate, StudyCandidate)
        else candidate
    )
    projection = normalized_candidate_projection(candidate)
    _validate_run_plan(
        candidate=base_candidate,
        authorized_experiment=authorized_experiment,
        scientific_approval=scientific_approval,
        run_plan=run_plan,
        registry=registry,
    )
    _validate_execution_plan(
        run_plan=run_plan,
        execution_plan=execution_plan,
        registry=registry,
    )
    projection_sha256 = projection.fingerprint()
    record_type_scientificgraphparityreceipt: type[ScientificGraphPreservationReceipt] = (
        RetrospectiveGraphParity
        if isinstance(projection, RetrospectiveGraphProjection)
        else ScientificGraphPreservationReceipt
    )
    base_receipt = record_type_scientificgraphparityreceipt(
        receipt_id=f"scientific-graph-parity.{run_plan.run_plan_id}",
        candidate=candidate_identity,
        issue_manifest=issue_manifest,
        package=package,
        scientific_approval=scientific_approval,
        execution_authority=execution_authority,
        run_plan=ObjectIdentity.from_record(run_plan.run_plan_id, run_plan),
        execution_plan=ObjectIdentity.from_record(
            execution_plan.execution_plan_id,
            execution_plan,
        ),
        projection=projection,
        candidate_projection_sha256=projection_sha256,
        run_plan_projection_sha256=projection_sha256,
        execution_plan_projection_sha256=projection_sha256,
    )
    if isinstance(run_plan, EnvelopeRunPlan):
        return EnvelopeGraphPreservationReceipt(
            receipt_id=f"elapsed-envelope-scientific-graph-parity.{run_plan.run_plan_id}",
            base=base_receipt,
            issued_extension_set=run_plan.issued_extension_set,
            execution_envelope_spec=run_plan.execution_envelope_spec,
        )
    if isinstance(run_plan, RunPlan):
        record_type_resource_graph_preservation_receipt: type[ResourceGraphPreservationReceipt] = (
            RetrospectiveEnvelopeGraphParity
            if isinstance(base_receipt, RetrospectiveGraphParity)
            else ResourceGraphPreservationReceipt
        )
        return record_type_resource_graph_preservation_receipt(
            receipt_id=f"resource-envelope-scientific-graph-parity.{run_plan.run_plan_id}",
            base=base_receipt,
            issued_extension_set=run_plan.issued_extension_set,
            execution_resource_envelope_spec=(run_plan.execution_resource_envelope_spec),
            predevelopment_jit_signature_census=(run_plan.predevelopment_jit_signature_census),
            jit_graph_signature_manifest=run_plan.jit_graph_signature_manifest,
        )
    return base_receipt


def _scientific_graph_indexes(graph):
    """Index only this proof's actual supplied graph, retaining edge order."""
    edge_by_id, incoming = {}, {}
    for edge in graph.edges:
        if edge.edge_id in edge_by_id:
            raise ValueError("scientific graph repeats an exact edge identity")
        edge_by_id[edge.edge_id] = edge
        incoming.setdefault(edge.consumer_node_id, []).append(edge)
    external_by_id = {}
    for value in graph.external_inputs:
        if value.input_id in external_by_id:
            raise ValueError("scientific graph repeats an exact external input identity")
        external_by_id[value.input_id] = value
    return edge_by_id, {node: tuple(edges) for node, edges in incoming.items()}, external_by_id


def _validate_run_plan(
    *,
    candidate: DraftStudyCandidate,
    authorized_experiment: ExperimentSpec,
    scientific_approval: ObjectIdentity,
    run_plan: ProtocolRunPlan,
    registry: CapabilityRegistry,
) -> None:
    if run_plan.campaign != ObjectIdentity.from_record(
        candidate.campaign.campaign_id,
        candidate.campaign,
    ):
        raise ValueError("run plan campaign differs from the candidate")
    if run_plan.system != ObjectIdentity.from_record(
        candidate.system.system_id,
        candidate.system,
    ):
        raise ValueError("run plan system differs from the candidate")
    if run_plan.experiment != ObjectIdentity.from_record(
        authorized_experiment.experiment_id,
        authorized_experiment,
    ):
        raise ValueError("run plan experiment differs from the approved candidate")
    if run_plan.authorization != scientific_approval:
        raise ValueError("run plan binds another scientific approval")
    expected_claims = tuple(
        sorted(
            (
                ObjectIdentity.from_record(value.claim_id, value)
                for value in candidate.experiment.claims
            ),
            key=lambda value: value.object_id,
        )
    )
    if run_plan.claims != expected_claims:
        raise ValueError("run plan claim set differs from the candidate")
    if (
        run_plan.world_id != candidate.system.world.world_id
        or run_plan.world_kind is not candidate.system.world.kind
        or run_plan.physical_preparation_ids
        != (
            candidate.experiment.known_physical_independent_unit_ids
            if isinstance(candidate.experiment, RetrospectiveExperimentSpec)
            else (candidate.system.independent_unit.unit_id,)
        )
        or run_plan.registry_sha256 != registry.fingerprint()
        or run_plan.implementation_commit == ""
        or run_plan.robust_model_set_required != candidate.protocol.requires_model_set
        or run_plan.controller_requested != candidate.protocol.requests_controller
        or run_plan.nonactuating != candidate.protocol.nonactuating
    ):
        raise ValueError("run plan root scientific fields differ from the candidate")
    graph_nodes = {value.node_id: value for value in candidate.scientific_graph.nodes}
    edge_by_id, incoming_by_consumer, external_by_id = _scientific_graph_indexes(candidate.scientific_graph)
    template_steps = {value.step_id: value for value in candidate.protocol.steps}
    run_steps = {value.step_id: value for value in run_plan.steps}
    if set(graph_nodes) != set(template_steps) or set(run_steps) != set(template_steps):
        raise ValueError("run plan node set differs from the candidate graph")
    for step_id, template in template_steps.items():
        node = graph_nodes[step_id]
        step = run_steps[step_id]
        if not isinstance(step, RunPlanStep):
            raise ValueError("run plan contains a step outside the RunPlanStep exact-edge contract")
        manifest = registry.resolve(
            step.capability.capability_key,
            step.capability.capability_version,
        )
        if (
            step.stage is not template.stage
            or step.capability.capability_key != node.capability_key
            or step.capability.capability_version != node.capability_version
            or manifest.implementation_sha256 != node.implementation_sha256
            or step.capability.config != template.config
            or step.capability.required_permissions != template.required_permissions
            or step.capability.requested_outcome_access is not template.requested_outcome_access
            or step.capability.requested_resources != node.resource_budget
            or step.dependency_step_ids != template.dependency_step_ids
            or step.resource_lock_ids != template.resource_lock_ids
            or step.barrier is not template.barrier
            or step.maximum_attempts != template.maximum_attempts
            or step.obligation_ids != node.obligation_ids
        ):
            raise ValueError(f"run plan scientific node {step_id!r} drifted")
        expected_edges = incoming_by_consumer.get(step_id, ())
        _validate_external_edges(incoming_edges=expected_edges,
            external_by_id=external_by_id, external_inputs=step.external_inputs)
        observed_edges = {value.edge_id: value for value in step.scientific_inputs}
        if set(observed_edges) != {value.edge_id for value in expected_edges}:
            raise ValueError("run plan scientific edge set differs from the candidate")
        for edge in expected_edges:
            observed = observed_edges[edge.edge_id]
            if (
                observed.consumer_input_id != edge.consumer_input_id
                or observed.scientific_role is not edge.scientific_role
                or observed.producer_task_id != edge.producer_node_id
                or observed.external_input_id != edge.external_input_id
                or observed.logical_artifact_id != edge.logical_artifact_id
                or observed.payload_schema != edge.payload_schema
                or observed.media_type != edge.media_type
                or observed.maximum_size_bytes != edge.maximum_size_bytes
                or observed.outcome_access is not edge.outcome_access
                or observed.visibility_ceiling is not edge.visibility_ceiling
                or observed.barrier is not edge.barrier
            ):
                raise ValueError("run plan scientific edge fields drifted")
            if edge.producer_node_id is not None:
                expected_output_id = f"{edge.producer_node_id}.{edge.producer_output_id}"
                producer = run_steps[edge.producer_node_id]
                output = next(
                    (value for value in producer.outputs if value.output_id == expected_output_id),
                    None,
                )
                if (
                    output is None
                    or observed.producer_output_id != expected_output_id
                    or observed.operational_logical_artifact_id != output.logical_artifact_id
                ):
                    raise ValueError("run plan scientific dependency output drifted")
            else:
                external = external_by_id[edge.external_input_id or ""]
                if (
                    observed.producer_output_id is not None
                    or observed.operational_logical_artifact_id != external.logical_artifact_id
                ):
                    raise ValueError("run plan scientific external input drifted")
    for edge in edge_by_id.values():
        if edge.producer_node_id is None:
            continue
        producer = run_steps[edge.producer_node_id]
        if edge.consumer_node_id not in run_steps:
            raise ValueError("run plan omits an internal edge consumer")
        if edge.producer_node_id not in run_steps[edge.consumer_node_id].dependency_step_ids:
            raise ValueError("run plan internal dependency differs from the candidate edge")
        expected_output_id = f"{edge.producer_node_id}.{edge.producer_output_id}"
        output = next(
            (value for value in producer.outputs if value.output_id == expected_output_id),
            None,
        )
        if (
            output is None
            or output.payload_schema != edge.payload_schema
            or output.media_type != edge.media_type
        ):
            raise ValueError("run plan internal edge output differs from the candidate")


def _validate_external_edges(
    *,
    incoming_edges,
    external_by_id,
    external_inputs: tuple[object, ...],
) -> None:
    from .plans import ExternalInputSpec

    typed_inputs = tuple(value for value in external_inputs if isinstance(value, ExternalInputSpec))
    inputs_by_id = {value.input_id: value for value in typed_inputs}
    for edge in incoming_edges:
        if edge.external_input_id is None:
            continue
        expected = external_by_id[edge.external_input_id]
        observed = inputs_by_id.get(edge.consumer_input_id)
        if observed is None or (
            observed.logical_artifact_id != expected.logical_artifact_id
            or observed.expected_content_sha256 != expected.expected_content_sha256
            or observed.expected_payload_schema != expected.payload_schema
            or observed.expected_media_type != expected.media_type
            or observed.expected_visibility_ceiling is not expected.visibility_ceiling
            or observed.expected_outcome_access is not expected.outcome_access
        ):
            raise ValueError("run plan external scientific edge drifted")


def _validate_execution_plan(
    *,
    run_plan: ProtocolRunPlan,
    execution_plan: ProtocolExecutionPlan,
    registry: CapabilityRegistry,
) -> None:
    if (
        execution_plan.source_plan != ObjectIdentity.from_record(run_plan.run_plan_id, run_plan)
        or execution_plan.registry_sha256 != run_plan.registry_sha256
        or execution_plan.implementation_commit != run_plan.implementation_commit
        or execution_plan.nonactuating != run_plan.nonactuating
    ):
        raise ValueError("execution-plan root differs from the run plan")
    run_steps = {value.step_id: value for value in run_plan.steps}
    tasks = {value.task_id: value for value in execution_plan.tasks}
    if set(run_steps) != set(tasks):
        raise ValueError("execution task set differs from the run plan")
    for step_id, step in run_steps.items():
        task = tasks[step_id]
        if not isinstance(task, ExecutionTask):
            raise ValueError("execution plan contains a task outside the ExecutionTask exact-edge contract")
        manifest = registry.require(step.capability)
        if (
            task.stage is not step.stage
            or task.capability != step.capability
            or task.capability_implementation_sha256 != manifest.implementation_sha256
            or task.dependency_task_ids != step.dependency_step_ids
            or task.external_inputs != step.external_inputs
            or task.outputs != step.outputs
            or task.resource_lock_ids != step.resource_lock_ids
            or task.barrier is not step.barrier
            or task.maximum_attempts != step.maximum_attempts
            or task.obligation_ids != step.obligation_ids
            or not isinstance(step, RunPlanStep)
            or task.scientific_inputs != step.scientific_inputs
        ):
            raise ValueError(f"execution scientific task {step_id!r} drifted")


__all__ = [
    "NormalizedScientificGraphProjection",
    'ScientificGraphPreservationReceipt',
    "normalized_candidate_projection",
    "prove_scientific_graph_parity",
]


@dataclass(frozen=True, slots=True)
class RetrospectiveGraphProjection(NormalizedScientificGraphProjection):
    """Explicit historical compatibility; the predecessor schema is unchanged."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retrospective-graph-projection'

    candidate_experiment: RetrospectiveExperimentSpec
    design_origin: RetrospectiveDesignOrigin

    def __post_init__(self) -> None:
        if type(self.candidate_experiment) is not RetrospectiveExperimentSpec:
            raise ValueError(
                "RetrospectiveGraphProjection requires its exact candidate_experiment schema"
            )
        if type(self.design_origin) is not RetrospectiveDesignOrigin:
            raise ValueError("RetrospectiveGraphProjection requires its exact design_origin schema")
        NormalizedScientificGraphProjection.__post_init__(self)


@dataclass(frozen=True, slots=True)
class RetrospectiveGraphParity(ScientificGraphPreservationReceipt):
    """Explicit historical compatibility; the predecessor schema is unchanged."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retrospective-graph-parity'

    projection: RetrospectiveGraphProjection

    def __post_init__(self) -> None:
        if type(self.projection) is not RetrospectiveGraphProjection:
            raise ValueError("RetrospectiveGraphParity requires its exact projection schema")
        ScientificGraphPreservationReceipt.__post_init__(self)


@dataclass(frozen=True, slots=True)
class RetrospectiveEnvelopeGraphParity(ResourceGraphPreservationReceipt):
    """Explicit historical compatibility; the predecessor schema is unchanged."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/retrospective-envelope-graph-parity'

    base: RetrospectiveGraphParity

    def __post_init__(self) -> None:
        if type(self.base) is not RetrospectiveGraphParity:
            raise ValueError("RetrospectiveEnvelopeGraphParity requires its exact base schema")
        ResourceGraphPreservationReceipt.__post_init__(self)


@dataclass(frozen=True, slots=True)
class DevelopmentGraphPreservationReceipt(CanonicalRecord):
    """Actual development correspondence, without issue or execution authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/development-graph-preservation-receipt"
    receipt_id: str
    draft: ObjectIdentity
    scientific_selection: ObjectIdentity
    template: ObjectIdentity
    run_plan: ObjectIdentity
    execution_plan: ObjectIdentity
    registry_sha256: str
    node_count: int
    edge_count: int
    requirement_count: int

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        validate_sha256(self.registry_sha256)
        if self.node_count < 1 or self.edge_count < 0 or self.requirement_count < 0:
            raise ValueError("development correspondence census is invalid")
        if self.run_plan.object_schema != "empirical-lawhood/runtime/development-run-plan" or self.execution_plan.object_schema != "empirical-lawhood/runtime/development-execution-plan":
            raise ValueError("development correspondence requires its genuine authority-free plans")


def _validate_configuration_graph_bindings(graph, operations, template_steps):
    """Authenticate reserved config edges independently of lowered input specs."""
    from .compiler import _configuration_input_for_step
    from .plans import BarrierKind, ScientificInputRole
    from .recursive_compiler import configuration_edge_id, configuration_input_id

    operations = {operation.node_id: operation for operation in operations}
    expected_edges = {configuration_edge_id(node) for node in operations}
    actual_edges = tuple(edge for edge in graph.edges if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    if {edge.edge_id for edge in actual_edges} != expected_edges or len(actual_edges) != len(expected_edges):
        raise ValueError("scientific graph changes its exact compiler-owned configuration census")
    by_external = {value.input_id: value for value in graph.external_inputs}
    expected_external_ids = {configuration_input_id(operation.config_id) for operation in operations.values()}
    if {value.input_id for value in graph.external_inputs if value.scientific_role is ScientificInputRole.CONFIGURATION} != expected_external_ids:
        raise ValueError("scientific graph adds or omits a compiler-owned configuration publication")
    result = {}
    for edge in actual_edges:
        operation = operations.get(edge.consumer_node_id)
        if (operation is None or edge.edge_id != configuration_edge_id(operation.node_id)
                or edge.consumer_input_id != "config" or edge.producer_node_id is not None
                or edge.external_input_id != configuration_input_id(operation.config_id)
                or edge.barrier is not BarrierKind.NONE):
            raise ValueError("scientific graph substitutes its exact compiler-owned configuration edge")
        spec = _configuration_input_for_step(template_steps[operation.node_id], (edge,), by_external)
        if (spec.expected_content_sha256, spec.expected_payload_schema, spec.expected_size_bytes) != (
                operation.config_identity.object_fingerprint, operation.config_identity.object_schema,
                len(operation.config_payload.encode())):
            raise ValueError("scientific graph changes its original exact configuration bytes")
        result[operation.node_id] = spec
    return result


def prove_development_graph_parity(*, draft, selection, template, run_plan, execution_plan, registry):
    """Compare actual selected operands, topology and every lowered contract field."""
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection, RecursiveStudyDraft
    from .compiler import _project_output_custody, _scientific_external_inputs_for_step, _scientific_inputs_for_step
    from .plans import ArtifactOutputSpec, DevelopmentExecutionPlan, DevelopmentRunPlan

    if not isinstance(draft, RecursiveStudyDraft) or not isinstance(selection, RecursiveScientificSelection):
        raise TypeError("development correspondence requires typed scientific authoring records")
    if draft.development_study is None or not isinstance(run_plan, DevelopmentRunPlan) or not isinstance(execution_plan, DevelopmentExecutionPlan):
        raise ValueError("development correspondence requires a genuine development study")
    expected_draft = ObjectIdentity.from_record(draft.draft_id, draft)
    expected_selection = ObjectIdentity.from_record(selection.selection_id, selection)
    expected_template = ObjectIdentity.from_record(template.template_key, template)
    if (run_plan.draft != expected_draft or run_plan.scientific_projection != expected_selection
        or run_plan.template != expected_template or run_plan.registry_sha256 != registry.fingerprint()
        or run_plan.campaign != ObjectIdentity.from_record(draft.campaign.campaign_id, draft.campaign)
        or run_plan.study != ObjectIdentity.from_record(draft.development_study.study_id, draft.development_study)
        or selection.scientific_root != run_plan.study):
        raise ValueError("development scientific root or authored operands drifted")
    selected = set(draft.selected_operation_ids)
    if selection.operations != tuple(operation for operation in draft.operations if operation.node_id in selected):
        raise ValueError("development selected operation inventory drifted")
    if selection.links != tuple(link for link in draft.links if link.consumer_node_id in selected):
        raise ValueError("development selected scientific links drifted")
    from .recursive_compiler import _close_requirements
    requirements, connections, _ = _close_requirements(draft, selected, selection.links)
    if selection.requirements != requirements or selection.connections != connections:
        raise ValueError("development selected requirements or assessed connections drifted")
    external_ids = {link.external_input_id for link in selection.links if link.external_input_id is not None}
    if selection.external_inputs != tuple(value for value in draft.external_inputs if value.input_id in external_ids):
        raise ValueError("development selected external inputs drifted")
    expected_parents = tuple(ObjectIdentity.from_record(parent.contribution_id, parent) for parent in draft.contribution_parents)
    if selection.contribution_parents != expected_parents:
        raise ValueError("development contribution lineage drifted")
    if set(selected) != {step.step_id for step in template.protocol.steps} or set(selected) != {step.step_id for step in run_plan.steps}:
        raise ValueError("development selected step census drifted")
    graph = template.graph
    edge_by_id, incoming_by_consumer, externals = _scientific_graph_indexes(graph)
    steps = {step.step_id: step for step in run_plan.steps}
    template_steps = {step.step_id: step for step in template.protocol.steps}
    operations = {value.node_id: value for value in selection.operations}
    config_inputs = _validate_configuration_graph_bindings(graph, selection.operations, template_steps)
    from .recursive_compiler import configuration_edge_id
    if set(edge_by_id) != {link.edge_id for link in selection.links} | {
            configuration_edge_id(node) for node in operations}:
        raise ValueError("development scientific edge census drifted")
    for link in selection.links:
        edge = edge_by_id[link.edge_id]
        if (edge.consumer_node_id != link.consumer_node_id or edge.consumer_input_id != link.consumer_input_id
            or edge.producer_node_id != link.producer_node_id or edge.producer_output_id != link.producer_output_id
            or edge.external_input_id != link.external_input_id or edge.scientific_role.value != link.scientific_role):
            raise ValueError("development scientific edge role or endpoints drifted")
    for node, step in steps.items():
        original = template_steps[node]
        if (original.requested_outcome_access, original.visibility_ceiling) != draft.development_study.access_pair:
            raise ValueError("development template changes its exact exposed study access")
        operation = operations[node]
        manifest = registry.require(step.capability)
        incoming = incoming_by_consumer.get(node, ())
        parents = tuple(sorted((edge.visibility_ceiling for edge in incoming), key=lambda value: value.value))
        custody = _project_output_custody(original, parent_visibility_ceilings=parents,
            parent_outcome_accesses=tuple(edge.outcome_access for edge in incoming), scientific_graph=True)
        expected_outputs = tuple(ArtifactOutputSpec(
            f"{node}.{output.output_id}", f"artifact.{run_plan.run_plan_id}.{node}.{output.output_id}",
            f"runs/{run_plan.run_plan_id}/outputs/{node}/{output.output_id}{output.filename_suffix}",
            output.payload_schema, output.profile, output.media_type, pair[1],
            parents, pair[0]) for output, pair in zip(original.outputs, custody, strict=True))
        config = step.capability.config
        expected_config = config_inputs[node]
        expected_external = tuple(sorted((expected_config,
            *_scientific_external_inputs_for_step(graph, incoming_edges=incoming, external_by_id=externals)), key=lambda value: value.input_id))
        if (step.stage is not original.stage or step.capability.capability_key != original.capability_key
            or step.capability.capability_version != original.capability_version or config != original.config
            or config.content_sha256 != operation.config_identity.object_fingerprint
            or config.config_schema != operation.config_identity.object_schema or config.artifact_id != operation.config_id
            or manifest.implementation_sha256 != operation.selection.implementation_sha256
            or step.capability.required_permissions != original.required_permissions
            or step.capability.requested_resources != operation.resource_budget
            or step.capability.requested_evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
            or step.capability.requested_outcome_access is not original.requested_outcome_access
            or step.capability.required_input_schema_ids != tuple(sorted({config.config_schema, *(edge.payload_schema for edge in incoming)}))
            or step.capability.required_output_schema_ids != tuple(sorted({output.payload_schema for output in original.outputs}))
            or step.dependency_step_ids != original.dependency_step_ids or step.outputs != expected_outputs
            or step.external_inputs != expected_external or step.resource_lock_ids != operation.resource_lock_ids
            or step.barrier is not original.barrier or step.maximum_attempts != operation.maximum_attempts
            or step.obligation_ids != operation.obligation_ids
            or step.scientific_inputs != _scientific_inputs_for_step(incoming_edges=incoming, external_by_id=externals, compiled_steps=steps)):
            raise ValueError(f"development scientific step {node!r} drifted")
    _validate_execution_plan(run_plan=run_plan, execution_plan=execution_plan, registry=registry)
    return DevelopmentGraphPreservationReceipt(f"development-parity.{run_plan.run_plan_id}",
        expected_draft, expected_selection, expected_template,
        ObjectIdentity.from_record(run_plan.run_plan_id, run_plan),
        ObjectIdentity.from_record(execution_plan.execution_plan_id, execution_plan),
        registry.fingerprint(), len(selected), len(graph.edges), len(selection.requirements))


@dataclass(frozen=True, slots=True)
class RecursiveGraphPreservationReceipt(CanonicalRecord):
    """Issued graph correspondence plus the exact recursive scientific selection."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/recursive-graph-preservation-receipt"
    receipt_id: str
    base: ScientificGraphPreservationReceipt
    scientific_selection: ObjectIdentity
    issued_extension_set: ObjectIdentity
    issued_selection_member: ObjectIdentity
    requirement_count: int
    connection_count: int

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id, field_name="receipt_id")
        if self.scientific_selection.object_schema != "empirical-lawhood/planning/recursive-scientific-selection":
            raise ValueError("recursive correspondence requires its exact scientific selection")
        if self.requirement_count < 0 or self.connection_count < 0:
            raise ValueError("recursive correspondence scientific census is invalid")


def prove_recursive_graph_parity(*, base_receipt, selection, template, candidate,
                                 run_plan, execution_plan, registry, issued_extensions):
    """Validate issued selection bytes and actual topology beside existing authority proof."""
    from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection, validate_selected_requirement_graph
    from .candidate_compiler import ExecutableStudyCandidate
    from .study_issue import IssuedExtensionSet

    if not isinstance(selection, RecursiveScientificSelection) or not isinstance(candidate, ExecutableStudyCandidate):
        raise TypeError("recursive issue correspondence requires the actual selected science and executable candidate")
    validate_selected_requirement_graph(requirements=selection.requirements)
    if not isinstance(issued_extensions, IssuedExtensionSet):
        raise TypeError("recursive issue correspondence requires the actual issued extension set")
    base = base_receipt.base if isinstance(base_receipt, (EnvelopeGraphPreservationReceipt, ResourceGraphPreservationReceipt)) else base_receipt
    if (not isinstance(base, ScientificGraphPreservationReceipt)
        or base.candidate != ObjectIdentity.from_record(candidate.candidate_id, candidate)
        or base.run_plan != ObjectIdentity.from_record(run_plan.run_plan_id, run_plan)
        or base.execution_plan != ObjectIdentity.from_record(execution_plan.execution_plan_id, execution_plan)):
        raise ValueError("recursive correspondence changes the already authenticated authority proof")
    if (base.projection.protocol != template.protocol or base.projection.scientific_graph != template.graph
        or base.projection.obligation_coverage != template.coverage):
        raise ValueError("recursive template differs from the issued scientific graph")
    proposals = tuple(proposal for proposal in candidate.authoring_package.extension_set.extensions
                      if proposal.payload.object_schema == selection.SCHEMA)
    identity = ObjectIdentity.from_record(selection.selection_id, selection)
    if len(proposals) != 1 or proposals[0].payload != identity or not proposals[0].required_for_activation:
        raise ValueError("issued recursive scientific selection is missing, optional or changed")
    if issued_extensions.proposed_extension_set != candidate.proposed_extension_set:
        raise ValueError("recursive correspondence binds another issued extension set")
    proposal = proposals[0]
    binding = next((binding for binding in issued_extensions.bindings if binding.extension_id == proposal.extension_id), None)
    if binding is None or binding.proposed_extension != ObjectIdentity.from_record(proposal.extension_id, proposal):
        raise ValueError("recursive selection proposal lacks its exact issued member binding")
    member = next((member for member in issued_extensions.members
                   if ObjectIdentity.from_record(member.member_id, member) == binding.issued_member), None)
    if member is None or member.logical_content_sha256 != identity.object_fingerprint or member.payload_schema != selection.SCHEMA:
        raise ValueError("recursive issued selection member changes its scientific bytes")
    operations = {operation.node_id: operation for operation in selection.operations}
    steps = {step.step_id: step for step in template.protocol.steps}
    if set(operations) != set(steps):
        raise ValueError("recursive issued operation census differs from its actual template")
    for node, operation in operations.items():
        step = steps[node]
        if (step.config.content_sha256 != operation.config_identity.object_fingerprint
            or step.config.config_schema != operation.config_identity.object_schema
            or step.config.artifact_id != operation.config_id
            or step.capability_key != operation.selection.capability_key
            or step.capability_version != operation.selection.capability_version
            or step.resource_budget != operation.resource_budget
            or step.maximum_attempts != operation.maximum_attempts
            or step.resource_lock_ids != operation.resource_lock_ids
            or step.obligation_ids != operation.obligation_ids):
            raise ValueError("recursive issued operation/config/resource operands drifted")
    edge_by_id, _, _ = _scientific_graph_indexes(template.graph)
    _validate_configuration_graph_bindings(template.graph, selection.operations, steps)
    from .recursive_compiler import configuration_edge_id
    if set(edge_by_id) != {link.edge_id for link in selection.links} | {
            configuration_edge_id(node) for node in operations}:
        raise ValueError("recursive issued edge census drifted")
    for link in selection.links:
        edge = edge_by_id[link.edge_id]
        if (edge.consumer_node_id != link.consumer_node_id or edge.consumer_input_id != link.consumer_input_id
            or edge.producer_node_id != link.producer_node_id or edge.producer_output_id != link.producer_output_id
            or edge.external_input_id != link.external_input_id or edge.scientific_role.value != link.scientific_role):
            raise ValueError("recursive issued scientific edge roles or endpoints drifted")
    requirements = {requirement.requirement_id: requirement for requirement in selection.requirements}
    for connection in selection.connections:
        requirement = requirements.get(connection.requirement_id)
        if requirement is None or requirement.scope is None or requirement.assessment_operation_id != connection.assessment_operation_id:
            raise ValueError("recursive issued assessment or scope is unresolved")
        if connection.evidence_role not in requirement.permitted_roles or connection.assessment_operation_id not in steps:
            raise ValueError("recursive issued connection exceeds its role or selected assessment")
        matching = tuple(link for link in selection.links if link.connection_id == connection.connection_id)
        if len(matching) != 1:
            raise ValueError("recursive issued assessed connection lacks its exact edge")
        link = matching[0]
        if (link.requirement_id != requirement.requirement_id or link.consumer_node_id != requirement.consumer_operation_id
            or link.consumer_input_id != connection.consumer_input_id or link.producer_node_id != connection.supplier_operation_id
            or link.producer_output_id != connection.supplier_output_id
            or link.external_input_id != connection.external_input_id):
            raise ValueError("recursive issued assessed connection differs from actual scientific use")
    _validate_execution_plan(run_plan=run_plan, execution_plan=execution_plan, registry=registry)
    return RecursiveGraphPreservationReceipt(f"recursive-parity.{run_plan.run_plan_id}", base, identity,
        ObjectIdentity.from_record(issued_extensions.issued_extension_set_id, issued_extensions), binding.issued_member,
        len(selection.requirements), len(selection.connections))
