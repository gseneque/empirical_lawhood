# SPDX-License-Identifier: MPL-2.0
"""Pure current prepared-config ancestry; no I/O or admission verdict."""
from bisect import bisect_left
from empirical_lawhood.kernel.provenance import ObjectIdentity
from .selected_produced_inputs import validate_produced_input_parents


def prepared_config_parents(config,records,*,owner,root_types,root_phase):
    owner.phase_of(config)
    prefix=owner.NAMESPACE+"."+root_phase+"."
    index=bisect_left(records,prefix,key=lambda row:row[0])
    if index==len(records) or not records[index][0].startswith(prefix):
        raise ValueError("prepared configuration omits its actual committed entry/design")
    node,root=records[index]
    if (type(root) not in root_types or root.phase!=root_phase
            or index+1<len(records) and records[index+1][0].startswith(prefix)
            or owner.task_id(root)!=node):
        raise ValueError("prepared configuration changes its single actual committed entry/design")
    actual=bisect_left(records,owner.task_id(config),key=lambda row:row[0])
    if actual==len(records) or records[actual]!=(owner.task_id(config),config):
        raise ValueError("prepared configuration is foreign to the actual complete decoded census")
    programme=getattr(config,"programme",None)
    if type(programme) is ObjectIdentity:
        # The current root constructor/whole-root validator independently joins
        # this deterministic node suffix to its canonical whole programme.
        # Reuse that exact frozen digest without hashing the population per leaf.
        digest=node.removeprefix(prefix)
        expected=ObjectIdentity(root.programme.record_id,root.programme.SCHEMA,root.programme.VERSION,digest)
        if programme!=expected:raise ValueError("prepared configuration substitutes its owning programme")
    elif programme is not None and programme!=root.programme:
        raise ValueError("prepared configuration substitutes its owning programme")
    validate_produced_input_parents(root.produced_input_parents)
    # Existing whole scientific-root validation independently checks every
    # source, link, phase, unit and denominator before compilation acceptance.
    return root.produced_input_parents
