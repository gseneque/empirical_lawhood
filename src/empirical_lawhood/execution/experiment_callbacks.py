# SPDX-License-Identifier: MPL-2.0
"""Named call forms for the existing experiment declaration and runtime hooks.

Alternatives describe selected capabilities, not overloads which every adapter
must implement. Access, incomplete assessment, file inputs and prospective
composition remain optional. Static discovery calls none of these hooks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeAlias, TypeVar

from empirical_lawhood.execution.experiment_ports import CompositeProgrammeService, CurrentAccessGuard, ExperimentReport, ExperimentServiceContext, OriginalInputAccess, OriginalMemberReader, ProspectiveOriginalInputAccess, ReadAccessSelection, RetainedProspectiveSelection, SelectedLocatorReader

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from empirical_lawhood.science.experiments.experimental_design import UnitAllocation
    from empirical_lawhood.science.records.serialization import CanonicalRecord
    from empirical_lawhood.design.experiment_inputs import ExperimentFileInputSelection, ExperimentInputSelection
    from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
    from empirical_lawhood.storage.contracts.artifacts import ArtifactWriter
    from empirical_lawhood.execution.execution import SchedulerResult
    from empirical_lawhood.execution.experiment_preparation import ExecutionSelection, ExperimentInputDerivationResult, ExperimentInstanceBinding, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs
    from empirical_lawhood.execution.experiment_programme import ExperimentProgrammeDescriptor
    from empirical_lawhood.execution.plans import ProtocolExecutionPlan
    from empirical_lawhood.execution.prospective_experiment import ProspectiveExperimentAssociation
    from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave
    from empirical_lawhood.execution.recursive_compiler import RecursiveCompilation
    from empirical_lawhood.execution.recursive_prospective import RecursiveCandidateContextProvider, RecursiveProspectiveDesignInputs
    from empirical_lawhood.execution.recursive_provider import RecursiveInputSupplier


class ExperimentPrepare(Protocol):
    def __call__(self, specification: CanonicalRecord, *, scientific_inputs: Mapping[str, UnitAllocation],
                 execution: ExecutionSelection, protocol_bytes: bytes | None) -> ExperimentPreparation: ...


class ExperimentPrepareWithMethods(Protocol):
    def __call__(self, specification: CanonicalRecord, *, scientific_inputs: Mapping[str, UnitAllocation],
                 execution: ExecutionSelection, protocol_bytes: bytes | None,
                 method_inputs: object | None = None) -> ExperimentPreparation: ...


class ExperimentInputBinder(Protocol):
    def __call__(self, specification: CanonicalRecord,
                 records: Mapping[str, CanonicalRecord]) -> PreparedExperimentInputs: ...


class ExperimentFileInputBinder(Protocol):
    def __call__(self, specification: CanonicalRecord, records: Mapping[str, CanonicalRecord], *,
                 files: Mapping[str, PreparedExperimentFile]) -> PreparedExperimentInputs: ...


class ExperimentLocatedInputBinder(Protocol):
    def __call__(self, specification: CanonicalRecord, records: Mapping[str, CanonicalRecord], *,
                 record_paths: Mapping[str, Path]) -> PreparedExperimentInputs: ...


class ExperimentLocatedFileInputBinder(Protocol):
    def __call__(self, specification: CanonicalRecord, records: Mapping[str, CanonicalRecord], *,
                 files: Mapping[str, PreparedExperimentFile],
                 record_paths: Mapping[str, Path]) -> PreparedExperimentInputs: ...


class ExperimentInstanceValidator(Protocol):
    def __call__(self, *, specification: CanonicalRecord, allocation: UnitAllocation,
                 draft: RecursiveStudyDraft, source_records: tuple[tuple[str, CanonicalRecord], ...]) -> None: ...


class ProspectiveHandoff(Protocol):
    """The immutable fields checked by the existing handoff owner.

    The callback preserves the concrete type and these actual values. Domain
    code may bind only the owning handoff's separate runtime ports.
    """

    @property
    def directory(self) -> Path: ...

    @property
    def compilation(self) -> RecursiveCompilation: ...

    @property
    def authoring(self) -> CanonicalRecord: ...

    @property
    def context(self) -> RecursiveCandidateContextProvider: ...

    @property
    def projection(self) -> object: ...

    @property
    def resources(self) -> object: ...


HandoffT = TypeVar("HandoffT", bound=ProspectiveHandoff)


class ExperimentHandoffBinder(Protocol):
    def __call__(self, handoff: HandoffT, *, specification: CanonicalRecord,
                 allocation: UnitAllocation, source_records: tuple[tuple[str, CanonicalRecord], ...],
                 artifact_writer: ArtifactWriter, reveal_authority_id: str | None = None) -> HandoffT: ...


class AccessibleExperimentHandoffBinder(Protocol):
    def __call__(self, handoff: HandoffT, *, specification: CanonicalRecord,
                 allocation: UnitAllocation, source_records: tuple[tuple[str, CanonicalRecord], ...],
                 artifact_writer: ArtifactWriter, reveal_authority_id: str | None = None,
                 original_input_access: ProspectiveOriginalInputAccess | None = None,
                 read_access: ReadAccessSelection | None = None) -> HandoffT: ...


class ExperimentAuthoringPreparer(Protocol):
    def __call__(self, preparation: ExperimentPreparation, *, project_root: Path,
                 artifact_writer: ArtifactWriter, output_dir: Path) -> ExperimentPreparation: ...


class SelectedAccessAuthoringPreparer(Protocol):
    def __call__(self, preparation: ExperimentPreparation, *, project_root: Path,
                 artifact_writer: ArtifactWriter, output_dir: Path,
                 read_access: ReadAccessSelection | None = None) -> ExperimentPreparation: ...


class OriginalAccessAuthoringPreparer(Protocol):
    def __call__(self, preparation: ExperimentPreparation, *, project_root: Path,
                 artifact_writer: ArtifactWriter, output_dir: Path,
                 read_access: ReadAccessSelection | None = None,
                 original_input_access: OriginalInputAccess | None = None) -> ExperimentPreparation: ...


class ProspectiveResultReader(Protocol):
    def __call__(self, *, selected: RetainedProspectiveSelection, artifact_writer: ArtifactWriter,
                 run_id: str, reveal_authority_id: str | None = None,
                 allow_partial: bool = False) -> ExperimentReport: ...


class AccessibleProspectiveResultReader(Protocol):
    def __call__(self, *, selected: RetainedProspectiveSelection, artifact_writer: ArtifactWriter,
                 run_id: str, reveal_authority_id: str | None = None, allow_partial: bool = False,
                 read_access: ReadAccessSelection | None = None) -> ExperimentReport: ...


class IncompleteProspectiveResultReader(Protocol):
    def __call__(self, *, selected: RetainedProspectiveSelection, artifact_writer: ArtifactWriter,
                 run_id: str, reveal_authority_id: str | None = None, allow_partial: bool = False,
                 assess_incomplete: bool = False) -> ExperimentReport: ...


class AccessibleIncompleteProspectiveResultReader(Protocol):
    def __call__(self, *, selected: RetainedProspectiveSelection, artifact_writer: ArtifactWriter,
                 run_id: str, reveal_authority_id: str | None = None, allow_partial: bool = False,
                 assess_incomplete: bool = False,
                 read_access: ReadAccessSelection | None = None) -> ExperimentReport: ...


class DevelopmentRuntimeBinder(Protocol):
    def __call__(self, *, supplier: RecursiveInputSupplier, writer: ArtifactWriter, directory: Path,
                 plan: ProtocolExecutionPlan,
                 output_codecs: Mapping[str, type[CanonicalRecord]]) -> RecursiveInputSupplier: ...


class AccessibleDevelopmentRuntimeBinder(Protocol):
    def __call__(self, *, supplier: RecursiveInputSupplier, writer: ArtifactWriter, directory: Path,
                 plan: ProtocolExecutionPlan, output_codecs: Mapping[str, type[CanonicalRecord]],
                 payloads: Mapping[str, bytes] | None = None,
                 read_access: ReadAccessSelection | None = None) -> RecursiveInputSupplier: ...


class DualRouteDevelopmentRuntimeBinder(Protocol):
    """The prospective declaration's separately checked exposed development route."""

    def __call__(self, *, specification: CanonicalRecord, supplier: RecursiveInputSupplier,
                 writer: ArtifactWriter, directory: Path, plan: ProtocolExecutionPlan,
                 output_codecs: Mapping[str, type[CanonicalRecord]]) -> RecursiveInputSupplier: ...


class ProgrammeServiceFactory(Protocol):
    def __call__(self, *, service: ExperimentServiceContext,
                 descriptor: ExperimentProgrammeDescriptor | None) -> CompositeProgrammeService: ...


class ExperimentInputDeriver(Protocol):
    def __call__(self, *, specification: CanonicalRecord, source_selection_path: Path, project_root: Path,
                 artifact_writer: ArtifactWriter, metadata_directory: Path, output_selection_path: Path,
                 execution: ExecutionSelection) -> ExperimentInputDerivationResult: ...


class AccessibleExperimentInputDeriver(Protocol):
    def __call__(self, *, specification: CanonicalRecord, source_selection_path: Path, project_root: Path,
                 artifact_writer: ArtifactWriter, metadata_directory: Path, output_selection_path: Path,
                 execution: ExecutionSelection,
                 read_access: ReadAccessSelection | None = None) -> ExperimentInputDerivationResult: ...


class DevelopmentProductExporter(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter,
                 selection_path: Path) -> ExperimentReport: ...


class AccessibleDevelopmentProductExporter(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, selection_path: Path,
                 read_access: ReadAccessSelection | None = None) -> ExperimentReport: ...


class ProspectiveProductExporter(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, selection_path: Path,
                 selected: RetainedProspectiveSelection, project_root: Path) -> ExperimentReport: ...


class DevelopmentResultReader(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, specification: CanonicalRecord,
                 instance: ExperimentInstanceBinding, payloads: Mapping[str, bytes], report: ExperimentReport,
                 products: Mapping[str, object], draft: RecursiveStudyDraft, plan: ProtocolExecutionPlan,
                 allow_partial: bool = False) -> ExperimentReport: ...


class AccessibleDevelopmentResultReader(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, specification: CanonicalRecord,
                 instance: ExperimentInstanceBinding, payloads: Mapping[str, bytes], report: ExperimentReport,
                 products: Mapping[str, object], draft: RecursiveStudyDraft, plan: ProtocolExecutionPlan,
                 allow_partial: bool = False, read_access: ReadAccessSelection | None = None) -> ExperimentReport: ...


class ExperimentInstanceAuthenticator(Protocol):
    def __call__(self, *, specification: CanonicalRecord, allocation: UnitAllocation,
                 draft: RecursiveStudyDraft, source_records: tuple[tuple[str, CanonicalRecord], ...],
                 artifact_writer: ArtifactWriter) -> None: ...


class DevelopmentResultCompleter(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, project_root: Path,
                 maximum_parallel_tasks: int, specification: CanonicalRecord, instance: ExperimentInstanceBinding,
                 payloads: Mapping[str, bytes], draft: RecursiveStudyDraft, plan: ProtocolExecutionPlan,
                 scheduler_result: SchedulerResult) -> ExperimentReport: ...


class AccessibleDevelopmentResultCompleter(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, project_root: Path,
                 maximum_parallel_tasks: int, specification: CanonicalRecord, instance: ExperimentInstanceBinding,
                 payloads: Mapping[str, bytes], draft: RecursiveStudyDraft, plan: ProtocolExecutionPlan,
                 scheduler_result: SchedulerResult,
                 read_access: ReadAccessSelection | None = None) -> ExperimentReport: ...


class DevelopmentReadAccessValidator(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, specification: CanonicalRecord,
                 instance: ExperimentInstanceBinding, payloads: Mapping[str, bytes], draft: RecursiveStudyDraft,
                 plan: ProtocolExecutionPlan, read_access: ReadAccessSelection | None) -> None: ...


class AuthoringReadAccessValidator(Protocol):
    def __call__(self, *, preparation: ExperimentPreparation, artifact_writer: ArtifactWriter,
                 read_access: ReadAccessSelection | None) -> None: ...


class DevelopmentInputAccessBootstrap(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, specification: CanonicalRecord,
                 instance: ExperimentInstanceBinding, packet: AuthoredRecursiveWave,
                 read_member: OriginalMemberReader,
                 read_access: ReadAccessSelection | None = None) -> OriginalInputAccess: ...


class AuthoringInputAccessBootstrap(Protocol):
    def __call__(self, *, preparation: ExperimentPreparation, artifact_writer: ArtifactWriter,
                 read_access: ReadAccessSelection | None = None) -> OriginalInputAccess | None: ...


class SelectedInputAccessBootstrap(Protocol):
    def __call__(self, *, specification: CanonicalRecord,
                 selection: ExperimentInputSelection | ExperimentFileInputSelection,
                 read_locator: SelectedLocatorReader, artifact_writer: ArtifactWriter | None,
                 read_access: ReadAccessSelection | None = None,
                 selection_path: Path | None = None) -> CurrentAccessGuard: ...


class ExperimentReadAccessSelector(Protocol):
    def __call__(self, records: tuple[CanonicalRecord, ...]) -> ReadAccessSelection: ...


class ProspectiveInputAccessBootstrap(Protocol):
    def __call__(self, *, directory: Path, artifact_writer: ArtifactWriter, specification: CanonicalRecord,
                 instance: ExperimentInstanceBinding, association: ProspectiveExperimentAssociation,
                 read_member: OriginalMemberReader,
                 read_access: ReadAccessSelection | None = None) -> ProspectiveOriginalInputAccess: ...


class ProspectiveDesignInputDeriver(Protocol):
    def __call__(self, preparation: ExperimentPreparation) -> RecursiveProspectiveDesignInputs: ...


class ServiceExperimentInputDeriver(Protocol):
    def __call__(self, *, service: ExperimentServiceContext, specification: CanonicalRecord,
                 source_selection_path: Path, metadata_directory: Path, output_selection_path: Path,
                 execution: ExecutionSelection) -> ExperimentInputDerivationResult: ...


class AccessibleServiceExperimentInputDeriver(Protocol):
    def __call__(self, *, service: ExperimentServiceContext, specification: CanonicalRecord,
                 source_selection_path: Path, metadata_directory: Path, output_selection_path: Path,
                 execution: ExecutionSelection,
                 read_access: ReadAccessSelection | None = None) -> ExperimentInputDerivationResult: ...


PrepareHook: TypeAlias = ExperimentPrepare | ExperimentPrepareWithMethods
InputBinderHook: TypeAlias = (ExperimentInputBinder | ExperimentFileInputBinder
                             | ExperimentLocatedInputBinder | ExperimentLocatedFileInputBinder)
HandoffBinderHook: TypeAlias = ExperimentHandoffBinder | AccessibleExperimentHandoffBinder
AuthoringPreparerHook: TypeAlias = (ExperimentAuthoringPreparer | SelectedAccessAuthoringPreparer
                                  | OriginalAccessAuthoringPreparer)
ProspectiveReaderHook: TypeAlias = (ProspectiveResultReader | AccessibleProspectiveResultReader
                                  | IncompleteProspectiveResultReader | AccessibleIncompleteProspectiveResultReader)
DevelopmentBinderHook: TypeAlias = (DevelopmentRuntimeBinder | AccessibleDevelopmentRuntimeBinder
                                   | DualRouteDevelopmentRuntimeBinder)
InputDeriverHook: TypeAlias = ExperimentInputDeriver | AccessibleExperimentInputDeriver
ProductExporterHook: TypeAlias = (DevelopmentProductExporter | AccessibleDevelopmentProductExporter
                                 | ProspectiveProductExporter)
DevelopmentReaderHook: TypeAlias = DevelopmentResultReader | AccessibleDevelopmentResultReader
DevelopmentCompleterHook: TypeAlias = DevelopmentResultCompleter | AccessibleDevelopmentResultCompleter
ServiceInputDeriverHook: TypeAlias = ServiceExperimentInputDeriver | AccessibleServiceExperimentInputDeriver
