# SPDX-License-Identifier: MPL-2.0
"""Current Matrix exclusions, independent of historical packages and examples.

The mandatory floor is immutable implementation data. The remaining union is
an explicit factual input: its type and hashes do not establish completeness,
independence, source qualification or authority. Audit those facts externally
before freezing the ordinary current census publication.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.adapters.simulators.six_matrix_response.contracts import BetaCouplingRule
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_sha256, validate_stable_id,
)

MANDATORY_FLOOR_SIZE = 82149
MANDATORY_FLOOR_SHA256 = '5f101c839749230507d73ba61f214d5ab241d382841895cd1f02a0fbb8df853b'


def _seeds(values):
    if (type(values) is not tuple or any(type(value) is not int or not 0 <= value < 2**128 for value in values)
            or values != tuple(sorted(set(values)))):
        raise ValueError('Matrix exclusions require sorted unique actual unsigned128-bit effective seeds')


def _physical_model(record):
    if (record.mass_x != record.mass_y or any(getattr(record, name) == 0 for name in
            ('mass_x', 'mass_y', 'cross_coupling_gamma', 'bath_temperature', 'friction_gamma'))):
        raise ValueError('Matrix physical exclusions retain positive symmetric masses, coupling and bath values')


@dataclass(frozen=True, slots=True)
class MatrixMandatoryExposureFloor(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/mandatory-exposure-floor'
    floor_id: str
    effective_seed_exclusions: tuple[int, ...]

    def __post_init__(self):
        _seeds(self.effective_seed_exclusions)
        if (self.floor_id != 'matrix.exposure.mandatory-floor.v1'
                or len(self.effective_seed_exclusions) != 2074
                or self.fingerprint() != MANDATORY_FLOOR_SHA256):
            raise ValueError('Matrix mandatory exposure floor differs from its exact independently checked bytes')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.floor_id, self)


def load_mandatory_exposure_floor(path: Path | None = None):
    """Fresh bounded byte check; ordinary constructors reuse its immutable value.

    The optional path permits an independent loader check on copied bytes. It
    never changes the required identity or establishes external factual truth.
    """
    selected = (files('empirical_lawhood.resources').joinpath('matrix_factor_response/mandatory-exposure-floor.json')
        if path is None else path)
    with selected.open('rb') as stream:
        raw = stream.read(MANDATORY_FLOOR_SIZE + 1)
    if len(raw) != MANDATORY_FLOOR_SIZE or sha256(raw).hexdigest() != MANDATORY_FLOOR_SHA256:
        raise ValueError('Matrix mandatory exposure floor resource bytes differ')
    return decode_canonical_bytes(raw, MatrixMandatoryExposureFloor, maximum_bytes=MANDATORY_FLOOR_SIZE)


MANDATORY_EXPOSURE_FLOOR = load_mandatory_exposure_floor()
MANDATORY_EFFECTIVE_SEEDS = frozenset(MANDATORY_EXPOSURE_FLOOR.effective_seed_exclusions)
MANDATORY_FLOOR_IDENTITY = MANDATORY_EXPOSURE_FLOOR.identity


@dataclass(frozen=True, slots=True)
class MatrixConstantPhysicalExclusion(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/constant-physical-exclusion'
    mass_x: Decimal
    mass_y: Decimal
    cross_coupling_gamma: Decimal
    beta_rule: BetaCouplingRule
    bath_temperature: Decimal
    friction_gamma: Decimal
    alpha_x: Decimal
    alpha_y: Decimal

    def __post_init__(self):
        for name in ('mass_x', 'mass_y', 'cross_coupling_gamma', 'bath_temperature', 'friction_gamma', 'alpha_x', 'alpha_y'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if type(self.beta_rule) is not BetaCouplingRule:
            raise TypeError('constant physical exclusion requires its exact beta rule')
        _physical_model(self)

    @property
    def key(self):
        return (self.mass_x, self.mass_y, self.cross_coupling_gamma, self.beta_rule,
            self.bath_temperature, self.friction_gamma, self.alpha_x, self.alpha_y)


@dataclass(frozen=True, slots=True)
class MatrixScheduledPhysicalExclusion(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/scheduled-physical-exclusion'
    mass_x: Decimal
    mass_y: Decimal
    cross_coupling_gamma: Decimal
    beta_rule: BetaCouplingRule
    friction_gamma: Decimal
    bath_temperature: Decimal
    family_id: str
    target_x: Decimal
    target_y: Decimal
    decreasing_start: Decimal
    ramp_duration: Decimal
    autonomous_duration: Decimal
    initial_state_rule_id: str
    preparation_rule_id: str

    def __post_init__(self):
        for name in ('mass_x', 'mass_y', 'cross_coupling_gamma', 'friction_gamma', 'bath_temperature',
                'target_x', 'target_y', 'decreasing_start', 'ramp_duration', 'autonomous_duration'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        for name in ('family_id', 'initial_state_rule_id', 'preparation_rule_id'):
            validate_stable_id(getattr(self, name))
        if type(self.beta_rule) is not BetaCouplingRule:
            raise TypeError('scheduled physical exclusion requires its exact beta rule')
        _physical_model(self)

    @property
    def key(self):
        return (self.mass_x, self.mass_y, self.cross_coupling_gamma, self.beta_rule,
            self.friction_gamma, self.bath_temperature, self.family_id, self.target_x, self.target_y,
            self.decreasing_start, self.ramp_duration, self.autonomous_duration,
            self.initial_state_rule_id, self.preparation_rule_id)

    @classmethod
    def from_coordinate(cls, coordinate):
        return cls(coordinate.member.mass_x, coordinate.member.mass_y, coordinate.member.cross_coupling_gamma,
            coordinate.member.beta_rule, coordinate.primary_view.friction_gamma, coordinate.primary_view.bath_temperature,
            coordinate.family_id, coordinate.target_x, coordinate.target_y, coordinate.decreasing_start,
            coordinate.ramp_ticks * coordinate.primary_view.timestep,
            coordinate.autonomous_ticks * coordinate.primary_view.timestep,
            coordinate.initial_state_rule_id, coordinate.preparation_rule_id)


@dataclass(frozen=True, slots=True)
class MatrixFactorExposureCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-response/exposure-census'
    VERSION: ClassVar[str] = '2.0.0'
    census_id: str
    mandatory_floor: ObjectIdentity
    effective_seed_exclusions: tuple[int, ...]
    exposed_independent_groups: tuple[str, ...]
    exposed_regimes: tuple[str, ...]
    constant_physical_exclusions: tuple[MatrixConstantPhysicalExclusion, ...]
    scheduled_physical_exclusions: tuple[MatrixScheduledPhysicalExclusion, ...]
    exposed_artifact_sha256s: tuple[str, ...]
    factual_provenance: tuple[ArtifactIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.census_id)
        _seeds(self.effective_seed_exclusions)
        if (type(self.mandatory_floor) is not ObjectIdentity or self.mandatory_floor != MANDATORY_FLOOR_IDENTITY
                or not MANDATORY_EFFECTIVE_SEEDS.issubset(self.effective_seed_exclusions)):
            raise ValueError('Matrix exposure union omits or substitutes its immutable mandatory floor')
        for name in ('exposed_independent_groups', 'exposed_regimes', 'exposed_artifact_sha256s'):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        for digest in self.exposed_artifact_sha256s:
            validate_sha256(digest)
        for values, kind in ((self.constant_physical_exclusions, MatrixConstantPhysicalExclusion),
                (self.scheduled_physical_exclusions, MatrixScheduledPhysicalExclusion)):
            if type(values) is not tuple or any(type(value) is not kind for value in values):
                raise TypeError('Matrix exposure requires immutable exact typed physical exclusions')
            for value in values:
                value.__post_init__()
            if values != tuple(sorted(set(values), key=lambda value: value.fingerprint())):
                raise ValueError('Matrix physical exclusions repeat or reorder exact physical keys')
        if (type(self.factual_provenance) is not tuple or not self.factual_provenance
                or any(type(value) is not ArtifactIdentity for value in self.factual_provenance)
                or tuple(value.artifact_id for value in self.factual_provenance)
                    != tuple(sorted({value.artifact_id for value in self.factual_provenance}))):
            raise ValueError('Matrix exclusions require explicit unique content-pinned external factual provenance')
        for value in self.factual_provenance:
            value.__post_init__()
        required = {MANDATORY_FLOOR_SHA256, *(value.sha256 for value in self.factual_provenance)}
        if not required.issubset(self.exposed_artifact_sha256s):
            raise ValueError('Matrix exposure digests omit its mandatory floor or factual provenance')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.census_id, self)
