# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='matrix-geometry',
                          schema_id='empirical-lawhood/matrix-geometry/scan-input',
                          record_module='empirical_lawhood.domains.matrix.matrix_response_study.geometry_records',
                          record_name='MatrixGeometryScanInput',
                          disposition='editable',
                          maximum_bytes=8388608,
                          requires_canonical=True,
                          command='campaign matrix-geometry-prove',
                          owner='MatrixGeometryScanInput',
                          supplied_inputs=('programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json',)),)
