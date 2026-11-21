# SPDX-License-Identifier: MPL-2.0
"""Bounded local exchange over existing custody, replica and catalogue owners."""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from functools import wraps
from hashlib import sha256
import json
import os
from pathlib import Path

from empirical_lawhood.storage.artifact_replication import ReplicaFile, replicate_artifact_publications
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.file_locks import exclusive_file_lock
from empirical_lawhood.storage.guarded_catalog import GuardedCatalogAccess
from empirical_lawhood.storage.portable_closure import bounded_custody_members, copy_closure_members, recursive_closure_limits, require_closure_members
from empirical_lawhood.storage.sql.repository import SQLiteCatalogRepository
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.storage.contracts.catalog import ArtifactLocatorRecord, CatalogArtifactQuery, CatalogSnapshot, CatalogVerificationStatus, LogicalArtifactRecord, StorageRootRecord
from empirical_lawhood.storage.contracts.knowledge_store import KnowledgeDependencyLocation, KnowledgeImportReceipt, KnowledgeObjectLocator, KnowledgeStoreHeader, KnowledgeStoreLimits, KnowledgeTransferManifest, KnowledgeVerificationContext, PortableKnowledgeObject, ScientificTypeRegistry, dependency_order, object_key
from empirical_lawhood.storage.contracts.record_codecs import record_envelope_key

from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.recursive_contributions import _publish, _selected_directory


TRANSFER_PATH = "control/transfer.json"


def _bounded_store_operation(method):
    @wraps(method)
    def selected(self, *args, **kwargs):
        with recursive_closure_limits(self.limits.closure):
            return method(self, *args, **kwargs)
    return selected


@dataclass(frozen=True, slots=True)
class KnowledgeObjectSource:
    """An explicit original location, never an inferred scientific identity."""
    identity: ObjectIdentity
    directory: Path
    origin_namespace: str
    publisher_label: str
    record_filename: str


def _require_access(callback, identities, action):
    if not callable(callback):
        raise TypeError("knowledge operations require their current code-owned access guard")
    for identity in identities:
        if callback(identity, action) is not None:
            raise TypeError("knowledge access guard must refuse by exception or return None")


def _read_record(path, kind, bound):
    return decode_canonical_bytes(read_bounded_bytes(path, maximum_bytes=bound), kind, maximum_bytes=bound)


def _published_record(plane, path, kind, bound):
    relative = path.relative_to(Path(plane.root.contract.canonical_path)).as_posix()
    manifest = plane.read_manifest(relative, maximum_bytes=bound)
    plane.verify_manifest(manifest)
    record = _read_record(plane.root.resolve(relative, for_write=False), kind, bound)
    if (manifest.materialization.relative_path != relative or manifest.logical.payload_schema != kind.SCHEMA
            or manifest.logical.content_sha256 != record.fingerprint()
            or manifest.materialization.physical_sha256 != record.fingerprint()):
        raise ValueError("knowledge control differs from its exact published custody")
    if plane.read_manifest(relative, maximum_bytes=bound) != manifest:
        raise ValueError("knowledge publication changed during current read")
    return record, manifest


def _packet_plane(plane, directory, manifest):
    # Only the outer transport publication receives this operational namespace.
    # All embedded scientific bytes retain their original namespaces and paths.
    contract = replace(plane.root.contract, canonical_path=str(directory),
        storage_root_id="knowledge-transfer." + manifest.fingerprint())
    return ExternalArtifactPlane(GuardedExternalRoot(contract, inspector=plane.root.inspector),
        validators=plane.validators, semantic_validations=plane.semantic_validations,
        custody_limits=plane.custody_limits, artifact_verification=plane.artifact_verification)


def _load_transfer(directory, plane, limits, expected=None):
    selected = _selected_directory(directory, plane)
    manifest = _read_record(selected / TRANSFER_PATH, KnowledgeTransferManifest, limits.closure.maximum_control_bytes)
    if expected is not None and manifest.identity != expected:
        raise ValueError("knowledge transfer substitutes its selected complete identity")
    require_closure_members(manifest.members, limits.closure)
    dependency_order(manifest.objects, manifest.roots, limits)
    packet = _packet_plane(plane, selected, manifest)
    current, publication = _published_record(packet, selected / TRANSFER_PATH,
        KnowledgeTransferManifest, limits.closure.maximum_control_bytes)
    if current != manifest or publication.publication is None:
        raise ValueError("knowledge transfer lacks its original committed publication")
    return manifest, packet, publication


def _decode_object(row, directory, registry, limits):
    payload = read_bounded_bytes(directory / row.record_filename, maximum_bytes=limits.closure.maximum_control_bytes)
    if sha256(payload).hexdigest() != row.identity.object_fingerprint:
        raise ValueError("knowledge object changes its complete content identity")
    schema, version = record_envelope_key(payload, expected_schema=row.identity.object_schema)
    if version != row.identity.object_version:
        raise ValueError("knowledge object substitutes its exact record revision")
    descriptor = registry.descriptor(row.identity)
    if descriptor is None:
        return None, None
    if row.record_filename != descriptor.record_filename:
        raise ValueError("knowledge object changes its registered original record filename")
    record = decode_canonical_bytes(payload, registry.codecs.resolve(schema, version),
                                    maximum_bytes=limits.closure.maximum_control_bytes)
    if descriptor.identity(record) != row.identity:
        raise ValueError("knowledge object changes its original scientific ID")
    return descriptor, record


def _describe_source(source, plane, registry, limits, require_access):
    _require_access(require_access, (source.identity,), "EXPORT")
    directory = _selected_directory(source.directory, plane)
    row = PortableKnowledgeObject(source.identity, source.origin_namespace, source.publisher_label,
        source.record_filename, (), "OPAQUE_UNINTERPRETED")
    descriptor, record = _decode_object(row, directory, registry, limits)
    if descriptor is not None:
        dependencies = descriptor.dependencies(record)
        row = replace(row, dependencies=dependencies, dependency_description="REGISTERED_COMPLETE")
    return row, directory


def _verify_objects(objects, roots, directories, artifact_writer, registry, limits, require_access):
    reports = {}
    for row in dependency_order(objects, roots, limits):
        _require_access(require_access, (row.identity,), "READ")
        selected = directories[row.identity]
        descriptor, record = _decode_object(row, selected, registry, limits)
        if descriptor is None:
            report = {"interpretation": "OPAQUE_UNINTERPRETED", "scientific_assessment": "NOT_INTERPRETED",
                "dependency_completeness": "NOT_ESTABLISHED_BY_INSTALLED_READER"}
        else:
            if descriptor.dependencies(record) != row.dependencies:
                raise ValueError("knowledge object changes its registered complete dependency census")
            dependencies = tuple(KnowledgeDependencyLocation(value, directories[value])
                                 for value in row.dependencies)
            context = KnowledgeVerificationContext(selected, artifact_writer, row.identity, record, dependencies)
            verification = None if descriptor.verify is None else descriptor.verify(context)
            if verification is not None and type(verification) is not dict:
                raise TypeError("registered knowledge verifier returned another report contract")
            report = {"interpretation": "EXACT_REGISTERED_RECORD", "descriptor": descriptor.descriptor_id,
                "scientific_assessment": "NOT_ASSESSED" if verification is None else "REGISTERED_VERIFIER_REPLAYED",
                "verification": verification}
        reports[object_key(row.identity)] = {"identity": row.identity.to_document(), **report,
            "consumer_admission": "NOT_EVALUATED", "current_execution_authority": "NONE"}
        _require_access(require_access, (row.identity,), "READ")
    return reports


def _verify_transfer(*, directory, artifact_writer, registry, limits, require_access, expected=None):
    manifest, packet, publication = _load_transfer(directory, artifact_writer, limits, expected)
    identities = tuple(row.identity for row in manifest.objects)
    _require_access(require_access, identities, "READ")
    root = Path(packet.root.contract.canonical_path)
    before = bounded_custody_members(root, ("",), limits=limits.closure)
    objects = tuple(value for value in before if value.relative_path.startswith("objects/"))
    allowed_controls = {TRANSFER_PATH, TRANSFER_PATH + ".manifest.json",
                        publication.publication.commit_marker_relative_path}
    if objects != manifest.members or any(value.relative_path not in allowed_controls
            and not value.relative_path.startswith("objects/") for value in before):
        raise ValueError("knowledge transfer omits, substitutes or adds unassigned closure bytes")
    reports = _verify_objects(manifest.objects, manifest.roots,
        {row.identity: root / row.relative_directory for row in manifest.objects},
        packet, registry, limits, require_access)
    if bounded_custody_members(root, ("",), limits=limits.closure) != before:
        raise ValueError("knowledge closure changed during current verification")
    if _load_transfer(root, artifact_writer, limits, manifest.identity)[0] != manifest:
        raise ValueError("knowledge transfer changed during verification")
    _require_access(require_access, identities, "READ")
    artifact_writer.root.verify(for_write=False)
    return manifest, reports, packet, publication


def verify_knowledge_transfer(*, directory, artifact_writer, registry, require_access,
                              limits=KnowledgeStoreLimits(), expected_transfer=None):
    with recursive_closure_limits(limits.closure):
        manifest, reports, _, _ = _verify_transfer(directory=directory, artifact_writer=artifact_writer,
            registry=registry, limits=limits, require_access=require_access, expected=expected_transfer)
    return {"status": "VERIFIED_TRANSFER_BYTES", "transfer": manifest.identity.to_document(),
        "objects": reports, **_transfer_description(manifest),
        "consumer_admission": "NOT_EVALUATED", "new_native_contacts": 0,
        "authorship": "NOT_ATTESTED", "update_freshness": "ONLY_THIS_SELECTED_TRANSFER_OBSERVED"}


def _prepare_knowledge_transfer(*, sources, roots, output_directory, project_root, artifact_writer,
                                registry, require_access, limits):
    """The existing export validation; its operation-local result grants no future access."""
    if type(sources) is not tuple or not 1 <= len(sources) <= limits.maximum_objects:
        raise ValueError("knowledge export requires a bounded explicit original-source census")
    if type(registry) is not ScientificTypeRegistry:
        raise TypeError("knowledge export requires its code-owned exact type registry")
    destination = preflight_authoring_output_directory(directory=Path(output_directory),
        repo_root=Path(project_root), artifact_writer=artifact_writer)
    described = tuple(_describe_source(source, artifact_writer, registry, limits, require_access) for source in sources)
    rows = tuple(sorted((row for row, _ in described), key=lambda row: object_key(row.identity)))
    if len({row.identity for row in rows}) != len(rows):
        raise ValueError("knowledge export repeats a complete scientific identity")
    dependency_order(rows, roots, limits)
    original = {row.identity: directory for row, directory in described}
    if any(destination.is_relative_to(directory) or directory.is_relative_to(destination)
           for directory in original.values()):
        raise ValueError("knowledge export must be disjoint from its original packages")
    censuses, members = {}, []
    for row in rows:
        selected = bounded_custody_members(original[row.identity], ("",), limits=limits.closure)
        censuses[row.identity] = selected
        members.extend(replace(value, relative_path=row.relative_directory + "/" + value.relative_path)
                       for value in selected)
    members = tuple(sorted(members, key=lambda value: value.relative_path))
    require_closure_members(members, limits.closure)
    # Resolve actual original scientific/access prerequisites before copying
    # any selected package; the copied packet is checked again at its new root.
    reports = _verify_objects(rows, roots, original, artifact_writer, registry, limits, require_access)
    roots = tuple(sorted(roots, key=object_key))
    key = sha256(canonical_json_bytes((roots, rows, members))).hexdigest()
    manifest = KnowledgeTransferManifest("knowledge-transfer." + key, roots, rows, members)
    if limits.closure.maximum_control_bytes is not None and len(manifest.canonical_bytes()) > limits.closure.maximum_control_bytes:
        raise ValueError("knowledge transfer manifest exceeds its selected control bound")
    return destination, manifest, censuses, original, reports


def _transfer_description(manifest):
    return {"roots": tuple(value.to_document() for value in manifest.roots),
        "object_census": tuple(value.to_document() for value in manifest.objects),
        "physical_closure": {"objects": len(manifest.objects), "members": len(manifest.members),
            "bytes": sum(value.size_bytes for value in manifest.members),
            "scope": "COMPLETE_SELECTED_OBJECT_PACKAGES; outer transfer controls are additional"}}


def preview_knowledge_transfer(*, sources, roots, output_directory, project_root, artifact_writer,
                               registry, require_access, limits=KnowledgeStoreLimits()):
    """Review the original export operands without creating a destination or copying bytes."""
    with recursive_closure_limits(limits.closure):
        destination, manifest, censuses, original, reports = _prepare_knowledge_transfer(
            sources=sources, roots=roots, output_directory=output_directory, project_root=project_root,
            artifact_writer=artifact_writer, registry=registry, require_access=require_access, limits=limits)
        for row in manifest.objects:
            if bounded_custody_members(original[row.identity], ("",), limits=limits.closure) != censuses[row.identity]:
                raise ValueError("original knowledge package changed during export review")
        _require_access(require_access, tuple(row.identity for row in manifest.objects), "EXPORT")
        artifact_writer.root.verify(for_write=False)
    return {"status": "REVIEWED_CURRENT_EXPORT", "transfer": manifest.identity.to_document(),
        "directory": str(destination), "objects": reports, **_transfer_description(manifest),
        "consumer_admission": "NOT_EVALUATED", "current_execution_authority": "NONE",
        "original_records_rewritten": False, "new_native_contacts": 0}


def create_knowledge_transfer(*, sources, roots, output_directory, project_root, artifact_writer,
                              registry, require_access, limits=KnowledgeStoreLimits(), expected_transfer=None):
    """Assemble complete original packages; the existing replica service imports them."""
    if expected_transfer is not None and type(expected_transfer) is not ObjectIdentity:
        raise TypeError("reviewed export requires an exact transfer identity")
    with recursive_closure_limits(limits.closure):
        destination, manifest, censuses, original, _ = _prepare_knowledge_transfer(
            sources=sources, roots=roots, output_directory=output_directory, project_root=project_root,
            artifact_writer=artifact_writer, registry=registry, require_access=require_access, limits=limits)
        if expected_transfer is not None and manifest.identity != expected_transfer:
            raise ValueError("knowledge export differs from its reviewed complete transfer identity")
        rows = manifest.objects
        destination.mkdir(parents=True)
        root = Path(artifact_writer.root.contract.canonical_path)
        for row in rows:
            _require_access(require_access, (row.identity,), "EXPORT")
            copy_closure_members(members=censuses[row.identity], source_guard=artifact_writer.root,
                destination_guard=artifact_writer.root,
                source_prefix=original[row.identity].relative_to(root).as_posix(),
                destination_prefix=(destination / row.relative_directory).relative_to(root).as_posix())
        for row in rows:
            if bounded_custody_members(original[row.identity], ("",), limits=limits.closure) != censuses[row.identity]:
                raise ValueError("original knowledge package changed during export")
        packet = _packet_plane(artifact_writer, destination, manifest)
        _require_access(require_access, tuple(row.identity for row in rows), "EXPORT")
        _publish(packet, destination / "control", "transfer.json", manifest, manifest.transfer_id)
        report = verify_knowledge_transfer(directory=destination, artifact_writer=artifact_writer,
            registry=registry, require_access=require_access, limits=limits, expected_transfer=manifest.identity)
    return {**report, "directory": str(destination)}


class KnowledgeStore:
    """An explicit local guarded store; its catalogue remains a disposable projection."""

    def __init__(self, *, directory, namespace, artifact_writer, registry, require_access,
                 project_root, limits=KnowledgeStoreLimits()):
        KnowledgeStoreHeader(namespace)
        if (type(registry) is not ScientificTypeRegistry or type(limits) is not KnowledgeStoreLimits
                or not callable(require_access)):
            raise TypeError("knowledge store requires registered types, explicit limits and a current access guard")
        limits.__post_init__()
        self.directory, self.namespace = Path(directory), namespace
        self.artifact_writer, self.registry = artifact_writer, registry
        self.require_access, self.project_root, self.limits = require_access, Path(project_root), limits

    def initialize(self):
        directory = preflight_authoring_output_directory(directory=self.directory,
            repo_root=self.project_root, artifact_writer=self.artifact_writer)
        directory.mkdir(parents=True)
        _publish(self.artifact_writer, directory, "store.json", KnowledgeStoreHeader(self.namespace),
                 "knowledge-store." + sha256(self.namespace.encode()).hexdigest())
        return {"status": "INITIALIZED", "namespace": self.namespace, "directory": str(directory)}

    def _selected(self):
        directory = _selected_directory(self.directory, self.artifact_writer)
        header, _ = _published_record(self.artifact_writer, directory / "store.json",
            KnowledgeStoreHeader, self.limits.closure.maximum_control_bytes)
        if header.namespace != self.namespace:
            raise ValueError("knowledge store selection changes its original namespace")
        return directory

    def _import_directories(self):
        parent = self._selected() / "imports"
        if not parent.exists():
            return ()
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError("knowledge import location is not an ordinary selected directory")
        values = []
        with os.scandir(parent) as entries:
            for entry in entries:
                if len(values) >= self.limits.maximum_imports:
                    raise ValueError("knowledge store exceeds its selected import census bound")
                if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                    raise ValueError("knowledge import census contains an unexpected path")
                values.append(Path(entry.path))
        return tuple(sorted(values))

    def _receipt(self, directory, expected=None):
        record, publication = _published_record(self.artifact_writer, directory / "import.json",
            KnowledgeImportReceipt, self.limits.closure.maximum_control_bytes)
        root = Path(self.artifact_writer.root.contract.canonical_path)
        if (record.store_namespace != self.namespace or record.import_relative_path != directory.relative_to(root).as_posix()
                or directory.parent != self._selected() / "imports"
                or directory.name != record.transfer.object_fingerprint
                or expected is not None and record.identity != expected):
            raise ValueError("knowledge import receipt changes its exact local location or identity")
        replica = read_bounded_bytes(directory / "replica.json", maximum_bytes=self.limits.closure.maximum_control_bytes)
        if sha256(replica).hexdigest() != record.replica_receipt_sha256:
            raise ValueError("knowledge import changes its original replica completion receipt")
        return record, publication

    def _locators(self, directory, receipt, manifest):
        root = Path(self.artifact_writer.root.contract.canonical_path)
        return tuple(KnowledgeObjectLocator(self.namespace, (directory / "import.json").relative_to(root).as_posix(),
            receipt.identity, manifest.identity, row.identity) for row in manifest.objects)

    @_bounded_store_operation
    def import_transfer(self, *, directory, source_artifact_writer, source_require_access, expected_transfer,
                        resume=False):
        """Use the established durable replica owner, publishing store completion last."""
        if type(resume) is not bool or type(expected_transfer) is not ObjectIdentity:
            raise TypeError("knowledge import requires an exact transfer identity and boolean recovery selection")
        selected = self._selected()
        self.artifact_writer.root.verify(for_write=True)
        with exclusive_file_lock(selected / ".knowledge-import.lock", blocking=False):
            with recursive_closure_limits(self.limits.closure):
                manifest, _, source, publication = _verify_transfer(directory=directory,
                    artifact_writer=source_artifact_writer, registry=self.registry, limits=self.limits,
                    require_access=source_require_access, expected=expected_transfer)
                identities = tuple(row.identity for row in manifest.objects)
                _require_access(self.require_access, identities, "IMPORT")
                destination = selected / "imports" / manifest.fingerprint()
                existing = self._import_directories()
                if destination not in existing and len(existing) >= self.limits.maximum_imports:
                    raise ValueError("knowledge store has reached its selected import bound")
                if (destination / "import.json").exists():
                    receipt, _ = self._receipt(destination)
                    checked = self._verify_import(destination, receipt)
                    return {"status": "DUPLICATE_VERIFIED", "directory": str(destination),
                        "locators": self._locators(destination, receipt, manifest), "objects": checked[1]}
                if destination.exists() and not resume:
                    raise ValueError("knowledge import is incomplete; select explicit recovery of its original copy plan")
                destination.mkdir(parents=True, exist_ok=resume)
                packet_directory = destination / "packet"
                packet_directory.mkdir(exist_ok=resume)
                target = _packet_plane(self.artifact_writer, packet_directory, manifest)

                def current():
                    self._selected()
                    _require_access(source_require_access, identities, "EXPORT")
                    _require_access(self.require_access, identities, "IMPORT")

                def final_source():
                    _verify_transfer(directory=directory, artifact_writer=source_artifact_writer,
                        registry=self.registry, limits=self.limits, require_access=source_require_access,
                        expected=manifest.identity)

                replicate_artifact_publications(source, target.root, publications=(publication,),
                    supplemental_files=tuple(ReplicaFile(value.relative_path, value.size_bytes, value.sha256)
                                             for value in manifest.members),
                    receipt_path=destination / "replica.json", maximum_bytes=self.limits.closure.maximum_total_bytes,
                    maximum_files=self.limits.closure.maximum_members, require_current=current,
                    before_complete=final_source, resume=True)
                checked = _verify_transfer(directory=packet_directory, artifact_writer=self.artifact_writer,
                    registry=self.registry, limits=self.limits, require_access=self.require_access,
                    expected=manifest.identity)
                root = Path(self.artifact_writer.root.contract.canonical_path)
                replica = read_bounded_bytes(destination / "replica.json", maximum_bytes=self.limits.closure.maximum_control_bytes)
                receipt = KnowledgeImportReceipt("knowledge-import." + sha256(canonical_json_bytes(
                    (self.namespace, manifest.identity))).hexdigest(), self.namespace, manifest.identity,
                    datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
                    destination.relative_to(root).as_posix(), sha256(replica).hexdigest())
                current()
                _publish(self.artifact_writer, destination, "import.json", receipt, receipt.receipt_id)
                self._receipt(destination, receipt.identity)
                self._require_replica_members(destination, receipt)
                current()
                return {"status": "IMPORTED", "directory": str(destination),
                    "locators": self._locators(destination, receipt, manifest), "objects": checked[1],
                    "consumer_admission": "NOT_EVALUATED", "original_records_rewritten": False}

    def _require_replica_members(self, directory, receipt):
        raw = read_bounded_bytes(directory / "replica.json", maximum_bytes=self.limits.closure.maximum_control_bytes)
        if sha256(raw).hexdigest() != receipt.replica_receipt_sha256:
            raise ValueError("knowledge replica completion changed during current read")
        replica = json.loads(raw)
        packet = directory / "packet"
        files = bounded_custody_members(packet, ("",), limits=self.limits.closure)
        if (replica.get("status") != "COMPLETE"
                or replica.get("files") != [{"relative_path": v.relative_path, "size_bytes": v.size_bytes,
                                              "sha256": v.sha256} for v in files]):
            raise ValueError("knowledge import no longer matches its exact original replica completion")

    def _verify_import(self, directory, receipt):
        checked = _verify_transfer(directory=directory / "packet", artifact_writer=self.artifact_writer,
            registry=self.registry, limits=self.limits, require_access=self.require_access, expected=receipt.transfer)
        self._require_replica_members(directory, receipt)
        self._receipt(directory, receipt.identity)
        return checked

    @_bounded_store_operation
    def resolve(self, locator, *, allow_incomplete=False):
        if type(locator) is not KnowledgeObjectLocator or type(allow_incomplete) is not bool:
            raise TypeError("knowledge resolution requires an exact locator and incomplete-read selection")
        locator.__post_init__()
        if locator.store_namespace != self.namespace:
            raise ValueError("knowledge locator belongs to another store namespace")
        self._selected()
        root = Path(self.artifact_writer.root.contract.canonical_path)
        path = self.artifact_writer.root.resolve(locator.receipt_relative_path, for_write=False)
        with recursive_closure_limits(self.limits.closure):
            receipt, _ = self._receipt(path.parent, locator.import_receipt)
            if receipt.transfer != locator.transfer:
                raise ValueError("knowledge locator substitutes its exact original transfer")
            try:
                _require_access(self.require_access, (locator.object_identity,), "READ")
                manifest, reports, _, _ = self._verify_import(path.parent, receipt)
                if locator.object_identity not in {row.identity for row in manifest.objects}:
                    raise ValueError("knowledge locator object is absent from its original import")
            except (OSError, ValueError, RuntimeError) as error:
                if not allow_incomplete:
                    raise
                return {"status": "ACCESS_REFUSED" if isinstance(error, PermissionError) else "UNAVAILABLE_OR_UNVERIFIED",
                    "identity": locator.object_identity.to_document(),
                    "reason": str(error)[:1024], "consumer_admission": "NOT_EVALUATED",
                    "scientific_assessment": "NOT_VERIFIED", "unseen_updates": "UNKNOWN"}
        return {"status": "RESOLVED_CURRENT_CUSTODY", **reports[object_key(locator.object_identity)],
            "observed_update_source": receipt.identity.to_document(), "import_observed_at_utc": receipt.imported_at_utc,
            "unseen_updates": "UNKNOWN", "directory": str(path.parent / "packet" / ("objects/" + object_key(locator.object_identity))),
            "locator": replace(locator, receipt_relative_path=path.relative_to(root).as_posix()).to_document()}

    def _export_sources(self, locators):
        if type(locators) is not tuple or not 1 <= len(locators) <= self.limits.maximum_objects:
            raise ValueError("knowledge export requires its bounded exact locator census")
        sources = []
        for locator in locators:
            resolved = self.resolve(locator)
            path = self.artifact_writer.root.resolve(locator.receipt_relative_path, for_write=False)
            receipt, _ = self._receipt(path.parent, locator.import_receipt)
            manifest, _, _ = _load_transfer(path.parent / "packet", self.artifact_writer, self.limits, receipt.transfer)
            row, = tuple(row for row in manifest.objects if row.identity == locator.object_identity)
            sources.append(KnowledgeObjectSource(row.identity, Path(resolved["directory"]), row.origin_namespace,
                row.publisher_label, row.record_filename))
        return tuple(sources)

    @_bounded_store_operation
    def preview_export(self, *, locators, roots, output_directory):
        return preview_knowledge_transfer(sources=self._export_sources(locators), roots=roots,
            output_directory=output_directory, project_root=self.project_root,
            artifact_writer=self.artifact_writer, registry=self.registry,
            require_access=self.require_access, limits=self.limits)

    @_bounded_store_operation
    def export(self, *, locators, roots, output_directory, expected_transfer=None):
        return create_knowledge_transfer(sources=self._export_sources(locators), roots=roots,
            output_directory=output_directory, project_root=self.project_root,
            artifact_writer=self.artifact_writer, registry=self.registry,
            require_access=self.require_access, limits=self.limits, expected_transfer=expected_transfer)

    @_bounded_store_operation
    def rebuild_projection(self, *, catalog_access):
        """Authenticate primary imports, then populate a new explicit empty catalogue."""
        if type(catalog_access) is not GuardedCatalogAccess:
            raise TypeError("knowledge projection requires its explicit guarded catalogue selection")
        catalog_access.verify(for_write=True)
        if catalog_access.database_path.exists():
            raise ValueError("knowledge projection rebuild requires a new selected catalogue destination")
        logical, locators, incomplete = [], [], []
        for directory in self._import_directories():
            if not (directory / "import.json").exists():
                incomplete.append(str(directory))
                continue
            with recursive_closure_limits(self.limits.closure):
                receipt, publication = self._receipt(directory)
                self._verify_import(directory, receipt)
            value, physical = publication.logical, publication.materialization
            logical.append(LogicalArtifactRecord(value.logical_artifact_id, value.content_sha256, value.payload_schema,
                value.profile, value.media_type, value.visibility_ceiling))
            locators.append(ArtifactLocatorRecord(physical.materialization_id, value.logical_artifact_id,
                physical.storage_root_id, physical.relative_path, physical.physical_sha256, physical.size_bytes,
                physical.compression, physical.partition_selector, CatalogVerificationStatus.VERIFIED))
        contract = self.artifact_writer.root.contract
        root = StorageRootRecord(contract.storage_root_id, contract.logical_name, contract.canonical_path,
            contract.mount_contract_schema, CatalogVerificationStatus.VERIFIED)
        snapshot = CatalogSnapshot((root,), tuple(sorted(logical, key=lambda row: row.logical_artifact_id)),
            tuple(sorted(locators, key=lambda row: row.materialization_id)), (), (), (), (), (), ())
        self._selected()
        engine = catalog_access.initialize_engine()
        try:
            repository = SQLiteCatalogRepository(engine)
            repository.append_snapshot(snapshot)
            if repository.snapshot() != snapshot or repository.integrity_check():
                raise ValueError("knowledge projection differs from its authenticated original imports")
        finally:
            engine.dispose()
        return {"status": "REBUILT_FROM_PRIMARY_IMPORTS", "catalog": catalog_access.display_locator,
            "complete_imports": len(locators), "incomplete_imports": tuple(incomplete),
            "scientific_objects_reclassified": 0, "consumer_admission": "NOT_EVALUATED",
            "unseen_updates": "UNKNOWN"}

    @_bounded_store_operation
    def query(self, *, catalog_access, limit=8, after_materialization_id=None):
        """Return discovery locations, with no cached current assessment verdict."""
        if type(limit) is not int or not 1 <= limit <= self.limits.maximum_query_imports:
            raise ValueError("knowledge query exceeds its selected import-page bound")
        directory = self._selected()
        root = Path(self.artifact_writer.root.contract.canonical_path)
        query = CatalogArtifactQuery(self.artifact_writer.root.contract.storage_root_id, KnowledgeImportReceipt.SCHEMA,
            (directory / "imports").relative_to(root).as_posix(), limit, after_materialization_id)
        engine = catalog_access.read_only_engine()
        try:
            page = SQLiteCatalogRepository(engine).query_artifacts(query)
        finally:
            engine.dispose()
        rows = []
        for value in page.rows:
            if value.storage_root.canonical_path != str(root):
                raise ValueError("knowledge catalogue location changes the selected guarded root")
            path = self.artifact_writer.root.resolve(value.locator.relative_path, for_write=False)
            receipt, published = self._receipt(path.parent)
            if (value.logical.logical_artifact_id != published.logical.logical_artifact_id
                    or value.logical.content_sha256 != published.logical.content_sha256
                    or value.locator.materialization_id != published.materialization.materialization_id
                    or value.locator.physical_sha256 != published.materialization.physical_sha256):
                raise ValueError("knowledge catalogue location substitutes its original import custody")
            manifest, _, _ = _load_transfer(path.parent / "packet", self.artifact_writer, self.limits, receipt.transfer)
            found = self._locators(path.parent, receipt, manifest)
            _require_access(self.require_access, tuple(row.identity for row in manifest.objects), "DISCOVER")
            rows.append({"import_receipt": receipt.identity.to_document(), "import_observed_at_utc": receipt.imported_at_utc,
                "objects": tuple({"identity": row.identity.to_document(), "origin_namespace": row.origin_namespace,
                    "publisher_label": row.publisher_label, "locator": locator.to_document()}
                    for row, locator in zip(manifest.objects, found, strict=True)),
                "current_scientific_assessment": "NOT_CHECKED_BY_DISCOVERY"})
        return {"status": "DISCOVERY_ONLY", "imports": tuple(rows), "has_more": page.has_more,
            "next_after_materialization_id": page.next_after_materialization_id,
            "query_work_steps": page.query_work_steps, "query_work_limit": page.query_work_limit,
            "consumer_admission": "NOT_EVALUATED", "update_sources": "ONLY_THE_SELECTED_PROJECTED_IMPORTS",
            "unseen_updates": "UNKNOWN"}
