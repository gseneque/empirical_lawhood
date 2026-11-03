# SPDX-License-Identifier: MPL-2.0
"""Exact PURE invocation construction before any actual parent contact."""

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import canonical_json_bytes

from .control_preparation_admission import validate_operands
from . import control_roster


def build_invocation(plan, source, preparation, integrity, geometry, assets, custody,
                     selected, *, source_root, implementation=None):
    validate_operands(plan,source,preparation,integrity,geometry,assets,custody)
    if not selected:
        raise ValueError("chemical/force invocation omits its whole actual definition roster")
    first = selected[0]
    expected = control_roster.definitions(plan,first.parent_contact,sources=first.sources,
        input_materialization_ids=first.input_materialization_ids,implementation=implementation,source_root=source_root)
    if tuple(selected) != expected:
        raise ValueError("chemical/force invocation substitutes actual complete selected definitions")
    def encode(record):
        raw = record.canonical_bytes()
        if decode_canonical_bytes(raw,type(record),maximum_bytes=len(raw)) != record:
            raise ValueError("chemical/force operand omits its complete typed canonical roundtrip")
        return raw.decode()
    from .closed_raw_model_admission import InstanceChemicalForcePlan
    instance_form = type(plan) is InstanceChemicalForcePlan
    # Tuples are the kernel's canonical sequence input; no post-contact list
    # serialization or synthetic substitute for the actual compiled context.
    return canonical_json_bytes(dict(plan=encode(plan),source=encode(source),
        preparation=encode(preparation),integrity="null" if instance_form else encode(integrity),
        geometry="null" if instance_form else encode(geometry),
        assets=tuple(encode(row) for row in assets),
        custody=tuple((name,encode(definition),encode(completion_identity),encode(completion),
            encode(return_identity),encode(returned))
            for name,definition,completion_identity,completion,return_identity,returned in custody),
        definitions=tuple(encode(row) for row in selected),source_root=source_root))
