# SPDX-License-Identifier: MPL-2.0
"""Locked supplied-kinetics numerical admissibility, without runtime capture."""

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


def validate_kinetic_producing_provenance(provenance: NumericalProducingProvenance) -> None:
    """Validate the selected binary64 assay profile, without biological admission."""
    if not isinstance(provenance, NumericalProducingProvenance):
        raise ValueError("kinetic join requires exact numerical producing provenance")
    provenance.__post_init__()
    value = json.loads(provenance.runtime_observation_json)
    if canonical_json_bytes(_immutable_json(value)).decode() != provenance.runtime_observation_json:
        raise ValueError("kinetic join runtime observation requires exact canonical JSON")
    if tuple(value.get(key) for key in ("python", "numpy", "scipy", "system", "machine")) != (
            "3.11.14", "2.4.6", "1.17.1", "linux", "x86_64"):
        raise ValueError("kinetic join runtime observation differs from its selected numerical profile")
    if not isinstance(value.get("threadpools"), list) or any(
            type(pool) is not dict or type(pool.get("num_threads")) is not int
            or pool["num_threads"] != 1 for pool in value["threadpools"]):
        raise ValueError("kinetic join runtime observation lacks its actual single-thread bootstrap")


KINETIC_PROVENANCE_REQUIREMENT = RegisteredProvenanceRequirement(
    "rubisco-kinetic-join.selected-numerical-profile.v1", validate_kinetic_producing_provenance)
