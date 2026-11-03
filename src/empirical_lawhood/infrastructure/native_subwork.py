# SPDX-License-Identifier: MPL-2.0
"""Per-subcall progress using the existing artifact plane and task receipts.

Only the creating contact publisher receives an in-process entry token. A lost
token cannot be reconstructed from persisted bytes. Recovery authenticates
completed evidence; it never invokes a native worker or repairs uncertain contact.
"""

from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.artifact_stream_primitives import (
    STREAM_CHUNK_BYTES as STREAM_CHUNK_BYTES,
    _output_chunk_bound as _output_chunk_bound,
    _output_chunks as _output_chunks,
)
from empirical_lawhood.infrastructure.bounded_io import (
    BoundedFileIOError, _open_contained_regular,
    _regular_chunks, _stable_descriptor, read_bounded_bytes,
)
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork_inputs import validate_native_subwork_inputs
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore, decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent,
    ArtifactManifest,
    ArtifactProfile,
    ArtifactStreamWriteRequest,
    ArtifactWriteRequest,
    CanonicalTaskReceipt,
    ReceiptCheck,
    lineage_parent_sort_key,
)
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkBegin,
    NativeSubworkCallEntry,
    NativeSubworkCallReturn,
    NativeSubworkCompletion,
    NativeSubworkContact,
    NativeSubworkDefinition,
    NativeSubworkInspection,
    NativeSubworkPartialOutput,
    NativeSubworkReceiptPublicationPending,
    NativeSubworkRoster,
    NativeSubworkState,
    NativeSubworkUncertainContact,
)
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract






@dataclass(slots=True, eq=False)
class _NativeSubworkEntry:
    owner: object
    definition: NativeSubworkDefinition
    begin_manifest: ArtifactManifest
    contact_manifest: ArtifactManifest | None = None
    call_entry_manifest: ArtifactManifest | None = None
    call_return_manifest: ArtifactManifest | None = None
    outputs: dict[str, ArtifactManifest] = field(default_factory=dict)
    partials: dict[str, tuple[ArtifactManifest, ArtifactManifest]] = field(default_factory=dict)
    completed: bool = False


@dataclass(frozen=True, slots=True)
class NativeSubworkMetadata:
    """Control/receipt membership only; output bytes have NOT been verified."""

    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion | None
    receipt: CanonicalTaskReceipt | None
    outputs: tuple[ArtifactManifest, ...]
    partial_outputs: tuple[ArtifactManifest, ...]
    call_entry: NativeSubworkCallEntry | None
    call_return: NativeSubworkCallReturn | None


class ExternalNativeSubworkStore:
    """A progress seam inside an already entered task, not another scheduler.

Adapters freeze each definition before that subcall, including conditional
segment/initializer calls whose operands become available during execution.
The parent scheduler's authority and contact recovery remain authoritative.
The caller must not use this store to bypass a blocked parent task.
"""

    def __init__(self, *, plane: ExternalArtifactPlane,
                 parent_contacts: ExternalNativeEffectContactStore, parent_contact=None,
                 parent_inputs: tuple[ArtifactManifest, ...] = (), completed_only: bool = False,
                 prepared_invocation: PreparedInvocationContract | None = None,
                 before_contact: Callable[[NativeSubworkDefinition], None] | None = None):
        if not isinstance(plane, ExternalArtifactPlane) or not isinstance(
                parent_contacts, ExternalNativeEffectContactStore):
            raise TypeError("native subwork requires the guarded artifact/contact owners")
        if plane.root.contract != parent_contacts.plane.root.contract:
            raise ValueError("native subwork and parent contact custody roots differ")
        if type(completed_only) is not bool:
            raise TypeError("native subwork completed-only selection requires an actual boolean")
        if prepared_invocation is not None:
            if type(prepared_invocation) is not PreparedInvocationContract:
                raise TypeError("native subwork requires the actual prepared invocation")
            prepared_invocation.require_complete()
            if prepared_invocation.expected_parent_contact != parent_contact:
                raise ValueError("native subwork prepared invocation changes its exact parent")
        if before_contact is not None and not callable(before_contact):
            raise TypeError("native subwork entry guard must be a coordinator callback")
        self.plane, self.parent_contacts = plane, parent_contacts
        self.visibility = parent_contacts.visibility_ceiling
        self.access = parent_contacts.outcome_access
        self.minimum_free_bytes = parent_contacts.minimum_free_bytes
        self.receipts = ExternalTaskReceiptStore(plane, minimum_free_bytes=self.minimum_free_bytes)
        if parent_contacts.continuation_scopes and parent_contact is None:
            raise ValueError('native continuation subwork requires its bound original parent selection')
        if parent_contact is not None:
            scopes = tuple(row for row in parent_contacts.continuation_scopes if row.task_id == parent_contact.task_id)
            if scopes:
                from .task_receipts import ExternalNativeContinuationReceiptStore
                scope, = scopes
                self.receipts = ExternalNativeContinuationReceiptStore(plane, continuation_scope=scope,
                    minimum_free_bytes=self.minimum_free_bytes)
        self._owner = object()
        self._conditional_parents: dict[str, _NativeSubworkEntry] = {}
        self._bound_parent = parent_contact
        self.parent_inputs = parent_inputs
        self.completed_only = completed_only
        self.prepared_invocation = prepared_invocation
        self.before_contact = before_contact

    def _require_progress_mutation(self) -> None:
        if self.completed_only:
            raise NativeSubworkUncertainContact("completed-only native progress prohibits acquisition and mutation")

    @property
    def parent_contact(self):
        if self._bound_parent is None or self.parent_contacts.read(
                self._bound_parent.run_id, self._bound_parent.task_id) != self._bound_parent:
            raise ValueError("native subwork port lacks its exact selected parent")
        return self._bound_parent

    @staticmethod
    def _key(definition: NativeSubworkDefinition) -> str:
        return sha256((definition.parent_contact.task_id + ":" + definition.subwork_id).encode()).hexdigest()

    def _storage_key(self, definition):
        parent = definition.parent_contact
        return self.parent_contacts.storage_key(parent.run_id, parent.task_id, self._key(definition))

    def _definition_path(self, parent, subwork_id):
        key = sha256((parent.task_id + ':' + subwork_id).encode()).hexdigest()
        key = self.parent_contacts.storage_key(parent.run_id, parent.task_id, key)
        root = self.parent_contacts.custody_root(parent.run_id, parent.task_id)
        return f'{root}/native-subwork/{key}/definition.json'

    def _root(self, definition: NativeSubworkDefinition) -> str:
        parent = definition.parent_contact
        root = self.parent_contacts.custody_root(parent.run_id, parent.task_id)
        return f'{root}/native-subwork/{self._storage_key(definition)}'

    def _id(self, definition: NativeSubworkDefinition, name: str) -> str:
        return f"native-subwork.{self._key(definition)}.{name}"

    def _parent(self, identity: ObjectIdentity) -> ArtifactLineageParent:
        return ArtifactLineageParent(identity, self.visibility, self.access)

    def _parents(self, *identities: ObjectIdentity) -> tuple[ArtifactLineageParent, ...]:
        return tuple(sorted((self._parent(identity) for identity in identities), key=lineage_parent_sort_key))

    def _assert_parent(self, definition: NativeSubworkDefinition) -> None:
        if type(definition) is not NativeSubworkDefinition:
            raise ValueError("native subwork requires its selected typed definition")
        definition.__post_init__()
        parent = definition.parent_contact
        if self.parent_contacts.read(parent.run_id, parent.task_id) != parent:
            raise ValueError("native subwork has no actual exact entered parent contact")

    def _assert_live_parent(self, definition: NativeSubworkDefinition) -> None:
        self._require_progress_mutation()
        self._assert_parent(definition)
        if not self.parent_contacts.is_live_creator(definition.parent_contact):
            raise NativeSubworkUncertainContact("persisted parent contact has no live creating launch; no new subwork entry")

    def _manifest(self, relative: str, *, _metadata_only: bool = False) -> ArtifactManifest | None:
        path = self.plane.root.resolve(relative, for_write=False)
        meta = self.plane.root.resolve(relative + ".manifest.json", for_write=False)
        if not path.exists() and not meta.exists():
            return None
        if not path.is_file() or not meta.is_file():
            raise NativeSubworkUncertainContact("native subwork publication is partial; no retry")
        manifest = decode_artifact_manifest(
            read_bounded_bytes(meta, maximum_bytes=self.plane.custody_limits.manifest_bytes),
            maximum_bytes=self.plane.custody_limits.manifest_bytes,
        )
        if (manifest.materialization.relative_path != relative
                or manifest.logical.visibility_ceiling is not self.visibility
                or manifest.logical.outcome_access is not self.access):
            raise ValueError("native subwork manifest substitutes its path or access")
        if _metadata_only:
            # Authenticate actual sidecar/commit metadata, never scientific bytes.
            if self.plane.read_manifest(relative) != manifest:
                raise ValueError("native output changes its exact publication metadata")
        else:
            self.plane.verify_manifest(manifest)
        return manifest

    def _control(self, definition, name, kind, parents):
        manifest = self._manifest(self._root(definition) + "/" + name + ".json")
        if manifest is None:
            return None, None
        logical = manifest.logical
        if (logical.logical_artifact_id != self._id(definition, name)
                or logical.payload_schema != kind.SCHEMA
                or logical.profile is not ArtifactProfile.CANONICAL_JSON
                or logical.media_type != "application/json"
                or logical.lineage_parents != parents
                or self.plane.custody_limits.exceeds("control_record_bytes", manifest.materialization.size_bytes)):
            raise ValueError("native subwork progress changes its exact contract or lineage")
        raw = read_bounded_bytes(
            self.plane.root.resolve(manifest.materialization.relative_path, for_write=False),
            maximum_bytes=manifest.materialization.size_bytes,
        )
        if sha256(raw).hexdigest() != logical.content_sha256:
            raise ValueError("native subwork progress differs from authenticated bytes")
        return decode_canonical_bytes(raw, kind, maximum_bytes=manifest.materialization.size_bytes), manifest

    def _write_control(self, definition, name, record, parents):
        self._require_progress_mutation()
        root = self._root(definition)
        result = self.plane.write(ArtifactWriteRequest(
            self._id(definition, name), root + "/" + name + ".json",
            record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            self._id(definition, "progress"), root, record.canonical_bytes(),
            self.visibility, tuple(parent.visibility_ceiling for parent in parents), self.access,
            lineage_parents=parents, minimum_free_bytes=self.minimum_free_bytes,
        ))
        actual, manifest = self._control(definition, name, type(record), parents)
        if actual != record or manifest is None or manifest.materialization != result.materialization:
            raise ValueError("native subwork progress did not survive exact publication")
        return manifest, result.created

    def _invocation_key(self, parent):
        return self.parent_contacts.storage_key(parent.run_id, parent.task_id, sha256(parent.task_id.encode()).hexdigest())

    def _invocation_path(self, parent):
        root = self.parent_contacts.custody_root(parent.run_id, parent.task_id)
        return f'{root}/native-invocations/{self._invocation_key(parent)}.json'

    def read_prepared_invocation(self, parent) -> PreparedInvocationContract | None:
        """Authenticate the one original invocation; never infer missing history."""
        if self.parent_contacts.read(parent.run_id, parent.task_id) != parent:
            raise ValueError("native invocation changes its exact entered parent")
        manifest = self._manifest(self._invocation_path(parent))
        if manifest is None:
            return None
        logical = manifest.logical
        if (logical.logical_artifact_id != "native-invocation." + self._invocation_key(parent)
                or logical.payload_schema != PreparedInvocationContract.SCHEMA
                or logical.profile is not ArtifactProfile.CANONICAL_JSON
                or logical.media_type != "application/json"
                or logical.lineage_parents != self._parents(parent.execution_plan, parent.execution_task)
                or self.plane.custody_limits.exceeds("control_record_bytes", manifest.materialization.size_bytes)):
            raise ValueError("native invocation changes its exact custody or lineage")
        raw = read_bounded_bytes(self.plane.root.resolve(manifest.materialization.relative_path, for_write=False),
            maximum_bytes=manifest.materialization.size_bytes)
        invocation = decode_canonical_bytes(raw, PreparedInvocationContract,
            maximum_bytes=manifest.materialization.size_bytes)
        invocation.require_complete()
        if invocation.expected_parent_contact != parent:
            raise ValueError("native invocation substitutes its original parent, inputs or source")
        return invocation

    def _persist_prepared_invocation(self, parent) -> None:
        self._require_progress_mutation()
        invocation = self.prepared_invocation
        if invocation is None:
            return
        if invocation.expected_parent_contact != parent:
            raise ValueError("native invocation changes its current parent")
        root = self.parent_contacts.custody_root(parent.run_id, parent.task_id) + '/native-invocations'
        parents = self._parents(parent.execution_plan, parent.execution_task)
        self.plane.write(ArtifactWriteRequest(
            "native-invocation." + self._invocation_key(parent), self._invocation_path(parent),
            invocation.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            "native-invocation." + self._invocation_key(parent), root, invocation.canonical_bytes(),
            self.visibility, tuple(row.visibility_ceiling for row in parents), self.access,
            lineage_parents=parents, minimum_free_bytes=self.minimum_free_bytes,
        ))
        if self.read_prepared_invocation(parent) != invocation:
            raise ValueError("native invocation did not survive exact publication")

    def _receipt_locator(self, definition):
        parent = definition.parent_contact
        task = "native-subwork." + self._key(definition)
        attempt = f"{parent.run_id}.{task}.attempt-001"
        return parent.run_id, task, attempt

    def _roster_key(self, parent, roster_id):
        key = sha256((parent.task_id + ':' + roster_id).encode()).hexdigest()
        return self.parent_contacts.storage_key(parent.run_id, parent.task_id, key)

    def _roster_root(self, parent):
        root = self.parent_contacts.custody_root(parent.run_id, parent.task_id)
        return f'{root}/native-subwork-rosters/{self._invocation_key(parent)}'

    def _roster_path(self, parent, roster_id):
        return f'{self._roster_root(parent)}/{self._roster_key(parent, roster_id)}.json'

    def read_roster(self, parent, roster_id="selected.native-subwork") -> NativeSubworkRoster | None:
        if self.parent_contacts.read(parent.run_id, parent.task_id) != parent:
            raise ValueError("native subwork roster substitutes its actual parent")
        relative = self._roster_path(parent, roster_id)
        manifest = self._manifest(relative)
        if manifest is None:
            return None
        logical = manifest.logical
        if (logical.logical_artifact_id != "native-subwork-roster." + self._roster_key(parent, roster_id)
                or logical.payload_schema != NativeSubworkRoster.SCHEMA
                or logical.profile is not ArtifactProfile.CANONICAL_JSON
                or logical.media_type != "application/json"
                or self.plane.custody_limits.exceeds("control_record_bytes", manifest.materialization.size_bytes)):
            raise ValueError("native subwork roster changes its exact custody contract")
        raw = read_bounded_bytes(self.plane.root.resolve(relative, for_write=False),
            maximum_bytes=manifest.materialization.size_bytes)
        roster = decode_canonical_bytes(raw, NativeSubworkRoster, maximum_bytes=manifest.materialization.size_bytes)
        parents = (parent.execution_plan,) if roster.parent_subwork is None else (parent.execution_plan, roster.parent_subwork)
        if (roster.parent_contact != parent or roster.roster_id != roster_id
                or logical.lineage_parents != self._parents(*parents)):
            raise ValueError("native subwork roster changes its actual parent")
        return roster

    def freeze_roster(self, roster: NativeSubworkRoster,
                      parent_entry: _NativeSubworkEntry | None = None, *,
                      definitions: tuple[NativeSubworkDefinition, ...]) -> None:
        self._require_progress_mutation()
        if type(roster) is not NativeSubworkRoster:
            raise ValueError("native subwork requires its typed selected roster")
        roster.__post_init__()
        parent = roster.parent_contact
        if (type(definitions) is not tuple
                or any(type(row) is not NativeSubworkDefinition for row in definitions)
                or tuple(row.identity for row in definitions) != roster.subworks
                or any(row.parent_contact != parent or row.roster_id != roster.roster_id
                       for row in definitions)):
            raise ValueError("native subwork roster omits or substitutes its complete selected definitions")
        if not self.parent_contacts.is_live_creator(parent):
            raise NativeSubworkUncertainContact("persisted parent contact has no live creating launch; no roster entry")
        if roster.parent_subwork is not None:
            self._entry(parent_entry)
            if parent_entry.definition.parent_contact != parent or parent_entry.definition.identity != roster.parent_subwork:
                raise ValueError("conditional subwork roster substitutes its actual live parent subwork")
        elif parent_entry is not None:
            raise ValueError("initial native subwork roster unexpectedly supplies a parent subwork")
        existing = self.read_roster(parent, roster.roster_id)
        if existing is not None and existing != roster:
            raise ValueError("native subwork changes its immutable selected roster")
        # A frozen roster already published every definition. Missing custody is
        # never repaired by repeating the selection, even with a live creator.
        for definition in definitions:
            self.inspect(definition)
        if existing is not None:
            if roster.parent_subwork is not None:
                self._conditional_parents[roster.roster_id] = parent_entry
            return
        for definition in definitions:
            self._assert_live_parent(definition)
            self._write_control(definition, "definition", definition,
                self._parents(parent.execution_plan))
        relative = self._roster_path(parent, roster.roster_id)
        token = self._roster_key(parent, roster.roster_id)
        identities = (parent.execution_plan,) if roster.parent_subwork is None else (parent.execution_plan, roster.parent_subwork)
        parents = self._parents(*identities)
        self.plane.write(ArtifactWriteRequest("native-subwork-roster." + token, relative,
            roster.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            "native-subwork-rosters." + parent.run_id + "." + self._invocation_key(parent), self._roster_root(parent),
            roster.canonical_bytes(), self.visibility, tuple(p.visibility_ceiling for p in parents), self.access,
            lineage_parents=parents, minimum_free_bytes=self.minimum_free_bytes))
        if self.read_roster(parent, roster.roster_id) != roster:
            raise ValueError("native subwork roster did not survive exact custody")
        if roster.parent_subwork is not None:
            self._conditional_parents[roster.roster_id] = parent_entry

    def iter_rosters(self, parent) -> Iterator[NativeSubworkRoster]:
        """Read initial and conditional selections from immutable custody only."""
        root = self.plane.root.resolve(self._roster_root(parent), for_write=False)
        if not root.exists():
            return
        for path in root.iterdir():
            if path.name.startswith(".") or not path.name.endswith(".json") or path.name.endswith(".manifest.json"):
                continue
            manifest = self._manifest(path.relative_to(self.plane.root.contract.canonical_path).as_posix())
            if self.plane.custody_limits.exceeds("control_record_bytes", manifest.materialization.size_bytes):
                raise ValueError("native subwork roster exceeds selected metadata allowance")
            raw = read_bounded_bytes(path, maximum_bytes=manifest.materialization.size_bytes)
            roster = decode_canonical_bytes(raw, NativeSubworkRoster, maximum_bytes=manifest.materialization.size_bytes)
            if roster.parent_contact.task_id == parent.task_id:
                yield self.read_roster(parent, roster.roster_id)

    def iter_roster_states(self, parent, roster_id="selected.native-subwork") -> Iterator[tuple[ObjectIdentity, NativeSubworkState]]:
        """Project the retained full denominator without reading scientific arrays."""
        roster = self.read_roster(parent, roster_id)
        if roster is None:
            raise ValueError("native subwork lacks its retained selected full denominator")
        for identity in roster.subworks:
            relative = self._definition_path(parent, identity.object_id)
            manifest = self._manifest(relative)
            if manifest is None:
                raise NativeSubworkUncertainContact("native subwork selected definition is missing; no retry")
            if self.plane.custody_limits.exceeds("control_record_bytes", manifest.materialization.size_bytes):
                raise ValueError("native subwork definition exceeds selected metadata allowance")
            raw = read_bounded_bytes(self.plane.root.resolve(relative, for_write=False),
                maximum_bytes=manifest.materialization.size_bytes)
            definition = decode_canonical_bytes(raw, NativeSubworkDefinition, maximum_bytes=manifest.materialization.size_bytes)
            if definition.identity != identity or definition.parent_contact != parent:
                raise ValueError("native subwork roster member changes its exact selected definition")
            yield identity, self.inspect(definition).state

    def iter_roster_definitions(self, parent, roster_id="selected.native-subwork") -> Iterator[NativeSubworkDefinition]:
        """Recover every selected unit's operands, including never-entered units."""
        roster = self.read_roster(parent, roster_id)
        if roster is None:
            raise ValueError("native subwork lacks its retained selected full denominator")
        for identity in roster.subworks:
            relative = self._definition_path(parent, identity.object_id)
            manifest = self._manifest(relative)
            if manifest is None:
                raise ValueError("native subwork roster lacks its full portable selected operands")
            if self.plane.custody_limits.exceeds("control_record_bytes", manifest.materialization.size_bytes):
                raise ValueError("native subwork definition exceeds selected metadata allowance")
            raw = read_bounded_bytes(self.plane.root.resolve(relative, for_write=False),
                maximum_bytes=manifest.materialization.size_bytes)
            definition = decode_canonical_bytes(raw, NativeSubworkDefinition,
                maximum_bytes=manifest.materialization.size_bytes)
            if (definition.identity != identity or definition.parent_contact != parent
                    or definition.roster_id != roster_id):
                raise ValueError("native subwork roster member substitutes its full selected operands")
            # Also validates definition profile, lineage and canonical identity.
            self.inspect(definition)
            yield definition

    @contextmanager
    def _completed_reader(self, parent=None):
        """Own one effect-free custody lifetime, without a live entry capability."""
        with self.plane.read_context() as plane:
            if parent is None:
                parent = self.parent_contact
            elif self._bound_parent is not None and parent != self.parent_contact:
                raise ValueError("completed native output changes its exact selected parent")
            selected = self.parent_contacts.for_task(parent.task_id)
            contacts = ExternalNativeEffectContactStore(plane=plane,
                execution_plan=selected.execution_plan,
                visibility_ceiling=selected.visibility_ceiling,
                outcome_access=selected.outcome_access,
                minimum_free_bytes=selected.minimum_free_bytes,
                task_scopes={parent.task_id: (selected.visibility_ceiling, selected.outcome_access)},
                continuation_scopes=tuple(row for row in selected.continuation_scopes if row.task_id == parent.task_id))
            yield ExternalNativeSubworkStore(plane=plane,
                parent_contacts=contacts.for_task(parent.task_id), parent_contact=parent,
                parent_inputs=self.parent_inputs, completed_only=True)

    def _require_completed(self, definition):
        inspection = self.inspect(definition)
        if inspection.has_uncertain_contact:
            raise NativeSubworkUncertainContact(
                "native subwork contacted without a known return; no automatic retry")
        if (inspection.state is not NativeSubworkState.COMPLETED
                or inspection.completion is None or inspection.receipt is None):
            raise ValueError("native output has no authenticated complete subwork receipt")
        return inspection

    def _completed_output_manifest(self, definition, output_id):
        """Select a declared complete product through its actual primary receipt."""
        if type(output_id) is not str or output_id not in {row.output_id for row in definition.outputs}:
            raise ValueError("completed native output is outside its exact declared port census")
        with self._completed_reader(definition.parent_contact) as reader:
            inspection = reader._require_completed(definition)
            logical_id = self._id(definition, "output." + output_id)
            matches = tuple(row for row in inspection.outputs if row.logical.logical_artifact_id == logical_id)
            if len(matches) != 1:
                raise ValueError("completed native output was omitted; a partial prefix is not its product")
            return matches[0]

    def read_definition(self, identity: ObjectIdentity) -> NativeSubworkDefinition:
        """Authenticate original definition metadata without opening its outputs."""
        if type(identity) is not ObjectIdentity or identity.object_schema != NativeSubworkDefinition.SCHEMA:
            raise ValueError("completed native definition requires its exact immutable identity")
        parent = self.parent_contact
        relative = self._definition_path(parent, identity.object_id)
        manifest = self._manifest(relative)
        if manifest is None:
            raise ValueError("completed native definition has no retained exact operands")
        if self.plane.custody_limits.exceeds("control_record_bytes", manifest.materialization.size_bytes):
            raise ValueError("native definition exceeds its selected metadata allowance")
        raw = read_bounded_bytes(self.plane.root.resolve(relative, for_write=False),
            maximum_bytes=manifest.materialization.size_bytes)
        definition = decode_canonical_bytes(raw, NativeSubworkDefinition, maximum_bytes=manifest.materialization.size_bytes)
        if (definition.identity != identity or definition.parent_contact != parent
                or manifest.logical.payload_schema != NativeSubworkDefinition.SCHEMA
                or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or manifest.logical.media_type != 'application/json'
                or manifest.materialization.relative_path != relative
                or len(raw) != manifest.materialization.size_bytes or raw != definition.canonical_bytes()
                or sha256(raw).hexdigest() != manifest.logical.content_sha256
                or sha256(raw).hexdigest() != manifest.materialization.physical_sha256):
            raise ValueError("completed native definition substitutes its exact identity or parent")
        return definition

    def resolve_completed_definition(self, identity: ObjectIdentity) -> NativeSubworkDefinition:
        """Read original definition bytes and authenticate its complete return."""
        with self._completed_reader() as reader:
            definition = reader.read_definition(identity)
            reader._require_completed(definition)
            return definition

    def iter_completed_output(self, definition: NativeSubworkDefinition, output_id: str, *,
                              maximum_chunk_bytes: int = STREAM_CHUNK_BYTES) -> Iterator[bytes]:
        """Authenticate and stream one receipted physical output, with no new effects.

        The exact same contained descriptor is hashed before delivery, then read
        completely and checked again. Buffer size does not limit the output's
        total size. No store path or live creator handle crosses this port.
        """
        if type(maximum_chunk_bytes) is not int or maximum_chunk_bytes <= 0:
            raise ValueError("completed native output requires a positive integer chunk allowance")
        with self._completed_reader(definition.parent_contact) as reader:
            yield from reader._iter_completed_output(definition, output_id,
                maximum_chunk_bytes=maximum_chunk_bytes)

    def _iter_completed_output(self, definition, output_id, *, maximum_chunk_bytes):
        manifest = self._completed_output_manifest(definition, output_id)
        materialization = manifest.materialization
        path = self.plane.root.resolve(materialization.relative_path, for_write=False)
        descriptor, before = _open_contained_regular(
            Path(self.plane.root.contract.canonical_path), path, materialization.size_bytes)
        bound = min(maximum_chunk_bytes, STREAM_CHUNK_BYTES)
        with _stable_descriptor(descriptor, before, operation="completed native output relay"):
            if before.st_size != materialization.size_bytes:
                raise BoundedFileIOError("completed native output changes its exact byte denominator")
            for deliver in (False, True):
                digest = sha256()
                count = 0
                for chunk in _regular_chunks(descriptor, before, maximum_bytes=before.st_size,
                        chunk_bytes=bound, opened_size_bound=True, operation="completed native output relay"):
                    digest.update(chunk)
                    count += len(chunk)
                    if deliver:
                        yield chunk
                if count != materialization.size_bytes or digest.hexdigest() != materialization.physical_sha256:
                    raise BoundedFileIOError("completed native output changes its authenticated complete bytes")
                if not deliver:
                    os.lseek(descriptor, 0, os.SEEK_SET)

    def inspect(self, definition: NativeSubworkDefinition) -> NativeSubworkInspection:
        """Authenticate retained progress without publishing or entering work."""
        if self.completed_only:
            # A bounded read context owns its complete closing byte guard.
            # Keep each native member's checks without rehashing that growing
            # census for every definition. Ordinary scopes remain eager.
            self.plane.require_verification_context()
        return self._inspect(definition)

    def inspect_metadata(self, definition: NativeSubworkDefinition) -> NativeSubworkMetadata:
        """Authenticate retained control/receipt facts without hashing outputs.

        This is a membership census only. Full ``inspect`` and completed output
        readers retain all original body checks after metadata admission.
        """
        if not self.completed_only:
            raise ValueError("native metadata inspection requires a read-only completed store")
        self.plane.require_active_verification_scope()
        observed = self._inspect(definition, _metadata_only=True)
        return NativeSubworkMetadata(observed.definition, observed.completion, observed.receipt,
            observed.outputs, observed.partial_outputs, observed.call_entry, observed.call_return)

    def _inspect(self, definition: NativeSubworkDefinition, *, finalize=False,
                 _metadata_only=False) -> NativeSubworkInspection:
        if finalize:
            self._require_progress_mutation()
        self._assert_parent(definition)
        roster = self.read_roster(definition.parent_contact, definition.roster_id)
        actual, definition_manifest = self._control(definition, "definition", NativeSubworkDefinition,
            self._parents(definition.parent_contact.execution_plan))
        if definition_manifest is None:
            if roster is not None and any(row.object_id == definition.subwork_id for row in roster.subworks):
                raise NativeSubworkUncertainContact("native subwork selected definition is missing; no retry")
            self._assert_no_later_progress(definition, ("begin", "contact", "completion"))
            # A later member without its definition is orphaned custody, never a fresh slot.
            root = self.plane.root.resolve(self._root(definition), for_write=False)
            if root.exists() and any(root.iterdir()):
                raise NativeSubworkUncertainContact("native subwork definition is missing; no retry")
            return NativeSubworkInspection(definition, NativeSubworkState.NOT_ENTERED)
        if actual != definition:
            raise ValueError("native subwork substitutes source, inputs, operation, stream or output census")
        if roster is None or definition.identity not in roster.subworks:
            raise ValueError("native subwork definition is outside its retained selected denominator")
        begin, begin_manifest = self._control(definition, "begin", NativeSubworkBegin, self._parents(definition.identity))
        if begin is None:
            self._assert_no_later_progress(definition, ("contact", "completion"))
            return NativeSubworkInspection(definition, NativeSubworkState.NOT_ENTERED)
        if begin != NativeSubworkBegin(definition.identity):
            raise ValueError("native subwork begin changes its exact definition")
        begin_identity = ObjectIdentity.from_record(self._id(definition, "begin"), begin)
        contact, contact_manifest = self._control(definition, "contact", NativeSubworkContact, self._parents(begin_identity))
        if contact is None:
            self._assert_no_later_progress(definition, ("completion",))
            return NativeSubworkInspection(definition, NativeSubworkState.BEGUN, begin)
        if contact != NativeSubworkContact(begin_identity):
            raise ValueError("native subwork contact changes its exact begin record")
        contact_identity = ObjectIdentity.from_record(self._id(definition, "contact"), contact)
        call_entry, call_return, call_manifests = self._call_facts(definition, contact_identity)
        completion, completion_manifest = self._control(definition, "completion", NativeSubworkCompletion,
            self._parents(definition.identity, contact_identity))
        outputs = []
        partials, partial_records, partial_metadata = [], [], []
        for output in definition.outputs:
            manifest = self._manifest(self._root(definition) + "/outputs/" + output.output_id,
                _metadata_only=_metadata_only)
            if manifest is not None:
                self._validate_output(definition, contact_identity, output, manifest)
                outputs.append(manifest)
            partial, metadata, record = self._partial(definition, contact_identity, output,
                _metadata_only=_metadata_only)
            if partial is not None:
                partials.append(partial)
                partial_metadata.append(metadata)
                partial_records.append(record)
        if completion is not None:
            self._validate_completion(definition, contact_identity, completion, tuple(outputs))
            self._validate_call_completion(call_entry, call_return, completion.operational_status)
            if partials and completion.operational_status is OperationalStatus.SUCCEEDED:
                raise ValueError("successful native subwork retains an incomplete scientific output")
        run, task, attempt = self._receipt_locator(definition)
        try:
            receipt = self.receipts.read(run, task, attempt)
        except ArtifactIdentityConflict:
            if not finalize or completion is None:
                raise
            # The exact ordinary publication below may finish its own interrupted
            # receipt pair. Foreign or changed residue still refuses in commit.
            receipt = None
        expected = None
        if completion is not None and completion_manifest is not None:
            expected = self._completion_receipt(definition, definition_manifest, begin_manifest,
                contact_manifest, completion, completion_manifest, tuple(outputs),
                tuple((*partials, *partial_metadata)), call_manifests)
        if receipt is None and finalize and expected is not None:
            # Only the durable known return and complete authenticated census can
            # supply a receipt. No live creator or native-entry token is restored.
            self.plane.require_verification_snapshot()
            self._assert_parent(definition)
            try:
                self.receipts.commit(expected, visibility_ceiling=self.visibility, outcome_access=self.access)
            except OSError as error:
                raise NativeSubworkReceiptPublicationPending(
                    "durable known native return has an interrupted receipt publication") from error
            receipt = self.receipts.read(run, task, attempt)
            if receipt is None:
                raise ValueError("native subwork completion receipt did not survive exact recovery")
        if receipt is None:
            return NativeSubworkInspection(definition, NativeSubworkState.UNKNOWN_COMPLETION,
                begin, contact, completion, outputs=tuple(outputs), partial_outputs=tuple(partials),
                partial_output_records=tuple(partial_records), call_entry=call_entry, call_return=call_return)
        if completion is None or completion_manifest is None:
            raise ValueError("native subwork receipt lacks its exact completion metadata")
        if receipt != expected:
            raise ValueError("native subwork receipt changes exact source, inputs, outputs or outcome")
        return NativeSubworkInspection(definition, NativeSubworkState.COMPLETED,
            begin, contact, completion, receipt, tuple(outputs), tuple(partials), tuple(partial_records),
            call_entry, call_return)

    def _call_facts(self, definition, contact_identity):
        if self._manifest(self._root(definition) + "/call-entry.json") is None:
            if self._manifest(self._root(definition) + "/call-return.json") is not None:
                raise NativeSubworkUncertainContact("native raw return lost its original call entry")
            return None, None, ()
        invocation = self.read_prepared_invocation(definition.parent_contact)
        if invocation is None:
            raise ValueError("native call entry lost its original prepared invocation")
        call_entry, entry_manifest = self._control(definition, "call-entry", NativeSubworkCallEntry,
            self._parents(definition.identity, contact_identity, invocation.identity))
        if (call_entry.definition != definition.identity
                or call_entry.contact != contact_identity or call_entry.invocation != invocation.identity):
            raise ValueError("native call entry substitutes its exact definition, contact or invocation")
        entry_identity = ObjectIdentity.from_record(self._id(definition, "call-entry"), call_entry)
        call_return, return_manifest = self._control(definition, "call-return", NativeSubworkCallReturn,
            self._parents(entry_identity))
        if call_return is not None and call_return.entry != entry_identity:
            raise ValueError("native raw return substitutes its exact observed entry")
        invocation_manifest = self._manifest(self._invocation_path(definition.parent_contact))
        return call_entry, call_return, tuple(row for row in
            (invocation_manifest, entry_manifest, return_manifest) if row is not None)

    @staticmethod
    def _validate_call_completion(call_entry, call_return, status):
        if call_entry is None:
            return
        if call_return is None:
            raise ValueError("native completion lacks its observed raw call return")
        raw_failed = call_return.error_type is not None or call_return.return_code not in (None, 0)
        if raw_failed != (status is OperationalStatus.FAILED):
            raise ValueError("native completion confuses raw native return with later publication failure")

    def _assert_no_later_progress(self, definition, names):
        progress_names = (*names, "call-entry", "call-return",
            *("partial-output." + output.output_id for output in definition.outputs))
        if any(self._manifest(self._root(definition) + "/" + name + ".json") is not None
               for name in progress_names):
            raise NativeSubworkUncertainContact("native subwork lost an earlier progress record; no retry")
        for name in ("outputs", "partial-outputs"):
            root = self.plane.root.resolve(self._root(definition) + "/" + name, for_write=False)
            if root.exists() and any(root.iterdir()):
                raise NativeSubworkUncertainContact("native subwork retained outputs without earlier progress; no retry")
        if self.receipts.read(*self._receipt_locator(definition)) is not None:
            raise NativeSubworkUncertainContact("native subwork retained a receipt without earlier progress; no retry")

    def _partial(self, definition, contact_identity, output, *, _metadata_only=False):
        name = "partial-output." + output.output_id
        record, metadata = self._control(definition, name, NativeSubworkPartialOutput,
            self._parents(definition.identity, contact_identity))
        prefix = self._manifest(self._root(definition) + "/partial-outputs/" + output.output_id,
            _metadata_only=_metadata_only)
        if record is None and prefix is None:
            return None, None, None
        if record is None or prefix is None:
            raise NativeSubworkUncertainContact("native subwork partial output publication is incomplete; no retry")
        logical = prefix.logical
        if (record.definition != definition.identity or record.contact != contact_identity
                or record.output_id != output.output_id
                or logical.logical_artifact_id != self._id(definition, "partial-prefix." + output.output_id)
                or logical.payload_schema != "empirical-lawhood/runtime/native-subwork-received-prefix"
                or logical.profile is not ArtifactProfile.NATIVE_SUBWORK_PREFIX
                or logical.media_type != "application/octet-stream"
                or logical.lineage_parents != self._parents(definition.identity, contact_identity)
                or (prefix.materialization.size_bytes, prefix.materialization.physical_sha256)
                    != (record.received_size_bytes, record.received_physical_sha256)):
            raise ValueError("partial native output changes its exact received prefix or selected port")
        return prefix, metadata, record

    def retain_partial_output(self, entry, record: NativeSubworkPartialOutput, chunks: Iterable[bytes]):
        """Retain transport prefixes separately; never validate them as complete arrays."""
        self._entry(entry)
        definition = entry.definition
        if (type(record) is not NativeSubworkPartialOutput or record.definition != definition.identity
                or record.contact != self._contact_identity(entry)
                or record.output_id not in {output.output_id for output in definition.outputs}
                or record.output_id in entry.outputs or record.output_id in entry.partials):
            raise ValueError("native partial output is outside its actual entered port")
        parents = self._parents(definition.identity, self._contact_identity(entry))
        root = self._root(definition)
        relative = root + "/partial-outputs/" + record.output_id
        self.plane.write_stream(ArtifactStreamWriteRequest(
            self._id(definition, "partial-prefix." + record.output_id), relative,
            "empirical-lawhood/runtime/native-subwork-received-prefix", ArtifactProfile.NATIVE_SUBWORK_PREFIX,
            "application/octet-stream", self._id(definition, "partial-outputs"), root + "/partial-outputs", chunks,
            maximum_bytes=max(1, record.received_size_bytes),
            maximum_chunk_bytes=min(1024 * 1024, max(1, record.received_size_bytes)),
            expected_size_bytes=record.received_size_bytes,
            expected_physical_sha256=record.received_physical_sha256,
            visibility_ceiling=self.visibility,
            parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in parents),
            outcome_access=self.access, lineage_parents=parents, minimum_free_bytes=self.minimum_free_bytes))
        self._write_control(definition, "partial-output." + record.output_id, record, parents)
        output = next(row for row in definition.outputs if row.output_id == record.output_id)
        prefix, metadata, _ = self._partial(definition, self._contact_identity(entry), output)
        entry.partials[record.output_id] = (prefix, metadata)

    def iter_inspections(self, definitions: Iterable[NativeSubworkDefinition]) -> Iterator[NativeSubworkInspection]:
        """Retain the selected full denominator without loading scientific payloads."""
        for definition in definitions:
            yield self.inspect(definition)

    def recover(self, definition: NativeSubworkDefinition) -> NativeSubworkInspection | None:
        """Finish receipt publication from a durable known return, without acquisition.

        Inspection remains read-only. Recovery authenticates the whole retained
        census inside one guarded lifetime before publishing the same receipt as
        complete(). A known raw return with incomplete completion/output custody
        stays pending; an unobserved return stays uncertain. Neither grants entry.
        """
        if self.completed_only:
            self.plane.require_verification_snapshot()
            inspection = self.inspect(definition)
        else:
            with self.plane.verification_scope() as plane:
                reader = ExternalNativeSubworkStore(plane=plane, parent_contacts=self.parent_contacts,
                    parent_contact=self._bound_parent, parent_inputs=self.parent_inputs)
                inspection = reader._inspect(definition, finalize=True)
        if inspection.state is NativeSubworkState.UNKNOWN_COMPLETION:
            if inspection.native_return_status is not None:
                raise NativeSubworkReceiptPublicationPending(
                    "known native return lacks complete durable completion/output custody; no automatic retry")
            raise NativeSubworkUncertainContact("native subwork contacted without exact receipt; no automatic retry")
        return inspection if inspection.state is NativeSubworkState.COMPLETED else None

    def begin(self, definition: NativeSubworkDefinition,
              inputs: tuple[ArtifactManifest, ...] | None = None) -> _NativeSubworkEntry:
        self._require_progress_mutation()
        self._assert_parent(definition)
        if inputs is None:
            by_id = {manifest.materialization.materialization_id: manifest for manifest in self.parent_inputs}
            if not set(definition.input_materialization_ids).issubset(by_id):
                raise ValueError("native subwork input is outside its coordinator-held parent census")
            inputs = tuple(by_id[value] for value in definition.input_materialization_ids)
        validate_native_subwork_inputs(self.plane, definition, inputs,
            visibility=self.visibility, access=self.access,
            frozen_parent_inputs=self.parent_inputs or None)
        prior = self.inspect(definition)
        if prior.state is NativeSubworkState.COMPLETED:
            raise ValueError("native subwork already completed; reuse its exact receipt")
        if prior.state is NativeSubworkState.UNKNOWN_COMPLETION:
            if prior.native_return_status is not None:
                raise NativeSubworkReceiptPublicationPending(
                    "native subwork already returned with incomplete durable finalization; no automatic retry")
            raise NativeSubworkUncertainContact("native subwork already contacted; no automatic retry")
        self._assert_live_parent(definition)
        roster = self.read_roster(definition.parent_contact, definition.roster_id)
        if roster is None or definition.identity not in roster.subworks:
            raise ValueError("native subwork entry is outside its frozen selected denominator")
        if roster.parent_subwork is not None:
            parent_entry = self._conditional_parents.get(roster.roster_id)
            self._entry(parent_entry)
            if parent_entry.definition.identity != roster.parent_subwork:
                raise ValueError("conditional native subwork entry substitutes its live parent")
        manifest, _ = self._write_control(definition, "begin", NativeSubworkBegin(definition.identity),
            self._parents(definition.identity))
        return _NativeSubworkEntry(self._owner, definition, manifest)

    def _entry(self, entry: _NativeSubworkEntry, *, contacted: bool = True) -> None:
        self._require_progress_mutation()
        if type(entry) is not _NativeSubworkEntry or entry.owner is not self._owner or entry.completed:
            raise ValueError("native subwork entry belongs to another creator or is completed")
        self._assert_live_parent(entry.definition)
        if contacted and entry.contact_manifest is None:
            raise ValueError("native subwork output/completion precedes creating native contact")

    def contact(self, entry: _NativeSubworkEntry) -> None:
        """Must complete before invoking the native subcall; only the creator enters."""
        self._entry(entry, contacted=False)
        if entry.contact_manifest is not None:
            raise NativeSubworkUncertainContact("native subwork contact already entered; no repeat")
        if self.inspect(entry.definition).state is not NativeSubworkState.BEGUN:
            raise NativeSubworkUncertainContact(
                "native subwork contact reused or creating begin is no longer intact; only creating publisher may enter")
        begin = NativeSubworkBegin(entry.definition.identity)
        begin_identity = ObjectIdentity.from_record(self._id(entry.definition, "begin"), begin)
        self._persist_prepared_invocation(entry.definition.parent_contact)
        if self.before_contact is not None:
            self.before_contact(entry.definition)
        manifest, created = self._write_control(entry.definition, "contact", NativeSubworkContact(begin_identity),
            self._parents(begin_identity))
        if created is not True:
            raise NativeSubworkUncertainContact("native subwork contact reused; only creating publisher may enter")
        entry.contact_manifest = manifest

    def call_entry(self, entry: _NativeSubworkEntry, *, at_utc: str) -> None:
        """Retain the observed invocation boundary before its actual native call."""
        self._entry(entry)
        invocation = self.read_prepared_invocation(entry.definition.parent_contact)
        if invocation is None or invocation != self.prepared_invocation:
            raise ValueError("native call entry lacks its actual original prepared invocation")
        if entry.call_entry_manifest is not None:
            raise NativeSubworkUncertainContact("native call entry already observed; no duplicate invocation")
        begin = NativeSubworkBegin(entry.definition.identity)
        begin_identity = ObjectIdentity.from_record(self._id(entry.definition, "begin"), begin)
        contact, manifest = self._control(entry.definition, "contact", NativeSubworkContact,
            self._parents(begin_identity))
        if (contact != NativeSubworkContact(begin_identity) or manifest is None
                or manifest.materialization != entry.contact_manifest.materialization):
            raise ValueError("native call entry lost its exact retained creating contact")
        record = NativeSubworkCallEntry(entry.definition.identity, self._contact_identity(entry),
            invocation.identity, at_utc)
        if self.before_contact is not None:
            self.before_contact(entry.definition)
        manifest, created = self._write_control(entry.definition, "call-entry", record,
            self._parents(record.definition, record.contact, record.invocation))
        if created is not True:
            raise NativeSubworkUncertainContact("native call entry reused; only its original publisher may invoke")
        entry.call_entry_manifest = manifest

    def call_return(self, entry: _NativeSubworkEntry, *, at_utc: str,
                    error_type: str | None = None, return_code: int | None = None) -> None:
        """Retain raw return/error before classification, arrays and output custody."""
        self._entry(entry)
        if entry.call_entry_manifest is None or entry.call_return_manifest is not None:
            raise ValueError("native raw return lacks one original unreturned call entry")
        call_entry, _, _ = self._call_facts(entry.definition, self._contact_identity(entry))
        if call_entry is None:
            raise ValueError("native raw return lost its original call entry")
        record = NativeSubworkCallReturn(
            ObjectIdentity.from_record(self._id(entry.definition, "call-entry"), call_entry), at_utc, error_type, return_code)
        manifest, created = self._write_control(entry.definition, "call-return", record, self._parents(record.entry))
        if created is not True:
            raise ValueError("native raw return observation already published")
        entry.call_return_manifest = manifest

    def _contact_identity(self, entry):
        begin = NativeSubworkBegin(entry.definition.identity)
        contact = NativeSubworkContact(ObjectIdentity.from_record(self._id(entry.definition, "begin"), begin))
        return ObjectIdentity.from_record(self._id(entry.definition, "contact"), contact)

    def _validate_output(self, definition, contact_identity, output, manifest):
        logical = manifest.logical
        if (logical.logical_artifact_id != self._id(definition, "output." + output.output_id)
                or (logical.payload_schema, logical.profile, logical.media_type)
                != (output.payload_schema, output.profile, output.media_type)
                or logical.semantic_validation != output.semantic_validation
                or logical.lineage_parents != self._parents(definition.identity, contact_identity)):
            raise ValueError("native subwork output changes its selected port or contact lineage")

    def publish_output(self, entry: _NativeSubworkEntry, output_id: str, chunks: Iterable[bytes], *,
                       maximum_bytes: int, maximum_chunk_bytes: int = 1024 * 1024,
                       expected_size_bytes: int | None = None,
                       expected_physical_sha256: str | None = None) -> ArtifactManifest:
        self._entry(entry)
        selected = tuple(output for output in entry.definition.outputs if output.output_id == output_id)
        if len(selected) != 1 or output_id in entry.outputs:
            raise ValueError("native subwork output is undeclared or already published")
        chunk_bound = _output_chunk_bound(maximum_bytes, maximum_chunk_bytes,
            expected_size_bytes, expected_physical_sha256)
        output = selected[0]
        parents = self._parents(entry.definition.identity, self._contact_identity(entry))
        root = self._root(entry.definition)
        relative = root + "/outputs/" + output_id
        result = self.plane.write_stream(ArtifactStreamWriteRequest(
            self._id(entry.definition, "output." + output_id), relative,
            output.payload_schema, output.profile, output.media_type,
            self._id(entry.definition, "outputs"), root + "/outputs",
            _output_chunks(chunks, maximum_chunk_bytes, chunk_bound),
            maximum_bytes=maximum_bytes, maximum_chunk_bytes=chunk_bound,
            expected_size_bytes=expected_size_bytes, expected_physical_sha256=expected_physical_sha256,
            visibility_ceiling=self.visibility,
            parent_visibility_ceilings=tuple(parent.visibility_ceiling for parent in parents),
            outcome_access=self.access, lineage_parents=parents,
            minimum_free_bytes=self.minimum_free_bytes,
            semantic_validation=output.semantic_validation,
        ))
        manifest = self._manifest(relative)
        if manifest is None or manifest.materialization != result.materialization:
            raise ValueError("native subwork output publication is incomplete")
        self._validate_output(entry.definition, self._contact_identity(entry), output, manifest)
        entry.outputs[output_id] = manifest
        return manifest

    def _validate_completion(self, definition, contact_identity, completion, outputs):
        by_logical_id = {
            self._id(definition, 'output.' + output.output_id): output.output_id
            for output in definition.outputs
        }
        returned = tuple(sorted(by_logical_id[output.logical.logical_artifact_id] for output in outputs))
        omitted = tuple(output.output_id for output in definition.outputs if output.output_id not in returned)
        streams = tuple(sorted((*completion.consumed_streams, *completion.unconsumed_streams,
            *completion.unknown_streams), key=lambda stream: stream.object_id))
        if (completion.definition != definition.identity or completion.contact != contact_identity
                or completion.output_ids != returned or completion.omitted_output_ids != omitted
                or streams != definition.streams):
            raise ValueError("native subwork completion changes exact output/stream denominator")

    def _completion_receipt(self, definition, definition_manifest, begin_manifest,
                            contact_manifest, completion, completion_manifest, outputs, partials,
                            call_manifests=()):
        """Derive ordinary completion custody solely from authenticated publications."""
        manifests = tuple(sorted((*outputs, *partials, completion_manifest),
            key=lambda manifest: manifest.logical.logical_artifact_id))
        run, task, attempt = self._receipt_locator(definition)
        return CanonicalTaskReceipt("receipt." + attempt, run, task, attempt,
            definition.parent_contact.implementation_commit,
            tuple(sorted((*definition.input_materialization_ids, definition_manifest.materialization.materialization_id,
                begin_manifest.materialization.materialization_id, contact_manifest.materialization.materialization_id,
                *(row.materialization.materialization_id for row in call_manifests)))),
            tuple(manifest.materialization for manifest in manifests), tuple(manifest.logical for manifest in manifests),
            (ReceiptCheck("native-subwork-exact-completion-census", True, ()),),
            completion.operational_status, completion.reason_codes)

    def complete(self, entry: _NativeSubworkEntry, *, operational_status: OperationalStatus,
                 cost: InquiryCost, cost_scope: str, consumed_streams: tuple[ObjectIdentity, ...] = (),
                 unconsumed_streams: tuple[ObjectIdentity, ...] = (), unknown_streams: tuple[ObjectIdentity, ...] = (),
                 peak_rss_bytes: int | None = None, reason_codes: tuple[str, ...] = ()) -> NativeSubworkInspection:
        self._entry(entry)
        definition = entry.definition
        if entry.partials and operational_status is OperationalStatus.SUCCEEDED:
            raise ValueError("successful native subwork retains an incomplete scientific output")
        completion = NativeSubworkCompletion(definition.identity, self._contact_identity(entry), operational_status,
            tuple(sorted(entry.outputs)), tuple(output.output_id for output in definition.outputs if output.output_id not in entry.outputs),
            consumed_streams, unconsumed_streams, unknown_streams, cost, cost_scope, peak_rss_bytes, reason_codes)
        self._validate_completion(definition, self._contact_identity(entry), completion, tuple(entry.outputs.values()))
        call_entry, call_return, call_manifests = self._call_facts(definition, self._contact_identity(entry))
        self._validate_call_completion(call_entry, call_return, operational_status)
        manifest, _ = self._write_control(definition, "completion", completion,
            self._parents(definition.identity, self._contact_identity(entry)))
        _, definition_manifest = self._control(definition, "definition", NativeSubworkDefinition,
            self._parents(definition.parent_contact.execution_plan))
        receipt = self._completion_receipt(definition, definition_manifest, entry.begin_manifest,
            entry.contact_manifest, completion, manifest, tuple(entry.outputs.values()),
            tuple(member for pair in entry.partials.values() for member in pair), call_manifests)
        self.receipts.commit(receipt, visibility_ceiling=self.visibility, outcome_access=self.access)
        actual = self.inspect(definition)
        if actual.state is not NativeSubworkState.COMPLETED or actual.receipt != receipt:
            raise ValueError("native subwork completion receipt did not survive exact recovery")
        entry.completed = True
        return actual
