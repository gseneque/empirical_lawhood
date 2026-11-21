# SPDX-License-Identifier: MPL-2.0
"""Exact first-exit moments and independently enclosed network dynamics.

Moment quotients are conditional summaries, not automatically Markov rates.
All chemical, release and return waits remain in the transient generator.
"""

from fractions import Fraction as F
import math

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.science import solve
from empirical_lawhood.methods._arb import arb_precision, endpoint_decimal
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational
from empirical_lawhood.domains.rubisco.rubisco_response.physical_rate_science import status


def network_moments(network, rates):
    """Solve the finite absorbing CTMC using the existing exact balance owner."""
    transient = tuple(s.state_id for s in network.states if s.terminal_outcome is None)
    outcomes = tuple(sorted({s.terminal_outcome for s in network.states if s.terminal_outcome is not None}))
    states = {s.state_id:s for s in network.states}
    indexes = {s:i for i,s in enumerate(transient)}
    n = len(transient)
    a = [[F() for _ in transient] for _ in transient]
    b = {outcome:[F() for _ in transient] for outcome in outcomes}
    for edge in network.edges:
        rate = F(rates[edge.rate])
        if rate<=0:
            raise ValueError('network moment reduction requires every positive original edge; missing rates are not zeros')
        i = indexes[edge.source_state_id]
        a[i][i] += rate
        target = states[edge.target_state_id]
        if target.terminal_outcome is None:
            a[i][indexes[target.state_id]] -= rate
        else:
            b[target.terminal_outcome][i] += rate
    means = solve(tuple((*row,F(1)) for row in a))
    seconds = solve(tuple((*row,2*mean) for row,mean in zip(a,means,strict=True)))
    probabilities = {outcome:solve(tuple((*row,value) for row,value in zip(a,values,strict=True))) for outcome,values in b.items()}
    if (min(means)<=0 or any(sum(p[i] for p in probabilities.values()) != 1 for i in range(n))
            or any(value<0 or value>1 for rows in probabilities.values() for value in rows)):
        raise ValueError('exact network moments violate finite residence or complete absorption probability')
    # Verify every independently formed backward equation, not just a printed
    # point result from the elimination routine.
    for i,row in enumerate(a):
        if sum(x*y for x,y in zip(row,means,strict=True)) != 1 or sum(x*y for x,y in zip(row,seconds,strict=True)) != 2*means[i]:
            raise ValueError('exact network first/second moment equations disagree')
        if any(sum(x*y for x,y in zip(row,probabilities[k],strict=True)) != b[k][i] for k in outcomes):
            raise ValueError('exact network competing-outcome balance disagrees')
    initial = {r.state_id:r.weight.fraction for r in network.initial}
    alpha = tuple(initial.get(s,F()) for s in transient)
    mean = sum(w*v for w,v in zip(alpha,means,strict=True))
    second = sum(w*v for w,v in zip(alpha,seconds,strict=True))
    probability = {k:sum(w*v for w,v in zip(alpha,rows,strict=True)) for k,rows in probabilities.items()}
    quotient = {k:v/mean for k,v in probability.items()}
    return dict(transient_states=transient,outcomes=outcomes,negative_transient_generator=a,exit_columns=b,initial=alpha,
        state_means=means,state_second_moments=seconds,state_outcome_probabilities=probabilities,
        mean=mean,second_moment=second,probabilities=probability,moment_quotients=quotient)


def _bounds(value):
    return tuple(str(endpoint_decimal(value,upper=upper)) for upper in (False,True))


def _comparison(value, threshold):
    lower,upper = (F(v) for v in _bounds(abs(value)))
    return 'SATISFIED' if upper<=F(threshold) else 'FALSIFIED' if lower>F(threshold) else 'UNEVALUABLE'


def _log_fraction(value):
    return math.log(value.numerator)-math.log(value.denominator)


def assess_network_dynamics(network, moments, *, times=None, model_mean=None):
    """Check SciPy propagation with Arb enclosures of the exact entered rates."""
    import numpy as np
    from scipy.linalg import expm
    from flint import arb, arb_mat, fmpq
    a,b,alpha = moments['negative_transient_generator'],moments['exit_columns'],moments['initial']
    n,outcomes = len(alpha),moments['outcomes']
    m = n+len(outcomes)
    generator = [[F() for _ in range(m)] for _ in range(m)]
    for i in range(n):
        generator[i][:n] = [-v for v in a[i]]
        generator[i][n:] = [b[k][i] for k in outcomes]
    entered = np.asarray(generator,dtype=float)
    initial = np.asarray((*alpha,*([F()]*len(outcomes))),dtype=float)
    if not np.isfinite(entered).all():
        return dict(numerical_assessment='UNEVALUABLE',constant_hazard_assessment='UNEVALUABLE',
            reason='GENERATOR_OUTSIDE_FINITE_BINARY64_REPRESENTATION',curves=[])
    curves, numerics, memory = [], [], []
    with arb_precision(network.verification_precision_bits):
        def ball(value):
            value = F(value)
            return arb(fmpq(value.numerator,value.denominator))
        exact_initial = arb_mat(1,m,[ball(v) for v in (*alpha,*([F()]*len(outcomes)))])
        for time in network.observation_times_seconds if times is None else times:
            with np.errstate(over='ignore',invalid='ignore'):
                argument = entered*float(time)
            if not np.isfinite(argument).all():
                curves.append(dict(time_seconds=rational(F(time)),status='UNEVALUABLE',reason='NONFINITE_EXPONENTIAL_ARGUMENT'))
                numerics.append('UNEVALUABLE')
                memory.append('UNEVALUABLE')
                continue
            finite = expm(argument)
            numerical = initial @ finite
            matrix = arb_mat(m,m,[ball(value*F(time)) for row in generator for value in row])
            exact = exact_initial * matrix.exp()
            if not np.isfinite(numerical).all() or any(not exact[0,j].is_finite() for j in range(m)):
                curves.append(dict(time_seconds=rational(F(time)),status='UNEVALUABLE',reason='NONFINITE_EXPONENTIAL_RETURN'))
                numerics.append('UNEVALUABLE')
                memory.append('UNEVALUABLE')
                continue
            difference = [abs(exact[0,j]-ball(F.from_float(float(numerical[j])))) for j in range(m)]
            numeric = status(*(_comparison(v,network.maximum_arithmetic_error) for v in difference))
            survival = sum((exact[0,j] for j in range(n)),arb(0))
            model_survival = (-ball(F(time)/(moments['mean'] if model_mean is None else model_mean))).exp()
            departures = {k:exact[0,n+j] for j,k in enumerate(outcomes)}
            errors = [abs(survival-model_survival),*(abs(departures[k]-ball(moments['probabilities'][k])*(1-model_survival)) for k in outcomes)]
            constant = status(*(_comparison(v,network.maximum_probability_error) for v in errors))
            curves.append(dict(time_seconds=rational(F(time)),survival_enclosure=_bounds(survival),
                outcome_probability_enclosures={k:_bounds(v) for k,v in departures.items()},
                exponential_survival_enclosure=_bounds(model_survival),
                absolute_constant_hazard_error_enclosures=[_bounds(v) for v in errors],
                scipy_probabilities=tuple(map(float,numerical)),
                absolute_numerical_error_enclosures=[_bounds(v) for v in difference],
                numerical_assessment=numeric,constant_hazard_assessment=constant))
            numerics.append(numeric)
            memory.append(constant)
    return dict(numerical_assessment=status(*numerics),constant_hazard_assessment=status(*memory),curves=curves,
        verification_precision_bits=network.verification_precision_bits,
        scope='EXACT_ENTERED_RATE_MODEL_WITH_SCIPY_PROPAGATION_AND_INDEPENDENT_ARB_ENCLOSURES')


def summarize_network(network, moments, *, input_assessments):
    dynamics = assess_network_dynamics(network,moments)
    mean,second = moments['mean'],moments['second_moment']
    squared_cv = (second-mean*mean)/(mean*mean)
    cv_status = 'SATISFIED' if abs(squared_cv-1)<=F(network.maximum_squared_cv_error) else 'FALSIFIED'
    entries = {}
    indexes = {s:i for i,s in enumerate(moments['transient_states'])}
    for entry in network.initial:
        i = indexes[entry.state_id]
        changes = {'mean_exit_time':abs(_log_fraction(moments['state_means'][i]/mean))}
        for outcome,values in moments['state_outcome_probabilities'].items():
            local,pooled = values[i],moments['probabilities'][outcome]
            changes[outcome] = abs(_log_fraction((local/moments['state_means'][i])/(pooled/mean))) if local and pooled else None
        result = 'FALSIFIED' if any(v is None for v in changes.values()) or max(changes.values())>float(network.maximum_entry_log_moment_change) else 'SATISFIED'
        entries[entry.state_id] = dict(absolute_log_moment_changes=changes,status=result)
    entry_status = status(*(r['status'] for r in entries.values()))
    complete_fates = 'UNEVALUABLE' if 'OTHER' in moments['outcomes'] else 'SATISFIED'
    closure = status(*input_assessments,dynamics['numerical_assessment'],dynamics['constant_hazard_assessment'],cv_status,entry_status,complete_fates)
    return dict(role=network.role,mean_exit_seconds=rational(mean),second_exit_moment_seconds_squared=rational(second),
        squared_coefficient_of_variation=rational(squared_cv),squared_cv_assessment=cv_status,
        outcome_probabilities={k:rational(v) for k,v in moments['probabilities'].items()},
        moment_quotients_per_second={k:rational(v) for k,v in moments['moment_quotients'].items()},
        entry_state_check=dict(status=entry_status,entries=entries),dynamics=dynamics,
        complete_outcome_reduction=complete_fates,conditional_memoryless_reduction=closure,
        interpretation='PRODUCT_PROBABILITY_DIVIDED_BY_COMPLETE_EXIT_MEAN_REQUIRES_ASSESSED_STATE_REDUCTION',
        physical_model_admission='UNEVALUABLE')


def assess_encounter_elimination(*, selection, network, moments, association_coefficient, input_assessment):
    """Compare the eliminated coefficient with the exact encounter renewal mean.

    The explicit network retains each residence and escape back to bulk.
    A bulk-to-product observation must not also be used as the association edge.
    """
    kon = F(association_coefficient)
    if kon<=0 or 'OTHER' in moments['outcomes']:
        return dict(status='UNEVALUABLE',reason='MISSING_POSITIVE_ASSOCIATION_OR_ADDITIONAL_EXIT',coefficient_per_uM_second=None)
    probability = moments['probabilities']['COMMITTED']
    mean = moments['mean']
    if not probability:
        return dict(status='UNEVALUABLE',reason='NO_SUPPORTED_PRODUCTIVE_ENCOUNTER',coefficient_per_uM_second=None)
    eliminated = kon*probability
    rows = []
    for concentration in selection.dissolved_concentration_queries_uM:
        arrival = kon*F(concentration)
        a = moments['negative_transient_generator']
        alpha = moments['initial']
        # Independent enlarged backward system: bulk wait, full internal
        # dynamics, every escape returns to bulk, commitment absorbs.
        system = [[arrival,*(-arrival*w for w in alpha),F(1)]]
        for row,escape in zip(a,moments['exit_columns']['ESCAPED'],strict=True):
            system.append([-escape,*row,F(1)])
        explicit_mean = solve(system)[0]
        renewal_mean = (1/arrival+mean)/probability
        if explicit_mean != renewal_mean:
            raise ValueError('encounter elimination differs from its independent complete network first-passage mean')
        actual_coefficient = 1/(explicit_mean*F(concentration))
        relative = (eliminated-actual_coefficient)/actual_coefficient
        # Error is relative to the explicit finite-concentration coefficient, and is
        # explicitly not a guarantee for all unmeasured concentrations.
        augmented_a = [row[:-1] for row in system]
        exits = {'COMMITTED':[F(),*moments['exit_columns']['COMMITTED']]}
        augmented = dict(negative_transient_generator=augmented_a,exit_columns=exits,initial=(F(1),*([F()]*len(alpha))),
            outcomes=('COMMITTED',),probabilities={'COMMITTED':F(1)},mean=explicit_mean)
        proposed_mean = 1/(eliminated*F(concentration))
        dynamics = assess_network_dynamics(network,augmented,
            times=tuple(F(t)*proposed_mean for t in selection.mean_time_multipliers),model_mean=proposed_mean)
        rows.append(dict(dissolved_concentration_uM=str(concentration),exact_mean_capture_seconds=rational(explicit_mean),
            finite_concentration_coefficient_per_uM_second=rational(actual_coefficient),
            elimination_relative_error=rational(relative),
            capture_distribution_check=dynamics,
            status=status(dynamics['numerical_assessment'],dynamics['constant_hazard_assessment'],
                'SATISFIED' if relative<=F(selection.maximum_elimination_relative_error) else 'FALSIFIED')))
    return dict(status=status(input_assessment,*(r['status'] for r in rows)),
        coefficient_per_uM_second=rational(eliminated),encounter_productive_probability=rational(probability),
        complete_mean_residence_seconds=rational(mean),queries=rows,
        exact_backward_equations='SATISFIED',
        scope='FIXED_ENTRY_RENEWAL_ELIMINATION_AT_SELECTED_DISSOLVED_CONCENTRATIONS',
        physical_model_admission='UNEVALUABLE')
