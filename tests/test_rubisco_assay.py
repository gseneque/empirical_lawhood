"""Independent equations, scientific identity joins and exposed R1 preservation."""

from dataclasses import replace
from decimal import Decimal, localcontext
from math import log

import numpy as np
import pytest

from empirical_lawhood.adapters.simulators.rubisco_assay import core
from empirical_lawhood.adapters.simulators.rubisco_assay.core import (
    GasQuery, Kinetics, Products, compatible_kinetics, execute_assay,
    log_sensitivity, next_query, reduce_products, reference_rates, specificity_energy_scale,
)
from empirical_lawhood.adapters.simulators.rubisco_assay.fixture import historical_r1_config
from empirical_lawhood.adapters.simulators.rubisco_assay.records import (
    AssayConfig, AssayEvaluation, AssayProjection, AssayQuery, AssayResult,
)
from empirical_lawhood.adapters.simulators.rubisco_assay.science import (
    evaluate_histories, execute_round, project_history, run_assay,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import ScientificStatus

P = Kinetics(6, 75, 1, 750)


@pytest.mark.parametrize("co2,o2", [(0, 0), (10, 0), (0, 250), (10, 250), (7500, 250)])
def test_products_match_independent_competitive_equations(co2, o2):
    query = GasQuery(co2, o2, 2.5)
    products = execute_assay(P, query)
    # Direct mass-action competitive equations are independent of the solver
    # and of the implementation's reference_rates function.
    vc = 6 * co2 / (75 * (1 + o2 / 750) + co2)
    vo = o2 / (750 * (1 + co2 / 75) + o2)
    assert products.pga_per_site == pytest.approx((2 * vc + vo) * 2.5, abs=1e-12)
    assert products.pgly_per_site == pytest.approx(vo * 2.5, abs=1e-12)
    assert reduce_products(products) == pytest.approx((vc, vo), abs=1e-12)
    assert reference_rates(P, query) == pytest.approx((vc, vo), abs=1e-12)
    assert products.balance_residual < 1e-12


def test_product_solver_does_not_use_closed_form_oracle(monkeypatch):
    def forbidden(*args):
        raise AssertionError("oracle was used to create products")
    monkeypatch.setattr(core, "reference_rates", forbidden)
    assert execute_assay(P, GasQuery(10, 250)).pga_per_site > 0


def test_specificity_and_concentration_units_scale_together():
    query = GasQuery(15, 250)
    vc, vo = reduce_products(execute_assay(P, query))
    assert vc / vo * query.o2_um / query.co2_um == pytest.approx(60)
    scaled = replace(P, kc=750, ko=7500)
    assert reference_rates(scaled, GasQuery(150, 2500)) == pytest.approx((vc, vo))


def test_feedback_uses_observation_and_declared_threshold():
    previous = GasQuery(10, 250)
    assert next_query(previous, execute_assay(P, previous)).co2_um == 20
    assert next_query(previous, Products(2.01, .01, 1, 0)).co2_um == 5
    # Exactly vo/vc=.1 falls in the otherwise-halving arm.
    assert next_query(previous, Products(2.1, .1, 1, 0)).co2_um == 5
    with pytest.raises(ValueError, match="NONATTEMPT"):
        next_query(GasQuery(1000, 250), Products(3, 1, 1, 0))
    with pytest.raises(ValueError, match="duration"):
        next_query(previous, Products(2, .1, 2, 0))
    with pytest.raises(ValueError, match="positive carboxylation"):
        next_query(GasQuery(0, 250), execute_assay(P, GasQuery(0, 250)))


def test_three_summary_values_leave_oxygenation_parameters_nonidentified():
    family = tuple(compatible_kinetics(kcat_c=6, kc_air=100, specificity=60,
                                       air_o2_um=250, ko=ko) for ko in (100, 750, 3000))
    for parameters in family:
        assert parameters.kc * (1 + 250 / parameters.ko) == pytest.approx(100)
        assert parameters.specificity == pytest.approx(60)
        assert reference_rates(parameters, GasQuery(10, 250)) == pytest.approx((6 / 11, 5 / 22))
    rates = tuple(reference_rates(p, GasQuery(10, 1000))[0] for p in family)
    assert max(rates) / min(rates) > 2


def test_local_sensitivity_rank_and_independent_finite_difference():
    query = GasQuery(10, 250)
    single = log_sensitivity(P, (query,))
    varied = log_sensitivity(P, tuple(GasQuery(c, o) for c in (10, 200) for o in (50, 1000)))
    assert np.linalg.matrix_rank(single) == 2
    assert np.linalg.matrix_rank(varied) == 4
    for index, name in enumerate(("kcat_c", "kc", "kcat_o", "ko")):
        epsilon = 1e-5
        high = replace(P, **{name: getattr(P, name) * np.exp(epsilon)})
        low = replace(P, **{name: getattr(P, name) * np.exp(-epsilon)})
        derivative = (np.log(reference_rates(high, query)) - np.log(reference_rates(low, query))) / (2 * epsilon)
        assert single[:, index] == pytest.approx(derivative, abs=1e-9)
    assert specificity_energy_scale(1.1) == pytest.approx(.00831446261815324 * 298.15 * log(1.1))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, None, "1"])
def test_invalid_gases_and_parameters_refuse(value):
    with pytest.raises(ValueError):
        GasQuery(value, 250)
    with pytest.raises(ValueError):
        Kinetics(value, 75, 1, 750)


def test_invalid_products_and_bounds_refuse():
    for query in ((10001, 0, 1), (0, 10001, 1), (0, 0, 1001), (0, 0, 0)):
        with pytest.raises(ValueError):
            GasQuery(*query)
    with pytest.raises(ValueError, match="stoichiometry"):
        Products(0, 1, 1, 0)
    with pytest.raises(ValueError, match="positive-gas"):
        log_sensitivity(P, (GasQuery(0, 250),))
    with pytest.raises(ArithmeticError, match="finite occupancy"):
        execute_assay(Kinetics(6, 1e-320, 1, 750), GasQuery(10, 250))


def test_exposed_twelve_query_fixture_preserves_constants_and_feedback_path():
    config = historical_r1_config(plan_sha256="a" * 64)
    assert config.cases[0].kcat_c == Decimal("6.08339")
    assert config.cases[1].kcat_c == Decimal("3.78385")
    assert config.assumed_ko_um == 750 and config.assumed_air_o2_um == 250
    reports, evaluation = run_assay(config)
    assert len(config.tasks()) == 12
    assert evaluation.scientific_status is ScientificStatus.SUPPORTED
    assert evaluation.independent_biological_units == 0
    assert evaluation.biological_validation == "NOT_PERFORMED"
    expected_path = ((10, 50), (200, 50), (10, 1000), (200, 1000), (100, 1000), (200, 1000))
    for report in reports:
        assert tuple((r.realized_query.co2_um, r.realized_query.o2_um) for r in report.source_results) == expected_path
        assert report.log_sensitivity_rank == 4
        assert report.maximum_relative_forecast_error <= Decimal("1e-10")
        assert report.source_results[-1].committed_next_query is None
    assert float(reports[0].smallest_singular_value) == pytest.approx(.388954, abs=1e-6)
    assert float(reports[1].smallest_singular_value) == pytest.approx(.378395, abs=1e-6)
    assert float(reports[0].condition_number) == pytest.approx(7.50435, abs=1e-5)
    assert float(reports[1].condition_number) == pytest.approx(7.74800, abs=1e-5)


def test_successor_records_round_trip_through_strict_current_decoder():
    config = historical_r1_config(plan_sha256="a" * 64)
    reports, evaluation = run_assay(config)
    for record, record_type in ((config, AssayConfig), (reports[0].source_results[0], AssayResult),
                                (reports[0], AssayProjection), (evaluation, AssayEvaluation)):
        assert decode_canonical_bytes(record.canonical_bytes(), record_type, maximum_bytes=65536) == record
    assert config.SCHEMA.startswith("empirical-lawhood/")
    assert b"icf-yolo" not in config.canonical_bytes()


def test_conditional_assumptions_cannot_silently_change():
    config = historical_r1_config(plan_sha256="a" * 64)
    for key, value in (("temperature_k", Decimal("300")), ("molecular_prediction_claimed", True),
                       ("activated_enzyme", False), ("saturating_rubp", False),
                       ("clamped_gases", False), ("stationary_repreparation_per_query", False),
                       ("maximum_native_calls", 11), ("rounds_per_case", True),
                       ("assumed_ko_um", Decimal("500"))):
        with pytest.raises(ValueError):
            replace(config, **{key: value})
    with pytest.raises(ValueError):
        replace(config.cases[0], preparation_scope="BIOLOGICAL_UNIT")


def test_missing_reordered_and_substituted_histories_refuse():
    config = historical_r1_config(plan_sha256="a" * 64)
    reports, _ = run_assay(config)
    history = reports[0].source_results
    for invalid in (history[:-1], tuple(reversed(history)), reports[1].source_results):
        with pytest.raises(ValueError, match="census"):
            project_history(config, config.cases[0].case_id, invalid)
    with pytest.raises(ValueError, match="assigned"):
        evaluate_histories(config, reports[:1])
    with pytest.raises(ValueError, match="inconsistent"):
        evaluate_histories(config, (replace(reports[0], maximum_relative_forecast_error=Decimal(0)), reports[1]))


def test_predecessor_identity_and_policy_checked_before_solver(monkeypatch):
    config = historical_r1_config(plan_sha256="a" * 64)
    case = config.cases[0]
    first = execute_round(config, case.case_id, 0)
    def forbidden(*args):
        raise AssertionError("native calculation entered before predecessor check")
    monkeypatch.setattr("empirical_lawhood.adapters.simulators.rubisco_assay.science.execute_assay", forbidden)
    with pytest.raises(ValueError, match="predecessor"):
        execute_round(config, case.case_id, 1, replace(first, case=ObjectIdentity.from_record(
            config.cases[1].case_id, config.cases[1])))
    with pytest.raises(ValueError, match="policy"):
        execute_round(config, case.case_id, 1, replace(first, committed_next_query=AssayQuery(
            Decimal(300), Decimal(50), Decimal(1))))
    changed_query = AssayQuery(Decimal(30), Decimal(50), Decimal(1))
    with pytest.raises(ValueError, match="initial gas probe"):
        execute_round(config, case.case_id, 1, replace(first, requested_query=changed_query,
            accepted_query=changed_query, applied_query=changed_query, realized_query=changed_query))


def test_wrong_frozen_forecast_retains_negative_complete_result():
    config = historical_r1_config(plan_sha256="a" * 64)
    wrong = replace(config.cases[0], initial_forecast=(Decimal(100), Decimal(100)))
    config = replace(config, cases=(wrong, config.cases[1]))
    reports, evaluation = run_assay(config)
    assert len(reports[0].source_results) == 6
    assert evaluation.scientific_status is ScientificStatus.NOT_SUPPORTED
    assert reports[0].maximum_relative_forecast_error > 1


def test_one_gas_probe_retains_rank_obstruction_instead_of_infinite_condition_number():
    original = historical_r1_config(plan_sha256="a" * 64)
    config = replace(original, cases=(original.cases[0],), initial_fixed_queries=original.initial_fixed_queries[:1],
                     rounds_per_case=1, maximum_native_calls=1)
    reports, evaluation = run_assay(config)
    assert reports[0].log_sensitivity_rank == 2
    assert reports[0].condition_number is None
    assert reports[0].smallest_singular_value == 0
    assert evaluation.scientific_status is ScientificStatus.NOT_SUPPORTED
    assert "CONDITIONAL_LOCAL_INFORMATION_RANK_DEFICIENT" in evaluation.reason_codes


def test_science_is_independent_of_ambient_decimal_context():
    config = historical_r1_config(plan_sha256="a" * 64)
    expected = run_assay(config)
    with localcontext() as context:
        context.prec = 3
        actual = run_assay(config)
    assert actual == expected
