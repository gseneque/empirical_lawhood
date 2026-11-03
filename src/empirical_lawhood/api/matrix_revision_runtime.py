# SPDX-License-Identifier: MPL-2.0
"""Current issued native preparation with actual original E4 seal custody.

This API composes existing current-task and prior-execution readers. It creates
no issue, grant, publication, qualification or native execution of its own.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history import operation_bindings as core, response_bindings as response
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_bindings import ScheduledProgrammeAcquisitionAdmission
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_custody import validate_acquisition_operation_census
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_future_bindings import (
    BLIND, MAXIMUM_RECORD_BYTES, ROLES, AuthenticatedRevisionFuture, ScheduledRevisionFutureScope,
    ScheduledRevisionSealCustody, prepared_runner,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration import ScheduledRevisionForecastSeal
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_seal_custody import prior_seal_scope_validator
from empirical_lawhood.api.current_task_custody import issued_custody_for_supplier
from empirical_lawhood.api.recursive_qualified_parents import _authenticate_prior_execution
from empirical_lawhood.kernel.provenance import ObjectIdentity


def prepare_revision_future(supplier, context, runner):
    """Fresh current grants precede every original source and producer read."""
    expected_type = response.ScheduledPulseNativeRunner if getattr(runner, "role", None) == "responses" else core.ScheduledNativeRunner
    if type(runner) is not expected_type or runner.role not in ROLES:
        raise PermissionError("revision future preparation requires its actual installed original native worker")
    current = issued_custody_for_supplier(supplier)
    package, plan, task = current.current_task(context, runner)
    receipts, controls = current.task_inputs(context, task)

    def record(name, kind):
        links = tuple(row for row in task.scientific_inputs if row.consumer_input_id == name)
        if len(links) != 1:
            raise PermissionError("revision future preparation loses its actual scientific prerequisite edge")
        manifest = controls.get(links[0].operational_logical_artifact_id)
        if manifest is None or manifest.logical.payload_schema != kind.SCHEMA:
            raise PermissionError("revision future preparation substitutes its actual persisted prerequisite")
        return current.control_record(manifest, kind, MAXIMUM_RECORD_BYTES)

    scope = record("revision-scope", ScheduledRevisionFutureScope)
    calibration_custody = None
    if scope.calibration is not None:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibrated_future_bindings import NAMESPACE as CALIBRATED_NAMESPACE
        if not runner.manifest.capability_key.startswith(CALIBRATED_NAMESPACE + "."):
            # The historical variant never accepts an undeclared extra parent.
            raise PermissionError("SOFTWARE: genuine original E4 revision-CAL producer custody is not installed for confirmation futures")
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration_custody import ScheduledRevisionCalibrationCustody
        from empirical_lawhood.api.matrix_revision_calibration_runtime import authenticate_revision_calibration
        from empirical_lawhood.api.recursive_operations import operation_catalog
        calibration_custody = record("revision-calibration-custody", ScheduledRevisionCalibrationCustody)
        with current.original_read_scope() as (writer, read_scope):
            authenticate_revision_calibration(writer=writer, custody=calibration_custody, future=scope,
                codecs=operation_catalog()[2], read_scope=read_scope)
            writer.require_verification_snapshot()
    elif runner.manifest.capability_key.startswith("matrix-scheduled-revision-calibrated-future."):
        raise PermissionError("calibrated revision future cannot bypass its actual original-CAL parent")
    custody = record("revision-custody", ScheduledRevisionSealCustody)
    seal = record("revision-seal", ScheduledRevisionForecastSeal)
    if seal != custody.forecast or seal != scope.forecast(seal.case_id, record_id=seal.record_id):
        raise PermissionError("revision future preparation substitutes its original frozen prediction")
    admission_edges = tuple(row for row in task.scientific_inputs if row.consumer_input_id == "admission")
    if len(admission_edges) != 1 or admission_edges[0].producer_task_id is None:
        raise PermissionError("revision future preparation loses the actual admitted native wave")
    admission_receipt = receipts.get(admission_edges[0].producer_task_id)
    if admission_receipt is None:
        raise PermissionError("revision future preparation lacks its actual successful wave admission")
    # The worker independently checks original admission bytes. Current input
    # custody has already authenticated this receipt and full dependency set.
    if not any(row.payload_schema == ScheduledProgrammeAcquisitionAdmission.SCHEMA
            for row in admission_receipt.output_logical_artifacts):
        raise PermissionError("revision future preparation substitutes the actual original admission producer")
    wave = next((row for row in scope.programme.waves if seal.case_id in row.root_ids), None)
    if wave is None:
        raise PermissionError("revision future preparation changes its complete assigned wave")
    validate_acquisition_operation_census(scope.programme, wave, "collect", plan, revision_scope=scope)
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication

    _, _, installed = operation_catalog()
    with current.original_read_scope() as (writer, read_scope):
        original = _authenticate_prior_execution(custody.prior_execution, writer, installed,
            scope_validator=prior_seal_scope_validator, parent_evidence=(scope, custody), required_outcome_access=BLIND, read_scope=read_scope)
        if (original.product.payload != seal.canonical_bytes() or original.product.logical != custody.publication.logical
                or original.product.materialization != custody.publication.materialization
                or tuple(row for row in original.receipts if row.task_id == custody.receipt.task_id) != (custody.receipt,)):
            raise PermissionError("revision future preparation substitutes actual original producing bytes or current receipt")
        authenticate_publication(writer, custody.receipt_publication, custody.receipt)
        writer.require_verification_snapshot()
    if current.current_task(context, runner) != (package, plan, task):
        raise PermissionError("revision current grant, issued source or task changed during prior replay")
    view = AuthenticatedRevisionFuture(context.run_id, context.task_id, context.input_materialization_ids,
        ObjectIdentity.from_record(plan.execution_plan_id, plan), scope.identity, seal.identity,
        ObjectIdentity.from_record(custody.prior_execution.binding_id, custody.prior_execution))
    if calibration_custody is not None:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibrated_future_bindings import prepared_runner as calibrated_runner
        return calibrated_runner(runner, view, calibration_custody.identity)
    return prepared_runner(runner, view)
