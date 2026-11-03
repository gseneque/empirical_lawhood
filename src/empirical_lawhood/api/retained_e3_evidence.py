# SPDX-License-Identifier: MPL-2.0
"""Receipt-bound E3 operands without retrospective numerical reconstruction.

Original outputs remain under their actual producers and current grants.
Only immutable records are shared within the live operation. No permission,
completion or scientific qualification is cached between invocations.
"""
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactManifest

_active = ContextVar('retained_e3_evidence', default=None)


def current_e3_evidence(writer):
    """Return only an active read of this exact guarded root and policy."""
    current = _active.get()
    if current is not None and current.active and current.writer.root is writer.root:
        from empirical_lawhood.infrastructure.artifacts import _has_stock_manifest_reads
        if (_has_stock_manifest_reads(writer) and _has_stock_manifest_reads(current.writer)
                and current.writer.custody_limits is writer.custody_limits
                and current.writer.validators is writer.validators
                and (current.writer.semantic_validations is writer.semantic_validations
                    or current.owns_output_view(writer))):
            return current
    return None


def retained_e3_reader(writer):
    """Borrow this invocation's read owner only for an unchanged publisher.

    Callers must use the returned plane for reads only. Scoped callers retain
    their own callbacks, and custom or differently selected policies keep
    their ordinary reader. This creates no publication or access authority.
    """
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, _has_stock_artifact_plane_state
    current = current_e3_evidence(writer)
    if (current is not None and type(writer) is ExternalArtifactPlane
            and _has_stock_artifact_plane_state(writer)
            and writer.artifact_verification is current.writer.artifact_verification
            and writer.maximum_parallel_verifications == current.writer.maximum_parallel_verifications):
        current.writer.require_active_verification_scope()
        return current.writer
    return writer


def recorded_product_kinds():
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import (
        ConfiguredProtectedE3ModelSet, ConfiguredProtectedE3FrozenProducts, ConfiguredProtectedE3Calibration,
    )
    return (ConfiguredProtectedE3ModelSet, ConfiguredProtectedE3FrozenProducts, ConfiguredProtectedE3Calibration)


def _pin(value, field):
    return ObjectIdentity.from_record(getattr(value, field), value)


@dataclass(frozen=True)
class RecordedProducer:
    package: object
    plan: object
    index: object
    report: dict
    reveal: object
    evidence: object
    control_pins: tuple

    @property
    def writer(self):
        """Typed output custody is needed when a scientific product is consumed."""
        from .recursive_operations import operation_catalog
        self.evidence.require_access(self)
        writer = self.evidence.reader.output_artifact_plane(package=self.package,
            execution_plan=self.plan, output_codecs=operation_catalog()[2])
        self.evidence._output_views.setdefault(id(writer), (writer, writer.semantic_validations))
        return writer


class RetainedE3Evidence:
    def __init__(self, writer, publisher):
        from .current_result_custody import CurrentResultPlanReader
        self.writer, self.publisher = writer, publisher
        self.reader = CurrentResultPlanReader(writer)
        self.producers = {}
        self.receipts = {}
        self.boundaries = {}
        self.scheduling = {}
        self.authored_controls = {}
        self.training = {}
        self._output_views = {}
        self.active = True

    def owns_output_view(self, writer):
        """Recognize only this reader's unchanged, registered typed output view.

        Control reuse stays on the original control writer. Scientific output
        reads still use the view's distinct semantic registry and validators.
        Merely sharing a root or an equivalent registry grants no reuse.
        """
        selected = self._output_views.get(id(writer))
        return (selected is not None and selected[0] is writer
            and selected[1] is writer.semantic_validations
            and writer.artifact_verification is self.writer.artifact_verification
            and getattr(writer, '_read_verification', None) is self.writer._read_verification)

    def require_access(self, producer=None):
        from .protected_e3_read_custody import _current_read_grants
        if not self.active:
            raise PermissionError('retained E3 evidence escaped its owning read')
        self.writer.require_active_verification_scope()
        for row in self.producers.values() if producer is None else (producer,):
            _current_read_grants(self.writer, row.package, row.reveal.authority_id)

    def require_custody(self):
        """Close the original complete control census, including absent attempts."""
        from .recursive_execution import _custody_control_pins
        self.require_access()
        for row in self.producers.values():
            if _custody_control_pins(self.writer, row.index) != row.control_pins:
                raise PermissionError('retained E3 execution controls changed during operand consumption')
        self.writer.require_verification_snapshot()

    def producer(self, run_id, reveal_id, *, package_pin=None, plan_pin=None):
        from .recursive_qualified_parents import _actual_package
        from .protected_e3_read_custody import authorize
        from .retained_e3_control_repair import selected_repair_index
        from .experiment_execution_read import read_execution_records
        from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
        key = run_id, reveal_id
        row = self.producers.get(key)
        if row is None:
            package = _actual_package(self.writer, run_id, control_reader=self.reader)
            authorize(self.writer, package, reveal_id, publication_reader=self.publisher)
            reveal = ExternalStudyOperationAuthorityStore(self.writer).load(reveal_id)
            plan = self.reader.authenticate_execution_plan(package=package, issued=package.issued_study, run_id=run_id)
            index = selected_repair_index(writer=self.writer, plan=plan,
                predecessor=self.reader.original_recovery_index(package=package, execution_plan=plan))
            controls = []
            report = read_execution_records(writer=self.writer, plan=plan, index=index,
                observe_controls=lambda index, pins: controls.append(pins))
            row = RecordedProducer(package, plan, index, report, reveal, self, controls[0])
            self.producers[key] = row
        if ((package_pin is not None and _pin(row.package, 'package_id') != package_pin)
                or (plan_pin is not None and _pin(row.plan, 'execution_plan_id') != plan_pin)):
            raise PermissionError('retained E3 changes an original producing package or plan')
        self.require_access(row)
        return row

    def receipt(self, producer, task_id, expected=None):
        from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
        from .current_result_custody import _require_current_task_receipt_outputs, authenticate_historical_execution_authority
        rows = tuple(row for row in producer.report['operational_census']
            if row['task_id'] == task_id and row['operational_status'] == 'SUCCEEDED')
        if len(rows) != 1:
            raise PermissionError('retained E3 requires one actual successful producing receipt')
        row, = rows
        receipt = ExternalTaskReceiptStore(self.writer).read_by_receipt_id(
            producer.package.run_plan_id, task_id, row['receipt_id'])
        if (receipt is None or receipt.fingerprint() != row['receipt_sha256']
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or expected is not None and _pin(receipt, 'receipt_id') != expected):
            raise PermissionError('retained E3 changes its actual successful receipt')
        task = self.reader.execution_task(execution_plan=producer.plan, task_id=task_id)
        _require_current_task_receipt_outputs(receipt=receipt, logical=receipt.output_logical_artifacts[0],
            execution_plan=producer.plan, task=task, capability_prefixes=('matrix-e3-configured-protected.',))
        authenticate_historical_execution_authority(package=producer.package, execution_plan=producer.plan,
            receipt=receipt, writer=self.writer)
        self.require_access(producer)
        return receipt

    def product_metadata(self, original, expected):
        from .recursive_qualified_parents import _replay_parent_authority
        original.__post_init__()
        binding = original.prior_execution
        if binding.record != expected:
            raise PermissionError('retained E3 substitutes its selected scientific product')
        row = self.producer(binding.run_id, original.reveal_authority.object_id,
            package_pin=binding.package, plan_pin=binding.execution_plan)
        issued, reveal = _replay_parent_authority(original, row.package, self.writer,
            _issued_reader=self.publisher)
        receipt = self.receipt(row, binding.task_id, binding.receipt)
        matches = tuple(value for value in receipt.output_logical_artifacts
            if value.logical_artifact_id == binding.logical_artifact_id)
        if len(matches) != 1 or (matches[0].payload_schema, matches[0].content_sha256) != (
                expected.object_schema, expected.object_fingerprint):
            raise PermissionError('retained E3 substitutes original receipt-bound output bytes')
        prefixes = tuple(sorted(value.capability_key for value in row.package.registry.capabilities))
        return row.package, issued, reveal, receipt, matches[0], prefixes

    def boundary(self, boundary):
        """Authenticate recorded exclusion and import custody, without recreating it."""
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution
        from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
        from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
        from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
        from .recursive_execution import _custody_control_pins
        key = boundary.identity
        if key in self.boundaries:
            self.require_access()
            return self.boundaries[key]
        producer = self.producer(boundary.predecessor_run_id, boundary.predecessor_reveal_authority.object_id,
            package_pin=boundary.predecessor_package, plan_pin=boundary.predecessor_plan)
        if producer.report.get('terminal') != (None if boundary.predecessor_terminal is None else boundary.predecessor_terminal.to_document()):
            raise PermissionError('retained E3 changes its original partial terminal')
        successes = {row['task_id']: row for row in producer.report['operational_census']
            if row['operational_status'] == 'SUCCEEDED'}
        # A closed boundary also carries previously imported successes. Their
        # actual producer is checked by imported(); do not create local receipts.
        for task_id, receipt in boundary.completed_receipts:
            if task_id in {task.task_id for task in producer.plan.tasks}:
                actual = successes.get(task_id)
                if actual is None or (actual['receipt_id'], actual['receipt_sha256']) != (
                        receipt.object_id, receipt.object_fingerprint):
                    raise PermissionError('retained E3 changes its original successful attempt census')
        if type(boundary) is ConfiguredE3ClosedExecution:
            if (_pin(producer.index, 'recovery_index_id') != boundary.predecessor_recovery_index
                    or sha256(canonical_json_bytes(_custody_control_pins(self.writer, producer.index))).hexdigest()
                        != boundary.predecessor_custody_sha256):
                raise PermissionError('retained CAL closeout changes its original complete control census')
            tasks = {row.task_id: row for row in producer.plan.tasks}
            contacts = ExternalNativeEffectContactStore(plane=self.writer,
                execution_plan=boundary.predecessor_plan, visibility_ceiling=VisibilityCeiling.PROSPECTIVE,
                outcome_access=OutcomeAccess.OUTCOME_BLIND,
                task_scopes={key: (task.outputs[0].visibility_ceiling, task.capability.requested_outcome_access)
                    for key, task in tasks.items()})
            for root in boundary.calibration_roots:
                contact = contacts.read(boundary.predecessor_run_id, root.native_task_id)
                if contact is None or ObjectIdentity.from_record('native-contact.' + contact.task_id, contact) != root.contact:
                    raise PermissionError('retained CAL closeout changes an original entered contact')
                if root.missing_products is not None and any(row['task_id'] == root.native_task_id
                        and row['operational_status'] == 'SUCCEEDED' for row in producer.report['operational_census']):
                    raise PermissionError('retained CAL closeout substitutes completion for an unknown contact')
            envelope = ExternalRunRecoveryStore(self.writer).reconstruct_execution_resource_envelope(
                index=producer.index, envelope_id='run-resource-envelope.' + producer.index.run_id,
                spec=producer.package.execution_resource_envelope_spec,
                execution_plan=boundary.predecessor_plan,
                jit_graph_signature_manifest=producer.package.jit_graph_signature_manifest)
            if _pin(envelope, 'envelope_id') != boundary.predecessor_resource_envelope:
                raise PermissionError('retained CAL closeout changes original resource reservations')
            self.boundary(boundary.original_boundary)
        self.boundaries[key] = producer
        return producer

    def imported(self, boundary, task_id):
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution
        self.boundary(boundary)
        imports = tuple(row for row in boundary.imported_outputs if row.task_id == task_id)
        if not imports or len({row.receipt for row in imports}) != 1:
            raise PermissionError('retained E3 omits its original imported product')
        actual = {PurePosixPath(row.materialization.relative_path).parts[1] for row in imports
            if PurePosixPath(row.materialization.relative_path).parts[0] == 'runs'}
        if len(actual) != 1:
            raise PermissionError('retained E3 imports have no unique actual producing run')
        run_id, = actual
        candidates = [boundary]
        if type(boundary) is ConfiguredE3ClosedExecution:
            candidates.append(boundary.original_boundary)
        matches = [row for row in candidates if row.predecessor_run_id == run_id]
        if len(matches) != 1:
            raise PermissionError('retained E3 imports an unrelated producer')
        source, = matches
        producer = self.producer(run_id, source.predecessor_reveal_authority.object_id,
            package_pin=source.predecessor_package, plan_pin=source.predecessor_plan)
        receipt = self.receipt(producer, task_id, imports[0].receipt)
        for row in imports:
            if row.logical not in receipt.output_logical_artifacts or row.materialization not in receipt.output_materializations:
                raise PermissionError('retained E3 import changes original receipt-bound bytes')
            producer.writer.verify_manifest(ArtifactManifest(row.logical, row.materialization))
        return producer, receipt

    def original_config(self, retention, task, config):
        """Authenticate a PURE byte adoption, without refitting or replaying arrays."""
        from .matrix_selected_runtime import _published_input
        config.validate_retention(retention)
        producer = self.producer(retention.original_run_id, retention.original_reveal_authority.object_id,
            package_pin=retention.original_package, plan_pin=retention.original_plan)
        if producer.report.get('terminal') != retention.original_terminal.to_document():
            raise PermissionError('retained E3 adoption changes its original terminal')
        receipt = self.receipt(producer, task.task_id, _pin(config.original_receipt, 'receipt_id'))
        original_task = self.reader.execution_task(execution_plan=producer.plan, task_id=task.task_id)
        if original_task != config.original_task or receipt != config.original_receipt:
            raise PermissionError('retained E3 adoption changes its original task or receipt')
        specs = tuple(row for row in original_task.external_inputs
            if row.logical_artifact_id == original_task.capability.config.artifact_id)
        if len(specs) != 1 or _published_input(producer.writer, retention.original_run_id,
                specs[0], type(config.original_config)) != config.original_config:
            raise PermissionError('retained E3 adoption changes its original scientific configuration')
        return config.original_config


@contextmanager
def retained_e3_evidence_context(artifact_writer):
    from empirical_lawhood.infrastructure.study_issue import ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore, PROGRAMME_ISSUE_GRANTEE_ID
    from .selected_e3_access import original_e3_authority_read_context
    current = current_e3_evidence(artifact_writer)
    if current is not None:
        current.require_access()
        yield current
        current.require_access()
        return
    with ExitStack() as lifetime:
        lifetime.enter_context(original_e3_authority_read_context(artifact_writer))
        writer = lifetime.enter_context(artifact_writer.read_context())
        publisher = ExternalIssuedStudyPublisher(artifact_plane=writer,
            authority_store=ExternalStudyOperationAuthorityStore(writer), grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)
        publisher = lifetime.enter_context(publisher.read_context())
        read = RetainedE3Evidence(writer, publisher)
        token = _active.set(read)
        try:
            yield read
        finally:
            try:
                read.require_custody()
            finally:
                read.active = False
                _active.reset(token)
