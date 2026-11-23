# SPDX-License-Identifier: MPL-2.0
"""Select the complete issued projection census for a nonacquiring calibration completion."""

from hashlib import sha256

from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedCalibrationViewObservation
from empirical_lawhood.domains.matrix.finite_response_law.completion.contracts import FiniteResponseLawAssignedCalibrationRetainedConfig, FiniteResponseLawRetainedProjection
from empirical_lawhood.domains.matrix.finite_response_law.native_provider import EVALUATOR_TASK_ID
from empirical_lawhood.execution.recovery import RunRecoveryIndex
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.storage.artifact_sidecars import read_artifact_sidecar
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.recovery import ExternalRunRecoveryStore
from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore


def retained_calibration_operands(packet, publication, artifact_writer):
    """Authenticate the original issue, failed terminal and every winning receipt.

    The original terminal stays in custody. Only its sealed view reports and their
    receipts are copied as scientific operands. The new study has zero native tokens.
    """
    from empirical_lawhood.api import finite_rerun_authoring as app

    if packet.stage != "calibration":
        raise ValueError("Retained measurements require the original calibration selection")
    source = packet.source
    run_id = publication.run_id
    with artifact_writer.read_context() as plane:
        issued, _, (package, _, plan) = app._authenticate_current_publication(
            publication, plane, expected_run=run_id, include_controls=True)
        app._require_issued_source(issued, source, plane)
        recovery = ExternalRunRecoveryStore(plane)
        relative = f"runs/{run_id}/recovery/wave.{package.package_id}/resource-run-recovery-index.json"
        index = recovery.read_index(relative, expected_schema=RunRecoveryIndex.SCHEMA)
        terminal = recovery.read_terminal(index)
        tasks = {task.task_id: task for task in plan.tasks}
        bindings = {binding.task_id: binding for binding in index.tasks}
        view_ids = tuple(f"{root.root_id}.flh-project.r{view}" for root in source.roots for view in (1, 2))
        if (index.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan)
                or index.implementation_commit != issued.source_closure.implementation_commit
                or terminal is None or terminal.run_id != run_id or terminal.operational_status != "FAILED"
                or terminal.blocked_task_ids or terminal.failed_task_ids != (EVALUATOR_TASK_ID,)
                or set(terminal.completed_task_ids) != tasks.keys() - {EVALUATOR_TASK_ID}
                or tasks.keys() != bindings.keys() or len(terminal.attempts) != len(tasks)
                or tuple(tasks[EVALUATOR_TASK_ID].dependency_task_ids) != view_ids
                or any(len(binding.attempts) != 1 for binding in bindings.values())):
            raise ValueError("Retained calibration requires the single failed evaluator after every original acquisition and view")
        cells = {cell.task_id: cell for cell in package.execution_resource_envelope_spec.task_cells}
        if (cells.keys() != tasks.keys() or cells[EVALUATOR_TASK_ID].native_simulator_launch
                or any(cells[task].native_simulator_launch != (task not in view_ids and task != EVALUATOR_TASK_ID)
                       for task in tasks)):
            raise ValueError("Retained calibration changes the original native task census")
        selected = {row.task_id: row for row in terminal.attempts}
        if selected.keys() != tasks.keys():
            raise ValueError("Retained calibration terminal repeats or loses an original task")
        failure = recovery.read_event(index, bindings[EVALUATOR_TASK_ID].attempts[0].event_relative_path)
        if (failure is None or failure.attempt_id != selected[EVALUATOR_TASK_ID].attempt_id
                or failure.failure is None or failure.failure.sanitized_exception_type != "ArtifactIdentityConflict"
                or failure.failure.failure_class.value != "PROVIDER_RUNNER_DEFECT"):
            raise ValueError("Retained calibration lacks its original technical evaluator failure")
        retained_outputs = {m for task in view_ids for m in tasks[task].dependency_task_ids}
        if retained_outputs != tasks.keys() - set(view_ids) - {EVALUATOR_TASK_ID}:
            raise ValueError("The retained views must cover every original native task")
        receipts = ExternalTaskReceiptStore(plane)
        seals = []
        for task_id in terminal.completed_task_ids:
            original = selected[task_id]
            candidate, = bindings[task_id].attempts
            receipt = receipts.read(run_id, task_id, candidate.attempt_id)
            if (receipt is None or original.attempt_id != candidate.attempt_id
                    or receipt.receipt_id != original.receipt_id or receipt.fingerprint() != original.receipt_sha256):
                raise ValueError("Retained calibration lost an original successful receipt")
            recovery._validate_receipt_static(index, tasks[task_id], candidate, receipt)
            if task_id in view_ids:
                manifests = tuple(read_artifact_sidecar(plane, m.relative_path + ".manifest.json",
                    maximum_bytes=plane.custody_limits.manifest_bytes) for m in receipt.output_materializations)
                if ({m.logical for m in manifests} != set(receipt.output_logical_artifacts)
                        or {m.materialization for m in manifests} != set(receipt.output_materializations)):
                    raise ValueError("Retained calibration view differs from its complete original publication")
                seals.append((receipt, manifests))
        app._require_current_grants(publication, plane)
        app._verify_current_task_manifests(plane, tuple(m for _, siblings in seals for m in siblings),
            tuple((package, tasks[r.task_id]) for r, _ in seals))
        inputs, rows = {}, []
        for receipt, siblings in seals:
            app._require_current_grants(publication, plane)
            report, = (m for m in siblings if m.logical.payload_schema == FiniteResponseLawAssignedCalibrationViewObservation.SCHEMA)
            path = plane.root.resolve(report.materialization.relative_path, for_write=False)
            raw = read_bounded_bytes(path, maximum_bytes=report.materialization.size_bytes)
            if (len(raw) != report.materialization.size_bytes
                    or sha256(raw).hexdigest() != report.logical.content_sha256
                    or report.materialization.physical_sha256 != report.logical.content_sha256):
                raise ValueError("Retained calibration view differs from its original canonical bytes")
            body = ArtifactIdentity(report.logical.logical_artifact_id, "retained-calibration-view",
                report.logical.payload_schema, report.logical.content_sha256, report.logical.media_type, len(raw))
            receipt_bytes = receipt.canonical_bytes()
            witness = ArtifactIdentity(receipt.receipt_id, "retained-calibration-receipt", receipt.SCHEMA,
                selected[receipt.task_id].receipt_sha256, "application/json", len(receipt_bytes))
            rows.append(FiniteResponseLawRetainedProjection(receipt.task_id, body, witness,
                ObjectIdentity.from_record(receipt.receipt_id, receipt)))
            inputs[body.artifact_id], inputs[witness.artifact_id] = raw, receipt_bytes
        app._require_current_grants(publication, plane)
        cls = FiniteResponseLawAssignedCalibrationRetainedConfig
        config = cls(f"{cls.PREFIX_ID}.config", source, run_id, index.implementation_commit,
            tuple(sorted(rows, key=lambda row: row.task_id)), publication.issued_study,
            publication.execution_authority, publication.reveal_authority,
            ObjectIdentity.from_record(terminal.terminal_event_id, terminal))
        return config, inputs
