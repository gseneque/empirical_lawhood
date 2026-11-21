# SPDX-License-Identifier: MPL-2.0
"""Explicit companion reads with original identity joins and one closing byte check."""

from datetime import datetime, timezone
from decimal import Decimal
import json

from empirical_lawhood.api.application_collection import selected_entry
from empirical_lawhood.api.application_contracts import ApplicationError, ApplicationRequest, _invalid_number, _unique, absolute_path, application_result, response_bytes


def _primary(context, entry, reader, index):
    from empirical_lawhood.api.application_presentations import application_presentations
    rows = entry["value"]["readers"]
    if type(index) is not int or not 0 <= index < len(rows):
        raise ApplicationError("INVALID_READER_INDEX", "Select the registered original presentation.")
    selected = rows[index]
    if selected.get("context_id", entry["value"]["context_id"]) != context.context_id:
        raise ApplicationError("CONTEXT_MISMATCH", "Open this locator through its registered engine and custody context.")
    if selected["operation"] != "presentation.read":
        raise ApplicationError("COMPANION_JOIN_UNAVAILABLE", "This reader has no registered companion join. Open its original records separately.")
    declaration = next((item for item in application_presentations() if item.panel_id == selected["panel_id"]), None)
    if declaration is None or declaration.version != selected["panel_version"]:
        raise ApplicationError("COMPANION_JOIN_UNAVAILABLE", "Select the supported presentation revision before combining companion summaries.")
    data = declaration.read(context=context, directory=absolute_path(selected["directory"], "directory"), artifact_writer=reader)
    data.__post_init__()
    if data.identity != selected.get("expected_identity", entry["value"]["identity"]):
        raise ApplicationError("ORIGINAL_SELECTION_CHANGED", "The selected original identity changed before the companion read.")
    return data, declaration.panel_id


def _cost(companion, primary, reader):
    from empirical_lawhood.api.work_costs import read_work_cost_account
    cost = read_work_cost_account(directory=absolute_path(companion["directory"], "directory"), artifact_writer=reader)
    if cost["account"].identity.to_document() != companion["identity"]:
        raise PermissionError("selected work account changes its original identity")
    subjects = [row.subject.to_document() for row in cost["account"].work]
    receipts = primary.provenance.get("product_receipts", ())
    if not receipts or any(receipt not in subjects for receipt in receipts):
        raise PermissionError("work account omits the selected root's actual producing receipts")
    return cost


def companion_operation(context, request, values):
    from empirical_lawhood.api.application_context import application_storage
    from empirical_lawhood.api.application_inquiry import _read as read_inquiry
    from empirical_lawhood.api.application_rc import _input_bytes
    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "This companion join accepts exposed original results only.")
    entry, digest = selected_entry(context, values["selection_id"])
    if entry["value"]["context_id"] != context.context_id:
        raise ApplicationError("COMPANION_CONTEXT_REQUIRED", "Open companions through the collection entry's registered custody context.")
    companions = {row["role"]: row for row in entry["value"]["companions"]}
    summary_only = request.operation == "exploration.summary"
    roles = (tuple(role for role in ("inquiry", "work-cost", "acquisition", "cost-observations") if role in companions)
        if summary_only else (values["role"],))
    if any(role not in companions for role in roles):
        raise ApplicationError("COMPANION_NOT_SELECTED", "Select this original companion in the operational collection first.")
    _, _, plane = application_storage(context)
    with plane.read_context() as reader:
        primary, panel = _primary(context, entry, reader, values.get("reader_index", 0))
        result = {"original_identity": primary.identity, "companions": {}, "missing": [],
            "observed_at_utc": datetime.now(timezone.utc).isoformat(), "scientific_authority": "NONE"}
        cost = None
        if any(role in roles for role in ("work-cost", "acquisition", "cost-observations")):
            if "work-cost" not in companions or "directory" not in companions["work-cost"]:
                raise ApplicationError("COST_ACCOUNT_REQUIRED", "Select the original cost account before reading its related attachments.")
            cost = _cost(companions["work-cost"], primary, reader)
        attachments = []
        for role in roles:
            selected = companions[role]
            if "attachment" in selected:
                pin = selected["attachment"]
                path = absolute_path(pin["path"], "attachment.path")
                raw = _input_bytes(context, reader, path, expected=pin["sha256"], maximum_bytes=1024**2)
                attachment = json.loads(raw, object_pairs_hook=_unique, parse_float=Decimal, parse_constant=_invalid_number)
                if panel != "rubisco.initial-root":
                    raise ApplicationError("ATTACHMENT_JOIN_UNAVAILABLE", "This domain has no installed attachment join.")
                from empirical_lawhood.api.domain_composition.rubisco_response.application_companions import validate_attachment
                validate_attachment(role, attachment, primary=primary, cost=cost)
                attachments.append((path, raw, pin))
                projected = {"scope": "CHECKSUMMED_AUDIT_ATTACHMENT_WITH_ORIGINAL_JOINS", "pin": pin, "data": attachment}
                if not summary_only:
                    projected["original_text"] = raw.decode()
                result["companions"][role] = projected
            elif role == "inquiry":
                parameters = {"directory": selected["directory"], "limit": 200}
                inquiry = read_inquiry(context, ApplicationRequest(request.request_id, context.context_id, "inquiry.read"), parameters, reader)
                sources = inquiry["inquiry"]["records"]["sources.json"]["value"]["waves"]
                if (inquiry["identity"] != selected["identity"]
                        or not any(row["value"]["packet"] == primary.identity for row in sources)):
                    raise PermissionError("inquiry companion does not name the selected original wave")
                result["companions"][role] = ({"identity": inquiry["identity"], "summary": inquiry["summary"],
                    "scope": inquiry["scope"]} if summary_only else inquiry)
            elif role == "work-cost":
                result["companions"][role] = {"identity": cost["account"].identity.to_document(), "summary": cost["summary"],
                    **({} if summary_only else {"account": cost["account"].to_document()})}
            elif role == "contribution":
                from empirical_lawhood.api.recursive_contributions import inspect_recursive_contribution
                from empirical_lawhood.science.identity.provenance import ObjectIdentity
                from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
                from empirical_lawhood.science.records.decoding import decode_canonical_record
                report = inspect_recursive_contribution(directory=absolute_path(selected["directory"], "directory"), artifact_writer=reader)
                manifest = decode_canonical_record(report["contribution"], ContributionManifest)
                if (ObjectIdentity.from_record(manifest.contribution_id, manifest).to_document() != selected["identity"]
                        or report["producing_run_id"] != primary.provenance.get("run_id")):
                    raise PermissionError("contribution substitutes its original producing wave")
                result["companions"][role] = report
            elif role == "assessment" and panel == "rubisco.initial-root":
                from empirical_lawhood.api.domain_composition.rubisco_response.application_companions import read_assessment
                result["companions"][role] = read_assessment(selected, primary=primary, artifact_writer=reader)
            else:
                raise ApplicationError("COMPANION_READER_UNAVAILABLE", "Use this companion's original reader with its complete source selections.")
        result["missing"] = [role for role in ("inquiry", "work-cost", "acquisition") if role not in companions]
        for path, raw, pin in attachments:
            if _input_bytes(context, reader, path, expected=pin["sha256"], maximum_bytes=1024**2) != raw:
                raise PermissionError("selected audit attachment changed during projection")
        after, current_digest = selected_entry(context, values["selection_id"])
        if after != entry or current_digest != digest:
            raise ApplicationError("COLLECTION_CHANGED", "The collection changed during this companion read.")
        response_bytes(application_result(request.operation, result))
        reader.require_verification_snapshot()
    return result
