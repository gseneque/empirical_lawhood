# SPDX-License-Identifier: MPL-2.0
"""Existing current paired-native science with distinct E2 ancestry.

All native contact and byte custody stay with existing runtime owners. No
learned response-error forecast is needed to measure utility measurements.
"""
from hashlib import sha256
from decimal import localcontext
from fractions import Fraction
import numpy as np

from empirical_lawhood.adapters.methods.matrix_scheduled_history import science, response_forecast
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_science import assess_paired_response_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from . import native_utility_records as r


def dev_arrays(value):
    return r.NativeUtilityArrays(value.operand_id, value.source, value.role, value.array_artifact,
        value.members, value.producers, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)


def numerical(source, history, arrays):
    history.validate_source(source)
    science.validate_prefix_arrays(source, arrays)
    controls = science.assess_prefix_values(source, arrays)
    return r.NativeUtilityNumericalAssessment("numerical." + source.root_id, scheduled_identity(source),
        r.identity(history), scheduled_identity(source.numerical_design), controls,
        all(value.disposition == "SATISFIED" for value in controls))


def measure(source, history, observed, arrays, *, artifact_id):
    if numerical(source, history, arrays) != observed:
        raise ValueError("native E2 measurement changes actual independent prefix controls")
    values, traces = science.measure_prefix_values(source, arrays)
    raw, operand = science._array_product(source, values, role="PREFIX_DIAGNOSTICS", artifact_id=artifact_id,
        producers=(scheduled_identity(source), r.identity(history), r.identity(observed)),
        nonfinite=tuple(name for name in values if not name.endswith(("_ticks", "_available", "_identifiable"))))
    return raw, r.NativeUtilityPrefixWitness("witness." + source.root_id, scheduled_identity(source), r.identity(history),
        r.identity(observed), scheduled_identity(source.policy), traces, dev_arrays(operand))


def frames(source, history, observed, witness, arrays, diagnostic):
    if (numerical(source, history, arrays) != observed or witness.history != r.identity(history)
            or witness.numerical != r.identity(observed) or witness.source != scheduled_identity(source)
            or witness.policy != scheduled_identity(source.policy)):
        raise ValueError("native E2 frame assessment changes original prefix/witness/control joins")
    controls = science.check_prefix_frame_values(source, witness.traces, arrays, diagnostic)
    return r.NativeUtilityFrameAssessment("frames." + source.root_id, scheduled_identity(source), r.identity(witness),
        scheduled_identity(source.policy.factor_numerical_design), controls,
        all(value.disposition in ("SATISFIED", "NOT_APPLICABLE") for value in controls))


def project(source, history, observed, witness, assessed, arrays, diagnostic, *, artifact_id):
    if frames(source, history, observed, witness, arrays, diagnostic) != assessed:
        raise ValueError("native E2 projection changes actual independent frame assessment")
    values, frame_sha, disposition, reason = science.causal_cutoff_values(source, witness.traces,
        observed.numerical_pass, assessed.numerical_pass, arrays, diagnostic)
    raw, operand = science._array_product(source, values, role="CAUSAL_STATE", artifact_id=artifact_id,
        producers=(scheduled_identity(source), r.identity(history), r.identity(witness), r.identity(assessed)),
        nonfinite=() if disposition == "AVAILABLE" else ("frame",))
    return raw, r.NativeUtilityCausalPrefix("causal." + source.root_id, scheduled_identity(source), r.identity(history),
        r.identity(observed), r.identity(witness), r.identity(assessed), scheduled_identity(source.policy),
        source.root.root, source.policy.cutoff_tick, frame_sha, disposition, reason, dev_arrays(operand))


def physical(protocol, causal, arrays, templates, *, artifact_id):
    public = protocol.public_source
    if (causal.source != public.source or causal.root != public.root or causal.policy != scheduled_identity(public.policy)
            or causal.cutoff_tick != public.policy.cutoff_tick
            or causal.frame_sha256 is not None and sha256(arrays["frame"].tobytes()).hexdigest() != causal.frame_sha256):
        raise ValueError("native E2 physical forecast substitutes actual source/frame/cutoff")
    for view, multiplier in (("primary", 1), ("fine", 2)):
        if (arrays[view + "_ticks"][-1] != multiplier * causal.cutoff_tick
                or not np.array_equal(arrays[view + "_alpha_tilde"][-1], np.asarray(
                    public.coordinate.couplings(multiplier * causal.cutoff_tick, refinement=multiplier), dtype="<f8"))):
            raise ValueError("native E2 physical forecast changes paired clock/realized schedule")
    values, disposition, dispositions = response_forecast.forecast_response_arrays(protocol, arrays, templates,
        disposition=causal.disposition)
    raw, operand = response_forecast.array_product(protocol, values, role="FORECAST", artifact_id=artifact_id,
        producers=(public.source, r.identity(causal), ObjectIdentity.from_record(protocol.protocol_id, protocol)),
        access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
        nonfinite=tuple(name for name, value in values.items() if not np.isfinite(value).all()))
    return raw, r.NativeUtilityPhysicalForecast("physical." + source_id(protocol), public.source, r.identity(causal),
        ObjectIdentity.from_record(protocol.protocol_id, protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id,
            protocol.mechanical_model), causal.frame_sha256, operand, disposition, dispositions)


def source_id(protocol):
    return protocol.public_source.root.root_id


def score(specification,source,protocol,panels,acquisition,history,causal,physical_record,responses,
          prefix_arrays,frozen_arrays,response_arrays):
    if (acquisition.specification!=specification.identity or responses.acquisition_seal!=acquisition.identity
            or physical_record.causal_prefix!=r.identity(causal)):
        raise ValueError("native E2 score changes actual pre-acquisition freeze/source lineage")
    if not responses.native:
        responses.validate_nonentry(causal, physical_record, protocol, panels)
    observed=assess_paired_response_arrays(source,causal,history,prefix_arrays,physical_record,frozen_arrays,
        protocol,panels,responses,response_arrays,error_forecast=acquisition.identity,
        score_id="score."+r.NAMESPACE+"."+source.root_id)
    result=r.NativeUtilityScore(observed.score_id,observed.source,observed.causal_prefix,observed.error_forecast,
        observed.physical_forecast,observed.responses,observed.root_id,observed.independent_group_id,observed.role,
        observed.criterion,observed.controls,observed.numerical_pass,observed.disposition,observed.cells,
        observed.cumulative_log_errors,observed.reason_codes,observed.dense)
    return result,assess_score(specification,protocol,panels,acquisition,result)


def assess_score(specification,protocol,panels,acquisition,score):
    """Pure complete paired contrasts from independently checked native scores.

    The ordinary producer/cold reader authenticates actual score, forecast,
    source and pre-future acquisition custody before calling this reducer.
    Neither a numerical pass nor this conditional count is qualification.
    """
    specification.__post_init__();protocol.__post_init__();acquisition.__post_init__();score.__post_init__()
    if type(score) is not r.NativeUtilityScore or type(acquisition) is not r.NativeUtilityAcquisitionSeal:
        raise TypeError("native E2 cannot consume TRAIN/passive/legacy result identities")
    criterion=specification.criterion
    if criterion is None:raise ValueError("native E2 utility criterion was not frozen before entry")
    if (type(criterion) is r.NativeAmendedUtilityCriterion) != (score.dense is not None):
        raise ValueError('native E2 amended questions require their original complete dense assay')
    public=protocol.public_source
    if (acquisition.specification!=specification.identity or score.acquisition_seal!=acquisition.identity
            or score.source!=public.source or score.root_id!=public.root.root_id
            or score.independent_group_id!=public.root.independent_group_id
            or score.role!=public.root.role.value
            or (score.root_id,score.independent_group_id,score.source) not in acquisition.source_roster
            or score.criterion!=protocol.criterion
            or protocol.criterion!=specification.mathematical_protocol or score.root_id not in specification.root_ids
            or tuple(sorted(value.role for value in panels))!=("COMMON_NOISE_PANEL","INDEPENDENT_FUTURE")
            or any(value.independent_group_id!=score.independent_group_id for value in panels)):
        raise ValueError("native E2 changes actual original frozen root/group/score/measurement")
    expected={(v,p.panel_id,a.action_id,m,h) for v in ("PRIMARY","FINE") for p in panels
        for a in protocol.actions for m in r.model_predictors(protocol.mechanical_model) for h in protocol.horizon_steps}
    if len(score.cells)!=len(expected) or {value.key for value in score.cells}!=expected:
        raise ValueError("native E2 drops complete nested view/panel/action/predictor/horizon denominator")
    if score.dense is not None:
        from .response_scoring import validate_dense_score_units
        validate_dense_score_units(protocol, score)
    else:
        shared={}
        for value in score.cells:
            value.__post_init__()
            key=(value.view,value.panel_id,value.action_id,value.horizon_tick)
            if shared.setdefault(key,value.actual_odd_responses)!=value.actual_odd_responses:raise ValueError("native E2 comparators receive different native truth")
            if value.actual_odd_responses is not None and len(value.actual_odd_responses)!=48:raise ValueError("native E2 drops original native truth denominator")
            if value.signed_errors is not None and len(value.signed_errors)!=48:raise ValueError("native E2 drops original receiver denominator")
            if value.signed_errors is None:
                if value.normalized_error is not None:raise ValueError("native E2 invents a finite unresolved receiver error")
            else:
                action=next(action for action in protocol.actions if action.action_id==value.action_id)
                with localcontext() as context:
                    context.prec=60
                    dt=public.coordinate.primary_view.timestep
                    duration=dt*value.horizon_tick; pulse=dt*min(action.pulse_steps,value.horizon_tick)
                    impulse=action.amplitude*action.force_norm*pulse
                    expected_loss=max(sum(error*error for error in value.signed_errors[:24]).sqrt()/(impulse*(duration-pulse/2)),
                        sum(error*error for error in value.signed_errors[24:]).sqrt()/impulse)
                if value.normalized_error!=expected_loss:raise ValueError("native E2 changes exact signed receiver norm/nominal actuator units")
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import branch_census
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl
    if score.numerical_pass:
        branches=branch_census(protocol,panels)
        expected_controls={"control.scheduled."+score.root_id+"."+branch: (1 if view=="PRIMARY" else 2)*protocol.horizon_steps[-1] for branch,view,*_ in branches}
        if (len(score.controls)!=len(expected_controls) or {value.control_id for value in score.controls}!=set(expected_controls)
                or any(type(value) is not ScheduledResponseTransitionControl or value.denominator_steps!=expected_controls[value.control_id]
                    or value.tolerance!=protocol.native_reference_tolerance for value in score.controls)):
            raise ValueError("native E2 omits complete independent branch/clock/tolerance controls")
    losses=[]
    for view in ("PRIMARY","FINE"):
        for predictor in r.model_predictors(protocol.mechanical_model):
            for horizon in protocol.horizon_steps:
                values=tuple(value.normalized_error for value in score.cells if value.view==view
                    and value.predictor==predictor and value.horizon_tick<=horizon)
                loss=None if any(value is None for value in values) else max(values)
                losses.append((view,predictor,horizon,loss))
    lossmap={(v,p,h):value for v,p,h,value in losses}
    selected=(criterion.candidate,*criterion.comparators)
    primary=criterion.primary_horizon
    finite=all(lossmap[v,p,primary] is not None for v in ("PRIMARY","FINE") for p in selected)
    with localcontext() as context:
        context.prec=60
        discrepancy=None if not finite else max(abs(lossmap["PRIMARY",p,primary]-lossmap["FINE",p,primary]) for p in selected)
    numerical=("UNEVALUABLE" if not score.numerical_pass or discrepancy is None else "SATISFIED"
        if discrepancy<=criterion.maximum_view_discrepancy else "VIOLATED")
    usable=score.numerical_pass and finite and numerical=="SATISFIED"
    with localcontext() as context:
        context.prec=60
        contrasts=tuple((view,predictor,None if lossmap[view,predictor,primary] is None
            or lossmap[view,criterion.candidate,primary] is None else
            lossmap[view,predictor,primary]-lossmap[view,criterion.candidate,primary])
            for view in ("PRIMARY","FINE") for predictor in criterion.comparators)
    success=usable and all(value is not None and value>criterion.improvement_margin for _,_,value in contrasts)
    reasons=set(score.reason_codes)
    if not score.numerical_pass:reasons.add("NATIVE_CROSSCHECK_NOT_SATISFIED")
    if not finite:reasons.add("SELECTED_COMPARISON_UNRESOLVED")
    if numerical=="VIOLATED":reasons.add("PAIRED_VIEW_DISCREPANCY_EXCEEDS_FROZEN_BUDGET")
    if not success:reasons.add("WHOLE_ROOT_IMPROVEMENT_NOT_ESTABLISHED")
    amended = None
    if type(criterion) is r.NativeAmendedUtilityCriterion:
        from .response_scoring import joint_structural_advantage, paired_adequacy
        curves = {(curve.view, curve.predictor): curve for curve in score.dense.curves}
        def adequate(predictor):
            return paired_adequacy(tuple(curves[view, predictor].duration(numerical_usable=score.numerical_pass,
                tolerance=criterion.adequacy_tolerance) for view in ('PRIMARY', 'FINE')), criterion.adequacy_horizon)
        structural = joint_structural_advantage(tuple(lossmap[view, 'FACTOR', 128] for view in ('PRIMARY', 'FINE')),
            {name: tuple(lossmap[view, name, 128] for view in ('PRIMARY', 'FINE')) for name in criterion.comparators},
            numerical_usable=score.numerical_pass)
        amended = r.NativeUtilityAmendedEndpoints(adequate('FACTOR'), structural, adequate('ZERO_RESPONSE'))
        if amended.adequacy is not True:
            reasons.add('PAIRED_SAMPLED32_FACTOR_ADEQUACY_NOT_ESTABLISHED')
    return r.NativeUtilityOutcome("outcome."+r.NAMESPACE+"."+score.root_id,specification.identity,acquisition.identity,
        score.root_id,score.independent_group_id,score.source,result_identity(score),tuple(sorted(losses)),
        tuple(sorted(contrasts)),usable,success,numerical,tuple(sorted(reasons)),amended)


def result_identity(score):return ObjectIdentity.from_record(score.score_id,score)


def summarize(specification,acquisition,outcomes):
    """Exact full-roster conditional arithmetic, with sampling explicitly absent."""
    from empirical_lawhood.runtime.experimental_statistics import binomial_upper_tail
    criterion=specification.criterion
    if criterion is None:raise ValueError("native E2 summary lacks its original frozen criterion")
    rows=tuple(sorted(outcomes,key=lambda value:value.unit_id))
    if (len(rows)!=len(specification.root_ids) or tuple(sorted(value.root_id for value in rows))!=specification.root_ids
            or len({value.unit_id for value in rows})!=len(rows)
            or tuple(root for root,_,_ in acquisition.source_roster)!=specification.root_ids
            or any(value.specification!=specification.identity or value.acquisition!=acquisition.identity
                or (value.root_id,value.unit_id,value.source) not in acquisition.source_roster for value in rows)):
        raise ValueError("native E2 summary omits, duplicates or substitutes assigned independent roots")
    successes=sum(value.success for value in rows);usable=sum(value.usable for value in rows)
    tail=binomial_upper_tail(len(rows),successes,Fraction(criterion.null_success_numerator,criterion.null_success_denominator))
    return r.NativeUtilitySummary("summary."+specification.specification_id,specification.identity,acquisition.identity,rows,
        len(rows),usable,successes,tail.numerator,tail.denominator,
        usable>=criterion.minimum_usable_units and tail<=Fraction(criterion.alpha_numerator,criterion.alpha_denominator),
        amended=r.amended_utility_inference(rows) if type(criterion) is r.NativeAmendedUtilityCriterion else None)


def amended_primary_report(inference):
    """Readable two-slot arithmetic; no promotion of scientific authority."""
    if inference is None:
        return None
    if type(inference) is not r.NativeUtilityAmendedInference:
        raise TypeError('amended E2 report requires its exact retained two-question inference')
    inference.__post_init__()
    result = {}
    for key, name in (('paired-factor-adequacy-through32', 'adequacy'),
            ('three-challenger-advantage-through128', 'structural_advantage')):
        value = getattr(inference, name)
        interval = value.descriptive_interval
        result[key] = {'assigned_units': len(value.unit_ids), 'known_successes': value.successes,
            'known_failures': value.failures, 'unknown_events': value.unknowns,
            'null_probability': {'numerator': value.null_numerator, 'denominator': value.null_denominator},
            'allocated_alpha': {'numerator': value.alpha_numerator, 'denominator': value.alpha_denominator},
            'critical_successes': value.critical_successes,
            'conditional_tail': {'numerator': value.tail_numerator, 'denominator': value.tail_denominator},
            'conditional_criterion_met': value.criterion_met,
            'unknown_test_rule': 'NONSUCCESS_IN_COMPLETE_ASSIGNED_DENOMINATOR',
            'descriptive_95_percent_true_event_envelope': {'lower': str(interval.lower), 'upper': str(interval.upper)},
            'complete_case_interval_scope': 'CONDITIONAL_ON_ASSESSABILITY',
            'qualification': 'NOT_ESTABLISHED_BY_EVENT_ARITHMETIC'}
    return result
