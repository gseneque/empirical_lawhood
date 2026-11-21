# SPDX-License-Identifier: MPL-2.0
"""Prospective common pilot selection from complete, original measured costs.

Adaptation of the cost-only selection in icf-yolo's rubisco_m1_v5/allocation.py
at aa9346547560abcb6500f2e97b53b96f456d9be3. The donor's deadlines, fixed case
counts, safety factor and authority are not selected. See pilot-provenance.json.
No molecular value, mutation direction or elapsed-time deadline enters selection.
"""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_nonempty, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import MODEL_NAMES
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import FirstPassageEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities


REQUIRED_ROLES = (
    'assessment-export', 'carbon-access-escape', 'carbon-chemistry-reversal',
    'carbon-processing-release-return', 'dividing-ensemble-dynamics',
    'formation-reversal', 'numerical-chemical-controls', 'oxygen-access-escape',
    'oxygen-charge-transfer', 'oxygen-processing-release-return',
    'oxygen-spin-recombination-commitment',
)
COMPLETE_COVERAGE = tuple((model, role) for model in MODEL_NAMES for role in REQUIRED_ROLES)


def _integer(value, name, *, positive=False):
    if type(value) is not int or value < (1 if positive else 0):
        raise ValueError(name+' requires its nonnegative integer count')


def _number(value, name, *, positive=False):
    validate_decimal(value, field_name=name, minimum=Decimal(0))
    if positive and value == 0:
        raise ValueError(name+' requires a positive exact value')


def rational(value):
    """Finite exact rendering; no ambient Decimal rounding or float money."""
    value = Fraction(value)
    return {'numerator': value.numerator, 'denominator': value.denominator}


@dataclass(frozen=True, slots=True)
class PilotCalibrationCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-calibration-case'
    calibration_id: str
    configuration: ObjectIdentity
    cost_class: str

    def __post_init__(self):
        validate_stable_id(self.calibration_id)
        exact(self.configuration, ObjectIdentity)
        validate_stable_id(self.cost_class)


@dataclass(frozen=True, slots=True)
class PilotCostClass(CanonicalRecord):
    """An explicit extrapolation premise, not physical or throughput admission."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-cost-class'
    class_id: str
    unit: str
    minimum_successful_calibrations: int
    measured_cost_multiplier: Decimal
    scope: ObjectIdentity
    extrapolation_assumption: str

    def __post_init__(self):
        validate_stable_id(self.class_id)
        if self.unit not in {'COMPLETE_COUPLED_FORCE_RETURN', 'COMPLETE_ANALYSIS_EXPORT'}:
            raise ValueError('pilot cost class requires an authenticated complete force return or analysis/export invocation')
        _integer(self.minimum_successful_calibrations, 'minimum calibration count', positive=True)
        _number(self.measured_cost_multiplier, 'prospective cost multiplier', positive=True)
        if self.measured_cost_multiplier < 1:
            raise ValueError('prospective multiplier cannot discount the maximum measured unit cost')
        exact(self.scope, ObjectIdentity)
        validate_nonempty(self.extrapolation_assumption, field_name='extrapolation_assumption')


@dataclass(frozen=True, slots=True)
class PilotWorkEstimate(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-work-estimate'
    work_id: str
    scientific_selection: ObjectIdentity
    cost_class: str
    units: int
    coverage: tuple[tuple[str, str], ...]
    host_memory_bytes: int
    device_memory_bytes: int
    retained_bytes: int

    def __post_init__(self):
        validate_stable_id(self.work_id)
        exact(self.scientific_selection, ObjectIdentity)
        validate_stable_id(self.cost_class)
        _integer(self.units, 'finite scientific work', positive=True)
        if (type(self.coverage) is not tuple or not self.coverage
                or any(type(row) is not tuple or row not in COMPLETE_COVERAGE for row in self.coverage)
                or self.coverage != tuple(sorted(set(self.coverage)))):
            raise ValueError('pilot work needs exact M1/V1 WT/I95M consequential-role coverage')
        for name in ('host_memory_bytes', 'device_memory_bytes', 'retained_bytes'):
            _integer(getattr(self, name), name, positive=name == 'host_memory_bytes')


@dataclass(frozen=True, slots=True)
class PilotCandidate(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-candidate'
    candidate_id: str
    work: tuple[PilotWorkEstimate, ...]
    overhead_charge: Decimal
    numerical_and_scientific_criteria: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.candidate_id)
        if type(self.work) is not tuple or not self.work:
            raise ValueError('pilot candidate requires its complete selected work')
        require_sorted_unique_ids(self.work, attribute='work_id', field_name='work')
        for row in self.work:
            exact(row, PilotWorkEstimate)
        if {cell for row in self.work for cell in row.coverage} != set(COMPLETE_COVERAGE):
            raise ValueError('pilot candidate omits a consequential role or paired material')
        # A shared original selection is one work item with several coverage
        # cells, never several bills or repeated native effects.
        if len({row.scientific_selection for row in self.work}) != len(self.work):
            raise ValueError('pilot candidate repeats one scientific selection instead of shared coverage')
        _number(self.overhead_charge, 'prospective overhead charge')
        identities(self.numerical_and_scientific_criteria)


@dataclass(frozen=True, slots=True)
class PilotAllocationRule(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-allocation-rule'
    rule_id: str
    calibrations: tuple[PilotCalibrationCase, ...]
    cost_classes: tuple[PilotCostClass, ...]
    candidates: tuple[PilotCandidate, ...]
    priority: tuple[str, ...]
    currency: str
    quoted_charge_per_second: Decimal | None
    quote_source: ObjectIdentity | None
    maximum_additional_projected_charge: Decimal | None
    available_host_memory_bytes: int
    available_device_memory_bytes: int
    available_retained_bytes: int
    prospective_design: ObjectIdentity
    scope: str = 'PROSPECTIVE_SERIAL_COST_ESTIMATES_NOT_AUTHORITY_OR_SCIENTIFIC_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.rule_id)
        exact(self.prospective_design, ObjectIdentity)
        for name, field, kind in (('calibrations', 'calibration_id', PilotCalibrationCase),
                ('cost_classes', 'class_id', PilotCostClass), ('candidates', 'candidate_id', PilotCandidate)):
            rows = getattr(self, name)
            if type(rows) is not tuple or not rows:
                raise ValueError('pilot rule requires its complete nonempty '+name)
            require_sorted_unique_ids(rows, attribute=field, field_name=name)
            for row in rows:
                exact(row, kind)
        classes = {row.class_id for row in self.cost_classes}
        if (any(row.cost_class not in classes for row in self.calibrations)
                or any(row.cost_class not in classes for c in self.candidates for row in c.work)):
            raise ValueError('pilot estimate refers to an undeclared cost class')
        if len({row.configuration for row in self.calibrations}) != len(self.calibrations):
            raise ValueError('pilot calibration repeats one original configuration')
        if (type(self.priority) is not tuple or len(self.priority) != len(self.candidates)
                or set(self.priority) != {row.candidate_id for row in self.candidates}):
            raise ValueError('pilot priority must contain every candidate exactly once')
        if type(self.currency) is not str or not re_currency(self.currency):
            raise ValueError('cost rule requires one explicit uppercase three-letter currency')
        if (self.quoted_charge_per_second is None) != (self.quote_source is None):
            raise ValueError('quoted price and its original source must be supplied together')
        if self.quote_source is not None:
            exact(self.quote_source, ObjectIdentity)
            _number(self.quoted_charge_per_second, 'quoted charge per second', positive=True)
        if self.maximum_additional_projected_charge is not None:
            _number(self.maximum_additional_projected_charge, 'additional projected charge')
        for name in ('available_host_memory_bytes', 'available_device_memory_bytes', 'available_retained_bytes'):
            _integer(getattr(self, name), name)
        if self.scope != 'PROSPECTIVE_SERIAL_COST_ESTIMATES_NOT_AUTHORITY_OR_SCIENTIFIC_ADMISSION':
            raise ValueError('cost preparation grants no spend, native entry, physical or policy admission')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.rule_id, self)


def re_currency(value):
    return len(value) == 3 and all('A' <= letter <= 'Z' for letter in value)


@dataclass(frozen=True, slots=True)
class PilotCostMeasurement(CanonicalRecord):
    """Numerical readout; the original reader separately authenticates custody."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-cost-measurement'
    calibration_id: str
    configuration: ObjectIdentity
    original: ObjectIdentity | None
    disposition: str
    cost: InquiryCost
    completed_units: int
    peak_rss_bytes: int | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.calibration_id)
        exact(self.configuration, ObjectIdentity)
        if self.original is not None:
            exact(self.original, ObjectIdentity)
        if self.disposition not in {'COMPLETE', 'FAILED', 'UNASSESSED', 'MISSING_ORIGINAL'}:
            raise ValueError('calibration loses original complete/failed/missing status')
        exact(self.cost, InquiryCost)
        _integer(self.completed_units, 'completed calibration units')
        if self.peak_rss_bytes is not None:
            _integer(self.peak_rss_bytes, 'observed peak memory')
        require_sorted_unique_strings(self.reason_codes, field_name='reason_codes')
        if (self.disposition == 'COMPLETE' and (self.original is None or self.completed_units <= 0 or self.reason_codes)
                or self.disposition != 'COMPLETE' and (not self.reason_codes or self.completed_units != 0)
                or self.disposition != 'MISSING_ORIGINAL' and self.original is None
                or self.disposition == 'MISSING_ORIGINAL' and (self.original is not None or self.completed_units
                    or self.cost != InquiryCost(None, None, None) or self.peak_rss_bytes is not None)):
            raise ValueError('calibration invents completed units or cost for missing/unassessed work')


def _measurements(rule, measurements):
    if (type(measurements) is not tuple or len(measurements) != len(rule.calibrations)
            or tuple(row.calibration_id for row in measurements) != tuple(row.calibration_id for row in rule.calibrations)):
        raise ValueError('allocation requires every selected calibration, including failures and unknowns')
    for case, measured in zip(rule.calibrations, measurements, strict=True):
        exact(measured, PilotCostMeasurement)
        if measured.configuration != case.configuration:
            raise ValueError('allocation substitutes the original calibration configuration')
    originals = [row.original for row in measurements if row.original is not None]
    if len(originals) != len(set(originals)):
        raise ValueError('allocation repeats one original measurement')


def allocate_pilot(rule, measurements):
    """Choose the first eligible complete candidate in its declared priority.

    Candidate units define finite scientific selections, not evaluation caps.
    Estimated wall seconds are serial cost projections, never native deadlines.
    All measured calibration costs remain separate from additional projections.
    """
    exact(rule, PilotAllocationRule)
    _measurements(rule, measurements)
    by_id = {row.calibration_id: row for row in measurements}
    classes, class_cost = {}, {}
    for profile in rule.cost_classes:
        rows = [by_id[c.calibration_id] for c in rule.calibrations if c.cost_class == profile.class_id]
        reasons = set()
        if any(row.disposition != 'COMPLETE' for row in rows):
            reasons.add('FAILED_UNASSESSED_OR_MISSING_CALIBRATION')
        if len(rows) < profile.minimum_successful_calibrations:
            reasons.add('INSUFFICIENT_COMPLETE_CALIBRATION_CENSUS')
        if any(row.cost.wall_seconds is None or row.cost.wall_seconds <= 0 for row in rows):
            reasons.add('COMPLETE_UNIT_COST_UNAVAILABLE')
        if any(row.peak_rss_bytes is None for row in rows):
            reasons.add('CALIBRATION_MEMORY_UNAVAILABLE')
        unit_cost = None if reasons else max(Fraction(row.cost.wall_seconds)/row.completed_units for row in rows)
        class_cost[profile.class_id] = None if unit_cost is None else unit_cost*Fraction(profile.measured_cost_multiplier)
        classes[profile.class_id] = dict(reason_codes=sorted(reasons), calibrations=[row.calibration_id for row in rows],
            maximum_measured_unit_seconds=None if unit_cost is None else rational(unit_cost),
            projected_unit_seconds=None if unit_cost is None else rational(class_cost[profile.class_id]),
            maximum_observed_rss_bytes=max((row.peak_rss_bytes for row in rows if row.peak_rss_bytes is not None), default=None),
            extrapolation_assumption=profile.extrapolation_assumption)
    candidates = {}
    for candidate in rule.candidates:
        reasons = set()
        available = all(class_cost[row.cost_class] is not None for row in candidate.work)
        duration = sum((row.units*class_cost[row.cost_class] for row in candidate.work), Fraction()) if available else None
        if not available:
            reasons.add('REQUIRED_COST_CLASS_UNAVAILABLE')
        if rule.quote_source is None:
            reasons.add('CURRENT_QUOTE_UNAVAILABLE')
        if rule.maximum_additional_projected_charge is None:
            reasons.add('PROJECTED_CHARGE_ENVELOPE_UNSELECTED')
        host = max(row.host_memory_bytes for row in candidate.work)
        device = max(row.device_memory_bytes for row in candidate.work)
        retained = sum(row.retained_bytes for row in candidate.work)
        if host > rule.available_host_memory_bytes or device > rule.available_device_memory_bytes or retained > rule.available_retained_bytes:
            reasons.add('SELECTED_RESOURCE_CAPACITY_INSUFFICIENT')
        if any(classes[row.cost_class]['maximum_observed_rss_bytes'] is not None
                and classes[row.cost_class]['maximum_observed_rss_bytes'] > row.host_memory_bytes for row in candidate.work):
            reasons.add('PROJECTED_MEMORY_BELOW_ORIGINAL_OBSERVATION')
        charge = None if duration is None or rule.quote_source is None else (
            duration*Fraction(rule.quoted_charge_per_second)+Fraction(candidate.overhead_charge))
        if charge is not None and rule.maximum_additional_projected_charge is not None and charge > Fraction(rule.maximum_additional_projected_charge):
            reasons.add('ADDITIONAL_PROJECTED_CHARGE_EXCEEDED')
        candidates[candidate.candidate_id] = dict(eligible_estimate=not reasons, reason_codes=sorted(reasons),
            serial_seconds=None if duration is None else rational(duration),
            additional_charge=None if charge is None else rational(charge),
            host_memory_bytes=host, device_memory_bytes=device, retained_bytes=retained,
            scientific_work_items=len(candidate.work), complete_material_role_cells=len(COMPLETE_COVERAGE))
    selected = next((key for key in rule.priority if candidates[key]['eligible_estimate']), None)
    costs = {}
    for name in ('cpu_seconds', 'wall_seconds', 'retained_bytes'):
        values = [getattr(row.cost, name) for row in measurements]
        costs[name] = None if any(value is None for value in values) else rational(sum(map(Fraction, values), Fraction()))
    return dict(rule=rule.identity.to_document(), selected_candidate=selected,
        disposition='PROVISIONAL_COST_SELECTION' if selected is not None else 'NO_FEASIBLE_COMPLETE_PILOT',
        cost_classes=classes, candidates=candidates, priority=rule.priority, currency=rule.currency,
        original_calibrations=tuple(row.to_document() for row in measurements), total_original_calibration_cost=costs,
        interpretation=rule.scope, scientific_acquisition_authority='NONE',
        remaining_requirements=('actual-provider-spend-and-operation-authority', 'actual-host-device-and-storage-admission',
            'prospective-design-and-recipe-custody', 'supported-native-preparation-for-selected-recipes',
            'physical-and-numerical-supplier-assessment', 'scientific-stage-transition-and-stopping-assessment'))


@dataclass(frozen=True, slots=True)
class PilotAllocationEvidence(FirstPassageEvidence):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-allocation-evidence'
    SELECTION_KIND: ClassVar[type] = PilotAllocationRule
