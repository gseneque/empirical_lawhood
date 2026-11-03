# SPDX-License-Identifier: MPL-2.0
"""Same actual feature and exact frozen baseline arithmetic; no fitting."""

from dataclasses import replace
from decimal import Decimal as D, localcontext

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.protected_point import MatrixPreparedComparatorMethod, forecast_comparator
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import MatrixE3EstimatorModel, MatrixE3ModelSet, METHODS
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.serialization import CanonicalRecord
from tests.test_matrix_later_programme import ref
from tests import test_matrix_prepared_functional as fixture


endpoint = fixture.endpoint


def selected(endpoint, *, method_key="RAW_TRAIN_MEDIAN"):
    feature = endpoint[-1].point.feature
    training = ("group.original-training",)
    models = tuple(MatrixE3EstimatorModel(method, () if method == "RAW_TRAIN_MEDIAN" else ("bath-temperature",),
        (None,) * 15, (D(".5"),) * 15 if method == "RAW_TRAIN_MEDIAN" else (None,) * 15,
        training, (1 if method == "RAW_TRAIN_MEDIAN" else 0,) * 15) for method in METHODS)
    fitted = MatrixE3ModelSet("models.literal-protected-comparator", ref("spec.literal-comparator", "empirical-lawhood/matrix-response-experiment/specification"),
        ref("allocation.literal-comparator", UnitAllocation.SCHEMA),
        ref("features.literal-comparator", "empirical-lawhood/matrix-response-experiment/feature-bank"),
        ref("outcomes.literal-comparator", "empirical-lawhood/matrix-response-experiment/outcome-bank"), models)
    package = endpoint[1]
    package = replace(package, components=tuple((role, ObjectIdentity.from_record(fitted.record_id, fitted) if role == "comparator" else value)
        for role, value in package.components))
    method = MatrixPreparedComparatorMethod("method.literal-protected-comparator", package.identity, package.upstream_freeze,
        fitted, method_key, fitted.specification, training, package.component("preprocessing"))
    return method, package, feature


def test_original_raw_train_median_is_log_transformed_and_sealed_on_identical_feature(endpoint):
    method, package, feature = selected(endpoint)
    result = forecast_comparator(method, package, feature, record_id="point.literal-protected-comparator")
    assert result.feature is feature and result.model == package.component("comparator")
    assert result.log_error_uppers == (None,) * 15 and result.radius is None
    with localcontext() as context:
        context.prec = 50
        assert result.raw_log_error_points == result.log_error_points == ((D(1) + D(".5")).ln(),) * 15
    assert isinstance(result, CanonicalRecord)


def test_missing_fitted_comparator_endpoint_and_missing_feature_remain_unavailable(endpoint):
    method, package, feature = selected(endpoint, method_key="ALL_ORIGIN_RIDGE")
    result = forecast_comparator(method, package, feature, record_id="point.literal-unavailable-comparator")
    assert result.raw_log_error_points == result.log_error_points == (None,) * 15
    method, package, feature = selected(endpoint)
    unavailable = replace(feature, disposition="UNAVAILABLE", values=())
    result = forecast_comparator(method, package, unavailable, record_id="point.literal-unavailable-feature")
    assert result.raw_log_error_points == result.log_error_points == (None,) * 15


@pytest.mark.parametrize("damage", ("model", "preprocessing", "freeze", "method", "training-use"))
def test_comparator_refuses_changed_package_method_or_known_upstream_group(endpoint, damage):
    method, package, feature = selected(endpoint)
    with pytest.raises(ValueError):
        if damage == "model":
            package = replace(package, components=tuple((role, ref("model.foreign-comparator") if role == "comparator" else value) for role, value in package.components))
        elif damage == "preprocessing":
            method = replace(method, preprocessing=ref("preprocessing.foreign-comparator"))
        elif damage == "freeze":
            method = replace(method, upstream_freeze=ref("freeze.foreign-comparator"))
        elif damage == "method":
            method = replace(method, method_key="UNDECLARED_METHOD")
        else:
            feature = replace(feature, independent_group_id=method.training_unit_ids[0])
        forecast_comparator(method, package, feature, record_id="point.refused-comparator")
