# SPDX-License-Identifier: MPL-2.0
"""Authenticate a stopped continued E3 before selecting its unfinished suffix."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from types import MappingProxyType

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_composition import operation_declarations
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import selected_configs, task_id, operation_class, lower_protected_matrix_response_error
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import RETAINED_PHASES, source_binding
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3CompletedOutput, ConfiguredE3UnfinishedExecution
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeState

from .configured_e3_retained_custody import _pin, _resources
from .configured_e3_retained_read import continued_plan_read
from .current_result_custody import CurrentResultPlanReader
from .domain_composition.matrix_configured_protected_response.scientific_read import _selected_preparation, _original_design
from .protected_e3_read_custody import authorize, _current_read_grants
from .prospective_experiment import load_retained_prospective_experiment
from .recursive_execution import _custody_control_pins
from .recursive_qualified_parents import _actual_package, _verify_receipt_closure


_active_unfinished_reads = ContextVar('configured_e3_unfinished_reads', default=())


def _require_unentered(contacts, run_id, task_ids):
    if any(contacts.read(run_id, key) is not None for key in task_ids):
        raise PermissionError('unfinished E3 refuses every prior native contact in the adoption run')


@dataclass(frozen=True, slots=True)
class UnfinishedE3Custody:
    directory: str
    selection: object
    specification: object
    allocation: object
    package: object
    plan: object
    terminal: object
    reveal: object
    envelope: object
    receipts: object
    configurations: object
    original: object
    writer: object
    require_current: object
    require_access: object

    @property
    def array_descriptors(self):
        return self.original.array_descriptors

    def product_source(self, task_id_):
        self.require_access()
        if task_id_ not in self.receipts:
            raise PermissionError('unfinished E3 product lacks its actual producing receipt')
        return self

    def continuation(self, **kwargs):
        self.require_access()
        return self.original.continuation(**kwargs)

    def unfinished(self, *, record_id, retention):
        """Project the authenticated graph; publication/exit check its custody."""
        self.require_access()
        lowered = lower_protected_matrix_response_error(self.specification, self.allocation, self.selection)
        completed = set(self.receipts)
        remaining = {row.task_id for row in self.plan.tasks} - completed
        boundary = { (link.producer_node_id, link.producer_output_id.rsplit('.', 1)[-1])
            for link in lowered.draft.links if link.consumer_node_id in remaining and link.producer_node_id in completed }
        tasks = {row.task_id: row for row in self.plan.tasks}
        outputs = []
        for producer, port in sorted(boundary):
            receipt = self.receipts[producer]
            spec, = (row for row in tasks[producer].outputs if row.output_id.rsplit('.', 1)[-1] == port)
            logical, = (row for row in receipt.output_logical_artifacts if row.logical_artifact_id == spec.logical_artifact_id)
            physical, = (row for row in receipt.output_materializations if row.logical_artifact_id == spec.logical_artifact_id)
            outputs.append(ConfiguredE3CompletedOutput(producer, spec.output_id, _pin(receipt, 'receipt_id'), logical, physical))
        result = ConfiguredE3UnfinishedExecution(record_id, self.directory, self.package.run_plan_id,
            _pin(self.package, 'package_id'), _pin(self.plan, 'execution_plan_id'), _pin(self.terminal, 'terminal_event_id'),
            _pin(self.envelope, 'envelope_id'), _pin(self.reveal, 'authority_id'),
            source_binding(self.selection.retention.response_provenance), retention,
            tuple((key, _pin(receipt, 'receipt_id')) for key, receipt in sorted(self.receipts.items())),
            tuple(sorted(remaining)), tuple(outputs))
        self.require_access()
        return result


@contextmanager
def read_unfinished_e3(*, artifact_writer, directory, run_id, reveal_authority_id):
    """Require successful ancestors and zero future native contact under lock."""
    for current in _active_unfinished_reads.get():
        if (current.writer.root is artifact_writer.root and current.directory == directory
                and current.package.run_plan_id == run_id and current.reveal.authority_id == reveal_authority_id):
            current.require_access()
            yield current
            current.require_access()
            return
    active = True
    with artifact_writer.read_context() as view:
        reader = CurrentResultPlanReader(view)
        package = _actual_package(view, run_id, control_reader=reader)
        authorize(view, package, reveal_authority_id)
        reveal = ExternalStudyOperationAuthorityStore(view).load(reveal_authority_id)
        selected = load_retained_prospective_experiment(directory=view.root.resolve(directory, for_write=False), artifact_writer=view)
        selection = _selected_preparation(selected)
        if (type(selection) is not ConfiguredE3ContinuedPreparationSelection
                or package.issued_study.source_closure != selected.implementation
                or package.run_plan_id != run_id or selection.retention.continued_run_id != run_id
                or _pin(package.issued_study.candidate, 'candidate_id') != selected.association.candidate):
            raise PermissionError('unfinished E3 requires its exact original continued issued execution')
        specification, allocation = _original_design(selected)
        # Its exact source/candidate joins are established above. The retained
        # scientific records and final snapshot guard outlive the bulky packet.
        del selected
        plan = reader.authenticate_execution_plan(package=package, issued=package.issued_study, run_id=run_id)
        scopes = {task.task_id: (task.outputs[0].visibility_ceiling, task.capability.requested_outcome_access) for task in plan.tasks}
        contacts = ExternalNativeEffectContactStore(plane=view, execution_plan=_pin(plan, 'execution_plan_id'),
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND, task_scopes=scopes)
        with contacts.execution_lock(run_id):
            closure = reader.collect_receipt_closure(package=package, execution_plan=plan, reveal=reveal,
                capability_prefixes=('matrix-e3-configured-protected.',), allow_partial=True)
            index, receipts = closure.recovery_index, closure.by_task
            recovery = ExternalRunRecoveryStore(view)
            terminal = recovery.read_terminal(index)
            if terminal is None or terminal.operational_status != 'BLOCKED' or terminal.failed_task_ids:
                raise PermissionError('unfinished E3 requires a closed preflight-blocked predecessor')
            configs = {task_id(row): row for row in selected_configs(specification, allocation, selection)}
            if set(configs) != {task.task_id for task in plan.tasks}:
                raise PermissionError('unfinished E3 substitutes its complete original scientific graph')
            required = {'prefix', 'numerical', 'measure', 'check', 'project', 'feature', 'physical-forecast', 'fit', 'model-freeze'}
            for task in plan.tasks:
                config, phase = configs[task.task_id], operation_class(configs[task.task_id])
                if (task.capability.config.config_schema, task.capability.config.content_sha256) != (config.SCHEMA, config.fingerprint()):
                    raise PermissionError('unfinished E3 changes an original issued configuration')
                if phase in required and task.task_id not in receipts:
                    raise PermissionError('unfinished E3 requires every prefix, feature, physical forecast, fit and model freeze')
                if task.task_id in receipts and phase not in RETAINED_PHASES:
                    raise PermissionError('unfinished E3 cannot follow completed future response work')
                if task.task_id in receipts and phase == 'forecast':
                    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_continued_response import original_config
                    if original_config(config).mode != 'calibration':
                        raise PermissionError('unfinished E3 refuses a completed confirmation forecast')
            unfinished = set(configs) - set(receipts)
            if not unfinished:
                raise PermissionError('unfinished E3 requires remaining work')
            _require_unentered(contacts, run_id, configs)
            for attempt in terminal.attempts:
                if attempt.task_id in unfinished and (attempt.disposition.value != 'BLOCKED'
                        or attempt.reason_code != 'resource-computability-unavailable'):
                    raise PermissionError('unfinished E3 refuses entered or uncertain pending attempts')
            for task in plan.tasks:
                if task.task_id in unfinished and any(view.root.resolve(path, for_write=False).exists()
                        for output in task.outputs for path in (output.relative_path, output.relative_path + '.manifest.json')):
                    raise PermissionError('unfinished E3 refuses unreceipted pending outputs')
            envelope = _resources(recovery, package, plan, index, receipts, terminal)
            cells = {row.cell_id: row for row in envelope.cells}
            for task_id_ in unfinished:
                cell = cells[package.execution_resource_envelope_spec.cell_for_task(task_id_).cell_id]
                if (cell.state not in (ExecutionResourceEnvelopeState.PENDING_BRANCH, ExecutionResourceEnvelopeState.ISSUED,
                        ExecutionResourceEnvelopeState.RESOURCE_STOP, ExecutionResourceEnvelopeState.RECEIPT_OBSERVED)
                        or any(value is not None for value in (cell.first_valid_receipt, cell.published_artifact,
                            cell.recovery_candidate_artifact, cell.recovery_proof))):
                    raise PermissionError('unfinished E3 refuses reserved, active or uncertain resource work')
            codecs = {schema: kind for declaration in operation_declarations() for schema, kind in declaration.record_codecs.items()}
            writer = reader.output_artifact_plane(package=package, execution_plan=plan, output_codecs=codecs)
            _verify_receipt_closure(writer, closure)
            controls = _custody_control_pins(view, index)
            with continued_plan_read(writer=writer, plan=plan, receipts=receipts) as retained:
                if retained is None or retained.retention != selection.retention:
                    raise PermissionError('unfinished E3 loses its actual original prefix and model custody')
                del reader, closure, codecs, cells

                def access():
                    if not active:
                        raise PermissionError('unfinished E3 custody lifetime has ended')
                    _current_read_grants(view, package, reveal_authority_id)
                    if ExternalStudyOperationAuthorityStore(view).load(reveal_authority_id) != reveal:
                        raise PermissionError('unfinished E3 predecessor reveal changed')
                    retained.original.require_access()

                def current():
                    from empirical_lawhood.infrastructure.artifacts import verify_read_context_snapshots

                    access()
                    if _custody_control_pins(view, index) != controls:
                        raise PermissionError('unfinished E3 predecessor controls or native contact changed')
                    _require_unentered(contacts, run_id, unfinished)
                    retained.original.require_controls()
                    verify_read_context_snapshots(view, retained.original.writer)
                    access()

                custody = UnfinishedE3Custody(directory, selection, specification, allocation, package, plan,
                    terminal, reveal, envelope, receipts, MappingProxyType(configs), retained.original, writer, current, access)
                token = _active_unfinished_reads.set((*_active_unfinished_reads.get(), custody))
                try:
                    current()
                    yield custody
                    current()
                finally:
                    _active_unfinished_reads.reset(token)
                    active = False
