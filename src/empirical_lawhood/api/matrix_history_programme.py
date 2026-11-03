# SPDX-License-Identifier: MPL-2.0
"""Thin E2 facade; original source/result receipts remain its durable state."""
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_history_analysis.experiment_preparation import (
    PROTOCOL_ID,MatrixHistoryProgrammePlan)
from empirical_lawhood.api.composite_experiment_programme import write_experiment_programme_descriptor
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile,ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_programme import ExperimentProgrammeDescriptor,PROGRAMME_DESCRIPTOR_FILENAME

PLAN_FILENAME='history-programme.json'


class MatrixHistoryProgrammeService:
    def __init__(self,*,service,descriptor=None):
        self.service,self.writer,self.descriptor=service,service.artifact_writer,descriptor

    def _path(self,directory,*,writing):
        directory=Path(directory)
        if not directory.is_absolute() or any(value.is_symlink() for value in (directory,*directory.parents)):
            raise ValueError('E2 programme requires its selected absolute guarded directory')
        relative=(directory/PLAN_FILENAME).relative_to(self.writer.root.contract.canonical_path).as_posix()
        return self.writer.root.resolve(relative,for_write=writing),relative

    def _plan(self,directory):
        path,relative=self._path(directory,writing=False)
        manifest=self.writer.read_manifest(relative)
        self.writer.verify_manifest(manifest)
        raw=read_bounded_bytes(path,maximum_bytes=manifest.materialization.size_bytes)
        plan=decode_canonical_bytes(raw,MatrixHistoryProgrammePlan,maximum_bytes=len(raw))
        if raw!=plan.canonical_bytes() or self.descriptor is None or (
                self.descriptor.programme,self.descriptor.specification)!=(plan.identity,plan.specification.identity):
            raise PermissionError('E2 programme descriptor differs from actual retained canonical selection')
        if (manifest.logical.payload_schema!=plan.SCHEMA or manifest.logical.content_sha256!=plan.fingerprint()
                or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or plan.output_root!=self.writer.root.contract.canonical_path):
            raise PermissionError('E2 programme changes its actual original publication/root/access')
        return plan

    def author(self,*,preparation,output_dir):
        plan=preparation.programme
        if type(plan) is not MatrixHistoryProgrammePlan or plan.specification.identity!=preparation.specification:
            raise TypeError('E2 authoring requires its exact prepared descriptive plan')
        if not preparation.executable:raise ValueError('E2 authoring retains its explicit unmet prerequisites')
        from empirical_lawhood.api.recursive_authoring import implementation_binding
        from empirical_lawhood.kernel.provenance import ObjectIdentity
        actual=implementation_binding(self.service.project_root)
        if plan.source_snapshot!=ObjectIdentity.from_record('recursive-member.implementation',actual):
            raise ValueError('E2 authoring source differs from the actual selected checkout')
        if plan.output_root!=self.writer.root.contract.canonical_path:
            raise ValueError('E2 authoring storage differs from its selected guarded root')
        self.service._selected_workers(plan.workers)
        _,relative=self._path(output_dir,writing=True)
        publication=self.writer.write(ArtifactWriteRequest(plan.record_id,relative,plan.SCHEMA,
            ArtifactProfile.CANONICAL_JSON,'application/json',plan.record_id,Path(relative).parent.as_posix(),
            plan.canonical_bytes(),VisibilityCeiling.DEVELOPMENT_ONLY,(),OutcomeAccess.DEVELOPMENT_VISIBLE))
        descriptor=ExperimentProgrammeDescriptor('descriptor.'+plan.record_id,PROTOCOL_ID,
            plan.specification.identity,plan.identity)
        descriptor_relative=(Path(relative).parent/PROGRAMME_DESCRIPTOR_FILENAME).as_posix()
        path=self.writer.root.resolve(descriptor_relative,for_write=True)
        if path.exists():
            if read_bounded_bytes(path,maximum_bytes=len(descriptor.canonical_bytes()))!=descriptor.canonical_bytes():
                raise PermissionError('E2 authoring retry changes its exact public descriptor')
        else:
            write_experiment_programme_descriptor(service=self.service,directory=output_dir,descriptor=descriptor)
        return {'programme':plan.identity.to_document(),'publication':publication.to_document(),
            'state':'DESCRIPTIVE_PLAN_RETAINED','scientific_authority':'NONE','native_contact':'NONE'}

    def _read_result(self,plan):
        from empirical_lawhood.api.matrix_history_analysis import read_matrix_history_analysis,matrix_history_result_summary
        receipt=read_matrix_history_analysis(writer=self.writer,
            relative_path=plan.specification.result_relative_root+'/receipt.json',config=plan.analysis)
        if receipt.allocation_publication.logical.content_sha256!=plan.allocation.fingerprint():
            raise PermissionError('E2 result changes its exact original complete allocation')
        actual=tuple(sorted(value.source_receipt_path for value in receipt.roots if value.source_receipt_path is not None))
        if (receipt.source_receipt_locators!=plan.specification.source_receipt_paths
                or set(actual)-set(plan.specification.source_receipt_paths)):
            raise PermissionError('E2 result adds an unselected original source receipt')
        return {'programme':plan.identity.to_document(),'state':'DESCRIPTIVE_RESULT_RETAINED',
            'receipt':{'receipt_id':receipt.receipt_id,'schema':receipt.SCHEMA,'version':receipt.VERSION,'sha256':receipt.fingerprint()},
            'result':matrix_history_result_summary(receipt),'native_contact':'NONE','scientific_qualification':'NOT_ESTABLISHED'}

    def run(self,*,directory,maximum_parallel_tasks,programme_request_path=None,confirmed=False):
        if programme_request_path is not None or confirmed:
            raise ValueError('E2 descriptive programme accepts its immutable plan; scientific campaign requests are inapplicable')
        plan=self._plan(directory)
        if self.service._selected_workers(maximum_parallel_tasks)!=plan.workers:
            raise ValueError('E2 run changes its selected worker capacity')
        if plan.specification.mode=='ACQUIRE_AND_ANALYZE':
            raise ValueError('E2 parallel native lowering is absent; existing dedicated imports/retained analyses remain available')
        if plan.specification.mode=='READ_RETAINED':return self._read_result(plan)
        from empirical_lawhood.api.recursive_authoring import implementation_binding
        from empirical_lawhood.kernel.provenance import ObjectIdentity
        if ObjectIdentity.from_record('recursive-member.implementation',implementation_binding(self.service.project_root))!=plan.source_snapshot:
            raise ValueError('E2 calculation source differs from its original selected implementation')
        from empirical_lawhood.api.matrix_history_analysis import analyze_matrix_histories
        analyze_matrix_histories(config=plan.analysis,allocation=plan.allocation,
            source_receipt_paths=plan.specification.source_receipt_paths,writer=self.writer,
            relative_root=plan.specification.result_relative_root,repo_root=self.service.project_root,recover=False)
        return self._read_result(plan)

    def recover(self,*,directory,maximum_parallel_tasks,programme_request_path=None,confirmed=False):
        if programme_request_path is not None or confirmed:raise ValueError('E2 recovery accepts only its exact original retained plan')
        plan=self._plan(directory)
        if self.service._selected_workers(maximum_parallel_tasks)!=plan.workers:raise ValueError('E2 recovery changes worker selection')
        # Existing completed result is read without calculation. Missing completion
        # enters only the original owner's explicit receipt-based recovery path.
        result=plan.specification.result_relative_root+'/receipt.json'
        path=self.writer.root.resolve(result,for_write=False)
        if path.exists():return self._read_result(plan)
        if plan.specification.mode!='ANALYZE_RETAINED':raise FileNotFoundError('E2 selected retained result is absent')
        from empirical_lawhood.api.recursive_authoring import implementation_binding
        from empirical_lawhood.kernel.provenance import ObjectIdentity
        if ObjectIdentity.from_record('recursive-member.implementation',implementation_binding(self.service.project_root))!=plan.source_snapshot:
            raise ValueError('E2 incomplete recovery source differs from its original selected implementation')
        from empirical_lawhood.api.matrix_history_analysis import analyze_matrix_histories
        analyze_matrix_histories(config=plan.analysis,allocation=plan.allocation,
            source_receipt_paths=plan.specification.source_receipt_paths,writer=self.writer,
            relative_root=plan.specification.result_relative_root,repo_root=self.service.project_root,recover=True)
        return self._read_result(plan)

    def read(self,*,directory,allow_partial=False,programme_request_path=None):
        if programme_request_path is not None:raise ValueError('E2 read accepts only its exact original retained plan')
        plan=self._plan(directory)
        result=self.writer.root.resolve(plan.specification.result_relative_root+'/receipt.json',for_write=False)
        if not result.exists() and allow_partial:
            return {'programme':plan.identity.to_document(),'state':'AWAITING_DESCRIPTIVE_RESULT',
                'assigned_roots':len(plan.allocation.roots),'native_contact':'NONE',
                'scientific_qualification':'NOT_ESTABLISHED'}
        return self._read_result(plan)
