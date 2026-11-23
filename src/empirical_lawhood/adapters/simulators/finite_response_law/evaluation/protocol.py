"Complete finite response-law evaluation acquisition/control graph, ending sealed before recovery/reveal."

from dataclasses import replace
from math import ceil

from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.source_qualification import PredecessorBoundSourceQualificationExperiment
from empirical_lawhood.execution.capabilities import CapabilityPermission
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.plans import BarrierKind, ProtocolStepTemplate, ScientificStage
from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.domains.matrix.finite_response_law.evaluation_results import FiniteResponseLawEvaluationRevealConfig, FiniteResponseLawEvaluationCohort, COHORT, ADJUDICATE, reveal_tasks
from empirical_lawhood.domains.matrix.finite_response_law.evaluation_provider import reveal_dependencies
from empirical_lawhood.domains.matrix.finite_response_law.control_reveal import FiniteResponseLawProspectiveRootEvaluation
from empirical_lawhood.domains.matrix.finite_response_law.evaluation_readout import FiniteResponseLawRootInferenceOperands
from empirical_lawhood.execution.protocol_helpers import capability_config_ref as _config_ref, protocol_outputs as _outputs
from empirical_lawhood.domains.matrix.finite_response_law.control_provider import control_tasks, control_dependencies, CONTROL_RECORDS, OPERATIONS
from empirical_lawhood.domains.matrix.finite_response_law.control_records import FiniteResponseLawControlConfig
from empirical_lawhood.domains.matrix.finite_response_law.method_records import FiniteResponseLawAssignedQualificationReport
from empirical_lawhood.domains.matrix.finite_response_law.control_closeout import FiniteResponseLawRootSealedControl
from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedEvaluationProjectionConfig, FiniteResponseLawAssignedEvaluationCompletionConfig, FiniteResponseLawAssignedEvaluationViewObservation, FiniteResponseLawAssignedEvaluationNativeCompletion
from empirical_lawhood.domains.matrix.finite_response_law.native_provider import EVALUATOR_TASK_ID
from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import FiniteResponseLawAssignedEvaluationConfig
from empirical_lawhood.domains.matrix.finite_response_law.contracts import native_invocations
from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_retention import FiniteResponseLawEvaluationRetention
from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_provider import control_dependency
from empirical_lawhood.adapters.simulators.finite_response_law.source_outputs import FiniteResponseLawAssignedEvaluationTaskResult
from empirical_lawhood.adapters.simulators.finite_response_law.native_artifact import NATIVE_PAIR_SCHEMA
from empirical_lawhood.adapters.simulators.finite_response_law.evaluation.discovery import SOURCE_CAPABILITY, PROJECTION_CAPABILITY, EVALUATION_CAPABILITY, CONTROL_CAPABILITY, REVEAL_CAPABILITY


def evaluation_protocol_steps(
    source: FiniteResponseLawAssignedEvaluationConfig,
    carrier: PredecessorBoundSourceQualificationExperiment,
    projection: FiniteResponseLawAssignedEvaluationProjectionConfig,
    completion: FiniteResponseLawAssignedEvaluationCompletionConfig,
    control: FiniteResponseLawControlConfig,
    reveal: FiniteResponseLawEvaluationRevealConfig,
    retention: FiniteResponseLawEvaluationRetention | None = None,
) -> tuple[ProtocolStepTemplate, ...]:
    if retention is not None and retention.source != source:
        raise ValueError("Finite response-law evaluation retention substitutes its original source")
    if (
        projection.native_spec != source
        or completion.projection != projection
        or control.source != source
        or reveal.control != control
        or carrier.projection_config != ObjectIdentity.from_record(projection.config_id, projection)
        or carrier.evaluator_config != ObjectIdentity.from_record(completion.config_id, completion)
        or carrier.source_config != ObjectIdentity.from_record(source.spec_id, source)
        or carrier.projection_capability
        != ObjectIdentity.from_record(PROJECTION_CAPABILITY.capability_key, PROJECTION_CAPABILITY)
        or carrier.evaluator_capability
        != ObjectIdentity.from_record(EVALUATION_CAPABILITY.capability_key, EVALUATION_CAPABILITY)
    ):
        raise ValueError(
            "Finite response-law evaluation protocol substitutes its exact source/control/projection configuration"
        )
    from empirical_lawhood.adapters.simulators.finite_response_law.locked_evaluation import FiniteResponseLawLockedEvaluationRetention
    locked = retention if isinstance(retention, FiniteResponseLawLockedEvaluationRetention) else None
    native = {t.task_id: t for t in native_invocations(source)}
    controls = control_tasks(control)
    projections = {f"{r.root_id}.flh-project.r{v}": r for r in source.roots for v in (1, 2)}
    closures = {f"{r.stage_unit}.seal-control": r for r in source.roots}
    bounds = {
        task_id: SOURCE_CAPABILITY.resource_ceiling.output_bytes
        if t.phase == "prefix"
        else 5 * 512 * 1024
        for task_id, t in native.items()
    }
    bounds.update(
        {task_id: PROJECTION_CAPABILITY.resource_ceiling.output_bytes for task_id in projections}
    )
    bounds.update(
        {
            task_id: (
                8 * 1024**2
                if op in ("forecast", "freeze-prior")
                else 1024**2
                if op == "reveal-request"
                else CONTROL_CAPABILITY.resource_ceiling.output_bytes
            )
            for task_id, (_, op) in controls.items()
        }
    )
    bounds[EVALUATOR_TASK_ID] = EVALUATION_CAPABILITY.resource_ceiling.output_bytes
    bounds.update(
        {task_id: EVALUATION_CAPABILITY.resource_ceiling.output_bytes for task_id in closures}
    )
    reveals = set(reveal_tasks(reveal))
    bounds.update({task_id: REVEAL_CAPABILITY.resource_ceiling.output_bytes for task_id in reveals})
    if locked is not None:
        # Import products have their original exact sizes, including both native views.
        bounds.update({key: sum(a.size_bytes for a in members[:-1]) for key, members in locked.import_inputs.items()})
    steps = []
    config: CanonicalRecord
    for task_id in sorted(bounds):
        prior_bytes = 0
        if task_id in native:
            invocation = native[task_id]
            guard = control_dependency(invocation)
            dependencies = tuple(
                sorted((*invocation.dependency_task_ids, *((guard,) if guard else ())))
            )
            manifest, config, config_id = SOURCE_CAPABILITY, source, source.spec_id
            stage = ScientificStage.PREPARE
            outputs = _outputs(
                (
                    ("native-result", FiniteResponseLawAssignedEvaluationTaskResult.SCHEMA),
                    ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                ),
                ("native-observations", NATIVE_PAIR_SCHEMA),
            )
            access = (
                OutcomeAccess.EVALUATION_SEALED
                if invocation.phase == "future"
                else OutcomeAccess.OUTCOME_BLIND
            )
            wall = ceil(2 + invocation.maximum_native_updates * 0.004)
            barrier = BarrierKind.NONE
            copies = 2 if invocation.phase == "prefix" else 1
            # Native guards verify six durable parent locks in addition to the
            # receipted graph input. They do not reread compiled programmes.
            prior_bytes = 12 * 1024**2 if guard else 0
            if retention is not None:
                from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_continuation.discovery import SOURCE_CAPABILITY as CONTINUATION_SOURCE, IMPORT_CAPABILITY

                manifest = CONTINUATION_SOURCE
                if invocation.phase == "prefix":
                    prior = next(p for p in retention.prefixes if p.segment_id == task_id)
                    manifest, config, config_id = IMPORT_CAPABILITY, retention, retention.config_id
                    stage, wall, copies, barrier = ScientificStage.FREEZE, 30, 1, BarrierKind.FREEZE
                    prior_bytes = sum(a.size_bytes for a in (*prior.artifacts, prior.task_receipt))
                    outputs = _outputs(
                        (
                            ("product", FiniteResponseLawAssignedEvaluationTaskResult.SCHEMA),
                            ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                        ),
                        ("native-observations", NATIVE_PAIR_SCHEMA),
                    )
        elif task_id in controls:
            index, operation = controls[task_id]
            manifest, config, config_id = CONTROL_CAPABILITY, control, control.config_id
            dependencies = control_dependencies(control, index, operation)
            stage = ScientificStage.CONTROLLER
            output_type = (
                FiniteResponseLawAssignedQualificationReport
                if operation == "freeze-prior"
                else CONTROL_RECORDS[OPERATIONS.index(operation)]
            )
            outputs = _outputs((("product", output_type.SCHEMA),))
            # Per-operation ceilings: lightweight request publication does not
            # reserve a full six-controller compilation budget.
            access, wall, copies = (
                OutcomeAccess.OUTCOME_BLIND,
                {
                    "freeze-prior": 30,
                    "forecast": 30,
                    "reveal-request": 5,
                    "lock-choices": 180,
                    "join-parent": 120,
                }[operation],
                1,
            )
            barrier = (
                BarrierKind.FREEZE
                if operation in ("forecast", "lock-choices", "freeze-prior")
                else BarrierKind.NONE
            )
            if operation in ("forecast", "lock-choices", "freeze-prior"):
                prior_bytes = sum(a.size_bytes for a in control.inputs) + 16 * 1024**2
            elif operation == "join-parent":
                prior_bytes = 6 * 16 * 1024**2 + 12 * 1024**2
        elif task_id in projections:
            manifest, config, config_id = PROJECTION_CAPABILITY, projection, projection.config_id
            dependencies = tuple(
                sorted(t.task_id for t in native.values() if t.root == projections[task_id])
            )
            stage = ScientificStage.TRANSFORM
            outputs = _outputs(
                (
                    ("product", FiniteResponseLawAssignedEvaluationViewObservation.SCHEMA),
                    ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA),
                )
            )
            access, wall, copies, barrier = (
                OutcomeAccess.EVALUATION_SEALED,
                120,
                1,
                BarrierKind.FREEZE,
            )
        elif task_id in reveals:
            manifest, config, config_id = REVEAL_CAPABILITY, reveal, reveal.config_id
            dependencies = reveal_dependencies(reveal, task_id)
            if task_id == ADJUDICATE:
                outputs = _outputs((("product", ScientificAdjudicationRecord.SCHEMA),))
                stage, access = ScientificStage.EVALUATE, OutcomeAccess.EVALUATOR_REVEAL
            elif task_id == COHORT:
                outputs = _outputs((("product", FiniteResponseLawEvaluationCohort.SCHEMA),))
                stage, access = ScientificStage.EVALUATE, OutcomeAccess.EVALUATOR_REVEAL
            else:
                outputs = _outputs(
                    (
                        ("product", FiniteResponseLawProspectiveRootEvaluation.SCHEMA),
                        ("scalar", FiniteResponseLawRootInferenceOperands.SCHEMA),
                    )
                )
                stage, access = ScientificStage.EVALUATE, OutcomeAccess.EVALUATOR_REVEAL
                prior_bytes = 6 * 16 * 1024**2
            wall, copies, barrier = 120, 1, BarrierKind.REVEAL
        else:
            manifest, config, config_id = EVALUATION_CAPABILITY, completion, completion.config_id
            dependencies = (
                tuple(sorted((*projections, *closures)))
                if task_id == EVALUATOR_TASK_ID
                else tuple(
                    sorted(
                        (
                            f"{closures[task_id].stage_unit}.join-parent",
                            *(f"{closures[task_id].root_id}.flh-project.r{v}" for v in (1, 2)),
                        )
                    )
                )
            )
            stage = ScientificStage.FREEZE
            outputs = _outputs(
                (
                    (
                        "product",
                        FiniteResponseLawAssignedEvaluationNativeCompletion.SCHEMA
                        if task_id == EVALUATOR_TASK_ID
                        else FiniteResponseLawRootSealedControl.SCHEMA,
                    ),
                )
            )
            access, wall, copies, barrier = (
                OutcomeAccess.EVALUATION_SEALED,
                120,
                1,
                BarrierKind.FREEZE,
            )
        if locked is not None and task_id in locked.import_inputs:
            from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_continuation.discovery import LOCKED_IMPORT_CAPABILITY
            manifest, config, config_id = LOCKED_IMPORT_CAPABILITY, locked, locked.config_id
            stage, access, barrier = ScientificStage.FREEZE, OutcomeAccess.OUTCOME_BLIND, BarrierKind.FREEZE
            dependencies, wall, copies = locked.import_dependencies[task_id], 30, 1
            members = locked.import_inputs[task_id]
            prior_bytes = sum(a.size_bytes for a in members)
            if task_id.endswith(".lock-choices"):
                # Original and continued prepared-event stores both authenticate the lock subjects.
                prior_bytes += 8 * members[0].size_bytes
            if task_id in native:
                outputs = _outputs(
                    (("product", FiniteResponseLawAssignedEvaluationTaskResult.SCHEMA), ("stage-envelope", LinkedCampaignStageEnvelope.SCHEMA)),
                    ("native-observations", NATIVE_PAIR_SCHEMA),
                )
        scan = (
            copies * len(config.canonical_bytes())
            + prior_bytes
            + sum(bounds[d] for d in dependencies)
        )
        if scan > manifest.resource_ceiling.source_scan_bytes:
            raise ValueError(f'Finite response-law evaluation exact source/control scan exceeds declared bound: {task_id}')
        permissions = tuple(
            p
            for p in manifest.permissions
            if (
                access is not OutcomeAccess.OUTCOME_BLIND
                or p is not CapabilityPermission.READ_SEALED_OUTCOMES
            )
        )
        steps.append(
            ProtocolStepTemplate(
                task_id,
                stage,
                manifest.capability_key,
                manifest.capability_version,
                _config_ref(config, ObjectIdentity.from_record(config_id, config), manifest),
                dependencies,
                outputs,
                permissions,
                access,
                VisibilityCeiling.PROSPECTIVE,
                replace(
                    manifest.resource_ceiling,
                    source_scan_bytes=scan,
                    output_bytes=bounds[task_id],
                    wall_time_seconds=wall,
                ),
                (),
                barrier,
                1,
                ("finite-response-law.prospective-evaluation.single-terminal",)
                if task_id == COHORT
                else (f"custody.{task_id}",),
            )
        )
    if len(steps) != 1796:
        raise ValueError(
            "Finite response-law evaluation protocol changes its sealed 1730-task census plus 64 controller-use roots/cohort/adjudication"
        )
    return tuple(steps)
