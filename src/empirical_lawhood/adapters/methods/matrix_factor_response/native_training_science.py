# SPDX-License-Identifier: MPL-2.0
"""Existing current paired-native science with distinct TRAIN ancestry.

All native contact and byte custody stay with existing runtime owners. No
learned response-error forecast is needed to measure training targets.
"""
from hashlib import sha256
import numpy as np

from empirical_lawhood.adapters.methods.matrix_scheduled_history import science, forecast, response_forecast
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as scheduled_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_science import assess_paired_response_arrays
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from . import native_training_records as r


def dev_arrays(value):
    return r.NativeTrainingArrays(value.operand_id, value.source, value.role, value.array_artifact,
        value.members, value.producers, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)


def numerical(source, history, arrays):
    history.validate_source(source)
    science.validate_prefix_arrays(source, arrays)
    controls = science.assess_prefix_values(source, arrays)
    return r.NativeTrainingNumericalAssessment("numerical." + source.root_id, scheduled_identity(source),
        r.identity(history), scheduled_identity(source.numerical_design), controls,
        all(value.disposition == "SATISFIED" for value in controls))


def measure(source, history, observed, arrays, *, artifact_id):
    if numerical(source, history, arrays) != observed:
        raise ValueError("native TRAIN measurement changes actual independent prefix controls")
    values, traces = science.measure_prefix_values(source, arrays)
    raw, operand = science._array_product(source, values, role="PREFIX_DIAGNOSTICS", artifact_id=artifact_id,
        producers=(scheduled_identity(source), r.identity(history), r.identity(observed)),
        nonfinite=tuple(name for name in values if not name.endswith(("_ticks", "_available", "_identifiable"))))
    return raw, r.NativeTrainingPrefixWitness("witness." + source.root_id, scheduled_identity(source), r.identity(history),
        r.identity(observed), scheduled_identity(source.policy), traces, dev_arrays(operand))


def frames(source, history, observed, witness, arrays, diagnostic):
    if (numerical(source, history, arrays) != observed or witness.history != r.identity(history)
            or witness.numerical != r.identity(observed) or witness.source != scheduled_identity(source)
            or witness.policy != scheduled_identity(source.policy)):
        raise ValueError("native TRAIN frame assessment changes original prefix/witness/control joins")
    controls = science.check_prefix_frame_values(source, witness.traces, arrays, diagnostic)
    return r.NativeTrainingFrameAssessment("frames." + source.root_id, scheduled_identity(source), r.identity(witness),
        scheduled_identity(source.policy.factor_numerical_design), controls,
        all(value.disposition in ("SATISFIED", "NOT_APPLICABLE") for value in controls))


def project(source, history, observed, witness, assessed, arrays, diagnostic, *, artifact_id):
    if frames(source, history, observed, witness, arrays, diagnostic) != assessed:
        raise ValueError("native TRAIN projection changes actual independent frame assessment")
    values, frame_sha, disposition, reason = science.causal_cutoff_values(source, witness.traces,
        observed.numerical_pass, assessed.numerical_pass, arrays, diagnostic)
    raw, operand = science._array_product(source, values, role="CAUSAL_STATE", artifact_id=artifact_id,
        producers=(scheduled_identity(source), r.identity(history), r.identity(witness), r.identity(assessed)),
        nonfinite=() if disposition == "AVAILABLE" else ("frame",))
    return raw, r.NativeTrainingCausalPrefix("causal." + source.root_id, scheduled_identity(source), r.identity(history),
        r.identity(observed), r.identity(witness), r.identity(assessed), scheduled_identity(source.policy),
        source.root.root, source.policy.cutoff_tick, frame_sha, disposition, reason, dev_arrays(operand))


def feature(specification, request, public, causal, witness, assessed, arrays, diagnostic, *,
        protocol=None, physical_record=None, frozen_arrays=None, curve_primary=False):
    if (causal.source != public.source or causal.root != public.root or causal.policy != scheduled_identity(public.policy)
            or causal.cutoff_tick != public.policy.cutoff_tick or witness.source != public.source
            or witness.history != causal.history or witness.numerical != causal.numerical
            or causal.witness != r.identity(witness) or causal.frame_assessment != r.identity(assessed)
            or assessed.witness != r.identity(witness)):
        raise ValueError("native TRAIN feature changes actual causal prefix/witness/frame ancestry")
    measurement = specification.measurement
    options = dict(prefix_disposition=causal.disposition, prefix_frame_sha256=causal.frame_sha256, traces=witness.traces,
        causal_arrays=arrays, diagnostics=diagnostic, feature_window_ticks=measurement.feature_window_ticks,
        feature_cadence_ticks=measurement.feature_cadence_ticks)
    physical_pin, fine_defect = None, None
    if measurement.is_matched:
        from .matched_response_prediction import matched_causal_feature_values
        if (type(physical_record) is not r.NativeTrainingPhysicalForecast or protocol is None
                or protocol.public_source != public or physical_record.source != public.source
                or physical_record.causal_prefix != r.identity(causal) or physical_record.protocol != r.identity(protocol)
                or physical_record.frame_sha256 != causal.frame_sha256
                or physical_record.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)):
            raise ValueError('matched TRAIN feature substitutes its actual causal mechanical producer')
        physical_record.__post_init__()
        disposition, values, fine_defect = matched_causal_feature_values(protocol, frozen_arrays=frozen_arrays,
            curve_primary=curve_primary, **options)
        physical_pin = r.identity(physical_record)
    else:
        disposition, values = forecast.causal_feature_values(public.coordinate, public.policy, **options)
    evidence = tuple(sorted((r.identity(causal), causal.numerical, r.identity(witness), r.identity(assessed),
        *((physical_pin,) if physical_pin is not None else ())),
        key=lambda value: value.object_id))
    return r.NativeTrainingFeature("feature." + r.NAMESPACE + "." + public.root.root_id,
        public.root.independent_group_id, request, public.source, r.identity(causal), public.root.clock_id,
        public.coordinate.physical_time(public.policy.cutoff_tick), causal.frame_sha256, disposition, values, evidence,
        physical_forecast=physical_pin, fine_response_defect=fine_defect)


def physical(protocol, causal, arrays, templates, *, artifact_id):
    public = protocol.public_source
    if (causal.source != public.source or causal.root != public.root or causal.policy != scheduled_identity(public.policy)
            or causal.cutoff_tick != public.policy.cutoff_tick
            or causal.frame_sha256 is not None and sha256(arrays["frame"].tobytes()).hexdigest() != causal.frame_sha256):
        raise ValueError("native TRAIN physical forecast substitutes actual source/frame/cutoff")
    for view, multiplier in (("primary", 1), ("fine", 2)):
        if (arrays[view + "_ticks"][-1] != multiplier * causal.cutoff_tick
                or not np.array_equal(arrays[view + "_alpha_tilde"][-1], np.asarray(
                    public.coordinate.couplings(multiplier * causal.cutoff_tick, refinement=multiplier), dtype="<f8"))):
            raise ValueError("native TRAIN physical forecast changes paired clock/realized schedule")
    values, disposition, dispositions = response_forecast.forecast_response_arrays(protocol, arrays, templates,
        disposition=causal.disposition)
    raw, operand = response_forecast.array_product(protocol, values, role="FORECAST", artifact_id=artifact_id,
        producers=(public.source, r.identity(causal), ObjectIdentity.from_record(protocol.protocol_id, protocol)),
        access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility=VisibilityCeiling.DEVELOPMENT_ONLY,
        nonfinite=tuple(name for name, value in values.items() if not np.isfinite(value).all()))
    return raw, r.NativeTrainingPhysicalForecast("physical." + source_id(protocol), public.source, r.identity(causal),
        ObjectIdentity.from_record(protocol.protocol_id, protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id,
            protocol.mechanical_model), causal.frame_sha256, operand, disposition, dispositions)


def source_id(protocol):
    return protocol.public_source.root.root_id


def admit_response(source, protocol, panels, acquisition, causal, physical, responses):
    """Admit actual typed TRAIN response lineage before any array/scoring work."""
    if (type(acquisition) is not r.NativeTrainingAcquisitionSeal or type(causal) is not r.NativeTrainingCausalPrefix
            or type(physical) is not r.NativeTrainingPhysicalForecast or type(responses) is not r.NativeTrainingResponse):
        raise TypeError("native TRAIN response admission requires its exact actual family")
    protocol.public_source.validate_source(source)
    if ((causal.source, physical.source, physical.causal_prefix, physical.protocol, physical.frame_sha256) !=
            (scheduled_identity(source), scheduled_identity(source), r.identity(causal), r.identity(protocol), causal.frame_sha256)
            or (responses.source, responses.causal_prefix, responses.physical_forecast, responses.protocol, responses.acquisition_seal) !=
            (scheduled_identity(source), r.identity(causal), r.identity(physical), r.identity(protocol), acquisition.identity)):
        raise ValueError("native TRAIN response admission changes actual source/seal/causal/physical lineage")
    if not responses.native:
        responses.validate_nonentry(causal, physical, protocol, panels)
    elif causal.disposition != "AVAILABLE" or physical.disposition != "AVAILABLE":
        raise ValueError("native TRAIN response admission enters an unavailable causal/physical future")
    return responses


def score(specification, source, protocol, panels, acquisition, history, causal, physical_record, responses,
          prefix_arrays, frozen_arrays, response_arrays, feature_record):
    from .configured_protected_methods import paired_response_view_values
    admit_response(source, protocol, panels, acquisition, causal, physical_record, responses)
    if (responses.acquisition_seal != acquisition.identity or feature_record.origin != r.identity(causal)
            or feature_record.native_source != scheduled_identity(source)
            or physical_record.causal_prefix != r.identity(causal)
            or specification.measurement.is_matched and feature_record.physical_forecast != r.identity(physical_record)):
        raise ValueError("native TRAIN score changes real acquisition seal/source/feature lineage")
    observed = assess_paired_response_arrays(source, causal, history, prefix_arrays, physical_record, frozen_arrays,
        protocol, panels, responses, response_arrays, error_forecast=acquisition.identity,
        score_id="score." + r.NAMESPACE + "." + source.root_id)
    # Preserve the arithmetic result under a schema naming the actual seal,
    # rather than publishing an invented fitted response-error forecast.
    result = r.NativeTrainingScore(observed.score_id, observed.source, observed.causal_prefix, observed.error_forecast,
        observed.physical_forecast, observed.responses, observed.root_id, observed.independent_group_id, observed.role,
        observed.criterion, observed.controls, observed.numerical_pass, observed.disposition, observed.cells,
        observed.cumulative_log_errors, observed.reason_codes, observed.dense)
    views, numerical_disposition = paired_response_view_values(specification, source, protocol, panels, result)
    outcome = r.NativeTrainingOutcome("outcome." + r.NAMESPACE + "." + source.root_id,
        feature_record.unit_id, feature_record.source_manifest, feature_record.native_source, feature_record.origin,
        feature_record.clock_id, feature_record.cutoff, feature_record.frame_sha256, views, numerical_disposition,
        tuple(sorted((result.identity, responses.identity, acquisition.identity), key=lambda value: value.object_id)))
    return result, outcome
