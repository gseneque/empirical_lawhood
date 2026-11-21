# SPDX-License-Identifier: MPL-2.0
"""Portable custody and exact type-description contracts, without global trust."""

from collections.abc import Callable
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_relative_locator, validate_sha256, validate_stable_id
from empirical_lawhood.science.models.time import validate_utc_timestamp

from empirical_lawhood.storage.contracts.artifacts import ArtifactWriter
from empirical_lawhood.storage.contracts.record_codecs import RecordCodecCatalog
from empirical_lawhood.execution.recursive_handoff import RecursiveClosureLimits, RecursiveClosureMember


def object_key(identity):
    """Include ID, schema, exact version and complete content digest."""
    if type(identity) is not ObjectIdentity:
        raise TypeError("knowledge identity requires its complete canonical reference")
    identity.__post_init__()
    return sha256(identity.canonical_bytes()).hexdigest()


def _identities(values, *, nonempty=False):
    if type(values) is not tuple or len(values) > 64 or (nonempty and not values):
        raise ValueError("knowledge reference census must be a bounded tuple")
    keys = tuple(object_key(value) for value in values)
    if keys != tuple(sorted(set(keys))):
        raise ValueError("knowledge references repeat or reorder complete content identities")


@dataclass(frozen=True, slots=True)
class KnowledgeStoreLimits:
    closure: RecursiveClosureLimits = field(default_factory=RecursiveClosureLimits)
    maximum_objects: int = 16
    maximum_dependency_depth: int = 8
    maximum_imports: int = 64
    maximum_query_imports: int = 8

    def __post_init__(self):
        if type(self.closure) is not RecursiveClosureLimits:
            raise TypeError("knowledge store needs explicit typed closure bounds")
        self.closure.__post_init__()
        for name, ceiling in (("maximum_objects", 64), ("maximum_dependency_depth", 32),
                              ("maximum_imports", 256), ("maximum_query_imports", 64)):
            if type(getattr(self, name)) is not int or not 1 <= getattr(self, name) <= ceiling:
                raise ValueError("knowledge store bound is outside its supported finite range: " + name)


@dataclass(frozen=True, slots=True)
class KnowledgeDependencyLocation:
    identity: ObjectIdentity
    directory: Path


@dataclass(frozen=True, slots=True)
class KnowledgeVerificationContext:
    directory: Path
    artifact_writer: ArtifactWriter
    identity: ObjectIdentity
    record: CanonicalRecord
    dependencies: tuple[KnowledgeDependencyLocation, ...]


@dataclass(frozen=True, slots=True)
class ScientificTypeDescriptor:
    """Code-owned exact decoder, dependency contract and optional current verifier."""

    descriptor_id: str
    record_type: type[CanonicalRecord]
    identity_field: str
    record_filename: str
    dependencies: Callable[[CanonicalRecord], tuple[ObjectIdentity, ...]]
    verify: Callable[[KnowledgeVerificationContext], dict] | None = None

    def __post_init__(self):
        validate_stable_id(self.descriptor_id)
        RecordCodecCatalog((self.record_type,))
        if self.identity_field not in self.record_type.__dataclass_fields__:
            raise ValueError("knowledge descriptor identity field is not in its exact record")
        validate_relative_locator(self.record_filename)
        if "/" in self.record_filename or self.record_filename.endswith(".manifest.json"):
            raise ValueError("knowledge record filename must be a simple payload name")
        if not callable(self.dependencies) or (self.verify is not None and not callable(self.verify)):
            raise TypeError("knowledge descriptor callbacks must be registered code-owned callables")

    def identity(self, record):
        if type(record) is not self.record_type:
            raise TypeError("knowledge descriptor received another exact record revision")
        return ObjectIdentity.from_record(getattr(record, self.identity_field), record)


class ScientificTypeRegistry:
    """Exact extension census; no data-selected imports or central domain enum."""

    def __init__(self, descriptors):
        if type(descriptors) is not tuple or len(descriptors) > 256:
            raise ValueError("knowledge descriptor registry requires a bounded tuple")
        selected, names = {}, set()
        for value in descriptors:
            if type(value) is not ScientificTypeDescriptor:
                raise TypeError("knowledge registry requires typed code-owned descriptors")
            value.__post_init__()
            key = value.record_type.SCHEMA, value.record_type.VERSION
            if key in selected or value.descriptor_id in names:
                raise ValueError("knowledge registry repeats an exact revision or descriptor identity")
            selected[key] = value
            names.add(value.descriptor_id)
        self.codecs = RecordCodecCatalog(value.record_type for value in descriptors)
        self.descriptors = MappingProxyType(selected)

    def descriptor(self, identity):
        return self.descriptors.get((identity.object_schema, identity.object_version))


@dataclass(frozen=True, slots=True)
class PortableKnowledgeObject(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/portable-knowledge-object"
    identity: ObjectIdentity
    origin_namespace: str
    publisher_label: str
    record_filename: str
    dependencies: tuple[ObjectIdentity, ...]
    dependency_description: str

    def __post_init__(self):
        object_key(self.identity)
        validate_stable_id(self.origin_namespace)
        validate_stable_id(self.publisher_label)
        validate_relative_locator(self.record_filename)
        if "/" in self.record_filename or self.record_filename.endswith(".manifest.json"):
            raise ValueError("portable knowledge object needs a simple original record filename")
        _identities(self.dependencies)
        if self.dependency_description not in ("REGISTERED_COMPLETE", "OPAQUE_UNINTERPRETED"):
            raise ValueError("knowledge object changes its dependency-description contract")

    @property
    def relative_directory(self):
        return "objects/" + object_key(self.identity)


@dataclass(frozen=True, slots=True)
class KnowledgeTransferManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/knowledge-transfer-manifest"
    transfer_id: str
    roots: tuple[ObjectIdentity, ...]
    objects: tuple[PortableKnowledgeObject, ...]
    members: tuple[RecursiveClosureMember, ...]

    def __post_init__(self):
        validate_stable_id(self.transfer_id)
        _identities(self.roots, nonempty=True)
        if type(self.objects) is not tuple or not 1 <= len(self.objects) <= 64:
            raise ValueError("knowledge transfer requires its bounded object census")
        for value in self.objects:
            if type(value) is not PortableKnowledgeObject:
                raise TypeError("knowledge transfer contains another object contract")
            value.__post_init__()
        _identities(tuple(value.identity for value in self.objects), nonempty=True)
        identities = {v.identity for v in self.objects}
        if not set(self.roots) <= identities:
            raise ValueError("knowledge transfer omits a selected root")
        if any(not set(value.dependencies) <= identities for value in self.objects):
            raise ValueError("knowledge transfer has a missing dependency")
        if type(self.members) is not tuple or not 1 <= len(self.members) <= 65536:
            raise ValueError("knowledge transfer requires a bounded complete member census")
        paths = []
        for member in self.members:
            if type(member) is not RecursiveClosureMember:
                raise TypeError("knowledge transfer requires original typed closure members")
            member.__post_init__()
            paths.append(member.relative_path)
        if paths != sorted(set(paths)):
            raise ValueError("knowledge transfer repeats or reorders physical members")
        by_path = {member.relative_path: member for member in self.members}
        prefixes = tuple(value.relative_directory + "/" for value in self.objects)
        if any(not path.startswith(prefixes) for path in paths):
            raise ValueError("knowledge transfer contains unassigned custody bytes")
        for value in self.objects:
            selected = by_path.get(value.relative_directory + "/" + value.record_filename)
            if selected is None or selected.sha256 != value.identity.object_fingerprint:
                raise ValueError("knowledge transfer omits or changes an exact selected object")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.transfer_id, self)


def dependency_order(objects, roots, limits):
    """One bounded complete topological census, preserving adverse branches too."""
    if len(objects) > limits.maximum_objects:
        raise ValueError("knowledge closure exceeds its selected object bound")
    by_identity = {value.identity: value for value in objects}
    active, finished, ordered = set(), set(), []

    def visit(identity, depth):
        if depth > limits.maximum_dependency_depth:
            raise ValueError("knowledge closure exceeds its selected dependency depth")
        if identity in active:
            raise ValueError("knowledge dependency closure cycles")
        if identity in finished:
            return
        if identity not in by_identity:
            raise ValueError("knowledge closure has a missing dependency")
        active.add(identity)
        for dependency in by_identity[identity].dependencies:
            visit(dependency, depth + 1)
        active.remove(identity)
        finished.add(identity)
        ordered.append(by_identity[identity])

    for root in roots:
        visit(root, 1)
    if finished != by_identity.keys():
        raise ValueError("knowledge transfer contains objects outside its selected closure")
    return tuple(ordered)


@dataclass(frozen=True, slots=True)
class KnowledgeStoreHeader(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/knowledge-store-header"
    namespace: str
    authority_scope: str = "LOCAL_CUSTODY_AND_DISCOVERY_ONLY"

    def __post_init__(self):
        validate_stable_id(self.namespace)
        if self.authority_scope != "LOCAL_CUSTODY_AND_DISCOVERY_ONLY":
            raise ValueError("knowledge store header cannot grant scientific authority")


@dataclass(frozen=True, slots=True)
class KnowledgeImportReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/knowledge-import-receipt"
    receipt_id: str
    store_namespace: str
    transfer: ObjectIdentity
    imported_at_utc: str
    import_relative_path: str
    replica_receipt_sha256: str

    def __post_init__(self):
        validate_stable_id(self.receipt_id)
        validate_stable_id(self.store_namespace)
        validate_utc_timestamp(self.imported_at_utc)
        validate_relative_locator(self.import_relative_path)
        validate_sha256(self.replica_receipt_sha256)
        object_key(self.transfer)
        if (self.transfer.object_schema, self.transfer.object_version) != (
                KnowledgeTransferManifest.SCHEMA, KnowledgeTransferManifest.VERSION):
            raise ValueError("knowledge import changes its exact transfer contract")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.receipt_id, self)


@dataclass(frozen=True, slots=True)
class KnowledgeObjectLocator(CanonicalRecord):
    """An operational location plus exact pins; discovery is not admission."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/knowledge-object-locator"
    store_namespace: str
    receipt_relative_path: str
    import_receipt: ObjectIdentity
    transfer: ObjectIdentity
    object_identity: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.store_namespace)
        validate_relative_locator(self.receipt_relative_path)
        for value in (self.import_receipt, self.transfer, self.object_identity):
            object_key(value)
        if (self.import_receipt.object_schema, self.import_receipt.object_version) != (
                KnowledgeImportReceipt.SCHEMA, KnowledgeImportReceipt.VERSION):
            raise ValueError("knowledge locator changes its original import-receipt contract")
