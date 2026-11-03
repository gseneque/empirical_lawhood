# SPDX-License-Identifier: MPL-2.0
"""Receipt-authenticated, authority-free portable contribution handoffs."""

from contextvars import ContextVar
from dataclasses import replace
from pathlib import Path

from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.recursive_execution import read_recursive_wave
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, copy_bounded_file, read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, artifact_custody_limits
from empirical_lawhood.runtime.recursive_handoff import PortableRecursiveContribution, RecursiveClosureMember

MAX_MEMBER_BYTES = None
_READ_STACK = ContextVar("recursive_contribution_read_stack", default=())


def _callbacks(draft, products, name):
    from empirical_lawhood.api.recursive_operations import operation_factories
    selected = {operation.selection.selection_id for operation in draft.operations
                if operation.node_id in products["records"]}
    values = {}
    for factory in operation_factories():
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
    source = _selected_directory(directory, artifact_writer)
    report, products, draft, _ = read_recursive_wave(directory=source, artifact_writer=artifact_writer, include_products=True)
    manifest = _described(draft, products)
    destination = preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root),
                                                       artifact_writer=artifact_writer)
    root = Path(artifact_writer.root.contract.canonical_path)
    parent_paths = ()
    if draft.contribution_parents:
        from empirical_lawhood.api.recursive_authoring import load_authored_wave
        from empirical_lawhood.runtime.recursive_handoff import recursive_parent_closure_bindings
        _, _, _, payloads = load_authored_wave(directory=source, artifact_writer=artifact_writer, lazy_payloads=True)
        parent_paths = tuple(sorted(binding.relative_path for binding in recursive_parent_closure_bindings(payloads)))
    prefixes = (source.relative_to(root).as_posix(), report["retained_directory"], *parent_paths)
    members = _custody_members(root, prefixes)
    transport = PortableRecursiveContribution("portable." + manifest.fingerprint()[:24],
        artifact_writer.root.contract.storage_root_id, prefixes[0], prefixes[1],
        ObjectIdentity.from_record(manifest.contribution_id, manifest), members, parent_paths)
    destination.mkdir(parents=True)
    for member in members:
        selected = artifact_writer.root.resolve(member.relative_path, for_write=False)
        target = artifact_writer.root.resolve((destination / "custody" / member.relative_path).relative_to(root).as_posix(), for_write=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        copied = copy_bounded_file(selected, target, maximum_bytes=member.size_bytes)
        if copied != (member.size_bytes, member.sha256):
            raise ValueError("source custody changed while exporting the portable handoff")
    if _custody_members(root, prefixes) != members:
        raise ValueError("source custody changed during portable export; retain the incomplete packet")
    _publish(artifact_writer, destination, "contribution.json", manifest, transport.transport_id)
    _publish(artifact_writer, destination, "transport.json", transport, transport.transport_id)
    next_waves = tuple(value for callback in _callbacks(draft, products, "next_wave_builder")
                       if (value := callback(draft, manifest, products)) is not None)
    if len(next_waves) > 1:
        raise ValueError("selected contribution has ambiguous registered successor authoring")
    if next_waves:
        from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
        if not isinstance(next_waves[0], RecursiveStudyDraft):
            raise TypeError("registered successor authoring must return a typed scientific draft")
        _publish(artifact_writer, destination, "next-wave.json", next_waves[0], transport.transport_id)
    return {"status": "EXPORTED", "contribution_dir": str(destination), "contribution_sha256": manifest.fingerprint(),
            "transport_sha256": transport.fingerprint(), "custody_member_count": len(members),
            "native_contact": "none", "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}


def authenticate_recursive_contribution(*, directory, artifact_writer):
    """Bind copied immutable custody to a new guarded root without rewriting it."""
    selected = _selected_directory(directory, artifact_writer)
    stack = _READ_STACK.get()
    if selected in stack:
        raise ValueError("portable contribution parent closure cycles")
    token = _READ_STACK.set((*stack, selected))
    try:
        return _authenticate_selected(selected, artifact_writer)
    finally:
        _READ_STACK.reset(token)


def authenticate_recursive_parents(*, draft, artifact_writer, directory=None, directories=None, payloads=None):
    """Authenticate the whole exact direct-parent set, including every copied byte."""
    from empirical_lawhood.runtime.recursive_handoff import recursive_parent_closure_bindings

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


def _authenticate_selected(selected, artifact_writer):
    # Transport is an explicit locator declaration. Its authenticity comes from the
    # actual producing receipts and canonical manifest independently checked below.
    transport = decode_canonical_bytes(read_bounded_bytes(selected / "transport.json", maximum_bytes=None),
                                      PortableRecursiveContribution, maximum_bytes=None)
    manifest = decode_canonical_bytes(read_bounded_bytes(selected / "contribution.json", maximum_bytes=None),
                                     ContributionManifest, maximum_bytes=None)
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
    report, products, draft, _ = read_recursive_wave(directory=custody / transport.authoring_relative_path,
                                                   artifact_writer=view, include_products=True)
    if _described(draft, products) != manifest:
        raise ValueError("portable contribution does not follow from its exact actual producing receipts and scientific products")
    return selected, transport, manifest, report, products, view


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
    if len(authenticated) > 1 and origins is None:
        raise ValueError("multiple portable parents require explicit exact input origins")
    if origins is not None:
        from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOriginKind
        origins.validate_draft(draft)
        parent_digests, parent_artifact_ids = set(), set()
        owners = {}
        for _, transport, manifest, _, products, view in authenticated:
            digests, artifact_ids = _authenticated_parent_output_ownership(
                transport=transport, products=products, view=view)
            parent_digests.update(digests)
            parent_artifact_ids.update(artifact_ids)
            owners[ObjectIdentity.from_record(manifest.contribution_id, manifest)] = (manifest, products, view)
        externals = {value.input_id: value for value in draft.external_inputs}
        bindings = []
        for origin in origins.inputs:
            if origin.kind is RecursiveInputOriginKind.SOURCE:
                if (origin.expected_content_sha256 in parent_digests
                    or externals[origin.input_id].logical_artifact_id in parent_artifact_ids):
                    raise ValueError("source origin disguises an authenticated parent-produced output")
                continue
            manifest, products, view = owners[origin.parent]
            product = next(value for value in manifest.products if value.product_id == origin.product_id)
            matches = []
            for task_id, receipt in products["receipts"].items():
                if ObjectIdentity.from_record(receipt.receipt_id, receipt) != product.producing_receipt:
                    continue
                for logical in receipt.output_logical_artifacts:
                    if (logical.logical_artifact_id == product.artifact.artifact_id
                        and logical.content_sha256 == product.artifact.sha256
                        and logical.payload_schema == product.artifact.payload_schema):
                        matches.append(products["outputs"][logical.logical_artifact_id])
            if len(matches) != 1:
                raise ValueError("contribution origin lacks its exact authenticated producing receipt product")
            bindings.append((origin.input_id, view.root.resolve(matches[0].materialization.relative_path, for_write=False)))
        return tuple(bindings)
    if not authenticated:
        return ()
    selected, _, manifest, _, products, view = authenticated[0]
    paths = {manifest.fingerprint(): selected / "contribution.json"}
    for values in products["records"].values():
        for record in values.values():
            candidates = [value for value in products["outputs"].values() if value.logical.content_sha256 == record.fingerprint()]
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
