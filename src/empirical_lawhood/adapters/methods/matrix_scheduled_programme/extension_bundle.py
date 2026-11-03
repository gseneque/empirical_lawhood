# SPDX-License-Identifier: MPL-2.0
"""Separate bounded discovery contribution; no source inspection or effects."""

from hashlib import sha256

from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.runtime.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.runtime.experiment_preparation import ExperimentProtocolDeclaration
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_global import operation_factories as global_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_bindings import operation_manifests as wave_manifests
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_calibration_bindings import calibration_manifests
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_confirmation import operation_factories as confirmation_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_acquisition_bindings import operation_manifests as acquisition_manifests
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_tail_freeze import operation_factories as tail_freeze_factories
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import operation_manifests as selection_manifests
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import operation_manifests as factorial_manifests
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation import operation_manifests as factorial_confirmation_manifests
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_forecast_bindings import operation_manifests as revision_forecast_manifests
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_future_bindings import operation_manifests as revision_future_manifests
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibration_bindings import operation_declarations as revision_calibration_declarations
from empirical_lawhood.adapters.methods.matrix_scheduled_history.revision_calibrated_future_bindings import operation_manifests as calibrated_revision_future_manifests
from empirical_lawhood.adapters.methods.matrix_sampling_bindings import sampling_declaration
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial import ScheduledFactorialSpecification
from empirical_lawhood.adapters.methods.matrix_scheduled_history.factorial_preparation import (
    PROTOCOL_ID as FACTORIAL_PROTOCOL_ID, bind_factorial_inputs, prepare_factorial_experiment,
    validate_factorial_experiment_instance,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selection_specification import ScheduledRevisionExperimentSpecification
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selection_preparation import (
    INPUT_TYPES, PROTOCOL_ID, bind_selection_inputs, prepare_selection_experiment,
    validate_selection_experiment_instance,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import NAMESPACE
from empirical_lawhood.adapters.methods.matrix_scheduled_history.compact_records import ScheduledCompactBank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_reduction import ScheduledProgrammeReduction
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_selection import ScheduledRevisionDataBank
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_specification import (
    PROTOCOL_ID as PROTECTED_FACTORIAL_PROTOCOL_ID, ProtectedFactorialExperimentSpecification,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import (
    bind_protected_factorial_experiment_inputs, input_record_types as protected_input_record_types,
    prepare_protected_factorial_experiment, validate_protected_factorial_experiment_instance,
)

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_bindings import (
    operation_declarations as selected_e3_e4_declarations,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import (
    protocol_declaration as selected_e3_e4_protocol_declaration,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_bindings import (
    ScheduledFullFactorReduceConfig, operation_declarations as full_factor_declarations,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_preparation import (
    protocol_declarations as full_factor_protocol_declarations,
)


from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_method_bindings import (
    operation_declarations as selected_e4_method_declarations,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_bindings import (
    SelectedE4ProtectedEntryConfig, SelectedE4PhaseCollectConfig,
    operation_declarations as selected_e4_native_declarations,
)

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_revision_preparation import (
    protocol_declaration as selected_e4_revision_protocol_declaration,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_revision_transition import (
    protocol_declaration as selected_e4_revision_transition_protocol_declaration,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_declarative import (
    protocol_declaration as selected_e4_declarative_protocol_declaration,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_preparation import (
    protocol_declarations as selected_e4_native_protocol_declarations,
)

MANIFESTS = tuple(sorted((*(f.manifest for f in global_factories()), *wave_manifests(), *calibration_manifests(),
    *(f.manifest for f in confirmation_factories()), *acquisition_manifests(), *(f.manifest for f in tail_freeze_factories()),
    *selection_manifests(), *factorial_manifests(), *factorial_confirmation_manifests(),
    *revision_forecast_manifests(), *revision_future_manifests(), *(row.manifest() for row in revision_calibration_declarations()),
    *calibrated_revision_future_manifests(), *(row.manifest() for row in selected_e3_e4_declarations()),
    *(row.manifest() for row in selected_e4_method_declarations()),
    *(row.manifest() for row in selected_e4_native_declarations()),
    *(row.manifest() for row in full_factor_declarations()),
    sampling_declaration("E4").manifest()), key=lambda m: m.registry_id))
# Stateless recursive bindings own their actual provider descriptors directly.
# They have no discovery components or independent objective profiles.
# The complete E4 entry and phase collector retain the predeclared scientific root. Their
# existing prospective decoder/member and selected resource bounds own size;
# the smaller legacy leaf allocation must not truncate that full denominator.
_REGISTRATIONS = tuple(CandidateCapabilityRegistration(m, 'recursive.provider.'+m.capability_key,
    '1.0.0', 'application/json', None if m.config_schema in
        (SelectedE4ProtectedEntryConfig.SCHEMA, SelectedE4PhaseCollectConfig.SCHEMA,
            ScheduledFullFactorReduceConfig.SCHEMA) else 4*1024**2) for m in MANIFESTS)
_WORKFLOW_PROFILE = ExtensionProfileRegistration('profile-registration.'+NAMESPACE+'.workflow',
    NAMESPACE+'.workflow', '1.0.0', ExtensionProfileKind.OBJECTIVE_TERMINAL,
    ExperimentObjectiveProfile.SCHEMA, sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(m.fingerprint() for m in MANIFESTS))).hexdigest())
EXTENSION_BUNDLE_CONTRIBUTION = ExtensionBundleContribution('method.'+NAMESPACE, '1.0.0', ExtensionContributionKind.METHOD,
    (), MANIFESTS, _REGISTRATIONS, (), (_WORKFLOW_PROFILE,), (), (), (), (), (), False, False)

EXPERIMENT_PROTOCOL_DECLARATIONS = (*full_factor_protocol_declarations(), selected_e3_e4_protocol_declaration(),
    selected_e4_revision_protocol_declaration(), selected_e4_revision_transition_protocol_declaration(),
    selected_e4_declarative_protocol_declaration(), *selected_e4_native_protocol_declarations(), ExperimentProtocolDeclaration(
    PROTOCOL_ID, ScheduledRevisionExperimentSpecification, prepare_selection_experiment,
    "matrix-e4-declared-selection", input_record_types=tuple(INPUT_TYPES.values()),
    bind_inputs=bind_selection_inputs, validate_instance=validate_selection_experiment_instance),
    ExperimentProtocolDeclaration(FACTORIAL_PROTOCOL_ID, ScheduledFactorialSpecification,
        prepare_factorial_experiment, "matrix-e4-factorial", input_record_types=tuple(INPUT_TYPES.values()),
        bind_inputs=bind_factorial_inputs, validate_instance=validate_factorial_experiment_instance),
    ExperimentProtocolDeclaration(PROTECTED_FACTORIAL_PROTOCOL_ID, ProtectedFactorialExperimentSpecification,
        prepare_protected_factorial_experiment, "matrix-e4-protected-factorial",
        input_record_types=protected_input_record_types(), bind_inputs=bind_protected_factorial_experiment_inputs,
        validate_instance=validate_protected_factorial_experiment_instance,
        requires_prospective_runtime_binding=True,
        input_file_record_types=tuple(sorted((ScheduledCompactBank, ScheduledProgrammeReduction, ScheduledRevisionDataBank),
            key=lambda kind: (kind.SCHEMA, kind.VERSION)))))
