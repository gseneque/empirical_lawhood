# SPDX-License-Identifier: MPL-2.0
"""Selected Matrix numerical admissibility, independent of observation I/O."""

import json

from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.recursive_compiler import RegisteredProvenanceRequirement


def _immutable_json(value):
    if isinstance(value, (list, tuple)):
        return tuple(_immutable_json(item) for item in value)
    if isinstance(value, dict):
        return {key: _immutable_json(item) for key, item in value.items()}
    return value


def validate_matrix_runtime_observation_json(observation_json: str) -> None:
    """Preserve the historical profile and exact retained observation bytes."""
    value = json.loads(observation_json)
    if canonical_json_bytes(_immutable_json(value)).decode() != observation_json:
        raise ValueError("Matrix runtime observation requires exact canonical JSON")
    if tuple(value.get(key) for key in ("python", "numpy", "scipy", "system", "machine")) != (
            "3.11.14", "2.4.6", "1.17.1", "linux", "x86_64"):
        raise ValueError("Matrix runtime observation differs from its selected numerical profile")
    if not isinstance(value.get("threadpools"), list) or any(
            type(pool) is not dict or type(pool.get("num_threads")) is not int
            or pool["num_threads"] != 1 for pool in value["threadpools"]):
        raise ValueError("Matrix runtime observation lacks its actual single-thread bootstrap")


def validate_matrix_producing_provenance(provenance: NumericalProducingProvenance) -> None:
    """Assess producing evidence; never substitute the reader's environment."""
    if not isinstance(provenance, NumericalProducingProvenance):
        raise ValueError("Exact numerical producing provenance is required")
    provenance.__post_init__()
    validate_matrix_runtime_observation_json(provenance.runtime_observation_json)


MATRIX_PROVENANCE_REQUIREMENT = RegisteredProvenanceRequirement(
    "matrix-response-study.selected-numerical-profile.v1", validate_matrix_producing_provenance)
