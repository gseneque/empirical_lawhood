# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='finite-canary',
                          schema_id='empirical-lawhood/simulators/finite-response-law/finite-response-law-canary',
                          record_module='empirical_lawhood.adapters.simulators.finite_response_law.native_quickstart',
                          record_name='FiniteResponseLawCanary',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign finite-response-native-check',
                          owner='FiniteResponseLawCanary',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/finite-response-law/finite-canary.json',)),)
