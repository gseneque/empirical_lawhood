# SPDX-License-Identifier: MPL-2.0
"""Complete exposed domain-shaped custody; no acquisition or qualification."""

from dataclasses import replace
from decimal import Decimal as D
import gc
from hashlib import sha256
import json
from pathlib import Path
import resource
import shutil
import sys

import h5py
import numpy as np

from empirical_lawhood.adapters.methods.analytic_material_inquiry import science as material
from empirical_lawhood.adapters.physical.virtual_cell.contracts import MatrixEncoding, VirtualCellSplit
from empirical_lawhood.adapters.physical.virtual_cell.dataset import inspect_h5ad
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, copy_bounded_file
from empirical_lawhood.infrastructure.matrix_array_io import iter_worker_matrix_array_chunks
from empirical_lawhood.infrastructure.recursive_custody import iter_exact_custody_file_chunks, iter_recursive_product_records
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ArtifactStreamWriteRequest
from tests.rubisco_nomination_fixture import sources
from tests.test_battery_thermal_service import _trace
from tests.test_matrix_array_worker_delivery import stock
from tests.test_recursive_public_service import _plane


def _rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


def main():
    selected = Path(sys.argv[1])
    selected.mkdir()
    plane = _plane(selected / "published")
    base = Path(plane.root.contract.canonical_path)
    products = {"product_index": [], "outputs": {}}
    codecs, populations = {}, {}
    baseline = _rss()

    def retain(kind, record, count, population):
        raw = record.canonical_bytes()
        assert decode_canonical_bytes(raw, type(record), maximum_bytes=len(raw)).canonical_bytes() == raw
        scratch = selected / (kind + ".json")
        scratch.write_bytes(raw)
        digest, size = sha256(raw).hexdigest(), len(raw)
        del raw
        codecs[record.SCHEMA] = type(record)
        populations[kind] = population
        for number in range(count):
            logical_id = f"exposed.{kind}.copy-{number:03d}"
            path = f"products/{kind}-{number:03d}.json"
            manifest = plane.write_stream(ArtifactStreamWriteRequest(
                logical_artifact_id=logical_id, relative_path=path,
                payload_schema=record.SCHEMA, profile=ArtifactProfile.CANONICAL_JSON,
                media_type="application/json", publication_scope_id=logical_id,
                publication_scope_relative_root="products",
                chunks=iter_exact_custody_file_chunks(scratch, size_bytes=size,
                    expected_sha256=digest), maximum_bytes=size,
                maximum_chunk_bytes=min(size, 65536),
                visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
                parent_visibility_ceilings=(), outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                expected_size_bytes=size, expected_physical_sha256=digest))
            products["outputs"][logical_id] = ArtifactManifest(manifest.logical, manifest.materialization)
            products["product_index"].append({"task_id": "exposed." + kind,
                "output_id": logical_id, "logical_artifact_id": logical_id,
                "relative_path": path, "size_bytes": size, "sha256": digest,
                "schema": record.SCHEMA})
        # Operational copies retain the same scientific bytes and identity.
        # They create no additional observations or independent units.

    trace = _trace()
    count = 50001
    times = tuple(D("0.018") * number for number in range(count))
    trace = replace(trace, times_s=times, current_a=(trace.requested_current_a,) * count,
        voltage_v=(D("3.700"),) * count,
        discharge_capacity_ah=tuple(-D("0.000007275") * number for number in range(count)),
        volume_mean_temperature_k=(D("296.150"),) * count)
    retain("battery", trace, 12, {"complete_receiver_rows": count,
        "receiver_columns": 5, "terminal": trace.disposition,
        "decimal_spellings": ["0.018", "3.700", "296.150"]})
    del trace, times
    mechanism, macro = sources()
    retain("rubisco", macro, 2, {"complete_source_count": len(macro.sources),
        "biological_qualification": "NOT_PERFORMED"})
    del mechanism, macro
    config = decode_canonical_bytes((Path(__file__).resolve().parents[1] /
        "programmes/materials/superconductivity/workflows/electron-gas-response/config.json").read_bytes(),
        UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None)
    supply = material.supply(config)
    retain("material", supply, 1, {"complete_response_rows": len(supply.panel.rows),
        "complete_slab_rows": len(supply.panel.slab_profile),
        "scope": supply.scope.to_document(), "disposition": supply.disposition.value})
    del supply, config

    # The selected closed complex array bundle uses the real anonymous port.
    matrix_plane, allocation, saved, arrays, raw, value = stock(selected,
        arrays={"complex": (np.arange(262144, dtype="<f8") +
            1j * np.arange(262144, dtype="<f8")[::-1]).reshape(256, 1024),
            "empty": np.empty((0, 2), dtype="<f8"),
            "mask": np.asarray([True, False, True], dtype="|b1")})
    del arrays, raw
    retain("matrix", saved, 1, {"complete_member_count": len(saved.members),
        "allocation": saved.allocation.to_document(), "fresh_independent_units": 0})
    def matrix_read(selected_plane):
        port = selected_plane.open(value, maximum_bytes=saved.array_artifact.size_bytes)
        totals = {member.name: 0 for member in saved.members}
        try:
            for member, offset, chunk in iter_worker_matrix_array_chunks(port,
                    manifest=saved, allocation=allocation.identity,
                    expected_producers=saved.producers, maximum_chunk_bytes=65536):
                assert offset == totals[member.name]
                totals[member.name] += chunk.size
            # The common array reader uses bounded replay cursors on the same
            # sealed descriptor. It does not consume the one-shot port cursor.
            assert port.bytes_read == 0
        finally:
            port.close()
        assert totals == {member.name: int(np.prod(member.shape)) for member in saved.members}
        return totals
    matrix_totals = matrix_read(matrix_plane)

    # A generated, explicitly exposed CSR source exercises the existing
    # path-free biological parser and full byte custody. No real test is read.
    rows, genes, per_row = 250000, 1024, 8
    h5path = selected / "exposed-csr.h5ad"
    with h5py.File(h5path, "w") as handle:
        matrix = handle.create_group("X")
        matrix.attrs["encoding-type"] = "csr_matrix"
        matrix.attrs["shape"] = (rows, genes)
        matrix.create_dataset("data", data=np.ones(rows * per_row, dtype="<f4"))
        matrix.create_dataset("indices", data=np.tile(np.arange(per_row, dtype="<i4"), rows))
        matrix.create_dataset("indptr", data=np.arange(rows + 1, dtype="<i8") * per_row)
        obs = handle.create_group("obs")
        obs.create_dataset("target_gene", data=np.full(rows, b"EXPOSED", dtype="S7"))
        var = handle.create_group("var")
        var.create_dataset("_index", data=np.asarray([f"gene-{n:04d}".encode() for n in range(genes)]))
    with h5path.open("rb") as stream:
        inspection = inspect_h5ad(stream, inspection_id="inspection.exposed-csr",
            split=VirtualCellSplit.TRAIN, maximum_rows=rows, maximum_genes=genes,
            expected_obs_fields=("target_gene",))
    assert inspection.matrix_encoding is MatrixEncoding.CSR
    # Structural inspection does not independently assess biological values.
    retain("sparse-biological", inspection, 1, {"complete_rows": rows,
        "complete_genes": genes, "complete_nonzero_count": rows * per_row,
        "value_assessment": "EXPOSED_GENERATED_CSR_ONLY_NO_BIOLOGICAL_RESULT"})
    raw_size, raw_hash = bounded_file_sha256(h5path, maximum_bytes=None)
    exported_h5 = selected / "exported-csr.h5ad"
    assert copy_bounded_file(h5path, exported_h5, maximum_bytes=None) == (raw_size, raw_hash)
    with h5py.File(exported_h5, "r") as handle:
        for start in range(0, rows * per_row, 8192):
            stop = min(start + 8192, rows * per_row)
            assert np.all(handle["X/data"][start:stop] == 1)
            np.testing.assert_array_equal(handle["X/indices"][start:stop],
                np.arange(start, stop, dtype="<i4") % per_row)
        for start in range(0, rows + 1, 8192):
            stop = min(start + 8192, rows + 1)
            np.testing.assert_array_equal(handle["X/indptr"][start:stop],
                np.arange(start, stop, dtype="<i8") * per_row)

    def typed_read(selected_plane):
        consumed = 0
        for _, output_id, record in iter_recursive_product_records(plane=selected_plane,
                products=products, output_codecs=codecs):
            expected = products["outputs"][output_id]
            assert record.fingerprint() == expected.logical.content_sha256
            consumed += 1
        assert consumed == len(products["product_index"])
        return consumed
    gc.collect()
    phase_peaks = {"complete_generation_publication_and_value_checks": _rss()}
    complete_typed_reads = typed_read(plane)
    gc.collect()
    phase_peaks["complete_first_typed_read"] = _rss()
    relocated = _plane(selected / "relocated")
    shutil.copytree(base, selected / "relocated", dirs_exist_ok=True)
    recovered_typed_reads = typed_read(relocated)
    gc.collect()
    phase_peaks["complete_relocated_typed_read"] = _rss()
    repeated_typed_reads = typed_read(relocated)
    gc.collect()
    phase_peaks["complete_repeated_relocated_typed_read"] = _rss()
    recovered_matrix = _plane(selected / "relocated-matrix")
    shutil.copytree(matrix_plane.root.contract.canonical_path,
                    selected / "relocated-matrix", dirs_exist_ok=True)
    assert matrix_read(recovered_matrix) == matrix_totals
    recovered_h5 = selected / "recovered-csr.h5ad"
    assert copy_bounded_file(exported_h5, recovered_h5, maximum_bytes=None) == (raw_size, raw_hash)
    with recovered_h5.open("rb") as stream:
        assert inspect_h5ad(stream, inspection_id=inspection.inspection_id,
            split=VirtualCellSplit.TRAIN, maximum_rows=rows, maximum_genes=genes,
            expected_obs_fields=("target_gene",)) == inspection
    peak = _rss()
    report = {"evidence_role": "EXPOSED_TYPED_CUSTODY_CONFORMANCE_ONLY",
        "native_contact_count": 0, "fresh_independent_units": 0,
        "scientific_qualification": "NOT_PERFORMED",
        "baseline_peak_rss_bytes": baseline, "peak_rss_bytes": peak,
        "additional_peak_rss_bytes": peak - baseline,
        "complete_typed_product_count": complete_typed_reads,
        "recovered_typed_product_count": recovered_typed_reads,
        "repeated_recovered_typed_product_count": repeated_typed_reads,
        "total_complete_typed_reads": complete_typed_reads + recovered_typed_reads + repeated_typed_reads,
        "phase_peak_rss_bytes": phase_peaks,
        "replay_incremental_peak_rss_bytes": max(phase_peaks.values()) - phase_peaks["complete_first_typed_read"],
        "complete_serialized_bytes": sum(row["size_bytes"] for row in products["product_index"]),
        "maximum_serialized_member_bytes": max(row["size_bytes"] for row in products["product_index"]),
        "complete_member_index": products["product_index"], "populations": populations,
        "matrix_array_bytes": saved.array_artifact.size_bytes,
        "matrix_expanded_member_bytes": sum(member.size_bytes for member in saved.members),
        "matrix_member_element_counts": matrix_totals,
        "sparse_source_bytes": raw_size, "sparse_source_sha256": raw_hash,
        "typed_memory_scope": "ONE_CANONICAL_RECORD_AT_A_TIME_PLUS_CLOSED_NPZ_AND_CSR_CHUNKS",
        "scientific_joint_assessment_memory": "NOT_ESTABLISHED",
        "probe_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    (selected / "typed-memory-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
