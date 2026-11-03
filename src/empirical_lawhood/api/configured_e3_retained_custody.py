# SPDX-License-Identifier: MPL-2.0
"""Read an entered E3 prefix/fit without changing its original terminal.

The original issued plan, every completed receipt, native completion and
resource event remain authoritative. This scope neither repairs that history
nor supplies a native entry token or a new scientific qualification.
"""
from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
from dataclasses import dataclass
from types import MappingProxyType

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_composition import operation_declarations
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import ConfiguredProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import operation_class, selected_configs, task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3FrozenProducts, ConfiguredProtectedE3ModelSet
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_prefix_records import ConfiguredProtectedE3PrefixHistory
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import statistical_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_retained_execution import ConfiguredE3RetainedExecution, ConfiguredE3RetainedTaskConfig, RETAINED_PHASES, source_binding
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore, ExternalIssuedStudyPublisher, PROGRAMME_ISSUE_GRANTEE_ID
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeEventKind, ExecutionResourceEnvelopeState
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorNativeBinding

from .current_result_custody import CurrentResultPlanReader
from .domain_composition.matrix_configured_protected_response.scientific_read import _original_design, _selected_preparation
from .protected_e3_read_custody import authorize, product, _current_read_grants
from .prospective_experiment import load_retained_prospective_experiment
from .recursive_execution import _custody_control_pins
from .recursive_qualified_parents import _actual_package, _prior_native_subwork, _verify_receipt_closure

_active_original_reads = ContextVar('configured_e3_original_partial_reads', default=())


def _pin(record, field='record_id'):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class _NativeBinding:
    native_subwork: tuple
    execution_plan: ObjectIdentity
    run_id: str


@dataclass(frozen=True, slots=True)
class RetainedE3Custody:
    """Immutable observations usable only inside their current read scope."""
    directory: str
    selection: object
    specification: object
    allocation: object
    package: object
    plan: object
    terminal: object
    reveal: object
    receipts: object
    configurations: object
    arrays: tuple
    array_descriptors: object
    models: object
    model_freeze: object
    prefit: object
    writer: object
    require_current: object
    require_access: object
    require_controls: object

    def product_source(self, task_id_):
        self.require_access()
        if task_id_ not in self.receipts:
            raise PermissionError('retained E3 product lacks its actual producing receipt')
        return self

    def continuation(self, *, record_id, continued_run_id, response_provenance):
        """Project already authenticated records inside the owner's live scope.

        This performs no body read or publication. Current access stays fresh;
        publication and scope exit own the complete control/byte checkpoints.
        """
        self.require_access()
        record = ConfiguredE3RetainedExecution(record_id, self.directory, self.package.run_plan_id,
            continued_run_id, _pin(self.package, 'package_id'), _pin(self.plan, 'execution_plan_id'),
            _pin(self.terminal, 'terminal_event_id'), _pin(self.reveal, 'authority_id'),
            source_binding(self.selection.manifest.provenances[0]), response_provenance,
            self.specification.identity, self.allocation.identity, _pin(self.model_freeze),
            tuple((key, _pin(value, 'receipt_id')) for key, value in sorted(self.receipts.items())), self.arrays)
        tasks = {row.task_id: row for row in self.plan.tasks}
        retained = tuple(ConfiguredE3RetainedTaskConfig('config.retained.' + key, record.identity,
            self.configurations[key], tasks[key], receipt) for key, receipt in sorted(self.receipts.items()))
        self.require_access()
        return record, retained


def _original_configurations(selection, specification, allocation, plan, receipts):
    if type(selection) is not ConfiguredProtectedE3PreparationSelection:
        raise PermissionError('retained E3 requires its original uncontinued preparation')
    configs = {task_id(config): config for config in selected_configs(specification, allocation, selection)}
    if set(configs) != {task.task_id for task in plan.tasks}:
        raise PermissionError('retained E3 changes its complete original configured graph')
    mandatory = {'prefix', 'numerical', 'measure', 'check', 'project', 'physical-forecast', 'fit', 'model-freeze'}
    for task in plan.tasks:
        config, done = configs[task.task_id], task.task_id in receipts
        phase = operation_class(config)
        if (task.capability.config.config_schema != config.SCHEMA
                or task.capability.config.content_sha256 != config.fingerprint()):
            raise PermissionError('retained E3 changes an original issued task configuration')
        if phase in mandatory and not done:
            raise PermissionError('retained E3 requires every original prefix, physical forecast, fit and model freeze')
        if done and (phase not in RETAINED_PHASES or phase == 'forecast' and config.mode != 'calibration'):
            raise PermissionError('retained E3 cannot follow completed future response or assessment work')
    return MappingProxyType(configs)


def _resources(recovery, package, plan, index, receipts, terminal):
    envelope = recovery.reconstruct_execution_resource_envelope(index=index,
        envelope_id='run-resource-envelope.' + index.run_id, spec=package.execution_resource_envelope_spec,
        execution_plan=_pin(plan, 'execution_plan_id'), jit_graph_signature_manifest=package.jit_graph_signature_manifest)
    # The ordinary resource owner records a known preflight failure as
    # RECEIPT_OBSERVED with no successful receipt. Preserve that disposition and
    # its spent reservation; it is neither a native result nor unknown work.
    candidate_ids = {row.attempt_id for task in index.tasks for row in task.attempts}
    attempts = {}
    for row in terminal.attempts:
        if row.attempt_id in candidate_ids:
            attempts.setdefault(row.task_id, []).append(row)
    failures = {}
    for event in envelope.events:
        if event.kind is ExecutionResourceEnvelopeEventKind.OPERATIONAL_FAILURE:
            failures.setdefault((event.cell_id, event.attempt_id), []).append(event)
    cells = {row.cell_id: row for row in envelope.cells}
    for spec in package.execution_resource_envelope_spec.task_cells:
        receipt = receipts.get(spec.task_id)
        cell = cells[spec.cell_id]
        rows = tuple(attempts.get(spec.task_id, ()))
        if cell.attempt_ids != tuple(row.attempt_id for row in rows):
            raise PermissionError('retained E3 resource attempts differ from the complete original terminal')
        if receipt is not None:
            if (cell.state is not ExecutionResourceEnvelopeState.TERMINAL
                    or cell.current_attempt_id != receipt.attempt_id
                    or cell.first_valid_receipt != _pin(receipt, 'receipt_id')
                    or cell.published_artifact != _pin(receipt, 'receipt_id')):
                raise PermissionError('retained E3 resource completion differs from its original successful receipt')
        elif rows:
            final = rows[-1]
            candidate, = (row for row in index.task(spec.task_id).attempts if row.attempt_id == final.attempt_id)
            event = recovery.read_event(index, candidate.event_relative_path)
            resource_failures = failures.get((cell.cell_id, final.attempt_id), ())
            if (final.disposition.value not in ('BLOCKED', 'FAILED')
                    or cell.state not in (ExecutionResourceEnvelopeState.RECEIPT_OBSERVED, ExecutionResourceEnvelopeState.RESOURCE_STOP)
                    or cell.current_attempt_id != final.attempt_id
                    or any(value is not None for value in (cell.first_valid_receipt, cell.published_artifact,
                        cell.recovery_candidate_artifact, cell.recovery_proof))
                    or event is None or event.failure is None or event.failure.scientific_evidence
                    or len(resource_failures) != 1
                    or resource_failures[0].reason_code != event.failure.failure_class.value
                    or resource_failures[0].scientific_terminal is not False):
                raise PermissionError('retained E3 has active, unpublished or unknown original resource work')
        elif (cell.state not in (ExecutionResourceEnvelopeState.PENDING_BRANCH, ExecutionResourceEnvelopeState.ISSUED,
                ExecutionResourceEnvelopeState.ZERO_CALL_SKIPPED)
                or cell.current_attempt_id is not None
                or any(value is not None for value in (cell.first_valid_receipt, cell.published_artifact,
                    cell.recovery_candidate_artifact, cell.recovery_proof))):
            raise PermissionError('retained E3 has an unaccounted original resource reservation or launch')
    return envelope


def _arrays(writer, plan, receipts, declarations):
    result = []
    for task in plan.tasks:
        receipt = receipts.get(task.task_id)
        if receipt is None:
            continue
        logicals = tuple(row for row in receipt.output_logical_artifacts if row.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
        if not logicals:
            continue
        if len(logicals) != 1:
            raise PermissionError('retained E3 array producer changes its exact single-archive contract')
        logical, = logicals
        physical, = (row for row in receipt.output_materializations if row.logical_artifact_id == logical.logical_artifact_id)
        declarations_by_schema = declarations[task.capability.capability_key].record_codecs
        arrays = []
        for output in receipt.output_logical_artifacts:
            kind = declarations_by_schema.get(output.payload_schema)
            if kind is not None:
                record, _ = product(writer, plan, receipts, task.task_id, kind)
                value = getattr(record, 'arrays', None)
                if value is not None:
                    arrays.append(value)
        if len(arrays) != 1:
            raise PermissionError('retained E3 array copy requires its exact original canonical array descriptor')
        descriptor, = arrays
        artifact = descriptor.array_artifact
        if ((artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes) !=
                (logical.logical_artifact_id, logical.payload_schema, logical.content_sha256, logical.media_type, physical.size_bytes)
                or artifact.sha256 != physical.physical_sha256):
            raise PermissionError('retained E3 array descriptor changes its exact successful original archive')
        result.append((task.task_id, descriptor))
    return tuple(sorted(result))


@contextmanager
def read_original_partial_e3(*, artifact_writer, directory, run_id, reveal_authority_id):
    """Authenticate the complete partial history without replacing its terminal."""
    active = True
    with artifact_writer.read_context() as view, ExitStack() as lifetime:
        publisher = ExternalIssuedStudyPublisher(artifact_plane=view,
            authority_store=ExternalStudyOperationAuthorityStore(view), grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)
        publication_reader = lifetime.enter_context(publisher.read_context())
        reader = CurrentResultPlanReader(view)
        package = _actual_package(view, run_id, control_reader=reader)
        authorize(view, package, reveal_authority_id, publication_reader=publication_reader)
        reveal = ExternalStudyOperationAuthorityStore(view).load(reveal_authority_id)
        selected = load_retained_prospective_experiment(directory=view.root.resolve(directory, for_write=False),
            artifact_writer=view)
        if (package.run_plan_id != run_id or package.issued_study.source_closure != selected.implementation
                or _pin(package.issued_study.candidate, 'candidate_id') != selected.association.candidate):
            raise PermissionError('retained E3 substitutes its original issued source or candidate')
        selection = _selected_preparation(selected)
        specification, allocation = _original_design(selected)
        # The companion's candidate, projection, draft and raw payloads have
        # served their joins. Keep the needed scientific records and the live
        # byte/access guards, not another complete authoring packet per ancestor.
        del selected
        plan = reader.authenticate_execution_plan(package=package, issued=package.issued_study, run_id=run_id)
        plan_pin = _pin(plan, 'execution_plan_id')
        scopes = {task.task_id: (task.outputs[0].visibility_ceiling, task.capability.requested_outcome_access)
            for task in plan.tasks}
        contacts = ExternalNativeEffectContactStore(plane=view, execution_plan=plan_pin,
            visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND,
            task_scopes=scopes)
        with contacts.execution_lock(run_id):
            closure = reader.collect_receipt_closure(package=package, execution_plan=plan, reveal=reveal,
                capability_prefixes=('matrix-e3-configured-protected.',), allow_partial=True)
            index, receipts = closure.recovery_index, closure.by_task
            recovery = ExternalRunRecoveryStore(view)
            terminal = recovery.read_terminal(index)
            if terminal is None or terminal.operational_status not in ('BLOCKED', 'FAILED'):
                raise PermissionError('retained E3 needs its exact closed original partial terminal')
            configs = _original_configurations(selection, specification, allocation, plan, receipts)
            if (len(selection.manifest.provenances) != 1
                    or selection.manifest.provenances[0].observed_git_head != package.issued_study.source_closure.implementation_commit
                    or any(receipt.implementation_commit != package.issued_study.source_closure.implementation_commit
                        for receipt in receipts.values())):
                raise PermissionError('retained E3 changes its actual original prefix-producing source')
            controls = _custody_control_pins(view, index)
            envelope = _resources(recovery, package, plan, index, receipts, terminal)
            declarations = {row.capability_key: row for row in operation_declarations()}
            codecs = {schema: kind for declaration in declarations.values() for schema, kind in declaration.record_codecs.items()}
            writer = reader.output_artifact_plane(package=package, execution_plan=plan, output_codecs=codecs)
            _verify_receipt_closure(writer, closure)
            native, histories, contact_rows = [], {}, []
            for task in plan.tasks:
                config = configs[task.task_id]
                phase = operation_class(config)
                contact = contacts.read(run_id, task.task_id)
                contact_rows.append((task.task_id, contact))
                if phase != 'prefix':
                    if contact is not None:
                        raise PermissionError('retained E3 has entered future work or an undeclared native task')
                    continue
                history, _ = product(writer, plan, receipts, task.task_id, ConfiguredProtectedE3PrefixHistory)
                history.validate_source(config, selection.manifest, specification=specification)
                evidence = history.native
                native.append(RecursivePriorNativeBinding(task.task_id, evidence.definition.identity,
                    ObjectIdentity.from_record('completion.' + evidence.definition.subwork_id, evidence.completion),
                    _pin(evidence.receipt, 'receipt_id')))
                histories[task.task_id] = history
            prior = _prior_native_subwork(writer, _NativeBinding(tuple(native), plan_pin, run_id), plan,
                receipts, control_reader=reader)
            for row in prior:
                evidence = histories[row.binding.task_id].native
                if ((row.inspection.definition, row.inspection.completion, row.inspection.receipt) !=
                        (evidence.definition, evidence.completion, evidence.receipt)):
                    raise PermissionError('retained E3 prefix metadata changes its actual completed native evidence')
            ids = specification.identity, allocation.identity
            models, _ = product(writer, plan, receipts, statistical_task_id(*ids, 'fit'), ConfiguredProtectedE3ModelSet)
            prefit, _ = product(writer, plan, receipts, statistical_task_id(*ids, 'fit'), ConfiguredProtectedE3PreFitJoin)
            freeze, _ = product(writer, plan, receipts, statistical_task_id(*ids, 'freeze', mode='model'), ConfiguredProtectedE3FrozenProducts)
            if (models.reservation_join != _pin(prefit) or freeze.models != _pin(models)
                    or freeze.reservation_join != _pin(prefit) or freeze.calibration is not None):
                raise PermissionError('retained E3 changes its original fitted models or pre-future freeze')
            descriptors = _arrays(writer, plan, receipts, declarations)
            arrays = tuple((key, value.array_artifact) for key, value in descriptors)
            # The live custody below owns the required records and all byte,
            # contact and access guards. Validation-only plans and native
            # inspections must not remain cached for the whole continuation.
            del reader, closure, declarations, codecs, native, histories, prior
            history = evidence = row = None

            def check_controls():
                if not active:
                    raise PermissionError('retained E3 original read scope has expired')
                if (_custody_control_pins(view, index) != controls
                        or tuple((key, contacts.read(run_id, key)) for key, _ in contact_rows) != tuple(contact_rows)
                        or _resources(recovery, package, plan, index, receipts, terminal) != envelope):
                    raise PermissionError('retained E3 original controls, effects or resources changed during the read')
                authorize(view, package, reveal_authority_id, publication_reader=publication_reader)
                if ExternalStudyOperationAuthorityStore(view).load(reveal_authority_id) != reveal:
                    raise PermissionError('retained E3 original reveal selection changed during the read')

            def access():
                if not active:
                    raise PermissionError('retained E3 original read scope has expired')
                view.require_active_verification_scope()
                _current_read_grants(view, package, reveal_authority_id)
                if ExternalStudyOperationAuthorityStore(view).load(reveal_authority_id) != reveal:
                    raise PermissionError('retained E3 original reveal selection changed during the read')

            def current():
                check_controls()
                view.require_verification_snapshot()
                access()

            token = None
            try:
                current()
                retained = RetainedE3Custody(directory, selection, specification, allocation, package, plan,
                    terminal, reveal, receipts, configs, arrays, MappingProxyType(dict(descriptors)),
                    models, freeze, prefit, writer, current, access, check_controls)
                token = _active_original_reads.set((*_active_original_reads.get(), retained))
                yield retained
                current()
            finally:
                active = False
                if token is not None:
                    _active_original_reads.reset(token)
