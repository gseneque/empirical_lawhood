# SPDX-License-Identifier: MPL-2.0
"""Original selected point and received-array arithmetic for protected E4 phases.

The three frozen learned accounts predict original PRIMARY targets. Repeating
those points opposite PRIMARY/FINE observed endpoints is an explicit pairing,
not thirty fitted observations or any transport/calibration warrant.
"""

from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_parameter_history import independent
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterHistoryControl
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays, decode_matrix_arrays, matrix_array_members
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity

from . import science, forecast, response_forecast
from .programme_reduction import (ScheduledProgrammeNativeDisposition, ScheduledProgrammeReceiptReference)
from .records import identity
from .selected_e4_native_records import (BLIND, PROSPECTIVE, SelectedE4ProtectedArrays, SelectedE4ProtectedWitness,
    SelectedE4ProtectedNumericalAssessment, SelectedE4ProtectedFrames, SelectedE4ProtectedCausalPrefix, SelectedE4ProtectedFeature,
    SelectedE4ProtectedAccountSeal, SelectedE4ProtectedMechanicalForecast, SelectedE4NativeCaseResult, SelectedE4NativeReduction, pin)


def array_product(source, arrays, *, role, artifact_id, producers, nonfinite=(), raw=None):
    if raw is None:
        raw, members = encode_matrix_arrays(arrays, nonfinite_members=nonfinite)
    else:
        members = matrix_array_members(arrays, nonfinite_members=nonfinite)
    artifact = ArtifactIdentity(artifact_id, "selected-e4-protected-" + role.lower(), MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    product = SelectedE4ProtectedArrays("arrays." + artifact_id, identity(source), role, artifact, members,
        tuple(sorted(producers, key=lambda value: value.object_id)), BLIND, PROSPECTIVE)
    decode_matrix_arrays(raw, product)
    return raw, product


def numerical(source, history, arrays, *, full=False):
    if full:
        science.validate_full_arrays(source, arrays)
        design = source.numerical_design
        controls = tuple(MatrixParameterHistoryControl(**row) for row in independent.assess_arrays(source.coordinate, arrays,
            trajectory_tolerance=design.trajectory_tolerance, bridge_tolerance=design.bridge_tolerance))
    else:
        science.validate_prefix_arrays(source, arrays)
        controls = science.assess_prefix_values(source, arrays)
    return SelectedE4ProtectedNumericalAssessment(("full-numerical." if full else "numerical.") + source.root_id,
        "full" if full else "prefix", identity(source), identity(history), identity(source.numerical_design), controls,
        all(value.disposition == "SATISFIED" for value in controls))


def validate_numerical(source, history, numerical_record, arrays):
    observed = numerical(source, history, arrays)
    if numerical_record != observed:
        raise ValueError("selected E4 numerical record changes original complete transition assessment")


def measure(source, history, numerical_record, native, *, artifact_id):
    validate_numerical(source, history, numerical_record, native)
    arrays, traces = science.measure_prefix_values(source, native)
    raw, product = array_product(source, arrays, role="PREFIX_DIAGNOSTICS", artifact_id=artifact_id,
        producers=(identity(source), identity(history), identity(numerical_record)),
        nonfinite=tuple(name for name in arrays if not name.endswith(("_ticks", "_available", "_identifiable"))))
    return raw, SelectedE4ProtectedWitness("witness." + source.root_id, identity(source), identity(history), identity(numerical_record),
        identity(source.policy), traces, product)


def check_frames(source, witness, native, diagnostic):
    if witness.source != identity(source) or witness.policy != identity(source.policy):
        raise ValueError("selected E4 frame check replaces original source or factor rule")
    controls = science.check_prefix_frame_values(source, witness.traces, native, diagnostic)
    return SelectedE4ProtectedFrames("frames." + source.root_id, identity(source), identity(witness),
        identity(source.policy.factor_numerical_design), controls,
        all(value.disposition in ("SATISFIED", "NOT_APPLICABLE") for value in controls))


def project(source, history, numerical_record, witness, frames, native, diagnostic, *, artifact_id):
    validate_numerical(source, history, numerical_record, native)
    if (witness.history != identity(history) or witness.numerical != identity(numerical_record)
            or check_frames(source, witness, native, diagnostic) != frames):
        raise ValueError("selected E4 causal projection replaces actual prefix/witness/frame chain")
    arrays, frame_sha, disposition, reason = science.causal_cutoff_values(source, witness.traces,
        numerical_record.numerical_pass, frames.numerical_pass, native, diagnostic)
    raw, product = array_product(source, arrays, role="CAUSAL_STATE", artifact_id=artifact_id,
        producers=(identity(source), identity(history), identity(witness), identity(frames)),
        nonfinite=() if disposition == "AVAILABLE" else ("frame",))
    return raw, SelectedE4ProtectedCausalPrefix("causal." + source.root_id, identity(source), identity(history), identity(numerical_record),
        identity(witness), identity(frames), identity(source.policy), source.root.root, source.policy.cutoff_tick,
        frame_sha, disposition, reason, product)


def account(design, public, causal, witness, causal_arrays, diagnostics, *, record_id, programme, decision, models,
        calibration, original_summary, protocol=None, physical=None, frozen_arrays=None):
    from .selected_e3_e4_science import selected_feature_values
    disposition, values, physical_pin, fine_defect = selected_feature_values(design, public, causal, witness,
        causal_arrays, diagnostics, protocol=protocol, physical=physical, frozen_arrays=frozen_arrays,
        physical_kind=SelectedE4ProtectedMechanicalForecast)
    feature = SelectedE4ProtectedFeature('feature.' + public.root.root_id, public.source, identity(causal), public.root.root_id,
        public.root.independent_group_id, forecast.FAMILY_MAP[public.coordinate.family_id], public.coordinate.clock_id,
        public.coordinate.physical_time(public.policy.cutoff_tick), causal.frame_sha256, disposition, values,
        physical_pin, fine_defect)
    points = design.package.predict(values=feature.values, disposition=feature.disposition)
    return SelectedE4ProtectedAccountSeal(record_id, pin(design), public.source, identity(causal), feature,
        design.package.original_package, design.package.calibration, original_summary, points,
        None if models is None else _forecast_public_source(models, programme, public, record_id="revision."+public.root.root_id,
            feature=feature, calibration=calibration),
        decision.identity, None if calibration is None else calibration.identity)


def mechanical(protocol, causal, values, templates, *, artifact_id, retained=None, raw=None):
    public = protocol.public_source
    if (causal.source != public.source or causal.root != public.root or causal.policy != identity(public.policy)
            or causal.cutoff_tick != public.policy.cutoff_tick
            or causal.frame_sha256 is not None and sha256(values["frame"].tobytes()).hexdigest() != causal.frame_sha256):
        raise ValueError("selected E4 mechanical forecast changes original source/cutoff/frame")
    # Original helper validates clocks/schedule before any physical derivative.
    for view, multiplier in (("primary", 1), ("fine", 2)):
        import numpy as np
        if (values[view + "_ticks"][-1] != multiplier * causal.cutoff_tick or not np.array_equal(
                values[view + "_alpha_tilde"][-1], np.asarray(public.coordinate.couplings(multiplier * causal.cutoff_tick,
                    refinement=multiplier), dtype="<f8"))):
            raise ValueError("selected E4 mechanical forecast changes actual paired clock/schedule")
    arrays, disposition, dispositions = response_forecast.forecast_response_arrays(protocol, values, templates,
        disposition=causal.disposition, retained=retained)
    nonfinite = tuple(name for name, value in arrays.items() if not np.isfinite(value).all())
    raw, product = response_forecast.array_product(protocol, arrays, role="FORECAST", artifact_id=artifact_id,
        producers=(public.source, identity(causal), pin(protocol, "protocol_id")), access=BLIND, visibility=PROSPECTIVE,
        nonfinite=nonfinite, raw=raw)
    return raw, SelectedE4ProtectedMechanicalForecast("mechanical." + public.root.root_id, public.source, identity(causal),
        pin(protocol, "protocol_id"), pin(protocol.mechanical_model, "model_id"), causal.frame_sha256, product, disposition, tuple(dispositions))


def paired_targets(score, protocol, panels):
    from .paired_target_reduction import paired_targets as reduce_targets
    return reduce_targets(score, protocol, panels)


def _forecast_public_source(models, programme, public, *, record_id, feature=None, calibration=None):
    """Forecast from the exact closed public view without fabricating a case.

    Public sources intentionally omit private stream and compact-descriptor
    operands required by ScheduledProgrammeCase. The existing coordinate path
    checks the same frozen grid and performs the same point arithmetic.
    """
    from .forecast import ScheduledPublicSource
    from .selected_e4_programme import SelectedE4ForecastSeal, SelectedE4PublicModels, SelectedE4PhaseProgramme
    from .selected_e4_native_records import exact_pin, POPULATIONS
    from empirical_lawhood.kernel.time import InformationCutoff, CausalPhase
    if type(models) is not SelectedE4PublicModels or type(public) is not ScheduledPublicSource:
        raise TypeError("selected E4 forecast requires exact original public models and source")
    models.__post_init__()
    public.__post_init__()
    exact_pin(programme, SelectedE4PhaseProgramme)
    if public.root.role.value not in POPULATIONS:
        raise ValueError("selected E4 forecast requires its actual protected phase source")
    if models.relation_fit is not None:
        coordinate = public.coordinate
        return models.forecast_matched(programme, root_id=public.root.root_id, group_id=public.root.independent_group_id,
            source=public.source, coordinate=ObjectIdentity.from_record(coordinate.coordinate_id, coordinate),
            cutoff=InformationCutoff('cutoff.' + public.root.root_id, coordinate.clock_id, CausalPhase.PRE_ACTION,
                coordinate.physical_time(public.policy.cutoff_tick)),
            factor_values=(coordinate.primary_view.bath_temperature, coordinate.primary_view.friction_gamma, coordinate.member.cross_coupling_gamma),
            family_id=coordinate.family_id, feature=feature, calibration=calibration, phase=public.root.role.value, record_id=record_id)
    points = models.predict_coordinate(public.coordinate)
    return SelectedE4ForecastSeal(record_id, programme, public.root.root_id,
        public.root.independent_group_id, public.source,
        ObjectIdentity.from_record(public.coordinate.coordinate_id, public.coordinate),
        InformationCutoff("cutoff." + public.root.root_id, public.coordinate.clock_id,
            CausalPhase.PRE_ACTION, public.coordinate.physical_time(public.policy.cutoff_tick)),
        models.frozen, models.revision_model.identity, models.baseline_model.identity,
        models.target.identity, points[0][1], points[1][1])


def validate_revision_account(config, account):
    expected = None if config.models is None else _forecast_public_source(config.models, config.programme, config.public_source
        if hasattr(config,"public_source") else config.source.public,
        record_id="revision."+(config.public_source.root.root_id if hasattr(config,"public_source") else config.source.root_id),
        feature=account.feature, calibration=config.calibration)
    if (account.original_summary != config.original_summary or account.revision != expected or account.decision != config.decision.identity
            or account.calibration != (None if config.calibration is None else config.calibration.identity)):
        raise ValueError("protected E4 future substitutes actual sealed revision, baseline or calibration")
    return expected


def completed_case(case, protocol, panels, *, account_seal, score, score_projection, full_numerical, prefix, causal, full, responses, receipts):
    from .selected_e4_programme import SelectedE4PrefixProjection, SelectedE4ScoreProjection, SelectedE4CausalFeatureProjection
    if (account_seal.source != case.source or score.source != case.source or score.error_forecast != account_seal.identity
            or full_numerical.phase != "full" or full_numerical.source != case.source or full_numerical.history != identity(full)
            or full.source != case.source or full.forecast != account_seal.identity or score.responses != identity(responses)
            or score.causal_prefix != identity(causal)
            or score_projection != SelectedE4ScoreProjection.from_record(score,protocol,panels,record_id="score-projection."+case.root_id)):
        raise ValueError("protected E4 collector changes actual native/score/forecast projection lineage")
    native = []
    for phase,event in (("continue",full.native),("prefix",prefix.native),
            ("responses",None if not responses.native else responses.native[0])):
        native.append(ScheduledProgrammeNativeDisposition(phase,"NOT_USED" if event is None else "COMPLETED",
            None if event is None else event.definition.identity,
            None if event is None else ObjectIdentity.from_record(event.receipt.task_id + ".completion", event.completion),
            None if event is None else ObjectIdentity.from_record(event.receipt.receipt_id,event.receipt),
            ("actual-no-causal-origin-or-instrument-nonuse",) if event is None else ()))
    return SelectedE4NativeCaseResult(case.root_id,case.source,case.independent_group_id,"COMPLETED",
        "SATISFIED" if full_numerical.numerical_pass and score.numerical_pass else "VIOLATED",score.disposition,
        score_projection.paired_log_targets,account_seal.log_points,account_seal.identity,identity(score),identity(full_numerical),
        tuple(sorted((ScheduledProgrammeReceiptReference.from_binding(v) for v in receipts),key=lambda v:v.receipt_id)),
        tuple(native),score.reason_codes,SelectedE4PrefixProjection.from_record(causal,record_id="projection."+case.root_id),
        score_projection,account_seal.revision,case.coordinate,score_projection.target_contract,
        SelectedE4CausalFeatureProjection.from_account(account_seal) if score_projection.target_contract == 'MATCHED_FACTOR58' else None)


def reduce_cases(programme,bank,cases,*,record_id,wave_id=None):
    from . import selected_e4_programme as p
    if bank!=programme.bank:raise ValueError("protected E4 reducer changes exact original source bank")
    declared=programme.cases if wave_id is None else tuple(c for c in programme.cases if c.root_id in next(w.root_ids for w in programme.waves if w.wave_id==wave_id))
    if (tuple(v.root_id for v in cases)!=tuple(v.root_id for v in declared)
            or any((v.source,v.group_id,r_pin_coordinate(v.coordinate))!=(c.source,c.independent_group_id,c.coordinate) for v,c in zip(cases,declared,strict=True))):
        raise ValueError("protected E4 reduction substitutes complete declared case/group census")
    reduction=SelectedE4NativeReduction(record_id,programme.identity,bank,cases,tuple(sorted({v.group_id for v in cases})),wave_id)
    observed=p.SelectedE4ObservedData("observed."+programme.programme_id,programme.identity,reduction.identity,
        tuple(p.SelectedE4ObservedCase(v.root_id,v.source,v.group_id,v.coordinate,v.causal_prefix,
            v.score_projection,v.disposition,v.numerical_disposition,v.forecast,v.revision_forecast,v.original_log_points,v.target_contract,
            v.causal_feature) for v in cases))
    forecasts=p.SelectedE4ForecastBank("forecasts."+programme.programme_id,programme.identity,
        tuple(v.revision_seal for v in cases if v.revision_seal is not None))
    return reduction,observed,forecasts

def r_pin_coordinate(coordinate):
    return ObjectIdentity.from_record(coordinate.coordinate_id,coordinate)


def collect_selected_e4_programme(declaration,observations,*,record_id):
    from .selected_e4_native_records import SelectedE4WaveObservation
    if (type(observations) is not tuple or tuple(v.wave_id for v in observations)!=tuple(v.wave_id for v in declaration.programme.waves)
            or any(type(v) is not SelectedE4WaveObservation or v.declaration!=declaration.identity for v in observations)):
        raise ValueError("selected E4 collector lacks complete exact original wave closure")
    for wave,observed in zip(declaration.programme.waves,observations,strict=True):
        if tuple(c.root_id for c in observed.cases)!=wave.root_ids:
            raise ValueError("selected E4 collector thins actual assigned whole groups")
    cases=tuple(sorted((c for v in observations for c in v.cases),key=lambda c:c.root_id))
    return reduce_cases(declaration.programme,declaration.bank,cases,record_id=record_id)


def entry_forecasts(config):
    """Physical-only entry points; matched points await their actual causal inputs."""
    from .selected_e4_programme import SelectedE4ForecastBank
    return SelectedE4ForecastBank("forecasts.entry."+config.programme.programme_id+"."+config.wave_id,
        config.programme.identity,() if config.models is None or config.models.relation_fit is not None else tuple(config.models.forecast(
            config.programme,case,record_id="revision."+case.root_id) for case in config.scope_cases))
