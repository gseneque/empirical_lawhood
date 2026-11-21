# SPDX-License-Identifier: MPL-2.0
"""Explicit operational run selections; original readers own every scientific fact."""

from hashlib import sha256
import json

from empirical_lawhood.api.application_contracts import ApplicationError, absolute_path, exact_mapping, identifier, load_application_json
from empirical_lawhood.api.application_projections import projection
from empirical_lawhood.api.application_state import operational_state_store


COLLECTION_SCHEMA = "empirical-lawhood/application/run-collection"
SELECTION_SCHEMA = "empirical-lawhood/application/run-selection"
COLLECTION_VERSION = "1.0.0"
MAX_ENTRIES = 256
READERS = frozenset(("recursive.execution", "rc.design", "rc.findings", "sci02d.findings", "analysis.inspect", "analysis.member",
    "presentation.read", "programme.read", "matrix.inspect"))
COMPANIONS = frozenset(("inquiry", "work-cost", "assessment", "acquisition", "cost-observations", "methods", "contribution"))


def document_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def document_digest(value):
    return sha256(document_bytes(value)).hexdigest()


def _text(value, name, maximum=192):
    if (type(value) is not str or not value.strip() or len(value) > maximum
            or any(ord(char) < 32 and char not in "\n\t" for char in value)):
        raise ApplicationError("INVALID_SELECTION_TEXT", "Select bounded descriptive text.", field=name)
    return value


def _sequence(value, name, maximum):
    if type(value) is not list or len(value) > maximum:
        raise ApplicationError("SELECTION_CENSUS_LIMIT", "The operational selection exceeds its census bound.", field=name)
    return value


def _identity(value):
    from empirical_lawhood.science.records.decoding import decode_canonical_record
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    decode_canonical_record(value, ObjectIdentity)
    return value


def _pin(value):
    from empirical_lawhood.science.records.serialization import validate_sha256
    exact_mapping(value, ("path", "sha256"), required=("path", "sha256"))
    absolute_path(value["path"], "path")
    validate_sha256(value["sha256"])


def _reader(value):
    exact_mapping(value, ("operation", "directory", "panel_id", "panel_version", "expected_identity", "member", "context_id"), required=("operation", "directory"))
    if value["operation"] not in READERS:
        raise ApplicationError("UNSUPPORTED_COLLECTION_READER", "Select an installed retained-result reader.")
    absolute_path(value["directory"], "directory")
    if value["operation"] == "presentation.read":
        identifier(value.get("panel_id"), "panel_id")
        from empirical_lawhood.science.records.serialization import validate_semantic_version
        validate_semantic_version(value.get("panel_version"))
    elif value["operation"] == "analysis.member":
        from empirical_lawhood.science.records.serialization import validate_relative_locator
        validate_relative_locator(value.get("member"))
        if set(value) - {"operation", "directory", "expected_identity", "member", "context_id"}:
            raise ApplicationError("INVALID_READER_SELECTION", "An analysis member has no panel selection.")
    elif set(value) - {"operation", "directory", "expected_identity", "context_id"}:
        raise ApplicationError("INVALID_READER_SELECTION", "This reader has no panel selection.")
    if value["operation"] == "presentation.read" and "member" in value:
        raise ApplicationError("INVALID_READER_SELECTION", "A registered presentation has no arbitrary member selection.")
    if "expected_identity" in value:
        _identity(value["expected_identity"])
    if "context_id" in value:
        identifier(value["context_id"], "reader.context_id")


def validate_selection(document, *, context_id):
    """Validate operator metadata without opening its original result or invoking science."""
    exact_mapping(document, ("schema", "version", "value"), required=("schema", "version", "value"))
    if document["schema"] != SELECTION_SCHEMA or document["version"] != COLLECTION_VERSION:
        raise ApplicationError("UNSUPPORTED_SELECTION_VERSION", "Select the supported run-selection revision.")
    required = ("selection_id", "investigation_id", "context_id", "label", "question", "identity", "readers",
        "classification", "companions", "stages", "deployment", "links")
    row = exact_mapping(document["value"], required, required=required)
    for name in ("selection_id", "investigation_id", "context_id"):
        identifier(row[name], name)
    if row["context_id"] != context_id:
        raise ApplicationError("CONTEXT_MISMATCH", "Register this selection in its declared engine context.")
    _text(row["label"], "label")
    _text(row["question"], "question", 2048)
    # A pending authored wave may have no returned result identity yet. Its UI
    # identifier then remains operational, never a fabricated scientific identity.
    if row["identity"] is not None:
        _identity(row["identity"])
    readers = _sequence(row["readers"], "readers", 16)
    if not readers:
        raise ApplicationError("READER_REQUIRED", "Select the original returned or authored locator.")
    for reader in readers:
        _reader(reader)
    if len({document_digest(reader) for reader in readers}) != len(readers):
        raise ApplicationError("DUPLICATE_LOCATOR", "Keep each original locator once.")
    classification = exact_mapping(row["classification"], ("programmes", "disciplines", "source"),
        required=("programmes", "disciplines", "source"))
    _pin(classification["source"])
    for axis in ("programmes", "disciplines"):
        for group in _sequence(classification[axis], axis, 16):
            exact_mapping(group, ("id", "label"), required=("id", "label"))
            identifier(group["id"], "classification.id")
            _text(group["label"], "classification.label")
        if len({item["id"] for item in classification[axis]}) != len(classification[axis]):
            raise ApplicationError("DUPLICATE_CLASSIFICATION", "A classification repeats its identifier.")
    roles = set()
    for companion in _sequence(row["companions"], "companions", 16):
        exact_mapping(companion, ("role", "directory", "identity", "attachment", "sources"), required=("role",))
        role = companion["role"]
        if role not in COMPANIONS or role in roles:
            raise ApplicationError("INVALID_COMPANION", "Select each supported companion role once.")
        roles.add(role)
        if "attachment" in companion:
            if set(companion) != {"role", "attachment"}:
                raise ApplicationError("INVALID_COMPANION", "An audit attachment is distinct from an original package.")
            _pin(companion["attachment"])
        else:
            absolute_path(companion.get("directory"), "companion.directory")
            _identity(companion.get("identity"))
            if "sources" in companion:
                if role != "assessment":
                    raise ApplicationError("INVALID_COMPANION", "Only the standalone assessment selects its original source publications.")
                from empirical_lawhood.science.records.decoding import decode_canonical_record
                from empirical_lawhood.science.records.serialization import validate_relative_locator
                from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
                for source in _sequence(companion["sources"], "companion.sources", 128):
                    exact_mapping(source, ("identity", "contract", "relative_path"), required=("identity", "contract", "relative_path"))
                    _identity(source["identity"])
                    decode_canonical_record(source["contract"], ExternalRootContract)
                    validate_relative_locator(source["relative_path"])
    stage_ids = set()
    for stage in _sequence(row["stages"], "stages", 32):
        exact_mapping(stage, ("id", "label", "revision", "state", "depends_on", "source", "decision", "intent"),
            required=("id", "label", "revision", "state", "depends_on", "source", "decision", "intent"))
        identifier(stage["id"], "stage.id")
        _text(stage["label"], "stage.label")
        if stage["id"] in stage_ids or type(stage["revision"]) is not int or stage["revision"] < 1:
            raise ApplicationError("INVALID_STAGE_REVISION", "Stage identifiers and positive revisions must be distinct.")
        stage_ids.add(stage["id"])
        if stage["state"] not in ("PLANNED", "SELECTED", "DECLINED", "AUTHORED", "RETURNED", "UNAVAILABLE"):
            raise ApplicationError("INVALID_STAGE_STATE", "Use an operational stage state, with assessment kept separate.")
        for dependency in _sequence(stage["depends_on"], "stage.depends_on", 32):
            identifier(dependency, "stage.dependency")
            if dependency == stage["id"]:
                raise ApplicationError("INVALID_STAGE_DEPENDENCY", "A stage cannot depend on itself.")
        _pin(stage["source"])
        for name in ("decision", "intent"):
            if stage[name] is not None:
                _identity(stage[name])
    deployment = row["deployment"]
    if deployment is not None:
        deployment_fields = ("deployment_id", "allocation", "job_card", "observation_path", "run_id", "packet_sha256",
            "controller_source_sha256", "worker_source_sha256")
        exact_mapping(deployment, (*deployment_fields, "return_path"), required=deployment_fields)
        identifier(deployment["deployment_id"], "deployment_id")
        identifier(deployment["run_id"], "run_id")
        from empirical_lawhood.science.records.serialization import validate_sha256
        for name in ("packet_sha256", "controller_source_sha256", "worker_source_sha256"):
            validate_sha256(deployment[name])
        for name in ("allocation", "job_card"):
            # Allocations and operator job cards are operational documents,
            # not fabricated canonical scientific ObjectIdentity records.
            _pin(deployment[name])
        absolute_path(deployment["observation_path"], "observation_path")
        if deployment.get("return_path") is not None:
            absolute_path(deployment["return_path"], "return_path")
    for link in _sequence(row["links"], "links", 32):
        exact_mapping(link, ("target", "kind", "label", "source"), required=("target", "kind", "label", "source"))
        identifier(link["target"], "link.target")
        _text(link["label"], "link.label")
        if link["kind"] not in ("INFORMING_REFERENCE", "CLASSIFICATION"):
            raise ApplicationError("SCIENTIFIC_EDGE_REQUIRES_OWNER", "Scientific supply and lineage require their original owning reader.")
        _pin(link["source"])
    return document


def _load(context):
    store = operational_state_store(context)
    raw = store.read()
    if raw is None:
        return store, None, {"schema": COLLECTION_SCHEMA, "version": COLLECTION_VERSION,
            "created_by_context": context.context_id, "revision": 0, "entries": [], "aliases": {}}
    doc = load_application_json(raw, maximum_bytes=1024 * 1024)
    names = ("schema", "version", "created_by_context", "revision", "entries", "aliases")
    exact_mapping(doc, names, required=names)
    if doc["schema"] != COLLECTION_SCHEMA or doc["version"] != COLLECTION_VERSION:
        raise ApplicationError("UNSUPPORTED_COLLECTION_VERSION", "Select the supported collection revision.")
    identifier(doc["created_by_context"], "created_by_context")
    if type(doc["revision"]) is not int or doc["revision"] < 1:
        raise ApplicationError("INVALID_COLLECTION_REVISION", "The retained collection revision is invalid.")
    ids, identities = set(), set()
    for entry in _sequence(doc["entries"], "entries", MAX_ENTRIES):
        validate_selection(entry, context_id=entry.get("value", {}).get("context_id"))
        selected_id = entry["value"]["selection_id"]
        identity = entry["value"]["identity"]
        key = None if identity is None else document_digest(identity)
        if selected_id in ids or key is not None and key in identities:
            raise ApplicationError("DUPLICATE_SELECTION", "The collection repeats an original identity or selection.")
        ids.add(selected_id)
        if key is not None:
            identities.add(key)
    aliases = doc["aliases"]
    if type(aliases) is not dict or len(aliases) > MAX_ENTRIES:
        raise ApplicationError("ALIAS_LIMIT", "The collection exceeds its alias bound.")
    for alias, target in aliases.items():
        identifier(alias, "alias")
        if alias in ids or target not in ids:
            raise ApplicationError("INVALID_ALIAS", "An alias must select one original entry without chaining.")
    return store, sha256(raw).hexdigest(), doc


def selected_entry(context, selection_id):
    _, digest, document = _load(context)
    identifier(selection_id, "selection_id")
    target = document["aliases"].get(selection_id, selection_id)
    selected = next((entry for entry in document["entries"] if entry["value"]["selection_id"] == target), None)
    if selected is None:
        raise ApplicationError("SELECTION_UNAVAILABLE", "The selected run is absent from this collection.")
    return selected, digest


def _preserved(previous, current):
    """A subsequent handoff may attach return locators, never substitute entered work."""
    before, after = previous["value"], current["value"]
    for name in ("selection_id", "investigation_id", "context_id"):
        if before[name] != after[name]:
            raise ApplicationError("SELECTION_BINDING_CHANGED", "Keep the original investigation and context binding.")
    if before["identity"] is not None and before["identity"] != after["identity"]:
        raise ApplicationError("ORIGINAL_IDENTITY_CHANGED", "Register another original result as a separate wave.")
    if any(item not in after["readers"] for item in before["readers"]):
        raise ApplicationError("ORIGINAL_LOCATOR_REMOVED", "Preserve the original locators when attaching returned custody.")
    if any(item not in after["companions"] for item in before["companions"]):
        raise ApplicationError("COMPANION_SUBSTITUTION", "Keep original companion identities and attachment pins.")
    if before["deployment"] is not None and before["deployment"] != after["deployment"]:
        raise ApplicationError("DEPLOYMENT_SUBSTITUTION", "Register a changed allocation as another wave.")
    old_stages = {item["id"]: item for item in before["stages"]}
    new_stages = {item["id"]: item for item in after["stages"]}
    if not old_stages.keys() <= new_stages.keys():
        raise ApplicationError("STAGE_REMOVED", "Preserve the complete recorded stage census.")
    for key, stage in old_stages.items():
        new = new_stages[key]
        if new == stage:
            continue
        if new["revision"] <= stage["revision"]:
            raise ApplicationError("STAGE_REVISION_REQUIRED", "Retain a later revision for a changed operational stage.")
        for name in ("decision", "intent"):
            if stage[name] is not None and stage[name] != new[name]:
                raise ApplicationError("STAGE_INTENT_SUBSTITUTION", "A changed decision or intent requires another wave.")


def collection_operation(context, request, values):
    store, digest, document = _load(context)
    if request.operation == "collection.neighbourhood":
        from empirical_lawhood.api.application_neighbourhood import collection_neighbourhood
        result = collection_neighbourhood(document, request=request, values=values)
        if digest is not None and store.read() != document_bytes(document):
            raise ApplicationError("COLLECTION_CHANGED", "The selected collection changed during relationship inspection.")
        return result
    if request.operation == "collection.register":
        entry = validate_selection(load_application_json(values["text"].encode()), context_id=context.context_id)
        expected = values.get("expected_collection_sha256")
        if expected != digest:
            raise ApplicationError("COLLECTION_CHANGED", "Read the current collection before updating it.")
        rows = document["entries"]
        incoming = entry["value"]
        selected_id = incoming["selection_id"]
        existing = next((item for item in rows if item["value"]["selection_id"] == selected_id), None)
        original = next((item for item in rows if incoming["identity"] is not None
            and item["value"]["identity"] == incoming["identity"]), None)
        if selected_id in document["aliases"]:
            raise ApplicationError("ALIAS_IS_NOT_PRIMARY", "Update the original selection identified by this alias.")
        if existing is not None:
            _preserved(existing, entry)
            if original is not None and original is not existing:
                raise ApplicationError("ORIGINAL_ALREADY_SELECTED", "Attach this handoff to its existing original selection.")
            rows[rows.index(existing)] = entry
        elif original is not None:
            original_value = original["value"]
            if (original_value["investigation_id"] != incoming["investigation_id"]
                    or original_value["deployment"] != incoming["deployment"]
                    or original_value["stages"] != incoming["stages"]
                    or original_value["companions"] != incoming["companions"]):
                raise ApplicationError("ALIAS_BINDING_CONFLICT", "Duplicate identities must retain their existing work bindings.")
            original_value["readers"] += [reader for reader in incoming["readers"] if reader not in original_value["readers"]]
            document["aliases"][selected_id] = original_value["selection_id"]
            selected_id = original_value["selection_id"]
        else:
            rows.append(entry)
        if len(rows) > MAX_ENTRIES or len(document["aliases"]) > MAX_ENTRIES:
            raise ApplicationError("COLLECTION_LIMIT", "Select a smaller collection of at most 256 entries and aliases.")
        for row in rows:
            validate_selection(row, context_id=row["value"]["context_id"])
        document["revision"] += 1
        from empirical_lawhood.storage.workbench_state import WorkbenchStateConflict
        try:
            digest = store.replace(document_bytes(document), expected_sha256=digest)
        except WorkbenchStateConflict as error:
            raise ApplicationError("COLLECTION_CHANGED", "Another operator updated this collection. Reopen it.") from error
        return {"schema": COLLECTION_SCHEMA, "version": COLLECTION_VERSION, "selection_id": selected_id,
            "revision": document["revision"], "collection_sha256": digest, "entry_count": len(rows),
            "scientific_reads": 0, "native_calls": 0, "scope": "OPERATIONAL_LOCATORS_ONLY"}
    if request.operation == "collection.entry":
        entry, _ = selected_entry(context, values["selection_id"])
        # Recheck against this operation's first snapshot before returning metadata.
        if store.read() != document_bytes(document):
            raise ApplicationError("COLLECTION_CHANGED", "The selected collection changed during its read.")
        return {"entry": entry, "collection_sha256": digest, "scope": "OPERATOR_METADATA_NOT_AUTHENTICATED_FINDINGS"}
    rows = [{**entry["value"], "entry_sha256": document_digest(entry)} for entry in document["entries"]]
    return projection(request=request, kind="collection", title="Selected investigations", identity=None,
        scope="OPERATOR_METADATA_NOT_AUTHENTICATED_FINDINGS", records=rows, parameters=values,
        summary={"entry_count": len(rows), "revision": document["revision"], "exists": digest is not None,
            "collection_sha256": digest, "scientific_reads": 0, "native_calls": 0}, aliases=document["aliases"])
