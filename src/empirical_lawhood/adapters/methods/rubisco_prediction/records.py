# SPDX-License-Identifier: MPL-2.0
"""Closed source roles and finite exposed natural-sequence KNN diagnostics.

Native member fingerprints seal source projections without putting mutant
labels in predictor inputs. The source decoder owns native interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.physical.rubisco_kinetics.iqbal2023 import (
    IqbalNaturalRowV1, IqbalTrainingTableV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.mcdonald2026 import (
    Mcdonald2026PanelV1, PlantContextV1, PlantProteinRecipeV1,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_decimal, validate_stable_id

PREFIX = "rubisco-plant-prediction.v1"
PROTOCOL_SHA256 = "4651c2e8e84debecd4a23f2f493b674e139eef87d0d81e258b6acdc67cc34c11"
IQBAL_TABLE_FINGERPRINT = "28c34d5393aa4b627fc76c56ebbc979ec237fc8ddf3252a618a39f9c9fd41a21"
PLANT_PANEL_FINGERPRINT = "23e913faf1c50f6e4afbbbbe642521e4894e32c891eb1d913eac1107862a73d0"
PARENT_LSU_SHA256 = "c2848529f02b8a7af725d5af304b2292ba487328eb935acf437ab6b86c84b1f8"
PARENT_SSU_SHA256 = "1387c44309233c1b3b6c006da2ddf0800e8007ca6c87405da6a33feff3cb0370"
K_VALUES = (1, 3, 5, 9, 15, 31)
ENDPOINTS = ("KCAT_C", "SPECIFICITY_CO")
METHODS = ("parent", "1nn", "selected-knn")
FOCAL_EDITS = ("I251L", "T391C", "T391I", "T391V", "A438R", "I465V", "N468D", "N468Q", "A470R")
EDITS = (*FOCAL_EDITS, "A369V")
SITES = (251, 391, 438, 465, 468, 470)
SCOPE = "EXPOSED_FINITE_PLANT_MUTANT_POINT_ASSESSMENT_ONLY"
NUMERICAL_CONTEXT = Context(prec=50)
DISTANCE_BACKEND = "rapidfuzz-3.14.3-levenshtein-unit-costs-processor-none-no-cutoff"

# Exact native context identities keep target endpoint values out of queries.
PLANT_CONTEXT_FINGERPRINTS = {
    None: "7c290fe3dfe9befea7999fb9b01aa4617acb86c06625bb7b74be975693195377",
    "I251L": "382254132d60d769ec4774150465d10c0f2572c6c5522719ea9996909c54bb84",
    "T391C": "ef825834db6d8640699881544bff24298fbaff5cbca19171f404fce944915c9e",
    "T391I": "ad54a74ff4431cbe7a16043be284c5c56ef928bacc92bf78da3a2ec6af671733",
    "T391V": "8a66a29fd2e7878891368ef31abaa469e79c6d71c2601b082ba72bad97fd3bef",
    "A438R": "465f3ebbd96f09bc0fa72a2dcb70ec2abfd374740d252012d49731e4efa44830",
    "I465V": "03a5309eb20b4f8af3ff4ff66b306593366407f4f24f990239cb5a8938d377a8",
    "N468D": "87be8fac2eeccf2561ff3570386e892a3b49b3dc59fec907b891e18e77c7e568",
    "N468Q": "b09fc54f9669543a08ab4c913a261f96ee7058de4084f676763ae2852d6c8ce0",
    "A470R": "d27250b7e19b21d5c18b6b30627b32061de7832b16135cee470c39e5f6b0ddd1",
    "A369V": "1d87704a00c90996d1a46d1bf26b651cbdf4a316b9113d865a7edebcca75ad04",
}


def natural_identity() -> ObjectIdentity:
    return ObjectIdentity("rubisco-iqbal2023-training-table", IqbalTrainingTableV1.SCHEMA, "1.0.0", IQBAL_TABLE_FINGERPRINT)


def plant_identity() -> ObjectIdentity:
    return ObjectIdentity("rubisco-mcdonald2026-panel", Mcdonald2026PanelV1.SCHEMA, "1.0.0", PLANT_PANEL_FINGERPRINT)


def case_id(edit: str) -> str:
    if edit not in EDITS:
        raise ValueError("plant prediction changes its frozen mutant/diagnostic roster")
    return PREFIX + "." + edit.lower()


def context_identity(edit: str | None) -> ObjectIdentity:
    return ObjectIdentity("mcdonald2026-" + (edit.lower() if edit else "parent"),
                          PlantContextV1.SCHEMA, "1.0.0", PLANT_CONTEXT_FINGERPRINTS[edit])


def _id(value: str, suffix: str) -> None:
    validate_stable_id(value)
    if value != PREFIX + "." + suffix:
        raise ValueError("plant prediction changes its frozen role identity")


def _protocol(value: str) -> None:
    if value != PROTOCOL_SHA256:
        raise ValueError("plant prediction changes its frozen protocol")


def _tuple(values, item_type, *, minimum=1, maximum=100000) -> None:
    if (type(values) is not tuple or not minimum <= len(values) <= maximum
            or any(type(item) is not item_type for item in values)):
        raise ValueError("plant prediction needs a bounded immutable typed roster")


def _positive(value: Decimal) -> None:
    validate_decimal(value, field_name="positive_endpoint")
    if value <= 0:
        raise ValueError("plant prediction refuses absent/nonpositive kinetic outputs")


def mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("plant prediction refuses an empty mean")
    with localcontext(NUMERICAL_CONTEXT):
        return sum(values, Decimal(0)) / Decimal(len(values))


def _recipe(recipe: PlantProteinRecipeV1, edit: str | None) -> None:
    if (type(recipe) is not PlantProteinRecipeV1 or recipe.edit != edit
            or sha256(recipe.immediate_parent_lsu.encode("ascii")).hexdigest() != PARENT_LSU_SHA256
            or sha256(recipe.translated_ssu.encode("ascii")).hexdigest() != PARENT_SSU_SHA256):
        raise ValueError("plant prediction requires its exact A369 LSU/123-aa SSU recipe")
    recipe.__post_init__()


def _context(context: PlantContextV1, edit: str | None) -> None:
    if (type(context) is not PlantContextV1 or context.fingerprint() != PLANT_CONTEXT_FINGERPRINTS.get(edit)
            or context.name_cell.token != "NtRbcL" + (f" {edit}" if edit else "")):
        raise ValueError("plant prediction refuses a changed native endpoint/source projection")
    _recipe(context.protein_recipe, edit)
    for endpoint in ENDPOINTS:
        _positive(context.quantity(endpoint).mean)


@dataclass(frozen=True, slots=True)
class NaturalTrainingRowV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/natural-training-row"
    native: IqbalNaturalRowV1

    def __post_init__(self) -> None:
        if type(self.native) is not IqbalNaturalRowV1:
            raise ValueError("natural training needs a typed native source-row projection")
        self.native.__post_init__()
        for endpoint in ENDPOINTS:
            value = self.value(endpoint)
            if value is not None:
                _positive(value)

    @property
    def row_id(self) -> str:
        return f"iqbal2023-row{self.native.native_row}"

    @property
    def genus(self) -> str:
        return self.native.genus

    @property
    def sequence(self) -> str:
        return self.native.sequence

    def value(self, endpoint: str) -> Decimal | None:
        if endpoint not in ENDPOINTS:
            raise ValueError("natural training changes the two intrinsic endpoint roles")
        return self.native.turnover_s_inv if endpoint == "KCAT_C" else self.native.specificity_dimensionless


@dataclass(frozen=True, slots=True)
class NaturalTrainingV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/natural-training"
    training_id: str
    source_table: ObjectIdentity
    protocol_sha256: str
    rows: tuple[NaturalTrainingRowV1, ...]
    native_source: IqbalTrainingTableV1

    def __post_init__(self) -> None:
        _id(self.training_id, "training")
        _protocol(self.protocol_sha256)
        _tuple(self.rows, NaturalTrainingRowV1, minimum=183, maximum=183)
        if (type(self.native_source) is not IqbalTrainingTableV1
                or self.source_table != natural_identity()
                or ObjectIdentity.from_record(self.source_table.object_id, self.native_source) != natural_identity()
                or tuple(row.native.native_row for row in self.rows) != tuple(range(2, 185))):
            raise ValueError("natural training changes its exact source or complete 183-row census")
        self.native_source.__post_init__()
        if tuple(row.native for row in self.rows) != self.native_source.rows:
            raise ValueError("natural training changes its sealed native source-row projection")
        for row in self.rows:
            row.__post_init__()


@dataclass(frozen=True, slots=True)
class PlantQueryV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/query"
    source_context: ObjectIdentity
    recipe: PlantProteinRecipeV1

    def __post_init__(self) -> None:
        if type(self.recipe) is not PlantProteinRecipeV1 or self.recipe.edit not in EDITS:
            raise ValueError("plant query requires a frozen focal or diagnostic edit")
        _recipe(self.recipe, self.recipe.edit)
        if self.source_context != context_identity(self.recipe.edit):
            raise ValueError("plant query changes its exact source context")

    @property
    def case_id(self) -> str:
        return case_id(self.recipe.edit)


@dataclass(frozen=True, slots=True)
class PlantQueriesV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/queries"
    queries_id: str
    source_panel: ObjectIdentity
    protocol_sha256: str
    queries: tuple[PlantQueryV1, ...]

    def __post_init__(self) -> None:
        _id(self.queries_id, "queries")
        _protocol(self.protocol_sha256)
        _tuple(self.queries, PlantQueryV1, minimum=10, maximum=10)
        if self.source_panel != plant_identity() or tuple(q.recipe.edit for q in self.queries) != EDITS:
            raise ValueError("plant queries change the complete nine-mutant plus reversion census")
        for query in self.queries:
            query.__post_init__()


@dataclass(frozen=True, slots=True)
class PlantParentAnchorsV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/parent-anchors"
    anchors_id: str
    source_panel: ObjectIdentity
    protocol_sha256: str
    native_parent: PlantContextV1

    def __post_init__(self) -> None:
        _id(self.anchors_id, "anchors")
        _protocol(self.protocol_sha256)
        if self.source_panel != plant_identity():
            raise ValueError("parent anchors change the frozen source panel")
        _context(self.native_parent, None)

    def value(self, endpoint: str) -> Decimal:
        if endpoint not in ENDPOINTS:
            raise ValueError("parent anchors change the intrinsic endpoint roles")
        return self.native_parent.quantity(endpoint).mean


@dataclass(frozen=True, slots=True)
class PlantLabelV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/label"
    native: PlantContextV1

    def __post_init__(self) -> None:
        if (type(self.native) is not PlantContextV1 or self.native.protein_recipe is None
                or self.native.protein_recipe.edit not in EDITS):
            raise ValueError("plant labels change their exact focal/diagnostic role")
        _context(self.native, self.native.protein_recipe.edit)

    @property
    def case_id(self) -> str:
        return case_id(self.native.protein_recipe.edit)

    def value(self, endpoint: str) -> Decimal:
        if endpoint not in ENDPOINTS:
            raise ValueError("plant labels change the intrinsic endpoint roles")
        return self.native.quantity(endpoint).mean


@dataclass(frozen=True, slots=True)
class PlantLabelsV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/labels"
    labels_id: str
    source_panel: ObjectIdentity
    protocol_sha256: str
    labels: tuple[PlantLabelV1, ...]

    def __post_init__(self) -> None:
        _id(self.labels_id, "labels")
        _protocol(self.protocol_sha256)
        _tuple(self.labels, PlantLabelV1, minimum=10, maximum=10)
        if (self.source_panel != plant_identity()
                or tuple(label.case_id for label in self.labels) != tuple(case_id(edit) for edit in EDITS)):
            raise ValueError("plant labels change the complete assessment census")
        for label in self.labels:
            label.__post_init__()


@dataclass(frozen=True, slots=True)
class SequenceDistanceV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/sequence-distance"
    row_id: str
    distance: int

    def __post_init__(self) -> None:
        validate_stable_id(self.row_id)
        if type(self.distance) is not int or not 0 <= self.distance <= 485:
            raise ValueError("sequence distance must be an exact bounded nonnegative integer")


@dataclass(frozen=True, slots=True)
class NeighbourMeanV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/neighbour-mean"
    k: int
    boundary_distance: int
    neighbours: tuple[SequenceDistanceV1, ...]
    mean: Decimal

    def __post_init__(self) -> None:
        _tuple(self.neighbours, SequenceDistanceV1, maximum=183)
        _positive(self.mean)
        if (type(self.k) is not int or self.k not in K_VALUES or len(self.neighbours) < self.k
                or type(self.boundary_distance) is not int
                or tuple((n.distance, n.row_id) for n in self.neighbours)
                != tuple(sorted((n.distance, n.row_id) for n in self.neighbours))
                or len({n.row_id for n in self.neighbours}) != len(self.neighbours)
                or self.neighbours[self.k - 1].distance != self.boundary_distance
                or self.neighbours[-1].distance != self.boundary_distance):
            raise ValueError("KNN mean changes sorted membership or complete kth-boundary tie")


def check_neighbour_mean(value: NeighbourMeanV1, distances: tuple[SequenceDistanceV1, ...],
                         rows: dict[str, NaturalTrainingRowV1], endpoint: str) -> None:
    value.__post_init__()
    if (len(distances) < value.k
            or value.boundary_distance != distances[value.k - 1].distance
            or value.neighbours != tuple(d for d in distances if d.distance <= value.boundary_distance)
            or value.mean != mean(tuple(rows[n.row_id].value(endpoint) for n in value.neighbours))):
        raise ValueError("KNN mean changes its exact complete distance tie or source-row arithmetic")


def check_distances(distances: tuple[SequenceDistanceV1, ...], expected_ids: tuple[str, ...]) -> None:
    _tuple(distances, SequenceDistanceV1, maximum=183)
    if (tuple((d.distance, d.row_id) for d in distances) != tuple(sorted((d.distance, d.row_id) for d in distances))
            or tuple(sorted(d.row_id for d in distances)) != tuple(sorted(expected_ids))):
        raise ValueError("distance roster changes its complete eligible source census")


@dataclass(frozen=True, slots=True)
class NaturalCVQueryV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/natural-cv-query"
    row_id: str
    held_genus: str
    distances: tuple[SequenceDistanceV1, ...]
    predictions: tuple[NeighbourMeanV1, ...]
    absolute_errors: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.row_id)
        _tuple(self.distances, SequenceDistanceV1, maximum=183)
        _tuple(self.predictions, NeighbourMeanV1, minimum=6, maximum=6)
        _tuple(self.absolute_errors, Decimal, minimum=6, maximum=6)
        if (type(self.held_genus) is not str or not self.held_genus or self.held_genus != self.held_genus.strip()
                or tuple(p.k for p in self.predictions) != K_VALUES):
            raise ValueError("natural tuning omits a frozen k value")
        for error in self.absolute_errors:
            validate_decimal(error, field_name="natural_absolute_error", minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class GenusErrorV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/genus-error"
    genus: str
    row_ids: tuple[str, ...]
    mean_absolute_error: Decimal

    def __post_init__(self) -> None:
        if type(self.genus) is not str or not self.genus or self.genus != self.genus.strip():
            raise ValueError("natural tuning requires the exact native genus")
        if type(self.row_ids) is not tuple or not self.row_ids or self.row_ids != tuple(sorted(set(self.row_ids))):
            raise ValueError("natural tuning needs a complete sorted held-genus roster")
        validate_decimal(self.mean_absolute_error, field_name="genus_mae", minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class KSelectionV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/k-selection"
    k: int
    genus_errors: tuple[GenusErrorV1, ...]
    mean_genus_absolute_error: Decimal

    def __post_init__(self) -> None:
        _tuple(self.genus_errors, GenusErrorV1, minimum=2, maximum=86)
        if (type(self.k) is not int or self.k not in K_VALUES or tuple(e.genus for e in self.genus_errors)
                != tuple(sorted(set(e.genus for e in self.genus_errors)))
                or self.mean_genus_absolute_error != mean(tuple(e.mean_absolute_error for e in self.genus_errors))):
            raise ValueError("natural tuning changes equal-genus weighting or frozen k roster")


@dataclass(frozen=True, slots=True)
class EndpointFitV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/endpoint-fit"
    endpoint: str
    eligible_row_ids: tuple[str, ...]
    cross_validation: tuple[NaturalCVQueryV1, ...]
    tuning: tuple[KSelectionV1, ...]
    chosen_k: int

    def __post_init__(self) -> None:
        _tuple(self.cross_validation, NaturalCVQueryV1, maximum=183)
        _tuple(self.tuning, KSelectionV1, minimum=6, maximum=6)
        if (self.endpoint not in ENDPOINTS or self.eligible_row_ids != tuple(sorted(set(self.eligible_row_ids)))
                or tuple(q.row_id for q in self.cross_validation) != self.eligible_row_ids
                or tuple(t.k for t in self.tuning) != K_VALUES
                or self.chosen_k != min(self.tuning, key=lambda t: (t.mean_genus_absolute_error, t.k)).k):
            raise ValueError("endpoint fit changes its complete natural census or smaller-k tie rule")


def check_endpoint_fit(fit: EndpointFitV1, training: NaturalTrainingV1) -> None:
    fit.__post_init__()
    rows = {row.row_id: row for row in training.rows if row.value(fit.endpoint) is not None}
    if fit.eligible_row_ids != tuple(sorted(rows)):
        raise ValueError("endpoint fit changes natural missing-value membership")
    for query in fit.cross_validation:
        row = rows[query.row_id]
        if query.held_genus != row.genus:
            raise ValueError("natural tuning changes its source genus")
        eligible = tuple(row_id for row_id, row in rows.items() if row.genus != query.held_genus)
        check_distances(query.distances, eligible)
        for prediction in query.predictions:
            check_neighbour_mean(prediction, query.distances, rows, fit.endpoint)
        with localcontext(NUMERICAL_CONTEXT):
            expected = tuple(abs(p.mean - row.value(fit.endpoint)) for p in query.predictions)
        if query.absolute_errors != expected:
            raise ValueError("natural tuning changes source-only held-row errors")
    queries = {q.row_id: q for q in fit.cross_validation}
    for index, tuning in enumerate(fit.tuning):
        expected = tuple(GenusErrorV1(genus, ids, mean(tuple(queries[row_id].absolute_errors[index] for row_id in ids)))
                         for genus in sorted({row.genus for row in rows.values()})
                         for ids in (tuple(sorted(row_id for row_id, row in rows.items() if row.genus == genus)),))
        if tuning.genus_errors != expected:
            raise ValueError("natural tuning omits held genera or changes their arithmetic")


@dataclass(frozen=True, slots=True)
class PlantKNNModelV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/knn-model"
    model_id: str
    training: NaturalTrainingV1
    endpoint_fits: tuple[EndpointFitV1, ...]
    distance_backend: str = DISTANCE_BACKEND

    def __post_init__(self) -> None:
        _id(self.model_id, "model")
        if type(self.training) is not NaturalTrainingV1 or self.distance_backend != DISTANCE_BACKEND:
            raise ValueError("KNN model changes its natural-only fit or maintained distance backend")
        self.training.__post_init__()
        _tuple(self.endpoint_fits, EndpointFitV1, minimum=2, maximum=2)
        if tuple(f.endpoint for f in self.endpoint_fits) != ENDPOINTS:
            raise ValueError("KNN model omits one intrinsic endpoint")
        for fit in self.endpoint_fits:
            check_endpoint_fit(fit, self.training)


@dataclass(frozen=True, slots=True)
class QueryModelPointV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/query-model-point"
    case_id: str
    endpoint: str
    distances: tuple[SequenceDistanceV1, ...]
    fixed_1nn: NeighbourMeanV1
    selected_knn: NeighbourMeanV1

    def __post_init__(self) -> None:
        if self.case_id not in (PREFIX + ".parent", *(case_id(edit) for edit in EDITS)) or self.endpoint not in ENDPOINTS:
            raise ValueError("query model point changes its frozen case or endpoint")
        _tuple(self.distances, SequenceDistanceV1, maximum=183)
        if type(self.fixed_1nn) is not NeighbourMeanV1 or type(self.selected_knn) is not NeighbourMeanV1 or self.fixed_1nn.k != 1:
            raise ValueError("query model point omits its fixed 1NN comparator")


@dataclass(frozen=True, slots=True)
class PlantForecastPointV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/forecast-point"
    case_id: str
    method: str
    endpoint: str
    anchored_value: Decimal
    predicted_log_contrast: Decimal
    same_neighbourhood: bool | None
    same_model_value: bool | None
    same_sequence: bool | None
    same_distances: bool | None

    def __post_init__(self) -> None:
        if self.case_id not in tuple(case_id(edit) for edit in EDITS) or self.method not in METHODS or self.endpoint not in ENDPOINTS:
            raise ValueError("forecast point changes its complete case/method/endpoint grammar")
        _positive(self.anchored_value)
        validate_decimal(self.predicted_log_contrast, field_name="predicted_log_contrast")
        diagnostics = (self.same_neighbourhood, self.same_model_value, self.same_sequence, self.same_distances)
        if (self.method == "parent" and any(d is not None for d in diagnostics)
                or self.method != "parent" and any(type(d) is not bool for d in diagnostics)):
            raise ValueError("forecast point changes its explicit model-degeneracy diagnostics")


def forecast_values(parent: Decimal, numerator: Decimal, denominator: Decimal) -> tuple[Decimal, Decimal]:
    for value in (parent, numerator, denominator):
        _positive(value)
    with localcontext(NUMERICAL_CONTEXT):
        ratio = numerator / denominator
        return parent * numerator / denominator, ratio.ln()


@dataclass(frozen=True, slots=True)
class PlantForecastsV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/forecasts"
    forecast_id: str
    model_identity: ObjectIdentity
    model: PlantKNNModelV1
    queries: PlantQueriesV1
    anchors: PlantParentAnchorsV1
    model_points: tuple[QueryModelPointV1, ...]
    forecasts: tuple[PlantForecastPointV1, ...]
    scope: str = SCOPE

    def __post_init__(self) -> None:
        _id(self.forecast_id, "forecasts")
        if type(self.model) is not PlantKNNModelV1 or type(self.queries) is not PlantQueriesV1 or type(self.anchors) is not PlantParentAnchorsV1:
            raise ValueError("forecasts require separated natural fit, exact queries and parent-only anchors")
        self.model.__post_init__()
        self.queries.__post_init__()
        self.anchors.__post_init__()
        if self.model_identity != ObjectIdentity.from_record(self.model.model_id, self.model) or self.scope != SCOPE:
            raise ValueError("forecasts change their exact model identity or exposed point scope")
        _tuple(self.model_points, QueryModelPointV1, minimum=22, maximum=22)
        _tuple(self.forecasts, PlantForecastPointV1, minimum=60, maximum=60)
        cases = (PREFIX + ".parent", *(case_id(edit) for edit in EDITS))
        if (tuple((p.case_id, p.endpoint) for p in self.model_points) != tuple((case, e) for case in cases for e in ENDPOINTS)
                or tuple((p.case_id, p.method, p.endpoint) for p in self.forecasts)
                != tuple((case_id(edit), m, e) for edit in EDITS for m in METHODS for e in ENDPOINTS)):
            raise ValueError("forecasts omit or reorder a case/method/endpoint before global commitment")
        rows = {row.row_id: row for row in self.model.training.rows}
        queries = {query.case_id: query for query in self.queries.queries}
        fits = {fit.endpoint: fit for fit in self.model.endpoint_fits}
        points = {(point.case_id, point.endpoint): point for point in self.model_points}
        for point in self.model_points:
            fit = fits[point.endpoint]
            check_distances(point.distances, fit.eligible_row_ids)
            if point.selected_knn.k != fit.chosen_k:
                raise ValueError("forecast substitutes its natural-only chosen k")
            for neighbours in (point.fixed_1nn, point.selected_knn):
                check_neighbour_mean(neighbours, point.distances, rows, point.endpoint)
        for forecast in self.forecasts:
            parent = self.anchors.value(forecast.endpoint)
            expected = (parent, Decimal(0), None, None, None, None)
            if forecast.method != "parent":
                query_point = points[forecast.case_id, forecast.endpoint]
                parent_point = points[PREFIX + ".parent", forecast.endpoint]
                name = "fixed_1nn" if forecast.method == "1nn" else "selected_knn"
                query, base = getattr(query_point, name), getattr(parent_point, name)
                expected = (*forecast_values(parent, query.mean, base.mean),
                            tuple(sorted(n.row_id for n in query.neighbours)) == tuple(sorted(n.row_id for n in base.neighbours)),
                            query.mean == base.mean,
                            queries[forecast.case_id].recipe.translated_lsu == self.anchors.native_parent.protein_recipe.translated_lsu,
                            query_point.distances == parent_point.distances)
            if (forecast.anchored_value, forecast.predicted_log_contrast,
                    forecast.same_neighbourhood, forecast.same_model_value,
                    forecast.same_sequence, forecast.same_distances) != expected:
                raise ValueError("forecast changes source-bound anchoring or degeneracy arithmetic")


@dataclass(frozen=True, slots=True)
class PlantCommitmentV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/commitment"
    commitment_id: str
    forecast_identity: ObjectIdentity
    forecasts: PlantForecastsV1

    def __post_init__(self) -> None:
        _id(self.commitment_id, "commitment")
        if type(self.forecasts) is not PlantForecastsV1:
            raise ValueError("global commitment requires complete all-case forecasts")
        self.forecasts.__post_init__()
        if self.forecast_identity != ObjectIdentity.from_record(self.forecasts.forecast_id, self.forecasts):
            raise ValueError("global commitment changes its complete forecast identity")


@dataclass(frozen=True, slots=True)
class PlantPointErrorV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/point-error"
    case_id: str
    method: str
    endpoint: str
    absolute_error: Decimal
    absolute_log_error: Decimal
    log_contrast_error: Decimal
    observed_log_contrast: Decimal

    def __post_init__(self) -> None:
        if self.case_id not in tuple(case_id(edit) for edit in EDITS) or self.method not in METHODS or self.endpoint not in ENDPOINTS:
            raise ValueError("point error changes its complete assessment grammar")
        for value in (self.absolute_error, self.absolute_log_error, self.log_contrast_error):
            validate_decimal(value, field_name="point_error", minimum=Decimal(0))
        validate_decimal(self.observed_log_contrast, field_name="observed_log_contrast")


@dataclass(frozen=True, slots=True)
class PlantErrorSummaryV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/error-summary"
    method: str
    endpoint: str
    weighting: str
    member_ids: tuple[str, ...]
    mean_absolute_error: Decimal
    mean_absolute_log_error: Decimal
    mean_log_contrast_error: Decimal

    def __post_init__(self) -> None:
        if (self.method not in METHODS or self.endpoint not in ENDPOINTS
                or self.weighting not in ("NINE_ROWS", "SIX_SITES")
                or self.member_ids != (tuple(case_id(edit) for edit in FOCAL_EDITS) if self.weighting == "NINE_ROWS"
                                       else tuple(str(site) for site in SITES))):
            raise ValueError("error summary changes the focal row/site denominator")
        for value in (self.mean_absolute_error, self.mean_absolute_log_error, self.mean_log_contrast_error):
            validate_decimal(value, field_name="summary_error", minimum=Decimal(0))


def error_summaries(errors: tuple[PlantPointErrorV1, ...]) -> tuple[PlantErrorSummaryV1, ...]:
    summaries = []
    for method in METHODS:
        for endpoint in ENDPOINTS:
            selected = tuple(error for error in errors if error.method == method and error.endpoint == endpoint
                             and error.case_id != case_id("A369V"))
            for weighting in ("NINE_ROWS", "SIX_SITES"):
                groups = tuple((error,) for error in selected) if weighting == "NINE_ROWS" else tuple(
                    tuple(error for error in selected if error.case_id in tuple(case_id(edit) for edit in FOCAL_EDITS
                                                                              if int(edit[1:-1]) == site)) for site in SITES)
                values = tuple(mean(tuple(mean(tuple(getattr(error, field) for error in group)) for group in groups))
                               for field in ("absolute_error", "absolute_log_error", "log_contrast_error"))
                members = tuple(case_id(edit) for edit in FOCAL_EDITS) if weighting == "NINE_ROWS" else tuple(str(site) for site in SITES)
                summaries.append(PlantErrorSummaryV1(method, endpoint, weighting, members, *values))
    return tuple(summaries)


@dataclass(frozen=True, slots=True)
class PlantEvaluationV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/prediction/evaluation"
    evaluation_id: str
    commitment: ObjectIdentity
    labels: ObjectIdentity
    errors: tuple[PlantPointErrorV1, ...]
    summaries: tuple[PlantErrorSummaryV1, ...]
    scope: str = SCOPE
    independent_biological_units: int | None = None
    calibrated_joint_coverage: Decimal | None = None
    candidate_nomination_established: bool = False
    el_advantage_established: bool = False

    def __post_init__(self) -> None:
        _id(self.evaluation_id, "evaluation")
        _tuple(self.errors, PlantPointErrorV1, minimum=60, maximum=60)
        _tuple(self.summaries, PlantErrorSummaryV1, minimum=12, maximum=12)
        if (tuple((p.case_id, p.method, p.endpoint) for p in self.errors)
                != tuple((case_id(edit), m, e) for edit in EDITS for m in METHODS for e in ENDPOINTS)
                or tuple((s.method, s.endpoint, s.weighting) for s in self.summaries)
                != tuple((m, e, w) for m in METHODS for e in ENDPOINTS for w in ("NINE_ROWS", "SIX_SITES"))):
            raise ValueError("evaluation changes complete focal/diagnostic method/endpoint reporting")
        if self.summaries != error_summaries(self.errors):
            raise ValueError("evaluation changes its complete focal row/site arithmetic")
        for identity, schema, suffix in ((self.commitment, PlantCommitmentV1.SCHEMA, "commitment"),
                                         (self.labels, PlantLabelsV1.SCHEMA, "labels")):
            if (type(identity) is not ObjectIdentity or identity.object_id != PREFIX + "." + suffix
                    or identity.object_schema != schema or identity.object_version != "1.0.0"):
                raise ValueError("evaluation changes its complete commitment or label-role identity")
        if (self.scope != SCOPE or self.independent_biological_units is not None or self.calibrated_joint_coverage is not None
                or self.candidate_nomination_established is not False or self.el_advantage_established is not False):
            raise ValueError("exposed point assessment cannot promote biological calibration, nomination or EL advantage")


RECORD_TYPES = (NaturalTrainingRowV1, NaturalTrainingV1, PlantQueryV1, PlantQueriesV1, PlantParentAnchorsV1,
                PlantLabelV1, PlantLabelsV1, SequenceDistanceV1, NeighbourMeanV1, NaturalCVQueryV1, GenusErrorV1,
                KSelectionV1, EndpointFitV1, PlantKNNModelV1, QueryModelPointV1, PlantForecastPointV1,
                PlantForecastsV1, PlantCommitmentV1, PlantPointErrorV1, PlantErrorSummaryV1, PlantEvaluationV1)
