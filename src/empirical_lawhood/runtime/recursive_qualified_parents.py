# SPDX-License-Identifier: MPL-2.0
"""Exact prior qualification locators; these declarations confer no authority."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_schema, validate_stable_id

from .adjudication import ScientificAdjudicationRecord
from .artifacts import ArtifactMaterialization, CanonicalTaskReceipt, LogicalArtifactIdentity
from .plans import ExecutionPlan, ProtocolExecutionPlan
from .native_subwork import NativeSubworkInspection


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
        if self.record_id_field not in ('record_id', 'result_id', 'config_id', 'calibration_id', 'admission_id', 'evidence_id', 'receipt_id'):
            raise ValueError('prior execution requires an explicit installed record identifier field')
        expected = ((self.issued_study, 'empirical-lawhood/runtime/issued-executable-study-manifest'),
            (self.execution_authority, 'empirical-lawhood/planning/study-operation-authority'),
            (self.package, 'empirical-lawhood/api/experiment-package'),
            (self.execution_plan, ExecutionPlan.SCHEMA), (self.receipt, CanonicalTaskReceipt.SCHEMA))
        if any((identity.object_schema, identity.object_version) != (schema, '1.0.0') for identity, schema in expected):
            raise ValueError('prior execution requires exact current issued package, grant, plan and receipt types')
        schemas = self.additional_output_schema_ids
        if type(schemas) is not tuple or len(schemas) > 4 or schemas != tuple(sorted(set(schemas))):
            raise ValueError('prior execution additional outputs exceed their bounded exact schema census')
        for schema in schemas:
            validate_schema(schema)
        scope_schemas = self.scope_output_schema_ids
        if (type(scope_schemas) is not tuple or len(scope_schemas) > 4
                or scope_schemas != tuple(sorted(set(scope_schemas)))
                or not set(scope_schemas) <= set(schemas)):
            raise ValueError('prior execution scope metadata must be a bounded declared additional output subset')
        natives = self.native_subwork
        if (type(natives) is not tuple or len(natives) > 216
                or any(type(value) is not RecursivePriorNativeBinding for value in natives)
                or len({(value.task_id, value.definition) for value in natives}) != len(natives)):
            raise ValueError('prior native execution exceeds its exact bounded subwork census')


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
