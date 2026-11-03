# SPDX-License-Identifier: MPL-2.0
"""Prepared-state causal factor measurements with original independent checks.

These are numerical methods. Owning native declarations must retain actual
measurement/projection custody. They create no source eligibility, supplier
applicability, scientific qualification or future-noise access.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_lifetime import science as factor_science
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.products import validate_diagnostics
from empirical_lawhood.adapters.methods.matrix_factor_lifetime.scalar_assessment import independent_scalar_closure_ratio
from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
from empirical_lawhood.adapters.methods.matrix_parameter_factor.independent import _control, pauli_residual, raw_operator
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import (
    DIAGNOSTICS, METHODS, MatrixParameterFactorControl, expected_members, prefix,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledPrefixPolicy, ScheduledPrefixTrace, identity as original_identity
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays, encode_matrix_arrays, matrix_array_members
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .preparation_records import MatrixPreparationArrays, MatrixPreparationAssessment, MatrixPreparationSource, preparation_identity
from .preparation_science import consume_preparation_arrays, validate_preparation_assessment


STANDING = "PREPARED_ARRAY_CAUSAL_MEASUREMENT_CUSTODY_AND_APPLICABILITY_NOT_ASSESSED"


def identity(record):
    return ObjectIdentity.from_record(record.record_id, record)


@dataclass(frozen=True, slots=True)
class MatrixPreparedPrefixArrays(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-prefix-arrays"
    record_id: str
    source: ObjectIdentity
    role: str
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]
    producers: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (type(self.source) is not ObjectIdentity or self.source.object_schema != MatrixPreparationSource.SCHEMA
                or self.role not in ("DIAGNOSTICS", "CAUSAL_STATE") or type(self.array_artifact) is not ArtifactIdentity
                or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA or self.array_artifact.media_type != "application/x-npz"
                or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or type(self.members) is not tuple or not self.members or any(type(row) is not MatrixArrayMember for row in self.members)
                or tuple(row.name for row in self.members) != tuple(sorted({row.name for row in self.members}))
                or sum(row.size_bytes for row in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES
                or type(self.producers) is not tuple or not self.producers or any(type(row) is not ObjectIdentity for row in self.producers)
                or tuple(row.object_id for row in self.producers) != tuple(sorted({row.object_id for row in self.producers}))):
            raise ValueError("prepared prefix arrays lose their separate source, complete bounded members or original producer identities")


@dataclass(frozen=True, slots=True)
class MatrixPreparedFactorWitness(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-factor-witness"
    record_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    numerical: ObjectIdentity
    policy: ObjectIdentity
    traces: tuple[ScheduledPrefixTrace, ...]
    arrays: MatrixPreparedPrefixArrays
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.standing != STANDING or self.source != self.arrays.source or self.arrays.role != "DIAGNOSTICS"
                or self.source.object_schema != MatrixPreparationSource.SCHEMA or self.preparation.object_schema != MatrixPreparationArrays.SCHEMA
                or self.numerical.object_schema != MatrixPreparationAssessment.SCHEMA or self.policy.object_schema != ScheduledPrefixPolicy.SCHEMA
                or type(self.traces) is not tuple or not self.traces or any(type(row) is not ScheduledPrefixTrace for row in self.traces)):
            raise ValueError("prepared factor witness substitutes its actual pre-future subject or invents custody standing")


@dataclass(frozen=True, slots=True)
class MatrixPreparedFrameAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-frame-assessment"
    record_id: str
    source: ObjectIdentity
    witness: ObjectIdentity
    numerical_design: ObjectIdentity
    controls: tuple[MatrixParameterFactorControl, ...]
    numerical_pass: bool

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.source.object_schema != MatrixPreparationSource.SCHEMA or self.witness.object_schema != MatrixPreparedFactorWitness.SCHEMA
                or type(self.controls) is not tuple or any(type(row) is not MatrixParameterFactorControl for row in self.controls)
                or tuple(row.method for row in self.controls) != METHODS or type(self.numerical_pass) is not bool
                or self.numerical_pass != all(row.disposition in ("SATISFIED", "NOT_APPLICABLE") for row in self.controls)):
            raise ValueError("prepared frame assessment thins original independent controls or changes measured verdict")


@dataclass(frozen=True, slots=True)
class MatrixPreparedCausalPrefix(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-causal-prefix"
    record_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    numerical: ObjectIdentity
    witness: ObjectIdentity
    frame_assessment: ObjectIdentity
    policy: ObjectIdentity
    cutoff_tick: int
    frame_sha256: str | None
    disposition: str
    reason: str | None
    arrays: MatrixPreparedPrefixArrays

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.source != self.arrays.source or self.arrays.role != "CAUSAL_STATE" or self.source.object_schema != MatrixPreparationSource.SCHEMA
                or self.preparation.object_schema != MatrixPreparationArrays.SCHEMA or self.numerical.object_schema != MatrixPreparationAssessment.SCHEMA
                or self.witness.object_schema != MatrixPreparedFactorWitness.SCHEMA or self.frame_assessment.object_schema != MatrixPreparedFrameAssessment.SCHEMA
                or self.policy.object_schema != ScheduledPrefixPolicy.SCHEMA or type(self.cutoff_tick) is not int or self.cutoff_tick < 1
                or self.disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE")
                or (self.frame_sha256 is not None) != (self.disposition == "AVAILABLE")
                or (self.reason is None) != (self.disposition == "AVAILABLE")):
            raise ValueError("prepared causal projection changes source, original cutoff or measured nonuse")


def _product(source, arrays, *, role, artifact_id, producers, nonfinite=(), raw=None):
    if raw is None:
        raw, members = encode_matrix_arrays(arrays, nonfinite_members=nonfinite)
    else:
        members = matrix_array_members(arrays, nonfinite_members=nonfinite)
    artifact = ArtifactIdentity(artifact_id, "prepared-prefix-" + role.lower().replace("_", "-"), MATRIX_ARRAY_SCHEMA,
        sha256(raw).hexdigest(), "application/x-npz", len(raw))
    operand = MatrixPreparedPrefixArrays("arrays." + artifact_id, source.identity, role, artifact, members,
        tuple(sorted(producers, key=lambda row: row.object_id)))
    decoded = decode_matrix_arrays(raw, operand)
    if any(not np.array_equal(value, decoded[name], equal_nan=True) for name, value in arrays.items()):
        raise ValueError("prepared prefix retained bytes change complete original measured values")
    return raw, operand


def measure_prepared_prefix(source, initial_raw, preparation, numerical, preparation_raw, *, artifact_id):
    """Same raw operator, all15 eigenpairs, causal rule and original scalar."""
    validate_preparation_assessment(source, preparation, numerical)
    native = consume_preparation_arrays(source, initial_raw, preparation, preparation_raw)
    rule = source.original.policy.factor_rule
    if rule.lattice[-1] != source.total_ticks or rule.primary_dt != source.primary_view.timestep:
        raise ValueError("prepared measurement changes original observation lattice or physical clock")
    arrays = {name: np.asarray(rule.lattice, dtype=dtype) if name.endswith("_ticks") else
        np.zeros(shape, dtype=dtype) if dtype == "|b1" else np.full(shape, np.nan, dtype=dtype)
        for name, (dtype, shape) in expected_members(rule).items()}
    traces = []
    for view, mult in (("PRIMARY", 1), ("FINE", 2)):
        for sector in rule.sectors:
            stem, index = prefix(view, sector), ("X", "Y").index(sector)
            measurements, unavailable, scalar = {}, {}, {}
            for at, tick in enumerate(rule.lattice):
                fields = native[view.lower() + "_positions"][mult * tick, index]
                alpha = native[view.lower() + "_alpha_tilde"][mult * tick, index]
                try:
                    scalar[tick] = independent_scalar_closure_ratio(fields, alpha)
                except ValueError:
                    scalar[tick] = None
                try:
                    measured = factor_science.measure_sector(fields, rule)
                    operator = algebra.operator(fields)
                    spectrum, vectors = np.linalg.eigh(operator)
                    if not np.array_equal(spectrum, measured.spectrum):
                        raise ValueError("prepared measurement changes original complete spectral witness")
                except np.linalg.LinAlgError:
                    measurements[tick], unavailable[tick] = None, "NUMERICAL_INVALID"
                    continue
                measurements[tick] = measured
                arrays[stem + "available"][at], arrays[stem + "identifiable"][at] = True, measured.identifiable
                for name in ("spectrum", "projector", "basis"):
                    arrays[stem + name][at] = getattr(measured, name)
                arrays[stem + "operator"][at], arrays[stem + "eigenvectors"][at] = operator, vectors
                if measured.identifiable:
                    arrays[stem + "factor"][at] = measured.factor
            observations, frames = factor_science.causal_observations(rule, measurements, unavailable=unavailable, scalar_closure=scalar)
            for at, tick in enumerate(rule.lattice):
                if tick in frames:
                    arrays[stem + "aligned_factor"][at] = frames[tick]
            traces.append(ScheduledPrefixTrace(rule.identity, view, sector, observations,
                factor_science.lifetime(observations, rule), factor_science.lifetime(observations, rule, origin_fixed=True)))
    producers = source.identity, preparation_identity(preparation), preparation_identity(numerical)
    raw, operand = _product(source, arrays, role="DIAGNOSTICS", artifact_id=artifact_id, producers=producers,
        nonfinite=tuple(name for name in arrays if not name.endswith(("_ticks", "_available", "_identifiable"))))
    return raw, MatrixPreparedFactorWitness("witness." + source.source_id, *producers,
        original_identity(source.original.policy), tuple(traces), operand)


def check_prepared_frames(source, initial_raw, preparation, numerical, witness, preparation_raw, diagnostic_raw):
    """Literal raw-state/operator/all15-eigenpair checks, with no eigensolve."""
    validate_preparation_assessment(source, preparation, numerical)
    rule, design = source.original.policy.factor_rule, source.original.policy.factor_numerical_design
    if (type(witness) is not MatrixPreparedFactorWitness or witness.source != source.identity
            or witness.preparation != preparation_identity(preparation) or witness.numerical != preparation_identity(numerical)
            or witness.policy != original_identity(source.original.policy)
            or tuple((row.view, row.sector) for row in witness.traces) != tuple((view, sector) for view in ("PRIMARY", "FINE") for sector in rule.sectors)
            or witness.arrays.producers != tuple(sorted((source.identity, preparation_identity(preparation), preparation_identity(numerical)), key=lambda row: row.object_id))
            or {row.name: (row.dtype, row.shape) for row in witness.arrays.members} != expected_members(rule)):
        raise ValueError("prepared frame witness changes original source/rule/complete lattice")
    native = consume_preparation_arrays(source, initial_raw, preparation, preparation_raw)
    arrays = decode_matrix_arrays(diagnostic_raw, witness.arrays)
    errors, applicable = {name: [] for name in METHODS}, []
    for trace in witness.traces:
        factor_science.validate_trace(trace, rule)
        stem = prefix(trace.view, trace.sector)
        diagnostics = {name: arrays[stem + name] for name in DIAGNOSTICS}
        validate_diagnostics(diagnostics, trace, rule)
        mult, sector_index = 1 if trace.view == "PRIMARY" else 2, ("X", "Y").index(trace.sector)
        for at, observation in enumerate(trace.observations):
            fields = native[trace.view.lower() + "_positions"][mult * observation.tick, sector_index]
            alpha = native[trace.view.lower() + "_alpha_tilde"][mult * observation.tick, sector_index]
            try:
                scalar = independent_scalar_closure_ratio(fields, alpha)
            except ValueError:
                scalar = None
            if (scalar is None) != (observation.scalar_closure_ratio is None):
                raise ValueError("prepared scalar witness changes original missingness")
            errors["scalar-contrast"].append(None if scalar is None else abs(float(scalar - observation.scalar_closure_ratio)))
            available, identified = bool(diagnostics["available"][at]), bool(diagnostics["identifiable"][at])
            applicable.append(not available or identified)
            errors["pauli-factor"].append(pauli_residual(diagnostics["factor"][at]) if identified else None)
            operator, vectors, spectrum = arrays[stem + "operator"][at], arrays[stem + "eigenvectors"][at], diagnostics["spectrum"][at]
            if not available:
                if not np.isnan(operator).all() or not np.isnan(vectors).all():
                    raise ValueError("unavailable prepared measurement invents spectral witnesses")
                for name in ("raw-operator", "eigenvector-orthogonality", "slow-projector"):
                    errors[name].append(None)
                errors["all-eigenpairs"].extend([None] * 15)
                continue
            if not np.isfinite(operator).all() or not np.isfinite(vectors).all() or np.any(np.diff(spectrum) < 0):
                raise ValueError("prepared measurement loses ordered finite eigenpairs")
            formed = raw_operator(fields)
            errors["raw-operator"].append(np.linalg.norm(operator - formed))
            errors["all-eigenpairs"].extend(np.linalg.norm(formed @ vectors - vectors * spectrum[None, :], axis=0))
            errors["eigenvector-orthogonality"].append(np.linalg.norm(vectors.T @ vectors - np.eye(15)))
            errors["slow-projector"].append(np.linalg.norm(diagnostics["projector"][at] - vectors[:, :3] @ vectors[:, :3].T))
    controls = tuple(_control(name, errors[name], tolerance, dimension, applicable if name == "pauli-factor" else None)
        for name, tolerance, dimension in zip(METHODS, (design.operator_tolerance, design.eigenpair_tolerance,
            design.orthogonality_tolerance, design.projector_tolerance, design.factor_tolerance, design.scalar_tolerance),
            (225, 15, 225, 225, 48, 1), strict=True))
    count = 2 * len(rule.sectors) * len(rule.lattice)
    if tuple(len(row.measured_errors) for row in controls) != (count, 15 * count, count, count, count, count):
        raise ValueError("prepared frame assessment thins complete view/sector/tick/eigenpair denominators")
    return MatrixPreparedFrameAssessment("frames." + source.source_id, source.identity, identity(witness), original_identity(design),
        controls, all(row.disposition in ("SATISFIED", "NOT_APPLICABLE") for row in controls))


def project_prepared_prefix(source, initial_raw, preparation, numerical, witness, frames, preparation_raw, diagnostic_raw, *, artifact_id, raw=None):
    measured = check_prepared_frames(source, initial_raw, preparation, numerical, witness, preparation_raw, diagnostic_raw)
    if measured != frames:
        raise ValueError("prepared projection substitutes original independent frame assessment")
    native = consume_preparation_arrays(source, initial_raw, preparation, preparation_raw)
    diagnostic = decode_matrix_arrays(diagnostic_raw, witness.arrays)
    trace = next(row for row in witness.traces if row.view == "PRIMARY" and row.sector == source.original.policy.origin_sector)
    observation = trace.observations[-1]
    if not numerical.numerical_pass or not frames.numerical_pass:
        disposition, reason = "UNEVALUABLE", "PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED"
    elif observation.raw_admitted is None:
        disposition, reason = "UNEVALUABLE", "CAUSAL_CUTOFF_OBSERVATION_UNAVAILABLE"
    elif observation.causal_admitted is not True or observation.alignment_ambiguous:
        disposition, reason = "NO_ORIGIN", "DECLARED_CUTOFF_NOT_CAUSALLY_ADMITTED"
    else:
        disposition, reason = "AVAILABLE", None
    frame = diagnostic[prefix("PRIMARY", source.original.policy.origin_sector) + "aligned_factor"][-1].copy() if disposition == "AVAILABLE" else np.full((3, 4, 4), np.nan, dtype="<c16")
    values = {name: value for name, value in native.items() if not name.endswith("innovations")}
    values["frame"] = frame
    encoded, operand = _product(source, values, role="CAUSAL_STATE", artifact_id=artifact_id,
        producers=(source.identity, preparation_identity(preparation), identity(witness), identity(frames)),
        nonfinite=() if disposition == "AVAILABLE" else ("frame",), raw=raw)
    return encoded, MatrixPreparedCausalPrefix("causal." + source.source_id, source.identity, preparation_identity(preparation),
        preparation_identity(numerical), identity(witness), identity(frames), original_identity(source.original.policy), source.total_ticks,
        sha256(frame.tobytes()).hexdigest() if disposition == "AVAILABLE" else None, disposition, reason, operand)
