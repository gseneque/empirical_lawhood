# SPDX-License-Identifier: MPL-2.0
"""Shared bounded custody mechanics for original and configured protected E3.

Scientific codecs, method projections and falsifiers remain in their typed
families. Each invocation replays its current grants and exact original receipts;
no authorization or mutable evidence cache survives the owning read.
"""
from contextlib import contextmanager
from dataclasses import dataclass

from .current_result_custody import _index_execution_tasks, _require_current_task_receipt_outputs, authenticate_historical_execution_authority, require_current_result_reveal_authority
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from ..infrastructure.recovery import ExternalRunRecoveryStore
from empirical_lawhood.infrastructure.study_issue import ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore, PROGRAMME_ISSUE_GRANTEE_ID
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_bytes_with_identity
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.runtime.prospective_experiment import ALLOCATION_FILENAME, SPECIFICATION_FILENAME
from empirical_lawhood.runtime.recovery import RunRecoveryIndex


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


def original_design(selected, *, specification_type):
    specification = decode_canonical_bytes(selected.payloads[SPECIFICATION_FILENAME],
        specification_type, maximum_bytes=None)
    allocation = decode_canonical_bytes(selected.payloads[ALLOCATION_FILENAME], UnitAllocation, maximum_bytes=None)
    if ((specification.identity, allocation.identity) != (selected.instance.specification, selected.instance.allocation)
            or specification.evidence_scope != 'PROSPECTIVE_REQUIRED'):
        raise PermissionError('PROTECTED_E3_READ_ORIGINAL_DESIGN_REQUIRED')
    return specification, allocation


def _publication(writer, package, *, publication_reader=None):
    """Replay the historical issue act; it need not be a new current issue act."""
    if publication_reader is None:
        publication_reader = ExternalIssuedStudyPublisher(artifact_plane=writer,
            authority_store=ExternalStudyOperationAuthorityStore(writer), grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)
    elif (type(publication_reader) is not ExternalIssuedStudyPublisher
            or not publication_reader._read_only_context
            or publication_reader._artifact_plane.root is not writer.root):
        raise PermissionError('PROTECTED_E3_READ_ORIGINAL_PUBLICATION_READER_REQUIRED')
    published = publication_reader.load_executable_study(package.issued_study.issue_id,
        **({'expected_manifest': package.issued_study} if publication_reader._read_only_context else {}))
    if (published.manifest != package.issued_study or published.publication_receipt != package.publication_receipt):
        raise PermissionError('PROTECTED_E3_READ_ORIGINAL_ISSUED_PUBLICATION_REQUIRED')


def _current_read_grants(writer, package, reveal_authority_id):
    """Authenticate genuine current reveal; historical execution is per receipt."""
    if reveal_authority_id is None:
        raise PermissionError('PROTECTED_E3_READ_REVEAL_AUTHORITY_REQUIRED')
    validate_stable_id(reveal_authority_id)
    require_current_result_reveal_authority(writer=writer, package=package,
        reveal_authority_id=reveal_authority_id)


def authorize(writer, package, reveal_authority_id, *, publication_reader=None):
    """Fresh explicit current grants precede any protected scientific payload."""
    if reveal_authority_id is None:
        raise PermissionError('PROTECTED_E3_READ_REVEAL_AUTHORITY_REQUIRED')
    _publication(writer, package, **({} if publication_reader is None else {'publication_reader': publication_reader}))
    _current_read_grants(writer, package, reveal_authority_id)


def _require_current_read_layout(writer, run_id):
    """Refuse retired continuation layouts without loading their contracts."""
    for name in ('source-continuation', 'native-parent-closeout'):
        if writer.root.resolve(f'runs/{run_id}/recovery/{name}', for_write=False).exists():
            raise PermissionError('PROTECTED_E3_READ_RETIRED_LAYOUT_UNSUPPORTED')


def completed_receipts(writer, package, plan, *, capability_prefix):
    """Authenticate the current plan's complete terminal and exact outputs."""
    _require_current_read_layout(writer, package.run_plan_id)
    wave_id = 'wave.' + package.package_id
    recovery = ExternalRunRecoveryStore(writer)
    index = recovery.read_index(f'runs/{package.run_plan_id}/recovery/{wave_id}/resource-run-recovery-index.json',
        expected_schema=RunRecoveryIndex.SCHEMA)
    if index.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan):
        raise PermissionError('PROTECTED_E3_READ_EXACT_RECOVERY_PLAN_REQUIRED')
    terminal = recovery.read_terminal(index)
    expected = set(_index_execution_tasks(plan))
    if (terminal is None or terminal.operational_status != 'SUCCEEDED'
            or set(terminal.completed_task_ids) != expected or terminal.failed_task_ids or terminal.blocked_task_ids
            or {row.task_id for row in index.tasks} != expected):
        raise PermissionError('PROTECTED_E3_READ_COMPLETE_TERMINAL_REQUIRED')
    receipts = _completed_task_receipts(writer, package, plan, terminal=terminal,
        expected=expected, capability_prefix=capability_prefix)
    _require_consumed_parents(plan, receipts, expected)
    return receipts, terminal


def _completed_task_receipts(writer, package, plan, *, terminal, expected, capability_prefix):
    tasks_by_id = _index_execution_tasks(plan)
    store = ExternalTaskReceiptStore(writer)
    # Index only within this authenticated read. No receipt or authority cache
    # survives its owning verification operation.
    attempts_by_task = {}
    for row in terminal.attempts:
        attempts_by_task.setdefault(row.task_id, []).append(row)
    receipts = {}
    for task_id in sorted(expected):
        attempts = attempts_by_task.get(task_id, ())
        if not attempts:
            raise PermissionError('PROTECTED_E3_READ_EXACT_SUCCESS_RECEIPT_REQUIRED')
        last = attempts[-1]
        receipt = store.read_by_receipt_id(package.run_plan_id, task_id, last.receipt_id)
        if (receipt is None or receipt.fingerprint() != last.receipt_sha256
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or not receipt.output_logical_artifacts):
            raise PermissionError('PROTECTED_E3_READ_EXACT_SUCCESS_RECEIPT_REQUIRED')
        _require_current_task_receipt_outputs(receipt=receipt, logical=receipt.output_logical_artifacts[0],
            execution_plan=plan, task=tasks_by_id[task_id], capability_prefixes=(capability_prefix,))
        authenticate_historical_execution_authority(package=package, execution_plan=plan,
            receipt=receipt, writer=writer)
        manifests = tuple(ArtifactManifest(logical, next(row for row in receipt.output_materializations
            if row.logical_artifact_id == logical.logical_artifact_id)) for logical in receipt.output_logical_artifacts)
        # Nested products share the operation's immutable closure. A plain
        # caller still gets a finite context for this exact output batch.
        with writer.read_context() as output_writer:
            output_writer.verify_manifests(manifests)
        receipts[task_id] = receipt
    return receipts


def _require_consumed_parents(plan, receipts, completed):
    for task in plan.tasks:
        if task.task_id not in completed:
            continue
        for edge in task.scientific_inputs:
            if edge.producer_task_id is None:
                continue
            parent = receipts.get(edge.producer_task_id)
            if parent is None:
                raise PermissionError('PROTECTED_E3_READ_EXACT_CONSUMED_PARENT_REQUIRED')
            parents = tuple(row for row in parent.output_materializations
                if row.logical_artifact_id == edge.operational_logical_artifact_id)
            if len(parents) != 1 or parents[0].materialization_id not in receipts[task.task_id].input_materialization_ids:
                raise PermissionError('PROTECTED_E3_READ_EXACT_CONSUMED_PARENT_REQUIRED')


@dataclass(frozen=True, slots=True)
class ProtectedE3ReceiptRead:
    writer: object
    receipts: dict
    terminal: object
    _current_read: object = None
    _active_read: object = None
    _access_read: object = None

    def require_active(self):
        if not callable(self._active_read):
            raise PermissionError('PROTECTED_E3_READ_CURRENT_SCOPE_REQUIRED')
        self._active_read()

    def require_current(self):
        """Replay this live read's current custody/grants; confer no execution."""
        if not callable(self._current_read):
            raise PermissionError('PROTECTED_E3_READ_CURRENT_SCOPE_REQUIRED')
        self._current_read()

    def require_access(self):
        """Refresh live grants without traversing the whole product snapshot."""
        if not callable(self._access_read):
            raise PermissionError('PROTECTED_E3_READ_CURRENT_SCOPE_REQUIRED')
        self._access_read()


@contextmanager
def configured_receipt_read(writer, package, plan, *, reveal_authority_id):
    """Keep current receipts and product reads inside one authenticated lifetime."""
    _require_current_read_layout(writer, package.run_plan_id)
    authorize(writer, package, reveal_authority_id)
    lifetime = {'active': True}

    def require_live():
        if not lifetime['active']:
            raise PermissionError('PROTECTED_E3_READ_CURRENT_SCOPE_EXPIRED')

    try:
        with writer.read_context() as view:
            receipts, terminal = completed_receipts(view, package, plan,
                capability_prefix='matrix-e3-configured-protected.')

            def access():
                require_live()
                _current_read_grants(writer, package, reveal_authority_id)

            def current():
                access()
                view.require_verification_snapshot()

            yield ProtectedE3ReceiptRead(view, receipts, terminal, current, require_live, access)
            view.require_verification_snapshot()
        authorize(writer, package, reveal_authority_id)
    finally:
        lifetime['active'] = False


def product(writer, plan, receipts, task_id, kind):
    receipt = receipts[task_id]
    matches = tuple(row for row in receipt.output_logical_artifacts if row.payload_schema == kind.SCHEMA)
    if len(matches) != 1:
        raise PermissionError('PROTECTED_E3_READ_EXACT_TYPED_PRODUCT_REQUIRED')
    logical = matches[0]
    physical, = (row for row in receipt.output_materializations if row.logical_artifact_id == logical.logical_artifact_id)
    # Authenticate again in this small typed-product lifetime before decoding.
    writer.verify_manifest(ArtifactManifest(logical, physical))
    raw = read_bounded_bytes(writer.root.resolve(physical.relative_path, for_write=False), maximum_bytes=physical.size_bytes)
    decoded = decode_canonical_bytes_with_identity(raw, kind, maximum_bytes=physical.size_bytes,
        expected_sha256=logical.content_sha256)
    record = decoded.record
    if (decoded.size_bytes != physical.size_bytes or decoded.content_sha256 != physical.physical_sha256
            or record.fingerprint() != decoded.content_sha256):
        raise PermissionError('PROTECTED_E3_READ_TYPED_PRODUCT_BYTES_MISMATCH')
    return record, {'receipt': ObjectIdentity.from_record(receipt.receipt_id, receipt).to_document(),
        'logical_artifact': logical.to_document(), 'materialization': physical.to_document()}
