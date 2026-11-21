# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='reactor-assigned-profile',
                          schema_id='empirical-lawhood/composition/reactor-prefix-response/assigned-reactor-authoring-profile',
                          record_module='empirical_lawhood.adapters.composition.reactor_prefix_response.fresh_authoring',
                          record_name='AssignedReactorAuthoringProfile',
                          disposition='retained',
                          maximum_bytes=67108864,
                          requires_canonical=True,
                          command='campaign reactor-author',
                          owner='AssignedReactorAuthoringProfile',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/reactor-assigned-exposed.json',)),
 ConfigurationDeclaration(consumer='reactor-fresh-profile',
                          schema_id='empirical-lawhood/composition/reactor-prefix-response/fresh-reactor-authoring-profile',
                          record_module='empirical_lawhood.adapters.composition.reactor_prefix_response.fresh_authoring',
                          record_name='FreshReactorAuthoringProfile',
                          disposition='editable',
                          maximum_bytes=67108864,
                          requires_canonical=True,
                          command='campaign reactor-author',
                          owner='FreshReactorAuthoringProfile',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/reactor-response/profile.json',)))
