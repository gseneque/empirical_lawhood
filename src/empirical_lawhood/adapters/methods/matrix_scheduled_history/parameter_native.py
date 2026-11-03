# SPDX-License-Identifier: MPL-2.0
"""One domain owner for original parameter-segment acquisition and recovery.

Owning adapters validate scientific operands and derive PreparedNativeWork.
The existing native progress service retains entry, receipts, unknown contacts
and recovery. This function creates no scheduler, store or authority.
"""

from decimal import Decimal
from dataclasses import dataclass, replace
from hashlib import sha256
from types import MappingProxyType
import resource
import time

from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, invoke_native_subwork

from . import science
from .records import ScheduledArrays, ScheduledCheckpoint, identity
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling


@dataclass(frozen=True, slots=True)
class ParameterNativeReturn:
    """One local native return; retain historical five-value unpacking."""
    raw: bytes
    arrays: object
    checkpoint: object
    definition: object
    completed: object
    array_product: object

    def __iter__(self):
        return iter((self.raw, self.arrays, self.checkpoint, self.definition, self.completed))

    def rebind_prefix(self, source, *, record_type, artifact_id, artifact_role, access, visibility):
        """Rebind selected presentation after exact local native/checkpoint checks."""
        operand = self.array_product
        if type(operand) is not ScheduledArrays or type(self.raw) is not bytes:
            raise ValueError('scheduled prefix return lacks its exact local array operand')
        science.validate_prefix_operand(source, operand)
        science.validate_prefix_arrays(source, self.arrays)
        if ((len(self.raw), sha256(self.raw).hexdigest()) !=
                (operand.array_artifact.size_bytes, operand.array_artifact.sha256)
                or science.matrix_array_members(self.arrays) != operand.members):
            raise ValueError('scheduled prefix return changes exact local archive or members')
        self.checkpoint.validate_source(source, operand)
        artifact = replace(operand.array_artifact, artifact_id=artifact_id, role=artifact_role)
        return record_type('arrays.'+artifact_id, operand.source, operand.role, artifact,
            operand.members, operand.producers, access, visibility)


def _recovered_prefix_operand(source, raw, arrays, checkpoint):
    """Metadata over the receipt-authenticated, independently decoded archive."""
    artifact = checkpoint.prefix_arrays
    if (len(raw), sha256(raw).hexdigest()) != (artifact.size_bytes, artifact.sha256):
        raise ValueError('scheduled recovered prefix changes exact checkpoint archive')
    product = ScheduledArrays('arrays.'+artifact.artifact_id, identity(source), 'PREFIX', artifact,
        science.matrix_array_members(arrays), tuple(sorted((identity(source), coordinate_identity(source.coordinate)),
            key=lambda value: value.object_id)), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    science.validate_prefix_operand(source, product)
    checkpoint.validate_source(source, product)
    return product


def execute_parameter_native_work(source, work, native_subwork, *, prefix_only, start, stop,
        history=None, prefix_raw=None, terminal=None, progress=None, prefix_values=None, artifact_id=None):
    """Run the unchanged complete segment controller over already joined inputs."""
    parent = work.expected_parent
    checkpoint = None
    product = None
    definition, = work.definitions
    subwork = definition.subwork_id
    completed = native_subwork.recover(definition)
    if completed is not None:
        if completed.state is not NativeSubworkState.COMPLETED or completed.receipt is None or completed.completion.operational_status is not OperationalStatus.SUCCEEDED:
            raise ValueError('scheduled native phase refuses failed/unknown contact replay')
        raw = b''.join(native_subwork.iter_completed_output(definition, 'arrays'))
        arrays = science.unpack_native(source, raw, prefix_only=prefix_only)
        if prefix_only:
            checkpoint = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'checkpoint')), ScheduledCheckpoint, maximum_bytes=None)
            product = _recovered_prefix_operand(source, raw, arrays, checkpoint)
        elif artifact_id is not None:
            # The original receipt service authenticated raw and unpack_native
            # independently checked its complete scientific layouts and values.
            # Reuse that exact return without another archive expansion.
            product = science._full_array_operand(source, history, raw,
                science.matrix_array_members(arrays), artifact_id=artifact_id)
    else:
        if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
            raise ValueError('scheduled unreceipted/unknown native contact cannot be repeated')
        if prefix_only:
            segments.validate_segment_entry(source.coordinate, source.root.streams, start, stop)
        native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
        entry = native_subwork.begin(definition)
        native_subwork.contact(entry)
        cpu, wall = time.process_time(), time.monotonic()
        try:
            def completed_integrations(count):
                progress.advance(Decimal(count))
            segment = invoke_native_subwork(native_subwork, entry, segments.acquire_parameter_segment,
                source.coordinate, source.root.streams, start, stop,
                **({} if progress is None else {'progress': completed_integrations}),
                **({} if prefix_only else {'terminal': terminal, 'generator_states': history.checkpoint.generators}))
        except (ArithmeticError, MemoryError, ValueError):
            native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)), None),
                cost_scope='scheduled original native phase nested in ordinary task', unknown_streams=definition.streams,
                reason_codes=('scheduled-native-failure',))
            raise
        native_task = 'native-subwork.'+sha256((parent.task_id+':'+subwork).encode()).hexdigest()
        if prefix_only:
            raw, product, checkpoint, arrays = science.prefix_from_segment(source, segment,
                artifact_id=native_task+'.output.arrays', return_values=True)
        else:
            raw, product, arrays = science.full_from_continuation(source, history, prefix_raw, segment,
                artifact_id=native_task+'.output.arrays' if artifact_id is None else artifact_id,
                prefix_values=prefix_values, return_values=True)
        native_subwork.publish_output(entry, 'arrays', (raw,), maximum_bytes=len(raw), maximum_chunk_bytes=len(raw),
            expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
        if prefix_only:
            value = checkpoint.canonical_bytes()
            native_subwork.publish_output(entry, 'checkpoint', (value,), maximum_bytes=len(value), maximum_chunk_bytes=len(value),
                expected_size_bytes=len(value), expected_physical_sha256=sha256(value).hexdigest())
        consumed = tuple(sorted((source.root.stream_identity(s) for s in source.root.streams if
            s.purpose.startswith('preparation') and start < source.coordinate.ramp_ticks
            or s.purpose.startswith('autonomous') and stop > max(start, source.coordinate.ramp_ticks)), key=lambda o: o.object_id))
        completed = native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)), Decimal(len(raw))),
            cost_scope='scheduled original native phase nested in ordinary task', consumed_streams=consumed,
            unconsumed_streams=tuple(s for s in definition.streams if s not in consumed),
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    # Native consumers previously received raw-backed read-only decoded arrays.
    # Preserve that no-mutation contract for the directly assembled return too.
    for value in arrays.values():
        value.setflags(write=False)
    return ParameterNativeReturn(raw, MappingProxyType(dict(arrays)), checkpoint, definition, completed, product)
