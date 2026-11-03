# SPDX-License-Identifier: MPL-2.0
"""Measured protected public authoring, without acquisition or worker execution.

Select admitted committed source with EL_E3_SCALING_PROJECT_ROOT and external pytest
basetemp. EL_E3_SCALING_CASE selects both (default), alternative or selected64;
a single-case resume does not establish the two-population comparison.
Disclosed original fixtures and qualifications establish software
conformance only. The counters describe measured owners; they are not a claim
that all Python loops, source-closure subprocess I/O or memory are bounded.
"""

from collections import Counter
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
import tracemalloc

from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
from empirical_lawhood.infrastructure import bounded_io
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.infrastructure.source_closure import capture_admitted_target_source, capture_target_closure
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from empirical_lawhood.runtime.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile
from empirical_lawhood.runtime.recursive_compiler import derive_recursive_scientific_selection
from tests import test_matrix_e3_public_programme as public
from tests.test_matrix_e3_protected_public_lowering import write_public_file_selection
from tests.test_matrix_experiment_scaling import embedded_allocations


def _head(root):
    return capture_admitted_target_source(root).implementation_commit


def _file_census(paths):
    rows = {}
    for path in paths:
        raw, stat = path.read_bytes(), path.stat()
        rows[str(path)] = (len(raw), sha256(raw).hexdigest(), stat.st_mtime_ns)
    return rows


@contextmanager
def _measure(monkeypatch, *, original_root):
    """Observe the shared bounded descriptor stream and actual owning callbacks."""
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_original_publications as originals
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_source_records import ProtectedE3NativeSourceManifest

    counters, opened, path_reads = Counter(), {}, Counter()
    open_regular, chunks = bounded_io._open_regular, bounded_io._regular_chunks
    validate, unit_ids, unit = UnitAllocation.__post_init__, UnitAllocation.unit_ids, UnitAllocation.unit
    validate_manifest = ProtectedE3NativeSourceManifest.__post_init__
    authenticate = originals.authenticate_protected_e3_fit_originals
    canonical_original = originals._canonical_original

    def counted_open(path, **kwargs):
        descriptor, stat = open_regular(path, **kwargs)
        opened[descriptor] = Path(path)
        counters["bounded_open_calls"] += 1
        path_reads[str(path)] += 1
        return descriptor, stat

    def counted_chunks(descriptor, before, **kwargs):
        operation = kwargs["operation"]
        path = opened.get(descriptor)
        for chunk in chunks(descriptor, before, **kwargs):
            counters["bounded_" + operation + "_bytes"] += len(chunk)
            counters["bounded_" + operation + "_chunks"] += 1
            if path is not None and path.is_relative_to(original_root):
                counters["selected_plane_bounded_bytes"] += len(chunk)
            yield chunk

    def counted_validation(allocation):
        counters["allocation_validation_calls"] += 1
        counters["allocation_validation_unit_rows_presented"] += len(allocation.units)
        counters["allocation_validation_role_rows_presented"] += len(allocation.roles)
        return validate(allocation)

    def counted_unit_ids(allocation, role=None):
        counters["unit_ids_projection_calls"] += 1
        counters["unit_ids_role_rows_presented"] += len(allocation.roles)
        return unit_ids(allocation, role)

    def counted_unit(allocation, unit_id):
        counters["binary_unit_lookup_calls"] += 1
        return unit(allocation, unit_id)

    def counted_manifest(manifest):
        counters["source_manifest_validation_calls"] += 1
        counters["source_manifest_roots_presented"] += len(manifest.reservation.allocation.roots)
        return validate_manifest(manifest)

    def counted_authentication(*args, **kwargs):
        counters["global_original_fit_authentication_calls"] += 1
        return authenticate(*args, **kwargs)

    def counted_original(plane, publication, kind):
        counters["original_metadata_decode_calls"] += 1
        counters["original_metadata_decode_bytes"] += publication.materialization.size_bytes
        return canonical_original(plane, publication, kind)

    with monkeypatch.context() as observed:
        observed.setattr(bounded_io, "_open_regular", counted_open)
        observed.setattr(bounded_io, "_regular_chunks", counted_chunks)
        observed.setattr(UnitAllocation, "__post_init__", counted_validation)
        observed.setattr(UnitAllocation, "unit_ids", counted_unit_ids)
        observed.setattr(UnitAllocation, "unit", counted_unit)
        observed.setattr(ProtectedE3NativeSourceManifest, "__post_init__", counted_manifest)
        observed.setattr(originals, "authenticate_protected_e3_fit_originals", counted_authentication)
        observed.setattr(originals, "_canonical_original", counted_original)
        tracemalloc.start()
        started = perf_counter()
        result = {}
        try:
            yield result
        except BaseException as error:
            result["outcome"] = "FAILED"
            result["error_type"] = type(error).__name__
            result["error_message"] = str(error)
            raise
        else:
            result["outcome"] = "SUCCEEDED"
        finally:
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            result.update({"elapsed_seconds": perf_counter() - started,
                "python_traced_peak_bytes": peak, "counters": dict(sorted(counters.items())),
                "distinct_bounded_paths": len(path_reads),
                "maximum_bounded_opens_for_one_path": max(path_reads.values(), default=0),
                "most_repeated_bounded_paths": [{"path": path, "opens": count}
                    for path, count in path_reads.most_common(10)]})


def test_protected_public_authoring_measures_complete_populations_and_repeated_original_binding(tmp_path, monkeypatch):
    requested = os.environ.get("EL_E3_SCALING_CASE", "both")
    if requested not in ("both", "alternative", "selected64"):
        raise ValueError("EL_E3_SCALING_CASE must be both, alternative or selected64")
    designs = ("alternative", "selected64") if requested == "both" else (requested,)
    root = Path(os.environ.get("EL_E3_SCALING_PROJECT_ROOT", Path(__file__).resolve().parents[1]))
    assert public.ROOT.resolve() == root.resolve(), "select fixture assets and executing package from the same frozen source"
    selected_source = capture_admitted_target_source(root)
    selected_head = selected_source.implementation_commit
    report_path = tmp_path / "protected-e3-authoring-scaling.json"
    report = {
        "scope": "Public FILE input loading, public prepare, public author, and two complete cold executable handoff loads for the explicitly selected protected E3 populations; no workers or native acquisition.",
        "standing": "EXPOSED_CONFORMANCE_NONPROMOTABLE", "qualification": "NOT_ESTABLISHED",
        "fixture": "Existing public worker control's valid instrument and actual selected-source producing provenance, bound before publication",
        "wider_a04_closure": False, "project_root": str(root), "source_commit": selected_head,
        "source_observation_before": selected_source.to_mapping(),
        "requested_cases": list(designs), "completed_cases": [],
        "all_requested_cases_complete": False, "two_population_measurement_complete": False,
        "measurement_limits": [
            "Bounded byte counts instrument the shared descriptor/chunk owner, including its reads and streaming hashes; subprocess/source-closure I/O and other direct file I/O are excluded.",
            "Allocation and manifest rows presented count callback inputs, not every internal Python loop or canonical serialization traversal.",
            "Traced peaks count Python allocations in each stage, not complete RSS, native allocations, fixture construction or source-closure setup.",
            "Elapsed times include tracing/instrumentation and concurrent host activity; they are not isolated production benchmarks.",
            "Two cold loads intentionally repeat source authentication as separate verified operations; there is no promise of cross-operation caching.",
            "Pre-author serialized sizes and the pure scientific projection derivation are collected outside the measured stages and retained even when authoring refuses.",
        ], "cases": [],
    }

    def retain_measurements():
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    @contextmanager
    def measured_stage(row, label, plane):
        try:
            with _measure(monkeypatch, original_root=Path(plane.root.contract.canonical_path)) as measurement:
                row["stages"][label] = measurement
                yield
        finally:
            retain_measurements()

    def forbidden_worker(*_args, **_kwargs):
        raise AssertionError("metadata scaling entered an actual worker")

    for name in ("execute", "execute_deadline_free", "execute_prepared", "execute_parallel"):
        if hasattr(LocalProcessExecutor, name):
            monkeypatch.setattr(LocalProcessExecutor, name, forbidden_worker)

    for design in designs:
        name = "selected64" if design == "selected64" else "alternative12-20-8"
        case = public._selected_case(tmp_path / name / "originals", design)
        source_path = write_public_file_selection(case)
        original_paths = tuple(path for path in Path(case.plane.root.contract.canonical_path).rglob("*") if path.is_file())
        original_files = _file_census(original_paths)
        scientific_records = (case.specification, case.allocation, case.manifest, case.inputs.training_allocation,
            case.originals, case.response_selection, *case.protocols, *case.numerical_profiles)
        original_records = tuple(record.canonical_bytes() for record in scientific_records)
        profile = OperatorStorageProfile("software.e3.scaling-storage", "external-filesystem", "1.0.0",
            str(tmp_path / name / "originals"), str(tmp_path / name), "selected", "scientific-scratch",
            OperatorStorageAccessMode.READ_WRITE, None, None, (), "strict-mount-contained-no-symlink",
            1, (), 1, False)
        programme = ExperimentProgrammeService(root, case.plane, profile)
        closure = capture_target_closure(root, case.selection.selection_id + ".prospective.source-closure").closure
        execution = ExecutionSelection(workers=1, environment_id="main-locked",
            source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", closure),
            output_root=case.plane.root.contract.canonical_path)
        row = {"selection": name, "design": design, "metadata_complete": False,
            "stages": {}, "original_file_count": len(original_files),
            "original_file_bytes": sum(value[0] for value in original_files.values())}
        report["cases"].append(row)
        retain_measurements()
        with measured_stage(row, "load_public_file_inputs", case.plane):
            resolved = load_experiment_inputs(case.specification, source_path)
        with measured_stage(row, "prepare", case.plane):
            preparation = programme.prepare(case.specification, scientific_inputs=resolved.scientific_inputs,
                method_inputs=resolved.method_inputs, execution=execution, protocol_bytes=case.candidate_bytes)
        # Authoring binds the derived resources to its actual public candidate;
        # the pure preparation intentionally retains precisely this dependency.
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import RESOURCE_BINDING_DEPENDENCY
        row["pre_author_dependency_codes"] = [value.code for value in preparation.dependencies]
        assert set(row["pre_author_dependency_codes"]) == {RESOURCE_BINDING_DEPENDENCY}
        assert preparation.draft is not None
        allocation_inputs = tuple(record for _, record in preparation.input_records if type(record) is UnitAllocation)
        selected_rosters = tuple(record for record in allocation_inputs if record.identity == preparation.allocation.identity)
        assert len({record.identity for record in selected_rosters}) == 1
        assert len({id(record) for record in selected_rosters}) == 1
        assert sum(record.identity == case.inputs.training_allocation.identity for record in allocation_inputs) == 1
        row.update({"unique_selected_allocation_roster_identities": 1,
            "distinct_selected_allocation_objects_in_inputs": 1,
            "selected_allocation_external_bindings": len(selected_rosters),
            "allocation_external_inputs": [{"input_id": key, "allocation_id": record.allocation_id,
                "sha256": record.fingerprint(), "bytes": len(record.canonical_bytes())}
                for key, record in preparation.input_records if type(record) is UnitAllocation]})
        retain_measurements()
        config_documents = tuple(json.loads(operation.config_payload) for operation in preparation.draft.operations)
        assert embedded_allocations(preparation.draft.to_document()) == 0
        assert all(embedded_allocations(document) == 0 for document in config_documents)
        config_sizes = tuple(len(operation.config_payload.encode()) for operation in preparation.draft.operations)
        projection = derive_recursive_scientific_selection(preparation.draft)
        draft_payload = preparation.draft.canonical_bytes()
        projection_payload = projection.canonical_bytes()
        query_count = sum(len(preparation.allocation.unit_ids(role)) for role in ("calibration", "evaluation"))
        expected_operation_count = 10 * query_count + 6
        row.update({"role_counts": dict(preparation.census.role_counts),
            "allocation_role_counts": dict(preparation.allocation.role_counts), "whole_unit_count": len(preparation.allocation.units),
            "query_count": query_count, "expected_operation_count": expected_operation_count,
            "operation_count": len(preparation.draft.operations), "external_record_count": len(preparation.input_records),
            "external_file_count": len(preparation.input_files),
            "original_training_allocation_rosters": 1, "embedded_allocation_rosters_in_draft_and_configs": 0,
            "specification_bytes": len(preparation.specification_record.canonical_bytes()),
            "allocation_bytes": len(preparation.allocation.canonical_bytes()), "draft_bytes": len(draft_payload),
            "scientific_projection_bytes": len(projection_payload),
            "scientific_projection_operation_count": len(projection.operations),
            "scientific_projection_link_count": len(projection.links),
            "input_record_bytes": sum(len(record.canonical_bytes()) for _, record in preparation.input_records),
            "design_record_bytes": sum(len(record.canonical_bytes()) for _, record in preparation.design_records),
            "config_count": len(config_sizes), "config_bytes": sum(config_sizes), "maximum_config_bytes": max(config_sizes),
            "config_size_histogram": dict(sorted(Counter(config_sizes).items())),
            "scientific_identities": {"specification": preparation.specification_record.fingerprint(),
                "allocation": preparation.allocation.fingerprint(), "draft": sha256(draft_payload).hexdigest(),
                "scientific_projection": sha256(projection_payload).hexdigest(), "original_manifest": case.manifest.fingerprint()}})
        retain_measurements()
        assert row["operation_count"] == row["scientific_projection_operation_count"] == expected_operation_count
        del draft_payload, projection_payload, projection, config_documents
        directory = Path(case.plane.root.contract.canonical_path) / "public-e3-programme"
        with measured_stage(row, "author", case.plane):
            authored = programme.author(preparation=preparation, output_dir=directory)
        assert authored["scientific_authority"] == "NONE" and authored["native_contact"] == "none"
        retained_identities = []
        for repetition in (1, 2):
            assert _head(root) == selected_head
            label = "cold_load_" + str(repetition)
            with measured_stage(row, label, case.plane):
                selected = load_prepared_prospective_experiment(directory=directory, project_root=root,
                    storage_profile=profile, artifact_writer=case.plane)
            measurement = row["stages"][label]
            assert selected.specification.canonical_bytes() == original_records[0]
            assert selected.allocation.canonical_bytes() == original_records[1]
            assert selected.handoff.compilation.draft.operations == preparation.draft.operations
            retained_identities.append((selected.association.identity, selected.candidate.fingerprint(), selected.instance.fingerprint()))
            assert measurement["counters"]["global_original_fit_authentication_calls"] >= 1
            assert measurement["counters"]["original_metadata_decode_calls"] >= 3
        assert retained_identities[0] == retained_identities[1]
        assert _head(root) == selected_head
        assert _file_census(original_paths) == original_files
        assert tuple(record.canonical_bytes() for record in scientific_records) == original_records
        published = tuple(path for path in directory.rglob("*") if path.is_file())
        row.update({"authored_file_count": len(published), "authored_file_bytes": sum(path.stat().st_size for path in published),
            "original_bytes_and_mtimes_unchanged": True, "workers_started": 0, "native_acquisitions": 0,
            "metadata_complete": True})
        report["completed_cases"].append(design)
        retain_measurements()
    assert len(report["cases"]) == len(designs)
    assert all(row["operation_count"] == row["expected_operation_count"] for row in report["cases"])
    assert all(row["unique_selected_allocation_roster_identities"] == 1 for row in report["cases"])
    final_source = capture_admitted_target_source(root)
    report["source_commit_after"] = final_source.implementation_commit
    report["source_observation_after"] = final_source.to_mapping()
    assert report["source_commit_after"] == selected_head
    assert report["completed_cases"] == list(designs)
    report["all_requested_cases_complete"] = True
    report["two_population_measurement_complete"] = set(designs) == {"alternative", "selected64"}
    retain_measurements()
