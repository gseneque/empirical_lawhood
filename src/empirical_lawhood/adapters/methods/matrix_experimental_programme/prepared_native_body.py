# SPDX-License-Identifier: MPL-2.0
"""Original preparation child body after an owning receiver's exact guards.

This private helper changes no source role, context, native identity or access.
The ordinary caller owns its PreparedNativeWork and validates actual authority.
"""

from decimal import Decimal
from dataclasses import dataclass
from hashlib import sha256
import resource
import time

import numpy as np

from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNativeHistory, expected_members
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkState, invoke_native_subwork

from . import preparation_science as science
from .preparation_records import MatrixPreparationHistory


def _retained(source, initial, raw):
    from empirical_lawhood.infrastructure.matrix_array_io import decode_native_matrix_arrays
    arrays = decode_native_matrix_arrays(raw, expected_members(source))
    science.validate_preparation_arrays(source, arrays, initial=initial)
    return arrays




def _execute_preparation_native(context, source, allocation, initial, native_subwork, work, *, progress=None, prepared_initial=None):
    definition, = work.definitions
    output, = tuple(port for port in context.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
    initial_state = science.initial_state(source.initial, initial) if prepared_initial is None else prepared_initial
    completed = native_subwork.recover(definition)
    if completed is not None:
        if (completed.state is not NativeSubworkState.COMPLETED or completed.completion is None
                or completed.receipt is None or completed.completion.operational_status is not OperationalStatus.SUCCEEDED):
            raise ValueError("retained prepared native child is not a known successful completion")
        raw = b"".join(native_subwork.iter_completed_output(definition, "arrays"))
        arrays = _retained(source, initial_state, raw)
        operand = science._preparation_array_operand(source, raw, science.matrix_array_members(arrays),
            artifact_id=output.logical_artifact_id)
    else:
        if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
            raise ValueError("uncertain or failed prepared native contact cannot be repeated")
        native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
        entry = native_subwork.begin(definition)
        native_subwork.contact(entry)
        cpu, wall = time.process_time(), time.monotonic()
        try:
            arrays = invoke_native_subwork(native_subwork, entry, science.acquire_preparation, source, initial,
                **({"on_step": lambda count: progress.advance(Decimal(count))} if progress is not None else {}),
                prepared_initial=initial_state)
        except (ArithmeticError, MemoryError, ValueError):
            native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), None),
                cost_scope="coupling-only paired preparation nested inside complete ordinary task",
                unknown_streams=definition.streams, reason_codes=("matrix-coupling-preparation-native-failure",))
            raise
        raw, operand = science._preparation_array_product(source, initial_state, arrays,
            artifact_id=output.logical_artifact_id)
        native_subwork.publish_output(entry, "arrays", (raw,), maximum_bytes=len(raw), maximum_chunk_bytes=len(raw),
            expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
        consumed = tuple(sorted((source.root.stream_identity(row) for row in source.root.streams
            if row.purpose.startswith("preparation")), key=lambda row: row.object_id))
        completed = native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
            cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), Decimal(len(raw))),
            cost_scope="coupling-only paired preparation nested inside complete ordinary task", consumed_streams=consumed,
            unconsumed_streams=tuple(row for row in definition.streams if row not in consumed),
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    root = source.root.root
    product = MatrixPreparationHistory("history." + source.source_id, source.identity, root.root_id, root.independent_group_id,
        root.clock_id, operand, MatrixParameterNativeHistory(definition, completed.completion, completed.receipt),
        source.total_ticks, 2 * source.total_ticks)
    product.validate_source(source, allocation)
    return product, raw


@dataclass(frozen=True, slots=True)
class _FutureNativeResult:
    """Only this invocation's checked output, with ordinary four-value unpacking."""
    arrays: object
    raw: bytes | None
    native: tuple
    disposition: str
    operand: object

    def __iter__(self):
        return iter((self.arrays, self.raw, self.native, self.disposition))

    def __reduce__(self):
        raise TypeError("prepared native output belongs only to its current invocation")


def _close_future_arrays(result, source, *, artifact_id):
    from .prepared_future_custody import array_product
    if type(result) is _FutureNativeResult and result.operand is not None:
        operand = result.operand
        if (type(result.raw) is not bytes or operand.source != source.identity or operand.array_artifact.artifact_id != artifact_id
                or operand.array_artifact.sha256 != sha256(result.raw).hexdigest()
                or operand.array_artifact.size_bytes != len(result.raw)):
            raise ValueError("prepared native output changes its invocation-bound source or array publication")
        return result.raw, operand
    arrays, raw, _, _ = result
    return array_product(source, arrays, artifact_id=artifact_id, raw=raw)


def _execute_future_native(config, history, causal, mechanical, initial_raw, preparation_raw, frozen_raw, native_subwork, work, *, progress=None, prepared_arrays=None, array_artifact_id=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_bindings import unpack_native
    from .prepared_future_custody import acquire_future, array_product, stream_id, _array_operand
    from empirical_lawhood.infrastructure.matrix_array_io import matrix_array_members

    source = config.source
    native = ()
    operand = None
    if causal.disposition != "AVAILABLE" or mechanical.disposition != "AVAILABLE":
        arrays = {"unentered_branches": np.arange(48, dtype="<i8")}
        raw = None
        disposition = "NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else "INSTRUMENT_UNRESOLVED" if mechanical.disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE"
    else:
        definition, = work.definitions
        completed = native_subwork.recover(definition)
        if completed is not None:
            if (completed.state is not NativeSubworkState.COMPLETED or completed.completion is None or completed.receipt is None
                    or completed.completion.operational_status is not OperationalStatus.SUCCEEDED):
                raise ValueError("prepared future refuses unknown or failed native contact replay")
            raw = b"".join(native_subwork.iter_completed_output(definition, "arrays"))
            arrays = unpack_native(raw, config.protocol, config.panels)
            if array_artifact_id is not None:
                operand = _array_operand(source, raw, matrix_array_members(arrays), artifact_id=array_artifact_id)
        else:
            if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                raise ValueError("prepared future refuses unreceipted native contact replay")
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            entry = native_subwork.begin(definition)
            native_subwork.contact(entry)
            cpu, wall = time.process_time(), time.monotonic()
            try:
                arrays = invoke_native_subwork(native_subwork, entry, acquire_future,
                    config, history, initial_raw, preparation_raw, mechanical, frozen_raw,
                    **({"on_step": lambda count: progress.advance(Decimal(count))} if progress is not None else {}),
                    **({"prepared_arrays": prepared_arrays} if prepared_arrays is not None else {}))
            except (ArithmeticError, MemoryError, ValueError):
                native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                    cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), None),
                    cost_scope="prepared complete paired pulse collection nested in ordinary task", unknown_streams=definition.streams,
                    reason_codes=("prepared-pulse-native-failure",))
                raise
            raw, operand = array_product(source, arrays,
                artifact_id=array_artifact_id or "native.prepared-response-arrays")
            native_subwork.publish_output(entry, "arrays", (raw,), maximum_bytes=len(raw), maximum_chunk_bytes=len(raw),
                expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
            consumed = tuple(sorted((stream_id(config, panel, row) for panel in config.panels for row in panel.streams
                if row.purpose.startswith("autonomous")), key=lambda row: row.object_id))
            completed = native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), Decimal(len(raw))),
                cost_scope="prepared complete paired pulse collection nested in ordinary task", consumed_streams=consumed,
                unconsumed_streams=tuple(row for row in definition.streams if row not in consumed), peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
        native = (MatrixParameterNativeHistory(definition, completed.completion, completed.receipt),)
        disposition = "COMPLETED"
    if array_artifact_id is not None and operand is None:
        raw, operand = array_product(source, arrays, artifact_id=array_artifact_id, raw=raw)
    return _FutureNativeResult(arrays, raw, native, disposition, operand if array_artifact_id is not None else None)
