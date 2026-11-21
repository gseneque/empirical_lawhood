# SPDX-License-Identifier: MPL-2.0
"""Explicit controller and worker installation contracts; no environment probes."""

from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import WorkerEnvironment, WorkflowInstallationDeclaration

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id="isolated-native-starter-worker",
    python_version="3.11.14", distribution_versions=(("numpy", "2.3.5"),),
    lock_path="environments/isolated-native-starter/uv.lock", dependency_groups=()),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id="isolated-native-starter",
    profile_id="standard", adapter_module="empirical_lawhood.adapters.isolated_native_starter",
    adapter_version="1.0.0", controller_environment="base",
    workers=(WorkerEnvironment("calculation", "base", "explicit"),),
    source_prerequisites=("Select the locked controller and worker, source, operator profile and new external input, artifact and scratch paths.",)),
    WorkflowInstallationDeclaration(workflow_id="isolated-native-starter", profile_id="separate-numpy",
        adapter_module="empirical_lawhood.adapters.isolated_native_starter", adapter_version="1.0.0",
        controller_environment="base", workers=(WorkerEnvironment("calculation", "isolated-native-starter-worker", "explicit"),),
        source_prerequisites=("Select the separate locked NumPy worker and explicit exposed inputs and storage.",)),)
