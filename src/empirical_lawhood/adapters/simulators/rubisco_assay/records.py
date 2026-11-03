"""Strict supplied operands and complete committed conditional assay histories.

These are successor records, not renamed historical canonical bytes.
SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings,
    validate_decimal, validate_sha256, validate_stable_id,
)
from empirical_lawhood.kernel.status import ScientificStatus

from .core import GasQuery, Kinetics, Products

PREFIX = "rubisco-conditional-assay"
PREPARATION_SCOPE = "CONDITIONAL_NUMERICAL_CONFIGURATION_NOT_BIOLOGICAL_UNIT"
FEEDBACK_POLICY = "double-co2-if-vo-over-vc-above-0.1-otherwise-halve"
EVIDENCE_ROLE = "EXPOSED_CONDITIONAL_NUMERICAL_DEVELOPMENT_NONPROMOTABLE"


def finite(values: tuple[Decimal, ...], *, positive: bool = False) -> None:
    if not isinstance(values, tuple):
        raise ValueError("assay scalar collections must be immutable tuples")
    for value in values:
        validate_decimal(value, field_name="assay_scalar", minimum=Decimal(0))
        if positive and value == 0:
            raise ValueError("assay scalar must be positive")


def _identity(value: ObjectIdentity, schema: str) -> None:
    if not isinstance(value, ObjectIdentity) or value.object_schema != schema:
        raise ValueError("assay record has a different operand schema")


@dataclass(frozen=True, slots=True)
class AssayQuery(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/rubisco-assay/query"
    co2_um: Decimal
    o2_um: Decimal
    duration_s: Decimal

    def __post_init__(self) -> None:
        finite((self.co2_um, self.o2_um, self.duration_s))
        self.native()

    def native(self) -> GasQuery:
        return GasQuery(float(self.co2_um), float(self.o2_um), float(self.duration_s))


@dataclass(frozen=True, slots=True)
class AssayCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/rubisco-assay/case"
    case_id: str
    kcat_c: Decimal
    kc: Decimal
    kcat_o: Decimal
    ko: Decimal
    calibration_summary_ids: tuple[str, ...]
    initial_query: AssayQuery
    initial_forecast: tuple[Decimal, Decimal]
    preparation_scope: str = PREPARATION_SCOPE

    def __post_init__(self) -> None:
        validate_stable_id(self.case_id, field_name="case_id")
        finite((self.kcat_c, self.kc, self.kcat_o, self.ko), positive=True)
        self.native()
        require_sorted_unique_strings(self.calibration_summary_ids, field_name="calibration_summary_ids")
        for identifier in self.calibration_summary_ids:
            validate_stable_id(identifier, field_name="calibration_summary_id")
        if not 1 <= len(self.calibration_summary_ids) <= 16 or not isinstance(self.initial_query, AssayQuery):
            raise ValueError("assay case needs bounded kinetics lineage and its typed query")
        finite(self.initial_forecast)
        if len(self.initial_forecast) != 2 or self.preparation_scope != PREPARATION_SCOPE:
            raise ValueError("assay case requires paired forecasts and numerical preparation scope")

    def native(self) -> Kinetics:
        return Kinetics(float(self.kcat_c), float(self.kc), float(self.kcat_o), float(self.ko))


@dataclass(frozen=True, slots=True)
class AssayConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/rubisco-assay/config"
    config_id: str
    cases: tuple[AssayCase, ...]
    curation_audit_sha256: str
    plan_sha256: str
    initial_fixed_queries: tuple[AssayQuery, ...]
    assumed_air_o2_um: Decimal
    assumed_ko_um: Decimal
    maximum_native_calls: int = 12
    rounds_per_case: int = 6
    feedback_policy: str = FEEDBACK_POLICY
    temperature_k: Decimal = Decimal("298.15")
    numerical_relative_tolerance: Decimal = Decimal("1e-10")
    molecular_prediction_claimed: bool = False
    activated_enzyme: bool = True
    saturating_rubp: bool = True
    clamped_gases: bool = True
    stationary_repreparation_per_query: bool = True
    evidence_role: str = EVIDENCE_ROLE

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        if not isinstance(self.cases, tuple) or not 1 <= len(self.cases) <= 16:
            raise ValueError("assay case roster must contain one to sixteen immutable cases")
        if any(not isinstance(case, AssayCase) for case in self.cases):
            raise ValueError("assay case roster has an untyped member")
        require_sorted_unique_strings(tuple(c.case_id for c in self.cases), field_name="case_ids")
        validate_sha256(self.curation_audit_sha256)
        validate_sha256(self.plan_sha256)
        finite((self.assumed_air_o2_um, self.assumed_ko_um, self.temperature_k,
                self.numerical_relative_tolerance), positive=True)
        if (type(self.rounds_per_case) is not int or not 1 <= self.rounds_per_case <= 16
            or type(self.maximum_native_calls) is not int
            or self.maximum_native_calls != len(self.cases) * self.rounds_per_case
            or self.maximum_native_calls > 256):
            raise ValueError("assay calls must equal the bounded complete case/round census")
        if (not isinstance(self.initial_fixed_queries, tuple)
            or not 1 <= len(self.initial_fixed_queries) <= self.rounds_per_case
            or any(not isinstance(q, AssayQuery) or q.duration_s != 1
                   or q.co2_um <= 0 or q.o2_um <= 0 for q in self.initial_fixed_queries)
            or any(case.initial_query != self.initial_fixed_queries[0] for case in self.cases)):
            raise ValueError("assay fixed probes must be positive paired gases in one-second queries")
        if any(case.ko != self.assumed_ko_um for case in self.cases):
            raise ValueError("supplied case KO differs from the explicitly assumed KO")
        if (self.feedback_policy != FEEDBACK_POLICY or self.temperature_k != Decimal("298.15")
            or self.numerical_relative_tolerance != Decimal("1e-10")
            or self.molecular_prediction_claimed is not False
            or any(value is not True for value in (self.activated_enzyme, self.saturating_rubp,
                   self.clamped_gases, self.stationary_repreparation_per_query))
            or self.evidence_role != EVIDENCE_ROLE):
            raise ValueError("assay changes its conditional preparation or evidence ceiling")

    def tasks(self) -> tuple[tuple[str, AssayCase, int], ...]:
        return tuple((f"{case.case_id}.round-{i:02d}", case, i)
                     for case in self.cases for i in range(self.rounds_per_case))


@dataclass(frozen=True, slots=True)
class AssayResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/rubisco-assay/result"
    result_id: str
    config: ObjectIdentity
    case: ObjectIdentity
    round_index: int
    prior_commitment: ObjectIdentity
    requested_query: AssayQuery
    accepted_query: AssayQuery
    applied_query: AssayQuery
    realized_query: AssayQuery
    pga_per_active_site: Decimal
    pgly_per_active_site: Decimal
    balance_residual: Decimal
    native_start_s: Decimal
    native_end_s: Decimal
    committed_next_query: AssayQuery | None
    committed_next_forecast: tuple[Decimal, Decimal] | None

    def __post_init__(self) -> None:
        validate_stable_id(self.result_id, field_name="result_id")
        _identity(self.config, AssayConfig.SCHEMA)
        _identity(self.case, AssayCase.SCHEMA)
        if type(self.round_index) is not int or not 0 <= self.round_index < 16:
            raise ValueError("assay round exceeds its bounded census")
        _identity(self.prior_commitment, AssayConfig.SCHEMA if self.round_index == 0 else self.SCHEMA)
        if not all(isinstance(q, AssayQuery) for q in (self.requested_query, self.accepted_query,
                                                      self.applied_query, self.realized_query)):
            raise ValueError("assay action must be a typed query")
        if not self.requested_query == self.accepted_query == self.applied_query == self.realized_query:
            raise ValueError("assay requires exact requested/accepted/applied/realized actions")
        if self.realized_query.duration_s != 1:
            raise ValueError("assay observation requires a declared one-second query")
        finite((self.pga_per_active_site, self.pgly_per_active_site, self.balance_residual,
                self.native_start_s, self.native_end_s))
        self.products()
        if self.native_start_s != self.round_index or self.native_end_s != self.round_index + 1:
            raise ValueError("assay clocks must retain their declared one-second preparation index")
        if (self.committed_next_query is None) != (self.committed_next_forecast is None):
            raise ValueError("assay continuation needs both query and paired forecast")
        if self.committed_next_query is not None:
            if not isinstance(self.committed_next_query, AssayQuery):
                raise ValueError("assay continuation query is untyped")
            finite(self.committed_next_forecast)
            if len(self.committed_next_forecast) != 2:
                raise ValueError("assay forecast omits one branch")
            if self.committed_next_query.duration_s != 1:
                raise ValueError("assay continuation requires a one-second query")

    def products(self) -> Products:
        return Products(float(self.pga_per_active_site), float(self.pgly_per_active_site),
                        float(self.realized_query.duration_s), float(self.balance_residual))


@dataclass(frozen=True, slots=True)
class AssayProjection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/rubisco-assay/projection"
    report_id: str
    config: ObjectIdentity
    case_id: str
    source_results: tuple[AssayResult, ...]
    branch_rates: tuple[tuple[Decimal, Decimal], ...]
    maximum_relative_forecast_error: Decimal
    maximum_balance_residual: Decimal
    specificity_estimates: tuple[Decimal, ...]
    log_sensitivity_rank: int
    smallest_singular_value: Decimal
    condition_number: Decimal | None
    maximum_absolute_log_specificity_reconstruction_error: Decimal
    ten_percent_specificity_energy_scale_kj_mol: Decimal

    def __post_init__(self) -> None:
        validate_stable_id(self.report_id, field_name="report_id")
        validate_stable_id(self.case_id, field_name="case_id")
        _identity(self.config, AssayConfig.SCHEMA)
        if (not isinstance(self.source_results, tuple) or not isinstance(self.branch_rates, tuple)
            or not 1 <= len(self.source_results) <= 16
            or any(not isinstance(r, AssayResult) for r in self.source_results)
            or len(self.branch_rates) != len(self.source_results)
            or len(self.specificity_estimates) != len(self.source_results)):
            raise ValueError("assay projection loses bounded source/rate/specificity census")
        for rates in self.branch_rates:
            finite(rates)
            if len(rates) != 2:
                raise ValueError("assay projection drops a branch rate")
        finite(self.specificity_estimates, positive=True)
        finite((self.maximum_relative_forecast_error, self.maximum_balance_residual,
                self.smallest_singular_value, self.maximum_absolute_log_specificity_reconstruction_error,
                self.ten_percent_specificity_energy_scale_kj_mol))
        if self.condition_number is not None:
            finite((self.condition_number,), positive=True)
        if type(self.log_sensitivity_rank) is not int or not 0 <= self.log_sensitivity_rank <= 4:
            raise ValueError("assay local sensitivity rank exceeds four supplied parameters")


@dataclass(frozen=True, slots=True)
class AssayEvaluation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulators/rubisco-assay/evaluation"
    evaluation_id: str
    config: ObjectIdentity
    source_reports: tuple[ObjectIdentity, ...]
    scientific_status: ScientificStatus
    reason_codes: tuple[str, ...]
    independent_biological_units: int = 0
    biological_validation: str = "NOT_PERFORMED"
    evidence_role: str = EVIDENCE_ROLE

    def __post_init__(self) -> None:
        validate_stable_id(self.evaluation_id, field_name="evaluation_id")
        _identity(self.config, AssayConfig.SCHEMA)
        if not isinstance(self.source_reports, tuple) or not 1 <= len(self.source_reports) <= 16:
            raise ValueError("assay evaluation needs its bounded complete report roster")
        for report in self.source_reports:
            _identity(report, AssayProjection.SCHEMA)
        require_sorted_unique_strings(tuple(r.object_id for r in self.source_reports), field_name="source_report_ids")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes", allow_empty=False)
        if self.scientific_status not in (ScientificStatus.SUPPORTED, ScientificStatus.NOT_SUPPORTED):
            raise ValueError("assay evaluation has an unsupported scientific state")
        if (type(self.independent_biological_units) is not int or self.independent_biological_units != 0
            or self.biological_validation != "NOT_PERFORMED" or self.evidence_role != EVIDENCE_ROLE):
            raise ValueError("conditional numerical evaluation cannot promote biological evidence")
