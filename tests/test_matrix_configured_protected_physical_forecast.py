# SPDX-License-Identifier: MPL-2.0
"""Actual configured physical nonuse path over disclosed literal arrays.

No native acquisition, fresh evidence or scientific qualification is asserted.
The real configured forecast consumes the retained paired array codecs and the
real public protocol validator; no scientific-root guard is bypassed.
"""
from dataclasses import fields, replace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_prefix_records as prefix
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_response_records as records
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_response_science as science
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_protocol import ConfiguredProtectedE3ProtocolProjection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_tasks import NAMESPACE
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_configured_e3_v2 import configured_case
from tests.test_matrix_e3_response_records import case as case  # noqa: F401
from tests.test_matrix_e3_response_science import LIMITS, blocked, byte_fetch, no_native as no_native, store


def configured_operands(case):
    exposed, _ = configured_case()
    previous = case.originals.projection
    role_coordinates = tuple((role, previous.nearby if role == "TRANSFER_NEARBY" else
        previous.shifted if role == "TRANSFER_SHIFTED" else previous.nominal) for role, _ in exposed.role_coordinates)
    specification = ConfiguredProtectedE3Specification("experiment.configured-physical.literal", exposed.question,
        exposed.protocol, case.specification.populations, exposed.methods, exposed.assessment,
        exposed.calibration_alpha, role_coordinates, evidence_scope="PROSPECTIVE_REQUIRED",
        calibration_target_view="MAX_PAIRED_VIEWS")
    projection = ConfiguredProtectedE3ProtocolProjection("projection.configured-physical.literal", specification.identity,
        specification.protocol_sha256, len(specification.protocol.canonical_bytes()),
        **{field.name: getattr(previous, field.name) for field in fields(ConfiguredProtectedE3ProtocolProjection)
           if field.name not in ("record_id", "specification", "protocol_sha256", "protocol_size_bytes")})
    numerical = records.project_protected_e3_response_numerics(case.protocol, provenance=case.selection,
        publication=case.publication, qualification=case.qualification)
    kinds = {kind.SCHEMA.replace("/configured-protected-", "/protected-"): kind for kind in
        (prefix.ConfiguredProtectedE3PrefixHistory, prefix.ConfiguredProtectedE3NumericalAssessment,
         prefix.ConfiguredProtectedE3PrefixWitness, prefix.ConfiguredProtectedE3FrameAssessment)}
    def current(pin):
        kind = kinds[pin.object_schema]
        return ObjectIdentity(pin.object_id + ".configured-literal", kind.SCHEMA, kind.VERSION, pin.object_fingerprint)
    changes = {name: current(getattr(case.causal, name)) for name in
        ("history", "numerical", "witness", "frame_assessment")}
    producers = {getattr(case.causal, name): pin for name, pin in changes.items()}
    arrays = replace(case.causal.arrays, producers=tuple(sorted(
        (producers.get(pin, pin) for pin in case.causal.arrays.producers), key=lambda pin: pin.object_id)))
    causal = prefix.ConfiguredProtectedE3CausalPrefix("causal.configured-physical.literal",
        **{field.name: changes.get(field.name, arrays if field.name == "arrays" else getattr(case.causal, field.name))
           for field in fields(prefix.ConfiguredProtectedE3CausalPrefix) if field.name != "record_id"})
    config = records.ConfiguredProtectedE3PhysicalForecastConfig(
        "config." + NAMESPACE + "." + case.source.root_id + ".physical-forecast", case.source.root_id,
        specification.identity, records._object(case.protocol), records._object(numerical))
    return config, causal, dict(specification=specification, protocol=case.protocol,
        numerical_profile=numerical, mathematical_protocol=case.originals.mathematical, projection=projection)


def test_configured_physical_forecast_reads_real_protocol_and_paired_nonuse_arrays(case):  # noqa: F811
    config, causal, public = configured_operands(case)
    raw, forecast = science.forecast_physical(config, causal, **public, fetch=byte_fetch(store(case)), **LIMITS,
        artifact_id="literal.configured-physical.arrays", forecast_id="literal.configured-physical.forecast",
        outcome_access=case.physical.arrays.outcome_access, visibility_ceiling=case.physical.arrays.visibility_ceiling)
    assert raw == case.physical_raw
    assert forecast.disposition == case.physical.disposition == "UNEVALUABLE"
    assert forecast.dispositions == case.physical.dispositions and len(forecast.dispositions) == 10
    forecast.validate_public_inputs(config, causal=causal, **public)
    values = decode_matrix_arrays(raw, forecast.arrays)
    assert len(values) == 10 and all(np.isnan(value).all() for value in values.values())
    wrong = replace(public["projection"], protocol_sha256="e" * 64)
    with pytest.raises(ValueError, match="original selected protocol"):
        science.forecast_physical(config, causal, **{**public, "projection": wrong}, fetch=blocked, **LIMITS,
            artifact_id="literal.configured-physical.refused", forecast_id="literal.configured-physical.refused",
            outcome_access=case.physical.arrays.outcome_access, visibility_ceiling=case.physical.arrays.visibility_ceiling)
