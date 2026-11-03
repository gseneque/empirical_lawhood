# SPDX-License-Identifier: MPL-2.0
"""Bounded member contracts for a frozen recursive authoring export."""

from empirical_lawhood.kernel.decoding import validate_record_fields
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_ids, validate_relative_locator,
    validate_sha256, validate_stable_id,
)


@dataclass(frozen=True, slots=True)
class RecursiveWaveMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/recursive-wave-member"
    filename: str
    identity: ObjectIdentity
    size_bytes: int

    def __post_init__(self):
        validate_relative_locator(self.filename)
        if "/" in self.filename or self.filename.endswith(".manifest.json"):
            raise ValueError("authored wave members require simple exact file names")
        if type(self.size_bytes) is not int or self.size_bytes <= 0:
            raise ValueError("authored wave member needs its positive exact byte size")


@dataclass(frozen=True, slots=True)
class RecursiveImplementationBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/recursive-implementation-binding"
    package_sources: tuple[tuple[str, str], ...]
    code_sources_sha256: str
    dependency_lock_sha256: str
    observed_git_head: str
    observed_checkout_clean: bool

    def __post_init__(self):
        from hashlib import sha256
        from empirical_lawhood.kernel.serialization import canonical_json_bytes

        if not self.package_sources or self.package_sources != tuple(sorted(set(self.package_sources))):
            raise ValueError("implementation binding requires an exact source inventory")
        if len({name for name, _ in self.package_sources}) != len(self.package_sources):
            raise ValueError("implementation source inventory repeats a path")
        for name, digest in self.package_sources:
            validate_relative_locator(name)
            validate_sha256(digest)
        validate_sha256(self.code_sources_sha256)
        validate_sha256(self.dependency_lock_sha256)
        if sha256(canonical_json_bytes(self.package_sources)).hexdigest() != self.code_sources_sha256:
            raise ValueError("implementation source digest differs from its member inventory")
        if len(self.observed_git_head) != 40 or any(c not in "0123456789abcdef" for c in self.observed_git_head):
            raise ValueError("implementation binding requires its actually observed Git commit")
        if type(self.observed_checkout_clean) is not bool:
            raise ValueError("implementation checkout cleanliness must be observed")


@dataclass(frozen=True, slots=True)
class AuthoredRecursiveWave(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/authored-recursive-wave"
    packet_id: str
    draft: ObjectIdentity
    implementation: ObjectIdentity
    members: tuple[RecursiveWaveMember, ...]

    def __post_init__(self):
        validate_stable_id(self.packet_id, field_name="packet_id")
        require_sorted_unique_ids(self.members, attribute="filename", field_name="members")
        if not self.members:
            raise ValueError("authoring export requires its complete member census")
        by_name = {value.filename: value.identity for value in self.members}
        if by_name.get("draft.json") != self.draft or by_name.get("implementation.json") != self.implementation:
            raise ValueError("authoring export omits its exact draft or implementation")


@dataclass(frozen=True, slots=True)
class RecursiveClosureMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/recursive-closure-member"
    relative_path: str
    size_bytes: int
    sha256: str

    def __post_init__(self):
        validate_relative_locator(self.relative_path)
        validate_sha256(self.sha256)
        if type(self.size_bytes) is not int or self.size_bytes <= 0:
            raise ValueError("closure member needs its positive exact byte size")


@dataclass(frozen=True, slots=True)
class PortableRecursiveContribution(CanonicalRecord):
    """Explicit byte relocation, preserving the original custody identities."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/portable-recursive-contribution"
    transport_id: str
    original_storage_root_id: str
    authoring_relative_path: str
    run_relative_path: str
    contribution: ObjectIdentity
    members: tuple[RecursiveClosureMember, ...]
    parent_closure_relative_paths: tuple[str, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.transport_id, field_name="transport_id")
        validate_stable_id(self.original_storage_root_id, field_name="original_storage_root_id")
        validate_relative_locator(self.authoring_relative_path)
        validate_relative_locator(self.run_relative_path)
        require_sorted_unique_ids(self.members, attribute="relative_path", field_name="members")
        if not self.members:
            raise ValueError("portable contribution requires its complete custody census")
        for name in self.parent_closure_relative_paths:
            validate_relative_locator(name)
        if self.parent_closure_relative_paths != tuple(sorted(set(self.parent_closure_relative_paths))):
            raise ValueError("portable contribution repeats or reorders a parent closure")
        prefixes = tuple(name + "/" for name in (self.authoring_relative_path, self.run_relative_path, *self.parent_closure_relative_paths))
        if any(not v.relative_path.startswith(prefixes) for v in self.members):
            raise ValueError("portable custody includes a member outside its declared source wave")


@dataclass(frozen=True, slots=True)
class RecursiveParentClosureBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/recursive-parent-closure-binding"
    relative_path: str
    transport: ObjectIdentity
    contribution: ObjectIdentity

    def __post_init__(self):
        validate_relative_locator(self.relative_path)


@dataclass(frozen=True, slots=True)
class RecursiveParentClosuresBinding(CanonicalRecord):
    """Complete direct-parent census; singleton records retain their old format."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/recursive-parent-closures-binding"
    bindings: tuple[RecursiveParentClosureBinding, ...]

    def __post_init__(self):
        if not isinstance(self.bindings, tuple) or not self.bindings or any(
            type(value) is not RecursiveParentClosureBinding for value in self.bindings
        ):
            raise ValueError("parent closures require a nonempty tuple of typed bindings")
        keys = tuple(value.contribution.object_id for value in self.bindings)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("parent closures must preserve sorted unique contribution identities")
        if len({value.relative_path for value in self.bindings}) != len(self.bindings):
            raise ValueError("parent closures repeat a portable directory")
        for value in self.bindings:
            validate_record_fields(value)
            if (value.transport.object_schema != PortableRecursiveContribution.SCHEMA
                    or value.contribution.object_schema != "empirical-lawhood/kernel/contribution-manifest"):
                raise ValueError("parent closure changes its transport or contribution schema")


def recursive_parent_closure_bindings(payloads):
    """Decode exactly one historical singleton or explicit complete collection."""
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes

    single, multiple = "parent-closure.json" in payloads, "parent-closures.json" in payloads
    if single and multiple:
        raise ValueError("wave cannot declare two different parent closure formats")
    if single:
        raw = payloads["parent-closure.json"]
        return (decode_canonical_bytes(raw, RecursiveParentClosureBinding, maximum_bytes=len(raw)),)
    if multiple:
        raw = payloads["parent-closures.json"]
        return decode_canonical_bytes(raw, RecursiveParentClosuresBinding, maximum_bytes=len(raw)).bindings
    return ()
