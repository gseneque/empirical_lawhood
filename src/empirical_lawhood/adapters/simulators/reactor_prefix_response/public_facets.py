# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='reactor-batch-input',
                          schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-batch-input',
                          record_module='empirical_lawhood.adapters.simulators.reactor_prefix_response.batch_input',
                          record_name='ReactorBatchInput',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign reactor-batch-input-check',
                          owner='ReactorBatchInput',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/reactor-response/batch-input.json',)),
 ConfigurationDeclaration(consumer='reactor-prepared-input',
                          schema_id='empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input',
                          record_module='empirical_lawhood.adapters.simulators.reactor_prefix_response.prepared_input',
                          record_name='ReactorPreparedInput',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign reactor-prepared-input-check',
                          owner='ReactorPreparedInput',
                          supplied_inputs=('programmes/foundations/measurement-and-response/workflows/reactor-response/causal-response-study-input.json',
                                           'programmes/foundations/measurement-and-response/workflows/reactor-response/feed-input.json',
                                           'programmes/foundations/measurement-and-response/workflows/reactor-response/finite-control-frontier-input.json',
                                           'programmes/foundations/measurement-and-response/workflows/reactor-response/local-input.json',
                                           'programmes/foundations/measurement-and-response/workflows/reactor-response/matched-replay-history-input.json',
                                           'programmes/foundations/measurement-and-response/workflows/reactor-response/regime-input.json',
                                           'programmes/foundations/measurement-and-response/workflows/reactor-response/selected-action-response-input.json',
                                           'programmes/foundations/measurement-and-response/workflows/reactor-response/staged-pulse-response-input.json')))
