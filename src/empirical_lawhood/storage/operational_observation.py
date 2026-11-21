# SPDX-License-Identifier: MPL-2.0
"""Bounded retained observations and atomic transport, without provider clients."""

from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
from uuid import uuid4

from empirical_lawhood.execution.deployment_budget import utc
from empirical_lawhood.execution.operational_observation import FINANCIAL_STATES, MAX_BYTES, MAX_ROWS, MONEY_FIELDS, VERSION, document, document_bytes, exact_amount, fields, validate_snapshot
from empirical_lawhood.storage.transfer_files import seal_transfer, verify_transfer
from empirical_lawhood.storage.artifact_replication import _durable_bytes
from empirical_lawhood.storage.bounded_io import _open_contained_regular, _stable_descriptor, _read_regular_descriptor
from empirical_lawhood.execution.remote.deployment_supervision_selection import SupervisionSelection


def _contained(root, path, *, maximum_bytes):
    descriptor, before = _open_contained_regular(root, path, maximum_bytes)
    return _read_regular_descriptor(descriptor, before, maximum_bytes=maximum_bytes)


def read_selected_pin(selected, *, maximum_bytes=128 * 1024):
    path = Path(selected["path"])
    raw = _contained(path.parent, path, maximum_bytes=maximum_bytes)
    if sha256(raw).hexdigest() != selected["sha256"]:
        raise PermissionError("selected operational source changed its retained digest")
    return raw


def _event_window(directory):
    """Read only a bounded suffix, retaining offsets and complete JSONL lines."""
    path = directory / "events.jsonl"
    descriptor, before = _open_contained_regular(directory, path, 64 * MAX_BYTES)
    with _stable_descriptor(descriptor, before, operation="supervisor event suffix"):
        start = max(0, before.st_size - MAX_BYTES)
        os.lseek(descriptor, start, os.SEEK_SET)
        chunks, remaining = [], before.st_size - start
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                raise PermissionError("supervisor event suffix changed during its read")
            chunks.append(chunk)
            remaining -= len(chunk)
    raw = b"".join(chunks)
    offset = start
    if start:
        boundary = raw.find(b"\n")
        if boundary < 0:
            raise ValueError("supervisor event exceeds the bounded suffix")
        offset += boundary + 1
        raw = raw[boundary + 1:]
    # A writer can be between append and fsync. Never promote its partial line.
    end = raw.rfind(b"\n")
    complete = raw[:end + 1] if end >= 0 else b""
    lines = complete.splitlines(keepends=True)
    omitted = max(0, len(lines) - MAX_ROWS)
    offset += sum(len(line) for line in lines[:omitted])
    result = []
    for line in lines[omitted:]:
        row = document(line, maximum_bytes=64 * 1024)
        source = {"path": str(path), "sha256": sha256(line).hexdigest(), "byte_offset": offset, "size_bytes": len(line)}
        result.append((row, source))
        offset += len(line)
    return result, "BOUNDED_SUFFIX" if start or omitted else "COMPLETE_RETAINED_EVENT_CENSUS"


def read_supervision(selections, allocation):
    """Project allowed fields from original supervisor records, never its actions."""
    allocation.__post_init__()
    result = {"status": "UNAVAILABLE", "allocation": allocation.to_document(), "accounting": None,
        "lifecycle": None, "events": [], "event_coverage": "NO_SELECTED_SUPERVISOR",
        "liabilities": "UNKNOWN_OUTSIDE_REPORTED_ACCOUNTING_INTERVAL",
        "retained_volume_charges": "CONTINUING_UNTIL_SEPARATE_VOLUME_RETIREMENT"}
    before, previous_accounted = [], None
    for selected in selections:
        root = Path(selected["directory"])
        pin = {"path": str(root / "selection.json"), "sha256": selected["selection_sha256"]}
        raw = read_selected_pin(pin)
        original = SupervisionSelection.from_document(document(raw, maximum_bytes=128 * 1024))
        declared, actual = allocation.to_document(), original.allocation.to_document()
        # A subsequent supervisor may raise its retained accounting floor. Other
        # allocation, quote and liability selections remain the same binding.
        for value in (declared, actual):
            value["budget"].pop("accounting_floor_usd")
        if actual != declared:
            raise PermissionError("supervisor changes the selected allocation or monetary policy")
        if previous_accounted is not None and exact_amount(original.allocation.budget.accounting_floor_usd) < previous_accounted:
            raise PermissionError("new supervisor loses the previous lifetime's accounting floor")
        window, coverage = _event_window(root)
        for event, source in window:
            state = event.get("status")
            if state not in FINANCIAL_STATES:
                raise ValueError("supervisor event has an unsupported lifecycle state")
            if (event.get("native_work_dispatched") is not False or event.get("automatic_replay") is not False
                    or event.get("keep_volume_id") != allocation.volume_id):
                raise PermissionError("supervisor event changes its original effect or volume scope")
            utc(event["recorded_utc"])
            lifecycle = {"status": state, "recorded_utc": event["recorded_utc"], "source": source}
            result["events"].append(lifecycle)
            result["lifecycle"] = lifecycle
            result["status"] = state
            if "accounted_usd" in event:
                # Arithmetic and decisions remain verbatim from account_deployment.
                amount = exact_amount(event["accounted_usd"])
                if amount < exact_amount(original.allocation.budget.accounting_floor_usd) or (
                        previous_accounted is not None and amount < previous_accounted):
                    raise PermissionError("retained supervisor accounting regressed")
                previous_accounted = amount
                result["accounting"] = {name: event[name] for name in
                    ("status", "observed_utc", "recorded_utc", "volume_billing_hours_upper", *MONEY_FIELDS)}
                result["accounting"]["source"] = source
        result["event_coverage"] = coverage
        before.append((pin, raw))
    result["events"] = result["events"][-MAX_ROWS:]
    for pin, raw in before:
        if read_selected_pin(pin) != raw:
            raise PermissionError("supervision binding changed during observation")
    return result


def export_snapshot(snapshot, *, root, output_directory):
    """Publish one completed snapshot and the stock original-byte transfer seal."""
    validate_snapshot(snapshot)
    output = Path(output_directory)
    relative = output.relative_to(root.contract.canonical_path).as_posix()
    target = root.resolve(relative, for_write=True)
    if target.exists() or not target.parent.is_dir():
        raise ValueError("select a fresh observation directory below the guarded output root")
    temporary = target.with_name("." + target.name + "." + uuid4().hex + ".pending")
    temporary.mkdir(mode=0o700)
    payload = temporary / "payload"
    payload.mkdir(mode=0o700)
    raw = document_bytes(snapshot)
    _durable_bytes(payload / "snapshot.json", raw)
    sealed = seal_transfer(payload, temporary / "transfer.json", maximum_bytes=MAX_BYTES, maximum_files=1)
    root.verify(for_write=True)
    # A directory rename exposes either the old absence or the entire closed package.
    temporary.rename(target)
    descriptor = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    root.verify(for_write=True)
    return {"status": "SEALED_OPERATIONAL_OBSERVATION", "directory": str(target),
        "manifest": str(target / "transfer.json"), "manifest_sha256": sealed["sha256"],
        "snapshot_sha256": sha256(raw).hexdigest(), "bytes": len(raw),
        "collector_id": snapshot["collector_id"], "sequence": snapshot["sequence"],
        "scientific_authority": "NONE"}


def read_export(directory, *, expected_manifest_sha256):
    directory = Path(directory)
    manifest = directory / "transfer.json"
    original = read_selected_pin({"path": str(manifest), "sha256": expected_manifest_sha256}, maximum_bytes=64 * 1024)
    contents = document(original, maximum_bytes=64 * 1024)
    if (contents.get("maximum_bytes") != MAX_BYTES or contents.get("maximum_files") != 1
            or len(contents.get("files", ())) != 1 or contents["files"][0].get("relative_path") != "snapshot.json"):
        raise ValueError("observation transfer must contain exactly one bounded snapshot")
    verify_transfer(directory / "payload", manifest, expected_sha256=expected_manifest_sha256)
    raw = _contained(directory / "payload", directory / "payload/snapshot.json", maximum_bytes=MAX_BYTES)
    value = validate_snapshot(document(raw))
    if document_bytes(value) != raw:
        raise ValueError("operational snapshot has noncanonical transport bytes")
    verify_transfer(directory / "payload", manifest, expected_sha256=expected_manifest_sha256)
    return raw, value


def read_retained_observation(store):
    raw = store.read()
    if raw is None:
        return None, None
    state = document(raw)
    fields(state, ("schema", "version", "snapshot", "snapshot_sha256", "manifest_sha256",
        "received_utc", "retired_collectors", "sequence_gap"))
    if state["schema"] != "empirical-lawhood/operational/retained-observation" or state["version"] != VERSION:
        raise ValueError("unsupported retained observation revision")
    validate_snapshot(state["snapshot"])
    if sha256(document_bytes(state["snapshot"])).hexdigest() != state["snapshot_sha256"]:
        raise PermissionError("retained observation changes its verified original snapshot")
    if type(state["retired_collectors"]) is not list or len(state["retired_collectors"]) > 64:
        raise ValueError("retained collector census exceeds its bound")
    utc(state["received_utc"])
    return sha256(raw).hexdigest(), state


def import_snapshot(directory, *, expected_manifest_sha256, expected_binding, expected_allocation, store,
                    expected_current_sha256=None, restart_from_snapshot_sha256=None, now=None):
    raw, snapshot = read_export(directory, expected_manifest_sha256=expected_manifest_sha256)
    if snapshot["binding"] != expected_binding:
        raise PermissionError("observation substitutes its registered run, allocation, job card or source")
    if snapshot["financial"]["allocation"] != expected_allocation:
        raise PermissionError("observation changes the body of its selected original allocation")
    current_digest, previous = read_retained_observation(store)
    if expected_current_sha256 != current_digest:
        raise PermissionError("reopen the changed observation before importing another snapshot")
    retired, gap = [], 0
    if previous is not None:
        before = previous["snapshot"]
        if before["binding"] != snapshot["binding"]:
            raise PermissionError("observation history changes its original work binding")
        retired = list(previous["retired_collectors"])
        if snapshot["collector_id"] in retired:
            raise PermissionError("a retired collector cannot replace the current lifetime")
        if snapshot["collector_id"] == before["collector_id"]:
            if snapshot["sequence"] <= before["sequence"]:
                raise PermissionError("operational observation sequence regressed or repeated")
            if snapshot["selection_sha256"] != before["selection_sha256"]:
                raise PermissionError("a collector lifetime cannot change its source selection")
            gap = snapshot["sequence"] - before["sequence"] - 1
        else:
            if (restart_from_snapshot_sha256 != previous["snapshot_sha256"] or snapshot["sequence"] != 1
                    or snapshot["previous_snapshot_sha256"] != previous["snapshot_sha256"]):
                raise PermissionError("bind a new collector explicitly to the last permitted observation")
            retired.append(before["collector_id"])
        if utc(snapshot["source_observed_utc"]) < utc(before["source_observed_utc"]):
            raise PermissionError("operational observation time regressed")
        old_money, new_money = before["financial"]["accounting"], snapshot["financial"]["accounting"]
        if old_money is not None and new_money is not None and exact_amount(new_money["accounted_usd"]) < exact_amount(old_money["accounted_usd"]):
            raise PermissionError("observation loses previously reported cumulative expenditure")
    elif snapshot["sequence"] != 1 or restart_from_snapshot_sha256 is not None:
        raise PermissionError("the first imported collector must begin with its explicit first observation")
    if len(retired) > 64:
        raise ValueError("select a new retained observation history after 64 collector lifetimes")
    state = {"schema": "empirical-lawhood/operational/retained-observation", "version": VERSION,
        "snapshot": snapshot, "snapshot_sha256": sha256(raw).hexdigest(), "manifest_sha256": expected_manifest_sha256,
        "received_utc": now or datetime.now(timezone.utc).isoformat(), "retired_collectors": retired, "sequence_gap": gap}
    # Verify the complete source again immediately before the guarded replacement.
    if read_export(directory, expected_manifest_sha256=expected_manifest_sha256)[0] != raw:
        raise PermissionError("observation export changed before local publication")
    digest = store.replace(document_bytes(state), expected_sha256=current_digest)
    return {"status": "IMPORTED_OPERATIONAL_OBSERVATION", "state_sha256": digest,
        "snapshot_sha256": state["snapshot_sha256"], "received_utc": state["received_utc"],
        "collector_id": snapshot["collector_id"], "sequence": snapshot["sequence"], "sequence_gap": gap,
        "provider_calls": 0, "native_calls": 0, "lifecycle_actions": 0}
