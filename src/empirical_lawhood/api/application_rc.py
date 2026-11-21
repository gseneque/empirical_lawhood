# SPDX-License-Identifier: MPL-2.0
"""The selected copied-input and RC lifecycle through existing scientific owners."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.api.application_contracts import ApplicationError, MAX_EDIT_BYTES, absolute_path
from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.rc_workbench import is_bounded_rc_draft, load_bounded_rc, MAX_RC_INSPECTION_DRAFT_BYTES


def _input_root(context, plane, *, for_write=False):
    selected = context.input_root
    if selected is None:
        raise ApplicationError("INPUT_ROOT_REQUIRED", "Select the copied-input directory in this context.", field="input_root")
    from_selected_source = (not for_write and context.project_root is not None
                            and selected.is_relative_to(context.project_root))
    if (not selected.is_dir() or any(path.is_symlink() for path in (selected, *selected.parents))
            or not from_selected_source and selected.stat().st_dev != Path(plane.root.contract.canonical_path).stat().st_dev):
        raise ApplicationError("INPUT_ROOT_UNAVAILABLE", "The copied-input root must be a real directory on the selected storage volume.")
    return selected


def _input_bytes(context, plane, path, *, expected=None, maximum_bytes=MAX_EDIT_BYTES):
    from empirical_lawhood.adapters._bounded_files import read_bounded_contained
    root = _input_root(context, plane)
    raw = read_bounded_contained(root, path, maximum_bytes=maximum_bytes)
    if expected is not None and sha256(raw).hexdigest() != expected:
        raise ApplicationError("REVIEWED_INPUT_CHANGED", "The original input differs from the reviewed bytes. Open it again.", field="input")
    return raw


def _edits(values):
    text = values["text"]
    if type(text) is not str or len(text.encode("utf-8")) > MAX_EDIT_BYTES:
        raise ApplicationError("EDIT_LIMIT", "Select bounded editable text.", field="text")
    format = values.get("format", ".json")
    if format not in (".json", ".yaml", ".yml"):
        raise ApplicationError("UNSUPPORTED_FORMAT", "Select JSON or YAML editable text.", field="format")
    return text.encode("utf-8"), format


def configuration_operation(context, operation, values):
    from empirical_lawhood.api.configuration import ConfigurationError, validate_configuration_bytes, prepare_configuration_bytes
    try:
        if operation == "configuration.validate":
            raw, format = _edits(values)
            return validate_configuration_bytes(raw, format=format, consumer="recursive-inquiry")
        _root, _profile, plane = application_storage(context, for_write=operation == "configuration.prepare")
        path = absolute_path(values["input"], "input")
        original = _input_bytes(context, plane, path, expected=values.get("expected_input_sha256"))
        if operation == "configuration.open":
            # Invalid copied edits remain inspectable and editable. A declaration
            # of another schema never changes this selected consumer.
            try:
                validation = validate_configuration_bytes(original, format=path.suffix, consumer="recursive-inquiry")
            except ConfigurationError as error:
                validation = error.to_document()
            return {"input": str(path), "text": original.decode("utf-8"), "format": path.suffix,
                    "input_sha256": sha256(original).hexdigest(), "input_bytes": len(original),
                    "consumer": "recursive-inquiry", "validation": validation,
                    "original_bytes_preserved": True, "authority_granted": False}
        raw, format = _edits(values)
        if sha256(raw).hexdigest() != values["expected_edit_sha256"]:
            raise ApplicationError("REVIEWED_EDITS_CHANGED", "Validate the current edits before preparation.", field="text")
        output = absolute_path(values["output_file"], "output_file")
        selected = _input_root(context, plane, for_write=True)
        if not output.is_relative_to(selected) or output == selected:
            raise ApplicationError("INPUT_DESTINATION_REFUSED", "Select a fresh file below the copied-input root.", field="output_file")
        # This owner performs exclusive, no-follow publication and preserves the
        # original file. The transport never normalizes scientific numeric text.
        return prepare_configuration_bytes(raw, output, format=format, consumer="recursive-inquiry",
                                           expected_parent_device=selected.stat().st_dev)
    except ConfigurationError as error:
        raise ApplicationError(error.code, str(error), field=error.field) from error


def _selected_draft(raw, format):
    from empirical_lawhood.api.configuration import load_configuration_bytes
    draft = load_configuration_bytes(raw, format=format, consumer="recursive-inquiry")
    if (not is_bounded_rc_draft(draft) or draft.contribution_parents
            or len(draft.canonical_bytes()) > MAX_RC_INSPECTION_DRAFT_BYTES):
        raise ApplicationError("UNSUPPORTED_RC_EFFECT", "Select one bounded exposed RC wave without imported parent contributions.")
    return draft


def rc_lifecycle(context, operation, values):
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, explain_recursive_draft, implementation_binding
    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "The exposed RC lifecycle does not accept protected access selections.")
    root, profile, plane = application_storage(context, for_write=True)
    from empirical_lawhood.execution.experiment_preparation import select_experiment_workers
    from empirical_lawhood.execution.resources.capacity import WorkerSelectionExceedsProfile
    try:
        workers = select_experiment_workers(context.maximum_parallel_tasks,
                                            profile_maximum=profile.maximum_parallel_tasks)
    except WorkerSelectionExceedsProfile as error:
        raise ApplicationError("WORKER_SELECTION_EXCEEDS_PROFILE", "Select a worker count within the operator profile.",
            field="maximum_parallel_tasks") from error
    if operation in ("rc.prepare", "recursive.author"):
        path = absolute_path(values["input"], "input")
        raw = _input_bytes(context, plane, path, expected=values["expected_input_sha256"])
        draft = _selected_draft(raw, path.suffix)
        # Retain a bounded validated snapshot when an invocation destination is
        # selected; the same composition is used by the legacy terminal client.
        from empirical_lawhood.api.invocation_retention import attempt_input
        attempt_input(path, maximum_bytes=MAX_RC_INSPECTION_DRAFT_BYTES,
            consumer="recursive-inquiry", role="authoring_input", expected_sha256=values["expected_input_sha256"])
        if operation == "rc.prepare":
            source = implementation_binding(root)
            return {**explain_recursive_draft(draft), "input": str(path),
                "input_sha256": values["expected_input_sha256"],
                "implementation": source.to_document(), "implementation_sha256": source.fingerprint(),
                "maximum_parallel_tasks": workers,
                "entry_requirements": {
                    "software": "Reviewed implementation is rechecked by the authoring owner.",
                    "input": "Exact copied input is bound; changing it requires a new preparation.",
                    "resources": "Actual worker capacity and native resources are admitted at execution entry.",
                    "authority": "Exposed development only; preparation creates no scientific qualification."}}
        return author_recursive_wave(draft=draft, project_root=root, artifact_writer=plane,
            output_dir=absolute_path(values["output_dir"], "output_dir"),
            expected_implementation_sha256=values["expected_implementation_sha256"])
    directory = absolute_path(values["directory"], "directory")
    packet, _draft, _source, _payloads = load_bounded_rc(directory=directory, plane=plane)
    if packet.fingerprint() != values["expected_packet_sha256"]:
        raise ApplicationError("REVIEWED_PACKET_CHANGED", "Inspect the original authored package before run or recovery.")
    from empirical_lawhood.api.recursive_execution import run_recursive_wave
    return run_recursive_wave(directory=directory, project_root=root, artifact_writer=plane,
        terminal_product_format=values.get("terminal_product_format", "documents"),
        maximum_parallel_tasks=workers,
        expected_packet_sha256=values["expected_packet_sha256"])
