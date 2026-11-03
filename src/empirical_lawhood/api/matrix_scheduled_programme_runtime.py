# SPDX-License-Identifier: MPL-2.0
"""Original issued custody preparation for bounded programme pure workers.

No current or prior authority is inferred from the handoff, a digest or a
proposed plan. Preparation runs only in the parent executor against actual
stored grants, original issued sources, actual plans and successful receipts.
"""
from dataclasses import replace

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody, CurrentIssuedTaskCustodySupplier
from empirical_lawhood.api.current_result_custody import require_current_result_receipt_outputs
from empirical_lawhood.api.recursive_qualified_parents import (
    _authenticate, _authenticate_prior_execution,
    _output_payload, _semantic_writer,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort

from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_calibration import (
    CALIBRATE_TASK_ID, MAXIMUM_CALIBRATION_BYTES, QUALIFY_TASK_ID,
    ScheduledProgrammeCalibrationConfig, ScheduledProgrammeCalibrationEvidence,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_confirmation import (
    ScheduledProgrammeAuthenticatedParent, ScheduledProgrammeConfirmationGlobalConfig,
    ScheduledProgrammeConfirmationGlobalCommitter,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_qualified_parent import (
    _validate_prior_products, prior_execution_bindings, prior_execution_scope_validator,
    validate_qualified_parent_declaration_evidence,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_runtime_views import (
    ScheduledProgrammeCurrentCalibration, ScheduledProgrammeVerifiedCalibrationCustody,
)


def authenticate_programme_qualified_parent(writer, bank, declaration, output_codecs, *, read_scope=None):
    product, = (p for p in declaration.contribution.products if p.product_id == declaration.binding.product_id)
    parent = _authenticate(declaration.binding, declaration.contribution, product, writer, output_codecs,
        qualified_parent_evidence_schema_ids=(ScheduledProgrammeCalibrationEvidence.SCHEMA,), read_scope=read_scope)
    requests = prior_execution_bindings(parent)
    prior = tuple(_authenticate_prior_execution(request, writer, output_codecs,
        scope_validator=prior_execution_scope_validator, parent_evidence=parent, read_scope=read_scope) for request in requests)
    parent = replace(parent, prior_executions=prior)
    validate_qualified_parent_declaration_evidence(bank, declaration, parent)
    return ScheduledProgrammeAuthenticatedParent(declaration.identity,
        ObjectIdentity.from_record(bank.bank_id, bank), ObjectIdentity.from_record(parent.package.package_id, parent.package),
        ObjectIdentity.from_record(parent.execution_plan.execution_plan_id, parent.execution_plan),
        ObjectIdentity.from_record(parent.producing_receipt.receipt_id, parent.producing_receipt),
        ObjectIdentity.from_record(parent.qualification_receipt.receipt_id, parent.qualification_receipt),
        ObjectIdentity.from_record(parent.adjudication.adjudication_id, parent.adjudication), declaration.evidence)


class ProgrammeRuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    """API-owned selected custody port; exact operand supply remains unchanged."""
    def __init__(self, supplier, *, writer, output_codecs, reveal_authority_id=None, custody=None):
        if reveal_authority_id is not None:
            validate_stable_id(reveal_authority_id)
        self.supplier = supplier
        self.writer = writer
        self.output_codecs = dict(output_codecs)
        self.reveal_authority_id = reveal_authority_id
        if custody is not None and (type(custody) is not CurrentIssuedTaskCustody
                or custody.writer is not writer or custody.reveal_authority_id != reveal_authority_id):
            raise TypeError("programme custody changes its exact writer or reveal selection")
        self.custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id) if custody is None else custody

    def resolve_input(self, spec):
        return self.supplier.resolve_input(spec)

    def _current(self, context, runner):
        return self.custody.current_task(context, runner)

    def _inputs(self, context, task):
        return self.custody.task_inputs(context, task)

    def _control(self, manifest, record_type, maximum):
        return self.custody.control_record(manifest, record_type, maximum)

    def prepare_factorial_task(self, context, runner):
        from empirical_lawhood.api.matrix_scheduled_factorial_runtime import prepare_factorial_task
        with self.custody.preparation_scope():
            return prepare_factorial_task(self, context, runner)

    def prepare_matrix_sampling(self, context, runner):
        from empirical_lawhood.api.matrix_sampling_runtime import prepare_matrix_sampling
        with self.custody.preparation_scope():
            return prepare_matrix_sampling(self, context, runner)

    def prepare_selected_matrix(self, context, runner):
        from empirical_lawhood.api.matrix_selected_runtime import prepare_selected_matrix
        with self.custody.preparation_scope():
            return prepare_selected_matrix(self, context, runner)

    def prepare_revision_future(self, context, runner):
        from empirical_lawhood.api.matrix_revision_runtime import prepare_revision_future
        with self.custody.preparation_scope():
            return prepare_revision_future(self, context, runner)

    def prepare_revision_calibration(self, context, runner):
        from empirical_lawhood.api.matrix_revision_calibration_runtime import prepare_revision_calibration
        with self.custody.preparation_scope():
            return prepare_revision_calibration(self, context, runner)

    def prepare_programme_task(self, context, runner):
        with self.custody.preparation_scope():
            current = self._current(context, runner)
            with self.custody.original_read_scope() as (writer, read_scope):
                return self._prepare_programme_task(context, runner, writer, read_scope, current)

    def _prepare_programme_task(self, context, runner, original_writer, read_scope, current):
        package, plan, task = current
        def current_result(result):
            if self._current(context, runner) != (package, plan, task):
                raise PermissionError("programme authority or original issued task changed during preparation")
            return result
        by_task, controls = self._inputs(context, task)
        if type(runner) is ScheduledProgrammeConfirmationGlobalCommitter:
            config = self._control(controls[context.config.artifact_id], ScheduledProgrammeConfirmationGlobalConfig, 4*1024**2)
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import ScheduledCompactBank
            bank = self._control(controls[config.bank.object_id], ScheduledCompactBank, 16*1024**2)
            parent = authenticate_programme_qualified_parent(original_writer, bank, config.qualified_parent, self.output_codecs, read_scope=read_scope)
            return current_result(ScheduledProgrammeConfirmationGlobalCommitter(runner.manifest, parent))
        if context.task_id != QUALIFY_TASK_ID:
            raise PermissionError('programme preparation refuses an undeclared runtime role')
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_calibration_bindings import ScheduledProgrammeCalibrator
        if type(runner) is not ScheduledProgrammeCalibrator or runner.role != 'calibration-qualify':
            raise PermissionError('programme preparation refuses a foreign qualifier implementation')
        config = self._control(controls[context.config.artifact_id], ScheduledProgrammeCalibrationConfig, 4*1024**2)
        producing = by_task.get(CALIBRATE_TASK_ID)
        if producing is None:
            raise PermissionError('programme qualifier lacks its actual current global producer')
        logical, = (p for p in producing.output_logical_artifacts if p.payload_schema == ScheduledProgrammeCalibrationEvidence.SCHEMA)
        require_current_result_receipt_outputs(receipt=producing, logical=logical, execution_plan=plan,
            capability_prefixes=(runner.manifest.capability_key.rsplit('.', 1)[0]+'.',))
        writer = _semantic_writer(package, plan, original_writer, self.output_codecs)
        raw = _output_payload(writer, producing, logical, MAXIMUM_CALIBRATION_BYTES)
        evidence = decode_canonical_bytes(raw, ScheduledProgrammeCalibrationEvidence, maximum_bytes=MAXIMUM_CALIBRATION_BYTES)
        if (evidence.canonical_bytes() != raw or evidence.configuration != replace(config,
                config_id=config.config_id.rsplit('.', 1)[0]+'.calibrate', operation='calibrate')):
            raise PermissionError('programme qualifier substitutes its actual current producer companion')
        source = ScheduledProgrammeCurrentCalibration(package, plan, producing, evidence)
        prior = tuple(_authenticate_prior_execution(request, writer, self.output_codecs,
            scope_validator=prior_execution_scope_validator, parent_evidence=source, read_scope=read_scope) for request in prior_execution_bindings(source))
        source = replace(source, prior_executions=prior)
        _validate_prior_products(source, evidence)
        view = ScheduledProgrammeVerifiedCalibrationCustody(ObjectIdentity.from_record(config.config_id, config),
            config.programme.identity, config.bank, ObjectIdentity.from_record(plan.execution_plan_id, plan),
            ObjectIdentity.from_record(task.task_id, task), ObjectIdentity.from_record(producing.receipt_id, producing),
            evidence.identity, context.input_materialization_ids, context.dependency_receipt_ids,
            tuple(ObjectIdentity.from_record(p.binding.binding_id, p.binding) for p in prior))
        return current_result(ScheduledProgrammeCalibrator(runner.role, runner.manifest, verified_custody=view))


def bind_programme_runtime_handoff(handoff, *, writer, reveal_authority_id=None):
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    ports = []
    custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id)
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError('programme handoff changes its installed exact input port')
        supplier = ProgrammeRuntimeInputSupplier(platform.port.supplier, writer=writer,
            output_codecs=handoff.compilation.output_codecs, reveal_authority_id=reveal_authority_id, custody=custody)
        ports.append(ExecutablePlatformPort(platform.port_key, RecursiveOperationInputPort(supplier)))
    return replace(handoff, platform_ports=tuple(ports))
