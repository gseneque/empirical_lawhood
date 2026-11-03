# SPDX-License-Identifier: MPL-2.0
"""Selected isolated chemical/force entry; no unassessed or absent models."""

from hashlib import sha256
import json
from pathlib import Path
import sys


def validate_plugin_environment(inventory, environment):
    """Named existing stock only; no platform import or Context qualification."""
    selected = {}
    for name in ("libOpenMMCUDA.so","libOpenMMCPU.so","libOpenMMPME.so",
                 "libnvrtc.so.12","libcufft.so.11","libcudart.so.12"):
        matches = tuple(row for row in inventory["entries"] if row["kind"] == "file" and Path(row["actual_path"]).name == name)
        if len(matches) != 1:
            raise ValueError("chemical/force selected full engine omits unique required CUDA/CPU runtime: "+name)
        selected[name] = matches[0]
    plugins = Path(selected["libOpenMMCUDA.so"]["actual_path"]).parent
    if (any(Path(selected[name]["actual_path"]).parent != plugins for name in ("libOpenMMCPU.so","libOpenMMPME.so"))
            or environment.get("OPENMM_PLUGIN_DIR") != str(plugins)):
        raise ValueError("chemical/force entry needs explicit authenticated bundled plugin directory; empty/default override refused")
    return selected


def selected_child(progress, invocation):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import _SelectedSourceFinder
    data = json.loads(invocation.read())
    if set(data) != {"plan","source","preparation","integrity","geometry","assets","custody","definitions","source_root"}:
        raise ValueError("chemical/force invocation changes its complete selected operand census")
    finder = _SelectedSourceFinder(data["source_root"],json.loads(data["plan"])["value"]["code_sources"])
    sys.meta_path.insert(0,finder)
    try:
        _authenticated_child(progress,data,invocation.prepared_invocation)
    finally:
        sys.meta_path.remove(finder)


def _prepare_child(data, parent, prepared_contract=None):
    """Original predecessor, roster and runtime admission without contact."""
    import os
    import shutil
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p, science as preparation_science
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableUnitReturn
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import authenticate_engine_stock
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import file_chunks
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkCompletion
    from . import control_roster
    from .control_preparation_admission import decode_assessments, decode_plan, validate_operands
    from .closed_raw_model_admission import InstanceChemicalForcePlan, ModelInstanceInputs

    def decode(value, kind):
        raw = value.encode()
        return decode_canonical_bytes(raw,kind,maximum_bytes=len(raw))
    plan = decode_plan(data["plan"])
    source = decode(data["source"],p.PreparationSelection)
    if type(plan) is InstanceChemicalForcePlan:
        if data["integrity"] != "null" or data["geometry"] != "null" or data["custody"] != []:
            raise ValueError("instance chemical child substitutes absent legacy assessment/custody slots")
        preparation = decode(data["preparation"],ModelInstanceInputs)
        integrity = geometry = None
    else:
        preparation = decode(data["preparation"],p.PreparationProduct)
        integrity, geometry = decode_assessments(data["integrity"], data["geometry"])
    assets = tuple(decode(row,p.ModelAssets) for row in data["assets"])
    custody = tuple((name,decode(definition,NativeSubworkDefinition),decode(completion_id,ObjectIdentity),
        decode(completion,NativeSubworkCompletion),decode(return_id,ObjectIdentity),decode(returned,DurableUnitReturn))
        for name,definition,completion_id,completion,return_id,returned in data["custody"])
    selected = tuple(decode(row,NativeSubworkDefinition) for row in data["definitions"])
    validate_operands(plan,source,preparation,integrity,geometry,assets,custody)
    if plan.engine_inventory_sha256 != source.engine_inventory_sha256:
        raise ValueError("chemical/force entry substitutes original selected full engine stock")
    if any(row.parent_contact != parent for row in selected):
        raise ValueError("chemical/force child changes its actual entered parent contact")
    if (not selected or selected != control_roster.definitions(plan,parent,
            sources=selected[0].sources,input_materialization_ids=selected[0].input_materialization_ids,
            implementation=None if prepared_contract is None else prepared_contract.implementation,source_root=data["source_root"])):
        raise ValueError("chemical/force child changes its complete original 24/96/metadata roster")
    stock = preparation_science.validate_stock(source.source_members)
    inventory = authenticate_engine_stock(stock)
    runtime_files = validate_plugin_environment(inventory,os.environ)
    if sha256((Path(data["source_root"])/"uv.lock").read_bytes()).hexdigest() != plan.dependency_lock_sha256:
        raise ValueError("chemical/force child substitutes its locked dependency bytes")
    for path,digest in ((plan.interpreter_path,plan.interpreter_sha256),
                        (plan.hardware_inspector_path,plan.hardware_inspector_sha256)):
        current = sha256()
        for chunk in file_chunks(Path(path).resolve()):
            current.update(chunk)
        if current.hexdigest() != digest:
            raise ValueError("chemical/force selected actual executable bytes changed")
    drivers = tuple(row for row in plan.external_runtime_files if Path(row[0]).name == "libcuda.so."+plan.hardware.driver_version)
    if len(drivers) != 1:
        raise ValueError("chemical/force entry omits selected actual OS CUDA driver bytes; hardware query is not Context qualification")
    for path,size,digest in plan.external_runtime_files:
        actual,size_actual = sha256(),0
        for chunk in file_chunks(Path(path)):
            actual.update(chunk)
            size_actual += len(chunk)
        if (size_actual,actual.hexdigest()) != (size,digest):
            raise ValueError("chemical/force selected external runtime bytes changed")
    if not any(row["kind"] == "file" and row["sha256"] == plan.interpreter_sha256 for row in inventory["entries"]):
        raise ValueError("chemical/force interpreter is absent from selected engine stock")
    if Path(shutil.which("nvidia-smi") or "").resolve() != Path(plan.hardware_inspector_path).resolve():
        raise ValueError("chemical/force actual hardware query escapes selected authenticated tool")
    if (os.environ.get("PYTHONDONTWRITEBYTECODE") != "1" or not all(os.environ.get(name) == "1"
            for name in ("OPENMM_CPU_THREADS","OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS",
                         "NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"))):
        raise ValueError("chemical/force child changed selected one-thread environment")
    return plan, source, preparation, integrity, geometry, assets, custody, selected, inventory, runtime_files


def preflight_selected_child(*, invocation, expected_parent, prepared_contract):
    """Exact selected chemical control input/runtime checks, without Context."""
    import importlib
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import (
        _SelectedSourceFinder, _prepared_embedded_work, authenticate_loaded_engine_modules, refuse_external_network)
    data=json.loads(invocation.read())
    if set(data)!={"plan","source","preparation","integrity","geometry","assets","custody","definitions","source_root"}:
        raise ValueError("chemical/force invocation changes complete selected operand census")
    finder=_SelectedSourceFinder(data["source_root"],json.loads(data["plan"])["value"]["code_sources"])
    sys.meta_path.insert(0,finder)
    try:
        plan,source,preparation,integrity,geometry,assets,custody,selected,inventory,_=_prepare_child(data,expected_parent,prepared_contract)
        from .closed_raw_model_admission import InstanceChemicalForcePlan, ordinary_instance_records
        from .operation_bindings import native_effect_slot_ids, p
        if type(plan) is InstanceChemicalForcePlan:
            originals = dict(ordinary_instance_records(preparation)) | {plan.source: source,
                **{identity: asset for (_, identity), asset in zip(plan.selected_assets, assets, strict=True)}}
            ordered = tuple(sorted(originals.items(), key=lambda row: row[0].object_id))
            records = tuple(record for _, record in ordered)
            identities = (plan.identity, *(identity for identity, _ in ordered))
        else:
            records=(source,preparation,*(row for row in (integrity,geometry) if row is not None),*assets,
                *(record for row in custody for record in (row[1],row[3],row[5])))
            identities=None
        work=_prepared_embedded_work(prepared_contract,expected_parent,plan,selected,records,
            scientific_unit_ids=(p.UNIT,),
            native_effect_slot_ids=native_effect_slot_ids(SimpleNamespace(plan=plan,source=source,operation="chemical-force")),
            record_identities=identities)
        refuse_external_network(None)
        for name in ("numpy","scipy","openmm"):
            importlib.import_module(name)
        authenticate_loaded_engine_modules(inventory)
        return work
    finally:
        sys.meta_path.remove(finder)


def _authenticated_child(progress, data, prepared_contract=None):
    import os
    import traceback

    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import (
        authenticate_loaded_engine_modules, refuse_external_network)
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import (
        publish_directory, publish_record)
    from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
    from empirical_lawhood.kernel.status import OperationalStatus
    from . import control_contracts as c, control_roster, storage

    plan, source, preparation, integrity, geometry, assets, custody, selected, inventory, runtime_files = _prepare_child(data, progress.parent_contact,prepared_contract)
    control_roster.freeze(progress,plan,selected,implementation=None if prepared_contract is None else prepared_contract.implementation,
        source_root=data["source_root"])
    root = Path(plan.workdir)
    refuse_external_network(root/"launcher/network-refusals.jsonl")
    # Actual native imports follow original independent admission and full stock
    # authentication. No old standalone calibration or 96-case launcher is used.
    import numpy as np
    import openmm as mm
    from openmm import app, unit
    from . import native
    from .control_instrumentation import selected_control_instrumentation
    from .control_native_ledger import ChemicalForceLedger

    storage.immutable_bytes(root/"launcher/loaded-engine-modules.json",
        json.dumps(authenticate_loaded_engine_modules(inventory),sort_keys=True,separators=(",",":" )).encode()+b"\n")
    storage.immutable_bytes(root/"launcher/selected-cuda-runtime.json",json.dumps(dict(
        engine_runtime_files=runtime_files,external_runtime_files=plan.external_runtime_files,
        plugin_directory=os.environ["OPENMM_PLUGIN_DIR"],context_qualification="NOT_ESTABLISHED_BY_STATIC_STOCK"),
        sort_keys=True,separators=(",",":" )).encode()+b"\n")
    by_id = {row.subwork_id:row for row in selected}
    for asset in assets:
        key = asset.construct_id,asset.joint_view_id,asset.parameter_view
        definition = by_id[c.force_id(key)]
        # begin() rejects uncertain previous work; this fresh child never replays.
        entry = progress.begin(definition)
        progress.contact(entry)
        directory = root/("shared-model."+".".join(key))
        ledger = ChemicalForceLedger(progress,plan,root,entry,directory)
        error,result = None,None
        try:
            with selected_control_instrumentation(native,mm,unit,ledger,directory,np,
                    before_materialization=lambda:native._verify_hardware(plan,directory,ledger)):
                result = native._shared_model(plan,asset,root,ledger,mm,app,unit,np)
        except Exception:
            error = traceback.format_exc()
            # _shared_model owns directory creation. A pre-creation known error
            # still retains its full technical return, without inventing assets.
            directory.mkdir(exist_ok=True)
            storage.immutable_bytes(directory/"technical-failure.txt",error.encode())
        full,_ = publish_directory(progress,entry,directory,root)
        returned = c.ChemicalForceReturn(definition.subwork_id,plan.identity,p.identity(asset),error is None,
            result["atom_count"] if result is not None else 0,
            result["force_path"] if result is not None else None,full.files,
            tuple(sorted((row.identity for row in ledger.call_definitions),key=lambda row:row.object_id)),error)
        publish_record(progress,entry,"unit.return",returned)
        progress.complete(entry,operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
            cost=InquiryCost(None,None,None),
            cost_scope="Selected chemical/force return; launcher inclusive window measured separately; unit cost unknown",
            reason_codes=() if error is None else ("known-chemical-force-operator-error",))
