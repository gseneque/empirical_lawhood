# SPDX-License-Identifier: MPL-2.0
"""Typed exact mechanism selection and assessed source-conditional findings."""

from dataclasses import dataclass, fields
from fractions import Fraction
from hashlib import sha256
from typing import ClassVar
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition as A,
    ScientificConditionScope,
)
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .source_manifest import SOURCE_MANIFEST

NAMESPACE = "rubisco-insilico-mechanism"
UNIT = NAMESPACE + ".exposed-conditional-mechanism"
QUESTION = "Do authentic Rubisco chemistry and source uncertainty support the nominated release/commitment explanation, and which microscopic quantities remain unidentifiable?"
CASE_IDS = (
    "donor-nominal-compatibility",
    "gp-mutation-no-release-effect",
    "gp-donor-speed-headroom-insufficient",
    "gp-oxygen-recapture-larger-specificity-loss",
    "gp-sufficient-unmeasured-headroom",
)
TOPOLOGIES = (
    "coarse-reversible-formation",
    "irreversible-postprocessing",
    "explicit-pregas-enolization",
    "thermodynamic-coupling",
)
UNKNOWN_REASONS = (
    "I95M_ENDPOINTS_UNMEASURED",
    "GP_MICROSCOPIC_RATES_UNIDENTIFIED",
    "GP_SOURCE_UNCERTAINTY_UNQUANTIFIED",
    "DONOR_TARGET_TRANSPORT_UNASSESSED",
    "ATOMISTIC_PROCESSED_STATE_UNIDENTIFIED",
    "BRANCH_FREE_ENERGY_AND_CHEMICAL_POTENTIALS_UNKNOWN",
)
PREREQUISITES = (
    "activated-carbamylated-lysine-and-magnesium",
    "rubp-enediolate-and-both-gas-intermediates",
    "hydration-scission-protonation-versus-product-release-state-map",
    "matched-reactant-transition-product-ensembles-and-rate-bearing-coordinate",
    "branch-specific-forward-and-reverse-free-energies-with-standard-states",
    "independent-kinetic-observations-and-matched-active-site-assays",
)


def identity(record):
    key = next(
        k
        for k in ("input_id", "selection_id", "config_id", "product_id")
        if hasattr(record, k)
    )
    return ObjectIdentity.from_record(getattr(record, key), record)


@dataclass(frozen=True, slots=True)
class Exact(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-mechanism/exact-rational"
    )
    numerator: int
    denominator: int

    def __post_init__(self):
        if (
            type(self.numerator) is not int
            or type(self.denominator) is not int
            or self.denominator <= 0
        ):
            raise ValueError(
                "exact rational needs integer numerator and positive denominator"
            )
        q = Fraction(self.numerator, self.denominator)
        if (q.numerator, q.denominator) != (self.numerator, self.denominator):
            raise ValueError(
                "exact rational must retain normalized numerator/denominator"
            )

    @classmethod
    def of(cls, value):
        q = Fraction(value)
        return cls(q.numerator, q.denominator)

    @property
    def fraction(self):
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True, slots=True)
class PrimarySource(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-mechanism/primary-source"
    )
    filename: str
    doi: str
    raw_utf8: str

    def __post_init__(self):
        expected = tuple(row for row in SOURCE_MANIFEST if row[0] == self.filename)
        raw = self.raw_utf8.encode()
        if (
            len(expected) != 1
            or (self.filename, self.doi, len(raw), sha256(raw).hexdigest())
            != expected[0]
        ):
            raise ValueError(
                "selected primary chemistry source original bytes/identity differ"
            )


@dataclass(frozen=True, slots=True)
class MechanismSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-mechanism/selection"
    selection_id: str
    candidate_id: str = "gp.i95m"
    case_ids: tuple[str, ...] = CASE_IDS
    topologies: tuple[str, ...] = TOPOLOGIES
    reference_views: tuple[str, ...] = ("coupled", "radiometric")
    gas_probes: tuple[Exact, ...] = (Exact(1, 100), Exact(1, 1), Exact(100, 1))
    uncertainty_rule: str = (
        "SOURCE_STANDARD_ERRORS_AND_ALL_CORRELATIONS_NOT_CONFIDENCE_INTERVALS"
    )
    partition_bound_scope: str = (
        "PUBLISHED_OTHER_ENZYMES_CONDITIONAL_NOT_GP_MEASUREMENT"
    )
    primary_forward_partition: Exact = Exact(93, 100)
    commentary_forward_partition: Exact = Exact(19, 20)
    mathematical_rates_are_estimates: bool = False
    physical_units: int = 0
    biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        if any(
            getattr(self, row.name) != row.default
            for row in fields(self)
            if row.name != "selection_id"
        ):
            raise ValueError(
                "selected mechanism changes complete source/scenario/uncertainty contract"
            )


@dataclass(frozen=True, slots=True)
class MechanismSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-mechanism/source"
    input_id: str
    nomination: ObjectIdentity
    macro_source: ObjectIdentity
    selection: MechanismSelection
    primary_sources: tuple[PrimarySource, ...]

    def __post_init__(self):
        validate_stable_id(self.input_id)
        self.selection.__post_init__()
        if tuple(row.filename for row in self.primary_sources) != tuple(
            row[0] for row in SOURCE_MANIFEST
        ):
            raise ValueError(
                "mechanism source omits or changes complete primary-source census"
            )
        for row in self.primary_sources:
            row.__post_init__()


def scope(source):
    return ScientificConditionScope(
        "system.rubisco-nomination.gp-i95m",
        "world.rubisco-nomination.exploratory-preparation",
        source.input_id,
        ("mechanistic-constraints", "specificity", "turnover"),
        ("dimensionless", "dimensionless", "s^-1"),
        "receiver.source-conditional-mechanistic-challenge",
        "clock.exposed-mechanism-analysis",
        "Pure source-conditional chemistry/identifiability challenge; all candidate biology and atomistic rate mapping UNEVALUABLE.",
        source_config_sha256=source.fingerprint(),
        instance_id="gp.i95m",
    )


@dataclass(frozen=True, slots=True)
class CaseFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-mechanism/case-finding"
    case_id: str
    values: tuple[tuple[str, Exact], ...]
    original_matrix_checks: int
    irreversible_matrix_checks: int
    expanded_matrix_checks: int
    original_balances_pass: bool
    irreversible_specificity_invariant: bool
    expanded_specificity_shared_pregas_invariant: bool
    source_conditional_partition_compatible: bool
    carbon_state_equilibrium_favours_putative_product: bool
    microscopic_parameter_count: int = 10
    observed_endpoint_jacobian_rank: int = 2
    unidentifiable_dimensions_at_least: int = 8
    biological_disposition: A = A.UNEVALUABLE

    def __post_init__(self):
        if (
            self.case_id not in CASE_IDS
            or tuple(k for k, _ in self.values)
            != tuple(sorted(set(k for k, _ in self.values)))
            or (
                self.original_matrix_checks,
                self.irreversible_matrix_checks,
                self.expanded_matrix_checks,
            )
            != (14, 2, 4)
            or (
                self.microscopic_parameter_count,
                self.observed_endpoint_jacobian_rank,
                self.unidentifiable_dimensions_at_least,
            )
            != (10, 2, 8)
            or self.biological_disposition is not A.UNEVALUABLE
        ):
            raise ValueError(
                "case drops exact check denominator or fabricates microscopic/biological identifiability"
            )


@dataclass(frozen=True, slots=True)
class TargetCondition(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-mechanism/target-condition"
    )
    reference_view: str
    required_nominal_turnover_multiplier: Exact
    minimum_removable_waiting_fraction: Exact
    conditional_minimum_lambda_given_prior_v: Exact
    required_nominal_specificity_multiplier: Exact
    robust_joint_target_status: str = (
        "UNEVALUABLE_UNQUANTIFIED_GP_AND_MATCHED_REFERENCE_UNCERTAINTY"
    )

    def __post_init__(self):
        if (
            self.reference_view not in ("coupled", "radiometric")
            or self.robust_joint_target_status
            != "UNEVALUABLE_UNQUANTIFIED_GP_AND_MATCHED_REFERENCE_UNCERTAINTY"
        ):
            raise ValueError(
                "target calculation promotes nominal unmatched source anchors"
            )


@dataclass(frozen=True, slots=True)
class DonorUncertainty(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-mechanism/donor-uncertainty"
    )
    endpoint: str
    before_mean: Exact
    after_mean: Exact
    before_se: Exact
    after_se: Exact
    mean_ratio: Exact
    one_se_box_ratio: tuple[Exact, Exact]
    delta_log_ratio_variance_bounds: tuple[Exact, Exact]
    before_native_error_token: str
    after_native_error_token: str
    scope: str = "PUBLISHED_SE_PAIRED_COVARIANCE_AND_CROSS_ENDPOINT_COVARIANCE_UNKNOWN_NO_CI_OR_SIGNIFICANCE"

    def __post_init__(self):
        if (
            self.endpoint not in ("specificity", "turnover")
            or self.scope
            != "PUBLISHED_SE_PAIRED_COVARIANCE_AND_CROSS_ENDPOINT_COVARIANCE_UNKNOWN_NO_CI_OR_SIGNIFICANCE"
        ):
            raise ValueError(
                "donor uncertainty invents covariance/probability or changes paired endpoint"
            )


@dataclass(frozen=True, slots=True)
class MechanismAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-mechanism/assessment"
    product_id: str
    source: MechanismSource
    prior_nomination_scope: ScientificConditionScope
    cases: tuple[CaseFinding, ...]
    targets: tuple[TargetCondition, ...]
    donor_uncertainty: tuple[DonorUncertainty, ...]
    source_partition_specificity_gain_upper_bound: Exact
    commentary_partition_specificity_gain_upper_bound: Exact
    donor_minimum_removable_waiting_fraction: Exact
    check4_prerequisites: tuple[str, ...] = PREREQUISITES
    unknown_reasons: tuple[str, ...] = UNKNOWN_REASONS
    disposition: A = A.SATISFIED
    biological_disposition: A = A.UNEVALUABLE
    independent_physical_units: int = 0
    independent_biological_units: int = 0

    @property
    def scope(self):
        return scope(self.source)

    def __post_init__(self):
        validate_stable_id(self.product_id)
        self.source.__post_init__()
        if (
            tuple(r.case_id for r in self.cases) != CASE_IDS
            or tuple(r.reference_view for r in self.targets)
            != ("coupled", "radiometric")
            or tuple(r.endpoint for r in self.donor_uncertainty)
            != ("specificity", "turnover")
            or self.check4_prerequisites != PREREQUISITES
            or self.unknown_reasons != UNKNOWN_REASONS
            or self.disposition is not A.SATISFIED
            or self.biological_disposition is not A.UNEVALUABLE
            or self.independent_physical_units != 0
            or self.independent_biological_units != 0
        ):
            raise ValueError(
                "mechanism assessment drops source/scenario/unknown denominator or promotes biology"
            )
        for row in (*self.cases, *self.targets, *self.donor_uncertainty):
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class MechanismOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-insilico-mechanism/operation-config"
    )
    config_id: str
    source: MechanismSource
    nomination_scope: ScientificConditionScope
    operands: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        if (
            self.config_id != "config." + NAMESPACE + ".challenge"
            or self.operands
            != tuple(
                sorted(
                    (
                        identity(self.source),
                        self.source.nomination,
                        self.source.macro_source,
                    ),
                    key=lambda r: r.object_id,
                )
            )
        ):
            raise ValueError(
                "mechanism config changes selected source or original outcome identity"
            )
