# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='reaction-development',
                          schema_id='empirical-lawhood/reaction-diffusion-development/reaction-diffusion-development-input',
                          record_module='empirical_lawhood.adapters.simulators.reaction_diffusion_development_input',
                          record_name='ReactionDiffusionDevelopmentInput',
                          disposition='editable',
                          maximum_bytes=32768,
                          requires_canonical=False,
                          command='campaign reaction-response-native-check',
                          owner='ReactionDiffusionDevelopmentInput',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/reaction-diffusion-response/config.json',
                                           'programmes/foundations/measurement-and-response/workflows/reactor-flow-response/config.json')),)
