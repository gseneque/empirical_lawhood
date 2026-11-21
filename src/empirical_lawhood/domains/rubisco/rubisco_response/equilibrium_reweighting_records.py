# SPDX-License-Identifier: MPL-2.0
"""Prospective complete-window, basin and joint resampling selections.

These records name numerical diagnostics and a conditional sampling model.
They do not grant equilibrium, chemical, biological or rate admission.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import math
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias import ReferenceBiasConvention
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import ReferenceBiasGeometryCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.contracts import UmbrellaWindow


def _number(value, name, *, positive=False):
    validate_decimal(value, field_name=name)
    if not math.isfinite(float(value)) or value != 0 and float(value) == 0 or positive and value <= 0:
        raise ValueError(name+' must be a representable finite Decimal'+(' greater than zero' if positive else ''))


def _roster(values, kind, field, *, nonempty=True):
    if type(values) is not tuple or nonempty and not values:
        raise ValueError('reweighting requires a complete immutable '+field+' census')
    for row in values:
        exact(row, kind)
    ids = tuple(getattr(row, field) for row in values)
    if ids != tuple(sorted(set(ids))):
        raise ValueError('reweighting requires sorted unique '+field+' values')


@dataclass(frozen=True, slots=True)
class EquilibriumBasin(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/equilibrium-basin'
    VERSION: ClassVar[str] = '1.0.0'
    basin_id: str
    lower: tuple[Decimal, ...]
    upper: tuple[Decimal, ...]

    def __post_init__(self):
        validate_stable_id(self.basin_id)
        if type(self.lower) is not tuple or type(self.upper) is not tuple or not self.lower or len(self.lower) != len(self.upper):
            raise ValueError('basin needs one explicit half-open interval per selected coordinate')
        for low, high in zip(self.lower, self.upper, strict=True):
            _number(low, 'basin lower endpoint')
            _number(high, 'basin upper endpoint')
            if low >= high or float(low) >= float(high):
                raise ValueError('basin interval must have positive resolved width')


@dataclass(frozen=True, slots=True)
class ReweightingEnsemble(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reweighting-ensemble'
    VERSION: ClassVar[str] = '1.0.0'
    ensemble_id: str
    prototype: ObjectIdentity
    temperature_kelvin: Decimal
    coordinate_window: UmbrellaWindow
    coordinate_convention: ReferenceBiasConvention
    basins: tuple[EquilibriumBasin, ...]

    def __post_init__(self):
        validate_stable_id(self.ensemble_id)
        exact(self.prototype, ObjectIdentity)
        if (self.prototype.object_schema != PeriodicProbeSelection.SCHEMA
                or self.prototype.object_version != PeriodicProbeSelection.VERSION):
            raise ValueError('ensemble requires its exact complete reference operator selection')
        _number(self.temperature_kelvin, 'ensemble temperature', positive=True)
        exact(self.coordinate_window, UmbrellaWindow)
        exact(self.coordinate_convention, ReferenceBiasConvention)
        if self.coordinate_convention.window != ObjectIdentity.from_record(self.coordinate_window.window_id, self.coordinate_window):
            raise ValueError('ensemble coordinate definition changes its original convention')
        _roster(self.basins, EquilibriumBasin, 'basin_id')
        dimension = len(self.coordinate_window.cv_kinds)
        if any(len(b.lower) != dimension for b in self.basins):
            raise ValueError('basin changes the complete selected coordinate denominator')
        for i, first in enumerate(self.basins):
            for second in self.basins[i+1:]:
                if all(a < d and c < b for a, b, c, d in zip(first.lower, first.upper, second.lower, second.upper, strict=True)):
                    raise ValueError('selected basins overlap and double-count probability')


@dataclass(frozen=True, slots=True)
class ReweightingTrace(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reweighting-trace'
    VERSION: ClassVar[str] = '1.0.0'
    trace_id: str
    ensemble_id: str
    configuration: ObjectIdentity
    resampling_group_id: str
    block_samples: int
    bias_geometry_criteria: ReferenceBiasGeometryCriteria | None

    def __post_init__(self):
        for value in (self.trace_id, self.ensemble_id, self.resampling_group_id):
            validate_stable_id(value)
        exact(self.configuration, ObjectIdentity)
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_operation import ReferenceEquilibriumConfig, AcceleratedReferenceEquilibriumConfig, ObservedElectronicEquilibriumConfig
        if (self.configuration.object_schema not in (ReferenceEquilibriumConfig.SCHEMA,
                AcceleratedReferenceEquilibriumConfig.SCHEMA, ObservedElectronicEquilibriumConfig.SCHEMA)
                or self.configuration.object_version != '1.0.0'):
            raise ValueError('reweighting trace needs its original equilibrium acquisition configuration')
        if type(self.block_samples) is not int or self.block_samples <= 0:
            raise ValueError('reweighting needs an explicit positive circular block length')
        if self.bias_geometry_criteria is not None:
            exact(self.bias_geometry_criteria, ReferenceBiasGeometryCriteria)


@dataclass(frozen=True, slots=True)
class BasinContrastTerm(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/basin-contrast-term'
    VERSION: ClassVar[str] = '1.0.0'
    ensemble_id: str
    basin_id: str
    coefficient: Decimal

    def __post_init__(self):
        validate_stable_id(self.ensemble_id)
        validate_stable_id(self.basin_id)
        _number(self.coefficient, 'basin contrast coefficient')
        if self.coefficient == 0:
            raise ValueError('zero contrast terms cannot obscure the actual operand census')


@dataclass(frozen=True, slots=True)
class BasinFreeEnergyContrast(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/basin-free-energy-contrast'
    VERSION: ClassVar[str] = '1.0.0'
    contrast_id: str
    terms: tuple[BasinContrastTerm, ...]

    def __post_init__(self):
        validate_stable_id(self.contrast_id)
        if type(self.terms) is not tuple or len(self.terms) < 2:
            raise ValueError('a free-energy contrast needs its complete signed operands')
        for term in self.terms:
            exact(term, BasinContrastTerm)
        keys = tuple((r.ensemble_id, r.basin_id) for r in self.terms)
        if keys != tuple(sorted(set(keys))):
            raise ValueError('contrast terms must be sorted and unique')
        for ensemble in {r.ensemble_id for r in self.terms}:
            if sum((Fraction(r.coefficient) for r in self.terms if r.ensemble_id == ensemble), Fraction(0)) != 0:
                raise ValueError('contrast must cancel each ensemble free-energy gauge separately')


@dataclass(frozen=True, slots=True)
class EquilibriumReweightingCriteria(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/equilibrium-reweighting-criteria'
    VERSION: ClassVar[str] = '1.0.0'
    criteria_id: str
    solver_tolerance: Decimal
    solver_maximum_iterations: int
    minimum_window_weight_ess: Decimal
    minimum_target_weight_ess: Decimal
    minimum_overlap: Decimal
    minimum_blocks: int
    block_inefficiency_multiplier: Decimal
    maximum_split_contrast_kj_mol: Decimal
    bootstrap_replicates: int
    bootstrap_seed: int
    simultaneous_coverage: Decimal
    maximum_workspace_bytes: int

    def __post_init__(self):
        validate_stable_id(self.criteria_id)
        for name in ('solver_tolerance', 'minimum_window_weight_ess', 'minimum_target_weight_ess',
                'minimum_overlap', 'block_inefficiency_multiplier', 'simultaneous_coverage'):
            _number(getattr(self, name), name, positive=True)
        _number(self.maximum_split_contrast_kj_mol, 'maximum split contrast')
        if (self.maximum_split_contrast_kj_mol < 0 or self.minimum_overlap >= 1
                or self.simultaneous_coverage >= 1 or self.block_inefficiency_multiplier < 1):
            raise ValueError('reweighting thresholds change their probability or block interpretation')
        for name, minimum in (('solver_maximum_iterations', 1), ('minimum_blocks', 2),
                ('bootstrap_replicates', 2), ('maximum_workspace_bytes', 1)):
            if type(getattr(self, name)) is not int or getattr(self, name) < minimum:
                raise ValueError('reweighting requires an explicit positive '+name)
        if type(self.bootstrap_seed) is not int or not 0 <= self.bootstrap_seed < 2**128:
            raise ValueError('reweighting needs its exact PCG64DXSM resampling seed')


@dataclass(frozen=True, slots=True)
class EquilibriumReweightingSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/equilibrium-reweighting-selection'
    VERSION: ClassVar[str] = '1.0.0'
    selection_id: str
    ensembles: tuple[ReweightingEnsemble, ...]
    traces: tuple[ReweightingTrace, ...]
    contrasts: tuple[BasinFreeEnergyContrast, ...]
    criteria: EquilibriumReweightingCriteria
    dependence_basis: ObjectIdentity
    assumptions: tuple[str, ...]
    scope: str = 'CONDITIONAL_EQUILIBRIUM_STATISTICS_WITHOUT_CHEMICAL_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        _roster(self.ensembles, ReweightingEnsemble, 'ensemble_id')
        _roster(self.traces, ReweightingTrace, 'trace_id')
        _roster(self.contrasts, BasinFreeEnergyContrast, 'contrast_id')
        exact(self.criteria, EquilibriumReweightingCriteria)
        exact(self.dependence_basis, ObjectIdentity)
        if (type(self.assumptions) is not tuple or not self.assumptions
                or any(type(s) is not str or not s.strip() for s in self.assumptions)
                or self.scope != 'CONDITIONAL_EQUILIBRIUM_STATISTICS_WITHOUT_CHEMICAL_OR_RATE_ADMISSION'):
            raise ValueError('reweighting must preserve its declared dependence assumptions and evidence ceiling')
        ids = {r.ensemble_id for r in self.ensembles}
        if {r.ensemble_id for r in self.traces} != ids or len({r.configuration for r in self.traces}) != len(self.traces):
            raise ValueError('reweighting omits an ensemble or repeats an original acquisition')
        basins = {(r.ensemble_id, b.basin_id) for r in self.ensembles for b in r.basins}
        if any((t.ensemble_id, t.basin_id) not in basins for c in self.contrasts for t in c.terms):
            raise ValueError('contrast names an unselected ensemble or basin')
        groups = {}
        for trace in self.traces:
            if groups.setdefault(trace.resampling_group_id, trace.block_samples) != trace.block_samples:
                raise ValueError('one declared dependence group must retain one shared block length')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class EquilibriumReweightingEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/equilibrium-reweighting-evidence'
    VERSION: ClassVar[str] = '1.0.0'
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
        if (self.selection.object_schema != EquilibriumReweightingSelection.SCHEMA
                or self.selection.object_version != EquilibriumReweightingSelection.VERSION
                or self.array_artifact.payload_schema != 'empirical-lawhood/source/checksummed-uninterpreted-public-bytes'
                or self.array_artifact.media_type != 'application/zip' or self.readout.relative_path != 'readout.json'
                or self.cost_scope != 'ORIGINAL_READ_AND_ANALYSIS_EXCLUDING_ENVIRONMENT_CAPTURE_AND_PUBLICATION'):
            raise ValueError('reweighting evidence changes its exact interpretation or physical carriers')
        if type(self.original_results) is not tuple or any(type(p) is not ObjectIdentity for p in self.original_results):
            raise ValueError('reweighting evidence requires its exact original result census')
        if tuple(p.object_id for p in self.original_results) != tuple(sorted({p.object_id for p in self.original_results})):
            raise ValueError('reweighting evidence repeats or reorders original results')
        references = tuple(sorted((self.selection, self.provenance.identity, *self.original_results), key=lambda p:p.object_id))
        if self.arrays.scientific_references != references:
            raise ValueError('reweighting arrays lose original results, source or selection')
        for value in (self.analysis_cpu_seconds, self.analysis_wall_seconds):
            _number(value, 'original analysis cost')
            if value < 0:
                raise ValueError('original analysis cost cannot be negative')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evidence_id, self)
