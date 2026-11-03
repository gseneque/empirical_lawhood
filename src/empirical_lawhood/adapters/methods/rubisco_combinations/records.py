# SPDX-License-Identifier: MPL-2.0
"""Closed, exposed Wilson quartet roles and continuous point diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import ClassVar

from empirical_lawhood.adapters.physical.rubisco_kinetics.genbank import NativeTeParentConstructV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.records import ReportedEndpointsV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import (
    TeProteinSpecificationV1, WilsonMutantPanelV1, WilsonMutantRowV1, WilsonReportedEndpointV1,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id

PREFIX = "rubisco-wilson2017.combinations.v1"
PROTOCOL_SHA256 = "2c27de0e3b6d88bf3e18f4e69aec9c76abf7be04c0a0e3194a922aaadfb03bd9"
SOURCE_PANEL_FINGERPRINT = "097f682b0df3f1f34754df28aafaa55278650e329b6b9021a45b605feaea9db2"
PARENT_FINGERPRINT = "72cb283eca1859d289e34163df77651d644bf33936832d1896a55172243f4b8b"
SOURCE_ARTICLE_SHA256 = "102a96a551bf11104b7ca7563572010adf8dc540a937165c671f23c618a24316"
DEPOSITED_PARENT_SHA256 = "62f8c50c51ba007b4d6b99273b9c397ceea85d97985449f6c0bcef376e51b305"
PANEL_ID = "rubisco-wilson2017-mutant-panel"
PARENT_ID = "rubisco-te-mg000148-parent"
SCOPE = "POSTHOC_EXPOSED_ZERO_LOG_INTERACTION_POINT_DIAGNOSTIC_ONLY"
NUMERICAL_CONTEXT = Context(prec=50)

SOURCE_ROSTER = (
    (4, "Se-LS(WT)"), (5, "Se-F345I"), (6, "Se-F140I"), (7, "Se-V186I"),
    (8, "Te-LS (WT)"), (11, "Te-F345I"), (12, "Te-P415A"), (13, "Te-V300A"),
    (14, "Te-FIPA"), (17, "Te-2Ga (1)"), (18, "Te-2Gb (2)"), (19, "Te-2Gc (3)"),
    (20, "Te-2Gd (5)"), (21, "Te-2Ge (8)"), (22, "Te-2Gf (10)"), (23, "Te-2Gg (11)"),
    (24, "Te-2Gh (12)"), (25, "Te-2Gi (13)"), (26, "Te-2Gj (15)"),
)
# Identities of actual native source rows, not a copied kinetic lookup table.
# Training/label operands carry those rows; the source decoder supplies them.
SOURCE_MEMBER_FINGERPRINTS = {
    4: "e94a6b4094d3c86b77150df0d261654999cf76a5d90a82102720e7c67714baa2",
    5: "6eb27bff8ca4de7aaa1947d2b5600635b2615435158600df0035293c3f119c0c",
    6: "d14f09bc25cfefca874a320c166985ac8deefa9e0ead6d1d3eae083db304455e",
    7: "c87b94b1556a020bf142924fb9533b2cb379802bd6c70954f8964c4173b8aafa",
    8: "966a6cb39c4ae05e631756fd15349594713e471c0da3cdcf4f07f10bfce7fed0",
    11: "83b1bc24c69838d9a2473dfe2b79c2552277bb48e3ecd9a414a2e2af5e1d3080",
    12: "74f0b585dfb08d1c50b62fdda2e39f3e2d9b953d0b4ed3097782cbce62a1ac07",
    13: "f699eb53bf3c64c8175c8aa4bca62ea97856c37d9edf5a599a8b90ac63928618",
    14: "ccde8ac1e51b38b7e2ab1a3023a9b0c25c99661048cb9445e8ec2d982210a4b7",
    17: "fe7cf463804290b574025e088729107a64cd87ef91724cf51c8e82562d72f86b",
    18: "9b7647a43fd31d5ff8779e2963a17a693b4ef3068fd5fa55fc116456583f9b27",
    19: "c9dfb8ea199b166ad66c4e39ec8a3fe6467506f07725064881208e672cb9d080",
    20: "c93b313cb9676019be3c2b0d5758aa6e7149a6e7dc87617380d0b2e281835d74",
    21: "52ca766d45e48715310536e8b258fff1b8f75ccd96be2faf2febbb7884084de3",
    22: "376a07182de6baeca9c30fa6e57b7dd9a4b4fd699ead5d2ec9aeef85270d6002",
    23: "12880975892e9e6d47d69a0ac9e03ebf27ffcc652b0393485e2533ef9332ad05",
    24: "583e644ec8e3ea67ef0fc50abb889872467a943c0dd36843dbd28c16fe162da3",
    25: "135465b1213c12215e6fccd3ac6f2d7633bd381118903cba0883558efefa5150",
    26: "3efcad5daaedc5b68a3c51e0b17969c020ea4c012a549fa6630dced1b09fa34d",
}
CORNER_SPECS = {
    "LSU": (26, "Te-2Gj (15)", frozenset(("A398T", "P415A")), frozenset()),
    "PARENT": (12, "Te-P415A", frozenset(("P415A",)), frozenset()),
    "SSU": (18, "Te-2Gb (2)", frozenset(("P415A",)), frozenset(("A48V",))),
    "TARGET": (22, "Te-2Gf (10)", frozenset(("A398T", "P415A")), frozenset(("A48V",))),
}
CORNER_NATIVE_EDITS = {
    "LSU": ("A398T, P415A", "None"), "PARENT": ("P415A", "None"),
    "SSU": ("P415A", "A48V"), "TARGET": ("A398T, P415A", "A48V"),
}
TRAINING_IDS = ("wilson2017-row12", "wilson2017-row18", "wilson2017-row26")
TARGET_ID = "wilson2017-row22"


def panel_identity() -> ObjectIdentity:
    return ObjectIdentity(PANEL_ID, WilsonMutantPanelV1.SCHEMA, "1.0.0", SOURCE_PANEL_FINGERPRINT)


def parent_identity() -> ObjectIdentity:
    return ObjectIdentity(PARENT_ID, NativeTeParentConstructV1.SCHEMA, "1.0.0", PARENT_FINGERPRINT)


def _science_identity(value: ObjectIdentity) -> None:
    if (type(value) is not ObjectIdentity or value.object_id != PREFIX + ".science"
        or value.object_schema != CombinationScienceV1.SCHEMA or value.object_version != "1.0.0"):
        raise ValueError("combination role changes its frozen scientific identity")


def _source_identity(value: ObjectIdentity) -> None:
    if value != panel_identity():
        raise ValueError("combination role changes the exact full nineteen-row source panel")


def _id(value: str, suffix: str) -> None:
    validate_stable_id(value)
    if value != PREFIX + "." + suffix:
        raise ValueError("combination record changes its frozen role identity")


def _scalars(values: tuple[Decimal, ...], *, nonnegative: bool = False) -> None:
    if type(values) is not tuple:
        raise ValueError("combination scalar collections must be immutable")
    for value in values:
        validate_decimal(value, field_name="combination_scalar", minimum=Decimal(0) if nonnegative else None)


@dataclass(frozen=True, slots=True)
class CombinationSourceDispositionV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/source-disposition"
    source_member: ObjectIdentity
    native_ordinal_0based: int
    native_name: str
    disposition: str

    def __post_init__(self) -> None:
        expected = dict(SOURCE_ROSTER).get(self.native_ordinal_0based)
        if (type(self.native_ordinal_0based) is not int or expected != self.native_name
            or type(self.source_member) is not ObjectIdentity
            or self.source_member.object_id != f"wilson2017-row{self.native_ordinal_0based}"
            or self.source_member.object_schema != WilsonMutantRowV1.SCHEMA
            or self.source_member.object_version != "1.0.0"
            or self.source_member.object_fingerprint != SOURCE_MEMBER_FINGERPRINTS.get(self.native_ordinal_0based)):
            raise ValueError("combination source disposition changes its exact native member")
        selected = next((role for role, spec in CORNER_SPECS.items() if spec[0] == self.native_ordinal_0based), None)
        if self.disposition != (f"SELECTED_{selected}" if selected else "SOURCE_CONTEXT_ONLY"):
            raise ValueError("combination selection changes its explicit source disposition")


@dataclass(frozen=True, slots=True)
class CombinationCornerV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/corner-features"
    role: str
    source_member: ObjectIdentity
    native_name: str
    protein_recipe: TeProteinSpecificationV1

    def __post_init__(self) -> None:
        spec = CORNER_SPECS.get(self.role)
        if spec is None or type(self.protein_recipe) is not TeProteinSpecificationV1:
            raise ValueError("combination corner requires its exact paired-subunit recipe")
        ordinal, name, lsu, ssu = spec
        recipe = self.protein_recipe
        if (self.native_name != name or type(self.source_member) is not ObjectIdentity
            or self.source_member.object_id != f"wilson2017-row{ordinal}"
            or self.source_member.object_schema != WilsonMutantRowV1.SCHEMA
            or self.source_member.object_version != "1.0.0"
            or self.source_member.object_fingerprint != SOURCE_MEMBER_FINGERPRINTS.get(ordinal)
            or ObjectIdentity.from_record(PARENT_ID, recipe.parent) != parent_identity()
            or recipe.parent.source_sha256 != DEPOSITED_PARENT_SHA256
            or (recipe.native_rbcl_edits, recipe.native_rbcs_edits) != CORNER_NATIVE_EDITS[self.role]
            or frozenset(edit.substitution for edit in recipe.large_subunit_edits) != lsu
            or frozenset(edit.substitution for edit in recipe.small_subunit_edits) != ssu):
            raise ValueError("combination corner changes source parent, LSU/SSU edit namespaces or exact recipe")


@dataclass(frozen=True, slots=True)
class CombinationScienceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/science"
    science_id: str
    source_panel: ObjectIdentity
    parent: ObjectIdentity
    protocol_sha256: str
    source_roster: tuple[CombinationSourceDispositionV1, ...]
    corners: tuple[CombinationCornerV1, ...]
    claim_scope: str = SCOPE

    def __post_init__(self) -> None:
        _id(self.science_id, "science")
        _source_identity(self.source_panel)
        validate_sha256(self.protocol_sha256)
        if self.parent != parent_identity() or self.protocol_sha256 != PROTOCOL_SHA256:
            raise ValueError("combination science substitutes its exact deposited parent or protocol")
        if (type(self.source_roster) is not tuple or len(self.source_roster) != 19
            or any(type(member) is not CombinationSourceDispositionV1 for member in self.source_roster)
            or tuple((member.native_ordinal_0based, member.native_name) for member in self.source_roster) != SOURCE_ROSTER):
            raise ValueError("combination science loses its complete nineteen-row source denominator")
        if (type(self.corners) is not tuple or any(type(value) is not CombinationCornerV1 for value in self.corners)
            or tuple(corner.role for corner in self.corners) != tuple(CORNER_SPECS)):
            raise ValueError("combination science changes its complete selected quartet")
        roster = {member.source_member.object_id: member.source_member for member in self.source_roster}
        if any(roster.get(corner.source_member.object_id) != corner.source_member for corner in self.corners):
            raise ValueError("combination selected recipe detaches its exact retained source member")
        if self.claim_scope != SCOPE:
            raise ValueError("combination diagnostic cannot promote its exposed source or model scope")


@dataclass(frozen=True, slots=True)
class CombinationObservationV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/observation"
    sample_id: str
    turnover: WilsonReportedEndpointV1
    specificity: WilsonReportedEndpointV1
    native_row: WilsonMutantRowV1

    def __post_init__(self) -> None:
        if self.sample_id not in (*TRAINING_IDS, TARGET_ID):
            raise ValueError("combination observation is outside its exact quartet")
        if (type(self.turnover) is not WilsonReportedEndpointV1 or type(self.specificity) is not WilsonReportedEndpointV1
            or self.turnover.kind != "KCAT_C" or self.specificity.kind != "SPECIFICITY_CO"
            or self.turnover.mean is None or self.specificity.mean is None):
            raise ValueError("combination observation needs both direct native intrinsic endpoints")
        if (type(self.native_row) is not WilsonMutantRowV1 or self.native_row.sample_id != self.sample_id
            or self.native_row.fingerprint() != SOURCE_MEMBER_FINGERPRINTS.get(self.native_row.native_table_row.ordinal_0based)
            or self.turnover != self.native_row.endpoint("KCAT_C")
            or self.specificity != self.native_row.endpoint("SPECIFICITY_CO")):
            raise ValueError("combination observation changes its exact native source-row projection")

    def point(self) -> ReportedEndpointsV1:
        return ReportedEndpointsV1(self.sample_id, self.turnover.mean, self.specificity.mean)


@dataclass(frozen=True, slots=True)
class CombinationTrainingV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/training"
    training_id: str
    science: ObjectIdentity
    source_panel: ObjectIdentity
    observations: tuple[CombinationObservationV1, ...]

    def __post_init__(self) -> None:
        _id(self.training_id, "training")
        _science_identity(self.science)
        _source_identity(self.source_panel)
        if (type(self.observations) is not tuple or any(type(value) is not CombinationObservationV1 for value in self.observations)
            or tuple(value.sample_id for value in self.observations) != TRAINING_IDS):
            raise ValueError("combination training requires precisely its three corners, never target labels")


@dataclass(frozen=True, slots=True)
class CombinationFeaturesV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/features"
    features_id: str
    science: ObjectIdentity
    source_panel: ObjectIdentity
    target: CombinationCornerV1

    def __post_init__(self) -> None:
        _id(self.features_id, "features")
        _science_identity(self.science)
        _source_identity(self.source_panel)
        if type(self.target) is not CombinationCornerV1 or self.target.role != "TARGET":
            raise ValueError("combination target features require the exact combined LSU/SSU recipe")


@dataclass(frozen=True, slots=True)
class CombinationLabelsV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/labels"
    labels_id: str
    science: ObjectIdentity
    source_panel: ObjectIdentity
    target: CombinationObservationV1

    def __post_init__(self) -> None:
        _id(self.labels_id, "labels")
        _science_identity(self.science)
        _source_identity(self.source_panel)
        if type(self.target) is not CombinationObservationV1 or self.target.sample_id != TARGET_ID:
            raise ValueError("combination labels require precisely the combined target observation")


def predicted_points(training: CombinationTrainingV1) -> tuple[ReportedEndpointsV1, ReportedEndpointsV1]:
    points = {value.sample_id: value.point() for value in training.observations}
    parent, lsu, ssu = (points[sample] for sample in ("wilson2017-row12", "wilson2017-row26", "wilson2017-row18"))
    with localcontext(NUMERICAL_CONTEXT):
        additive = ReportedEndpointsV1(TARGET_ID, lsu.turnover_s_inv * ssu.turnover_s_inv / parent.turnover_s_inv,
                                      lsu.specificity_dimensionless * ssu.specificity_dimensionless / parent.specificity_dimensionless)
    baseline = ReportedEndpointsV1(TARGET_ID, parent.turnover_s_inv, parent.specificity_dimensionless)
    return additive, baseline


@dataclass(frozen=True, slots=True)
class CombinationForecastV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/forecast"
    forecast_id: str
    science: ObjectIdentity
    training: CombinationTrainingV1
    features: CombinationFeaturesV1
    additive_point: ReportedEndpointsV1
    parent_point: ReportedEndpointsV1
    prediction_scope: str = SCOPE

    def __post_init__(self) -> None:
        _id(self.forecast_id, "forecast")
        _science_identity(self.science)
        if (type(self.training) is not CombinationTrainingV1 or type(self.features) is not CombinationFeaturesV1
            or self.training.science != self.science or self.features.science != self.science
            or self.training.source_panel != self.features.source_panel
            or (self.additive_point, self.parent_point) != predicted_points(self.training)
            or self.prediction_scope != SCOPE):
            raise ValueError("combination forecast changes its fixed three-corner calculation or source roles")


@dataclass(frozen=True, slots=True)
class CombinationCommitmentV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/commitment"
    commitment_id: str
    science: ObjectIdentity
    forecast: ObjectIdentity
    forecast_product: CombinationForecastV1
    barrier_scope: str = "BOTH_ENDPOINT_FORECASTS_AND_PARENT_BASELINE_BEFORE_EVALUATION_LABEL_READ"

    def __post_init__(self) -> None:
        _id(self.commitment_id, "commitment")
        _science_identity(self.science)
        if (type(self.forecast_product) is not CombinationForecastV1 or self.forecast_product.science != self.science
            or self.forecast != ObjectIdentity.from_record(self.forecast_product.forecast_id, self.forecast_product)
            or self.barrier_scope != "BOTH_ENDPOINT_FORECASTS_AND_PARENT_BASELINE_BEFORE_EVALUATION_LABEL_READ"):
            raise ValueError("combination commitment changes its complete frozen forecast")


def point_errors(point: ReportedEndpointsV1, observed: ReportedEndpointsV1):
    with localcontext(NUMERICAL_CONTEXT):
        pairs = ((point.turnover_s_inv, observed.turnover_s_inv),
                 (point.specificity_dimensionless, observed.specificity_dimensionless))
        return (tuple(abs(p - y) for p, y in pairs), tuple(abs(p - y) / y for p, y in pairs),
                tuple(abs((p / y).ln()) for p, y in pairs))


def parent_log_contrasts(point: ReportedEndpointsV1, parent: ReportedEndpointsV1):
    with localcontext(NUMERICAL_CONTEXT):
        return ((point.turnover_s_inv / parent.turnover_s_inv).ln(),
                (point.specificity_dimensionless / parent.specificity_dimensionless).ln())


def improves_both(point: ReportedEndpointsV1, parent: ReportedEndpointsV1) -> bool:
    return point.turnover_s_inv > parent.turnover_s_inv and point.specificity_dimensionless > parent.specificity_dimensionless


@dataclass(frozen=True, slots=True)
class CombinationPointErrorV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/point-error"
    method: str
    point: ReportedEndpointsV1
    observed: ReportedEndpointsV1
    absolute_errors: tuple[Decimal, Decimal]
    relative_errors: tuple[Decimal, Decimal]
    absolute_log_errors: tuple[Decimal, Decimal]

    def __post_init__(self) -> None:
        if (self.method not in {"CONVENTIONAL_ZERO_LOG_INTERACTION", "PARENT_NO_CHANGE"}
            or type(self.point) is not ReportedEndpointsV1 or type(self.observed) is not ReportedEndpointsV1
            or self.point.sample_id != TARGET_ID or self.observed.sample_id != TARGET_ID):
            raise ValueError("combination diagnostic substitutes a method, endpoint or target")
        for collection in (self.absolute_errors, self.relative_errors, self.absolute_log_errors):
            _scalars(collection, nonnegative=True)
        if (self.absolute_errors, self.relative_errors, self.absolute_log_errors) != point_errors(self.point, self.observed):
            raise ValueError("combination error differs from its exact continuous point operands")


@dataclass(frozen=True, slots=True)
class CombinationEvaluationV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/evaluation"
    evaluation_id: str
    science: ObjectIdentity
    commitment: ObjectIdentity
    forecast_product: CombinationForecastV1
    labels: CombinationLabelsV1
    errors: tuple[CombinationPointErrorV1, ...]
    predicted_parent_log_contrasts: tuple[Decimal, Decimal]
    observed_parent_log_contrasts: tuple[Decimal, Decimal]
    log_interaction_residual: tuple[Decimal, Decimal]
    predicted_joint_point_improvement: bool
    observed_joint_point_improvement: bool
    source_panel_contrasts: int = 1
    independent_biological_units: int | None = None
    calibrated_joint_coverage: Decimal | None = None
    candidate_nomination_established: bool = False
    el_advantage_established: bool = False
    claim_scope: str = SCOPE

    def __post_init__(self) -> None:
        _id(self.evaluation_id, "evaluation")
        _science_identity(self.science)
        if (type(self.forecast_product) is not CombinationForecastV1 or type(self.labels) is not CombinationLabelsV1
            or self.forecast_product.science != self.science or self.labels.science != self.science):
            raise ValueError("combination evaluation changes its source-bound forecast/label joins")
        committed = CombinationCommitmentV1(PREFIX + ".commitment", self.science,
            ObjectIdentity.from_record(self.forecast_product.forecast_id, self.forecast_product), self.forecast_product)
        if self.commitment != ObjectIdentity.from_record(committed.commitment_id, committed):
            raise ValueError("combination evaluation detaches its exact prior commitment")
        observed, forecast, parent = self.labels.target.point(), self.forecast_product.additive_point, self.forecast_product.parent_point
        if (type(self.errors) is not tuple or tuple(error.method for error in self.errors)
            != ("CONVENTIONAL_ZERO_LOG_INTERACTION", "PARENT_NO_CHANGE")
            or any(type(error) is not CombinationPointErrorV1 or error.observed != observed for error in self.errors)
            or tuple(error.point for error in self.errors) != (forecast, parent)):
            raise ValueError("combination assessment drops its complete two-method point census")
        for collection in (self.predicted_parent_log_contrasts, self.observed_parent_log_contrasts, self.log_interaction_residual):
            _scalars(collection)
        if (self.predicted_parent_log_contrasts != parent_log_contrasts(forecast, parent)
            or self.observed_parent_log_contrasts != parent_log_contrasts(observed, parent)
            or self.log_interaction_residual != parent_log_contrasts(observed, forecast)
            or self.predicted_joint_point_improvement is not improves_both(forecast, parent)
            or self.observed_joint_point_improvement is not improves_both(observed, parent)):
            raise ValueError("combination direction or interaction residual differs from exact point means")
        if (type(self.source_panel_contrasts) is not int or self.source_panel_contrasts != 1
            or self.independent_biological_units is not None or self.calibrated_joint_coverage is not None
            or self.candidate_nomination_established is not False or self.el_advantage_established is not False
            or self.claim_scope != SCOPE):
            raise ValueError("combination diagnostic cannot invent calibration, biological n, nomination or EL advantage")
