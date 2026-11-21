# SPDX-License-Identifier: MPL-2.0
"""Disclosed process/telemetry controls. No application handler is executed."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import select
import sys
import time
from uuid import uuid4

from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationRequest
from empirical_lawhood.execution.local.application_progress import ApplicationProgressReporter
from empirical_lawhood.storage.application_invocations import ApplicationInvocationStore, process_identity, utc_now
from empirical_lawhood.workbench.broker import load_contexts
from empirical_lawhood.workbench.launcher import negotiate_engine


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def prepare(args):
    source = ApplicationContext.from_document(json.loads(args.context.read_text()))
    args.output_dir.mkdir(parents=True, exist_ok=False)
    contexts = []
    for index in range(2):
        root = args.output_dir / f"context-{index}"
        for name in ("invocations", "progress", "inputs"):
            (root / name).mkdir(parents=True)
        context = replace(source, context_id=f"exposed.progress.{uuid4().hex}",
            label=f"Exposed progress control {index + 1}; no scientific execution",
            invocation_root=root / "invocations", progress_root=root / "progress",
            input_root=root / "inputs", collection_path=None, observation_root=None,
            operator_profile=args.operator_profile, operational_profile=args.operator_profile)
        contexts.append(context.to_document())
    path = args.output_dir / "contexts.json"
    write(path, {"schema": "empirical-lawhood/application/contexts", "version": "1.0.0", "contexts": contexts})
    write(args.output_dir / "controls.json", {"scope": "EXPOSED_PROCESS_AND_TELEMETRY_CONTROL_NO_HANDLER_EXECUTION",
        "contexts": str(path), "required_mount": str(args.required_mount), "python": sys.executable})
    print(json.dumps({"contexts": str(path), "expected_file": str(args.output_dir / "controls.json")}))


def worker(args):
    rows, owners = [], []
    try:
        for context in load_contexts(args.contexts):
            selected = negotiate_engine(context)
            operation = "recursive.run"
            assert any(item["operation_id"] == operation and item["lifecycle"] == "EFFECT" for item in selected.description["operations"])
            request = ApplicationRequest(uuid4().hex, context.context_id, operation, (("directory", str(context.input_root)),))
            store = ApplicationInvocationStore(context.invocation_root, args.required_mount)
            handle, fresh = store.claim(context_id=context.context_id, context_sha256=context.fingerprint(),
                engine_sha256=selected.identity_sha256, context=context.to_document(), request=request.to_document(), client="browser")
            assert fresh
            binding = store.intent(handle)["binding_sha256"]
            store.publish(handle, "entered", {"handle": handle, "binding_sha256": binding,
                "entered_utc": utc_now(), "process": process_identity(), "control_scope": "NO_HANDLER_EXECUTION"})
            reporter = ApplicationProgressReporter(context.progress_root / (handle + ".json"), operation, store=store, handle=handle)
            owners.append((store, handle, binding, reporter))
            for index in range(70):
                reporter.step_completed(phase=f"control.step.{index}", done=1, total=2, unit="items",
                    elapsed_seconds=0.125, status="FAILED" if index == 68 else "INTERRUPTED" if index == 69 else "RETURNED")
            reporter.workflow_update(done=5, total=12, failed=2, unit="tasks")
            reporter.update(phase="control.file-publication", done=9007199254740993,
                total=9007199254740999, failed=0, unit="bytes", detail="Exposed counters; no scientific work", task_id="exposed.task.1")
            reporter.heartbeat()
            rows.append({"handle": handle, "context_id": context.context_id, "operation": operation})
        print(json.dumps({"event": "ready", "rows": rows}), flush=True)
        last = time.monotonic()
        while True:
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if ready:
                line = sys.stdin.readline()
                if not line:
                    break
                command = json.loads(line)
                if command["action"] == "quit":
                    break
                for store, handle, binding, reporter in owners:
                    if command["action"] == "unknown":
                        reporter.update(phase="control.native-iterations", done=7, total=None, unit="iterations", detail="Required convergence count unknown")
                        reporter.heartbeat()
                    elif command["action"] == "return":
                        reporter.finish("RETURNED")
                        store.publish(handle, "returned", {"handle": handle, "binding_sha256": binding,
                            "returned_utc": utc_now(), "status": "SUCCEEDED", "reason_codes": [],
                            "control_scope": "NO_HANDLER_EXECUTION", "response_body_retained": False})
                    elif command["action"] == "heartbeat":
                        reporter.heartbeat()
                    else:
                        raise ValueError("unknown control action")
                print(json.dumps({"event": "ack", "id": command["id"]}), flush=True)
            if time.monotonic() - last >= 2:
                for _, _, _, reporter in owners:
                    reporter.heartbeat()
                last = time.monotonic()
    finally:
        for _, _, _, reporter in owners:
            reporter.finish("INTERRUPTED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--context", type=Path)
    parser.add_argument("--contexts", type=Path)
    parser.add_argument("--operator-profile", type=Path)
    parser.add_argument("--required-mount", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args)
    else:
        if None in (args.context, args.output_dir, args.operator_profile):
            parser.error("preparation requires --context, --operator-profile and --output-dir")
        prepare(args)


if __name__ == "__main__":
    main()
