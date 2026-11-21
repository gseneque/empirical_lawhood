# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='prepared-canary',
                          schema_id='empirical-lawhood/simulators/prepared-response/prepared-response-prepared-canary',
                          record_module='empirical_lawhood.adapters.simulators.prepared_response.native_quickstart',
                          record_name='PreparedResponsePreparedCanary',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign prepared-response-native-check',
                          owner='PreparedResponsePreparedCanary',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/prepared-response/prepared-canary.json',)),)
