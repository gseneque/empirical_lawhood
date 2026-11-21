# SPDX-License-Identifier: MPL-2.0
"""Selected original reads and progressively deeper inspection, without a response cache."""

from hashlib import sha256
from pathlib import Path
from datetime import datetime, timezone

from empirical_lawhood.api.application_collection import selected_entry
from empirical_lawhood.api.application_contracts import ApplicationError, ApplicationRequest, absolute_path


def _read(context, request, values, entry):
    from empirical_lawhood.api.application import execute_application
    index = values.get("reader_index", 0)
    readers = entry["value"]["readers"]
    if type(index) is not int or not 0 <= index < len(readers):
        raise ApplicationError("INVALID_READER_INDEX", "Select one declared original reader.")
    selected = readers[index]
    if selected.get("context_id", entry["value"]["context_id"]) != context.context_id:
        raise ApplicationError("CONTEXT_MISMATCH", "Open this locator through its registered engine and custody context.")
    parameters = {key: value for key, value in selected.items() if key not in ("operation", "expected_identity", "context_id")}
    parameters.update({key: values[key] for key in ("cursor", "limit", "filter") if key in values})
    result = execute_application(context, ApplicationRequest(request.request_id, request.context_id,
        selected["operation"], tuple(sorted(parameters.items()))))
    if not result.succeeded:
        error = result.errors[0]
        raise ApplicationError(error.reason_code, error.message, category=error.category, field=error.field)
    body = result.payload
    expected = selected.get("expected_identity", entry["value"]["identity"])
    matches = body.get("identity") == expected
    if selected["operation"] == "sci02d.findings" and expected is not None:
        original = expected["value"]
        matches = ((original["object_schema"], original["object_version"]) == ("empirical-lawhood/runtime/authored-recursive-wave", "1.0.0")
            and body.get("identity", {}).get("packet_sha256") == original["object_fingerprint"]
            and body.get("provenance", {}).get("packet_sha256") == original["object_fingerprint"])
    if expected is not None and not matches:
        raise ApplicationError("ORIGINAL_SELECTION_CHANGED", "The returned original identity differs from this registered locator.")
    return body


def _record(body, key):
    from empirical_lawhood.science.records.serialization import canonical_json_document_bytes
    if key == "projection":
        from empirical_lawhood.api.application_contracts import application_result, response_bytes
        raw = response_bytes(application_result("exploration.original-projection", body))
        return {"record": body, "canonical_text": raw.decode(), "sha256": sha256(raw).hexdigest(),
            "size_bytes": len(raw), "identity": body.get("identity"),
            "scope": "EXACT_APPLICATION_TRANSPORT_NOT_CANONICAL_SCIENTIFIC_RECORD"}
    exploration = body.get("exploration")
    record, identity = None, None
    if exploration is not None:
        node = next((row for row in exploration["nodes"] if row["id"] == key), None)
        if node is not None:
            record, identity = node["record"], node["source"]
    if record is None:
        original = body.get("presentation", {}).get("original_report", {})
        if key in ("result", "assessment", "requirement_graph"):
            record = original.get(key)
    if record is None:
        raise ApplicationError("RECORD_UNAVAILABLE", "This original reader does not supply the selected exact record.")
    raw = canonical_json_document_bytes(record)
    if identity is not None and sha256(raw).hexdigest() != identity["value"]["object_fingerprint"]:
        raise PermissionError("exact record does not match its original identity")
    return {"record": record, "canonical_text": raw.decode(), "sha256": sha256(raw).hexdigest(),
        "size_bytes": len(raw), "identity": identity, "scope": body["scope"], "original_identity": body["identity"]}


def _method_source(body, values, context):
    import ast
    import empirical_lawhood
    from empirical_lawhood.adapters._bounded_files import read_bounded_contained
    selected = next((row for row in body.get("exploration", {}).get("methods", ()) if row["id"] == values["method_id"]), None)
    if selected is None:
        raise ApplicationError("METHOD_UNAVAILABLE", "The selected original presentation has no declared method reference.")
    source = next((row for row in selected["sources"] if row["path"] == values["source_path"]), None)
    protocol = values["source_path"] in selected.get("guides", ())
    if protocol:
        source = {"path": values["source_path"], "symbols": []}
    if source is None:
        raise ApplicationError("UNDECLARED_METHOD_SOURCE", "Select one source declared by this installed presentation.")
    package = Path(empirical_lawhood.__file__).parent
    relative = Path(source["path"])
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != (".md" if protocol else ".py"):
        raise ApplicationError("UNSAFE_METHOD_SOURCE", "Select a declared Python source or scientific protocol.")
    root = package
    if protocol:
        if context.project_root is None:
            raise ApplicationError("SOURCE_REQUIRED", "Select the matching reader source distribution for protocol inspection.")
        from empirical_lawhood.storage.source_origin import require_selected_implementation
        require_selected_implementation(context.project_root)
        root = context.project_root.resolve(strict=True)
    raw = read_bounded_contained(root, root / relative, maximum_bytes=256 * 1024)
    digest = sha256(raw).hexdigest()
    if values.get("expected_source_sha256", digest) != digest:
        raise ApplicationError("METHOD_SOURCE_CHANGED", "The selected method source changed. Reopen its reference.")
    symbols = {} if protocol else {item.name: item.lineno for item in ast.walk(ast.parse(raw))
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    if any(name not in symbols for name in source["symbols"]):
        raise ApplicationError("METHOD_SYMBOL_UNAVAILABLE", "A declared method symbol is absent from this selected installation.")
    if read_bounded_contained(root, root / relative, maximum_bytes=256 * 1024) != raw:
        raise PermissionError("method source changed during inspection")
    return {"method": selected, "source_path": source["path"], "source_text": raw.decode(), "sha256": digest,
        "size_bytes": len(raw), "symbols": [{"name": name, "line": symbols[name]} for name in source["symbols"]],
        "source_scope": "CURRENT_SELECTED_READER_PROTOCOL" if protocol else "CURRENT_SELECTED_READER_IMPLEMENTATION",
        "original_producing_source": body.get("provenance", {}).get("implementation"),
        "original_native_runtime": "NOT_SUPPLIED_BY_THIS_SOURCE_READ"}


def exploration_operation(context, request, values):
    entry, digest = selected_entry(context, values["selection_id"])
    if request.operation == "exploration.execution":
        result = _execution(context, request, values, entry)
        after, current_digest = selected_entry(context, values["selection_id"])
        if after != entry or current_digest != digest:
            raise ApplicationError("COLLECTION_CHANGED", "The collection changed during execution observation.")
        return result
    body = _read(context, request, values, entry)
    if request.operation == "exploration.record":
        result = _record(body, values["record_id"])
    elif request.operation == "exploration.method":
        result = _method_source(body, values, context)
    else:
        result = dict(body)
        result["selection"] = {"selection_id": entry["value"]["selection_id"],
            "investigation_id": entry["value"]["investigation_id"], "classification": entry["value"]["classification"],
            "label": entry["value"]["label"], "question": entry["value"]["question"],
            "original_identity": entry["value"]["identity"],
            "stages": entry["value"]["stages"], "deployment": entry["value"]["deployment"],
            "companion_roles": [row["role"] for row in entry["value"]["companions"]
                if entry["value"]["context_id"] == context.context_id],
            "links": entry["value"]["links"], "metadata_scope": "OPERATOR_SELECTION_NOT_SCIENTIFIC_ASSESSMENT"}
        result["current_reader"] = {"operation": entry["value"]["readers"][values.get("reader_index", 0)]["operation"],
            "observation": "FRESH_OWNING_READ", "collection_sha256": digest,
            "observed_at_utc": datetime.now(timezone.utc).isoformat()}
    after, current_digest = selected_entry(context, values["selection_id"])
    if after != entry or current_digest != digest:
        raise ApplicationError("COLLECTION_CHANGED", "The collection changed during original-result inspection. Reopen the selection.")
    return result


def _execution(context, request, values, entry):
    from empirical_lawhood.api.application import execute_application
    index = values.get("reader_index", 0)
    readers = entry["value"]["readers"]
    if type(index) is not int or not 0 <= index < len(readers):
        raise ApplicationError("INVALID_READER_INDEX", "Select the registered original execution locator.")
    selected = readers[index]
    if selected.get("context_id", entry["value"]["context_id"]) != context.context_id:
        raise ApplicationError("CONTEXT_MISMATCH", "Use the original selected engine for this execution observation.")
    original = selected.get("expected_identity", entry["value"]["identity"])
    if original is not None and original["value"]["object_schema"] != "empirical-lawhood/runtime/authored-recursive-wave":
        raise ApplicationError("LOCAL_EXECUTION_UNAVAILABLE", "This original object is not an authored recursive wave.")
    parameters = {"directory": selected["directory"], **{key: values[key] for key in ("cursor", "limit", "filter") if key in values}}
    response = execute_application(context, ApplicationRequest(request.request_id, context.context_id, "recursive.execution",
        tuple(sorted(parameters.items()))))
    if not response.succeeded:
        error = response.errors[0]
        raise ApplicationError(error.reason_code, error.message, category=error.category, field=error.field)
    body = response.payload
    if original is not None and body.get("provenance", {}).get("packet_sha256") != original["value"]["object_fingerprint"]:
        raise ApplicationError("ORIGINAL_SELECTION_CHANGED", "The execution observation differs from the registered original wave.")
    return {**body, "observed_at_utc": datetime.now(timezone.utc).isoformat(), "original_identity": original,
        "observation_scope": "LOCAL_EXECUTION_METADATA; NO_SCIENTIFIC_RECONSTRUCTION"}


def work_cost_operation(context, request, values):
    from empirical_lawhood.api.application_context import application_storage
    from empirical_lawhood.api.application_contracts import application_result, response_bytes
    from empirical_lawhood.api.application_projections import projection
    from empirical_lawhood.api.work_costs import read_work_cost_account
    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "The cost route accepts exposed operational evidence only.")
    _, _, plane = application_storage(context)
    with plane.read_context() as reader:
        read = read_work_cost_account(directory=absolute_path(values["directory"], "directory"), artifact_writer=reader)
        account = read["account"]
        result = projection(request=request, kind="work-cost", title=account.account_id,
            identity=account.identity.to_document(), scope=account.comparison_scope, summary=read["summary"],
            records=tuple(row.to_document() for row in account.work), parameters=values,
            account=account.to_document(), provenance={"evidence": [row.to_document() for row in account.evidence]},
            value_semantics="Measured work is distinct from billing and prospective estimates. Unknown total cost is not zero.")
        response_bytes(application_result(request.operation, result))
        reader.require_verification_snapshot()
    return result
