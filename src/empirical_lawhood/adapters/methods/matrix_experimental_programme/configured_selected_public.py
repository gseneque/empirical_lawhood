# SPDX-License-Identifier: MPL-2.0
"""Configured E3 seedless projection retaining exact producer record types."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import ConfiguredProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from .configured_selected_package import ConfiguredMatrixSelectedFrozenPackage


@dataclass(frozen=True, slots=True)
class ConfiguredMatrixSelectedPublicPackage(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/configured-selected-public-package"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    original_package: ObjectIdentity
    specification: ConfiguredProtectedE3Specification
    allocation: UnitAllocation
    prefit: ConfiguredProtectedE3PreFitJoin
    models: e3.ConfiguredProtectedE3ModelSet
    model_freeze: e3.ConfiguredProtectedE3FrozenProducts
    calibration: ObjectIdentity
    calibrated_freeze: e3.ConfiguredProtectedE3FrozenProducts
    selection_unit_ids: tuple[str, ...]

    def __post_init__(self):
        from .selected_public import MatrixSelectedPublicPackage
        MatrixSelectedPublicPackage._validate(self, (ConfiguredProtectedE3Specification, UnitAllocation,
            ConfiguredProtectedE3PreFitJoin, e3.ConfiguredProtectedE3ModelSet, e3.ConfiguredProtectedE3FrozenProducts,
            e3.ConfiguredProtectedE3FrozenProducts), ConfiguredMatrixSelectedFrozenPackage,
            e3.ConfiguredProtectedE3Calibration, e3.freeze_protected_e3)

    @classmethod
    def from_package(cls, package):
        if type(package) is not ConfiguredMatrixSelectedFrozenPackage:
            raise TypeError("configured public package requires exact configured original products")
        package.__post_init__()
        return cls("public." + package.record_id, package.identity, package.specification, package.allocation, package.prefit,
            package.models, package.model_freeze, ObjectIdentity.from_record(package.calibration.record_id, package.calibration),
            package.calibrated_freeze, package.selection_unit_ids)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @property
    def training_unit_ids(self):
        return self.allocation.unit_ids("train")

    def require_unused_groups(self, groups):
        from .selected_public import MatrixSelectedPublicPackage
        return MatrixSelectedPublicPackage.require_unused_groups(self, groups)

    def require_reserved_transfer_groups(self, groups, *, reservation):
        from .selected_public import MatrixSelectedPublicPackage
        return MatrixSelectedPublicPackage.require_reserved_transfer_groups(self, groups, reservation=reservation)

    def predict(self, *, values, disposition):
        from .selected_public import MatrixSelectedPublicPackage
        return MatrixSelectedPublicPackage.predict(self, values=values, disposition=disposition)
