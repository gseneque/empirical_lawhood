# SPDX-License-Identifier: MPL-2.0
"""Measure the exposed RC public lifecycle with explicit source and custody."""

from __future__ import annotations

import argparse
import cProfile
from dataclasses import replace
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import pstats
import resource
import statistics
import subprocess
import sys
import threading
import time
import traceback


PHASES = ("import", "source_capture", "compile", "author", "run_compact", "read_compact",
          "read_documents", "completed_resume", "export")
THREADS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")


def save(path, value):
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def rss_bytes():
    return int(Path("/proc/self/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")


def process_io():
    return {key: int(value) for key, value in
            (line.split(":") for line in Path("/proc/self/io").read_text().splitlines())}


def measure(name, operation, *, output, profiled=False):
    """Keep stage sampling distinct from lifetime HWM and unmeasured heap."""
    stop = threading.Event()
    sampled = {"peak_bytes": rss_bytes(), "samples": 0, "monitor_cpu_seconds": 0.0}

    def monitor():
        started = time.thread_time()
        while not stop.wait(0.02):
            sampled["peak_bytes"] = max(sampled["peak_bytes"], rss_bytes())
            sampled["samples"] += 1
        sampled["monitor_cpu_seconds"] = time.thread_time() - started

    thread = threading.Thread(target=monitor, daemon=True)
    children_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    io_before = process_io()
    rss_before = rss_bytes()
    profile = cProfile.Profile() if profiled else None
    row = {"stage": name, "profiled": profiled, "status": "RUNNING"}
    wall, cpu = time.perf_counter(), time.process_time()
    thread.start()
    try:
        if profile:
            profile.enable()
        result = operation()
        row["status"] = "PASSED"
        return result, row
    except BaseException as error:
        row.update(status="FAILED", error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        if profile:
            profile.disable()
        row.update(wall_seconds=time.perf_counter() - wall, controller_cpu_seconds=time.process_time() - cpu)
        stop.set()
        thread.join()
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        io_after, rss_after = process_io(), rss_bytes()
        row.update(child_cpu_seconds=children.ru_utime + children.ru_stime - children_before.ru_utime - children_before.ru_stime,
            controller_lifetime_hwm_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            terminated_child_hwm_bytes=children.ru_maxrss * 1024,
            sampled_controller_peak_bytes=max(sampled["peak_bytes"], rss_before, rss_after),
            controller_rss_before_bytes=rss_before, controller_rss_after_bytes=rss_after,
            retained_python_heap_bytes=None, child_live_rss_bytes=None,
            rss_sample_interval_seconds=0.02, rss_samples=sampled["samples"],
            monitor_cpu_seconds=sampled["monitor_cpu_seconds"],
            process_io_delta={key: io_after[key] - io_before[key] for key in io_before})
        if profile:
            profile.dump_stats(output / f"{name}.pstats")
            with (output / f"{name}.profile.txt").open("w") as stream:
                stats = pstats.Stats(profile, stream=stream)
                stats.sort_stats("cumulative").print_stats(65)
                stats.sort_stats("tottime").print_stats(40)
            row["call_counts"] = [{"file": key[0], "line": key[1], "function": key[2],
                "primitive_calls": value[0], "total_calls": value[1], "self_seconds": value[2],
                "cumulative_seconds": value[3]} for key, value in sorted(pstats.Stats(profile).stats.items())
                if key[0].endswith(("artifacts.py", "recursive_input_publication.py", "source_origin.py",
                    "source_closure.py", "run_source_admission.py", "capabilities.py", "providers.py",
                    "recursive_operation_index.py", "scientific_binding.py"))]
        save(output / f"{name}.measurement.json", row)


def import_rc():
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave
    from empirical_lawhood.domains.circuits.rc_prerequisite_chain.contracts import RCPrerequisiteChainConfig
    from empirical_lawhood.domains.circuits.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    return author_recursive_wave, RCPrerequisiteChainConfig, rc_recursive_draft, decode_canonical_bytes


def selected_config(repo, imported):
    _, kind, _, decode = imported
    path = repo / "programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json"
    return decode(path.read_bytes(), kind, maximum_bytes=8 * 1024**2)


def make_plane(args):
    from empirical_lawhood.api.codecs import load_registered_authoring
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
    from empirical_lawhood.execution.operator_profile import OperatorStorageProfile, resolve_external_root_contract

    profile = load_registered_authoring(args.operator_profile, root_schemas={OperatorStorageProfile.SCHEMA: OperatorStorageProfile})
    base = resolve_external_root_contract(profile, repo_root=args.repo, home_root=Path.home())
    GuardedExternalRoot(base).verify(for_write=True)
    if args.artifact_dir == Path(base.canonical_path) or not args.artifact_dir.is_relative_to(base.canonical_path):
        raise ValueError("select a separate benchmark custody directory beneath the operator artifact root")
    # Narrow the physical destination while retaining mount, volume and capacity
    # policy. Separate repeated software fixtures cannot reuse one run directory.
    contract = replace(base, canonical_path=str(args.artifact_dir),
        storage_root_id="benchmark.rc." + sha256(str(args.artifact_dir).encode()).hexdigest()[:24])
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    plane = ExternalArtifactPlane(GuardedExternalRoot(contract), integration_artifact_profile_validators(),
                                 maximum_parallel_verifications=profile.maximum_parallel_tasks)
    plane.root.verify(for_write=True)
    return plane


def child(args):
    if "pytest" in sys.modules:
        raise RuntimeError("ordinary software measurements must not import pytest")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    summary = {"phase": args.phase, "source_commit": args.source_commit, "status": "RUNNING",
        "python": sys.version, "affinity": sorted(os.sched_getaffinity(0)),
        "numerical_threads": {name: os.environ.get(name) for name in THREADS},
        "versions": {name: importlib.metadata.version(name) for name in
            ("numpy", "scipy", "python-flint", "sqlalchemy", "hatchling")},
        "filesystem_cache": "not flushed; repeated observations use the same filesystem",
        "bytecode_prefix": sys.pycache_prefix,
        "measurement_limits": "20ms controller RSS samples; lifetime HWM; child CPU includes waited children; heap and live child RSS unmeasured; profiling is separate"}
    try:
        if args.phase == "import":
            _, metrics = measure("import", import_rc, output=args.output_dir, profiled=args.profile)
            summary["measurement"] = metrics
        elif args.phase in ("source_capture", "compile", "author"):
            imported, _ = measure("setup_import", import_rc, output=args.output_dir)
            if args.phase == "source_capture":
                from empirical_lawhood.storage.run_source_admission import _capture_source
                captured, metrics = measure("source_capture", lambda: _capture_source(args.repo),
                    output=args.output_dir, profiled=args.profile)
                assert captured.implementation_commit == args.source_commit
                summary.update(source_archive_sha256=captured.implementation_sha256,
                    source_tree_sha256=captured.source_tree_sha256, tracked_members=len(captured.tracked_files),
                    tracked_body_bytes=sum(row.size_bytes for row in captured.tracked_files),
                    selected_members=len(captured.final_source_admission.selected_paths), measurement=metrics)
            else:
                config = selected_config(args.repo, imported)
                if args.phase == "compile":
                    from empirical_lawhood.domains.circuits.rc_prerequisite_chain import recursive_translation as owner
                    from empirical_lawhood.api.recursive_operations import operation_catalog_for_draft
                    from empirical_lawhood.execution.recursive_compiler import compile_recursive_wave
                    original, calls, rows = owner.rc_recursive_draft, [], []
                    def counted(*values, **options):
                        draft = original(*values, **options)
                        calls.append(len(draft.operations))
                        return draft
                    owner.rc_recursive_draft = counted
                    try:
                        for size in (1, 2, 4, 8, 11):
                            draft = original(config, unit_ids=tuple(unit.unit_id for unit in config.units[:size]), include_summary=False)
                            registrations, registry, codecs = operation_catalog_for_draft(draft)
                            calls.clear()
                            result, metrics = measure(f"compile_{size}", lambda: compile_recursive_wave(draft=draft,
                                registrations=registrations, registry=registry, implementation_commit=args.source_commit,
                                run_plan_id="benchmark.rc.compiler", output_codecs=codecs), output=args.output_dir, profiled=args.profile)
                            rows.append({"units": size, "tasks": len(result.execution_plan.tasks),
                                "installed_capabilities": len(registry.capabilities), "selected_capabilities": len(registrations),
                                "reference_draft_reconstructions": len(calls), "reference_operation_objects": sum(calls),
                                "execution_plan_sha256": result.execution_plan.fingerprint(), "measurement": metrics})
                    finally:
                        owner.rc_recursive_draft = original
                    summary["compilations"] = rows
                else:
                    draft, _ = measure("draft", lambda: imported[2](config, unit_ids=(config.units[6].unit_id,), include_summary=False),
                                       output=args.output_dir)
                    assert len(draft.operations) == 9
                    plane = make_plane(args)
                    result, metrics = measure("author", lambda: imported[0](draft=draft, project_root=args.repo,
                        artifact_writer=plane, output_dir=args.artifact_dir / "authored"), output=args.output_dir, profiled=args.profile)
                    summary.update(result=result, measurement=metrics, draft_sha256=draft.fingerprint())
                    summary["input"] = {"schema": config.SCHEMA, "sha256": config.fingerprint(),
                                        "canonical_bytes": len(config.canonical_bytes())}
        else:
            if args.authored_dir is None:
                raise ValueError("retained phases require the actual authoring path returned by author")
            plane = make_plane(args)
            if args.phase == "export":
                from empirical_lawhood.api.recursive_contributions import export_recursive_contribution
                def operation():
                    try:
                        return export_recursive_contribution(directory=args.authored_dir,
                            output_dir=args.artifact_dir / "exported", project_root=args.repo, artifact_writer=plane)
                    except ValueError as error:
                        if str(error) != "selected wave has no unique registered contribution description":
                            raise
                        if (args.artifact_dir / "exported").exists():
                            raise AssertionError("unsupported RC contribution wrote an export") from error
                        return {"status": "UNSUPPORTED", "reason": str(error), "native_contact": "none",
                                "new_native_contact_count": 0}
            else:
                from empirical_lawhood.api.recursive_execution import run_recursive_wave, read_recursive_wave
                if args.phase in ("run_compact", "completed_resume"):
                    operation = lambda: run_recursive_wave(directory=args.authored_dir, project_root=args.repo,
                        artifact_writer=plane, terminal_product_format="compact")
                else:
                    operation = lambda: read_recursive_wave(directory=args.authored_dir, artifact_writer=plane,
                        terminal_product_format="documents" if args.phase == "read_documents" else "compact")
            result, metrics = measure(args.phase, operation, output=args.output_dir, profiled=args.profile)
            save(args.output_dir / "report.json", result)
            if args.phase == "export":
                assert result["status"] in ("EXPORTED", "UNSUPPORTED")
            else:
                assert result["status"] == "SUCCEEDED", result
                assert result["new_native_contact_count"] == (2 if args.phase == "run_compact" else 0), result
            summary.update(result={key: result.get(key) for key in
                ("status", "reason", "task_count", "native_contact", "new_native_contact_count", "contribution_dir", "custody_member_count")}, measurement=metrics)
        assert "pytest" not in sys.modules
        summary["loaded_el_modules"] = sorted(name for name in sys.modules if name.startswith("empirical_lawhood"))
        if args.artifact_dir.is_dir():
            paths = [path for path in args.artifact_dir.rglob("*") if path.is_file()]
            summary["retained"] = {"files": len(paths), "bytes": sum(path.stat().st_size for path in paths)}
        summary["status"] = "PASSED"
    except BaseException as error:
        summary.update(status="FAILED", error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        save(args.output_dir / "observation.json", summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--operator-profile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--profile", action="store_true", help="Separate profiled attribution; do not compare its latencies with ordinary measurements.")
    parser.add_argument("--phase", choices=PHASES, help=argparse.SUPPRESS)
    parser.add_argument("--source-commit", help=argparse.SUPPRESS)
    parser.add_argument("--authored-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    for name in ("repo", "operator_profile", "output_dir", "artifact_dir"):
        path = getattr(args, name)
        if not path.is_absolute() or ".." in path.parts or any(item.is_symlink() for item in (path, *path.parents)):
            parser.error(f"{name} requires an absolute path without traversal or symlinks")
    if args.phase:
        child(args)
        return
    if args.repeats < 1:
        parser.error("repeats must be positive")
    selected_profile = json.loads(args.operator_profile.read_text())["value"]
    for path in (args.output_dir, args.artifact_dir):
        if path.exists() or not path.is_relative_to(selected_profile["external_root_locator"]):
            parser.error("select new separate output and artifact directories beneath the operator external root")
    if args.output_dir.is_relative_to(args.artifact_dir) or args.artifact_dir.is_relative_to(args.output_dir):
        parser.error("measurement output and artifact custody must be disjoint")
    if not os.path.ismount(selected_profile["required_mount_path"]):
        parser.error("the selected external mount is unavailable")
    args.output_dir.mkdir(parents=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.repo, text=True).strip()
    affinity = sorted(os.sched_getaffinity(0))[:selected_profile["maximum_parallel_tasks"]]
    os.sched_setaffinity(0, affinity)
    filesystem = subprocess.check_output(["findmnt", "--json", "--target", str(args.output_dir),
        "--output", "TARGET,SOURCE,FSTYPE,OPTIONS"], text=True)
    plan = {"schema": "empirical-lawhood/development/recursive-benchmark", "version": "1.0.0",
        "source_commit": commit, "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "lock_sha256": sha256((args.repo / "uv.lock").read_bytes()).hexdigest(),
        "operator_profile": str(args.operator_profile), "operator_profile_sha256": sha256(args.operator_profile.read_bytes()).hexdigest(),
        "artifact_dir": str(args.artifact_dir), "repeats": args.repeats, "profiled": args.profile,
        "filesystem": json.loads(filesystem), "affinity": affinity,
        "fixture": "exposed config.units[6]; nine tasks; each repetition has separate custody",
        "comparison": "same script/fixture/profile/affinity/thread settings/filesystem; fresh process per phase; fresh bytecode prefix then populated prefix per repetition; no filesystem cache flush; compare medians and ranges only within the same profiling setting",
        "evidence_ceiling": "software observations only; no scientific qualification or molecular savings", "runs": [], "status": "RUNNING"}
    save(args.output_dir / "benchmark.json", plan)
    try:
        for repeat in range(args.repeats):
            artifact_dir = args.artifact_dir / f"repeat-{repeat:02}"
            authored = None
            phases = (("cold_import", "import"), ("warm_import", "import"), *((name, name) for name in PHASES[1:]))
            for label, phase in phases:
                output = args.output_dir / f"repeat-{repeat:02}-{label}"
                environment = dict(os.environ, **{name: "1" for name in THREADS})
                environment.update(PYTHONHASHSEED="0", PYTHONPYCACHEPREFIX=str(args.output_dir / f"bytecode-{repeat:02}"))
                command = [sys.executable, str(Path(__file__).resolve()), "--repo", str(args.repo),
                    "--operator-profile", str(args.operator_profile), "--output-dir", str(output),
                    "--artifact-dir", str(artifact_dir), "--phase", phase, "--source-commit", commit]
                if args.profile:
                    command.append("--profile")
                if authored:
                    command.extend(("--authored-dir", authored))
                log = args.output_dir / f"repeat-{repeat:02}-{label}.log"
                with log.open("wb") as stream:
                    result = subprocess.run(command, env=environment, stdout=stream, stderr=subprocess.STDOUT)
                row = {"repeat": repeat, "phase": label, "command": command, "returncode": result.returncode,
                    "log": log.name, "log_sha256": sha256(log.read_bytes()).hexdigest()}
                observation = output / "observation.json"
                if observation.is_file():
                    row["observation"] = json.loads(observation.read_text())
                    row["observation_sha256"] = sha256(observation.read_bytes()).hexdigest()
                plan["runs"].append(row)
                save(args.output_dir / "benchmark.json", plan)
                print(json.dumps({"repeat": repeat, "phase": label, "returncode": result.returncode,
                    "wall_seconds": row.get("observation", {}).get("measurement", {}).get("wall_seconds")}), flush=True)
                if result.returncode:
                    raise RuntimeError(f"{label} failed; retained log: {log}")
                if phase == "author":
                    authored = row["observation"]["result"]["authoring_dir"]
        if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.repo, text=True).strip() != commit:
            raise RuntimeError("source commit changed during the benchmark")
        plan["latency_seconds"] = {}
        for label, _ in phases:
            values = [row["observation"]["measurement"]["wall_seconds"] for row in plan["runs"]
                      if row["phase"] == label and "measurement" in row["observation"]]
            if values:
                plan["latency_seconds"][label] = {"n": len(values), "median": statistics.median(values), "min": min(values), "max": max(values)}
        plan["status"] = "PASSED"
    except BaseException as error:
        plan.update(status="FAILED", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        save(args.output_dir / "benchmark.json", plan)


if __name__ == "__main__":
    main()
