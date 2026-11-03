# SPDX-License-Identifier: MPL-2.0
"""Immutable native-contact markers in the existing guarded artifact plane."""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256

from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.bounded_io import MAX_ARTIFACT_MANIFEST_BYTES, read_bounded_bytes
from empirical_lawhood.infrastructure.file_locks import exclusive_file_lock
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_effects import NativeEffectContact


MAX_NATIVE_CONTACT_BYTES = 1024 * 1024


class ExternalNativeEffectContactStore:
    """A persisted contact without a completion receipt conservatively stops."""

    def __init__(self, *, plane: ExternalArtifactPlane, execution_plan: ObjectIdentity,
                 visibility_ceiling: VisibilityCeiling, outcome_access: OutcomeAccess,
                 minimum_free_bytes: int = 0,
                 task_scopes: Mapping[str, tuple[VisibilityCeiling, OutcomeAccess]] | None = None,
                 continuation_scopes: tuple = ()):
        if not isinstance(plane, ExternalArtifactPlane):
            raise TypeError("native contact requires the guarded artifact plane")
        if minimum_free_bytes < 0:
            raise ValueError("native contact free-space floor must be nonnegative")
        self.plane, self.execution_plan = plane, execution_plan
        self.visibility_ceiling, self.outcome_access = visibility_ceiling, outcome_access
        self.minimum_free_bytes = minimum_free_bytes
        from empirical_lawhood.runtime.native_continuation_execution import NativeContinuationCustodyScope
        if (type(continuation_scopes) is not tuple
                or any(type(row) is not NativeContinuationCustodyScope for row in continuation_scopes)
                or len({row.task_id for row in continuation_scopes}) != len(continuation_scopes)):
            raise TypeError('native contact requires exact unique continuation custody scopes')
        for scope in continuation_scopes:
            scope.__post_init__()
            if (scope.original_contact.execution_plan != execution_plan
                    or visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                    or outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
                raise ValueError('native continuation custody changes its original exposed development plan')
        self.continuation_scopes = continuation_scopes
        self._continuations = {row.task_id: row for row in continuation_scopes}
        # Runtime ownership is separate from authenticated historical custody.
        # Fresh readers never acquire a live launch merely by finding its bytes.
        self._live_creators: set[tuple[str, str, str]] = set()
        self._selected_task_id: str | None = None
        self._task_stores: dict[str, ExternalNativeEffectContactStore] | None = None
        if task_scopes is not None:
            if not isinstance(task_scopes, Mapping) or not task_scopes:
                raise ValueError("native contact task scopes require a nonempty exact task roster")
            stores = {}
            for task_id, scope in task_scopes.items():
                validate_stable_id(task_id, field_name="native_effect_task_id")
                if (type(scope) is not tuple or len(scope) != 2
                        or type(scope[0]) is not VisibilityCeiling or type(scope[1]) is not OutcomeAccess):
                    raise TypeError("native contact task scope requires exact custody labels")
                store = ExternalNativeEffectContactStore(plane=plane, execution_plan=execution_plan,
                    visibility_ceiling=scope[0], outcome_access=scope[1], minimum_free_bytes=minimum_free_bytes,
                    continuation_scopes=tuple(row for row in continuation_scopes if row.task_id == task_id))
                store._selected_task_id = task_id
                stores[task_id] = store
            self._task_stores = stores
            if not set(self._continuations) <= set(stores):
                raise ValueError('native continuation custody leaves its selected native task roster')

    def custody_root(self, run_id, task_id):
        validate_stable_id(run_id)
        validate_stable_id(task_id)
        scope = self._continuations.get(task_id)
        if scope is None:
            return f'runs/{run_id}'
        if scope.original_contact.run_id != run_id:
            raise ValueError('native continuation custody substitutes its original run')
        return scope.relative_root

    def storage_key(self, run_id, task_id, original_key):
        self.custody_root(run_id, task_id)
        scope = self._continuations.get(task_id)
        return original_key if scope is None else scope.storage_key(original_key)

    def relative_path(self, run_id, task_id):
        return self.custody_root(run_id, task_id) + '/native-contacts/' + sha256(task_id.encode()).hexdigest() + '.json'

    def _require_continuation_contact(self, contact):
        scope = self._continuations.get(contact.task_id)
        if scope is not None and contact != scope.expected_contact:
            raise ValueError('native continuation contact changes its one separate attempt or original operands')

    def _lineage(self, run_id, task_id):
        parents = [ArtifactLineageParent(self.execution_plan, self.visibility_ceiling, self.outcome_access)]
        scope = self._continuations.get(task_id)
        if scope is not None:
            self.custody_root(run_id, task_id)
            parents.append(ArtifactLineageParent(scope.continuation, self.visibility_ceiling, self.outcome_access))
        from empirical_lawhood.runtime.artifacts import lineage_parent_sort_key
        return tuple(sorted(parents, key=lineage_parent_sort_key))

    def for_task(self, task_id: str) -> "ExternalNativeEffectContactStore":
        """Select this launch's existing store for one frozen native task.

        The run lock stays on the same root. Views retain their own live-creator
        capability, so a historical reader never gains entry by selecting one.
        """
        validate_stable_id(task_id, field_name="native_effect_task_id")
        if self._selected_task_id is not None and task_id != self._selected_task_id:
            raise ValueError("native contact scope view belongs to another exact frozen task")
        if self._task_stores is None:
            return self
        try:
            return self._task_stores[task_id]
        except KeyError as error:
            raise ValueError("native contact task is absent from its exact frozen scope roster") from error

    def is_live_creator(self, contact: NativeEffectContact) -> bool:
        self.for_task(contact.task_id)
        if self._task_stores is not None:
            return self.for_task(contact.task_id).is_live_creator(contact)
        key = (contact.run_id, contact.task_id, contact.fingerprint())
        return key in self._live_creators and self.read(contact.run_id, contact.task_id) == contact

    def retire_live_creator(self, contact: NativeEffectContact) -> None:
        """End this launch's progress capability without altering historical bytes."""
        self.for_task(contact.task_id)
        if self._task_stores is not None:
            self.for_task(contact.task_id).retire_live_creator(contact)
            return
        self._live_creators.discard((contact.run_id, contact.task_id, contact.fingerprint()))

    @contextmanager
    def execution_lock(self, run_id: str) -> Iterator[None]:
        """Refuse another live launch before it can alter shared run custody.

        The zero-byte lock is coordination, not a completion or retry grant.
        Process death releases flock; retained unreceipted contacts still stop
        recovery. Opening an existing lock read-only preserves its bytes/mtime.
        """
        validate_stable_id(run_id, field_name="run_id")
        relative = f"runs/{run_id}/.native-execution.lock"
        path = self.plane.root.resolve(relative, for_write=True,
            operation_minimum_free_bytes=self.minimum_free_bytes)
        path.parent.mkdir(parents=True, exist_ok=True)
        path = self.plane.root.resolve(relative, for_write=True,
            operation_minimum_free_bytes=self.minimum_free_bytes)
        with exclusive_file_lock(path, blocking=False):
            yield

    @staticmethod
    def _path(run_id: str, task_id: str) -> str:
        validate_stable_id(run_id, field_name="run_id")
        validate_stable_id(task_id, field_name="task_id")
        return f"runs/{run_id}/native-contacts/{sha256(task_id.encode()).hexdigest()}.json"

    def read(self, run_id: str, task_id: str) -> NativeEffectContact | None:
        self.for_task(task_id)
        if self._task_stores is not None:
            return self.for_task(task_id).read(run_id, task_id)
        relative = self.relative_path(run_id, task_id)
        path = self.plane.root.resolve(relative, for_write=False)
        manifest_path = self.plane.root.resolve(relative + ".manifest.json", for_write=False)
        if not path.exists() and not manifest_path.exists():
            return None
        if not path.is_file() or not manifest_path.is_file():
            raise ValueError("native contact publication is partial; effects cannot be repeated")
        manifest = decode_artifact_manifest(read_bounded_bytes(manifest_path, maximum_bytes=MAX_ARTIFACT_MANIFEST_BYTES))
        parents = self._lineage(run_id, task_id)
        if (manifest.materialization.relative_path != relative
            or manifest.logical.payload_schema != NativeEffectContact.SCHEMA
            or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or manifest.logical.media_type != "application/json"
            or manifest.logical.visibility_ceiling is not self.visibility_ceiling
            or manifest.logical.outcome_access is not self.outcome_access
            or manifest.logical.lineage_parents != parents
            or manifest.materialization.size_bytes > MAX_NATIVE_CONTACT_BYTES):
            raise ValueError("native contact changes its plan, path, access role or bounded contract")
        self.plane.verify_manifest(manifest)
        raw = read_bounded_bytes(path, maximum_bytes=MAX_NATIVE_CONTACT_BYTES)
        if (len(raw) != manifest.materialization.size_bytes
            or sha256(raw).hexdigest() != manifest.materialization.physical_sha256
            or sha256(raw).hexdigest() != manifest.logical.content_sha256):
            raise ValueError("native contact bytes differ from authenticated custody")
        contact = decode_canonical_bytes(raw, NativeEffectContact, maximum_bytes=MAX_NATIVE_CONTACT_BYTES)
        if (contact.run_id, contact.task_id, contact.execution_plan) != (run_id, task_id, self.execution_plan):
            raise ValueError("native contact substitutes its exact run, task or plan")
        self._require_continuation_contact(contact)
        return contact

    def begin(self, contact: NativeEffectContact) -> None:
        self.for_task(contact.task_id)
        if self._task_stores is not None:
            self.for_task(contact.task_id).begin(contact)
            return
        if contact.execution_plan != self.execution_plan:
            raise ValueError("native contact belongs to another compiled plan")
        self._require_continuation_contact(contact)
        scope = self._continuations.get(contact.task_id)
        if scope is not None:
            original = ExternalNativeEffectContactStore(plane=self.plane, execution_plan=self.execution_plan,
                visibility_ceiling=self.visibility_ceiling, outcome_access=self.outcome_access,
                minimum_free_bytes=self.minimum_free_bytes)
            if original.read(contact.run_id, contact.task_id) != scope.original_contact:
                raise ValueError('native continuation loses its unchanged original contact')
        if self.read(contact.run_id, contact.task_id) is not None:
            raise ValueError("native contact is already committed; no completion grants no retry")
        raw = contact.canonical_bytes()
        if len(raw) > MAX_NATIVE_CONTACT_BYTES:
            raise ValueError("native contact input census exceeds its bound")
        parents = self._lineage(contact.run_id, contact.task_id)
        relative = self.relative_path(contact.run_id, contact.task_id)
        key = self.storage_key(contact.run_id, contact.task_id, sha256(contact.task_id.encode()).hexdigest())
        publication_id = f'native-contact.{contact.run_id}.{key}'
        publication_root = self.custody_root(contact.run_id, contact.task_id) + '/native-contacts'
        scope_id = f'native-contacts.{contact.run_id}' if scope is None else publication_id
        publication = self.plane.write(ArtifactWriteRequest(
            publication_id, relative,
            NativeEffectContact.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            scope_id, publication_root, raw,
            self.visibility_ceiling, tuple(parent.visibility_ceiling for parent in parents), self.outcome_access,
            lineage_parents=parents, minimum_free_bytes=self.minimum_free_bytes))
        # The initial read can race another launch. The guarded writer locks
        # publication across processes; matching reused bytes grant no effect
        # entry to a second launch, even when its catalog is independent.
        if publication.created is not True:
            raise ValueError("native contact publication was reused; only its creating launch may enter the worker")
        if self.read(contact.run_id, contact.task_id) != contact:
            raise ValueError("native contact did not survive exact custody verification")
        self._live_creators.add((contact.run_id, contact.task_id, contact.fingerprint()))
