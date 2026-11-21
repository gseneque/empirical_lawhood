# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='battery-development',
                          schema_id='empirical-lawhood/simulators/py-ba-mm-development-input',
                          record_module='empirical_lawhood.adapters.simulators.pybamm_development_input',
                          record_name='PyBaMMDevelopmentInput',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign battery-native-check',
                          owner='PyBaMMDevelopmentInput',
                          supplied_inputs=('programmes/energy/battery-charging/workflows/battery-response-and-restart/config.json',)),)
