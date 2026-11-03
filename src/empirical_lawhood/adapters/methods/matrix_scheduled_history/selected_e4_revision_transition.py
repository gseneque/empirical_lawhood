# SPDX-License-Identifier: MPL-2.0
"""Declared original-DEV acquisition to existing selected revision component."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_relative_locator, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentInputConfigurationDeclaration,
    ExperimentPreparation, ExperimentProtocolDeclaration, PreparedExperimentInputs,
)
from . import selected_e3_e4_records as r, selected_e4_methods as science, selected_e4_method_bindings as method


PROTOCOL_ID = "matrix.selected-e4.revision-from-acquisition"


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionAcquisitionSource(CanonicalRecord):
    """A selected original DEV directory; no caller asserts its receipt or data."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/revision-acquisition-source"
    record_id: str
    authored_directory: str
    allow_partial: bool

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_relative_locator(self.authored_directory)
        if (type(self.authored_directory) is not str or not self.authored_directory
                or PurePosixPath(self.authored_directory).is_absolute()
                or any(part in (".", "..") for part in self.authored_directory.split("/"))
                or type(self.allow_partial) is not bool):
            raise ValueError("selected revision requires its guarded original DEV directory and explicit partial-read selection")

    @property
    def identity(self):
        return r.pin(self)


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionAcquisitionSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/revision-acquisition-specification"
    specification_id: str
    revision: science.SelectedE4RevisionExperimentSpecification

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if type(self.revision) is not science.SelectedE4RevisionExperimentSpecification:
            raise TypeError("selected DEV transition embeds its exact separately declared revision specification")
        self.revision.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


INPUT_TYPES = {"allocation": UnitAllocation, "campaign": CampaignSpec,
    "source": SelectedE4RevisionAcquisitionSource, "resources": method.SelectedE4MethodResources}


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionAcquisitionInputs:
    allocation: UnitAllocation | None = None
    campaign: CampaignSpec | None = None
    source: SelectedE4RevisionAcquisitionSource | None = None
    resources: method.SelectedE4MethodResources | None = None

    def __post_init__(self):
        for name, kind in INPUT_TYPES.items():
            value = getattr(self, name)
            if value is not None:
                if type(value) is not kind:
                    raise TypeError("selected DEV transition changes its exact declared input role " + name)
                value.__post_init__()


@dataclass(frozen=True, slots=True)
class SelectedE4RevisionAcquisitionProgramme(CanonicalRecord):
    """Immutable declared choices plus exact authored component custody pins."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/revision-acquisition-programme"
    record_id: str
    specification: SelectedE4RevisionAcquisitionSpecification
    allocation: UnitAllocation
    campaign: CampaignSpec
    source: SelectedE4RevisionAcquisitionSource
    resources: method.SelectedE4MethodResources
    workers: int
    environment_id: str
    source_snapshot: ObjectIdentity
    output_root: str
    resolved_source: method.SelectedE4DevelopmentAcquisition | None = None
    child_packet: ObjectIdentity | None = None
    child_plan: ObjectIdentity | None = None
    child_instance: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, SelectedE4RevisionAcquisitionSpecification),
                (self.allocation, UnitAllocation), (self.campaign, CampaignSpec),
                (self.source, SelectedE4RevisionAcquisitionSource), (self.resources, method.SelectedE4MethodResources)):
            if type(value) is not kind:
                raise TypeError("selected DEV transition changes its immutable declared scientific/operational choices")
            value.__post_init__()
        validate_declared_allocation(self.specification, self.allocation)
        self.resources.for_operations(("revision-fit", "revision-freeze"))
        self.execution.__post_init__()
        if (type(self.workers) is not int or self.workers < 1 or type(self.environment_id) is not str
                or type(self.source_snapshot) is not ObjectIdentity or type(self.output_root) is not str):
            raise ValueError("selected DEV transition requires all explicit execution selections")
        bound = (self.resolved_source, self.child_packet, self.child_plan, self.child_instance)
        if any(value is not None for value in bound):
            if (type(self.resolved_source) is not method.SelectedE4DevelopmentAcquisition
                    or any(type(value) is not ObjectIdentity for value in bound[1:])):
                raise ValueError("selected DEV transition cannot retain an incomplete authored component closure")
            for value in bound:
                value.__post_init__()
            if (self.resolved_source.authored_directory != self.source.authored_directory
                    or self.resolved_source.allow_partial != self.source.allow_partial):
                raise ValueError("selected DEV transition substitutes its exact selected original acquisition")
            from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
            from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
            from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
            for value, kind in ((self.child_packet, AuthoredRecursiveWave), (self.child_plan, DevelopmentExecutionPlan),
                    (self.child_instance, ExperimentInstanceBinding)):
                r.exact_pin(value, kind)

    @property
    def identity(self):
        return r.pin(self)

    @property
    def execution(self):
        return ExecutionSelection(workers=self.workers, environment_id=self.environment_id,
            source_snapshot=self.source_snapshot, output_root=self.output_root)


def validate_declared_allocation(specification, allocation):
    specification.__post_init__()
    allocation.__post_init__()
    declared = specification.revision
    if (allocation.sources != (declared.programme,) or allocation.unit_ids("development") !=
            tuple(row.unit_id for row in declared.folds)):
        raise ValueError("selected DEV transition changes its exact original declared allocation or whole-unit folds")


def bind_inputs(specification, records, *, files=None):
    if files:
        raise ValueError("selected DEV transition accepts no file inputs")
    if (type(specification) is not SelectedE4RevisionAcquisitionSpecification or not isinstance(records, Mapping)
            or set(records) - set(INPUT_TYPES)):
        raise TypeError("selected DEV transition accepts its exact original allocation/source/campaign/resource input roles")
    specification.__post_init__()
    inputs = SelectedE4RevisionAcquisitionInputs(**records)
    if inputs.allocation is not None:
        validate_declared_allocation(specification, inputs.allocation)
    return PreparedExperimentInputs({} if inputs.allocation is None else {"development": inputs.allocation}, inputs)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    if type(specification) is not SelectedE4RevisionAcquisitionSpecification or type(execution) is not ExecutionSelection:
        raise TypeError("selected DEV transition requires separate exact scientific and operational selections")
    specification.__post_init__()
    execution.__post_init__()
    inputs = SelectedE4RevisionAcquisitionInputs() if method_inputs is None else method_inputs
    if type(inputs) is not SelectedE4RevisionAcquisitionInputs or not isinstance(scientific_inputs, Mapping):
        raise TypeError("selected DEV transition requires its exact bound original input roles")
    inputs.__post_init__()
    dependencies = []
    def missing(code, kind, detail):
        key = "matrix.selected-e4.revision-transition." + code
        if not any(row.code == key for row in dependencies):
            dependencies.append(ExperimentDependency(key, kind, detail, code))
    for name in INPUT_TYPES:
        if getattr(inputs, name) is None:
            missing(name, DependencyKind.EXTERNAL_INPUT, "Select the original " + name + " input before authoring.")
    if scientific_inputs != ({} if inputs.allocation is None else {"development": inputs.allocation}):
        missing("allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Preserve the exact complete original development allocation.")
    for name in ("workers", "environment_id", "source_snapshot", "output_root"):
        if getattr(execution, name) is None:
            missing(name, DependencyKind.ENVIRONMENT, "Select explicit operational " + name + " before authoring.")
    if protocol_bytes is not None:
        missing("protocol", DependencyKind.SCIENTIFIC_EVIDENCE, "The nested editable scientific declaration owns all supported choices.")
    programme = None
    if not dependencies:
        validate_declared_allocation(specification, inputs.allocation)
        programme = SelectedE4RevisionAcquisitionProgramme("programme.revision-transition." + specification.fingerprint(),
            specification, inputs.allocation, inputs.campaign, inputs.source, inputs.resources,
            execution.workers, execution.environment_id, execution.source_snapshot, execution.output_root)
    groups = len(specification.revision.folds)
    census = ExperimentCensus((("development-groups", groups),),
        (("development-groups", 0 if inputs.allocation is None else len(inputs.allocation.units)),),
        (("revision-fit", 1), ("revision-freeze", 1)), (("canonical-products", sum(len(method.output_types(operation))
            for operation in ("revision-fit", "revision-freeze"))),), 0)
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        inputs.allocation, execution=execution, specification_record=specification, programme=programme)


def protocol_declaration():
    return ExperimentProtocolDeclaration(PROTOCOL_ID, SelectedE4RevisionAcquisitionSpecification, prepare,
        "experiment.matrix-selected-e4-revision-from-acquisition",
        example_paths=("programmes/foundations/emergent-structure/workflows/matrix-selected-e4-revision/specification.json",), maximum_config_bytes=128*1024**2,
        input_record_types=tuple(INPUT_TYPES.values()), bind_inputs=bind_inputs,
        programme_record_type=SelectedE4RevisionAcquisitionProgramme,
        configuration_inputs=(ExperimentInputConfigurationDeclaration("matrix-selected-e4-revision-acquisition",
            SelectedE4RevisionAcquisitionSource, maximum_config_bytes=64*1024),))
