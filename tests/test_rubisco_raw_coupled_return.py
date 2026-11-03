# SPDX-License-Identifier: MPL-2.0
"""Lossless exposed returns through real AR3 custody; no molecular contact."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import gzip
import io
import subprocess
import sys
import tracemalloc
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import raw_coupled_return as m
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkDefinition, NativeSubworkRoster, NativeSubworkUncertainContact,
)
from tests.runtime_platform.test_native_subwork import ExposedInput, _plane, _store


@pytest.fixture
def custody(tmp_path):
    plane = _plane(tmp_path / "raw-return")
    source_records = tuple(ExposedInput(name, "DISCLOSED-SYNTHETIC") for name in (
        "source.protocol", "source.preparation", "source.coordinates"))
    sources = tuple(ObjectIdentity.from_record(row.selected_id, row) for row in source_records)
    package_sources = (("src/exposed-raw-return.py", "4" * 64),)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "5" * 64, package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(), "3" * 40, False)
    request = m.CoupledEvaluationRequest("exposed.coupled", *sources, provenance.identity, 2)
    inputs = []
    for name, record in (*((row.selected_id, row) for row in source_records),
                         (provenance.identity.object_id, provenance), (request.request_id, request)):
        result = plane.write(ArtifactWriteRequest(name, "inputs/" + name + ".json", record.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.raw.inputs", "inputs",
            record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        inputs.append(decode_artifact_manifest(plane.root.resolve(
            result.materialization.relative_path + ".manifest.json", for_write=False).read_bytes()))
    inputs = tuple(sorted(inputs, key=lambda row: row.materialization.materialization_id))
    parent = NativeEffectContact("exposed.raw", "coupled.return", "exposed.raw.coupled.return.attempt-001",
        ObjectIdentity("plan.exposed", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity("coupled.return", "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        "3" * 40, tuple(row.materialization.materialization_id for row in inputs), ())
    store = _store(plane, parent, inputs)
    store.parent_contacts.begin(parent)
    definition = NativeSubworkDefinition("coupled.one", "exposed.coupled", parent, request.identity,
        tuple(sorted((*sources, provenance.identity), key=lambda row: row.object_id)),
        provenance.code_sources_sha256, provenance.dependency_lock_sha256,
        parent.input_materialization_ids, (), m.return_outputs())
    store.freeze_roster(NativeSubworkRoster("selected.native-subwork", parent, (definition.identity,)),
        definitions=(definition,))
    entry = store.begin(definition, inputs)
    store.contact(entry)  # Exposed software contact, no solver invocation.
    def reader(manifest):
        plane.verify_manifest(manifest)
        return plane.root.resolve(manifest.materialization.relative_path, for_write=False).open("rb")
    return SimpleNamespace(request=request, store=store, entry=entry, definition=definition,
        plane=plane, reader=reader, inputs=inputs)


ASSESSOR = ObjectIdentity("assessor.exposed", "empirical-lawhood/tests/raw-operand-assessor", "1.0.0", "a" * 64)


def assessed(custody, record, **kwargs):
    return m.assess_native_return(custody.request, record, custody.reader,
        assessor_source=ASSESSOR, **kwargs)


def decoded(custody, capture):
    with custody.reader(capture.artifact_manifest) as stream:
        payload = gzip.decompress(stream.read())
    assert sha256(payload).hexdigest() == capture.uncompressed_sha256
    return np.load(io.BytesIO(payload), allow_pickle=False)


def test_capture_precedes_guards_and_exact_negative_return_recovers(custody):
    record = m.capture_native_return(custody.request, 4.83e12,
        np.array([[0., -0., 1.], [2., 3., 4.]]), custody.store, custody.entry)
    assert record.scientific_admission is A.NOT_ATTEMPTED
    assert len(custody.store.inspect(custody.definition).outputs) == 3
    report = assessed(custody, record, maximum_absolute_value=Decimal("1e8"))
    assert report.disposition == "FALSIFIED"
    assert report.operands[0].absolute_maximum == Decimal.from_float(4.83e12)
    assert report.operands[0].reason_codes == ("DECLARED_NUMERICAL_MAGNITUDE_EXCEEDED",)
    assert report.derivative_consistency is report.preparation_adequacy is A.NOT_ATTEMPTED
    completion = custody.store.complete(custody.entry, operational_status=OperationalStatus.SUCCEEDED,
        cost=InquiryCost(None, Decimal(".20"), None), cost_scope="exposed returned-call capture; no native computation")
    fresh = ExternalNativeSubworkStore(plane=custody.plane, parent_contacts=custody.store.parent_contacts)
    assert fresh.recover(custody.definition) == completion
    with pytest.raises(ValueError, match="completed"):
        fresh.begin(custody.definition, custody.inputs)
    products = {row.logical.logical_artifact_id.rsplit(".", 1)[-1]: row for row in completion.outputs}
    assert products
    manifest = next(row for row in completion.outputs if row.logical.payload_schema == m.RawCoupledReturn.SCHEMA)
    with custody.reader(manifest) as source:
        exact = source.read()
    assert decode_canonical_bytes(exact, m.RawCoupledReturn, maximum_bytes=len(exact)) == record


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_nonfinite_actual_return_is_retained_and_falsified(custody, value):
    gradient = np.zeros((2, 3)); gradient[1, 2] = value
    record = m.capture_native_return(custody.request, value, gradient, custody.store, custody.entry)
    assert decoded(custody, record.gradient).tobytes() == gradient.tobytes()
    report = assessed(custody, record)
    assert report.disposition == "FALSIFIED"
    assert [row.nonfinite_values for row in report.operands] == [1, 1]


@pytest.mark.parametrize("shape", [(1, 3), (2, 2), (0, 3), (6,)])
def test_wrong_or_missing_physical_rows_retained_before_negative(custody, shape):
    record = m.capture_native_return(custody.request, 0., np.zeros(shape), custody.store, custody.entry)
    assert record.gradient.shape == shape
    report = assessed(custody, record)
    assert report.disposition == "FALSIFIED"
    assert report.operands[1].retained_values == np.prod(shape)
    assert "WRONG_COMPLETE_NATIVE_SHAPE" in report.operands[1].reason_codes


def test_noncontiguous_big_endian_bits_and_unknown_dtype_are_not_cast(custody):
    original = np.arange(12, dtype=">f8").reshape(2, 6)[:, ::-2]
    record = m.capture_native_return(custody.request, np.float32(-0.), original, custody.store, custody.entry)
    assert record.gradient.dtype == original.dtype.str
    assert record.gradient.source_strides == original.strides
    assert decoded(custody, record.gradient).tobytes() == original.tobytes()
    assert decoded(custody, record.energy).tobytes() == np.array(np.float32(-0.)).tobytes()
    assert assessed(custody, record).disposition == "SATISFIED"


@pytest.mark.parametrize("dtype", [np.int64, np.complex128, np.bool_])
def test_other_primitive_numeric_types_capture_but_remain_unsupported(custody, dtype):
    record = m.capture_native_return(custody.request, 1., np.ones((2, 3), dtype=dtype), custody.store, custody.entry)
    assert decoded(custody, record.gradient).dtype == dtype
    report = assessed(custody, record)
    assert report.disposition == "UNSUPPORTED" and report.operands[1].nonfinite_values is None


def test_ambiguous_operand_cannot_be_completed_from_expected_zeros(custody):
    record = m.capture_native_return(custody.request, 1., [[0., 0., 0.]] * 2, custody.store, custody.entry)
    assert record.energy is not None and record.gradient is None
    assert record.capture_failures[0][0] == "gradient"
    assert assessed(custody, record).disposition == "UNEVALUABLE"
    assert len(custody.store.inspect(custody.definition).outputs) == 2
    completion = custody.store.complete(custody.entry, operational_status=OperationalStatus.FAILED,
        cost=InquiryCost(None, None, None), cost_scope="exposed return with unsupported source type",
        reason_codes=("UNREPRESENTABLE_NATIVE_RETURN",))
    assert completion.completion.omitted_output_ids == ("raw.gradient",)


def test_request_substitution_and_missing_output_commitment_refuse_before_capture(custody):
    with pytest.raises(ValueError, match="configuration/sources"):
        m.capture_native_return(replace(custody.request, physical_atom_count=3), 0., np.zeros((2, 3)),
            custody.store, custody.entry)
    entry = SimpleNamespace(definition=replace(custody.definition, outputs=()))
    with pytest.raises(ValueError, match="complete output"):
        m.capture_native_return(custody.request, 0., np.zeros((2, 3)), custody.store, entry)
    assert custody.store.inspect(custody.definition).outputs == ()


def test_publication_failure_stays_uncertain_without_assessment_or_replay(custody):
    class RefusingPort:
        def publish_output(self, *args, **kwargs):
            raise ArtifactIdentityConflict("exposed custody failure")
    with pytest.raises(ArtifactIdentityConflict, match="custody failure"):
        m.capture_native_return(custody.request, 1., np.zeros((2, 3)), RefusingPort(), custody.entry)
    with pytest.raises(NativeSubworkUncertainContact):
        custody.store.begin(custody.definition, custody.inputs)
    with pytest.raises(NativeSubworkUncertainContact):
        custody.store.recover(custody.definition)


def test_source_corruption_refuses_and_admission_forgery_refuses(custody):
    record = m.capture_native_return(custody.request, 1., np.ones((2, 3)), custody.store, custody.entry)
    corrupt = replace(record, gradient=replace(record.gradient, uncompressed_sha256="f" * 64))
    with pytest.raises(ValueError, match="complete custody"):
        assessed(custody, corrupt)
    report = assessed(custody, record, maximum_absolute_value=Decimal(".5"))
    with pytest.raises(ValueError, match="adverse operand"):
        replace(report, disposition="SATISFIED")
    with pytest.raises(ValueError, match="physical/biological"):
        replace(report, biological_prediction="ESTABLISHED")
    assert m.validate_native_return_assessment(custody.request, record, report, custody.reader) == report
    fabricated = replace(report, operands=(replace(report.operands[0], absolute_maximum=Decimal(".75")), report.operands[1]))
    with pytest.raises(ValueError, match="actual complete native"):
        m.validate_native_return_assessment(custody.request, record, fabricated, custody.reader)


def test_large_source_serialization_has_bounded_buffers_and_complete_denominator():
    array = np.arange(900_000, dtype=np.float64).reshape(300_000, 3)
    header = m._header(array)
    tracemalloc.start()
    chunks = 0; total = 0
    try:
        for chunk in m._gzip_chunks(m._npy_chunks(array, header)):
            assert len(chunk) <= m.BLOCK_BYTES
            chunks += 1; total += len(chunk)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert total and chunks and peak < 8 * m.BLOCK_BYTES
    size, _ = m._digest_chunks(m._npy_chunks(array, header))
    assert size == len(header) + array.nbytes


def test_cold_capture_import_performs_no_scientific_import():
    code = "from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import raw_coupled_return; import sys; assert not any(n.split('.')[0] in {'numpy','openmm','parmed','ash','pyscf'} for n in sys.modules)"
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)
