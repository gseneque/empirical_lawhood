# SPDX-License-Identifier: MPL-2.0
"""Authenticate actual current issued tasks and their persisted input custody.

This API service uses the existing issue, authority, plan and receipt owners.
Actual effect/access boundaries recheck current grants and exact source custody;
immutable facts may share one finite read context. No authorization is cached.
Domain services retain their scientific scope and companion-record checks.
"""

from contextlib import contextmanager, ExitStack
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from functools import wraps
from threading import RLock
from pathlib import Path

from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader, authenticate_current_execution_plan, authenticate_task_dispatch_authority
from empirical_lawhood.api.models import ExperimentPackage
from empirical_lawhood.api.recursive_qualified_parents import _actual_package
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.study_issue import (
    ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore,
    PROGRAMME_EXECUTION_GRANTEE_ID, PROGRAMME_ISSUE_GRANTEE_ID, PROGRAMME_REVEAL_GRANTEE_ID,
)
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.planning.study_issue import StudyAuthorityKind, require_study_authority
from empirical_lawhood.runtime.adjudication import MAX_ADJUDICATION_BYTES, ScientificAdjudicationOutputContract, ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import artifact_custody_limits, most_restrictive_outcome_access
from empirical_lawhood.runtime.execution import TaskContext, VerifiedArtifactInput, WorkerInputBinding, WorkerInputKind, WorkerOutputPort
from empirical_lawhood.runtime.plans import BarrierKind
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

from .development_task_reads import DevelopmentTaskReadScopes, development_read_call


def _provider_input_specs(plan):
    """Complete pinned external census, independent of caller-selected sidecars."""
    from empirical_lawhood.runtime.plans import ExecutionPlan, ExternalInputSpec
    from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges
    if type(plan) is not ExecutionPlan:
        raise TypeError("issued provider inputs require their actual frozen execution plan")
    result = {}
    for task in plan.tasks:
        scientific = validated_task_scientific_input_edges(task)
        scientific_external_ids = {edge.operational_logical_artifact_id for edge in scientific
            if edge.external_input_id is not None}
        for spec in task.external_inputs:
            # Current prospective scientific sources freeze an exact content
            # identity but deliberately leave width nullable. CONFIGURATION
            # remains fully pinned by the shared compiler-owned validator.
            nullable_scientific_width = (spec.logical_artifact_id in scientific_external_ids
                and spec.expected_size_bytes is None)
            if (type(spec) is not ExternalInputSpec or spec.expected_content_sha256 is None
                    or spec.expected_payload_schema is None or spec.expected_media_type is None
                    or not nullable_scientific_width and (type(spec.expected_size_bytes) is not int
                        or spec.expected_size_bytes <= 0)
                    or type(spec.expected_outcome_access) is not OutcomeAccess
                    or type(spec.expected_visibility_ceiling) is not VisibilityCeiling):
                raise PermissionError("issued provider input lacks its complete frozen external specification")
            prior = result.setdefault(spec.logical_artifact_id, spec)
            if replace(prior, input_id=spec.input_id) != spec:
                raise PermissionError("issued tasks disagree on one exact provider input")
    return result


def _require_provider_input_manifest(writer, run_id, spec, manifest, *, authenticated_size_bytes):
    """Authenticate metadata and durable publication before opening copy bytes."""
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, artifact_publication_member
    # This width comes only from the closed payload/persisted-copy join or the
    # actual reader's registered receipt closure, never a selected sidecar.
    if (type(authenticated_size_bytes) is not int or authenticated_size_bytes <= 0
            or spec.expected_size_bytes is not None and spec.expected_size_bytes != authenticated_size_bytes):
        raise PermissionError("issued provider copy changes its authenticated positive byte width")
    relative, scope_id, scope_root = provider_input_location(writer, run_id, spec.logical_artifact_id)
    logical, physical, publication = manifest.logical, manifest.materialization, manifest.publication
    if (logical.logical_artifact_id != spec.logical_artifact_id
            or physical.logical_artifact_id != spec.logical_artifact_id
            or physical.relative_path != relative
            or physical.storage_root_id != writer.root.contract.storage_root_id
            or physical.compression != "none" or physical.partition_selector is not None
            or type(logical.profile) is not ArtifactProfile
            or (logical.content_sha256, physical.physical_sha256, physical.size_bytes,
                logical.payload_schema, logical.media_type, logical.outcome_access, logical.visibility_ceiling) != (
                spec.expected_content_sha256, spec.expected_content_sha256, authenticated_size_bytes,
                spec.expected_payload_schema, spec.expected_media_type, spec.expected_outcome_access,
                spec.expected_visibility_ceiling)
            or spec.identity_scope_sha256 is not None and not any(
                parent.identity.object_fingerprint == spec.identity_scope_sha256 for parent in logical.lineage_parents)
            or publication is None or publication.publication_scope.publication_scope_id != scope_id
            or publication.publication_scope.relative_root != scope_root
            or publication.publication_scope.storage_root_id != writer.root.contract.storage_root_id
            or publication.members != (artifact_publication_member(logical, physical),)):
        raise PermissionError("issued provider copy changes its frozen input or deterministic publication")



def _serialized_custody_call(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        # Development custody delegates the ordinary reader without shared
        # issued controls; preserve that existing call path exactly.
        lock = getattr(self, "_preparation_lock", None)
        if lock is None:
            return method(self, *args, **kwargs)
        with lock:
            if type(self) is not CurrentIssuedTaskCustody or not self._original_input_accesses:
                return method(self, *args, **kwargs)
            self.require_original_input_access()
            with self.verification_scope():
                result = method(self, *args, **kwargs)
            self.require_original_input_access()
            return result
    return guarded


class CurrentIssuedTaskCustody:
    """Fresh current authority and exact task inputs for domain preparation.

    Successful authentication supplies custody facts only. The domain must still
    validate its scientific records, allocation, source joins and prepared role.
    """

    def __init__(self, *, writer, reveal_authority_id=None, original_input_access=None, original_control_scopes=()):
        if reveal_authority_id is not None:
            validate_stable_id(reveal_authority_id)
        self.writer = writer
        self.reveal_authority_id = reveal_authority_id
        if type(original_control_scopes) is not tuple or any(not callable(scope) for scope in original_control_scopes):
            raise TypeError('issued original controls require explicit code-owned context factories')
        self._original_control_scopes = original_control_scopes
        accesses = (() if original_input_access is None else original_input_access
            if type(original_input_access) is tuple else (original_input_access,))
        for access in accesses:
            if (type(getattr(access, "parents", None)) is not tuple
                    or not callable(getattr(access, "require_current", None))
                    or not callable(getattr(access, "require_issued_member", None))):
                raise TypeError("issued original input access requires its code-owned current scope")
        self.original_input_access = original_input_access
        self._original_input_accesses = accesses
        self._input_member_guard = self.require_input_member
        self._original_read_member_guard = self._require_original_read_member
        self._original_member_facts = set()
        self._current_package_plan = None
        self._current_run_id = None
        self._prepared_run_records = None
        self._provider_inputs = None
        self._retained_read_guard = None
        self._retained_member_guard = None
        self._joining_receipt_members = set()
        self._control_reader = None
        self._issued_reader = None
        self._parent_read_scope = None
        self._preparation_lock = RLock()

    def require_original_input_access(self):
        for access in self._original_input_accesses:
            if access.require_current(artifact_writer=self.writer) is not None:
                raise ValueError("issued original input guard must return None or raise")

    def require_input_member(self, manifest):
        # Parallel consumers may need the same producer's metadata. Serialize
        # joining/fact admission, retaining RLock's same-thread cycle refusal.
        if self._original_input_accesses:
            with self._preparation_lock:
                return self._require_input_member(manifest)
        return self._require_input_member(manifest)

    def _require_input_member(self, manifest):
        self._require_retained_read()
        self.require_original_input_access()
        fact = manifest.logical, manifest.materialization
        if fact in self._original_member_facts and self._current_package_plan is not None:
            self._require_current_issued_identity(self._current_package_plan[0])
        if fact not in self._original_member_facts:
            if self._current_package_plan is not None:
                package, plan = self._current_package_plan
                owners = tuple(task for task in plan.tasks if any(
                    output.logical_artifact_id == manifest.logical.logical_artifact_id for output in task.outputs))
            else:
                owners = ()
            if len(owners) == 1:
                if fact in self._joining_receipt_members:
                    raise PermissionError("issued output receipt metadata recursively selects itself")
                self._joining_receipt_members.add(fact)
                try:
                    self._require_current_issued_identity(package)
                    _, _, facts = self._control_reader.read_receipted_output_metadata(
                        package=package, execution_plan=plan, task_id=owners[0].task_id,
                        before_header=self._before_receipt_header)
                    if fact not in facts:
                        raise PermissionError("issued input substitutes its exact receipted output")
                    self._original_member_facts.update(facts)
                finally:
                    self._joining_receipt_members.remove(fact)
            else:
                for access in self._original_input_accesses:
                    if access.require_issued_member(manifest) is not None:
                        raise ValueError("issued original member guard must return None or raise")
        self.require_original_input_access()
        self._require_retained_read()

    def _require_retained_read(self):
        if self._retained_read_guard is not None and self._retained_read_guard() is not None:
            raise ValueError("issued retained read guard must return None or raise")

    def bind_current_run(self, run_id, *, package=None, source_plan=None, execution_plan=None,
            package_name="campaign-package", source_plan_name="run-plan", provider_reconstruction=None,
            require_current_source=None):
        from empirical_lawhood.runtime.plans import RunPlan, ExecutionPlan
        self.require_original_input_access()
        validate_stable_id(run_id)
        if self._current_run_id not in (None, run_id):
            raise PermissionError("issued custody cannot change its actual current run")
        self._current_run_id = run_id
        if package is None and source_plan is None and execution_plan is None:
            return
        if (type(package) is not ExperimentPackage or package.run_plan_id != run_id
                or type(source_plan) is not RunPlan or type(execution_plan) is not ExecutionPlan
                or execution_plan.source_plan != ObjectIdentity.from_record(run_id, source_plan)
                or execution_plan.execution_plan_id != package.execution_plan_id
                or source_plan.candidate != ObjectIdentity.from_record(package.issued_study.candidate.candidate_id,
                    package.issued_study.candidate)
                or execution_plan.candidate != source_plan.candidate
                or source_plan.implementation_commit != package.issued_study.source_closure.implementation_commit
                or execution_plan.implementation_commit != source_plan.implementation_commit
                or source_plan.registry_sha256 != package.registry.fingerprint()
                or execution_plan.registry_sha256 != source_plan.registry_sha256
                or (package_name, source_plan_name) != ("campaign-package", "run-plan")):
            raise PermissionError("issued custody changes its actual prepared package or plan")
        if self._original_input_accesses:
            if not callable(require_current_source):
                raise TypeError("issued original binding requires its actual selected-source inspector")
            require_current_source(package)
        self._require_current_issued_identity(package)
        published = ExternalIssuedStudyPublisher(artifact_plane=self.writer,
            authority_store=ExternalStudyOperationAuthorityStore(self.writer),
            grantee_id=PROGRAMME_ISSUE_GRANTEE_ID).load_executable_study(package.issued_study.issue_id)
        if (published.manifest != package.issued_study
                or published.publication_receipt != package.publication_receipt):
            raise PermissionError("issued binding changes its actual current issue publication")
        self.require_original_input_access()
        records = package, source_plan, execution_plan, provider_reconstruction
        if self._prepared_run_records is not None and self._prepared_run_records != records:
            raise PermissionError("issued custody cannot replace its prepared run records")
        self._prepared_run_records = records
        if self._control_reader is not None:
            self._admit_run_control_metadata(self._control_reader.writer)
        self.require_original_input_access()

    def bind_provider_inputs(self, *, execution_plan, payloads, inputs):
        """Bind actual persisted copies to the already-authenticated provider census.

        Payload metadata remains immutable after its source is closed; no chunk
        iterator is reopened. These are input facts, never a permission verdict.
        """
        from empirical_lawhood.runtime.providers import ExternalInputPayload
        if not self._original_input_accesses:
            return
        with self._preparation_lock:
            self.require_original_input_access()
            if (self._prepared_run_records is None or self._prepared_run_records[2] != execution_plan
                    or self._current_run_id != self._prepared_run_records[0].run_plan_id):
                raise PermissionError("provider copies lack their actual bound package and frozen plan")
            self._require_current_issued_identity(self._prepared_run_records[0])
            specs = _provider_input_specs(execution_plan)
            expected_ids = tuple(sorted(specs))
            if (type(payloads) is not tuple or any(type(value) is not ExternalInputPayload for value in payloads)
                    or tuple(value.logical_artifact_id for value in payloads) != expected_ids
                    or type(inputs) is not tuple or any(type(value) is not VerifiedArtifactInput for value in inputs)
                    or tuple(value.artifact_id for value in inputs) != expected_ids):
                raise PermissionError("provider copies change the complete actual external census")
            for payload, value in zip(payloads, inputs, strict=True):
                payload.__post_init__()
                logical, physical = value.logical, value.materialization
                if (type(payload.size_bytes) is not int or payload.size_bytes <= 0
                        or type(physical.size_bytes) is not int or physical.size_bytes <= 0):
                    raise PermissionError("provider copy lacks its actual positive source byte width")
                expected_hash = payload.logical_content_sha256 or payload.source_sha256
                if ((logical.logical_artifact_id, logical.payload_schema, logical.profile, logical.media_type,
                        logical.content_sha256, logical.visibility_ceiling, logical.outcome_access,
                        logical.parent_visibility_ceilings, logical.lineage_parents, physical.physical_sha256,
                        physical.size_bytes) != (
                        payload.logical_artifact_id, payload.payload_schema, payload.profile, payload.media_type,
                        expected_hash, payload.visibility_ceiling, payload.outcome_access,
                        payload.parent_visibility_ceilings, payload.lineage_parents, payload.source_sha256,
                        payload.size_bytes)):
                    raise PermissionError("provider copy changes its actual source bytes or complete parent lineage")
                relative, _, _ = provider_input_location(self.writer, self._current_run_id, value.artifact_id)
                manifest = self.writer.read_manifest(relative)
                _require_provider_input_manifest(self.writer, self._current_run_id, specs[value.artifact_id], manifest,
                    authenticated_size_bytes=payload.size_bytes)
                if (manifest.logical, manifest.materialization) != (logical, physical):
                    raise PermissionError("provider copy substitutes its actual persisted materialization")
            if self._provider_inputs is not None and self._provider_inputs != inputs:
                raise PermissionError("issued provider copies cannot replace their original immutable facts")
            self._provider_inputs = inputs
            self.require_original_input_access()

    def _admit_provider_input_metadata(self, writer, plan):
        """Re-read exact sidecars each invocation, before its first member hash."""
        if self._provider_inputs is None:
            return
        specs = _provider_input_specs(plan)
        if tuple(value.artifact_id for value in self._provider_inputs) != tuple(sorted(specs)):
            raise PermissionError("issued provider admission changes its frozen input census")
        facts = []
        for value in self._provider_inputs:
            self.require_original_input_access()
            self._require_current_issued_identity(self._current_package_plan[0])
            relative, _, _ = provider_input_location(writer, self._current_run_id, value.artifact_id)
            manifest = writer.read_manifest(relative)
            _require_provider_input_manifest(writer, self._current_run_id, specs[value.artifact_id], manifest,
                authenticated_size_bytes=value.materialization.size_bytes)
            if (manifest.logical, manifest.materialization) != (value.logical, value.materialization):
                raise PermissionError("issued provider sidecar changes its actual admitted input")
            facts.append((manifest.logical, manifest.materialization))
        # Admit the whole independently checked census together: a publication
        # sibling may be visited before this task's own selected body.
        self._original_member_facts.update(facts)
        self.require_original_input_access()

    @contextmanager
    def retained_binding(self, *, package, execution_plan, control_reader, receipt_closure, require_current_read):
        """Bind exact receipted inputs within the caller's actual live read scope."""
        if not callable(require_current_read):
            raise TypeError("issued retained inputs require their current scientific read guard")
        if (type(control_reader) is not CurrentResultPlanReader
                or control_reader.writer.root is not self.writer.root or self._control_reader is not None):
            raise PermissionError("issued retained inputs change their actual reader or guarded root")
        control_reader.writer.require_verification_context()
        source = control_reader.require_receipt_closure(package=package, execution_plan=execution_plan,
            receipt_closure=receipt_closure)
        if require_current_read() is not None:
            raise ValueError("issued retained read guard must return None or raise")
        self.require_original_input_access()
        self._require_current_issued_identity(package)
        if (type(package) is not ExperimentPackage
                or control_reader.authenticate_execution_plan(package=package, issued=package.issued_study,
                    run_id=package.run_plan_id) is not execution_plan
                or _actual_package(control_reader.writer, package.run_plan_id, control_reader=control_reader) != package):
            raise PermissionError("issued retained inputs change their actual package and authenticated plan")
        saved = (self._current_run_id, self._current_package_plan, self._prepared_run_records,
            self._control_reader, self._retained_read_guard, self._retained_member_guard,
            control_reader._input_member_guard, set(self._original_member_facts))
        self._current_run_id = package.run_plan_id
        self._current_package_plan = package, execution_plan
        self._prepared_run_records = package, source, execution_plan, None
        self._control_reader = control_reader
        self._retained_read_guard = require_current_read
        try:
            self._require_retained_read()
            self.require_original_input_access()
            self._require_current_issued_identity(package)
            self._admit_run_control_metadata(control_reader.writer)
            specs = _provider_input_specs(execution_plan)
            facts = []
            for expected in receipt_closure.manifests:
                self._require_retained_read()
                actual = control_reader.writer.read_manifest(expected.materialization.relative_path)
                if actual != expected:
                    raise PermissionError("issued retained input changes its exact receipted publication")
                spec = specs.get(actual.logical.logical_artifact_id)
                if spec is not None:
                    _require_provider_input_manifest(control_reader.writer, package.run_plan_id, spec, actual,
                        authenticated_size_bytes=expected.materialization.size_bytes)
                facts.append((actual.logical, actual.materialization))
            self._original_member_facts.update(facts)
            admitted = frozenset(self._original_member_facts)
            accesses = self._original_input_accesses

            def retained_member_guard(manifest):
                # Final path verifiers may run at the caller's outer context
                # exit, after this binding restores its temporary class state.
                # Capture immutable exact facts, never a permission decision.
                # Final snapshot callbacks already own body verification; only
                # authenticate their lifetime here, without re-entering it.
                control_reader.writer.require_active_verification_scope()
                if require_current_read() is not None:
                    raise ValueError("issued retained read guard must return None or raise")
                for access in accesses:
                    if access.require_current(artifact_writer=self.writer) is not None:
                        raise ValueError("issued original input guard must return None or raise")
                self._require_current_issued_identity(package)
                if (manifest.logical, manifest.materialization) not in admitted:
                    if not accesses:
                        raise PermissionError("issued retained input is outside its actual closed receipt census")
                    for access in accesses:
                        if access.require_issued_member(manifest) is not None:
                            raise ValueError("issued original member guard must return None or raise")
                for access in accesses:
                    if access.require_current(artifact_writer=self.writer) is not None:
                        raise ValueError("issued original input guard must return None or raise")
                if require_current_read() is not None:
                    raise ValueError("issued retained read guard must return None or raise")

            self._retained_member_guard = retained_member_guard
            control_reader._input_member_guard = retained_member_guard
            yield self
            control_reader.writer.require_verification_snapshot()
            self._require_current_issued_identity(package)
            self.require_original_input_access()
            self._require_retained_read()
        finally:
            (self._current_run_id, self._current_package_plan, self._prepared_run_records,
                self._control_reader, self._retained_read_guard, self._retained_member_guard,
                control_reader._input_member_guard, original_facts) = saved
            self._original_member_facts.clear()
            self._original_member_facts.update(original_facts)
            self._joining_receipt_members.clear()

    def _admit_run_control_metadata(self, writer):
        """Exact already-admitted runtime records, before their first body hash."""
        from empirical_lawhood.api.execution import CampaignExecutionService
        from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, lineage_parent_sort_key
        if self._prepared_run_records is None:
            return
        package, source, plan, reconstruction = self._prepared_run_records
        self.require_original_input_access()
        self._require_current_issued_identity(package)
        parents = CampaignExecutionService._package_lineage_parents(package)
        visibility = VisibilityCeiling.most_restrictive(*(value.visibility_ceiling for value in parents))
        access = CampaignExecutionService._most_restrictive_access(parents)
        package_parent = ArtifactLineageParent(ObjectIdentity.from_record(package.package_id, package), visibility, access)
        source_parent = ArtifactLineageParent(ObjectIdentity.from_record(self._current_run_id, source), visibility, access)
        rows = [("campaign-package", package, parents), ("run-plan", source, (package_parent,)),
            ("execution-plan", plan, tuple(sorted((package_parent, source_parent), key=lineage_parent_sort_key)))]
        if reconstruction is not None:
            replay = ArtifactLineageParent(reconstruction.payload_replay_set,
                VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)
            rows.append(("provider-reconstruction", reconstruction,
                tuple(sorted((package_parent, replay), key=lineage_parent_sort_key))))
        for name, record, lineage in rows:
            relative = "runs/" + self._current_run_id + "/plans/" + name + ".json"
            manifest = writer.read_manifest(relative)
            logical, material = manifest.logical, manifest.materialization
            if (material.relative_path != relative or material.storage_root_id != writer.root.contract.storage_root_id
                    or logical.logical_artifact_id != name + "." + self._current_run_id
                    or logical.payload_schema != record.SCHEMA or logical.profile is not ArtifactProfile.CANONICAL_JSON
                    or logical.media_type != "application/json" or logical.content_sha256 != record.fingerprint()
                    or material.physical_sha256 != record.fingerprint()
                    or material.size_bytes != len(record.canonical_bytes())
                    or material.compression != "none" or material.partition_selector is not None
                    or logical.lineage_parents != lineage
                    or logical.visibility_ceiling is not VisibilityCeiling.most_restrictive(
                        *(value.visibility_ceiling for value in lineage))
                    or logical.outcome_access is not CampaignExecutionService._most_restrictive_access(lineage)
                    or manifest.publication is None
                    or manifest.publication.publication_scope.publication_scope_id != "campaign-plans." + self._current_run_id
                    or manifest.publication.publication_scope.relative_root != "runs/" + self._current_run_id + "/plans"):
                raise PermissionError("issued runtime control changes its exact prepared record publication")
            self._original_member_facts.add((logical, material))
        # This supplies initial exact objects only. The ordinary reader below
        # still authenticates stored bytes and the original issue/plan graph.
        self._current_package_plan = package, plan
        self.require_original_input_access()

    def _require_current_issued_identity(self, package):
        store = ExternalStudyOperationAuthorityStore(self.writer)
        current = store.load(package.execution_authority.authority_id)
        if current != package.execution_authority:
            raise PermissionError("issued receipt changes its actual current execution authority")
        # This is immutable custody/current stored identity, not new entry.
        # Actual effect expiry remains in require_native_entry after Ready.
        return current

    def _before_receipt_header(self, manifest, *, index, task, candidate, authenticated_facts=()):
        """Exact current-index header metadata, never a generic SEALED exception."""
        self.require_original_input_access()
        if self._current_package_plan is None:
            raise PermissionError("issued receipt header lacks its authenticated current plan")
        package, plan = self._current_package_plan
        self._require_current_issued_identity(package)
        expected_index = self._control_reader.original_recovery_index(package=package, execution_plan=plan)
        from .retained_e3_control_repair import selected_repair_index
        expected_index = selected_repair_index(writer=self._control_reader.writer,
            plan=plan, predecessor=expected_index)
        if index != expected_index:
            raise PermissionError("issued receipt header substitutes its actual frozen recovery index")
        if task is not None:
            if (self._control_reader.execution_task(execution_plan=plan, task_id=task.task_id) != task
                    or candidate not in index.task(task.task_id).attempts):
                raise PermissionError("issued receipt header substitutes a foreign task or recovery candidate")
        elif (manifest.logical.payload_schema != index.SCHEMA
                or manifest.logical.content_sha256 != index.fingerprint()):
            raise PermissionError("issued receipt header changes its exact recovery index publication")
        self._original_member_facts.add((manifest.logical, manifest.materialization))
        self._original_member_facts.update(authenticated_facts)
        self.require_original_input_access()

    def _original_member_options(self):
        return ({} if not self._original_input_accesses else
            {"before_member": self._retained_member_guard or self._input_member_guard})

    @contextmanager
    def preparation_scope(self):
        """Serialize shared parent checks; return before any child execution.

        The graph's verification lifetime remains open without holding this
        lock. Reentrancy permits fresh task/control checks inside one complete
        parent preparation and single-flight immutable prerequisite derivation.
        """
        with self._preparation_lock:
            try:
                yield self
            finally:
                if self._control_reader is not None:
                    # Completed-only finalization has no new-entry callback.
                    # Close its original custody before any worker publication,
                    # without asking for a new execution permission.
                    self._require_static_custody()

    def _require_static_custody(self):
        controls = self._control_reader.writer
        controls.require_verification_snapshot()
        if self._issued_reader is None:
            if self._retained_read_guard is None:
                raise PermissionError("issued static custody loses its actual issue read scope")
        else:
            issued = self._issued_reader.artifact_plane
            if issued is not controls:
                issued.require_verification_snapshot()

    @contextmanager
    def verification_scope(self):
        """Share immutable issue/plan facts; current grants use the ordinary writer."""
        self.require_original_input_access()
        if (type(self.writer) is not ExternalArtifactPlane
                or any(name in vars(self.writer) for name in (
                    "write","write_stream","write_batch","write_compact_batch"))):
            if self._original_control_scopes:
                raise PermissionError('issued original control scopes require ordinary guarded custody')
            yield self
            return
        if self._control_reader is not None:
            self._control_reader.writer.require_verification_context()
            yield self
            self._control_reader.writer.require_verification_context()
            self.require_original_input_access()
            return
        reader = None
        try:
            with ExitStack() as originals, self.writer.read_context(**self._original_member_options()) as controls:
                publisher=ExternalIssuedStudyPublisher(artifact_plane=controls,
                    authority_store=ExternalStudyOperationAuthorityStore(self.writer),grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)
                with publisher.read_context() as issued:
                    reader=CurrentResultPlanReader(controls)
                    self._control_reader,self._issued_reader=reader,issued
                    for scope in self._original_control_scopes:
                        originals.enter_context(scope())
                    if self._original_input_accesses and self._current_run_id is not None:
                        self._admit_run_control_metadata(controls)
                        package = _actual_package(controls, self._current_run_id, control_reader=reader)
                        published = issued.load_executable_study(package.issued_study.issue_id)
                        if (published.manifest != package.issued_study
                                or published.publication_receipt != package.publication_receipt):
                            raise PermissionError("issued input scope changes its actual published study")
                        plan = reader.authenticate_execution_plan(package=package, issued=published.manifest,
                            run_id=self._current_run_id)
                        self._current_package_plan = package, plan
                        self._admit_provider_input_metadata(controls, plan)
                    yield self
                    self._require_static_custody()
                    self.require_original_input_access()
            self.require_original_input_access()
        finally:
            if reader is not None:
                self._control_reader,self._issued_reader=None,None
                self._current_package_plan = None
                self._original_member_facts.clear()
                self._joining_receipt_members.clear()
                if self._parent_read_scope is not None:
                    self._parent_read_scope.closures.clear()
                self._parent_read_scope = None
                reader._controls.clear()
                reader._plans.clear()
                reader._task_indexes.clear()
                reader._recovery_indexes.clear()
                reader._execution_history.clear()
                reader._output_writers.clear()
                reader._receipt_closures.clear()

    def _require_original_read_member(self, manifest):
        """Use each original producer's closed member owner, never child outputs."""
        self.require_original_input_access()
        for access in self._original_input_accesses:
            callback = getattr(access, "require_original_member", None)
            if not callable(callback):
                raise TypeError("issued original replay requires its exact original-member owner")
            if callback(manifest) is not None:
                raise ValueError("issued original member guard must return None or raise")
        self.require_original_input_access()

    @contextmanager
    def original_read_scope(self):
        """Reuse immutable original-parent controls, with fresh grants per call."""
        from empirical_lawhood.api.recursive_qualified_parents import _ParentReadScope
        if self._control_reader is None:
            options = ({} if not self._original_input_accesses else
                {"before_member": self._original_read_member_guard})
            with self.writer.read_context(**options) as writer:
                yield writer, _ParentReadScope(writer)
                writer.require_verification_snapshot()
            return
        writer = self._control_reader.writer
        writer.require_verification_context()
        if not self._original_input_accesses:
            if self._parent_read_scope is None:
                self._parent_read_scope = _ParentReadScope(writer, plan_reader=self._control_reader)
            yield writer, self._parent_read_scope
            writer.require_verification_context()
            return
        with writer.read_context(before_member=self._original_read_member_guard) as original_writer:
            if self._parent_read_scope is None:
                self._parent_read_scope = _ParentReadScope(original_writer, plan_reader=self._control_reader)
            yield original_writer, self._parent_read_scope
            original_writer.require_verification_context()

    @_serialized_custody_call
    def current_task(self, context, runner):
        if type(context) is not TaskContext or context.permissions != runner.manifest.permissions:
            raise PermissionError('programme preparation requires exact actual task authority')
        reader=self._control_reader
        package = (_actual_package(self.writer,context.run_id) if reader is None else
            _actual_package(reader.writer,context.run_id,control_reader=reader))
        if type(package) is not ExperimentPackage or package.run_plan_id != context.run_id:
            raise PermissionError('programme preparation requires a genuine current issued experiment')
        store = ExternalStudyOperationAuthorityStore(self.writer)
        execution = store.load(package.execution_authority.authority_id)
        issued_pin = ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study)
        execution_pin = ObjectIdentity.from_record(execution.authority_id, execution)
        if execution != package.execution_authority:
            raise PermissionError('programme preparation changes the actual current execution grant')
        publisher=(self._issued_reader if reader is not None else ExternalIssuedStudyPublisher(
            artifact_plane=self.writer,authority_store=store,grantee_id=PROGRAMME_ISSUE_GRANTEE_ID))
        published=publisher.load_executable_study(issued_pin.object_id)
        if published.manifest != package.issued_study or published.publication_receipt != package.publication_receipt:
            raise PermissionError('programme preparation substitutes current original issued sources')
        plan = (authenticate_current_execution_plan(package=package,issued=published.manifest,
            run_id=context.run_id,writer=self.writer) if reader is None else reader.authenticate_execution_plan(
                package=package,issued=published.manifest,run_id=context.run_id))
        if reader is None:
            tasks = tuple(t for t in plan.tasks if t.task_id == context.task_id)
        else:
            selected = reader.execution_task(execution_plan=plan, task_id=context.task_id)
            tasks = () if selected is None else (selected,)
        if (len(tasks) != 1 or tasks[0].capability.capability_key != runner.manifest.capability_key
                or tasks[0].capability_implementation_sha256 != runner.manifest.implementation_sha256
                or context.config != tasks[0].capability.config
                or context.outcome_access is not tasks[0].capability.requested_outcome_access
                or context.permissions != tasks[0].capability.required_permissions
                or context.resource_budget != tasks[0].capability.requested_resources
                or context.output_ports != tuple(WorkerOutputPort(p.output_id, p.payload_schema, p.profile,
                    p.media_type, p.logical_artifact_id) for p in tasks[0].outputs)):
            raise PermissionError('programme preparation changes its actual current installed task/config/access')
        task = tasks[0]
        if self._original_input_accesses:
            self.bind_current_run(context.run_id)
            self._current_package_plan = package, plan
        contacts = ExternalNativeEffectContactStore(plane=self.writer,
            execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
            visibility_ceiling=VisibilityCeiling.most_restrictive(*(output.visibility_ceiling for output in task.outputs)),
            outcome_access=most_restrictive_outcome_access(task.capability.requested_outcome_access,
                *(output.outcome_access for output in task.outputs)))
        contact = contacts.read(context.run_id, context.task_id)
        if contact is not None:
            if (contact.attempt_id != context.attempt_id
                    or contact.execution_task != ObjectIdentity.from_record(task.task_id, task)
                    or contact.implementation_commit != plan.implementation_commit
                    or contact.input_materialization_ids != context.input_materialization_ids
                    or contact.dependency_receipt_ids != context.dependency_receipt_ids):
                raise PermissionError('programme preparation changes its exact original native contact')
            # Retained contact permits no new entry. Until native facts carry
            # their own real entry time, this proves dispatch validity only.
            authenticate_task_dispatch_authority(package=package, execution_plan=plan,
                run_id=context.run_id, task_id=context.task_id, attempt_id=context.attempt_id, writer=self.writer)
        if task.barrier is BarrierKind.REVEAL:
            if self.reveal_authority_id is None:
                raise PermissionError('programme reveal requires an explicitly selected genuine current reveal grant')
            reveal = store.load(self.reveal_authority_id)
            if reveal.authority_id != self.reveal_authority_id:
                raise PermissionError('programme reveal substitutes its selected reveal grant')
            now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
            require_study_authority(reveal, kind=StudyAuthorityKind.OUTCOME_REVEAL, subject=issued_pin,
                prerequisite_authority=execution_pin, grantee_id=PROGRAMME_REVEAL_GRANTEE_ID, at_utc=now)
        adjudications = tuple(p for p in task.outputs if p.payload_schema == ScientificAdjudicationRecord.SCHEMA)
        if adjudications:
            if len(adjudications) != 1:
                raise PermissionError('programme preparation requires one registered scientific adjudication output')
            from empirical_lawhood.api.execution import CampaignExecutionService
            output, = adjudications
            bound = CampaignExecutionService._bind_scientific_adjudication(package, plan, ScientificAdjudicationOutputContract(
                task.capability.capability_key, task.capability.capability_version, output.output_id,
                ScientificAdjudicationRecord.SCHEMA, MAX_ADJUDICATION_BYTES))
            if bound is None or bound.context != context.scientific_adjudication_context:
                raise PermissionError('programme evaluator changes its actual genuine global reveal context')
        elif context.scientific_adjudication_context is not None:
            raise PermissionError('programme preparation adds an undeclared scientific adjudication context')
        return package, plan, tasks[0]

    @_serialized_custody_call
    def require_native_entry(self, context, runner, *, prepared_contract):
        """Recheck current effect permission at the parent's actual Ready boundary.

        This supplies no lease or repeat permission. The scheduler still owns
        the exact original attempt lease and durable first-contact boundary.
        Completed-only finalization must never call this new-effect boundary.
        """
        if (type(prepared_contract) is not PreparedInvocationContract
                or prepared_contract.native_effect is not True):
            raise PermissionError('native entry requires its exact prepared effect contract')
        prepared_contract.validate_context(context)
        package, plan, task = self.current_task(context, runner)
        if (prepared_contract.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan)
                or prepared_contract.execution_task != ObjectIdentity.from_record(task.task_id, task)
                or prepared_contract.execution_task_record != task
                or prepared_contract.implementation.observed_git_head != plan.implementation_commit
                or prepared_contract.manifest != runner.manifest):
            raise PermissionError('native entry substitutes its actual issued task or prepared contract')
        if self._control_reader is not None:
            # Cached immutable controls must still close their actual custody
            # before the fresh permission clock at a real effect boundary.
            self._require_static_custody()
        # Sample the permission clock after exact issue/plan/contract replay.
        # Loading from the ordinary writer prevents an immutable control cache
        # from standing in for the current genuine permission record.
        store = ExternalStudyOperationAuthorityStore(self.writer)
        execution = store.load(package.execution_authority.authority_id)
        if execution != package.execution_authority:
            raise PermissionError('native entry substitutes the actual stored execution authority')
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        require_study_authority(execution, kind=StudyAuthorityKind.EXPERIMENT_EXECUTION,
            subject=ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
            prerequisite_authority=ObjectIdentity.from_record(package.scientific_approval.authorization_id,
                package.scientific_approval), grantee_id=PROGRAMME_EXECUTION_GRANTEE_ID, at_utc=now)

    @_serialized_custody_call
    def task_inputs(self, context, task):
        """Join current ports to actual persisted controls without consuming them."""
        from empirical_lawhood.infrastructure.execution import LocalScheduler
        by_task, dependencies = {}, {}
        if self._original_input_accesses and self._current_package_plan is None:
            raise PermissionError("issued inputs lack their actual current task/plan authentication")
        receipts = ExternalTaskReceiptStore(
            self._control_reader.writer if self._control_reader is not None else self.writer)
        for header in context.dependency_receipts:
            if self._original_input_accesses:
                package, plan = self._current_package_plan
                receipt, _, facts = self._control_reader.read_receipted_output_metadata(
                    package=package, execution_plan=plan, task_id=header.task_id,
                    expected_receipt_id=header.receipt_id, before_header=self._before_receipt_header)
                self._original_member_facts.update(facts)
            else:
                receipt = receipts.read_by_receipt_id(context.run_id, header.task_id, header.receipt_id)
            if (receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
                    or not set(header.output_materialization_ids) <= {
                        p.materialization_id for p in receipt.output_materializations}):
                raise PermissionError('programme preparation changes its current successful dependency receipt')
            by_task[header.task_id] = receipt
            physical = {p.logical_artifact_id: p for p in receipt.output_materializations}
            dependencies[header.task_id] = tuple(VerifiedArtifactInput(l, physical[l.logical_artifact_id])
                for l in receipt.output_logical_artifacts)
        if tuple(sorted(by_task)) != task.dependency_task_ids:
            raise PermissionError('programme preparation changes its actual current dependency task census')
        dependency_outputs = LocalScheduler._dependency_outputs(task, dependencies)
        expected = [WorkerInputBinding.from_verified(v, kind=WorkerInputKind.DEPENDENCY)
            for v in dependency_outputs]
        if context.dependency_receipts != LocalScheduler._dependency_receipt_bindings(task,
                dependency_outputs=dependency_outputs, receipts=by_task):
            raise PermissionError('programme preparation changes selected actual dependency outputs')
        controls = {}
        for spec in task.external_inputs:
            relative, _, _ = provider_input_location(self.writer, context.run_id, spec.logical_artifact_id)
            m = self.writer.read_manifest(relative,
                maximum_bytes=artifact_custody_limits(self.writer).manifest_bytes)
            if (m.materialization.relative_path != relative or m.materialization.storage_root_id != self.writer.root.contract.storage_root_id
                    or m.logical.logical_artifact_id != spec.logical_artifact_id
                    or any(wanted is not None and actual != wanted for actual, wanted in (
                        (m.logical.payload_schema, spec.expected_payload_schema), (m.logical.content_sha256, spec.expected_content_sha256),
                        (m.materialization.size_bytes, spec.expected_size_bytes), (m.logical.media_type, spec.expected_media_type),
                        (m.logical.outcome_access, spec.expected_outcome_access), (m.logical.visibility_ceiling, spec.expected_visibility_ceiling)))):
                raise PermissionError('programme preparation changes an exact current external input')
            expected.append(WorkerInputBinding.from_verified(VerifiedArtifactInput(m.logical, m.materialization), kind=WorkerInputKind.EXTERNAL))
            controls[spec.logical_artifact_id] = m
        if tuple(sorted(expected, key=lambda v: v.artifact_id)) != context.input_bindings:
            raise PermissionError('programme preparation changes complete actual current task input bindings')
        return by_task, controls

    def immutable_control_record(self, manifest, record_type, maximum, **lane):
        """Explicit static plan input; never use for a dependency or output record."""
        return self.control_record(manifest,record_type,maximum,_immutable=True,**lane)

    @_serialized_custody_call
    def control_record(self, manifest, record_type, maximum, *, _immutable=False,
            expected_outcome_access=OutcomeAccess.OUTCOME_BLIND,
            expected_visibility_ceiling=VisibilityCeiling.PROSPECTIVE):
        """Read exact canonical control bytes in their authenticated issued lane.

        Callers selecting another lane first authenticate its actual issue/grant
        and exact task input. Historical callers retain the blind-only default.
        """
        if (type(expected_outcome_access) is not OutcomeAccess
                or type(expected_visibility_ceiling) is not VisibilityCeiling
                or manifest.logical.outcome_access is not expected_outcome_access
                or manifest.logical.visibility_ceiling is not expected_visibility_ceiling):
            raise PermissionError('programme preparation config changes its exact issued access or visibility lane')
        reader=self._control_reader if _immutable else None
        if reader is not None:return reader.read_control(manifest,record_type,maximum)
        self.writer.verify_manifest(manifest, **self._original_member_options())
        if self._original_input_accesses:
            self.require_input_member(manifest)
        raw = read_bounded_bytes(self.writer.root.resolve(manifest.materialization.relative_path, for_write=False), maximum_bytes=maximum)
        record = decode_canonical_bytes(raw,record_type,maximum_bytes=maximum)
        digest = sha256(raw).hexdigest()
        if (not record.canonical_equals(raw) or len(raw) != manifest.materialization.size_bytes
                or digest != manifest.logical.content_sha256
                or digest != manifest.materialization.physical_sha256):
            raise PermissionError('programme preparation changes exact canonical current configuration')
        return record


class CurrentIssuedTaskCustodySupplier:
    """Explicit parent-supplier participation in the shared custody lifetime."""

    custody: CurrentIssuedTaskCustody

    def current_issued_task_custody(self):
        custody = self.custody
        if type(custody) is CurrentDevelopmentTaskCustody:
            return None
        if type(custody) is not CurrentIssuedTaskCustody:
            raise TypeError("issued supplier changes its actual typed custody owner")
        return custody


def issued_custody_for_supplier(supplier):
    """Exact shared owner, or ordinary uncached legacy helper invocation."""
    custody = (supplier.current_issued_task_custody()
        if isinstance(supplier, CurrentIssuedTaskCustodySupplier) else getattr(supplier, "custody", None))
    if custody is None:
        custody = CurrentIssuedTaskCustody(writer=supplier.writer,
            reveal_authority_id=supplier.reveal_authority_id)
    if (type(custody) is not CurrentIssuedTaskCustody or custody.writer is not supplier.writer
            or custody.reveal_authority_id != supplier.reveal_authority_id):
        raise TypeError("shared issued custody changes its exact writer or reveal selection")
    return custody


@contextmanager
def current_issued_task_control_scope(api_or_service):
    """Own immutable control reuse for the actual synchronous public run/recovery."""
    with ExitStack() as scopes:
        for custody in current_issued_task_custodies(api_or_service):
            scopes.enter_context(custody.verification_scope())
        yield


def current_issued_task_custodies(api_or_service):
    """Select only actual typed supplier custody owners, holding strong references."""
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    execution = getattr(api_or_service, "_execution_service", api_or_service)
    suppliers = ((execution,) if isinstance(execution, CurrentIssuedTaskCustodySupplier) else
        tuple(platform.port.supplier for platform in getattr(execution, "executable_platform_ports", ())
            if type(platform.port) is RecursiveOperationInputPort))
    selected = []
    for supplier in suppliers:
        if not isinstance(supplier, CurrentIssuedTaskCustodySupplier):
            continue
        custody = supplier.current_issued_task_custody()
        if custody is not None and not any(custody is previous for previous in selected):
            selected.append(custody)
    return tuple(selected)


def current_issued_original_input_accesses(api_or_service):
    selected = []
    for custody in current_issued_task_custodies(api_or_service):
        for access in custody._original_input_accesses:
            if not any(access is previous for previous in selected):
                selected.append(access)
    return tuple(selected)


def _development_receipt_output_metadata(*, writer, plan, index, inputs, task_id, receipt, _ancestors=(), _validated=None):
    """Shared exact DEV receipt/input-lineage check; never hash output bodies.

    The caller authenticates the actual retained plan, recovery index and full
    external publication census. Ordinary development custody and the closed
    native TRAIN metadata scope both use this same validator.
    """
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, lineage_parent_sort_key
    from empirical_lawhood.infrastructure.execution import LocalScheduler

    task = plan.task(task_id)
    if task_id in _ancestors:
        raise PermissionError("development receipt ancestry contains a cycle")
    if _validated is not None and task_id in _validated:
        original, outputs = _validated[task_id]
        if receipt != original:
            raise PermissionError('development receipt ancestry substitutes its authenticated receipt')
        return outputs
    candidates = tuple(value for value in index.task(task_id).attempts if value.attempt_id == receipt.attempt_id)
    if len(candidates) != 1:
        raise PermissionError("development input loses its exact original recovery candidate")
    ExternalRunRecoveryStore._validate_receipt_static(index, task, candidates[0], receipt)
    physical = {value.logical_artifact_id: value for value in receipt.output_materializations}
    logical = {value.logical_artifact_id: value for value in receipt.output_logical_artifacts}
    if set(physical) != set(logical) or set(logical) != {value.logical_artifact_id for value in task.outputs}:
        raise PermissionError("development input changes its complete original output census")
    dependencies = {}
    store = ExternalTaskReceiptStore(writer)
    for parent in task.dependency_task_ids:
        if _validated is not None and parent in _validated:
            dependencies[parent] = _validated[parent][1]
            continue
        successful = []
        for candidate in index.task(parent).attempts:
            retained = store.read(index.run_id, parent, candidate.attempt_id)
            if retained is not None and retained.operational_status is OperationalStatus.SUCCEEDED:
                successful.append(retained)
        if len(successful) != 1:
            raise PermissionError("development receipt loses its unique successful original dependency")
        dependencies[parent] = _development_receipt_output_metadata(writer=writer, plan=plan, index=index, inputs=inputs,
            task_id=parent, receipt=successful[0], _ancestors=(*_ancestors, task_id), _validated=_validated)
    inputs = (*LocalScheduler._dependency_outputs(task, dependencies),
        *(inputs[value.logical_artifact_id] for value in task.external_inputs))
    if receipt.input_materialization_ids != tuple(sorted(value.materialization.materialization_id for value in inputs)):
        raise PermissionError("development receipt changes its exact actual input materializations")
    expected_parents = tuple(sorted((ArtifactLineageParent(
        ObjectIdentity.from_record(value.logical.logical_artifact_id, value.logical),
        value.logical.visibility_ceiling, value.logical.outcome_access) for value in inputs), key=lineage_parent_sort_key))
    result = []
    for spec in task.outputs:
        value, material = logical[spec.logical_artifact_id], physical[spec.logical_artifact_id]
        if (value.payload_schema, value.profile, value.media_type, value.outcome_access, value.visibility_ceiling) != (
                spec.payload_schema, spec.profile, spec.media_type, spec.outcome_access, spec.visibility_ceiling):
            raise PermissionError("development dependency changes its frozen output custody")
        if value.lineage_parents != expected_parents:
            raise PermissionError("development dependency changes its exact original input lineage")
        result.append(VerifiedArtifactInput(value, material))
    result = tuple(result)
    if _validated is not None:
        _validated[task_id] = receipt, result
    return result


class CurrentDevelopmentTaskCustody(DevelopmentTaskReadScopes):
    """Actual authored development tasks, without prospective authority fields.

    The existing authored-wave and retained-plan readers authenticate the frozen
    global closure once. Every preparation still joins current input manifests
    and successful ordinary dependency receipts. This does not issue a study,
    reveal a protected outcome or qualify development evidence.
    """

    def __init__(self, *, writer, directory, plan, original_input_access=None, read_access=None, payloads=None):
        from empirical_lawhood.api.recursive_authoring import (
            AuthoredRecursiveWave, MAX_DRAFT_BYTES, RecursiveImplementationBinding, RecursiveStudyDraft,
            _authenticate_authored_wave_roots, load_authored_wave,
        )
        from empirical_lawhood.api.recursive_execution import _external_inputs, _retained_plans
        from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads, read_exposed_recursive_payload
        from empirical_lawhood.runtime.input_access import derive_original_parent_input_contracts
        from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
        from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input, project_recursive_config_inputs
        from empirical_lawhood.api.recursive_operations import operation_catalog

        if type(plan) is not DevelopmentExecutionPlan:
            raise TypeError("development custody requires its actual retained development execution plan")
        self.writer = writer
        if payloads is None:
            self.packet, self.draft, self.source, payloads = load_authored_wave(directory=directory,
                artifact_writer=writer, lazy_payloads=True, read_access=read_access)
        else:
            if (type(payloads) is not AuthenticatedRecursivePayloads or payloads.plane is not writer
                    or Path(payloads.directory).resolve(strict=True) != Path(directory).resolve(strict=True)):
                raise PermissionError("development custody substitutes its actual authenticated authored members")
            scope = getattr(payloads, "original_input_access", None)
            if scope is not None:
                scope.require_current()
            limit = artifact_custody_limits(writer).manifest_bytes
            packet_relative = (Path(directory).resolve(strict=True) / "authored-wave.json").relative_to(
                writer.root.contract.canonical_path).as_posix()
            packet_manifest = writer.read_manifest(packet_relative, maximum_bytes=limit)
            raw = read_exposed_recursive_payload(writer, packet_manifest,
                maximum_bytes=packet_manifest.materialization.size_bytes, original_input_access=scope)
            self.packet = decode_canonical_bytes(raw, AuthoredRecursiveWave, maximum_bytes=len(raw))
            self.draft = decode_canonical_bytes(payloads["draft.json"], RecursiveStudyDraft, maximum_bytes=MAX_DRAFT_BYTES)
            self.source = decode_canonical_bytes(payloads["implementation.json"], RecursiveImplementationBinding, maximum_bytes=None)
            if tuple(payloads.member_identity(member.filename) for member in self.packet.members) != tuple(
                    member.identity for member in self.packet.members) or len(payloads) != len(self.packet.members):
                raise PermissionError("development custody changes its actual packet member census")
            _authenticate_authored_wave_roots(packet=self.packet, draft=self.draft, source=self.source,
                payloads=payloads, artifact_writer=writer, lazy_payloads=True)
        self.original_input_access = getattr(payloads, "original_input_access", None)
        if original_input_access is not None and (self.original_input_access is None
                or original_input_access.parents != self.original_input_access.parents):
            raise PermissionError("development custody substitutes its exact current original-input scope")
        self._require_current_original_access()
        self.run, actual, self.index = _retained_plans(payloads, self.draft)
        if actual != plan or self.draft.development_study is None or self.draft.prospective_draft is not None:
            raise PermissionError("development custody substitutes its actual authored development root or plan")
        from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationRecoveryIndex
        self._native_continuation_entry_guard = None
        if type(self.index) is DevelopmentNativeContinuationRecoveryIndex:
            from .native_continuation_execution import current_native_entry_guard
            self._native_continuation_entry_guard = current_native_entry_guard(self.index)
        self.plan = actual
        self.access_pair = self.draft.development_study.access_pair
        registrations, _, _ = operation_catalog()
        by_selection = {value.selection.selection_id: value for value in registrations}
        selected = set(self.draft.selected_operation_ids)
        operations = tuple(value for value in self.draft.operations if value.node_id in selected)
        by_node = {value.node_id: by_selection[value.selection.selection_id] for value in operations}
        configs = project_recursive_config_inputs(tuple(decode_recursive_config_input(value, by_node[value.node_id])
            for value in operations), by_node)
        contracts = derive_original_parent_input_contracts(actual, config_inputs=configs, registrations_for_node=by_node)
        if contracts and (self.original_input_access is None
                or any(value.input_parents != self.original_input_access.parents for value in contracts)):
            raise PermissionError("development custody lacks its actual complete original-parent access scope")
        self.original_input_contracts = {(value.task.object_id, value.logical_artifact_id): value for value in contracts}
        self.inputs = {value.logical.logical_artifact_id: value for value in
            _external_inputs(plane=writer, plan=actual, draft=self.draft, payloads=payloads, read_only=True)}
        self._original_member_facts = {(value.logical, value.materialization) for value in self.inputs.values()}
        self._original_member_facts.update((payloads.manifest(name).logical, payloads.manifest(name).materialization)
            for name in payloads)
        root = Path(writer.root.contract.canonical_path)
        relative = (Path(directory).resolve(strict=True) / "authored-wave.json").relative_to(root).as_posix()
        self.packet_manifest = self._manifest(relative)
        if (self.packet_manifest.logical.payload_schema != self.packet.SCHEMA
                or self.packet_manifest.logical.content_sha256 != self.packet.fingerprint()
                or self.packet_manifest.materialization.size_bytes != len(self.packet.canonical_bytes())):
            raise PermissionError("development custody substitutes its actual authored packet publication")
        self._require_current_original_access()

        self.initialize_task_reads()

    def _require_current_original_access(self):
        if getattr(self, "original_input_access", None) is not None:
            self.original_input_access.require_current()

    @development_read_call
    def require_input_member(self, manifest):
        """Refresh original permission before the storage owner's next body hash."""
        if self.original_input_access is None:
            return
        self._require_current_original_access()
        fact = manifest.logical, manifest.materialization
        if fact not in self._original_member_facts:
            # Input publication hashing precedes worker preparation. Authenticate
            # a descendant's complete successful receipt and exact input lineage
            # before its body or publication siblings can enter that first hash.
            owners = (self._output_owners.get(manifest.logical.logical_artifact_id, ())
                if hasattr(self, '_output_owners') else tuple(task for task in self.plan.tasks if any(
                    output.logical_artifact_id == manifest.logical.logical_artifact_id
                    for output in task.outputs)))
            if len(owners) == 1:
                task, = owners
                store = ExternalTaskReceiptStore(self.writer)
                receipts = tuple(receipt for candidate in self.index.task(task.task_id).attempts
                    if (receipt := store.read(self.run.run_plan_id, task.task_id, candidate.attempt_id)) is not None
                    and receipt.operational_status is OperationalStatus.SUCCEEDED)
                if len(receipts) != 1:
                    raise PermissionError("development input lacks its unique successful original producer receipt")
                outputs = self._receipt_outputs(task.task_id, receipts[0], _metadata_only=True)
                facts = {(value.logical, value.materialization) for value in outputs}
                if fact not in facts:
                    raise PermissionError("development input substitutes its exact original producer publication")
                self._original_member_facts.update(facts)
            else:
                # An original/authored member still needs its exact parent
                # census. A current grant or label admits no foreign body.
                self.original_input_access.require_member(manifest)
        self._require_current_original_access()

    @development_read_call
    def _manifest(self, relative, *, expected=None):
        limit = artifact_custody_limits(self.writer).manifest_bytes
        manifest = self.writer.read_manifest(relative, maximum_bytes=limit)
        if (manifest.materialization.relative_path != relative
                or manifest.materialization.storage_root_id != self.writer.root.contract.storage_root_id
                or (expected is not None and (manifest.logical != expected.logical
                    or manifest.materialization != expected.materialization))):
            raise PermissionError("development custody changes its exact original publication path or development lane")
        pair = (manifest.logical.outcome_access, manifest.logical.visibility_ceiling)
        if pair not in {(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY), self.access_pair}:
            if (expected is None or self.original_input_access is None
                    or manifest.logical.outcome_access is not OutcomeAccess.EVALUATION_SEALED):
                raise PermissionError("development custody lacks an exact owned protected input")
            self._require_current_original_access()
        options = {} if getattr(self, "original_input_access", None) is None else {"before_member": self.member_preflight}
        self.writer.verify_manifest(manifest, **options)
        self._require_current_original_access()
        return manifest

    @development_read_call
    def current_task(self, context, runner):
        if type(context) is not TaskContext:
            raise TypeError("development preparation requires its actual TaskContext")
        context.__post_init__()
        if self._manifest(self.packet_manifest.materialization.relative_path) != self.packet_manifest:
            raise PermissionError("development preparation changes its authenticated original authored packet")
        tasks = tuple(value for value in self.plan.tasks if value.task_id == context.task_id)
        if len(tasks) != 1:
            raise PermissionError("development preparation loses its exact original task")
        task, = tasks
        from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairRecoveryIndex
        dispatched = self.index.repair.task(task) if isinstance(self.index, DevelopmentOutputRepairRecoveryIndex) else task
        if (context.run_id != self.run.run_plan_id
                or (task.capability.capability_key, task.capability.capability_version, task.capability_implementation_sha256) !=
                    (runner.manifest.capability_key, runner.manifest.capability_version, runner.manifest.implementation_sha256)
                or (context.config.config_schema, context.config.config_schema_sha256) !=
                    (runner.manifest.config_schema, runner.manifest.config_schema_sha256)
                or task.capability.config != context.config or task.capability.requested_outcome_access is not self.access_pair[0]
                or context.outcome_access is not self.access_pair[0]
                or context.permissions != runner.manifest.permissions or context.permissions != task.capability.required_permissions
                or context.resource_budget != dispatched.capability.requested_resources
                or task.barrier is BarrierKind.REVEAL or context.scientific_adjudication_context is not None
                or context.output_ports != tuple(WorkerOutputPort(value.output_id, value.payload_schema, value.profile,
                    value.media_type, value.logical_artifact_id) for value in task.outputs)):
            raise PermissionError("development preparation changes its actual task, manifest, complete outputs or nonpromotable lane")
        if context.prepared_invocation is not None and context.prepared_invocation.execution_plan != ObjectIdentity.from_record(self.plan.execution_plan_id, self.plan):
            raise PermissionError("development preparation substitutes its actual original execution plan")
        return self.packet, self.plan, task

    @development_read_call
    def _receipt_outputs(self, task_id, receipt, *, _metadata_only=False, _ancestors=()):
        """Authenticate actual successful output metadata against its frozen owner."""
        from empirical_lawhood.runtime.artifacts import ArtifactManifest
        state = self._task_read()
        result = _development_receipt_output_metadata(writer=self.writer, plan=self.plan,
            index=self.index, inputs=self.inputs, task_id=task_id, receipt=receipt, _ancestors=_ancestors,
            _validated=None if state is None else state.receipts)
        if not _metadata_only:
            # Register the complete exact output census before storage inspects
            # any publication sibling. These are immutable facts, not permission.
            self._original_member_facts.update((value.logical, value.materialization) for value in result)
            for value in result:
                self._manifest(value.materialization.relative_path,
                    expected=ArtifactManifest(value.logical, value.materialization))
        return tuple(result)

    @development_read_call
    def require_original_input_access(self, task, value):
        """Fresh original grants after exact frozen task, receipt and input joins."""
        from empirical_lawhood.runtime.plans import ExternalInputSpec

        try:
            actual = self.plan.task(task.task_id)
        except KeyError:
            actual = None
        from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairRecoveryIndex
        if (actual is not None and isinstance(self.index, DevelopmentOutputRepairRecoveryIndex)
                and task == self.index.repair.task(actual)):
            task = actual
        contract = self.original_input_contracts.get((task.task_id, value.logical.logical_artifact_id))
        if (actual != task or contract is None or self.original_input_access is None
                or contract.task != ObjectIdentity.from_record(task.task_id, task)
                or contract.input_parents != self.original_input_access.parents):
            raise PermissionError("development input lacks its actual original-parent contract")
        spec = contract.input_spec
        if type(spec) is ExternalInputSpec:
            if self.inputs.get(spec.logical_artifact_id) != value:
                raise PermissionError("development input substitutes its authored original configuration")
            from empirical_lawhood.runtime.artifacts import ArtifactManifest
            self._manifest(value.materialization.relative_path, expected=ArtifactManifest(value.logical, value.materialization))
        else:
            store = ExternalTaskReceiptStore(self.writer)
            matched = []
            for candidate in self.index.task(spec.producer_task_id).attempts:
                receipt = store.read(self.run.run_plan_id, spec.producer_task_id, candidate.attempt_id)
                if receipt is not None and receipt.operational_status is OperationalStatus.SUCCEEDED:
                    matched.extend(row for row in self._receipt_outputs(spec.producer_task_id, receipt) if row == value)
            if len(matched) != 1:
                raise PermissionError("development input lacks its exact successful original producer receipt")
        self._require_current_original_access()

    @development_read_call
    def require_native_entry(self, context, runner, *, prepared_contract):
        from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairRecoveryIndex
        if type(self.index) is DevelopmentOutputRepairRecoveryIndex:
            raise PermissionError("development output repair cannot enter native acquisition")
        if type(prepared_contract) is not PreparedInvocationContract or prepared_contract.native_effect is not True:
            raise PermissionError("development native entry requires its exact prepared effect contract")
        prepared_contract.validate_context(context)
        _, plan, task = self.current_task(context, runner)
        if (prepared_contract.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan)
                or prepared_contract.execution_task != ObjectIdentity.from_record(task.task_id, task)
                or prepared_contract.execution_task_record != task
                or prepared_contract.implementation.observed_git_head != plan.implementation_commit
                or prepared_contract.manifest != runner.manifest):
            raise PermissionError("development native entry substitutes its actual prepared task")
        self.task_inputs(context, task)
        self._require_current_original_access()
        if self._native_continuation_entry_guard is not None:
            self._native_continuation_entry_guard(writer=self.writer, prepared_contract=prepared_contract)
        self._require_current_original_access()

    @development_read_call
    def task_inputs(self, context, task):
        from empirical_lawhood.infrastructure.execution import LocalScheduler

        store, by_task, dependencies = ExternalTaskReceiptStore(self.writer), {}, {}
        for header in context.dependency_receipts:
            receipt = store.read_by_receipt_id(context.run_id, header.task_id, header.receipt_id)
            if (receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
                    or not set(header.output_materialization_ids) <= {value.materialization_id for value in receipt.output_materializations}):
                raise PermissionError("development preparation changes an actual successful original dependency receipt")
            by_task[header.task_id] = receipt
            dependencies[header.task_id] = self._receipt_outputs(header.task_id, receipt)
        if tuple(sorted(by_task)) != task.dependency_task_ids:
            raise PermissionError("development preparation changes its actual dependency task census")
        selected = LocalScheduler._dependency_outputs(task, dependencies)
        expected = [WorkerInputBinding.from_verified(value, kind=WorkerInputKind.DEPENDENCY) for value in selected]
        if context.dependency_receipts != LocalScheduler._dependency_receipt_bindings(task, dependency_outputs=selected, receipts=by_task):
            raise PermissionError("development preparation changes selected original dependency outputs")
        controls = {}
        for spec in task.external_inputs:
            value = self.inputs.get(spec.logical_artifact_id)
            if value is None:
                raise PermissionError("development preparation adds an unauthored external input")
            from empirical_lawhood.runtime.artifacts import ArtifactManifest
            manifest = self._manifest(value.materialization.relative_path,
                expected=ArtifactManifest(value.logical, value.materialization))
            if (manifest.logical != value.logical or manifest.materialization != value.materialization
                    or any(wanted is not None and actual != wanted for actual, wanted in (
                        (manifest.logical.payload_schema, spec.expected_payload_schema), (manifest.logical.content_sha256, spec.expected_content_sha256),
                        (manifest.materialization.size_bytes, spec.expected_size_bytes), (manifest.logical.media_type, spec.expected_media_type),
                        (manifest.logical.outcome_access, spec.expected_outcome_access), (manifest.logical.visibility_ceiling, spec.expected_visibility_ceiling)))):
                raise PermissionError("development preparation changes an exact original external input")
            expected.append(WorkerInputBinding.from_verified(value, kind=WorkerInputKind.EXTERNAL))
            controls[spec.logical_artifact_id] = manifest
        if tuple(sorted(expected, key=lambda value: value.artifact_id)) != context.input_bindings:
            raise PermissionError("development preparation changes its complete actual input bindings")
        return by_task, controls

    @development_read_call
    def control_record(self, manifest, record_type, maximum):
        pair = (manifest.logical.outcome_access, manifest.logical.visibility_ceiling)
        if pair not in {(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY), self.access_pair}:
            owned = tuple(value for value in self.inputs.values() if value.logical == manifest.logical
                and value.materialization == manifest.materialization)
            if (not owned or self.original_input_access is None
                    or pair[0] is not OutcomeAccess.EVALUATION_SEALED):
                raise PermissionError("development control changes its exact original input custody")
            self._require_current_original_access()
        from empirical_lawhood.runtime.artifacts import ArtifactManifest
        self._manifest(manifest.materialization.relative_path,
            expected=ArtifactManifest(manifest.logical, manifest.materialization))
        self._require_current_original_access()
        raw = read_bounded_bytes(self.writer.root.resolve(manifest.materialization.relative_path, for_write=False),
            maximum_bytes=maximum)
        record = decode_canonical_bytes(raw, record_type, maximum_bytes=maximum)
        if (record.canonical_bytes() != raw or len(raw) != manifest.materialization.size_bytes
                or sha256(raw).hexdigest() != manifest.logical.content_sha256
                or sha256(raw).hexdigest() != manifest.materialization.physical_sha256):
            raise PermissionError("development configuration changes its exact canonical bytes")
        self._require_current_original_access()
        return record
