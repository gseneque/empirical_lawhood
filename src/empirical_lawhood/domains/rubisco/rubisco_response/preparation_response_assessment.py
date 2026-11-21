# SPDX-License-Identifier: MPL-2.0
"""Complete local response, mutation-error and preparation-benefit assessment."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_action_read import direction_values
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, POSITIONS, is_environmental, require_response_design, response_effects, response_stages, diagnostic_stages, primary_response_frame
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import PreparationResponsePointReadout
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import PreparationResponsePrediction, read_response_center

from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment_records import LABELS, PreparationResponseAction, PreparationResponseAssessment, PreparationResponseCoverage, PreparationResponseFinding, PreparationResponseQuantity, EnvironmentalPreparationResponseAssessment, require_response_assessment


def _decimal(value):
    return value if value is None or type(value) is Decimal else Decimal.from_float(float(value))


def _difference(later, initial):
    """Keep the exact finite Decimal contrast of the retained numerical values."""
    if later is None or initial is None:
        return None
    with localcontext() as context:
        context.prec = max(later.adjusted(), initial.adjusted()) - min(
            later.as_tuple().exponent, initial.as_tuple().exponent) + 3
        return later - initial


def _magnitude(value):
    return None if value is None else value.copy_abs()


def _product(left, right):
    with localcontext() as context:
        context.prec = len(left.as_tuple().digits) + len(right.as_tuple().digits) + 2
        return left * right


def assess_response_operands(*, design, centers, frames, center_bytes, selected_points, readouts, values,
                            assessor_source, assessment_id):
    """Pure calculation over freshly authenticated operands; called by the owning reader.

    `values` contains complete native gradient arrays, never a scalar summary.
    The public reader owns authentication and preserves every missing point.
    """
    import numpy  # noqa: F401 -- Load BLAS before selecting the assessor's thread count.
    from threadpoolctl import threadpool_limits
    # The registered non-native assessor has one CPU core. Direct preparation
    # and independent reading must reproduce that same numerical reduction.
    with threadpool_limits(limits=1):
        return _assess_response_operands(design=design, centers=centers, frames=frames,
            center_bytes=center_bytes, selected_points=selected_points, readouts=readouts, values=values,
            assessor_source=assessor_source, assessment_id=assessment_id)


def _assess_response_operands(*, design, centers, frames, center_bytes, selected_points, readouts, values,
                             assessor_source, assessment_id):
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import BOHR_ANGSTROM
    require_response_design(design)
    environmental = is_environmental(design)
    expected = tuple(e for stage in response_stages(design) for e in response_effects(design, stage))
    by_effect = {e.effect_id: e for e in expected}
    if (set(selected_points) - set(by_effect) or set(readouts) - set(selected_points) or set(values) - set(readouts)
            or set(centers) != set(POSITIONS) or set(frames) != set(MODELS) or set(center_bytes) != set(POSITIONS)):
        raise ValueError('response assessment changes its assigned effects or four nested state operands')
    center_arrays = {key: read_response_center(center, center_bytes[key]) for key, center in centers.items()}
    if environmental:
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import validate_environmental_primary_frame
        for model, frame in frames.items():
            validate_environmental_primary_frame(design=design, frame=frame, coordinates=center_arrays[model, 'initial'][0])
    directions = {model: {role: None if getattr(frame, role) is None else direction_values(getattr(frame, role), frame.primary.physical_atom_count)
                         for role in ('primary', 'additional', 'challenge')} for model, frame in frames.items()}
    coverage, evidence = [], []
    for effect in expected:
        key = effect.effect_id
        point, readout, value = selected_points.get(key), readouts.get(key), values.get(key)
        if point is not None:
            center, frame = centers[effect.model_name, effect.position], frames[effect.model_name]
            if effect.stage == 'initial-primary':
                frame = primary_response_frame(frame)
            if (point.effect != effect or point.center != center.identity or point.frame != frame.identity
                    or center.design != design.identity or frame.design != design.identity
                    or center.original_readout.original_result.prefix != design.prefix):
                raise ValueError('response assessment substitutes original effect, center or fixed frame')
        if readout is not None:
            exact(readout, PreparationResponsePointReadout)
            if readout.point != point:
                raise ValueError('response assessment substitutes an original selected readout')
            evidence.append(readout.identity)
        if value is not None:
            if (readout.numerical_findings or readout.original.original_result.returned.error is not None
                    or type(value) is not tuple or len(value) != 2
                    or not np.isfinite(value[0]) or value[1].dtype.str != '<f8'
                    or value[1].shape != center_arrays[effect.model_name, effect.position][0].shape
                    or not np.isfinite(value[1]).all()):
                raise ValueError('response assessment substitutes a complete finite native force')
        state = ('AVAILABLE' if value is not None else 'UNAVAILABLE' if readout is not None
                 else 'NOT_ENTERED' if point is not None or effect.stage != 'additional-refinement' else 'NOT_SELECTED')
        coverage.append(PreparationResponseCoverage(effect.identity, effect.stage, state,
            None if point is None else point.identity, None if readout is None else readout.identity))
    by_query = {(e.model_name, e.position, e.direction, e.signed_step_bohr): e for e in expected if e.stage != 'challenge'}
    action_rows, arrays, action_values = [], [], {}
    for model, position in POSITIONS:
        for role in ('primary', 'additional') if position == 'later' else ('primary',):
            for step in design.steps_bohr:
                minus, plus = (by_query[model, position, role, sign * step] for sign in (-1, 1))
                original = center_arrays[model, position][0]
                pair = (values.get(minus.effect_id), values.get(plus.effect_id))
                manifest = secant = midpoint = None
                if all(v is not None for v in pair):
                    action = np.asarray((pair[1][1] - pair[0][1]) / float(2 * step), dtype='<f8')
                    if not np.isfinite(action).all():
                        raise ValueError('response action arithmetic is nonfinite')
                    direction = directions[model][role]
                    delta = float(step * BOHR_ANGSTROM) * direction
                    xm, xp = original - delta, original + delta
                    secant = _decimal(np.max(np.abs((xp - xm) / float(2 * step * BOHR_ANGSTROM) - direction)))
                    midpoint = _decimal(np.max(np.abs((xp - original) + (xm - original))) / float(2 * BOHR_ANGSTROM))
                    references = tuple(sorted((selected_points[minus.effect_id].identity, selected_points[plus.effect_id].identity,
                        getattr(frames[model], role).identity), key=lambda p: p.object_id))
                    manifest = ArrayDatasetManifest('arrays.preparation-response.' + plus.fingerprint(),
                        (ArrayDatasetMember('cartesian-hessian-action', '<f8', action.shape, sha256(action.tobytes()).hexdigest()),), references)
                    arrays.append((manifest, action))
                    action_values[model, position, role, step] = action
                action_rows.append(PreparationResponseAction(model, position, role, step, minus.identity, plus.identity,
                    manifest, secant, midpoint))
    nomination = None
    if environmental:
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import nominate_response_environment, prepare_environmental_frames, validate_environmental_frame
        nomination = nominate_response_environment(design=design, centers=centers, frames=frames,
            center_arrays=center_arrays, actions=action_rows, action_values=action_values, readouts=readouts)
        final_selected = any(p.effect.stage != 'initial-primary' for p in selected_points.values())
        if final_selected and nomination.disposition != 'AVAILABLE':
            raise ValueError('environmental acquisition follows an unavailable original nomination')
        if nomination.disposition == 'AVAILABLE':
            nominated_frames = prepare_environmental_frames(design=design, frames=frames, nomination=nomination)
            for model, frame in frames.items():
                if frame.additional is not None:
                    validate_environmental_frame(design=design, frame=frame, nomination=nomination)
            if final_selected and any(f.additional is None for f in frames.values()):
                raise ValueError('environmental effects lack the original frozen nominated frame')
            directions = {model: {role: direction_values(getattr(frame, role), frame.primary.physical_atom_count)
                for role in ('primary', 'additional', 'challenge')} for model, frame in nominated_frames.items()}
    quantities, metrics = [], {}
    def add(name, model, position, value, unit='hartree/bohr'):
        number = _decimal(value)
        metrics[name, model, position] = number
        quantities.append(PreparationResponseQuantity(name, model, position, number, unit))
        return number
    alpha, big, small = float(design.challenge_amplitude_bohr), *design.steps_bohr
    for model, position in POSITIONS:
        u, v, w = (directions[model][role] for role in ('primary', 'additional', 'challenge'))
        _, gradient = center_arrays[model, position]
        receiver = add('base-receiver', model, position, -np.vdot(u, gradient))
        large, fine = (action_values.get((model, position, 'primary', step)) for step in (big, small))
        # The chemical challenge splits amplitude equally between orthogonal
        # primary/additional directions; the environmental challenge uses its
        # independently nominated direction at the full authored amplitude.
        weight = alpha if environmental else alpha / np.sqrt(2.)
        predicted = add('predicted-change', model, position, None if fine is None or w is None else -alpha * np.vdot(w, fine))
        add('scalar-predicted-change', model, position, Decimal(0) if environmental
            else None if fine is None else -weight * np.vdot(u, fine))
        add('omitted-coupling-change', model, position, None if fine is None or v is None else -weight * np.vdot(v, fine))
        add('prediction-scale-discrepancy', model, position,
            None if fine is None or large is None or w is None else alpha * abs(np.vdot(w, fine - large)))
        add('scalar-scale-discrepancy', model, position,
            Decimal(0) if environmental else None if fine is None or large is None else weight * abs(np.vdot(u, fine - large)))
        add('coupling-scale-discrepancy', model, position,
            None if fine is None or large is None or v is None else weight * abs(np.vdot(v, fine - large)))
        checks = [metrics[name, model, position] for name in (
            'prediction-scale-discrepancy', 'scalar-scale-discrepancy', 'coupling-scale-discrepancy')]
        add('primary-receiver-numerical-discrepancy', model, position,
            None if any(value is None for value in checks) else max(checks))
        add('complete-action-scale-discrepancy', model, position,
            None if fine is None or large is None else np.linalg.norm(fine - large), 'hartree/bohr2')
        add('complete-action-norm', model, position, None if fine is None else np.linalg.norm(fine), 'hartree/bohr2')
        add('orthogonal-action-norm', model, position,
            None if fine is None else np.linalg.norm(fine - np.vdot(u, fine) * u), 'hartree/bohr2')
        challenge = next(e for e in response_effects(design, 'challenge') if (e.model_name, e.position) == (model, position))
        actual = values.get(challenge.effect_id)
        observed = add('observed-change', model, position, None if actual is None else -np.vdot(u, actual[1]) - float(receiver))
        point = selected_points.get(challenge.effect_id)
        frozen = None if point is None else point.prediction
        if frozen is not None:
            expected_action = next(row.action for row in action_rows if (row.model_name, row.position, row.direction, row.step_bohr)
                == (model, position, 'primary', small))
            if (frozen.primary_action != expected_action or frozen.predicted_change_hartree_per_bohr != predicted
                    or frozen.base_receiver_hartree_per_bohr != receiver):
                raise ValueError('challenge prediction changes after its withheld native observation')
        error = add('signed-prediction-error', model, position,
            None if frozen is None else _difference(observed, frozen.predicted_change_hartree_per_bohr))
        add('scalar-prediction-error', model, position,
            None if frozen is None else _difference(observed, frozen.scalar_change_hartree_per_bohr))
        add('zero-response-error', model, position, observed)
        add('absolute-prediction-error', model, position, _magnitude(error))
        add('error-over-signal', model, position,
            None if error is None or not observed else abs(error / observed), 'dimensionless')
        if position == 'later':
            additional_big = action_values.get((model, position, 'additional', big))
            additional_small = action_values.get((model, position, 'additional', small))
            add('reciprocal-coupling-discrepancy', model, position,
                None if additional_big is None or large is None or v is None else np.vdot(u, additional_big) - np.vdot(v, large), 'hartree/bohr2')
            add('reciprocal-receiver-discrepancy', model, position,
                None if additional_big is None or large is None or v is None else weight
                * abs(np.vdot(u, additional_big) - np.vdot(v, large)))
            add('additional-action-scale-discrepancy', model, position,
                None if additional_small is None or additional_big is None else np.linalg.norm(additional_small - additional_big), 'hartree/bohr2')
            add('additional-receiver-scale-discrepancy', model, position,
                None if additional_small is None or additional_big is None else weight
                * abs(np.vdot(u, additional_small - additional_big)))
            if environmental:
                add('fine-reciprocal-receiver-discrepancy', model, position,
                    None if additional_small is None or fine is None or v is None else alpha
                    * abs(np.vdot(u, additional_small) - np.vdot(v, fine)))
    def get(name, model, position):
        return metrics.get((name, model, position))
    def difference(name, model, output):
        initial, later = (get(name, model, position) for position in ('initial', 'later'))
        return add(output, model, 'later-minus-initial', _difference(later, initial))
    for model in MODELS:
        before, after = (action_values.get((model, position, 'primary', small)) for position in ('initial', 'later'))
        add('operator-action-change', model, 'later-minus-initial',
            None if before is None or after is None else np.linalg.norm(after - before), 'hartree/bohr2')
        difference('predicted-change', model, 'operator-prediction-change')
        difference('absolute-prediction-error', model, 'absolute-error-change')
        add('stale-operator-prediction-error', model, 'later',
            _difference(get('observed-change', model, 'later'), get('predicted-change', model, 'initial')))
        initial_signal, later_signal = (_magnitude(get('observed-change', model, p)) for p in ('initial', 'later'))
        add('absolute-signal-change', model, 'later-minus-initial', _difference(later_signal, initial_signal))
        for position in ('initial', 'later'):
            error, signal = (_magnitude(get(name, model, position)) for name in ('signed-prediction-error', 'observed-change'))
            add('error-minus-zero-response-error', model, position, _difference(error, signal))
        for name, unit in (('wall_seconds', 'wall-seconds'), ('cpu_seconds', 'cpu-seconds'), ('retained_bytes', 'bytes')):
            cost = centers[model, 'initial'].original_readout.original_result.unit.completion.cost
            # Monetary cost is supplied by the independent provider ledger.
            add('preparation-' + name.replace('_', '-'), model, 'later-minus-initial', getattr(cost, name), unit)
    for position in ('initial', 'later'):
        for name in ('signed-prediction-error', 'observed-change', 'predicted-change'):
            mutant, wt = get(name, 'm1-i95m', position), get(name, 'm1-wt', position)
            add('paired-' + name, 'I95M-minus-WT', position, _difference(mutant, wt))
    paired_before, paired_after = (get('paired-signed-prediction-error', 'I95M-minus-WT', p) for p in ('initial', 'later'))
    add('paired-absolute-error-change', 'I95M-minus-WT', 'later-minus-initial',
        _difference(_magnitude(paired_after), _magnitude(paired_before)))
    questions = _questions(design, tuple(quantities), tuple(evidence))
    decision = next_response_supplier(questions)
    kind = EnvironmentalPreparationResponseAssessment if environmental else PreparationResponseAssessment
    report = kind(assessment_id, design, assessor_source, tuple(coverage), tuple(action_rows),
        tuple(quantities), questions, decision, **(dict(nomination=nomination) if environmental else {}))
    if environmental:
        report = replace(report, next_supplier_decision=response_supplier_decision(report))
    return report, tuple(arrays)


def _questions(design, quantities, evidence):
    tolerance = design.useful_error_hartree_per_bohr
    numeric = _product(tolerance, design.numerical_allowance_fraction)
    paired_tolerance = _product(Decimal(2), tolerance)
    def select(*names):
        return tuple(q for q in quantities if q.name in names)
    def complete(rows):
        return sum(q.value is not None for q in rows)
    def any_large(rows, bound):
        return any(q.value is not None and q.value.copy_abs() > bound for q in rows)
    checks = select('primary-receiver-numerical-discrepancy', 'reciprocal-receiver-discrepancy')
    extra_checks = select('additional-receiver-scale-discrepancy', 'fine-reciprocal-receiver-discrepancy')
    coupling = select('omitted-coupling-change')
    operator = select('operator-prediction-change')
    errors = select('signed-prediction-error')
    paired = select('paired-signed-prediction-error')
    benefit = select('absolute-error-change')
    numerical = ('CONSEQUENTIAL_SCALE_SENSITIVITY' if any_large(checks + extra_checks, numeric)
                 else 'EMPIRICALLY_CONSISTENT' if complete(checks) == 6 else 'UNAVAILABLE')
    metrics = {(q.name, q.model_name, q.position): q.value for q in quantities}
    def get(name, model, position):
        return metrics.get((name, model, position))
    def within(position):
        values = [get('signed-prediction-error', model, position) for model in MODELS]
        return all(value is not None and value.copy_abs() <= tolerance for value in values)
    if complete(errors) != 4:
        finite = 'OBSERVED_FINITE_MISMATCH_INCOMPLETE' if any_large(errors, tolerance) else 'UNAVAILABLE'
    elif numerical != 'EMPIRICALLY_CONSISTENT':
        finite = 'NUMERICALLY_UNRESOLVED'
    elif within('later'):
        finite = 'WITHIN_SELECTED_ERROR_ALL_POSITIONS' if within('initial') else 'WITHIN_SELECTED_ERROR_AFTER_PREPARATION'
    else:
        finite = 'PREPARATION_LOSES_LOCAL_APPLICABILITY' if within('initial') else 'FINITE_RESPONSE_REMAINDER_UNRESOLVED'
    benefit_disposition = _preparation_benefit(metrics, tolerance=tolerance, numeric=numeric, numerical=numerical)
    rows = (
        (numerical,
         select('primary-receiver-numerical-discrepancy', 'prediction-scale-discrepancy', 'scalar-scale-discrepancy',
             'coupling-scale-discrepancy', 'complete-action-scale-discrepancy', 'reciprocal-receiver-discrepancy',
             'additional-receiver-scale-discrepancy', 'fine-reciprocal-receiver-discrepancy'), checks, 6,
         ('Four environmental projections of the primary scale difference and two reciprocal receiver checks must agree empirically. '
          'The scalar floor is exactly zero. The additional half-scale and native force bound remain separate.'
          if is_environmental(design) else
          'Four primary scale comparisons and two reciprocal receiver checks must agree empirically. Cancellation in the mixed projection cannot hide scalar/coupling sensitivity. The additional half-scale and native force bound remain separate.')),
        ('NUMERICALLY_UNRESOLVED' if numerical != 'EMPIRICALLY_CONSISTENT' else
            'CONSEQUENTIAL_OMITTED_COUPLING' if any_large(coupling, tolerance) else 'SMALL_SELECTED_OMISSION' if complete(coupling) == 4 else 'UNAVAILABLE',
         select('omitted-coupling-change', 'orthogonal-action-norm', 'reciprocal-coupling-discrepancy',
             'additional-action-scale-discrepancy', 'scalar-prediction-error', 'signed-prediction-error'), coupling, 4,
         ('Compare the zero local prediction with the frozen cross-interface prediction on the same pure environmental challenge. '
          'This one selected common-protein direction does not identify an I95M mechanism or bound all omitted dependence.'
          if is_environmental(design) else
          'Compare the scalar and coupled predictions against the same withheld response. The named bond-sum pathway does not bound every environmental coupling; a reciprocal discrepancy requests numerical refinement.')),
        ('NUMERICALLY_UNRESOLVED' if numerical != 'EMPIRICALLY_CONSISTENT' else
            'CONSEQUENTIAL_OPERATOR_CHANGE' if any_large(operator, tolerance) else 'SMALL_SELECTED_CHANGE' if complete(operator) == 2 else 'UNAVAILABLE',
         select('operator-prediction-change', 'operator-action-change', 'stale-operator-prediction-error', 'signed-prediction-error'), operator, 2,
         'Update response information at the prepared state when the fixed-frame prediction changes consequentially; preparation order is not physical time.'),
        (finite,
         select('predicted-change', 'observed-change', 'signed-prediction-error', 'error-over-signal'), errors, 4,
         'Keep initial and prepared outcomes distinct. A prepared pass can succeed despite an initial failure. An unexplained finite remainder is not uniquely attributed to nonlinearity while native force uncertainty is unavailable.'),
        ('NUMERICALLY_UNRESOLVED' if numerical != 'EMPIRICALLY_CONSISTENT' else
            'CONSEQUENTIAL_MUTATION_ERROR' if any_large(paired, paired_tolerance) else 'WITHIN_PAIRED_ERROR_ALLOWANCE' if complete(paired) == 2 else 'UNAVAILABLE',
         select('paired-signed-prediction-error', 'paired-observed-change', 'paired-predicted-change'), paired, 2,
         'Use I95M-minus-WT signed errors directly. The paired allowance is twice the per-position error; no biological uncertainty is estimated.'),
        (benefit_disposition,
         select('absolute-error-change', 'paired-absolute-error-change', 'observed-change', 'error-over-signal',
             'absolute-signal-change', 'zero-response-error', 'error-minus-zero-response-error',
             'preparation-wall-seconds', 'preparation-cpu-seconds', 'preparation-retained-bytes'), benefit, 2,
         'Require a useful prepared response, improvement beyond observed numerical sensitivity, performance better than zero response and no consequential paired-error deterioration. Signal suppression remains a separate finding. Report the actual prefix cost; cost effectiveness and future acquisition savings require the shared monetary/work account.'),
    )
    pins = tuple(sorted(set(evidence), key=lambda p: p.object_id))
    return tuple(PreparationResponseFinding('Q' + str(i), LABELS[i - 1], disposition, selected, assigned,
        complete(required), pins, consequence) for i, (disposition, selected, required, assigned, consequence) in enumerate(rows, 1))


def _preparation_benefit(metrics, *, tolerance, numeric, numerical):
    """Interpret the same four challenges without selecting favorable positions."""
    def get(name, model, position):
        return metrics.get((name, model, position))
    errors = {(m, p): get('signed-prediction-error', m, p) for m, p in POSITIONS}
    signals = {(m, p): get('observed-change', m, p) for m, p in POSITIONS}
    if any(v is None for v in (*errors.values(), *signals.values())):
        return 'UNAVAILABLE'
    if numerical != 'EMPIRICALLY_CONSISTENT':
        return 'NUMERICALLY_UNRESOLVED'
    if any(signals[m, 'later'].copy_abs() <= tolerance for m in MODELS):
        return 'SIGNAL_TOO_SMALL_FOR_PREPARATION_BENEFIT'
    paired_change = get('paired-absolute-error-change', 'I95M-minus-WT', 'later-minus-initial')
    if paired_change is None:
        return 'UNAVAILABLE'
    if paired_change > _product(Decimal(2), numeric):
        return 'PAIRED_ERROR_WORSENS_DESPITE_PREPARATION'
    if any(errors[m, 'later'].copy_abs() >= signals[m, 'later'].copy_abs() for m in MODELS):
        return 'NO_BENEFIT_OVER_ZERO_RESPONSE'
    # A smaller signal with no relative-error gain cannot establish an improved
    # response description. Exact cross multiplication avoids unstable ratios.
    for model in MODELS:
        before, after = (signals[model, p].copy_abs() for p in ('initial', 'later'))
        old_error, new_error = (errors[model, p].copy_abs() for p in ('initial', 'later'))
        if (before and _difference(after, before) < numeric.copy_negate()
                and Fraction(new_error) * Fraction(before) >= Fraction(old_error) * Fraction(after)):
            return 'ERROR_REDUCTION_CONFOUNDED_BY_SIGNAL_SUPPRESSION'
    if any(errors[m, 'later'].copy_abs() > tolerance for m in MODELS):
        return 'PREPARATION_NOT_SUFFICIENT_FOR_SELECTED_CHALLENGE'
    if all(errors[m, 'initial'].copy_abs() <= tolerance for m in MODELS):
        return 'PREPARATION_NOT_NEEDED_FOR_SELECTED_TOLERANCE'
    changes = [_difference(errors[m, 'later'].copy_abs(), errors[m, 'initial'].copy_abs()) for m in MODELS]
    if any(value > numeric for value in changes) or not any(value < numeric.copy_negate() for value in changes):
        return 'PREPARATION_BENEFIT_NOT_RESOLVED_BEYOND_SCALE_SENSITIVITY'
    later_paired_signal = get('paired-observed-change', 'I95M-minus-WT', 'later')
    if later_paired_signal is None:
        return 'UNAVAILABLE'
    if later_paired_signal.copy_abs() <= _product(Decimal(2), tolerance):
        return 'PREPARATION_IMPROVES_ARMS_PAIRED_SIGNAL_BELOW_ALLOWANCE'
    return 'PREPARATION_ESTABLISHES_LOCAL_APPLICABILITY'


def next_response_supplier(questions):
    """Choose a scientific requirement, never financial or execution authority."""
    q1, q2, q3, q4, q5, q6 = questions
    if q1.disposition == 'CONSEQUENTIAL_SCALE_SENSITIVITY':
        return 'RESOLVE_NUMERICAL_OR_RECIPROCAL_DISCREPANCY_BEFORE_PHYSICAL_ATTRIBUTION'
    if q1.disposition == 'UNAVAILABLE':
        return 'SUPPLY_OR_JUSTIFIABLY_DECLINE_MISSING_PREPARATION_AND_RESPONSE_OPERANDS'
    if q4.disposition in ('UNAVAILABLE', 'OBSERVED_FINITE_MISMATCH_INCOMPLETE'):
        return 'COMPLETE_OR_JUSTIFIABLY_DECLINE_WITHHELD_RESPONSE_WITH_FULL_DENOMINATOR'
    if q6.disposition == 'PAIRED_ERROR_WORSENS_DESPITE_PREPARATION':
        return 'REASSESS_PAIRED_RESPONSE_SUPPLIER_BEFORE_CREDITING_PREPARATION'
    if q6.disposition in ('SIGNAL_TOO_SMALL_FOR_PREPARATION_BENEFIT', 'ERROR_REDUCTION_CONFOUNDED_BY_SIGNAL_SUPPRESSION',
                         'PREPARATION_IMPROVES_ARMS_PAIRED_SIGNAL_BELOW_ALLOWANCE'):
        return 'RETAIN_SIGNAL_LIMIT_AND_ASSESS_A_CONSEQUENTIAL_FORMATION_RECEIVER'
    if q6.disposition == 'PREPARATION_ESTABLISHES_LOCAL_APPLICABILITY':
        return 'ASSESS_PREPARED_LOCAL_SUPPLIER_AT_OBSERVED_COST_FOR_NEXT_FORMATION_REQUIREMENT'
    if q6.disposition == 'PREPARATION_NOT_NEEDED_FOR_SELECTED_TOLERANCE':
        return 'RETAIN_SUFFICIENT_INITIAL_RESPONSE_AND_ASSESS_OMITTING_ADDITIONAL_PREPARATION'
    if q4.disposition in ('FINITE_RESPONSE_REMAINDER_UNRESOLVED', 'PREPARATION_LOSES_LOCAL_APPLICABILITY'):
        return 'DISCRIMINATE_FINITE_REMAINDER_FROM_NUMERICAL_AND_PHYSICAL_BRANCH_ERROR_OR_STOP'
    if q5.disposition == 'CONSEQUENTIAL_MUTATION_ERROR':
        return 'RETAIN_UNRESOLVED_MUTATION_CONTRAST_AND_SELECT_PAIRED_ERROR_REQUIREMENT'
    if q3.disposition == 'CONSEQUENTIAL_OPERATOR_CHANGE':
        return 'COMPARE_UPDATED_AND_REUSED_OPERATOR_AT_THE_SAME_PREPARED_CHALLENGE'
    if q2.disposition == 'CONSEQUENTIAL_OMITTED_COUPLING':
        return 'RETAIN_NAMED_COUPLING_AND_ITS_UNRESOLVED_PHYSICAL_SCOPE'
    return 'RETAIN_SCOPED_LOCAL_FINDING_WITH_UNRESOLVED_PREPARATION_ECONOMICS_AND_KINETIC_OPERANDS'


def freeze_response_predictions(*, assessment, centers, frames):
    """Freeze four challenge predictions from the complete original diagnostic."""
    require_response_assessment(assessment)
    if (assessment.questions[0].disposition != 'EMPIRICALLY_CONSISTENT'
            or any(c.state != 'AVAILABLE' for c in assessment.coverage if c.stage in diagnostic_stages(assessment.design))
            or any(c.state != 'NOT_ENTERED' or c.point is not None for c in assessment.coverage if c.stage == 'challenge')):
        raise ValueError('withheld predictions require a complete consistent diagnostic before any challenge selection or reveal')
    if is_environmental(assessment.design):
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_environment import validate_environmental_frame
        if assessment.nomination is None or assessment.nomination.disposition != 'AVAILABLE':
            raise ValueError('withheld environmental prediction lacks its original available nomination')
        for frame in frames.values():
            validate_environmental_frame(design=assessment.design, frame=frame, nomination=assessment.nomination)
    metrics = {(q.name, q.model_name, q.position): q.value for q in assessment.quantities}
    predictions = []
    for model, position in POSITIONS:
        action, = (row.action for row in assessment.actions if (row.model_name, row.position, row.direction, row.step_bohr)
            == (model, position, 'primary', assessment.design.steps_bohr[1]))
        values = tuple(metrics[name, model, position] for name in ('base-receiver', 'predicted-change',
            'scalar-predicted-change', 'omitted-coupling-change', 'prediction-scale-discrepancy'))
        if action is None or any(value is None for value in values):
            raise ValueError('withheld prediction lacks complete original response operands')
        provisional = PreparationResponsePrediction('prediction.preparation-response.pending', assessment.design.identity,
            assessment.identity, centers[model, position].identity, frames[model].identity, action, *values)
        predictions.append(((model, position), replace(provisional,
            prediction_id='prediction.preparation-response.' + provisional.fingerprint())))
    return tuple(predictions)


UNAVAILABLE_PREFIX_DECISION = 'REASSESS_UNAVAILABLE_PAIRED_PREPARATION_OR_JUSTIFIABLY_STOP_WITH_ORIGINAL_DENOMINATOR'


def assess_unavailable_preparation(*, design, readouts, assessor_source, assessment_id):
    """Preserve all questions when an assigned prefix supplies no usable handoff.

    The caller must use the original independent prefix reader. A missing or
    failed molecular state cannot be replaced with the other genotype or with
    a duplicate initial checkpoint.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
    require_response_design(design)
    if type(readouts) is not tuple or len(readouts) != 2:
        raise ValueError('unavailable preparation retains both assigned original readouts')
    for model, readout in zip(MODELS, readouts, strict=True):
        exact(readout, ActivePreparationPrefixReadout)
        if (readout.original_result.prefix != design.prefix
                or readout.original_result.model_name != model):
            raise ValueError('unavailable preparation substitutes its assigned original prefix')
    if all(r.assessment is not None and all(p.disposition == 'AVAILABLE'
            for p in r.assessment.positions) for r in readouts):
        raise ValueError('available paired preparation requires the original response assessment')
    quantities = []
    def add(name, model, position, unit='hartree/bohr', value=None):
        quantities.append(PreparationResponseQuantity(name, model, position, value, unit))
    for model, position in POSITIONS:
        for name in ('primary-receiver-numerical-discrepancy', 'omitted-coupling-change',
                     'signed-prediction-error', 'observed-change', 'predicted-change'):
            add(name, model, position)
    for model, readout in zip(MODELS, readouts, strict=True):
        for name in ('reciprocal-receiver-discrepancy', 'additional-receiver-scale-discrepancy'):
            add(name, model, 'later')
        for name in ('operator-prediction-change', 'absolute-error-change'):
            add(name, model, 'later-minus-initial')
        cost = readout.original_result.unit.completion.cost
        for name, unit in (('wall_seconds', 'wall-seconds'), ('cpu_seconds', 'cpu-seconds'), ('retained_bytes', 'bytes')):
            add('preparation-' + name.replace('_', '-'), model, 'later-minus-initial', unit, getattr(cost, name))
    for position in ('initial', 'later'):
        for name in ('paired-signed-prediction-error', 'paired-observed-change', 'paired-predicted-change'):
            add(name, 'I95M-minus-WT', position)
    add('paired-absolute-error-change', 'I95M-minus-WT', 'later-minus-initial')
    questions = _questions(design, tuple(quantities), tuple(r.identity for r in readouts))
    coverage = tuple(PreparationResponseCoverage(effect.identity, stage,
        'NOT_SELECTED' if stage == 'additional-refinement' else 'NOT_ENTERED', None, None)
        for stage in response_stages(design) for effect in response_effects(design, stage))
    kind = EnvironmentalPreparationResponseAssessment if is_environmental(design) else PreparationResponseAssessment
    return kind(assessment_id, design, assessor_source, coverage, (), tuple(quantities), questions,
        UNAVAILABLE_PREFIX_DECISION)


def response_supplier_decision(assessment):
    """Retain nomination stops before any further native stage is selected."""
    require_response_assessment(assessment)
    # This is the original unavailable-prefix report shape. A usable paired
    # handoff, even with no entered actions, has an explicit action census and
    # (for the environmental design) a retained nomination. Preserve the
    # original adverse report's consequence without changing its canonical bytes.
    dispositions = tuple(row.disposition for row in assessment.questions)
    missing_physical_questions = ('UNAVAILABLE', 'NUMERICALLY_UNRESOLVED', 'NUMERICALLY_UNRESOLVED',
                                  'UNAVAILABLE', 'NUMERICALLY_UNRESOLVED', 'UNAVAILABLE')
    if (dispositions in (('UNAVAILABLE',) * 6, missing_physical_questions)
            and tuple(q.assigned_comparisons for q in assessment.questions) == (6, 4, 2, 4, 2, 2)
            and all(q.assessable_comparisons == 0 for q in assessment.questions)
            and not assessment.actions and getattr(assessment, 'nomination', None) is None
            and all(row.point is None and row.original_readout is None
                and row.state == ('NOT_SELECTED' if row.stage == 'additional-refinement' else 'NOT_ENTERED')
                for row in assessment.coverage)):
        return UNAVAILABLE_PREFIX_DECISION
    if is_environmental(assessment.design) and assessment.nomination is not None:
        nominee = assessment.nomination
        if nominee.disposition != 'AVAILABLE':
            return 'RETAIN_' + nominee.disposition + '_WITHOUT_ENVIRONMENTAL_ACQUISITION'
        later = [row for row in assessment.coverage if row.stage == 'environment-diagnostic']
        if all(row.point is None and row.state == 'NOT_ENTERED' for row in later):
            return 'ASSESS_SELECTED_ENVIRONMENT_DIAGNOSTIC_WITH_FIXED_INITIAL_WT_DIRECTION'
    return next_response_supplier(assessment.questions)
