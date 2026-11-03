# SPDX-License-Identifier: MPL-2.0
"""Seedless selected predictor projections without original CAL score banks.

The original package is authenticated and recomputed by the parent supplier.
These projections retain its exact models and original calibration identity;
constructing them grants neither custody nor downstream applicability.
"""

from dataclasses import dataclass
from types import SimpleNamespace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import ProtectedE3PreFitJoin
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .preparation_records import MatrixCouplingRecipe, MatrixOriginalScheduleRecipe
from .prepared_point import MatrixPreparedPublicSource, MatrixPreparedRecipeInterpretation
from .prepared_prefix import identity
from .records import MatrixFunctionalCriterion
from .science import MatrixPreparationNomination
from .selected_package import MatrixSelectedFrozenPackage, predict_selected_points, selected_frozen_package_types
from .configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from .selected_point import MatrixSelectedPointDesign


@dataclass(frozen=True, slots=True)
class MatrixSelectedPublicPackage(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-public-package"
    record_id: str
    original_package: ObjectIdentity
    specification: MatrixResponseErrorSpecification
    allocation: UnitAllocation
    prefit: ProtectedE3PreFitJoin
    models: e3.ProtectedE3ModelSet
    model_freeze: e3.ProtectedE3FrozenProducts
    calibration: ObjectIdentity
    calibrated_freeze: e3.ProtectedE3FrozenProducts
    selection_unit_ids: tuple[str, ...]

    def __post_init__(self):
        self._validate((MatrixResponseErrorSpecification, UnitAllocation, ProtectedE3PreFitJoin, e3.ProtectedE3ModelSet,
            e3.ProtectedE3FrozenProducts, e3.ProtectedE3FrozenProducts), MatrixSelectedFrozenPackage,
            e3.ProtectedE3Calibration, e3.freeze_protected_e3)

    def _validate(self, record_types, package_type, calibration_type, freeze):
        validate_stable_id(self.record_id)
        for value, kind in zip((self.specification, self.allocation, self.prefit, self.models,
                self.model_freeze, self.calibrated_freeze), record_types, strict=True):
            if type(value) is not kind:
                raise TypeError("selected public package requires exact original frozen model owners")
            value.__post_init__()
        if (type(self.original_package) is not ObjectIdentity or (self.original_package.object_schema, self.original_package.object_version) != (package_type.SCHEMA, package_type.VERSION)
                or type(self.calibration) is not ObjectIdentity or (self.calibration.object_schema, self.calibration.object_version) != (calibration_type.SCHEMA, calibration_type.VERSION)
                or self.selection_unit_ids != tuple(sorted(set(self.selection_unit_ids)))
                or (self.models.specification, self.models.allocation, self.models.reservation_join) !=
                    (self.specification.identity, self.allocation.identity, self.prefit.identity)
                or self.model_freeze != freeze(self.specification, self.allocation, self.models, record_id=self.model_freeze.record_id)
                or self.calibrated_freeze.calibration != self.calibration
                or self.calibrated_freeze.model_freeze != identity(self.model_freeze)
                or self.calibrated_freeze.models != identity(self.models)):
            raise ValueError("selected public package substitutes original model/freeze/calibration ancestry")
        known = {*self.allocation.unit_ids("calibration"), *self.allocation.unit_ids("evaluation")}
        if not known <= set(self.selection_unit_ids):
            raise ValueError("selected public package omits original calibration/confirmation whole-group use")

    @classmethod
    def from_package(cls, package):
        if type(package) is not MatrixSelectedFrozenPackage:
            raise TypeError("selected public package projects its actual validated full original package")
        package.__post_init__()
        return cls("public." + package.record_id, package.identity, package.specification, package.allocation, package.prefit,
            package.models, package.model_freeze, identity(package.calibration), package.calibrated_freeze, package.selection_unit_ids)

    @property
    def identity(self):
        return identity(self)

    @property
    def training_unit_ids(self):
        return self.allocation.unit_ids("train")

    def require_unused_groups(self, groups):
        if (type(groups) is not tuple or groups != tuple(sorted(set(groups)))
                or set(groups).intersection((*self.training_unit_ids, *self.selection_unit_ids))):
            raise ValueError("selected public consumer reuses an original upstream whole group")

    def require_reserved_transfer_groups(self, groups, *, reservation):
        self.require_unused_groups(groups)
        reserved = tuple(sorted((*self.allocation.unit_ids("transfer_nearby"), *self.allocation.unit_ids("transfer_shifted"))))
        if reservation != self.prefit.reservation or groups != reserved:
            raise ValueError("selected public transfer changes the complete original pre-fit reserve")

    def predict(self, *, values, disposition):
        # The original numerical helper only reads specification and models;
        # the public adapter never fabricates an old full calibration record.
        from empirical_lawhood.adapters.methods.matrix_factor_response.e3_numerical_methods import forecast_point_values
        from .selected_package import validate_selected_features
        validate_selected_features(self.specification, values, disposition)
        return forecast_point_values(self.models.models, SimpleNamespace(values=values, disposition=disposition))


@dataclass(frozen=True, slots=True)
class MatrixSelectedPointPayload(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-point-payload"
    record_id: str
    original_design: ObjectIdentity
    package: MatrixSelectedPublicPackage | ConfiguredMatrixSelectedPublicPackage
    phase: str
    expected_groups: int
    arms: tuple[tuple[str, MatrixCouplingRecipe | MatrixOriginalScheduleRecipe], ...]
    sources: tuple[tuple[str, MatrixPreparedPublicSource], ...]
    interpretations: tuple[MatrixPreparedRecipeInterpretation, ...]

    def __post_init__(self):
        if (type(self.original_design) is not ObjectIdentity or self.original_design.object_schema != MatrixSelectedPointDesign.SCHEMA
                or type(self.package) not in selected_public_package_types()):
            raise TypeError("selected point payload requires its exact original design and seedless frozen projection")
        MatrixSelectedPointDesign._validate(self, selected_public_package_types())

    @classmethod
    def from_design(cls, design):
        if type(design) is not MatrixSelectedPointDesign:
            raise TypeError("selected point payload projects its actual full validated design")
        design.__post_init__()
        return cls("public." + design.record_id, design.identity, public_package_from_frozen(design.package),
            design.phase, design.expected_groups, design.arms, design.sources, design.interpretations)

    @property
    def identity(self):
        return identity(self)

    def family(self, public):
        return MatrixSelectedPointDesign.family(self, public)


@dataclass(frozen=True, slots=True)
class MatrixSelectedNominationSelection(CanonicalRecord):
    """Published recipe decision without original opportunity outcome rows."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-nomination-selection"
    record_id: str
    original_nomination: ObjectIdentity
    package: ObjectIdentity
    disposition: str
    selected_arm_id: str
    selected_recipe: ObjectIdentity
    hold_recipe: ObjectIdentity
    functional_criterion: MatrixFunctionalCriterion
    development_unit_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.selected_arm_id)
        if (type(self.original_nomination) is not ObjectIdentity or self.original_nomination.object_schema != MatrixPreparationNomination.SCHEMA
                or (self.package.object_schema, self.package.object_version) not in tuple((kind.SCHEMA, kind.VERSION) for kind in selected_frozen_package_types()) or self.disposition != "NOMINATED"
                or type(self.selected_recipe) is not ObjectIdentity or type(self.hold_recipe) is not ObjectIdentity
                or type(self.functional_criterion) is not MatrixFunctionalCriterion
                or not self.development_unit_ids or self.development_unit_ids != tuple(sorted(set(self.development_unit_ids)))):
            raise ValueError("selected nomination projection changes original selected decision or development census")
        self.functional_criterion.__post_init__()

    @classmethod
    def from_nomination(cls, nomination):
        if type(nomination) is not MatrixPreparationNomination or nomination.disposition != "NOMINATED":
            raise TypeError("selected confirmation projects its exact original successful nomination")
        nomination.__post_init__()
        return cls("public." + nomination.result_id, nomination.identity, nomination.package, nomination.disposition,
            nomination.selected_arm_id, nomination.selected_recipe, nomination.hold_recipe, nomination.functional_criterion, nomination.development_unit_ids)

    @property
    def identity(self):
        return identity(self)


def package_identity(package):
    return package.original_package if type(package) in selected_public_package_types() else package.identity


def calibration_identity(package):
    return package.calibration if type(package) in selected_public_package_types() else identity(package.calibration)


def point_values(package, *, values, disposition):
    return package.predict(values=values, disposition=disposition) if type(package) in selected_public_package_types() else predict_selected_points(package, values=values, disposition=disposition)


def selected_public_package_types():
    return MatrixSelectedPublicPackage, ConfiguredMatrixSelectedPublicPackage


def public_package_from_frozen(package):
    if type(package) is MatrixSelectedFrozenPackage:
        return MatrixSelectedPublicPackage.from_package(package)
    return ConfiguredMatrixSelectedPublicPackage.from_package(package)
