# SPDX-License-Identifier: MPL-2.0
"""Exact weights, physical event definitions and complete original path rosters.

Selections define conditional path observables, not a qualified entry ensemble,
physical rate, memoryless reduction or biological independent unit.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import gcd, isfinite
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection


def roster(rows, kind, field, *, allow_empty=False):
    if type(rows) is not tuple or not rows and not allow_empty:
        raise ValueError('first passage requires its complete immutable '+field+' census')
    for row in rows:
        exact(row, kind)
    keys = tuple(getattr(row, field) for row in rows)
    if keys != tuple(sorted(set(keys))):
        raise ValueError('first passage requires sorted unique '+field+' values')


def decimal_number(value, field, *, positive=False):
    validate_decimal(value, field_name=field)
    if not isfinite(float(value)) or value != 0 and float(value) == 0 or positive and value <= 0:
        raise ValueError('first passage requires a representable finite '+field)


@dataclass(frozen=True, slots=True)
class PathWeight(CanonicalRecord):
    """An exact positive probability, including nonterminating decimal splits."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/path-weight'
    VERSION: ClassVar[str] = '1.0.0'
    numerator: int
    denominator: int

    def __post_init__(self):
        if (type(self.numerator) is not int or type(self.denominator) is not int
                or not 0 < self.numerator <= self.denominator or gcd(self.numerator, self.denominator) != 1):
            raise ValueError('path probability must be a reduced positive rational no greater than one')

    @property
    def fraction(self):
        return Fraction(self.numerator, self.denominator)

    @classmethod
    def from_fraction(cls, value):
        if type(value) is not Fraction:
            raise TypeError('path weights require exact rational input')
        return cls(value.numerator, value.denominator)


@dataclass(frozen=True, slots=True)
class PassageRegion(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/passage-region'
    VERSION: ClassVar[str] = '1.0.0'
    region_id: str
    lower: tuple[Decimal, ...]
    upper: tuple[Decimal, ...]

    def __post_init__(self):
        validate_stable_id(self.region_id)
        if type(self.lower) is not tuple or type(self.upper) is not tuple or not self.lower or len(self.lower) != len(self.upper):
            raise ValueError('passage region requires one half-open interval per coordinate')
        for low, high in zip(self.lower, self.upper, strict=True):
            decimal_number(low, 'lower region boundary')
            decimal_number(high, 'upper region boundary')
            if low >= high or float(low) >= float(high):
                raise ValueError('passage region must have positive resolved width')


@dataclass(frozen=True, slots=True)
class PassageEvent(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/passage-event'
    VERSION: ClassVar[str] = '1.0.0'
    event_id: str
    region: PassageRegion
    role: str
    residence_steps: int
    physical_definition: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.event_id)
        exact(self.region, PassageRegion)
        exact(self.physical_definition, ObjectIdentity)
        if (self.role not in {'PRODUCTIVE', 'REVERSE', 'ASSOCIATION', 'DISSOCIATION', 'RELEASE', 'SUBSTRATE_READY', 'OTHER'}
                or type(self.residence_steps) is not int or self.residence_steps < 0):
            raise ValueError('passage event requires an explicit physical role and nonnegative residence horizon')


@dataclass(frozen=True, slots=True)
class PassageEnsemble(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/passage-ensemble'
    VERSION: ClassVar[str] = '1.0.0'
    ensemble_id: str
    prototype: ObjectIdentity
    coordinate_window: UmbrellaWindow
    coordinate_convention: ReferenceBiasConvention
    entry_region: PassageRegion
    events: tuple[PassageEvent, ...]
    entry_distribution_source: ObjectIdentity
    dissolved_gas_uM: Decimal | None
    concentration_source: ObjectIdentity | None
    dynamics_model: str = 'NVE'
    temperature_kelvin: Decimal | None = None
    friction_per_picosecond: Decimal | None = None

    def __post_init__(self):
        validate_stable_id(self.ensemble_id)
        for value in (self.prototype, self.entry_distribution_source):
            exact(value, ObjectIdentity)
        if (self.prototype.object_schema != PeriodicProbeSelection.SCHEMA
                or self.prototype.object_version != PeriodicProbeSelection.VERSION):
            raise ValueError('passage ensemble needs its exact complete reference operator')
        exact(self.coordinate_window, UmbrellaWindow)
        exact(self.coordinate_convention, ReferenceBiasConvention)
        exact(self.entry_region, PassageRegion)
        if self.coordinate_convention.window != ObjectIdentity.from_record(self.coordinate_window.window_id, self.coordinate_window):
            raise ValueError('passage coordinate definition changes its exact image convention')
        roster(self.events, PassageEvent, 'event_id')
        regions = (self.entry_region, *(event.region for event in self.events))
        if (len({r.region_id for r in regions}) != len(regions)
                or any(len(r.lower) != len(self.coordinate_window.cv_kinds) for r in regions)):
            raise ValueError('passage events change the selected coordinate or region census')
        for index, first in enumerate(regions):
            for second in regions[index+1:]:
                if all(a < d and c < b for a,b,c,d in zip(first.lower, first.upper, second.lower, second.upper, strict=True)):
                    raise ValueError('overlapping passage regions make first-exit classification ambiguous')
        if (self.dissolved_gas_uM is None) != (self.concentration_source is None):
            raise ValueError('dissolved gas concentration and its source must be supplied together')
        if self.dissolved_gas_uM is not None:
            decimal_number(self.dissolved_gas_uM, 'free dissolved gas concentration', positive=True)
            exact(self.concentration_source, ObjectIdentity)
        if self.dynamics_model not in {'NVE','DECLARED_UNBIASED_LANGEVIN'}:
            raise ValueError('first passage requires its explicit unbiased dynamical model')
        if self.dynamics_model == 'NVE':
            if self.temperature_kelvin is not None or self.friction_per_picosecond is not None:
                raise ValueError('NVE paths cannot acquire an undeclared bath or friction')
        else:
            decimal_number(self.temperature_kelvin, 'dynamical bath temperature', positive=True)
            decimal_number(self.friction_per_picosecond, 'dynamical bath friction', positive=True)


@dataclass(frozen=True, slots=True)
class FirstPassagePath(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/first-passage-path'
    VERSION: ClassVar[str] = '1.0.0'
    path_id: str
    ensemble_id: str
    configuration: ObjectIdentity
    run_id: str
    preparation_id: str
    site_id: str
    entry_history_id: str
    weight: PathWeight

    def __post_init__(self):
        for value in (self.path_id, self.ensemble_id, self.run_id, self.preparation_id, self.site_id, self.entry_history_id):
            validate_stable_id(value)
        exact(self.configuration, ObjectIdentity)
        exact(self.weight, PathWeight)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_operation import ReferenceTrajectoryConfig, AcceleratedReferenceTrajectoryConfig
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_operation import ReferenceEquilibriumConfig, AcceleratedReferenceEquilibriumConfig
        if (self.configuration.object_schema not in (ReferenceTrajectoryConfig.SCHEMA, AcceleratedReferenceTrajectoryConfig.SCHEMA,
                ReferenceEquilibriumConfig.SCHEMA, AcceleratedReferenceEquilibriumConfig.SCHEMA)
                or self.configuration.object_version != '1.0.0'):
            raise ValueError('first passage requires its original unbiased trajectory configuration')


@dataclass(frozen=True, slots=True)
class FirstPassageSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/first-passage-selection'
    VERSION: ClassVar[str] = '1.0.0'
    selection_id: str
    ensembles: tuple[PassageEnsemble, ...]
    paths: tuple[FirstPassagePath, ...]
    dependence_basis: ObjectIdentity
    assumptions: tuple[str, ...]
    maximum_projection_bytes: int
    scope: str = 'CONDITIONAL_PHYSICAL_FIRST_PASSAGES_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        roster(self.ensembles, PassageEnsemble, 'ensemble_id')
        roster(self.paths, FirstPassagePath, 'path_id')
        exact(self.dependence_basis, ObjectIdentity)
        if ({p.ensemble_id for p in self.paths} != {e.ensemble_id for e in self.ensembles}
                or len({p.configuration for p in self.paths}) != len(self.paths)):
            raise ValueError('first passage repeats an acquisition or omits a selected ensemble')
        if (type(self.assumptions) is not tuple or not self.assumptions
                or any(type(a) is not str or not a.strip() for a in self.assumptions)
                or type(self.maximum_projection_bytes) is not int or self.maximum_projection_bytes <= 0
                or self.scope != 'CONDITIONAL_PHYSICAL_FIRST_PASSAGES_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'):
            raise ValueError('first passage needs its dependence assumptions, projection allocation and evidence ceiling')
        groups = {(p.ensemble_id, p.run_id) for p in self.paths}
        for ensemble, run in groups:
            if sum((p.weight.fraction for p in self.paths if (p.ensemble_id, p.run_id) == (ensemble, run)), Fraction()) != 1:
                raise ValueError('every selected run must preserve unit total initial probability')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class WeightedPathState(CanonicalRecord):
    """A complete path history and phase boundary for one declared WE run."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/weighted-path-state'
    VERSION: ClassVar[str] = '1.0.0'
    path_id: str
    ensemble_id: str
    run_id: str
    bin_id: str
    weight: PathWeight
    phase: ObjectIdentity
    history: tuple[ObjectIdentity, ...]
    physical_step: int
    disposition: str

    def __post_init__(self):
        for value in (self.path_id, self.ensemble_id, self.run_id, self.bin_id):
            validate_stable_id(value)
        exact(self.weight, PathWeight)
        exact(self.phase, ObjectIdentity)
        if type(self.history) is not tuple or not self.history or any(type(p) is not ObjectIdentity for p in self.history):
            raise ValueError('weighted resampling must preserve the complete ordered path history')
        if (type(self.physical_step) is not int or self.physical_step < 0
                or self.disposition not in {'ACTIVE', 'ABSORBED', 'CENSORED', 'FAILED', 'MISSING'}):
            raise ValueError('weighted path state changes its physical clock or terminal disposition')


@dataclass(frozen=True, slots=True)
class WeightedResamplingSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/weighted-resampling-selection'
    VERSION: ClassVar[str] = '1.0.0'
    selection_id: str
    bin_ids: tuple[str, ...]
    offspring_per_occupied_bin: tuple[int, ...]
    seed: int
    maximum_integer_bits: int
    rule: str = 'INDEPENDENT_MULTINOMIAL_PER_RUN_AND_BIN_EXACT_RATIONAL_WEIGHTS'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        if type(self.bin_ids) is not tuple or not self.bin_ids or self.bin_ids != tuple(sorted(set(self.bin_ids))):
            raise ValueError('weighted resampling requires the complete unique ordered bin census')
        for value in self.bin_ids:
            validate_stable_id(value)
        if (type(self.offspring_per_occupied_bin) is not tuple
                or len(self.offspring_per_occupied_bin) != len(self.bin_ids)
                or any(type(n) is not int or n <= 0 for n in self.offspring_per_occupied_bin)
                or type(self.seed) is not int or not 0 <= self.seed < 2**128
                or type(self.maximum_integer_bits) is not int or self.maximum_integer_bits < 64
                or self.rule != 'INDEPENDENT_MULTINOMIAL_PER_RUN_AND_BIN_EXACT_RATIONAL_WEIGHTS'):
            raise ValueError('weighted resampling requires explicit counts, PCG64DXSM seed and integer allocation')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class FirstPassageEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/first-passage-evidence'
    VERSION: ClassVar[str] = '1.0.0'
    SELECTION_KIND: ClassVar[type] = FirstPassageSelection
    evidence_id: str
    selection: ObjectIdentity
    provenance: NumericalProducingProvenance
    arrays: ArrayDatasetManifest
    array_artifact: ArtifactIdentity
    readout: FileEvidence
    original_results: tuple[ObjectIdentity, ...]
    analysis_cpu_seconds: Decimal
    analysis_wall_seconds: Decimal
    cost_scope: str = 'ORIGINAL_READ_AND_ANALYSIS_EXCLUDING_ENVIRONMENT_CAPTURE_AND_PUBLICATION'

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        for value, kind in ((self.selection, ObjectIdentity), (self.provenance, NumericalProducingProvenance),
                (self.arrays, ArrayDatasetManifest), (self.array_artifact, ArtifactIdentity), (self.readout, FileEvidence)):
            exact(value, kind)
        if (self.selection.object_schema != self.SELECTION_KIND.SCHEMA
                or self.selection.object_version != self.SELECTION_KIND.VERSION
                or self.array_artifact.payload_schema != 'empirical-lawhood/source/checksummed-uninterpreted-public-bytes'
                or self.array_artifact.media_type != 'application/zip' or self.readout.relative_path != 'readout.json'
                or self.cost_scope != 'ORIGINAL_READ_AND_ANALYSIS_EXCLUDING_ENVIRONMENT_CAPTURE_AND_PUBLICATION'):
            raise ValueError('first-passage evidence changes its exact interpretation or physical carriers')
        if type(self.original_results) is not tuple or any(type(p) is not ObjectIdentity for p in self.original_results):
            raise ValueError('first-passage evidence requires its exact original result census')
        if tuple(p.object_id for p in self.original_results) != tuple(sorted({p.object_id for p in self.original_results})):
            raise ValueError('first-passage evidence repeats or reorders original results')
        references = tuple(sorted((self.selection, self.provenance.identity, *self.original_results), key=lambda p:p.object_id))
        if self.arrays.scientific_references != references:
            raise ValueError('first-passage arrays lose original results, source or selection')
        for value in (self.analysis_cpu_seconds, self.analysis_wall_seconds):
            decimal_number(value, 'original analysis cost')
            if value < 0:
                raise ValueError('original analysis cost cannot be negative')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evidence_id, self)
