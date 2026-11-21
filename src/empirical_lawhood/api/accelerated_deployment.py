# SPDX-License-Identifier: MPL-2.0
"""Compose deployment, authorized supervision and original transport services."""

import json
import os
from pathlib import Path

from empirical_lawhood.execution.progress import progress_operation

from empirical_lawhood.api.configuration import load_configuration_record
from empirical_lawhood.execution.remote.accelerated_deployment import RunpodDeploymentSelection, prepare_runpod_task
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.deployment_archive import archive_original_tree, verify_original_archive
from empirical_lawhood.execution.remote.deployment_supervision import (
    observe_deployment_budget as _observe_deployment_budget,
    supervise_deployment as _supervise_deployment,
)
from empirical_lawhood.adapters.cloud.runpod_budget import RunpodBudgetObserver
from empirical_lawhood.adapters.cloud.skypilot_budget import SkyPilotBudgetActions
from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_backend import (
    BACKEND as PERIODIC_CUDA_BACKEND, REFERENCE_MM_BACKEND as PERIODIC_REFERENCE_MM_BACKEND,
)
from empirical_lawhood.execution.local.worker_environment_restore import restore_worker_environment
from empirical_lawhood.execution.compute_backend import JAX_TORAX_BACKEND
from empirical_lawhood.execution.remote.worker_profiles import hosted_worker_profile


@progress_operation("deployment.prepare_accelerated_deployment")
def prepare_accelerated_deployment(selection_path, *, payload_root, output_directory):
    """Prepare a selected path or public typed selection; never contact a provider."""
    selected = (selection_path if type(selection_path) is RunpodDeploymentSelection
        else RunpodDeploymentSelection.from_document(json.loads(
            read_bounded_bytes(Path(selection_path), maximum_bytes=128*1024))))
    hosted_worker_profile(selected.numerical_backend)
    configuration = load_configuration_record(Path(payload_root)/selected.operational_config,
        consumer='operational-configuration')
    if not configuration.accelerated_compute:
        raise ValueError('accelerated deployment requires accelerated_compute: true in its selected operational input')
    return prepare_runpod_task(selected, payload_root=payload_root, output_directory=output_directory)


def _deployment_observer(selected):
    return RunpodBudgetObserver(selected, credential=os.environ.get('RUNPOD_API_KEY'))


@progress_operation("deployment.observe_deployment_budget")
def observe_deployment_budget(selection_path, *, output_directory):
    """Compose read-only provider observation with the shared custody owner."""
    return _observe_deployment_budget(selection_path, output_directory=output_directory,
        observer_factory=_deployment_observer)


@progress_operation("deployment.supervise_deployment")
def supervise_deployment(selection_path, *, output_directory, **kwargs):
    """Bind cloud adapters to the ordinary authorized supervision lifecycle."""
    return _supervise_deployment(selection_path, output_directory=output_directory,
        observer_factory=_deployment_observer, action_factory=SkyPilotBudgetActions, **kwargs)


__all__ = ['PERIODIC_CUDA_BACKEND', 'PERIODIC_REFERENCE_MM_BACKEND', 'JAX_TORAX_BACKEND', 'RunpodDeploymentSelection', 'prepare_accelerated_deployment',
    'archive_original_tree', 'verify_original_archive', 'observe_deployment_budget', 'supervise_deployment',
    'restore_worker_environment']
