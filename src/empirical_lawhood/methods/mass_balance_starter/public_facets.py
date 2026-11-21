# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import ExternalSoftware, WorkerEnvironment, WorkflowInstallationDeclaration  # noqa: F401

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='mass-balance',
                        python_version='3.11.14',
                        distribution_versions=(),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=(),
                        supported_platforms=(('Linux', 'x86_64'),)),)

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='mass-balance-starter',
                                 profile_id='standard',
                                 adapter_module='empirical_lawhood.methods.mass_balance_starter',
                                 adapter_version='1.0.0',
                                 controller_environment='mass-balance',
                                 workers=(),
                                 external_software=(),
                                 source_prerequisites=('Select canonical evidence, tolerance in kg, locked '
                                                       'source, operator profile and explicit external '
                                                       'destinations.',),
                                 continuing_source_prerequisites=(),
                                 descriptor_version='1.0.0'),)
