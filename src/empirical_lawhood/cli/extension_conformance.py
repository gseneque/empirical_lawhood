# SPDX-License-Identifier: MPL-2.0
"""Explicit bounded conformance for a trusted local Python fixture.

Run with ``python -m empirical_lawhood.cli.extension_conformance``. This
developer operation is separate from effect-free installed discovery.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
from time import monotonic
from types import ModuleType

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.execution.local.bounded_process import run_bounded_command
from empirical_lawhood.storage.numerical_provenance import immutable_json
from empirical_lawhood.science.records.serialization import canonical_json_bytes


MAX_FIXTURE_BYTES = 256 * 1024


def _worker(project_root, filename):
    # Bounds apply to disclosed software checks only, never a native campaign.
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
    # Python's lazy processor field can invoke uname during extension imports.
    # Observe it before trusted fixture entry, under the outer process bounds.
    # Cases retain the full subprocess guard; no synthetic host value is used.
    host = platform.uname()._asdict()
    raw = sys.stdin.buffer.read(MAX_FIXTURE_BYTES + 1)
    if len(raw) > MAX_FIXTURE_BYTES:
        raise ValueError("selected conformance fixture exceeds 256 KiB")
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.extension_conformance import run_extension_conformance
    from empirical_lawhood.storage.extension_conformance import forbid_conformance_contact
    binding = implementation_binding(project_root)
    source = dict(project_root=str(project_root), implementation=binding.to_document(),
                  fixture_path=filename, fixture_sha256=sha256(raw).hexdigest(), conformance_host=host)
    module = ModuleType("_selected_extension_conformance_" + sha256(raw).hexdigest())
    module.__file__ = filename
    sys.modules[module.__name__] = module
    report = dict(status="FAILED", source=source, profile=None, checks=[], unmet_prerequisites=[],
        scientific_authority="NONE", qualification="NOT_ESTABLISHED", full_installed_lifecycle=False)
    with redirect_stdout(sys.stderr), forbid_conformance_contact() as load_contacts:
        try:
            exec(compile(raw, filename, "exec"), module.__dict__)
            selection = getattr(module, "CONFORMANCE_SELECTION", None)
            if selection is None:
                raise ValueError("fixture must define CONFORMANCE_SELECTION")
            report = run_extension_conformance(selection, source=source)
        except Exception as error:
            report["failure"] = dict(type=type(error).__name__, message=str(error)[:2000])
    if load_contacts:
        report.update(status="FAILED_CONTACT_ATTEMPT", load_contact_attempts=list(load_contacts))
    report["load_storage_diagnostics"] = load_contacts.storage_diagnostics
    if implementation_binding(project_root) != binding:
        raise ValueError("selected implementation changed during conformance")
    sys.stdout.buffer.write(canonical_json_bytes(immutable_json(report)))
    return 0 if report["status"] == "PASSED_SELECTED_CHECKS" else 1


def check_fixture(*, fixture: Path, project_root: Path, output_dir: Path, timeout_seconds=60) -> dict:
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 120:
        raise ValueError("conformance duration must be between 1 and 120 seconds")
    fixture, project_root = fixture.resolve(strict=True), project_root.resolve(strict=True)
    raw = read_bounded_bytes(fixture, maximum_bytes=MAX_FIXTURE_BYTES)
    output_dir = output_dir.resolve()
    if output_dir.is_relative_to(project_root):
        raise ValueError("select a new external conformance output directory")
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "selected-fixture.py").write_bytes(raw)
    started = monotonic()
    report = dict(status="FAILED", fixture_path=str(fixture), fixture_sha256=sha256(raw).hexdigest(),
                  project_root=str(project_root), profile=None, checks=[], unmet_prerequisites=[],
                  scientific_authority="NONE", qualification="NOT_ESTABLISHED")
    try:
        from empirical_lawhood.api.recursive_authoring import implementation_binding
        selected_source = implementation_binding(project_root)
        (output_dir / "selected-source.json").write_bytes(selected_source.canonical_bytes())
        report["implementation_sha256"] = selected_source.fingerprint()
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1",
                           OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        result = run_bounded_command((sys.executable, "-B", "-m", __spec__.name, "--worker",
            "--project-root", str(project_root), "--fixture", str(fixture)),
            cwd=output_dir, environment=environment, input_bytes=raw,
            maximum_input_bytes=MAX_FIXTURE_BYTES, timeout_seconds=timeout_seconds,
            maximum_stdout_bytes=8 * 1024**2, maximum_stderr_bytes=64 * 1024)
        (output_dir / "worker.stderr.txt").write_bytes(result.stderr)
        (output_dir / "worker.stdout.json").write_bytes(result.stdout)
        report = json.loads(result.stdout) if result.stdout else report
        report["worker_exit_code"] = result.returncode
        if result.returncode:
            if report["status"] == "PASSED_SELECTED_CHECKS":
                report["status"] = "FAILED"
            if not result.stdout:
                report["failure"] = dict(type="ConformanceWorkerFailure", message="See retained worker.stderr.txt for the original refusal")
        if read_bounded_bytes(fixture, maximum_bytes=MAX_FIXTURE_BYTES) != raw:
            report.update(status="FAILED", failure=dict(type="FixtureChanged", message="Selected fixture changed during conformance"))
        if implementation_binding(project_root) != selected_source:
            report.update(status="FAILED", failure=dict(type="SourceChanged", message="Selected implementation changed during conformance"))
        return report
    except Exception as error:
        report["failure"] = dict(type=type(error).__name__, message=str(error)[:2000])
        return report
    finally:
        report["outer_wall_seconds"] = str(monotonic() - started)
        (output_dir / "conformance.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path, help="Trusted local Python fixture to execute")
    parser.add_argument("--project-root", required=True, type=Path, help="Selected checkout or matching installed source distribution")
    parser.add_argument("--output-dir", type=Path, help="New external directory for exact fixture and results")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="Conformance process bound, at most 120 seconds")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return _worker(args.project_root, str(args.fixture))
    if args.output_dir is None:
        parser.error("--output-dir is required")
    report = check_fixture(fixture=args.fixture, project_root=args.project_root,
        output_dir=args.output_dir, timeout_seconds=args.timeout_seconds)
    print(json.dumps(dict(status=report["status"], report_path=str(args.output_dir / "conformance.json"))))
    return 0 if report["status"] == "PASSED_SELECTED_CHECKS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
