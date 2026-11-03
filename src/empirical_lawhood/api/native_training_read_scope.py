# SPDX-License-Identifier: MPL-2.0
"""Exact original TRAIN membership, separate from scientific array replay.

The scope reads canonical control records only while constructing its census.
It never enters work, recovers an attempt, qualifies a source or verifies an
array. Actual downstream readers retain their full body/replay checks and fresh
original-parent permission before every use of these immutable member facts.
"""
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent, ArtifactManifest, ArtifactProfile, CanonicalTaskReceipt,
    artifact_publication_member, lineage_parent_sort_key,
)

_DEV = OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY
_BLIND = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE


@dataclass(frozen=True, slots=True)
class NativeTrainingReadScope:
    """Finite immutable membership facts, never an access/array verdict."""
    locator: object
    _writer: object
    _members: Mapping

    def __post_init__(self):
        self._writer.require_active_verification_scope()
        values=dict(self._members)
        if any(type(value) is not ArtifactManifest or key!=value.materialization.relative_path
                for key,value in values.items()):
            raise TypeError('native TRAIN scope requires exact immutable member bindings')
        object.__setattr__(self,'_members',MappingProxyType(values))

    def require_member(self, manifest):
        self._writer.require_active_verification_scope()
        if type(manifest) is not ArtifactManifest:
            raise TypeError('native TRAIN membership requires its actual manifest')
        expected = self._members.get(manifest.materialization.relative_path)
        if expected != manifest:
            raise PermissionError('member is outside the exact original native TRAIN closure')
        if self._writer.read_manifest(manifest.materialization.relative_path) != manifest:
            raise PermissionError('native TRAIN member changed after metadata authentication')
        self._writer.require_active_verification_scope()


class _Metadata:
    """Invocation-local construction state; only closed typed roles read bodies."""
    def __init__(self, writer):
        self.writer = writer
        self.members = {}
        self.final_censuses = []

    def add(self, manifest, *, pair=None, expected=None, width=None, parents=None):
        if type(manifest) is not ArtifactManifest:
            raise TypeError('native TRAIN metadata needs actual publication custody')
        logical, physical, publication = manifest.logical, manifest.materialization, manifest.publication
        if (physical.storage_root_id != self.writer.root.contract.storage_root_id
                or physical.logical_artifact_id != logical.logical_artifact_id
                or physical.physical_sha256 != logical.content_sha256
                or type(physical.size_bytes) is not int or physical.size_bytes < 1
                or physical.compression != 'none' or physical.partition_selector is not None
                or publication is None or publication.members.count(artifact_publication_member(logical, physical)) != 1
                or self.writer.read_manifest(physical.relative_path) != manifest
                or pair is not None and (logical.outcome_access, logical.visibility_ceiling) != pair
                or parents is not None and logical.lineage_parents != parents
                or width is not None and physical.size_bytes != width
                or expected is not None and (logical.payload_schema, logical.content_sha256) != (
                    expected.object_schema, expected.object_fingerprint)):
            raise PermissionError('native TRAIN member substitutes exact published bytes, role or lineage')
        previous = self.members.setdefault(physical.relative_path, manifest)
        if previous != manifest:
            raise PermissionError('native TRAIN closure aliases conflicting member metadata')
        return manifest

    def require_member(self, manifest):
        self.writer.require_active_verification_scope()
        if type(manifest) is not ArtifactManifest or self.members.get(manifest.materialization.relative_path) != manifest:
            raise PermissionError('native TRAIN body lacks its exact authenticated metadata role')

    def control(self, relative, kind, *, expected=None, width=None, parents=None,
                logical_id=None, expected_record=None, singleton=False, input_ids=None, pair=_DEV):
        manifest = self.writer.read_manifest(relative)
        logical, physical = manifest.logical, manifest.materialization
        if (logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != 'application/json'
                or logical.payload_schema != kind.SCHEMA
                or self.writer.custody_limits.exceeds('control_record_bytes', physical.size_bytes)
                or self.writer.custody_limits.exceeds('in_memory_payload_bytes', physical.size_bytes)
                or logical_id is not None and logical.logical_artifact_id != logical_id
                or input_ids is not None and physical.materialization_id not in input_ids
                or singleton and manifest.publication.members != (artifact_publication_member(logical, physical),)):
            raise PermissionError('native TRAIN control changes its closed selected codec or producer role')
        if expected_record is not None:
            expected = ObjectIdentity.from_record(logical.logical_artifact_id, expected_record)
            width = len(expected_record.canonical_bytes())
        self.add(manifest, pair=pair, expected=expected, width=width, parents=parents)
        # Partial control proof deliberately verifies ONE body, never publication
        # sibling arrays. Whole-publication membership is closed before yielding.
        self.require_member(manifest)
        raw = read_bounded_bytes(self.writer.root.resolve(relative, for_write=False), maximum_bytes=physical.size_bytes)
        if len(raw) != physical.size_bytes or sha256(raw).hexdigest() != logical.content_sha256:
            raise PermissionError('native TRAIN control changes its actual canonical bytes')
        record = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        if (record.canonical_bytes() != raw
                or expected is not None and ObjectIdentity.from_record(expected.object_id, record) != expected
                or expected_record is not None and record != expected_record):
            raise PermissionError('native TRAIN control substitutes its exact typed original')
        self.require_member(manifest)
        self.writer.verify(physical)
        return record, manifest

    def publication(self, publication, *, record=None, pair=_BLIND):
        manifest = self.writer.read_manifest(publication.materialization.relative_path)
        if (manifest.logical, manifest.materialization) != (publication.logical, publication.materialization):
            raise PermissionError('native TRAIN source publication changes its actual original handle')
        expected = None if record is None else ObjectIdentity.from_record(manifest.logical.logical_artifact_id, record)
        return self.add(manifest, pair=pair, expected=expected,
            width=None if record is None else len(record.canonical_bytes()))

    def close(self):
        for census in self.final_censuses:
            census()
        # A familiar hash, label or shared parent cannot admit another sibling.
        for manifest in tuple(self.members.values()):
            for member in manifest.publication.members:
                expected = self.members.get(member.relative_path)
                if expected is None or expected.publication != manifest.publication:
                    raise PermissionError('native TRAIN publication includes an unowned member')
                self.require_member(self.writer.read_manifest(member.relative_path))


class _Packet(Mapping):
    """Exact packet-pinned canonical controls; binary members remain metadata."""
    def __init__(self, metadata, directory, packet):
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingAcquisitionSpecification
        from empirical_lawhood.kernel.experimental_design import UnitAllocation
        from empirical_lawhood.planning.recursive_authoring import RecursiveScientificSelection, RecursiveStudyDraft
        from empirical_lawhood.runtime.candidate_compiler import StudyTemplate
        from empirical_lawhood.runtime.capabilities import CapabilityRegistry
        from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
        from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan
        from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
        from empirical_lawhood.runtime.scientific_graph_preservation import DevelopmentGraphPreservationReceipt
        self.metadata, self.directory, self.packet = metadata, directory, packet
        self._readable = {
            'draft.json': RecursiveStudyDraft, 'implementation.json': RecursiveImplementationBinding,
            'run-plan.json': DevelopmentRunPlan, 'execution-plan.json': DevelopmentExecutionPlan,
            'template.json': StudyTemplate, 'scientific-projection.json': RecursiveScientificSelection,
            'registry.json': CapabilityRegistry, 'graph-preservation.json': DevelopmentGraphPreservationReceipt,
            'experiment-specification.json': NativeTrainingAcquisitionSpecification,
            'experiment-instance.json': ExperimentInstanceBinding, 'experiment-allocation.json': UnitAllocation,
        }
        self._members = {row.filename: row for row in packet.members}
        for name, member in self._members.items():
            metadata.add(metadata.writer.read_manifest(directory+'/'+name), pair=_DEV,
                expected=member.identity, width=member.size_bytes)

    def select_request(self, instance):
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingAcquisitionRequest
        kind=NativeTrainingAcquisitionRequest
        if len(instance.sources)!=1:
            raise PermissionError('native TRAIN metadata requires its sole exact current request source')
        reference,=instance.sources
        name='experiment-source-'+sha256(reference.object_id.encode()).hexdigest()+'.json'
        member=self._members.get(name)
        if (member is None or member.identity!=reference
                or (reference.object_schema,reference.object_version)!=(kind.SCHEMA,kind.VERSION)):
            raise PermissionError('native TRAIN metadata refuses an undeclared scientific source codec')
        self._readable[name]=kind

    def __iter__(self):
        return iter(self._members)

    def __len__(self):
        return len(self._members)

    def manifest(self, name):
        member = self._members[name]
        return self.metadata.add(self.metadata.writer.read_manifest(self.directory+'/'+name),
            pair=_DEV, expected=member.identity, width=member.size_bytes)

    def __getitem__(self, name):
        kind=self._readable.get(name)
        member=self._members.get(name)
        if (kind is None or member is None
                or (member.identity.object_schema,member.identity.object_version)!=(kind.SCHEMA,kind.VERSION)):
            raise PermissionError('native TRAIN metadata refuses a non-control packet body')
        manifest = self.manifest(name)
        if (manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or manifest.logical.media_type != 'application/json'
                or self.metadata.writer.custody_limits.exceeds('control_record_bytes',manifest.materialization.size_bytes)
                or self.metadata.writer.custody_limits.exceeds('in_memory_payload_bytes',manifest.materialization.size_bytes)):
            raise PermissionError('metadata TRAIN bootstrap cannot open a scientific binary or unbounded control member')
        self.metadata.require_member(manifest)
        raw = read_bounded_bytes(self.metadata.writer.root.resolve(manifest.materialization.relative_path,
            for_write=False), maximum_bytes=manifest.materialization.size_bytes)
        if len(raw) != manifest.materialization.size_bytes or sha256(raw).hexdigest() != manifest.logical.content_sha256:
            raise PermissionError('native TRAIN packet control differs from its frozen member')
        record=decode_canonical_bytes(raw,kind,maximum_bytes=len(raw))
        if record.canonical_bytes()!=raw or ObjectIdentity.from_record(member.identity.object_id,record)!=member.identity:
            raise PermissionError('native TRAIN control changes its closed canonical owner or identity')
        self.metadata.writer.verify(manifest.materialization)
        return raw


def _external_metadata(metadata, packet, draft, plan):
    """Same frozen path/body/lineage contract as ordinary DEV _external_inputs."""
    from empirical_lawhood.api.recursive_authoring import _external_storage_contract
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput
    from .recursive_operations import operation_storage_codecs
    storage_codecs = operation_storage_codecs()
    selected = {}
    for task in plan.tasks:
        for spec in task.external_inputs:
            old = selected.setdefault(spec.logical_artifact_id, spec)
            if any(getattr(old, name) != getattr(spec, name) for name in (
                    'expected_content_sha256', 'expected_payload_schema', 'expected_media_type',
                    'expected_size_bytes', 'expected_outcome_access', 'expected_visibility_ceiling', 'identity_scope_sha256')):
                raise PermissionError('native TRAIN tasks disagree on exact retained external inputs')
    by_sha = {}
    for name in packet:
        member = packet.manifest(name)
        by_sha.setdefault(member.logical.content_sha256, []).append(member)
    result = {}
    parents = (ArtifactLineageParent(ObjectIdentity.from_record(draft.draft_id, draft), _DEV[1], _DEV[0]),)
    for number, (logical_id, spec) in enumerate(sorted(selected.items())):
        held = by_sha.get(spec.expected_content_sha256, ())
        if not held or len({row.materialization.size_bytes for row in held}) != 1:
            raise PermissionError('native TRAIN external omits its actual packet-pinned bytes')
        profile, suffix = _external_storage_contract(payload_schema=spec.expected_payload_schema,
            media_type=spec.expected_media_type, storage_codecs=storage_codecs)
        manifest = metadata.writer.read_manifest('runs/'+plan.source_plan.object_id+'/inputs/input-'+str(number).zfill(4)+suffix)
        logical, physical = manifest.logical, manifest.materialization
        width = held[0].materialization.size_bytes
        if ((logical.logical_artifact_id, logical.payload_schema, logical.profile, logical.media_type,
                logical.content_sha256, logical.outcome_access, logical.visibility_ceiling) != (
                logical_id, spec.expected_payload_schema, profile, spec.expected_media_type,
                spec.expected_content_sha256, spec.expected_outcome_access, spec.expected_visibility_ceiling)
                or spec.expected_size_bytes is not None and spec.expected_size_bytes != width):
            raise PermissionError('native TRAIN retained external changes its frozen task specification')
        metadata.add(manifest, pair=_DEV, width=width, parents=parents)
        result[logical_id] = VerifiedArtifactInput(logical, physical)
    return result


def _receipt(metadata, index, task, candidate):
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    store = ExternalTaskReceiptStore(metadata.writer)
    envelope = store._read_envelope(index.run_id, task.task_id, candidate.attempt_id)
    if envelope is None:
        return None
    _, manifest = envelope
    receipt, _ = metadata.control(manifest.materialization.relative_path, CanonicalTaskReceipt,
        logical_id='task-receipt.receipt.'+candidate.attempt_id, singleton=True)
    ExternalRunRecoveryStore._validate_receipt_static(index, task, candidate, receipt)
    expected = tuple(sorted((ArtifactLineageParent(ObjectIdentity.from_record(row.logical_artifact_id, row),
        row.visibility_ceiling, row.outcome_access) for row in receipt.output_logical_artifacts), key=lineage_parent_sort_key))
    if manifest.logical.lineage_parents != expected:
        raise PermissionError('native TRAIN receipt changes its exact output-publication parents')
    return receipt


def _native_metadata(metadata, plan, index, task, receipt, by_task, inputs, source):
    from empirical_lawhood.infrastructure.execution import LocalScheduler
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.native_parent_finalization import _native_parent_definitions
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput
    from empirical_lawhood.runtime.native_effects import NativeEffectContact
    from empirical_lawhood.runtime.native_subwork import (
        NativeSubworkBegin, NativeSubworkContact, NativeSubworkDefinition, NativeSubworkRoster,
        NativeSubworkCallEntry, NativeSubworkCallReturn, NativeSubworkCompletion,
    )
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
    dependencies = {key: tuple(VerifiedArtifactInput(logical, material) for logical, material in
        zip(row.output_logical_artifacts, row.output_materializations, strict=True)) for key, row in by_task.items()}
    actual = (*LocalScheduler._dependency_outputs(task, dependencies), *(inputs[row.logical_artifact_id] for row in task.external_inputs))
    parent = NativeEffectContact(index.run_id, task.task_id, receipt.attempt_id, index.execution_plan,
        ObjectIdentity.from_record(task.task_id, task), plan.implementation_commit,
        tuple(sorted(row.materialization.materialization_id for row in actual)),
        tuple(sorted(by_task[key].receipt_id for key in task.dependency_task_ids)))
    contacts = ExternalNativeEffectContactStore(plane=metadata.writer, execution_plan=index.execution_plan,
        visibility_ceiling=_DEV[1], outcome_access=_DEV[0])
    metadata.control(contacts._path(index.run_id, task.task_id), NativeEffectContact, expected_record=parent,
        parents=(ArtifactLineageParent(index.execution_plan, _DEV[1], _DEV[0]),), singleton=True)
    store = ExternalNativeSubworkStore(plane=metadata.writer, parent_contacts=contacts, parent_contact=parent,
        parent_inputs=tuple(ArtifactManifest(row.logical,row.materialization) for row in actual), completed_only=True)
    invocation, _ = metadata.control(store._invocation_path(parent), PreparedInvocationContract,
        parents=store._parents(parent.execution_plan, parent.execution_task),
        logical_id='native-invocation.'+store._invocation_key(parent), singleton=True)
    invocation.require_complete()
    if (invocation.expected_parent_contact != parent or invocation.execution_task_record != task
            or invocation.implementation != source
            or invocation.native_work is None or not invocation.native_work.definitions
            or tuple((row.logical,row.materialization.materialization_id,row.materialization.size_bytes,
                    row.materialization.physical_sha256) for row in sorted(actual,key=lambda row:row.logical.logical_artifact_id)) !=
                tuple((row.logical,row.binding.materialization_id,row.binding.size_bytes,row.physical_sha256)
                    for row in invocation.inputs)
            or invocation.dependency_receipts != LocalScheduler._dependency_receipt_bindings(task,
                dependency_outputs=LocalScheduler._dependency_outputs(task,dependencies),receipts=by_task)):
        raise PermissionError('native TRAIN invocation changes its original task or complete prepared inputs')
    work = invocation.native_work
    root = metadata.writer.root.resolve(store._roster_root(parent), for_write=False)
    def roster_paths():
        return tuple(sorted(path.relative_to(metadata.writer.root.contract.canonical_path).as_posix()
            for path in root.iterdir() if not path.name.startswith('.') and path.name.endswith('.json')
            and not path.name.endswith('.manifest.json')))
    before = roster_paths()
    rosters=[]
    for path in before:
        row, manifest = metadata.control(path, NativeSubworkRoster, singleton=True)
        if (row.parent_contact != parent or path != store._roster_path(parent,row.roster_id)
                or manifest.logical.lineage_parents != store._parents(parent.execution_plan,
                    *((row.parent_subwork,) if row.parent_subwork is not None else ()))):
            raise PermissionError('native TRAIN roster changes its actual parent/selection role')
        rosters.append(row)
    for roster in rosters:
        for identity in roster.subworks:
            # Read_definition's deterministic path is derived only from this
            # exact roster identity and frozen parent, never a directory grant.
            key=sha256((parent.task_id+':'+identity.object_id).encode()).hexdigest()
            metadata.control('runs/'+parent.run_id+'/native-subwork/'+key+'/definition.json',
                NativeSubworkDefinition,expected=identity,parents=store._parents(parent.execution_plan),
                logical_id='native-subwork.'+key+'.definition',singleton=True)
    actual_rosters, actual_definitions = _native_parent_definitions(store=store,work=work)
    if tuple(sorted(rosters,key=lambda row:row.roster_id))!=actual_rosters:
        raise PermissionError('native TRAIN roster census changed during metadata projection')
    for definition in actual_definitions:
        if (definition.code_sources_sha256,definition.dependency_lock_sha256)!=(
                source.code_sources_sha256,source.dependency_lock_sha256):
            raise PermissionError('native TRAIN definition changes its actual producing source closure')
        run, child_task, attempt = store._receipt_locator(definition)
        receipt_store=ExternalTaskReceiptStore(metadata.writer)
        envelope=receipt_store._read_envelope(run,child_task,attempt)
        if envelope is None:raise PermissionError('native TRAIN child lacks its actual completion receipt')
        _,header=envelope
        child,_=metadata.control(header.materialization.relative_path,CanonicalTaskReceipt,
            logical_id='task-receipt.receipt.'+attempt,singleton=True)
        if (child.run_id,child.task_id,child.attempt_id)!=(run,child_task,attempt):
            raise PermissionError('native TRAIN child receipt changes its exact deterministic producer')
        if child.operational_status is not OperationalStatus.SUCCEEDED:
            raise PermissionError('native TRAIN child did not return a complete successful control census')
        receipt_parents=tuple(sorted((ArtifactLineageParent(ObjectIdentity.from_record(row.logical_artifact_id,row),
            row.visibility_ceiling,row.outcome_access) for row in child.output_logical_artifacts),key=lineage_parent_sort_key))
        if header.logical.lineage_parents!=receipt_parents:
            raise PermissionError('native TRAIN child receipt changes its exact output parents')
        for logical,physical in zip(child.output_logical_artifacts,child.output_materializations,strict=True):
            manifest=metadata.writer.read_manifest(physical.relative_path)
            if (manifest.logical,manifest.materialization)!=(logical,physical):
                raise PermissionError('native TRAIN child substitutes its receipted output metadata')
            metadata.add(manifest,pair=_DEV)
        start=NativeSubworkBegin(definition.identity)
        metadata.control(store._root(definition)+'/begin.json',NativeSubworkBegin,expected_record=start,
            parents=store._parents(definition.identity),logical_id=store._id(definition,'begin'),singleton=True)
        contact=NativeSubworkContact(ObjectIdentity.from_record(store._id(definition,'begin'),start))
        metadata.control(store._root(definition)+'/contact.json',NativeSubworkContact,expected_record=contact,
            parents=store._parents(contact.begin),logical_id=store._id(definition,'contact'),singleton=True)
        contact_pin=ObjectIdentity.from_record(store._id(definition,'contact'),contact)
        entry,entry_manifest=metadata.control(store._root(definition)+'/call-entry.json',NativeSubworkCallEntry,
            parents=store._parents(definition.identity,contact_pin,invocation.identity),
            input_ids=child.input_materialization_ids,logical_id=store._id(definition,'call-entry'),singleton=True)
        metadata.control(store._root(definition)+'/call-return.json',NativeSubworkCallReturn,
            parents=store._parents(ObjectIdentity.from_record(entry_manifest.logical.logical_artifact_id,entry)),
            input_ids=child.input_materialization_ids,logical_id=store._id(definition,'call-return'),singleton=True)
        completion_path=store._root(definition)+'/completion.json'
        completion=metadata.members.get(completion_path)
        if completion is None:raise PermissionError('native TRAIN child receipt omits its original completion')
        metadata.control(completion_path,NativeSubworkCompletion,
            expected=ObjectIdentity(completion.logical.logical_artifact_id,NativeSubworkCompletion.SCHEMA,
                NativeSubworkCompletion.VERSION,completion.logical.content_sha256),
            parents=store._parents(definition.identity,contact_pin),logical_id=store._id(definition,'completion'),singleton=True)
        observed=store.inspect_metadata(definition)
        if (observed.receipt!=child or observed.completion is None
                or observed.completion.operational_status is not OperationalStatus.SUCCEEDED
                or observed.completion.unknown_streams or observed.partial_outputs
                or observed.call_entry is None or observed.call_return is None):
            raise PermissionError('native TRAIN nested control/return/receipt chain is incomplete')
    def require_roster_census():
        if roster_paths()!=before:
            raise PermissionError('native TRAIN changes its complete conditional roster census during read')
    require_roster_census()
    metadata.final_censuses.append(require_roster_census)


def _operational_metadata(metadata, plan, index, by_task):
    """Reuse the real immutable recovery/event census, with no output reads."""
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.recursive_custody import _operational_census
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex, DevelopmentRunRecoveryTerminalEvent, TaskRecoveryEvent
    metadata.control(index.index_relative_path,DevelopmentRunRecoveryIndex,expected_record=index)
    for binding in index.tasks:
        for path in (*(row.event_relative_path for row in binding.attempts),binding.nonattempt_event_relative_path):
            actual=metadata.writer.root.resolve(path,for_write=False)
            sidecar=actual.with_name(actual.name+'.manifest.json')
            if not actual.exists() and not sidecar.exists():continue
            event,manifest=metadata.control(path,TaskRecoveryEvent,singleton=True)
            if (event.recovery_index!=ObjectIdentity.from_record(index.recovery_index_id,index)
                    or event.run_id!=index.run_id or ExternalRunRecoveryStore._event_path(index,event)!=path
                    or manifest.logical.logical_artifact_id!=event.event_id):
                raise PermissionError('native TRAIN event changes its exact original recovery role')
            parents=[ArtifactLineageParent(ObjectIdentity.from_record(index.recovery_index_id,index),_DEV[1],_DEV[0])]
            if event.receipt_id is not None:
                receipt=by_task.get(event.task_id)
                if receipt is None or (receipt.receipt_id,receipt.fingerprint())!=(event.receipt_id,event.receipt_sha256):
                    raise PermissionError('native TRAIN event substitutes its exact successful receipt')
                parents.append(ArtifactLineageParent(ObjectIdentity.from_record(receipt.receipt_id,receipt),_DEV[1],_DEV[0]))
            if manifest.logical.lineage_parents!=tuple(sorted(parents,key=lineage_parent_sort_key)):
                raise PermissionError('native TRAIN event changes its exact index/receipt ancestry')
    terminal,manifest=metadata.control(index.terminal_event_relative_path,DevelopmentRunRecoveryTerminalEvent,
        parents=(ArtifactLineageParent(ObjectIdentity.from_record(index.recovery_index_id,index),_DEV[1],_DEV[0]),),singleton=True)
    if (terminal.recovery_index!=ObjectIdentity.from_record(index.recovery_index_id,index)
            or terminal.run_id!=index.run_id or terminal.operational_status!='SUCCEEDED'
            or terminal.completed_task_ids!=tuple(sorted(by_task)) or terminal.failed_task_ids or terminal.blocked_task_ids
            or manifest.logical.logical_artifact_id!=terminal.terminal_event_id):
        raise PermissionError('native TRAIN operational closure is not its complete actual successful task census')
    _operational_census(recovery=ExternalRunRecoveryStore(metadata.writer),
        store=ExternalTaskReceiptStore(metadata.writer),plan=plan,index=index,terminal=terminal,decode_products=False)


def _source_publications(metadata, request):
    """Only exact original C/manifest handles; no body or source replay shortcut."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import _manifest_publications
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
    from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1AllocationReservation
    from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
    from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import MatrixE6EmpiricalTransportPolicy
    from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
    from empirical_lawhood.kernel.time import AvailabilitySpec
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    selected=request.input_commitments
    original,_=metadata.control(selected.publication.materialization.relative_path,MatrixProgrammeInputCommitments,
        expected=selected.record,pair=_BLIND)
    metadata.publication(selected.publication,record=original)
    kinds=(MatrixProgrammeScientificDesign,E1AllocationReservation,MatrixFactorExposureCensus,
        MatrixParameterScalarDefinition,scheduled.ScheduledReservation,scheduled.ScheduledSpecification,
        ScheduledExposureAudit,ScheduledResponseSelection,MatrixE6EmpiricalTransportPolicy,
        NumericalProducingProvenance,AvailabilitySpec)
    for selected in original.publications():
        kind,=(kind for kind in kinds if (kind.SCHEMA,kind.VERSION)==(selected.record.object_schema,selected.record.object_version))
        record,_=metadata.control(selected.publication.materialization.relative_path,kind,expected=selected.record,pair=_BLIND)
        metadata.publication(selected.publication,record=record)
        if type(record) in (scheduled.ScheduledReservation,scheduled.ScheduledSpecification,E1AllocationReservation):
            metadata.publication(record.publication)
        if type(record) is ScheduledResponseSelection:
            for publication in record.template_publications:metadata.publication(publication)
        if type(record) is ScheduledExposureAudit:
            for publication in record.prior_corpus:metadata.publication(publication)
    for _,publication in original.support_files:metadata.publication(publication)
    for source in (request.train_manifest,request.future_manifest):
        for publication,record in _manifest_publications(source):metadata.publication(publication,record=record)
    for publication in request.template_publications:metadata.publication(publication)
    for _,publication in request.exposure_support:
        if type(publication) is ArtifactWriteResult:metadata.publication(publication)


@contextmanager
def authenticated_native_training_read_scope(*, artifact_writer, locator):
    """Hold exact original TRAIN membership through ordinary full read/replay.

    Construct before entering a dependent original-parent ambient read guard;
    never disable an inherited guard. This context authenticates membership only.
    Its returned callback cannot survive the actual writer lifetime.
    """
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
    from empirical_lawhood.api.current_task_custody import _development_receipt_output_metadata
    from empirical_lawhood.api.native_training_banks import _read_instance
    from empirical_lawhood.api.recursive_authoring import _authenticate_experiment_instance
    from empirical_lawhood.api.recursive_execution import _retained_plans
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.infrastructure.recursive_custody import _require_no_orphaned_native_custody
    from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
    from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave,RecursiveImplementationBinding
    if type(locator) is not MatrixFiniteDtTrainingLocator:
        raise TypeError('native TRAIN read scope requires its exact current locator')
    locator.__post_init__()
    with artifact_writer.verification_scope() as writer:
        metadata=_Metadata(writer)
        packet,_=metadata.control(locator.authored_directory+'/authored-wave.json',AuthoredRecursiveWave,
            expected=locator.packet,parents=())
        payloads=_Packet(metadata,locator.authored_directory,packet)
        draft=decode_canonical_bytes(payloads['draft.json'],RecursiveStudyDraft,maximum_bytes=None)
        source=decode_canonical_bytes(payloads['implementation.json'],RecursiveImplementationBinding,maximum_bytes=None)
        if (ObjectIdentity.from_record(draft.draft_id,draft)!=packet.draft
                or ObjectIdentity.from_record('recursive-member.implementation',source)!=packet.implementation
                or draft.development_study is None or draft.prospective_draft is not None
                or draft.contribution_parents):
            raise PermissionError('native TRAIN metadata changes its actual original development root')
        from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
        instance=decode_canonical_bytes(payloads['experiment-instance.json'],ExperimentInstanceBinding,maximum_bytes=None)
        payloads.select_request(instance)
        specification,request,_=_read_instance(payloads)
        _authenticate_experiment_instance(payloads=payloads,draft=draft,artifact_writer=writer)
        run,plan,index=_retained_plans(payloads,draft)
        if (type(plan) is not DevelopmentExecutionPlan or run.run_plan_id!=locator.run_id
                or ObjectIdentity.from_record(plan.execution_plan_id,plan)!=locator.execution_plan):
            raise PermissionError('native TRAIN metadata changes its exact locator run/plan')
        from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
        provenance,_=metadata.control('runs/'+run.run_plan_id+'/inputs/producing-provenance.json',
            NumericalProducingProvenance,parents=())
        if (provenance.package_sources,provenance.code_sources_sha256,provenance.dependency_lock_sha256,
                provenance.observed_git_head)!=(source.package_sources,source.code_sources_sha256,
                source.dependency_lock_sha256,source.observed_git_head) or source.observed_git_head!=plan.implementation_commit:
            raise PermissionError('native TRAIN metadata changes its actual complete producing source provenance')
        inputs=_external_metadata(metadata,payloads,draft,plan)
        by_task={}
        for task in plan.tasks:
            rows=tuple(value for candidate in index.task(task.task_id).attempts
                if (value:=_receipt(metadata,index,task,candidate)) is not None
                and value.operational_status is OperationalStatus.SUCCEEDED)
            if len(rows)!=1:raise PermissionError('native TRAIN metadata needs its complete unique successful task census')
            by_task[task.task_id]=rows[0]
        with writer.read_context(before_member=metadata.require_member):
            _operational_metadata(metadata,plan,index,by_task)
            for task in plan.tasks:
                for value in _development_receipt_output_metadata(writer=writer,plan=plan,index=index,
                        inputs=inputs,task_id=task.task_id,receipt=by_task[task.task_id]):
                    manifest=writer.read_manifest(value.materialization.relative_path)
                    if (manifest.logical,manifest.materialization)!=(value.logical,value.materialization):
                        raise PermissionError('native TRAIN metadata substitutes its actual successful task output')
                    metadata.add(manifest,pair=_DEV)
            registrations={row.selection.capability_key:row for row in operation_catalog()[0]}
            for task in plan.tasks:
                registration=registrations[task.capability.capability_key]
                if registration.native_effect:
                    _native_metadata(metadata,plan,index,task,by_task[task.task_id],by_task,inputs,source)
                else:
                    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
                    path=writer.root.resolve(ExternalNativeEffectContactStore._path(index.run_id,task.task_id),for_write=False)
                    if path.exists() or path.with_name(path.name+'.manifest.json').exists():
                        raise PermissionError('pure TRAIN task has foreign native parent contact custody')
                    _require_no_orphaned_native_custody(plane=writer,run_id=index.run_id,task_id=task.task_id)
            _source_publications(metadata,request)
            metadata.close()
            scope=NativeTrainingReadScope(locator,writer,MappingProxyType(dict(metadata.members)))
            yield scope
            metadata.close()
            writer.require_verification_snapshot()
