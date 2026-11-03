# SPDX-License-Identifier: MPL-2.0
"""Natural-only genus tuning, anchored forecasts and post-commit point errors."""

from __future__ import annotations

from decimal import Decimal, localcontext
from functools import lru_cache
from importlib.metadata import version

from empirical_lawhood.adapters.physical.rubisco_kinetics.iqbal2023 import IqbalTrainingTableV1
from empirical_lawhood.adapters.physical.rubisco_kinetics.mcdonald2026 import Mcdonald2026PanelV1
from empirical_lawhood.kernel.provenance import ObjectIdentity

from . import records as r


@lru_cache(maxsize=1)
def _distance_backend():
    # Discovery, codecs and record constructors never import the optional
    # scientific library. Only the selected numerical operation crosses here.
    if version("rapidfuzz") != "3.14.3":
        raise ValueError("plant prediction requires the selected RapidFuzz 3.14.3 profile")
    from rapidfuzz.distance import Levenshtein
    return Levenshtein.distance


def _levenshtein(left: str, right: str) -> int:
    return _distance_backend()(left, right, weights=(1, 1, 1), processor=None, score_cutoff=None)


def prepare_training(table: IqbalTrainingTableV1) -> r.NaturalTrainingV1:
    """Project admitted natural data only; no plant labels are accepted."""
    if type(table) is not IqbalTrainingTableV1:
        raise ValueError("training preparation requires the exact typed natural source")
    return r.NaturalTrainingV1(r.PREFIX + ".training", r.natural_identity(), r.PROTOCOL_SHA256,
                              tuple(r.NaturalTrainingRowV1(row) for row in table.rows), table)


def prepare_plant_roles(panel: Mcdonald2026PanelV1) -> tuple[r.PlantQueriesV1, r.PlantParentAnchorsV1, r.PlantLabelsV1]:
    """Source admission projects roles; fit/predict never take this full panel."""
    if (type(panel) is not Mcdonald2026PanelV1
            or ObjectIdentity.from_record(r.plant_identity().object_id, panel) != r.plant_identity()):
        raise ValueError("plant role preparation requires the exact sealed native panel")
    contexts = {context.protein_recipe.edit: context for context in panel.contexts if context.protein_recipe is not None}
    queries = r.PlantQueriesV1(r.PREFIX + ".queries", r.plant_identity(), r.PROTOCOL_SHA256,
        tuple(r.PlantQueryV1(r.context_identity(edit), contexts[edit].protein_recipe) for edit in r.EDITS))
    anchors = r.PlantParentAnchorsV1(r.PREFIX + ".anchors", r.plant_identity(), r.PROTOCOL_SHA256, contexts[None])
    labels = r.PlantLabelsV1(r.PREFIX + ".labels", r.plant_identity(), r.PROTOCOL_SHA256,
                           tuple(r.PlantLabelV1(contexts[edit]) for edit in r.EDITS))
    return queries, anchors, labels


def _distances(sequence: str, rows: tuple[r.NaturalTrainingRowV1, ...], distance) -> tuple[r.SequenceDistanceV1, ...]:
    return tuple(sorted((r.SequenceDistanceV1(row.row_id, distance(sequence, row.sequence)) for row in rows),
                        key=lambda item: (item.distance, item.row_id)))


def _neighbour_mean(distances: tuple[r.SequenceDistanceV1, ...], rows: dict[str, r.NaturalTrainingRowV1],
                    endpoint: str, k: int) -> r.NeighbourMeanV1:
    if len(distances) < k:
        raise ValueError("natural training fold has fewer source rows than the frozen k")
    boundary = distances[k - 1].distance
    neighbours = tuple(item for item in distances if item.distance <= boundary)
    return r.NeighbourMeanV1(k, boundary, neighbours, r.mean(tuple(rows[n.row_id].value(endpoint) for n in neighbours)))


def _check_model_distances(model: r.PlantKNNModelV1, distance) -> None:
    for fit in model.endpoint_fits:
        rows = {row.row_id: row for row in model.training.rows if row.value(fit.endpoint) is not None}
        for query in fit.cross_validation:
            held = rows[query.row_id]
            expected = _distances(held.sequence, tuple(row for row in rows.values() if row.genus != held.genus), distance)
            if query.distances != expected:
                raise ValueError("KNN model changes its source-sequence distances")


def validate_commitment(commitment: r.PlantCommitmentV1) -> None:
    """Complete source, arithmetic and maintained-distance proof before labels."""
    if type(commitment) is not r.PlantCommitmentV1:
        raise ValueError("evaluation requires a complete global forecast commitment before labels")
    commitment.__post_init__()
    forecast = commitment.forecasts
    distance = lru_cache(maxsize=40000)(_levenshtein)
    _check_model_distances(forecast.model, distance)
    sequences = {r.PREFIX + ".parent": forecast.anchors.native_parent.protein_recipe.translated_lsu,
                 **{query.case_id: query.recipe.translated_lsu for query in forecast.queries.queries}}
    for point in forecast.model_points:
        rows = tuple(row for row in forecast.model.training.rows if row.value(point.endpoint) is not None)
        if point.distances != _distances(sequences[point.case_id], rows, distance):
            raise ValueError("committed forecast changes its source-sequence distances")


def fit(training: r.NaturalTrainingV1) -> r.PlantKNNModelV1:
    """Tune six k values using natural-only complete leave-genus-out folds."""
    if type(training) is not r.NaturalTrainingV1:
        raise ValueError("KNN fit accepts only typed natural training, never plant labels")
    training.__post_init__()
    distance = lru_cache(maxsize=40000)(_levenshtein)
    fits = []
    for endpoint in r.ENDPOINTS:
        eligible = tuple(row for row in training.rows if row.value(endpoint) is not None)
        rows = {row.row_id: row for row in eligible}
        cross_validation = []
        for row_id in sorted(rows):
            held = rows[row_id]
            fold_rows = tuple(row for row in eligible if row.genus != held.genus)
            distances = _distances(held.sequence, fold_rows, distance)
            predictions = tuple(_neighbour_mean(distances, rows, endpoint, k) for k in r.K_VALUES)
            with localcontext(r.NUMERICAL_CONTEXT):
                errors = tuple(abs(prediction.mean - held.value(endpoint)) for prediction in predictions)
            cross_validation.append(r.NaturalCVQueryV1(row_id, held.genus, distances, predictions, errors))
        queries = tuple(cross_validation)
        tuning = []
        for index, k in enumerate(r.K_VALUES):
            genus_errors = tuple(r.GenusErrorV1(genus, tuple(query.row_id for query in queries if query.held_genus == genus),
                r.mean(tuple(query.absolute_errors[index] for query in queries if query.held_genus == genus)))
                for genus in sorted({row.genus for row in eligible}))
            tuning.append(r.KSelectionV1(k, genus_errors, r.mean(tuple(error.mean_absolute_error for error in genus_errors))))
        chosen = min(tuning, key=lambda candidate: (candidate.mean_genus_absolute_error, candidate.k)).k
        fits.append(r.EndpointFitV1(endpoint, tuple(sorted(rows)), queries, tuple(tuning), chosen))
    return r.PlantKNNModelV1(r.PREFIX + ".model", training, tuple(fits))


def predict(model: r.PlantKNNModelV1, queries: r.PlantQueriesV1,
            anchors: r.PlantParentAnchorsV1) -> r.PlantForecastsV1:
    """Read exact recipes and measured parent anchors; no mutant labels."""
    if (type(model) is not r.PlantKNNModelV1 or type(queries) is not r.PlantQueriesV1
            or type(anchors) is not r.PlantParentAnchorsV1):
        raise ValueError("predict accepts natural model, label-free queries and parent anchors only")
    model.__post_init__()
    queries.__post_init__()
    anchors.__post_init__()
    distance = lru_cache(maxsize=40000)(_levenshtein)
    _check_model_distances(model, distance)
    fits = {fit.endpoint: fit for fit in model.endpoint_fits}
    model_points = []
    sequences = ((r.PREFIX + ".parent", anchors.native_parent.protein_recipe.translated_lsu),
                 *((query.case_id, query.recipe.translated_lsu) for query in queries.queries))
    for case, sequence in sequences:
        for endpoint in r.ENDPOINTS:
            rows = tuple(row for row in model.training.rows if row.value(endpoint) is not None)
            by_id = {row.row_id: row for row in rows}
            distances = _distances(sequence, rows, distance)
            model_points.append(r.QueryModelPointV1(case, endpoint, distances,
                _neighbour_mean(distances, by_id, endpoint, 1),
                _neighbour_mean(distances, by_id, endpoint, fits[endpoint].chosen_k)))
    points = {(point.case_id, point.endpoint): point for point in model_points}
    forecasts = []
    for query in queries.queries:
        for method in r.METHODS:
            for endpoint in r.ENDPOINTS:
                parent = anchors.value(endpoint)
                value, contrast, same_neighbours, same_value, same_sequence, same_distances = parent, Decimal(0), None, None, None, None
                if method != "parent":
                    name = "fixed_1nn" if method == "1nn" else "selected_knn"
                    point = getattr(points[query.case_id, endpoint], name)
                    base = getattr(points[r.PREFIX + ".parent", endpoint], name)
                    value, contrast = r.forecast_values(parent, point.mean, base.mean)
                    same_neighbours = tuple(sorted(n.row_id for n in point.neighbours)) == tuple(sorted(n.row_id for n in base.neighbours))
                    same_value = point.mean == base.mean
                    same_sequence = query.recipe.translated_lsu == anchors.native_parent.protein_recipe.translated_lsu
                    same_distances = points[query.case_id, endpoint].distances == points[r.PREFIX + ".parent", endpoint].distances
                forecasts.append(r.PlantForecastPointV1(query.case_id, method, endpoint, value, contrast,
                    same_neighbours, same_value, same_sequence, same_distances))
    return r.PlantForecastsV1(r.PREFIX + ".forecasts", ObjectIdentity.from_record(model.model_id, model),
                            model, queries, anchors, tuple(model_points), tuple(forecasts))


def commit(forecasts: r.PlantForecastsV1) -> r.PlantCommitmentV1:
    if type(forecasts) is not r.PlantForecastsV1:
        raise ValueError("global commitment requires typed complete all-case forecasts")
    commitment = r.PlantCommitmentV1(r.PREFIX + ".commitment", ObjectIdentity.from_record(forecasts.forecast_id, forecasts), forecasts)
    validate_commitment(commitment)
    return commitment


def evaluate(commitment: r.PlantCommitmentV1, labels: r.PlantLabelsV1) -> r.PlantEvaluationV1:
    """Validate complete global commitment before accessing any label operand."""
    validate_commitment(commitment)
    # This boundary is intentional: even type/field inspection of labels follows
    # all-case model/source/forecast/census validation above.
    if type(labels) is not r.PlantLabelsV1:
        raise ValueError("evaluation needs only the typed post-commit mutant labels")
    labels.__post_init__()
    forecast = commitment.forecasts
    targets = {label.case_id: label for label in labels.labels}
    queries = {query.case_id: query for query in forecast.queries.queries}
    for case, target in targets.items():
        if target.native.protein_recipe != queries[case].recipe:
            raise ValueError("evaluation labels change a committed exact paired-subunit query")
    errors = []
    with localcontext(r.NUMERICAL_CONTEXT):
        for point in forecast.forecasts:
            observed = targets[point.case_id].value(point.endpoint)
            parent = forecast.anchors.value(point.endpoint)
            observed_contrast = (observed / parent).ln()
            errors.append(r.PlantPointErrorV1(point.case_id, point.method, point.endpoint,
                abs(point.anchored_value - observed), abs(point.anchored_value.ln() - observed.ln()),
                abs(point.predicted_log_contrast - observed_contrast), observed_contrast))
    error_roster = tuple(errors)
    return r.PlantEvaluationV1(r.PREFIX + ".evaluation", ObjectIdentity.from_record(commitment.commitment_id, commitment),
                              ObjectIdentity.from_record(labels.labels_id, labels), error_roster, r.error_summaries(error_roster))
