"""Structural input routes, separate from actual permission to open bytes.

Prospective frozen models keep their explicit internal MODEL route. Development
original-parent routes require code-owned CONFIGURATION ancestry and a separate
fresh runtime guard. Neither route grants reveal authority or lowers custody.
"""

from dataclasses import dataclass

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from .artifacts import ArtifactLineageParent, lineage_parent_sort_key
from .capabilities import CapabilityPermission, input_access_allowed
from .plans import BarrierKind, ExternalInputSpec, PlanLane, ProtocolExecutionPlan, ProtocolExecutionTask, ExecutionTask, ScientificInputRole, ScientificInputSpec


@dataclass(frozen=True, slots=True)
class OriginalParentInputContract:
    """Computed original-input route; actual current permission is not a field."""

    task: ObjectIdentity
    input_spec: ExternalInputSpec | ScientificInputSpec
    original_configurations: tuple[ExternalInputSpec, ...]
    input_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self):
        access = (self.input_spec.expected_outcome_access if type(self.input_spec) is ExternalInputSpec
            else self.input_spec.outcome_access if type(self.input_spec) is ScientificInputSpec else None)
        if (type(self.task) is not ObjectIdentity
                or type(self.input_spec) not in (ExternalInputSpec, ScientificInputSpec)
                or access is not OutcomeAccess.EVALUATION_SEALED
                or type(self.original_configurations) is not tuple or not self.original_configurations
                or any(type(value) is not ExternalInputSpec or value.input_id != "config"
                    or value.expected_content_sha256 is None or value.expected_size_bytes is None
                    or value.expected_payload_schema is None or value.expected_media_type != "application/json"
                    for value in self.original_configurations)
                or tuple(value.logical_artifact_id for value in self.original_configurations) !=
                    tuple(sorted({value.logical_artifact_id for value in self.original_configurations}))
                or type(self.input_parents) is not tuple or not self.input_parents
                or any(type(value) is not ArtifactLineageParent
                    or type(value.identity) is not ObjectIdentity
                    or type(value.outcome_access) is not OutcomeAccess
                    or type(value.visibility_ceiling) is not VisibilityCeiling for value in self.input_parents)
                or tuple(lineage_parent_sort_key(value) for value in self.input_parents) !=
                    tuple(sorted({lineage_parent_sort_key(value) for value in self.input_parents}))
                or not any(value.outcome_access is OutcomeAccess.EVALUATION_SEALED for value in self.input_parents)
                or not any(value.expected_outcome_access is OutcomeAccess.EVALUATION_SEALED
                    for value in self.original_configurations)):
            raise ValueError("original input route loses its exact config and parent custody census")
        self.task.__post_init__()

    @property
    def logical_artifact_id(self):
        return (self.input_spec.logical_artifact_id if type(self.input_spec) is ExternalInputSpec
            else self.input_spec.operational_logical_artifact_id)


def validated_task_scientific_input_edges(task):
    """Validate frozen CONFIGURATION metadata without reading or granting access.

    Actual byte custody, scientific-owner joins and current permission remain
    with the caller. Remaining edges retain their exact objects and ordering.
    """
    from .capabilities import CapabilityConfigRef, CapabilityRequirement
    from .recursive_compiler import configuration_edge_id, configuration_input_id

    if (type(task) is not ExecutionTask or type(task.capability) is not CapabilityRequirement
            or type(task.capability.config) is not CapabilityConfigRef):
        raise ValueError("scientific inputs require their exact frozen CONFIGURATION task")
    config = task.capability.config
    if (config.artifact_id != config.config_id
            or type(task.external_inputs) is not tuple
            or any(type(spec) is not ExternalInputSpec for spec in task.external_inputs)
            or type(task.scientific_inputs) is not tuple
            or any(type(edge) is not ScientificInputSpec for edge in task.scientific_inputs)):
        raise ValueError("scientific inputs substitute their frozen CONFIGURATION metadata")
    task.__post_init__()
    config.__post_init__()
    edges = tuple(edge for edge in task.scientific_inputs
        if edge.scientific_role is ScientificInputRole.CONFIGURATION)
    specs = tuple(spec for spec in task.external_inputs
        if spec.input_id == "config" or spec.logical_artifact_id == config.artifact_id)
    if len(edges) != 1 or len(specs) != 1:
        raise ValueError("scientific inputs lose the unique compiler-owned CONFIGURATION census")
    edge, spec = edges[0], specs[0]
    if (type(spec.expected_size_bytes) is not int or spec.expected_size_bytes <= 0
            or type(edge.maximum_size_bytes) is not int
            or type(spec.expected_outcome_access) is not OutcomeAccess
            or type(spec.expected_visibility_ceiling) is not VisibilityCeiling
            or type(edge.outcome_access) is not OutcomeAccess
            or type(edge.visibility_ceiling) is not VisibilityCeiling):
        raise ValueError("scientific inputs lose exact CONFIGURATION size or custody metadata")
    expected_edge = ScientificInputSpec(configuration_edge_id(task.task_id), "config",
        ScientificInputRole.CONFIGURATION, None, None, configuration_input_id(config.config_id),
        config.config_id, config.artifact_id, config.config_schema, "application/json",
        spec.expected_size_bytes, spec.expected_outcome_access, spec.expected_visibility_ceiling, BarrierKind.NONE)
    expected_spec = ExternalInputSpec("config", config.artifact_id, config.content_sha256,
        config.config_schema, "application/json", spec.expected_size_bytes,
        spec.expected_visibility_ceiling, spec.expected_outcome_access, None)
    if edge != expected_edge or spec != expected_spec:
        raise ValueError("scientific inputs change their exact compiler-owned CONFIGURATION edge or bytes")
    scientific = tuple(edge for edge in task.scientific_inputs
        if edge.scientific_role is not ScientificInputRole.CONFIGURATION)
    if any(edge.consumer_input_id == "config" or edge.logical_artifact_id == config.config_id
            or edge.operational_logical_artifact_id == config.artifact_id
            or edge.external_input_id == configuration_input_id(config.config_id) for edge in scientific):
        raise ValueError("scientific inputs alias the compiler-owned CONFIGURATION operand")
    return scientific


def validated_scientific_input_edges(context, *, config_port):
    """Join frozen task metadata to the actual complete prepared worker inputs.

    The pure task validator supplies no byte, profile, materialization or access
    verdict. This worker boundary retains those exact prepared-contract checks.
    """
    from .artifacts import ArtifactProfile
    from .execution import TaskContext, WorkerInputKind, WorkerInputPort
    from .prepared_native_invocation import PreparedInvocationContract

    if (type(context) is not TaskContext or type(config_port) is not WorkerInputPort
            or type(context.prepared_invocation) is not PreparedInvocationContract):
        raise ValueError("scientific inputs require their exact prepared configuration port")
    prepared = context.prepared_invocation
    prepared.require_complete()
    prepared.validate_context(context)
    task, config = prepared.execution_task_record, context.config
    if (type(task) is not ExecutionTask
            or sum(port is config_port for port in context.input_ports) != 1
            or config_port.artifact_id != config.artifact_id
            or config.artifact_id != config.config_id
            or config_port.kind is not WorkerInputKind.EXTERNAL):
        raise ValueError("scientific inputs substitute their actual compiler configuration port")
    scientific = validated_task_scientific_input_edges(task)
    spec, = (row for row in task.external_inputs if row.input_id == "config")
    inputs = tuple(row for row in prepared.inputs if row.artifact_id == config.artifact_id)
    if len(inputs) != 1:
        raise ValueError("scientific inputs lose the unique compiler-owned CONFIGURATION input")
    actual = inputs[0]
    if (actual.binding != config_port.binding
            or (config_port.payload_schema, config_port.media_type, config_port.size_bytes,
                config_port.outcome_access, config_port.visibility_ceiling) != (
                config.config_schema, "application/json", spec.expected_size_bytes,
                spec.expected_outcome_access, spec.expected_visibility_ceiling)
            or actual.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or (actual.logical.content_sha256, actual.physical_sha256) != (
                config.content_sha256, config.content_sha256)):
        raise ValueError("scientific inputs change their exact compiler-owned CONFIGURATION port or bytes")
    return scientific

def derive_original_parent_input_contracts(execution_plan, *, config_inputs, registrations_for_node):
    """Derive supported routes only from actual hooked CONFIGURATION ancestry.

    The returned descriptors can satisfy structural preflight. Opening actual
    bytes still requires the API's fresh exact original-input access guard.
    """
    from .recursive_compiler import DecodedRecursiveConfigInput, RecursiveConfigInput, configuration_graph_bindings, project_recursive_config_inputs

    if execution_plan.lane is not PlanLane.DEVELOPMENT:
        return ()
    tasks = {task.task_id: task for task in execution_plan.tasks}
    if (type(config_inputs) is not tuple or any(type(row) is not RecursiveConfigInput for row in config_inputs)
            or {row.node_id for row in config_inputs} != set(tasks)
            or set(registrations_for_node) != set(tasks)):
        raise ValueError("original input projection needs its complete finalized task/config census")
    projected = project_recursive_config_inputs(tuple(DecodedRecursiveConfigInput(row.node_id, row.config_id,
        row.payload, row.record, row.record_type) for row in config_inputs), registrations_for_node)
    if projected != config_inputs:
        raise ValueError("original input projection changes actual registered configuration custody")
    _, configuration_edges = configuration_graph_bindings(config_inputs)
    config_edges = {edge.consumer_node_id: edge for edge in configuration_edges}
    rows = {row.node_id: row for row in config_inputs}
    for node, task in tasks.items():
        row, expected = rows[node], config_edges[node]
        registration = registrations_for_node[node]
        actual = tuple(edge for edge in task.scientific_inputs if edge.scientific_role is ScientificInputRole.CONFIGURATION)
        if (len(actual) != 1 or actual[0].edge_id != expected.edge_id
                or actual[0].external_input_id != expected.external_input_id
                or actual[0].consumer_input_id != "config" or actual[0].producer_task_id is not None
                or actual[0].operational_logical_artifact_id != row.config_id
                or (actual[0].payload_schema, actual[0].media_type, actual[0].maximum_size_bytes,
                    actual[0].outcome_access, actual[0].visibility_ceiling) != (
                    expected.payload_schema, expected.media_type, expected.maximum_size_bytes,
                    expected.outcome_access, expected.visibility_ceiling)
                or sum(value == row.input_spec for value in task.external_inputs) != 1
                or (task.capability.config.config_id, task.capability.config.config_schema,
                    task.capability.config.content_sha256, task.capability.config.artifact_id) != (
                    row.config_id, row.record.SCHEMA, row.record.fingerprint(), row.config_id)
                or (task.capability.capability_key, task.capability.capability_version,
                    task.capability_implementation_sha256) != (registration.selection.capability_key,
                    registration.selection.capability_version, registration.selection.implementation_sha256)):
            raise ValueError("original input projection substitutes its frozen owning CONFIGURATION edge")
    scopes = {}
    result = []
    for group in execution_plan.parallel_ready_groups():
        for node in group:
            task, row = tasks[node], rows[node]
            origins = ({node} if row.input_parents else set())
            for edge in task.scientific_inputs:
                if edge.producer_task_id is not None:
                    origins.update(scopes[edge.producer_task_id])
            scopes[node] = origins
            if task.capability.requested_outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or not origins:
                continue
            parents = {}
            for origin in sorted(origins):
                for parent in rows[origin].input_parents:
                    if parents.setdefault(parent.identity, parent) != parent:
                        raise ValueError("original input ancestry changes one exact original parent's labels")
            parent_census = tuple(sorted(parents.values(), key=lineage_parent_sort_key))
            if not any(parent.outcome_access is OutcomeAccess.EVALUATION_SEALED for parent in parent_census):
                continue
            configurations = tuple(sorted((rows[origin].input_spec for origin in origins),
                key=lambda value: value.logical_artifact_id))
            # Shared exact configs can feed multiple selected nodes.
            configurations = tuple({value.logical_artifact_id: value for value in configurations}.values())
            inputs = tuple(value for value in task.external_inputs
                if value.expected_outcome_access is OutcomeAccess.EVALUATION_SEALED)
            inputs += tuple(edge for edge in task.scientific_inputs if edge.producer_task_id is not None
                and edge.outcome_access is OutcomeAccess.EVALUATION_SEALED)
            result.extend(OriginalParentInputContract(ObjectIdentity.from_record(node, task), value,
                configurations, parent_census) for value in inputs)
    return tuple(sorted(result, key=lambda value: (value.task.object_id, value.logical_artifact_id)))


def validate_planned_input_access(execution_plan: ProtocolExecutionPlan, *, original_parent_input_contracts=()) -> None:
    """Refuse unreadable planned inputs before publication or worker admission.

    This checks declared permissions only. A planned reveal barrier supplies no
    execution authority; the execution owner still authenticates that authority
    and every actual input receipt before opening a worker cursor.
    """
    by_task = {task.task_id: task for task in execution_plan.tasks}
    original = {}
    if type(original_parent_input_contracts) is not tuple:
        raise TypeError("original input preflight requires its exact computed contract tuple")
    if any(type(value) is not OriginalParentInputContract for value in original_parent_input_contracts):
        raise TypeError("original input preflight substitutes its computed contract type")
    needed = {value.logical_artifact_id for contract in original_parent_input_contracts
        for value in contract.original_configurations}
    roots_by_task = {}
    for node in execution_plan.topological_task_ids():
        task = by_task[node]
        roots = {}
        for parent in task.dependency_task_ids:
            roots.update(roots_by_task[parent])
        for spec in task.external_inputs:
            if spec.input_id != "config" or spec.logical_artifact_id not in needed:
                continue
            matching = tuple(edge for edge in task.scientific_inputs
                if edge.scientific_role is ScientificInputRole.CONFIGURATION and edge.consumer_input_id == "config"
                and edge.producer_task_id is None and edge.operational_logical_artifact_id == spec.logical_artifact_id
                and (edge.payload_schema, edge.media_type, edge.maximum_size_bytes, edge.outcome_access, edge.visibility_ceiling) == (
                    spec.expected_payload_schema, spec.expected_media_type, spec.expected_size_bytes,
                    spec.expected_outcome_access, spec.expected_visibility_ceiling))
            if len(matching) == 1:
                roots[spec.logical_artifact_id] = spec
        roots_by_task[node] = roots
    for contract in original_parent_input_contracts:
        if type(contract) is not OriginalParentInputContract:
            raise TypeError("original input preflight substitutes its computed contract type")
        task = by_task.get(contract.task.object_id)
        if (execution_plan.lane is not PlanLane.DEVELOPMENT or task is None
                or contract.task != ObjectIdentity.from_record(task.task_id, task)
                or task.capability.requested_outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or not {CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT} <=
                    set(task.capability.required_permissions)
                or contract.input_spec not in (*task.external_inputs, *task.scientific_inputs)
                or any(roots_by_task[task.task_id].get(value.logical_artifact_id) != value
                    for value in contract.original_configurations)):
            raise ValueError("original input preflight substitutes its exact task or selected input")
        key = (task.task_id, contract.logical_artifact_id)
        if key in original:
            raise ValueError("original input preflight repeats an exact selected input")
        original[key] = contract
    for task in execution_plan.tasks:
        selected = (
            {
                edge.operational_logical_artifact_id
                for edge in task.scientific_inputs
                if edge.producer_task_id is not None
            }
            if isinstance(task, ExecutionTask)
            else None
        )
        accesses: list[tuple[str, OutcomeAccess, VisibilityCeiling | None]] = [
            (output.logical_artifact_id, output.outcome_access, output.visibility_ceiling)
            for parent in task.dependency_task_ids
            for output in by_task[parent].outputs
            if selected is None or output.logical_artifact_id in selected
        ]
        accesses.extend(
            (value.logical_artifact_id, value.expected_outcome_access, value.expected_visibility_ceiling)
            for value in task.external_inputs
            if value.expected_outcome_access is not None
        )
        for artifact_id, access, visibility in accesses:
            if not planned_input_access_allowed(
                task,
                artifact_id,
                access,
                visibility,
                reveal_barrier_authorized=task.barrier is BarrierKind.REVEAL,
            ) and (task.task_id, artifact_id) not in original:
                raise ValueError(f"task {task.task_id} lacks read permission for planned input {artifact_id}")


def planned_input_access_allowed(
    task: ProtocolExecutionTask,
    artifact_id: str,
    access: OutcomeAccess,
    visibility: VisibilityCeiling | None,
    *,
    reveal_barrier_authorized: bool = False,
) -> bool:
    model_edges = (
        tuple(
            edge
            for edge in task.scientific_inputs
            if edge.operational_logical_artifact_id == artifact_id
        )
        if isinstance(task, ExecutionTask)
        else ()
    )
    frozen_model = (
        visibility is VisibilityCeiling.PROSPECTIVE
        and bool(model_edges)
        and all(
            edge.scientific_role is ScientificInputRole.MODEL
            and edge.producer_task_id in task.dependency_task_ids
            and edge.external_input_id is None
            and edge.outcome_access is OutcomeAccess.EVALUATOR_REVEAL
            and edge.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
            for edge in model_edges
        )
    )
    return input_access_allowed(
        task.capability,
        access,
        reveal_barrier_authorized=reveal_barrier_authorized,
        frozen_model_authorized=frozen_model,
    )
