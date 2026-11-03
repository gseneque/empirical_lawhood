# SPDX-License-Identifier: MPL-2.0
"""A distinct preparation edition retaining entered E3 before future outcomes."""
from dataclasses import dataclass
from typing import ClassVar

from .configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
from .configured_retained_execution import ConfiguredE3RetainedExecution, ConfiguredE3RetainedTaskConfig, source_binding
from .configured_unfinished_execution import ConfiguredE3UnfinishedExecution
from .configured_closeout_execution import ConfiguredE3ClosedExecution


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfiguredE3ContinuedPreparationSelection(ConfiguredProtectedE3PreparationSelection):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-continued-preparation-selection'
    VERSION: ClassVar[str] = '1.0.0'
    retention: ConfiguredE3RetainedExecution
    retained_tasks: tuple[ConfiguredE3RetainedTaskConfig, ...]

    def __post_init__(self):
        super(ConfiguredE3ContinuedPreparationSelection, self).__post_init__()
        if type(self.retention) is not ConfiguredE3RetainedExecution:
            raise TypeError('continued E3 preparation requires its exact retained execution')
        self.retention.__post_init__()
        if (self.retention.specification != self.fit_config.specification
                or self.retention.allocation != self.fit_config.allocation
                or tuple(source_binding(row) for row in self.manifest.provenances) != (self.retention.original_source,)):
            raise ValueError('continued E3 preparation changes original science or prefix-producing source')
        tasks = self.retained_tasks
        if type(tasks) is not tuple or any(type(row) is not ConfiguredE3RetainedTaskConfig for row in tasks):
            raise TypeError('continued E3 requires its exact retained task roster')
        if tuple(row.original_task.task_id for row in tasks) != tuple(task for task, _ in self.retention.completed_receipts):
            raise ValueError('continued E3 must retain every original completed task exactly once')
        for row in tasks:
            row.__post_init__()
            row.validate_retention(self.retention)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfiguredE3UnfinishedPreparationSelection(ConfiguredE3ContinuedPreparationSelection):
    """Keep the whole design while selecting only the unfinished operations."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-unfinished-preparation-selection'
    unfinished: ConfiguredE3UnfinishedExecution

    def __post_init__(self):
        super(ConfiguredE3UnfinishedPreparationSelection, self).__post_init__()
        if type(self.unfinished) is not ConfiguredE3UnfinishedExecution or self.unfinished.retention != self.retention:
            raise ValueError('unfinished E3 selection substitutes its exact source continuation')
        self.unfinished.__post_init__()


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfiguredE3ClosedPreparationSelection(ConfiguredE3ContinuedPreparationSelection):
    """Keep entered CAL closed while selecting its missingness and untouched CONF."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-closed-preparation-selection'
    closeout: ConfiguredE3ClosedExecution

    def __post_init__(self):
        super(ConfiguredE3ClosedPreparationSelection, self).__post_init__()
        if type(self.closeout) is not ConfiguredE3ClosedExecution or self.closeout.retention != self.retention:
            raise ValueError('CAL closeout selection substitutes its exact source continuation')
        self.closeout.__post_init__()


def retained_file_versions(selection):
    """Use actual original output codecs, including non-default record editions."""
    from .configured_protected_composition import operation_declarations
    from .configured_retained_bindings import retained_input_id
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    declarations = {row.capability_key: row for row in operation_declarations()}
    versions = {}
    for config in selection.retained_tasks:
        declaration = declarations[config.original_task.capability.capability_key]
        for logical in config.original_receipt.output_logical_artifacts:
            kind = declaration.record_codecs.get(logical.payload_schema)
            if logical.profile is ArtifactProfile.CANONICAL_JSON and kind is None:
                raise ValueError('retained E3 copy loses its original typed output codec')
            versions[retained_input_id(logical)] = '1.0.0' if kind is None else kind.VERSION
    if type(selection) in (ConfiguredE3UnfinishedPreparationSelection, ConfiguredE3ClosedPreparationSelection):
        codecs = {schema: kind for row in declarations.values() for schema, kind in row.record_codecs.items()}
        from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_NPZ_CODEC
        scope = selection.unfinished if type(selection) is ConfiguredE3UnfinishedPreparationSelection else selection.closeout
        for imported in scope.imported_outputs:
            logical = imported.logical
            versions[logical.logical_artifact_id] = (codecs[logical.payload_schema].VERSION
                if logical.profile is ArtifactProfile.CANONICAL_JSON else MATRIX_NPZ_CODEC.record_version)
        if type(selection) is ConfiguredE3ClosedPreparationSelection:
            from .configured_closeout_execution import ConfiguredE3MissingOutcomeProducts
            for row in scope.calibration_roots:
                if row.missing_products is not None:
                    versions[row.missing_products.object_id] = ConfiguredE3MissingOutcomeProducts.VERSION
    return versions
