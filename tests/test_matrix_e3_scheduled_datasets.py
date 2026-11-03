# SPDX-License-Identifier: MPL-2.0
"""Real lossless physical transforms over disclosed E3 mathematical fixtures.

The selected arrays are authored test data, never native qualification evidence.
The existing transform writer admits each physical member before consumption.
"""

from contextlib import ExitStack, contextmanager
from dataclasses import replace
import json
import tracemalloc

import pytest

from empirical_lawhood.adapters.methods.matrix_dataset_readers import bridge_saved_arrays, verified_array_mappings
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_prefix_science as prefix
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseArrays
from empirical_lawhood.infrastructure.dataset_readers import ArrayDatasetReader, ArrayTransformWriter, DatasetFDMember, PhysicalFDByteSource
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_e3_protected_feature import finite_case, project
from tests.test_matrix_e3_protected_prefix_science import case as case, context, forbid_native as forbid_native  # noqa: F401


BLOCK = 65536


@contextmanager
def physical_dataset(original, raw, directory):
    """Use the actual existing admitted transpose codec, without a new roster."""
    directory.mkdir()
    bridge = bridge_saved_arrays(original, raw, maximum_chunk_bytes=BLOCK,
        maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES)
    witnesses = {}
    source = None
    try:
        with ExitStack() as stack:
            with bridge.reader.verified_session(block_size_bytes=BLOCK) as session:
                for member in session.manifest.members:
                    handle = stack.enter_context((directory / (member.name + ".values")).open("x+b"))
                    handle.truncate(member.size_bytes)
                    writer = ArrayTransformWriter(session.manifest, member.name,
                        DatasetFDMember(handle.fileno(), 0, member.size_bytes, member.size_bytes),
                        axis_order=tuple(reversed(range(len(member.shape)))) if member.name == "frame"
                            else tuple(range(len(member.shape))),
                        block_size_bytes=BLOCK, maximum_chunk_bytes=BLOCK)
                    try:
                        for block in session.iter_member_bytes(member.name):
                            assert writer.write(block) == len(block)
                        witnesses[member.name] = writer.finish()
                    finally:
                        writer.close()
            source = PhysicalFDByteSource(bridge.reader.manifest, witnesses,
                maximum_chunk_bytes=BLOCK, maximum_cache_bytes=2 * BLOCK)
            reader = ArrayDatasetReader(bridge.reader.manifest, source, maximum_chunk_bytes=BLOCK,
                maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES)
            yield reader
    finally:
        if source is not None:
            source.close()
        for witness in witnesses.values():
            witness.close()
        bridge.close()


def scientific_products(case, native, *, diagnostics=None, diagnostic_owner=None):
    arguments = context(case)
    numerical = prefix.assess_prefix(case.history, native, **arguments)
    raw, witness = prefix.measure_prefix(case.history, numerical, native,
        artifact_id="literal.dataset.diagnostics", **arguments)
    if diagnostics is None:
        diagnostics = raw
    else:
        # Physical encoding does not change the scientific witness's original
        # ordinary array identity. This is the exact separately retained owner.
        witness = replace(witness, arrays=diagnostic_owner)
    frames = prefix.check_frames(case.history, numerical, witness, native, diagnostics, **arguments)
    causal_raw, causal = prefix.causal_delivery(case.history, numerical, witness, frames, native, diagnostics,
        artifact_id="literal.dataset.causal", **arguments)
    return numerical, raw, witness, frames, causal_raw, causal


def test_all_current_prefix_products_match_over_npz_and_admitted_physical_members(case, tmp_path):
    expected = scientific_products(case, case.native_raw)
    arguments = context(case)
    with physical_dataset(case.history.arrays, case.native_raw, tmp_path / "native-numerical") as native:
        numerical = prefix.assess_prefix(case.history, native, **arguments)
        native_bytes = native.manifest.size_bytes
    with physical_dataset(case.history.arrays, case.native_raw, tmp_path / "native-measure") as native:
        raw, witness = prefix.measure_prefix(case.history, numerical, native,
            artifact_id="literal.dataset.diagnostics", **arguments)
    with physical_dataset(case.history.arrays, case.native_raw, tmp_path / "native-check") as native:
        with physical_dataset(witness.arrays, raw, tmp_path / "diagnostic-check") as diagnostics:
            frames = prefix.check_frames(case.history, numerical, witness, native, diagnostics, **arguments)
    with physical_dataset(case.history.arrays, case.native_raw, tmp_path / "native-project") as native:
        with physical_dataset(witness.arrays, raw, tmp_path / "diagnostic-project") as diagnostics:
            tracemalloc.start()
            try:
                causal_raw, causal = prefix.causal_delivery(case.history, numerical, witness, frames, native, diagnostics,
                    artifact_id="literal.dataset.causal", **arguments)
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            diagnostic_bytes = diagnostics.manifest.size_bytes
    actual = numerical, raw, witness, frames, causal_raw, causal
    assert tuple(value.canonical_bytes() if hasattr(value, "canonical_bytes") else value for value in actual) == tuple(
        value.canonical_bytes() if hasattr(value, "canonical_bytes") else value for value in expected)
    assert not numerical.numerical_pass and causal.disposition == "UNEVALUABLE"
    (tmp_path / "assessment-memory.json").write_text(json.dumps({
        "prefix_logical_bytes": native_bytes, "diagnostic_logical_bytes": diagnostic_bytes,
        "traced_peak_bytes_through_causal_assessment_and_final_seals": peak,
        "chunk_bytes": BLOCK, "physical_cache_bytes_per_source": 2 * BLOCK,
        "scope": "Includes scientific source/record validation and output assembly; excludes fixture/transform construction, process RSS and kernel caches. Each operation uses a fresh one-shot lease. No speedup or global bounded-population claim.",
    }, indent=2) + "\n")


@pytest.mark.parametrize("available", (False, True))
def test_same_seedless_feature_over_npz_and_real_transposed_value_storage(case, tmp_path, available):
    selected = finite_case(case) if available else case
    expected = project(selected)
    with physical_dataset(selected.causal.arrays, selected.causal_raw, tmp_path / "causal") as causal:
        with physical_dataset(selected.witness.arrays, selected.diagnostic_raw, tmp_path / "diagnostics") as diagnostics:
            actual = project(selected, causal_raw=causal, diagnostic_raw=diagnostics)
    assert actual.canonical_bytes() == expected.canonical_bytes()
    assert (actual.disposition, len(actual.values)) == (("AVAILABLE", 21) if available else ("UNAVAILABLE", 0))


def test_original_response_envelope_uses_source_and_producers_without_invented_allocation(case):
    original = case.causal.arrays
    response = ScheduledResponseArrays("literal.dataset.response-envelope", "FORECAST", original.source,
        original.array_artifact, original.members, original.producers,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    bridge = bridge_saved_arrays(response, case.causal_raw, maximum_chunk_bytes=BLOCK,
        maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES)
    try:
        assert not hasattr(response, "allocation")
        assert set(bridge.reader.manifest.scientific_references) == {*response.producers, response.source}
        with verified_array_mappings((response,), (bridge,)) as (values,):
            assert set(values) == {member.name for member in response.members}
    finally:
        bridge.close()


@pytest.mark.parametrize("change", ("source", "producer", "member"))
def test_existing_logical_reader_cannot_substitute_original_scientific_associations(case, tmp_path, change):
    owner = case.causal.arrays
    with physical_dataset(owner, case.causal_raw, tmp_path / "causal") as reader:
        reference = ObjectIdentity("literal.foreign.source", owner.source.object_schema,
            owner.source.object_version, "b" * 64)
        if change == "source":
            other = replace(owner, source=reference)
        elif change == "producer":
            other = replace(owner, producers=tuple(sorted((*owner.producers, reference), key=lambda row: row.object_id)))
        else:
            other = replace(owner, members=(replace(owner.members[0], sha256="c" * 64), *owner.members[1:]))
        with pytest.raises(ValueError, match="scientific values or source associations"):
            with verified_array_mappings((other,), (reader,)):
                raise AssertionError("substituted original reached scientific arithmetic")
