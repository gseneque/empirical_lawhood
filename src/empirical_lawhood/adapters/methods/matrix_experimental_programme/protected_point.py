# SPDX-License-Identifier: MPL-2.0
"""Frozen same-information comparator points on the actual prepared feature.

Supported fitted method records retain their original identities and standing.
No fit, calibration, transfer applicability or scientific qualification occurs.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_methods import MatrixE3ModelSet
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_joint_v2 import points
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import MatrixResponseErrorModel, MatrixResponseErrorPredictionSpec, _validate_model
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import predict_standardized_ridge

from .prepared_point import MatrixPreparedPointFeature, MatrixPreparedPointSeal
from .records import MatrixFrozenConsumerPackage


@dataclass(frozen=True, slots=True)
class MatrixPreparedComparatorMethod(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-comparator-method"
    record_id: str
    package: ObjectIdentity
    upstream_freeze: ObjectIdentity
    model_record: MatrixResponseErrorModel | MatrixE3ModelSet
    method_key: str
    training_spec: ObjectIdentity
    training_unit_ids: tuple[str, ...]
    preprocessing: ObjectIdentity
    original_training_record: MatrixResponseErrorPredictionSpec | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.package) is not ObjectIdentity or self.package.object_schema != MatrixFrozenConsumerPackage.SCHEMA
                or type(self.upstream_freeze) is not ObjectIdentity or type(self.training_spec) is not ObjectIdentity
                or type(self.preprocessing) is not ObjectIdentity
                or type(self.model_record) not in (MatrixResponseErrorModel, MatrixE3ModelSet)
                or type(self.training_unit_ids) is not tuple or not self.training_unit_ids
                or self.training_unit_ids != tuple(sorted(set(self.training_unit_ids)))):
            raise TypeError("prepared comparator requires exact original package/model/training/preprocessing owners")
        self.model_record.__post_init__()
        for value in self.training_unit_ids:
            validate_stable_id(value)
        if type(self.model_record) is MatrixResponseErrorModel:
            if type(self.original_training_record) is not MatrixResponseErrorPredictionSpec:
                raise TypeError("old comparator requires its actual original root-to-whole-group training record")
            self.original_training_record.__post_init__()
            _validate_model(self.original_training_record, self.model_record)
            groups = tuple(sorted({row[1] for row in self.original_training_record.roles.rows if row[3] == "TRAIN"}))
            if (self.method_key != self.model_record.method or self.training_spec != self.model_record.spec
                    or self.training_unit_ids != groups):
                raise ValueError("prepared comparator changes its actual original fitted method or training specification")
        elif (self.original_training_record is not None or self.training_spec != self.model_record.specification
                or self.method_key not in tuple(row.method_key for row in self.model_record.models)
                or next(row for row in self.model_record.models if row.method_key == self.method_key).training_unit_ids != self.training_unit_ids):
            raise ValueError("prepared comparator changes its exact original fitted method/training-unit census")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def model(self):
        return ObjectIdentity.from_record(self.model_record.record_id, self.model_record)

    def validate_package(self, package):
        if type(package) is not MatrixFrozenConsumerPackage:
            raise TypeError("prepared comparator requires its exact frozen package owner")
        self.__post_init__()
        package.__post_init__()
        if (self.package != package.identity or self.model != package.component("comparator")
                or self.upstream_freeze != package.upstream_freeze or self.preprocessing != package.component("preprocessing")
                or not set(self.training_unit_ids) <= set(package.training_unit_ids)
                or type(self.model_record) is MatrixResponseErrorModel and self.model_record.reservation != package.reservation):
            raise ValueError("prepared comparator replaces the original package's frozen fitted/preprocessing/reservation scope")


def forecast_comparator(method, package, feature, *, record_id):
    """Same actual feature values/cutoff, with the selected immutable algorithm."""
    if type(method) is not MatrixPreparedComparatorMethod or type(feature) is not MatrixPreparedPointFeature:
        raise TypeError("prepared comparator forecast requires its exact fitted method and actual causal feature")
    method.validate_package(package)
    feature.__post_init__()
    if feature.independent_group_id in set(package.training_unit_ids) | set(package.selection_unit_ids):
        raise ValueError("protected comparator receives a known upstream fitted/calibrated/selected whole group")
    if type(method.model_record) is MatrixResponseErrorModel:
        # The original low-level point method accepts these exact model/training
        # identities. This new typed method is its actual caller, not an invented
        # original forecast design or substituted scientific ancestor.
        raw, cumulative = points(method, method.model_record, feature)
    else:
        model = next(row for row in method.model_record.models if row.method_key == method.method_key)
        raw = []
        for index in range(15):
            if feature.disposition != "AVAILABLE":
                value = None
            elif model.method_key == "RAW_TRAIN_MEDIAN":
                with localcontext() as context:
                    context.prec = 50
                    value = None if model.raw_constants[index] is None else (Decimal(1) + model.raw_constants[index]).ln()
            else:
                parameter = model.ridge_parameters[index]
                value = None if parameter is None else predict_standardized_ridge(parameter,
                    tuple(dict(feature.values)[name] for name in model.feature_names))
            raw.append(value)
        cumulative = []
        for start in range(0, 15, 3):
            prior, missing = Decimal(0), False
            for value in raw[start:start + 3]:
                missing = missing or value is None
                if missing:
                    cumulative.append(None)
                else:
                    prior = max(prior, value)
                    cumulative.append(prior)
        raw, cumulative = tuple(raw), tuple(cumulative)
    return MatrixPreparedPointSeal(record_id, feature, package.identity, method.model, package.component("criterion"),
        raw, cumulative, (None,) * 15, None)
