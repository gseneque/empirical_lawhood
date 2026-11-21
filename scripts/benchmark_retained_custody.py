# SPDX-License-Identifier: MPL-2.0
"""Measure retained custody work on disclosed controls, without scientific acquisition.

Run the same script/interpreter against two source trees using PYTHONPATH, with
separate new output directories. Timing, Python heap profiling and deterministic
work counts are separate passes. No remote or numerical-utilization claim follows.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import statistics
import sys
import time
import tracemalloc
from typing import ClassVar

from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.artifact_validation import ArtifactProfileValidatorRegistry
from empirical_lawhood.storage.artifact_verification import artifact_verification_operation
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.storage.bounded_io import bounded_file_sha256
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest, ExternalRootContract


@dataclass(frozen=True, slots=True)
class BenchmarkPayload(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/retained-custody-benchmark"
    member: int
    rows: tuple[str, ...]


def measure(operation):
    wall, cpu = time.perf_counter(), time.process_time()
    result = operation()
    return result, {
        "wall_seconds": time.perf_counter() - wall,
        "controller_cpu_seconds": time.process_time() - cpu,
        "controller_lifetime_hwm_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
    }


def benchmark(root: Path, members: int, payload_bytes: int, repeats: int):
    root.mkdir()
    mount = next(parent for parent in root.parents if parent.is_mount())
    plane = ExternalArtifactPlane(GuardedExternalRoot(ExternalRootContract(
        "benchmark.retained-custody", "Disclosed software benchmark; no scientific authority",
        str(root), str(mount), "empirical-lawhood/testing/retained-custody-benchmark", 1)),
        maximum_parallel_verifications=1)
    rows = tuple("x" * 1024 for _ in range(max(1, payload_bytes // 1024)))
    requests, preparation = measure(lambda: tuple(ArtifactWriteRequest(
        f"exposed.member.{index}", f"outputs/member-{index}.json", BenchmarkPayload.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", "exposed.benchmark", "outputs",
        BenchmarkPayload(index, rows).canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE) for index in range(members)))
    published, publication = measure(lambda: plane.write_batch(requests))
    manifests, metadata = measure(lambda: tuple(
        plane.read_manifest(row.materialization.relative_path) for row in published))

    def read_three_consumers():
        with artifact_verification_operation():
            for _ in range(3):
                with plane.read_context() as reading:
                    reading.verify_manifests(manifests)
                    reading.require_verification_snapshot()

    # The complete publication remains on disk and is authenticated on every
    # invocation. Only the OS page cache is warm; no invocation cache survives.
    read_three_consumers()
    observations = [measure(read_three_consumers)[1] for _ in range(repeats)]
    tracemalloc.start()
    read_three_consumers()
    heap_current, heap_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    counts = Counter()
    deep = ArtifactProfileValidatorRegistry.validate_file.__code__
    hash_code = bounded_file_sha256.__code__
    checkpoint = ExternalArtifactPlane._require_verification_snapshot_paths.__code__

    def profile(frame, event, _arg):
        if event == "call" and frame.f_code is deep:
            counts["deep_validations"] += 1
        if (event == "call" and frame.f_code is hash_code
                and frame.f_back.f_code is checkpoint):
            counts["final_or_checkpoint_hashes"] += 1
            counts["final_or_checkpoint_hash_bytes"] += frame.f_locals["maximum_bytes"]

    previous = sys.getprofile()
    try:
        sys.setprofile(profile)
        read_three_consumers()
    finally:
        sys.setprofile(previous)
    paths = [path for path in root.rglob("*") if path.is_file()]
    return {
        "members": members, "payload_bytes_per_member_requested": payload_bytes,
        "consumers_per_invocation": 3, "timed_repeats": repeats,
        "preparation": preparation, "publication": publication, "metadata": metadata,
        "verification_observations": observations,
        "verification_median_wall_seconds": statistics.median(row["wall_seconds"] for row in observations),
        "verification_median_controller_cpu_seconds": statistics.median(row["controller_cpu_seconds"] for row in observations),
        "heap_profile_separate_pass": {"retained_bytes": heap_current, "peak_bytes": heap_peak},
        "work_counts_separate_pass": dict(counts),
        "retained_files": len(paths), "retained_bytes": sum(path.stat().st_size for path in paths),
        "payload_census_sha256": sha256(b"".join(request.payload for request in requests)).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "empirical-lawhood/software/retained-custody-benchmark-v1",
        "python": sys.version, "affinity": sorted(os.sched_getaffinity(0)),
        "scientific_qualification": "NOT_PERFORMED",
        "scope": "Same retained small and large synthetic publications through three consumers; no native acquisition",
        "limits": "Concurrent-host timings; warm filesystem cache; heap excludes native allocations and child processes; no remote transfer or numerical utilization measured",
        "workloads": [],
    }
    for name, members, size in (("small", 4, 1024), ("census", 128, 1024), ("large", 2, 4 * 2**20)):
        report["workloads"].append({"name": name, **benchmark(output / name, members, size, args.repeats)})
    source = []
    for name, module in sorted(sys.modules.items()):
        path = getattr(module, "__file__", None)
        if name.startswith("empirical_lawhood.") and path and Path(path).suffix == ".py":
            source.append({"module": name, "sha256": sha256(Path(path).read_bytes()).hexdigest()})
    report["loaded_source"] = source
    report["status"] = "PASSED"
    (output / "measurements.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "PASSED", "workloads": len(report["workloads"]), "output": str(output / "measurements.json")}))


if __name__ == "__main__":
    main()
