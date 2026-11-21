# SPDX-License-Identifier: MPL-2.0
"""Receipt-authenticated, authority-free portable contribution handoffs."""

from contextvars import ContextVar
from collections import OrderedDict
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import replace
import os
from pathlib import Path
from threading import get_ident

from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.recursive_execution import read_recursive_wave
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.storage.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.storage.portable_closure import bounded_custody_members, copy_closure_members, current_closure_budget, require_closure_members
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest, artifact_custody_limits
from empirical_lawhood.execution.recursive_handoff import PortableRecursiveContribution, RecursiveClosureMember

MAX_MEMBER_BYTES = None
_READ_STACK = ContextVar("recursive_contribution_read_stack", default=())
_READ_CONTEXT = ContextVar('recursive_contribution_read_context', default=None)


def _read_policy_key(writer):
    """Select finite structural reuse only for the unchanged stock read policy."""
    from empirical_lawhood.api.recursive_execution import _read_only_custody_policy
    from empirical_lawhood.storage.artifacts import _has_stock_manifest_reads
    verification = getattr(writer, '_read_verification', None)
    # Explicit closure work/depth budgets count the original traversal. Keep
    # that bounded path eager; a reused ancestor must not hide deeper visits.
    if (current_closure_budget() is not None
            or _read_only_custody_policy(writer) is None or not _has_stock_manifest_reads(writer)
            or verification is not None and (verification.context_preflights or verification.manifest_observers)):
        return None
    return (writer.root.contract, id(writer.validators), id(writer.semantic_validations),
        writer.custody_limits, writer.artifact_verification, writer.maximum_parallel_verifications)


class _ContributionReads:
    """One finite ancestry index; each physical copy keeps its own byte guard."""

    def __init__(self, lifetime):
        self.lifetime, self.entries, self.bytes = lifetime, OrderedDict(), 0
        self.active, self.process, self.thread = True, os.getpid(), get_ident()

    def require_current(self):
        if not self.active or (self.process, self.thread) != (os.getpid(), get_ident()):
            raise ValueError('contribution ancestry read escaped its owning invocation')

    def close(self):
        self.active = False
        self.entries.clear()
        self.bytes = 0
        self.lifetime = None

    def get(self, key):
        self.require_current()
        entry = self.entries.get(key)
        if entry is None:
            return None
        result, guard, size, reuse_eligible = entry
        guard()
        if not reuse_eligible():
            # A changed pure scientific read policy needs fresh decoding and
            # validation. It is not evidence of changed physical custody.
            del self.entries[key]
            self.bytes -= size
            return None
        self.entries.move_to_end(key)
        from empirical_lawhood.api.retained_read_metadata import copy_metadata_containers
        return copy_metadata_containers(result, owner_objects=(result[5],))

    def retain(self, key, result, guard, *, roots, reuse_eligible):
        self.require_current()
        from empirical_lawhood.science.records.decoded_record_store import MAX_SHARED_RECORD_BYTES, MAX_SHARED_RECORDS
        from empirical_lawhood.api.retained_read_metadata import copy_metadata_containers, retained_metadata_bytes
        if key is None:
            return
        # Physical payload size is not retained memory: a multi-GiB copied
        # trajectory can have a small immutable control graph. Include actual
        # report/product containers, typed roots and cached canonical buffers.
        # Custody scopes are separately owned until their complete final guard.
        size = retained_metadata_bytes((result, roots), maximum_bytes=MAX_SHARED_RECORD_BYTES,
            owner_objects=(result[5],))
        if size is None:
            return
        try:
            retained = copy_metadata_containers(result, owner_objects=(result[5],))
        except (TypeError, RecursionError):
            return
        # Snapshot containers may have a different allocation capacity. Charge
        # the graph actually retained, not the source projection's allocation.
        size = retained_metadata_bytes((retained, roots), maximum_bytes=MAX_SHARED_RECORD_BYTES,
            owner_objects=(result[5],))
        if size is None:
            return
        # Replacing one physical key must release its previous accounting.
        old = self.entries.pop(key, None)
        if old is not None:
            self.bytes -= old[2]
        while self.entries and (len(self.entries) >= MAX_SHARED_RECORDS
                or self.bytes + size > MAX_SHARED_RECORD_BYTES):
            _, (_, _, removed, _) = self.entries.popitem(last=False)
            self.bytes -= removed
        self.entries[key] = retained, guard, size, reuse_eligible
        self.bytes += size


def _current_contribution_reads():
    current = _READ_CONTEXT.get()
    return current if (current is not None and current.active
        and (current.process, current.thread) == (os.getpid(), get_ident())) else None


@contextmanager
def recursive_contribution_read_context():
    """Own ancestry reconstruction inside one API read, never between calls.

    Exact typed records share the existing finite decoding scope. Different
    custody locations still authenticate their own complete bytes and access.
    """
    current = _current_contribution_reads()
    if current is not None:
        yield current
        return
    from empirical_lawhood.science.records.decoded_record_store import decoded_record_scope
    with decoded_record_scope():
        current = _ContributionReads(ExitStack())
        token = _READ_CONTEXT.set(current)
        stack_token = _READ_STACK.set(())
        try:
            # Final guards run with their owner still live, including on an
            # exception. A copied context cannot append guards after closure.
            with current.lifetime:
                yield current
        finally:
            current.close()
            _READ_STACK.reset(stack_token)
            _READ_CONTEXT.reset(token)


def _callbacks(draft, products, name):
    from empirical_lawhood.api.recursive_operations import selected_operation_factories
    selected = {operation.selection.selection_id for operation in draft.operations
                if operation.node_id in products["records"]}
    values = {}
    for factory in selected_operation_factories(selected):
        callback = getattr(factory, name)
        if factory.registration.selection.selection_id in selected and callback is not None:
            values.setdefault(callback, None)
    return tuple(values)


def _described(draft, products):
    manifests = tuple(manifest for callback in _callbacks(draft, products, "contribution_describer")
                      for manifest in callback(draft, products))
    if len(manifests) != 1 or not isinstance(manifests[0], ContributionManifest):
        raise ValueError("selected wave has no unique registered contribution description")
    return manifests[0]


def _selected_directory(directory, writer):
    path = Path(directory)
    if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("portable contribution refuses links and traversal")
    path = path.resolve(strict=True)
    root = Path(writer.root.contract.canonical_path)
    if not path.is_relative_to(root):
        raise ValueError("portable contribution lies outside the explicitly selected guarded root")
    writer.root.verify(for_write=False)
    return path


def _custody_members(root, prefixes):
    budget = current_closure_budget()
    if budget is not None:
        return bounded_custody_members(root, prefixes, limits=budget.limits)
    members = {}
    for prefix in prefixes:
        base = root / prefix
        if not base.is_dir() or base.is_symlink():
            raise ValueError("portable contribution omits its original custody directory")
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                raise ValueError("portable custody cannot include symbolic links")
            if not path.is_file():
                continue
            # File-system locks carry no scientific identity or publication authority.
            if path.name.endswith(".lock"):
                continue
            size, digest = bounded_file_sha256(path, maximum_bytes=MAX_MEMBER_BYTES)
            member = RecursiveClosureMember(path.relative_to(root).as_posix(), size, digest)
            previous = members.setdefault(member.relative_path, member)
            if previous != member:
                raise ValueError("shared custody member changed between parent closures")
    return tuple(members[name] for name in sorted(members))


def _publish(writer, directory, name, record, packet_id):
    root = Path(writer.root.contract.canonical_path)
    relative = directory.relative_to(root).as_posix()
    writer.write(ArtifactWriteRequest(packet_id + "." + name.removesuffix(".json"), relative + "/" + name,
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", packet_id,
        relative, record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))


def export_recursive_contribution(*, directory, output_dir, project_root, artifact_writer):
    from empirical_lawhood.api.recursive_execution import _read_only_custody_policy

    source = _selected_directory(directory, artifact_writer)
    # Compose the two read consumers in one effect-free lifetime. Publication
    # and copying below still use the ordinary writer after its final guard.
    stock = (type(artifact_writer) is ExternalArtifactPlane
        and _read_only_custody_policy(artifact_writer) is not None)
    scope = artifact_writer.read_context() if stock else nullcontext(artifact_writer)
    with scope as reading:
        report, products, draft, _ = read_recursive_wave(directory=source, artifact_writer=reading, include_products=True)
        manifest = _described(draft, products)
        parent_paths = ()
        if draft.contribution_parents:
            from empirical_lawhood.api.recursive_authoring import load_authored_wave
            from empirical_lawhood.execution.recursive_handoff import recursive_parent_closure_bindings
            _, _, _, payloads = load_authored_wave(directory=source, artifact_writer=reading, lazy_payloads=True)
            parent_paths = tuple(sorted(binding.relative_path for binding in recursive_parent_closure_bindings(payloads)))
    destination = preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root),
                                                       artifact_writer=artifact_writer)
    root = Path(artifact_writer.root.contract.canonical_path)
    prefixes = (source.relative_to(root).as_posix(), report["retained_directory"], *parent_paths)
    members = _custody_members(root, prefixes)
    transport = PortableRecursiveContribution("portable." + manifest.fingerprint()[:24],
        artifact_writer.root.contract.storage_root_id, prefixes[0], prefixes[1],
        ObjectIdentity.from_record(manifest.contribution_id, manifest), members, parent_paths)
    destination.mkdir(parents=True)
    copy_closure_members(members=members, source_guard=artifact_writer.root, destination_guard=artifact_writer.root,
        destination_prefix=(destination / "custody").relative_to(root).as_posix())
    if _custody_members(root, prefixes) != members:
        raise ValueError("source custody changed during portable export; retain the incomplete packet")
    _publish(artifact_writer, destination, "contribution.json", manifest, transport.transport_id)
    _publish(artifact_writer, destination, "transport.json", transport, transport.transport_id)
    next_waves = tuple(value for callback in _callbacks(draft, products, "next_wave_builder")
                       if (value := callback(draft, manifest, products)) is not None)
    if len(next_waves) > 1:
        raise ValueError("selected contribution has ambiguous registered successor authoring")
    if next_waves:
        from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
        if not isinstance(next_waves[0], RecursiveStudyDraft):
            raise TypeError("registered successor authoring must return a typed scientific draft")
        _publish(artifact_writer, destination, "next-wave.json", next_waves[0], transport.transport_id)
    return {"status": "EXPORTED", "contribution_dir": str(destination), "contribution_sha256": manifest.fingerprint(),
            "transport_sha256": transport.fingerprint(), "custody_member_count": len(members),
            "native_contact": "none", "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}


def authenticate_recursive_contribution(*, directory, artifact_writer, include_draft=False):
    """Bind copied immutable custody to a new guarded root without rewriting it."""
    if type(include_draft) is not bool:
        raise TypeError("contribution draft selection requires an explicit boolean")
    selected = _selected_directory(directory, artifact_writer)
    with recursive_contribution_read_context() as reading:
        stack = _READ_STACK.get()
        if selected in stack:
            raise ValueError("portable contribution parent closure cycles")
        budget = current_closure_budget()
        if budget is not None:
            budget.authenticate(len(stack) + 1)
        token = _READ_STACK.set((*stack, selected))
        try:
            policy = _read_policy_key(artifact_writer)
            key = None if policy is None else (selected, policy)
            result = None if key is None else reading.get(key)
            if result is None:
                result = _authenticate_selected(selected, artifact_writer, include_draft=True)
            return result if include_draft else result[:6]
        finally:
            _READ_STACK.reset(token)


def authenticate_recursive_parents(*, draft, artifact_writer, directory=None, directories=None, payloads=None):
    """Authenticate the whole exact direct-parent set, including every copied byte."""
    from empirical_lawhood.execution.recursive_handoff import recursive_parent_closure_bindings

    if sum(value is not None for value in (directory, directories, payloads)) > 1:
        raise ValueError("select exactly one portable parent directory interface")
    bindings = None
    if payloads is not None:
        bindings = recursive_parent_closure_bindings(payloads)
        selected_directories = tuple(artifact_writer.root.resolve(value.relative_path, for_write=False)
                                     for value in bindings)
    elif directories is not None:
        if not isinstance(directories, tuple) or not directories:
            raise ValueError("portable parents require a nonempty explicit directory tuple")
        selected_directories = directories
    else:
        selected_directories = () if directory is None else (directory,)
    if len(selected_directories) != len(draft.contribution_parents):
        raise ValueError("selected contribution parents require their complete authenticated portable receipt closure")
    authenticated = tuple(authenticate_recursive_contribution(directory=value, artifact_writer=artifact_writer)
                          for value in selected_directories)
    if len({value[0] for value in authenticated}) != len(authenticated):
        raise ValueError("portable parents repeat a selected directory")
    if bindings is not None:
        for binding, (_, transport, manifest, _, _, _) in zip(bindings, authenticated, strict=True):
            if (ObjectIdentity.from_record(transport.transport_id, transport) != binding.transport
                    or ObjectIdentity.from_record(manifest.contribution_id, manifest) != binding.contribution):
                raise ValueError("wave changes its authenticated portable parent closure identities")
    authenticated = tuple(sorted(authenticated, key=lambda value: value[2].contribution_id))
    if tuple(value[2] for value in authenticated) != draft.contribution_parents:
        raise ValueError("draft changes its exact authenticated contribution parents or scientific scopes")
    return authenticated


def _authenticate_selected(selected, artifact_writer, *, include_draft=False):
    # Transport is an explicit locator declaration. Its authenticity comes from the
    # actual producing receipts and canonical manifest independently checked below.
    budget = current_closure_budget()
    bound = None if budget is None else budget.limits.maximum_control_bytes
    from empirical_lawhood.science.records.decoded_record_store import decode_scoped_canonical_bytes
    transport = decode_scoped_canonical_bytes(read_bounded_bytes(selected / "transport.json", maximum_bytes=bound),
                                      PortableRecursiveContribution, maximum_bytes=bound)
    manifest = decode_scoped_canonical_bytes(read_bounded_bytes(selected / "contribution.json", maximum_bytes=bound),
                                     ContributionManifest, maximum_bytes=bound)
    if budget is not None:
        require_closure_members(transport.members, budget.limits)
    if ObjectIdentity.from_record(manifest.contribution_id, manifest) != transport.contribution:
        raise ValueError("portable contribution changes its canonical scientific identity")
    custody = selected / "custody"
    contract = replace(artifact_writer.root.contract, storage_root_id=transport.original_storage_root_id,
                       canonical_path=str(custody))
    view = ExternalArtifactPlane(GuardedExternalRoot(contract, inspector=artifact_writer.root.inspector), artifact_writer.validators, artifact_writer.semantic_validations, custody_limits=artifact_custody_limits(artifact_writer), artifact_verification=artifact_writer.artifact_verification)
    view.root.verify(for_write=False)
    prefixes = (transport.authoring_relative_path, transport.run_relative_path, *transport.parent_closure_relative_paths)
    if _custody_members(custody, prefixes) != transport.members:
        raise ValueError("portable handoff is missing, adding or substituting original custody bytes")
    current = _current_contribution_reads()
    policy = _read_policy_key(artifact_writer)
    # Custom policies retain the independent original reader and checks.
    if current is None or policy is None:
        report, products, draft, _ = read_recursive_wave(directory=custody / transport.authoring_relative_path,
                                                       artifact_writer=view, include_products=True)
        from empirical_lawhood.api.recursive_operations import inquiry_selection_scope
        with inquiry_selection_scope(draft):
            if _described(draft, products) != manifest:
                raise ValueError("portable contribution does not follow from its exact actual producing receipts and scientific products")
        result = selected, transport, manifest, report, products, view
        return (*result, draft) if include_draft else result
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
    from empirical_lawhood.api.recursive_operations import inquiry_selection_scope
    reading = current.lifetime.enter_context(view.read_context())
    accesses = []
    def preflight(**roots):
        from empirical_lawhood.execution.recursive_handoff import recursive_parent_closure_bindings
        bindings = recursive_parent_closure_bindings(roots['payloads'])
        if (tuple(sorted(binding.relative_path for binding in bindings)) != transport.parent_closure_relative_paths
                or tuple(ObjectIdentity.from_record(parent.contribution_id, parent)
                    for parent in roots['draft'].contribution_parents) != manifest.predecessors):
            raise ValueError('portable contribution changes its complete original predecessor membership')
        current.lifetime.enter_context(inquiry_selection_scope(roots['draft']))
        access = getattr(roots['payloads'], 'original_input_access', None)
        if access is not None:
            accesses.append(access)
    def require_current():
        if _read_policy_key(artifact_writer) != policy:
            raise ValueError('portable contribution changes its original read policy')
        _selected_directory(selected, artifact_writer)
        for name, record in (('transport.json', transport), ('contribution.json', manifest)):
            if bounded_file_sha256(selected / name, maximum_bytes=bound) != (record.canonical_size_bytes(), record.fingerprint()):
                raise ValueError('portable contribution changed during its finite read')
        for access in accesses:
            access.require_current(artifact_writer=reading)
        reading.require_verification_snapshot()
    def complete():
        require_current()
        if _custody_members(custody, prefixes) != transport.members:
            raise ValueError('portable contribution closure changed during its finite read')
    current.lifetime.callback(complete)
    result, roots = _read_recursive_wave_with_retained_roots(
        directory=custody / transport.authoring_relative_path, artifact_writer=reading,
        include_products=True, _validate_authored=preflight)
    report, products, draft, _ = result
    if _described(draft, products) != manifest:
        raise ValueError("portable contribution does not follow from its exact actual producing receipts and scientific products")
    require_current()
    result = selected, transport, manifest, report, products, view
    # The physical custody policy alone does not identify scientific decoders,
    # registered callbacks or numerical settings. Bind reuse to the same stock
    # immutable-root policy used by authored inquiry projections.
    from types import SimpleNamespace
    from empirical_lawhood.api.recursive_inquiry_read import _authored_reuse_key
    retained_roots = SimpleNamespace(packet=roots[0], draft=roots[1], implementation=roots[2],
        run=roots[3], plan=roots[4])
    reuse_policy = _authored_reuse_key(retained_roots)
    # Keep immutable roots alive for the existing weak typed-record index.
    # No reader, permission verdict or stale payload map is a reusable token.
    def guard(_roots=roots):
        require_current()
    def reuse_eligible():
        return _authored_reuse_key(retained_roots) == reuse_policy
    if reuse_policy is not None:
        current.retain((selected, policy), (*result, draft), guard, roots=(roots, reuse_policy),
            reuse_eligible=reuse_eligible)
    return (*result, draft) if include_draft else result


def inspect_recursive_contribution(*, directory, artifact_writer):
    selected, transport, manifest, report, _, _ = authenticate_recursive_contribution(directory=directory, artifact_writer=artifact_writer)
    return {"status": "AUTHENTICATED", "contribution_dir": str(selected), "contribution": manifest.to_document(),
            "transport_sha256": transport.fingerprint(), "producing_run_id": report["run_id"],
            "native_contact": "none", "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}


def _authenticated_parent_output_ownership(*, transport, products, view, ancestors=()):
    """Complete producing output census, including unexported and ancestral products."""
    identity = transport.fingerprint()
    if identity in ancestors:
        raise ValueError("parent output ownership closure cycles")
    outputs = list(products["outputs"].values())
    digests = {value.logical.content_sha256 for value in outputs}
    artifact_ids = {value.logical.logical_artifact_id for value in outputs}
    for receipt in products["attempt_receipts"].values():
        digests.update(value.content_sha256 for value in receipt.output_logical_artifacts)
        artifact_ids.update(value.logical_artifact_id for value in receipt.output_logical_artifacts)
    for path in transport.parent_closure_relative_paths:
        _, parent_transport, _, _, parent_products, parent_view = authenticate_recursive_contribution(
            directory=view.root.resolve(path, for_write=False), artifact_writer=view)
        parent_digests, parent_ids = _authenticated_parent_output_ownership(
            transport=parent_transport, products=parent_products, view=parent_view, ancestors=(*ancestors, identity))
        digests.update(parent_digests)
        artifact_ids.update(parent_ids)
    return digests, artifact_ids


def contribution_input_bindings(*, directory=None, directories=None, draft, artifact_writer, origins=None):
    authenticated = authenticate_recursive_parents(draft=draft, artifact_writer=artifact_writer,
                                                  directory=directory, directories=directories)
    return _contribution_input_bindings(authenticated=authenticated, draft=draft, origins=origins)


def _contribution_input_bindings(*, authenticated, draft, origins):
    from empirical_lawhood.api.recursive_read_indexes import ReceiptProductIndex, unique_index

    if len(authenticated) > 1 and origins is None:
        raise ValueError("multiple portable parents require explicit exact input origins")
    if origins is not None:
        from empirical_lawhood.design.recursive_input_origins import RecursiveInputOriginKind
        origins.validate_draft(draft)
        parent_digests, parent_artifact_ids = set(), set()
        owners = {}
        for _, transport, manifest, _, products, view in authenticated:
            digests, artifact_ids = _authenticated_parent_output_ownership(
                transport=transport, products=products, view=view)
            parent_digests.update(digests)
            parent_artifact_ids.update(artifact_ids)
            product_by_id = unique_index(manifest.products, lambda product: product.product_id,
                label='contribution product')
            owner = ObjectIdentity.from_record(manifest.contribution_id, manifest)
            if owner in owners:
                raise ValueError('contribution origins repeat an exact parent owner')
            owners[owner] = (product_by_id, ReceiptProductIndex(products), view)
        externals = {value.input_id: value for value in draft.external_inputs}
        bindings = []
        for origin in origins.inputs:
            if origin.kind is RecursiveInputOriginKind.SOURCE:
                if (origin.expected_content_sha256 in parent_digests
                    or externals[origin.input_id].logical_artifact_id in parent_artifact_ids):
                    raise ValueError("source origin disguises an authenticated parent-produced output")
                continue
            product_by_id, indexed, view = owners[origin.parent]
            product = product_by_id[origin.product_id]
            matches = indexed.matches(product.producing_receipt, product.artifact)
            if len(matches) != 1:
                raise ValueError("contribution origin lacks its exact authenticated producing receipt product")
            bindings.append((origin.input_id, view.root.resolve(matches[0].materialization.relative_path, for_write=False)))
        return tuple(bindings)
    if not authenticated:
        return ()
    selected, _, manifest, _, products, view = authenticated[0]
    paths = {manifest.fingerprint(): selected / "contribution.json"}
    indexed = ReceiptProductIndex(products)
    for values in products["records"].values():
        for record in values.values():
            candidates = indexed.by_content.get(record.fingerprint(), ())
            if len(candidates) == 1:
                paths[record.fingerprint()] = view.root.resolve(candidates[0].materialization.relative_path, for_write=False)
    selected_external_ids = {link.external_input_id for link in draft.links
                             if link.consumer_node_id in draft.selected_operation_ids and link.external_input_id is not None}
    bindings = []
    for value in draft.external_inputs:
        if value.input_id not in selected_external_ids:
            continue
        path = paths.get(value.expected_content_sha256)
        if path is None:
            raise ValueError("selected contribution input is absent from the authenticated actual product census")
        bindings.append((value.input_id, path))
    return tuple(bindings)
