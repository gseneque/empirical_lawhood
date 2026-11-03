# SPDX-License-Identifier: MPL-2.0
"""Select exact original E3 record owners without converting scientific records."""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class SelectedE3ProductFamily:
    namespace: str
    configured: bool
    operation_declarations: Callable
    statistical_task_id: Callable
    package_type: type
    public_type: type
    calibration_type: type
    preparation_type: type
    projection_type: type
    numerical_type: type
    selected_protocol: Callable


def selected_e3_product_family(specification):
    """An edition is selected by its actual typed scientific specification."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification

    if type(specification) is MatrixResponseErrorSpecification:
        from empirical_lawhood.adapters.methods.matrix_factor_response import protected_composition as composition
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import statistical_task_id
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_methods import ProtectedE3Calibration
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3PreparationSelection
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_protocol import ProtectedE3ProtocolProjection
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_response_records import ProtectedE3ResponseNumericalProfile, _selected_protocol
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import MatrixSelectedFrozenPackage
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
        return SelectedE3ProductFamily("matrix-e3-protected", False, composition.operation_declarations,
            statistical_task_id, MatrixSelectedFrozenPackage, MatrixSelectedPublicPackage,
            ProtectedE3Calibration, ProtectedE3PreparationSelection, ProtectedE3ProtocolProjection,
            ProtectedE3ResponseNumericalProfile, _selected_protocol)
    if type(specification) is ConfiguredProtectedE3Specification:
        from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_composition as composition
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_tasks import statistical_task_id
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3Calibration
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_protocol import ConfiguredProtectedE3ProtocolProjection
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import ConfiguredProtectedE3ResponseNumericalProfile, _selected_protocol
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
        return SelectedE3ProductFamily("matrix-e3-configured-protected", True, composition.operation_declarations,
            statistical_task_id, ConfiguredMatrixSelectedFrozenPackage, ConfiguredMatrixSelectedPublicPackage,
            ConfiguredProtectedE3Calibration, ConfiguredProtectedE3PreparationSelection,
            ConfiguredProtectedE3ProtocolProjection, ConfiguredProtectedE3ResponseNumericalProfile, _selected_protocol)
    raise TypeError("selected original E3 requires an exact supported scientific specification edition")
