# SPDX-License-Identifier: MPL-2.0
"""Shared HDF5 prototype only; no native source or scientific qualification."""

from dataclasses import replace
from hashlib import sha256

import h5py
import numpy as np
import pytest

from empirical_lawhood.infrastructure.matrix_hdf5_io import (
    HDF5ReadLimits, HDF5DatasetSource, open_verified_hdf5, open_verified_hdf5_port,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.references import ArtifactIdentity


def limits(**changes):
    values = dict(maximum_chunk_bytes=65536, maximum_slice_bytes=1048576,
        maximum_decoded_chunk_bytes=65536, maximum_raw_chunk_cache_bytes=1048576,
        maximum_metadata_cache_bytes=1048576, maximum_cache_slots=127,
        maximum_members=8, maximum_groups=4, maximum_attributes=16,
        maximum_attribute_bytes=4096, maximum_path_bytes=256)
    return HDF5ReadLimits(**(values | changes))


def fixture(tmp_path, *, chunks=None, attribute=None, compression=None):
    path = tmp_path / "source.h5"
    values = np.arange(800, dtype="<f8").reshape(100, 8)
    with h5py.File(path, "w") as handle:
        handle.attrs["fixed-source"] = np.bytes_(b"exposed fixture")
        if attribute is not None:
            handle.attrs["adverse"] = attribute
        handle.create_dataset("primary/positions", data=values, chunks=chunks, compression=compression)
    raw = path.read_bytes()
    artifact = ArtifactIdentity("fixture.exposed.hdf", "exposed-software-input",
        "empirical-lawhood/source/checksummed-uninterpreted-public-bytes", sha256(raw).hexdigest(),
        "application/x-hdf5", len(raw))
    return artifact, values, path


@pytest.mark.parametrize("chunks,compression", ((None, None), ((10, 8), "gzip")))
def test_actual_same_descriptor_hdf5_rows_and_metadata_close(tmp_path, chunks, compression):
    artifact, expected, _ = fixture(tmp_path, chunks=chunks, compression=compression)
    with open_verified_hdf5(artifact, root=tmp_path, relative_path="source.h5", limits=limits()) as source:
        assert source.read_attribute("fixed-source") == b"exposed fixture"
        assert source.members[0].shape == expected.shape and source.members[0].dtype == expected.dtype.str
        selected = source.read_array_slice("primary/positions", 31, 33)
        assert selected.tobytes() == expected[31:33].tobytes() and not selected.flags.writeable
        assert b"".join(source.open_member("primary/positions")) == expected.tobytes()
        assert source.read_member_range("primary/positions", 63, 137) == expected.tobytes()[63:137]
    with pytest.raises(ValueError, match="closed"):
        source.read_array_slice("primary/positions", 0, 1)


@pytest.mark.parametrize("damage", ("hash", "size", "chunk", "attributes", "members", "groups", "soft-link", "external-link"))
def test_original_container_and_operational_metadata_bounds_refuse(tmp_path, damage):
    artifact, _, path = fixture(tmp_path, chunks=(100, 8))
    selected = limits()
    if damage in {"soft-link", "external-link"}:
        with h5py.File(path, "r+") as handle:
            handle["unexpected"] = h5py.SoftLink("/primary") if damage == "soft-link" else h5py.ExternalLink("never-open.h5", "/")
        raw = path.read_bytes()
        artifact = replace(artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
    if damage == "hash":
        artifact = replace(artifact, sha256="8" * 64)
    elif damage == "size":
        artifact = replace(artifact, size_bytes=artifact.size_bytes + 1)
    elif damage == "chunk":
        selected = limits(maximum_decoded_chunk_bytes=64)
    elif damage == "attributes":
        selected = limits(maximum_attribute_bytes=4)
    elif damage == "members":
        with h5py.File(path, "r+") as handle:
            handle.create_dataset("other", data=np.zeros(1))
        raw = path.read_bytes()
        artifact = replace(artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
        selected = limits(maximum_members=1)
    elif damage == "groups":
        with h5py.File(path, "r+") as handle:
            handle.create_group("extra/subgroup")
        raw = path.read_bytes()
        artifact = replace(artifact, sha256=sha256(raw).hexdigest(), size_bytes=len(raw))
        selected = limits(maximum_groups=1)
    with pytest.raises(ValueError):
        with open_verified_hdf5(artifact, root=tmp_path, relative_path="source.h5", limits=selected):
            pytest.fail("adverse metadata reached a value consumer")


def test_variable_string_metadata_does_not_claim_a_decoded_length(tmp_path):
    artifact, _, _ = fixture(tmp_path, attribute="x" * 100000)
    with open_verified_hdf5(artifact, root=tmp_path, relative_path="source.h5", limits=limits()) as source:
        field = next(row for row in source.attributes if row.name == "adverse")
        assert field.variable_string and field.decoded_bytes is None
        with pytest.raises(ValueError, match="unsupported software"):
            source.read_attribute("adverse")


def test_variable_string_arrays_refuse_before_attribute_value_read(tmp_path):
    artifact, _, _ = fixture(tmp_path, attribute=np.asarray(("one", "two"), dtype=h5py.string_dtype()))
    with pytest.raises(ValueError, match="original scalar attribute"):
        with open_verified_hdf5(artifact, root=tmp_path, relative_path="source.h5", limits=limits()):
            pytest.fail("an unsupported variable string array reached attribute decoding")


def test_member_stream_honors_independently_selected_smaller_slice_bound(tmp_path):
    artifact, expected, _ = fixture(tmp_path)
    with open_verified_hdf5(artifact, root=tmp_path, relative_path="source.h5",
            limits=limits(maximum_slice_bytes=4096)) as source:
        chunks = list(source.open_member("primary/positions"))
        assert b"".join(chunks) == expected.tobytes()
        assert max(map(len, chunks)) <= 4096


def test_late_unused_container_mutation_refuses_final_whole_seal(tmp_path):
    artifact, _, path = fixture(tmp_path)
    with pytest.raises(ValueError, match="descriptor changed|hash verification"):
        with open_verified_hdf5(artifact, root=tmp_path, relative_path="source.h5", limits=limits()) as source:
            source.read_array_slice("primary/positions", 0, 1)
            with path.open("r+b", buffering=0) as changed:
                changed.seek(-1, 2)
                byte = changed.read(1)
                changed.seek(-1, 2)
                changed.write(bytes((byte[0] ^ 1,)))


def test_admitted_source_and_checked_cursor_bindings_cannot_be_replaced(tmp_path):
    artifact, _, _ = fixture(tmp_path)
    with open_verified_hdf5(artifact, root=tmp_path, relative_path="source.h5", limits=limits()) as source:
        with pytest.raises(AttributeError, match="read-only"):
            source._handle = None
        with pytest.raises(AttributeError, match="read-only"):
            source._physical.descriptor = 0
        with pytest.raises(AttributeError, match="read-only"):
            source.limits = limits(maximum_attribute_bytes=1)


def test_operational_limits_are_one_canonical_contract_without_scientific_defaults():
    from empirical_lawhood.runtime.array_datasets import HDF5ReadLimits as RuntimeLimits
    selected = limits()
    assert RuntimeLimits is HDF5ReadLimits
    assert decode_canonical_bytes(selected.canonical_bytes(), RuntimeLimits, maximum_bytes=8192) == selected
    with pytest.raises(ValueError, match="exact integers"):
        limits(maximum_members=True)


def test_unbounded_or_label_only_context_refuses_before_any_hdf5_value_admission(tmp_path):
    from empirical_lawhood.infrastructure.execution import ResourceAdmissionError
    artifact, _, _ = fixture(tmp_path, attribute="genuine original scalar string")
    with pytest.raises(ResourceAdmissionError, match="original prepared task"):
        with open_verified_hdf5_port(artifact, None, limits=limits(), task_context=None):
            pytest.fail("an absent actual worker bound admitted HDF5")
    with pytest.raises(TypeError, match="actual process allocation scope"):
        HDF5DatasetSource(None, limits(), None, allocation_scope=True)


@pytest.mark.parametrize("view", ("PRIMARY", "FINE"))
def test_original_measurement_equations_accept_bounded_native_rows_without_whole_coercion(view):
    from empirical_lawhood.adapters.methods.matrix_dataset_readers import MatrixArrayRows
    from empirical_lawhood.adapters.methods.matrix_history_analysis import algebra
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import measure_trace
    from empirical_lawhood.infrastructure.dataset_readers import ArrayDatasetReader, AuthenticatedBlockByteSource
    from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember
    from tests.test_matrix_factor_lifetime import root, spec

    positions = np.broadcast_to(np.stack((algebra.LEFT, algebra.RIGHT)), (97, 2, 3, 4, 4)).copy()
    expected, diagnostic_values = measure_trace(spec(), root(), view, "Y", positions)
    raw = positions.tobytes()
    requests = []

    class ExposedValues:
        def open_member(self, name):
            for start in range(0, len(raw), 8192):
                yield raw[start:start + 8192]

        def read_range(self, name, start, stop):
            requests.append((start, stop))
            return raw[start:stop]

        def close(self):
            pass

    member = ArrayDatasetMember("positions", positions.dtype.str, positions.shape, sha256(raw).hexdigest())
    manifest = ArrayDatasetManifest("dataset.exposed.factor-native-row-control", (member,), ())
    source = ExposedValues()
    reader = ArrayDatasetReader(manifest, AuthenticatedBlockByteSource(source, read_range=source.read_range, close=source.close),
        maximum_chunk_bytes=8192, maximum_slice_bytes=8192)
    with reader.verified_session(block_size_bytes=8192) as verified:
        rows = MatrixArrayRows(verified, member)
        assert rows.ndim == 5 and rows[96, 1].tobytes() == positions[96, 1].tobytes()
        with pytest.raises(TypeError, match="whole-population"):
            np.asarray(rows)
        actual, diagnostics = measure_trace(spec(), root(), view, "Y", rows)
        assert actual.canonical_bytes() == expected.canonical_bytes()
        assert all(np.array_equal(diagnostics[name], diagnostic_values[name], equal_nan=True) for name in diagnostics)
    assert requests and max(stop - start for start, stop in requests) <= 8192
    with pytest.raises(ValueError, match="closed"):
        rows[0]
