# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='selected-parent',
                          schema_id='empirical-lawhood/selected-events/parent-request',
                          record_module='empirical_lawhood.domains.matrix.matrix_response_study.selected_event_records',
                          record_name='MatrixSelectedParentRequest',
                          disposition='editable',
                          maximum_bytes=1048576,
                          requires_canonical=True,
                          command='campaign selected-parent-reconstruct',
                          owner='MatrixSelectedParentRequest',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',)),
 ConfigurationDeclaration(consumer='selected-events',
                          schema_id='empirical-lawhood/selected-events/input',
                          record_module='empirical_lawhood.domains.matrix.matrix_response_study.selected_event_records',
                          record_name='MatrixSelectedEventInput',
                          disposition='editable',
                          maximum_bytes=16777216,
                          requires_canonical=True,
                          command='campaign selected-events-run',
                          owner='MatrixSelectedEventInput',
                          supplied_inputs=()))
