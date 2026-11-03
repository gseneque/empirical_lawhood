# SPDX-License-Identifier: MPL-2.0
"""Freeze complete selected units and recover their original receipts."""

from hashlib import sha256
from dataclasses import dataclass, replace

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster,
    NativeSubworkState, NativeSubworkUncertainContact,
)

from .durable_contracts import (
    DurableNativeCallOperand, DurablePreparationCensus, DurableRawFileCensus, DurableUnitReturn,
    geometry_id, model_id,
)

RAW_SCHEMA = "empirical-lawhood/source/capture-assured-uninterpreted-public-bytes"
JSON_MEDIA = "application/json"


def json_output(name, record):
    return NativeSubworkOutput(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, JSON_MEDIA)


def raw_output(name):
    return NativeSubworkOutput(name, RAW_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES,
                               "application/gzip")


def definitions(plan, parent_contact, *, sources, input_materialization_ids,
                implementation=None, source_root=None):
    """One authentic plan selects every unit before the first native effect."""
    expected = {plan.source, plan.nomination, plan.inventory, plan.coordinates}
    if not expected.issubset(set(sources)):
        raise ValueError("preparation roster lacks full original scientific operand identities")
    ids = (*[geometry_id(*key) for key in plan.geometry_census],
           *[model_id(*key) for key in plan.model_census])
    source_rows = tuple(sorted(sources, key=lambda row: row.object_id))
    code_digest = sha256(canonical_json_bytes(plan.code_sources)).hexdigest()
    if implementation is not None:
        from .durable_runner import validate_current_source_descriptor
        code_digest = validate_current_source_descriptor(plan, implementation, source_root)
    outputs = (json_output("files.census", DurableRawFileCensus), raw_output("files.raw"),
               json_output("unit.return", DurableUnitReturn))
    units = tuple(NativeSubworkDefinition(unit_id, "rubisco.durable-preparation.unit",
        parent_contact, plan.identity, source_rows, code_digest, plan.dependency_lock_sha256,
        tuple(sorted(input_materialization_ids)), (), outputs) for unit_id in sorted(ids))
    metadata = NativeSubworkDefinition("preparation.metadata", "rubisco.durable-preparation.metadata",
        parent_contact, plan.identity, source_rows, code_digest, plan.dependency_lock_sha256,
        tuple(sorted(input_materialization_ids)), (),
        (json_output("files.census", DurableRawFileCensus), raw_output("files.raw"),
         json_output("preparation.census", DurablePreparationCensus),
         json_output("process.selection", IsolatedNativeEntrySelection)))
    return tuple(sorted((*units, metadata), key=lambda row: row.subwork_id))


def freeze(progress, selected):
    if len(selected) != 37:
        raise ValueError("preparation needs full 12 geometry + 24 model + metadata denominator")
    progress.freeze_roster(NativeSubworkRoster("selected.native-subwork", progress.parent_contact,
        tuple(row.identity for row in selected)), definitions=selected)


def census(progress, plan, selected):
    unit_ids = {geometry_id(*key) for key in plan.geometry_census} | {
        model_id(*key) for key in plan.model_census}
    actual = tuple(row for row in selected if row.subwork_id in unit_ids)
    if len(actual) != 36:
        raise ValueError("preparation census cannot drop an unentered selected unit")
    return DurablePreparationCensus(plan.identity, tuple(
        (row.subwork_id, progress.inspect(row).state) for row in actual))


def recover_unit(progress, identity, output_id, *, maximum_chunk_bytes=1024 * 1024):
    """Exact stored definition/receipt/raw output; no native reexecution."""
    definition = progress.resolve_completed_definition(identity)
    if definition.operation_id != "rubisco.durable-preparation.unit":
        raise ValueError("preparation recovery substitutes its original unit owner")
    return progress.iter_completed_output(definition, output_id,
                                         maximum_chunk_bytes=maximum_chunk_bytes)


@dataclass(frozen=True, slots=True)
class DurableCallCustody:
    """Read-only original conditional custody; uncertainty grants no replay."""
    call: ObjectIdentity
    call_state: NativeSubworkState
    call_definition: NativeSubworkDefinition | None
    operand_definition: NativeSubworkDefinition | None
    operand_state: NativeSubworkState | None


def completed_call_custody(progress, unit_definition):
    """Authenticate every actually declared call and its original operand carrier.

    The native call identity comes from the completed original unit return.
    Carrier operands are derived by this owner's unchanged declaration formula,
    then checked against stored exact definition bytes and primary receipts.
    A contacted call without completion remains explicit UNKNOWN, with no output.
    """
    from empirical_lawhood.infrastructure.bounded_io import MAX_CONTROL_PLANE_JSON_BYTES

    actual_unit = progress.resolve_completed_definition(unit_definition.identity)
    if actual_unit != unit_definition or actual_unit.operation_id != "rubisco.durable-preparation.unit":
        raise ValueError("conditional recovery substitutes its original preparation unit")
    chunks = progress.iter_completed_output(actual_unit, "unit.return")
    parts, size = [], 0
    try:
        for chunk in chunks:
            size += len(chunk)
            if size > MAX_CONTROL_PLANE_JSON_BYTES:
                raise ValueError("unit return exceeds existing finite control record envelope")
            parts.append(chunk)
    finally:
        close = getattr(chunks, "close", None)
        if close is not None:
            close()
    returned = decode_canonical_bytes(b"".join(parts), DurableUnitReturn, maximum_bytes=size)
    if returned.unit_id != actual_unit.subwork_id or returned.plan != actual_unit.configuration:
        raise ValueError("conditional recovery changes actual unit return/plan join")
    rows = []
    for identity in returned.native_calls:
        prefix = actual_unit.subwork_id + ".call."
        if not identity.object_id.startswith(prefix) or not identity.object_id[len(prefix):].isdigit():
            raise ValueError("conditional recovery substitutes a foreign call identity")
        try:
            call = progress.resolve_completed_definition(identity)
        except NativeSubworkUncertainContact:
            rows.append(DurableCallCustody(identity, NativeSubworkState.UNKNOWN_COMPLETION, None, None, None))
            continue
        if (call.operation_id != "rubisco.durable-preparation.native-call"
                or call.parent_contact != actual_unit.parent_contact
                or call.configuration.object_schema != DurableNativeCallOperand.SCHEMA):
            raise ValueError("conditional recovery changes original native call owner")
        carrier = replace(actual_unit, subwork_id=identity.object_id + ".operand",
            operation_id="rubisco.durable-preparation.call-operand",
            roster_id=identity.object_id + ".operand-roster",
            outputs=(json_output("call.operand", DurableNativeCallOperand),
                json_output("files.census", DurableRawFileCensus), raw_output("files.raw")))
        observed = progress.inspect(carrier)
        if observed.state is NativeSubworkState.COMPLETED:
            if progress.resolve_completed_definition(carrier.identity) != carrier:
                raise ValueError("conditional recovery changes original operand carrier")
        rows.append(DurableCallCustody(identity, NativeSubworkState.COMPLETED, call, carrier, observed.state))
    return tuple(rows)
