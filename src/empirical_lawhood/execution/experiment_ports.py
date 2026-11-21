# SPDX-License-Identifier: MPL-2.0
"""Structural extension ports; implementations and custody stay with their owners.

These ports introduce no canonical records, access verdicts or lifecycle engine.
Report values remain domain-owned: exact Decimal values and typed records are
permitted. A report's shape does not establish completion or qualification.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, Self, TypeAlias, TypeVar

if TYPE_CHECKING:
    from pathlib import Path

    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.records.serialization import CanonicalRecord
    from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
    from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactManifest, ArtifactWriter
    from empirical_lawhood.execution.candidate_compiler import ExecutableStudyCandidate
    from empirical_lawhood.execution.experiment_preparation import ExperimentInstanceBinding, ExperimentPreparation
    from empirical_lawhood.execution.operator_profile import OperatorStorageProfile
    from empirical_lawhood.execution.prospective_experiment import ProspectiveExperimentAssociation
    from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave


ExperimentReport: TypeAlias = Mapping[str, object]
RecordT = TypeVar("RecordT", bound="CanonicalRecord")


class ReadAccessSelection(Protocol):
    """Editable locator selection, never an authorization or retained verdict."""

    @property
    def selected_records(self) -> tuple[CanonicalRecord, ...]: ...


class CurrentAccessGuard(Protocol):
    def __call__(self) -> None: ...


class OriginalInputAccess(Protocol):
    """Live original-input guard. Each call must use the current owning checks."""

    @property
    def parents(self) -> tuple[ArtifactLineageParent, ...]: ...

    def require_current(self) -> None: ...

    def require_member(self, manifest: ArtifactManifest) -> None: ...

    def record_parents(self, record: CanonicalRecord) -> tuple[ArtifactLineageParent, ...]: ...


class ProspectiveOriginalInputAccess(OriginalInputAccess, Protocol):
    def require_issued_member(self, manifest: ArtifactManifest) -> None: ...

    def bind_issued_members(self, manifests: tuple[ArtifactManifest, ...], *,
                           packet: AuthoredRecursiveWave, association: ProspectiveExperimentAssociation,
                           directory: Path | None = None) -> Self: ...

    def bind_source_provenance(self, *, packet: AuthoredRecursiveWave, directory: Path) -> Self: ...


class OriginalMemberReader(Protocol):
    def __call__(self, reference: ObjectIdentity, kind: type[RecordT]) -> RecordT: ...


class SelectedLocatorReader(Protocol):
    def __call__(self, key: str, reference: ObjectIdentity, kind: type[RecordT]) -> RecordT: ...


class ExperimentServiceContext(Protocol):
    """Selected outer composition supplied to an adapter's API factory.

    A factory which needs another operation uses that operation's documented
    API port. This context does not promise arbitrary service attributes.
    """

    @property
    def project_root(self) -> Path: ...

    @property
    def artifact_writer(self) -> ArtifactWriter: ...

    @property
    def storage_profile(self) -> OperatorStorageProfile | None: ...


class CompositeProgrammeService(Protocol):
    """The four required methods, with the actual common keyword call forms.

    Derivation, export, execution-only reads and refinement are optional
    capabilities. They are not implied by implementing these four methods.
    """

    def author(self, *, preparation: ExperimentPreparation, output_dir: Path) -> ExperimentReport: ...

    def run(self, *, directory: Path, maximum_parallel_tasks: int,
            programme_request_path: Path | None = None, confirmed: bool = False) -> ExperimentReport: ...

    def recover(self, *, directory: Path, maximum_parallel_tasks: int,
                programme_request_path: Path | None = None, confirmed: bool = False) -> ExperimentReport: ...

    def read(self, *, directory: Path, allow_partial: bool = False,
             programme_request_path: Path | None = None) -> ExperimentReport: ...


class RetainedProspectiveSelection(Protocol):
    """Authenticated original metadata; contains no new execution authority."""

    @property
    def association(self) -> ProspectiveExperimentAssociation: ...

    @property
    def instance(self) -> ExperimentInstanceBinding: ...

    @property
    def candidate(self) -> ExecutableStudyCandidate: ...

    @property
    def draft(self) -> RecursiveStudyDraft: ...

    @property
    def payloads(self) -> Mapping[str, bytes]: ...

    @property
    def original_input_access(self) -> ProspectiveOriginalInputAccess | None: ...


def require_experiment_report(value: object, *, hook: str) -> ExperimentReport:
    """Validate the outer return contract without interpreting scientific fields."""
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
        raise TypeError(f"{hook} must return a report mapping with string keys")
    return value


def require_read_access_selection(value: object, records: tuple[CanonicalRecord, ...]) -> ReadAccessSelection:
    """Require the complete copied locator census, without reading any source."""
    from empirical_lawhood.science.records.serialization import CanonicalRecord

    selected = getattr(value, "selected_records", None)
    if (isinstance(value, CanonicalRecord) or type(selected) is not tuple
            or any(not isinstance(record, CanonicalRecord) for record in selected)):
        raise TypeError("current access projection must return its operation-local selection, not a permission result; selected_records are required")
    # Selection owners may sort copied locators. They cannot replace a codec,
    # revision, byte, or member, or collapse repeated members into a set.
    def census(rows):
        return sorted((record.SCHEMA, record.VERSION, record.canonical_bytes()) for record in rows)

    if census(selected) != census(records) or sorted(map(type, selected), key=str) != sorted(map(type, records), key=str):
        raise ValueError("current access projection changes its complete selected locator census")
    return value
