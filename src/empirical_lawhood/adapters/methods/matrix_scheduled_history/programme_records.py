# SPDX-License-Identifier: MPL-2.0
"""Frozen whole-programme scope and storage subdivisions, without authority.

An E4 wave is a subdivision of this record, never a smaller calibration study.
Original scientific subjects are references to the authenticated compact bank;
no oversized scientific graph is reconstructed from those references.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, require_sorted_unique_strings,
    validate_decimal, validate_sha256, validate_stable_id,
)

from .compact_records import ScheduledCompactBank, compact_identity
from .records import identity

NAMESPACE = 'matrix-scheduled-programme'
MAXIMUM_PROGRAMME_BYTES = 16 * 1024**2
MODES = {
    'E4_DEVELOPMENT': (MatrixProgrammeRole.DEVELOPMENT.value, 32),
    'E4_REVISION_CALIBRATION': (MatrixProgrammeRole.CALIBRATION.value, 64),
    'E4_CONFIRMATION': (MatrixProgrammeRole.CONFIRMATION.value, 64),
}


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeFactor(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/factor'
    factor_id: str
    scale: str
    low: Decimal
    center: Decimal
    high: Decimal

    def __post_init__(self):
        if self.factor_id not in ('temperature', 'friction', 'coupling') or self.scale not in ('LINEAR', 'LOG'):
            raise ValueError('programme requires the original three explicitly scaled factors')
        for name in ('low', 'center', 'high'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        if not 0 < self.low < self.center < self.high:
            raise ValueError('programme factors require distinct positive log or nonnegative linear levels')
        # Exact Decimal equalities preserve the prespecified symmetric grid.
        low, center, high = map(Fraction, (self.low, self.center, self.high))
        if (self.scale == 'LINEAR' and 2*center != low+high
                or self.scale == 'LOG' and center*center != low*high):
            raise ValueError('programme factors are not symmetric in their declared coordinates')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/case'
    VERSION: ClassVar[str] = '2.0.0'
    root_id: str
    independent_group_id: str
    family_id: str
    role: str
    source: ObjectIdentity
    coordinate: ObjectIdentity
    factor_values: tuple[Decimal, Decimal, Decimal]
    streams_sha256: str
    information_cutoff: InformationCutoff

    def __post_init__(self):
        for name in ('root_id', 'independent_group_id', 'family_id'):
            validate_stable_id(getattr(self, name))
        validate_sha256(self.streams_sha256)
        if (type(self.information_cutoff) is not InformationCutoff or self.information_cutoff.cutoff_id != 'cutoff.'+self.root_id
                or self.information_cutoff.phase is not CausalPhase.PRE_ACTION):
            raise ValueError('programme case changes its original absolute pre-action cutoff')
        if self.role not in {v.value for v in MatrixProgrammeRole} or len(self.factor_values) != 3:
            raise ValueError('programme case omits its original role or physical factors')
        for value in self.factor_values:
            validate_decimal(value, field_name='physical factor', minimum=Decimal(0))
        from .records import ScheduledSource
        if (self.source.object_schema, self.source.object_version) != (ScheduledSource.SCHEMA, ScheduledSource.VERSION):
            raise ValueError('programme case changes its exact current bounded source identity')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeWave(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/wave'
    wave_id: str
    group_ids: tuple[str, ...]
    root_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.wave_id)
        require_sorted_unique_strings(self.group_ids, field_name='whole wave groups', allow_empty=False)
        require_sorted_unique_strings(self.root_ids, field_name='complete wave cases', allow_empty=False)
        if len(self.group_ids) > 8 or len(self.root_ids) != 9*len(self.group_ids):
            raise ValueError('programme wave thins the nine cases of a whole matched group')


@dataclass(frozen=True, slots=True)
class ScheduledProgramme(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/programme'
    VERSION: ClassVar[str] = '2.0.0'
    programme_id: str
    mode: str
    bank: ObjectIdentity
    reservation: ObjectIdentity
    allocation: ObjectIdentity
    specification: ObjectIdentity
    forecast_design: ObjectIdentity
    response_selection: ObjectIdentity
    criterion: ObjectIdentity
    calibration_criterion: ObjectIdentity | None
    factors: tuple[ScheduledProgrammeFactor, ...]
    cases: tuple[ScheduledProgrammeCase, ...]
    source_census: tuple[ObjectIdentity, ...]
    waves: tuple[ScheduledProgrammeWave, ...]
    confidence: Decimal
    minimum_group_count: int

    def __post_init__(self):
        from .programme_roster import validate_programme_roster
        validate_programme_roster(self, bank_schema=ScheduledCompactBank.SCHEMA)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.programme_id, self)

    @property
    def group_ids(self):
        return tuple(sorted({c.independent_group_id for c in self.cases}))

    @property
    def order_statistic_rank(self):
        # ceil((n+1)*.95), once for the global roster; never per wave.
        value = (len(self.group_ids)+1)*Fraction(self.confidence)
        return (value.numerator+value.denominator-1)//value.denominator

    @classmethod
    def from_bank(cls, bank, *, programme_id, mode, wave_group_count=4,
            factor_scales=('LINEAR', 'LINEAR', 'LINEAR')):
        if type(bank) is not ScheduledCompactBank or type(wave_group_count) is not int or not 1 <= wave_group_count <= 8:
            raise ValueError('programme requires an authentic typed bank and one-to-eight whole groups per bounded wave')
        if mode not in MODES or len(factor_scales) != 3:
            raise ValueError('programme requires an explicit mode and three prespecified scales')
        if bank.response_selection is None:
            raise ValueError('E4 programme requires the complete original pulse selection')
        if Fraction(bank.forecast_design.population_alpha) != Fraction(1, 20):
            raise ValueError('E4 programme changes original nominal 95 percent pooled confidence')
        calibration_criterion = bank.response_selection.calibration_criterion
        if (mode == 'E4_REVISION_CALIBRATION' and (calibration_criterion is None
                or calibration_criterion.minimum_group_count != 64
                or calibration_criterion.required_family_ids != tuple(sorted(FOUR_FAMILY_PREPARATION_IDS)))):
            raise ValueError('E4 revision calibration changes original global minimum64/four-family criterion')
        selected = tuple(s for s in bank.sources if s.root_id in bank.selected_root_ids)
        coordinates = {c.coordinate_id: c for c in bank.reservation.allocation.coordinates}
        policies = {p.policy_id: p for p in bank.specification.selection.prefix_policies}
        coordinate_policies = dict(bank.specification.selection.coordinate_policies)
        cases = tuple(ScheduledProgrammeCase(s.root_id, s.root.root.independent_group_id,
            coordinates[s.root.root.coordinate_id].family_id, s.root.root.role.value, identity(s),
            s.root.coordinate, (coordinates[s.root.root.coordinate_id].primary_view.bath_temperature,
                coordinates[s.root.root.coordinate_id].primary_view.friction_gamma,
                coordinates[s.root.root.coordinate_id].member.cross_coupling_gamma),
            sha256(canonical_json_bytes(s.root.streams)).hexdigest(),
            InformationCutoff('cutoff.'+s.root_id, coordinates[s.root.root.coordinate_id].clock_id, CausalPhase.PRE_ACTION,
                coordinates[s.root.root.coordinate_id].physical_time(policies[coordinate_policies[s.root.coordinate].object_id].cutoff_tick))) for s in selected)
        levels = tuple(tuple(sorted({c.factor_values[i] for c in cases})) for i in range(3))
        if any(len(values) != 3 for values in levels):
            raise ValueError('E4 programme requires all original low/center/high physical levels')
        factors = tuple(ScheduledProgrammeFactor(name, scale, *values)
            for name, scale, values in zip(('temperature', 'friction', 'coupling'), factor_scales, levels, strict=True))
        groups = tuple(sorted({c.independent_group_id for c in cases}))
        waves = tuple(ScheduledProgrammeWave(f'{programme_id}.wave.{i//wave_group_count:03}', groups[i:i+wave_group_count],
            tuple(c.root_id for c in cases if c.independent_group_id in groups[i:i+wave_group_count]))
            for i in range(0, len(groups), wave_group_count))
        criterion = bank.response_selection.calibration_criterion
        return cls(programme_id, mode, compact_identity(bank), identity(bank.reservation), identity(bank.reservation.allocation),
            identity(bank.specification), identity(bank.forecast_design), bank.response_selection.identity,
            bank.forecast_design.criterion, criterion.identity if criterion is not None else None, factors, cases,
            tuple(identity(s) for s in bank.sources), waves, Decimal('.95'), MODES[mode][1])


def validate_programme_bank(programme, bank):
    """Authenticate exact shared bytes and the global source/protocol population."""
    if type(programme) is not ScheduledProgramme or type(bank) is not ScheduledCompactBank or compact_identity(bank) != programme.bank:
        raise ValueError('programme substitutes its original global compact bank')
    # Preserve arbitrary caller-selected bounded partitions while rebuilding
    # every scientific field from the exact authenticated original operands.
    rebuilt = ScheduledProgramme.from_bank(bank, programme_id=programme.programme_id, mode=programme.mode,
        wave_group_count=1, factor_scales=tuple(f.scale for f in programme.factors))
    from dataclasses import replace
    if replace(rebuilt, waves=programme.waves) != programme:
        raise ValueError('programme substitutes original sources, roles, factors, model or global selection identities')
    return bank
