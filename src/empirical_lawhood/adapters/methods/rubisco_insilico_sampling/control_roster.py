# SPDX-License-Identifier: MPL-2.0
"""Complete 24/96 denominator for an explicit chemical/force selected subset."""

from hashlib import sha256

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.isolated_native_subwork import IsolatedNativeEntrySelection
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkRoster

from . import control_contracts as c

METADATA = "control.chemical-force.metadata"


def definitions(plan, parent, *, sources, input_materialization_ids, implementation=None, source_root=None):
    plan.__post_init__()
    from .closed_raw_model_admission import InstanceChemicalForcePlan
    if type(plan) is InstanceChemicalForcePlan:
        expected = set(plan.instance_operands)
    else:
        expected = {plan.source,plan.preparation,plan.assignment_integrity,plan.mathematical_geometry,
            *(row[1] for row in plan.selected_assets),
            *(identity for row in plan.preparation_custody for identity in row[1:])}
    from .derived_model_admission import DerivedChemicalForcePlan
    if type(plan) is DerivedChemicalForcePlan:
        expected.update((plan.preparation_plan.identity, *(row.identity for row in plan.derived_supplies)))
    if not expected.issubset(sources):
        raise ValueError("control roster omits genuine selected independent/custody operands")
    identities = tuple(sorted(sources,key=lambda row:row.object_id))
    code = sha256(canonical_json_bytes(plan.code_sources)).hexdigest()
    if implementation is not None:
        from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_runner import validate_current_source_descriptor
        code = validate_current_source_descriptor(plan, implementation, source_root)
    inputs = tuple(sorted(input_materialization_ids))
    outputs = (json_output("files.census",DurableRawFileCensus),raw_output("files.raw"),
        json_output("unit.return",c.ChemicalForceReturn))
    # The later NVE denominator is retained without inventing a preparation
    # return schema for it. This stage has no NVE entry or output implementation.
    units = tuple(NativeSubworkDefinition(name,
        "rubisco.chemical-force.unentered-nve" if name.startswith("control.nve.") else "rubisco.chemical-force.unit",
        parent,plan.identity,identities,code,plan.dependency_lock_sha256,inputs,(),
        () if name.startswith("control.nve.") else outputs) for name in c.control_ids())
    metadata = NativeSubworkDefinition(METADATA,"rubisco.chemical-force.metadata",parent,
        plan.identity,identities,code,plan.dependency_lock_sha256,inputs,(),
        (json_output("control.census",c.ChemicalForceCensus),
         json_output("files.census",DurableRawFileCensus),raw_output("files.raw"),
         json_output("process.selection",IsolatedNativeEntrySelection)))
    return tuple(sorted((*units,metadata),key=lambda row:row.subwork_id))


def freeze(progress, plan, selected, *, implementation=None, source_root=None):
    if (not selected or tuple(sorted(row.subwork_id for row in selected)) != tuple(sorted((*c.control_ids(),METADATA)))
            or any(row.configuration != plan.identity or row.parent_contact != progress.parent_contact for row in selected)):
        raise ValueError("chemical/force roster changes its exact parent/plan or 24/96 denominator")
    if tuple(selected) != definitions(plan,progress.parent_contact,sources=selected[0].sources,
            input_materialization_ids=selected[0].input_materialization_ids,
            implementation=implementation, source_root=source_root):
        raise ValueError("chemical/force roster substitutes actual source/operation/output definitions")
    progress.freeze_roster(NativeSubworkRoster("selected.native-subwork",progress.parent_contact,
        tuple(row.identity for row in selected)),definitions=selected)


def census(progress, plan, selected, *, implementation=None, source_root=None):
    freeze(progress,plan,selected,implementation=implementation,source_root=source_root)
    by_id = {row.subwork_id:row for row in selected}
    return c.ChemicalForceCensus(plan.identity,tuple((name,progress.inspect(by_id[name]).state) for name in c.control_ids()))
