# SPDX-License-Identifier: MPL-2.0
"""Compatibility routes for current Matrix consumers of shared observation.

Source/lock capture has one shared owner. These Matrix entry points retain the
selected domain numerical predicate and historical producing bytes.
"""

from pathlib import Path

from empirical_lawhood.api.numerical_provenance import (
    authenticate_recorded_numerical_provenance, capture_numerical_provenance,
    numerical_package_code_sha256, numerical_package_sources,
    numerical_runtime_observation, selected_dependency_lock_sha256,
)

# Retained imports for named Matrix consumers, not a second implementation.
__all__ = ("authenticate_recorded_matrix_provenance", "capture_matrix_provenance",
    "matrix_native_runtime_observation", "numerical_package_code_sha256",
    "numerical_package_sources", "preflight_matrix_output_directory",
    "selected_dependency_lock_sha256")


def matrix_native_runtime_observation():
    from empirical_lawhood.api.matrix_native_custody import MatrixNativeRuntimeObservation
    from empirical_lawhood.kernel.serialization import canonical_json_bytes

    observation = numerical_runtime_observation()
    MatrixNativeRuntimeObservation(canonical_json_bytes(observation).decode())
    return observation


def preflight_matrix_output_directory(*, directory, artifact_writer, project_root,
                                      allow_existing_empty=False):
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    return preflight_authoring_output_directory(directory=Path(directory), repo_root=Path(project_root),
        artifact_writer=artifact_writer, allow_existing_empty=allow_existing_empty)


def capture_matrix_provenance(*, project_root, expected_code_sha256=None, expected_lock_sha256=None,
        _admitted_source=None):
    arguments = {} if _admitted_source is None else {"_admitted_source": _admitted_source}
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=expected_code_sha256, expected_lock_sha256=expected_lock_sha256, **arguments)
    return authenticate_recorded_matrix_provenance(provenance)


def authenticate_recorded_matrix_provenance(provenance):
    from empirical_lawhood.api.matrix_native_custody import MatrixNativeRuntimeObservation

    authenticate_recorded_numerical_provenance(provenance)
    MatrixNativeRuntimeObservation(provenance.runtime_observation_json)
    return provenance
