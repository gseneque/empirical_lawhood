# SPDX-License-Identifier: MPL-2.0
"""Inward, nonexecuting workflow facts for adapter-owned public discovery."""

from dataclasses import dataclass
from pathlib import PurePosixPath
from empirical_lawhood.science.records.serialization import validate_stable_id


@dataclass(frozen=True, slots=True)
class WorkflowInput:
    path: str
    role: str
    schema_id: str


@dataclass(frozen=True, slots=True)
class WorkflowOperation:
    command: str
    boundary: str
    inputs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Workflow:
    workflow_id: str
    title: str
    kind: str
    substrates: tuple[str, ...]
    methods: tuple[str, ...]
    environment: str
    operations: tuple[WorkflowOperation, ...]
    inputs: tuple[WorkflowInput, ...]
    input_availability: str
    scientific_ceiling: str
    first_missing_prerequisite: str
    guide: str
    verification_owners: tuple[str, ...]
    output_retention: str = (
        "See each command's current effects and guide for explicit development export "
        "or closed authoring outputs. Discovery writes nothing."
    )
    resources: str = (
        "Guide and input paths belong to the selected source checkout/distribution, "
        "not the installed wheel. No current directory is assumed."
    )


@dataclass(frozen=True, slots=True)
class WorkflowDeclaration:
    workflow: Workflow
    display_state: str
    descriptor_version: str = "1.0.0"
    operations_available: bool = True
    catalogue_order: int = 1000

    def __post_init__(self):
        if type(self.workflow) is not Workflow or self.descriptor_version != "1.0.0":
            raise TypeError("workflow descriptor requires its exact supported static contract")
        if type(self.catalogue_order) is not int or self.catalogue_order < 0:
            raise ValueError("workflow catalogue order requires a nonnegative exact integer")
        w = self.workflow
        validate_stable_id(w.workflow_id)
        for value in (w.title, w.kind, w.environment, w.input_availability, w.scientific_ceiling,
                      w.first_missing_prerequisite, w.output_retention, w.resources, self.display_state):
            if type(value) is not str or not value.strip():
                raise ValueError("workflow descriptor omits a required public boundary or presentation fact")
        for rows in (w.substrates, w.methods, w.verification_owners):
            if type(rows) is not tuple or not rows or any(type(v) is not str or not v for v in rows):
                raise ValueError("workflow descriptor requires immutable complete public facts")
        if (type(self.operations_available) is not bool or type(w.operations) is not tuple
                or bool(w.operations) != self.operations_available
                or any(type(v) is not WorkflowOperation for v in w.operations)
                or type(w.inputs) is not tuple or any(type(v) is not WorkflowInput for v in w.inputs)
                or len({v.command for v in w.operations}) != len(w.operations)
                or len({v.path for v in w.inputs}) != len(w.inputs)):
            raise ValueError("workflow descriptor repeats or substitutes a public operation/input")
        paths = (w.guide, *w.verification_owners, *(v.path for v in w.inputs))
        if any(type(p) is not str or not p or PurePosixPath(p).is_absolute() or ".." in PurePosixPath(p).parts for p in paths):
            raise ValueError("workflow descriptor paths belong to the selected source distribution")
        if any(not v.command or not v.boundary or type(v.inputs) is not tuple or
               not set(v.inputs).issubset({p.path for p in w.inputs}) for v in w.operations):
            raise ValueError("workflow descriptor operation loses its boundary or declared input role")
