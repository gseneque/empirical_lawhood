# SPDX-License-Identifier: MPL-2.0
"""E1 occurrence and first-admission persistence with complete missingness.

The caller authenticates the complete assigned source/product/assessment census.
This owner consumes categorical observations only; it does not measure spectra,
select a later episode, replace a missing root or establish sampling authority.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorObservation
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import _moving_state
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import IncompleteBinomialInterval, incomplete_binomial_interval

from .records import ENDPOINTS, VIEWS


@dataclass(frozen=True, slots=True)
class E1RootOccurrence(CanonicalRecord):
    """One assigned root/view/sector, with no episode-level independence."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/root-occurrence'
    root_id: str
    unit_id: str
    source: ObjectIdentity
    family_id: str
    view: str
    sector: str
    occurrence_end_tick: int
    survival_duration_ticks: int
    source_disposition: str
    numerical_usable: bool
    initial_presence: bool | None
    occurrence: bool | None
    first_observed_admission_tick: int | None
    first_admission_tick: int | None
    first_admission_after_absence: bool | None
    return_after_exit: bool | None
    moving_survival: bool | None
    origin_fixed_survival: bool | None
    joint_survival: bool | None
    identification_loss_ticks: tuple[int, ...]
    unobserved_ticks: tuple[int, ...]
    observed_exit_ticks: tuple[int, ...]

    def __post_init__(self):
        for value in (self.root_id, self.unit_id):
            validate_stable_id(value)
        if (type(self.source) is not ObjectIdentity or self.family_id not in FOUR_FAMILY_PREPARATION_IDS
                or self.view not in VIEWS or self.sector not in ('X', 'Y')
                or type(self.occurrence_end_tick) is not int or self.occurrence_end_tick < 1
                or type(self.survival_duration_ticks) is not int or self.survival_duration_ticks < 1
                or type(self.numerical_usable) is not bool
                or self.source_disposition not in ('ASSESSED', 'NUMERICAL_UNUSABLE', 'UNAVAILABLE', 'UNKNOWN_CONTACT')):
            raise ValueError('E1 root event changes its exact assigned identity, clock or usability')
        self.source.__post_init__()
        flags = (self.initial_presence, self.occurrence, self.first_admission_after_absence,
            self.return_after_exit, self.moving_survival, self.origin_fixed_survival, self.joint_survival)
        if any(value is not None and type(value) is not bool for value in flags):
            raise ValueError('E1 root event requires explicit true/false/unknown observations')
        for tick in (self.first_observed_admission_tick, self.first_admission_tick):
            if tick is not None and (type(tick) is not int or not 0 <= tick <= self.occurrence_end_tick):
                raise ValueError('E1 root event changes its first-admission window')
        if (self.first_admission_tick is not None and self.first_admission_tick != self.first_observed_admission_tick
                or (self.occurrence is True) != (self.first_observed_admission_tick is not None)
                or self.initial_presence is True and self.first_admission_tick != 0
                or self.first_admission_tick is None and any(value is not None for value in
                    (self.first_admission_after_absence, self.moving_survival, self.origin_fixed_survival, self.joint_survival))
                or not self.numerical_usable and (any(value is not None for value in flags)
                    or self.first_observed_admission_tick is not None)
                or self.joint_survival != _joint((self.moving_survival, self.origin_fixed_survival))):
            raise ValueError('E1 root event invents first-origin knowledge or survival from nonuse')
        for ticks in (self.identification_loss_ticks, self.unobserved_ticks, self.observed_exit_ticks):
            if (type(ticks) is not tuple or ticks != tuple(sorted(set(ticks)))
                    or any(type(tick) is not int or tick < 0 for tick in ticks)):
                raise ValueError('E1 root event changes ordered identification/observation/exit diagnostics')

    @property
    def key(self):
        return self.root_id, self.view, self.sector

    def allowed_states(self, endpoint):
        if endpoint == 'OCCURRENCE':
            return ('SUCCESS',) if self.occurrence is True else ('FAILURE',) if self.occurrence is False else ('FAILURE', 'SUCCESS')
        if endpoint not in ENDPOINTS:
            raise ValueError('E1 event substitutes its occurrence or persistence endpoint')
        if self.occurrence is False:
            return ('INELIGIBLE',)
        if self.occurrence is None:
            return ('FAILURE', 'INELIGIBLE', 'SUCCESS')
        value = {'MOVING': self.moving_survival, 'ORIGIN_FIXED': self.origin_fixed_survival, 'BOTH': self.joint_survival}[endpoint]
        return ('SUCCESS',) if value is True else ('FAILURE',) if value is False else ('FAILURE', 'SUCCESS')


def _joint(values):
    if any(value is False for value in values):
        return False
    return None if any(value is None for value in values) else True


def root_occurrence(*, root_id, unit_id, source, family_id, view, sector, rule,
        occurrence_end_tick, survival_duration_ticks, observations, numerical_usable,
        source_disposition='ASSESSED'):
    """Initial presence, earliest causal admission, and its original 128-window.

    Initial raw admission is explicitly eligible at tick zero. Later admissions
    retain the selected causal trailing rule. Earlier missing/identification
    intervals prevent a later observed event from being called the first one.
    """
    if (type(numerical_usable) is not bool or rule.risk_start_tick != 0
            or occurrence_end_tick not in rule.lattice
            or type(survival_duration_ticks) is not int or survival_duration_ticks < 1
            or survival_duration_ticks % (rule.lattice[1] - rule.lattice[0])
            or occurrence_end_tick + survival_duration_ticks > rule.lattice[-1]):
        raise ValueError('E1 occurrence requires time-zero risk and its complete first-admission follow-up')
    missing = observations is None
    if missing:
        if numerical_usable or source_disposition not in ('UNAVAILABLE', 'UNKNOWN_CONTACT'):
            raise ValueError('absent E1 observations require their actual unavailable/contact disposition')
    elif (type(observations) is not tuple or tuple(row.tick for row in observations) != rule.lattice
            or any(type(row) is not FactorObservation for row in observations)
            or source_disposition not in ('ASSESSED', 'NUMERICAL_UNUSABLE')
            or numerical_usable != (source_disposition == 'ASSESSED')):
        raise ValueError('E1 events require complete original observations and exact numerical usability')
    else:
        for row in observations:
            row.__post_init__()
    initial = occurrence = first_after_absence = returned = moving = fixed = None
    first_observed = first = None
    losses = unobserved = exits = ()
    if not missing:
        losses = tuple(row.tick for row in observations if row.status == 'UNIDENTIFIABLE')
        unobserved = tuple(row.tick for row in observations if row.status in ('UNAVAILABLE', 'NUMERICAL_INVALID'))
    if numerical_usable:
        window = tuple(row for row in observations if row.tick <= occurrence_end_tick)
        initial = window[0].raw_admitted
        admitted = tuple(row.tick for row in window if (row.tick == 0 and row.raw_admitted is True)
            or row.causal_admitted is True)
        first_observed = admitted[0] if admitted else None
        occurrence = True if admitted else None if any(row.raw_admitted is None for row in window) else False
        if first_observed is not None and all(row.raw_admitted is not None for row in window if row.tick < first_observed):
            first = first_observed
            first_after_absence = first > 0 and any(row.raw_admitted is False for row in window if row.tick < first)
            followup = tuple(row for row in observations if first < row.tick <= first + survival_duration_ticks)
            moving = _joint(tuple(_moving_state(row, rule) for row in followup))
            fixed = _joint(tuple(False if _moving_state(row, rule) is False else None
                if _moving_state(row, rule) is None or row.origin_angle_degrees is None else
                row.origin_angle_degrees <= rule.origin_angle_maximum_degrees for row in followup))
        in_episode = seen_exit = returned = False
        exit_ticks = []
        for row in observations:
            state = _moving_state(row, rule)
            if in_episode and state is False:
                exit_ticks.append(row.tick)
                seen_exit = True
                in_episode = False
            if row.tick == 0 and row.raw_admitted is True or row.causal_admitted is True:
                returned = returned or seen_exit
                in_episode = True
        if not returned and any(row.raw_admitted is None for row in observations):
            returned = None
        exits = tuple(exit_ticks)
    return E1RootOccurrence(root_id, unit_id, source, family_id, view, sector, occurrence_end_tick,
        survival_duration_ticks, source_disposition, numerical_usable, initial, occurrence,
        first_observed, first, first_after_absence, returned, moving, fixed, _joint((moving, fixed)),
        losses, unobserved, exits)


@dataclass(frozen=True, slots=True)
class E1OccurrenceCell(CanonicalRecord):
    """Population uncertainty with its primary or descriptive inference scope."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-factor-confirmation/occurrence-cell'
    family_id: str
    view: str
    sector: str
    endpoint: str
    primary: bool
    interval: IncompleteBinomialInterval

    def __post_init__(self):
        expected_primary = self.view == 'PRIMARY' and self.sector == 'Y' and self.endpoint in ('OCCURRENCE', 'BOTH')
        if (self.family_id not in FOUR_FAMILY_PREPARATION_IDS or self.view not in VIEWS
                or self.sector not in ('X', 'Y') or self.endpoint not in ('OCCURRENCE', *ENDPOINTS)
                or type(self.primary) is not bool or self.primary != expected_primary
                or type(self.interval) is not IncompleteBinomialInterval
                or (self.interval.tail_numerator, self.interval.tail_denominator) != ((1, 2560) if self.primary else (1, 40))):
            raise ValueError('E1 interval changes its fixed eight-cell PRIMARY-Y allocation or diagnostic scope')
        self.interval.__post_init__()


def occurrence_cells(events, *, family_counts):
    """Eight primary CP envelopes; X/FINE and separate endpoints are descriptive."""
    if (type(events) is not tuple or any(type(event) is not E1RootOccurrence for event in events)
            or len({event.key for event in events}) != len(events)
            or type(family_counts) is not dict or set(family_counts) != set(FOUR_FAMILY_PREPARATION_IDS)
            or any(type(count) is not int or count < 1 for count in family_counts.values())):
        raise ValueError('E1 occurrence map requires its complete original family/root/view/sector census')
    identities = {}
    for event in events:
        event.__post_init__()
        identity = event.root_id, event.source, event.family_id
        if identities.setdefault(event.unit_id, identity) != identity:
            raise ValueError('E1 occurrence map aliases independent-unit source or family identity')
    if len({(event.occurrence_end_tick, event.survival_duration_ticks) for event in events}) != 1:
        raise ValueError('E1 occurrence map changes its frozen endpoint clocks between units')
    rows = []
    for family in sorted(family_counts):
        expected_units = None
        for view in VIEWS:
            for sector in ('X', 'Y'):
                selected = tuple(sorted((event for event in events
                    if (event.family_id, event.view, event.sector) == (family, view, sector)), key=lambda event: event.unit_id))
                units = tuple(event.unit_id for event in selected)
                if (len(units) != family_counts[family] or len(set(units)) != len(units)
                        or expected_units is not None and expected_units != units):
                    raise ValueError('E1 occurrence map thins or substitutes assigned roots across nested views/sectors')
                expected_units = units
                for endpoint in ('OCCURRENCE', *ENDPOINTS):
                    primary = view == 'PRIMARY' and sector == 'Y' and endpoint in ('OCCURRENCE', 'BOTH')
                    result = incomplete_binomial_interval(units, tuple(event.allowed_states(endpoint) for event in selected),
                        tail_probability=Fraction(1, 2560) if primary else Fraction(1, 40))
                    rows.append(E1OccurrenceCell(family, view, sector, endpoint, primary, result))
    if sum(row.primary for row in rows) != 8:
        raise ValueError('E1 map changes its complete eight-cell primary family')
    return tuple(rows)


def cell_report(cell):
    """Readable counts accompany the canonical unit-by-unit completion sets."""
    if type(cell) is not E1OccurrenceCell:
        raise TypeError('E1 cell reporting requires its exact retained interval')
    cell.__post_init__()
    interval = cell.interval
    return {'family_id': cell.family_id, 'view': cell.view, 'sector': cell.sector, 'endpoint': cell.endpoint,
        'inference_scope': 'SIMULTANEOUS_PRIMARY_EIGHT_CELLS' if cell.primary else 'DESCRIPTIVE_MARGINAL_95_PERCENT',
        'assigned_roots': len(interval.unit_ids), 'known_successes': interval.known_successes,
        'known_failures': interval.known_failures, 'known_risk_unknown_outcomes': interval.known_risk_unknown_outcomes,
        'known_ineligible': sum(row == ('INELIGIBLE',) for row in interval.allowed_states),
        'unknown_eligibility': interval.unknown_eligibility,
        'eligible_roots_lower': interval.risk_count_lower, 'eligible_roots_upper': interval.risk_count_upper,
        'assigned_population_interval': {'lower': None if interval.lower is None else str(interval.lower),
            'upper': None if interval.upper is None else str(interval.upper)},
        'complete_case_scope': 'CONDITIONAL_ON_ASSESSABILITY', 'complete_case_interval': interval.complete_case.to_document(),
        'tail_probability': {'numerator': interval.tail_numerator, 'denominator': interval.tail_denominator}}
