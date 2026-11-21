# SPDX-License-Identifier: MPL-2.0
"""Explicit original-return handoff around existing transfer and scientific readers."""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from empirical_lawhood.storage.transfer_files import verify_transfer
from empirical_lawhood.storage.operational_observation import read_selected_pin
from empirical_lawhood.execution.operational_observation import MAX_BYTES, RETURN_STAGES, VERSION, document, document_bytes, fields, pin
from empirical_lawhood.api.application_contracts import ApplicationError, ApplicationRequest, absolute_path, response_bytes
from empirical_lawhood.api.application_state import operational_state_store


def _store(context, entry):
    path = entry["value"]["deployment"].get("return_path")
    if path is None:
        raise ApplicationError("RETURN_PATH_REQUIRED", "Select an explicit operational return journal for this deployment.")
    if context.observation_root is None:
        raise ApplicationError("OBSERVATION_ROOT_REQUIRED", "Select the guarded local observation root.")
    selected = absolute_path(path, "return_path")
    selected.relative_to(context.observation_root)
    return operational_state_store(context, path=selected)


def _initial(binding):
    return {"schema": "empirical-lawhood/operational/original-return", "version": VERSION, "binding": binding,
        "revision": 0, "observed_utc": None, "terminal": False, "stages": [{"stage": stage, "status": "UNAVAILABLE",
            "source": None, "scope": "NOT_YET_OBSERVED", "closed": False} for stage in RETURN_STAGES]}


def _read(store, binding):
    raw = store.read()
    if raw is None:
        return None, _initial(binding)
    value = document(raw)
    fields(value, ("schema", "version", "binding", "revision", "observed_utc", "terminal", "stages"))
    if (value["schema"] != "empirical-lawhood/operational/original-return" or value["version"] != VERSION
            or value["binding"] != binding or tuple(row.get("stage") for row in value["stages"]) != RETURN_STAGES):
        raise PermissionError("return journal changes its original work or complete stage census")
    if type(value["revision"]) is not int or value["revision"] < 1:
        raise ValueError("return journal requires its positive operational revision")
    from empirical_lawhood.execution.deployment_budget import utc
    from empirical_lawhood.execution.operational_observation import text
    utc(value["observed_utc"])
    for row in value["stages"]:
        fields(row, ("stage", "status", "source", "scope", "closed"))
        text(row["status"])
        text(row["scope"], maximum=512)
        if row["source"] is not None:
            pin(row["source"])
        if type(row["closed"]) is not bool:
            raise ValueError("return stage requires an explicit lifetime disposition")
    if type(value["terminal"]) is not bool or value["terminal"] != all(row["closed"] for row in value["stages"]):
        raise ValueError("return terminal state changes its complete stage census")
    return sha256(raw).hexdigest(), value


def read_return(context, *, entry, binding):
    if entry["value"]["deployment"].get("return_path") is None:
        return {**_initial(binding), "state_sha256": None, "status": "RETURN_JOURNAL_NOT_SELECTED"}
    store = _store(context, entry)
    digest, value = _read(store, binding)
    if digest is not None and store.read() != document_bytes(value):
        raise ApplicationError("RETURN_CHANGED", "The original-return observation changed. Reopen it.")
    return {**value, "state_sha256": digest, "status": "OBSERVED" if digest else "NOT_YET_RECORDED"}


def _require_original_binding(identity, binding, *, reader_operation=None):
    from empirical_lawhood.science.records.decoding import decode_canonical_record
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.execution.recursive_handoff import AuthoredRecursiveWave
    if reader_operation == "sci02d.findings":
        fields(identity, ("packet_sha256", "draft_sha256", "execution_plan_sha256"))
        from empirical_lawhood.science.records.serialization import validate_sha256
        for value in identity.values():
            validate_sha256(value)
        if identity["packet_sha256"] != binding["packet_sha256"]:
            raise PermissionError("returned original differs from the deployment's authored wave")
        return
    original = decode_canonical_record(identity, ObjectIdentity)
    if (original.object_schema != AuthoredRecursiveWave.SCHEMA
            or original.object_fingerprint != binding["packet_sha256"]):
        raise PermissionError("returned original differs from the deployment's authored wave")


def record_return(context, request, values, *, entry, binding):
    """Explicit terminal/API actions only. No action is driven by a browser refresh."""
    selected = document(values["text"].encode(), maximum_bytes=128 * 1024)
    fields(selected, ("stage", "action"), optional=("root", "manifest", "manifest_sha256", "source", "close", "reader_index"))
    stage, action = selected["stage"], selected["action"]
    if stage not in RETURN_STAGES:
        raise ValueError("select one original-return stage")
    allowed = ({"stage", "action", "source", "close"} if action in ("STARTED", "FAILED", "UNAVAILABLE", "DECLINED") else
        {"stage", "action", "root", "manifest", "manifest_sha256"} if action == "VERIFY_FILES" else
        {"stage", "action", "reader_index"} if action in ("READ_ORIGINAL", "READ_CONTRIBUTION") else None)
    if allowed is None or set(selected) - allowed:
        raise ValueError("return action includes unsupported selections")
    store = _store(context, entry)
    digest, journal = _read(store, binding)
    if values.get("expected_return_sha256") != digest:
        raise ApplicationError("RETURN_CHANGED", "Read the current return journal before updating it.")
    source, details, closed = None, {}, False
    if action in ("STARTED", "FAILED", "UNAVAILABLE", "DECLINED"):
        source = selected.get("source")
        if source is not None:
            pin(source)
            if context.input_root is None:
                raise ApplicationError("INPUT_ROOT_REQUIRED", "Select the operational source root.")
            Path(source["path"]).relative_to(context.input_root)
            read_selected_pin(source, maximum_bytes=MAX_BYTES)
        closed = selected.get("close", False)
        if type(closed) is not bool:
            raise ValueError("select the return-stage lifetime explicitly")
        status, scope = action, "OPERATOR_REPORTED; NO_SCIENTIFIC_OR_TRANSFER_VERDICT"
    elif action == "VERIFY_FILES":
        if stage not in RETURN_STAGES[:4]:
            raise ValueError("file verification does not replace an original scientific read")
        root, manifest = absolute_path(selected["root"], "root"), absolute_path(selected["manifest"], "manifest")
        if context.input_root is None:
            raise ApplicationError("INPUT_ROOT_REQUIRED", "Select the explicit original-return input root.")
        root.relative_to(context.input_root)
        manifest.relative_to(context.input_root)
        source = {"path": str(manifest), "sha256": selected["manifest_sha256"]}
        details = verify_transfer(root, manifest, expected_sha256=source["sha256"])
        status, scope, closed = "BYTE_VERIFIED", "COMPLETE_SELECTED_FILES; ORIGINAL_READING_AND_ASSESSMENT_REMAIN_SEPARATE", True
    elif action in ("READ_ORIGINAL", "READ_CONTRIBUTION"):
        expected_stage = "INDEPENDENT_READING" if action == "READ_ORIGINAL" else "CONTRIBUTION"
        if stage != expected_stage:
            raise ValueError("select the actual original reader's return stage")
        from empirical_lawhood.api.application import execute_application
        operation = "exploration.read" if action == "READ_ORIGINAL" else "exploration.companion"
        parameters = {"selection_id": entry["value"]["selection_id"], "reader_index": selected.get("reader_index", 0)}
        if action == "READ_CONTRIBUTION":
            parameters["role"] = "contribution"
        result = execute_application(context, ApplicationRequest(request.request_id, context.context_id, operation, tuple(parameters.items())))
        if not result.succeeded:
            raise ApplicationError("ORIGINAL_RETURN_READ_REFUSED", "The original owning reader refused this return. Its unresolved stage remains visible.")
        reader_operation = entry["value"]["readers"][parameters["reader_index"]]["operation"] if action == "READ_ORIGINAL" else None
        _require_original_binding(result.payload.get("identity" if action == "READ_ORIGINAL" else "original_identity"), binding,
            reader_operation=reader_operation)
        details = {"operation": operation, "response_sha256": sha256(response_bytes(result)).hexdigest(),
            "original_identity": entry["value"]["identity"], "new_native_calls": 0}
        status, scope, closed = "ORIGINAL_READ_COMPLETED", "ORIGINAL_OWNER_READ; DISPOSITION_AND_CONSUMER_ADMISSION_NOT_INFERRED", True
    else:
        raise ValueError("unsupported original-return action")
    from empirical_lawhood.api.application_collection import selected_entry
    current, _ = selected_entry(context, entry["value"]["selection_id"])
    if current != entry:
        raise ApplicationError("COLLECTION_CHANGED", "The registered work changed during the return handoff.")
    observed = datetime.now(timezone.utc).isoformat()
    receipt = {"schema": "empirical-lawhood/operational/return-observation", "version": VERSION,
        "binding": binding, "stage": stage, "status": status, "scope": scope, "source": source,
        "observed_utc": observed, "details": details, "previous_return_sha256": digest,
        "native_calls": 0, "lifecycle_actions": 0, "scientific_authority": "NONE"}
    revision = journal["revision"] + 1
    path = store.path.with_name(store.path.name + ".records") / f"return-{revision:06d}-{uuid4().hex}.json"
    receipt_store = operational_state_store(context, path=path)
    receipt_digest = receipt_store.replace(document_bytes(receipt), expected_sha256=None)
    row = next(row for row in journal["stages"] if row["stage"] == stage)
    row.update(status=status, source={"path": str(path), "sha256": receipt_digest}, scope=scope, closed=closed)
    journal.update(revision=revision, observed_utc=observed, terminal=all(item["closed"] for item in journal["stages"]))
    result = store.replace(document_bytes(journal), expected_sha256=digest)
    return {"status": status, "stage": stage, "state_sha256": result, "revision": revision,
        "receipt": row["source"], "native_calls": 0, "lifecycle_actions": 0, "scientific_authority": "NONE"}
