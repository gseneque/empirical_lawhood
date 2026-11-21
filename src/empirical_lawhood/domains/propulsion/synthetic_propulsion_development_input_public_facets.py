# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='propulsion-reference',
                          schema_id='empirical-lawhood/methods/synthetic-propulsion-development-input',
                          record_module='empirical_lawhood.domains.propulsion.synthetic_propulsion_development_input',
                          record_name='SyntheticPropulsionDevelopmentInput',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign propulsion-reference-check',
                          owner='SyntheticPropulsionDevelopmentInput',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/propulsion-reliability-reference/config.json',)),)
