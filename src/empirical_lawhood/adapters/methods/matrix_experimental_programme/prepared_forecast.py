# SPDX-License-Identifier: MPL-2.0
"""Selected mechanical methods for a separately prepared causal subject.

This owner retains full eigensystem witnesses and independently rechecks them
on cold consumption. It creates neither forecast publication chronology nor a
cross-preparation statistical bound.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import model_predictors
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_forecast import forecast_response_arrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.infrastructure.matrix_array_io import DecodedMatrixArrayInput, decode_matrix_arrays, encode_matrix_arrays, matrix_array_members
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .preparation_records import MatrixPreparationSource
from .prepared_point import MatrixPreparedPublicSource
from .prepared_prefix import MatrixPreparedCausalPrefix, identity
from .prepared_response_science import MatrixPreparedForecastArrays


STANDING = "PREPARED_MECHANICAL_NUMERICAL_FORECAST_PUBLICATION_AND_APPLICABILITY_NOT_ASSESSED"


@dataclass(frozen=True, slots=True)
class MatrixPreparedMechanicalForecast(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-mechanical-forecast"
    record_id: str
    source: ObjectIdentity
    causal: ObjectIdentity
    original_protocol: ObjectIdentity
    mechanical_model: ObjectIdentity
    arrays: MatrixPreparedForecastArrays
    disposition: str
    predictor_dispositions: tuple[tuple[str, str, str, str | None], ...]
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.source.object_schema != MatrixPreparationSource.SCHEMA or self.causal.object_schema != MatrixPreparedCausalPrefix.SCHEMA
                or self.original_protocol.object_schema != ScheduledResponseProtocol.SCHEMA
                or type(self.arrays) is not MatrixPreparedForecastArrays or self.arrays.source != self.source
                or self.arrays.original_protocol != self.original_protocol or self.standing != STANDING
                or self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")
                or tuple((view, name) for view, name, _, _ in self.predictor_dispositions) !=
                    tuple((view, name) for view in ("PRIMARY", "FINE") for name in model_predictors(self.mechanical_model))
                or any(status not in ("AVAILABLE", "UNRESOLVED") or (reason is None) != (status == "AVAILABLE")
                    for _, _, status, reason in self.predictor_dispositions)
                or self.disposition != "AVAILABLE" and any(status == "AVAILABLE" for _, _, status, _ in self.predictor_dispositions)):
            raise ValueError("prepared mechanical forecast changes exact source/model, its complete selected methods or known nonuse")


def forecast(source, protocol, causal, causal_raw, template_raw, *, artifact_id, retained=None, raw=None, retained_input=None):
    if type(source) is not MatrixPreparationSource:
        raise ValueError("prepared mechanical forecast requires its actual separate subject")
    return forecast_public(MatrixPreparedPublicSource.from_source(source), protocol, causal, causal_raw, template_raw,
        artifact_id=artifact_id, retained=retained, raw=raw, retained_input=retained_input)


def forecast_public(public, protocol, causal, causal_raw, template_raw, *, artifact_id, retained=None, raw=None, retained_input=None):
    """Produce, or independently reprove, actual origin-fixed full96 responses.

    In retained mode no native response producer, Hessian producer, random
    generator or eigensolve is entered. The independent literal derivative
    checks every real coordinate of both origin states.
    """
    if (type(public) is not MatrixPreparedPublicSource or type(protocol) is not ScheduledResponseProtocol
            or type(causal) is not MatrixPreparedCausalPrefix or causal.source != public.source
            or protocol.public_source != public.original or causal.cutoff_tick != public.original.policy.cutoff_tick
            or causal.cutoff_tick < public.original.coordinate.ramp_ticks):
        raise ValueError("prepared mechanical forecast changes original restored source, fixed assay or causal cutoff")
    protocol.__post_init__()
    if retained_input is not None:
        if type(retained_input) is not DecodedMatrixArrayInput or retained is not None or raw is None:
            raise TypeError("prepared cold forecast requires one actual decoded retained input and its original bytes")
        retained = retained_input.for_operand(raw, retained_input.original)
    causal_arrays, templates = decode_matrix_arrays(causal_raw, causal.arrays), decode_matrix_arrays(template_raw, protocol.templates)
    if any(name.endswith("innovations") for name in causal_arrays):
        raise ValueError("prepared mechanical forecast receives forbidden future innovations")
    if causal.frame_sha256 is not None and sha256(causal_arrays["frame"].tobytes()).hexdigest() != causal.frame_sha256:
        raise ValueError("prepared mechanical forecast changes actual admitted primary frame")
    coordinate = public.original.coordinate
    for view, multiplier in (("primary", 1), ("fine", 2)):
        if (not np.array_equal(causal_arrays[view + "_ticks"], np.arange(multiplier * causal.cutoff_tick + 1, dtype="<i8"))
                or not np.array_equal(causal_arrays[view + "_alpha_tilde"][-1],
                    np.asarray(coordinate.couplings(multiplier * causal.cutoff_tick, refinement=multiplier), dtype="<f8"))):
            raise ValueError("prepared mechanical forecast changes actual restored coupling or paired physical clocks")
    arrays, disposition, dispositions = forecast_response_arrays(protocol, causal_arrays, templates,
        disposition=causal.disposition, retained=retained,
        no_origin_reason="NO_ADMITTED_OR_RESOLVED_PREPARED_ORIGIN_FIXED_INSTRUMENT")
    nonfinite = tuple(name for name, value in arrays.items() if not np.isfinite(value).all())
    if raw is None:
        result_raw, members = encode_matrix_arrays(arrays, nonfinite_members=nonfinite)
    else:
        result_raw, members = raw, matrix_array_members(arrays, nonfinite_members=nonfinite)
    operand = MatrixPreparedForecastArrays("arrays." + artifact_id, public.source, causal.preparation,
        ObjectIdentity.from_record(protocol.protocol_id, protocol), ArtifactIdentity(artifact_id, "prepared-mechanical-forecast", MATRIX_ARRAY_SCHEMA,
            sha256(result_raw).hexdigest(), "application/x-npz", len(result_raw)), members)
    decoded = (decode_matrix_arrays(result_raw, operand) if retained_input is None
        else retained_input.for_operand(result_raw, operand))
    if any(not np.array_equal(value, decoded[name], equal_nan=True) for name, value in arrays.items()):
        raise ValueError("prepared forecast retained physical bytes change exact numerical results")
    return result_raw, MatrixPreparedMechanicalForecast("mechanical." + public.source.object_id, public.source, identity(causal),
        ObjectIdentity.from_record(protocol.protocol_id, protocol), ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model),
        operand, disposition, tuple(dispositions))
