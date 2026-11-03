# SPDX-License-Identifier: MPL-2.0
"""Exposed software controls for complete finite-response frontier consumers."""

from dataclasses import replace as dataclass_replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.records import (
    PREDICTORS, MatrixFactorResponseScore, identity,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import (
    MatrixResponseActionScale, MatrixResponseFrontierProtocol, MatrixResponseRootFrontier,
    MatrixResponseFactorRuleCompatibility,
    assess_receiver_metric as _assess_receiver_metric, reduce_response_frontier as _reduce_response_frontier, root_frontier_census,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.response_contracts import (
    MatrixResponsePopulationPolicy, select_population_origins,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from tests.test_matrix_factor_response import object_id, product, mechanical_case, mechanical_origin
from tests.test_matrix_factor_confirmation_eligibility import provenance as provenance  # noqa: F401
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorStream


def replace(value, **changes):
    """Edit disclosed numerical inputs; canonical records retain real validation."""
    if type(value) is SimpleNamespace:
        return SimpleNamespace(**{**vars(value), **changes})
    return dataclass_replace(value, **changes)


def bind_numerical_identities(monkeypatch, *operands):
    """Only these exact arithmetic inputs get literal, non-authority test PINs."""
    from empirical_lawhood.adapters.methods.matrix_factor_response import records, response_frontier
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_joint_bindings_v2, response_error_pooled_bindings
    canonical_identity = records.identity
    def projected(value):
        for operand in operands:
            if value is operand:
                return operand._numerical_identity
        return canonical_identity(value)
    for module in (records, response_frontier):
        monkeypatch.setattr(module, "identity", projected)
    for module in (response_error_joint_bindings_v2, response_error_pooled_bindings):
        monkeypatch.setattr(module, "response_identity", projected)
    return projected


def numerical_origin(source, past, *, artifact_id):
    """A supplied numerical view, with no source record, publication or authority."""
    from empirical_lawhood.adapters.simulators.six_matrix_response.factor_bridge import factor_frame_sha256
    _, arrays = product(past, artifact_id, (source._numerical_identity, identity(source.design)))
    return SimpleNamespace(origin_id="numerical.origin", source=source._numerical_identity, design=source.design,
        root_id=source.root.root_id, independent_group_id=source.root.independent_group_id,
        clock_id=source.root.clock_id, arrays=arrays, frame_sha256=factor_frame_sha256(past["frame"]),
        _numerical_identity=object_id("numerical.origin"))


def numerical_operands(design, initial, templates, model, *, provenance=None):
    """Literal math inputs only; these namespaces have no canonical Source API."""
    _, past = mechanical_origin((design, initial, templates, model))
    streams = (MatrixFactorStream("common", "panel.common", 701, "COMMON_NOISE_PANEL"),
        MatrixFactorStream("independent", "panel.independent", 702, "INDEPENDENT_FUTURE"),
        MatrixFactorStream("prefix", "panel.prefix", 703, "PREFIX"))
    root = SimpleNamespace(root_id="numerical.root", independent_group_id="numerical.group",
        clock_id="numerical.clock", streams=streams)
    _, instrument = product(templates, "numerical.instrument", (design.instrument, design.receiver))
    source = SimpleNamespace(design=design, root=root, instrument_arrays=instrument, provenance=provenance,
        _numerical_identity=object_id("numerical.source"))
    return source, numerical_origin(source, past, artifact_id="numerical.origin-arrays"), past


def assess_receiver_metric(protocol, origin, receivers):
    with pytest.MonkeyPatch.context() as patch:
        bind_numerical_identities(patch, origin)
        return _assess_receiver_metric(protocol, origin, receivers)


def reduce_response_frontier(protocol, source, origin, assessment, metric, **kwargs):
    with pytest.MonkeyPatch.context() as patch:
        bind_numerical_identities(patch, source, origin, assessment)
        return _reduce_response_frontier(protocol, source, origin, assessment, metric, **kwargs)


@pytest.fixture
def complete_frontier_input(provenance):
    # Known 3-4-5 score norms over disclosed numerical inputs, not acquired outcomes.
    design, initial, templates, model = mechanical_case()
    design = replace(design, horizon_steps=(1, 2), receiver_count=48)
    templates = templates | {"receiver_coefficients": np.eye(48).reshape(48, 2, 2, 3, 4)}
    source, origin, _ = numerical_operands(design, initial, templates, model, provenance=provenance)
    axes = np.asarray([np.diag(np.eye(4)[i]) for i in range(4)], dtype="<c16")
    receivers = np.einsum("rpsjc,cab->rpsjab", templates["receiver_coefficients"], axes)
    _, receiver_arrays = product({"receivers": receivers}, "test.frontier.origin-arrays",
        (source._numerical_identity, identity(design)))
    origin = replace(origin, arrays=receiver_arrays)
    protocol = MatrixResponseFrontierProtocol("test.frontier.protocol", design.rule.identity, design.view.timestep,
        design.horizon_steps, tuple(sorted((MatrixResponseActionScale(a.role, a.amplitude, a.force_norm, a.pulse_steps)
            for a in design.actions), key=lambda a: a.role)), D("1e-12"))
    panels = tuple(panel for panel in source.root.streams if panel.role != "PREFIX")
    scores = []
    for panel in panels:
        for action in design.actions:
            for horizon in design.horizon_steps:
                for receiver in range(48):
                    error = {0: D("3e-6"), 1: D("4e-6"), 24: D("1e-3")}.get(receiver, D(0)) * horizon
                    for predictor in PREDICTORS:
                        truth = D("-1e-10")
                        scores.append(MatrixFactorResponseScore(panel.panel_id, panel.role, action.action_id,
                            horizon, receiver, predictor, truth + error, truth, abs(error), error, None, True, D(0)))
    assessment = SimpleNamespace(source=source._numerical_identity, origin=origin._numerical_identity,
        scores=tuple(scores), native_reference_pass=True, requested_original_roots=1, requested_panels=2,
        numerical_convergence="UNASSESSED", _numerical_identity=object_id("numerical.assessment"))
    metric = assess_receiver_metric(protocol, origin, receivers)
    return protocol, source, origin, assessment, metric, receivers


def reduce(case):
    return reduce_response_frontier(*case[:5], stratum_id="test.family")


def test_nominal_scales_and_complete_weak_negative_census(complete_frontier_input):
    protocol, source, _, original, _, _ = complete_frontier_input
    result = reduce(complete_frontier_input)
    assert len(result.cells) == 2 * 4 * 2 * 5
    assert all(c.weak_receiver_count == c.negative_receiver_count == 48 for c in result.cells)
    cell = next(c for c in result.cells if c.horizon_step == 1)
    assert cell.position_error == D("5e-6")
    assert cell.momentum_error == D("1e-3")
    assert cell.scaled_loss == D(100)  # q scale .1 * .001**2 / 2
    assert protocol.action_scales[0].scales(D(".001"), 2) == (D(".00000015"), D(".0001"))
    assert source.design.normalization == "ODD_FINITE_RESPONSE_HALF_PLUS_MINUS"
    assert original.numerical_convergence == "UNASSESSED"
    assert result.admission.startswith("UNASSESSED")
    assert decode_canonical_bytes(result.canonical_bytes(), MatrixResponseRootFrontier, maximum_bytes=None) == result


def test_common_receiver_rotation_preserves_norm(complete_frontier_input):
    protocol, source, origin, assessment, metric, receivers = complete_frontier_input
    rotation = np.eye(48)
    rotation[:2, :2] = ((.6, .8), (-.8, .6))
    rotated = np.einsum("rt,tpsjab->rpsjab", rotation, receivers)
    assess_receiver_metric(protocol, origin, rotated)
    scores = []
    for row in assessment.scores:
        error = D("5e-6") * row.horizon_step if row.receiver_index == 0 else D(0) if row.receiver_index == 1 else row.signed_error
        scores.append(replace(row, predicted_odd_response=row.actual_odd_response + error, signed_error=error, absolute_error=abs(error)))
    result = reduce_response_frontier(protocol, source, origin, replace(assessment, scores=tuple(scores)), metric, stratum_id="test.family")
    assert [c.scaled_loss for c in result.cells] == [c.scaled_loss for c in reduce(complete_frontier_input).cells]


@pytest.mark.parametrize("defect", ("scaled", "mixed-phase", "nonfinite", "nonhermitian"))
def test_metric_refuses_invalid_native_receiver_chart(complete_frontier_input, defect):
    protocol, _, origin, _, _, values = complete_frontier_input
    bad = values.copy()
    if defect == "scaled":
        bad[0] *= 2
    elif defect == "mixed-phase":
        bad[[0, 24]] = bad[[24, 0]]
    elif defect == "nonfinite":
        bad[0, 0, 0, 0, 0, 0] = np.nan
    else:
        bad *= 1j
    with pytest.raises(ValueError, match="receiver|metric"):
        assess_receiver_metric(protocol, origin, bad)


@pytest.mark.parametrize("defect", ("missing", "duplicate", "truth", "signed"))
def test_reducer_refuses_census_or_same_outcome_substitution(complete_frontier_input, defect):
    protocol, source, origin, assessment, metric, _ = complete_frontier_input
    rows = assessment.scores
    if defect == "missing":
        rows = rows[:-1]
    elif defect == "duplicate":
        rows = rows[:-1] + (rows[0],)
    elif defect == "truth":
        rows = (replace(rows[0], actual_odd_response=D("-2e-10")),) + rows[1:]
    else:
        rows = (replace(rows[0], signed_error=D(0), absolute_error=D(0)),) + rows[1:]
    with pytest.raises(ValueError, match="census|outcome|difference"):
        reduce_response_frontier(protocol, source, origin, replace(assessment, scores=rows), metric, stratum_id="test.family")


def test_unresolved_comparator_remains_unresolved_at_every_later_horizon(complete_frontier_input):
    protocol, source, origin, assessment, metric, _ = complete_frontier_input
    rows = tuple(replace(r, predictor_disposition="UNRESOLVED", predicted_odd_response=None,
                        absolute_error=None, signed_error=None) if r.predictor == "SPECTRA" else r for r in assessment.scores)
    result = reduce_response_frontier(protocol, source, origin, replace(assessment, scores=rows), metric, stratum_id="test.family")
    assert all(v.cumulative_loss is None for v in result.horizon_losses if v.predictor == "SPECTRA")
    census = root_frontier_census(protocol, (result,), requested_root_ids=(result.root_id,))
    assert all(r["unresolved_roots"] == 1 for r in census if r["predictor"] == "SPECTRA")


def test_no_origin_and_numerical_failure_remain_in_original_denominator(complete_frontier_input):
    protocol = complete_frontier_input[0]
    measured = reduce(complete_frontier_input)
    absent = MatrixResponseRootFrontier("frontier.test.absent", protocol.identity, "test.absent", "test.absent-unit",
        "test.family", measured.source, "NO_CAUSAL_ORIGIN", None, None, None, None, (), (), (), (), (), None)
    requested = tuple(sorted((absent.root_id, measured.root_id)))
    census = root_frontier_census(protocol, (measured, absent), requested_root_ids=requested)
    assert all(r["requested_roots"] == 2 and r["no_origin_roots"] == 1 and r["crosschecked_measured_roots"] == 1 for r in census)
    failed = replace(measured, native_reference_pass=False)
    failed_census = root_frontier_census(protocol, (failed, absent), requested_root_ids=requested)
    assert all(r["unresolved_roots"] == 1 and not r["empirical_loss_breakpoints"] for r in failed_census)
    all_refusal = root_frontier_census(protocol, (absent,), requested_root_ids=(absent.root_id,))
    assert all(r["crosschecked_measured_roots"] == 0 and r["admission"] == "UNASSESSED" for r in all_refusal)
    with pytest.raises(ValueError, match="population"):
        root_frontier_census(protocol, (measured,), requested_root_ids=requested)
    with pytest.raises(ValueError, match="nested"):
        root_frontier_census(protocol, (measured, replace(absent, independent_group_id=measured.independent_group_id)), requested_root_ids=requested)


def test_source_metric_and_protocol_substitutions_refuse(complete_frontier_input):
    protocol, source, origin, assessment, metric, _ = complete_frontier_input
    with pytest.raises(ValueError, match="clocks"):
        reduce_response_frontier(replace(protocol, primary_timestep=D(".002")), source, origin, assessment, metric, stratum_id="test.family")
    with pytest.raises(ValueError, match="source/origin/metric"):
        reduce_response_frontier(protocol, source, origin, assessment, replace(metric, origin=object_id("test.other-origin")), stratum_id="test.family")


def test_retained_cells_and_cumulative_maxima_cannot_be_thinned_or_zeroed(complete_frontier_input):
    result = reduce(complete_frontier_input)
    with pytest.raises(ValueError, match="cumulative maximum"):
        replace(result, horizon_losses=tuple(replace(v, cumulative_loss=D(0)) for v in result.horizon_losses))
    with pytest.raises(ValueError, match="complete cell"):
        replace(result, cells=result.cells[:1])
    with pytest.raises(ValueError, match="complete panel"):
        replace(result, panel_census=result.panel_census[:1])
    changed = replace(result, cells=tuple(replace(c, position_error=c.position_error / 2) for c in result.cells))
    with pytest.raises(ValueError, match="metric loss"):
        root_frontier_census(complete_frontier_input[0], (changed,), requested_root_ids=(changed.root_id,))


def test_rule_compatibility_preserves_every_admission_tracking_operand(complete_frontier_input):
    protocol, source, origin, assessment, metric, _ = complete_frontier_input
    old = source.design.rule
    target = replace(old, spec_id="test.successor-rule")
    compatibility = MatrixResponseFactorRuleCompatibility("test.rule-compatibility", old, target)
    successor = replace(protocol, factor_rule=target.identity, factor_rule_compatibilities=(compatibility,))
    result = reduce_response_frontier(successor, source, origin, assessment, metric, stratum_id="test.family")
    assert result.factor_rule_compatibility == compatibility.identity
    assert source.design.rule is old and assessment.numerical_convergence == "UNASSESSED"
    with pytest.raises(ValueError, match="scientific criteria"):
        replace(compatibility, target=replace(target, associative_leakage_maximum=D(".1")))
    with pytest.raises(ValueError, match="scientific criteria"):
        replace(compatibility, original=SimpleNamespace(**{name: getattr(old, name) for name in old.__dataclass_fields__}))


def test_extra_panels_require_explicit_protocol_and_complete_actual_census(complete_frontier_input):
    protocol, source, origin, assessment, metric, _ = complete_frontier_input
    extended = replace(protocol, panel_roles=("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE", "INDEPENDENT_FUTURE"))
    # More panels are permitted by the scientific protocol, but missing them is not.
    with pytest.raises(ValueError, match="declared panel task"):
        reduce_response_frontier(extended, source, origin, assessment, metric, stratum_id="test.family")


def test_realized_origin_fields_cannot_substitute_actual_source(complete_frontier_input):
    protocol, source, origin, assessment, metric, _ = complete_frontier_input
    changed = replace(origin, clock_id="test.other-clock", _numerical_identity=object_id("numerical.other-clock"))
    changed_assessment = replace(assessment, origin=changed._numerical_identity)
    changed_metric = replace(metric, origin=changed._numerical_identity)
    with pytest.raises(ValueError, match="source/origin/metric"):
        reduce_response_frontier(protocol, source, changed, changed_assessment, changed_metric, stratum_id="test.family")


def test_origin_selection_retains_negative_uncertain_and_ambiguous_roots(complete_frontier_input):
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import (
        FactorObservation, FactorPopulation, FactorPopulationResult, FactorTrace,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import lifetime
    from tests.test_matrix_factor_lifetime import artifact, root, spec
    rule = spec()
    roots = tuple(root("test.origin." + suffix) for suffix in ("ambiguous", "negative", "selected", "unknown"))
    population = FactorPopulation("test.origin.population", roots, artifact("test.origin.inventory", b"inventory"), ())
    traces = []
    for original_root in roots:
        unknown, negative, ambiguous = (original_root.root_id.endswith(s) for s in ("unknown", "negative", "ambiguous"))
        observations = tuple(FactorObservation(t, "UNAVAILABLE", None, None, None, None,
                None, None, None, None, None, False, "unavailable") if unknown else
            FactorObservation(t, "AVAILABLE", True, not negative, not negative and t >= 16, None,
                D(1) if negative else D(0), D(0), D(0), None if t == 0 else D(0),
                None if t < 16 else D(0), ambiguous, None) for t in rule.lattice)
        _, diagnostics = product({"fixture": np.zeros(1)}, original_root.root_id + ".diagnostics", (rule.identity,))
        for view in ("PRIMARY", "FINE"):
            traces.append(FactorTrace(original_root, rule.identity, view, "Y", observations,
                lifetime(observations, rule), lifetime(observations, rule, origin_fixed=True),
                diagnostics.array_artifact, diagnostics.members))
    # The owner's order is PRIMARY/FINE; all nested views stay inside one root.
    result = FactorPopulationResult("test.origin.result", population, rule, tuple(traces), complete_frontier_input[1].provenance)
    policy = MatrixResponsePopulationPolicy("test.origin.policy", population.identity,
        ObjectIdentity.from_record(result.result_id, result), artifact("test.origin.case", b"exposed-case"),
        replace(complete_frontier_input[0], factor_rule=rule.identity), tuple(r.root_id for r in roots))
    artifacts = {t.root.root_id: ArtifactIdentity(t.root.root_id + ".primary.y.trace", "factor-trace-publication",
        t.SCHEMA, sha256(t.canonical_bytes()).hexdigest(), "application/json", len(t.canonical_bytes()))
        for t in traces if t.view == "PRIMARY"}
    selected = select_population_origins(policy, result, trace_artifacts=artifacts)
    assert tuple(r.disposition for r in selected) == ("NO_CAUSAL_ORIGIN", "NO_CAUSAL_ORIGIN", "SELECTED", "OBSERVATION_UNRESOLVED")
    assert selected[2].origin_tick == 16 and selected[2].cutoff == D(".016")
    assert traces[0].moving_lifetime.origin_tick == 16  # frame ambiguity is not structural disappearance
    assert len(selected) == 4
    with pytest.raises(ValueError, match="published trace identity"):
        select_population_origins(policy, result, trace_artifacts={k: v for k, v in artifacts.items() if k != roots[0].root_id})
    with pytest.raises(ValueError, match="published trace bytes"):
        select_population_origins(policy, result, trace_artifacts=artifacts | {
            roots[0].root_id: replace(artifacts[roots[0].root_id], sha256="f" * 64)})
    with pytest.raises(ValueError, match="supplier population/rule"):
        select_population_origins(replace(policy, requested_root_ids=policy.requested_root_ids[:-1]), result, trace_artifacts=artifacts)
