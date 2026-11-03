# SPDX-License-Identifier: MPL-2.0
"""Shared E1 arithmetic over authenticated values; no source or authority facade."""
from decimal import Decimal
from hashlib import sha256
import numpy as np
from scipy.stats import beta
from empirical_lawhood.adapters.methods.matrix_factor_lifetime import science as factor_science
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.products import validate_diagnostics
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.scalar_assessment import independent_scalar_closure_ratio
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_parameter_factor.independent import _control,pauli_residual,raw_operator
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import DIAGNOSTICS,METHODS as FACTOR_METHODS,expected_members as factor_members,prefix
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.status import ScientificStatus
from .records import E1RiskRow,VIEWS

def measurement_values(rule,native,*,artifact_id,initial_presence=False):
    diagnostics = {}
    for name, (dtype, shape) in factor_members(rule).items():
        diagnostics[name] = (np.asarray(rule.lattice, dtype=dtype) if name.endswith('_ticks')
            else np.zeros(shape, dtype=dtype) if dtype == '|b1' else np.full(shape, np.nan, dtype=dtype))
    trace_parts = []
    for view in VIEWS:
        for sector in rule.sectors:
            base, multiplier, index = prefix(view, sector), 1 if view == 'PRIMARY' else 2, ('X', 'Y').index(sector)
            measurements, missing, scalar = {}, {}, {}
            for i, tick in enumerate(rule.lattice):
                fields = native[view.lower()+'_positions'][multiplier*tick, index]
                alpha = native[view.lower()+'_alpha_tilde'][multiplier*tick, index]
                # Published scalar geometry is a distinct original 0.30
                # comparison; it does not select the structural factor rule.
                try:
                    scalar[tick] = independent_scalar_closure_ratio(fields, alpha)
                except ValueError:
                    scalar[tick] = None
                try:
                    measured = factor_science.measure_sector(fields, rule)
                    operator = algebra.operator(fields)
                    values, vectors = np.linalg.eigh(operator)
                    if not np.array_equal(values, measured.spectrum):
                        raise ValueError('E1 spectral witness differs from its measured complete spectrum')
                except np.linalg.LinAlgError:
                    measurements[tick], missing[tick] = None, 'NUMERICAL_INVALID'
                    continue
                measurements[tick] = measured
                diagnostics[base+'available'][i] = True
                diagnostics[base+'identifiable'][i] = measured.identifiable
                for name in ('spectrum', 'projector', 'basis'):
                    diagnostics[base+name][i] = getattr(measured, name)
                diagnostics[base+'operator'][i], diagnostics[base+'eigenvectors'][i] = operator, vectors
                if measured.identifiable:
                    diagnostics[base+'factor'][i] = measured.factor
            observations, frames = factor_science.causal_observations(rule, measurements,
                unavailable=missing, scalar_closure=scalar, initial_presence=initial_presence)
            for i, tick in enumerate(rule.lattice):
                if tick in frames:
                    diagnostics[base+'aligned_factor'][i] = frames[tick]
            trace_parts.append((view, sector, observations, factor_science.lifetime(observations, rule),
                                factor_science.lifetime(observations, rule, origin_fixed=True)))
    nonfinite = tuple(n for n in diagnostics if not n.endswith(('_ticks', '_available', '_identifiable')))
    raw, members = encode_matrix_arrays(diagnostics, nonfinite_members=nonfinite)
    artifact = ArtifactIdentity(artifact_id, 'e1-factor-diagnostics', MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), 'application/x-npz', len(raw))
    return raw,members,artifact,tuple(trace_parts)

def factor_control_values(rule,design,traces,native,arrays):
    errors, applicable = {method: [] for method in FACTOR_METHODS}, []
    for trace in traces:
        base = prefix(trace.view, trace.sector)
        diag = {name: arrays[base+name] for name in DIAGNOSTICS}
        validate_diagnostics(diag, trace, rule)
        multiplier, sector_index = 1 if trace.view == 'PRIMARY' else 2, ('X', 'Y').index(trace.sector)
        for i, observation in enumerate(trace.observations):
            fields = native[trace.view.lower()+'_positions'][multiplier*observation.tick, sector_index]
            alpha = native[trace.view.lower()+'_alpha_tilde'][multiplier*observation.tick, sector_index]
            try:
                ratio = independent_scalar_closure_ratio(fields, alpha)
            except ValueError:
                ratio = None
            if (ratio is None) != (observation.scalar_closure_ratio is None):
                raise ValueError('E1 scalar contrast manufactures missingness')
            errors['scalar-contrast'].append(None if ratio is None else abs(float(ratio-observation.scalar_closure_ratio)))
            available, identified = bool(diag['available'][i]), bool(diag['identifiable'][i])
            applicable.append(not available or identified)
            errors['pauli-factor'].append(pauli_residual(diag['factor'][i]) if identified else None)
            op, vectors = arrays[base+'operator'][i], arrays[base+'eigenvectors'][i]
            if not available:
                if not np.isnan(op).all() or not np.isnan(vectors).all():
                    raise ValueError('E1 unavailable witness manufactures eigenpairs')
                for name in ('raw-operator', 'eigenvector-orthogonality', 'slow-projector'):
                    errors[name].append(None)
                errors['all-eigenpairs'].extend([None]*15)
                continue
            spectrum = diag['spectrum'][i]
            if (not np.isfinite(op).all() or not np.isfinite(vectors).all() or not np.isfinite(spectrum).all()
                    or np.any(np.diff(spectrum) < 0)):
                raise ValueError('E1 witness omits finite ordered complete 15 eigenpairs')
            formed = raw_operator(fields)
            errors['raw-operator'].append(np.linalg.norm(op-formed))
            errors['all-eigenpairs'].extend(np.linalg.norm(formed@vectors-vectors*spectrum[None, :], axis=0))
            errors['eigenvector-orthogonality'].append(np.linalg.norm(vectors.T@vectors-np.eye(15)))
            errors['slow-projector'].append(np.linalg.norm(diag['projector'][i]-vectors[:, :3]@vectors[:, :3].T))
    tolerances = (design.operator_tolerance, design.eigenpair_tolerance, design.orthogonality_tolerance,
                  design.projector_tolerance, design.factor_tolerance, design.scalar_tolerance)
    controls = tuple(_control(name, errors[name], tol, dimension, applicable if name == 'pauli-factor' else None)
        for name, tol, dimension in zip(FACTOR_METHODS, tolerances, (225, 15, 225, 225, 48, 1), strict=True))
    n = len(VIEWS)*len(rule.sectors)*len(rule.lattice)
    if tuple(len(c.measured_errors) for c in controls) != (n, 15*n, n, n, n, n):
        raise ValueError('E1 independent factor assessment loses full tick/eigenpair denominator')
    return controls

def _survival(life, end_tick):
    if life.origin_tick is None:
        return 'NOT_AT_RISK'
    if life.last_known_survival_tick >= end_tick:
        return 'SUCCESS'
    if life.exit_upper_tick is not None and life.exit_upper_tick <= end_tick:
        return 'FAILURE'
    if life.disposition == 'RIGHT_CENSORED':
        return 'CENSORED_BEFORE_HORIZON'
    return 'UNKNOWN'

def population_values(sources,received,checked,missing,*,criterion,rule,alpha,identity,survival_origin_end_tick=None):
    findings, risk_rows = [], []
    for requirement in criterion.family_requirements:
        local = tuple((s, received[identity(s)], checked[identity(s)]) for s in sources
            if s.coordinate.family_id == requirement.family_id and identity(s) not in missing)
        unavailable_count = sum(s.coordinate.family_id == requirement.family_id and identity(s) in missing for s in sources)
        for view in criterion.views:
            for sector in rule.sectors:
                traces = tuple(next(t for t in p.traces if (t.view, t.sector) == (view, sector)) for _, p, _ in local)
                admitted = sum(t.moving_lifetime.origin_tick is not None for t in traces)
                left = sum(t.moving_lifetime.onset == 'LEFT_PRESENT' for t in traces)
                newly = sum(t.moving_lifetime.onset == 'OBSERVED_ADMISSION' for t in traces)
                never = sum(t.moving_lifetime.disposition == 'NOT_AT_RISK' for t in traces)
                unknown = unavailable_count+sum(t.moving_lifetime.origin_tick is None and t.moving_lifetime.disposition == 'UNKNOWN' for t in traces)
                numeric = unavailable_count == 0 and all(p.history_numerical_pass and a.numerical_pass for _, p, a in local)
                groups = requirement.requested_roots
                for tick_index, tick in enumerate(rule.lattice):
                    obs = tuple(t.observations[tick_index] for t in traces)
                    left_traces = tuple(t for t in traces if t.moving_lifetime.onset == 'LEFT_PRESENT')
                    left_unknown = sum(bool(t.moving_lifetime.unavailable_ticks and t.moving_lifetime.unavailable_ticks[0] <= tick) for t in left_traces)
                    left_exited = sum(t.moving_lifetime.exit_upper_tick is not None and t.moving_lifetime.exit_upper_tick <= tick for t in left_traces)
                    risk_rows.append(E1RiskRow(requirement.family_id, view, sector, tick, requirement.requested_roots,
                        sum(o.status == 'AVAILABLE' for o in obs), sum(o.status == 'UNIDENTIFIABLE' for o in obs),
                        unavailable_count+sum(o.status in ('UNAVAILABLE', 'NUMERICAL_INVALID') for o in obs),
                        sum(o.raw_admitted is True for o in obs), sum(o.causal_admitted is True for o in obs),
                        sum(t.moving_lifetime.origin_tick == tick for t in traces),
                        sum(t.moving_lifetime.origin_tick is not None and t.moving_lifetime.origin_tick <= tick for t in traces),
                        left, left-left_exited-left_unknown if tick >= rule.risk_start_tick else 0,
                        left_exited, left_unknown))
                for endpoint in ('RECURRENCE', *criterion.survival_endpoints):
                    success = fail = censored = excluded_late = 0
                    unresolved = unavailable_count if endpoint == 'RECURRENCE' else 0
                    risk = unavailable_count if endpoint == 'RECURRENCE' else 0
                    for trace in traces:
                        life = trace.moving_lifetime
                        if endpoint == 'RECURRENCE':
                            risk += 1
                            observations = tuple(o for o in trace.observations if rule.risk_start_tick <= o.tick <= criterion.recurrence_end_tick)
                            if criterion.recurrence_estimand == 'EVER_CAUSALLY_ADMITTED_IN_RISK_WINDOW':
                                ok = any(o.causal_admitted is True for o in observations)
                                uncertain = any(o.causal_admitted is None for o in observations)
                            else:
                                ok = life.onset == 'OBSERVED_ADMISSION' and life.origin_tick <= criterion.recurrence_end_tick
                                uncertain = any(o.causal_admitted is None for o in observations) or (
                                    life.onset == 'UNRESOLVED_ADMISSION' and life.origin_tick <= criterion.recurrence_end_tick)
                            success += bool(ok)
                            unresolved += bool(not ok and uncertain)
                            fail += bool(not ok and not uncertain)
                        elif life.origin_tick is not None:
                            if survival_origin_end_tick is not None and life.origin_tick > survival_origin_end_tick:
                                excluded_late += 1
                                continue
                            risk += 1
                            if survival_origin_end_tick is not None and life.onset == 'UNRESOLVED_ADMISSION':
                                unresolved += 1
                                continue
                            horizon = life.origin_tick+criterion.survival_duration_ticks
                            outcomes = tuple(_survival(x, horizon) for x in
                                ((trace.moving_lifetime, trace.origin_fixed_lifetime) if endpoint == 'BOTH'
                                 else (trace.moving_lifetime,) if endpoint == 'MOVING' else (trace.origin_fixed_lifetime,)))
                            state = ('FAILURE' if 'FAILURE' in outcomes else 'SUCCESS' if all(x == 'SUCCESS' for x in outcomes)
                                else 'UNKNOWN' if 'UNKNOWN' in outcomes else 'CENSORED_BEFORE_HORIZON')
                            success += state == 'SUCCESS'
                            fail += state == 'FAILURE'
                            censored += state == 'CENSORED_BEFORE_HORIZON'
                            unresolved += state == 'UNKNOWN'
                    required = requirement.required_recurrence_probability if endpoint == 'RECURRENCE' else requirement.required_survival_probability
                    lower = Decimal(0) if success == 0 else Decimal(str(float(beta.ppf(float(alpha), success, risk-success+1))))
                    unresolved_onset = sum(t.moving_lifetime.onset == 'UNRESOLVED_ADMISSION' for t in traces)
                    evaluable = bool(numeric and unresolved == 0 and censored == 0 and
                        (endpoint == 'RECURRENCE' or survival_origin_end_tick is None or unresolved_onset == 0) and
                        (risk == requirement.requested_roots if endpoint == 'RECURRENCE' else risk >= requirement.minimum_admitted_roots and unknown == 0))
                    findings.append(dict(family_id=requirement.family_id,view=view,sector=sector,endpoint=endpoint,
                        requested_roots=requirement.requested_roots,independent_units=groups,admitted_roots=admitted,
                        left_present_roots=left,observed_new_admissions=newly,never_admitted_roots=never,
                        unknown_admission_roots=unknown,risk_roots=risk,successes=success,failures=fail,
                        censored_before_horizon=censored,unresolved_roots=unresolved,
                        excluded_late_survival_roots=excluded_late,unresolved_onset_roots=unresolved_onset,
                        probability_lower=lower,required_probability=required,evaluable=evaluable))

    complete = all(f['evaluable'] for f in findings)
    simultaneous = criterion.multiplicity == 'BONFERRONI_FROZEN_FAMILY_VIEW_SECTOR_ENDPOINT_MENU'
    supported = all(f['probability_lower'] >= f['required_probability'] for f in findings)
    status = (ScientificStatus.UNEVALUABLE if not complete else ScientificStatus.PARTIAL if supported and not simultaneous
              else ScientificStatus.SUPPORTED if supported else ScientificStatus.NOT_SUPPORTED)
    reasons = ('e1-unresolved-numerical-admission-risk-or-censoring',) if not complete else (
        'e1-marginal-cells-no-full-study-claim',) if supported and not simultaneous else (
        'e1-frozen-full-family-recurrence-survival-supported',) if supported else ('e1-frozen-full-family-recurrence-survival-not-supported',)
    return tuple(findings),tuple(risk_rows),status,reasons
