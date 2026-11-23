# SPDX-License-Identifier: MPL-2.0
"""Closed artifact profiles shared by current public integration composition."""

from functools import cache

from empirical_lawhood.domains.history.simulator_morphism_challenges.authoring import ARRAY_PAYLOAD_SCHEMA
from empirical_lawhood.storage.artifact_validation import ArtifactProfileValidatorRegistry, NumpyArrayContract
from empirical_lawhood.api.recursive_operations import operation_storage_codecs


def _integration_validators() -> ArtifactProfileValidatorRegistry:
    return ArtifactProfileValidatorRegistry(binary_codecs=operation_storage_codecs(),
        numpy_contracts=(NumpyArrayContract(ARRAY_PAYLOAD_SCHEMA, "float64", (None,)),))


# Preserve every default production profile and the one exact RC array shape.
# No generic NumPy, Arrow, Parquet or HDF5 admission is introduced.
INTEGRATION_ARTIFACT_PROFILE_VALIDATORS = _integration_validators()


@cache
def _finite_response_validators() -> ArtifactProfileValidatorRegistry:
    from empirical_lawhood.adapters.simulators.finite_response_law.native_pair_profile import finite_response_pair_contract

    return ArtifactProfileValidatorRegistry(hdf5_contracts=(finite_response_pair_contract(),))


def integration_artifact_profile_validators(family: str | None = None) -> ArtifactProfileValidatorRegistry:
    """Return the code-owned registry; custody and current authority stay separate."""
    if family == "finite-response-law":
        return _finite_response_validators()
    return INTEGRATION_ARTIFACT_PROFILE_VALIDATORS
