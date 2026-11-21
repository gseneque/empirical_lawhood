# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='preparation-applicability-selection',
                          schema_id='empirical-lawhood/composition/preparation-applicability/selection',
                          record_module='empirical_lawhood.domains.matrix.preparation_applicability.authoring.selection',
                          record_name='PreparationApplicabilitySelection',
                          disposition='editable',
                          maximum_bytes=4194304,
                          requires_canonical=True,
                          command='campaign preparation-author',
                          owner='PreparationApplicabilitySelection',
                          supplied_inputs=()),)
