# SPDX-License-Identifier: MPL-2.0
"""Shared received-record/array custody for current native Matrix DEV readers."""
from hashlib import sha256
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.plans import BarrierKind
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile


def _record(products, tasks, run_id, selected_task, kind, label="product"):
    """Use the common owner's decoded canonical product and exact receipt once."""
    task = tasks[selected_task]
    receipt = products["receipts"].get(selected_task)
    outputs = tuple(value for value in task.outputs if value.output_id == selected_task + "." + label)
    if (receipt is None or (receipt.run_id, receipt.task_id) != (run_id, selected_task)
            or receipt.operational_status is not OperationalStatus.SUCCEEDED or len(outputs) != 1):
        raise PermissionError("native Matrix read lacks its actual successful producing receipt/output")
    output, = outputs
    logicals = tuple(value for value in receipt.output_logical_artifacts
        if value.logical_artifact_id == output.logical_artifact_id)
    materials = tuple(value for value in receipt.output_materializations
        if value.logical_artifact_id == output.logical_artifact_id)
    retained = products["outputs"].get(output.logical_artifact_id)
    value = products["records"].get(selected_task, {}).get(output.output_id)
    if (len(logicals) != 1 or len(materials) != 1 or retained is None or type(value) is not kind
            or (retained.logical, retained.materialization) != (logicals[0], materials[0])):
        raise PermissionError("native Matrix read lacks its original typed receipted canonical product")
    logical, material = logicals[0], materials[0]
    raw = value.canonical_bytes()
    if (output.payload_schema != kind.SCHEMA or logical.payload_schema != kind.SCHEMA
            or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != "application/json"
            or logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or sha256(raw).hexdigest() != logical.content_sha256
            or material.physical_sha256 != logical.content_sha256 or len(raw) != material.size_bytes):
        raise PermissionError("native Matrix read changes actual canonical product bytes/schema/exposure custody")
    return value


def _array(products, tasks, selected_task, arrays):
    """Join the consumer's descriptor to its actual ordinary array output."""
    task = tasks[selected_task]
    output, = (value for value in task.outputs if value.output_id == selected_task + ".arrays")
    receipt = products["receipts"][selected_task]
    logicals = tuple(value for value in receipt.output_logical_artifacts
        if value.logical_artifact_id == output.logical_artifact_id)
    materials = tuple(value for value in receipt.output_materializations
        if value.logical_artifact_id == output.logical_artifact_id)
    retained = products["outputs"].get(output.logical_artifact_id)
    if (len(logicals) != 1 or len(materials) != 1 or retained is None
            or (retained.logical, retained.materialization) != (logicals[0], materials[0])):
        raise PermissionError("native Matrix read omits the actual receipted array output")
    logical, material = logicals[0], materials[0]
    artifact = arrays.array_artifact
    if ((artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.sha256, artifact.size_bytes) !=
            (logical.logical_artifact_id, logical.payload_schema, logical.media_type, logical.content_sha256, material.size_bytes)
            or material.physical_sha256 != artifact.sha256 or logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
            or (logical.outcome_access, logical.visibility_ceiling) != (arrays.outcome_access, arrays.visibility_ceiling)):
        raise PermissionError("native Matrix read substitutes the consumer's actual receipted array descriptor")


def _producers(arrays, expected):
    if (arrays.producers != tuple(sorted(expected, key=lambda value: value.object_id))
            or arrays.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or arrays.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise PermissionError("native Matrix read changes exact array producer or exposure scope")



def _expected_contact(*, task, plan, run_id, attempt_id, products):
    """Reconstruct only the original contact header from actual declared operands."""
    materials = {}
    external = {value.logical.logical_artifact_id: value for value in products["external_inputs"]}
    for spec in task.external_inputs:
        value = external.get(spec.logical_artifact_id)
        if value is None:
            raise PermissionError("native E2 missing contact loses an original authenticated external operand")
        materials[value.materialization.materialization_id] = value
    from empirical_lawhood.runtime.execution import dependency_artifact_inputs
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, ExecutionTask
    if type(plan) is not DevelopmentExecutionPlan or type(task) is not ExecutionTask:
        raise TypeError("native DEV parent contact requires its exact original development task/plan")
    dependency_outputs = {}
    for dependency in task.dependency_task_ids:
        producer = products["receipts"].get(dependency)
        if producer is None:
            raise PermissionError("native DEV contact lacks an actual successful direct producer")
        logicals = {row.logical_artifact_id: row for row in producer.output_logical_artifacts}
        values = []
        for material in producer.output_materializations:
            value = products["outputs"].get(material.logical_artifact_id)
            if value is None or value.materialization != material or value.logical != logicals.get(material.logical_artifact_id):
                raise PermissionError("native DEV contact substitutes a direct producer materialization")
            values.append(value)
        dependency_outputs[dependency] = tuple(values)
    try:
        selected = dependency_artifact_inputs(task, dependency_outputs)
    except (TypeError, ValueError) as error:
        raise PermissionError("native DEV contact changes its exact scientific dependency operands") from error
    materials.update((value.materialization.materialization_id, value) for value in selected)
    try:
        receipt_ids = tuple(sorted(products["receipts"][key].receipt_id for key in task.dependency_task_ids))
    except KeyError as error:
        raise PermissionError("native E2 contact omits an original direct producing receipt") from error
    return NativeEffectContact(run_id, task.task_id, attempt_id,
        ObjectIdentity.from_record(plan.execution_plan_id, plan), ObjectIdentity.from_record(task.task_id, task),
        plan.implementation_commit, tuple(sorted(materials)), receipt_ids)



def _graph(specification, request, draft, plan):
    # Pure mathematical layout, without current operation discovery, compilation,
    # provider construction or comparison to current source implementation bytes.
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as training
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as utility
    if type(specification) is utility.NativeUtilitySpecification:
        from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_utility_bindings import ARRAY_PHASES, PRODUCTS, config_phase, stage
        r, score_kind = utility, utility.NativeUtilityScore
    elif type(specification) is training.NativeTrainingAcquisitionSpecification:
        from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as owner
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_bindings import ARRAY_PHASES, PRODUCTS, config_phase, config_capability_suffix, stage
        r, score_kind = training, training.NativeTrainingScore
    else:
        raise TypeError("native graph read requires its exact TRAIN or E2 specification")
    configs, external, links, _, _ = owner.contracts(specification, request)
    tasks = {value.task_id: value for value in plan.tasks}
    if (len(tasks) != len(plan.tasks) or set(tasks) != {node for node, _ in configs}
            or tuple(value.node_id for value in draft.operations) != tuple(node for node, _ in configs)
            or draft.selected_operation_ids != tuple(node for node, _ in configs)
            or draft.external_inputs != external or draft.links != links
            or draft.campaign != request.campaign or draft.development_study is None
            or draft.development_study != owner.development_root(specification, request, draft.development_study.study_id)):
        raise PermissionError("native Matrix read changes its complete original graph/root/source census")
    for operation, (node, config) in zip(draft.operations, configs, strict=True):
        phase = config_phase(config)
        suffix = config_capability_suffix(config) if r is training else phase
        task = tasks[node]
        selected = operation.selection
        budget = request.resources.for_operation(phase)
        expected_outputs = {("product", PRODUCTS[phase].SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")}
        if phase in ARRAY_PHASES:
            expected_outputs.add(("arrays", r.MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"))
        if phase == "prefix":
            expected_outputs.add(("checkpoint", r.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"))
        if phase == "response-score":
            expected_outputs.add(("score", score_kind.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"))
        actual_outputs = {(value.output_id.removeprefix(node + "."), value.payload_schema, value.profile, value.media_type)
            for value in task.outputs}
        if (operation.config_id != config.record_id or operation.config_payload.encode() != config.canonical_bytes()
                or selected.capability_key != r.NAMESPACE + "." + suffix or selected.capability_version != "1.0.0"
                or operation.resource_budget != budget or task.capability.requested_resources != budget
                or task.stage is not stage(phase) or task.capability.capability_key != selected.capability_key
                or task.capability.capability_version != selected.capability_version
                or task.capability_implementation_sha256 != selected.implementation_sha256
                or task.capability.requested_evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE
                or task.capability.requested_outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or task.capability.config.config_id != config.record_id
                or task.capability.config.config_schema != config.SCHEMA
                or task.capability.config.content_sha256 != config.fingerprint()
                or operation.resource_lock_ids or operation.maximum_attempts != 1
                or operation.obligation_ids != ("obligation." + node + ".complete-selected-scope",)
                or task.resource_lock_ids or task.maximum_attempts != operation.maximum_attempts
                or task.obligation_ids != operation.obligation_ids or actual_outputs != expected_outputs
                or len(task.outputs) != len(expected_outputs)
                or task.barrier is not (BarrierKind.FREEZE if phase in ("entry", "physical-forecast") else BarrierKind.NONE)):
            raise PermissionError("native Matrix read changes an original operation/configuration/resource binding")
    return dict(configs), tasks
