# SPDX-License-Identifier: MPL-2.0
"""Historical continuing-source views through the original bounded custody readers."""

from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import ApplicationError, absolute_path, application_result, response_bytes
from empirical_lawhood.api.application_projections import projection
from empirical_lawhood.api.continuing_source import exposed_continuing_store


def continuing_operation(context, request, values):
    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION",
            "Select exposed source history. Protected histories need their owning access route.")
    directory = absolute_path(values["directory"], "directory")
    # Refuse invalid window controls before opening any historical record.
    controls = {key: values.get(key, default) for key, default in (
        ("first_segment", 1), ("segment_count", 1), ("first_boundary", 1), ("boundary_count", 16))}
    if any(type(value) is not int or value < 1 or key.endswith("count") and value > 16
            for key, value in controls.items()):
        raise ApplicationError("INVALID_HISTORY_WINDOW", "Select positive indices and at most sixteen records per window.")
    from empirical_lawhood.science.records.serialization import validate_stable_id
    if request.operation == "continuing.operation":
        validate_stable_id(values["request_id"])
        if len(values["request_id"]) > 512:
            raise ApplicationError("INVALID_FINITE_REQUEST", "Select the original bounded finite request ID.")
    _, _, plane = application_storage(context)
    with plane.read_context() as reader:
        store = exposed_continuing_store(directory=directory, artifact_plane=reader)
        session = store.session
        summary = {"retained_disposition": store.retained_disposition(), "source_generation": session.source_generation,
            "dependence_root": session.dependence_root.to_document(), "scientific_qualification": "NOT_ESTABLISHED",
            "new_native_contacts_this_read": 0, "current_actor_access": "NOT_GRANTED_BY_HISTORY"}
        original = {"session": session.to_document()}
        if request.operation == "continuing.session":
            if "boundary_count" not in values:
                controls["boundary_count"] = min(16, session.maximum_segments - controls["first_boundary"] + 1)
            window = store.read_event_window(controls["first_segment"], controls["segment_count"])
            boundaries = store.read_boundaries(controls["first_boundary"], controls["boundary_count"])
            from empirical_lawhood.science.inquiry.continuing_source import LiveBoundaryKind
            actors = {row.index: store.read_actor_lease(row.selected) for row in boundaries if row.kind is LiveBoundaryKind.ACTOR}
            rows = tuple({"record_kind": "BOUNDARY", "ordinal": row.index, "disposition": row.kind.value,
                "selected_identity": None if row.selected is None else row.selected.to_document(),
                "actor_id": actors[row.index].actor_id if row.index in actors else None,
                "actor_lease": actors[row.index].to_document() if row.index in actors else None,
                "record": row.to_document()} for row in boundaries)
            rows += tuple({"record_kind": "EVENT_SEGMENT", "ordinal": row.index,
                "disposition": "SEQUENCE_GAP" if row.gaps else "RETAINED_SELECTED_SEGMENT",
                "selected_identity": row.identity.to_document(), "record": row.to_document()} for row in window["segments"])
            summary.update(selected_boundary_records=len(boundaries), selected_event_segments=len(window["segments"]),
                complete_selected_event_window=window["complete_selected_window"], whole_session_complete=False,
                event_window_status="COMPLETE_SELECTED_EVENT_WINDOW" if window["complete_selected_window"] else "INCOMPLETE_SELECTED_EVENT_WINDOW")
            original.update(event_window={key: tuple(row.to_document() for row in value)
                if key in ("segments", "sequence_gaps") else value for key, value in window.items()},
                boundaries=tuple(row.to_document() for row in boundaries), selected_windows=controls,
                actor_leases=tuple(row.to_document() for row in actors.values()))
            identity, title = session.identity, session.session_id
        else:
            from empirical_lawhood.execution.continuing_source import LiveOperationReadout
            operation = store.read_operation(values["request_id"])
            if operation is None:
                raise ApplicationError("FINITE_REQUEST_NOT_RETAINED", "The selected original request is not retained.")
            readout = LiveOperationReadout(operation, store.read_effect(operation), store.has_contact(operation))
            original.update(operation=operation.to_document(), receipt=None if readout.receipt is None else readout.receipt.to_document(),
                possible_contact=readout.contacted)
            summary.update(effect_disposition=readout.disposition, finite_requests_selected=1,
                actor_id=operation.actor_lease.actor_id, actor_generations=operation.actor_lease.generations)
            rows = tuple({"record_kind": "FINITE_OPERATION", "field": key, "value": value}
                for key, value in original.items() if key != "session")
            identity, title = operation.identity, operation.request_id
        result = projection(request=request, kind=request.operation, title=title, identity=identity.to_document(),
            scope="EXPOSED_HISTORICAL_SOURCE_INSPECTION", summary=summary, records=rows, parameters=values,
            continuing=original, provenance={"session": session.identity.to_document(), "source": session.source.to_document(),
                "dependence_root": session.dependence_root.to_document()},
            value_semantics="Original history grants no current actor memory, lease or effect. A selected complete window is not complete session history. Unknown effects must not be repeated.")
        response_bytes(application_result(request.operation, result))
        reader.require_verification_snapshot()
    return result
