# SPDX-License-Identifier: MPL-2.0
"""Independent scheduled reader joins and final seals over disclosed literals.

Transforms use the existing admitted physical codec. No native acquisition,
worker process, source qualification or exposure authority is exercised.
"""

from dataclasses import replace
import os

import pytest

from empirical_lawhood.adapters.methods import matrix_dataset_readers as datasets
from empirical_lawhood.adapters.methods.matrix_scheduled_history import forecast, science
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
from tests.test_matrix_dataset_readers import real_port
from tests.test_matrix_e3_protected_feature import finite_case, project
from tests.test_matrix_e3_protected_prefix_science import blocked
from tests.test_matrix_e3_protected_prefix_science import case as case, forbid_native as forbid_native  # noqa: F401
from tests.test_matrix_e3_scheduled_datasets import BLOCK, physical_dataset


@pytest.fixture(scope="module")
def finite(case):
    return finite_case(case)


def test_logical_equivalence_keeps_domain_phase_and_access_guards(case, tmp_path, monkeypatch):
    owner = case.history.arrays
    other_phase = replace(owner, role="CAUSAL_STATE")
    monkeypatch.setattr(science, "decode_matrix_arrays", blocked)
    with physical_dataset(owner, case.native_raw, tmp_path / "native") as reader:
        # The storage manifest is deliberately packaging/phase independent.
        # Acceptance here cannot stand in for the original scientific guard.
        with datasets.verified_array_mappings((other_phase,), (reader,)) as (values,):
            assert set(values) == {member.name for member in owner.members}
            with pytest.raises(ValueError, match="wrong original source/member scope"):
                science.consume_prefix(case.source, other_phase, reader)
            with pytest.raises(ValueError, match="array phase"):
                replace(case.history, arrays=other_phase)
    with pytest.raises(ValueError, match="causal/protected scope"):
        replace(owner, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)


def test_transformed_values_keep_ordinary_physical_alias_outside_logical_identity(finite, tmp_path):
    owner = finite.causal.arrays
    alias = replace(owner, array_artifact=replace(owner.array_artifact,
        artifact_id="literal.independent.ordinary-causal-alias"))
    causal = replace(finite.causal, arrays=alias)
    expected = project(finite, causal=causal)
    with physical_dataset(owner, finite.causal_raw, tmp_path / "causal") as reader:
        actual = project(finite, causal=causal, causal_raw=reader)
        assert actual.canonical_bytes() == expected.canonical_bytes()
        assert actual.disposition == "AVAILABLE" and len(actual.values) == 21
        assert set(reader.manifest.scientific_references) == {*owner.producers, owner.source}
        assert owner.array_artifact.artifact_id != alias.array_artifact.artifact_id
        assert not hasattr(owner, "allocation")


@pytest.mark.parametrize("cached", (False, True))
def test_feature_cannot_escape_final_seal_after_calculation(finite, tmp_path, monkeypatch, cached):
    original = forecast.causal_feature_values
    completed = []
    directory = tmp_path / "causal"
    with physical_dataset(finite.causal.arrays, finite.causal_raw, directory) as reader:
        def calculate_then_change_physical_bytes(*args, **kwargs):
            result = original(*args, **kwargs)
            assert result[0] == "AVAILABLE" and len(result[1]) == 21
            # One member is already read by the original equations; the fine
            # positions member is unused by those equations. Both must seal.
            member = "primary_positions" if cached else "fine_positions"
            path = directory / (member + ".values")
            with path.open("r+b", buffering=0) as handle:
                end = path.stat().st_size - 1
                value = os.pread(handle.fileno(), 1, end)
                assert len(value) == 1
                assert os.pwrite(handle.fileno(), bytes((value[0] ^ 1,)), end) == 1
            completed.append(result)
            return result

        monkeypatch.setattr(forecast, "causal_feature_values", calculate_then_change_physical_bytes)
        with pytest.raises(ValueError, match="physical array final whole seal"):
            project(finite, causal_raw=reader)
        assert len(completed) == 1


def test_preflight_failure_does_not_consume_an_unopened_caller_bridge(finite, tmp_path):
    first = datasets.bridge_saved_arrays(finite.causal.arrays, finite.causal_raw,
        maximum_chunk_bytes=BLOCK, maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES)
    try:
        with physical_dataset(finite.witness.arrays, finite.diagnostic_raw, tmp_path / "diagnostics") as second:
            foreign = replace(finite.witness.arrays, source=replace(finite.witness.arrays.source,
                object_fingerprint="f" * 64))
            inputs = iter((first, second))
            with pytest.raises(ValueError, match="aliases differing original scientific identities"):
                with datasets.retained_array_mappings((finite.causal.arrays, foreign), lambda artifact: next(inputs),
                        maximum_chunk_bytes=BLOCK, maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES):
                    pytest.fail("foreign second owner reached scientific calculation")
            # No verified session was entered during complete preflight.
            # Successful use below consumes the original one-shot lease.
            with datasets.verified_array_mappings((finite.causal.arrays,), (first,)) as (values,):
                assert values["frame"].tobytes() == finite.values["frame"].tobytes()
    finally:
        first.close()


def test_late_closed_reader_refusal_reaps_created_bridge_but_preserves_original_port(finite, tmp_path, monkeypatch):
    # Closing a genuine physical source retains its original manifest but
    # makes acquiring its actual descriptor lease fail on the later operand.
    with physical_dataset(finite.witness.arrays, finite.diagnostic_raw, tmp_path / "diagnostics") as second:
        pass
    port = real_port(finite.causal.arrays.array_artifact, finite.causal_raw)
    created = []
    bridge_saved_arrays = datasets.bridge_saved_arrays

    def capture_created(*args, **kwargs):
        bridge = bridge_saved_arrays(*args, **kwargs)
        created.append(bridge)
        return bridge

    monkeypatch.setattr(datasets, "bridge_saved_arrays", capture_created)
    try:
        inputs = iter((port, second))
        with pytest.raises(ValueError, match="physical array descriptor lease is closed"):
            with datasets.retained_array_mappings((finite.causal.arrays, finite.witness.arrays),
                    lambda artifact: next(inputs), maximum_chunk_bytes=BLOCK,
                    maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES):
                pytest.fail("closed second lease reached scientific calculation")
        assert len(created) == 1
        assert created[0]._source.physical[0]._closed
        cursor = port.cursor()
        try:
            assert cursor.read() == finite.causal_raw
        finally:
            cursor.close()
    finally:
        port.close()
        for bridge in created:
            bridge.close()
