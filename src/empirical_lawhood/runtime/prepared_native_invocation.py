# SPDX-License-Identifier: MPL-2.0
"""Joined prepared native inputs; no source lookup, publication or authority."""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import PurePath
from typing import ClassVar

from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactManifest, LogicalArtifactIdentity
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityManifest, CapabilityPermission, CapabilityRegistry
from empirical_lawhood.runtime.execution import DependencyReceiptBinding, TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputPort, WorkerIsolationProfile, WorkerOutputPort
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkRoster
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceTaskCellSpec
from empirical_lawhood.runtime.plans import ExecutionTask, ProtocolExecutionTask
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationContext
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection


@dataclass(frozen=True, slots=True)
class PreparedWorkerEnvironment(CanonicalRecord):
    """Selected executable, interpreter environment and post-sanitize settings."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/prepared-worker-environment"
    interpreter_path: str
    interpreter_sha256: str
    prefix: str
    selected_environment: tuple[tuple[str, str], ...]

    def __post_init__(self):
        for value in (self.interpreter_path, self.prefix):
            if type(value) is not str or not PurePath(value).is_absolute() or ".." in PurePath(value).parts:
                raise ValueError("prepared worker environment requires exact absolute interpreter paths")
        validate_sha256(self.interpreter_sha256)
        if (type(self.selected_environment) is not tuple
                or self.selected_environment != tuple(sorted(self.selected_environment))
                or len({name for name, _ in self.selected_environment}) != len(self.selected_environment)
                or any(type(name) is not str or not name or type(value) is not str
                    for name, value in self.selected_environment)):
            raise ValueError("prepared worker settings require sorted unique string bindings")


@dataclass(frozen=True, slots=True)
class PreparedNativeInputContract(CanonicalRecord):
    """Exact logical/physical byte identity without a storage locator or port."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/prepared-native-input-contract"
    logical: LogicalArtifactIdentity
    binding: WorkerInputBinding
    physical_sha256: str
    scientific_identity: ObjectIdentity | None = None

    def __post_init__(self):
        if type(self.logical) is not LogicalArtifactIdentity or type(self.binding) is not WorkerInputBinding:
            raise ValueError("prepared input contract requires exact typed logical/transport identities")
        validate_sha256(self.physical_sha256)
        if (self.binding.artifact_id, self.binding.payload_schema, self.binding.media_type,
                self.binding.visibility_ceiling, self.binding.outcome_access) != (
                self.logical.logical_artifact_id, self.logical.payload_schema, self.logical.media_type,
                self.logical.visibility_ceiling, self.logical.outcome_access):
            raise ValueError("prepared input contract changes its logical transport boundary")
        if self.scientific_identity is not None and (
                type(self.scientific_identity) is not ObjectIdentity
                or (self.scientific_identity.object_schema, self.scientific_identity.object_fingerprint)
                != (self.logical.payload_schema, self.logical.content_sha256)):
            raise ValueError("prepared input contract changes its original scientific identity")

    @property
    def artifact_id(self):
        return self.binding.artifact_id


@dataclass(frozen=True, slots=True)
class PreparedNativeWork(CanonicalRecord):
    """PURE initial effect scope; an unpublished contact value grants no entry."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/prepared-native-work"
    VERSION: ClassVar[str] = "1.1.0"
    expected_parent: NativeEffectContact
    scientific_unit_ids: tuple[str, ...]
    native_effect_slot_ids: tuple[str, ...]
    definitions: tuple[NativeSubworkDefinition, ...] = ()
    rosters: tuple[NativeSubworkRoster, ...] = ()
    isolated_selection: IsolatedNativeEntrySelection | None = None
    isolated_environment: PreparedWorkerEnvironment | None = None
    isolated_diagnostics: "tuple[WorkerPreflightResult, ...]" = ()

    def __post_init__(self):
        if type(self.expected_parent) is not NativeEffectContact:
            raise ValueError("prepared native work requires its exact anticipated parent")
        self.expected_parent.__post_init__()
        require_sorted_unique_strings(self.scientific_unit_ids, field_name="scientific_unit_ids", allow_empty=False)
        require_sorted_unique_strings(self.native_effect_slot_ids, field_name="native_effect_slot_ids", allow_empty=False)
        for rows, kind, key in ((self.definitions, NativeSubworkDefinition, "subwork_id"),
                (self.rosters, NativeSubworkRoster, "roster_id")):
            if type(rows) is not tuple or any(type(row) is not kind for row in rows):
                raise ValueError("prepared native work requires its exact typed initial census")
            require_sorted_unique_ids(rows, attribute=key, field_name=key)
            for row in rows:
                row.__post_init__()
                if row.parent_contact != self.expected_parent:
                    raise ValueError("prepared native work changes its complete anticipated parent")
        if bool(self.definitions) != bool(self.rosters):
            raise ValueError("prepared nested native work requires its complete initial roster")
        if self.rosters:
            if (len(self.rosters) != 1 or self.rosters[0].roster_id != "selected.native-subwork"
                    or self.rosters[0].parent_subwork is not None
                    or self.rosters[0].subworks != tuple(row.identity for row in self.definitions)):
                raise ValueError("prepared native work changes its complete initial definition census")
        if (self.isolated_selection is None) != (self.isolated_environment is None):
            raise ValueError("prepared native work requires its complete isolated selection/environment pair")
        if self.isolated_selection is not None:
            if type(self.isolated_selection) is not IsolatedNativeEntrySelection or type(self.isolated_environment) is not PreparedWorkerEnvironment:
                raise ValueError("prepared native work requires exact typed isolated selection/environment")
            self.isolated_selection.__post_init__()
            self.isolated_environment.__post_init__()
            environment_sha256 = sha256(json.dumps(dict(self.isolated_environment.selected_environment),
                sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
            if (self.isolated_selection.interpreter_path, self.isolated_selection.interpreter_sha256,
                    self.isolated_selection.environment_sha256) != (
                    self.isolated_environment.interpreter_path, self.isolated_environment.interpreter_sha256,
                    environment_sha256):
                raise ValueError("prepared isolated work changes its exact interpreter/hash/full environment")
        if (type(self.isolated_diagnostics) is not tuple or len(self.isolated_diagnostics) > 2
                or any(type(row) is not WorkerPreflightResult for row in self.isolated_diagnostics)):
            raise ValueError("prepared isolated work requires at most two exact typed diagnostic snapshots")
        projection = (self.expected_parent, self.scientific_unit_ids, self.native_effect_slot_ids,
            self.definitions, self.rosters)
        for diagnostic in self.isolated_diagnostics:
            diagnostic.__post_init__()
            observed = diagnostic.native_work
            if observed is not None and (observed.isolated_diagnostics or (
                    observed.expected_parent, observed.scientific_unit_ids, observed.native_effect_slot_ids,
                    observed.definitions, observed.rosters) != projection):
                raise ValueError("prepared isolated diagnostics substitute work or contain recursive evidence")
            if diagnostic.ready and (self.isolated_environment is None
                    or diagnostic.environment != self.isolated_environment
                    or observed is None or observed.isolated_selection != self.isolated_selection
                    or observed.isolated_environment != self.isolated_environment):
                raise ValueError("prepared isolated positive diagnostic changes its selected environment/work")
        if len(self.isolated_diagnostics) == 2:
            initial, final = self.isolated_diagnostics
            if (tuple(row.operand_id for row in initial.mismatches) != ("worker.prefix",)
                    or initial.environment != self.isolated_environment or not final.ready):
                raise ValueError("prepared isolated diagnostics change initial prefix observation/final readiness order")


@dataclass(frozen=True, slots=True)
class PreparedInvocationContract(CanonicalRecord):
    """One complete port-free invocation; custody and effect authority stay outside."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/prepared-invocation-contract"
    VERSION: ClassVar[str] = "1.1.0"
    invocation_id: str
    manifest: CapabilityManifest
    implementation: RecursiveImplementationBinding
    environment: PreparedWorkerEnvironment
    run_id: str
    task_id: str
    attempt_id: str
    config: CapabilityConfigRef
    inputs: tuple[PreparedNativeInputContract, ...]
    output_ports: tuple[WorkerOutputPort, ...]
    permissions: tuple[CapabilityPermission, ...]
    outcome_access: OutcomeAccess
    resource_budget: ResourceBudget
    isolation_profile: WorkerIsolationProfile
    dependency_receipts: tuple[DependencyReceiptBinding, ...] = ()
    cpu_affinity: tuple[int, ...] = ()
    execution_plan: ObjectIdentity | None = None
    execution_task: ObjectIdentity | None = None
    native_work: PreparedNativeWork | None = None
    resource_cell: ExecutionResourceTaskCellSpec | None = None
    provenance_requirement_ids: tuple[str, ...] = ()
    required_input_artifact_ids: tuple[str, ...] = ()
    native_effect: bool = False
    execution_task_record: ExecutionTask | ProtocolExecutionTask | None = None
    scientific_adjudication_context: ScientificAdjudicationContext | None = None
    native_preparation_error: str | None = None

    def __post_init__(self):
        for value in (self.invocation_id, self.run_id, self.task_id, self.attempt_id):
            validate_stable_id(value)
        for value, kind in ((self.manifest, CapabilityManifest),
                (self.implementation, RecursiveImplementationBinding),
                (self.environment, PreparedWorkerEnvironment), (self.config, CapabilityConfigRef),
                (self.resource_budget, ResourceBudget)):
            if type(value) is not kind:
                raise ValueError("prepared invocation requires exact typed execution selections")
            value.__post_init__()
        for rows, kind, attribute in ((self.inputs, PreparedNativeInputContract, "artifact_id"),
                (self.output_ports, WorkerOutputPort, "output_id"),
                (self.dependency_receipts, DependencyReceiptBinding, "receipt_id")):
            if type(rows) is not tuple or any(type(value) is not kind for value in rows):
                raise ValueError("prepared invocation requires an exact typed complete census")
            require_sorted_unique_ids(rows, attribute=attribute, field_name=attribute)
            for value in rows:
                value.__post_init__()
        require_sorted_unique_strings(self.permissions, field_name="permissions")
        require_sorted_unique_strings(self.provenance_requirement_ids, field_name="provenance_requirement_ids")
        require_sorted_unique_strings(self.required_input_artifact_ids, field_name="required_input_artifact_ids")
        if type(self.native_effect) is not bool:
            raise ValueError("prepared invocation requires its exact declared effect selection")
        if self.native_preparation_error is not None and (type(self.native_preparation_error) is not str or not self.native_preparation_error):
            raise ValueError("prepared invocation requires its actual native preparation error")
        if self.native_work is not None:
            if type(self.native_work) is not PreparedNativeWork or not self.native_effect:
                raise ValueError("prepared invocation changes its explicit native effect selection")
            self.native_work.__post_init__()
            if self.native_work.expected_parent != self.expected_parent_contact:
                raise ValueError("prepared invocation changes its complete anticipated native parent")
            for diagnostic in self.native_work.isolated_diagnostics:
                if diagnostic.ready or tuple(row.operand_id for row in diagnostic.mismatches) == ("worker.prefix",):
                    provenance = diagnostic.producing_provenance
                    if provenance is None or (provenance.package_sources, provenance.code_sources_sha256,
                            provenance.dependency_lock_sha256, provenance.observed_git_head) != (
                            self.implementation.package_sources, self.implementation.code_sources_sha256,
                            self.implementation.dependency_lock_sha256, self.implementation.observed_git_head):
                        raise ValueError("prepared isolated diagnostic changes its full selected implementation")
                    if (diagnostic.invocation.object_id, diagnostic.invocation.object_schema,
                            diagnostic.invocation.object_version) != (self.invocation_id, self.SCHEMA, self.VERSION):
                        raise ValueError("prepared isolated diagnostic changes its original task/input/output selection")
                    if diagnostic.ready:
                        snapshot = replace(self, environment=self.native_work.isolated_environment,
                            native_work=diagnostic.native_work, native_preparation_error=None)
                        if diagnostic.invocation != snapshot.identity:
                            raise ValueError("prepared isolated readiness changes its original task/input/output selection")
        if self.execution_task_record is not None:
            self.validate_task_projection()
        if self.scientific_adjudication_context is not None:
            if (type(self.scientific_adjudication_context) is not ScientificAdjudicationContext
                    or self.scientific_adjudication_context.execution_plan != self.execution_plan):
                raise ValueError("prepared invocation changes its exact adjudication execution scope")
        for value in (self.execution_plan, self.execution_task):
            if value is not None and type(value) is not ObjectIdentity:
                raise ValueError("prepared invocation requires exact execution identities")
        if self.execution_task is not None and self.execution_task.object_id != self.task_id:
            raise ValueError("prepared invocation substitutes its execution task identity")
        if (self.config.config_schema, self.config.config_schema_sha256) != (
                self.manifest.config_schema, self.manifest.config_schema_sha256):
            raise ValueError("prepared invocation changes its declared configuration schema")
        if not self.manifest.resource_ceiling.contains(self.resource_budget):
            raise ValueError("prepared invocation exceeds its declared resources")
        if not set(self.permissions).issubset(self.manifest.permissions):
            raise ValueError("prepared invocation changes its declared permissions")
        if not set(row.payload_schema for row in self.output_ports).issubset(self.manifest.output_schema_ids):
            raise ValueError("prepared invocation changes its declared output schemas")
        if (self.cpu_affinity != tuple(sorted(set(self.cpu_affinity)))
                or any(type(value) is not int or value < 0 for value in self.cpu_affinity)
                or len(self.cpu_affinity) > self.resource_budget.cpu_cores):
            raise ValueError("prepared invocation changes its CPU placement")
        materializations = tuple(row.binding.materialization_id for row in self.inputs)
        if len(set(materializations)) != len(materializations):
            raise ValueError("prepared invocation duplicates an input materialization")
        if tuple(sorted(value for row in self.dependency_receipts
                for value in row.output_materialization_ids)) != tuple(sorted(
                row.binding.materialization_id for row in self.inputs if row.binding.kind.value == "DEPENDENCY")):
            raise ValueError("prepared invocation changes its dependency receipt census")
        if self.resource_cell is not None:
            if type(self.resource_cell) is not ExecutionResourceTaskCellSpec:
                raise ValueError("prepared invocation requires its typed execution resource cell")
            self.resource_cell.__post_init__()
            if self.resource_cell.task_id != self.task_id:
                raise ValueError("prepared invocation changes its selected resource task cell")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.invocation_id, self)

    def require_complete(self):
        if self.execution_plan is None or self.execution_task is None or self.execution_task_record is None:
            raise ValueError("prepared invocation lacks its selected execution plan/task identities and original task")
        self.validate_task_projection()

    @property
    def expected_parent_contact(self):
        if self.execution_plan is None or self.execution_task is None:
            raise ValueError("prepared native work lacks its exact plan/task identity")
        return NativeEffectContact(self.run_id, self.task_id, self.attempt_id, self.execution_plan,
            self.execution_task, self.implementation.observed_git_head,
            tuple(sorted(row.binding.materialization_id for row in self.inputs)),
            tuple(row.receipt_id for row in self.dependency_receipts))

    @property
    def native_definitions(self):
        return () if self.native_work is None else self.native_work.definitions

    @property
    def native_rosters(self):
        return () if self.native_work is None else self.native_work.rosters

    def validate_task_projection(self):
        task = self.execution_task_record
        if type(task) not in (ExecutionTask, ProtocolExecutionTask):
            raise ValueError("prepared invocation requires its original typed execution task")
        task.__post_init__()
        CapabilityRegistry("prepared.selected-capability", (self.manifest,)).require(task.capability)
        if ObjectIdentity.from_record(task.task_id, task) != self.execution_task:
            raise ValueError("prepared invocation substitutes its original execution task fingerprint")
        outputs = tuple(WorkerOutputPort(row.output_id, row.payload_schema, row.profile,
            row.media_type, row.logical_artifact_id) for row in task.outputs)
        if (self.task_id, self.config, self.output_ports, self.permissions, self.outcome_access,
                self.resource_budget, self.manifest.capability_key, self.manifest.capability_version,
                self.manifest.implementation_sha256) != (task.task_id, task.capability.config,
                outputs, task.capability.required_permissions, task.capability.requested_outcome_access,
                task.capability.requested_resources, task.capability.capability_key,
                task.capability.capability_version, task.capability_implementation_sha256):
            raise ValueError("prepared invocation changes the original task config/output/permission/resource projection")
        expected = set(task.external_input_artifact_ids)
        if type(task) is ExecutionTask:
            expected.update(row.operational_logical_artifact_id for row in task.scientific_inputs)
        else:
            # Historical protocol tasks carry producer task/receipt identities
            # without the later exact scientific-edge record. Preserve that
            # original boundary; do not invent output-edge metadata for them.
            expected.update(row.artifact_id for row in self.inputs if row.binding.kind.value == "DEPENDENCY")
        if expected != set(self.required_input_artifact_ids):
            raise ValueError("prepared invocation changes the original complete task input census")
        if not {row.artifact_id for row in self.inputs}.issubset(expected):
            raise ValueError("prepared invocation adds an undeclared task input")
        specs = {row.logical_artifact_id: row for row in task.external_inputs}
        scientific_edges = () if type(task) is not ExecutionTask else task.scientific_inputs
        receipt_by_materialization = {materialization: receipt for receipt in self.dependency_receipts
            for materialization in receipt.output_materialization_ids}
        for row in self.inputs:
            spec = specs.get(row.artifact_id)
            if spec is not None and ((spec.expected_payload_schema is not None and row.logical.payload_schema != spec.expected_payload_schema)
                    or (spec.expected_media_type is not None and row.logical.media_type != spec.expected_media_type)
                    or (spec.expected_visibility_ceiling is not None and row.logical.visibility_ceiling is not spec.expected_visibility_ceiling)
                    or (spec.expected_outcome_access is not None and row.logical.outcome_access is not spec.expected_outcome_access)
                    or (spec.expected_content_sha256 is not None and row.logical.content_sha256 != spec.expected_content_sha256)
                    or (spec.expected_size_bytes is not None and row.binding.size_bytes != spec.expected_size_bytes)):
                raise ValueError("prepared invocation changes an exact original external input")
            for edge in scientific_edges:
                if edge.operational_logical_artifact_id != row.artifact_id:
                    continue
                if ((row.logical.payload_schema, row.logical.media_type, row.logical.visibility_ceiling,
                        row.logical.outcome_access) != (edge.payload_schema, edge.media_type,
                        edge.visibility_ceiling, edge.outcome_access)
                        or (edge.maximum_size_bytes is not None and row.binding.size_bytes > edge.maximum_size_bytes)):
                    raise ValueError("prepared invocation changes its original scientific input edge")
                receipt = receipt_by_materialization.get(row.binding.materialization_id)
                if edge.producer_task_id is not None:
                    if receipt is None or receipt.task_id != edge.producer_task_id or row.binding.kind.value != "DEPENDENCY":
                        raise ValueError("prepared invocation changes its original scientific producer receipt")
                elif receipt is not None or row.binding.kind.value != "EXTERNAL":
                    raise ValueError("prepared invocation changes its original scientific external input origin")
        if tuple(sorted(row.task_id for row in self.dependency_receipts)) != task.dependency_task_ids:
            raise ValueError("prepared invocation changes its original dependency task receipt census")

    def validate_context(self, context):
        if (type(context) is not TaskContext or (context.prepared_invocation is not None
                and (type(context.prepared_invocation) is not PreparedInvocationContract
                    or context.prepared_invocation != self))):
            raise ValueError("prepared invocation changes its exact bound worker contract")
        expected = (self.run_id, self.task_id, self.attempt_id, self.config,
            tuple(row.binding for row in self.inputs), self.output_ports, self.permissions,
            self.outcome_access, self.resource_budget, self.isolation_profile,
            self.dependency_receipts, self.cpu_affinity, self.scientific_adjudication_context)
        actual = (context.run_id, context.task_id, context.attempt_id, context.config,
            context.input_bindings, context.output_ports, context.permissions, context.outcome_access,
            context.resource_budget, context.isolation_profile, context.dependency_receipts, context.cpu_affinity,
            context.scientific_adjudication_context)
        if actual != expected:
            raise ValueError("prepared invocation changes its complete worker context")


@dataclass(frozen=True, slots=True)
class WorkerPreflightMismatch(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/worker-preflight-mismatch"
    operand_id: str
    reason: str

    def __post_init__(self):
        validate_stable_id(self.operand_id)
        if type(self.reason) is not str or not self.reason:
            raise ValueError("worker preflight mismatch requires its actual reason")


@dataclass(frozen=True, slots=True)
class WorkerPreflightResult(CanonicalRecord):
    """Observed actual-worker readiness; never effect or qualification authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/worker-preflight-result"
    VERSION: ClassVar[str] = "1.1.0"
    invocation: ObjectIdentity
    producing_provenance: NumericalProducingProvenance | None
    environment: PreparedWorkerEnvironment | None
    mismatches: tuple[WorkerPreflightMismatch, ...]
    native_work: PreparedNativeWork | None = None

    def __post_init__(self):
        if type(self.invocation) is not ObjectIdentity or self.invocation.object_schema != PreparedInvocationContract.SCHEMA:
            raise ValueError("worker preflight changes its selected invocation")
        if (type(self.mismatches) is not tuple
                or any(type(row) is not WorkerPreflightMismatch for row in self.mismatches)
                or self.mismatches != tuple(sorted(set(self.mismatches), key=lambda row: (row.operand_id, row.reason)))):
            raise ValueError("worker preflight requires its complete sorted unique mismatch census")
        if not self.mismatches and (type(self.producing_provenance) is not NumericalProducingProvenance
                or type(self.environment) is not PreparedWorkerEnvironment):
            raise ValueError("worker readiness requires actual producing observations")

    @property
    def ready(self):
        return not self.mismatches


@dataclass(frozen=True, slots=True)
class PreparedNativeInput:
    """One scientific identity paired with its authenticated worker bytes."""

    identity: ObjectIdentity
    manifest: ArtifactManifest
    port: WorkerInputPort

    def __post_init__(self):
        if (type(self.identity) is not ObjectIdentity or type(self.manifest) is not ArtifactManifest
                or type(self.port) is not WorkerInputPort):
            raise ValueError("prepared native input requires exact identity, manifest and worker port")
        logical = self.manifest.logical
        if (logical.payload_schema, logical.content_sha256) != (
                self.identity.object_schema, self.identity.object_fingerprint):
            raise ValueError("prepared native input changes its scientific source identity")
        verified = VerifiedArtifactInput(logical, self.manifest.materialization)
        if self.port.binding != WorkerInputBinding.from_verified(verified, kind=self.port.kind):
            raise ValueError("prepared native input changes its authenticated worker port")


@dataclass(frozen=True, slots=True)
class PreparedNativeInvocation:
    """Complete available inputs, with all execution projections derived once."""

    inputs: tuple[PreparedNativeInput, ...]
    contract: PreparedInvocationContract | None = None

    def __post_init__(self):
        if not self.inputs or any(type(value) is not PreparedNativeInput for value in self.inputs):
            raise ValueError("prepared native invocation requires its complete typed inputs")
        ids = tuple(value.port.artifact_id for value in self.inputs)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("prepared native inputs require sorted unique transport identities")
        if len(set(self.input_materialization_ids)) != len(self.inputs):
            raise ValueError("prepared native invocation duplicates a materialization")
        for value in self.inputs:
            value.__post_init__()
        if self.contract is not None:
            if type(self.contract) is not PreparedInvocationContract:
                raise ValueError("prepared native invocation requires its typed complete contract")
            self.contract.__post_init__()
            expected = tuple(PreparedNativeInputContract(value.manifest.logical, value.port.binding,
                value.manifest.materialization.physical_sha256, value.identity) for value in self.inputs)
            if self.contract.inputs != expected:
                raise ValueError("prepared invocation contract substitutes its exact joined inputs")

    @property
    def complete(self):
        return (self.contract is not None and self.contract.execution_plan is not None
            and self.contract.execution_task is not None and self.contract.execution_task_record is not None)

    @property
    def input_materialization_ids(self):
        return tuple(sorted(value.port.materialization_id for value in self.inputs))

    @property
    def manifests(self):
        return tuple(value.manifest for value in self.inputs)

    @property
    def input_bindings(self):
        return tuple(value.port.binding for value in self.inputs)

    @property
    def verified_inputs(self):
        return tuple(VerifiedArtifactInput(value.manifest.logical, value.manifest.materialization)
            for value in self.inputs)

    @property
    def input_ports(self):
        return tuple(value.port for value in self.inputs)

    def close(self):
        for port in self.input_ports:
            port.close()

    def open_many(self, values, *, bindings, maximum_bytes):
        """Supply these exact ports through the existing scheduler factory port."""
        if maximum_bytes is not None and (type(maximum_bytes) is not int or maximum_bytes < 0):
            raise ValueError("prepared native input budget is invalid")
        if len(values) != len(self.inputs) or len(bindings) != len(values):
            raise ValueError("prepared native factory changes its complete input census")
        by_id = {value.port.materialization_id: value for value in self.inputs}
        actual_ids = tuple(sorted(value.materialization.materialization_id for value in values))
        if actual_ids != self.input_materialization_ids:
            raise ValueError("prepared native factory substitutes its exact input materializations")
        if maximum_bytes is not None and sum(value.materialization.size_bytes for value in values) > maximum_bytes:
            raise ValueError("prepared native inputs exceed the selected source-scan budget")
        result = []
        for value, binding in zip(values, bindings, strict=True):
            selected = by_id[value.materialization.materialization_id]
            if (value != VerifiedArtifactInput(selected.manifest.logical, selected.manifest.materialization)
                    or binding != selected.port.binding):
                raise ValueError("prepared native factory substitutes its verified input or worker binding")
            if selected.port.bytes_read:
                raise ValueError("prepared native factory input was already consumed")
            selected.port.read(0)  # Refuse consumed/closed ports rather than silently reopen them.
            result.append(selected.port)
        return tuple(result)

    def open(self, value, *, binding=None, maximum_bytes):
        """The existing single-input port exposes only its exact prepared member."""
        matches = tuple(row for row in self.inputs
            if row.manifest.materialization == value.materialization and row.manifest.logical == value.logical)
        if len(matches) != 1 or (binding is not None and binding != matches[0].port.binding):
            raise ValueError("prepared native single input substitutes its exact binding")
        if maximum_bytes is not None and (type(maximum_bytes) is not int or maximum_bytes < value.materialization.size_bytes):
            raise ValueError("prepared native single input exceeds its selected source-scan budget")
        if matches[0].port.bytes_read:
            raise ValueError("prepared native single input was already consumed")
        matches[0].port.read(0)
        return matches[0].port

    def definition(self, *, subwork_id, operation_id, parent_contact, configuration,
                   sources, provenance: NumericalProducingProvenance, streams=(), outputs=(),
                   roster_id="selected.native-subwork"):
        """Derive the selected definition without another input/source census."""
        available = {value.identity for value in self.inputs}
        selected_sources = tuple(sorted((*sources, provenance.identity), key=lambda value: value.object_id))
        for identity in (configuration, *selected_sources, *streams):
            if identity not in available:
                raise ValueError("native definition identity is outside its prepared input bindings: "
                    + identity.object_id)
        return NativeSubworkDefinition(subwork_id, operation_id, parent_contact, configuration,
            selected_sources, provenance.code_sources_sha256, provenance.dependency_lock_sha256,
            self.input_materialization_ids, tuple(sorted(streams, key=lambda value: value.object_id)),
            tuple(sorted(outputs, key=lambda value: value.output_id)), roster_id)
