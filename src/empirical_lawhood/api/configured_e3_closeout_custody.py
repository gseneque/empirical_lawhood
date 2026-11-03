# SPDX-License-Identifier: MPL-2.0
"""Authenticate entered CAL work without changing its original execution.

The complete original contact, receipt and resource census stays under lock.
This owner has no native runner, recovery mutation or completion writer.
"""
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, fields, replace
from hashlib import sha256
from types import MappingProxyType

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import (
    ConfiguredE3CALRootCloseout, ConfiguredE3ClosedExecution, ConfiguredE3MissingOutcomeProducts,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_continued_response import ConfiguredE3ContinuedNativeResponse, original_config
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_composition import operation_declarations
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import lower_protected_matrix_response_error, operation_class, selected_configs, task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3PairedOutcome
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_preparation import response_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_unknown_response import ConfiguredProtectedE3UnknownResponseAvailability
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import source_binding
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_preparation import ConfiguredE3ContinuedPreparationSelection, ConfiguredE3UnfinishedPreparationSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3CompletedOutput
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.retained_input_read import RetainedInputRead
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeEventKind as ResourceEvent, ExecutionResourceEnvelopeState as ResourceState
from empirical_lawhood.runtime.native_subwork import NativeSubworkState

from .configured_e3_incomplete_read import _configuration, _external_inputs, _operands, _unknown_response
from .configured_e3_retained_custody import _pin
from .configured_e3_retained_read import continued_plan_read
from .current_result_custody import CurrentResultPlanReader, authenticate_task_dispatch_authority
from .domain_composition.matrix_configured_protected_response.scientific_read import _original_design, _selected_preparation
from .protected_e3_read_custody import _current_read_grants, authorize, product
from .prospective_experiment import load_retained_prospective_experiment
from .recursive_execution import _custody_control_pins
from .recursive_qualified_parents import _actual_package, _verify_receipt_closure


_active_closeout_reads = ContextVar('configured_e3_closeout_reads', default=())


def _contact_pin(contact):
    return ObjectIdentity.from_record('native-contact.' + contact.task_id, contact)


def _outcome_visibility(plan, node):
    task, = (task for task in plan.tasks if task.task_id == node)
    lanes = {(output.outcome_access, output.visibility_ceiling) for output in task.outputs}
    if len(lanes) != 1 or next(iter(lanes))[0] is not OutcomeAccess.EVALUATION_SEALED:
        raise PermissionError('CAL closeout changes the original sealed outcome lane')
    return next(iter(lanes))[1]


def _require_unpublished_outputs(writer, tasks, receipts):
    for node, task in tasks.items():
        if node not in receipts and any(writer.root.resolve(path, for_write=False).exists()
                for output in task.outputs for path in (output.relative_path, output.relative_path + '.manifest.json')):
            raise PermissionError('CAL closeout requires ordinary recovery of durable unreceipted parent outputs')


def _require_unknown_current(writer, contacts, unknown):
    """Recheck absent native returns as well as the already observed byte census."""
    for node, evidence in unknown.items():
        expected = evidence['availability']
        store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts.for_task(node),
            parent_contact=expected.parent_contact, completed_only=True)
        inspection = store.inspect(expected.definition)
        actual = ConfiguredProtectedE3UnknownResponseAvailability.from_inspection(expected.record_id,
            parent_contact=expected.parent_contact, roster=store.read_roster(expected.parent_contact),
            inspection=inspection, contact_identity=expected.contact_identity)
        if (actual != expected or inspection.call_entry != evidence['call_entry']
                or inspection.call_return != evidence['call_return']):
            raise PermissionError('CAL closeout original unknown native custody changed')


def _closed_resources(recovery, package, plan, closure, contacts, unknown):
    """Keep UNKNOWN reservations exactly; no terminal or successful event is made."""
    index, receipts = closure.recovery_index, closure.by_task
    envelope = recovery.reconstruct_execution_resource_envelope(index=index,
        envelope_id='run-resource-envelope.' + index.run_id, spec=package.execution_resource_envelope_spec,
        execution_plan=_pin(plan, 'execution_plan_id'), jit_graph_signature_manifest=package.jit_graph_signature_manifest)
    unknown_events = {}
    for event in envelope.events:
        if event.kind is ResourceEvent.UNKNOWN_COMPLETION:
            unknown_events.setdefault(event.cell_id, []).append(event)
    cells = {cell.cell_id: cell for cell in envelope.cells}
    for spec in envelope.spec.task_cells:
        node = spec.task_id
        cell, receipt = cells[spec.cell_id], receipts.get(node)
        candidates = {row.attempt_id for row in index.task(node).attempts}
        if not set(cell.attempt_ids) <= candidates:
            raise PermissionError('CAL closeout substitutes an original resource attempt')
        if receipt is not None:
            if (cell.state is not ResourceState.TERMINAL or cell.current_attempt_id != receipt.attempt_id
                    or cell.first_valid_receipt != _pin(receipt, 'receipt_id')
                    or cell.published_artifact != _pin(receipt, 'receipt_id')):
                raise PermissionError('CAL closeout resource completion loses its actual receipt')
        elif node in unknown:
            contact = contacts[node]
            events = unknown_events.get(cell.cell_id, ())
            if (cell.state is not ResourceState.UNKNOWN_COMPLETION or cell.current_attempt_id != contact.attempt_id
                    or cell.attempt_ids != (contact.attempt_id,) or len(events) != 1
                    or events[0].attempt_id != contact.attempt_id
                    or any(value is not None for value in (cell.first_valid_receipt, cell.published_artifact,
                        cell.recovery_candidate_artifact, cell.recovery_proof))):
                raise PermissionError('CAL closeout must preserve the exact original UNKNOWN resource reservation')
        elif (cell.state not in (ResourceState.PENDING_BRANCH, ResourceState.ISSUED, ResourceState.ZERO_CALL_SKIPPED)
                or cell.attempt_ids or cell.current_attempt_id is not None
                or any(value is not None for value in (cell.first_valid_receipt, cell.published_artifact,
                    cell.recovery_candidate_artifact, cell.recovery_proof))):
            raise PermissionError('CAL closeout refuses unresolved resources outside its original unknown CAL contacts')
        summary = closure.operational_summaries.get(node)
        if (summary is not None and getattr(summary, 'attempt_id', None) is not None
                and summary.attempt_id not in cell.attempt_ids):
            raise PermissionError('CAL closeout drops an original operational resource attempt')
    return envelope


def _completed_response(writer, package, plan, task, contact, receipts, external, input_read, control_reader):
    """Require actual durable native completion, original forecasts and score."""
    authenticate_task_dispatch_authority(package=package, execution_plan=plan, run_id=contact.run_id,
        task_id=task.task_id, attempt_id=contact.attempt_id, writer=writer)
    prepared = _operands(writer, package, task, contact, receipts, external,
        input_read=input_read, control_reader=control_reader)
    if prepared is None:
        raise PermissionError('CAL closeout loses original completed-response operands')
    operands, work, inputs = prepared
    response, _ = product(writer, plan, receipts, task.task_id, ConfiguredE3ContinuedNativeResponse)
    response.validate_source(operands.config,
        **{key: value for key, value in operands.science_arguments().items() if key != 'prefix_config'})
    contacts = ExternalNativeEffectContactStore(plane=writer, execution_plan=_pin(plan, 'execution_plan_id'),
        visibility_ceiling=operands.visibility, outcome_access=operands.outcome_access)
    store = ExternalNativeSubworkStore(plane=writer, parent_contacts=contacts, parent_contact=contact, parent_inputs=inputs)
    if (store.read_roster(contact) != work.rosters[0]
            or tuple(store.iter_roster_definitions(contact)) != work.definitions or len(response.native) != 1):
        raise PermissionError('CAL closeout loses its original completed native roster')
    evidence, = response.native
    inspection = store.inspect(work.definitions[0])
    if (inspection.state is not NativeSubworkState.COMPLETED
            or (inspection.definition, inspection.completion, inspection.receipt) != (
                evidence.definition, evidence.completion, evidence.receipt)):
        raise PermissionError('CAL closeout cannot infer native completion from a parent receipt')
    score_task = response_task_id(operands.config.source.root_id, 'response-score')
    if score_task not in receipts:
        raise PermissionError('CAL closeout requires durable completed scoring before retaining a finite outcome')
    score, _ = product(writer, plan, receipts, score_task, ScheduledResponseScore)
    outcome, _ = product(writer, plan, receipts, score_task, ConfiguredProtectedE3PairedOutcome)
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_score_validation import validate_current_score
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_secondary_readout import _checked_pair
    values = operands.science_arguments()
    validate_current_score(score, operands.config, response, source=values['source'], protocol=values['protocol'],
        panels=values['panels'], causal_identity=_pin(values['causal']), error_identity=_pin(values['error']),
        physical_identity=_pin(values['physical'], 'forecast_id'), response_identity=_pin(response, 'response_id'))
    _checked_pair(values['specification'], values['allocation'], 'calibration', outcome, values['error'], score)


@dataclass(frozen=True, slots=True)
class ClosedE3Custody:
    directory: str
    selection: object
    specification: object
    allocation: object
    package: object
    plan: object
    terminal: object
    recovery_index: object
    custody_sha256: str
    reveal: object
    envelope: object
    receipts: object
    configurations: object
    original: object
    predecessor: object
    writer: object
    contacts: object
    unknown: object
    require_current: object
    require_access: object

    @property
    def array_descriptors(self):
        return self.original.array_descriptors

    def continuation(self, **kwargs):
        self.require_access()
        return self.original.continuation(**kwargs)

    def product_source(self, task_id_):
        self.require_access()
        if task_id_ not in self.receipts:
            raise PermissionError('closed E3 product lacks its actual producing receipt')
        return self.predecessor if task_id_ in self.predecessor.receipts else self

    def receipt_sources(self):
        self.require_access()
        original = self.predecessor
        current_tasks = {row.task_id for row in self.plan.tasks}
        return ((original.writer, original.plan, original.receipts),
            (self.writer, self.plan, MappingProxyType({key: value for key, value in self.receipts.items() if key in current_tasks})))

    def missing_products(self, provenance):
        """Give missingness its actual assessment source, never a native source."""
        self.require_access()
        result = {}
        for node, evidence in self.unknown.items():
            config = self.configurations[node]
            suffix = provenance.fingerprint()[:24] + '.' + config.source.root_id
            score = replace(evidence['score'], score_id='closeout-score.' + suffix)
            outcome = replace(evidence['outcome'], record_id='closeout-outcome.' + suffix,
                original_score=_pin(score, 'score_id'))
            result[node] = ConfiguredE3MissingOutcomeProducts('missing-outcome.' + suffix,
                provenance, config, evidence['availability'], score, outcome,
                _outcome_visibility(self.plan, response_task_id(config.source.root_id, 'response-score')))
        self.require_access()
        return result

    def closeout(self, *, record_id, retention):
        """Derive the full graph cut from authenticated receipts and contacts."""
        self.require_access()
        missing = self.missing_products(retention.response_provenance)
        roots = []
        for node, config in sorted(self.configurations.items()):
            science = original_config(config)
            if operation_class(config) != 'responses' or science.source.root.root.role.value != 'CALIBRATION':
                continue
            root = science.source.root.root
            absent = missing.get(node)
            roots.append(ConfiguredE3CALRootCloseout(root.root_id, root.independent_group_id,
                _pin(config, 'config_id'), _contact_pin(self.contacts[node]),
                None if absent is not None else _pin(self.receipts[node], 'receipt_id'),
                None if absent is not None else _pin(self.receipts[response_task_id(root.root_id, 'response-score')], 'receipt_id'),
                None if absent is None else absent.identity, None if absent is None else len(absent.canonical_bytes()),
                _outcome_visibility(self.plan, response_task_id(root.root_id, 'response-score'))))
        base = ConfiguredE3ContinuedPreparationSelection(**{field.name: getattr(self.selection, field.name)
            for field in fields(ConfiguredE3ContinuedPreparationSelection)})
        lowered = lower_protected_matrix_response_error(self.specification, self.allocation, base)
        completed = set(self.receipts)
        remaining = {row.node_id for row in lowered.draft.operations} - completed - set(missing)
        missing_scores = {response_task_id(self.configurations[node].source.root_id, 'response-score') for node in missing}
        boundary = {(link.producer_node_id, link.producer_output_id.rsplit('.', 1)[-1])
            for link in lowered.draft.links if link.consumer_node_id in remaining - missing_scores
            and link.producer_node_id in completed}
        outputs = []
        task_maps = {id(owner): {row.task_id: row for row in owner.plan.tasks} for owner in (self, self.predecessor)}
        for producer, port in sorted(boundary):
            owner = self.product_source(producer)
            receipt = owner.receipts[producer]
            spec, = (row for row in task_maps[id(owner)][producer].outputs if row.output_id.rsplit('.', 1)[-1] == port)
            logical, = (row for row in receipt.output_logical_artifacts if row.logical_artifact_id == spec.logical_artifact_id)
            physical, = (row for row in receipt.output_materializations if row.logical_artifact_id == spec.logical_artifact_id)
            outputs.append(ConfiguredE3CompletedOutput(producer, spec.output_id, _pin(receipt, 'receipt_id'), logical, physical))
        result = ConfiguredE3ClosedExecution(record_id, self.directory, self.package.run_plan_id,
            _pin(self.package, 'package_id'), _pin(self.plan, 'execution_plan_id'),
            None if self.terminal is None else _pin(self.terminal, 'terminal_event_id'),
            _pin(self.envelope, 'envelope_id'), _pin(self.reveal, 'authority_id'),
            source_binding(self.selection.retention.response_provenance), retention,
            tuple((key, _pin(receipt, 'receipt_id')) for key, receipt in sorted(self.receipts.items())),
            tuple(sorted(remaining)), tuple(outputs), _pin(self.recovery_index, 'recovery_index_id'), self.custody_sha256,
            self.selection.unfinished,
            tuple(sorted(self.allocation.unit_ids('calibration'))), tuple(sorted(roots, key=lambda row: row.root_id)))
        self.require_access()
        return result


@contextmanager
def read_closed_e3(*, artifact_writer, directory, run_id, reveal_authority_id):
    """Close only entered CAL with unknown calls and untouched confirmation."""
    for current in _active_closeout_reads.get():
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
        if (type(selection) is not ConfiguredE3UnfinishedPreparationSelection
                or package.issued_study.source_closure != selected.implementation
                or package.run_plan_id != run_id or selection.retention.continued_run_id != run_id
                or _pin(package.issued_study.candidate, 'candidate_id') != selected.association.candidate):
            raise PermissionError('CAL closeout requires its exact original unfinished issued execution')
        specification, allocation = _original_design(selected)
        # Keep the authenticated scientific operands, not the now-unused
        # authoring candidate/projection/draft and complete raw payload mapping.
        # The original read scope still owns every final byte/access check.
        del selected
        plan = reader.authenticate_execution_plan(package=package, issued=package.issued_study, run_id=run_id)
        configs = {task_id(row): row for row in selected_configs(specification, allocation, selection)}
        tasks = {row.task_id: row for row in plan.tasks}
        if set(tasks) != set(selection.unfinished.unfinished_task_ids):
            raise PermissionError('CAL closeout changes the original selected execution graph')
        for node, task in tasks.items():
            config = configs[node]
            if (task.capability.config.config_schema, task.capability.config.content_sha256) != (config.SCHEMA, config.fingerprint()):
                raise PermissionError('CAL closeout changes an original issued configuration')
        contacts = ExternalNativeEffectContactStore(plane=view, execution_plan=_pin(plan, 'execution_plan_id'),
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND,
            task_scopes={key: (task.outputs[0].visibility_ceiling, task.capability.requested_outcome_access) for key, task in tasks.items()})
        with contacts.execution_lock(run_id):
            closure = reader.collect_receipt_closure(package=package, execution_plan=plan, reveal=reveal,
                capability_prefixes=('matrix-e3-configured-protected.',), allow_partial=True)
            index, receipts = closure.recovery_index, closure.by_task
            recovery = ExternalRunRecoveryStore(view)
            terminal = recovery.read_terminal(index)
            if terminal is not None and (terminal.operational_status != 'BLOCKED' or terminal.failed_task_ids):
                raise PermissionError('CAL closeout requires an original blocked terminal or its preserved absence')
            codecs = {schema: kind for declaration in operation_declarations() for schema, kind in declaration.record_codecs.items()}
            writer = reader.output_artifact_plane(package=package, execution_plan=plan, output_codecs=codecs)
            _verify_receipt_closure(writer, closure)
            controls = _custody_control_pins(view, index)
            with continued_plan_read(writer=writer, plan=plan, receipts=receipts) as retained:
                if retained is None or retained.unfinished != selection.unfinished or retained.retention != selection.retention:
                    raise PermissionError('CAL closeout loses its actual earlier prefix/model custody')
                predecessor = retained.predecessor
                all_receipts = {**predecessor.receipts, **receipts}
                if set(predecessor.receipts) & set(receipts):
                    raise PermissionError('CAL closeout repeats completed predecessor work')
                calibration = {node: task for node, task in tasks.items() if operation_class(configs[node]) == 'responses'
                    and configs[node].source.root.root.role.value == 'CALIBRATION'}
                if {configs[node].source.root.root.independent_group_id for node in calibration} != set(allocation.unit_ids('calibration')):
                    raise PermissionError('CAL closeout changes the complete assigned CAL denominator')
                observed = {node: contacts.read(run_id, node) for node in tasks}
                if {node for node, contact in observed.items() if contact is not None} != set(calibration):
                    raise PermissionError('CAL closeout requires every original CAL contact and untouched confirmation')
                allowed = set(calibration) | {response_task_id(configs[node].source.root_id, 'response-score') for node in calibration}
                for node in receipts:
                    config = original_config(configs[node])
                    if node not in allowed and not (operation_class(config) == 'forecast' and config.mode == 'calibration'):
                        raise PermissionError('CAL closeout refuses completed later work')
                _require_unpublished_outputs(view, tasks, receipts)
                unknown = {}
                frequencies = Counter(spec.logical_artifact_id for task in calibration.values() for spec in task.external_inputs)
                with RetainedInputRead(writer, shared_artifact_ids=(key for key, count in frequencies.items() if count > 1)) as input_read:
                    control_reader = CurrentResultPlanReader(writer)
                    for node, task in sorted(calibration.items()):
                        external = _external_inputs(writer, task, run_id)
                        if _configuration(writer, task, external) != configs[node]:
                            raise PermissionError('CAL closeout substitutes original response operands')
                        if node in receipts:
                            _completed_response(writer, package, plan, task, observed[node], receipts, external, input_read, control_reader)
                        else:
                            state, evidence = _unknown_response(writer, package, plan, task, configs[node], external, receipts,
                                tuple(row.attempt_id for row in index.task(node).attempts), input_read=input_read, control_reader=control_reader)
                            if state != 'UNKNOWN_CONTACT':
                                raise PermissionError('CAL closeout requires authentic unknown contact or durable completed work: ' + state)
                            unknown[node] = evidence
                if not unknown:
                    raise PermissionError('CAL closeout requires entered missing outcomes')
                envelope = _closed_resources(recovery, package, plan, closure, observed, unknown)
                # Completed input/control readers retain no permission result.
                # The receipt closure, unknown contacts and live guards remain.
                del reader, control_reader, input_read

                def access():
                    if not active:
                        raise PermissionError('CAL closeout custody lifetime has ended')
                    _current_read_grants(view, package, reveal_authority_id)
                    if ExternalStudyOperationAuthorityStore(view).load(reveal_authority_id) != reveal:
                        raise PermissionError('CAL closeout original reveal changed')
                    predecessor.require_access()

                def current():
                    from empirical_lawhood.infrastructure.artifacts import verify_read_context_snapshots
                    access()
                    if _custody_control_pins(view, index) != controls:
                        raise PermissionError('CAL closeout original controls or resource history changed')
                    if _closed_resources(recovery, package, plan, closure, observed, unknown) != envelope:
                        raise PermissionError('CAL closeout original resource journal changed')
                    if any(contacts.read(run_id, node) != contact for node, contact in observed.items()):
                        raise PermissionError('CAL closeout original contact census changed')
                    _require_unpublished_outputs(view, tasks, receipts)
                    _require_unknown_current(writer, contacts, unknown)
                    predecessor.require_current()
                    verify_read_context_snapshots(view)
                    access()

                custody = ClosedE3Custody(directory, selection, specification, allocation, package, plan,
                    terminal, index, sha256(canonical_json_bytes(controls)).hexdigest(), reveal, envelope,
                    MappingProxyType(all_receipts), MappingProxyType(configs), retained.original,
                    predecessor, writer, MappingProxyType(observed), MappingProxyType(unknown), current, access)
                token = _active_closeout_reads.set((*_active_closeout_reads.get(), custody))
                try:
                    current()
                    yield custody
                    current()
                finally:
                    _active_closeout_reads.reset(token)
                    active = False
