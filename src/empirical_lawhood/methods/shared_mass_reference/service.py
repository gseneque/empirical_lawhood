# SPDX-License-Identifier: MPL-2.0
"""One immutable scope service; it contains no observations or effect handles."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.methods.mass_balance_starter.records import MassScope
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_semantic_version, validate_stable_id


@dataclass(frozen=True, slots=True)
class ScopeServiceSelection:
    """A code-injected service selection, separate from canonical scientific data."""

    service_key: str
    service_version: str
    configuration: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.service_key)
        validate_semantic_version(self.service_version)
        if type(self.configuration) is not ObjectIdentity:
            raise TypeError('shared scope selection requires its exact configuration identity')
        self.configuration.__post_init__()


@dataclass(frozen=True, slots=True)
class MassScopeService:
    """Share only the common immutable source/receiver/clock/unit configuration."""

    KEY: ClassVar[str] = 'mass-balance.shared-scope'
    VERSION: ClassVar[str] = '1.0.0'
    configuration: MassScope
    reference: ObjectIdentity

    def __post_init__(self):
        if type(self.configuration) is not MassScope or type(self.reference) is not ObjectIdentity:
            raise TypeError('shared scope service accepts only an immutable MassScope@1.0.0 and its identity')
        self.configuration.__post_init__()
        self.reference.__post_init__()
        if self.reference != ObjectIdentity.from_record(self.reference.object_id, self.configuration):
            raise ValueError('shared scope configuration differs from its exact schema/revision/bytes')

    @property
    def selection(self):
        return ScopeServiceSelection(self.KEY, self.VERSION, self.reference)

    def resolve(self, selection):
        if type(selection) is not ScopeServiceSelection:
            raise TypeError('shared scope requires its typed read-only service selection')
        if selection.service_key != self.KEY:
            raise ValueError('shared scope service namespace has another owner')
        if selection.service_version != self.VERSION:
            raise ValueError('unsupported shared scope service revision; supported revision: 1.0.0')
        if selection.configuration != self.reference:
            raise ValueError('shared scope service configuration identity differs')
        self.__post_init__()
        return self.configuration
