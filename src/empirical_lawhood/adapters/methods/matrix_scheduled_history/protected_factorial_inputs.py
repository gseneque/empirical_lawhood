# SPDX-License-Identifier: MPL-2.0
"""Exact original scientific carriers and separate preparation prerequisites."""

from dataclasses import dataclass, fields
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_ids, validate_stable_id
from empirical_lawhood.planning.experiment_entry import StudyDefinition
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt
from empirical_lawhood.runtime.execution_envelope import ExecutionResourceEnvelopeSpec
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig

from .programme_factorial_confirmation import ScheduledFactorialCriteriaBinding
from .protected_factorial_resources import ProtectedFactorialResourceSelection, bind_protected_factorial_resources
from .protected_factorial_specification import ProtectedFactorialAcquisitionRoster
from .records import ScheduledAllocation


@dataclass(frozen=True, slots=True)
class ProtectedFactorialOriginalSource(CanonicalRecord):
    """The original global entry occurs once, without rewriting historical bytes."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/protected-factorial-original-source"
    source_id: str
    study: StudyDefinition
    criteria: ScheduledFactorialCriteriaBinding
    acquisitions: ProtectedFactorialAcquisitionRoster
    allocation: ScheduledAllocation

    def __post_init__(self):
        validate_stable_id(self.source_id)
        for row, kind in ((self.study, StudyDefinition), (self.criteria, ScheduledFactorialCriteriaBinding),
                (self.acquisitions, ProtectedFactorialAcquisitionRoster), (self.allocation, ScheduledAllocation)):
            if type(row) is not kind:
                raise TypeError("protected original source requires its exact original typed scientific carriers")
            row.__post_init__()
        if len({self.source_id, self.study.package_id, self.criteria.binding_id, self.acquisitions.roster_id,
                self.allocation.allocation_id}) != 5:
            raise ValueError("protected original source aliases its scientific record roles")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.source_id, self)


@dataclass(frozen=True, slots=True)
class ProtectedFactorialPreparationSelection(CanonicalRecord):
    """Actual source qualifications and execution metadata, never new authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/protected-factorial-preparation-selection"
    selection_id: str
    bank: ArtifactIdentity
    operational_budget: ResourceBudget
    formal_methods: FormalMethodCatalog
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    source_configs: tuple[SourceMaterializationConfig, ...]
    resources: ExecutionResourceEnvelopeSpec | None
    paired_inputs: tuple[ArtifactIdentity, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        _validate_preparation_components(self)
        if self.resources is not None:
            if type(self.resources) is not ExecutionResourceEnvelopeSpec:
                raise TypeError("protected preparation needs the actual existing resource envelope")
            self.resources.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


def _validate_preparation_components(selection):
    for row, kind in ((selection.bank, ArtifactIdentity), (selection.operational_budget, ResourceBudget),
            (selection.formal_methods, FormalMethodCatalog)):
        if type(row) is not kind:
            raise TypeError("protected preparation requires exact artifact, budget and formal catalog records")
        row.__post_init__()
    for rows, kind, attribute in ((selection.formal_source_inventories, FormalGapSourceCapabilityInventory, "denominator_id"),
            (selection.qualifications, MaterializationQualificationReceipt, "receipt_id")):
        if type(rows) is not tuple or not rows or any(type(row) is not kind for row in rows):
            raise TypeError("protected preparation needs the actual complete formal and source qualification rosters")
        require_sorted_unique_ids(rows, attribute=attribute, field_name=attribute)
        for row in rows:
            row.__post_init__()
    if (type(selection.source_configs) is not tuple
            or any(type(row) is not SourceMaterializationConfig for row in selection.source_configs)
            or tuple(row.fingerprint() for row in selection.source_configs) != tuple(sorted({row.fingerprint() for row in selection.source_configs}))):
        raise ValueError("protected source configurations require their exact canonical SHA-keyed roster")
    for row in selection.source_configs:
        row.__post_init__()
    if (type(selection.paired_inputs) is not tuple or any(type(row) is not ArtifactIdentity for row in selection.paired_inputs)
            or tuple(row.artifact_id for row in selection.paired_inputs) != tuple(sorted({row.artifact_id for row in selection.paired_inputs}))):
        raise ValueError("protected paired sources need their exact sorted artifact identities")
    for row in (selection.bank, *selection.paired_inputs):
        row.__post_init__()
        if row.media_type != "application/json" or type(row.size_bytes) is not int or row.size_bytes <= 0:
            raise ValueError("protected canonical source metadata needs positive exact byte sizes")


@dataclass(frozen=True, slots=True)
class ProtectedFactorialPreparationRequest(CanonicalRecord):
    """Unbound operational request; neither issued identities nor authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/protected-factorial-preparation-request"
    request_id: str
    bank: ArtifactIdentity
    operational_budget: ResourceBudget
    formal_methods: FormalMethodCatalog
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    source_configs: tuple[SourceMaterializationConfig, ...]
    resource_selection: ProtectedFactorialResourceSelection
    paired_inputs: tuple[ArtifactIdentity, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.request_id)
        _validate_preparation_components(self)
        if type(self.resource_selection) is not ProtectedFactorialResourceSelection:
            raise TypeError("protected authoring request needs its exact unbound resource selection")
        self.resource_selection.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.request_id, self)


def validate_protected_factorial_request_binding(request, selection):
    """Check an exact request-to-bound transformation without granting authority."""
    if type(request) is not ProtectedFactorialPreparationRequest or type(selection) is not ProtectedFactorialPreparationSelection:
        raise TypeError("protected resource binding requires exact request and bound-selection records")
    request.__post_init__()
    selection.__post_init__()
    if (selection.selection_id != request.request_id + ".bound" or selection.resources is None
            or any(getattr(request, field.name) != getattr(selection, field.name)
                for field in fields(ProtectedFactorialPreparationSelection) if field.name not in {"selection_id", "resources"})
            or ProtectedFactorialResourceSelection(**{field.name: getattr(selection.resources, field.name)
                for field in fields(ProtectedFactorialResourceSelection)}) != request.resource_selection):
        raise ValueError("protected bound preparation changes its exact original request or resource choices")


def bind_protected_factorial_preparation_request(request, *, issued_extensions):
    if type(request) is not ProtectedFactorialPreparationRequest:
        raise TypeError("protected preparation binding requires its exact unbound request")
    request.__post_init__()
    resources = bind_protected_factorial_resources(request.resource_selection, issued_extensions=issued_extensions)
    selection = ProtectedFactorialPreparationSelection(request.request_id + ".bound", resources=resources,
        **{field.name: getattr(request, field.name) for field in fields(ProtectedFactorialPreparationSelection)
            if field.name not in {"selection_id", "resources"}})
    validate_protected_factorial_request_binding(request, selection)
    return selection
