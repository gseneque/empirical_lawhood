# SPDX-License-Identifier: MPL-2.0
"""Exact configured E3 products for selected downstream consumers."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import ConfiguredProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from .selected_package import MatrixSelectedFrozenPackage


@dataclass(frozen=True, slots=True)
class ConfiguredMatrixSelectedFrozenPackage(MatrixSelectedFrozenPackage):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/configured-selected-e3-frozen-package"
    VERSION: ClassVar[str] = '2.0.0'
    specification: ConfiguredProtectedE3Specification
    prefit: ConfiguredProtectedE3PreFitJoin
    models: e3.ConfiguredProtectedE3ModelSet
    model_freeze: e3.ConfiguredProtectedE3FrozenProducts
    calibration: e3.ConfiguredProtectedE3Calibration
    calibrated_freeze: e3.ConfiguredProtectedE3FrozenProducts

    def __post_init__(self):
        self._validate((ConfiguredProtectedE3Specification, UnitAllocation, ConfiguredProtectedE3PreFitJoin,
            e3.ConfiguredProtectedE3ModelSet, e3.ConfiguredProtectedE3FrozenProducts,
            e3.ConfiguredProtectedE3Calibration, e3.ConfiguredProtectedE3FrozenProducts), e3.freeze_protected_e3)
