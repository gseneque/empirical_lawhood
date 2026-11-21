# SPDX-License-Identifier: MPL-2.0
"""Code-owned public facts; discovery performs no scientific or prerequisite work."""

from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration

ENVIRONMENT_DECLARATIONS = (EnvironmentDeclaration(route_id='open-simulators',
                        python_version='3.11.14',
                        distribution_versions=(('gymtorax', '1.1.1'),
                                               ('torax', '1.4.2'),
                                               ('jax', '0.10.2'),
                                               ('jaxlib', '0.10.2'),
                                               ('numpy', '2.4.6'),
                                               ('scipy', '1.17.1'),
                                               ('xarray', '2026.7.0'),
                                               ('pybamm', '26.6.2.0')),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=('open-simulators',),
                        supported_platforms=(('Linux', 'x86_64'),)),
 EnvironmentDeclaration(route_id='reaction-response',
                        python_version='3.11.14',
                        distribution_versions=(('cantera', '3.2.0'), ('fipy', '4.0.3')),
                        lock_path='uv.lock',
                        python_implementation='CPython',
                        descriptor_version='1.0.0',
                        dependency_groups=('reaction-response-simulators',),
                        supported_platforms=(('Linux', 'x86_64'),)))
