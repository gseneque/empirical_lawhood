# SPDX-License-Identifier: MPL-2.0
"""Prospective finite-slab classical flux and complete shooting contracts.

A finite slab approximates the dividing delta measure. Its width, coordinate,
physical step and plateau checks remain explicit; no exact surface or physical
rate is manufactured by the record type.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_records import EquilibriumReweightingSelection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_bias_assessment import ReferenceBiasGeometryCriteria, validate_bias_geometry_criteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics_assessment import ReferenceTrajectoryCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_trajectory_selection import ReferenceTrajectorySelection
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageEvidence, decimal_number, roster
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_records import identifiers


@dataclass(frozen=True, slots=True)
class ReactiveFluxSurface(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reactive-flux-surface'
    surface_id: str
    ensemble_id: str
    coordinate_axis: int
    center: Decimal
    half_width: Decimal
    orientation: int
    reactant_basin_id: str
    product_basin_id: str
    physical_quantity: ObjectIdentity
    state_definition: ObjectIdentity
    geometry_criteria: ReferenceBiasGeometryCriteria

    def __post_init__(self):
        for name in ('surface_id', 'ensemble_id', 'reactant_basin_id', 'product_basin_id'):
            validate_stable_id(getattr(self, name))
        if (type(self.coordinate_axis) is not int or self.coordinate_axis < 0
                or type(self.orientation) is not int or self.orientation not in (-1, 1)
                or self.reactant_basin_id == self.product_basin_id):
            raise ValueError('flux surface requires an oriented coordinate and distinct stable basins')
        decimal_number(self.center, 'dividing coordinate')
        decimal_number(self.half_width, 'finite slab half-width', positive=True)
        if float(Fraction(self.center)-Fraction(self.half_width)) >= float(Fraction(self.center)+Fraction(self.half_width)):
            raise ValueError('dividing slab must retain numerically resolved endpoints')
        exact(self.physical_quantity, ObjectIdentity)
        exact(self.state_definition, ObjectIdentity)
        exact(self.geometry_criteria, ReferenceBiasGeometryCriteria)


@dataclass(frozen=True, slots=True)
class ReactiveFluxCriteria(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reactive-flux-criteria'
    criteria_id: str
    minimum_slab_configurations: int
    minimum_slab_weight_ess: Decimal
    maximum_positive_flux_relative_error: Decimal
    maximum_plateau_relative_range: Decimal
    maximum_uncommitted_probability: Decimal
    maximum_committor_rms_deviation: Decimal
    maximum_step_log_rate_change: Decimal
    maximum_arithmetic_relative_error: Decimal

    def __post_init__(self):
        validate_stable_id(self.criteria_id)
        if type(self.minimum_slab_configurations) is not int or self.minimum_slab_configurations < 2:
            raise ValueError('flux assessment needs an explicit multiple-configuration denominator')
        for name in ('minimum_slab_weight_ess', 'maximum_positive_flux_relative_error',
                'maximum_plateau_relative_range', 'maximum_step_log_rate_change', 'maximum_arithmetic_relative_error'):
            decimal_number(getattr(self, name), name, positive=True)
        for name in ('maximum_uncommitted_probability', 'maximum_committor_rms_deviation'):
            decimal_number(getattr(self, name), name)
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError('flux probability and committor limits require explicit unit-interval values')
        if self.minimum_slab_weight_ess < 1:
            raise ValueError('flux weight support cannot require less than one effective configuration')


@dataclass(frozen=True, slots=True)
class ReactiveFluxControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reactive-flux-control'
    control_id: str
    kind: str
    surface_ids: tuple[str, ...]
    correspondence: ObjectIdentity
    maximum_log_rate_change: Decimal

    def __post_init__(self):
        validate_stable_id(self.control_id)
        if self.kind not in ('SLAB_WIDTH', 'ALTERNATIVE_COORDINATE'):
            raise ValueError('flux control requires an actual width or coordinate alternative')
        identifiers(self.surface_ids, 'flux control surfaces', minimum=2)
        exact(self.correspondence, ObjectIdentity)
        decimal_number(self.maximum_log_rate_change, 'flux control log-rate limit', positive=True)


@dataclass(frozen=True, slots=True)
class ReactiveFluxRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reactive-flux-rule'
    rule_id: str
    equilibrium: EquilibriumReweightingSelection
    surfaces: tuple[ReactiveFluxSurface, ...]
    dynamics: tuple[ReferenceDynamicsSettings, ...]
    primary_dynamics_id: str
    trajectory_criteria: ReferenceTrajectoryCriteria
    plateau_times_seconds: tuple[Decimal, ...]
    momentum_pairs_per_configuration: int
    momentum_seed: int
    criteria: ReactiveFluxCriteria
    controls: tuple[ReactiveFluxControl, ...]
    density_guess_policy: str
    maximum_preparation_bytes: int
    maximum_analysis_bytes: int
    assumptions: tuple[str, ...]
    momentum_law: str = 'INDEPENDENT_CARTESIAN_MAXWELL_NATURAL_MASSES_ANTITHETIC_PAIRS'
    scope: str = 'FINITE_SLAB_CLASSICAL_FLUX_WITHOUT_PHYSICAL_OR_BIOLOGICAL_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.rule_id)
        exact(self.equilibrium, EquilibriumReweightingSelection)
        roster(self.surfaces, ReactiveFluxSurface, 'surface_id')
        roster(self.dynamics, ReferenceDynamicsSettings, 'settings_id')
        roster(self.controls, ReactiveFluxControl, 'control_id', allow_empty=True)
        exact(self.trajectory_criteria, ReferenceTrajectoryCriteria)
        exact(self.criteria, ReactiveFluxCriteria)
        ensembles = {e.ensemble_id: e for e in self.equilibrium.ensembles}
        if {s.ensemble_id for s in self.surfaces} != set(ensembles):
            raise ValueError('flux rule must retain a surface for every original equilibrium ensemble')
        for surface in self.surfaces:
            ensemble = ensembles[surface.ensemble_id]
            axis = surface.coordinate_axis
            if axis >= len(ensemble.coordinate_window.cv_kinds):
                raise ValueError('flux surface changes the selected coordinate denominator')
            # A global side indicator on a periodic angle has a second cut.
            # This version refuses that topology instead of ignoring its flux.
            if ensemble.coordinate_window.cv_kinds[axis] == 'IMPROPER_DIHEDRAL':
                raise ValueError('a periodic torsion needs an explicit two-cut flux successor')
            validate_bias_geometry_criteria(surface.geometry_criteria, ensemble.coordinate_window, ensemble.coordinate_convention)
            basins = {b.basin_id: b for b in ensemble.basins}
            if not {surface.reactant_basin_id, surface.product_basin_id}.issubset(basins):
                raise ValueError('flux surface substitutes its original stable-basin denominator')
            reactant, product = basins[surface.reactant_basin_id], basins[surface.product_basin_id]
            s, c, h = surface.orientation, Fraction(surface.center), Fraction(surface.half_width)
            arange = sorted(s*(Fraction(v)-c) for v in (reactant.lower[axis], reactant.upper[axis]))
            brange = sorted(s*(Fraction(v)-c) for v in (product.lower[axis], product.upper[axis]))
            if arange[-1] > -h or brange[0] < h:
                raise ValueError('flux stable basins must lie on opposite sides outside the complete slab')
        if (len(self.dynamics) < 2 or len({d.step_seconds for d in self.dynamics}) != len(self.dynamics)
                or len({Fraction(d.step_seconds)*d.steps for d in self.dynamics}) != 1
                or self.primary_dynamics_id not in {d.settings_id for d in self.dynamics}):
            raise ValueError('flux requires distinct physical steps with one complete common horizon')
        times = self.plateau_times_seconds
        if type(times) is not tuple or len(times) < 3 or times != tuple(sorted(set(times))):
            raise ValueError('flux plateau requires at least three prospective physical times')
        for value in times:
            decimal_number(value, 'flux plateau time', positive=True)
            if any(Fraction(value)/Fraction(d.step_seconds) > d.steps
                    or (Fraction(value)/Fraction(d.step_seconds)).denominator != 1 for d in self.dynamics):
                raise ValueError('flux plateau times must lie on every original complete physical grid')
        if (type(self.momentum_pairs_per_configuration) is not int or self.momentum_pairs_per_configuration < 1
                or type(self.momentum_seed) is not int or not 0 <= self.momentum_seed < 2**128
                or self.density_guess_policy not in ('COLD', 'PREVIOUS_SUCCESSFUL_RKS')
                or self.momentum_law != 'INDEPENDENT_CARTESIAN_MAXWELL_NATURAL_MASSES_ANTITHETIC_PAIRS'
                or self.scope != 'FINITE_SLAB_CLASSICAL_FLUX_WITHOUT_PHYSICAL_OR_BIOLOGICAL_ADMISSION'):
            raise ValueError('flux changes its explicit phase law, density policy or conditional scope')
        for value in (self.maximum_preparation_bytes, self.maximum_analysis_bytes):
            if type(value) is not int or value <= 0:
                raise ValueError('flux requires explicit finite preparation and analysis allocations')
        if type(self.assumptions) is not tuple or not self.assumptions or any(type(s) is not str or not s.strip() for s in self.assumptions):
            raise ValueError('flux requires its declared ensemble, classical-nuclear and kinetic assumptions')
        surfaces = {s.surface_id: s for s in self.surfaces}
        for control in self.controls:
            if not set(control.surface_ids).issubset(surfaces):
                raise ValueError('flux control names an unselected surface')
            rows = tuple(surfaces[k] for k in control.surface_ids)
            if len({(s.ensemble_id, s.reactant_basin_id, s.product_basin_id,
                    s.state_definition, s.physical_quantity) for s in rows}) != 1:
                raise ValueError('flux control changes the original operator, physical quantity or stable states')
            coordinate = {(s.coordinate_axis, s.center, s.orientation) for s in rows}
            if control.kind == 'SLAB_WIDTH' and (len(coordinate) != 1 or len({s.half_width for s in rows}) != len(rows)):
                raise ValueError('width control must vary only the actual slab width')
            if control.kind == 'ALTERNATIVE_COORDINATE' and len({s.coordinate_axis for s in rows}) < 2:
                raise ValueError('coordinate control must change the actual coordinate, not only its dividing location')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.rule_id, self)


@dataclass(frozen=True, slots=True)
class ReactiveFluxPhaseSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reactive-flux-phase-source'
    rule: ObjectIdentity
    original: ObjectIdentity
    trace_id: str
    sample_ordinal: int
    original_step: int
    coordinate_sha256: str
    mass_sha256: str
    momentum_pair: int
    momentum_sign: int
    derived_seed: int
    normal_sha256: str
    velocity_sha256: str
    numpy_version: str
    temperature_kelvin: Decimal

    def __post_init__(self):
        exact(self.rule, ObjectIdentity)
        exact(self.original, ObjectIdentity)
        validate_stable_id(self.trace_id)
        if (any(type(v) is not int or v < 1 for v in (self.sample_ordinal, self.original_step))
                or type(self.momentum_pair) is not int or self.momentum_pair < 0
                or type(self.momentum_sign) is not int or self.momentum_sign not in (-1, 1)
                or type(self.derived_seed) is not int or not 0 <= self.derived_seed < 2**128
                or type(self.numpy_version) is not str or not self.numpy_version):
            raise ValueError('flux phase source loses its exact sample or declared thermal draw')
        for name in ('coordinate_sha256', 'mass_sha256', 'normal_sha256', 'velocity_sha256'):
            validate_sha256(getattr(self, name))
        decimal_number(self.temperature_kelvin, 'momentum-law temperature', positive=True)

    @property
    def identity(self):
        return ObjectIdentity.from_record('source.reactive-flux-phase.'+self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class PreparedReactiveFluxShot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/prepared-reactive-flux-shot'
    shot_id: str
    phase_source: ReactiveFluxPhaseSource
    selection: ReferenceTrajectorySelection
    surface_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.shot_id)
        exact(self.phase_source, ReactiveFluxPhaseSource)
        exact(self.selection, ReferenceTrajectorySelection)
        identifiers(self.surface_ids, 'shared flux surfaces')
        if self.selection.phase_source != self.phase_source.identity:
            raise ValueError('flux trajectory loses its actual original configuration and thermal phase source')


@dataclass(frozen=True, slots=True)
class PreparedReactiveFlux(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/prepared-reactive-flux'
    preparation_id: str
    rule: ReactiveFluxRule
    assessor_source: ObjectIdentity
    original_results: tuple[ObjectIdentity, ...]
    complete_equilibrium_census: bool
    shots: tuple[PreparedReactiveFluxShot, ...]

    def __post_init__(self):
        validate_stable_id(self.preparation_id)
        exact(self.rule, ReactiveFluxRule)
        exact(self.assessor_source, ObjectIdentity)
        identities(self.original_results, allow_empty=True)
        roster(self.shots, PreparedReactiveFluxShot, 'shot_id', allow_empty=True)
        if type(self.complete_equilibrium_census) is not bool or not self.complete_equilibrium_census and self.shots:
            raise ValueError('incomplete equilibrium custody cannot silently prepare a successful subset')
        if any(s.phase_source.rule != self.rule.identity for s in self.shots):
            raise ValueError('flux shot changes its prospective preparation rule')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.preparation_id, self)


@dataclass(frozen=True, slots=True)
class ReactiveFluxEvidence(FirstPassageEvidence):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reactive-flux-evidence'
    SELECTION_KIND: ClassVar[type] = ReactiveFluxRule
