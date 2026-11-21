# SPDX-License-Identifier: MPL-2.0
"""One selected application boundary for CLI and local workbench clients."""

from dataclasses import asdict
from decimal import Decimal
from hashlib import sha256
import json

from empirical_lawhood.api.application_contracts import ApplicationContext, ApplicationError, ApplicationRequest, MAX_TEXT_BYTES, absolute_path, application_result, error_result, exact_mapping
from empirical_lawhood.api.application_context import application_programme, application_read_access, application_storage
from empirical_lawhood.api.application_operations import application_operation, application_operations
from empirical_lawhood.api.application_projections import execution_projection, projection
from empirical_lawhood.api.results import ApiResult, ErrorCategory


def _parameters(request):
    descriptor = application_operation(request.operation)
    values = dict(request.parameters)
    exact_mapping(values, descriptor.parameters, required=descriptor.required_parameters, field="parameters")
    for name in ("allow_partial",):
        if name in values and type(values[name]) is not bool:
            raise ApplicationError("INVALID_BOOLEAN", "Select an explicit boolean.", field=name)
    from empirical_lawhood.science.records.serialization import validate_sha256
    for name, value in values.items():
        if name.startswith("expected_") and name.endswith("_sha256"):
            try:
                validate_sha256(value)
            except (TypeError, ValueError) as error:
                raise ApplicationError("INVALID_REVIEW_PIN", "Select the exact digest returned by the owning review.", field=name) from error
    return descriptor, values


def _workflow(request, values):
    from empirical_lawhood.api.workflows import installation_profiles, list_workflows, show_workflow
    if request.operation == "workflow.list":
        rows = [asdict(workflow) for workflow in list_workflows()]
        return projection(request=request, kind="workflows", title="Installed workflows", identity=None,
            scope="STATIC_DECLARATIONS", summary={"workflow_count": len(rows), "prerequisites_inspected": False},
            records=rows, parameters=values)
    workflow_id = values["workflow_id"]
    if type(workflow_id) is not str:
        raise ApplicationError("INVALID_WORKFLOW", "Select an installed workflow ID.", field="workflow_id")
    workflow = show_workflow(workflow_id)
    route = {"recursive-inquiry": "recursive-rc", "matrix-programme": "matrix-programme"}.get(workflow_id)
    return {"workflow": asdict(workflow), "prerequisites_inspected": False,
            "installation_profiles": installation_profiles(workflow_id),
            "application_operations": [asdict(row) for row in application_operations() if row.route in ("installed", route)],
            "other_actions": "UNSUPPORTED_BY_SELECTED_WORKBENCH_MATRIX"}


def _analysis(directory, plane, request, values):
    from empirical_lawhood.storage.retained_analysis import read_retained_analysis, read_retained_analysis_member
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    completion = read_retained_analysis(directory=directory, artifact_writer=plane)
    identity = ObjectIdentity.from_record(completion.completion_id, completion).to_document()
    if request.operation == "analysis.inspect":
        rows = [{"relative_path": member.relative_path, "size_bytes": member.artifact.size_bytes,
            "sha256": member.artifact.sha256, "record": member.to_document()} for member in completion.members]
        result = projection(request=request, kind="analysis", title=completion.completion_id, identity=identity,
            scope="AUTHENTICATED_ORIGINAL_ANALYSIS", summary={"member_count": len(rows), "new_native_contacts_this_read": 0},
            records=rows, parameters=values, provenance={"completion": completion.to_document()},
            value_semantics="Original analysis scope is preserved. Member inspection is explicit.")
    else:
        name = values["member"]
        if type(name) is not str or not name.endswith((".json", ".txt", ".md")):
            raise ApplicationError("UNSUPPORTED_PREVIEW_MEDIA", "Select a JSON or text member. Executable HTML is not served.", field="member")
        raw = read_retained_analysis_member(completion, name, directory=directory, artifact_writer=plane, maximum_bytes=2*1024**2)
        if name.endswith(".json"):
            from empirical_lawhood.api.application_contracts import _unique, _invalid_number
            try:
                value = json.loads(raw, object_pairs_hook=_unique, parse_float=Decimal, parse_constant=_invalid_number)
            except (ValueError, UnicodeError, RecursionError) as error:
                raise ApplicationError("UNSUPPORTED_MEMBER_JSON", "The selected member has no bounded strict JSON view.") from error
            rows = [{"field": key, "value": item} for key, item in value.items()] if isinstance(value, dict) else (
                [{"index": index, "value": item} for index, item in enumerate(value)] if isinstance(value, list) else [{"value": value}])
        else:
            text = raw.decode("utf-8")
            if len(raw) > MAX_TEXT_BYTES:
                raise ApplicationError("TEXT_PREVIEW_LIMIT", "This text exceeds the bounded preview. Use its owning export procedure.")
            rows = [{"text": text}]
        result = projection(request=request, kind="analysis-member", title=name, identity=identity,
            scope="BOUNDED_ORIGINAL_MEMBER_PREVIEW", summary={"member_bytes": len(raw), "member_sha256": sha256(raw).hexdigest(),
                "new_native_contacts_this_read": 0}, records=rows, parameters=values, provenance={"completion": identity})
    # The member can be displayed only after the complete original closure remains current.
    after = read_retained_analysis(directory=directory, artifact_writer=plane)
    if after != completion:
        raise PermissionError("Retained analysis completion changed during projection")
    return result


def execute_application(context: ApplicationContext, request: ApplicationRequest) -> ApiResult:
    """Execute exactly one registered operation through its selected owning service."""
    operation = request.operation if type(request) is ApplicationRequest else "application.invalid"
    try:
        if type(context) is not ApplicationContext or type(request) is not ApplicationRequest:
            raise ApplicationError("INVALID_APPLICATION_TYPES", "Select the exact context and request types.")
        context.__post_init__()
        request.__post_init__()
        if context.context_id != request.context_id:
            raise ApplicationError("CONTEXT_MISMATCH", "The request selects another application context.", field="context_id")
        descriptor, values = _parameters(request)
        if request.operation.startswith("observation."):
            from empirical_lawhood.api.operational_observation import observation_operation
            return application_result(operation, observation_operation(context, request, values))
        if request.operation.startswith("collection."):
            from empirical_lawhood.api.application_collection import collection_operation
            return application_result(operation, collection_operation(context, request, values))
        if request.operation in ("exploration.summary", "exploration.companion"):
            from empirical_lawhood.api.application_companions import companion_operation
            return application_result(operation, companion_operation(context, request, values))
        if request.operation.startswith("exploration."):
            from empirical_lawhood.api.application_exploration import exploration_operation
            return application_result(operation, exploration_operation(context, request, values))
        if request.operation == "work-cost.read":
            from empirical_lawhood.api.application_exploration import work_cost_operation
            return application_result(operation, work_cost_operation(context, request, values))
        if request.operation.startswith("programme."):
            from empirical_lawhood.api.application_programme import programme_operation
            return application_result(operation, programme_operation(context, request, values))
        if request.operation.startswith("inquiry."):
            from empirical_lawhood.api.application_inquiry import inquiry_operation
            return application_result(operation, inquiry_operation(context, request, values))
        if request.operation.startswith("knowledge."):
            from empirical_lawhood.api.application_knowledge import knowledge_operation
            return application_result(operation, knowledge_operation(context, request, values))
        if request.operation.startswith("continuing."):
            from empirical_lawhood.api.application_continuing import continuing_operation
            return application_result(operation, continuing_operation(context, request, values))
        if request.operation.startswith("presentation."):
            from empirical_lawhood.api.application_presentations import presentation_operation
            return application_result(operation, presentation_operation(context, request, values))
        if request.operation == "catalog.query":
            raise ApplicationError(descriptor.unavailable_reason or "UNSUPPORTED_OPERATION",
                "This operation is unavailable in the selected application slice.", category=ErrorCategory.CAPABILITY)
        if request.operation == "workflow.environment":
            from empirical_lawhood.api.workflow_installation import workflow_environment_result
            def software_selections(name):
                value = values.get(name, "")
                if type(value) is not str:
                    raise ApplicationError("INVALID_SOFTWARE_SELECTION", "Use one ID=/absolute/path per line.", field=name)
                return tuple(value.splitlines())
            return workflow_environment_result(values["workflow_id"], operation=operation,
                profile=values.get("profile", "standard"), project_root=context.project_root,
                worker_pythons=software_selections("worker_pythons"), external_software=software_selections("external_software"),
                assert_prerequisites=values.get("assert_prerequisites", False))
        if request.operation.startswith("workflow."):
            return application_result(operation, _workflow(request, values))
        if request.operation.startswith("configuration."):
            from empirical_lawhood.api.application_rc import configuration_operation
            return application_result(operation, configuration_operation(context, operation, values))
        if request.operation in ("rc.prepare", "recursive.author", "recursive.run", "recursive.recover"):
            from empirical_lawhood.api.application_rc import rc_lifecycle
            return application_result(operation, rc_lifecycle(context, operation, values))
        if context.read_access_paths and request.operation in ("analysis.inspect", "analysis.member", "matrix.inspect"):
            raise ApplicationError("ACCESS_SELECTION_NOT_APPLICABLE",
                "This route uses its own closed-package or programme-request access contract.", field="read_access_paths")
        directory = absolute_path(values["directory"], "directory")
        root, profile, plane = application_storage(context)
        if request.operation in ("recursive.execution", "recursive.result"):
            read_access = application_read_access(context, directory=directory, artifact_writer=plane)
            if request.operation == "recursive.execution":
                from empirical_lawhood.api.experiment_execution_read import read_development_execution
                report = read_development_execution(directory=directory, artifact_writer=plane, read_access=read_access)
                result = execution_projection(report, request=request, parameters=values)
            else:
                from empirical_lawhood.api.recursive_execution import read_recursive_wave
                result = read_recursive_wave(directory=directory, artifact_writer=plane, read_access=read_access,
                    terminal_product_format=values.get("terminal_product_format", "compact"), allow_partial=values.get("allow_partial", False))
        elif request.operation in ("rc.design", "rc.findings", "rc.export"):
            if context.read_access_paths:
                raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "The exposed RC view does not accept protected locator selections.")
            from empirical_lawhood.api.rc_workbench import inspect_rc, load_bounded_rc
            if request.operation == "rc.export":
                from empirical_lawhood.api.recursive_execution import read_recursive_wave
                with plane.read_context() as reader:
                    load_bounded_rc(directory=directory, plane=reader)
                    result = read_recursive_wave(directory=directory, artifact_writer=reader, terminal_product_format="documents")
                    reader.require_verification_snapshot()
            else:
                result = inspect_rc(directory=directory, plane=plane, request=request, parameters=values,
                                    findings=request.operation == "rc.findings")
        elif request.operation in ("sci02d.findings", "sci02d.assess"):
            if context.read_access_paths:
                raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "The exposed SCI02-D view does not accept protected locator selections.")
            from empirical_lawhood.api.sci02d_workbench import read_sci02d, sci02d_projection
            result = read_sci02d(directory=directory, plane=plane, reconstruct=request.operation == "sci02d.assess")
            if request.operation == "sci02d.findings":
                result = sci02d_projection(result, request=request, parameters=values)
        elif request.operation in ("analysis.inspect", "analysis.member"):
            result = _analysis(directory, plane, request, values)
        elif request.operation == "matrix.inspect":
            from empirical_lawhood.api.composite_experiment_programme import selected_composite_programme_service
            from empirical_lawhood.api.matrix_researcher_programme import MatrixResearchProgrammeService
            from empirical_lawhood.execution.operational_configuration import scientific_reconstruction_operation, ScientificReconstructionMode
            service = application_programme(context, root=root, profile=profile, plane=plane)
            owner = selected_composite_programme_service(service=service, directory=directory)
            if type(owner) is not MatrixResearchProgrammeService:
                raise ApplicationError("UNSUPPORTED_PROGRAMME", "Select the exact registered Matrix programme for this view.")
            with scientific_reconstruction_operation(ScientificReconstructionMode.OFF):
                report = owner.read(directory=directory, programme_request_path=context.programme_request_path)
            if report["scientific_reconstruction"] != "off":
                raise RuntimeError("Matrix inspection changed reconstruction scope")
            result = projection(request=request, kind="programme", title=report["programme"]["value"]["object_id"],
                identity=report["programme"], scope=report["read_scope"], summary={key: report[key] for key in (
                    "state", "scientific_reconstruction", "scientific_qualification", "denominator_aggregation")},
                records=report["phases"], parameters=values, frontier=report["frontier"],
                provenance={key: report[key] for key in ("programme", "input_commitments", "source_continuations", "prospective_amendments", "scientific_design")},
                dependencies=report["dependencies"])
        else:
            raise ApplicationError("UNSUPPORTED_OPERATION", "This application handler is unavailable.", category=ErrorCategory.CAPABILITY)
        return application_result(operation, result)
    except Exception as error:
        return error_result(operation, error, authored_object=(request.request_id if type(request) is ApplicationRequest else None))
