# SPDX-License-Identifier: MPL-2.0
"""Bounded presentation derived from an already authenticated owning result."""

from collections import Counter
import base64
from hashlib import sha256
import json

from empirical_lawhood.api.application_contracts import ApplicationError, MAX_PAGE_ROWS, PROJECTION_VERSION, load_application_json, transport_value


def page(records, *, request, identity, parameters):
    """A cursor binds the complete observed census, context and current filter."""
    limit = parameters.get("limit", 50)
    if type(limit) is not int or not 1 <= limit <= MAX_PAGE_ROWS:
        raise ApplicationError("INVALID_PAGE_LIMIT", f"Select between one and {MAX_PAGE_ROWS} rows.", field="limit")
    query = parameters.get("filter", "")
    if type(query) is not str or len(query) > 256:
        raise ApplicationError("INVALID_FILTER", "Select a filter of at most 256 characters.", field="filter")
    rows = tuple(records)
    material = transport_value({"context_id": request.context_id, "operation": request.operation,
                                "identity": identity, "filter": query, "records": rows})
    fingerprint = sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    selected = rows if not query else tuple(row for row in rows if query.casefold() in json.dumps(
        transport_value(row), sort_keys=True, ensure_ascii=False).casefold())
    cursor, offset = parameters.get("cursor"), 0
    if cursor is not None:
        try:
            if type(cursor) is not str or len(cursor) > 256:
                raise ValueError("cursor size")
            value = load_application_json(base64.b64decode(cursor, altchars=b"-_", validate=True), maximum_bytes=192)
            if type(value) is not dict or set(value) != {"census", "offset"} or value["census"] != fingerprint:
                raise ValueError("cursor scope")
            offset = value["offset"]
            if type(offset) is not int or not 0 <= offset <= len(selected):
                raise ValueError("cursor position")
        except (ValueError, TypeError) as error:
            raise ApplicationError("STALE_OR_INVALID_CURSOR", "The observed census or selection changed. Start from the first page.", field="cursor") from error
    next_offset = offset + limit
    next_cursor = None
    if next_offset < len(selected):
        next_cursor = base64.urlsafe_b64encode(json.dumps({"census": fingerprint, "offset": next_offset},
            sort_keys=True, separators=(",", ":")).encode()).decode()
    return {"rows": list(selected[offset:next_offset]), "total": len(rows), "matching_total": len(selected),
            "returned_count": len(selected[offset:next_offset]), "offset": offset, "limit": limit,
            "next_cursor": next_cursor, "census_sha256": fingerprint, "filter": query}


def projection(*, request, kind, title, identity, scope, summary, records=(), parameters=None, **extra):
    return {"schema": "empirical-lawhood/application/console-projection", "version": PROJECTION_VERSION,
            "context_id": request.context_id, "kind": kind, "title": title, "identity": identity,
            "scope": scope, "summary": summary,
            "page": page(records, request=request, identity=identity, parameters=parameters or dict(request.parameters)),
            **extra}


def execution_projection(report, *, request, parameters):
    rows = report["operational_census"]
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.records.serialization import canonical_json_document_bytes
    diagnostics = {(row["operation"], row["retained_event"]["value"]["object_id"]): row
        for row in report.get("failure_diagnostics", ())}
    if diagnostics:
        projected = []
        for row in rows:
            # Terminal nonattempt rows have synthetic block IDs while their
            # original event has no attempt. Join the exact authenticated event,
            # so an earlier block without an event cannot borrow this cause.
            event = row.get("recovery_event")
            diagnostic = None
            if event is not None:
                candidate = diagnostics.get((row["task_id"], event["value"]["event_id"]))
                if candidate is not None:
                    identity = ObjectIdentity(event["value"]["event_id"], event["schema"], event["version"],
                        sha256(canonical_json_document_bytes(event)).hexdigest())
                    if identity.to_document() == candidate["retained_event"]:
                        diagnostic = candidate
            projected.append({**row, **({"diagnostic": diagnostic} if diagnostic is not None else {})})
        rows = tuple(projected)
    identity = report["execution_plan"]
    latest = {}
    for row in rows:
        key = row["task_id"]
        if key not in latest or (row.get("ordinal") or 0) >= (latest[key].get("ordinal") or 0):
            latest[key] = row
    status_counts = dict(sorted(Counter(row["operational_status"] for row in latest.values()).items()))
    return projection(request=request, kind="execution", title=report["run_id"], identity=identity,
        scope=report["read_scope"], parameters=parameters, records=rows,
        summary={"execution_status": report["status"], "assigned_tasks": report["task_count"],
                 "attempt_records": len(rows), "observed_task_statuses": status_counts,
                 "scientific_completion": report["scientific_completion"],
                 "qualification": report["scientific_qualification"],
                 "new_native_contacts_this_read": report["new_native_contact_count"]},
        provenance={key: report[key] for key in ("execution_plan", "execution_plan_sha256", "recovery_index", "terminal",
            "packet_sha256", "observed_producing_git_head", "producing_code_sha256", "dependency_lock_sha256") if key in report},
        scientific_relationships={"status": "NOT_SUPPLIED_BY_EXECUTION_RECORDS", "requirements": [], "connections": []})


def finding_projection(report, *, request, parameters, identity):
    from empirical_lawhood.science.records.serialization import canonical_json_document_bytes
    records = []
    for record in report["connection_assessments"]:
        value = record["value"]
        records.append({"assessment_id": value["assessment_id"], "disposition": value["disposition"],
            "phase": value["phase"], "requirement": value["requirement"], "connection": value["connection"],
            "reason_codes": value["reason_codes"], "record": record,
            "identity": {"object_id": value["assessment_id"], "object_schema": record["schema"],
                         "object_version": record["version"], "object_fingerprint": sha256(canonical_json_document_bytes(record)).hexdigest()}})
    return projection(request=request, kind="findings", title=report["run_id"], identity=identity,
        scope="EXPLICIT_BOUNDED_RC_SCIENTIFIC_READ", records=records, parameters=parameters,
        summary={"execution_status": report["status"], "assigned_tasks": report["task_count"],
                 "assigned_unit_ids": report["assigned_unit_ids"], "assessment_count": len(records),
                 "dispositions": dict(sorted(Counter(row["disposition"] for row in records).items())),
                 "qualification": report["qualification"], "new_native_contacts_this_read": report["new_native_contact_count"]},
        provenance={key: report[key] for key in ("draft_sha256", "execution_plan_sha256", "packet_sha256",
            "observed_producing_git_head", "producing_code_sha256", "dependency_lock_sha256", "producing_provenance_sha256")},
        evidence_index=report["retained_product_index"],
        value_semantics="Exact canonical records. Execution success does not replace individual scientific dispositions.")
