# SPDX-License-Identifier: MPL-2.0
"""Static installation facts reuse the original locked mass-balance environment."""

from empirical_lawhood.execution.installation_descriptors import WorkflowInstallationDeclaration

WORKFLOW_INSTALLATIONS = (WorkflowInstallationDeclaration(workflow_id='mass-balance-record-upgrade',
    profile_id='standard', adapter_module='empirical_lawhood.methods.mass_balance_revision',
    adapter_version='1.0.0', controller_environment='mass-balance', workers=(), external_software=(),
    source_prerequisites=('Select a complete retained exposed version-1 mass forecast and assessment, '
        'their current access profile, locked source and explicit derivative destinations.',),
    continuing_source_prerequisites=(), descriptor_version='1.0.0'),)
