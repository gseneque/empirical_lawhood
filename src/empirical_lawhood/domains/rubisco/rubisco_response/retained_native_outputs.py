# SPDX-License-Identifier: MPL-2.0
"""Close derived reads against every exact original native completion and output."""

from hashlib import sha256
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class ScopedOriginalNativeReference(CanonicalRecord):
    """A unique reference to an unchanged, locally named original result.

    Native result labels are local to their producing operations. A combined
    named-array manifest requires globally unique reference labels instead.
    This separate record binds the exact original bytes without renaming them.
    """

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/scoped-original-native-reference'
    VERSION: ClassVar[str] = '1.0.0'
    configuration: ObjectIdentity
    original_result: ObjectIdentity
    receipt: ObjectIdentity

    def __post_init__(self):
        if any(type(p) is not ObjectIdentity for p in (self.configuration, self.original_result, self.receipt)):
            raise TypeError('scoped original reference needs exact configuration, result and receipt identities')

    @property
    def identity(self):
        return ObjectIdentity.from_record('reference.original-native.'+self.fingerprint(), self)


def scoped_original_reference(source):
    result = source.original_result
    if result is None:
        raise ValueError('an absent original cannot supply a result reference')
    return ScopedOriginalNativeReference(source.config.identity, ObjectIdentity.from_record(result.result_id, result),
        ObjectIdentity.from_record(result.receipt.receipt_id, result.receipt))


def recheck_original_native_outputs(sources, *, description):
    """Close the analysis lifetime against every original receipted output.

    This uses the existing authenticated stream port. It performs no numerical
    reconstruction, source acquisition or native effect, and keeps no arrays.
    """
    for source in sources:
        original = source.original_result
        if original is None:
            continue
        completed = source.native_subwork.recover(original.definition)
        if completed is None or completed.completion != original.completion or completed.receipt != original.receipt:
            raise ValueError(description+' original completion changed before return')
        omitted = set(original.completion.omitted_output_ids)
        expected = {original.receipt.task_id+'.output.'+o.output_id for o in original.definition.outputs
            if o.output_id not in omitted}
        # Recovery above authenticates completion and any retained partials
        # too. Here select the declared scientific outputs from that receipt.
        rows = tuple(r for r in original.receipt.output_materializations
            if r.logical_artifact_id.startswith(original.receipt.task_id+'.output.'))
        if len(rows) != len(expected) or {r.logical_artifact_id for r in rows} != expected:
            raise ValueError(description+' changes its original complete present/omitted output census')
        for output in original.definition.outputs:
            if output.output_id in omitted:
                # Known failed calls can retain diagnostics without a force
                # array. The original completion owns this exact omission.
                continue
            key = original.receipt.task_id+'.output.'+output.output_id
            rows = [r for r in original.receipt.output_materializations if r.logical_artifact_id == key]
            if len(rows) != 1:
                raise ValueError(description+' loses its complete original output census')
            materialization, digest, count = rows[0], sha256(), 0
            for block in source.native_subwork.iter_completed_output(original.definition, output.output_id,
                    maximum_chunk_bytes=2**20):
                if type(block) is not bytes or len(block) > 2**20:
                    raise ValueError(description+' original stream changes its bounded byte contract')
                count += len(block)
                if count > materialization.size_bytes:
                    raise ValueError(description+' original output exceeds its receipted size')
                digest.update(block)
            if count != materialization.size_bytes or digest.hexdigest() != materialization.physical_sha256:
                raise ValueError(description+' original output changed before return')
