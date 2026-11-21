# SPDX-License-Identifier: MPL-2.0
"""Explicit composite clients over registered preparation and component owners."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_document_bytes
from empirical_lawhood.execution.experiment_preparation import select_experiment_workers
from empirical_lawhood.execution.operational_configuration import scientific_reconstruction_operation, ScientificReconstructionMode

from empirical_lawhood.api.application_context import application_programme, application_storage
from empirical_lawhood.api.application_contracts import ApplicationError, absolute_path, application_result, response_bytes
from empirical_lawhood.api.application_projections import projection
from empirical_lawhood.api.application_rc import _input_bytes
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.composite_experiment_programme import read_experiment_programme_descriptor


MAX_PROGRAMME_INPUT_BYTES = 1024 * 1024


def _input(context, plane, path, pins, name):
    raw = _input_bytes(context, plane, path, maximum_bytes=MAX_PROGRAMME_INPUT_BYTES)
    pins[name] = {"path": str(path), "sha256": sha256(raw).hexdigest(), "size_bytes": len(raw)}
    return raw


def _preparation(context, values, service, pins):
    from empirical_lawhood.api.codecs import loads_registered_authoring
    from empirical_lawhood.api.experiment_preparation import experiment_protocols, load_experiment_inputs
    from empirical_lawhood.execution.experiment_preparation import ExecutionSelection
    from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding

    plane = service.artifact_writer
    path = absolute_path(values["input"], "input")
    raw = _input(context, plane, path, pins, "input")
    media = {".json": "application/json", ".yaml": "application/yaml", ".yml": "application/yaml"}.get(path.suffix)
    if media is None:
        raise ApplicationError("UNSUPPORTED_FORMAT", "Select a copied JSON or YAML programme specification.")
    declarations = tuple(value for value in experiment_protocols() if value.programme_record_type is not None)
    specification = loads_registered_authoring(raw.decode("utf-8"), media_type=media,
        root_schemas={(value.specification_type.SCHEMA, value.specification_type.VERSION): value.specification_type
            for value in declarations}, maximum_bytes=MAX_PROGRAMME_INPUT_BYTES)
    snapshot = absolute_path(values["source_snapshot"], "source_snapshot")
    source = loads_registered_authoring(_input(context, plane, snapshot, pins, "source_snapshot").decode("utf-8"),
        media_type="application/json", root_schemas={RecursiveImplementationBinding.SCHEMA: RecursiveImplementationBinding},
        maximum_bytes=MAX_PROGRAMME_INPUT_BYTES)
    selection = absolute_path(values["sources"], "sources")
    _input(context, plane, selection, pins, "sources")
    resolved = load_experiment_inputs(specification, selection, artifact_writer=plane)
    protocol = None if "protocol" not in values else _input(context, plane,
        absolute_path(values["protocol"], "protocol"), pins, "protocol")
    execution = ExecutionSelection(workers=context.maximum_parallel_tasks, environment_id=values["environment_id"],
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", source),
        output_root=plane.root.contract.canonical_path)
    preparation = service.prepare(specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, protocol_bytes=protocol, execution=execution)
    if preparation.programme is None:
        raise ApplicationError("COMPOSITE_REQUIRED", "Select a registered composite programme.")
    return preparation


def _descriptor(service, directory):
    record = read_experiment_programme_descriptor(service=service, directory=directory)
    if record is None:
        raise ApplicationError("COMPOSITE_REQUIRED", "Select the original registered programme descriptor.")
    return record


def _selection(values):
    return {key: value for key, value in values.items() if key != "expected_review_sha256"}


def _review(context, values, root, profile, plane, service, *, authoring):
    selection = _selection(values)
    pins = {}
    if authoring:
        output = absolute_path(selection["output_dir"], "output_dir")
        preflight_authoring_output_directory(directory=output, repo_root=root, artifact_writer=plane)
        operand = _preparation(context, selection, service, pins)
        report = service.explain(operand)
        arguments = {"preparation": operand, "output_dir": output}
        action = "AUTHOR"
    else:
        action = selection["action"]
        if action not in ("RUN", "RECOVER"):
            raise ApplicationError("UNSUPPORTED_PROGRAMME_ACTION", "Select RUN or RECOVER explicitly.")
        directory = absolute_path(selection["directory"], "directory")
        operand = _descriptor(service, directory)
        request_path = context.programme_request_path
        if "programme_request" in selection:
            request_path = absolute_path(selection["programme_request"], "programme_request")
        if request_path is not None:
            _input(context, plane, request_path, pins, "programme_request")
        report = {"descriptor": operand.to_document(), "component_admission": "CHECKED_BY_OWNER_AT_ENTRY",
            "scientific_result": "NOT_READ_BY_REVIEW", "native_contact": "NONE"}
        arguments = {"directory": directory, "programme_request_path": request_path,
            "maximum_parallel_tasks": context.maximum_parallel_tasks, "confirmed": True}
    bindings = {"context": context.to_document(), "profile": profile.to_document(),
        "root": plane.root.contract.to_document(), "action": action, "selection": selection,
        "input_bytes": pins, "owning_review": report}
    for pin in pins.values():
        _input_bytes(context, plane, Path(pin["path"]), expected=pin["sha256"],
            maximum_bytes=MAX_PROGRAMME_INPUT_BYTES)
    return {"status": "REVIEWED_NOT_ENTERED", "action": action, "selection": selection,
        "review_sha256": sha256(canonical_json_document_bytes(bindings)).hexdigest(),
        "input_bytes": pins, "owning_review": report,
        "entry_conditions": "The original owner rechecks source, inputs, resource and component authority. This review supplies no execution or reveal authority."}, arguments


def programme_operation(context, request, values):
    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "Select the programme's original component authority request.")
    effect = request.operation in ("programme.author", "programme.apply")
    root, profile, plane = application_storage(context, for_write=effect)
    if request.operation != "programme.read":
        select_experiment_workers(context.maximum_parallel_tasks, profile_maximum=profile.maximum_parallel_tasks)
    with plane.read_context() as reader:
        service = application_programme(context, root=root, profile=profile, plane=reader)
        if request.operation == "programme.read":
            if type(values.get("allow_partial", False)) is not bool:
                raise ApplicationError("INVALID_BOOLEAN", "Select partial reading explicitly.")
            directory = absolute_path(values["directory"], "directory")
            descriptor = _descriptor(service, directory)
            with scientific_reconstruction_operation(ScientificReconstructionMode.OFF):
                report = service.read(directory=directory, programme_request_path=context.programme_request_path,
                    allow_partial=values.get("allow_partial", False))
            rows = tuple({"member": "phases[" + str(index) + "]", "record": row}
                for index, row in enumerate(report.get("phases", ()))) or tuple(
                    {"member": key, "record": value} for key, value in report.items())
            result = projection(request=request, kind="composite", title=descriptor.programme.object_id,
                identity=descriptor.programme.to_document(), scope="ORIGINAL_PROGRAMME_READ",
                summary={"protocol": descriptor.protocol_id, "state": report.get("state", "NOT_REPORTED"),
                    "scientific_qualification": report.get("scientific_qualification", "NOT_ESTABLISHED")},
                records=rows, parameters=values, programme=report, descriptor=descriptor.to_document(),
                frontier=report.get("frontier"), dependencies=report.get("dependencies"),
                value_semantics="Component, task and scientific-unit counts retain their own original scopes. Missing children are not fabricated.")
            if _descriptor(service, directory) != descriptor:
                raise PermissionError("Programme descriptor changed during original read")
        else:
            authoring = request.operation in ("programme.prepare", "programme.author")
            result, arguments = _review(context, values, root, profile, reader, service, authoring=authoring)
            # Refuse an undisplayable review before authoring or execution entry.
            response_bytes(application_result(request.operation, result))
            reader.require_verification_snapshot()
            if effect:
                if values["expected_review_sha256"] != result["review_sha256"]:
                    raise ApplicationError("REVIEW_CHANGED", "Review the current programme selection before entry.")
                selected = application_programme(context, root=root, profile=profile, plane=plane)
                action = result["action"]
                report = getattr(selected, {"AUTHOR": "author", "RUN": "run", "RECOVER": "recover"}[action])(**arguments)
                return {"status": "OWNER_RETURNED", "action": action, "report": report,
                    "review_sha256": result["review_sha256"], "scientific_authority": "ORIGINAL_COMPONENT_OWNERS_ONLY"}
        response_bytes(application_result(request.operation, result))
        reader.require_verification_snapshot()
        return result
