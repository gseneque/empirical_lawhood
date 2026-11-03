# SPDX-License-Identifier: MPL-2.0
"""Complete durable NVE denominator; only the explicit admitted subset enters."""
from hashlib import sha256
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition,NativeSubworkRoster
from . import nve_contracts as c

METADATA='control.nve.metadata'


def definitions(plan,parent,*,sources,input_materialization_ids,implementation=None,source_root=None):
    plan.__post_init__()
    expected={plan.chemical_controls.identity,plan.chemical_controls.source,*(identity for row in plan.admitted_parents for identity in row[1:])}
    from .serialized_nve_custody import source_projection
    expected=source_projection(plan,expected)
    if not expected.issubset(sources):raise ValueError('NVE roster omits actual chemical admission/custody')
    inputs=tuple(sorted(input_materialization_ids))
    identities=tuple(sorted(sources,key=lambda row:row.object_id))
    code=sha256(canonical_json_bytes(plan.code_sources)).hexdigest()
    if implementation is not None:
        from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import validate_current_source_descriptor
        code=validate_current_source_descriptor(plan,implementation,source_root)
    outputs=(json_output('files.census',DurableRawFileCensus),raw_output('files.raw'),json_output('unit.return',c.NVEControlReturn))
    units=tuple(NativeSubworkDefinition(name,'rubisco.nve-control.unit',parent,plan.identity,identities,code,
        plan.dependency_lock_sha256,inputs,(),outputs) for name in c.unit_ids())
    metadata=NativeSubworkDefinition(METADATA,'rubisco.nve-control.metadata',parent,plan.identity,identities,code,
        plan.dependency_lock_sha256,inputs,(),(json_output('control.census',c.NVEControlCensus),
            json_output('files.census',DurableRawFileCensus),raw_output('files.raw'),json_output('process.selection',IsolatedNativeEntrySelection)))
    return tuple(sorted((*units,metadata),key=lambda row:row.subwork_id))


def freeze(progress,plan,selected,*,implementation=None,source_root=None):
    if not selected or tuple(selected)!=definitions(plan,progress.parent_contact,sources=selected[0].sources,
            input_materialization_ids=selected[0].input_materialization_ids,implementation=implementation,source_root=source_root):
        raise ValueError('NVE roster substitutes full97 definitions/actual parent/operands')
    progress.freeze_roster(NativeSubworkRoster('selected.native-subwork',progress.parent_contact,tuple(row.identity for row in selected)),definitions=selected)


def census(progress,plan,selected,*,implementation=None,source_root=None):
    freeze(progress,plan,selected,implementation=implementation,source_root=source_root)
    by_id={row.subwork_id:row for row in selected}
    return c.NVEControlCensus(plan.identity,tuple((name,progress.inspect(by_id[name]).state) for name in c.unit_ids()))
