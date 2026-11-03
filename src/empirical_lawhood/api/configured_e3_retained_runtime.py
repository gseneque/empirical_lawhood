# SPDX-License-Identifier: MPL-2.0
"""Hold original E3 custody through the continued public execution lifetime."""
from contextlib import contextmanager

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_bindings import ConfiguredE3RetainedTaskRunner, retained_input_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import ConfiguredE3RetainedTaskConfig
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges

from .configured_e3_retained_custody import _active_original_reads, read_original_partial_e3
from .matrix_selected_runtime import _issued_configuration_lane


class RetainedE3ExecutionScope:
    """One bounded original reader; fresh original/current grants at each task."""

    def __init__(self, *, writer, selection):
        if type(selection) not in (ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection):
            raise TypeError('retained E3 execution requires its exact continued selection')
        selection.__post_init__()
        self.writer, self.selection = writer, selection
        self._active = None
        rows = tuple(value for value in _active_original_reads.get()
            if value.writer.root is writer.root and value.directory == selection.retention.original_authoring_directory
            and value.package.run_plan_id == selection.retention.original_run_id)
        if len(rows) > 1:
            raise PermissionError('retained E3 has ambiguous original read lifetimes')
        self._outer = rows[0] if rows else None
        self._tasks = {row.original_task.task_id: row for row in selection.retained_tasks}

    def _require_selection(self, original):
        expected = self.selection.retention
        retention, tasks = original.continuation(record_id=expected.record_id,
            continued_run_id=expected.continued_run_id, response_provenance=expected.response_provenance)
        if retention != expected or tasks != self.selection.retained_tasks:
            raise PermissionError('retained E3 execution changes its actual authenticated original receipt/configuration census')
        if type(self.selection) is ConfiguredE3UnfinishedPreparationSelection:
            scope = self.selection.unfinished
            if original.unfinished(record_id=scope.record_id, retention=retention) != scope:
                raise PermissionError('unfinished E3 changes its authenticated predecessor or selected tasks')
        if type(self.selection) is ConfiguredE3ClosedPreparationSelection:
            scope = self.selection.closeout
            if original.closeout(record_id=scope.record_id, retention=retention) != scope:
                raise PermissionError('CAL closeout changes its authenticated contacts or selected tasks')

    @contextmanager
    def open(self):
        if self._active is not None:
            self._active.require_access()
            yield self
            self._active.require_access()
            return
        expected = self.selection.retention

        @contextmanager
        def original_scope():
            if type(self.selection) is ConfiguredE3ClosedPreparationSelection:
                from .configured_e3_closeout_custody import read_closed_e3
                scope = self.selection.closeout
                with read_closed_e3(artifact_writer=self.writer, directory=scope.predecessor_authoring_directory,
                        run_id=scope.predecessor_run_id,
                        reveal_authority_id=scope.predecessor_reveal_authority.object_id) as original:
                    yield original
            elif type(self.selection) is ConfiguredE3UnfinishedPreparationSelection:
                from .configured_e3_unfinished_custody import read_unfinished_e3
                scope = self.selection.unfinished
                with read_unfinished_e3(artifact_writer=self.writer, directory=scope.predecessor_authoring_directory,
                        run_id=scope.predecessor_run_id,
                        reveal_authority_id=scope.predecessor_reveal_authority.object_id) as original:
                    yield original
            elif self._outer is not None:
                self._outer.require_access()
                yield self._outer
            else:
                with read_original_partial_e3(artifact_writer=self.writer,
                        directory=expected.original_authoring_directory, run_id=expected.original_run_id,
                        reveal_authority_id=expected.original_reveal_authority.object_id) as original:
                    yield original

        with original_scope() as original:
            self._require_selection(original)
            self._active = original
            try:
                yield self
                original.require_current()
            finally:
                self._active = None

    def require_task(self, config):
        if type(self.selection) in (ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection):
            raise PermissionError('unfinished E3 imports completed outputs and cannot repeat an adoption')
        original = self._active
        if original is None:
            raise PermissionError('retained E3 task lacks its active original custody lifetime')
        original.require_access()
        if self._tasks.get(config.original_task.task_id) != config:
            raise PermissionError('retained E3 task substitutes an original frozen adoption')
        receipt = ExternalTaskReceiptStore(original.writer).read_by_receipt_id(original.package.run_plan_id,
            config.original_task.task_id, config.original_receipt.receipt_id)
        if receipt != config.original_receipt:
            raise PermissionError('retained E3 original successful receipt changed before adoption')
        original.require_access()

    def require_access(self):
        """Refresh the actual retained-original grant during input replay."""
        if self._active is None:
            raise PermissionError('retained E3 input replay lacks its active original custody lifetime')
        self._active.require_access()

    def retained_task_config(self, task_id):
        """Select one actual frozen adoption through this original custody owner."""
        self.require_access()
        try:
            config = self._tasks[task_id]
        except KeyError as error:
            raise PermissionError('retained E3 has no original task for the selected adoption') from error
        self.require_task(config)
        return config


def retained_e3_execution_scope(service, run_id):
    """Select the retained control owner from the actual installed input ports."""
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    from .domain_composition.matrix_configured_protected_response.runtime import ProtectedE3RuntimeInputSupplier
    selected = []
    for platform in service.executable_platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            continue
        supplier = platform.port.supplier
        if type(supplier) is not ProtectedE3RuntimeInputSupplier or supplier.retained_e3_scope is None:
            continue
        scope = supplier.retained_e3_scope
        if (type(scope) is not RetainedE3ExecutionScope
                or scope.selection.retention.continued_run_id != run_id
                or (scope.writer.root.contract.storage_root_id, scope.writer.root.contract.canonical_path)
                != (service.artifact_plane.root.contract.storage_root_id,
                    service.artifact_plane.root.contract.canonical_path)):
            raise PermissionError('retained E3 input replay substitutes its actual retained control owner')
        if not any(scope is previous for previous in selected):
            selected.append(scope)
    if len(selected) != 1:
        raise PermissionError('retained E3 input replay requires one actual retained control owner')
    scope, = selected
    scope.require_access()
    return scope


def retained_e3_input_access_guard(service, run_id):
    scope = retained_e3_execution_scope(service, run_id)
    return scope.require_access


def prepare_retained_task(supplier, context, runner):
    if type(runner) is not ConfiguredE3RetainedTaskRunner or supplier.retained_e3_scope is None:
        raise PermissionError('retained E3 parent preparation requires its installed pure adoption runner')
    with supplier.custody.preparation_scope():
        custody = supplier.custody
        current = custody.current_task(context, runner)
        package, plan, task = current
        _, inputs = custody.task_inputs(context, task)
        manifest = inputs.get(context.config.artifact_id)
        if manifest is None:
            raise PermissionError('retained E3 adoption omits its exact issued configuration')
        config = custody.control_record(
            manifest,
            ConfiguredE3RetainedTaskConfig,
            manifest.materialization.size_bytes,
            **_issued_configuration_lane(task),
        )
        config.validate_retention(supplier.selection.retention)
        if (task.task_id != config.original_task.task_id or context.config.content_sha256 != config.fingerprint()
                or context.run_id != supplier.selection.retention.continued_run_id
                or package.issued_study.candidate.authoring_package.base.draft != supplier.root):
            raise PermissionError('retained E3 adoption changes its current issued task, run or root')
        supplier.retained_e3_scope.require_task(config)
        edges = {edge.consumer_input_id: edge for edge in validated_task_scientific_input_edges(task)}
        originals = {row.logical_artifact_id: row for row in config.original_receipt.output_logical_artifacts}
        physicals = {row.logical_artifact_id: row for row in config.original_receipt.output_materializations}
        for output in config.original_task.outputs:
            port = 'retained-' + output.output_id.rsplit('.', 1)[-1]
            edge = edges.get(port)
            logical, physical = originals[output.logical_artifact_id], physicals[output.logical_artifact_id]
            actual = None if edge is None else inputs.get(edge.operational_logical_artifact_id)
            if (edge is None or edge.producer_task_id is not None or actual is None
                    or actual.logical.logical_artifact_id != retained_input_id(logical)
                    or (actual.logical.payload_schema, actual.logical.profile, actual.logical.media_type,
                        actual.logical.content_sha256, actual.logical.outcome_access, actual.logical.visibility_ceiling,
                        actual.materialization.physical_sha256, actual.materialization.size_bytes) !=
                        (logical.payload_schema, logical.profile, logical.media_type, logical.content_sha256,
                            logical.outcome_access, logical.visibility_ceiling, physical.physical_sha256, physical.size_bytes)):
                raise PermissionError('retained E3 copy changes exact original receipted bytes or access')
        if custody.current_task(context, runner) != current:
            raise PermissionError('retained E3 current issue or authority changed before adoption')
        supplier.retained_e3_scope.require_task(config)
        return runner


@contextmanager
def authenticate_selection(*, writer, selection):
    """Use the same exact proof at authoring and later standalone entry."""
    scope = RetainedE3ExecutionScope(writer=writer, selection=selection)
    with scope.open():
        yield scope
