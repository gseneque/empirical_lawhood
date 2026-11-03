# SPDX-License-Identifier: MPL-2.0
"""Separate PURE structural production over one unchanged failed predecessor."""
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, validate_relative_locator, validate_sha256,
)
from .recursive_handoff import RecursiveImplementationBinding


@dataclass(frozen=True, slots=True)
class DevelopmentStructureRepair(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-structure-repair'

    development_directory: str
    owner_instruction_sha256: str
    acquisition_packet: ObjectIdentity
    acquisition_terminal: ObjectIdentity
    acquisition_controls_sha256: str
    structural_packet: ObjectIdentity
    structural_terminal: ObjectIdentity
    structural_controls_sha256: str
    original_source: RecursiveImplementationBinding
    replacement_source: RecursiveImplementationBinding

    def __post_init__(self):
        validate_relative_locator(self.development_directory)
        for value in (self.owner_instruction_sha256, self.acquisition_controls_sha256,
                self.structural_controls_sha256):
            validate_sha256(value)
        for value in (self.acquisition_packet, self.acquisition_terminal,
                self.structural_packet, self.structural_terminal):
            if type(value) is not ObjectIdentity:
                raise TypeError('structural repair requires exact original custody identities')
            value.__post_init__()
        for value in (self.original_source, self.replacement_source):
            if type(value) is not RecursiveImplementationBinding:
                raise TypeError('structural repair requires both actual source inventories')
            value.__post_init__()
        if (self.original_source.observed_git_head == self.replacement_source.observed_git_head
                or self.original_source.dependency_lock_sha256 != self.replacement_source.dependency_lock_sha256):
            raise ValueError('structural repair requires a distinct source with the original lock')

    @property
    def repair_id(self):
        return 'repair.development-structure.' + sha256(canonical_json_bytes(self)).hexdigest()[:24]

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.repair_id, self)

    @property
    def child_relative_path(self):
        return self.development_directory + '/structure/repairs/' + self.repair_id + '/analysis'
