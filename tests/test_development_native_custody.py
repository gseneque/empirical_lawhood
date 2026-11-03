# SPDX-License-Identifier: MPL-2.0
"""Actual manifest/receipt custody, generic effects, and historical marker bytes."""

from dataclasses import dataclass
from typing import ClassVar

import pytest

from empirical_lawhood.api.matrix_native_custody import MatrixNativeCustody, MatrixNativeEffectInput
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.development_native_custody import DevelopmentNativeCustody, DevelopmentNativeEffectInput
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile


@dataclass(frozen=True, slots=True)
class SyntheticConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/native-config"
    config_id: str = "synthetic.config"
    choice: int = 1


@dataclass(frozen=True, slots=True)
class SyntheticResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/tests/native-result"
    disposition: str = "NEGATIVE"


@pytest.fixture
def custody(tmp_path):
    root = tmp_path / "development"
    root.mkdir()
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "synthetic.development", "software conformance only", str(root), str(next(parent for parent in root.parents if parent.is_mount())),
        OperatorStorageProfile.SCHEMA, 1, None, None, ())))
    return DevelopmentNativeCustody(writer=plane, config=SyntheticConfig(),
        run_id="synthetic.run", implementation_commit="0" * 40,
        minimum_free_bytes=1, maximum_output_bytes=4096)


def test_retained_negative_uses_receipts_and_is_immutable_after_fresh_reader(custody):
    custody.begin_native_effect("unit-one")
    result = SyntheticResult()
    custody.retain("unit-one", result)
    fresh = DevelopmentNativeCustody(writer=ExternalArtifactPlane(custody.writer.root),
        config=custody.config, run_id=custody.run_id, implementation_commit="0" * 40,
        minimum_free_bytes=1, maximum_output_bytes=4096, read_only=True)
    assert fresh.load("unit-one", SyntheticResult) == result
    with pytest.raises(ValueError, match="immutable"):
        fresh.retain("unit-one", SyntheticResult("POSITIVE"))
    with pytest.raises(ArtifactIdentityConflict, match="bytes differ"):
        path = fresh.writer.root.resolve("runs/synthetic.run/outputs/unit-one.json", for_write=True)
        path.write_bytes(result.canonical_bytes().replace(b"NEGATIVE", b"POSITIVE"))
        fresh.load("unit-one", SyntheticResult)


def test_interrupted_marker_refuses_reacquisition_and_canonical_schema_is_generic(custody):
    custody.begin_native_effect("interrupted")
    raw = custody.writer.root.resolve(
        "runs/synthetic.run/inputs/effects/interrupted.json", for_write=False).read_bytes()
    marker = decode_canonical_bytes(raw, DevelopmentNativeEffectInput, maximum_bytes=4096)
    assert marker.configuration == custody.parent.identity
    assert marker.canonical_bytes() == raw
    with pytest.raises(ValueError, match="uncertain effects"):
        custody.load("interrupted", SyntheticResult)
    with pytest.raises(ValueError, match="no retry"):
        custody.begin_native_effect("interrupted")


def test_matrix_wrapper_keeps_original_effect_record_bytes(custody):
    wrapper = MatrixNativeCustody(writer=custody.writer, config=custody.config,
        run_id="synthetic.matrix", implementation_commit="0" * 40,
        minimum_free_bytes=1, maximum_output_bytes=4096)
    wrapper.begin_native_effect("unit-one")
    raw = wrapper.writer.root.resolve(
        "runs/synthetic.matrix/inputs/effects/unit-one.json", for_write=False).read_bytes()
    assert raw == MatrixNativeEffectInput(
        "synthetic.matrix", "unit-one", wrapper.parent.identity).canonical_bytes()


def test_source_and_selected_input_substitution_cannot_reuse_a_receipt(custody):
    custody.retain("unit-one", SyntheticResult())
    other_source = DevelopmentNativeCustody(writer=custody.writer, config=custody.config,
        run_id=custody.run_id, implementation_commit="1" * 40,
        minimum_free_bytes=1, maximum_output_bytes=4096, read_only=True)
    with pytest.raises(ValueError, match="changes source"):
        other_source.load("unit-one", SyntheticResult)
    with pytest.raises(ValueError, match="retained input differs"):
        DevelopmentNativeCustody(writer=custody.writer, config=SyntheticConfig(choice=2),
            run_id=custody.run_id, implementation_commit="0" * 40,
            minimum_free_bytes=1, maximum_output_bytes=4096, read_only=True)



def test_reader_derives_original_producer_but_cannot_publish_or_enter(custody):
    result = SyntheticResult()
    custody.retain("unit-one", result)
    fresh = DevelopmentNativeCustody(writer=ExternalArtifactPlane(custody.writer.root),
        config=custody.config, run_id=custody.run_id, implementation_commit=None,
        minimum_free_bytes=1, maximum_output_bytes=4096, read_only=True)
    assert fresh.implementation_commit is None
    assert fresh.load("unit-one", SyntheticResult) == result
    assert fresh.implementation_commit == "0" * 40
    with pytest.raises(ValueError, match="read-only"):
        fresh.retain("another-unit", result)
    with pytest.raises(ValueError, match="read-only"):
        fresh.begin_native_effect("another-unit")
    with pytest.raises(ValueError, match="selected producing commit"):
        DevelopmentNativeCustody(writer=custody.writer, config=custody.config,
            run_id=custody.run_id, implementation_commit=None,
            minimum_free_bytes=1, maximum_output_bytes=4096)


def test_inferred_producer_does_not_allow_mixed_receipt_sources(custody):
    custody.retain("first", SyntheticResult())
    other = DevelopmentNativeCustody(writer=custody.writer, config=custody.config,
        run_id=custody.run_id, implementation_commit="1" * 40,
        minimum_free_bytes=1, maximum_output_bytes=4096)
    other.retain("second", SyntheticResult())
    fresh = DevelopmentNativeCustody(writer=ExternalArtifactPlane(custody.writer.root),
        config=custody.config, run_id=custody.run_id, implementation_commit=None,
        minimum_free_bytes=1, maximum_output_bytes=4096, read_only=True)
    assert fresh.load("first", SyntheticResult) == SyntheticResult()
    with pytest.raises(ValueError, match="changes source"):
        fresh.load("second", SyntheticResult)
