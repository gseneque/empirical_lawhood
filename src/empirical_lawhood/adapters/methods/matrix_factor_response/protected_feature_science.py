# SPDX-License-Identifier: MPL-2.0
"""Seedless current E3 features over bounded immutable prefix operands.

The original scheduled owner supplies every feature equation. These joins do
not authenticate current dependency receipts, establish numerical/source
qualification or confer outcome access; those remain with the owning binding.
No native source manifest, allocation roster or generator state is accepted.
"""

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import validate_trace
from empirical_lawhood.adapters.methods.matrix_dataset_readers import MatrixDatasetBridge, retained_array_mappings
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import expected_members
from empirical_lawhood.adapters.methods.matrix_scheduled_history import forecast, records as scheduled
from empirical_lawhood.infrastructure.dataset_readers import ArrayDatasetReader
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.runtime.execution import WorkerInputPort

from .experiment_specification import MatrixResponseErrorSpecification
from .protected_experiment_methods import ProtectedE3CausalFeature, _selected_specification
from .protected_prefix_records import ProtectedE3CausalPrefix, ProtectedE3FrameAssessment, ProtectedE3PrefixWitness
from .protected_source_records import NAMESPACE, identity


ArrayInput = bytes | WorkerInputPort | MatrixDatasetBridge | ArrayDatasetReader

def _exact(value, kind):
    if type(value) is not kind:
        raise TypeError("protected E3 feature requires exact current seedless scientific operands")
    value.__post_init__()


def _join(specification, public, causal, witness, assessment):
    _selected_specification(specification)
    for value, kind in ((public, forecast.ScheduledPublicSource), (causal, ProtectedE3CausalPrefix),
            (witness, ProtectedE3PrefixWitness), (assessment, ProtectedE3FrameAssessment)):
        _exact(value, kind)
    for value in (public.root, public.coordinate, public.policy, public.policy.factor_rule, public.policy.factor_numerical_design):
        value.__post_init__()
    measurement, policy = specification.measurement, public.policy
    if (policy.cutoff_tick != measurement.origin_tick or policy.origin_sector != "Y"
            or public.coordinate.primary_view.timestep != measurement.primary_timestep
            or public.coordinate.fine_view.timestep != measurement.fine_timestep
            or causal.root != public.root or causal.cutoff_tick != policy.cutoff_tick
            or causal.source != public.source or witness.source != public.source or assessment.source != public.source
            or causal.policy != scheduled.identity(policy) or witness.policy != causal.policy
            or causal.history != witness.history or causal.numerical != witness.numerical
            or causal.witness != identity(witness) or causal.frame_assessment != identity(assessment)
            or assessment.witness != identity(witness)):
        raise ValueError("protected E3 feature substitutes actual source, root, cutoff, clock or current product joins")
    for trace in witness.traces:
        validate_trace(trace, policy.factor_rule)
    observation = next(t for t in witness.traces if (t.view, t.sector) == ("PRIMARY", policy.origin_sector)).observations[-1]
    if (causal.disposition == "AVAILABLE" and (observation.raw_admitted is None or observation.causal_admitted is not True
                or observation.alignment_ambiguous)
            or causal.disposition == "NO_ORIGIN" and (causal.reason != "DECLARED_CUTOFF_NOT_CAUSALLY_ADMITTED"
                or observation.raw_admitted is None or observation.causal_admitted is True and not observation.alignment_ambiguous)
            or causal.disposition == "UNEVALUABLE" and (causal.reason not in (
                "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED", "CAUSAL_CUTOFF_OBSERVATION_UNAVAILABLE")
                or causal.reason == "CAUSAL_CUTOFF_OBSERVATION_UNAVAILABLE" and (
                    not assessment.numerical_pass or observation.raw_admitted is not None))):
        raise ValueError("protected E3 feature changes retained cutoff admission or original nonuse")
    if ({m.name: (m.dtype, m.shape) for m in witness.arrays.members} != expected_members(policy.factor_rule)
            or witness.arrays.producers != tuple(sorted((public.source, causal.history, causal.numerical), key=lambda row: row.object_id))):
        raise ValueError("protected E3 feature changes complete diagnostic members or current producers")
    design = policy.factor_numerical_design
    n = 2*len(policy.factor_rule.sectors)*len(policy.factor_rule.lattice)
    if (assessment.numerical_design != scheduled.identity(design)
            or tuple(len(c.measured_errors) for c in assessment.controls) != (n, 15*n, n, n, n, n)
            or tuple(c.tolerance for c in assessment.controls) != (design.operator_tolerance, design.eigenpair_tolerance,
                design.orthogonality_tolerance, design.projector_tolerance, design.factor_tolerance, design.scalar_tolerance)
            or causal.disposition in ("AVAILABLE", "NO_ORIGIN") and not assessment.numerical_pass):
        raise ValueError("protected E3 feature changes selected independent frame assessment")


def project_protected_e3_feature(specification: MatrixResponseErrorSpecification,
        public_source: forecast.ScheduledPublicSource, causal: ProtectedE3CausalPrefix,
        witness: ProtectedE3PrefixWitness, assessment: ProtectedE3FrameAssessment,
        causal_raw: ArrayInput, diagnostic_raw: ArrayInput) -> ProtectedE3CausalFeature:
    """Read the selected original21 values, retaining refusal and nonuse.

    The current numerical product is an immutable reference here. Its actual
    authenticated receipt, the public/allocation join and the ordinary array
    port identities must be checked by the later owning current-task binding.
    """
    _join(specification, public_source, causal, witness, assessment)
    if any(type(value) not in (bytes, WorkerInputPort, MatrixDatasetBridge, ArrayDatasetReader)
            for value in (causal_raw, diagnostic_raw)):
        raise TypeError("protected E3 feature requires immutable bytes or authenticated array datasets")
    supplied = iter((causal_raw, diagnostic_raw))
    with retained_array_mappings((causal.arrays, witness.arrays), lambda artifact: next(supplied),
            maximum_chunk_bytes=1024 * 1024, maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES) as (arrays, diagnostics):
        for trace in witness.traces:
            name = trace.view.lower() + "_" + trace.sector.lower() + "_ticks"
            if not np.array_equal(diagnostics[name], np.asarray(public_source.policy.factor_rule.lattice, dtype="<i8")):
                raise ValueError("protected E3 feature changes the complete diagnostic clock")
        if causal.disposition != "AVAILABLE" and not np.isnan(arrays["frame"]).all():
            raise ValueError("protected E3 feature manufactures a nonuse frame")
        measurement = specification.measurement
        disposition, values = forecast.causal_feature_values(public_source.coordinate, public_source.policy,
            prefix_disposition=causal.disposition, prefix_frame_sha256=causal.frame_sha256, traces=witness.traces,
            causal_arrays=arrays, diagnostics=diagnostics, feature_window_ticks=measurement.feature_window_ticks,
            feature_cadence_ticks=measurement.feature_cadence_ticks)
    evidence = tuple(sorted((identity(causal), causal.numerical, identity(witness), identity(assessment)), key=lambda row: row.object_id))
    return ProtectedE3CausalFeature("feature." + NAMESPACE + "." + public_source.root.root_id,
        public_source.allocation, public_source, identity(causal), causal.frame_sha256, disposition, values, evidence)
