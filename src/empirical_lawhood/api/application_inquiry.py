# SPDX-License-Identifier: MPL-2.0
"""Selected inquiry clients over the existing decision and successor owners."""

from dataclasses import fields
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_inquiry import identity
from empirical_lawhood.science.records.serialization import canonical_json_document_bytes
from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigins

from empirical_lawhood.api import recursive_inquiry as owner
from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import ApplicationError, absolute_path, application_result, response_bytes
from empirical_lawhood.api.application_projections import projection
from empirical_lawhood.api.application_rc import _input_bytes
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory


def input_bindings(values):
    """Explicit bounded locators; no record identities are derived in the client."""
    text = values.get("text", "")
    if type(text) is not str:
        raise ApplicationError("INVALID_INPUT_BINDINGS", "Select one INPUT_ID=/absolute/path per line.")
    rows = text.splitlines()
    if len(rows) > 16:
        raise ApplicationError("INPUT_BINDING_LIMIT", "Select at most sixteen input bindings.")
    bindings = []
    for row in rows:
        name, separator, path = row.partition("=")
        if not separator or not name or len(name) > 192 or any(c.isspace() for c in name):
            raise ApplicationError("INVALID_INPUT_BINDINGS", "Select one INPUT_ID=/absolute/path per line.")
        bindings.append((name, absolute_path(path, "input_binding")))
    if len({name for name, _ in bindings}) != len(bindings):
        raise ApplicationError("DUPLICATE_INPUT_BINDING", "Each external input can have only one selected path.")
    return tuple(bindings)


def _records(packet, records):
    selected = next(row for row in records["menu.json"].alternatives
        if row.alternative_id == records["decision.json"].selected_alternative_id)
    return {"packet": packet.to_document(), "packet_sha256": packet.fingerprint(),
        "selected_action": selected.action.value, "selected_alternative": selected.to_document(),
        "records": {name: record.to_document() for name, record in records.items()},
        "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}


def _successor(directory, plane):
    admission, packet, records, authored, draft, source = owner.read_inquiry_successor(
        directory=directory, artifact_writer=plane)
    return {"directory": str(directory), "decision_directory": str(Path(plane.root.contract.canonical_path) / admission.decision_relative_path),
        "admission": admission.to_document(), "authored_wave": authored.to_document(),
        "draft": draft.to_document(), "producing_implementation": source.to_document(),
        "execution": "NOT_ENTERED_BY_THIS_READ"}, packet, records


def _read(context, request, values, plane):
    historical = values.get("historical", False)
    if type(historical) is not bool:
        raise ApplicationError("INVALID_BOOLEAN", "Select explicit historical reading.", field="historical")
    successor = None
    directory = absolute_path(values["directory"], "directory")
    if request.operation == "inquiry.successor":
        successor, packet, records = _successor(directory, plane)
        decision_directory = successor["decision_directory"]
    else:
        decision_directory = str(directory)
        packet, records = owner.read_inquiry_decision(directory=directory, artifact_writer=plane,
            revalidate_sources=not historical)
        if "successor_directory" in values:
            if historical:
                raise ApplicationError("CURRENT_ADMISSION_REQUIRED", "Inspect successor admission with a current decision read.")
            successor, parent, _ = _successor(absolute_path(values["successor_directory"], "successor_directory"), plane)
            if parent != packet or successor["decision_directory"] != str(directory):
                raise ValueError("selected successor belongs to another exact decision")
    report = _records(packet, records)
    report.update(decision_directory=decision_directory, successor=successor,
        admission_status="HISTORICAL_ARCHIVE" if historical else "CURRENT_SOURCE_VALIDATED",
        successor_discovery="EXPLICIT_ORIGINAL_LOCATOR_ONLY")
    decision = records["decision.json"]
    summary = {"selected_action": report["selected_action"], "admission_status": report["admission_status"],
        "outcome_id": decision.outcome_id, "successor": "AUTHENTICATED" if successor else "NOT_SELECTED",
        "qualification": "NOT_ESTABLISHED"}
    for name in ("unresolved_target_requirement_ids", "unresolved_target_claim_ids", "unentered_requirement_ids"):
        if hasattr(decision, name):
            summary[name] = getattr(decision, name)
    return projection(request=request, kind="inquiry", title=packet.packet_id,
        identity=identity(packet, packet.packet_id).to_document(), scope=report["admission_status"], summary=summary,
        records=tuple({"member": name, "record": value} for name, value in report["records"].items()),
        parameters=values, inquiry=report, provenance={"original_decision": decision_directory,
            "sources": records["sources.json"].to_document(), "implementation": records["implementation.json"].to_document()},
        value_semantics="Original alternatives, authority, cutoffs, work and costs retain their scope. Historical inspection supplies no current admission. Successor discovery uses an explicitly selected original locator.")


def _review(context, request, values, root, profile, plane):
    selection = {key: value for key, value in values.items() if key != "expected_review_sha256"}
    output = absolute_path(selection["output_dir"], "output_dir")
    preflight_authoring_output_directory(directory=output, repo_root=root, artifact_writer=plane)
    raw_pins = {}

    def read_input(key):
        path = absolute_path(selection[key], key)
        raw = _input_bytes(context, plane, path)
        raw_pins[key] = {"path": str(path), "sha256": sha256(raw).hexdigest(), "size_bytes": len(raw)}
        return raw

    committing = request.operation in ("inquiry.review", "inquiry.commit")
    if committing:
        typed = owner.decode_inquiry_decision_request(read_input("input"))
        arguments = {field.name: getattr(typed, field.name) for field in fields(typed)}
        packet, records = owner.preview_inquiry_decision(**arguments, project_root=root,
            artifact_writer=plane, output_dir=output)
        draft = None
    else:
        from empirical_lawhood.api.configuration import load_configuration_bytes
        origins = decode_canonical_bytes(read_input("origins"), RecursiveInputOrigins, maximum_bytes=None)
        initial = None
        if "initial_draft" in selection:
            initial = load_configuration_bytes(read_input("initial_draft"),
                format=Path(selection["initial_draft"]).suffix, consumer="recursive-inquiry")
        bindings = input_bindings(selection)
        for name, path in bindings:
            raw = _input_bytes(context, plane, path)
            raw_pins["external." + name] = {"path": str(path), "sha256": sha256(raw).hexdigest(), "size_bytes": len(raw)}
        arguments = {"decision_directory": absolute_path(selection["directory"], "directory"), "origins": origins,
            "initial_draft": initial, "supplier_directory": None if "supplier_directory" not in selection else
                absolute_path(selection["supplier_directory"], "supplier_directory"),
            "contribution_dir": None if "contribution_directory" not in selection else
                absolute_path(selection["contribution_directory"], "contribution_directory")}
        packet, records, draft = owner.preview_inquiry_authoring(**arguments, artifact_writer=plane)
        if owner.implementation_binding(root) != records["implementation.json"]:
            raise ValueError("successor requires the original decision implementation")
        arguments["input_bindings"] = bindings
    report = _records(packet, records)
    bindings = {"context": context.to_document(), "profile": profile.to_document(),
        "root": plane.root.contract.to_document(), "selection": selection, "input_bytes": raw_pins,
        "packet_sha256": packet.fingerprint(), "draft": None if draft is None else identity(draft, draft.draft_id).to_document()}
    review = {"status": "REVIEWED_NOT_COMMITTED" if committing else "REVIEWED_NOT_AUTHORED", "selection": selection,
        "review_sha256": sha256(canonical_json_document_bytes(bindings)).hexdigest(), "input_bytes": raw_pins,
        "decision": report, "draft": None if draft is None else draft.to_document(),
        "entry_conditions": "Commitment and authoring repeat the owning checks. No scientific task is launched by this action."}
    return review, arguments, packet


def inquiry_operation(context, request, values):
    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "This inquiry route accepts exposed development custody only.")
    read = request.operation in ("inquiry.read", "inquiry.successor")
    root, profile, plane = application_storage(context, for_write=not read)
    with plane.read_context() as reader:
        if read:
            result = _read(context, request, values, reader)
        else:
            result, arguments, packet = _review(context, request, values, root, profile, reader)
        response_bytes(application_result(request.operation, result))
        reader.require_verification_snapshot()
    if read or request.operation in ("inquiry.review", "inquiry.review-author"):
        return result
    if values["expected_review_sha256"] != result["review_sha256"]:
        raise ApplicationError("REVIEWED_SELECTION_CHANGED", "Review the current request, original inputs, context and destination again.")
    output = absolute_path(values["output_dir"], "output_dir")
    if request.operation == "inquiry.commit":
        packet, records = owner.commit_inquiry_decision(**arguments, project_root=root, artifact_writer=plane,
            output_dir=output, expected_packet_sha256=packet.fingerprint())
        return {"status": "COMMITTED", "decision_directory": str(output), **_records(packet, records), "native_contact": "none"}
    report = owner.author_inquiry_successor(**arguments, project_root=root, artifact_writer=plane,
        output_dir=output, expected_decision_packet_sha256=packet.fingerprint())
    return {**report, "decision_directory": str(arguments["decision_directory"]), "decision_packet_sha256": packet.fingerprint(),
        "execution": "NOT_ENTERED_BY_AUTHORING"}
