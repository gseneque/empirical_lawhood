# SPDX-License-Identifier: MPL-2.0
"""Bounded programme providers beside the unchanged scheduled v1/v2 owners."""

from empirical_lawhood.runtime.executable_bindings import ExecutableBindingContribution
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_global import operation_factories as global_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_bindings import operation_factories as wave_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_calibration_bindings import calibration_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_confirmation import operation_factories as confirmation_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_bindings import operation_factories as acquisition_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_tail_freeze import operation_factories as tail_freeze_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import operation_factories as selection_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import operation_factories as factorial_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation import operation_factories as factorial_confirmation_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_forecast_bindings import operation_factories as revision_forecast_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_future_bindings import operation_factories as revision_future_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration_bindings import operation_factories as revision_calibration_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibrated_future_bindings import operation_factories as calibrated_revision_future_factories
from empirical_lawhood.adapters.methods.matrix_sampling_bindings import sampling_declaration
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import NAMESPACE

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_bindings import (
    operation_declarations as selected_e3_e4_declarations,
)


from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_method_bindings import (
    operation_declarations as selected_e4_method_declarations,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_bindings import (
    operation_declarations as selected_e4_native_declarations,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_bindings import (
    operation_declarations as full_factor_declarations,
)

EXECUTABLE_BINDING_FACTORIES = tuple(sorted((*global_factories(), *wave_factories(), *calibration_factories(),
    *confirmation_factories(), *acquisition_factories(), *tail_freeze_factories(), *selection_factories(), *factorial_factories(),
    *factorial_confirmation_factories(), *revision_forecast_factories(), *revision_future_factories(),
    *revision_calibration_factories(), *calibrated_revision_future_factories(),
    *(row.provider_factory() for row in selected_e3_e4_declarations()),
    *(row.provider_factory() for row in selected_e4_method_declarations()),
    *(row.provider_factory() for row in selected_e4_native_declarations()),
    *(row.provider_factory() for row in full_factor_declarations()),
    sampling_declaration("E4").provider_factory()), key=lambda f: f.binding.binding_id))
EXECUTABLE_BINDING_CONTRIBUTION = ExecutableBindingContribution('executable-contribution.'+NAMESPACE, '1.0.0',
    tuple(f.binding for f in EXECUTABLE_BINDING_FACTORIES))
EXECUTABLE_RECORD_TYPES = ()
