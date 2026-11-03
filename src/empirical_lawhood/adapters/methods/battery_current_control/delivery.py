# SPDX-License-Identifier: MPL-2.0
"""Pure projection of actual current channels, with no simulator dispatch."""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_thermal_service.contracts import BatteryThermalConfig, BatteryThermalTrace
from empirical_lawhood.kernel.action_contracts import ActionDeliveryStage, OccurrenceActionWord, ObservedActionOccurrence
from empirical_lawhood.kernel.control import OperationalDeliveryState, ScientificCommitmentKind
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.controller_study import ImplementationBinding, ImplementationRole
from empirical_lawhood.runtime.controller_runtime import DeliveryPortResult
from .contracts import BatteryCurrentDeliveryEvidence, BatteryCurrentRecipe, current_recipe, PROTOCOL_SHA256
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.artifacts import ArtifactManifest, CanonicalTaskReceipt
from .words import coordinate, current_word


@dataclass(frozen=True, slots=True)
class BatteryCurrentSourceClock(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-current-control/source-clock"
    config: ObjectIdentity
    times_s: tuple[Decimal, ...]
    clock_id: str
    coordinate_frame: str
    origin: str


def from_authenticated_product(*, evidence_id: str, source_bytes: bytes, producing_receipt: CanonicalTaskReceipt, artifact: ArtifactManifest, word: OccurrenceActionWord, exposure: str) -> BatteryCurrentDeliveryEvidence:
    """Join API-authenticated custody members; no file I/O or authority issuance.

    The caller obtains receipt and manifest from the guarded custody reader.
    This boundary additionally checks complete bytes and both receipt members.
    """
    if exposure != "EXPOSED_RECORDED_INPUT_CONFORMANCE":
        raise ValueError("native exposure requires the authenticated wave acquisition join")
    source = decode_canonical_bytes(source_bytes, BatteryThermalTrace, maximum_bytes=4 * 1024**2)
    if source.canonical_bytes() != source_bytes:
        raise ValueError("battery source product bytes are not exact canonical bytes")
    observed, clock = project_current_stages(source, word, observation_id=f"{evidence_id}.observed")
    return BatteryCurrentDeliveryEvidence(evidence_id, exposure, source, producing_receipt, artifact, word, observed, clock)


def from_authenticated_wave(*, evidence_id, draft, plan, products, task_id, config_manifest, packet, implementation, word) -> BatteryCurrentDeliveryEvidence:
    """Bind the guarded reader's actual acquire task and authored source packet.

    Inputs come from read_recursive_wave(include_products=True) and its guarded
    authored-wave loader. This is a pure additional domain check, never custody
    authentication or scientific qualification authority on its own.
    """
    from empirical_lawhood.adapters.methods.battery_thermal_service.executable_binding import operation_registrations
    from empirical_lawhood.runtime.plans import ScientificStage
    if packet.draft != ObjectIdentity.from_record(draft.draft_id, draft):
        raise ValueError("battery native packet differs from its authenticated draft")
    records = products["records"].get(task_id, {})
    sources = tuple(record for record in records.values() if type(record) is BatteryThermalTrace)
    if len(sources) != 1:
        raise ValueError("battery native delivery needs one exact acquired source product")
    source = sources[0]
    operations = tuple(operation for operation in draft.operations if operation.config_identity == ObjectIdentity.from_record(source.config.config_id, source.config))
    if len(operations) != 1:
        raise ValueError("battery acquired source lacks its unique authored acquisition")
    operation = operations[0]
    if operation.node_id not in draft.selected_operation_ids:
        raise ValueError("battery source belongs to an unselected acquisition")
    task = next((task for task in plan.tasks if task.task_id == task_id), None)
    owner = next(r.selection for r in operation_registrations() if r.selection.capability_key == "battery-thermal-service.acquire")
    if task is None or task.stage is not ScientificStage.ACQUIRE or operation.selection != owner or task.capability.capability_key != owner.capability_key or task.capability_implementation_sha256 != owner.implementation_sha256:
        raise ValueError("battery native source belongs to another provider task")
    config_inputs = tuple(value for value in task.external_inputs if value.input_id == "config")
    if len(config_inputs) != 1 or config_inputs[0].logical_artifact_id != config_manifest.logical.logical_artifact_id or config_inputs[0].expected_content_sha256 != source.config.fingerprint():
        raise ValueError("battery native task changes its exact acquired configuration")
    receipt = products["receipts"][task_id]
    matches = tuple(logical for logical in receipt.output_logical_artifacts if logical.content_sha256 == source.fingerprint() and logical.payload_schema == source.SCHEMA)
    if len(matches) != 1 or receipt.task_id != task_id:
        raise ValueError("battery native source lacks its exact producing output and task")
    manifest = products["outputs"][matches[0].logical_artifact_id]
    observed, clock = project_current_stages(source, word, observation_id=f"{evidence_id}.observed")
    return BatteryCurrentDeliveryEvidence(evidence_id, "RECEIPT_BACKED_NATIVE_OBSERVATION", source, receipt, manifest, word, observed, clock, config_manifest, operation, packet, implementation)


def validate_current_word(word: OccurrenceActionWord, config: BatteryThermalConfig) -> None:
    if config.protocol_sha256 != PROTOCOL_SHA256 or len(word.occurrences) != 1:
        raise ValueError("battery current delivery changes its selected protocol or occurrence census")
    occurrence = word.occurrences[0]
    channel = occurrence.channel
    if channel.native_unit != "A" or channel.native_action_frame != "pybamm-terminal-current" or channel.native_direction != "positive-discharge-negative-charge":
        raise ValueError("battery current delivery substitutes its native unit/frame/direction")
    if occurrence.duration != Decimal(900) or occurrence.duration_unit != "s":
        raise ValueError("battery current delivery changes the selected service interval")
    for stage in ActionDeliveryStage:
        event = getattr(occurrence, stage.value.lower())
        if event.value != config.current_a or event.coordinate.coordinate != 0 or event.coordinate.clock_id != "battery-service-clock" or event.coordinate.coordinate_frame != "battery-service-time" or event.coordinate.time_unit != "s":
            raise ValueError("battery current word changes native current, stage clock or preparation")
    if word.denominator_id != config.source.denominator_id or word.retained_history_id != config.unit_id or word.receiver_id != "battery-native-current" or word.horizon_id != "battery-service-900s":
        raise ValueError("battery current word changes exact source or preparation binding")
    if word != current_word(config, occurrence.requested_to_accepted.evaluator):
        raise ValueError("battery current word changes its complete selected view, timing or grammar")


def project_current_stages(source: BatteryThermalTrace, word: OccurrenceActionWord, *, observation_id: str) -> tuple[ObservedActionOccurrence, ObjectIdentity]:
    """Keep missing stages missing; compare the entire sampled current timeline."""
    validate_current_word(word, source.config)
    occurrence = word.occurrences[0]
    reasons = set(source.reason_codes)
    if source.disposition != "COMPLETE":
        reasons.add("BATTERY_NATIVE_INTERVAL_INCOMPLETE")
    if source.times_s != tuple(Decimal(t) for t in range(0, 901, 10)) and source.config.view == "primary":
        reasons.add("BATTERY_CURRENT_SOURCE_CLOCK_DRIFT")
    if source.config.view == "tighter" and source.times_s != tuple(Decimal(t) for t in range(901)):
        reasons.add("BATTERY_CURRENT_SOURCE_CLOCK_DRIFT")
    # Values are taken from four separate acquisition channels. Capacity never
    # enters this proof, and no stage is filled from another stage's value.
    requested = replace(occurrence.requested, value=source.requested_current_a, coordinate=coordinate(source.requested_model_clock_s))
    accepted = None if source.accepted_current_a is None or source.accepted_model_clock_s is None else replace(occurrence.accepted, value=source.accepted_current_a, coordinate=coordinate(source.accepted_model_clock_s))
    applied = None if source.applied_current_a is None or source.applied_model_clock_s is None else replace(occurrence.applied, value=source.applied_current_a, coordinate=coordinate(source.applied_model_clock_s))
    realized = None
    if source.current_a:
        realized = replace(occurrence.realized, value=source.current_a[0], coordinate=coordinate(source.times_s[0]))
        if any(value != occurrence.realized.value for value in source.current_a):
            reasons.add("BATTERY_REALIZED_CURRENT_TRACE_MISMATCH")
    else:
        reasons.add("BATTERY_REALIZED_CURRENT_ABSENT")
    if accepted is None:
        reasons.add("BATTERY_ACCEPTED_CURRENT_ABSENT")
    if applied is None:
        reasons.add("BATTERY_APPLIED_CURRENT_ABSENT")
    observed = ObservedActionOccurrence(observation_id, occurrence.occurrence_id, requested, accepted, applied, realized, tuple(sorted(reasons)))
    clock_coordinate = occurrence.realized.coordinate
    clock = BatteryCurrentSourceClock(ObjectIdentity.from_record(source.config.config_id, source.config), source.times_s, clock_coordinate.clock_id, clock_coordinate.coordinate_frame, clock_coordinate.origin.value)
    return observed, ObjectIdentity.from_record(f"{observation_id}.source-clock", clock)


@dataclass(slots=True)
class BatteryCurrentReceiptDelivery:
    """A source receipt adapter. Recovery reuses the same immutable evidence."""
    implementation_binding: ImplementationBinding
    recipe: BatteryCurrentRecipe
    evidence: BatteryCurrentDeliveryEvidence | None = None
    delivery_calls: int = 0

    def __post_init__(self):
        if self.implementation_binding.role is not ImplementationRole.DELIVERY:
            raise ValueError("battery delivery port needs the installed delivery owner")
        if self.evidence is not None and current_recipe(self.evidence.source.config) != self.recipe:
            raise ValueError("battery delivery source changes its immutable recipe")

    def deliver(self, *, action_word: OccurrenceActionWord, commitment_kind: ScientificCommitmentKind) -> DeliveryPortResult:
        self.delivery_calls += 1
        if self.evidence is None:
            return DeliveryPortResult("battery-current-delivery.no-source", (), OperationalDeliveryState.DELIVERY_RECOVERY)
        evidence = self.evidence
        expected_kind = ScientificCommitmentKind.MEASURED_HOLD if evidence.source.config.word == "native-hold900" else ScientificCommitmentKind.ACTION
        if current_recipe(evidence.source.config) != self.recipe or action_word != evidence.word or commitment_kind is not expected_kind:
            return DeliveryPortResult(f"{evidence.evidence_id}.wrong-word", (), OperationalDeliveryState.DELIVERY_RECOVERY)
        observed = evidence.observed
        occurrence = action_word.occurrences[0]
        correct = observed.complete and not observed.reason_codes and all(getattr(observed, stage.value.lower()) == getattr(occurrence, stage.value.lower()) for stage in ActionDeliveryStage)
        return DeliveryPortResult(f"{evidence.evidence_id}.delivery", (observed,), None if correct else OperationalDeliveryState.DELIVERY_RECOVERY)
