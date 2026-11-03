# SPDX-License-Identifier: MPL-2.0
"""Exact configured-product consumers over disclosed arithmetic fixtures.

These controls establish typed dispatch and original-byte preservation, never
native acquisition, freshness, source qualification or scientific authority.
"""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import (
    MatrixSelectedFrozenPackage, predict_selected_points, validate_selected_package_calibration,
)
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import statistical_task_id
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from tests.test_matrix_configured_protected_e3 import actual_join, causal, paired_outcome
from tests.test_matrix_configured_protected_statistical import _native_bank_context, case as configured_statistical_case
from tests.test_matrix_e3_original_publications import case as original_case  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import publish
from tests.test_matrix_selected_package import package as legacy_package


ROOT = Path(__file__).resolve().parents[1]


def configured_package(original_case, *, return_context=False):  # noqa: F811
    """Reusable exact configured producer fixture; no original V1 record casts."""
    native_case = _native_bank_context(configured_statistical_case.__wrapped__(original_case), "configured-selected")
    inputs, allocation = native_case.inputs, native_case.allocation
    joined, _ = actual_join(native_case, inputs, allocation)
    def task(operation, mode="", root=None):
        return "result." + statistical_task_id(inputs.specification.identity, allocation.identity,
            operation, mode=mode, root=root)
    joined = replace(joined, record_id=task("fit") + ".prefit-join")
    features, outcomes = native_case.train_features, native_case.train_outcomes
    models = science.fit_protected_e3_models(inputs, joined, features, outcomes, record_id=task("fit"))
    frozen = science.freeze_protected_e3(inputs.specification, allocation, models, record_id=task("freeze", "model"))
    forecasts = []
    for unit in allocation.unit_ids("calibration"):
        source, feature = causal(original_case, unit)
        forecasts.append(science.forecast_protected_e3(inputs.specification, allocation, models, frozen,
            feature, role="calibration", record_id=task("forecast", "calibration", source.root.root)))
    forecasts = tuple(forecasts)
    calibration = science.calibrate_protected_e3(inputs.specification, allocation, models, frozen, forecasts,
        tuple(paired_outcome(forecast) for forecast in forecasts), record_id=task("calibrate"))
    calibrated = science.freeze_protected_e3(inputs.specification, allocation, models,
        record_id=task("freeze", "calibration"), model_freeze=frozen, calibration=calibration)
    package = ConfiguredMatrixSelectedFrozenPackage("package.configured-selected.control", inputs.specification,
        allocation, joined, models, frozen, calibration, calibrated,
        tuple(sorted((*allocation.unit_ids("calibration"), *allocation.unit_ids("evaluation")))))
    return (package, native_case) if return_context else package


def test_configured_selected_package_preserves_exact_fitted_records_and_bounded_public_projection(original_case):  # noqa: F811
    full = configured_package(original_case)
    public = ConfiguredMatrixSelectedPublicPackage.from_package(full)
    assert public.models is full.models and public.prefit is full.prefit
    assert public.calibration == science.identity(full.calibration)
    assert public.original_package == full.identity
    assert full.models.training_features.object_schema.endswith("/native-training-feature-bank")
    assert full.models.training_outcomes.object_schema.endswith("/native-training-outcome-bank")
    values = original_case.train_features.rows[0].values
    assert public.predict(values=values, disposition="AVAILABLE") == predict_selected_points(full, values=values)
    for record in (full, public):
        assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    assert b'"scores"' not in public.canonical_bytes()
    old = legacy_package()
    original_bytes = old.canonical_bytes()
    assert decode_canonical_bytes(original_bytes, MatrixSelectedFrozenPackage, maximum_bytes=None).canonical_bytes() == original_bytes
    with pytest.raises(TypeError):
        replace(full, models=old.models)
    with pytest.raises(ValueError):
        replace(public, original_package=old.identity)
    with pytest.raises(ValueError, match="record families"):
        validate_selected_package_calibration(full.identity, science.identity(old.calibration))
    with pytest.raises(ValueError, match="record families"):
        validate_selected_package_calibration(old.identity, science.identity(full.calibration))


def test_configured_selected_package_enters_existing_e4_forecast_contract_without_v1_relabel(original_case):  # noqa: F811
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4ForecastDesign
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4OriginalCalibrationSummary

    full = configured_package(original_case)
    public = ConfiguredMatrixSelectedPublicPackage.from_package(full)
    document = json.loads((ROOT / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate/candidate-design02.json").read_bytes())
    criterion = decode_canonical_record(document["target"]["original_mathematical_protocol"], MatrixResponseFrontierProtocol)
    publication = publish(original_case.plane, criterion, "configured-selected.e4-criterion")
    design = SelectedE3E4ForecastDesign("design.configured-selected.e4", public,
        identity(original_case.inputs.reservation.allocation), criterion, publication)
    assert type(design.package) is ConfiguredMatrixSelectedPublicPackage
    assert design.package.models == full.models and design.package.specification == full.specification
    from empirical_lawhood.api.matrix_training_provenance import original_comparator_training
    provenance = original_comparator_training(design.package)
    assert provenance["bank_edition"] == "NATIVE_BANKS"
    assert provenance["original_package"] == full.identity.to_document()
    assert provenance["model_set"] == science.identity(full.models).to_document()
    assert provenance["feature_bank"] == full.models.training_features.to_document()
    assert provenance["units"] == list(full.allocation.unit_ids("train"))
    old = legacy_package()
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
    legacy = original_comparator_training(MatrixSelectedPublicPackage.from_package(old))
    assert legacy["bank_edition"] == "LEGACY_BANKS"
    assert legacy["data_origin"] == "NOT_REESTABLISHED_BY_THIS_READ"
    with pytest.raises((ValueError, PermissionError)):
        original_comparator_training(replace(design.package, models=replace(full.models, record_id=full.models.record_id + ".foreign")))
    assert decode_canonical_bytes(design.canonical_bytes(), type(design), maximum_bytes=None) == design
    summary = SelectedE4OriginalCalibrationSummary.from_package(full, record_id="summary.configured-selected.e4")
    assert summary.original_package == full.identity and summary.calibration == science.identity(full.calibration)
    assert summary.rank == full.calibration.rank and summary.radius == full.calibration.radius
