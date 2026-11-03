"""Pure committed conditional queries and complete-history assessment.

Assessment is numerical agreement under supplied kinetics, not biochemical
validation, fresh evidence, an issued adjudication or a new EL capability.
SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from decimal import Decimal
from math import log

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import ScientificStatus

from .core import (Products, execute_assay, log_sensitivity, next_query, reduce_products,
                   reference_rates, specificity_energy_scale)
from .records import (AssayCase, AssayConfig, AssayEvaluation, AssayProjection,
                      AssayQuery, AssayResult)


def _case(config: AssayConfig, case_id: str) -> AssayCase:
    selected = tuple(case for case in config.cases if case.case_id == case_id)
    if len(selected) != 1:
        raise ValueError("assay case is outside the declared complete roster")
    return selected[0]


def _continuation(config: AssayConfig, case: AssayCase, index: int,
                  query: AssayQuery, products: Products) -> tuple[AssayQuery | None, tuple[Decimal, Decimal] | None]:
    if index == config.rounds_per_case - 1:
        return None, None
    if index + 1 < len(config.initial_fixed_queries):
        following = config.initial_fixed_queries[index + 1]
    else:
        selected = next_query(query.native(), products)
        following = AssayQuery(Decimal(str(selected.co2_um)), Decimal(str(selected.o2_um)),
                               Decimal(str(selected.duration_s)))
    rates = reference_rates(case.native(), following.native())
    return following, (Decimal(str(rates[0])), Decimal(str(rates[1])))


def execute_round(config: AssayConfig, case_id: str, round_index: int,
                  previous: AssayResult | None = None) -> AssayResult:
    """Perform one numerical query after verifying its committed predecessor.

    No paths, receipts, authorities or native processes are opened here. The
    caller's platform owner supplies authentic custody and complete lineage.
    """
    case = _case(config, case_id)
    if type(round_index) is not int or not 0 <= round_index < config.rounds_per_case:
        raise ValueError("assay round is outside the frozen query census")
    config_identity = ObjectIdentity.from_record(config.config_id, config)
    case_identity = ObjectIdentity.from_record(case.case_id, case)
    if round_index == 0:
        if previous is not None:
            raise ValueError("first assay query has an undeclared predecessor")
        query, prior = case.initial_query, config_identity
    else:
        if (previous is None or previous.config != config_identity or previous.case != case_identity
            or previous.result_id != f"{case.case_id}.round-{round_index - 1:02d}"
            or previous.round_index != round_index - 1 or previous.committed_next_query is None
            or previous.committed_next_forecast is None):
            raise ValueError("assay continuation changes its exact predecessor commitment")
        if (previous.round_index < len(config.initial_fixed_queries)
            and previous.realized_query != config.initial_fixed_queries[previous.round_index]):
            raise ValueError("assay predecessor changes a frozen initial gas probe")
        if (previous.round_index == 0 and previous.prior_commitment != config_identity) or (
            previous.round_index > 0 and previous.prior_commitment.object_id
            != f"{case.case_id}.round-{previous.round_index - 1:02d}"):
            raise ValueError("assay predecessor changes its earlier commitment scope")
        expected_query, _ = _continuation(config, case, round_index - 1,
                                           previous.realized_query, previous.products())
        if previous.committed_next_query != expected_query:
            raise ValueError("assay predecessor changed the frozen query policy")
        query = previous.committed_next_query
        prior = ObjectIdentity.from_record(previous.result_id, previous)
    products = execute_assay(case.native(), query.native())
    following, forecast = _continuation(config, case, round_index, query, products)
    return AssayResult(f"{case.case_id}.round-{round_index:02d}", config_identity, case_identity,
                       round_index, prior, query, query, query, query,
                       Decimal(str(products.pga_per_site)), Decimal(str(products.pgly_per_site)),
                       Decimal(str(products.balance_residual)), Decimal(round_index),
                       Decimal(round_index + 1), following, forecast)


def project_history(config: AssayConfig, case_id: str,
                    results: tuple[AssayResult, ...]) -> AssayProjection:
    """Reduce all assigned products and independently check scientific joins."""
    import numpy as np

    case = _case(config, case_id)
    config_identity = ObjectIdentity.from_record(config.config_id, config)
    case_identity = ObjectIdentity.from_record(case.case_id, case)
    if (not isinstance(results, tuple) or len(results) != config.rounds_per_case
        or tuple(r.result_id for r in results) != tuple(
            f"{case.case_id}.round-{i:02d}" for i in range(config.rounds_per_case))):
        raise ValueError("assay projection loses the complete ordered query census")
    rates, errors, specifics = [], [], []
    for index, result in enumerate(results):
        if result.config != config_identity or result.case != case_identity or result.round_index != index:
            raise ValueError("assay projection changes a parameter/history identity")
        prior = (config_identity if index == 0
                 else ObjectIdentity.from_record(results[index - 1].result_id, results[index - 1]))
        query = case.initial_query if index == 0 else results[index - 1].committed_next_query
        forecast = case.initial_forecast if index == 0 else results[index - 1].committed_next_forecast
        if result.prior_commitment != prior or result.realized_query != query or forecast is None:
            raise ValueError("assay observation detaches its forecast/action commitment")
        expected_next, _ = _continuation(config, case, index, result.realized_query, result.products())
        if result.committed_next_query != expected_next:
            raise ValueError("assay observation changes the frozen next-query policy or final stop")
        if (result.committed_next_forecast is None) != (index == config.rounds_per_case - 1):
            raise ValueError("assay forecast commitment omits continuation or exceeds the final stop")
        vc, vo = reduce_products(result.products())
        if vc <= 0 or vo <= 0:
            raise ValueError("paired-gas probe has no observable branch ratio")
        rates.append((Decimal(str(vc)), Decimal(str(vo))))
        errors.extend(abs(observed - float(predicted)) / max(abs(observed), 1e-12)
                      for observed, predicted in zip((vc, vo), forecast, strict=True))
        # Closed-form predictions and each separately observed product are
        # checked here. Their agreement concerns numerical implementation only.
        oracle = reference_rates(case.native(), result.realized_query.native())
        errors.extend(abs(observed - expected) / max(abs(expected), 1e-12)
                      for observed, expected in zip((vc, vo), oracle, strict=True))
        specifics.append((vc / vo) * (float(result.realized_query.o2_um) / float(result.realized_query.co2_um)))
    sensitivity = log_sensitivity(case.native(), tuple(q.native() for q in config.initial_fixed_queries))
    singular = np.linalg.svd(sensitivity, compute_uv=False)
    rank = int(np.linalg.matrix_rank(sensitivity, tol=1e-10))
    # A rank-deficient design retains its obstruction explicitly; no Infinity
    # is admitted into canonical records or mistaken for a usable condition.
    smallest = float(singular[-1]) if len(singular) == 4 else 0.0
    condition = Decimal(str(float(singular[0]) / smallest)) if rank == 4 and smallest > 0 else None
    return AssayProjection(f"{case.case_id}.project", config_identity, case_id, results, tuple(rates),
                           Decimal(str(max(errors))), max(r.balance_residual for r in results),
                           tuple(Decimal(str(s)) for s in specifics), rank, Decimal(str(smallest)),
                           condition, Decimal(str(max(abs(log(s / case.native().specificity))
                                                      for s in specifics))),
                           Decimal(str(specificity_energy_scale(1.1, float(config.temperature_k)))))


def evaluate_histories(config: AssayConfig,
                       projections: tuple[AssayProjection, ...]) -> AssayEvaluation:
    """Assess the complete case roster after reconstructing each projection."""
    if not isinstance(projections, tuple) or tuple(p.case_id for p in projections) != tuple(
            case.case_id for case in config.cases):
        raise ValueError("assay evaluator drops or substitutes an assigned numerical case")
    if any(project_history(config, p.case_id, p.source_results) != p for p in projections):
        raise ValueError("assay evaluator refuses a projection inconsistent with its complete products")
    supported = all(p.maximum_relative_forecast_error <= config.numerical_relative_tolerance
                    and p.maximum_balance_residual <= Decimal("1e-12")
                    and p.maximum_absolute_log_specificity_reconstruction_error <= Decimal("1e-10")
                    and p.log_sensitivity_rank == 4 for p in projections)
    reasons = ["BIOLOGICAL_PARAMETER_IDENTIFIABILITY_UNRESOLVED", "NO_MOLECULAR_OR_BIOLOGICAL_VALIDATION",
               "CONDITIONAL_NUMERICAL_ASSAY_PASSED" if supported else "CONDITIONAL_NUMERICAL_ASSAY_FAILED"]
    if any(p.log_sensitivity_rank < 4 for p in projections):
        reasons.append("CONDITIONAL_LOCAL_INFORMATION_RANK_DEFICIENT")
    return AssayEvaluation(f"{config.config_id}.evaluate", ObjectIdentity.from_record(config.config_id, config),
                           tuple(ObjectIdentity.from_record(p.report_id, p) for p in projections),
                           ScientificStatus.SUPPORTED if supported else ScientificStatus.NOT_SUPPORTED,
                           tuple(sorted(reasons)))


def run_assay(config: AssayConfig) -> tuple[tuple[AssayProjection, ...], AssayEvaluation]:
    """Exposed local computation; scheduler/custody integration is external."""
    projections = []
    for case in config.cases:
        results = []
        previous = None
        for index in range(config.rounds_per_case):
            previous = execute_round(config, case.case_id, index, previous)
            results.append(previous)
        projections.append(project_history(config, case.case_id, tuple(results)))
    reports = tuple(projections)
    return reports, evaluate_histories(config, reports)
