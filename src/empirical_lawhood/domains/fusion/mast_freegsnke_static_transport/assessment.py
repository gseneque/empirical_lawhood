"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast, Any, Sequence
import math
import numpy as np
from numpy.typing import NDArray
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.domains.fusion.mast_freegsnke_static_transport.contracts import StaticTransportCloseout, StaticTransportDisposition, StaticTransportFacePrediction, StaticTransportFaceResult, StaticTransportPredictionPackage


from typing import Final

EXPERIMENT_ID: Final = "mast-public-static-freegsnke-metatheory-validation"


MACHINE_ARCHIVE_SHA256: Final = "28294edad722037a3597e665ad4d1ae419a14b9422a2262689ddba7ac350710a"


SHOT_MEMBERS: Final = {
    "45292": (
        "MAST-U_validation_odr/data/MAST-U_shot_45292.pickle",
        "d2bc37eac5340bab0f23dc76e6ab824fec823e921b29b2e6996378ceda9fa5e2",
    ),
    "45425": (
        "MAST-U_validation_odr/data/MAST-U_shot_45425.pickle",
        "8768d670328f78ca8dc8722967c13e22c34bf383019571aa2f5843884a4abec4",
    ),
}


SLICE_TIMES_S: Final = (0.15, 0.25, 0.35, 0.45, 0.55, 0.65)


COORDINATES: Final = ("ACTIVE_ONLY", "FULL_NATIVE", "SYMMETRY_COLLAPSED")


VIEWS: Final = {"baseline-65": 65, "refined-129": 129}


FACES: Final = (
    "boundary.magnetic-axis",
    "boundary.primary-x-point",
    "boundary.separatrix",
    "boundary.strike-point",
    "category.equilibrium-topology",
    "composition.independent-comparator",
    "representation.normalized-poloidal-flux",
    "response.magnetic-flux-or-pickup",
)


COORDINATE_RESOLUTION_M: Final = 1e-12


FLUX_RESOLUTION: Final = 1e-12



class StaticTransportError(RuntimeError):
    """Typed experiment-local operational/contract failure."""

@dataclass(frozen=True, slots=True)
class StaticCellSummary:
    coordinate_id: str
    view_id: str
    valid: NDArray[np.bool_]
    relative_change: NDArray[np.float64]
    runtime_s: NDArray[np.float64]
    psi_normalized: NDArray[np.float64]
    axis_rz_m: NDArray[np.float64]
    xpoint_rz_m: NDArray[np.float64]
    xpoint_flux_mismatch: NDArray[np.float64]
    topology_code: NDArray[np.str_]
    midplane_r_m: NDArray[np.float64]

def _slice_indices(value: Mapping[str, object]) -> NDArray[np.int64]:
    times = np.asarray(value["efit_times"], dtype=np.float64)
    indices = []
    for requested in SLICE_TIMES_S:
        matches = np.flatnonzero(times == requested)
        if len(matches) != 1:
            raise StaticTransportError(f"shot lacks exact slice time: {requested}")
        indices.append(int(matches[0]))
    return np.asarray(indices, dtype=np.int64)

def preparation_arrays(value: Mapping[str, object]) -> dict[str, NDArray[np.generic]]:
    """Select preparation fields only; this function names no receiver field."""

    indices = _slice_indices(value)
    grid = cast(Mapping[str, object], value["efit_grid"])
    profiles = cast(Mapping[str, object], value["efit_1D_current_profiles"])
    currents = cast(Mapping[str, object], value["efit_currents"])
    plasma = cast(Mapping[str, object], value["efit_plasma_current"])
    other = cast(Mapping[str, object], value["efit_other_input_output_parameters"])
    labels = np.asarray(currents["coil_name"], dtype="U32")
    current_output = np.asarray(currents["currents_output"], dtype=np.float64)[indices]
    arrays: dict[str, NDArray[np.generic]] = {
        "alpha": np.asarray(profiles["pprime_coeffs"], dtype=np.float64)[indices],
        "alpha_logic": np.asarray(profiles["pprime_flatedge_logical"], dtype=np.int8)[indices],
        "beta": np.asarray(profiles["ffprime_coeffs"], dtype=np.float64)[indices],
        "beta_logic": np.asarray(profiles["ffprime_flatedge_logical"], dtype=np.int8)[indices],
        "coil_labels": labels,
        "currents_output_a": current_output,
        "fvac_t_m": np.asarray(other["bvacradiusproduct_input"], dtype=np.float64)[indices],
        "grid": np.asarray(
            [
                float(np.asarray(grid["rmin"])[0]),
                float(np.asarray(grid["rmax"])[0]),
                float(np.asarray(grid["zmin"])[0]),
                float(np.asarray(grid["zmax"])[0]),
            ],
            dtype=np.float64,
        ),
        "plasma_current_a": np.asarray(plasma["plasma_current_output"], dtype=np.float64)[indices],
        "slice_indices": indices,
        "slice_times_s": np.asarray(SLICE_TIMES_S, dtype=np.float64),
    }
    if any(not np.isfinite(value).all() for key, value in arrays.items() if key != "coil_labels"):
        raise StaticTransportError("preparation contains a non-finite selected value")
    if current_output.shape != (len(SLICE_TIMES_S), len(labels)):
        raise StaticTransportError("current preparation shape differs")
    return arrays

def receiver_arrays(value: Mapping[str, object]) -> dict[str, NDArray[np.generic]]:
    """Select the predeclared reconstruction receivers at evaluator reveal."""

    indices = _slice_indices(value)
    flux = cast(Mapping[str, object], value["efit_2D_poloidal_flux"])
    other = cast(Mapping[str, object], value["efit_other_input_output_parameters"])
    psi = 2 * np.pi * np.asarray(flux["psi"], dtype=np.float64)[indices]
    xpoints = np.stack(
        (
            np.asarray(flux["x_points_r"], dtype=np.float64)[indices],
            np.asarray(flux["x_points_z"], dtype=np.float64)[indices],
        ),
        axis=-1,
    )
    strikes = np.stack(
        (
            np.asarray(flux["r_strikepoints"], dtype=np.float64)[indices],
            np.asarray(flux["z_strikepoints"], dtype=np.float64)[indices],
        ),
        axis=-1,
    )
    for points in (xpoints, strikes):
        valid = (
            np.isfinite(points).all(axis=-1)
            & (points[..., 0] >= 0.06)
            & (points[..., 0] <= 2.0)
            & (points[..., 1] >= -2.2)
            & (points[..., 1] <= 2.2)
        )
        points[~valid] = np.nan
    arrays: dict[str, NDArray[np.generic]] = {
        "axis_rz_m": np.stack(
            (
                np.asarray(other["magnetic_axis_r"], dtype=np.float64)[indices],
                np.asarray(other["magnetic_axis_z"], dtype=np.float64)[indices],
            ),
            axis=-1,
        ),
        "midplane_r_m": np.stack(
            (
                np.asarray(flux["r_midplane_in"], dtype=np.float64)[indices],
                np.asarray(flux["r_midplane_out"], dtype=np.float64)[indices],
            ),
            axis=-1,
        ),
        "psi_axis_wb": 2 * np.pi * np.asarray(flux["psi_axis"], dtype=np.float64)[indices],
        "psi_boundary_wb": 2 * np.pi * np.asarray(flux["psi_boundary"], dtype=np.float64)[indices],
        "psi_total_wb": psi,
        "slice_times_s": np.asarray(SLICE_TIMES_S, dtype=np.float64),
        "strikepoints_rz_m": strikes,
        "xpoints_rz_m": xpoints,
    }
    required = ("axis_rz_m", "midplane_r_m", "psi_axis_wb", "psi_boundary_wb", "psi_total_wb")
    if any(not np.isfinite(arrays[name]).all() for name in required):
        raise StaticTransportError("required receiver field contains non-finite data")
    return arrays

def _cell(
    outputs: Mapping[str, NDArray[np.generic]], coordinate: str, view: str
) -> StaticCellSummary:
    prefix = f"{coordinate.lower()}__{view.replace('-', '_')}"
    return StaticCellSummary(
        coordinate_id=coordinate,
        view_id=view,
        valid=np.asarray(outputs[f"{prefix}__valid"], dtype=np.bool_),
        relative_change=np.asarray(outputs[f"{prefix}__relative_change"], dtype=np.float64),
        runtime_s=np.asarray(outputs[f"{prefix}__runtime_s"], dtype=np.float64),
        psi_normalized=np.asarray(outputs[f"{prefix}__psi_normalized"], dtype=np.float64),
        axis_rz_m=np.asarray(outputs[f"{prefix}__axis_rz_m"], dtype=np.float64),
        xpoint_rz_m=np.asarray(outputs[f"{prefix}__xpoint_rz_m"], dtype=np.float64),
        xpoint_flux_mismatch=np.asarray(
            outputs[f"{prefix}__xpoint_flux_mismatch"], dtype=np.float64
        ),
        topology_code=np.asarray(outputs[f"{prefix}__topology_code"], dtype=str),
        midplane_r_m=np.asarray(outputs[f"{prefix}__midplane_r_m"], dtype=np.float64),
    )

def static_output_validity(outputs: Mapping[str, NDArray[np.generic]]) -> dict[str, bool]:
    return {
        coordinate: all(
            bool(value)
            for view in sorted(VIEWS)
            for value in _cell(outputs, coordinate, view).valid
        )
        for coordinate in COORDINATES
    }

def _source_topology(receivers: Mapping[str, NDArray[np.generic]]) -> NDArray[np.str_]:
    points = np.asarray(receivers["xpoints_rz_m"], dtype=np.float64)
    labels = []
    for value in points:
        valid = value[np.isfinite(value).all(axis=1)]
        if len(valid) != 1:
            labels.append("UNQUALIFIED")
        else:
            labels.append("LOWER_SINGLE_NULL" if valid[0, 1] < 0 else "UPPER_SINGLE_NULL")
    return np.asarray(labels, dtype=str)

def face_point_estimates(
    receivers: Mapping[str, NDArray[np.generic]],
    outputs: Mapping[str, NDArray[np.generic]],
) -> dict[str, dict[str, dict[str, object]]]:
    source_psi = np.asarray(receivers["psi_total_wb"], dtype=np.float64)
    source_axis_flux = np.asarray(receivers["psi_axis_wb"], dtype=np.float64)
    source_boundary_flux = np.asarray(receivers["psi_boundary_wb"], dtype=np.float64)
    source_normalized = (source_psi - source_axis_flux[:, None, None]) / (
        source_boundary_flux - source_axis_flux
    )[:, None, None]
    source_axis = np.asarray(receivers["axis_rz_m"], dtype=np.float64)
    source_xpoints = np.asarray(receivers["xpoints_rz_m"], dtype=np.float64)
    source_midplane = np.asarray(receivers["midplane_r_m"], dtype=np.float64)
    source_topology = _source_topology(receivers)
    result: dict[str, dict[str, dict[str, object]]] = {}
    for coordinate in COORDINATES:
        result[coordinate] = {}
        for view in sorted(VIEWS):
            cell = _cell(outputs, coordinate, view)
            source_primary = np.full((len(SLICE_TIMES_S), 2), np.nan)
            for index, points in enumerate(source_xpoints):
                valid = points[np.isfinite(points).all(axis=1)]
                if len(valid) == 1:
                    source_primary[index] = valid[0]
            psi_delta = cell.psi_normalized - source_normalized
            result[coordinate][view] = {
                "axis_distance_m": np.linalg.norm(cell.axis_rz_m - source_axis, axis=1).tolist(),
                "complete_cell": cell.valid.tolist(),
                "flux_max_abs_1": np.max(np.abs(psi_delta), axis=(1, 2)).tolist(),
                "flux_rms_1": np.sqrt(np.mean(psi_delta**2, axis=(1, 2))).tolist(),
                "midplane_max_abs_m": np.max(
                    np.abs(cell.midplane_r_m - source_midplane), axis=1
                ).tolist(),
                "relative_change": cell.relative_change.tolist(),
                "runtime_s": cell.runtime_s.tolist(),
                "source_topology": source_topology.tolist(),
                "target_topology": cell.topology_code.tolist(),
                "topology_match": (cell.topology_code == source_topology).tolist(),
                "xpoint_distance_m": np.linalg.norm(
                    cell.xpoint_rz_m - source_primary, axis=1
                ).tolist(),
                "xpoint_source_complete": np.isfinite(source_primary).all(axis=1).tolist(),
            }
    return result

def _maximum(values: object) -> float:
    array = np.asarray(values, dtype=np.float64)
    finite = array[np.isfinite(array)]
    if not len(finite):
        raise StaticTransportError("no finite development metric values")
    return float(np.max(finite))

def build_prediction_package(
    development_receivers: Mapping[str, NDArray[np.generic]],
    development_outputs: Mapping[str, NDArray[np.generic]],
    *,
    evaluator_implementation_sha256: str,
) -> tuple[StaticTransportPredictionPackage, dict[str, object]]:
    metrics = face_point_estimates(development_receivers, development_outputs)
    full_refined = metrics["FULL_NATIVE"]["refined-129"]
    output_arrays = development_outputs
    full_base_cell = _cell(output_arrays, "FULL_NATIVE", "baseline-65")
    full_refined_cell = _cell(output_arrays, "FULL_NATIVE", "refined-129")
    if not all(full_base_cell.valid) or not all(full_refined_cell.valid):
        raise StaticTransportError("development FULL_NATIVE target is incomplete")
    view_disagreement = {
        "boundary.magnetic-axis": float(
            np.max(np.linalg.norm(full_base_cell.axis_rz_m - full_refined_cell.axis_rz_m, axis=1))
        ),
        "boundary.primary-x-point": float(
            np.max(
                np.linalg.norm(full_base_cell.xpoint_rz_m - full_refined_cell.xpoint_rz_m, axis=1)
            )
        ),
        "representation.normalized-poloidal-flux": float(
            np.max(
                np.sqrt(
                    np.mean(
                        (full_base_cell.psi_normalized - full_refined_cell.psi_normalized) ** 2,
                        axis=(1, 2),
                    )
                )
            )
        ),
    }
    metric_inputs = {
        "boundary.magnetic-axis": ("m", full_refined["axis_distance_m"]),
        "boundary.primary-x-point": ("m", full_refined["xpoint_distance_m"]),
        "representation.normalized-poloidal-flux": ("1", full_refined["flux_rms_1"]),
    }
    predictions: list[StaticTransportFacePrediction] = []
    for face in FACES:
        if face in metric_inputs:
            unit, values = metric_inputs[face]
            if face == "boundary.primary-x-point" and not all(
                cast(list[bool], full_refined["xpoint_source_complete"])
            ):
                predictions.append(
                    StaticTransportFacePrediction(
                        face_id=face,
                        predictive_level="METRIC",
                        applicable=False,
                        metric_unit=unit,
                        development_maximum=None,
                        development_view_disagreement_maximum=None,
                        categorical_prediction=None,
                        source_uncertainty_qualified=False,
                        decisive_falsifier="OPERAND_ABSENT",
                        limitation_codes=("DEVELOPMENT_SOURCE_XPOINT_INCOMPLETE",),
                    )
                )
                continue
            predictions.append(
                StaticTransportFacePrediction(
                    face_id=face,
                    predictive_level="METRIC",
                    applicable=True,
                    metric_unit=unit,
                    development_maximum=format(_maximum(values), ".17g"),
                    development_view_disagreement_maximum=format(view_disagreement[face], ".17g"),
                    categorical_prediction=None,
                    source_uncertainty_qualified=False,
                    decisive_falsifier="protected-shot-maximum-exceeds-issued-envelope",
                    limitation_codes=("SOURCE_OBSERVATION_UNCERTAINTY_UNKNOWN",),
                )
            )
        elif face == "category.equilibrium-topology":
            topology_complete = all(
                value != "UNQUALIFIED" for value in cast(list[str], full_refined["source_topology"])
            )
            predictions.append(
                StaticTransportFacePrediction(
                    face_id=face,
                    predictive_level="CATEGORICAL",
                    applicable=topology_complete,
                    metric_unit="category",
                    development_maximum=None,
                    development_view_disagreement_maximum=None,
                    categorical_prediction=(
                        "EXACT_SOURCE_SLICE_LABEL" if topology_complete else None
                    ),
                    source_uncertainty_qualified=True,
                    decisive_falsifier=(
                        "any-complete-protected-slice-category-mismatch"
                        if topology_complete
                        else "OPERAND_ABSENT"
                    ),
                    limitation_codes=(
                        () if topology_complete else ("DEVELOPMENT_SOURCE_TOPOLOGY_INCOMPLETE",)
                    ),
                )
            )
        else:
            predictions.append(
                StaticTransportFacePrediction(
                    face_id=face,
                    predictive_level="METRIC",
                    applicable=False,
                    metric_unit="unbound",
                    development_maximum=None,
                    development_view_disagreement_maximum=None,
                    categorical_prediction=None,
                    source_uncertainty_qualified=False,
                    decisive_falsifier="OPERAND_ABSENT",
                    limitation_codes=("SOURCE_QUALIFIED_OPERAND_ABSENT",),
                )
            )
    package = StaticTransportPredictionPackage(
        prediction_id="prediction.mast-static-transport.route-u",
        experiment_id=EXPERIMENT_ID,
        selected_route="ROUTE_U_26M5_JMPP",
        source_shot_id="45292",
        target_shot_id="45425",
        source_member_sha256=SHOT_MEMBERS["45292"][1],
        target_member_sha256=SHOT_MEMBERS["45425"][1],
        machine_archive_sha256=MACHINE_ARCHIVE_SHA256,
        slice_times_s=tuple(format(value, ".17g") for value in SLICE_TIMES_S),
        coordinate_ids=tuple(sorted(COORDINATES)),
        numerical_view_ids=tuple(sorted(VIEWS)),
        predictions=tuple(sorted(predictions, key=lambda value: value.face_id)),
        target_preparation_contact_count=0,
        target_receiver_contact_count=0,
        target_execution_count=0,
        evaluator_implementation_sha256=evaluator_implementation_sha256,
        claim_ceiling=(
            "ONE_PROTECTED_MASTU_SHOT_STATIC_PROPERTY_EXISTENCE_WITH_SHARED_PREPARATION_LINEAGE"
        ),
        outcome_access=OutcomeAccess.OUTCOME_BLIND,
    )
    dossier: dict[str, object] = {
        "development_metrics": metrics,
        "prediction_fingerprint": package.fingerprint(),
        "view_disagreement": view_disagreement,
    }
    return package, dossier

def _result_for_metric(
    prediction: StaticTransportFacePrediction,
    target_maximum: float,
) -> StaticTransportFaceResult:
    development = float(cast(str, prediction.development_maximum))
    disagreement = float(cast(str, prediction.development_view_disagreement_maximum))
    resolution = COORDINATE_RESOLUTION_M if prediction.metric_unit == "m" else FLUX_RESOLUTION
    descriptive_limit = development + disagreement + resolution
    inside = target_maximum <= descriptive_limit
    # Unknown source uncertainty is controlling; descriptive envelope is not promoted.
    return StaticTransportFaceResult(
        face_id=prediction.face_id,
        disposition=StaticTransportDisposition.UNEVALUABLE,
        predictive_level="METRIC",
        complete_unit_numerator=1,
        complete_unit_denominator=1,
        target_value=format(target_maximum, ".17g"),
        issued_limit=None,
        point_estimate_inside_development_envelope=inside,
        falsifier_triggered=None,
        reason_codes=("SOURCE_OBSERVATION_UNCERTAINTY_UNKNOWN",),
        evidence_ceiling="DESCRIPTIVE_POINT_ESTIMATE_ONLY",
    )

def evaluate_closeout(
    prediction: StaticTransportPredictionPackage,
    target_receivers: Mapping[str, NDArray[np.generic]],
    target_outputs: Mapping[str, NDArray[np.generic]],
    *,
    route_receipt: ArtifactIdentity,
    development_artifacts: tuple[ArtifactIdentity, ...],
    target_artifacts: tuple[ArtifactIdentity, ...],
) -> tuple[StaticTransportCloseout, dict[str, object]]:
    metrics = face_point_estimates(target_receivers, target_outputs)
    full = metrics["FULL_NATIVE"]["refined-129"]
    results: list[StaticTransportFaceResult] = []
    prediction_by_face = {value.face_id: value for value in prediction.predictions}
    for face in FACES:
        item = prediction_by_face[face]
        if not item.applicable:
            results.append(
                StaticTransportFaceResult(
                    face_id=face,
                    disposition=StaticTransportDisposition.NOT_APPLICABLE,
                    predictive_level=item.predictive_level,
                    complete_unit_numerator=0,
                    complete_unit_denominator=1,
                    target_value=None,
                    issued_limit=None,
                    point_estimate_inside_development_envelope=None,
                    falsifier_triggered=None,
                    reason_codes=("SOURCE_QUALIFIED_OPERAND_ABSENT",),
                    evidence_ceiling="OPERAND_ABSENT",
                )
            )
        elif face == "boundary.magnetic-axis":
            results.append(_result_for_metric(item, _maximum(full["axis_distance_m"])))
        elif face == "boundary.primary-x-point":
            if not all(cast(list[bool], full["xpoint_source_complete"])):
                results.append(
                    StaticTransportFaceResult(
                        face_id=face,
                        disposition=StaticTransportDisposition.UNEVALUABLE,
                        predictive_level="METRIC",
                        complete_unit_numerator=0,
                        complete_unit_denominator=1,
                        target_value=None,
                        issued_limit=None,
                        point_estimate_inside_development_envelope=None,
                        falsifier_triggered=None,
                        reason_codes=("AMBIGUOUS_SOURCE_XPOINT_SLOT",),
                        evidence_ceiling="SOURCE_RECONSTRUCTION_LABEL_UNQUALIFIED",
                    )
                )
            else:
                results.append(_result_for_metric(item, _maximum(full["xpoint_distance_m"])))
        elif face == "representation.normalized-poloidal-flux":
            results.append(_result_for_metric(item, _maximum(full["flux_rms_1"])))
        elif face == "category.equilibrium-topology":
            complete = [
                source != "UNQUALIFIED" and bool(match)
                for source, match in zip(
                    cast(list[str], full["source_topology"]),
                    cast(list[bool], full["topology_match"]),
                    strict=True,
                )
            ]
            source_complete = all(
                value != "UNQUALIFIED" for value in cast(list[str], full["source_topology"])
            )
            disposition = (
                StaticTransportDisposition.SUPPORTED
                if source_complete and all(complete)
                else StaticTransportDisposition.OPPOSED
                if source_complete
                else StaticTransportDisposition.UNEVALUABLE
            )
            reasons = (
                ()
                if disposition is StaticTransportDisposition.SUPPORTED
                else ("PROTECTED_TOPOLOGY_MISMATCH",)
                if disposition is StaticTransportDisposition.OPPOSED
                else ("AMBIGUOUS_SOURCE_TOPOLOGY_LABEL",)
            )
            results.append(
                StaticTransportFaceResult(
                    face_id=face,
                    disposition=disposition,
                    predictive_level="CATEGORICAL",
                    complete_unit_numerator=int(source_complete),
                    complete_unit_denominator=1,
                    target_value=None,
                    issued_limit=None,
                    point_estimate_inside_development_envelope=None,
                    falsifier_triggered=(not all(complete)) if source_complete else None,
                    reason_codes=reasons,
                    evidence_ceiling="ONE_PROTECTED_MASTU_SHOT_CATEGORY_EXISTENCE",
                )
            )
    entered_metric_keys = ("axis_distance_m", "flux_rms_1")
    full_maxima = {key: _maximum(full[key]) for key in entered_metric_keys}
    no_worse = True
    strictly_better = False
    challenger_summary: dict[str, object] = {}
    for challenger in ("ACTIVE_ONLY", "SYMMETRY_COLLAPSED"):
        challenger_values = metrics[challenger]["refined-129"]
        targetable = all(cast(list[bool], challenger_values["complete_cell"]))
        if not targetable:
            challenger_summary[challenger] = {
                "disposition": "COORDINATE_UNTARGETABLE",
                "complete_cell": challenger_values["complete_cell"],
            }
            continue
        maxima = {key: _maximum(challenger_values[key]) for key in entered_metric_keys}
        comparisons = {key: full_maxima[key] <= maxima[key] for key in entered_metric_keys}
        no_worse = no_worse and all(comparisons.values())
        strictly_better = strictly_better or any(
            full_maxima[key] < maxima[key] for key in entered_metric_keys
        )
        challenger_summary[challenger] = {
            "disposition": "TARGETABLE",
            "maxima": maxima,
            "full_no_worse": comparisons,
        }
    challenger_summary["DESCRIPTIVE_SUMMARY"] = {
        "full_native_no_worse_on_complete_point_estimates": no_worse,
        "full_native_strictly_better_on_at_least_one_point_estimate": strictly_better,
    }
    coordinate_disposition = StaticTransportDisposition.UNEVALUABLE
    coordinate_reasons = (
        "ENTERED_METRIC_FACE_UNEVALUABLE",
        "SOURCE_OBSERVATION_UNCERTAINTY_UNKNOWN",
    )
    closeout = StaticTransportCloseout(
        closeout_id="closeout.mast-static-freegsnke-metatheory-validation",
        experiment_id=EXPERIMENT_ID,
        prediction_package_fingerprint=prediction.fingerprint(),
        route_receipt=route_receipt,
        development_artifacts=tuple(
            sorted(development_artifacts, key=lambda value: value.artifact_id)
        ),
        target_artifacts=tuple(sorted(target_artifacts, key=lambda value: value.artifact_id)),
        face_results=tuple(sorted(results, key=lambda value: value.face_id)),
        coordinate_disposition=coordinate_disposition,
        coordinate_reason_codes=coordinate_reasons,
        achieved_dependence_class="SHARED_ARCHIVE_PREPARATION_AND_ANALYSIS_LINEAGE",
        shared_lineage=True,
        operational_status="COMPLETED",
        claim_ceiling=(
            "ONE_PROTECTED_MASTU_SHOT_STATIC_PROPERTY_EXISTENCE_NO_PREVALENCE_OR_INDEPENDENT_RECURRENCE"
        ),
        response_law_constructed=False,
        admission_or_controller_evaluation_constructed=False,
        outcome_access=OutcomeAccess.EVALUATION_REVEALED,
    )
    analysis: dict[str, object] = {
        "challenger_summary": challenger_summary,
        "coordinate_disposition": coordinate_disposition.value,
        "face_metrics": metrics,
        "full_native_target_maxima": full_maxima,
    }
    return closeout, analysis


SOLVER_TOLERANCE: Final = 1e-6


def map_coil_currents(
    active_coil_names: Sequence[str],
    machine: Mapping[str, object],
    coordinate_id: str,
    labels: list[str],
    values: NDArray[np.float64],
) -> dict[str, float]:
    result: dict[str, float] = {}
    lower_labels = [value.lower() for value in labels]
    if coordinate_id == "SYMMETRY_COLLAPSED":
        for name in cast(Mapping[str, object], machine["active-symmetric"]):
            source = "p1" if name == "Solenoid" else name.lower()
            indices = [index for index, label in enumerate(lower_labels[:24]) if source in label]
            if not indices:
                raise StaticTransportError(f"symmetric active mapping absent: {name}")
            polarity = float(np.sign(values[indices[0]]))
            result[name] = polarity * float(np.mean(np.abs(values[indices])))
    else:
        for name in active_coil_names[:23]:
            source = "p1" if name == "Solenoid" else name.lower()
            if source not in lower_labels:
                raise StaticTransportError(f"nonsymmetric active mapping absent: {name}")
            result[name] = float(values[lower_labels.index(source)])
    passive = cast(list[dict[str, object]], machine["passive"])
    for coil in passive:
        source = str(coil.get("efitGroup", coil.get("element", ""))).lower()
        current = 0.0
        if coordinate_id != "ACTIVE_ONLY" and source in lower_labels:
            current = float(values[lower_labels.index(source)]) * float(
                cast(Any, coil["current_multiplier"])
            )
        result[str(coil["name"])] = current
    return result


def primary_xpoint(points: NDArray[np.float64], psi_axis: float, psi_boundary: float) -> tuple[NDArray[np.float64], float, str]:
    points = np.asarray(points, dtype=np.float64)
    span = abs(psi_axis - psi_boundary)
    mismatch = np.abs(points[:, 2] - psi_boundary) / span
    order = np.lexsort((points[:, 1], points[:, 0], mismatch))
    selected = int(order[0])
    point = points[selected, :2]
    tolerance = float(mismatch[selected])
    if tolerance > 1e-3:
        return point, tolerance, "UNQUALIFIED"
    return point, tolerance, "LOWER_SINGLE_NULL" if point[1] < 0 else "UPPER_SINGLE_NULL"


def assess_static_equilibrium(
    *, psi_native: NDArray[np.float64], psi_axis_native: float, psi_boundary_native: float,
    r_coordinates: NDArray[np.float64], z_coordinates: NDArray[np.float64],
    grid: NDArray[np.float64], xpoints: NDArray[np.float64], midplane: NDArray[np.float64],
    axis_rz: NDArray[np.float64], relative_change: float, intersects_wall: bool,
    is_limited: bool, runtime_s: float,
) -> dict[str, NDArray[np.generic] | float | str | bool]:
    """Normalize, regrid and assess supplied equilibrium operands without a solver."""
    from scipy.interpolate import RegularGridInterpolator

    psi = 2 * np.pi * np.asarray(psi_native, dtype=np.float64)
    axis = 2 * np.pi * psi_axis_native
    boundary = 2 * np.pi * psi_boundary_native
    normalized = (psi - axis) / (boundary - axis)
    source_r = np.linspace(grid[0], grid[1], 65)
    source_z = np.linspace(grid[2], grid[3], 65)
    r_mesh, z_mesh = np.meshgrid(source_r, source_z, indexing="ij")
    common = RegularGridInterpolator(
        (np.asarray(r_coordinates), np.asarray(z_coordinates)),
        normalized,
        bounds_error=True,
    )(np.stack((r_mesh, z_mesh), axis=-1))
    point, mismatch, topology = primary_xpoint(xpoints, psi_axis_native, psi_boundary_native)
    midplane = np.asarray(midplane, dtype=np.float64)
    valid = bool(
        np.isfinite(common).all()
        and np.isfinite(point).all()
        and np.isfinite(midplane).all()
        and math.isfinite(relative_change)
        and relative_change <= SOLVER_TOLERANCE
        and not intersects_wall
        and not is_limited
        and topology != "UNQUALIFIED"
    )
    return {
        "axis_rz_m": np.asarray(axis_rz, dtype=np.float64),
        "midplane_r_m": midplane,
        "psi_normalized": common,
        "relative_change": relative_change,
        "runtime_s": runtime_s,
        "topology_code": topology,
        "valid": valid,
        "xpoint_flux_mismatch": mismatch,
        "xpoint_rz_m": point,
    }
