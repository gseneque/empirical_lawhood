# SPDX-License-Identifier: MPL-2.0
"""Receipt-only original isolated process custody and its exact input join."""

from dataclasses import replace

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntryReturn, IsolatedNativeEntrySelection, IsolatedNativeProcessStart
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from .durable_contracts import DurableRawFileCensus
from .durable_roster import json_output, raw_output


def launcher_definition(metadata, selection, outputs):
    manifests = dict(outputs)
    if set(manifests) - {"files.census", "files.raw", "process.selection", "preparation.census"}:
        raise ValueError("launcher recovery changes original metadata output census")
    inputs = tuple(manifests[name].materialization.materialization_id
        for name in ("process.selection", "files.census", "files.raw"))
    return replace(metadata, subwork_id="preparation.launch", operation_id="rubisco.durable-preparation.launch",
        configuration=selection.identity, roster_id="conditional.rubisco-preparation.launch",
        input_materialization_ids=tuple(sorted((*metadata.input_materialization_ids, *inputs))),
        outputs=(json_output("files.census", DurableRawFileCensus), raw_output("files.raw"),
            json_output("process.return", IsolatedNativeEntryReturn), json_output("process.start", IsolatedNativeProcessStart)))


def completed_launcher(progress, metadata):
    actual = progress.inspect(metadata)
    if actual.state is not NativeSubworkState.COMPLETED:
        return None, NativeSubworkState.NOT_ENTERED if actual.state is NativeSubworkState.NOT_ENTERED else None
    from empirical_lawhood.infrastructure.bounded_io import MAX_CONTROL_PLANE_JSON_BYTES
    raw = bytearray()
    for block in progress.iter_completed_output(metadata, "process.selection"):
        raw.extend(block)
        if len(raw) > MAX_CONTROL_PLANE_JSON_BYTES:
            raise ValueError("launcher selection exceeds original finite control envelope")
    selection = decode_canonical_bytes(bytes(raw), IsolatedNativeEntrySelection, maximum_bytes=len(raw))
    outputs = tuple((name, next(row for row in actual.outputs
        if row.logical.logical_artifact_id.endswith(".output." + name)))
        for name in actual.completion.output_ids)
    launcher = launcher_definition(metadata, selection, outputs)
    observed = progress.inspect(launcher)
    if observed.state is NativeSubworkState.COMPLETED and progress.resolve_completed_definition(launcher.identity) != launcher:
        raise ValueError("launcher recovery substitutes original retained process definition")
    return launcher, observed.state
