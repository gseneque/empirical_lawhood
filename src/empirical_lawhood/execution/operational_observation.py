# SPDX-License-Identifier: MPL-2.0
"""Finite operational transport contracts. These are not scientific records."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import PurePosixPath

from empirical_lawhood.science.records.serialization import validate_sha256, validate_stable_id
from empirical_lawhood.execution.deployment_budget import utc


VERSION = "1.0.0"
SELECTION_SCHEMA = "empirical-lawhood/operational/observation-selection"
SNAPSHOT_SCHEMA = "empirical-lawhood/operational/observation"
DOMAIN_SCHEMA = "empirical-lawhood/operational/domain-observation"
MAX_BYTES = 1024 * 1024
MAX_ROWS = 200
MONEY_FIELDS = ("accounted_usd", "remaining_usd", "pod_elapsed_upper_usd", "volume_bucket_upper_usd",
    "pod_billed_usd", "volume_billed_usd", "previous_attempts_usd", "science_stop_usd", "retirement_threshold_usd")
FINANCIAL_STATES = ("CONTINUE", "STOP_SCIENCE_RETURN_ONLY", "RETIRE_COMPUTE",
    "FINANCIAL_CANCELLATION_RETURNED", "SUPERVISION_REFUSED", "RETIREMENT_UNRESOLVED",
    "COMPUTE_ABSENT_VOLUME_RETAINED")
RETURN_STAGES = ("REMOTE_PUBLICATION", "SEALED_EXPORT", "TRANSFER", "BYTE_VERIFICATION",
    "INDEPENDENT_READING", "CONTRIBUTION")
RUNTIME_FIELDS = ("observed_gpu", "utilisation", "memory", "process", "native_phase")


def document_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode() + b"\n"


def digest(value):
    return sha256(document_bytes(value)).hexdigest()


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("operational JSON repeats a field")
        value[key] = item
    return value


def _invalid(_value):
    raise ValueError("operational values require integers or exact Decimal strings")


def document(raw, *, maximum_bytes=MAX_BYTES):
    if type(raw) is not bytes or len(raw) > maximum_bytes:
        raise ValueError("operational observation exceeds its byte bound")
    return json.loads(raw, object_pairs_hook=_unique, parse_float=_invalid, parse_constant=_invalid)


def fields(value, names, *, optional=()):
    if type(value) is not dict or set(value) - set((*names, *optional)) or set(names) - set(value):
        raise ValueError("operational fields do not match the selected revision")
    return value


def text(value, *, maximum=256):
    if type(value) is not str or not value or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError("operational text must be explicit, bounded and nonsecret")
    return value


def absolute(value):
    text(value, maximum=4096)
    path = PurePosixPath(value)
    if not path.is_absolute() or ".." in path.parts or str(path) != value or value == "/":
        raise ValueError("operational paths must be normalized absolute selections")
    return value


def pin(value):
    fields(value, ("path", "sha256"))
    absolute(value["path"])
    validate_sha256(value["sha256"])
    return value


def evidence_reference(value):
    if type(value) is dict and "byte_offset" in value:
        fields(value, ("path", "sha256", "byte_offset", "size_bytes"))
        absolute(value["path"])
        validate_sha256(value["sha256"])
        count(value["byte_offset"], maximum=64 * MAX_BYTES)
        count(value["size_bytes"], maximum=MAX_BYTES)
    else:
        pin(value)
    return value


def rows(value, *, maximum=MAX_ROWS):
    if type(value) is not list or len(value) > maximum:
        raise ValueError("operational observation exceeds its selected row bound")
    return value


def count(value, *, maximum=10**9):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError("operational counts must be bounded nonnegative integers")
    return value


def exact_amount(value, *, signed=False):
    text(value, maximum=100)
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("operational money requires an exact Decimal string") from error
    if not number.is_finite() or abs(number.as_tuple().exponent) > 100 or not signed and number < 0:
        raise ValueError("operational monetary observation is invalid")
    return number


def validate_binding(value):
    fields(value, ("deployment_id", "investigation_id", "selection_id", "run_id", "packet_sha256",
        "allocation_sha256", "job_card_sha256", "controller_source_sha256", "worker_source_sha256"))
    for name in ("deployment_id", "investigation_id", "selection_id", "run_id"):
        text(value[name], maximum=192)
        validate_stable_id(value[name])
    for name in value:
        if name.endswith("_sha256"):
            validate_sha256(value[name])
    return value


def validate_selection(value):
    fields(value, ("schema", "version", "binding", "directory", "allocation", "job_card", "supervisors",
        "cadence_seconds", "stale_after_seconds", "task_offset", "native_offset", "row_limit", "domain_panel"))
    if value["schema"] != SELECTION_SCHEMA or value["version"] != VERSION:
        raise ValueError("unsupported observation selection revision")
    binding = validate_binding(value["binding"])
    absolute(value["directory"])
    for name in ("allocation", "job_card"):
        pin(value[name])
        if binding[name + "_sha256"] != value[name]["sha256"]:
            raise ValueError("observation substitutes its original allocation or job card")
    for name in ("cadence_seconds", "stale_after_seconds"):
        count(value[name], maximum=86400)
    if not 2 <= value["cadence_seconds"] <= 3600 or value["stale_after_seconds"] < 2 * value["cadence_seconds"]:
        raise ValueError("select a cadence of at least two seconds and a stale interval of at least two cadences")
    for name in ("task_offset", "native_offset"):
        count(value[name])
    if not 1 <= count(value["row_limit"], maximum=MAX_ROWS):
        raise ValueError("select an explicit nonempty observation window")
    for supervisor in rows(value["supervisors"], maximum=16):
        fields(supervisor, ("directory", "selection_sha256"))
        absolute(supervisor["directory"])
        validate_sha256(supervisor["selection_sha256"])
    panel = value["domain_panel"]
    if panel is not None:
        fields(panel, ("panel_id", "panel_version", "observation_version"))
        for item in panel.values():
            text(item)
    return value


def _source(value):
    fields(value, ("schema", "version", "fingerprint", "object_id"))
    validate_sha256(value["fingerprint"])
    for name in ("schema", "version", "object_id"):
        text(value[name], maximum=512)


def validate_domain(value):
    """Installed domain owners supply operational coverage, never question findings."""
    fields(value, ("schema", "version", "status", "binding", "positions", "effects", "allowances",
        "complete_return_count", "return_count_scope", "pending_bindings"), optional=("runtime",))
    if value["schema"] != DOMAIN_SCHEMA or value["version"] != VERSION:
        raise ValueError("unsupported domain observation revision")
    if value["status"] not in ("SUPPORTED", "UNAVAILABLE"):
        raise ValueError("domain observation must state its installed support")
    fields(value["binding"], ("run_id", "packet_sha256"))
    text(value["binding"]["run_id"])
    validate_sha256(value["binding"]["packet_sha256"])
    if value["complete_return_count"] is not None:
        count(value["complete_return_count"])
    text(value["return_count_scope"], maximum=512)
    for item in rows(value["positions"], maximum=32):
        fields(item, ("id", "label", "genotype", "checkpoint", "trial", "safe_state", "publication",
            "independent_reading", "continuation", "source"))
        for key in item:
            if key != "source":
                text(item[key])
        if item["source"] is not None:
            _source(item["source"])
    for item in rows(value["effects"]):
        fields(item, ("id", "stage", "position", "direction", "scale", "side", "entry", "raw_return",
            "publication", "completion_receipt", "complete_force_return", "source"))
        for key in item:
            if key != "source":
                text(item[key])
        if item["source"] is not None:
            _source(item["source"])
    for item in rows(value["allowances"], maximum=32):
        fields(item, ("stage", "allowance", "complete_returns", "state", "depends_on", "source"))
        text(item["stage"])
        text(item["state"])
        count(item["allowance"])
        if item["complete_returns"] is not None:
            count(item["complete_returns"])
        for dependency in rows(item["depends_on"], maximum=32):
            text(dependency)
        if item["source"] is not None:
            _source(item["source"])
    for item in rows(value["pending_bindings"], maximum=16):
        text(item, maximum=512)
    runtime = value.get("runtime")
    if runtime is not None:
        fields(runtime, (*RUNTIME_FIELDS, "observed_utc", "worker_source_sha256", "source"))
        utc(runtime["observed_utc"])
        validate_sha256(runtime["worker_source_sha256"])
        _source(runtime["source"])
        for name in RUNTIME_FIELDS:
            if runtime[name] is not None:
                text(runtime[name], maximum=512)
    if value["status"] == "UNAVAILABLE" and (value["positions"] or value["effects"] or value["allowances"]
            or value["complete_return_count"] is not None or runtime is not None):
        raise ValueError("an unavailable reader cannot manufacture work coverage")
    return value


def unavailable_domain(binding):
    return {"schema": DOMAIN_SCHEMA, "version": VERSION, "status": "UNAVAILABLE",
        "binding": {name: binding[name] for name in ("run_id", "packet_sha256")},
        "positions": [], "effects": [], "allowances": [], "complete_return_count": None,
        "return_count_scope": "NOT_INFERRED_FROM_RAW_RETURNS_OR_TASK_RECEIPTS",
        "pending_bindings": ["No scientific observation callback is selected for this original wave."]}


def validate_snapshot(value):
    names = ("schema", "version", "binding", "selection_sha256", "collector_id", "sequence", "previous_snapshot_sha256",
        "source_observed_utc", "cadence_seconds", "stale_after_seconds", "execution", "native", "financial", "domain",
        "runtime", "return", "errors", "provider_calls", "native_calls", "lifecycle_actions", "scientific_authority")
    fields(value, names)
    if value["schema"] != SNAPSHOT_SCHEMA or value["version"] != VERSION:
        raise ValueError("unsupported operational observation revision")
    validate_binding(value["binding"])
    validate_sha256(value["selection_sha256"])
    text(value["collector_id"], maximum=192)
    validate_stable_id(value["collector_id"])
    if not 1 <= count(value["sequence"]):
        raise ValueError("observation sequence must be positive")
    if value["previous_snapshot_sha256"] is not None:
        validate_sha256(value["previous_snapshot_sha256"])
    utc(value["source_observed_utc"])
    if (type(value["cadence_seconds"]) is not int or not 2 <= value["cadence_seconds"] <= 3600
            or type(value["stale_after_seconds"]) is not int
            or not 2 * value["cadence_seconds"] <= value["stale_after_seconds"] <= 86400):
        raise ValueError("observation cadence and stale interval changed")
    for name in ("provider_calls", "native_calls", "lifecycle_actions"):
        if type(value[name]) is not int or value[name] != 0:
            raise ValueError("an observation must never contact providers, acquire or act")
    if value["scientific_authority"] != "NONE":
        raise ValueError("an observation supplies no scientific authority")
    execution = fields(value["execution"], ("status", "run_id", "task_count", "attempt_count", "offset", "rows", "source",
        "producing_code_sha256", "dependency_lock_sha256", "producing_commit"))
    for name in ("producing_code_sha256", "dependency_lock_sha256"):
        validate_sha256(execution[name])
    if execution["producing_code_sha256"] != value["binding"]["worker_source_sha256"]:
        raise ValueError("execution producer differs from the selected worker source")
    commit = execution["producing_commit"]
    if type(commit) is not str or len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        raise ValueError("execution observation requires its original producing commit")
    for name in ("task_count", "attempt_count", "offset"):
        if execution[name] is not None:
            count(execution[name])
    if execution["run_id"] != value["binding"]["run_id"]:
        raise ValueError("execution observation changes its original run")
    text(execution["status"])
    if execution["source"] is not None:
        _source(execution["source"])
    for row in rows(execution["rows"]):
        fields(row, ("task_id", "attempt_id", "ordinal", "operational_status", "receipt_id"))
        for key in ("task_id", "operational_status"):
            text(row[key], maximum=512)
        for key in ("attempt_id", "receipt_id"):
            if row[key] is not None:
                text(row[key], maximum=512)
        if row["ordinal"] is not None:
            count(row["ordinal"])
    native = fields(value["native"], ("total", "offset", "rows", "coverage", "body_validation"))
    if native["total"] is not None:
        count(native["total"])
    count(native["offset"])
    text(native["coverage"])
    if native["body_validation"] != "DEFERRED_TO_ORIGINAL_READER":
        raise ValueError("metadata observation cannot attest scientific output bodies")
    for row in rows(native["rows"]):
        fields(row, ("task_id", "attempt_id", "subwork_id", "state", "entry", "raw_return", "publication",
            "completion_receipt", "declared_outputs", "published_outputs", "source"))
        for key in ("task_id", "attempt_id", "subwork_id", "state", "entry", "raw_return", "publication", "completion_receipt"):
            text(row[key], maximum=512)
        count(row["declared_outputs"])
        count(row["published_outputs"])
        _source(row["source"])
    financial = fields(value["financial"], ("status", "allocation", "accounting", "lifecycle", "events",
        "event_coverage", "liabilities", "retained_volume_charges"))
    from empirical_lawhood.execution.deployment_budget import DeploymentAllocation
    allocation = DeploymentAllocation.from_document(financial["allocation"])
    if allocation.deployment_id != value["binding"]["deployment_id"]:
        raise ValueError("financial observation substitutes its allocation")
    for key in ("status", "event_coverage", "liabilities", "retained_volume_charges"):
        text(financial[key], maximum=512)
    for item in ([financial["accounting"]] if financial["accounting"] is not None else []):
        fields(item, ("status", "observed_utc", "recorded_utc", "source", "volume_billing_hours_upper", *MONEY_FIELDS))
        if item["status"] not in FINANCIAL_STATES[:3]:
            raise ValueError("accounting status must come from its original budget owner")
        utc(item["observed_utc"])
        utc(item["recorded_utc"])
        evidence_reference(item["source"])
        count(item["volume_billing_hours_upper"])
        for name in MONEY_FIELDS:
            exact_amount(item[name], signed=name == "remaining_usd")
    events = rows(financial["events"])
    for item in [*events, *([financial["lifecycle"]] if financial["lifecycle"] is not None else [])]:
        fields(item, ("status", "recorded_utc", "source"))
        if item["status"] not in FINANCIAL_STATES:
            raise ValueError("unknown financial lifecycle event")
        utc(item["recorded_utc"])
        evidence_reference(item["source"])
    validate_domain(value["domain"])
    if value["domain"]["binding"] != {name: value["binding"][name] for name in ("run_id", "packet_sha256")}:
        raise ValueError("domain observation changes the selected original work")
    runtime = fields(value["runtime"], ("provider", "selected_gpu", *RUNTIME_FIELDS, "scope"), optional=("observation",))
    for name, item in runtime.items():
        if name == "observation":
            continue
        if item is not None:
            text(item, maximum=512)
    observed_runtime = value["domain"].get("runtime")
    if observed_runtime is not None:
        if (observed_runtime["worker_source_sha256"] != value["binding"]["worker_source_sha256"]
                or runtime.get("observation") != observed_runtime
                or any(runtime[name] != observed_runtime[name] for name in RUNTIME_FIELDS)):
            raise ValueError("runtime observation differs from its selected worker or original domain source")
        if utc(observed_runtime["observed_utc"]) > utc(value["source_observed_utc"]):
            raise ValueError("runtime observation is later than its snapshot")
    elif runtime.get("observation") is not None or any(runtime[name] is not None for name in RUNTIME_FIELDS):
        raise ValueError("observed runtime requires its original domain source")
    returning = fields(value["return"], ("terminal", "stages"))
    if type(returning["terminal"]) is not bool:
        raise ValueError("return lifetime requires an explicit terminal observation")
    stages = rows(returning["stages"], maximum=len(RETURN_STAGES))
    if tuple(row.get("stage") for row in stages) != RETURN_STAGES:
        raise ValueError("return observation must retain its complete stage census")
    for row in stages:
        fields(row, ("stage", "status", "source", "scope"))
        text(row["status"])
        text(row["scope"], maximum=512)
        if row["source"] is not None:
            pin(row["source"])
    for row in rows(value["errors"], maximum=16):
        fields(row, ("scope", "reason"))
        text(row["scope"])
        text(row["reason"])
    if len(document_bytes(value)) > MAX_BYTES:
        raise ValueError("closed observation exceeds one MiB")
    return value


def observation_age(snapshot, *, now=None):
    now = datetime.now(timezone.utc) if now is None else utc(now)
    observed = utc(snapshot["source_observed_utc"])
    age = int((now - observed).total_seconds())
    if age < -5:
        raise ValueError("observation time is in the future")
    return {"age_seconds": max(age, 0), "stale": age > snapshot["stale_after_seconds"]}
