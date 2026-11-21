# SPDX-License-Identifier: MPL-2.0
"""Public application exports, loaded only when an operation needs them.

Importing a small authoring or diagnostic contract does not build the complete
scientific catalogue or inspect any execution prerequisites.
"""

from importlib import import_module

_EXPORTS = {
    'AcquisitionState': ('empirical_lawhood.design.datasets', 'AcquisitionState'),
    'AdvanceStudyBundleRequest': ('empirical_lawhood.api.results', 'AdvanceStudyBundleRequest'),
    'ApiError': ('empirical_lawhood.api.results', 'ApiError'),
    'ApiResult': ('empirical_lawhood.api.results', 'ApiResult'),
    'AssembleExperimentPackageRequest': ('empirical_lawhood.api.results', 'AssembleExperimentPackageRequest'),
    'AttemptHistorySummary': ('empirical_lawhood.api.execution', 'AttemptHistorySummary'),
    'AuthoringCodecError': ('empirical_lawhood.api.codecs', 'AuthoringCodecError'),
    'AuthorizationSummary': ('empirical_lawhood.api.models', 'AuthorizationSummary'),
    'BindElapsedBudgetRequest': ('empirical_lawhood.api.results', 'BindElapsedBudgetRequest'),
    'CampaignAuthorityRequired': ('empirical_lawhood.api.models', 'CampaignAuthorityRequired'),
    'CampaignMaintenanceInterruptionRequest': ('empirical_lawhood.api.results', 'CampaignMaintenanceInterruptionRequest'),
    'CampaignMaintenanceStopRequest': ('empirical_lawhood.api.results', 'CampaignMaintenanceStopRequest'),
    'CampaignStatusRequest': ('empirical_lawhood.api.results', 'CampaignStatusRequest'),
    'CapabilityKind': ('empirical_lawhood.execution.capabilities', 'CapabilityKind'),
    'CapabilityListRequest': ('empirical_lawhood.api.results', 'CapabilityListRequest'),
    'CapabilityListSummary': ('empirical_lawhood.api.models', 'CapabilityListSummary'),
    'CapabilityShowRequest': ('empirical_lawhood.api.results', 'CapabilityShowRequest'),
    'CapabilityShowSummary': ('empirical_lawhood.api.models', 'CapabilityShowSummary'),
    'CatalogObjectSummary': ('empirical_lawhood.api.models', 'CatalogObjectSummary'),
    'CatalogQueryRequest': ('empirical_lawhood.api.results', 'CatalogQueryRequest'),
    'CatalogQuerySummary': ('empirical_lawhood.api.models', 'CatalogQuerySummary'),
    'CatalogRebuildRequest': ('empirical_lawhood.api.results', 'CatalogRebuildRequest'),
    'CatalogRebuildSummary': ('empirical_lawhood.api.models', 'CatalogRebuildSummary'),
    'CatalogSummary': ('empirical_lawhood.api.models', 'CatalogSummary'),
    'CheckReadinessRequest': ('empirical_lawhood.api.results', 'CheckReadinessRequest'),
    'CloseStudyBundleRequest': ('empirical_lawhood.api.results', 'CloseStudyBundleRequest'),
    'CompilationSummary': ('empirical_lawhood.api.models', 'CompilationSummary'),
    'CompileCampaignRequest': ('empirical_lawhood.api.results', 'CompileCampaignRequest'),
    'CompileCandidateRequest': ('empirical_lawhood.api.results', 'CompileCandidateRequest'),
    'CompileLinkedCampaignProfileRequest': ('empirical_lawhood.api.results', 'CompileLinkedCampaignProfileRequest'),
    'CompileSourceProfileRequest': ('empirical_lawhood.api.results', 'CompileSourceProfileRequest'),
    'CompileStudyBundleRequest': ('empirical_lawhood.api.results', 'CompileStudyBundleRequest'),
    'CompileStudyRequest': ('empirical_lawhood.api.results', 'CompileStudyRequest'),
    'CustodyState': ('empirical_lawhood.design.datasets', 'CustodyState'),
    'DatabaseMutationRequest': ('empirical_lawhood.api.results', 'DatabaseMutationRequest'),
    'DatabaseMutationSummary': ('empirical_lawhood.api.models', 'DatabaseMutationSummary'),
    'DatasetBindingRole': ('empirical_lawhood.design.datasets', 'DatasetBindingRole'),
    'DatasetCatalogRecordKind': ('empirical_lawhood.execution.datasets', 'DatasetCatalogRecordKind'),
    'DatasetCatalogRecordSummary': ('empirical_lawhood.api.models', 'DatasetCatalogRecordSummary'),
    'DatasetListRequest': ('empirical_lawhood.api.results', 'DatasetListRequest'),
    'DatasetListSummary': ('empirical_lawhood.api.models', 'DatasetListSummary'),
    'DatasetManifestRequest': ('empirical_lawhood.api.results', 'DatasetManifestRequest'),
    'DatasetManifestSummary': ('empirical_lawhood.api.models', 'DatasetManifestSummary'),
    'DatasetOperationPreviewRequest': ('empirical_lawhood.api.results', 'DatasetOperationPreviewRequest'),
    'DatasetOperationPreviewSummary': ('empirical_lawhood.api.models', 'DatasetOperationPreviewSummary'),
    'DatasetProjectionRebuildRequest': ('empirical_lawhood.api.results', 'DatasetProjectionRebuildRequest'),
    'DatasetProjectionRebuildSummary': ('empirical_lawhood.api.models', 'DatasetProjectionRebuildSummary'),
    'DatasetRegistrationRequest': ('empirical_lawhood.api.results', 'DatasetRegistrationRequest'),
    'DatasetRegistrationSummary': ('empirical_lawhood.api.models', 'DatasetRegistrationSummary'),
    'DatasetShowRequest': ('empirical_lawhood.api.results', 'DatasetShowRequest'),
    'DatasetShowSummary': ('empirical_lawhood.api.models', 'DatasetShowSummary'),
    'DatasetStoragePreflightSummary': ('empirical_lawhood.api.models', 'DatasetStoragePreflightSummary'),
    'DoctorActionReadiness': ('empirical_lawhood.api.models', 'DoctorActionReadiness'),
    'DoctorAuthorityBoundary': ('empirical_lawhood.api.models', 'DoctorAuthorityBoundary'),
    'DoctorBackendSummary': ('empirical_lawhood.api.models', 'DoctorBackendSummary'),
    'DoctorDependencySummary': ('empirical_lawhood.api.models', 'DoctorDependencySummary'),
    'DoctorSummary': ('empirical_lawhood.api.models', 'DoctorSummary'),
    'DocumentRequest': ('empirical_lawhood.api.results', 'DocumentRequest'),
    'DocumentSummary': ('empirical_lawhood.api.models', 'DocumentSummary'),
    'EmpiricalLawhoodApi': ('empirical_lawhood.api.facade', 'EmpiricalLawhoodApi'),
    'ErrorCategory': ('empirical_lawhood.api.results', 'ErrorCategory'),
    'ExecutableStudyCompilationSummary': ('empirical_lawhood.api.models', 'ExecutableStudyCompilationSummary'),
    'ExecutableStudyIssueSummary': ('empirical_lawhood.api.models', 'ExecutableStudyIssueSummary'),
    'ExperimentPackageAssemblySummary': ('empirical_lawhood.api.models', 'ExperimentPackageAssemblySummary'),
    'ExplorationCompilationSummary': ('empirical_lawhood.api.models', 'ExplorationCompilationSummary'),
    'ExplorationPortfolioSummary': ('empirical_lawhood.api.models', 'ExplorationPortfolioSummary'),
    'ExternalIdentifier': ('empirical_lawhood.design.datasets', 'ExternalIdentifier'),
    'ExternalIdentifierKind': ('empirical_lawhood.design.datasets', 'ExternalIdentifierKind'),
    'HypothesisSummary': ('empirical_lawhood.api.models', 'HypothesisSummary'),
    'IssueExtensionsRequest': ('empirical_lawhood.api.results', 'IssueExtensionsRequest'),
    'IssueStudyBundleRequest': ('empirical_lawhood.api.results', 'IssueStudyBundleRequest'),
    'IssueStudyRequest': ('empirical_lawhood.api.results', 'IssueStudyRequest'),
    'LinkedCampaignCompilationSummary': ('empirical_lawhood.api.models', 'LinkedCampaignCompilationSummary'),
    'MAX_DATASET_PAGE_RECORDS': ('empirical_lawhood.execution.datasets', 'MAX_DATASET_PAGE_RECORDS'),
    'MultiWorldStudyIssueSummary': ('empirical_lawhood.api.models', 'MultiWorldStudyIssueSummary'),
    'NominationSummary': ('empirical_lawhood.api.models', 'NominationSummary'),
    'OperationStatus': ('empirical_lawhood.api.results', 'OperationStatus'),
    'PreissueReadinessSummary': ('empirical_lawhood.api.models', 'PreissueReadinessSummary'),
    'ProposalSummary': ('empirical_lawhood.api.models', 'ProposalSummary'),
    'PublicSourceAcquisitionRequest': ('empirical_lawhood.api.results', 'PublicSourceAcquisitionRequest'),
    'PublicSourceAcquisitionSummary': ('empirical_lawhood.api.models', 'PublicSourceAcquisitionSummary'),
    'PublicSourceCustodySummary': ('empirical_lawhood.api.models', 'PublicSourceCustodySummary'),
    'ResumeCampaignRequest': ('empirical_lawhood.api.results', 'ResumeCampaignRequest'),
    'RunCampaignRequest': ('empirical_lawhood.api.results', 'RunCampaignRequest'),
    'RunExecutionSummary': ('empirical_lawhood.api.execution', 'RunExecutionSummary'),
    'RunStatusSummary': ('empirical_lawhood.api.execution', 'RunStatusSummary'),
    'ScientificInspectionSummary': ('empirical_lawhood.api.models', 'ScientificInspectionSummary'),
    'SourceProfileCompilationSummary': ('empirical_lawhood.api.models', 'SourceProfileCompilationSummary'),
    'StudyBundleCompilationSummary': ('empirical_lawhood.api.models', 'StudyBundleCompilationSummary'),
    'StudyBundleStatusRequest': ('empirical_lawhood.api.results', 'StudyBundleStatusRequest'),
    'StudyCompilationSummary': ('empirical_lawhood.api.models', 'StudyCompilationSummary'),
    'StudyIssueSummary': ('empirical_lawhood.api.models', 'StudyIssueSummary'),
    'SystemSummary': ('empirical_lawhood.api.models', 'SystemSummary'),
    'WriteEffectSummary': ('empirical_lawhood.api.models', 'WriteEffectSummary'),
    'create_api': ('empirical_lawhood.api.composition', 'create_api'),
    'create_cli_api': ('empirical_lawhood.api.composition', 'create_cli_api'),
    'create_inspection_api': ('empirical_lawhood.api.inspection', 'create_inspection_api'),
    'load_authoring': ('empirical_lawhood.api.codecs', 'load_authoring'),
    'loads_authoring': ('empirical_lawhood.api.codecs', 'loads_authoring'),
}

__all__ = tuple(_EXPORTS)


def __getattr__(name: str) -> object:
    try:
        module, member = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no public attribute {name!r}") from None
    value = getattr(import_module(module), member)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
