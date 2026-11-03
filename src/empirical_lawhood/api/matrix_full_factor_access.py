# SPDX-License-Identifier: MPL-2.0
"""Original-parent access for the ordinary full-history structural child.

Only the current request and original locator evidence bootstrap access. The
original authored packet, plan and successful entry receipt remain independent
custody checks; neither their labels nor a prior permission check grants access.
"""
from dataclasses import dataclass, replace

from empirical_lawhood.adapters.methods.matrix_scheduled_history import full_factor_preparation as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as original_workers
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Evidence
from empirical_lawhood.api.selected_e3_access import SelectedE3OriginalInputAccess, selected_e3_originals
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.prospective_experiment import source_filename


def _pin(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


def development_packet_access(*,artifact_writer,directory,read_access=None):
    """Read exact packet-bound locator metadata under the existing E3 guard."""
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans
    _,draft,_,payloads=load_authored_wave(directory=directory,artifact_writer=artifact_writer,
        lazy_payloads=True,read_access=read_access)
    access=getattr(payloads,'original_input_access',None)
    if type(access) is not SelectedE3OriginalInputAccess:
        raise PermissionError('full factor original DEV packet lacks its authenticated original E3 access')
    access.require_current()
    run,plan,_=_retained_plans(payloads,draft)
    tasks=tuple(row for row in plan.tasks if row.capability.capability_key==original_workers.NAMESPACE+'.entry')
    if len(tasks)!=1:
        raise PermissionError('full factor DEV bootstrap lacks one actual original entry task')
    task,=tasks
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4ExperimentSpecification
    specification=decode_canonical_bytes(payloads['experiment-specification.json'],SelectedE3E4ExperimentSpecification,
        maximum_bytes=len(payloads['experiment-specification.json']))
    raw=payloads[source_filename(specification.evidence)]
    actual=decode_canonical_bytes(raw,SelectedE3E4Evidence,maximum_bytes=len(raw))
    if (actual.canonical_bytes()!=raw or actual.identity!=specification.evidence
            or actual.programme!=specification.programme or actual.produced_input_parents!=access.parents):
        raise PermissionError('full factor DEV bootstrap substitutes its exact original locator evidence')
    selected_e3_originals(actual.upstream_products,read_access)
    access.require_current()
    return access,actual,specification,run,plan,task


def development_original_access(*, artifact_writer, request, evidence=None, read_access=None):
    """Authenticate the actual original packet before any child protected body."""
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    if type(request) is not domain.ScheduledFullFactorDevelopmentRequestV3:
        raise TypeError('full factor DEV bootstrap requires its exact current locator request')
    request.__post_init__()
    original=request.original
    directory=artifact_writer.root.resolve(original.authored_directory,for_write=False)
    access,actual,specification,run,plan,task=development_packet_access(
        artifact_writer=artifact_writer,directory=directory,read_access=read_access)
    if (run.run_plan_id!=original.run_id or _pin(plan,'execution_plan_id')!=original.execution_plan
            or specification.programme!=request.programme or specification.bank!=request.bank
            or evidence is not None and evidence!=actual):
        raise PermissionError('full factor DEV bootstrap substitutes its original run, plan, programme, bank or evidence')
    store=ExternalTaskReceiptStore(artifact_writer)
    receipt_id=original.entry_receipt.object_id
    if not receipt_id.startswith('receipt.'):
        raise PermissionError('full factor original entry lacks its actual scheduler receipt locator')
    selected=store._read_envelope(original.run_id,task.task_id,receipt_id.removeprefix('receipt.'))
    if selected is None:
        raise PermissionError('full factor original entry receipt is missing')
    path,manifest=selected
    access.require_current()
    receipt=store._read_body(original.run_id,task.task_id,receipt_id.removeprefix('receipt.'),path,manifest)
    if (_pin(receipt,'receipt_id')!=original.entry_receipt or receipt.operational_status is not OperationalStatus.SUCCEEDED
            or {row.logical_artifact_id for row in receipt.output_logical_artifacts}!=
                {row.logical_artifact_id for row in task.outputs}):
        raise PermissionError('full factor original entry changes its actual successful receipt or output census')
    logicals={row.logical_artifact_id:row for row in receipt.output_logical_artifacts}
    facts={(manifest.logical,manifest.materialization)}
    facts.update((logicals[row.logical_artifact_id],row) for row in receipt.output_materializations
        if row.logical_artifact_id in logicals)
    def before_member(member):
        if (member.logical,member.materialization) not in facts:
            access.require_member(member)
        access.require_current()
    artifact_writer.verify_manifest(manifest,before_member=before_member)
    access.require_current()
    return access,actual


def bootstrap_selected_input_access(*,specification,selection,read_locator,artifact_writer,read_access=None,selection_path=None):
    if type(specification) is not domain.ScheduledFullFactorDevelopmentSpecification:
        raise TypeError('full factor DEV bootstrap requires its exact scientific leaf')
    request=read_locator('request',specification.request,domain.ScheduledFullFactorDevelopmentRequestV3)
    access,evidence=development_original_access(artifact_writer=artifact_writer,request=request,read_access=read_access)
    rows=tuple(row for row in selection.bindings if row.key=='original-evidence')
    if rows and read_locator('original-evidence',evidence.identity,SelectedE3E4Evidence)!=evidence:
        raise PermissionError('full factor selected input substitutes its actual original evidence')
    return access.require_current


def bootstrap_development_input_access(*,directory,artifact_writer,specification,instance,packet,read_member,read_access=None):
    if type(specification) is not domain.ScheduledFullFactorDevelopmentSpecification:
        raise TypeError('full factor authored bootstrap requires its exact DEV leaf')
    requests=tuple(row for row in instance.sources if row.object_id=='request')
    evidence=tuple(row for row in instance.sources if row.object_id=='original-evidence')
    if len(requests)!=1 or len(evidence)!=1:
        raise PermissionError('full factor authored packet omits its original request or evidence')
    request=read_member(requests[0],domain.ScheduledFullFactorDevelopmentRequestV3)
    if request.identity!=specification.request:
        raise PermissionError('full factor authored packet substitutes its selected original request')
    original=read_member(evidence[0],SelectedE3E4Evidence)
    access,_=development_original_access(artifact_writer=artifact_writer,request=request,evidence=original,read_access=read_access)
    return access


def bootstrap_authoring_input_access(*,preparation,artifact_writer,read_access=None):
    records=dict(preparation.design_records)
    request=records.get('request');evidence=records.get('original-evidence')
    if evidence is None or request is None or request.identity!=preparation.specification_record.request:
        raise PermissionError('full factor authoring omits its exact original request or evidence')
    access,_=development_original_access(artifact_writer=artifact_writer,request=request,evidence=evidence,read_access=read_access)
    return access


def validate_development_read_access(*,payloads,read_access=None,**_):
    access=getattr(payloads,'original_input_access',None)
    if type(access) is not SelectedE3OriginalInputAccess or selected_e3_originals(access.originals,read_access)!=access.selected_originals:
        raise PermissionError('full factor DEV read lacks its exact selected original E3 access')
    access.require_current()


def require_file_access(*,writer,file,access,source):
    """Recheck one actual history array and its exact original batch companion.

    The ordinary reader has authenticated this source's original receipt
    locators. Their immutable publication facts do not grant current access.
    """
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_records import (
        ScheduledFullFactorSource, ScheduledFullFactorProtectedProduct,
    )
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_bindings import array_logical
    from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentFile

    if type(source) is not ScheduledFullFactorSource or type(file) is not PreparedExperimentFile:
        raise TypeError('full factor alias requires its exact actual source and FILE handle')
    source.__post_init__();file.__post_init__()
    access.require_current()
    if (source.history is None or source.full_arrays is None
            or source.produced_input_parents!=access.parents):
        raise PermissionError('full factor alias lacks its actual history and original parent census')
    artifact=source.full_arrays.array_artifact
    if (file.identity!=replace(artifact,artifact_id=array_logical(source))
            or file.maximum_bytes!=artifact.size_bytes):
        raise PermissionError('full factor alias changes its exact original array operand')
    histories=tuple(row for row in source.original_products if row.record==source.history)
    if len(histories)!=1:
        raise PermissionError('full factor alias lacks its unique original history producer')
    history,=histories
    protected=type(history) is ScheduledFullFactorProtectedProduct
    if protected:
        from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings
        task=selected_e4_native_bindings.local_node(source.root_id,'continue')
        run_id=history.wave.run_id
    else:
        task=original_workers.local_node(source.root_id,'continue')
        run_id=history.run_id
    if history.task_id!=task:
        raise PermissionError('full factor alias substitutes its actual history producer task')
    publication=history.publication
    relative=file.path.relative_to(writer.root.contract.canonical_path).as_posix()
    manifest=writer.read_manifest(relative)
    if (manifest.logical.logical_artifact_id,manifest.logical.payload_schema,manifest.logical.profile,manifest.logical.media_type,
            manifest.logical.content_sha256,manifest.materialization.physical_sha256,
            manifest.materialization.size_bytes,manifest.materialization.storage_root_id)!=(
                artifact.artifact_id,artifact.payload_schema,ArtifactProfile.MATRIX_ARRAY_NPZ,artifact.media_type,artifact.sha256,artifact.sha256,
                artifact.size_bytes,writer.root.contract.storage_root_id):
        raise PermissionError('full factor alias changes its actual source publication bytes')
    access.require_current()
    companion=writer.read_manifest(publication.materialization.relative_path)
    if ((companion.logical,companion.materialization)!=(publication.logical,publication.materialization)
            or companion.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or companion.logical.media_type!='application/json'
            or companion.materialization.physical_sha256!=source.history.object_fingerprint
            or companion.publication is None or companion.publication!=manifest.publication
            or companion.publication.publication_scope.publication_scope_id!='task-output-scope.'+run_id+'.'+task
            or companion.publication.publication_scope.relative_root!='runs/'+run_id):
        raise PermissionError('full factor alias substitutes its exact original history companion or batch')
    # Pin the actual current sidecar to the descriptor already read from the
    # successful original producer; full batch verification below checks bodies.
    writer.verify(publication.manifest_materialization)
    access.require_current()
    facts=((manifest.logical,manifest.materialization),(companion.logical,companion.materialization))
    if facts[0]==facts[1]:
        raise PermissionError('full factor alias aliases its array and history companion')
    def before_member(member):
        if (member.logical,member.materialization) not in facts:
            access.require_member(member)
        access.require_current()
    writer.verify_manifest(manifest,before_member=before_member)
    access.require_current()
    return manifest


@dataclass(frozen=True,slots=True)
class ProtectedFullFactorInputAccess:
    """Current original-wave access; immutable parents are not an access grant."""
    writer:object
    waves:tuple
    declaration:object
    current_access:object

    @property
    def parents(self):return self.declaration.produced_input_parents

    def require_current(self,*,artifact_writer=None):
        from empirical_lawhood.api.selected_e4_access import require_current_e4_access
        from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane,_ScopedArtifactPlane
        writer=self.writer if artifact_writer is None else artifact_writer
        if writer.root.contract!=self.writer.root.contract:
            raise PermissionError('full factor access changes its actual guarded original root')
        if type(writer) is _ScopedArtifactPlane:
            writer=ExternalArtifactPlane(writer.root,writer.validators,writer.semantic_validations,custody_limits=writer.custody_limits, artifact_verification='strict')
        require_current_e4_access(writer=writer,originals=self.waves,current_access=self.current_access)

    def record_parents(self,record):
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_record_parents
        return produced_record_parents(record,self.parents)

    def require_member(self,manifest):
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
        from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
        from empirical_lawhood.runtime.artifacts import ArtifactManifest
        if type(manifest) is not ArtifactManifest:
            raise TypeError('full factor access requires the exact authenticated member')
        logical=manifest.logical
        selected=tuple(value for value in logical.lineage_parents if value.identity in {row.identity for row in self.parents})
        if selected:
            if selected!=self.parents or (logical.outcome_access,logical.visibility_ceiling)!=produced_access(
                    declared_access=OutcomeAccess.EVALUATION_REVEALED,declared_visibility=VisibilityCeiling.OUTCOME_VISIBLE,
                    parents=logical.lineage_parents):
                raise PermissionError('full factor member changes its exact original parent census or inherited custody')
        elif (logical.outcome_access,logical.visibility_ceiling) not in (
                (OutcomeAccess.DEVELOPMENT_VISIBLE,VisibilityCeiling.DEVELOPMENT_ONLY),
                (OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE)):
            raise PermissionError('full factor protected member lacks its actual original ancestry')
        self.require_current()


def protected_original_access(*,artifact_writer,request,read_access=None):
    from empirical_lawhood.api.matrix_full_factor_custody import _protected_declaration
    from empirical_lawhood.api.selected_e4_access import require_current_e4_access
    if type(request) is not domain.ScheduledFullFactorProtectedRequestV4:
        raise TypeError('full factor protected bootstrap requires its exact current locator request')
    request.__post_init__()
    require_current_e4_access(writer=artifact_writer,originals=request.waves,current_access=read_access)
    declaration=_protected_declaration(writer=artifact_writer,programme=None,declaration=request.declaration,
        waves=request.waves,current_access=read_access)
    if declaration.programme.identity!=request.programme or declaration.bank!=request.bank:
        raise PermissionError('full factor protected bootstrap changes its actual original programme or bank')
    access=ProtectedFullFactorInputAccess(artifact_writer,request.waves,declaration,read_access)
    access.require_current()
    return access


def bootstrap_protected_selected_input_access(*,specification,selection,read_locator,artifact_writer,read_access=None,selection_path=None):
    if type(specification) is not domain.ScheduledFullFactorProtectedSpecification:
        raise TypeError('full factor protected bootstrap requires its exact scientific leaf')
    request=read_locator('request',specification.request,domain.ScheduledFullFactorProtectedRequestV4)
    return protected_original_access(artifact_writer=artifact_writer,request=request,read_access=read_access).require_current


def bootstrap_protected_development_input_access(*,directory,artifact_writer,specification,instance,packet,read_member,read_access=None):
    if type(specification) is not domain.ScheduledFullFactorProtectedSpecification:
        raise TypeError('full factor protected packet requires its exact scientific leaf')
    requests=tuple(row for row in instance.sources if row.object_id=='request')
    if len(requests)!=1:
        raise PermissionError('full factor protected packet omits its exact original request')
    request=read_member(requests[0],domain.ScheduledFullFactorProtectedRequestV4)
    if request.identity!=specification.request:
        raise PermissionError('full factor protected packet substitutes its selected original request')
    return protected_original_access(artifact_writer=artifact_writer,request=request,read_access=read_access)


def bootstrap_protected_authoring_input_access(*,preparation,artifact_writer,read_access=None):
    request=dict(preparation.design_records).get('request')
    if request is None or request.identity!=preparation.specification_record.request:
        raise PermissionError('full factor protected authoring omits its exact original request')
    return protected_original_access(artifact_writer=artifact_writer,request=request,read_access=read_access)
