# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.discovery_descriptors import ConfigurationDeclaration

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='rubisco-prediction',
                        python_version='3.11.14',
                        distribution_versions=(('rapidfuzz', '3.14.3'),
                                               ('numpy', '2.4.6'),
                                               ('scipy', '1.17.1')),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=('rubisco-prediction',),
                        supported_platforms=(('Linux', 'x86_64'),)),)

CONFIGURATION_DECLARATIONS = (ConfigurationDeclaration(consumer='rubisco-kinetic-supply',
                          schema_id='empirical-lawhood/rubisco/kinetic-supply/joint-supply',
                          record_module='empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_supply',
                          record_name='JointKineticSupply',
                          disposition='retained',
                          maximum_bytes=None,
                          requires_canonical=True,
                          command='campaign recursive-author',
                          owner='JointKineticSupply',
                          supplied_inputs=('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/supply.json',)),
 ConfigurationDeclaration(consumer='rubisco-kinetic-comparison',
                          schema_id='empirical-lawhood/rubisco/kinetic-supply/target-comparison',
                          record_module='empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_supply',
                          record_name='KineticTargetComparison',
                          disposition='retained',
                          maximum_bytes=None,
                          requires_canonical=True,
                          command='campaign recursive-author',
                          owner='KineticTargetComparison',
                          supplied_inputs=('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/comparison.json',)))
