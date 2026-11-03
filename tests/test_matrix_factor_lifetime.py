"""Scientific falsifiers for new exposed factor semantics; no native campaign."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256

import numpy as np
import pytest
from scipy.linalg import expm

from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import (
    FactorEventSpec, FactorPopulation, FactorPopulationResult, FactorRootRole, ScalarClosureSpec,
)
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import (
    SectorMeasurement, causal_observations, eligible_origins, lifetime,
    align_factor, decimal_measurement, measure_sector, measure_trace, population_counts, risk_sets, scalar_closure_ratios, trace,
)
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.products import (
    read_result, recurrence_intervals, residual_survival_intervals, validate_diagnostics,
)
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.scalar_assessment import assess_scalar_trace, independent_scalar_closure_ratio
from empirical_lawhood.adapters.simulators.six_matrix_response.model import su2_generators
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays


def spec(**changes):
    defaults = dict(spec_id="test.factor.rule", sectors=("Y",), lattice=(0, 16, 32, 48),
        primary_dt=Decimal("0.001"), risk_start_tick=16, trailing_persistence_ticks=16,
        associative_leakage_maximum=Decimal("0.01"), lie_leakage_maximum=Decimal("0.01"),
        factor_fit_angle_maximum_degrees=Decimal("5"), adjacent_angle_maximum_degrees=Decimal("30"),
        origin_angle_maximum_degrees=Decimal("5"), identifiability_relative_gap=Decimal("1e-10"),
        identifiability_absolute_fourth=Decimal("1e-20"), frame_alignment_minimum_overlap=Decimal("0.1"))
    return FactorEventSpec(**(defaults | changes))


def artifact(name, raw, *, media="application/json"):
    return ArtifactIdentity(name, "development", "empirical-lawhood/test/factor-input",
                            sha256(raw).hexdigest(), media, len(raw))


def root(name="test.factor.root", family="test.family"):
    return FactorRootRole(name, name+".unit", family,
        ObjectIdentity("test.history.source", "empirical-lawhood/test/history-source", "1.0.0", "a"*64),
        artifact(name+".native", b"native"), artifact(name+".receipt", b"receipt"))


def measurements(rule, *, triplet=None):
    value = measure_sector(algebra.RIGHT if triplet is None else triplet, rule)
    return {tick: value for tick in rule.lattice}


def test_exact_factor_identification_is_not_lie_only_admission():
    rule = spec()
    exact = measure_sector(algebra.RIGHT, rule)
    assert exact.identifiable
    observations, _ = causal_observations(rule, measurements(rule))
    assert [o.causal_admitted for o in observations] == [False, True, True, True]
    # A Lie-closed irreducible spin3/2 algebra fails associative admission.
    low = algebra.coords(su2_generators(4)/np.sqrt(5)).T
    metrics, fields = algebra.algebra(low)
    lie_only = SectorMeasurement(True, exact.spectrum, low@low.T, low,
        algebra.exact_factor(fields), Decimal(repr(metrics["associative_leakage"])),
        Decimal(repr(metrics["lie_leakage"])), Decimal(0))
    bad, _ = causal_observations(rule, {t: lie_only for t in rule.lattice})
    assert all(not o.raw_admitted for o in bad)
    assert lifetime(bad, rule).disposition == "NOT_AT_RISK"


def test_degenerate_sector_preserves_spectrum_and_unknown_lifetime():
    rule = spec()
    empty = measure_sector(np.zeros((3, 4, 4), dtype="<c16"), rule)
    assert not empty.identifiable
    assert empty.spectrum.shape == (15,)
    observations, _ = causal_observations(rule, {t: empty for t in rule.lattice})
    assert all(o.status == "UNIDENTIFIABLE" and o.raw_admitted is None for o in observations)
    assert lifetime(observations, rule).disposition == "UNKNOWN"


def test_negative_finite_diagnostic_is_preserved_not_clipped():
    assert decimal_measurement(-.1) == Decimal("-0.1")
    rule = spec()
    data = measurements(rule)
    data[0] = replace(data[0], associative_leakage=Decimal("-0.1"))
    with pytest.raises(ValueError, match="at least"):
        causal_observations(rule, data)


def test_scalar_closure_disagreement_keeps_original_rule_and_independent_operand():
    scalar = ScalarClosureSpec("test.scalar.rule", artifact("test.scalar.owner", b"scalar"), Decimal("0.30"))
    rule = spec(scalar_closure=scalar)
    observations, _ = causal_observations(rule, measurements(rule),
        scalar_closure={t:Decimal("0.31") for t in rule.lattice})
    assert all(o.raw_admitted is True and o.scalar_closure_pass is False for o in observations)
    assert all(o.scalar_closure_ratio == Decimal("0.31") for o in observations)
    with pytest.raises(ValueError, match="independent normalization"):
        causal_observations(spec(), measurements(spec()), scalar_closure={16:Decimal("0.31")})
    with pytest.raises(ValueError, match="original 0.30"):
        replace(scalar, threshold=Decimal("0.31"))


def test_unknown_observation_does_not_manufacture_exit_or_survival():
    rule = spec()
    data = measurements(rule)
    data[32] = None
    observations, _ = causal_observations(rule, data)
    life = lifetime(observations, rule)
    assert life.onset == "LEFT_PRESENT"
    assert life.disposition == "UNKNOWN"
    assert life.last_known_survival_tick == 16
    assert life.exit_upper_tick is None
    assert life.unavailable_ticks == (32,)
    assert observations[-1].causal_admitted is False


def test_known_failure_has_observed_interval_and_never_admitted_denominator():
    rule = spec()
    data = measurements(rule)
    data[32] = replace(data[32], associative_leakage=Decimal("0.1"))
    observations, _ = causal_observations(rule, data)
    life = lifetime(observations, rule)
    assert (life.disposition, life.last_known_survival_tick, life.exit_upper_tick) == ("EXIT_INTERVAL", 16, 32)
    bad = {t: replace(data[0], associative_leakage=Decimal("0.1")) for t in rule.lattice}
    o, _ = causal_observations(rule, bad)
    assert lifetime(o, rule).onset == "NEVER_ADMITTED"


def test_first_admission_and_origin_are_causal_under_future_poisoning():
    rule = spec(risk_start_tick=0, trailing_persistence_ticks=0)
    data = measurements(rule)
    baseline, _ = causal_observations(rule, data)
    poisoned = dict(data)
    poisoned[48] = replace(data[48], associative_leakage=Decimal("0.9"))
    alternate, _ = causal_observations(rule, poisoned)
    assert baseline[:3] == alternate[:3]
    assert lifetime(baseline, rule).disposition == "RIGHT_CENSORED"
    assert lifetime(alternate, rule).disposition == "EXIT_INTERVAL"
    assert eligible_origins(trace(rule, root(), "PRIMARY", "Y", data)[0], rule)[0] == 0


def test_signs_and_degenerate_basis_rotations_do_not_create_exit():
    rule = spec()
    data = measurements(rule)
    old = data[16]
    rotation = np.array([[0., 1., 0.], [-1., 0., 0.], [0., 0., 1.]])
    data[16] = replace(old, basis=old.basis@rotation)
    result, _ = trace(rule, root(), "PRIMARY", "Y", data)
    assert result.moving_lifetime.disposition == "RIGHT_CENSORED"
    assert result.origin_fixed_lifetime.disposition == "RIGHT_CENSORED"


def test_ambiguous_frame_and_reflection_preserve_subspace_but_refuse_frame_use():
    rule = spec(risk_start_tick=0, trailing_persistence_ticks=0,
                adjacent_angle_maximum_degrees=Decimal("90"))
    data = measurements(rule)
    # LEFT/RIGHT are orthogonal factor spaces: their component match is
    # genuinely ambiguous, while the declared permissive structural rule can
    # retain a factor. That tick cannot supply an unambiguous B origin frame.
    data[16] = replace(data[16], factor=algebra.RIGHT)
    data[32] = replace(data[32], factor=algebra.LEFT)
    record, _ = trace(rule, root(), "PRIMARY", "Y", data)
    assert record.observations[2].alignment_ambiguous
    assert 32 not in eligible_origins(record, rule)
    assert 48 not in eligible_origins(record, rule)
    assert record.moving_lifetime.disposition == "RIGHT_CENSORED"
    reflected = algebra.LEFT.copy(); reflected[0] *= -1
    aligned, ambiguous, angle = align_factor(algebra.LEFT, reflected, Decimal("0.1"))
    assert ambiguous and float(angle) < 1e-5
    np.testing.assert_allclose(algebra.coords(aligned)@algebra.coords(aligned).T, np.eye(3), atol=1e-12)


def test_failed_factor_track_can_supply_a_separate_later_causal_origin():
    rule = spec(risk_start_tick=0, trailing_persistence_ticks=0,
                adjacent_angle_maximum_degrees=Decimal("90"))
    data = measurements(rule)
    data[16] = replace(data[16], factor=algebra.RIGHT)
    data[32] = replace(data[32], associative_leakage=Decimal("0.2"))
    record, _ = trace(rule, root(), "PRIMARY", "Y", data)
    assert record.observations[1].alignment_ambiguous
    assert not record.observations[-1].alignment_ambiguous
    assert 48 in eligible_origins(record, rule)
    assert record.moving_lifetime.disposition == "EXIT_INTERVAL"


def test_unitary_covariance_of_factor_admission_and_projector_tracking():
    rule = spec()
    rng = np.random.default_rng(421)
    unitary, _ = np.linalg.qr(rng.normal(size=(4, 4))+1j*rng.normal(size=(4, 4)))
    baseline, _ = trace(rule, root(), "PRIMARY", "Y", measurements(rule))
    transformed, _ = trace(rule, root(), "PRIMARY", "Y",
        measurements(rule, triplet=unitary@algebra.RIGHT@unitary.conj().T))
    assert [o.raw_admitted for o in baseline.observations] == [o.raw_admitted for o in transformed.observations]
    assert baseline.moving_lifetime == transformed.moving_lifetime


def test_moving_factor_and_origin_fixed_subspace_answer_distinct_questions():
    rule = spec(risk_start_tick=0, trailing_persistence_ticks=0)
    generator = np.kron(algebra.PAULI[2], algebra.PAULI[2])
    data = {}
    for tick in rule.lattice:
        unitary = expm(-1j*(tick/48)*.2*generator)
        data[tick] = measure_sector(unitary@algebra.RIGHT@unitary.conj().T, rule)
    result, _ = trace(rule, root(), "PRIMARY", "Y", data)
    assert result.moving_lifetime.disposition == "RIGHT_CENSORED"
    assert result.origin_fixed_lifetime.disposition == "EXIT_INTERVAL"


def test_common_lattice_and_matching_fine_times_preserve_dense_role():
    rule = spec()
    positions = np.broadcast_to(np.stack((algebra.LEFT, algebra.RIGHT)), (97, 2, 3, 4, 4)).copy()
    primary, p = measure_trace(rule, root(), "PRIMARY", "Y", positions)
    fine, f = measure_trace(rule, root(), "FINE", "Y", positions)
    assert primary.observations == fine.observations
    assert len(p["ticks"]) == len(f["ticks"]) == 4
    validate_diagnostics(p, primary, rule)
    with pytest.raises(ValueError, match="uniform"):
        spec(lattice=(0, 16, 17, 48))
    with pytest.raises(ValueError, match="full native"):
        measure_trace(rule, root(), "FINE", "Y", positions[:48])


def population_result(rule, records):
    population = FactorPopulation("test.factor.population", tuple(sorted((r.root for r in records[::2]), key=lambda r:r.root_id)),
        artifact("test.factor.inventory", b"inventory"), ("original.analysis.intermediate-source-unavailable",))
    source = (("test-fixture.py", "b"*64),)
    provenance = NumericalProducingProvenance('{"python":"fixture","numpy":"fixture","scipy":"fixture","system":"fixture","machine":"fixture","threadpools":[]}',
        "c"*64, source, sha256(canonical_json_bytes(source)).hexdigest(), "d"*40, False)
    return FactorPopulationResult("test.factor.result", population, rule, tuple(records), provenance)


def test_complete_root_family_view_denominators_and_unknown_envelopes():
    rule = spec()
    records = []
    for name, data in (("test.r0", measurements(rule)), ("test.r1", {t: None for t in rule.lattice})):
        for view in ("PRIMARY", "FINE"):
            records.append(trace(rule, root(name), view, "Y", data)[0])
    result = population_result(rule, records)
    counts = population_counts(result)
    for value in counts.values():
        assert value["requested_roots"] == 2
        assert value["admitted_roots"] == 1
        assert value["unknown_roots"] == 1
        assert value["requested_observations"] == 8
    intervals = recurrence_intervals(result, confidence=Decimal("0.95"))
    assert all(x["observed_admission_fraction_lower"] == .5 and x["observed_admission_fraction_upper"] == 1 for x in intervals.values())
    assert all(not x["simultaneous_coverage"] for x in intervals.values())
    risk = risk_sets(result)
    for rows in risk.values():
        assert rows[0]["requested_roots"] == 2
        assert rows[0]["left_present_roots"] == 1
        assert rows[0]["uncertain_admission_through_tick"] == 1
    with pytest.raises(ValueError, match="census"):
        replace(result, traces=result.traces[:-1])


def test_residual_survival_uses_independent_roots_and_retains_unknown_risk():
    rule = spec()
    records = []
    absent = {t:None for t in rule.lattice}
    gap = measurements(rule);gap[32] = None
    for name, data in (("test.r0", gap), ("test.r1", absent)):
        for view in ("PRIMARY", "FINE"):
            records.append(trace(rule, root(name), view, "Y", data)[0])
    result = population_result(rule, records)
    survival = residual_survival_intervals(result, confidence=Decimal("0.95"))
    for rows in survival.values():
        assert rows[0]["requested_roots"] == 2
        assert rows[0]["conditional_risk_roots"] == 1
        assert rows[0]["survival_fraction_lower"] == 1
        assert rows[-1]["survival_fraction_lower"] == 0
        assert rows[-1]["survival_fraction_upper"] == 1
    empty = population_result(rule, [trace(rule, root(), v, "Y", absent)[0] for v in ("PRIMARY", "FINE")])
    assert all(rows[-1]["survival_fraction_lower"] is None for rows in residual_survival_intervals(empty, confidence=Decimal("0.95")).values())


def test_strict_retained_read_authenticates_arrays_rule_and_population_without_spectra(monkeypatch):
    rule = spec()
    positions = np.broadcast_to(np.stack((algebra.LEFT, algebra.RIGHT)), (97, 2, 3, 4, 4)).copy()
    store = {root().native_arrays.artifact_id:b"native", root().native_result.artifact_id:b"receipt", "test.factor.inventory":b"inventory"}
    records = []
    for view in ("PRIMARY", "FINE"):
        value, arrays = measure_trace(rule, root(), view, "Y", positions)
        raw, members = encode_matrix_arrays(arrays, nonfinite_members=("spectrum", "projector", "basis", "factor", "aligned_factor"))
        identity = artifact("test.diagnostics."+view.lower(), raw, media="application/zip")
        records.append(replace(value, diagnostics=identity, diagnostic_members=members)); store[identity.artifact_id] = raw
    result = population_result(rule, records)
    monkeypatch.setattr(algebra, "sector", lambda *a, **k:pytest.fail("retained read recalculates spectra"))
    assert read_result(result.canonical_bytes(), expected_population=result.population, expected_rule=rule,
        expected_provenance=result.producing_provenance,
        artifact_reader=lambda i:store[i.artifact_id]) == result
    assert decode_canonical_bytes(result.canonical_bytes(), FactorPopulationResult, maximum_bytes=None) == result
    with pytest.raises(ValueError, match="event rule"):
        read_result(result.canonical_bytes(), expected_population=result.population, expected_rule=replace(rule, lie_leakage_maximum=Decimal("0.02")),
            expected_provenance=result.producing_provenance,
            artifact_reader=lambda i:store[i.artifact_id])
    store[root().native_arrays.artifact_id] = b"corrupt"
    with pytest.raises(ValueError, match="artifact bytes"):
        read_result(result.canonical_bytes(), expected_population=result.population, expected_rule=rule,
            expected_provenance=result.producing_provenance,
            artifact_reader=lambda i:store[i.artifact_id])


def test_retained_admission_or_root_substitution_refuses():
    rule = spec()
    records = [trace(rule, root(), view, "Y", measurements(rule))[0] for view in ("PRIMARY", "FINE")]
    result = population_result(rule, records)
    observations = list(records[0].observations)
    observations[0] = replace(observations[0], causal_admitted=True)
    altered = replace(records[0], observations=tuple(observations))
    with pytest.raises(ValueError, match="causal past"):
        population_counts(replace(result, traces=(altered, records[1])))
    with pytest.raises(ValueError, match="census"):
        replace(result, traces=(replace(records[0], root=root("test.other")), records[1]))


@pytest.mark.parametrize("view", ("PRIMARY", "FINE"))
def test_scalar_producer_extraction_preserves_original_geometry_and_independent_oracle(view, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import ScalarClosureSpec
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.scalar_assessment import independent_scalar_closure_ratio
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import ideal_state
    from empirical_lawhood.adapters.simulators.six_matrix_response import response_observer
    original = ideal_state(q=2, alpha_tilde_x=8., alpha_tilde_y=8., constitution="11")
    positions = np.broadcast_to(original.positions, (97, *original.positions.shape)).copy()
    positions[:, 1, 0] *= 1.01
    arrays = {view.lower() + "_positions": positions,
        view.lower() + "_momenta": np.broadcast_to(original.momenta, (97, *original.momenta.shape)),
        view.lower() + "_alpha_tilde": np.full((97, 2), 8., dtype="<f8")}
    rule = spec(scalar_closure=ScalarClosureSpec("fixture.scalar", artifact("fixture.owner", b"original owner"), Decimal("0.30")))
    ratios = scalar_closure_ratios(rule, arrays, view)
    monkeypatch.setattr(response_observer, "geometry_sample", lambda **kwargs: pytest.fail("independent scalar oracle calls producer"))
    for sector, at in (("X", 0), ("Y", 1)):
        expected = independent_scalar_closure_ratio(positions[0, at], 8.)
        assert ratios[sector] == {tick: expected for tick in rule.lattice}


def test_independent_scalar_residual_uses_original_native_coupling_not_band_ratio(monkeypatch):
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
    from empirical_lawhood.adapters.simulators.six_matrix_response.history_source import history_native_parameters
    from empirical_lawhood.adapters.simulators.six_matrix_response.response_observer import geometry_sample
    member,_=history_native_parameters()
    fields=.4*algebra.LEFT+.1*algebra.RIGHT
    positions=np.stack((fields,2*fields))
    state=SixMatrixState(2,positions,np.zeros_like(positions),16,2/3,22/3)
    produced=geometry_sample(state=state,member=member,refinement=1)
    expected=(produced.x.closure_ratio,produced.y.closure_ratio)
    def blocked(*args,**kwargs):raise AssertionError('independent scalar reader entered spectrum')
    monkeypatch.setattr(np.linalg,'eigh',blocked);monkeypatch.setattr(np.linalg,'eigvalsh',blocked)
    assert independent_scalar_closure_ratio(positions[0],2/3)==expected[0]
    assert independent_scalar_closure_ratio(positions[1],22/3)==expected[1]
    assert independent_scalar_closure_ratio(positions[0],22/3)!=expected[0]
    assert independent_scalar_closure_ratio(np.zeros((3,4,4),dtype='<c16'),0)==Decimal('0.0')



@pytest.mark.parametrize("view", ("PRIMARY", "FINE"))
def test_self_consistent_wrong_scalar_ratio_refuses_raw_native_assessment(view):
    from empirical_lawhood.adapters.simulators.six_matrix_response.model import ideal_state
    initial = ideal_state(q=2, alpha_tilde_x=8., alpha_tilde_y=8., constitution="11")
    positions = np.broadcast_to(initial.positions, (97, *initial.positions.shape)).copy()
    positions[:, 1, 0] *= 1.01
    couplings = np.full((97, 2), 8., dtype="<f8")
    arrays = {view.lower() + "_positions": positions,
        view.lower() + "_momenta": np.broadcast_to(initial.momenta, (97, *initial.momenta.shape)),
        view.lower() + "_alpha_tilde": couplings}
    rule = spec(scalar_closure=ScalarClosureSpec("test.scalar.independent", artifact("test.scalar.owner", b"owner"), Decimal("0.30")))
    ratios = scalar_closure_ratios(rule, arrays, view)["Y"]
    observed, _ = measure_trace(rule, root(), view, "Y", positions, scalar_closure=ratios)
    result = assess_scalar_trace(observed, rule, positions, couplings)
    assert result == {"requested_observations": len(rule.lattice), "assessed_observations": len(rule.lattice),
        "disposition": "INDEPENDENTLY_ASSESSED"}
    values = list(observed.observations)
    wrong = values[1].scalar_closure_ratio + Decimal(1)
    values[1] = replace(values[1], scalar_closure_ratio=wrong, scalar_closure_pass=wrong <= rule.scalar_closure.threshold)
    with pytest.raises(ValueError, match="actual native fields/couplings"):
        assess_scalar_trace(replace(observed, observations=tuple(values)), rule, positions, couplings)
