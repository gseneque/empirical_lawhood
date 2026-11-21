# SPDX-License-Identifier: MPL-2.0
"""Physical-grid exits and finite-horizon weighted path accounting.

Unobserved future exits remain unidentified. No reciprocal censored mean,
unobserved reverse zero, exponential lifetime or rate prefactor is invented.
"""

from fractions import Fraction
import math

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_records import PassageEnsemble, FirstPassageSelection


def rational(value):
    value = Fraction(value)
    return dict(numerator=value.numerator, denominator=value.denominator)


def fraction(value):
    if (type(value) is not dict or set(value) != {'numerator','denominator'}
            or type(value['numerator']) is not int or type(value['denominator']) is not int
            or value['denominator'] <= 0):
        raise ValueError('first-passage readout changes an exact rational operand')
    result = Fraction(value['numerator'], value['denominator'])
    if rational(result) != value:
        raise ValueError('first-passage readout changes its reduced rational representation')
    return result


def contains(region, coordinates):
    if len(coordinates) != len(region.lower):
        raise ValueError('passage coordinate denominator differs from its selected region')
    return all(Fraction(low) <= Fraction(float(value)) < Fraction(high)
        for low,value,high in zip(region.lower, coordinates, region.upper, strict=True))


class PassageObserver:
    """Observe only checked physical-grid coordinates, with constant event state."""

    def __init__(self, *, ensemble, settings):
        exact(ensemble, PassageEnsemble)
        self.ensemble, self.settings = ensemble, settings
        self.count = 0
        self.last_label = None
        self.streak_start = None
        self.first_event = None
        self.entry_valid = None
        self.visits = {e.event_id:0 for e in ensemble.events}
        self.departures = {e.event_id:0 for e in ensemble.events}
        self.residence = {e.event_id:0 for e in ensemble.events}
        self.transitions = []

    def consume(self, *, step, physical_time_seconds, coordinates):
        if (type(step) is not int or step != self.count or step > self.settings.steps
                or Fraction(physical_time_seconds) != Fraction(self.settings.time_at_step(step))
                or len(coordinates) != len(self.ensemble.coordinate_window.cv_kinds)
                or any(not math.isfinite(float(v)) for v in coordinates)):
            raise ValueError('first-passage projection changes its complete physical clock or coordinate census')
        if step == 0:
            self.entry_valid = contains(self.ensemble.entry_region, coordinates)
        matched = tuple(event for event in self.ensemble.events if contains(event.region, coordinates))
        if len(matched) > 1:
            raise ValueError('one physical frame entered overlapping first-passage outcomes')
        event = matched[0] if matched else None
        label = event.event_id if event else None
        if label != self.last_label:
            if self.last_label is not None:
                self.departures[self.last_label] += 1
            if label is not None:
                self.visits[label] += 1
            self.transitions.append(dict(step=step, previous=self.last_label, current=label))
            self.streak_start = step if event else None
        if event is not None:
            if label == self.last_label:
                self.residence[label] += 1
            if self.first_event is None and step-self.streak_start >= event.residence_steps:
                entrance = self.streak_start
                self.first_event = dict(event_id=event.event_id, role=event.role, entrance_step=entrance,
                    confirmation_step=step, entrance_time_lower_seconds=rational(self.settings.time_at_step(max(0, entrance-1))),
                    entrance_time_upper_seconds=rational(self.settings.time_at_step(entrance)),
                    event_time_lower_seconds=rational(self.settings.time_at_step(max(0,step-1))),
                    event_time_upper_seconds=rational(self.settings.time_at_step(step)),
                    confirmation_time_seconds=rational(self.settings.time_at_step(step)),
                    physical_definition=event.physical_definition.to_document())
        self.last_label = label
        self.count += 1

    def finish(self):
        return dict(retained_frames=self.count, entry_region_satisfied=self.entry_valid,
            selected_horizon_seconds=rational(self.settings.time_at_step(self.settings.steps)),
            observed_time_seconds=rational(self.settings.time_at_step(max(0,self.count-1))),
            first_event=self.first_event, event_visits=self.visits, event_departures=self.departures,
            event_residence_grid_intervals=self.residence, region_transitions=tuple(self.transitions),
            pending_event=self.last_label if self.first_event is None else None,
            pending_entrance_step=self.streak_start if self.first_event is None else None,
            event_definition='FIRST_COMPLETION_OF_SELECTED_CONTIGUOUS_RESIDENCE_ON_PHYSICAL_GRID',
            crossing_resolution='ORIGINAL_ADJACENT_PHYSICAL_GRID_POINTS_NO_TIME_INTERPOLATION',
            initial_ensemble_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE')


def _average(rows):
    return sum(rows,Fraction())/len(rows)


def summarize_first_passages(*, selection, path_reports):
    """Retain exact run denominators and uncertainty from incomplete observation.

    Bounds here enclose the weighted empirical paths' unknown event/time values.
    They are not sampling-confidence intervals or model-error bounds. All joint
    path outcomes remain available for a separately selected paired reduction.
    """
    exact(selection, FirstPassageSelection)
    if set(path_reports) != {p.path_id for p in selection.paths}:
        raise ValueError('first-passage analysis changes the complete assigned path denominator')
    output = {}
    for ensemble in selection.ensembles:
        paths = tuple(p for p in selection.paths if p.ensemble_id == ensemble.ensemble_id)
        horizon_values = {fraction(path_reports[p.path_id]['selected_horizon_seconds']) for p in paths}
        if len(horizon_values) != 1:
            raise ValueError('one first-passage ensemble must retain one prospective physical horizon')
        horizon, = horizon_values
        run_rows = {}
        for run_id in sorted({p.run_id for p in paths}):
            group = tuple(p for p in paths if p.run_id == run_id)
            event_mass = {e.event_id:Fraction() for e in ensemble.events}
            unresolved = horizon_censored = computational = Fraction()
            lower_time = upper_time = observed_exposure = Fraction()
            costs = []
            for path in group:
                row, weight = path_reports[path.path_id], path.weight.fraction
                status = row['path_disposition']
                event = row['first_event'] if status == 'OBSERVED_EVENT' else None
                time = fraction(row['observed_time_seconds'])
                if not 0 <= time <= horizon:
                    raise ValueError('first-passage report changes its actual physical-time extent')
                if event is not None:
                    if event['event_id'] not in event_mass:
                        raise ValueError('first-passage report names an unselected event')
                    low, high = fraction(event['event_time_lower_seconds']), fraction(event['event_time_upper_seconds'])
                    confirmation = fraction(event['confirmation_time_seconds'])
                    if not 0 <= low <= high <= confirmation <= time:
                        raise ValueError('first-passage report changes its actual entrance or confirmation clock')
                    event_mass[event['event_id']] += weight
                    lower_time += weight*low
                    upper_time += weight*high
                    observed_exposure += weight*high
                else:
                    unresolved += weight
                    # Mechanically unassessed paths do not acquire a zero event
                    # count or an observed survival horizon in this reduction.
                    known_survival = time if status in {'HORIZON_CENSORED','COMPUTATIONAL_TRUNCATION',
                        'SCHEDULED_CONTINUATION_UNOBSERVED','UNOBSERVED_CONTINUATION'} else Fraction()
                    lower_time += weight*known_survival
                    upper_time += weight*horizon
                    observed_exposure += weight*known_survival
                    if status == 'HORIZON_CENSORED':
                        horizon_censored += weight
                    else:
                        computational += weight
                costs.append(dict(path_id=path.path_id, original_cost=row['original_cost']))
            run_rows[run_id] = dict(assigned_paths=len(group), preparation_ids=tuple(sorted({p.preparation_id for p in group})),
                site_ids=tuple(sorted({p.site_id for p in group})), entry_history_ids=tuple(sorted({p.entry_history_id for p in group})),
                assigned_weight=rational(1), observed_event_weight={key:rational(value) for key,value in event_mass.items()},
                horizon_censored_weight=rational(horizon_censored), computational_or_unassessed_weight=rational(computational),
                unresolved_eventual_weight=rational(unresolved),
                event_probability_by_horizon_bounds={key:(rational(value),rational(value+computational)) for key,value in event_mass.items()},
                eventual_event_probability_bounds={key:(rational(value),rational(value+unresolved)) for key,value in event_mass.items()},
                restricted_mean_first_passage_bounds_seconds=(rational(lower_time),rational(upper_time)),
                complete_mean_first_passage_bounds_seconds=(rational(lower_time),rational(upper_time)) if unresolved == 0 else None,
                observed_at_risk_time_seconds=rational(observed_exposure), costs=tuple(costs),
                memoryless_rates_per_second=None, reason='NO_MEMORYLESS_OR_NONINFORMATIVE_CENSORING_ASSUMPTION_SUPPLIED')
        run_values = tuple(run_rows.values())
        output[ensemble.ensemble_id] = dict(assigned_paths=len(paths), declared_run_groups=len(run_values),
            independent_biological_units='NOT_INFERRED_FROM_RUN_PATH_OR_SITE_LABELS', physical_horizon_seconds=rational(horizon),
            event_ids=tuple(e.event_id for e in ensemble.events), runs=run_rows,
            equal_run_restricted_mean_bounds_seconds=tuple(rational(_average([fraction(r['restricted_mean_first_passage_bounds_seconds'][i]) for r in run_values])) for i in (0,1)),
            equal_run_event_probability_by_horizon_bounds={event.event_id:tuple(rational(_average([
                fraction(r['event_probability_by_horizon_bounds'][event.event_id][i]) for r in run_values])) for i in (0,1)) for event in ensemble.events},
            dissolved_gas_uM=str(ensemble.dissolved_gas_uM) if ensemble.dissolved_gas_uM is not None else None,
            concentration_source=ensemble.concentration_source.to_document() if ensemble.concentration_source else None,
            dynamics_model=ensemble.dynamics_model,
            bath_temperature_kelvin=str(ensemble.temperature_kelvin) if ensemble.temperature_kelvin is not None else None,
            bath_friction_per_picosecond=str(ensemble.friction_per_picosecond) if ensemble.friction_per_picosecond is not None else None,
            bath_transport_dependence='UNEVALUABLE' if ensemble.dynamics_model!='NVE' else 'NO_BATH',
            association_coefficient_per_uM_second=None, concentration_scaling_admission='UNEVALUABLE',
            physical_rate_admission='UNEVALUABLE')
    return dict(ensembles=output, empirical_bounds_scope='UNOBSERVED_PATH_VALUES_NOT_A_SAMPLING_CONFIDENCE_REGION',
        memorylessness='UNEVALUABLE', initial_ensemble_admission='UNEVALUABLE', physical_rate_admission='UNEVALUABLE',
        resampling_or_wall_time_used_as_molecular_time=False)
