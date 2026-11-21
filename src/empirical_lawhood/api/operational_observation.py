# SPDX-License-Identifier: MPL-2.0
"""Compose original operational readers and expose only verified local observations."""

from datetime import datetime, timezone
from pathlib import Path

from empirical_lawhood.storage.operational_observation import export_snapshot, import_snapshot, read_retained_observation, read_selected_pin, read_supervision
from empirical_lawhood.execution.deployment_budget import DeploymentAllocation
from empirical_lawhood.execution.operational_observation import RETURN_STAGES, SNAPSHOT_SCHEMA, VERSION, document, document_bytes, fields, observation_age, unavailable_domain, validate_domain, validate_selection, validate_snapshot
from empirical_lawhood.api.application_collection import selected_entry
from empirical_lawhood.api.application_contracts import ApplicationError, absolute_path
from empirical_lawhood.api.application_state import operational_state_store


def registered_binding(entry):
    row = entry["value"]
    selected = row["deployment"]
    if selected is None:
        raise ApplicationError("DEPLOYMENT_NOT_SELECTED", "This investigation has no selected remote observation.")
    return {**{name: selected[name] for name in ("deployment_id", "run_id", "packet_sha256", "controller_source_sha256", "worker_source_sha256")},
        "allocation_sha256": selected["allocation"]["sha256"], "job_card_sha256": selected["job_card"]["sha256"],
        "investigation_id": row["investigation_id"], "selection_id": row["selection_id"]}


def _identity(value):
    original = value["value"] if type(value) is dict and "value" in value else value
    return {"schema": original["object_schema"], "version": original["object_version"],
        "object_id": original["object_id"], "fingerprint": original["object_fingerprint"]}


def native_progress_record(store, definition):
    """Use the read-only native owner; receipt metadata is not verified force data."""
    from empirical_lawhood.execution.native_subwork import NativeSubworkUncertainContact
    base = {"task_id": definition.parent_contact.task_id, "attempt_id": definition.parent_contact.attempt_id,
        "subwork_id": definition.subwork_id, "declared_outputs": len(definition.outputs),
        "source": _identity(definition.identity.to_document())}
    try:
        observed = store.inspect_metadata(definition)
    except NativeSubworkUncertainContact:
        return {**base, "state": "UNKNOWN_CONTACT", "entry": "UNKNOWN", "raw_return": "UNKNOWN",
            "publication": "UNAVAILABLE", "completion_receipt": "UNAVAILABLE", "published_outputs": 0}
    return {**base, "state": ("RECEIPT_METADATA_PRESENT" if observed.receipt is not None else
        "CONTACT_UNRESOLVED" if observed.call_entry is not None else "ENTRY_NOT_OBSERVED"),
        "entry": "OBSERVED" if observed.call_entry is not None else "NOT_OBSERVED",
        "raw_return": "OBSERVED" if observed.call_return is not None else "NOT_OBSERVED",
        "publication": ("COMPLETE_METADATA_CENSUS" if len(observed.outputs) == len(definition.outputs)
            and observed.completion is not None else "PARTIAL" if observed.outputs or observed.partial_outputs else "NOT_OBSERVED"),
        "completion_receipt": observed.receipt.operational_status.value if observed.receipt is not None else "NOT_OBSERVED",
        "published_outputs": len(observed.outputs)}


def _native_metadata(reader, plan, index, source, selection):
    from empirical_lawhood.storage.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.science.identity.provenance import ObjectIdentity

    parent_store = ExternalNativeEffectContactStore(plane=reader,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    references = []
    for task in plan.tasks:
        parent = parent_store.read(index.run_id, task.task_id)
        if parent is None:
            continue
        if (parent.execution_task != ObjectIdentity.from_record(task.task_id, task)
                or parent.implementation_commit != plan.implementation_commit
                or parent.attempt_id not in {attempt.attempt_id for attempt in index.task(task.task_id).attempts}):
            raise PermissionError("native observation substitutes its original task, source or attempt")
        store = ExternalNativeSubworkStore(plane=reader, parent_contacts=parent_store,
            parent_contact=parent, completed_only=True)
        for roster in store.iter_rosters(parent):
            for original in roster.subworks:
                references.append((store, original))
                if len(references) > 4096:
                    raise ValueError("native observation exceeds its selected metadata census")
    start, limit = selection["native_offset"], selection["row_limit"]
    records = []
    for store, original in references[start:start + limit]:
        definition = store.read_definition(original)
        if (definition.code_sources_sha256, definition.dependency_lock_sha256) != (
                source.code_sources_sha256, source.dependency_lock_sha256):
            raise PermissionError("native observation substitutes its original producing source")
        records.append(native_progress_record(store, definition))
    return {"total": len(references), "offset": start, "rows": records,
        "coverage": "COMPLETE_METADATA_WINDOW" if start == 0 and len(records) == len(references) else "PARTIAL_METADATA_WINDOW",
        "body_validation": "DEFERRED_TO_ORIGINAL_READER"}


def _observe_execution(context, selection):
    from empirical_lawhood.api.application_context import application_storage
    from empirical_lawhood.api.experiment_execution_read import load_development_execution_controls, read_execution_records
    from empirical_lawhood.api.selected_e3_access import original_e3_authority_read_context
    _, _, plane = application_storage(context)
    with original_e3_authority_read_context(plane), plane.read_context() as reader:
        packet, _, plan, index, source, access = load_development_execution_controls(
            directory=Path(selection["directory"]), artifact_writer=reader)
        # This export is exposed operational metadata, never an access-verdict cache.
        if access is not None:
            raise ApplicationError("PROTECTED_OBSERVATION_UNSUPPORTED", "Use the original current-access reader for protected custody.")
        if (packet.fingerprint(), index.run_id) != (selection["binding"]["packet_sha256"], selection["binding"]["run_id"]):
            raise PermissionError("execution observation substitutes its selected original wave")
        report = read_execution_records(writer=reader, plan=plan, index=index)
        start, limit = selection["task_offset"], selection["row_limit"]
        records = [{name: row.get(name) for name in ("task_id", "attempt_id", "ordinal", "operational_status", "receipt_id")}
            for row in report["operational_census"][start:start + limit]]
        execution = {"status": report["status"], "run_id": report["run_id"], "task_count": report["task_count"],
            "attempt_count": len(report["operational_census"]), "offset": start, "rows": records,
            "source": _identity(report["execution_plan"]), "producing_code_sha256": source.code_sources_sha256,
            "dependency_lock_sha256": source.dependency_lock_sha256, "producing_commit": plan.implementation_commit}
        native = _native_metadata(reader, plan, index, source, selection)
        domain = unavailable_domain(selection["binding"])
        chosen = selection["domain_panel"]
        if chosen is not None:
            from empirical_lawhood.api.application_presentations import application_presentations
            selected = next((row for row in application_presentations() if row.panel_id == chosen["panel_id"]), None)
            if (selected is not None and selected.version == chosen["panel_version"] and selected.observe is not None
                    and selected.observation_version == chosen["observation_version"] == VERSION):
                domain = validate_domain(selected.observe(context=context, directory=Path(selection["directory"]),
                    artifact_writer=reader, selection=selection))
        reader.require_verification_snapshot()
    return execution, native, domain


def collect_observation(context, selection_pin, *, collector_id, sequence, previous_snapshot_sha256=None,
                        output_directory, now=None):
    """Read one original metadata window and publish it without provider contact."""
    if context.read_access_paths:
        raise ApplicationError("PROTECTED_OBSERVATION_UNSUPPORTED", "Select exposed operational metadata, with no retained protected result bodies.")
    if context.input_root is None:
        raise ApplicationError("INPUT_ROOT_REQUIRED", "Select the observer input root explicitly.")
    path = absolute_path(selection_pin["path"], "selection.path")
    path.relative_to(context.input_root)
    selection_raw = read_selected_pin(selection_pin, maximum_bytes=128 * 1024)
    selection = validate_selection(document(selection_raw, maximum_bytes=128 * 1024))
    allocation_raw = read_selected_pin(selection["allocation"])
    allocation = DeploymentAllocation.from_document(document(allocation_raw, maximum_bytes=128 * 1024))
    if allocation.deployment_id != selection["binding"]["deployment_id"]:
        raise PermissionError("collector allocation differs from its original deployment binding")
    job_raw = read_selected_pin(selection["job_card"])
    job = document(job_raw, maximum_bytes=128 * 1024)
    observation = fields(job.get("observation"), ("cadence_seconds", "stale_after_seconds", "controller_source_sha256", "worker_source_sha256", "selected_gpu"))
    if any(observation[name] != selection[name] for name in ("cadence_seconds", "stale_after_seconds")) or any(
            observation[name] != selection["binding"][name] for name in ("controller_source_sha256", "worker_source_sha256")):
        raise PermissionError("collector cadence or source differs from its selected job card")
    execution, native, domain = _observe_execution(context, selection)
    observed_runtime = domain.get("runtime")
    financial = read_supervision(selection["supervisors"], allocation)
    snapshot = {"schema": SNAPSHOT_SCHEMA, "version": VERSION, "binding": selection["binding"],
        "selection_sha256": selection_pin["sha256"], "collector_id": collector_id, "sequence": sequence,
        "previous_snapshot_sha256": previous_snapshot_sha256,
        "source_observed_utc": now or datetime.now(timezone.utc).isoformat(),
        "cadence_seconds": selection["cadence_seconds"], "stale_after_seconds": selection["stale_after_seconds"],
        "execution": execution, "native": native, "financial": financial, "domain": domain,
        "runtime": {"provider": "Runpod", "selected_gpu": observation["selected_gpu"], "observed_gpu": None,
            "utilisation": None, "memory": None, "process": None, "native_phase": None,
            "scope": "SELECTED_RESOURCES; NO_CURRENT_GPU_TELEMETRY_SUPPLIED"},
        "return": {"terminal": False, "stages": [{"stage": stage, "status": "UNAVAILABLE", "source": None,
            "scope": "A_SNAPSHOT_IS_NOT_AN_ORIGINAL_EVIDENCE_RETURN"} for stage in RETURN_STAGES]},
        "errors": [], "provider_calls": 0, "native_calls": 0, "lifecycle_actions": 0, "scientific_authority": "NONE"}
    if observed_runtime is not None:
        from empirical_lawhood.execution.operational_observation import RUNTIME_FIELDS
        snapshot["runtime"].update({name: observed_runtime[name] for name in RUNTIME_FIELDS})
        snapshot["runtime"].update(observation=observed_runtime, scope="SOURCE_BOUND_DOMAIN_RUNTIME_OBSERVATION")
    validate_snapshot(snapshot)
    for pin, raw in ((selection_pin, selection_raw), (selection["allocation"], allocation_raw), (selection["job_card"], job_raw)):
        if read_selected_pin(pin) != raw:
            raise PermissionError("collector source changed before observation publication")
    if context.observation_root is None:
        raise ApplicationError("OBSERVATION_ROOT_REQUIRED", "Select the guarded observation destination.")
    target = absolute_path(output_directory, "output_directory")
    target.relative_to(context.observation_root)
    state = operational_state_store(context, path=context.observation_root / "observer-state.json")
    if not state.writable:
        raise PermissionError("the selected observer profile is read-only")
    return export_snapshot(snapshot, root=state.root, output_directory=target)


def observation_operation(context, request, values):
    if context.read_access_paths:
        raise ApplicationError("PROTECTED_OBSERVATION_UNSUPPORTED", "This exposed observation route has no protected-data export authority.")
    entry, collection_digest = selected_entry(context, values["selection_id"])
    if entry["value"]["context_id"] != context.context_id:
        raise ApplicationError("CONTEXT_MISMATCH", "Open this observation through its registered context.")
    binding = registered_binding(entry)
    allocation_pin = entry["value"]["deployment"]["allocation"]
    allocation_raw = read_selected_pin(allocation_pin)
    allocation = DeploymentAllocation.from_document(document(allocation_raw, maximum_bytes=128 * 1024))
    if allocation.deployment_id != binding["deployment_id"]:
        raise PermissionError("observation changes the registered allocation's deployment")
    if request.operation == "observation.record-return":
        from empirical_lawhood.api.observation_return import record_return
        return record_return(context, request, values, entry=entry, binding=binding)
    path = absolute_path(entry["value"]["deployment"]["observation_path"], "observation_path")
    if context.observation_root is None:
        raise ApplicationError("OBSERVATION_ROOT_REQUIRED", "Select the explicit local observation root.")
    path.relative_to(context.observation_root)
    store = operational_state_store(context, path=path)
    if request.operation == "observation.import":
        directory = absolute_path(values["directory"], "directory")
        if context.input_root is None:
            raise ApplicationError("INPUT_ROOT_REQUIRED", "Select the incoming transfer root.")
        directory.relative_to(context.input_root)
        return import_snapshot(directory, expected_manifest_sha256=values["expected_manifest_sha256"],
            expected_binding=binding, expected_allocation=allocation.to_document(), store=store,
            expected_current_sha256=values.get("expected_current_sha256"),
            restart_from_snapshot_sha256=values.get("restart_from_snapshot_sha256"))
    state_digest, retained = read_retained_observation(store)
    if retained is None:
        return {"schema": "empirical-lawhood/application/observation", "version": VERSION,
            "status": "NOT_YET_RETURNED", "binding": binding, "state_sha256": None, "snapshot": None,
            "scientific_authority": "NONE", "provider_calls": 0, "native_calls": 0, "lifecycle_actions": 0}
    snapshot = retained["snapshot"]
    if snapshot["binding"] != binding:
        raise PermissionError("retained observation differs from the registered original work")
    if snapshot["financial"]["allocation"] != allocation.to_document() or read_selected_pin(allocation_pin) != allocation_raw:
        raise PermissionError("retained observation changes its original allocation body")
    after, current_digest = selected_entry(context, values["selection_id"])
    if after != entry or current_digest != collection_digest or store.read() != document_bytes(retained):
        raise ApplicationError("OBSERVATION_CHANGED", "The selected observation changed during this read. Reopen it.")
    from empirical_lawhood.api.observation_return import read_return
    returning = read_return(context, entry=entry, binding=binding)
    age = observation_age(snapshot)
    from empirical_lawhood.execution.deployment_budget import utc
    money = snapshot["financial"]["accounting"]
    money_age = None if money is None else max(0, int((datetime.now(timezone.utc) - utc(money["observed_utc"])).total_seconds()))
    return {"schema": "empirical-lawhood/application/observation", "version": VERSION,
        "status": "STALE" if age["stale"] else "OBSERVED", "binding": binding,
        "state_sha256": state_digest, "snapshot_sha256": retained["snapshot_sha256"], "snapshot": snapshot,
        "received_utc": retained["received_utc"], "sequence_gap": retained["sequence_gap"], **age,
        "local_return": returning,
        "accounting_age_seconds": money_age, "accounting_stale": money_age is None or money_age > snapshot["stale_after_seconds"],
        "scientific_authority": "NONE", "provider_calls": 0, "native_calls": 0, "lifecycle_actions": 0}
