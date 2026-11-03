"""Artifact, catalog, execution, and environment implementations.

Public aggregate exports load their existing owner on demand. A raw progress
child can import the byte transport without loading catalogue or approval code.
"""

from importlib import import_module
from typing import Any

_EXPORT_MODULES = {
    'CATALOG_MUTATION_LOCK_FILENAME': '.catalog_mutation',
    'CatalogMutationLock': '.catalog_mutation',
    'CatalogMutationLockError': '.catalog_mutation',
    'CatalogMutationLockUnavailable': '.catalog_mutation',
    'CatalogRebuildError': '.catalog_rebuild',
    'CatalogRebuildResult': '.catalog_rebuild',
    'CleanRepositoryCommitPreflight': '.dataset_operations',
    'DatasetCatalogAuthorityBundle': '.dataset_catalog_authority',
    'DatasetCatalogAuthorityError': '.dataset_catalog_authority',
    'DatasetCatalogReadSessionProvider': '.dataset_catalog_access',
    'DatasetProjectionRebuildInstaller': '.dataset_rebuild',
    'DatasetStorageRootRegistry': '.dataset_operations',
    'Ed25519DatasetAuthorizationSigner': '.authority',
    'ExecutionErrorKind': '.execution',
    'ExecutionResourceAdmission': '.execution',
    'ExecutionResourceCapacity': '.execution',
    'ExternalDatasetCatalogAuthorityLoader': '.dataset_catalog_authority',
    'ExternalDatasetOperationAuthorityStore': '.dataset_operations',
    'ExternalDatasetProjectionRebuildAuthorityStore': '.dataset_rebuild',
    'ExternalExecutionBackendKind': '.external_execution',
    'ExternalExecutionError': '.external_execution',
    'ExternalRunRecoveryStore': '.recovery',
    'ExternalWorkerTransport': '.external_execution',
    'ExternalWorkerUnavailable': '.external_execution',
    'LocalCatalogTargetInspector': '.dataset_rebuild',
    'LocalExecutionResourceAdmitter': '.execution',
    'RegisteredExecutionBackend': '.external_execution',
    'RegisteredExternalTaskExecutor': '.external_execution',
    'RepositoryArtifactSpec': '.repository_identity',
    'RepositoryIdentityError': '.repository_identity',
    'ResourceAdmissionError': '.execution',
    'RunRecoveryError': '.recovery',
    'decode_dataset_catalog_snapshot': '.dataset_projection',
    'decode_dataset_record_json': '.dataset_projection',
    'decode_run_recovery_index': '.recovery',
    'decode_run_recovery_terminal_event': '.recovery',
    'decode_task_recovery_event': '.recovery',
    'decode_unified_catalog_snapshot': '.dataset_projection',
    'encode_dataset_catalog_snapshot': '.dataset_projection',
    'encode_unified_catalog_snapshot': '.dataset_projection',
    'load_clean_repository_artifacts': '.repository_identity',
    'load_local_dataset_projection_receipt_reference': '.dataset_catalog_access',
    'production_catalog_mutation_lock': '.catalog_mutation',
    'production_catalog_mutation_lock_path': '.catalog_mutation',
    'rebuild_production_catalog': '.catalog_rebuild',
}

__all__ = ['CATALOG_MUTATION_LOCK_FILENAME', 'CatalogMutationLock', 'CatalogMutationLockError', 'CatalogMutationLockUnavailable', 'CatalogRebuildError', 'CatalogRebuildResult', 'CleanRepositoryCommitPreflight', 'DatasetCatalogAuthorityBundle', 'DatasetCatalogAuthorityError', 'DatasetCatalogReadSessionProvider', 'load_local_dataset_projection_receipt_reference', 'DatasetStorageRootRegistry', 'DatasetProjectionRebuildInstaller', 'Ed25519DatasetAuthorizationSigner', 'decode_dataset_catalog_snapshot', 'decode_dataset_record_json', 'decode_unified_catalog_snapshot', 'encode_dataset_catalog_snapshot', 'encode_unified_catalog_snapshot', 'ExternalExecutionBackendKind', 'ExternalExecutionError', 'ExternalRunRecoveryStore', 'ExternalDatasetCatalogAuthorityLoader', 'ExternalDatasetOperationAuthorityStore', 'ExternalDatasetProjectionRebuildAuthorityStore', 'ExternalWorkerTransport', 'ExternalWorkerUnavailable', 'ExecutionErrorKind', 'ExecutionResourceAdmission', 'ExecutionResourceCapacity', 'LocalExecutionResourceAdmitter', 'LocalCatalogTargetInspector', 'ResourceAdmissionError', 'RegisteredExecutionBackend', 'RegisteredExternalTaskExecutor', 'RepositoryArtifactSpec', 'RepositoryIdentityError', 'RunRecoveryError', 'decode_run_recovery_index', 'decode_run_recovery_terminal_event', 'decode_task_recovery_event', 'load_clean_repository_artifacts', 'production_catalog_mutation_lock', 'production_catalog_mutation_lock_path', 'rebuild_production_catalog']


def __getattr__(name: str) -> Any:
    owner = _EXPORT_MODULES.get(name)
    if owner is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(owner, __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
