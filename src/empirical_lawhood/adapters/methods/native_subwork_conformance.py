# SPDX-License-Identifier: MPL-2.0
"""Installed exposed adapter fixture for shared native progress acceptance.

This tiny engine supplies software conformance only. It is deliberately outside
scientific acquisition/qualification registrations and imports no native solver.
Its negative/unevaluable labels cannot qualify battery, Rubisco or matrix claims.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import os
import resource
import time
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, StreamingOutputEmitter, TaskContext, TaskProgressEmitter
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkProgress, NativeSubworkRoster


@dataclass(frozen=True, slots=True)
class ExposedDerivedOperand(CanonicalRecord):
    """Fixture-only operand formed after the actual parent enters."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/adapters/exposed-native-derived-operand"
    config_id: str
    entered_parent_task_id: str
    observed_parent_outcome_sha256: str

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class ExposedNativeSubworkRelayRunner:
    """No native solver: proof of completed nested → ordinary streamed output."""

    definitions: tuple[NativeSubworkDefinition, ...]
    payload: bytes
    ordinary_output_id: str
    fail_after_first_chunk: bool = False

    def execute(self, context: TaskContext) -> RunnerResult:
        raise ValueError("exposed relay requires the actual native-progress/emitter composition")

    def execute_streaming_with_native_subwork(self, context: TaskContext,
            native_subwork: NativeSubworkProgress, emitter: StreamingOutputEmitter,
            progress: TaskProgressEmitter | None = None) -> tuple[ReceiptCheck, ...]:
        definition = self.definitions[0]
        if native_subwork.parent_contact != definition.parent_contact:
            raise ValueError("exposed relay substitutes its actual parent")
        native_subwork.freeze_roster(NativeSubworkRoster("selected.native-subwork",
            definition.parent_contact, tuple(row.identity for row in self.definitions)), definitions=self.definitions)
        entry = native_subwork.begin(definition)
        native_subwork.contact(entry)  # Disclosed software contact; no native engine.
        native_subwork.publish_output(entry, definition.outputs[0].output_id,
            (self.payload,), maximum_bytes=max(1, len(self.payload)),
            maximum_chunk_bytes=max(1, len(self.payload)), expected_size_bytes=len(self.payload),
            expected_physical_sha256=sha256(self.payload).hexdigest())
        native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(None, None, Decimal(len(self.payload))),
            cost_scope="exposed complete bytes; no scientific/native calculation",
            consumed_streams=definition.streams)
        for ordinal, chunk in enumerate(native_subwork.iter_completed_output(
                definition, definition.outputs[0].output_id)):
            emitter.write(self.ordinary_output_id, chunk)
            if self.fail_after_first_chunk and ordinal == 0:
                os._exit(96)
        if progress is not None:
            progress.advance(Decimal(1))
        return (ReceiptCheck("exposed-completed-nested-output-streamed-exactly", True, ()),)


@dataclass(frozen=True, slots=True)
class ExposedNativeSubworkRunner:
    definitions: tuple[NativeSubworkDefinition, ...]
    outcomes: tuple[bytes, ...]
    failure_point: str | None = None
    selected_definitions: tuple[NativeSubworkDefinition, ...] = ()

    def execute(self, context: TaskContext) -> RunnerResult:
        raise ValueError("exposed native adapter requires its live coordinator progress port")

    def execute_with_native_subwork(self, context: TaskContext, native_subwork: NativeSubworkProgress,
                                    progress: TaskProgressEmitter | None = None) -> RunnerResult:
        if len(self.definitions) != len(self.outcomes):
            raise ValueError("exposed adapter changes its full selected subcall denominator")
        if native_subwork.parent_contact != self.definitions[0].parent_contact:
            raise ValueError("exposed adapter substitutes its actual coordinator-observed parent")
        if self.selected_definitions:
            native_subwork.freeze_roster(NativeSubworkRoster("selected.native-subwork", native_subwork.parent_contact,
                tuple(row.identity for row in self.selected_definitions)), definitions=self.selected_definitions)
        for ordinal, (definition, outcome) in enumerate(zip(self.definitions, self.outcomes, strict=True)):
            native_output = next(row for row in definition.outputs if row.output_id == "result.output.native")
            if (definition.parent_contact.run_id, definition.parent_contact.task_id,
                    definition.parent_contact.attempt_id) != (context.run_id, context.task_id, context.attempt_id):
                raise ValueError("exposed adapter substitutes its actual task identity")
            completed = native_subwork.recover(definition)
            if completed is not None:
                if progress is not None:
                    progress.advance(Decimal(ordinal + 1))
                continue
            entry = native_subwork.begin(definition)
            if self.failure_point == "before-contact":
                os._exit(91)  # exposed process-loss boundary, not a scientific OOM claim
            native_subwork.contact(entry)
            if self.failure_point == "after-contact" or (self.failure_point == "after-first" and ordinal == 1):
                os._exit(92)
            cpu_start, wall_start = time.process_time(), time.monotonic()
            if self.failure_point == "after-conditional" and ordinal == 0:
                conditional = replace(definition, subwork_id=definition.subwork_id + ".segment.one",
                    operation_id="exposed.conditional-segment", roster_id="conditional.segment.one")
                native_subwork.freeze_roster(NativeSubworkRoster(conditional.roster_id,
                    definition.parent_contact, (conditional.identity,), definition.identity), entry,
                    definitions=(conditional,))
                segment = native_subwork.begin(conditional)
                native_subwork.contact(segment)
                native_subwork.publish_output(segment, native_output.output_id, (b"FALSIFIED",),
                    maximum_bytes=9, maximum_chunk_bytes=9,
                    expected_size_bytes=9, expected_physical_sha256=sha256(b"FALSIFIED").hexdigest())
                native_subwork.complete(segment, operational_status=OperationalStatus.SUCCEEDED,
                    cost=InquiryCost(None, None, Decimal(9)), cost_scope="conditional segment; contained in parent forecast",
                    consumed_streams=conditional.streams)
                os._exit(94)
            try:
                if self.failure_point == "memory-error":
                    raise MemoryError("exposed native memory failure")
                def chunks():
                    if self.failure_point == "before-first-output-chunk":
                        os._exit(95)
                    if self.failure_point == "memory-error-before-first-output-chunk":
                        raise MemoryError("exposed memory failure before emitting output")
                    yield outcome[:2]
                    if self.failure_point == "during-output":
                        os._exit(93)
                    if self.failure_point == "memory-error-during-output":
                        raise MemoryError("exposed memory failure while emitting output")
                    yield outcome[2:]
                native_subwork.publish_output(entry, native_output.output_id, chunks(),
                    maximum_bytes=max(1, len(outcome)), maximum_chunk_bytes=max(1, len(outcome)),
                    expected_size_bytes=len(outcome), expected_physical_sha256=sha256(outcome).hexdigest())
            except MemoryError:
                native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                    cost=InquiryCost(Decimal(str(time.process_time() - cpu_start)),
                        Decimal(str(time.monotonic() - wall_start)), None),
                    cost_scope="worker CPU and wall including custody; contained in parent task; retained bytes unknown",
                    unknown_streams=definition.streams, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                    reason_codes=("exposed-native-memory-error",))
            else:
                written_bytes = len(outcome)
                if self.failure_point in ("derived-conditional", "derived-grandchild") and ordinal == 0:
                    derived = ExposedDerivedOperand("exposed.derived-configuration", context.task_id,
                        sha256(outcome).hexdigest())
                    manifest = native_subwork.publish_output(entry, "derived.configuration", (derived.canonical_bytes(),),
                        maximum_bytes=len(derived.canonical_bytes()),
                        maximum_chunk_bytes=len(derived.canonical_bytes()),
                        expected_size_bytes=len(derived.canonical_bytes()),
                        expected_physical_sha256=derived.fingerprint())
                    child = replace(definition, subwork_id=definition.subwork_id + ".derived-segment",
                        configuration=derived.identity, roster_id="conditional.derived-segment",
                        input_materialization_ids=tuple(sorted((*definition.input_materialization_ids,
                            manifest.materialization.materialization_id))), outputs=(native_output,))
                    written_bytes += manifest.materialization.size_bytes
                    native_subwork.freeze_roster(NativeSubworkRoster(child.roster_id,
                        definition.parent_contact, (child.identity,), definition.identity), entry, definitions=(child,))
                    segment = native_subwork.begin(child)
                    native_subwork.contact(segment)
                    if self.failure_point == "derived-grandchild":
                        grandchild = replace(child, subwork_id=child.subwork_id + ".call-operand",
                            operation_id="exposed.inherited-operands", roster_id="conditional.derived-call-operand")
                        native_subwork.freeze_roster(NativeSubworkRoster(grandchild.roster_id,
                            definition.parent_contact, (grandchild.identity,), child.identity), segment,
                            definitions=(grandchild,))
                        operand = native_subwork.begin(grandchild)
                        native_subwork.contact(operand)
                        native_subwork.publish_output(operand, native_output.output_id, (b"FALSIFIED",),
                            maximum_bytes=9, maximum_chunk_bytes=9, expected_size_bytes=9,
                            expected_physical_sha256=sha256(b"FALSIFIED").hexdigest())
                        native_subwork.complete(operand, operational_status=OperationalStatus.SUCCEEDED,
                            cost=InquiryCost(None, None, Decimal(9)), cost_scope="exposed inherited operands; no native science",
                            consumed_streams=grandchild.streams)
                    native_subwork.publish_output(segment, child.outputs[0].output_id, (b"UNEVALUABLE",),
                        maximum_bytes=11, maximum_chunk_bytes=11, expected_size_bytes=11,
                        expected_physical_sha256=sha256(b"UNEVALUABLE").hexdigest())
                    native_subwork.complete(segment, operational_status=OperationalStatus.SUCCEEDED,
                        cost=InquiryCost(None, None, Decimal(11)), cost_scope="conditional segment; contained in parent",
                        consumed_streams=child.streams)
                native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                    cost=InquiryCost(Decimal(str(time.process_time() - cpu_start)),
                        Decimal(str(time.monotonic() - wall_start)), Decimal(written_bytes)),
                    cost_scope="worker CPU and wall including custody; scientific output bytes; contained in parent task",
                    consumed_streams=definition.streams, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
            if progress is not None:
                progress.advance(Decimal(ordinal + 1))
        return RunnerResult((), (ReceiptCheck("exposed-native-subwork-observed-returns-retained", True, ()),))
