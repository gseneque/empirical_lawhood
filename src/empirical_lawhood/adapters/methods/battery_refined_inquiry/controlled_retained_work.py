# SPDX-License-Identifier: MPL-2.0
"""Original unfinished forecast custody, without completion or replay authority.

The selected root is operational metadata. Scientific records remain independent
ports, and every current boundary rereads the selected original primary custody.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_segmented_inquiry import operation_bindings as original
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryAttempt, InquiryAttemptStatus
from empirical_lawhood.kernel.recursive_inquiry_policy import InquiryAttemptWorkBinding, ScientificInquiryWork
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_relative_locator, validate_sha256, validate_stable_id
from empirical_lawhood.planning.recursive_inquiry_policy import uncertain_contact_requires_recovery
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt, ExternalRootContract
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, ExecutionTask
from empirical_lawhood.runtime.recovery import TaskRecoveryEvent
from . import contracts as c, forecast_step_control as step

PRIMARY_TYPES = {
    "contact": NativeEffectContact,
    "event": TaskRecoveryEvent,
    "plan": DevelopmentExecutionPlan,
    "task": ExecutionTask,
    "config": original.SegmentedOperationConfig,
    "assignment": step.ActualForecastStepAssignment,
    "assignment-receipt": CanonicalTaskReceipt,
    "assignment-definition": NativeSubworkDefinition,
}
PATH_ROLES = tuple(sorted(set(PRIMARY_TYPES) - {"task"}))
MAX_PRIMARY_CLOSURE_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class RetainedForecastRootSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/retained-forecast-root-selection"
    selection_id: str
    storage: ExternalRootContract
    paths: tuple[tuple[str, str], ...]
    records: tuple[tuple[str, ObjectIdentity], ...]

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        if type(self.storage) is not ExternalRootContract:
            raise ValueError("retained forecast needs its explicitly selected original guarded root")
        self.storage.__post_init__()
        if (type(self.paths) is not tuple or tuple(role for role, _ in self.paths) != PATH_ROLES
                or type(self.records) is not tuple or tuple(role for role, _ in self.records) != tuple(sorted(PRIMARY_TYPES))):
            raise ValueError("retained forecast changes its complete primary path/record census")
        if len({path for _, path in self.paths}) != len(self.paths):
            raise ValueError("retained forecast aliases original primary roles")
        for _, path in self.paths:
            validate_relative_locator(path)
        for role, ref in self.records:
            kind = PRIMARY_TYPES[role]
            if type(ref) is not ObjectIdentity or (ref.object_schema, ref.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("retained forecast substitutes an original primary schema/revision")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class RetainedForecastWorkCondition(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/retained-forecast-work-condition"
    condition_id: str
    selected_root: ObjectIdentity
    attempt: InquiryAttempt
    binding: InquiryAttemptWorkBinding
    original_request_sha256: str

    def __post_init__(self):
        validate_stable_id(self.condition_id)
        validate_sha256(self.original_request_sha256)
        if (type(self.selected_root) is not ObjectIdentity or self.selected_root.object_schema != RetainedForecastRootSelection.SCHEMA
                or type(self.attempt) is not InquiryAttempt or type(self.binding) is not InquiryAttemptWorkBinding):
            raise ValueError("retained forecast condition loses its typed actual attempt witnesses")
        self.attempt.__post_init__()
        self.binding.__post_init__()
        if (self.attempt.status is not InquiryAttemptStatus.UNCERTAIN_CONTACT or self.attempt.products
                or self.binding.attempt_id != self.attempt.attempt_id or self.binding.configuration != self.attempt.operation
                or self.binding.witness != self.attempt.receipt or self.binding.work is not None
                or self.binding.authored_wave is not None):
            raise ValueError("retained unfinished forecast cannot invent completion or an authored scientific-work binding")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.condition_id, self)


@dataclass(frozen=True, slots=True)
class ControlledForecastPhysicalWork(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/controlled-forecast-physical-work"
    native_request_sha256: str

    def __post_init__(self):
        validate_sha256(self.native_request_sha256)



def request_sha256(native_config, selected_control):
    """The original physical recipe plus exact step, without instance labels."""
    return sha256(canonical_json_bytes({"original_forecast_primitive": original.forecast_primitive(native_config).decode(),
        "maximum_internal_step_s": selected_control.maximum_internal_step_s})).hexdigest()


def work_from_request(native_request_sha256, scoped):
    meaning = ControlledForecastPhysicalWork(native_request_sha256)
    identity = ObjectIdentity.from_record("method.battery-controlled-forecast.physical-request", meaning)
    scoped = replace(scoped, source_id="source.battery-controlled-forecast.physical-request",
        source_config_sha256=meaning.fingerprint(), receiver_id="receiver.battery-controlled-forecast")
    return ScientificInquiryWork(identity, (identity,), scoped,
        ObjectIdentity.from_record("observation.battery-controlled-forecast.original-full-trace", meaning))


def selected_work(native_config, selected_control):
    return work_from_request(request_sha256(native_config, selected_control), c.scope(native_config.native.source))


def require_permitted_work(condition, work, successor_config):
    if type(condition) is not RetainedForecastWorkCondition:
        raise ValueError("controlled forecast requires the original retained unfinished-work condition")
    condition.__post_init__()
    if uncertain_contact_requires_recovery(operational_census=(condition.attempt,), attempt_work_bindings=(condition.binding,),
            selected_work=work, successor_config=successor_config):
        raise ValueError("UNCERTAIN_CONTACT_RECOVERY_REQUIRED: original forecast remains UNKNOWN; authenticated receipt recovery is required before another native contact")


def require_no_uncertain_replay(condition, native_config, selected_control, successor_config):
    require_permitted_work(condition, selected_work(native_config, selected_control), successor_config)


def _identity(role, record, selected):
    expected = dict(selected.records)[role]
    if type(record) is not PRIMARY_TYPES[role]:
        raise ValueError("retained forecast substitutes an original typed primary record")
    record.__post_init__()
    actual = ObjectIdentity.from_record(expected.object_id, record)
    if actual != expected:
        raise ValueError("retained forecast substitutes an exact original primary identity")
    return actual


def derive_condition(selected, records):
    """Project exact original UNKNOWN evidence; no invented old authored wave."""
    if type(selected) is not RetainedForecastRootSelection or (set(records) != set(PRIMARY_TYPES)
            and set(records) != set(PRIMARY_TYPES) - {"assignment-receipt", "assignment-definition"}):
        raise ValueError("retained forecast loses its complete primary record census")
    selected.__post_init__()
    identities = {role: _identity(role, record, selected) for role, record in records.items()}
    parent, event, plan, task, config, assignment = (records[role] for role in
        ("contact", "event", "plan", "task", "config", "assignment"))
    if (parent.execution_plan != identities["plan"] or parent.execution_task != identities["task"]
            or task not in plan.tasks or len(tuple(row for row in plan.tasks if row.task_id == task.task_id)) != 1
            or parent.implementation_commit != plan.implementation_commit
            or parent.task_id != task.task_id or config.operation != "forecast"
            or task.task_id != original.node_id("forecast", config.index)
            or task.capability.config.config_id != config.config_id
            or task.capability.config.config_schema != config.SCHEMA or task.capability.config.content_sha256 != config.fingerprint()
            or event.run_id != parent.run_id or event.task_id != parent.task_id or event.attempt_id != parent.attempt_id
            or event.disposition.value != "BLOCKED" or event.reason_codes != ("unknown-completion",)
            or event.receipt_id is not None or event.receipt_sha256 is not None or event.receipt_relative_path is not None
            or event.output_materialization_ids):
        raise ValueError("retained forecast substitutes its original exact contact/plan/task/config/UNKNOWN event")
    native_config = original.roster_for(config).configurations[config.index]
    if (assignment.native_configuration != c.identity(native_config)
            or assignment.control.selected_roster != ObjectIdentity.from_record(original.roster_for(config).original_selection.roster_id, original.roster_for(config).original_selection)):
        raise ValueError("retained forecast substitutes its original actual child step assignment")
    if "assignment-receipt" in records:
        receipt, definition = records["assignment-receipt"], records["assignment-definition"]
        task_key = sha256((parent.task_id + ":" + definition.subwork_id).encode()).hexdigest()
        expected_native_root = "runs/" + parent.run_id + "/native-subwork/" + task_key
        expected_receipt_path = "runs/" + parent.run_id + "/receipts/native-subwork." + task_key + "/" + parent.run_id + ".native-subwork." + task_key + ".attempt-001.json"
        if (dict(selected.paths)["assignment-definition"] != expected_native_root + "/definition.json"
                or dict(selected.paths)["assignment-receipt"] != expected_receipt_path
                or definition.parent_contact != parent or definition.operation_id != "battery.segmented-native.forecast"
                or definition.configuration != c.identity(native_config)
                or receipt.run_id != parent.run_id or receipt.task_id != "native-subwork." + task_key
                or receipt.operational_status.value != "SUCCEEDED" or receipt.implementation_commit != parent.implementation_commit
                or not set(definition.input_materialization_ids).issubset(receipt.input_materialization_ids)
                or len(receipt.input_materialization_ids) != len(definition.input_materialization_ids) + 3):
            raise ValueError("retained forecast substitutes its actual completed child definition/receipt")
        assignment_outputs = tuple(row for row in receipt.output_logical_artifacts
            if row.payload_schema == assignment.SCHEMA and row.content_sha256 == assignment.fingerprint())
        if len(assignment_outputs) != 1:
            raise ValueError("retained forecast assignment is not an exact original child receipt output")
    witness = identities["event"]
    attempt = InquiryAttempt(parent.attempt_id, identities["config"], InquiryAttemptStatus.UNCERTAIN_CONTACT, witness, (),
        "Original parent contact has no completion receipt; completed child assignment does not complete the parent.")
    binding = InquiryAttemptWorkBinding(parent.attempt_id, identities["config"], None, None,
        parent.execution_plan, parent.execution_task, witness)
    return RetainedForecastWorkCondition("condition." + parent.attempt_id, selected.identity, attempt, binding,
        request_sha256(native_config, assignment.control))


def authenticate_primary(selected):
    """Read original guarded primary custody only; never recover full arrays."""
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.infrastructure.development_native_custody import read_development_native_payload
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling

    selected.__post_init__()
    plane = ExternalArtifactPlane(GuardedExternalRoot(selected.storage))
    plane.root.verify(for_write=False)
    manifests = {}
    closure = {}
    from pathlib import PurePosixPath
    selected_paths = dict(selected.paths)
    native_root = PurePosixPath(selected_paths["assignment-definition"]).parent
    pending = [*selected_paths.values(), str(native_root / "begin.json"), str(native_root / "contact.json")]
    while pending:
        relative = pending.pop()
        if relative in manifests:
            continue
        manifest = decode_artifact_manifest(read_bounded_bytes(plane.root.resolve(relative + ".manifest.json", for_write=False), maximum_bytes=1024*1024))
        if manifest.materialization.relative_path != relative:
            raise ValueError("retained forecast primary changes its selected manifest locator")
        manifests[relative] = manifest
        if manifest.publication is None:
            raise ValueError("retained forecast primary lacks original publication custody")
        for member in manifest.publication.members:
            old = closure.setdefault(member.relative_path, member)
            if old != member:
                raise ValueError("retained forecast primary publication census conflicts")
            pending.append(member.relative_path)
        if sum(member.size_bytes for member in closure.values()) > MAX_PRIMARY_CLOSURE_BYTES:
            raise ValueError("retained forecast primary metadata would read outside its bounded canonical closure; no array recovery")
    records = {}
    with plane.verification_scope() as checked:
        for role, relative in selected.paths:
            manifest = manifests[relative]
            kind = PRIMARY_TYPES[role]
            if manifest.logical.payload_schema != kind.SCHEMA or manifest.materialization.size_bytes > MAX_PRIMARY_CLOSURE_BYTES:
                raise ValueError("retained forecast primary changes its original canonical role")
            raw = read_development_native_payload(checked, manifest, maximum_bytes=MAX_PRIMARY_CLOSURE_BYTES)
            records[role] = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        plan, parent = records["plan"], records["contact"]
        records["task"], = (row for row in plan.tasks if row.task_id == parent.task_id)
        contact_store = ExternalNativeEffectContactStore(plane=checked, execution_plan=parent.execution_plan,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
        if contact_store.read(parent.run_id, parent.task_id) != parent:
            raise ValueError("retained forecast contact differs from original shared custody")
        ordinary_receipt = "runs/" + parent.run_id + "/receipts/" + parent.task_id + "/" + parent.attempt_id + ".json"
        if any(checked.root.resolve(path, for_write=False).exists() for path in (ordinary_receipt, ordinary_receipt + ".manifest.json")):
            raise ValueError("retained forecast completion state changed; reassess actual custody instead of treating it as UNKNOWN")
        assignment, receipt = records["assignment"], records["assignment-receipt"]
        logical, = (row for row in receipt.output_logical_artifacts if row.payload_schema == assignment.SCHEMA and row.content_sha256 == assignment.fingerprint())
        assignment_manifest = manifests[dict(selected.paths)["assignment"]]
        if (assignment_manifest.logical != logical or assignment_manifest.materialization not in receipt.output_materializations
                or assignment_manifest.materialization.relative_path != dict(selected.paths)["assignment"]):
            raise ValueError("retained forecast assignment loses exact native receipt materialization custody")
        from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
        from empirical_lawhood.runtime.native_subwork import NativeSubworkBegin, NativeSubworkContact
        definition = records["assignment-definition"]
        store = ExternalNativeSubworkStore(plane=checked, parent_contacts=contact_store, parent_contact=parent)
        original_definition, definition_manifest = store._control(definition, "definition", NativeSubworkDefinition,
            store._parents(parent.execution_plan))
        begin, begin_manifest = store._control(definition, "begin", NativeSubworkBegin, store._parents(definition.identity))
        if original_definition != definition or begin != NativeSubworkBegin(definition.identity):
            raise ValueError("retained forecast assignment loses its actual original native definition/begin custody")
        begin_identity = ObjectIdentity.from_record(store._id(definition, "begin"), begin)
        native_contact, native_contact_manifest = store._control(definition, "contact", NativeSubworkContact, store._parents(begin_identity))
        if native_contact != NativeSubworkContact(begin_identity):
            raise ValueError("retained forecast assignment loses its actual original native child contact custody")
        complete_inputs = tuple(sorted((*definition.input_materialization_ids,
            definition_manifest.materialization.materialization_id, begin_manifest.materialization.materialization_id,
            native_contact_manifest.materialization.materialization_id)))
        if receipt.input_materialization_ids != complete_inputs:
            raise ValueError("retained forecast child receipt substitutes its full original definition/begin/contact input census")
        condition = derive_condition(selected, records)
    return condition, records
