# SPDX-License-Identifier: MPL-2.0
"""General exposed development execution through the existing local scheduler."""

from dataclasses import replace
from hashlib import sha256
import json
import os

from empirical_lawhood.api.recursive_authoring import (
    _authenticate_authored_wave_roots, _external_storage_contract, implementation_binding, load_authored_wave,
)
from empirical_lawhood.api.recursive_operations import operation_catalog, operation_runners
from empirical_lawhood.runtime.artifacts import artifact_custody_limits
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactStreamWriteRequest, ArtifactWriteRequest, lineage_parent_sort_key
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan, DevelopmentRunPlan, PlanLane
from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryIndex

from .experiment_runtime_bindings import experiment_runtime_binding


def _retained_plans(payloads, draft):
    from empirical_lawhood.infrastructure.recursive_control_read import decode_authored_control
    from empirical_lawhood.runtime.recursive_compiler import derive_recursive_scientific_selection
    from empirical_lawhood.runtime.candidate_compiler import StudyTemplate
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    from empirical_lawhood.runtime.scientific_graph_preservation import DevelopmentGraphPreservationReceipt, prove_development_graph_parity

    def decode(name, codec):
        return decode_authored_control(payloads, name, codec)
    run = decode("run-plan.json", DevelopmentRunPlan)
    plan = decode("execution-plan.json", DevelopmentExecutionPlan)
    template = decode("template.json", StudyTemplate)
    # The projection repeats the draft's selected immutable scientific operands.
    # Use their owning pure projection and compare every retained byte, avoiding
    # a second parse and validation of the same large configuration records.
    selection = replace(derive_recursive_scientific_selection(draft),
        selection_id=run.scientific_projection.object_id)
    if payloads["scientific-projection.json"] != selection.canonical_bytes():
        raise ValueError("recursive retained scientific projection differs from its actual original draft")
    registry = decode("registry.json", CapabilityRegistry)
    proof = decode("graph-preservation.json", DevelopmentGraphPreservationReceipt)
    expected_proof = prove_development_graph_parity(draft=draft, selection=selection, template=template,
                                                   run_plan=run, execution_plan=plan, registry=registry)
    if proof != expected_proof:
        raise ValueError("recursive retained graph correspondence differs from the actual scientific/task fields")
    if plan.source_plan != ObjectIdentity.from_record(run.run_plan_id, run) or run.draft != ObjectIdentity.from_record(draft.draft_id, draft):
        raise ValueError("recursive execution substitutes its authored draft or scientific plan")
    index = DevelopmentRunRecoveryIndex.from_execution_plan(plan, run_id=run.run_plan_id,
        wave_id="wave.development", authority_identities=())
    from .development_output_repair import select_development_output_repair
    if getattr(payloads, "plane", None) is not None:
        index = select_development_output_repair(writer=payloads.plane, plan=plan, predecessor=index)
    return run, plan, index


def _can_batch_readonly_inputs(*, plane, payloads, input_count, policy):
    """Local stock-policy choice; every invocation still authenticates all bytes."""
    from empirical_lawhood.infrastructure.artifacts import (
        ExternalArtifactPlane, _ScopedArtifactPlane, _has_stock_manifest_reads,
    )
    from empirical_lawhood.infrastructure.recursive_custody import (
        AuthenticatedRecursivePayloads, _can_batch_authored_members,
    )
    current = _read_only_custody_policy(plane)
    return (input_count > 0 and type(payloads) is AuthenticatedRecursivePayloads
        and type(plane) in (ExternalArtifactPlane, _ScopedArtifactPlane)
        and (type(plane) is ExternalArtifactPlane or plane._read_verification.active)
        and type(policy) is tuple and current is not None
        and len(policy) == len(current) and all(a is b for a, b in zip(policy, current))
        and _has_stock_manifest_reads(plane) and _can_batch_authored_members(plane, input_count))


def _external_inputs(*, plane, plan, draft, payloads, read_only, _allow_batch=True, _source_scope=False,
        _publication_writer=None):
    """Materialize only exact declared inputs, preserving their scoped lineage."""
    from empirical_lawhood.infrastructure.recursive_custody import read_exposed_recursive_payload
    from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads
    from empirical_lawhood.infrastructure.artifacts import supports_closed_batch_writes, _has_stock_manifest_reads
    from empirical_lawhood.infrastructure.recursive_custody import _can_batch_authored_members
    writer = plane if _publication_writer is None else _publication_writer
    if (_allow_batch and not read_only and not _source_scope
            and type(payloads) is AuthenticatedRecursivePayloads and supports_closed_batch_writes(writer)
            and _has_stock_manifest_reads(payloads.plane)
            and _can_batch_authored_members(payloads.plane, len(payloads))):
        # Source reads share their finite proof while the ordinary output plane
        # publishes distinct run aliases. Close all source bytes before returning
        # to resource admission or dispatch; no read view gains write authority.
        with payloads.plane.read_context() as source_reader:
            sources = AuthenticatedRecursivePayloads(plane=source_reader, directory=payloads.directory,
                members=tuple(payloads._members.values()), original_input_access=payloads.original_input_access)
            return _external_inputs(plane=plane, plan=plan, draft=draft, payloads=sources,
                read_only=read_only, _allow_batch=_allow_batch, _source_scope=True,
                _publication_writer=writer)
    lazy = isinstance(payloads, AuthenticatedRecursivePayloads)
    original_access = getattr(payloads, "original_input_access", None)
    if original_access is not None:
        original_access.require_current()
    guarded_reads = {} if original_access is None else {"before_member": original_access.require_member}
    raws = {} if lazy else {sha256(raw).hexdigest(): raw for raw in payloads.values()}
    retained = {payloads.manifest(name).logical.content_sha256: payloads.manifest(name)
                for name in payloads} if lazy else {}
    names = {payloads.manifest(name).logical.content_sha256: name for name in payloads} if lazy else {}
    specs = {}
    for task in plan.tasks:
        for spec in task.external_inputs:
            if spec.logical_artifact_id in specs and specs[spec.logical_artifact_id] != replace(spec, input_id=specs[spec.logical_artifact_id].input_id):
                raise ValueError("recursive external input has conflicting frozen specifications")
            specs[spec.logical_artifact_id] = spec
    policy = (_read_only_custody_policy(plane) if _allow_batch is True
        and (read_only or supports_closed_batch_writes(writer)) else None)
    batch = _can_batch_readonly_inputs(plane=plane, payloads=payloads, input_count=len(specs), policy=policy)
    if batch:
        from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
        if type(plane) is ExternalArtifactPlane:
            # Full reads own this input-only scope. It closes before all later
            # typed/domain consumers; compact reads reuse their existing scope.
            with plane.verification_scope() as scoped:
                return _external_inputs(plane=scoped, plan=plan, draft=draft, payloads=payloads,
                    read_only=read_only, _allow_batch=_allow_batch, _source_scope=_source_scope,
                    _publication_writer=writer)
    from .recursive_operations import operation_storage_codecs
    storage_codecs = operation_storage_codecs()
    pending = []
    values = []
    writes, selections = [], []
    write_batches = batch and not read_only and supports_closed_batch_writes(writer)

    def require_current():
        if original_access is not None:
            original_access.require_current()

    def accept(spec, artifact_id, raw, raw_size, access, visibility, parents, expected_profile, relative, path):
        manifest = plane.read_manifest(relative, maximum_bytes=artifact_custody_limits(plane).manifest_bytes)
        if (manifest.materialization.relative_path != relative or manifest.logical.logical_artifact_id != artifact_id
            or manifest.logical.payload_schema != spec.expected_payload_schema
            or manifest.logical.content_sha256 != spec.expected_content_sha256
            or manifest.logical.profile is not expected_profile
            or manifest.logical.media_type != spec.expected_media_type
            or manifest.logical.visibility_ceiling is not visibility
            or manifest.logical.outcome_access is not access
            or manifest.logical.lineage_parents != parents
            or manifest.materialization.size_bytes != raw_size):
            raise ValueError("recursive retained input changes its frozen scientific identity")
        if lazy:
            if (batch and manifest.publication is not None
                    and manifest.materialization.physical_sha256 == spec.expected_content_sha256):
                pending.append(manifest)
            else:
                # Unknown/equivalence forms retain the original singular
                # validator and exact byte comparison for this member.
                plane.verify_manifest(manifest, **guarded_reads)
                if original_access is not None:
                    original_access.require_member(manifest)
                size, digest = bounded_file_sha256(path, maximum_bytes=raw_size)
                if size != raw_size or digest != spec.expected_content_sha256:
                    raise ValueError("recursive retained input differs from its authored bytes")
        elif read_exposed_recursive_payload(plane, manifest, maximum_bytes=raw_size) != raw:
            raise ValueError("recursive retained input differs from its authored bytes")
        values.append(VerifiedArtifactInput(manifest.logical, manifest.materialization))
        if original_access is not None:
            original_access.require_current()
    for number, (artifact_id, spec) in enumerate(sorted(specs.items())):
        raw = raws.get(spec.expected_content_sha256)
        member = retained.get(spec.expected_content_sha256)
        if raw is None and member is None:
            raise ValueError("authored wave omits an exact external/configuration operand")
        raw_size = member.materialization.size_bytes if member is not None else len(raw)
        access, visibility = spec.expected_outcome_access, spec.expected_visibility_ceiling
        allowed = {(OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)}
        if draft.development_study.access_pair[0] is OutcomeAccess.EVALUATION_REVEALED:
            allowed.add(draft.development_study.access_pair)
        if (access, visibility) not in allowed and not (
                original_access is not None and member is not None
                and access is OutcomeAccess.EVALUATION_SEALED
                and (member.logical.outcome_access, member.logical.visibility_ceiling) == (access, visibility)):
            raise ValueError("recursive input changes its exact exposed study access")
        if original_access is not None and member is not None:
            original_access.require_member(member)
            parent = ArtifactLineageParent(payloads.member_identity(names[spec.expected_content_sha256]),
                member.logical.visibility_ceiling, member.logical.outcome_access)
            parents = tuple(sorted({value.identity: value for value in
                (*member.logical.lineage_parents, parent)}.values(), key=lineage_parent_sort_key))
        else:
            parents = (ArtifactLineageParent(ObjectIdentity.from_record(draft.draft_id, draft),
                VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE),)
        expected_profile, suffix = _external_storage_contract(
            payload_schema=spec.expected_payload_schema, media_type=spec.expected_media_type,
            storage_codecs=storage_codecs)
        relative = f"runs/{plan.source_plan.object_id}/inputs/input-{number:04d}{suffix}"
        path = plane.root.resolve(relative, for_write=False)
        manifest_path = plane.root.resolve(relative + ".manifest.json", for_write=False)
        if write_batches or not path.exists() and not manifest_path.exists():
            if read_only:
                raise ValueError("completed recursive wave omits its retained input materialization")
            if lazy:
                request = ArtifactStreamWriteRequest(
                    logical_artifact_id=artifact_id, relative_path=relative,
                    payload_schema=spec.expected_payload_schema, profile=expected_profile,
                    media_type=spec.expected_media_type, publication_scope_id=plan.source_plan.object_id + ".inputs",
                    publication_scope_relative_root=f"runs/{plan.source_plan.object_id}/inputs",
                    chunks=payloads.chunks(names[spec.expected_content_sha256]), maximum_bytes=max(1, raw_size),
                    maximum_chunk_bytes=min(65536, max(1, raw_size)), expected_size_bytes=raw_size,
                    expected_physical_sha256=spec.expected_content_sha256,
                    visibility_ceiling=visibility,
                    parent_visibility_ceilings=tuple(value.visibility_ceiling for value in parents),
                    outcome_access=access, lineage_parents=parents)
            else:
                request = ArtifactWriteRequest(artifact_id, relative, spec.expected_payload_schema,
                    expected_profile, spec.expected_media_type, plan.source_plan.object_id + ".inputs",
                    f"runs/{plan.source_plan.object_id}/inputs", raw, visibility,
                    tuple(value.visibility_ceiling for value in parents), access,
                    lineage_parents=parents)
            if write_batches:
                writes.append(request)
                selections.append((spec, artifact_id, raw, raw_size, access, visibility, parents,
                    expected_profile, relative, path))
                continue
            if lazy:
                plane.write_stream(request)
            else:
                plane.write(request)
        accept(spec, artifact_id, raw, raw_size, access, visibility, parents, expected_profile, relative, path)
    if writes:
        from empirical_lawhood.infrastructure.recursive_input_publication import publish_recursive_metadata
        publish_recursive_metadata(writer, writes, require_current=require_current,
            before_member=None if original_access is None else original_access.require_member)
        for selection in selections:
            accept(*selection)
    if pending:
        def require_policy():
            if original_access is not None:
                original_access.require_current()
            if not _can_batch_readonly_inputs(plane=plane, payloads=payloads,
                    input_count=len(specs), policy=policy):
                raise ValueError("recursive input custody policy changed during its bounded read")
        def consume(authenticated):
            require_policy()
            for manifest in pending:
                actual = authenticated.get(manifest.materialization.relative_path)
                if actual != manifest:
                    raise ValueError("recursive retained input changes its actual publication metadata")
                # The stock owner just independently scanned every physical
                # byte and checked exact logical/physical equality. The original
                # scientific spec/role/lineage/size checks above remain intact.
                if actual.materialization.physical_sha256 != actual.logical.content_sha256:
                    raise ValueError("recursive retained input differs from its authored bytes")
            require_policy()
        require_policy()
        plane.verify_manifests_members(tuple(pending), validate_members=consume, **guarded_reads)
        require_policy()
    if original_access is not None:
        original_access.require_current()
    return tuple(values)


def _provenance(*, plane, run_id, observed=None):
    from empirical_lawhood.api.numerical_provenance import authenticate_recorded_numerical_provenance
    from empirical_lawhood.infrastructure.development_native_custody import read_development_native_payload
    from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
    from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance

    relative = f"runs/{run_id}/inputs/producing-provenance.json"
    path = plane.root.resolve(relative, for_write=False)
    manifest_path = plane.root.resolve(relative + ".manifest.json", for_write=False)
    if not path.exists() and not manifest_path.exists():
        if observed is None:
            raise ValueError("recursive result omits its actual producing provenance")
        plane.write(ArtifactWriteRequest(run_id + ".producing-provenance", relative, observed.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", run_id + ".inputs",
            f"runs/{run_id}/inputs", observed.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
            (), OutcomeAccess.DEVELOPMENT_VISIBLE))
    manifest = decode_artifact_manifest(read_bounded_bytes(manifest_path, maximum_bytes=artifact_custody_limits(plane).manifest_bytes), maximum_bytes=artifact_custody_limits(plane).manifest_bytes)
    if manifest.materialization.relative_path != relative or manifest.logical.payload_schema != NumericalProducingProvenance.SCHEMA:
        raise ValueError("recursive producing provenance changes its exact record/path")
    size = max(1, manifest.materialization.size_bytes)
    retained = decode_canonical_bytes(read_development_native_payload(plane, manifest, maximum_bytes=size),
                                      NumericalProducingProvenance, maximum_bytes=size)
    authenticate_recorded_numerical_provenance(retained)
    if observed is not None:
        def runtime(record):
            value = json.loads(record.runtime_observation_json)
            # Loaded-library enumeration order is process-local. Preserve every
            # observed library field while comparing the complete pool census.
            value["threadpools"] = sorted(value["threadpools"], key=lambda row: json.dumps(row, sort_keys=True))
            return value
        fields = ("package_sources", "code_sources_sha256", "dependency_lock_sha256", "observed_git_head")
        changed = [field for field in fields if getattr(retained, field) != getattr(observed, field)]
        if runtime(retained) != runtime(observed):
            changed.append("numerical_runtime")
        if changed:
            raise ValueError("recursive recovery changes producing commitments: " + ", ".join(changed))
    return retained


def _validate_terminal_product_format(value):
    if value not in ("documents", "references", "compact"):
        raise ValueError("terminal_product_format must be 'documents', 'references' or 'compact'")


def _authored_partial_read(*, packet, draft, run, plan):
    """Project authenticated authoring when no execution custody has been retained.

    Missing completion evidence does not establish whether a process entered.
    The authored source is a selection, never an observed producing provenance.
    """
    dispositions = [{"task_id": task_id, "operational_status": "NO_COMPLETION_RECEIPT",
        "reason_code": "ENTRY_OR_PROCESS_STATE_NOT_INFERRED"} for task_id in plan.topological_task_ids()]
    products = {"terminal": None, "receipts": {}, "records": {}, "outputs": {},
        "dispositions": dispositions, "operational_census": (), "recovery_events": {},
        "attempt_receipts": {}, "product_index": (), "typed_product_validation": "DEFERRED",
        "connection_assessments": ()}
    report = {"run_id": run.run_plan_id, "status": "PARTIAL",
        "packet_sha256": packet.fingerprint(), "draft_sha256": draft.fingerprint(),
        "execution_plan_sha256": plan.fingerprint(), "producing_provenance_sha256": None,
        "producing_code_sha256": None, "dependency_lock_sha256": None,
        "observed_producing_git_head": None, "observed_producing_checkout_clean": None,
        "assigned_unit_ids": draft.development_study.assigned_unit_ids,
        "connection_assessments": (), "task_count": len(plan.tasks), "task_census": dispositions,
        "operational_census": (), "retained_product_index": (), "terminal_products": {},
        "retained_directory": "runs/" + run.run_plan_id, "native_contact": "none",
        "new_native_contact_count": 0, "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED",
        "terminal_product_format": "compact", "typed_product_validation": "DEFERRED",
        "connection_assessment_projection": "NOT_DECODED",
        "scientific_completion": "NOT_ASSESSED_BY_COMPACT_CUSTODY", "operational_terminal": "ABSENT"}
    return report, products, draft, plan


def read_recursive_wave(*, directory, artifact_writer, include_products=False,
                        terminal_product_format="documents", allow_partial=False, read_access=None,
                        expected_specification_bytes=None, allow_unexecuted=False):
    """Authenticate complete products; optionally report their exact custody references."""
    result, _ = _read_recursive_wave_with_retained_roots(directory=directory, artifact_writer=artifact_writer,
        include_products=include_products, terminal_product_format=terminal_product_format,
        allow_partial=allow_partial, read_access=read_access,
        expected_specification_bytes=expected_specification_bytes, allow_unexecuted=allow_unexecuted)
    return result


def _read_recursive_wave_with_retained_roots(*, directory, artifact_writer, include_products=False,
                        terminal_product_format="documents", allow_partial=False, read_access=None,
                        expected_specification_bytes=None, allow_unexecuted=False, _scientific_consumer=None):
    """Return immutable authored roots from the same fully guarded public read.

    Locator consumers need the actual packet and run, not another packet load
    after science. No payload mapping or read authority escapes this boundary.
    """
    from contextlib import nullcontext
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane

    # Stock full reads share one immutable custody context through scientific
    # replay. Current access and explicit pre-product guards remain eager.
    # The compact report changes presentation, not the immutable input census.
    # It needs the same bounded read lifetime as documents and references.
    # Custom policies retain their original eager route.
    stock = (type(artifact_writer) is ExternalArtifactPlane
        and _read_only_custody_policy(artifact_writer) is not None)
    if stock and type(terminal_product_format) is str and terminal_product_format in ("documents", "references", "compact"):
        scope = artifact_writer.read_context()
    else:
        scope = nullcontext(artifact_writer)
    ordinary_writer = artifact_writer
    original_accesses = []
    unexecuted_paths = []
    with scope as artifact_writer:
        result, roots, _ = _read_recursive_wave_with_roots(directory=directory, artifact_writer=artifact_writer,
            include_products=include_products, terminal_product_format=terminal_product_format,
            allow_partial=allow_partial, read_access=read_access,
            expected_specification_bytes=expected_specification_bytes, allow_unexecuted=allow_unexecuted,
            scientific_consumer=_scientific_consumer,
            _retain_unexecuted_guard=unexecuted_paths.append,
            _retain_original_input_access=original_accesses.append)
    for original_access in original_accesses:
        original_access.require_current(artifact_writer=ordinary_writer)
    for run_path in unexecuted_paths:
        if run_path.exists() or run_path.is_symlink():
            raise ValueError("recursive execution custody appeared during authored-only inspection; retry the read")
    return result, roots


def _read_only_custody_policy(artifact_writer):
    """Select actual stock composition for one bounded readonly custody phase."""
    from empirical_lawhood.api.integration_artifact_profiles import INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry
    from empirical_lawhood.infrastructure.artifacts import (
        GuardedExternalRoot, LocalFilesystemInspector, _has_stock_artifact_plane_state,
    )
    from empirical_lawhood.runtime.artifacts import ExternalRootContract, ArtifactSemanticValidationRegistry, ArtifactCustodyLimits

    if (not _has_stock_artifact_plane_state(artifact_writer)
            or type(artifact_writer.validators) is not ArtifactProfileValidatorRegistry
            or artifact_writer.validators.binary_codecs != INTEGRATION_ARTIFACT_PROFILE_VALIDATORS.binary_codecs
            or type(artifact_writer.custody_limits) is not ArtifactCustodyLimits):
        return None
    # Current callers can construct the same closed installed codec roster
    # without the API singleton. Immutable schema contracts remain owned by
    # their actual registry; an added/replaced custom codec stays eager.
    root = artifact_writer.root
    if (type(root) is not GuardedExternalRoot or set(vars(root)) != {"contract", "inspector"}
            or type(root.contract) is not ExternalRootContract
            or type(root.inspector) is not LocalFilesystemInspector
            or set(vars(root.inspector)) != {"_bound"}
            or type(artifact_writer.semantic_validations) is not ArtifactSemanticValidationRegistry):
        return None
    return root, root.inspector, root.contract, artifact_writer.validators, artifact_writer.semantic_validations, artifact_writer.custody_limits


def _read_recursive_wave_with_roots(*, directory, artifact_writer, include_products=False,
                        terminal_product_format="documents", allow_partial=False, validate_authored=None,
                        scientific_consumer=None, read_access=None, _retain_original_input_access=None,
                        expected_specification_bytes=None, allow_unexecuted=False, _retain_unexecuted_guard=None):
    """Compose a fresh read with preflight values within this invocation only.

    The private callback runs before products. Only decoded roots and callback
    values escape; the live payload mapping is never returned or accepted as a
    replacement for a later read. The public wrapper keeps its original result.
    """
    _validate_terminal_product_format(terminal_product_format)
    if type(allow_unexecuted) is not bool:
        raise TypeError("authored-only inspection requires an explicit unexecuted selection")
    if expected_specification_bytes is not None and type(expected_specification_bytes) is not bytes:
        raise TypeError("selected development specification must have exact canonical bytes")
    if allow_partial and terminal_product_format != "compact":
        raise ValueError("partial recursive custody requires the explicit compact report route")
    from empirical_lawhood.infrastructure.recursive_custody import (
        RAW_BYTES_CONSUMER_JOIN_DEFERRED, read_recursive_products,
    )
    from empirical_lawhood.infrastructure.artifacts import _ScopedArtifactPlane
    from .experiment_scientific_read import read_prepared_development_science

    if validate_authored is not None and not callable(validate_authored):
        raise TypeError("authored read preflight requires a callable")
    if scientific_consumer is not None and not callable(scientific_consumer):
        raise TypeError("original scientific consumption requires a callable owning reader")
    if _retain_original_input_access is not None and not callable(_retain_original_input_access):
        raise TypeError("original access lifetime requires its private owning callback")
    if _retain_unexecuted_guard is not None and not callable(_retain_unexecuted_guard):
        raise TypeError("unexecuted read lifetime requires its private owning callback")
    consume_science = read_prepared_development_science if scientific_consumer is None else scientific_consumer
    compact = terminal_product_format == "compact"
    def load_roots():
        packet, draft, source, payloads = load_authored_wave(directory=directory,
            artifact_writer=artifact_writer, lazy_payloads=True, read_access=read_access)
        original_access = getattr(payloads, "original_input_access", None)
        if original_access is not None and _retain_original_input_access is not None:
            _retain_original_input_access(original_access)
        run, plan, index = _retained_plans(payloads, draft)
        return (packet, draft, source, run, plan, index), payloads
    roots, payloads = load_roots()
    packet, draft, source, run, plan, index = roots
    if (expected_specification_bytes is not None
            and payloads.get("experiment-specification.json") != expected_specification_bytes):
        raise PermissionError("Matrix child changes its actual original development specification")
    # The owning load supplies the plan and exact specification together. A
    # genuinely absent run can be projected without a preliminary second load;
    # any existing custody retains the caller's ordinary full-read checks.
    run_path = artifact_writer.root.resolve("runs/" + run.run_plan_id, for_write=False)
    if allow_unexecuted and not run_path.exists() and not run_path.is_symlink():
        allow_partial, terminal_product_format, compact = True, "compact", True
        if _retain_unexecuted_guard is not None:
            _retain_unexecuted_guard(run_path)

    def read_products():
        from .experiment_scientific_read import validate_prepared_development_read_access
        validate_prepared_development_read_access(directory=directory, artifact_writer=artifact_writer,
            payloads=payloads, draft=draft, plan=plan, read_access=read_access)
        science_options = {} if read_access is None else {"read_access": read_access}
        # Authoring retains the complete selected packet, not execution inputs,
        # producing provenance or recovery custody. Only an entirely absent run
        # namespace admits this pending projection. Existing run custody, including
        # a partial or corrupted member, retains all ordinary strict checks below.
        run_path = artifact_writer.root.resolve("runs/" + run.run_plan_id, for_write=False)
        if allow_partial and not run_path.exists() and not run_path.is_symlink():
            selected = _authored_partial_read(packet=packet, draft=draft, run=run, plan=plan)
            scientific = consume_science(directory=directory, artifact_writer=artifact_writer,
                payloads=payloads, report=selected[0], products=selected[1], draft=draft, plan=plan,
                allow_partial=allow_partial, **science_options)
            if scientific is not None:
                selected[0]["scientific_result"] = scientific
            if run_path.exists() or run_path.is_symlink():
                raise ValueError("recursive execution custody appeared during authored-only inspection; retry the read")
            return selected if include_products else selected[0]
        inputs = _external_inputs(plane=artifact_writer, plan=plan, draft=draft, payloads=payloads, read_only=True)
        provenance = _provenance(plane=artifact_writer, run_id=run.run_plan_id)
        if (provenance.code_sources_sha256, provenance.dependency_lock_sha256, provenance.observed_git_head) != (
            source.code_sources_sha256, source.dependency_lock_sha256, source.observed_git_head):
            raise ValueError("recursive producing evidence differs from the selected authored source")
        registrations, _, codecs = operation_catalog()
        from empirical_lawhood.api.numerical_provenance import validate_registered_provenance
        validate_registered_provenance(provenance=provenance, draft=draft, registrations=registrations)
        if isinstance(artifact_writer, _ScopedArtifactPlane):
            artifact_writer.require_verification_snapshot()
        original_access = getattr(payloads, "original_input_access", None)
        product_options = {} if original_access is None else {"original_input_access": original_access}
        products = read_recursive_products(plane=artifact_writer, plan=plan, index=index,
                                           external_inputs=inputs, output_codecs=codecs,
                                           decode_products=not compact, allow_partial=allow_partial,
                                           _read_policy=_read_only_custody_policy(artifact_writer),
                                           **product_options)
        products['external_inputs'] = inputs
        from empirical_lawhood.runtime.recursive_compiler import project_recursive_assessments
        authenticated_outputs = {(task_id, output_id.removeprefix(task_id + ".")): record
                                 for task_id, values in products["records"].items() for output_id, record in values.items()}
        assessments = () if compact else project_recursive_assessments(
            draft=draft, registrations=registrations, outputs=authenticated_outputs)
        products["connection_assessments"] = assessments
        product_index = list(products["product_index"])
        indexed_products = {(row['task_id'], row['output_id']): row for row in product_index}
        if len(indexed_products) != len(product_index):
            raise ValueError('retained products repeat a task/output identity')
        for task_id, records in sorted(products["records"].items()):
            receipt = products["receipts"][task_id]
            for output_id, record in sorted(records.items()):
                matches = tuple(value for value in receipt.output_logical_artifacts
                                if value.payload_schema == record.SCHEMA and value.content_sha256 == record.fingerprint())
                if len(matches) != 1:
                    raise ValueError("retained scientific product lacks its unique exact receipt output")
                artifact = products["outputs"][matches[0].logical_artifact_id]
                projected = {"task_id": task_id, "output_id": output_id,
                    "logical_artifact_id": artifact.logical.logical_artifact_id, "schema": record.SCHEMA,
                    "sha256": record.fingerprint(), "size_bytes": artifact.materialization.size_bytes,
                    "relative_path": artifact.materialization.relative_path,
                    "producing_receipt": ObjectIdentity.from_record(receipt.receipt_id, receipt).to_document(),
                    "outcome_access": artifact.logical.outcome_access.value,
                    "visibility_ceiling": artifact.logical.visibility_ceiling.value}
                if indexed_products.get((task_id, output_id)) != projected:
                    raise ValueError("typed product projection changes its authenticated custody index")
        depended = {dependency for task in plan.tasks for dependency in task.dependency_task_ids}
        if terminal_product_format in ("references", "compact"):
            terminal_products = {}
            for row in product_index:
                if row["task_id"] not in depended:
                    terminal_products.setdefault(row["task_id"], {})[row["output_id"]] = dict(
                        indexed_products[row["task_id"], row["output_id"]])
        else:
            terminal_products = {task_id: {name: record.to_document() for name, record in values.items()}
                                 for task_id, values in products["records"].items() if task_id not in depended}
            for row in product_index:
                if row["task_id"] not in depended:
                    terminal_products.setdefault(row["task_id"], {}).setdefault(row["output_id"], dict(row))
        report = {"run_id": run.run_plan_id,
                  "status": "PARTIAL" if products["terminal"] is None else products["terminal"].operational_status,
                  "packet_sha256": packet.fingerprint(), "draft_sha256": draft.fingerprint(),
                  "execution_plan_sha256": plan.fingerprint(), "producing_provenance_sha256": provenance.fingerprint(),
                  "producing_code_sha256": provenance.code_sources_sha256,
                  "dependency_lock_sha256": provenance.dependency_lock_sha256,
                  "observed_producing_git_head": provenance.observed_git_head,
                  "observed_producing_checkout_clean": provenance.observed_checkout_clean,
                  "assigned_unit_ids": draft.development_study.assigned_unit_ids,
                  "connection_assessments": tuple(value.to_document() for value in assessments),
                  "task_count": len(plan.tasks), "task_census": products["dispositions"],
                  "operational_census": products["operational_census"],
                  "retained_product_index": tuple(product_index),
                  "terminal_products": terminal_products,
                  "retained_directory": "runs/" + run.run_plan_id, "native_contact": "none",
                  "new_native_contact_count": 0,
                  "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED",
                  "operational_terminal": "ABSENT" if products["terminal"] is None else "AUTHENTICATED"}
        native_facts = products.get("native_observations", {})
        unavailable = products.get("native_observation_unavailable", {})
        if native_facts or unavailable:
            # These are current primary call facts beside the unchanged
            # operational census. A raw return is not parent completion.
            report["current_native_facts"] = tuple({
                "attempt_id": attempt_id, "task_id": observation.work.expected_parent.task_id,
                "uncertain_contact_definition_ids": tuple(pin.to_document()
                    for pin in observation.uncertain_contact_definition_ids),
                "pending_publication_definition_ids": tuple(pin.to_document()
                    for pin in observation.pending_publication_definition_ids),
                "uncontacted_definition_ids": tuple(pin.to_document()
                    for pin in observation.uncontacted_definition_ids),
                "failed_return_definition_ids": tuple(pin.to_document()
                    for pin in observation.failed_return_definition_ids),
                "native_returns": tuple({"definition": row.definition.identity.to_document(),
                    "native_return_status": None if row.native_return_status is None else row.native_return_status.value}
                    for row in observation.inspections)} for attempt_id, observation in sorted(native_facts.items()))
            report["native_observation_unavailable"] = tuple({"attempt_id": attempt_id, "reason": reason}
                for attempt_id, reason in sorted(unavailable.items()))
        if products["typed_product_validation"] == RAW_BYTES_CONSUMER_JOIN_DEFERRED:
            report["raw_array_validation"] = "EXACT_CUSTODY_CONSUMER_MANIFEST_JOIN_DEFERRED"
        if terminal_product_format in ("references", "compact"):
            report["terminal_product_format"] = terminal_product_format
        if compact:
            report["typed_product_validation"] = "DEFERRED"
            report["connection_assessment_projection"] = "NOT_DECODED"
            report["scientific_completion"] = "NOT_ASSESSED_BY_COMPACT_CUSTODY"
        from .development_output_repair import repair_report
        report.update(repair_report(index))
        scientific = consume_science(directory=directory, artifact_writer=artifact_writer,
            payloads=payloads, report=report, products=products, draft=draft, plan=plan,
            allow_partial=allow_partial, **science_options)
        if scientific is not None:
            report["scientific_result"] = scientific
        return (report, products, draft, plan) if include_products else report


    if validate_authored is None:
        # Ordinary public reads add no verification pass or payload context.
        return read_products(), roots, None
    def validate():
        return validate_authored(packet=packet, draft=draft, source=source, payloads=payloads,
            run=run, plan=plan, index=index)
    from empirical_lawhood.infrastructure.recursive_custody import (
        AuthenticatedRecursivePayloads, _can_batch_authored_members,
    )
    # The infrastructure owner preserves stock/custom policy and request limits.
    original_access = getattr(payloads, "original_input_access", None)
    guarded_reads = {} if original_access is None else {"before_member": original_access.require_member}
    batch = (type(payloads) is AuthenticatedRecursivePayloads
        and _can_batch_authored_members(artifact_writer, len(payloads) + 1))
    if batch:
        relative = (payloads.directory / "authored-wave.json").relative_to(
            artifact_writer.root.contract.canonical_path).as_posix()
        retained_packet = artifact_writer.read_manifest(relative)
        if (retained_packet.logical.payload_schema != packet.SCHEMA
                or (retained_packet.logical.outcome_access, retained_packet.logical.visibility_ceiling) !=
                    (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
                or retained_packet.logical.content_sha256 != packet.fingerprint()
                or retained_packet.materialization.physical_sha256 != packet.fingerprint()
                or retained_packet.materialization.size_bytes != packet.canonical_size_bytes()):
            raise ValueError("recursive preflight changes its actual authored packet")
        manifests = (retained_packet, *(payloads.manifest(name) for name in payloads))
        def consume(authenticated):
            if any(authenticated[value.materialization.relative_path] != value for value in manifests):
                raise ValueError("recursive preflight changes its exact authored metadata")
            preflight = validate()
            # Repeat the removed second-load boundary before any products:
            # current authored bytes plus all actual parents/origin files and
            # registered premises, including FILE bytes outside snapshots.
            artifact_writer.verify_manifests(manifests, **guarded_reads)
            _authenticate_authored_wave_roots(packet=packet, draft=draft, source=source,
                payloads=payloads, artifact_writer=artifact_writer, lazy_payloads=True)
            if isinstance(artifact_writer, _ScopedArtifactPlane):
                artifact_writer.require_verification_snapshot()
            return read_products(), roots, preflight
        # Existing owner checks complete raw bodies before the callback, then
        # every retained path/descriptor before returning, even without a scope.
        return artifact_writer.verify_manifests_members(manifests, validate_members=consume, **guarded_reads)
    preflight = validate()
    original_roots = roots
    roots, payloads = load_roots()
    if roots != original_roots:
        raise ValueError("recursive preflight changes its actual authored source or graph")
    packet, draft, source, run, plan, index = roots
    if isinstance(artifact_writer, _ScopedArtifactPlane):
        artifact_writer.require_verification_snapshot()
    return read_products(), roots, preflight


def _custody_control_pins(artifact_writer, index):
    """Bounded fresh primary control census; scientific arrays are not reopened."""
    paths = {index.index_relative_path, index.terminal_event_relative_path}
    from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairRecoveryIndex
    from .development_output_repair import repair_relative_path
    indexes = (index,)
    if isinstance(index, DevelopmentOutputRepairRecoveryIndex):
        indexes += (index.predecessor,)
        from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepairRecoveryIndex
        if type(index) is DevelopmentControllerRepairRecoveryIndex:
            from .development_controller_repair import repair_relative_path
        from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationRecoveryIndex
        if type(index) is DevelopmentNativeContinuationRecoveryIndex:
            from .native_continuation_execution import continuation_relative_path as repair_relative_path
        paths.add(repair_relative_path(index.run_id))
    for owner in indexes:
        paths.update((owner.index_relative_path, owner.terminal_event_relative_path))
        for binding in owner.tasks:
            paths.add(binding.nonattempt_event_relative_path)
            for candidate in binding.attempts:
                paths.update((candidate.receipt_relative_path, candidate.event_relative_path))
    rows = []
    limit = artifact_custody_limits(artifact_writer).control_record_bytes
    selected_paths = tuple(selected for relative in sorted(paths)
        for selected in (relative, relative + ".manifest.json"))
    with artifact_writer.root.read_paths(selected_paths) as resolved:
        for selected, path in resolved.items():
            if not path.exists():
                rows.append((selected, None, None))
            else:
                size, digest = bounded_file_sha256(path, maximum_bytes=limit)
                rows.append((selected, size, digest))
    return tuple(rows)


def _custody_contacts(*, plan, index, contacts, receipts, external_inputs, attempts, native_keys):
    """Join actual original parent headers with the DEV task's declared inputs."""
    from empirical_lawhood.runtime.native_effects import NativeEffectContact
    from empirical_lawhood.runtime.execution import dependency_artifact_inputs
    by_task = {row.task_id: row for row in receipts}
    dependency_outputs = {}
    for receipt in receipts:
        logicals = {row.logical_artifact_id: row for row in receipt.output_logical_artifacts}
        try:
            dependency_outputs[receipt.task_id] = tuple(VerifiedArtifactInput(logicals[row.logical_artifact_id], row)
                for row in receipt.output_materializations)
        except KeyError as error:
            raise PermissionError("custody-only native contact loses its actual producer logical identity") from error
    external = {row.logical.logical_artifact_id: row for row in external_inputs}
    latest = {row.task_id: row for row in sorted(attempts, key=lambda row: (row.task_id, row.ordinal))}
    result = []
    for task in plan.tasks:
        contact = contacts.read(index.run_id, task.task_id)
        prior = latest.get(task.task_id)
        native = task.capability.capability_key in native_keys
        if contact is None:
            if (native and task.task_id in by_task or prior is not None and prior.reason_code == "unknown-completion"):
                raise PermissionError("custody-only recovery lost an original native parent contact")
            result.append((task.task_id, None))
            continue
        candidates = {row.attempt_id for row in index.task(task.task_id).attempts}
        if not native or prior is None or contact.attempt_id != prior.attempt_id or contact.attempt_id not in candidates:
            raise PermissionError("custody-only recovery changes original native contact/task/attempt ancestry")
        try:
            materials = {external[row.logical_artifact_id].materialization.materialization_id for row in task.external_inputs}
            dependency_receipts = tuple(by_task[key] for key in task.dependency_task_ids)
        except KeyError as error:
            raise PermissionError("custody-only native contact lacks its actual direct successful producer") from error
        try:
            selected = dependency_artifact_inputs(task, dependency_outputs)
        except (TypeError, ValueError) as error:
            raise PermissionError("custody-only native contact changes its exact scientific dependency operands") from error
        materials.update(row.materialization.materialization_id for row in selected)
        expected = NativeEffectContact(index.run_id, task.task_id, contact.attempt_id,
            ObjectIdentity.from_record(plan.execution_plan_id, plan), ObjectIdentity.from_record(task.task_id, task),
            plan.implementation_commit, tuple(sorted(materials)), tuple(sorted(row.receipt_id for row in dependency_receipts)))
        if contact != expected:
            raise PermissionError("custody-only recovery substitutes original source/stream/materialization/receipt contact bindings")
        result.append((task.task_id, contact))
    return tuple(result)


def recover_recursive_custody(*, directory, project_root, artifact_writer, read_access=None):
    """Close only authentic settled initial DEV custody, without task dispatch.

    The original producing source and current committed read-side source are
    authenticated independently. This function creates no task completion,
    retry authority, native work, scratch retirement or scientific score.
    """
    from empirical_lawhood.infrastructure.source_closure import (
        _observe_admitted_target_source_current, capture_admitted_target_source,
    )
    from ..infrastructure.recovery import ExternalRunRecoveryStore, RunRecoveryError, settled_recovery_tasks
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog, SQLiteOperationalRepository
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.runtime.execution import TaskBlockReason, TaskAttemptDisposition
    from empirical_lawhood.api.numerical_provenance import validate_registered_provenance
    packet, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=artifact_writer,
        lazy_payloads=True, require_initial_experiment=True, read_access=read_access)
    if draft.development_study.access_pair != (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY):
        raise PermissionError("custody-only recovery requires ordinary exposed DEV custody; revealed initial studies use their own lifecycle")
    run, plan, index = _retained_plans(payloads, draft)
    if (type(plan) is not DevelopmentExecutionPlan or type(run) is not DevelopmentRunPlan
            or plan.implementation_commit != source.observed_git_head):
        raise PermissionError("custody-only recovery requires the exact initial development plans")
    run_path = artifact_writer.root.resolve("runs/" + run.run_plan_id, for_write=False)
    if not run_path.is_dir():
        raise PermissionError("custody-only recovery refuses unentered initial work")
    before = capture_admitted_target_source(project_root)
    contacts = ExternalNativeEffectContactStore(plane=artifact_writer,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    with contacts.execution_lock(run.run_plan_id):
        provenance = _provenance(plane=artifact_writer, run_id=run.run_plan_id)
        if (provenance.package_sources, provenance.code_sources_sha256, provenance.dependency_lock_sha256,
                provenance.observed_git_head) != (source.package_sources, source.code_sources_sha256,
                    source.dependency_lock_sha256, source.observed_git_head):
            raise PermissionError("custody-only recovery changes original producing provenance")
        registrations, _, _ = operation_catalog()
        validate_registered_provenance(provenance=provenance, draft=draft, registrations=registrations)
        native_keys = {row.selection.capability_key for row in registrations if row.native_effect}
        external = _external_inputs(plane=artifact_writer, plan=plan, draft=draft, payloads=payloads, read_only=True)
        recovery = ExternalRunRecoveryStore(artifact_writer)
        receipt_store = ExternalTaskReceiptStore(artifact_writer)
        original_controls = _custody_control_pins(artifact_writer, index)
        engine = create_catalog_engine("sqlite+pysqlite:///:memory:")
        try:
            upgrade_catalog(engine)
            repository = SQLiteOperationalRepository(engine)
            recovered = recovery.reconcile(index, plan, repository, receipt_store, repair_missing_events=False)
            attempts = repository.attempts(run.run_plan_id)
            completed, closed, unreachable, pending = settled_recovery_tasks(index, attempts)
            if pending:
                raise PermissionError("custody-only recovery refuses eligible or unsettled original tasks: " + ", ".join(pending))
            headers = _custody_contacts(plan=plan, index=index, contacts=contacts, receipts=recovered.recovered_receipts,
                external_inputs=external, attempts=attempts, native_keys=native_keys)
            if _custody_control_pins(artifact_writer, index) != original_controls:
                raise PermissionError("original custody changed during read-side closure admission")
            latest = {row.task_id: row for row in sorted(attempts, key=lambda row: (row.task_id, row.ordinal))}
            for task_id in unreachable:
                if task_id not in latest:
                    repository.block_task(index.run_id, task_id, TaskBlockReason.DEPENDENCY_BLOCKED)
            attempts = repository.attempts(run.run_plan_id)
            latest_after = {row.task_id: row for row in sorted(attempts, key=lambda row: (row.task_id, row.ordinal))}
            status = (OperationalStatus.FAILED if any(row.disposition is TaskAttemptDisposition.FAILED for row in latest_after.values())
                else OperationalStatus.BLOCKED if closed else OperationalStatus.SUCCEEDED)
            _observe_admitted_target_source_current(project_root, before)
            recovery.record_terminal(index, status=status, attempts=attempts, receipts=recovered.recovered_receipts)
            terminal = recovery.read_terminal(index)
            if terminal is None:
                raise RunRecoveryError("settled custody owner did not retain its original operational terminal")
            if _custody_contacts(plan=plan, index=index, contacts=contacts, receipts=recovered.recovered_receipts,
                    external_inputs=external, attempts=attempts, native_keys=native_keys) != headers:
                raise PermissionError("original native contact ancestry changed during read-side closure")
            final_controls = _custody_control_pins(artifact_writer, index)
            allowed = {index.terminal_event_relative_path, *(index.task(task).nonattempt_event_relative_path for task in unreachable)}
            allowed |= {path + ".manifest.json" for path in tuple(allowed)}
            if tuple(row for row in original_controls if row[0] not in allowed) != tuple(
                    row for row in final_controls if row[0] not in allowed):
                raise PermissionError("read-side closure changed original receipts/events outside proved unreachable rows")
        finally:
            engine.dispose()
        after = _observe_admitted_target_source_current(project_root, before)
    return {"run_id": index.run_id, "status": terminal.operational_status, "programme": "INITIAL_DEVELOPMENT_CUSTODY_CLOSURE",
        "operational_terminal": "AUTHENTICATED", "terminal": terminal.to_document(), "task_count": len(index.tasks),
        "completed_task_count": len(completed), "closed_non_success_task_count": len(closed),
        "proved_unreachable_task_ids": unreachable, "execution_plan_sha256": plan.fingerprint(),
        "recovery_index_sha256": index.fingerprint(), "packet_sha256": packet.fingerprint(),
        "observed_producing_git_head": source.observed_git_head,
        "producing_provenance": provenance.identity.to_document(),
        "read_side_source_before": before.to_mapping(), "read_side_source_after": after.to_mapping(),
        "original_control_census_sha256": sha256(canonical_json_bytes(original_controls)).hexdigest(),
        "final_control_census_sha256": sha256(canonical_json_bytes(final_controls)).hexdigest(),
        "original_contact_census_sha256": sha256(canonical_json_bytes(tuple((key, None if value is None else value.fingerprint())
            for key, value in headers))).hexdigest(), "native_contact": "none", "new_native_contact_count": 0,
        "scientific_execution_performed": False, "scientific_completion": "DEFERRED_TO_EXPLICIT_FULL_READ",
        "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}


def validate_recursive_worker_controls(maximum_parallel_tasks, parallel_resource_capacity):
    from ..infrastructure.execution import ExecutionResourceCapacity
    if type(maximum_parallel_tasks) is not int or maximum_parallel_tasks < 1:
        raise ValueError("maximum_parallel_tasks must be a positive integer")
    if parallel_resource_capacity is not None and not isinstance(parallel_resource_capacity, ExecutionResourceCapacity):
        raise TypeError("parallel_resource_capacity must be an ExecutionResourceCapacity")


def _development_runtime_supplier(*, directory, writer, plan, payloads, supplier, output_codecs, read_access=None):
    """Compose a declared API parent binder over the original development plan.

    Protocol discovery remains static. Only the retained exact specification
    can select an installed runtime binding; document values select no imports.
    """
    if "experiment-instance.json" not in payloads:
        if read_access is not None:
            raise ValueError("development access selection requires its original experiment owner")
        return supplier
    from .experiment_preparation import experiment_protocols

    raw = payloads["experiment-specification.json"]
    document = json.loads(raw)
    schema = document.get("schema") if type(document) is dict else None
    protocols = tuple(value for value in experiment_protocols() if
        (value.specification_type.SCHEMA, value.specification_type.VERSION) == (schema, document.get("version")))
    if len(protocols) != 1:
        raise ValueError("retained development specification lacks one installed protocol owner")
    protocol, = protocols
    specification = decode_canonical_bytes(raw, protocol.specification_type, maximum_bytes=len(raw))
    if specification.canonical_bytes() != raw:
        raise ValueError("retained development specification changes its exact canonical bytes")
    binding = experiment_runtime_binding(protocol)
    if protocol.requires_prospective_runtime_binding and (
            binding is None or binding.bind_development_runtime is None):
        raise PermissionError("a prospective runtime composition cannot enter the development lifecycle")
    if binding is None or binding.bind_development_runtime is None:
        if read_access is not None:
            raise ValueError("development access selection requires its declared runtime owner")
        return supplier
    options = {}
    if protocol.requires_prospective_runtime_binding:
        # A dual-route protocol must authenticate its exposed specification in
        # the declared domain binder; prospective inputs remain inadmissible.
        options['specification'] = specification
    if read_access is not None:
        if not callable(binding.validate_development_read_access):
            raise ValueError("selected development runtime does not support an operational access selection")
        options["read_access"] = read_access
    if getattr(payloads, "original_input_access", None) is not None:
        options["payloads"] = payloads
    return binding.bind_development_runtime(supplier=supplier, writer=writer,
        directory=directory, plan=plan, output_codecs=output_codecs, **options)


def run_recursive_wave(*, directory, project_root, artifact_writer, terminal_product_format="documents",
                       maximum_parallel_tasks=1, parallel_resource_capacity=None, require_initial_experiment=False,
                       read_access=None, result_read_scope="FULL"):

    if result_read_scope not in ("FULL", "EXECUTION_RECORDS"):
        raise ValueError("recursive execution requires an explicit full or execution-record result scope")
    if type(require_initial_experiment) is not bool:
        raise TypeError("initial experiment scope requires an explicit boolean")
    _validate_terminal_product_format(terminal_product_format)
    validate_recursive_worker_controls(maximum_parallel_tasks, parallel_resource_capacity)
    from .execution import _StaticInputResolver
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance, validate_registered_provenance
    from ..infrastructure.execution import LocalExecutionResourceAdmitter, LocalProcessExecutor, LocalScheduler
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.infrastructure.run_source_admission import _capture_source, ensure_run_source_entry
    from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
    from ..infrastructure.recovery import ExternalRunRecoveryStore
    from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog, SQLiteOperationalRepository
    from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
    from empirical_lawhood.runtime.execution import ExecutionAssuranceProfile
    from empirical_lawhood.runtime.recursive_compiler import project_recursive_assessments
    from threadpoolctl import threadpool_limits

    admitter = LocalExecutionResourceAdmitter(capacity=parallel_resource_capacity)
    affinity_count = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
    if maximum_parallel_tasks > admitter.capacity.cpu_cores:
        raise ValueError("maximum_parallel_tasks exceeds selected CPU capacity")
    if maximum_parallel_tasks > affinity_count:
        raise ValueError("maximum_parallel_tasks exceeds current process CPU affinity")
    packet, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=artifact_writer,
        lazy_payloads=True, require_initial_experiment=require_initial_experiment, read_access=read_access)
    run, plan, index = _retained_plans(payloads, draft)
    from .experiment_scientific_read import validate_prepared_development_read_access
    validate_prepared_development_read_access(directory=directory, artifact_writer=artifact_writer,
        payloads=payloads, draft=draft, plan=plan, read_access=read_access)
    admitted_source = _capture_source(project_root)
    current = implementation_binding(project_root, _admitted_source=admitted_source)
    from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairRecoveryIndex
    from .development_output_repair import authenticate_repair_controller
    repair = index.repair if isinstance(index, DevelopmentOutputRepairRecoveryIndex) else None
    worker_package_root = (authenticate_repair_controller(index=index, source=source, controller=current)
        if repair is not None else None)
    if repair is None and (current.code_sources_sha256, current.dependency_lock_sha256, current.observed_git_head) != (
        source.code_sources_sha256, source.dependency_lock_sha256, source.observed_git_head):
        raise ValueError("recursive execution source or lock changed after authoring; author a new wave")
    registrations, registry, output_codecs = operation_catalog()
    if registry.fingerprint() != plan.registry_sha256:
        raise ValueError("recursive operation registry changed after the plan froze")
    # A structurally preserved task graph cannot establish its scientific
    # premises. Recheck selected closure before publishing custody or entering
    # workers, including packets authored under an earlier validator.
    project_recursive_assessments(draft=draft, registrations=registrations, outputs={})
    artifact_writer.root.verify(for_write=True, operation_minimum_free_bytes=plan.minimum_free_bytes)
    with threadpool_limits(limits=1):
        require_admitted_target_source_current(project_root, admitted_source)
        observed = (_provenance(plane=artifact_writer, run_id=run.run_plan_id) if repair is not None else
            capture_numerical_provenance(project_root=project_root,
                expected_code_sha256=source.code_sources_sha256, expected_lock_sha256=source.dependency_lock_sha256,
                _admitted_source=admitted_source))
        validate_registered_provenance(provenance=observed, draft=draft, registrations=registrations)
        if repair is None:
            _provenance(plane=artifact_writer, run_id=run.run_plan_id, observed=observed)
        inputs = _external_inputs(plane=artifact_writer, plan=plan, draft=draft, payloads=payloads, read_only=repair is not None)
        input_resolver = _StaticInputResolver(inputs)
        recovery = ExternalRunRecoveryStore(artifact_writer)
        recovery.freeze(index)
        receipts = ExternalTaskReceiptStore(artifact_writer)
        engine = create_catalog_engine("sqlite+pysqlite:///:memory:")
        try:
            upgrade_catalog(engine)
            repository = SQLiteOperationalRepository(engine)
            original_access = getattr(payloads, "original_input_access", None)
            if original_access is not None:
                original_access.require_current()
            recovered = recovery.reconcile(index, plan, repository, receipts)
            if original_access is not None:
                original_access.require_current()
            native_keys = tuple(sorted({value.selection.capability_key for value in registrations if value.native_effect
                                        and any(task.capability.capability_key == value.selection.capability_key for task in plan.tasks)}))
            if native_keys and draft.development_study.access_pair[0] is OutcomeAccess.EVALUATION_REVEALED:
                raise PermissionError("revealed follow-up cannot acquire new native evidence")
            from empirical_lawhood.runtime.native_continuation_execution import native_continuation_scopes
            contact = ExternalNativeEffectContactStore(plane=artifact_writer,
                execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
                visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
                outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                continuation_scopes=native_continuation_scopes(index)) if native_keys else None
            native_task_ids = tuple(task.task_id for task in plan.tasks
                                    if task.capability.capability_key in native_keys)
            prior_contacts = {task_id for task_id in native_task_ids
                              if contact.read(run.run_plan_id, task_id) is not None} if contact else set()
            executor = LocalProcessExecutor(scratch_root=artifact_writer.root, **({} if repair is None else {
                'worker_environment': repair.worker_environment, 'worker_package_root': worker_package_root}))
            diagnostic = artifact_writer.root.diagnostic()
            reservation_plan = plan if repair is None else replace(plan, tasks=tuple(repair.task(task) for task in plan.tasks))
            admission = admitter.assess(reservation_plan,
                available_scratch_bytes=diagnostic.observed_free_bytes,
                executor_enforces_resources=False, executor_enforces_no_network=False,
                assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL)
            if not admission.admitted:
                raise ValueError("recursive resource admission refused: " + ", ".join(admission.reason_codes))
            if {receipt.task_id for receipt in recovered.recovered_receipts} != {task.task_id for task in plan.tasks}:
                ensure_run_source_entry(project_root=project_root, artifact_writer=artifact_writer,
                    run_id=(run.run_plan_id if repair is None else run.run_plan_id + '.' + repair.repair_id + '.controller'),
                    expected_commit=current.observed_git_head,
                    invocation=("programme.run_recursive_wave", run.run_plan_id),
                    source_bindings=(*(() if repair is None else (repair.identity,)), ObjectIdentity.from_record(draft.draft_id, draft),
                        ObjectIdentity.from_record(run.run_plan_id, run),
                        ObjectIdentity.from_record(plan.execution_plan_id, plan)),
                    _admitted_source=admitted_source)
            parent_supplier = _development_runtime_supplier(directory=directory, writer=artifact_writer,
                plan=plan, payloads=payloads, supplier=input_resolver, output_codecs=output_codecs,
                read_access=read_access)
            runners = operation_runners(registry=registry, plan=plan, input_supplier=parent_supplier)
            scheduler = LocalScheduler(operational_repository=repository, artifact_writer=artifact_writer,
                receipt_store=receipts, recovery_index=index, recovery_store=recovery,
                runner_registry=runners, implementation_commit=source.observed_git_head,
                external_input_resolver=input_resolver, executor=executor,
                input_port_factory=artifact_writer, lane=PlanLane.DEVELOPMENT, authorized_barriers=(),
                assurance_profile=ExecutionAssuranceProfile.TRUSTED_LOCAL,
                assurance_codes=tuple(sorted((*admission.assurance_codes, "REGISTERED_REVIEWED_NUMERICAL_WORKERS"))),
                maximum_parallel_tasks=maximum_parallel_tasks,
                parallel_resource_capacity=(admitter.capacity if maximum_parallel_tasks > 1 else None),
                native_effect_contact_store=contact, native_effect_capability_keys=native_keys,
                implementation_binding=source,
                provenance_requirements={value.selection.capability_key: value.provenance_requirements
                    for value in registrations},
                native_work_preparers={value.selection.capability_key: value.native_work_preparer
                    for value in registrations if value.native_work_preparer is not None},
                worker_environment_selectors={value.selection.capability_key: value.worker_environment_selector
                    for value in registrations if value.worker_environment_selector is not None},
                original_input_access_guard=getattr(parent_supplier, "require_original_input_access", None),
                native_entry_guard=getattr(parent_supplier, "require_native_entry", None),
                before_input_member=(None if original_access is None else
                    parent_supplier.custody.member_preflight))
            if repair is not None:
                scheduler.repair_worker_environment = repair.worker_environment
            from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
            with current_issued_task_control_scope(parent_supplier):
                scheduler_result = scheduler.execute(run.run_plan_id, plan)
            current_contacts = {task_id for task_id in native_task_ids
                                if contact.read(run.run_plan_id, task_id) is not None} if contact else set()
            new_contact_count = len(current_contacts - prior_contacts)
        finally:
            engine.dispose()
        require_admitted_target_source_current(project_root, admitted_source)
        final = implementation_binding(project_root, _admitted_source=admitted_source)
        if (final.code_sources_sha256, final.dependency_lock_sha256) != (current.code_sources_sha256, current.dependency_lock_sha256):
            raise ValueError("recursive producing source changed during the execution; preserve its outputs for inspection")
    from empirical_lawhood.kernel.status import OperationalStatus
    if scheduler_result.status is OperationalStatus.SUCCEEDED:
        if set(scheduler_result.completed_task_ids) != {task.task_id for task in plan.tasks}:
            raise ValueError("successful recursive execution lacks its complete assigned task census")
        from .experiment_scientific_read import complete_prepared_development_science
        complete_prepared_development_science(directory=directory, artifact_writer=artifact_writer,
            project_root=project_root, maximum_parallel_tasks=maximum_parallel_tasks,
            payloads=payloads, draft=draft, plan=plan, scheduler_result=scheduler_result, read_access=read_access)
        if result_read_scope == "EXECUTION_RECORDS":
            from .experiment_execution_read import read_development_execution
            report = read_development_execution(directory=directory, artifact_writer=artifact_writer,
                read_access=read_access)
        else:
            report = read_recursive_wave(directory=directory, artifact_writer=artifact_writer,
                                         terminal_product_format=terminal_product_format, read_access=read_access)
    else:
        # Refusal may stop dispatch before every assigned task has an attempt.
        # Authenticate the retained terminal and bytes without producing or
        # claiming the scientific completion that this run did not establish.
        report = read_recursive_wave(directory=directory, artifact_writer=artifact_writer,
            terminal_product_format="compact", allow_partial=True, read_access=read_access)
    # A durable marker records potential effect entry, not a manufactured
    # scientific observation. The adapters retain their actual acquisition census.
    return {**report, "native_contact": "possible" if new_contact_count else "none",
            "new_native_contact_count": new_contact_count}
