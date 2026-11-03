"""Current adapter; numerical owners load only when their exports are selected."""

from importlib import import_module

_EXPORTS = {
    "CompiledPrediction": (".analysis", "CompiledPrediction"),
    "EmpiricalReplaySpec": (".contracts", "EmpiricalReplaySpec"),
    "H5ADStructuralInspection": (".dataset", "H5ADStructuralInspection"),
    "LinearResponseModel": (".analysis", "LinearResponseModel"),
    "MetricContract": (".contracts", "MetricContract"),
    "ModelFamily": (".analysis", "ModelFamily"),
    "PredictionCommitment": (".contracts", "PredictionCommitment"),
    "ResponseSummaryArrays": (".dataset", "ResponseSummaryArrays"),
    "SegmentedBinaryReader": (".dataset", "SegmentedBinaryReader"),
    "TargetFeatureMatrix": (".analysis", "TargetFeatureMatrix"),
    "TargetResponseMatrix": (".analysis", "TargetResponseMatrix"),
    "TaskTranslation2026": (".contracts", "TaskTranslation2026"),
    "VirtualCellDenominator": (".contracts", "VirtualCellDenominator"),
    "ProvenanceBoundVirtualCellPipelineConfig": (
        ".contracts",
        "ProvenanceBoundVirtualCellPipelineConfig",
    ),
    "VirtualCellSourceManifest": (".contracts", "VirtualCellSourceManifest"),
    "adjudicate_placement": (".analysis", "adjudicate_placement"),
    "adjudicate_official_final_top100": (
        ".leaderboard",
        "adjudicate_official_final_top100",
    ),
    "compile_prediction_cells": (".analysis", "compile_prediction_cells"),
    "decode_official_final_top100": (".leaderboard", "decode_official_final_top100"),
    "fit_tier_l0_model": (".analysis", "fit_tier_l0_model"),
    "inspect_h5ad": (".dataset", "inspect_h5ad"),
    "official_aggregate_score": (".analysis", "official_aggregate_score"),
    "predict_response": (".analysis", "predict_response"),
    "summarize_h5ad": (".dataset", "summarize_h5ad"),
}

__all__ = [
    "CompiledPrediction",
    "EmpiricalReplaySpec",
    "H5ADStructuralInspection",
    "LinearResponseModel",
    "MetricContract",
    "ModelFamily",
    "PredictionCommitment",
    "ResponseSummaryArrays",
    "SegmentedBinaryReader",
    "TargetFeatureMatrix",
    "TargetResponseMatrix",
    "TaskTranslation2026",
    "VirtualCellDenominator",
    "ProvenanceBoundVirtualCellPipelineConfig",
    "VirtualCellSourceManifest",
    "adjudicate_placement",
    "adjudicate_official_final_top100",
    "compile_prediction_cells",
    "decode_official_final_top100",
    "fit_tier_l0_model",
    "inspect_h5ad",
    "official_aggregate_score",
    "predict_response",
    "summarize_h5ad",
]


def __getattr__(name):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value
