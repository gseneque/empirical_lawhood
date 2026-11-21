# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='rubisco-kinetic-query',
                          schema_id='empirical-lawhood/simulators/rubisco-assay/query',
                          record_module='empirical_lawhood.domains.rubisco.assay.records',
                          record_name='AssayQuery',
                          disposition='retained',
                          maximum_bytes=None,
                          requires_canonical=True,
                          command='campaign recursive-author',
                          owner='AssayQuery',
                          supplied_inputs=('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/query.json',)),)
