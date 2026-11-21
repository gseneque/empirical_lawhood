# SPDX-License-Identifier: MPL-2.0
"""Bounded knowledge views and reviewed exchange through the original owners."""

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.storage.guarded_catalog import select_operator_catalog
from empirical_lawhood.science.records.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import canonical_json_document_bytes
from empirical_lawhood.storage.contracts.knowledge_store import KnowledgeObjectLocator, ScientificTypeRegistry

from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import ApplicationError, MAX_EDIT_BYTES, absolute_path, application_result, exact_mapping, load_application_json, response_bytes
from empirical_lawhood.api.application_projections import projection
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.knowledge_certificate_types import development_certificate_access, knowledge_certificate_descriptors
from empirical_lawhood.api.knowledge_store import KnowledgeStore, verify_knowledge_transfer


def _selection(values):
    text = values["text"]
    if type(text) is not str:
        raise ApplicationError("INVALID_KNOWLEDGE_SELECTION", "Select the exact returned object locations.")
    return load_application_json(text.encode(), maximum_bytes=MAX_EDIT_BYTES)


def _safe_report(value):
    if isinstance(value, dict):
        # A notice's reason is an original custodian assertion, not a diagnostic.
        if set(value) == {"schema", "version", "value"}:
            return value
        partial = value.get("status") in {"ACCESS_REFUSED", "MISSING_DEPENDENCY", "UNSUPPORTED_REVISION",
            "NOT_VERIFIED", "UNAVAILABLE_OR_UNVERIFIED"}
        return {key: _safe_report(item) for key, item in value.items() if not (partial and key == "reason")}
    if isinstance(value, (tuple, list)):
        return tuple(_safe_report(item) for item in value)
    return value


def _store(selection, root, plane):
    return KnowledgeStore(directory=absolute_path(selection["directory"], "directory"),
        namespace=selection["namespace"], project_root=root, artifact_writer=plane,
        registry=ScientificTypeRegistry(knowledge_certificate_descriptors()),
        require_access=development_certificate_access(plane))


def _catalog(context, root, profile):
    access = select_operator_catalog(profile=profile, project_root=root,
        catalog_relative_path=context.catalog_relative_path)
    if access is None:
        raise ApplicationError("CATALOG_REQUIRED", "Select the store's explicit catalogue in this context.")
    return access


def _certificate(directory, reader, allow_incomplete):
    from empirical_lawhood.storage.recursive_custody import read_exposed_recursive_payload
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.science.evidence.knowledge_certificates import KnowledgeAssessmentCertificate
    from empirical_lawhood.api.knowledge_certificates import MAX_CERTIFICATE_MEMBER_BYTES, verify_assessment_certificate

    relative = (directory.relative_to(reader.root.contract.canonical_path) / "certificate.json").as_posix()
    manifest = reader.read_manifest(relative)
    if (manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or manifest.logical.payload_schema != KnowledgeAssessmentCertificate.SCHEMA
            or manifest.logical.lineage_parents):
        raise PermissionError("certificate inspection requires its original exposed development publication")
    raw = read_exposed_recursive_payload(reader, manifest, maximum_bytes=MAX_CERTIFICATE_MEMBER_BYTES)
    identified = decode_canonical_bytes(raw, KnowledgeAssessmentCertificate, maximum_bytes=MAX_CERTIFICATE_MEMBER_BYTES)
    return verify_assessment_certificate(directory=directory, artifact_writer=reader,
        expected_certificate=identified.identity, allow_incomplete=allow_incomplete)


def _read(context, request, values):
    root, profile, plane = application_storage(context)
    with plane.read_context() as reader:
        if request.operation == "knowledge.certificate":
            report = _certificate(absolute_path(values["directory"], "directory"), reader,
                values.get("allow_partial", False))
            identity, title = report["certificate_identity"], "Original assessment certificate"
        elif request.operation == "knowledge.resolve":
            selected = exact_mapping(_selection(values), ("directory", "namespace", "locator"),
                required=("directory", "namespace", "locator"))
            locator = decode_canonical_record(selected["locator"], KnowledgeObjectLocator)
            report = _store(selected, root, reader).resolve(locator, allow_incomplete=values.get("allow_partial", False))
            identity, title = locator.object_identity.to_document(), "Selected original knowledge object"
        else:
            store = _store(values, root, reader)
            report = store.query(catalog_access=_catalog(context, root, profile),
                limit=values.get("import_limit", 8), after_materialization_id=values.get("after_materialization_id"))
            identity, title = None, store.namespace
        report = _safe_report(report)
        if request.operation == "knowledge.query":
            rows = tuple({**row, "import_receipt": imported["import_receipt"],
                "import_observed_at_utc": imported["import_observed_at_utc"],
                "current_scientific_assessment": imported["current_scientific_assessment"]}
                for imported in report["imports"] for row in imported["objects"])
        else:
            rows = tuple({"field": key, "value": value} for key, value in report.items())
        summary = {"verification_status": report["status"], "consumer_admission": "NOT_EVALUATED",
            "unseen_updates": report.get("unseen_updates", "UNKNOWN"), "current_execution_authority": "NONE"}
        verified = report.get("verification") or report
        if "original_disposition" in verified:
            summary["original_disposition"] = verified["original_disposition"]
        if request.operation == "knowledge.query":
            summary.update(selected_imports=len(report["imports"]), selected_objects=len(rows),
                total_scope="ONLY_SELECTED_IMPORT_PAGE; not the whole store")
        result = projection(request=request, kind=request.operation, title=title, identity=identity,
            scope="EXPOSED_ORIGINAL_KNOWLEDGE", summary=summary, records=rows, parameters=values, knowledge=report,
            value_semantics="Original assessments and custodian notices retain their scope. Discovery is not current verification. Unseen updates are unknown. No current consumer admission or execution authority is granted.")
        response_bytes(application_result(request.operation, result))
        reader.require_verification_snapshot()
    return result


def _review(context, selection, root, profile, plane):
    action = selection.get("action") if type(selection) is dict else None
    extra = {"INITIALIZE": (), "REBUILD": (), "IMPORT": ("source_profile", "source_root_contract", "transfer_directory", "expected_transfer", "resume"),
        "EXPORT": ("locators", "roots", "output_directory", "expected_transfer")}
    if type(action) is not str or action not in extra:
        raise ApplicationError("UNSUPPORTED_KNOWLEDGE_ACTION", "Select initialize, import, export or a new catalogue rebuild.")
    required = {"INITIALIZE": (), "REBUILD": (), "IMPORT": ("source_profile", "transfer_directory", "resume"),
        "EXPORT": ("locators", "roots", "output_directory")}[action]
    selection = dict(exact_mapping(selection, ("action", "directory", "namespace", *extra[action]),
        required=("action", "directory", "namespace", *required)))
    store = _store(selection, root, plane)
    bindings = {"context": context.to_document(), "profile": profile.to_document(), "root": plane.root.contract.to_document()}
    report, source, catalog = {}, None, None
    if action == "INITIALIZE":
        preflight_authoring_output_directory(directory=store.directory, repo_root=root, artifact_writer=plane)
    else:
        store._selected()
    if action == "REBUILD":
        catalog = _catalog(context, root, profile)
        catalog.verify(for_write=True)
        if catalog.database_path.exists():
            raise ApplicationError("NEW_CATALOG_REQUIRED", "Select a new catalogue destination. Original imports remain primary.")
        bindings["catalog"] = {"root": catalog.root.contract.to_document(), "path": str(catalog.database_path)}
    elif action == "IMPORT":
        if type(selection["resume"]) is not bool:
            raise ApplicationError("INVALID_RECOVERY_SELECTION", "Select explicit recovery of the original copy plan.")
        selected_root = selection.get("source_root_contract")
        source_context = replace(context, operator_profile=absolute_path(selection["source_profile"], "source_profile"),
            artifact_root_contract=None if selected_root is None else absolute_path(selected_root, "source_root_contract"))
        _, source_profile, source = application_storage(source_context)
        bindings["source"] = {"profile": source_profile.to_document(), "root": source.root.contract.to_document()}
        report = verify_knowledge_transfer(directory=absolute_path(selection["transfer_directory"], "transfer_directory"),
            artifact_writer=source, registry=store.registry, require_access=development_certificate_access(source),
            expected_transfer=None if "expected_transfer" not in selection else decode_canonical_record(selection["expected_transfer"], ObjectIdentity))
    elif action == "EXPORT":
        for field in ("locators", "roots"):
            if type(selection[field]) is not list or not 1 <= len(selection[field]) <= store.limits.maximum_objects:
                raise ApplicationError("KNOWLEDGE_SELECTION_LIMIT", "Select between one and sixteen original objects and roots.")
        report = store.preview_export(locators=tuple(decode_canonical_record(row, KnowledgeObjectLocator) for row in selection["locators"]),
            roots=tuple(decode_canonical_record(row, ObjectIdentity) for row in selection["roots"]),
            output_directory=absolute_path(selection["output_directory"], "output_directory"))
    if report:
        if "expected_transfer" in selection and selection["expected_transfer"] != report["transfer"]:
            raise ApplicationError("REVIEWED_TRANSFER_CHANGED", "The complete selected transfer differs from the review.")
        selection["expected_transfer"] = report["transfer"]
    bindings["selection"] = selection
    result = {"status": "REVIEWED_CURRENT_SELECTION", "selection": selection,
        "review_sha256": sha256(canonical_json_document_bytes(bindings)).hexdigest(), "review": _safe_report(report),
        "destinations": {"store": str(store.directory), "export": selection.get("output_directory"),
            "catalog": None if catalog is None else str(catalog.database_path)},
        "consumer_admission": "NOT_EVALUATED", "current_execution_authority": "NONE",
        "entry_conditions": "Apply repeats current storage, access and original verification. Rebuild reads current primary imports. Import recovery uses the original replica plan."}
    return result, store, source, catalog


def knowledge_operation(context, request, values):
    if context.read_access_paths:
        raise ApplicationError("UNSUPPORTED_ACCESS_SELECTION", "This knowledge route accepts exposed development packages only.")
    if request.operation not in ("knowledge.review", "knowledge.apply"):
        return _read(context, request, values)
    selection = _selection(values)
    root, profile, plane = application_storage(context, for_write=True)
    review, store, source, catalog = _review(context, selection, root, profile, plane)
    response_bytes(application_result(request.operation, review))
    if request.operation == "knowledge.review":
        return review
    if values["expected_review_sha256"] != review["review_sha256"]:
        raise ApplicationError("REVIEWED_SELECTION_CHANGED", "Review the current context, complete transfer and destinations before applying.")
    selection = review["selection"]
    action = selection["action"]
    if action == "INITIALIZE":
        return store.initialize()
    if action == "REBUILD":
        return store.rebuild_projection(catalog_access=catalog)
    if action == "IMPORT":
        report = store.import_transfer(directory=absolute_path(selection["transfer_directory"], "transfer_directory"),
            source_artifact_writer=source, source_require_access=development_certificate_access(source),
            expected_transfer=decode_canonical_record(selection["expected_transfer"], ObjectIdentity), resume=selection["resume"])
        return {**report, "locators": tuple(row.to_document() for row in report["locators"])}
    return store.export(locators=tuple(decode_canonical_record(row, KnowledgeObjectLocator) for row in selection["locators"]),
        roots=tuple(decode_canonical_record(row, ObjectIdentity) for row in selection["roots"]),
        output_directory=absolute_path(selection["output_directory"], "output_directory"),
        expected_transfer=decode_canonical_record(selection["expected_transfer"], ObjectIdentity))
