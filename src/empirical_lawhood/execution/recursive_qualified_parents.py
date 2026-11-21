# SPDX-License-Identifier: MPL-2.0
"""Exact prior qualification locators; these declarations confer no authority."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_schema, validate_stable_id

from empirical_lawhood.execution.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.storage.contracts.artifacts import ArtifactMaterialization, CanonicalTaskReceipt, LogicalArtifactIdentity
from empirical_lawhood.execution.plans import ExecutionPlan, ProtocolExecutionPlan
from empirical_lawhood.execution.native_subwork import NativeSubworkInspection


# Existing revision-1 limits. These are local record/read limits, not an
# allocation or a bound on every EL graph. Keep canonical fields unchanged.
MAX_PARENT_BYTES = 16 * 1024**2
MAX_PARENT_BINDINGS = 32
MAX_PRIOR_EXECUTIONS = 32
MAX_PRIOR_COMPANION_SCHEMAS = 4
MAX_PRIOR_NATIVE_BINDINGS = 216
PRIOR_RECORD_ID_FIELDS = (
    'record_id', 'result_id', 'config_id', 'calibration_id',
    'admission_id', 'evidence_id', 'receipt_id',
)


@dataclass(frozen=True, slots=True)
class RecursiveQualifiedParentBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/recursive-qualified-parent-binding'

    binding_id: str
    external_input_id: str
    contribution_id: str
    product_id: str
    issued_study: ObjectIdentity
    execution_authority: ObjectIdentity
    reveal_authority: ObjectIdentity
    run_id: str
    task_id: str
    receipt_id: str
    qualification_task_id: str
    qualification_receipt_id: str
    qualification_output_id: str
    adjudication: ObjectIdentity

    def __post_init__(self):
        for name in ('binding_id', 'external_input_id', 'contribution_id', 'product_id', 'run_id',
                     'task_id', 'receipt_id', 'qualification_task_id', 'qualification_receipt_id',
                     'qualification_output_id'):
            validate_stable_id(getattr(self, name), field_name=name)
        if self.issued_study.object_schema != 'empirical-lawhood/runtime/issued-executable-study-manifest':
            raise ValueError('qualified parent requires a genuine issued executable study')
        if any(value.object_schema != 'empirical-lawhood/planning/study-operation-authority'
               for value in (self.execution_authority, self.reveal_authority)):
            raise ValueError('qualified parent requires exact execution and reveal grant identities')
        if self.adjudication.object_schema != ScientificAdjudicationRecord.SCHEMA:
            raise ValueError('qualified parent requires a registered typed adjudication')


@dataclass(frozen=True, slots=True)
class RecursivePriorNativeBinding(CanonicalRecord):
    """An exact completed subwork locator within an original execution task."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/recursive-prior-native-binding'
    task_id: str
    definition: ObjectIdentity
    completion: ObjectIdentity
    receipt: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.task_id)
        for value, schema in ((self.definition, 'empirical-lawhood/runtime/native-subwork-definition'),
                (self.completion, 'empirical-lawhood/runtime/native-subwork-completion'),
                (self.receipt, CanonicalTaskReceipt.SCHEMA)):
            if (value.object_schema, value.object_version) != (schema, '1.0.0'):
                raise ValueError('prior native execution changes an exact definition/completion/receipt type')
        if self.completion.object_id != 'completion.'+self.definition.object_id:
            raise ValueError('prior native completion changes its exact definition reference')


@dataclass(frozen=True, slots=True)
class RecursivePriorExecutionBinding(CanonicalRecord):
    """Exact original issued execution locator; it grants no authority."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/recursive-prior-execution-binding'
    binding_id: str
    issued_study: ObjectIdentity
    execution_authority: ObjectIdentity
    package: ObjectIdentity
    execution_plan: ObjectIdentity
    run_id: str
    task_id: str
    receipt: ObjectIdentity
    logical_artifact_id: str
    record: ObjectIdentity
    additional_output_schema_ids: tuple[str, ...] = ()
    native_subwork: tuple[RecursivePriorNativeBinding, ...] = ()
    record_id_field: str = 'record_id'
    scope_output_schema_ids: tuple[str, ...] = ()

    def __post_init__(self):
        for name in ('binding_id', 'run_id', 'task_id', 'logical_artifact_id'):
            validate_stable_id(getattr(self, name), field_name=name)
        if self.record_id_field not in PRIOR_RECORD_ID_FIELDS:
            raise ValueError('prior execution requires an explicit installed record identifier field')
        expected = ((self.issued_study, 'empirical-lawhood/runtime/issued-executable-study-manifest'),
            (self.execution_authority, 'empirical-lawhood/planning/study-operation-authority'),
            (self.package, 'empirical-lawhood/api/experiment-package'),
            (self.execution_plan, ExecutionPlan.SCHEMA), (self.receipt, CanonicalTaskReceipt.SCHEMA))
        if any((identity.object_schema, identity.object_version) != (schema, '1.0.0') for identity, schema in expected):
            raise ValueError('prior execution requires exact current issued package, grant, plan and receipt types')
        schemas = self.additional_output_schema_ids
        if type(schemas) is not tuple or len(schemas) > MAX_PRIOR_COMPANION_SCHEMAS or schemas != tuple(sorted(set(schemas))):
            raise ValueError('prior execution additional outputs exceed their bounded exact schema census')
        for schema in schemas:
            validate_schema(schema)
        scope_schemas = self.scope_output_schema_ids
        if (type(scope_schemas) is not tuple or len(scope_schemas) > MAX_PRIOR_COMPANION_SCHEMAS
                or scope_schemas != tuple(sorted(set(scope_schemas)))
                or not set(scope_schemas) <= set(schemas)):
            raise ValueError('prior execution scope metadata must be a bounded declared additional output subset')
        natives = self.native_subwork
        if (type(natives) is not tuple or len(natives) > MAX_PRIOR_NATIVE_BINDINGS
                or any(type(value) is not RecursivePriorNativeBinding for value in natives)
                or len({(value.task_id, value.definition) for value in natives}) != len(natives)):
            raise ValueError('prior native execution exceeds its exact bounded subwork census')


def require_prior_execution_bindings(requests):
    """The existing outer census check, shared by preflight and actual replay."""
    if (type(requests) is not tuple or not requests or len(requests) > MAX_PRIOR_EXECUTIONS
            or any(type(value) is not RecursivePriorExecutionBinding for value in requests)
            or len({value.binding_id for value in requests}) != len(requests)
            or len({(value.run_id, value.task_id) for value in requests}) != len(requests)):
        raise PermissionError('qualified parent prior executions lack their bounded exhaustive exact locator census')


def prior_result_capacity():
    """Report the installed unchanged limits without inspecting any source."""
    return dict(record_schema=RecursivePriorExecutionBinding.SCHEMA,
        record_version=RecursivePriorExecutionBinding.VERSION,
        record_identifier_fields=PRIOR_RECORD_ID_FIELDS,
        maximum_parent_bindings=MAX_PARENT_BINDINGS,
        maximum_prior_executions_per_parent=MAX_PRIOR_EXECUTIONS,
        maximum_companion_schemas_per_binding=MAX_PRIOR_COMPANION_SCHEMAS,
        maximum_native_bindings_per_prior_execution=MAX_PRIOR_NATIVE_BINDINGS,
        primary_payload_maximum_bytes=MAX_PARENT_BYTES,
        companion_aggregate_maximum_bytes=MAX_PARENT_BYTES,
        scope_metadata_aggregate_maximum_bytes=MAX_PARENT_BYTES,
        group_key=('run_id', 'task_id'), duplicate_original_task_per_parent=False,
        independent_units_inferred=False, complete_memory_capacity_established=False,
        scientific_authority='NONE')


def inspect_prior_execution_bindings(requests):
    """Describe an already supplied finite census; authenticate no evidence.

    References are not independent units. Original source, receipt, access and
    domain-scope admission still belong to the existing qualified-parent reader.
    """
    require_prior_execution_bindings(requests)
    for request in requests:
        request.__post_init__()
    natives = tuple(native for request in requests for native in request.native_subwork)
    return dict(capacity=prior_result_capacity(), prior_execution_count=len(requests),
        distinct_run_count=len({row.run_id for row in requests}),
        native_reference_count=len(natives),
        distinct_native_definition_count=len({row.definition for row in natives}),
        companion_schema_reference_count=sum(len(row.additional_output_schema_ids) for row in requests),
        scope_schema_reference_count=sum(len(row.scope_output_schema_ids) for row in requests),
        declared_binding_bytes=sum(row.canonical_size_bytes() for row in requests),
        binding_identities=tuple(ObjectIdentity.from_record(row.binding_id, row).to_document() for row in requests),
        independent_unit_count=None, authenticated_receipts=False, native_contacts=0)


@dataclass(frozen=True, slots=True)
class QualifiedParentAdditionalProduct:
    """One explicitly requested actual companion output, after custody replay."""

    logical: LogicalArtifactIdentity
    materialization: ArtifactMaterialization
    payload: bytes


@dataclass(frozen=True, slots=True)
class QualifiedParentPriorNative:
    binding: RecursivePriorNativeBinding
    inspection: NativeSubworkInspection


@dataclass(frozen=True, slots=True)
class QualifiedParentPriorExecution:
    """Noncanonical actual custody view; no per-run qualification is inferred."""

    binding: RecursivePriorExecutionBinding
    package: CanonicalRecord
    execution_plan: ExecutionPlan
    receipts: tuple[CanonicalTaskReceipt, ...]
    product: QualifiedParentAdditionalProduct
    additional_products: tuple[QualifiedParentAdditionalProduct, ...] = ()
    native_subwork: tuple[QualifiedParentPriorNative, ...] = ()


@dataclass(frozen=True, slots=True)
class QualifiedParentEvidence:
    """Authenticated read-only view supplied to a code-owned domain assessor."""

    binding: RecursiveQualifiedParentBinding
    package: CanonicalRecord
    execution_plan: ProtocolExecutionPlan
    producing_receipt: CanonicalTaskReceipt
    qualification_receipt: CanonicalTaskReceipt
    adjudication: ScientificAdjudicationRecord
    product_payload: bytes
    additional_products: tuple[QualifiedParentAdditionalProduct, ...] = ()
    prior_executions: tuple[QualifiedParentPriorExecution, ...] = ()
    prior_scope_products: tuple[QualifiedParentAdditionalProduct, ...] = ()
