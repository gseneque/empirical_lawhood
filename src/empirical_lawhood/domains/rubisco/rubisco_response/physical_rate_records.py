# SPDX-License-Identifier: MPL-2.0
"""Prospective constant-hazard reduction of complete physical path populations.

These contracts select quantitative model checks and whole-run resampling.
They do not certify independence, a physical entry distribution or a bath.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageEvidence, FirstPassageSelection, decimal_number, roster
from empirical_lawhood.domains.rubisco.rubisco_response.physical_gas_concentration import PeriodicGasConcentration
from empirical_lawhood.domains.rubisco.rubisco_response.weighted_path_population import WeightedPathCampaign


def identifiers(values, field, *, minimum=1):
    if type(values) is not tuple or len(values) < minimum or values != tuple(sorted(set(values))):
        raise ValueError('physical rate requires sorted unique '+field)
    for value in values:
        validate_stable_id(value)


def initial_passages(selection):
    if type(selection) is FirstPassageSelection:
        return selection
    if type(selection) is WeightedPathCampaign:
        return selection.initial_rule.initial_passages
    raise TypeError('physical rate requires original first passages or a complete weighted campaign')


@dataclass(frozen=True, slots=True)
class PhysicalRateCriteria(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-criteria'
    VERSION: ClassVar[str] = '1.0.0'
    criteria_id: str
    minimum_run_groups: int
    minimum_event_probability: Decimal
    minimum_at_risk_probability: Decimal
    maximum_cumulative_probability_error: Decimal
    maximum_dwell_log_rate_change: Decimal
    maximum_history_log_rate_change: Decimal
    maximum_arithmetic_error: Decimal

    def __post_init__(self):
        validate_stable_id(self.criteria_id)
        if type(self.minimum_run_groups) is not int or self.minimum_run_groups < 2:
            raise ValueError('physical rate uncertainty needs at least two declared whole-run groups')
        for name in ('minimum_event_probability', 'minimum_at_risk_probability',
                'maximum_cumulative_probability_error', 'maximum_dwell_log_rate_change',
                'maximum_history_log_rate_change', 'maximum_arithmetic_error'):
            decimal_number(getattr(self, name), name, positive=True)
        if any(getattr(self, name) >= 1 for name in ('minimum_event_probability',
                'minimum_at_risk_probability', 'maximum_cumulative_probability_error', 'maximum_arithmetic_error')):
            raise ValueError('physical rate probability and arithmetic thresholds must lie strictly between zero and one')


@dataclass(frozen=True, slots=True)
class PhysicalRateCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-case'
    VERSION: ClassVar[str] = '1.0.0'
    ensemble_id: str
    observation_times_seconds: tuple[Decimal, ...]
    entry_history_ids: tuple[str, ...]
    physical_quantity: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.ensemble_id)
        identifiers(self.entry_history_ids, 'entry histories')
        exact(self.physical_quantity, ObjectIdentity)
        times = self.observation_times_seconds
        if type(times) is not tuple or len(times) < 2 or times != tuple(sorted(set(times))):
            raise ValueError('physical rate needs at least two ordered prospective dwell-time boundaries')
        for value in times:
            decimal_number(value, 'observation time', positive=True)


@dataclass(frozen=True, slots=True)
class PhysicalRateRunBinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-run-binding'
    VERSION: ClassVar[str] = '1.0.0'
    ensemble_id: str
    run_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.ensemble_id)
        identifiers(self.run_ids, 'original run census')


@dataclass(frozen=True, slots=True)
class PhysicalRateRunGroup(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-run-group'
    VERSION: ClassVar[str] = '1.0.0'
    group_id: str
    bindings: tuple[PhysicalRateRunBinding, ...]

    def __post_init__(self):
        validate_stable_id(self.group_id)
        roster(self.bindings, PhysicalRateRunBinding, 'ensemble_id')


@dataclass(frozen=True, slots=True)
class PhysicalRateControl(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-control'
    VERSION: ClassVar[str] = '1.0.0'
    control_id: str
    kind: str
    ensemble_ids: tuple[str, ...]
    comparison_basis: ObjectIdentity
    maximum_log_rate_change: Decimal

    def __post_init__(self):
        validate_stable_id(self.control_id)
        identifiers(self.ensemble_ids, 'control ensembles', minimum=2)
        exact(self.comparison_basis, ObjectIdentity)
        decimal_number(self.maximum_log_rate_change, 'control log-rate threshold', positive=True)
        if self.kind not in {'INTEGRATION_STEP', 'BATH_FRICTION', 'DISSOLVED_CONCENTRATION'}:
            raise ValueError('physical rate control changes its selected physical comparison')


@dataclass(frozen=True, slots=True)
class PhysicalRateSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-selection'
    VERSION: ClassVar[str] = '1.0.0'
    selection_id: str
    passages: FirstPassageSelection | WeightedPathCampaign
    cases: tuple[PhysicalRateCase, ...]
    run_groups: tuple[PhysicalRateRunGroup, ...]
    controls: tuple[PhysicalRateControl, ...]
    criteria: PhysicalRateCriteria
    bootstrap_replicates: int
    bootstrap_seed: int
    central_resampling_mass: Decimal
    maximum_analysis_bytes: int
    assumptions: tuple[str, ...]
    gas_concentrations: tuple[PeriodicGasConcentration, ...] = ()
    scope: str = 'CONDITIONAL_CONSTANT_HAZARD_REDUCTION_WITHOUT_PHYSICAL_MODEL_OR_BIOLOGICAL_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        original = initial_passages(self.passages)
        roster(self.cases, PhysicalRateCase, 'ensemble_id')
        roster(self.run_groups, PhysicalRateRunGroup, 'group_id')
        roster(self.controls, PhysicalRateControl, 'control_id', allow_empty=True)
        roster(self.gas_concentrations, PeriodicGasConcentration, 'concentration_id', allow_empty=True)
        if not {r.identity for r in self.gas_concentrations}.issubset(e.concentration_source for e in original.ensembles):
            raise ValueError('physical rate concentration census includes an unselected gas source')
        exact(self.criteria, PhysicalRateCriteria)
        expected = tuple(e.ensemble_id for e in original.ensembles)
        if tuple(c.ensemble_id for c in self.cases) != expected:
            raise ValueError('physical rate drops an original ensemble, including an unfavorable or missing case')
        for case in self.cases:
            histories = tuple(sorted({p.entry_history_id for p in original.paths if p.ensemble_id == case.ensemble_id}))
            if case.entry_history_ids != histories:
                raise ValueError('physical rate changes the original entry-history denominator')
        all_runs = []
        for group in self.run_groups:
            if tuple(b.ensemble_id for b in group.bindings) != expected:
                raise ValueError('a joint resampling group must retain every paired condition and control')
            all_runs.extend((b.ensemble_id, run) for b in group.bindings for run in b.run_ids)
        assigned = {(p.ensemble_id, p.run_id) for p in original.paths}
        if len(set(all_runs)) != len(all_runs) or set(all_runs) != assigned:
            raise ValueError('physical rate repeats or omits an original run in its complete group census')
        if any(not set(c.ensemble_ids).issubset(expected) for c in self.controls):
            raise ValueError('physical rate control refers to an unselected ensemble')
        if (type(self.bootstrap_replicates) is not int or self.bootstrap_replicates < 2
                or type(self.bootstrap_seed) is not int or not 0 <= self.bootstrap_seed < 2**128
                or type(self.maximum_analysis_bytes) is not int or self.maximum_analysis_bytes <= 0
                or type(self.assumptions) is not tuple or not self.assumptions
                or any(type(a) is not str or not a.strip() for a in self.assumptions)
                or self.scope != 'CONDITIONAL_CONSTANT_HAZARD_REDUCTION_WITHOUT_PHYSICAL_MODEL_OR_BIOLOGICAL_ADMISSION'):
            raise ValueError('physical rate requires explicit resampling, workspace, assumptions and evidence limits')
        decimal_number(self.central_resampling_mass, 'central resampling mass', positive=True)
        if self.central_resampling_mass >= 1:
            raise ValueError('central resampling mass must lie strictly between zero and one')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


@dataclass(frozen=True, slots=True)
class PhysicalRateEvidence(FirstPassageEvidence):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/physical-rate-evidence'
    SELECTION_KIND: ClassVar[type] = PhysicalRateSelection
