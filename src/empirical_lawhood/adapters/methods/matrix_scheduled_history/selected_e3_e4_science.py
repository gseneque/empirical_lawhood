# SPDX-License-Identifier: MPL-2.0
"""Original selected point and received-array arithmetic for exposed E4 DEV.

The three frozen learned accounts predict original PRIMARY targets. Repeating
those points opposite PRIMARY/FINE observed endpoints is an explicit pairing,
not thirty fitted observations or any transport/calibration warrant.
"""

from decimal import Decimal, localcontext
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
from .selected_e3_e4_records import (DEV, EXPOSED, SelectedE3E4Arrays, SelectedE3E4Witness,
    SelectedE3E4NumericalAssessment, SelectedE3E4Frames, SelectedE3E4CausalPrefix, SelectedE3E4Feature,
    SelectedE3E4AccountSeal, SelectedE3E4MechanicalForecast, SelectedE3E4CaseResult, SelectedE3E4DevelopmentReduction, pin)


def array_product(source, arrays, *, role, artifact_id, producers, nonfinite=(), raw=None):
    if raw is None:
        raw, members = encode_matrix_arrays(arrays, nonfinite_members=nonfinite)
    else:
        members = matrix_array_members(arrays, nonfinite_members=nonfinite)
    artifact = ArtifactIdentity(artifact_id, "selected-e4-exposed-" + role.lower(), MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    product = SelectedE3E4Arrays("arrays." + artifact_id, identity(source), role, artifact, members,
        tuple(sorted(producers, key=lambda value: value.object_id)), DEV, EXPOSED)
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
    return SelectedE3E4NumericalAssessment(("full-numerical." if full else "numerical.") + source.root_id,
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
    return raw, SelectedE3E4Witness("witness." + source.root_id, identity(source), identity(history), identity(numerical_record),
        identity(source.policy), traces, product)


def check_frames(source, witness, native, diagnostic):
    if witness.source != identity(source) or witness.policy != identity(source.policy):
        raise ValueError("selected E4 frame check replaces original source or factor rule")
    controls = science.check_prefix_frame_values(source, witness.traces, native, diagnostic)
    return SelectedE3E4Frames("frames." + source.root_id, identity(source), identity(witness),
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
    return raw, SelectedE3E4CausalPrefix("causal." + source.root_id, identity(source), identity(history), identity(numerical_record),
        identity(witness), identity(frames), identity(source.policy), source.root.root, source.policy.cutoff_tick,
        frame_sha, disposition, reason, product)


def selected_feature_values(design, public, causal, witness, causal_arrays, diagnostics, *,
        protocol, physical, frozen_arrays, physical_kind):
    """One source-bound causal calculation for DEV and protected E4 accounts."""
    if (causal.source != public.source or causal.root != public.root or causal.policy != identity(public.policy)
            or causal.cutoff_tick != public.policy.cutoff_tick or witness.source != public.source
            or witness.history != causal.history or witness.numerical != causal.numerical
            or causal.witness != identity(witness)):
        raise ValueError('selected E4 account substitutes actual pre-cutoff source/witness chain')
    measurement = design.package.specification.measurement
    options = dict(prefix_disposition=causal.disposition, prefix_frame_sha256=causal.frame_sha256,
        traces=witness.traces, causal_arrays=causal_arrays, diagnostics=diagnostics,
        feature_window_ticks=measurement.feature_window_ticks, feature_cadence_ticks=measurement.feature_cadence_ticks)
    if getattr(measurement, 'is_matched', False):
        from empirical_lawhood.adapters.methods.matrix_factor_response.matched_response_prediction import matched_causal_feature_values
        if (type(physical) is not physical_kind or protocol is None or protocol.public_source != public
                or physical.source != public.source or physical.causal_prefix != identity(causal)
                or physical.protocol != pin(protocol, 'protocol_id') or physical.frame_sha256 != causal.frame_sha256
                or physical.mechanical_model != pin(protocol.mechanical_model, 'model_id')):
            raise ValueError('matched E4 feature substitutes its actual pre-future mechanical producer')
        physical.__post_init__()
        disposition, values, fine_defect = matched_causal_feature_values(protocol, frozen_arrays=frozen_arrays,
            curve_primary=design.package.specification.is_curve_primary, **options)
        return disposition, values, identity(physical), fine_defect
    disposition, values = forecast.causal_feature_values(public.coordinate, public.policy, **options)
    return disposition, values, None, None


def account(design, public, causal, witness, causal_arrays, diagnostics, *, record_id,
        protocol=None, physical=None, frozen_arrays=None):
    disposition, values, physical_pin, fine_defect = selected_feature_values(design, public, causal, witness,
        causal_arrays, diagnostics, protocol=protocol, physical=physical, frozen_arrays=frozen_arrays,
        physical_kind=SelectedE3E4MechanicalForecast)
    feature = SelectedE3E4Feature('feature.' + public.root.root_id, public.source, identity(causal), public.root.root_id,
        public.root.independent_group_id, forecast.FAMILY_MAP[public.coordinate.family_id], public.coordinate.clock_id,
        public.coordinate.physical_time(public.policy.cutoff_tick), causal.frame_sha256, disposition, values,
        physical_pin, fine_defect)
    points = design.package.predict(values=feature.values, disposition=feature.disposition)
    return SelectedE3E4AccountSeal(record_id, pin(design), public.source, identity(causal), feature,
        design.package.original_package, design.package.calibration, points)


def validate_selected_account_lineage(account, design, public, causal, witness, *, protocol, physical, physical_kind):
    """Join retained causal operands without recomputing their original values."""
    account.__post_init__()
    feature = account.feature
    if (causal.source != public.source or causal.root != public.root or causal.policy != identity(public.policy)
            or causal.cutoff_tick != public.policy.cutoff_tick or witness.source != public.source
            or witness.history != causal.history or witness.numerical != causal.numerical
            or causal.witness != identity(witness)):
        raise ValueError('selected E4 account substitutes actual pre-cutoff source/witness chain')
    if getattr(design.package.specification.measurement, 'is_matched', False):
        if (type(physical) is not physical_kind or protocol is None or protocol.public_source != public
                or physical.source != public.source or physical.causal_prefix != identity(causal)
                or physical.protocol != pin(protocol, 'protocol_id') or physical.frame_sha256 != causal.frame_sha256
                or physical.mechanical_model != pin(protocol.mechanical_model, 'model_id')
                or feature.physical_forecast != identity(physical)):
            raise ValueError('matched E4 feature substitutes its actual pre-future mechanical producer')
        physical.__post_init__()
    if ((account.design, account.source, account.prefix, account.original_package, account.original_calibration) !=
            (pin(design), public.source, identity(causal), design.package.original_package, design.package.calibration)
            or (feature.root_id, feature.independent_group_id, feature.clock_id, feature.cutoff, feature.frame_sha256) !=
                (public.root.root_id, public.root.independent_group_id, public.coordinate.clock_id,
                    public.coordinate.physical_time(public.policy.cutoff_tick), causal.frame_sha256)):
        raise ValueError('selected E4 retained account changes its original causal lineage')


def validate_selected_account(account, design, public, causal, witness, causal_arrays, diagnostics, *, protocol, physical, frozen_arrays, physical_kind):
    """Reproduce sealed causal values and original E3 points from retained arrays."""
    validate_selected_account_lineage(account, design, public, causal, witness,
        protocol=protocol, physical=physical, physical_kind=physical_kind)
    feature = account.feature
    checked = selected_feature_values(design, public, causal, witness, causal_arrays, diagnostics,
        protocol=protocol, physical=physical, frozen_arrays=frozen_arrays, physical_kind=physical_kind)
    if (checked != (feature.disposition, feature.values, feature.physical_forecast, feature.fine_response_defect)
            or design.package.predict(values=feature.values, disposition=feature.disposition) != account.log_points):
        raise ValueError('selected E4 retained account changes actual causal features or original frozen points')


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
        producers=(public.source, identity(causal), pin(protocol, "protocol_id")), access=DEV, visibility=EXPOSED,
        nonfinite=nonfinite, raw=raw)
    return raw, SelectedE3E4MechanicalForecast("mechanical." + public.root.root_id, public.source, identity(causal),
        pin(protocol, "protocol_id"), pin(protocol.mechanical_model, "model_id"), causal.frame_sha256, product, disposition, tuple(dispositions))


def paired_targets(score, protocol, panels):
    from .paired_target_reduction import paired_targets as reduce_targets
    return reduce_targets(score, protocol, panels)


def group_residuals(cases):
    result = []
    groups = tuple(sorted({case.group_id for case in cases}))
    contracts = {case.target_contract for case in cases}
    if len(contracts) != 1:
        raise ValueError("selected E4 residual changes the original paired target contract")
    from .selected_e3_e4_records import selected_target_shape
    methods, _, _ = selected_target_shape(next(iter(contracts)))
    matched = next(iter(contracts)) == "MATCHED_FACTOR58"
    for group in groups:
        rows = tuple(case for case in cases if case.group_id == group)
        if len(rows) != 9:
            raise ValueError("selected E4 residual omits a whole group's exact nine coordinates")
        scores = []
        for method in methods:
            maximum = Decimal(0)
            missing = False
            for case in rows:
                points = dict(case.original_log_points)[method] * (1 if matched else 2)
                missing = missing or case.disposition != "COMPLETED" or case.numerical_disposition != "SATISFIED"
                with localcontext() as context:
                    context.prec = 50
                    for target, point in zip(case.paired_log_targets, points, strict=True):
                        if target is None or point is None:
                            missing = True
                        else:
                            maximum = max(maximum, target - point)
            scores.append((method, None if missing else maximum))
        result.append((group, tuple(scores)))
    return tuple(result)


def reduce_cases(programme, cases, *, record_id):
    if (tuple(case.root_id for case in cases) != tuple(case.root_id for case in programme.cases)
            or any((row.source, row.group_id) != (case.source, case.independent_group_id)
                for row, case in zip(cases, programme.cases, strict=True))):
        raise ValueError("selected E4 reduction substitutes full original32x9 case/group census")
    return SelectedE3E4DevelopmentReduction(record_id, programme.identity, programme.bank, cases, group_residuals(cases), programme.design)


def completed_case(case, protocol, panels, *, account_seal, score, full_numerical, prefix, full, responses, receipts):
    if (account_seal.source != case.source or score.source != case.source or score.error_forecast != account_seal.identity
            or full_numerical.phase != "full" or full_numerical.source != case.source or full_numerical.history != identity(full)
            or full.source != case.source or full.forecast != account_seal.identity or score.responses != identity(responses)):
        raise ValueError("selected E4 collector changes actual case/source/forecast/score/full lineage")
    native = []
    for phase, event in (("continue", full.native), ("prefix", prefix.native),
            ("responses", None if not responses.native else responses.native[0])):
        native.append(ScheduledProgrammeNativeDisposition(phase, "NOT_USED" if event is None else "COMPLETED",
            None if event is None else event.definition.identity,
            None if event is None else ObjectIdentity.from_record(event.receipt.task_id + ".completion", event.completion),
            None if event is None else ObjectIdentity.from_record(event.receipt.receipt_id, event.receipt),
            ("actual-no-causal-origin-or-instrument-nonuse",) if event is None else ()))
    numerical_status = "SATISFIED" if full_numerical.numerical_pass and score.numerical_pass else "VIOLATED"
    from .paired_target_reduction import target_contract
    return SelectedE3E4CaseResult(case.root_id, case.source, case.independent_group_id, "COMPLETED", numerical_status,
        score.disposition, paired_targets(score, protocol, panels), account_seal.log_points, account_seal.identity, identity(score),
        identity(full_numerical), tuple(sorted((ScheduledProgrammeReceiptReference.from_binding(row) for row in receipts),
            key=lambda row: row.receipt_id)), tuple(native), score.reason_codes, target_contract=target_contract(protocol))
