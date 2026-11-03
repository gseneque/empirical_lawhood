# SPDX-License-Identifier: MPL-2.0
"""Actual original reader handoff for additive full-history structural analysis.

No synthetic receipt is supplied for an observed failed or unentered case.
The protected reader calls this consumer only after current issue/reveal and
complete actual original wave receipt authentication.
"""
from dataclasses import replace

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as dev
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as dev_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as protected
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as protected_owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseProgramme
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import ScheduledFullFactorScope
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_records import ScheduledFullFactorProtectedProduct
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_science import source_from_original
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_bindings import array_input,array_logical
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from .matrix_retained_replay import bounded_e4_replay_source, replay_weight, map_reconstructions, replay_e4_functional
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
from empirical_lawhood.kernel.decoding import decode_canonical_bytes_with_identity
from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentFile
from .matrix_read_indexes import unique_index


def _pin(record,field):return ObjectIdentity.from_record(getattr(record,field),record)


def _output(writer,products,plan,task_id,output_id,*,original_input_access=None,publication_facts=None,task_index=None):
    receipt=products['receipts'].get(task_id)
    if receipt is None:return None
    if task_index is None:
        task_index=unique_index(plan.tasks,lambda row:row.task_id,label='execution task')
    task=task_index.get(task_id)
    if task is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
        raise PermissionError('full factor original output lacks its exact successful ordinary task receipt')
    outputs=tuple(row for row in task.outputs if row.output_id==task_id+'.'+output_id)
    if len(outputs)!=1:raise PermissionError('full factor original task lacks its exact output contract')
    output,=outputs
    logicals=tuple(row for row in receipt.output_logical_artifacts if row.logical_artifact_id==output.logical_artifact_id)
    manifest=products['outputs'].get(output.logical_artifact_id)
    if (len(logicals)!=1 or manifest is None or manifest.logical!=logicals[0]
            or (manifest.logical.payload_schema,manifest.logical.media_type,manifest.logical.profile)!=(output.payload_schema,output.media_type,output.profile)):
        raise PermissionError('full factor original output substitutes actual ordinary receipt/publication bytes')
    def current():
        if original_input_access is not None:original_input_access.require_current()
    facts=(frozenset((row.logical,row.materialization) for row in products['outputs'].values())
        if publication_facts is None else publication_facts)
    def before_member(member):
        if original_input_access is not None and (member.logical,member.materialization) not in facts:
            original_input_access.require_member(member)
        current()
    current()
    actual=writer.read_manifest(manifest.materialization.relative_path)
    if (actual.logical,actual.materialization)!=(manifest.logical,manifest.materialization):
        raise PermissionError('full factor original publication changes its authenticated receipt output')
    writer.verify_manifest(actual,before_member=before_member)
    relative=actual.materialization.relative_path+'.manifest.json'
    raw=read_bounded_bytes(writer.root.resolve(relative,for_write=False),maximum_bytes=writer.custody_limits.manifest_bytes)
    sidecar=writer._manifest_materialization(logical_artifact_id=actual.logical.logical_artifact_id,relative_path=relative,payload=raw)
    writer.verify(sidecar)
    publication=ArtifactWriteResult(actual.logical,actual.materialization,sidecar,False)
    current()
    return receipt,publication


def _record(writer,products,plan,task_id,kind,field,*,output_id="product",original_input_access=None,publication_facts=None,task_index=None):
    actual=_output(writer,products,plan,task_id,output_id,original_input_access=original_input_access,publication_facts=publication_facts,task_index=task_index)
    if actual is None:return None,None
    receipt,publication=actual
    if publication.logical.payload_schema!=kind.SCHEMA:
        raise PermissionError('full factor original product substitutes actual installed record schema')
    if original_input_access is not None:original_input_access.require_current()
    raw=read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path,for_write=False),maximum_bytes=publication.materialization.size_bytes)
    decoded=decode_canonical_bytes_with_identity(raw,kind,maximum_bytes=publication.materialization.size_bytes,
        expected_sha256=publication.logical.content_sha256)
    value=decoded.record
    if (decoded.size_bytes!=publication.materialization.size_bytes
            or decoded.content_sha256!=publication.materialization.physical_sha256
            or _pin(value,field).object_fingerprint!=decoded.content_sha256):
        raise PermissionError('full factor original product changes canonical bytes')
    if original_input_access is not None:original_input_access.require_current()
    return value,(receipt,publication)



def _protected_declaration(*,writer,programme,declaration,waves,current_access=None):
    """Resolve a blind declaration pin only after current original grants.

    The declaration body stays in the revealed Scope FILE. Neither the copied
    request nor the blind follow-up companion/config carries its DEV/CAL values.
    The ordinary original reader below still verifies every complete wave.
    """
    from empirical_lawhood.api.current_result_custody import authenticate_current_execution_plan
    from empirical_lawhood.api.matrix_selected_runtime import _published_input
    from empirical_lawhood.api.recursive_qualified_parents import _actual_package,_replay_parent_authority
    if (type(declaration) is not ObjectIdentity or
            (declaration.object_schema,declaration.object_version)!=(protected.SelectedE4NativeProgrammeDeclaration.SCHEMA,protected.SelectedE4NativeProgrammeDeclaration.VERSION)
            or type(waves) is not tuple or not waves or any(type(row) is not protected.SelectedE4WaveLocator for row in waves)
            or programme is not None and tuple(row.wave_id for row in waves)!=tuple(row.wave_id for row in programme.waves)):
        raise ValueError('full factor protected declaration requires its exact pin and complete original wave census')
    declaration.__post_init__()
    for row in waves:row.__post_init__()
    locator=waves[0]
    package=_actual_package(writer,locator.run_id)
    if _pin(package,'package_id')!=locator.package:
        raise PermissionError('full factor declaration changes the actual original issued package')
    from empirical_lawhood.api.selected_e4_access import selected_e4_authority_binding
    issued,_=_replay_parent_authority(selected_e4_authority_binding(locator,current_access),package,writer)
    plan=authenticate_current_execution_plan(package=package,issued=issued,run_id=locator.run_id,writer=writer)
    if _pin(plan,'execution_plan_id')!=locator.execution_plan:
        raise PermissionError('full factor declaration changes the actual original execution plan')
    tasks=tuple(row for row in plan.tasks if row.capability.capability_key==protected_owner.NAMESPACE+'.entry')
    if len(tasks)!=1:raise PermissionError('full factor declaration lacks one actual original source-entry task')
    task,=tasks
    configs=tuple(row for row in task.external_inputs if row.logical_artifact_id==task.capability.config.artifact_id)
    if len(configs)!=1:raise PermissionError('full factor declaration lacks its exact original source-entry configuration')
    from empirical_lawhood.api.selected_e4_access import require_current_e4_access
    require_current_e4_access(writer=writer,originals=waves,current_access=current_access)
    entry=_published_input(writer,locator.run_id,configs[0],protected_owner.SelectedE4ProtectedEntryConfig)
    actual=entry.declaration
    if (type(actual) is not protected.SelectedE4NativeProgrammeDeclaration or actual.identity!=declaration
            or programme is not None and (actual.programme!=programme or actual.bank!=programme.bank)
            or tuple(row.wave_id for row in waves)!=tuple(row.wave_id for row in actual.programme.waves)
            or entry.wave_id!=locator.wave_id):
        raise PermissionError('full factor declaration substitutes the actual selected original programme/bank/declaration')
    actual.__post_init__()
    require_current_e4_access(writer=writer,originals=waves,current_access=current_access)
    return actual

def derive_original_full_factor_scope(*,writer,programme,bank,record_id,codecs,development=None,declaration=None,waves=(),
        _consume_functional=None,_consume_programme_result=None,_development_directory=None,current_access=None,
        _consume_original_access=None,_secondary_target=None,_secondary_readout=None,_consume_mechanism=None):
    """Read real original complete terminal censuses and derive immutable values.

    This is a data projection, never authority. Every access goes through the
    original owner. Returned files are explicit new input aliases over exact
    original bytes; original sealed metadata and record identities stay intact.
    """
    from empirical_lawhood.api.matrix_selected_e3_e4_read import read_selected_e3_e4_development
    from empirical_lawhood.api.selected_e4_native_read import read_selected_e4_programme
    if _consume_functional is not None and not callable(_consume_functional):
        raise TypeError('full factor functional consumer must be callable')
    if _consume_mechanism is not None and (not callable(_consume_mechanism) or _consume_functional is None):
        raise TypeError('mechanism consumer requires the original full functional read')
    if _consume_functional is not None and (_secondary_target is None or _secondary_readout is None):
        raise ValueError('dense E4 consumer requires its actual selected target and original publication')
    if _secondary_readout is not None:
        _secondary_readout.__post_init__()
        if _secondary_target is not None:
            _secondary_readout.validate_target(_secondary_target)
    if _consume_programme_result is not None and not callable(_consume_programme_result):
        raise TypeError('full factor original programme observer must be callable')
    programme.__post_init__()
    if bank is not None:bank.__post_init__()
    is_protected=type(programme) is SelectedE4PhaseProgramme
    if is_protected and type(declaration) is ObjectIdentity:
        declaration=_protected_declaration(writer=writer,programme=programme,declaration=declaration,waves=waves,
            current_access=current_access)
    if bank is not None and programme.bank!=bank.identity:raise PermissionError('full factor original bank differs from selected programme')
    if (is_protected and (development is not None or _development_directory is not None or declaration is None or declaration.programme!=programme
            or declaration.bank!=programme.bank or tuple(row.wave_id for row in waves)!=tuple(row.wave_id for row in programme.waves))
            or not is_protected and ((development is None)==(_development_directory is None)
                or development is not None and development.allow_partial or declaration is not None or waves)):
        raise ValueError('full factor follow-up requires complete exact DEV or protected original terminal selections')
    cases={};sources={};files={}
    from empirical_lawhood.api.matrix_full_factor_access import ProtectedFullFactorInputAccess
    if _consume_original_access is not None and not callable(_consume_original_access):
        raise TypeError('full factor original access consumer must be callable')
    access=None
    if is_protected:
        access=ProtectedFullFactorInputAccess(writer,waves,declaration,current_access)
        access.require_current()
        if _consume_original_access is not None:
            _consume_original_access(access,None)

    def validate_development(*,packet,draft,run,plan):
        from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
        entries=tuple(row for row in draft.operations if row.selection.capability_key==dev_owner.NAMESPACE+'.entry')
        if len(entries)!=1 or draft.development_study is None or draft.prospective_draft is not None:
            raise PermissionError('full factor original access requires its truthful original DEV entry')
        operation,=entries
        declaration=next(row for row in dev_owner.operation_declarations() if row.capability_key==operation.selection.capability_key)
        entry=decode_recursive_config_input(operation,declaration.registration()).record
        if (type(entry) is not dev_owner.SelectedE3E4EntryConfig
                or entry.programme!=programme or entry.bank.identity!=programme.bank):
            raise PermissionError('full factor original access substitutes its actual selected programme or bank')

    def consume(*,writer,products,plan,entry,bank:object,cases:tuple,locator=None,draft=None,run_id=None,
            original_input_access=None,original_evidence=None):
        nonlocal development,access
        if not is_protected:
            from empirical_lawhood.api.selected_e3_access import SelectedE3OriginalInputAccess
            if (type(original_input_access) is not SelectedE3OriginalInputAccess
                    or type(original_evidence) is not dev.SelectedE3E4Evidence
                    or original_evidence.identity!=entry.evidence
                    or original_evidence.programme!=programme.identity
                    or original_evidence.produced_input_parents!=original_input_access.parents):
                raise PermissionError('full factor original reader lacks its actual original access or packet evidence')
            access=original_input_access
        access.require_current()
        if _secondary_readout is not None and entry.secondary_readout != _secondary_readout:
            raise PermissionError('full factor original reader replaces the target sealed before native entry')
        if _secondary_target is not None:
            from .matrix_full_factor_secondary import authenticate_e4_secondary_target
            if authenticate_e4_secondary_target(writer=writer, selection=entry.secondary_readout, bank=bank) != _secondary_target:
                raise PermissionError('full factor original reader changes the declared dense target')
        if (entry.declaration.produced_input_parents if is_protected else entry.produced_input_parents)!=access.parents:
            raise PermissionError('full factor original entry changes its exact authenticated produced-parent census')
        if not is_protected and _development_directory is not None:
            from pathlib import Path
            from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_method_bindings import SelectedE4DevelopmentAcquisition
            receipt=products['receipts'].get(dev_owner.global_node(programme,'entry'))
            if receipt is None:raise PermissionError('ordinary E4 structure lacks its actual original source-entry receipt')
            relative=Path(_development_directory).resolve(strict=True).relative_to(writer.root.contract.canonical_path).as_posix()
            development=SelectedE4DevelopmentAcquisition('acquisition.'+plan.fingerprint(),relative,run_id,
                _pin(plan,'execution_plan_id'),_pin(receipt,'receipt_id'),False)
        if entry.programme!=programme or bank.identity!=programme.bank:
            raise PermissionError('full factor original reader changes actual programme or bank')
        if is_protected:
            if locator not in waves or entry.declaration!=declaration or entry.wave_id!=locator.wave_id or run_id!=locator.run_id:
                raise PermissionError('full factor original reader changes actual protected declaration/wave')
        else:
            if run_id!=development.run_id:
                raise PermissionError('full factor original reader changes actual DEV run')
            if (_pin(plan,'execution_plan_id')!=development.execution_plan or draft is None
                    or draft.development_study is None or draft.prospective_draft is not None):
                raise PermissionError('full factor original reader substitutes actual DEV plan/lifecycle')
            entry_task=dev_owner.global_node(programme,'entry')
            entry_receipt=products['receipts'].get(entry_task)
            if entry_receipt is None or _pin(entry_receipt,'receipt_id')!=development.entry_receipt:
                raise PermissionError('full factor original DEV entry receipt is absent or substituted')
        if not is_protected and _consume_original_access is not None:
            _consume_original_access(access,original_evidence)
        publication_facts=frozenset((row.logical,row.materialization) for row in products['outputs'].values())
        native_kind=protected.SelectedE4ProtectedNativeSource if is_protected else dev.SelectedE3E4NativeSource
        owner=protected_owner if is_protected else dev_owner
        kinds=(('project',protected.SelectedE4ProtectedCausalPrefix if is_protected else dev.SelectedE3E4CausalPrefix,'prefix_id'),
            ('continue',protected.SelectedE4ProtectedFullHistory if is_protected else dev.SelectedE3E4FullHistory,'history_id'),
            ('full-numerical',protected.SelectedE4ProtectedNumericalAssessment if is_protected else dev.SelectedE3E4NumericalAssessment,'assessment_id'))
        index=bank.source_index()
        task_index=unique_index(plan.tasks,lambda row:row.task_id,label='execution task')
        descriptors=unique_index(bank.sources,lambda row:row.root_id,label='source descriptor')
        protocols=unique_index(bank.response_selection.protocols,
            lambda row:row.public_source.root.root_id,label='response protocol')
        panels_by_group=unique_index(bank.response_selection.panels,lambda row:row[0],label='response panel')
        def reconstruction_inputs():
            for case in cases:
                descriptor=descriptors[case.root_id]
                native=native_kind.from_bank(programme,bank,descriptor,index=index)
                values={};locators=[]
                for phase,kind,field in kinds:
                    task=owner.local_node(case.root_id,phase)
                    value,custody=_record(writer,products,plan,task,kind,field,original_input_access=access,publication_facts=publication_facts,task_index=task_index)
                    values[phase]=value
                    if custody is None:continue
                    receipt,publication=custody;pin=_pin(value,field)
                    expected_access=(OutcomeAccess.OUTCOME_BLIND if phase=='project' and is_protected else
                        OutcomeAccess.EVALUATION_SEALED if is_protected else OutcomeAccess.DEVELOPMENT_VISIBLE)
                    expected_visibility=VisibilityCeiling.PROSPECTIVE if is_protected else VisibilityCeiling.DEVELOPMENT_ONLY
                    expected_access,expected_visibility=produced_access(declared_access=expected_access,
                        declared_visibility=expected_visibility,parents=access.parents)
                    if (publication.logical.outcome_access,publication.logical.visibility_ceiling)!=(expected_access,expected_visibility):
                        raise PermissionError('full factor original publication changes actual blind/sealed/DEV standing')
                    locators.append(ScheduledFullFactorProtectedProduct(pin,locator,task,_pin(receipt,'receipt_id'),publication)
                        if is_protected else protected.SelectedE4DevelopmentProduct(pin,development.authored_directory,
                            development.run_id,development.execution_plan,task,_pin(receipt,'receipt_id'),publication))
                selected=source_from_original(record_id='full-factor.'+case.root_id,source=native,
                    criterion=bank.forecast_design.criterion_record,case=case,original_products=tuple(locators),
                    produced_input_parents=access.parents,causal=values['project'],history=values['continue'],numerical=values['full-numerical'])
                if case.root_id in sources:raise PermissionError('full factor original wave census duplicates a case')
                # Observational cases may have no producing receipt. They are kept
                # verbatim from the owner; only genuinely present outputs above get locators.
                sources[case.root_id]=selected
                if _consume_functional is not None:
                    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
                        ScheduledResponseScore, ScheduledE4DenseMechanicalForecast, ScheduledE4DenseResponseScore,
                    )
                    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_secondary_readout import dense_e4_functional_rows
                    from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
                    node=lambda phase:owner.local_node(case.root_id,phase)
                    def record(phase,kind,field,output_id='product'):
                        return _record(writer,products,plan,node(phase),kind,field,output_id=output_id,
                            original_input_access=access,publication_facts=publication_facts,task_index=task_index)[0]
                    score=record('response-score',ScheduledResponseScore,'score_id')
                    dense_score=record('response-score',ScheduledE4DenseResponseScore,'score_id','dense-score')
                    def array_bytes(phase,output_id,operand):
                        actual=_output(writer,products,plan,node(phase),output_id,
                            original_input_access=access,publication_facts=publication_facts,task_index=task_index)
                        if actual is None:
                            raise PermissionError('dense E4 replay lacks a required winning array output')
                        _,publication=actual
                        artifact=operand.array_artifact
                        if (publication.logical.logical_artifact_id,publication.logical.payload_schema,
                                publication.logical.content_sha256,publication.logical.media_type,
                                publication.materialization.physical_sha256,publication.materialization.size_bytes)!=(
                                artifact.artifact_id,artifact.payload_schema,artifact.sha256,artifact.media_type,
                                artifact.sha256,artifact.size_bytes):
                            raise PermissionError('dense E4 replay substitutes a named winning scientific archive')
                        access.require_current()
                        raw=read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path,for_write=False),
                            maximum_bytes=artifact.size_bytes)
                        access.require_current()
                        return raw
                    protocol=protocols[case.root_id]
                    panels=panels_by_group[case.group_id][1]
                    physical=dense=responses=causal=template_raw=causal_raw=original_raw=dense_raw=response_raw=None
                    witness=diagnostic_raw=None
                    if score is not None:
                        physical=record('mechanical',protected.SelectedE4ProtectedMechanicalForecast if is_protected
                            else dev.SelectedE3E4MechanicalForecast,'forecast_id')
                        dense=record('mechanical',ScheduledE4DenseMechanicalForecast,'forecast_id','dense-product')
                        responses=record('responses',protected.SelectedE4ProtectedResponses if is_protected
                            else dev.SelectedE3E4Responses,'response_id')
                        causal=values['project']
                        if any(value is None for value in (dense_score,physical,dense,responses,causal)):
                            raise PermissionError('completed E4 scoring lacks its actual dense or original producer products')
                        causal_raw=array_bytes('project','arrays',causal.arrays)
                        original_raw=array_bytes('mechanical','arrays',physical.arrays)
                        dense_raw=array_bytes('mechanical','dense-arrays',dense.arrays)
                        response_raw=array_bytes('responses','arrays',responses.arrays)
                        artifact=protocol.templates.array_artifact
                        templates=tuple(row for row in bank.response_selection.template_publications
                            if (row.logical.logical_artifact_id,row.logical.payload_schema,row.logical.content_sha256,
                                row.logical.media_type,row.materialization.physical_sha256,row.materialization.size_bytes)==(
                                artifact.artifact_id,artifact.payload_schema,artifact.sha256,artifact.media_type,
                                artifact.sha256,artifact.size_bytes))
                        if len(templates)!=1:
                            raise PermissionError('dense E4 replay lacks its exact original blind template publication')
                        access.require_current()
                        authenticate_published_materialization(writer,templates[0])
                        template_raw=read_bounded_bytes(writer.root.resolve(templates[0].materialization.relative_path,for_write=False),
                            maximum_bytes=artifact.size_bytes)
                        access.require_current()
                    row=dense_e4_functional_rows(bank,case,score,dense_score=dense_score,
                        target=_secondary_target,secondary=_secondary_readout)
                    account=record('account',protected.SelectedE4ProtectedAccountSeal if is_protected
                        else dev.SelectedE3E4AccountSeal,'record_id')
                    if account is not None and account.feature.physical_forecast is not None:
                        protocol=protocols[case.root_id]
                        causal=values['project']
                        physical=record('mechanical',protected.SelectedE4ProtectedMechanicalForecast if is_protected
                            else dev.SelectedE3E4MechanicalForecast,'forecast_id')
                        witness=record('measure',protected.SelectedE4ProtectedWitness if is_protected
                            else dev.SelectedE3E4Witness,'product_id')
                        if any(value is None for value in (causal,physical,witness)):
                            raise PermissionError('matched E4 read omits the original sealed causal/mechanical feature evidence')
                        if score is None:
                            causal_raw=array_bytes('project','arrays',causal.arrays)
                            original_raw=array_bytes('mechanical','arrays',physical.arrays)
                        diagnostic_raw=array_bytes('measure','arrays',witness.arrays)
                    from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import prediction_case
                    row=replace(row,prediction=prediction_case(bank,case,row,account))
                    work=dict(row=row,case=case,is_protected=is_protected,protocol=protocol,source=bounded_e4_replay_source(native),
                        panels=panels,target=_secondary_target,secondary=_secondary_readout,score=score,dense_score=dense_score,
                        physical=physical,dense=dense,responses=responses,causal=causal,template_raw=template_raw,
                        causal_raw=causal_raw,original_raw=original_raw,dense_raw=dense_raw,response_raw=response_raw,
                        account=account,witness=witness,diagnostic_raw=diagnostic_raw,design=bank.forecast_design,
                        include_mechanism=_consume_mechanism is not None and getattr(bank.forecast_design.package.specification,'is_curve_primary',False),
                        root_id=case.root_id,group_id=case.group_id,source_identity=case.source)
                    operands=tuple((raw,manifest) for raw,manifest in (
                        (template_raw,protocol.templates),(causal_raw,None if causal is None else causal.arrays),
                        (original_raw,None if physical is None else physical.arrays),(dense_raw,None if dense is None else dense.arrays),
                        (response_raw,None if responses is None else responses.arrays),(diagnostic_raw,None if witness is None else witness.arrays))
                        if raw is not None)
                if selected.history is not None:
                    receipt,publication=_output(writer,products,plan,owner.local_node(case.root_id,'continue'),'arrays',original_input_access=access,publication_facts=publication_facts,task_index=task_index)
                    artifact=selected.full_arrays.array_artifact
                    if (publication.logical.logical_artifact_id,publication.logical.payload_schema,publication.logical.content_sha256,
                            publication.logical.media_type,publication.materialization.size_bytes)!=(artifact.artifact_id,
                            MATRIX_ARRAY_SCHEMA,artifact.sha256,artifact.media_type,artifact.size_bytes):
                        raise PermissionError('full factor original array output differs from exact native full-history operand')
                    expected_access=OutcomeAccess.EVALUATION_SEALED if is_protected else OutcomeAccess.DEVELOPMENT_VISIBLE
                    expected_pair=produced_access(declared_access=expected_access,
                        declared_visibility=VisibilityCeiling.PROSPECTIVE if is_protected else VisibilityCeiling.DEVELOPMENT_ONLY,parents=access.parents)
                    if (publication.logical.outcome_access,publication.logical.visibility_ceiling)!=expected_pair:
                        raise PermissionError('full factor original native array access is relabelled')
                    original_path=writer.root.resolve(publication.materialization.relative_path,for_write=False)
                    alias=replace(artifact,artifact_id=array_logical(selected))
                    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
                    formats=tuple(row for row in MATRIX_STORAGE_CODECS if (row.payload_schema,row.media_type)==(artifact.payload_schema,artifact.media_type))
                    if len(formats)!=1:raise PermissionError('full factor original arrays lack one exact installed codec edition')
                    files[array_input(selected)]=PreparedExperimentFile(alias,formats[0].record_version,original_path,artifact.size_bytes)
                if _consume_functional is not None:
                    yield replay_weight(records=(case,protocol,work['source'].transport,work['source'].provenance,*panels,_secondary_target,
                        _secondary_readout,score,dense_score,physical,dense,responses,causal,account,witness,bank.forecast_design),
                        archives=operands),work
        for row,mechanism in map_reconstructions(writer,replay_e4_functional,reconstruction_inputs()):
            access.require_current()
            _consume_functional(row)
            if mechanism is not None:_consume_mechanism(mechanism)
        access.require_current()
        return tuple(cases)

    def observed(**kwargs):
        rows=consume(**kwargs)
        for row in rows:
            if row.root_id in cases:raise PermissionError('full factor original census repeats assigned case')
            cases[row.root_id]=row

    if is_protected:
        observations,report=read_selected_e4_programme(writer=writer,declaration=declaration,locators=waves,
            codecs=codecs,_consume_original=observed,current_access=current_access)
    else:
        directory=(_development_directory if _development_directory is not None else
            writer.root.resolve(development.authored_directory,for_write=False))
        report=read_selected_e3_e4_development(directory=directory,artifact_writer=writer,
            allow_partial=False,_consume_original=observed,_validate_authored=validate_development,read_access=current_access)
        observations=()
    expected=tuple(row.root_id for row in programme.cases)
    if set(cases)!=set(expected) or set(sources)!=set(expected):
        raise PermissionError('full factor original readers do not establish complete assigned terminal census')
    scope=ScheduledFullFactorScope(record_id,programme,tuple(cases[root] for root in expected),
        tuple(sources[root] for root in expected),development,declaration,waves)
    if _consume_programme_result is not None:
        _consume_programme_result(observations=observations,report=report)
    access.require_current()
    return scope,tuple(sorted(files.items()))


def authenticate_original_full_factor_scope(*,writer,scope,bank,codecs,current_access=None,
        _secondary_target=None,_secondary_readout=None):
    actual,files=derive_original_full_factor_scope(writer=writer,programme=scope.programme,bank=bank,
        record_id=scope.record_id,codecs=codecs,development=scope.development,declaration=scope.declaration,waves=scope.waves,
        current_access=current_access,_secondary_target=_secondary_target,_secondary_readout=_secondary_readout)
    if actual!=scope:raise PermissionError('full factor follow-up changes actual original case values or source custody')
    return files


def authenticate_original_full_factor_reference(*,writer,reference,codecs,_consume_functional=None,
        _consume_programme_result=None,current_access=None,_secondary_target=None,_secondary_readout=None,_consume_mechanism=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import scope_reference
    scope,files=derive_original_full_factor_scope(writer=writer,programme=reference.programme,bank=None,
        record_id=reference.scope.object_id,codecs=codecs,development=reference.development,
        declaration=reference.declaration,waves=reference.waves,_consume_functional=_consume_functional,
        _secondary_target=_secondary_target,_secondary_readout=_secondary_readout,_consume_mechanism=_consume_mechanism,
        _consume_programme_result=_consume_programme_result,current_access=current_access)
    if scope_reference(scope)!=reference:raise PermissionError('full factor reference differs from freshly authenticated original observations')
    return scope,files
