# SPDX-License-Identifier: MPL-2.0
"""Explicit E3 source transition before the first future response.

These records describe custody adoption, never a replacement acquisition, fit,
freeze, source qualification or permission. The API authenticates the entire
original partial execution before publishing or consuming a transition.
"""
from empirical_lawhood.kernel.decoding import validate_record_fields
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import ExecutionPlan, ExecutionTask
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent

from .configured_protected_feature_bindings import ConfiguredProtectedE3FeatureConfig
from .configured_protected_methods import ConfiguredProtectedE3FrozenProducts
from .configured_protected_response_records import ConfiguredProtectedE3PhysicalForecastConfig
from .configured_protected_source_records import ConfiguredProtectedE3SourceConfig, NAMESPACE, _reference
from .configured_protected_specification import ConfiguredProtectedE3Specification
from .configured_protected_statistical_bindings import ConfiguredProtectedE3FitConfig, ConfiguredProtectedE3StatisticalConfig


# Continuation may repair metadata and custody joins. It cannot silently change
# the numerical owners or dependency lock used by the retained forecasts/fit.
NUMERICAL_OWNER_PREFIXES = (
    'adapters/simulators/',
    'adapters/methods/matrix_factor_response/e3_numerical_methods.py',
    'adapters/methods/matrix_factor_response/experiment_methods.py',
    'adapters/methods/matrix_factor_response/matched_response_fitting.py',
    'adapters/methods/matrix_factor_response/matched_response_prediction.py',
    'adapters/methods/matrix_factor_response/curve_',
    'adapters/methods/matrix_factor_response/configured_protected_methods.py',
    'adapters/methods/matrix_factor_response/configured_protected_feature_science.py',
    'adapters/methods/matrix_factor_response/protected_feature_science.py',
    'adapters/methods/matrix_scheduled_history/parameter_native.py',
    'adapters/methods/matrix_scheduled_history/response_native.py',
    'adapters/methods/matrix_scheduled_history/response_science.py',
    'adapters/methods/matrix_scheduled_history/response_forecast.py',
)
RETAINED_PHASES = ('check', 'feature', 'fit', 'forecast', 'measure', 'model-freeze',
    'numerical', 'physical-forecast', 'prefix', 'project')


def source_binding(provenance):
    if type(provenance) is not NumericalProducingProvenance:
        raise TypeError('retained E3 requires exact observed numerical provenance')
    validate_record_fields(provenance)
    return RecursiveImplementationBinding(provenance.package_sources, provenance.code_sources_sha256,
        provenance.dependency_lock_sha256, provenance.observed_git_head, provenance.observed_checkout_clean)


def require_numerical_source_continuity(original, current):
    """Compare actual source inventories without loading numerical providers."""
    for binding in (original, current):
        if type(binding) is not RecursiveImplementationBinding:
            raise TypeError('retained E3 requires exact original and continued source inventories')
        validate_record_fields(binding)
    if (original == current or original.observed_git_head == current.observed_git_head
            or original.dependency_lock_sha256 != current.dependency_lock_sha256):
        raise ValueError('retained E3 requires a distinct source with the original dependency lock')
    before, after = dict(original.package_sources), dict(current.package_sources)
    for prefix in NUMERICAL_OWNER_PREFIXES:
        old = {key: value for key, value in before.items() if key.startswith(prefix)}
        new = {key: value for key, value in after.items() if key.startswith(prefix)}
        if not old or old != new:
            raise ValueError('retained E3 changes or omits an original numerical owner: ' + prefix)


@dataclass(frozen=True, slots=True)
class ConfiguredE3RetainedExecution(CanonicalRecord):
    """One shared, original terminal/receipt/source census for a new execution."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-retained-execution'
    record_id: str
    original_authoring_directory: str
    original_run_id: str
    continued_run_id: str
    original_package: ObjectIdentity
    original_plan: ObjectIdentity
    original_terminal: ObjectIdentity
    original_reveal_authority: ObjectIdentity
    original_source: RecursiveImplementationBinding
    response_provenance: NumericalProducingProvenance
    specification: ObjectIdentity
    allocation: ObjectIdentity
    model_freeze: ObjectIdentity
    completed_receipts: tuple[tuple[str, ObjectIdentity], ...]
    retained_arrays: tuple[tuple[str, ArtifactIdentity], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_relative_locator(self.original_authoring_directory)
        validate_stable_id(self.original_run_id)
        validate_stable_id(self.continued_run_id)
        if self.original_run_id == self.continued_run_id:
            raise ValueError('retained E3 requires a separate continued run')
        for value, kind in ((self.original_plan, ExecutionPlan), (self.original_terminal, RunRecoveryTerminalEvent),
                (self.specification, ConfiguredProtectedE3Specification), (self.allocation, UnitAllocation),
                (self.model_freeze, ConfiguredProtectedE3FrozenProducts)):
            _reference(value, kind)
        if (type(self.original_package) is not ObjectIdentity or
                (self.original_package.object_schema, self.original_package.object_version) !=
                ('empirical-lawhood/api/experiment-package', '1.0.0')):
            raise ValueError('retained E3 requires its exact original issued package')
        validate_record_fields(self.original_package)
        if (type(self.original_reveal_authority) is not ObjectIdentity or
                (self.original_reveal_authority.object_schema, self.original_reveal_authority.object_version) !=
                ('empirical-lawhood/planning/study-operation-authority', '1.0.0')):
            raise ValueError('retained E3 requires its exact original reveal selection')
        validate_record_fields(self.original_reveal_authority)
        require_numerical_source_continuity(self.original_source, source_binding(self.response_provenance))
        rows = self.completed_receipts
        if (type(rows) is not tuple or not rows or len(rows) > 100000
                or any(type(row) is not tuple or len(row) != 2 for row in rows)
                or tuple(row[0] for row in rows) != tuple(sorted({row[0] for row in rows}))):
            raise ValueError('retained E3 requires its complete sorted original success census')
        for task, receipt in rows:
            validate_stable_id(task)
            _reference(receipt, CanonicalTaskReceipt)
            if not task.startswith(NAMESPACE + '.'):
                raise ValueError('retained E3 cannot adopt another experiment task')
        if len({pin for _, pin in rows}) != len(rows):
            raise ValueError('retained E3 aliases original success receipts')
        arrays = self.retained_arrays
        if (type(arrays) is not tuple or not arrays
                or any(type(row) is not tuple or len(row) != 2 for row in arrays)
                or tuple(row[0] for row in arrays) != tuple(sorted({row[0] for row in arrays}))
                or not {row[0] for row in arrays} <= {row[0] for row in rows}):
            raise ValueError('retained E3 arrays require their exact successful original producer census')
        for task, artifact in arrays:
            if type(artifact) is not ArtifactIdentity:
                raise TypeError('retained E3 requires exact original array artifact identities')
            validate_record_fields(artifact)
            if artifact.artifact_id != 'artifact.' + self.original_run_id + '.' + task + '.arrays':
                raise ValueError('retained E3 substitutes an original array producer alias')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def require_receipt(self, receipt):
        if (type(receipt) is not CanonicalTaskReceipt or receipt.run_id != self.original_run_id
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or dict(self.completed_receipts).get(receipt.task_id) !=
                    ObjectIdentity.from_record(receipt.receipt_id, receipt)):
            raise ValueError('retained E3 substitutes an original successful receipt')


@dataclass(frozen=True, slots=True)
class ConfiguredE3RetainedTaskConfig(CanonicalRecord):
    """A pure byte adoption with an explicit original configuration and task."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-retained-task-config'
    record_id: str
    continuation: ObjectIdentity
    original_config: (ConfiguredProtectedE3SourceConfig | ConfiguredProtectedE3FeatureConfig |
        ConfiguredProtectedE3PhysicalForecastConfig | ConfiguredProtectedE3FitConfig | ConfiguredProtectedE3StatisticalConfig)
    original_task: ExecutionTask
    original_receipt: CanonicalTaskReceipt

    def __post_init__(self):
        from .configured_protected_lowering import operation_class, task_id
        kinds = (ConfiguredProtectedE3SourceConfig, ConfiguredProtectedE3FeatureConfig,
            ConfiguredProtectedE3PhysicalForecastConfig, ConfiguredProtectedE3FitConfig, ConfiguredProtectedE3StatisticalConfig)
        if type(self.original_config) not in kinds:
            raise TypeError('retained E3 adoption changes its exact original configuration type')
        validate_record_fields(self.original_config)
        _reference(self.continuation, ConfiguredE3RetainedExecution)
        for record, kind in ((self.original_task, ExecutionTask), (self.original_receipt, CanonicalTaskReceipt)):
            if type(record) is not kind:
                raise TypeError('retained E3 adoption requires its exact original task and receipt')
            validate_record_fields(record)
        task, receipt, config = self.original_task, self.original_receipt, self.original_config
        phase = operation_class(config)
        node = task_id(config)
        if (self.record_id != 'config.retained.' + node or task.task_id != node or receipt.task_id != node
                or receipt.operational_status is not OperationalStatus.SUCCEEDED
                or phase not in RETAINED_PHASES
                or phase == 'forecast' and config.mode != 'calibration'):
            raise ValueError('retained E3 adopts only completed pre-response work, never future outcomes')
        if (task.capability.config.content_sha256 != config.fingerprint()
                or task.capability.config.config_schema != config.SCHEMA):
            raise ValueError('retained E3 changes its original task configuration')
        expected = {row.logical_artifact_id: row for row in task.outputs}
        logicals = {row.logical_artifact_id: row for row in receipt.output_logical_artifacts}
        physicals = {row.logical_artifact_id: row for row in receipt.output_materializations}
        if set(expected) != set(logicals) or set(expected) != set(physicals):
            raise ValueError('retained E3 drops an original output')
        for key, output in expected.items():
            logical, physical = logicals[key], physicals[key]
            if ((logical.payload_schema, logical.profile, logical.media_type, logical.outcome_access,
                    logical.visibility_ceiling, physical.relative_path) !=
                    (output.payload_schema, output.profile, output.media_type, output.outcome_access,
                        output.visibility_ceiling, output.relative_path)
                    or physical.physical_sha256 != logical.content_sha256):
                raise ValueError('retained E3 changes original output bytes, scope or location')

    @property
    def specification(self):
        return self.original_config.specification

    def validate_retention(self, retention):
        if type(retention) is not ConfiguredE3RetainedExecution or retention.identity != self.continuation:
            raise ValueError('retained E3 task changes its exact source continuation')
        retention.require_receipt(self.original_receipt)
        if (self.specification != retention.specification or
                self.original_receipt.implementation_commit != retention.original_source.observed_git_head):
            raise ValueError('retained E3 task changes its original scientific or producing source')
