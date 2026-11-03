# SPDX-License-Identifier: MPL-2.0
"""Receipt-bound inputs for an E3 wave containing only unfinished work.

These records describe original custody. They neither create successful tasks
nor permit another native contact. The API authenticates the preceding run and
its complete resource history before deriving or using this boundary.
"""
from empirical_lawhood.kernel.decoding import validate_record_fields
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt, LogicalArtifactIdentity, ArtifactMaterialization
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding

from .configured_retained_execution import ConfiguredE3RetainedExecution, require_numerical_source_continuity, source_binding


@dataclass(frozen=True, slots=True)
class ConfiguredE3CompletedOutput(CanonicalRecord):
    """One actual successful output selected by its original producing port."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-completed-output'
    task_id: str
    output_id: str
    receipt: ObjectIdentity
    logical: LogicalArtifactIdentity
    materialization: ArtifactMaterialization

    def __post_init__(self):
        validate_stable_id(self.task_id)
        validate_stable_id(self.output_id)
        if (type(self.receipt) is not ObjectIdentity or self.receipt.object_schema != CanonicalTaskReceipt.SCHEMA
                or type(self.logical) is not LogicalArtifactIdentity
                or type(self.materialization) is not ArtifactMaterialization):
            raise TypeError('completed E3 input requires its actual receipt and original output identities')
        for value in (self.receipt, self.logical, self.materialization):
            validate_record_fields(value)
        if (self.materialization.logical_artifact_id != self.logical.logical_artifact_id
                or self.materialization.physical_sha256 != self.logical.content_sha256):
            raise ValueError('completed E3 input changes its original output bytes')

    @property
    def key(self):
        return self.task_id, self.output_id.rsplit('.', 1)[-1]


@dataclass(frozen=True, slots=True)
class ConfiguredE3UnfinishedExecution(CanonicalRecord):
    """An immutable predecessor plus the disjoint remaining execution census."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-unfinished-execution'
    record_id: str
    predecessor_authoring_directory: str
    predecessor_run_id: str
    predecessor_package: ObjectIdentity
    predecessor_plan: ObjectIdentity
    predecessor_terminal: ObjectIdentity
    predecessor_resource_envelope: ObjectIdentity
    predecessor_reveal_authority: ObjectIdentity
    predecessor_source: RecursiveImplementationBinding
    retention: ConfiguredE3RetainedExecution
    completed_receipts: tuple[tuple[str, ObjectIdentity], ...]
    unfinished_task_ids: tuple[str, ...]
    imported_outputs: tuple[ConfiguredE3CompletedOutput, ...]

    def __post_init__(self):
        self._validate_boundary(allow_absent_terminal=False)

    def _validate_boundary(self, *, allow_absent_terminal):
        validate_stable_id(self.record_id)
        validate_relative_locator(self.predecessor_authoring_directory)
        validate_stable_id(self.predecessor_run_id)
        if type(self.retention) is not ConfiguredE3RetainedExecution:
            raise TypeError('unfinished E3 requires its original scientific retention contract')
        validate_record_fields(self.retention)
        if self.predecessor_run_id in (self.retention.original_run_id, self.retention.continued_run_id):
            raise ValueError('unfinished E3 must distinguish original science, preceding adoption and new execution')
        require_numerical_source_continuity(self.predecessor_source, source_binding(self.retention.response_provenance))
        schemas = (
            (self.predecessor_package, ('empirical-lawhood/api/experiment-package',)),
            (self.predecessor_plan, ('empirical-lawhood/runtime/execution-plan',)),
            (self.predecessor_terminal, ('empirical-lawhood/runtime/run-recovery-terminal-event',
                'empirical-lawhood/runtime/retained-e3-repair-terminal-event',
                'empirical-lawhood/runtime/retained-e3-continued-repair-terminal-event')),
            (self.predecessor_resource_envelope, ('empirical-lawhood/runtime/run-execution-resource-envelope',)),
            (self.predecessor_reveal_authority, ('empirical-lawhood/planning/study-operation-authority',)),
        )
        for pin, allowed in schemas:
            if (pin is None and allow_absent_terminal
                    and 'empirical-lawhood/runtime/run-recovery-terminal-event' in allowed):
                continue
            if type(pin) is not ObjectIdentity or pin.object_schema not in allowed:
                raise ValueError('unfinished E3 changes its exact predecessor custody contracts')
            validate_record_fields(pin)
        done = tuple(key for key, _ in self.completed_receipts)
        pending = self.unfinished_task_ids
        if (not done or done != tuple(sorted(set(done))) or not pending
                or pending != tuple(sorted(set(pending))) or set(done).intersection(pending)):
            raise ValueError('unfinished E3 requires disjoint complete successful and unexecuted task selections')
        for task, receipt in self.completed_receipts:
            validate_stable_id(task)
            if type(receipt) is not ObjectIdentity or receipt.object_schema != CanonicalTaskReceipt.SCHEMA:
                raise ValueError('unfinished E3 must retain actual successful receipt identities')
            validate_record_fields(receipt)
        for task in pending:
            validate_stable_id(task)
        imports = self.imported_outputs
        if (not imports or any(type(row) is not ConfiguredE3CompletedOutput for row in imports)
                or tuple(row.key for row in imports) != tuple(sorted({row.key for row in imports}))
                or len({row.logical.logical_artifact_id for row in imports}) != len(imports)):
            raise ValueError('unfinished E3 changes its unique imported output census')
        receipts = dict(self.completed_receipts)
        for row in imports:
            validate_record_fields(row)
            if receipts.get(row.task_id) != row.receipt:
                raise ValueError('unfinished E3 input loses its actual successful producer')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def imported(self, task_id, output_id):
        rows = tuple(row for row in self.imported_outputs if row.key == (task_id, output_id.rsplit('.', 1)[-1]))
        if len(rows) != 1:
            raise ValueError('unfinished E3 omits its exact original producing output')
        return rows[0]


def unfinished_input(context):
    """Read the optional frozen boundary through the ordinary bounded port."""
    from .protected_input_custody import read_protected_e3_response_input
    from .configured_closeout_execution import ConfiguredE3ClosedExecution
    kinds = {kind.SCHEMA: kind for kind in (ConfiguredE3UnfinishedExecution, ConfiguredE3ClosedExecution)}
    rows = tuple(port for port in context.input_ports if port.payload_schema in kinds)
    if not rows:
        return None
    if len(rows) != 1:
        raise ValueError('unfinished E3 duplicates its predecessor boundary')
    port = rows[0].cursor()
    try:
        scope = read_protected_e3_response_input(port, context.prepared_invocation, kinds[port.payload_schema])
    finally:
        port.close()
    if context.run_id != scope.retention.continued_run_id or context.task_id not in scope.unfinished_task_ids:
        raise ValueError('unfinished E3 attempts completed or foreign work')
    return scope


def require_imported_input(scope, context, port, producer, output):
    """Bind an external copy to the actual old receipt, without a new receipt."""
    from empirical_lawhood.runtime.execution import WorkerInputKind
    if scope is None or producer not in dict(scope.completed_receipts):
        return False
    original = scope.imported(producer, output)
    logical, physical = original.logical, original.materialization
    if (port.kind is not WorkerInputKind.EXTERNAL or
            (port.artifact_id, port.payload_schema, port.media_type, port.size_bytes,
                port.outcome_access, port.visibility_ceiling) != (
                logical.logical_artifact_id, logical.payload_schema, logical.media_type,
                physical.size_bytes, logical.outcome_access, logical.visibility_ceiling)):
        raise ValueError('unfinished E3 changes original receipted input identity or access')
    prepared = context.prepared_invocation
    if prepared is not None:
        row, = (row for row in prepared.inputs if row.artifact_id == port.artifact_id)
        if (row.logical.content_sha256, row.physical_sha256) != (logical.content_sha256, physical.physical_sha256):
            raise ValueError('unfinished E3 changes original receipted input bytes')
    return True


def unfinished_port():
    from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
    return RecursivePortContract('unfinished', ConfiguredE3UnfinishedExecution.SCHEMA,
        'application/json', None, minimum_count=0, maximum_count=1)
