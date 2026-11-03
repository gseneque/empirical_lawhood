# SPDX-License-Identifier: MPL-2.0
"""Local, explicitly selected battery lossless native and consumer composition.

Existing compiler/scheduler/contact/custody owners are unchanged. The local
registration declares the new ordinary stream schema; native child definitions
declare new physical raw/full schemas. No new public registration is created.
"""

from contextlib import contextmanager
from dataclasses import dataclass

from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as old
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import operation_bindings as bindings
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import runner as original_runner
from . import forecast_step_control as step
from . import lossless_evidence_stream as stream
from . import lossless_segment_consumer as consumer
from . import lossless_segment_native as storage
from . import lossless_segment_records as records
from . import segmented_native as native
from . import preparation_contracts as pc


@contextmanager
def contract_scope():
    """Declare the actual successor schema to the selected local composition."""
    previous = bindings.FORECAST_OUTPUTS
    if tuple(name for name, _ in previous) != ("evidence", "segments"):
        raise ValueError("lossless local contract substitutes complete forecast output roles")
    bindings.FORECAST_OUTPUTS = (("evidence", previous[0][1]), ("segments", stream.LosslessEvidenceLine))
    try:
        yield
    finally:
        bindings.FORECAST_OUTPUTS = previous


@dataclass(frozen=True)
class _RelayFrame:
    metadata: stream.LosslessSegmentMetadata
    raw_lines: object

    @property
    def segment_index(self):
        return self.metadata.segment_index


def relay_segments(progress, definition, inspection, trace, protocol):
    """Read original new-format completed products; no native replay or effects."""
    preparation = native.completed_preparation_checkpoint(progress, definition)
    previous = inspection if preparation is None else preparation
    context = () if preparation is None else tuple(row.materialization.materialization_id for row in preparation.outputs)
    for summary in trace.segments:
        name = "native.request.first" if summary.segment_index == 1 else "native.request.next"
        request = old.completed_record(progress, previous.definition, previous, name, native.SegmentRequest)
        if request.identity != summary.request:
            raise ValueError("lossless native relay changes exact original request")
        request_manifest = old._manifest(previous, name)
        additional = [request_manifest.materialization.materialization_id]
        if summary.segment_index != 1:
            terminal = old._manifest(previous, "actual-terminal")
            if terminal is None:
                raise ValueError("lossless successor lost complete prior terminal custody")
            additional.append(terminal.materialization.materialization_id)
        child = progress.resolve_completed_definition(summary.native_definition)
        if (child.identity != summary.native_definition or child.parent_contact != definition.parent_contact
                or child.subwork_id != definition.subwork_id + ".segment." + str(summary.segment_index)
                or child.operation_id != "battery.segmented-native.segment" or child.configuration != request.identity
                or child.input_materialization_ids != tuple(sorted(set((*definition.input_materialization_ids, *context, *additional))))
                or child.outputs != storage.segment_outputs() or child.sources != definition.sources or child.streams != definition.streams
                or child.code_sources_sha256 != definition.code_sources_sha256 or child.dependency_lock_sha256 != definition.dependency_lock_sha256
                or child.roster_id != "conditional.battery.segment." + str(summary.segment_index)):
            raise ValueError("lossless native relay changes actual frozen child/source/input/output census")
        current = progress.recover(child)
        if current is None or current.receipt is None or records.identity(current.receipt, "receipt_id") != summary.native_receipt:
            raise ValueError("lossless native relay lacks exact actual completed receipt")
        selected = {"returned": old.completed_record(progress, child, current, "native.return", native.SegmentReturn),
            "next_request": old.completed_record(progress, child, current, "native.request.next", native.SegmentRequest),
            "full_index": old.completed_record(progress, child, current, "full-state", records.FullSegmentIndex, optional=True)}
        for key in ("requested_initial", "actual_initial", "initial_derivative", "actual_terminal", "terminal_derivative"):
            selected[key] = old.completed_record(progress, child, current, key.replace("_", "-"), pc.StateObservation, optional=True)
        manifest = old._manifest(current, "raw-return")
        raw_index = raw_sha = raw_size = None
        def raw_lines(d=child):
            return stream.bounded_lines(progress.iter_completed_output(d, "raw-return", maximum_chunk_bytes=records.codec.CHUNK_BYTES))
        if manifest is not None:
            if manifest.logical.payload_schema != records.RawSegmentStreamLine.SCHEMA:
                raise ValueError("lossless native relay substitutes actual raw physical schema")
            initial = iter(raw_lines())
            try:
                raw_index = records._read_line(next(initial), 0).index
            finally:
                initial.close()
            if raw_index is None or raw_index.decoded_subject != summary.raw_return:
                raise ValueError("lossless raw physical header changes original scientific subject")
            raw_sha, raw_size = manifest.logical.content_sha256, manifest.materialization.size_bytes
        if (selected["full_index"] is None) != (summary.full_state is None) or selected["full_index"] is not None and selected["full_index"].decoded_subject != summary.full_state:
            raise ValueError("lossless full physical output changes original scientific subject")
        metadata = stream.LosslessSegmentMetadata(summary.segment_index, child, previous.receipt, current.receipt,
            request, raw_index=raw_index, raw_physical_sha256=raw_sha, raw_size_bytes=raw_size, **selected)
        yield _RelayFrame(metadata, raw_lines if manifest is not None else lambda: iter(()))
        previous = current


@contextmanager
def relay_scope():
    previous_relay, previous_emit = old.relay_segments, old.emit_frame
    def emit(emitter, output_id, record, frame_index, sequence):
        if type(record) is old.SegmentStreamHeader:
            if frame_index != 0 or sequence != 0:
                raise ValueError("lossless relay changes original header order")
            return stream.emit_header(emitter, output_id, record)
        if type(record) is not _RelayFrame or frame_index != record.segment_index:
            raise ValueError("lossless relay substitutes declared original frame type/order")
        return stream.emit_frame(emitter, output_id, record.metadata, record.raw_lines(), sequence)
    old.relay_segments, old.emit_frame = relay_segments, emit
    try:
        yield
    finally:
        old.relay_segments, old.emit_frame = previous_relay, previous_emit


class LosslessControlledRunner(step.ControlledSegmentedRunner):
    """Actual used domain runner; complete original native loop and live custody."""
    def forecast_operands(self, context):
        with contract_scope():
            return super().forecast_operands(context)

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        with contract_scope(), storage.native_storage_scope(), relay_scope():
            return super().execute_streaming_with_native_subwork(context, native_subwork, emitter, progress)


@contextmanager
def assessment_scope(*, temporary_file):
    """Expose exact new physical input schema and independent segment assessor."""
    previous = original_runner._assess
    def assess(config, evidence, port):
        return consumer.assess_trace(config, evidence, port, temporary_file=temporary_file)
    with contract_scope():
        original_runner._assess = assess
        try:
            yield
        finally:
            original_runner._assess = previous
