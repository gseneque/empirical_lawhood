# SPDX-License-Identifier: MPL-2.0
"""Release-only workflow observations; samples do not establish resource bounds."""

from collections import Counter
from contextlib import contextmanager
from functools import wraps
import json
import os
from pathlib import Path
from threading import Event, Thread
from time import perf_counter

from empirical_lawhood.infrastructure import bounded_io


def _resident_bytes(pid):
    try:
        rows = Path(f"/proc/{pid}/status").read_text().splitlines()
    except (OSError, UnicodeError):
        return None
    for row in rows:
        if row.startswith("VmRSS:"):
            return int(row.split()[1]) * 1024
    return None


def _process_sample():
    parent = os.getpid()
    pending, visited, child_bytes = [parent], set(), 0
    parent_bytes = _resident_bytes(parent)
    observed_children = 0
    while pending:
        pid = pending.pop()
        if pid in visited:
            continue
        visited.add(pid)
        if pid != parent:
            observed = _resident_bytes(pid)
            if observed is not None:
                child_bytes += observed
                observed_children += 1
        try:
            tasks = tuple(Path(f"/proc/{pid}/task").iterdir())
        except OSError:
            continue
        for task in tasks:
            try:
                children = (task / "children").read_text().split()
            except (OSError, UnicodeError):
                continue
            pending.extend(int(child) for child in children)
    return parent_bytes, child_bytes, observed_children


def _process_io():
    try:
        rows = Path("/proc/self/io").read_text().splitlines()
        return {key: int(value) for key, value in (row.split(": ", 1) for row in rows)}
    except (OSError, UnicodeError, ValueError):
        return {}


class _ResidentSampler:
    def __init__(self):
        self.stop = Event()
        self.thread = Thread(target=self._run, daemon=True)
        self.samples = 0
        self.parent_peak = self.children_peak = self.combined_peak = 0
        self.maximum_observed_children = 0
        self.parent_available = False

    def sample(self):
        parent, children, child_count = _process_sample()
        self.samples += 1
        if parent is not None:
            self.parent_available = True
            self.parent_peak = max(self.parent_peak, parent)
            self.combined_peak = max(self.combined_peak, parent + children)
        self.children_peak = max(self.children_peak, children)
        self.maximum_observed_children = max(self.maximum_observed_children, child_count)

    def _run(self):
        while not self.stop.wait(0.1):
            self.sample()

    def start(self):
        self.sample()
        self.thread.start()

    def finish(self):
        self.stop.set()
        self.thread.join()
        self.sample()
        return {
            "samples": self.samples,
            "parent_rss_available": self.parent_available,
            "parent_sampled_peak_rss_bytes": self.parent_peak if self.parent_available else None,
            "descendants_sampled_peak_summed_rss_bytes": self.children_peak,
            "parent_and_descendants_sampled_peak_summed_rss_bytes":
                self.combined_peak if self.parent_available else None,
            "maximum_observed_descendants": self.maximum_observed_children,
        }


@contextmanager
def _observations(monkeypatch, callbacks):
    counters, paths, descriptors = Counter(), Counter(), {}
    original_open = bounded_io._open_regular
    original_contained = bounded_io._open_contained_regular
    original_chunks = bounded_io._regular_chunks

    def observed_open(path, **kwargs):
        descriptor, before = original_open(path, **kwargs)
        descriptors[descriptor] = str(path)
        paths[str(path)] += 1
        counters["bounded_regular_opens"] += 1
        return descriptor, before

    def observed_contained(root, path, maximum_bytes):
        descriptor, before = original_contained(root, path, maximum_bytes)
        descriptors[descriptor] = str(path)
        paths[str(path)] += 1
        counters["bounded_contained_opens"] += 1
        return descriptor, before

    def observed_chunks(descriptor, before, **kwargs):
        try:
            for chunk in original_chunks(descriptor, before, **kwargs):
                counters["bounded_" + kwargs["operation"] + "_bytes"] += len(chunk)
                counters["bounded_" + kwargs["operation"] + "_chunks"] += 1
                yield chunk
        finally:
            descriptors.pop(descriptor, None)

    def counted(owner, name, label):
        original = getattr(owner, name)

        @wraps(original)
        def observed(*args, **kwargs):
            counters[label] += 1
            return original(*args, **kwargs)
        return observed

    with monkeypatch.context() as scope:
        scope.setattr(bounded_io, "_open_regular", observed_open)
        scope.setattr(bounded_io, "_open_contained_regular", observed_contained)
        scope.setattr(bounded_io, "_regular_chunks", observed_chunks)
        for owner, name, label in callbacks:
            scope.setattr(owner, name, counted(owner, name, label))
        yield counters, paths


def matrix_observation_callbacks():
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_original_publications
    from empirical_lawhood.api import recursive_qualified_parents
    from empirical_lawhood.infrastructure import source_closure

    return (
        (source_closure, "capture_admitted_target_source", "source_capture_calls"),
        (source_closure, "_verify_selected_member", "selected_source_member_verifications"),
        (recursive_qualified_parents, "_collect_receipt_closure", "complete_parent_receipt_closure_traversals"),
        (protected_original_publications, "authenticate_protected_e3_fit_originals", "original_fit_authentication_calls"),
        (protected_original_publications, "_canonical_original", "original_publication_decodes"),
    )


class WorkflowMeasurements:
    """Retain observed phase costs without changing the selected science."""

    def __init__(self, path, monkeypatch, *, selection, callbacks=()):
        self.path = Path(path)
        if not self.path.is_absolute() or self.path.exists():
            raise ValueError("Select a new absolute workflow measurement path")
        self.monkeypatch, self.callbacks = monkeypatch, callbacks
        self.started = perf_counter()
        self.report = {
            "schema": "empirical-lawhood/testing/workflow-phase-measurements",
            "version": "1.0.0",
            "status": "RUNNING",
            "selection": selection,
            "standing": "EXPOSED_CONFORMANCE_NONPROMOTABLE",
            "qualification": "NOT_ESTABLISHED",
            "wider_a04_closure": False,
            "limits": [
                "RSS is sampled every 0.1 seconds and at phase boundaries; short-lived peaks can be missed.",
                "Summed process RSS includes shared pages more than once; it is not unique physical memory.",
                "Bounded I/O and callback counters observe the parent process only; spawned worker and Git subprocess I/O are excluded.",
                "Callback counts include only calls through the named module attributes; imported aliases can bypass those counters.",
                "Process I/O includes instrumentation and page-cache effects; warm/cold cache conditions are uncontrolled.",
                "Elapsed times include monitoring overhead and concurrent host work. Unmeasured intervals remain explicit.",
                "Completed-run replay preserves original populations and is not another native workflow or fresh qualification.",
            ],
            "phases": [],
        }
        with self.path.open("x", encoding="utf-8") as stream:
            json.dump(self.report, stream, indent=2, sort_keys=True)
            stream.write("\n")

    def _retain(self):
        temporary = self.path.with_name(self.path.name + ".writing")
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(self.report, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.path)

    def call(self, label, operation, *args, **kwargs):
        if self.report["status"] != "RUNNING" or any(row["phase"] == label for row in self.report["phases"]):
            raise ValueError("Workflow phase must be new and the observation session must be active")
        row = {"phase": label, "status": "RUNNING"}
        self.report["phases"].append(row)
        self._retain()
        sampler, io_before = _ResidentSampler(), _process_io()
        started = perf_counter()
        sampler.start()
        try:
            with _observations(self.monkeypatch, self.callbacks) as (counters, paths):
                result = operation(*args, **kwargs)
            row["status"] = "SUCCEEDED"
            return result
        except BaseException as error:
            row.update(status="FAILED", exception_type=type(error).__name__)
            self.report["status"] = "FAILED"
            raise
        finally:
            row.update(sampler.finish())
            row["elapsed_seconds"] = perf_counter() - started
            after = _process_io()
            row["parent_process_io_delta"] = {
                key: after[key] - value for key, value in io_before.items() if key in after
            }
            if "counters" in locals():
                row["parent_callbacks_and_bounded_io"] = dict(sorted(counters.items()))
                row["distinct_bounded_paths"] = len(paths)
                row["maximum_bounded_opens_for_one_path"] = max(paths.values(), default=0)
                row["most_repeated_bounded_paths"] = [
                    {"path": path, "opens": count} for path, count in paths.most_common(10)
                ]
            self.report["observed_workflow_seconds"] = perf_counter() - self.started
            self._retain()

    def finish(self):
        if self.report["status"] != "RUNNING":
            raise ValueError("Failed workflow observations cannot be finalized as successful")
        measured = sum(row["elapsed_seconds"] for row in self.report["phases"])
        elapsed = perf_counter() - self.started
        self.report.update(status="SUCCEEDED", observed_workflow_seconds=elapsed,
            measured_phase_seconds=measured, unmeasured_interval_seconds=max(0.0, elapsed - measured))
        self._retain()


def measure_complete_retained_e3(measurements, *, writer, package, plan, specification, allocation, reveal_authority_id):
    """Recompute complete saved statistics after original current reveal checks."""
    from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as science
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import statistical_task_id
    from empirical_lawhood.api.domain_composition.matrix_protected_response import scientific_read
    from empirical_lawhood.api.current_result_custody import authenticate_current_execution_plan

    def load():
        scientific_read._authorize(writer, package, reveal_authority_id)
        authenticated = authenticate_current_execution_plan(package=package, issued=package.issued_study,
            run_id=package.run_plan_id, writer=writer)
        if authenticated != plan:
            raise PermissionError("Measurement requires the exact authenticated complete original plan")
        typed_writer = scientific_read._retained_scientific_writer(package, plan, writer)
        receipts, _terminal = scientific_read._completed_receipts(typed_writer, package, plan)
        identities = specification.identity, allocation.identity

        def one(operation, kind, **kwargs):
            return scientific_read._product(typed_writer, plan, receipts,
                statistical_task_id(*identities, operation, **kwargs), kind)[0]

        models = one("fit", science.ProtectedE3ModelSet)
        model_freeze = one("freeze", science.ProtectedE3FrozenProducts, mode="model")
        calibrated = one("freeze", science.ProtectedE3FrozenProducts, mode="calibration")
        calibration = one("calibrate", science.ProtectedE3Calibration)
        assessment = one("assess", science.ProtectedE3Assessment)
        forecasts, outcomes = [], []
        for task_id, receipt in sorted(receipts.items()):
            schemas = {value.payload_schema for value in receipt.output_logical_artifacts}
            for kind, destination in ((science.ProtectedE3Forecast, forecasts), (science.ProtectedE3PairedOutcome, outcomes)):
                if kind.SCHEMA in schemas:
                    destination.append(scientific_read._product(typed_writer, plan, receipts, task_id, kind)[0])
        return models, model_freeze, calibrated, calibration, assessment, tuple(forecasts), tuple(outcomes)

    products = measurements.call("load_complete_original_statistical_inputs", load)
    models, model_freeze, calibrated, calibration, assessment, forecasts, outcomes = products
    by_role = {}
    for role in ("calibration", "evaluation"):
        units = set(allocation.unit_ids(role))
        role_forecasts = tuple(sorted((value for value in forecasts if value.role == role),
            key=lambda value: value.feature.unit_id))
        role_outcomes = tuple(sorted((value for value in outcomes if value.unit_id in units),
            key=lambda value: value.unit_id))
        assert len(role_forecasts) == len(role_outcomes) == len(units)
        assert {value.feature.unit_id for value in role_forecasts} == {value.unit_id for value in role_outcomes} == units
        by_role[role] = role_forecasts, role_outcomes
    recalibrated = measurements.call("complete_calibration_math", science.calibrate_protected_e3,
        specification, allocation, models, model_freeze, *by_role["calibration"], record_id=calibration.record_id)
    reassessed = measurements.call("complete_confirmation_assessment_math", science.assess_protected_e3,
        specification, allocation, calibrated, *by_role["evaluation"], record_id=assessment.record_id)
    assert recalibrated.canonical_bytes() == calibration.canonical_bytes()
    assert reassessed.canonical_bytes() == assessment.canonical_bytes()
    return {
        "calibration_units": len(allocation.unit_ids("calibration")),
        "confirmation_units": len(allocation.unit_ids("evaluation")),
        "complete_forecasts": len(forecasts),
        "complete_outcomes": len(outcomes),
        "calibration_sha256": recalibrated.fingerprint(),
        "assessment_sha256": reassessed.fingerprint(),
        "original_statistical_bytes_reproduced": True,
        "native_acquisitions": 0,
        "random_streams_consumed": 0,
    }
