# SPDX-License-Identifier: MPL-2.0
"""Standalone metadata collector; browser and budget-supervisor lifetimes are separate."""

import argparse
from hashlib import sha256
from pathlib import Path
import sys
import time
from uuid import uuid4

from empirical_lawhood.api.application_contracts import ApplicationContext, load_application_json
from empirical_lawhood.api.application_state import operational_state_store
from empirical_lawhood.api.operational_observation import collect_observation
from empirical_lawhood.storage.artifact_replication import _durable_bytes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.execution.operational_observation import document, document_bytes, validate_selection


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--collector-id", default=None)
    parser.add_argument("--previous-snapshot-sha256")
    parser.add_argument("--watch", action="store_true", help="Continue at the frozen source cadence until stopped explicitly.")
    args = parser.parse_args(argv)
    try:
        context = ApplicationContext.from_document(load_application_json(read_bounded_bytes(args.context, maximum_bytes=256 * 1024)))
        if context.python_executable != Path(sys.executable).absolute():
            raise ValueError("start the collector with its selected engine interpreter")
        if context.project_root is not None:
            from empirical_lawhood.storage.source_origin import require_selected_implementation
            require_selected_implementation(context.project_root)
        raw = read_bounded_bytes(args.selection, maximum_bytes=128 * 1024)
        selected = validate_selection(document(raw, maximum_bytes=128 * 1024))
        if context.observation_root is None or not args.output_dir.is_absolute():
            raise ValueError("select explicit guarded observation and collector destinations")
        args.output_dir.relative_to(context.observation_root)
        store = operational_state_store(context, path=args.output_dir / "latest-export.json")
        if not store.writable:
            raise PermissionError("collector output profile is read-only")
        root = store.root
        root.resolve(args.output_dir.relative_to(root.contract.canonical_path).as_posix(), for_write=True)
        args.output_dir.mkdir(mode=0o700)
        collector_id = args.collector_id or "collector." + uuid4().hex
        _durable_bytes(args.output_dir / "selection.json", raw)
        _durable_bytes(args.output_dir / "collector.json", document_bytes({"collector_id": collector_id,
            "previous_snapshot_sha256": args.previous_snapshot_sha256, "selection_sha256": sha256(raw).hexdigest(),
            "provider_calls": 0, "native_calls": 0, "lifecycle_actions": 0}))
        sequence, prior, current = 0, args.previous_snapshot_sha256, None
        while True:
            sequence += 1
            exported = collect_observation(context, {"path": str(args.selection), "sha256": sha256(raw).hexdigest()},
                collector_id=collector_id, sequence=sequence, previous_snapshot_sha256=prior,
                output_directory=args.output_dir / f"observation-{sequence:06d}")
            current = store.replace(document_bytes(exported), expected_sha256=current)
            sys.stdout.buffer.write(document_bytes(exported))
            sys.stdout.buffer.flush()
            prior = exported["snapshot_sha256"]
            if not args.watch:
                return 0
            time.sleep(selected["cadence_seconds"])
    except KeyboardInterrupt:
        # Stopping this observer never cancels scientific work or its supervisor.
        return 130
    except Exception as error:
        sys.stderr.buffer.write(document_bytes({"status": "OBSERVATION_REFUSED", "reason": type(error).__name__,
            "message": "Inspect the selected source, storage and collector records. No scientific or financial action was taken."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
