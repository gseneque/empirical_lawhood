# SPDX-License-Identifier: MPL-2.0
"""Durable selected NVE child; no broad calibration or production entry."""
from hashlib import sha256
import json
from pathlib import Path
import sys


def build_invocation(plan,source,supplies,custody,selected,*,source_root):
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from . import nve_roster
    from .nve_science import validate_operands
    validate_operands(plan,source,supplies,custody)
    if not selected or tuple(selected)!=nve_roster.definitions(plan,selected[0].parent_contact,
            sources=selected[0].sources,input_materialization_ids=selected[0].input_materialization_ids):
        raise ValueError('NVE precontact invocation changes actual full97 definitions')
    def encode(record):
        raw=record.canonical_bytes()
        if decode_canonical_bytes(raw,type(record),maximum_bytes=len(raw))!=record:
            raise ValueError('NVE precontact invocation omits original full typed roundtrip')
        return raw.decode()
    return canonical_json_bytes(dict(plan=encode(plan),source=encode(source),supplies=tuple(encode(row) for row in supplies),
        custody=tuple((name,*(encode(row) for row in records)) for name,*records in custody),
        definitions=tuple(encode(row) for row in selected),source_root=source_root))


def selected_child(progress,invocation):
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import _SelectedSourceFinder
    data=json.loads(invocation.read())
    if set(data)!={'plan','source','supplies','custody','definitions','source_root'}:
        raise ValueError('NVE child substitutes complete actual invocation operand census')
    finder=_SelectedSourceFinder(data['source_root'],json.loads(data['plan'])['value']['code_sources'])
    sys.meta_path.insert(0,finder)
    try:_authenticated_child(progress,data,invocation.prepared_invocation)
    finally:sys.meta_path.remove(finder)


def _prepare_child(data,parent,prepared_contract=None):
    """Original full-state/predecessor/stock checks without a native contact."""
    import os
    import shutil
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p,science as preparation_science
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import authenticate_engine_stock
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import file_chunks
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition,NativeSubworkCompletion
    from . import control_contracts as f,nve_contracts as c,nve_roster
    from .nve_preparation_admission import decode_plan
    from .control_native_entry import validate_plugin_environment
    from .nve_science import validate_operands
    def decode(raw,kind):
        raw=raw.encode()
        return decode_canonical_bytes(raw,kind,maximum_bytes=len(raw))
    plan=decode_plan(data['plan'])
    source=decode(data['source'],p.PreparationSelection)
    supplies=tuple(decode(row,c.RelaxedModelSupply) for row in data['supplies'])
    custody=tuple((name,decode(definition,NativeSubworkDefinition),decode(completion_id,ObjectIdentity),
        decode(completion,NativeSubworkCompletion),decode(returned,f.ChemicalForceReturn),decode(assessment,f.ChemicalForceAssessment))
        for name,definition,completion_id,completion,returned,assessment in data['custody'])
    selected=tuple(decode(row,NativeSubworkDefinition) for row in data['definitions'])
    if (not selected or selected!=nve_roster.definitions(plan,parent,
            sources=selected[0].sources,input_materialization_ids=selected[0].input_materialization_ids,
            implementation=None if prepared_contract is None else prepared_contract.implementation,source_root=data['source_root'])):
        raise ValueError('NVE child substitutes complete original 96/metadata roster')
    inventory=authenticate_engine_stock(preparation_science.validate_stock(source.source_members))
    runtime=validate_plugin_environment(inventory,os.environ)
    controls=plan.chemical_controls
    if sha256((Path(data['source_root'])/'uv.lock').read_bytes()).hexdigest()!=plan.dependency_lock_sha256:
        raise ValueError('NVE child substitutes selected immutable lock')
    def verify_file(path,size=None,digest=None):
        actual,size_actual=sha256(),0
        for chunk in file_chunks(Path(path).resolve()):actual.update(chunk);size_actual+=len(chunk)
        if actual.hexdigest()!=digest or (size is not None and size_actual!=size):raise ValueError('NVE selected actual runtime bytes changed')
    for path,digest in ((controls.interpreter_path,controls.interpreter_sha256),(controls.hardware_inspector_path,controls.hardware_inspector_sha256)):
        verify_file(path,digest=digest)
    if len(tuple(row for row in controls.external_runtime_files if Path(row[0]).name=='libcuda.so.'+controls.hardware.driver_version))!=1:
        raise ValueError('NVE entry omits selected actual external OS driver')
    for path,size,digest in controls.external_runtime_files:verify_file(path,size,digest)
    if (Path(shutil.which('nvidia-smi') or '').resolve()!=Path(controls.hardware_inspector_path).resolve()
            or not any(row['kind']=='file' and row['sha256']==controls.interpreter_sha256 for row in inventory['entries'])):
        raise ValueError('NVE child substitutes actual selected executable/tool')
    if os.environ.get('PYTHONDONTWRITEBYTECODE')!='1' or not all(os.environ.get(name)=='1' for name in (
            'OPENMM_CPU_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')):
        raise ValueError('NVE child substitutes one-thread/bytecode selected environment')
    # This PURE full-array admission imports NumPy. Authenticate selected stock
    # first, and finish all genuine predecessor joins before importing OpenMM.
    validate_operands(plan,source,supplies,custody)
    return plan,source,supplies,custody,selected,inventory,runtime


def preflight_selected_child(*,invocation,expected_parent,prepared_contract):
    """Authenticate all selected NVE operands and libraries, no integration."""
    import importlib
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import (
        _SelectedSourceFinder,_prepared_embedded_work,authenticate_loaded_engine_modules,refuse_external_network)
    data=json.loads(invocation.read())
    if set(data)!={'plan','source','supplies','custody','definitions','source_root'}:
        raise ValueError('NVE child substitutes complete actual invocation operand census')
    finder=_SelectedSourceFinder(data['source_root'],json.loads(data['plan'])['value']['code_sources'])
    sys.meta_path.insert(0,finder)
    try:
        plan,source,supplies,custody,selected,inventory,_=_prepare_child(data,expected_parent,prepared_contract)
        from .serialized_nve_custody import SerializedCustodyNVEControlPlan
        from .operation_bindings import native_effect_slot_ids, p
        if type(plan) is SerializedCustodyNVEControlPlan:
            records=(source,plan.chemical_controls,*supplies,*plan.chemical_custody_supplies)
            identities=(plan.identity,plan.chemical_controls.source,plan.chemical_controls.identity,
                *(row.identity for row in supplies),*(row.identity for row in plan.chemical_custody_supplies))
        else:
            records=(source,*supplies,*(record for row in custody for record in (row[1],row[3],row[4],row[5])))
            identities=None
        work=_prepared_embedded_work(prepared_contract,expected_parent,plan,selected,records,
            scientific_unit_ids=(p.UNIT,),
            native_effect_slot_ids=native_effect_slot_ids(SimpleNamespace(plan=plan,source=source,operation="nve-control")),
            record_identities=identities)
        refuse_external_network(None)
        for name in ('numpy','scipy','openmm'):
            importlib.import_module(name)
        authenticate_loaded_engine_modules(inventory)
        return work
    finally:
        sys.meta_path.remove(finder)


def _authenticated_child(progress,data,prepared_contract=None):
    import traceback
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import (
        authenticate_loaded_engine_modules,refuse_external_network)
    from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import publish_directory,publish_record
    from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
    from empirical_lawhood.kernel.status import OperationalStatus
    from . import control_contracts as f,nve_contracts as c,nve_roster,storage
    plan,source,supplies,custody,selected,inventory,runtime=_prepare_child(data,progress.parent_contact,prepared_contract)
    controls=plan.chemical_controls
    nve_roster.freeze(progress,plan,selected,implementation=None if prepared_contract is None else prepared_contract.implementation,
        source_root=data['source_root'])
    root=Path(plan.workdir)
    refuse_external_network(root/'launcher/network-refusals.jsonl')
    import numpy as np
    import openmm as mm
    from openmm import app,unit
    from . import native
    from .control_native_ledger import ChemicalForceLedger
    from .control_instrumentation import materialize_flat_assets
    from .nve_instrumentation import selected_nve_instrumentation
    storage.immutable_bytes(root/'launcher/loaded-engine-modules.json',json.dumps(authenticate_loaded_engine_modules(inventory),sort_keys=True).encode()+b'\n')
    storage.immutable_bytes(root/'launcher/selected-cuda-runtime.json',json.dumps(dict(engine_files=runtime,
        external_files=controls.external_runtime_files,context_qualification='NOT_ESTABLISHED_BY_STATIC_STOCK'),sort_keys=True).encode()+b'\n')
    by_supply={row.model_id:row for row in supplies}
    by_definition={row.subwork_id:row for row in selected}
    for roster in plan.selected_cases:
        supply=by_supply[f.model_id(roster[:3])]
        definition=by_definition[c.unit_id(roster)]
        entry=progress.begin(definition)
        progress.contact(entry)
        directory=root/definition.subwork_id
        directory.mkdir()
        ledger=ChemicalForceLedger(progress,plan,root,entry,directory)
        error,result=None,None
        try:
            native._verify_hardware(plan,directory,ledger)
            paths=materialize_flat_assets(supply.model_assets,directory)
            storage.immutable_bytes(directory/'admitted-system.xml',supply.system.raw_utf8.encode())
            storage.immutable_bytes(directory/'admitted-relaxed-state.xml',supply.relaxed_state.raw_utf8.encode())
            state=ledger.call('sampling.deserialize-admitted-relaxed-state',dict(source_supply=supply.identity.to_document(),
                full_state_sha256=supply.relaxed_state.evidence.sha256),lambda:mm.XmlSerializer.deserialize(supply.relaxed_state.raw_utf8))
            shared=dict(paths=paths,positions=state.getPositions(asNumpy=True),box=state.getPeriodicBoxVectors(),
                atom_count=len(state.getPositions()),force_path=(directory/'admitted-relaxed-state.xml').relative_to(root).as_posix())
            with selected_nve_instrumentation(native,mm,unit,ledger,directory,np):
                result=native._nve_case(plan,shared,roster,directory,root,ledger,mm,app,unit)
        except Exception:
            error=traceback.format_exc()
            storage.immutable_bytes(directory/'technical-failure.txt',error.encode())
        full,_=publish_directory(progress,entry,directory,root)
        returned=c.NVEControlReturn(definition.subwork_id,plan.identity,supply.identity,error is None,
            shared['atom_count'] if result is not None else 0,full.files,
            tuple(sorted((row.identity for row in ledger.call_definitions),key=lambda row:row.object_id)),error)
        publish_record(progress,entry,'unit.return',returned)
        progress.complete(entry,operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
            cost=InquiryCost(None,None,None),cost_scope='Actual100ps numerical control; enclosing launcher inclusive cost measured separately',
            reason_codes=() if error is None else ('known-nve-control-operator-error',))
