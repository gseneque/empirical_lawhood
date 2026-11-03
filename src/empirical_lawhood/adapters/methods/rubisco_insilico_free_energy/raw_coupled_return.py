# SPDX-License-Identifier: MPL-2.0
"""Capture returned native operands before scientific guards, through AR3 custody.

This is a passive domain seam, not a launcher or a new scheduler. The selected
caller owns the actual native contact. Lossless gzip of no-pickle NPY operands
uses the existing uninterpreted-source route; custody confers no array admission.
Array length is an observed cost, not an arbitrary scientific output ceiling.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import io
import math
from typing import ClassVar
import zlib

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, validate_sha256, validate_stable_id,
)
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkOutput

BLOCK_BYTES = 1024 * 1024  # Working buffer only: every source element is retained.
RAW_SCHEMA = "empirical-lawhood/source/capture-assured-uninterpreted-public-bytes"


def _identity(value, field):
    if type(value) is not ObjectIdentity:
        raise ValueError(field + " requires its exact immutable identity")


@dataclass(frozen=True, slots=True)
class CoupledEvaluationRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/evaluation-request"
    request_id: str
    protocol: ObjectIdentity
    prepared_material: ObjectIdentity
    physical_coordinates: ObjectIdentity
    producing_provenance: ObjectIdentity
    physical_atom_count: int
    energy_unit: str = "Eh"
    gradient_unit: str = "Eh/ASH-Bohr"
    coordinate_frame: str = "prepared-physical-atom-order"

    def __post_init__(self):
        validate_stable_id(self.request_id)
        for name in ("protocol", "prepared_material", "physical_coordinates", "producing_provenance"):
            _identity(getattr(self, name), name)
        if type(self.physical_atom_count) is not int or self.physical_atom_count <= 0:
            raise ValueError("complete positive physical atom census required")
        if (self.energy_unit, self.gradient_unit, self.coordinate_frame) != (
                "Eh", "Eh/ASH-Bohr", "prepared-physical-atom-order"):
            raise ValueError("returned operand changes the selected units/physical frame")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.request_id, self)


@dataclass(frozen=True, slots=True)
class RawArrayCapture(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/raw-array-capture"
    operand: str
    source_type: str
    dtype: str
    shape: tuple[int, ...]
    source_strides: tuple[int, ...]
    npy_header_bytes: int
    uncompressed_bytes: int
    uncompressed_sha256: str
    artifact_manifest: ArtifactManifest
    encoding: str = "NPY-2.0-C-order-gzip-mtime0"

    def __post_init__(self):
        if self.operand not in {"energy", "gradient"} or not self.source_type or not self.dtype:
            raise ValueError("raw capture requires its actual operand/type/dtype")
        if (type(self.shape) is not tuple or type(self.source_strides) is not tuple
                or len(self.shape) != len(self.source_strides)
                or any(type(n) is not int or n < 0 for n in self.shape)
                or any(type(n) is not int for n in self.source_strides)
                or type(self.npy_header_bytes) is not int or self.npy_header_bytes <= 0
                or type(self.uncompressed_bytes) is not int
                or self.uncompressed_bytes < self.npy_header_bytes):
            raise ValueError("raw capture loses actual shape/stride/byte census")
        validate_sha256(self.uncompressed_sha256)
        if (type(self.artifact_manifest) is not ArtifactManifest
                or self.artifact_manifest.logical.payload_schema != RAW_SCHEMA
                or self.artifact_manifest.logical.profile is not ArtifactProfile.RAW_SOURCE_BYTES
                or self.artifact_manifest.logical.media_type != "application/gzip"
                or self.encoding != "NPY-2.0-C-order-gzip-mtime0"):
            raise ValueError("raw array changes its uninterpreted custody route")


@dataclass(frozen=True, slots=True)
class RawCoupledReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/raw-return"
    return_id: str
    request: ObjectIdentity
    energy: RawArrayCapture | None
    gradient: RawArrayCapture | None
    capture_failures: tuple[tuple[str, str], ...]
    native_disposition: str = "RETURNED"
    scientific_admission: A = A.NOT_ATTEMPTED

    def __post_init__(self):
        validate_stable_id(self.return_id)
        _identity(self.request, "request")
        if self.request.object_schema != CoupledEvaluationRequest.SCHEMA:
            raise ValueError("raw return substitutes its actual selected request")
        if self.native_disposition != "RETURNED" or self.scientific_admission is not A.NOT_ATTEMPTED:
            raise ValueError("native return/custody cannot establish scientific admission")
        keys = tuple(name for name, _ in self.capture_failures)
        if (keys != tuple(sorted(set(keys))) or set(keys) - {"energy", "gradient"}
                or any(type(error) is not str or not error for _, error in self.capture_failures)):
            raise ValueError("raw return must retain its exact capture failure census")
        for name in ("energy", "gradient"):
            operand = getattr(self, name)
            if (operand is None) != (name in keys) or operand is not None and (
                    type(operand) is not RawArrayCapture or operand.operand != name):
                raise ValueError("raw return loses or duplicates a returned operand")
        if self.energy is not None and self.gradient is not None and (
                self.energy.artifact_manifest.logical.logical_artifact_id
                == self.gradient.artifact_manifest.logical.logical_artifact_id):
            raise ValueError("two operands cannot use the same raw artifact")


def return_outputs():
    return (
        NativeSubworkOutput("raw.energy", RAW_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES, "application/gzip"),
        NativeSubworkOutput("raw.gradient", RAW_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES, "application/gzip"),
        NativeSubworkOutput("raw.return", RawCoupledReturn.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
    )


def _array(value):
    import numpy as np
    # No dtype conversion. Ambiguous containers/Decimal/object arrays remain
    # uncaptured and explicit; they never become invented expected float data.
    if type(value) not in (int, float) and not isinstance(value, (np.ndarray, np.generic)):
        raise ValueError("native operand is not an actual numeric array/scalar")
    array = np.asarray(value)
    if array.dtype.hasobject or array.dtype.fields is not None or array.dtype.kind not in "biufc":
        raise ValueError("native operand has no safe primitive numeric representation")
    return array


def _header(array):
    import numpy as np
    output = io.BytesIO()
    np.lib.format.write_array_header_2_0(output, {
        "descr": np.lib.format.dtype_to_descr(array.dtype),
        "fortran_order": False, "shape": array.shape,
    })
    return output.getvalue()


def _npy_chunks(array, header):
    import numpy as np
    yield header
    iterator = np.nditer(array, flags=["external_loop", "buffered", "zerosize_ok"],
        op_flags=["readonly"], order="C", buffersize=max(1, BLOCK_BYTES // array.dtype.itemsize))
    for values in iterator:
        payload = values.tobytes(order="C")
        for offset in range(0, len(payload), BLOCK_BYTES):
            yield payload[offset:offset + BLOCK_BYTES]


def _gzip_chunks(chunks):
    compressor = zlib.compressobj(wbits=31)
    for raw in chunks:
        encoded = compressor.compress(raw)
        for offset in range(0, len(encoded), BLOCK_BYTES):
            yield encoded[offset:offset + BLOCK_BYTES]
    tail = compressor.flush()
    for offset in range(0, len(tail), BLOCK_BYTES):
        yield tail[offset:offset + BLOCK_BYTES]


def _digest_chunks(chunks):
    digest, size = sha256(), 0
    for chunk in chunks:
        digest.update(chunk)
        size += len(chunk)
    return size, digest.hexdigest()


def capture_native_return(request, energy, gradient, progress, entry):
    """Publish full returned operands and unassessed metadata before any guard.

    Does not begin/contact/complete a native subwork or invoke an assessor. A
    publication failure propagates; AR3 retains its prefix/uncertain contact.
    Caller must complete the actual known return/cost separately. No replay.
    """
    if type(request) is not CoupledEvaluationRequest:
        raise ValueError("raw capture requires its actual typed request")
    definition = entry.definition
    expected_sources = {request.protocol, request.prepared_material, request.physical_coordinates,
                        request.producing_provenance}
    if definition.configuration != request.identity or not expected_sources.issubset(definition.sources):
        raise ValueError("raw capture changes entered native configuration/sources")
    declared = {row.output_id: row for row in definition.outputs}
    if any(declared.get(row.output_id) != row for row in return_outputs()):
        raise ValueError("raw capture lacks the committed complete output slots")
    captured, failures = {}, []
    for name, value in (("energy", energy), ("gradient", gradient)):
        try:
            array = _array(value)
        except ValueError as error:
            failures.append((name, str(error)))
            captured[name] = None
            continue
        header = _header(array)
        raw_size, raw_digest = _digest_chunks(_npy_chunks(array, header))
        stored_size, stored_digest = _digest_chunks(_gzip_chunks(_npy_chunks(array, header)))
        manifest = progress.publish_output(entry, "raw." + name,
            _gzip_chunks(_npy_chunks(array, header)), maximum_bytes=stored_size,
            maximum_chunk_bytes=min(BLOCK_BYTES, stored_size), expected_size_bytes=stored_size,
            expected_physical_sha256=stored_digest)
        if (manifest.materialization.size_bytes != stored_size
                or manifest.materialization.physical_sha256 != stored_digest):
            raise ValueError("publisher acknowledgement changes the actual raw return")
        captured[name] = RawArrayCapture(name, type(value).__module__ + "." + type(value).__qualname__,
            array.dtype.str, tuple(array.shape), tuple(array.strides), len(header), raw_size, raw_digest, manifest)
    result = RawCoupledReturn(request.request_id + ".raw-return", request.identity,
        captured["energy"], captured["gradient"], tuple(sorted(failures)))
    payload = result.canonical_bytes()
    progress.publish_output(entry, "raw.return", (payload,), maximum_bytes=len(payload),
        maximum_chunk_bytes=len(payload), expected_size_bytes=len(payload),
        expected_physical_sha256=sha256(payload).hexdigest())
    return result


@dataclass(frozen=True, slots=True)
class OperandIntegrity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/operand-integrity"
    operand: str
    expected_shape: tuple[int, ...]
    observed_shape: tuple[int, ...] | None
    retained_values: int
    nonfinite_values: int | None
    absolute_maximum: Decimal | None
    disposition: A
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        if self.operand not in {"energy", "gradient"}:
            raise ValueError("operand integrity changes the complete two-operand census")
        for shape in (self.expected_shape, self.observed_shape):
            if shape is not None and (type(shape) is not tuple or any(type(n) is not int or n < 0 for n in shape)):
                raise ValueError("operand integrity requires its complete typed shape")
        if (type(self.retained_values) is not int or self.retained_values < 0
                or self.observed_shape is not None and self.retained_values != math.prod(self.observed_shape)
                or self.observed_shape is None and self.retained_values != 0):
            raise ValueError("operand integrity changes actual element denominator")
        if self.nonfinite_values is not None and (type(self.nonfinite_values) is not int
                or not 0 <= self.nonfinite_values <= self.retained_values):
            raise ValueError("operand integrity changes its nonfinite denominator")
        if self.absolute_maximum is not None and (type(self.absolute_maximum) is not Decimal
                or not self.absolute_maximum.is_finite() or self.absolute_maximum < 0):
            raise ValueError("operand integrity changes the actual finite maximum")
        if type(self.disposition) is not A or self.disposition not in {A.SATISFIED, A.FALSIFIED, A.UNSUPPORTED, A.UNEVALUABLE}:
            raise ValueError("operand integrity uses an unsupported disposition")
        if (type(self.reason_codes) is not tuple or self.reason_codes != tuple(sorted(set(self.reason_codes)))
                or any(type(reason) is not str or not reason for reason in self.reason_codes)):
            raise ValueError("operand integrity requires exact sorted reason codes")
        if self.disposition == "SATISFIED" and (
                self.observed_shape != self.expected_shape or self.nonfinite_values != 0
                or self.absolute_maximum is None or self.reason_codes):
            raise ValueError("positive integrity requires complete finite correctly shaped operands")
        if self.disposition != "SATISFIED" and not self.reason_codes:
            raise ValueError("adverse integrity requires its actual reasons")


@dataclass(frozen=True, slots=True)
class CoupledNumericalIntegrity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/numerical-integrity"
    assessment_id: str
    request: ObjectIdentity
    raw_return: ObjectIdentity
    assessor_source: ObjectIdentity
    maximum_absolute_value: Decimal | None
    operands: tuple[OperandIntegrity, ...]
    disposition: A
    preparation_adequacy: A = A.NOT_ATTEMPTED
    derivative_consistency: A = A.NOT_ATTEMPTED
    reactive_model_adequacy: A = A.NOT_ATTEMPTED
    biological_prediction: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        for name in ("request", "raw_return", "assessor_source"):
            _identity(getattr(self, name), name)
        if (self.request.object_schema != CoupledEvaluationRequest.SCHEMA
                or self.raw_return.object_schema != RawCoupledReturn.SCHEMA
                or type(self.operands) is not tuple or len(self.operands) != 2
                or any(type(row) is not OperandIntegrity for row in self.operands)
                or tuple(row.operand for row in self.operands) != ("energy", "gradient")
                or self.operands[0].expected_shape != ()
                or len(self.operands[1].expected_shape) != 2
                or self.operands[1].expected_shape[0] <= 0
                or self.operands[1].expected_shape[1] != 3):
            raise ValueError("coupled integrity changes its actual request/return/physical denominator")
        if self.maximum_absolute_value is not None and (type(self.maximum_absolute_value) is not Decimal
                or not self.maximum_absolute_value.is_finite() or self.maximum_absolute_value <= 0):
            raise ValueError("numerical magnitude criterion requires its declared positive Decimal")
        expected = next(state for state in (A.UNEVALUABLE, A.FALSIFIED, A.UNSUPPORTED, A.SATISFIED)
                        if state in tuple(row.disposition for row in self.operands))
        if type(self.disposition) is not A or self.disposition != expected:
            raise ValueError("coupled integrity drops an adverse operand disposition")
        if (any(value is not A.NOT_ATTEMPTED for value in (
                self.preparation_adequacy, self.derivative_consistency, self.reactive_model_adequacy))
                or self.biological_prediction != "NOT_ESTABLISHED"):
            raise ValueError("numerical integrity cannot establish independent physical/biological adequacy")


def assess_native_return(request, record, reader_for_manifest, *, assessor_source,
                         maximum_absolute_value=None):
    """Independent bounded read of authentic raw bytes, after custody succeeds.

    The read port resolves the selected exact manifest, never a caller path or a
    producer report. Finite/shape/magnitude checks alone qualify neither physics
    nor derivatives. Any positive magnitude limit is an explicit numerical
    interpretation of this method, unrelated to operational resource ceilings.
    """
    import gzip
    import numpy as np
    _identity(assessor_source, "assessor source")
    if type(request) is not CoupledEvaluationRequest or type(record) is not RawCoupledReturn or record.request != request.identity:
        raise ValueError("assessor substitutes the actual request/raw return")
    if maximum_absolute_value is not None and (
            type(maximum_absolute_value) is not Decimal or not maximum_absolute_value.is_finite()
            or maximum_absolute_value <= 0):
        raise ValueError("numerical magnitude criterion must be declared positive Decimal or absent")
    assessments = []
    for name, shape in (("energy", ()), ("gradient", (request.physical_atom_count, 3))):
        capture = getattr(record, name)
        if capture is None:
            assessments.append(OperandIntegrity(name, shape, None, 0, None, None, A.UNEVALUABLE, ("RAW_OPERAND_NOT_CAPTURED",)))
            continue
        # Verify both compressed materialization and the original complete NPY.
        stored_hash, stored_size = sha256(), 0
        class HashingReader:
            def __init__(self, source):
                self.source = source
            def read(self, size=-1):
                nonlocal stored_size
                chunk = self.source.read(BLOCK_BYTES if size < 0 else min(size, BLOCK_BYTES))
                stored_hash.update(chunk)
                stored_size += len(chunk)
                return chunk
        source = reader_for_manifest(capture.artifact_manifest)
        digest, size, count, nonfinite, maximum = sha256(), 0, 0, 0, None
        try:
            with gzip.GzipFile(fileobj=HashingReader(source), mode="rb") as stream:
                header = stream.read(capture.npy_header_bytes)
                digest.update(header)
                size += len(header)
                header_stream = io.BytesIO(header)
                if np.lib.format.read_magic(header_stream) != (2, 0):
                    raise ValueError("raw operand has an unexpected NPY revision")
                observed, fortran, dtype = np.lib.format.read_array_header_2_0(
                    header_stream, max_header_size=capture.npy_header_bytes)
                if (tuple(observed) != capture.shape or dtype.str != capture.dtype or fortran
                        or header_stream.tell() != len(header) or dtype.hasobject or dtype.kind not in "biufc"):
                    raise ValueError("raw operand header differs from its actual capture")
                numeric_supported = dtype.kind == "f" and dtype.itemsize <= 8
                expected_bytes = math.prod(capture.shape) * dtype.itemsize
                remaining = expected_bytes
                chunk_bytes = max(dtype.itemsize, (BLOCK_BYTES // dtype.itemsize) * dtype.itemsize)
                while remaining:
                    payload = stream.read(min(chunk_bytes, remaining))
                    if not payload or len(payload) % dtype.itemsize:
                        raise ValueError("raw operand lost complete native elements")
                    digest.update(payload)
                    size += len(payload)
                    remaining -= len(payload)
                    values = np.frombuffer(payload, dtype=dtype)
                    count += values.size
                    if numeric_supported:
                        finite = np.isfinite(values)
                        nonfinite += int(values.size - np.count_nonzero(finite))
                        if np.any(finite):
                            candidate = Decimal.from_float(float(np.max(np.abs(values[finite]))))
                            maximum = candidate if maximum is None else max(maximum, candidate)
                if stream.read(1):
                    raise ValueError("raw operand contains unselected trailing values")
        finally:
            source.close()
        materialization = capture.artifact_manifest.materialization
        if (size != capture.uncompressed_bytes or digest.hexdigest() != capture.uncompressed_sha256
                or stored_size != materialization.size_bytes or stored_hash.hexdigest() != materialization.physical_sha256):
            raise ValueError("raw operand differs from its authenticated complete custody")
        reasons = []
        if capture.shape != shape:
            reasons.append("WRONG_COMPLETE_NATIVE_SHAPE")
        if not numeric_supported:
            reasons.append("UNSUPPORTED_NATIVE_NUMERIC_DTYPE")
        if numeric_supported and nonfinite:
            reasons.append("NONFINITE_NATIVE_OPERAND")
        if maximum_absolute_value is not None and maximum is not None and maximum > maximum_absolute_value:
            reasons.append("DECLARED_NUMERICAL_MAGNITUDE_EXCEEDED")
        state = A.UNSUPPORTED if not numeric_supported else A.FALSIFIED if reasons else A.SATISFIED
        assessments.append(OperandIntegrity(name, shape, capture.shape, count,
            nonfinite if numeric_supported else None, maximum, state, tuple(sorted(reasons))))
    states = tuple(row.disposition for row in assessments)
    disposition = next(state for state in (A.UNEVALUABLE, A.FALSIFIED, A.UNSUPPORTED, A.SATISFIED) if state in states)
    return CoupledNumericalIntegrity(request.request_id + ".numerical-integrity", request.identity,
        ObjectIdentity.from_record(record.return_id, record), assessor_source, maximum_absolute_value,
        tuple(assessments), disposition)


def validate_native_return_assessment(request, record, assessment, reader_for_manifest):
    """Recompute a supplied consumer assessment from the exact retained operands."""
    if type(assessment) is not CoupledNumericalIntegrity:
        raise ValueError("consumer requires the exact typed native-return assessment")
    expected = assess_native_return(request, record, reader_for_manifest,
        assessor_source=assessment.assessor_source,
        maximum_absolute_value=assessment.maximum_absolute_value)
    if assessment != expected:
        raise ValueError("consumer assessment differs from the actual complete native return")
    return assessment
