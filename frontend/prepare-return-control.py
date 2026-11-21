# SPDX-License-Identifier: MPL-2.0
"""Copy and independently reopen one real original through a disclosed return control.

The operational allocation is a software fixture, with no cloud action. Original
scientific packages, identities, source and all result reads remain authentic.
"""

import argparse
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys

from empirical_lawhood.api.application import execute_application
from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest, response_bytes
from empirical_lawhood.api.operational_observation import collect_observation, registered_binding
from empirical_lawhood.execution.remote.accelerated_deployment import seal_transfer, verify_transfer
from empirical_lawhood.execution.deployment_budget import DeploymentAllocation, DeploymentBudget
from empirical_lawhood.execution.operational_observation import SELECTION_SCHEMA, document, document_bytes
from empirical_lawhood.execution.operator_profile import OperatorStorageAccessMode, resolve_external_root_contract


def prepare(args):
    if not os.path.ismount(args.required_mount):
        raise ValueError('selected external mount is unavailable')
    for path in (args.output_dir, args.observation_root):
        path.relative_to(args.required_mount)
        if path.exists():
            raise ValueError('select fresh control destinations')
    original = ApplicationContext.from_document(document(args.context.read_bytes()))
    original = replace(original, project_root=None, python_executable=Path(sys.executable).absolute())
    args.output_dir.mkdir(mode=0o700)
    args.observation_root.mkdir(mode=0o700)
    def write(path, value):
        raw = document_bytes(value)
        with path.open('xb') as stream:
            stream.write(raw)
        return {'path': str(path), 'sha256': sha256(raw).hexdigest()}
    def call(context, name, operation, **values):
        request = ApplicationRequest(name, context.context_id, operation, tuple(values.items()))
        response = execute_application(context, request)
        write(args.output_dir / (name + '.request.json'), request.to_document())
        with (args.output_dir / (name + '.response.json')).open('xb') as stream:
            stream.write(response_bytes(response))
        if not response.succeeded:
            raise RuntimeError(str(response.reason_codes))
        return json.loads(response_bytes(response))['payload']
    selected = call(original, 'source-selection', 'collection.entry', selection_id=args.selection_id)['entry']
    primary = call(original, 'source-original', 'exploration.read', selection_id=args.selection_id)
    run_id = primary['provenance']['run_id']
    _, profile, source_plane = application_storage(original)
    source_root = Path(source_plane.root.contract.canonical_path)
    wave = Path(selected['value']['readers'][0]['directory'])
    contribution = next(row for row in selected['value']['companions'] if row['role'] == 'contribution')
    outgoing = args.output_dir / 'outgoing'
    outgoing.mkdir()
    paths = [wave.relative_to(source_root), Path(contribution['directory']).relative_to(source_root), Path('runs') / run_id]
    for relative in paths:
        target = outgoing / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_root / relative, target)
    sealed = seal_transfer(outgoing, args.output_dir / 'original-transfer.json', maximum_bytes=64*1024**2, maximum_files=4096)
    returned_root = args.output_dir / 'returned' / 'artifacts'
    returned_root.parent.mkdir()
    shutil.copytree(outgoing, returned_root)
    verify_transfer(returned_root, Path(sealed['manifest']), expected_sha256=sealed['sha256'])
    retained_profile = replace(profile, profile_id='ui-return-control', external_root_locator=str(returned_root.parent),
        access_mode=OperatorStorageAccessMode.READ_ONLY)
    profile_path = args.output_dir / 'retained-access-profile.json'
    profile_path.write_bytes(retained_profile.canonical_bytes())
    contract = resolve_external_root_contract(retained_profile, repo_root=Path.cwd(), home_root=Path.home(), for_write=False)
    contract = replace(contract, storage_root_id=source_plane.root.contract.storage_root_id, logical_name=source_plane.root.contract.logical_name)
    contract_path = args.output_dir / 'retained-root-contract.json'
    contract_path.write_bytes(contract.canonical_bytes())
    context = replace(original, context_id='exposed.original.return', label='Original return · disclosed transport control',
        operator_profile=profile_path, operational_profile=original.operational_profile or original.operator_profile,
        artifact_root_contract=contract_path, input_root=args.output_dir,
        collection_path=args.observation_root / 'collection.json', observation_root=args.observation_root,
        invocation_root=args.output_dir / 'invocations', progress_root=args.output_dir / 'progress')
    context.invocation_root.mkdir()
    context.progress_root.mkdir()
    source_context = replace(original, context_id='exposed.original.source', label='Original source custody · disclosed return control',
        collection_path=context.collection_path, observation_root=context.observation_root,
        invocation_root=args.output_dir/'source-invocations', progress_root=args.output_dir/'source-progress')
    source_context.invocation_root.mkdir()
    source_context.progress_root.mkdir()
    write(args.output_dir / 'context.json', context.to_document())
    write(args.output_dir / 'contexts.json', {'schema':'empirical-lawhood/application/contexts','version':'1.0.0',
        'contexts':[context.to_document(),source_context.to_document()]})
    implementation = document((wave / 'implementation.json').read_bytes())['value']
    from empirical_lawhood.workbench.engine import describe_engine
    controller = describe_engine()['identity_sha256']
    now = datetime.now(timezone.utc).isoformat()
    allocation = DeploymentAllocation('exposed-original-return', 'exposed-cluster', 'exposed-generation', 'exposed-pod',
        'exposed-head', 'exposed-volume', '/exposed/persistent', 'EXPOSED-1', now, now,
        DeploymentBudget('50', '10', '1', '0', '3.99', '0.01', '0.03'))
    allocation_pin = write(args.output_dir / 'allocation.json', allocation.to_document())
    job = write(args.output_dir / 'job-card.json', {'scope':'EXPOSED_RETURN_CONTROL; NO_REAL_ALLOCATION', 'observation':{
        'cadence_seconds':30,'stale_after_seconds':120,'controller_source_sha256':controller,
        'worker_source_sha256':implementation['code_sources_sha256'],'selected_gpu':'NONE; HISTORICAL_ANALYTICAL_ORIGINAL'}})
    source = write(args.output_dir / 'control-source.json', {'scope':'ORIGINAL_BYTES_WITH_DISCLOSED_OPERATIONAL_TRANSPORT_CONTROL',
        'original_selection':args.selection_id,'original_identity':primary['identity'],'provider_calls':0,'new_native_calls':0})
    entry = {'schema':'empirical-lawhood/application/run-selection','version':'1.0.0','value':{
        'selection_id':'returned.original','investigation_id':'original.return.control','context_id':context.context_id,
        'label':'Original Rubisco · disclosed return control','question':primary['exploration']['question'],
        'identity':primary['identity'],'readers':[{'operation':'presentation.read','directory':str(wave),'context_id':source_context.context_id,
            'panel_id':'rubisco.initial-root','panel_version':'1.0.0'}],
        'classification':{'programmes':[{'id':'original.return.control','label':'Disclosed original-return control'}],
            'disciplines':[],'source':source},'companions':[dict(contribution,directory=str(returned_root / paths[1]))],
        'stages':[],'links':[],'deployment':{'deployment_id':allocation.deployment_id,'run_id':run_id,
            'packet_sha256':primary['identity']['value']['object_fingerprint'],'controller_source_sha256':controller,
            'worker_source_sha256':implementation['code_sources_sha256'],'allocation':allocation_pin,'job_card':job,
            'observation_path':str(args.observation_root/'current.json'),'return_path':str(args.observation_root/'return.json')}}}
    registered = call(context, 'register-original', 'collection.register', text=document_bytes(entry).decode())
    # Preserve the source locator while attaching the copied original through its
    # separate retained-access context and unchanged original storage identity.
    entry['value']['readers'].append(dict(entry['value']['readers'][0],
        directory=str(returned_root / paths[0]), context_id=context.context_id))
    call(context, 'attach-return', 'collection.register', text=document_bytes(entry).decode(),
        expected_collection_sha256=registered['collection_sha256'])
    binding = registered_binding(entry)
    selection = {'schema':SELECTION_SCHEMA,'version':'1.0.0','binding':binding,
        'directory':str(returned_root / paths[0]),'allocation':allocation_pin,'job_card':job,'supervisors':[],
        'cadence_seconds':30,'stale_after_seconds':120,'task_offset':0,'native_offset':0,'row_limit':200,'domain_panel':None}
    pin = write(args.output_dir / 'observation-selection.json', selection)
    exported = collect_observation(context, pin, collector_id='original.return.collector', sequence=1,
        output_directory=args.observation_root/'export-01')
    incoming = args.output_dir/'incoming-observation'
    shutil.copytree(exported['directory'], incoming)
    call(context, 'import-observation', 'observation.import', selection_id='returned.original',
        directory=str(incoming), expected_manifest_sha256=exported['manifest_sha256'])
    digest = None
    for stage in ('REMOTE_PUBLICATION','SEALED_EXPORT','TRANSFER','BYTE_VERIFICATION'):
        event = {'stage':stage,'action':'VERIFY_FILES','root':str(returned_root),'manifest':sealed['manifest'],'manifest_sha256':sealed['sha256']}
        values = {'selection_id':'returned.original','text':document_bytes(event).decode()}
        if digest:values['expected_return_sha256']=digest
        result = call(context, 'return-'+stage.lower(), 'observation.record-return', **values)
        digest = result['state_sha256']
    for stage, action in (('INDEPENDENT_READING','READ_ORIGINAL'),('CONTRIBUTION','READ_CONTRIBUTION')):
        result = call(context, 'return-'+stage.lower(), 'observation.record-return', selection_id='returned.original',
            text=document_bytes({'stage':stage,'action':action,'reader_index':1}).decode(), expected_return_sha256=digest)
        digest=result['state_sha256']
    final = call(context, 'final-observation', 'observation.read', selection_id='returned.original')
    assert final['local_return']['terminal'] and len(final['local_return']['stages']) == 6
    write(args.output_dir/'acceptance.json', {'status':'PASS','scope':'REAL_ORIGINAL_COPY_AND_READ_WITH_DISCLOSED_ALLOCATION',
        'identity':primary['identity'],'transfer':sealed,'return_state_sha256':digest,'new_native_calls':0,'provider_calls':0,
        'original_files_unchanged':all((source_root/r/p.relative_to(outgoing/r)).read_bytes()==p.read_bytes()
            for r in paths for p in (outgoing/r).rglob('*') if p.is_file()),
        'contexts':str(args.output_dir/'contexts.json')})
    print(json.dumps({'status':'PASS','output_dir':str(args.output_dir),'new_native_calls':0,'provider_calls':0}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('context','output-dir','observation-root','required-mount'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--selection-id',required=True)
    prepare(parser.parse_args())


if __name__ == '__main__':
    main()
