# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='response-composition-input',
                          schema_id='empirical-lawhood/composition/response-composition/response-composition-input',
                          record_module='empirical_lawhood.domains.matrix.response_composition.authoring.input',
                          record_name='ResponseCompositionInput',
                          disposition='editable',
                          maximum_bytes=16384,
                          requires_canonical=False,
                          command='campaign response-composition-input-check',
                          owner='ResponseCompositionInput',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/causal-transfer-audit/analysis-input.json',)),)
