# SPDX-License-Identifier: MPL-2.0
"""Closed installed presentation declarations over current owning scientific reads."""

from __future__ import annotations

from dataclasses import dataclass
from inspect import signature
from pathlib import Path
from typing import Protocol, TYPE_CHECKING

from empirical_lawhood.science.records.serialization import validate_relative_locator, validate_semantic_version, validate_stable_id

from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationError, absolute_path, application_result, response_bytes
from empirical_lawhood.api.application_projections import projection

if TYPE_CHECKING:
    from empirical_lawhood.storage.contracts.artifacts import ArtifactWriter


@dataclass(frozen=True, slots=True)
class PresentationData:
    """An operation-local projection of authenticated results, never a scientific record."""

    identity: dict
    scope: str
    summary: dict
    records: tuple[dict, ...]
    original_report: dict
    provenance: dict
    value_semantics: str
    exploration: dict | None = None

    def __post_init__(self):
        from empirical_lawhood.science.records.decoding import decode_canonical_record
        from empirical_lawhood.science.identity.provenance import ObjectIdentity
        decode_canonical_record(self.identity, ObjectIdentity)
        if any(type(value) is not dict for value in (self.summary, self.original_report, self.provenance)):
            raise TypeError("presentation keeps exact named original data")
        if any(type(value) is not str or not value for value in (self.scope, self.value_semantics)):
            raise TypeError("presentation requires its original scope and value semantics")
        if self.exploration is not None:
            from empirical_lawhood.api.application_exploration_contracts import EXPLORATION_SCHEMA, EXPLORATION_VERSION, validate_exploration
            if type(self.exploration) is not dict or self.exploration.get("schema") != EXPLORATION_SCHEMA:
                raise TypeError("exploration requires its declared display schema")
            validate_semantic_version(self.exploration.get("version"))
            if self.exploration["version"] == EXPLORATION_VERSION:
                validate_exploration(self.exploration)


@dataclass(frozen=True, slots=True)
class ApplicationPresentation:
    panel_id: str
    version: str
    title: str
    workflow_id: str
    guide: str
    columns: tuple[str, ...]
    maximum_records: int
    read: PresentationReader
    observe: OperationalObservationReader | None = None
    observation_version: str | None = None

    def __post_init__(self):
        for value in (self.panel_id, self.workflow_id):
            validate_stable_id(value)
        validate_semantic_version(self.version)
        validate_relative_locator(self.guide)
        if type(self.title) is not str or not self.title or len(self.title) > 160:
            raise ValueError("presentation needs a bounded title")
        if (type(self.columns) is not tuple or not 1 <= len(self.columns) <= 12
                or len(set(self.columns)) != len(self.columns)):
            raise ValueError("presentation requires distinct bounded data columns")
        for column in self.columns:
            validate_stable_id(column)
        if type(self.maximum_records) is not int or not 1 <= self.maximum_records <= 4096:
            raise ValueError("presentation requires an explicit bounded complete record census")
        if not callable(self.read):
            raise TypeError("presentation requires its installed current-result reader")
        signature(self.read).bind(context=None, directory=None, artifact_writer=None)
        if (self.observe is None) != (self.observation_version is None):
            raise ValueError("an operational observer requires its explicit interface revision")
        if self.observe is not None:
            validate_semantic_version(self.observation_version)
            signature(self.observe).bind(context=None, directory=None, artifact_writer=None, selection=None)

    def description(self):
        return {key: getattr(self, key) for key in (
            "panel_id", "version", "title", "workflow_id", "guide", "columns", "maximum_records", "observation_version")}


class PresentationReader(Protocol):
    def __call__(self, *, context: ApplicationContext, directory: Path,
                 artifact_writer: ArtifactWriter) -> PresentationData: ...


class OperationalObservationReader(Protocol):
    """Read bounded original metadata only; no scientific reconstruction or effects."""

    def __call__(self, *, context: ApplicationContext, directory: Path,
                 artifact_writer: ArtifactWriter, selection: dict) -> dict: ...


def validate_presentations(rows):
    """Check the static complete tuple without calling a reader or inspecting storage."""
    if type(rows) is not tuple or len(rows) > 200 or any(type(row) is not ApplicationPresentation for row in rows):
        raise TypeError("presentation registry requires exact installed declarations")
    if len({row.panel_id for row in rows}) != len(rows):
        raise ValueError("presentation registry repeats an owning panel identity")
    for row in rows:
        row.__post_init__()
    return rows


def application_presentations():
    from empirical_lawhood.api.generated_application_presentations import APPLICATION_PRESENTATIONS
    return validate_presentations(APPLICATION_PRESENTATIONS)


def presentation_operation(context, request, values):
    declarations = application_presentations()
    if request.operation == "presentation.list":
        return projection(request=request, kind="presentations", title="Installed result presentations",
            identity=None, scope="STATIC_DECLARATIONS", summary={"presentation_count": len(declarations),
                "prerequisites_inspected": False}, records=tuple(row.description() for row in declarations), parameters=values)
    selected = next((row for row in declarations if row.panel_id == values["panel_id"]), None)
    if selected is None:
        raise ApplicationError("UNSUPPORTED_PRESENTATION", "Select an installed presentation identity.", field="panel_id")
    version = values["panel_version"]
    validate_semantic_version(version)
    directory = absolute_path(values["directory"], "directory")
    from empirical_lawhood.api.application_context import application_storage
    _, _, plane = application_storage(context)
    with plane.read_context() as reader:
        data = selected.read(context=context, directory=directory, artifact_writer=reader)
        if (type(data) is not PresentationData or type(data.records) is not tuple
                or len(data.records) > selected.maximum_records
                or any(type(row) is not dict for row in data.records)):
            raise TypeError("presentation reader exceeded its installed bounded result contract")
        data.__post_init__()
        from empirical_lawhood.api.application_exploration_contracts import EXPLORATION_VERSION
        supported = (version == selected.version and (data.exploration is None
            or data.exploration["version"] == EXPLORATION_VERSION))
        records = data.records if supported else tuple(
            {"field": key, "value": value} for key, value in data.original_report.items())
        result = projection(request=request, kind="presentation" if supported else "presentation-generic",
            title=selected.title, identity=data.identity, scope=data.scope, summary=data.summary,
            records=records, parameters=values, provenance=data.provenance, value_semantics=data.value_semantics,
            presentation={"panel_id": selected.panel_id, "installed_version": selected.version,
                "requested_version": version, "status": "SUPPORTED" if supported else "GENERIC_UNSUPPORTED_PANEL_REVISION",
                "columns": selected.columns if supported else ("field", "value"),
                "original_report": data.original_report})
        if supported and data.exploration is not None:
            result["exploration"] = data.exploration
        # Enforce the unchanged transport bound before the complete final byte check.
        response_bytes(application_result(request.operation, result))
        reader.require_verification_snapshot()
    return result
