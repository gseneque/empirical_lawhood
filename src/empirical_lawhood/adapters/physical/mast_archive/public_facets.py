# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='fair-mast-selection',
                          schema_id='empirical-lawhood/physical/mast-archive/fair-mast-public-selection',
                          record_module='empirical_lawhood.adapters.physical.mast_archive.fresh_source',
                          record_name='FairMastPublicSelection',
                          disposition='editable',
                          maximum_bytes=65536,
                          requires_canonical=True,
                          command='source acquire',
                          owner='FairMastPublicSelection',
                          supplied_inputs=('programmes/energy/fusion/workflows/fair-mast-source/fair-mast-level2.json',)),)
