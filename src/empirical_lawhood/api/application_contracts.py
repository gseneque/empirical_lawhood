# SPDX-License-Identifier: MPL-2.0
"""Finite application selections, independent of scientific records and grants."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import ClassVar

from empirical_lawhood.api.results import ApiError, ApiResult, ErrorCategory, OperationStatus


APPLICATION_VERSION = "1.0.0"
PROJECTION_VERSION = "1.0.0"
MAX_REQUEST_BYTES = 256 * 1024
MAX_RESPONSE_BYTES = 4 * 1024**2
MAX_PAGE_ROWS = 200
MAX_TEXT_BYTES = 64 * 1024
MAX_EDIT_BYTES = 128 * 1024
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,191}\Z")


class ApplicationError(ValueError):
    """An explicitly safe application error, without protected source contents."""

    def __init__(self, code: str, message: str, *, field: str | None = None,
                 category: ErrorCategory = ErrorCategory.VALIDATION,
                 expected: str | None = None, actual: str | None = None,
                 authored_object: str | None = None, owner: str | None = None):
        super().__init__(message)
        self.code, self.field, self.category = code, field, category
        self.expected, self.actual = expected, actual
        self.authored_object, self.owner = authored_object, owner


def identifier(value: object, field: str) -> str:
    if type(value) is not str or not _ID.fullmatch(value):
        raise ApplicationError("INVALID_IDENTIFIER", "Select a bounded application identifier.", field=field)
    return value


def absolute_path(value: object, field: str) -> Path:
    if not isinstance(value, (str, Path)):
        raise ApplicationError("INVALID_PATH", "Select an absolute path.", field=field)
    text = str(value)
    if len(text.encode("utf-8")) > 4096 or any(ord(c) < 32 for c in text):
        raise ApplicationError("INVALID_PATH", "The selected path exceeds its application bound.", field=field)
    path = Path(text)
    if not path.is_absolute() or ".." in path.parts:
        raise ApplicationError("INVALID_PATH", "Select an absolute path without parent traversal.", field=field)
    return path


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ApplicationError("DUPLICATE_FIELD", "Application JSON repeats a field.")
        result[key] = value
    return result


def _invalid_number(_value):
    raise ApplicationError("INVALID_NUMBER", "Use exact integer controls or explicit Decimal records.")


def load_application_json(raw: bytes, *, maximum_bytes: int = MAX_REQUEST_BYTES):
    if type(raw) is not bytes or len(raw) > maximum_bytes:
        raise ApplicationError("PAYLOAD_LIMIT", "Application input exceeds its byte limit.")
    try:
        value = json.loads(raw, object_pairs_hook=_unique, parse_float=_invalid_number,
                           parse_constant=_invalid_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ApplicationError("INVALID_JSON", "Select a bounded strict JSON document.") from error
    return value


def exact_mapping(value, allowed, *, required=(), field="request"):
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ApplicationError("INVALID_OBJECT", "Select an application object.", field=field,
                               expected="A JSON object with string keys.", actual=type(value).__name__)
    if set(value) - set(allowed) or set(required) - set(value):
        raise ApplicationError("INVALID_FIELDS", "Application fields do not match the selected contract.", field=field,
            expected="Required fields: " + ", ".join(sorted(required)) + "; allowed: " + ", ".join(sorted(allowed)),
            actual="The required/allowed field census differs; supplied values are not disclosed.")
    return value


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Immutable locators and limits; contains no current-access decision."""

    context_id: str
    label: str
    python_executable: Path
    project_root: Path | None = None
    operator_profile: Path | None = None
    artifact_root_contract: Path | None = None
    catalog_relative_path: str | None = None
    approval_checker_trust: Path | None = None
    programme_request_path: Path | None = None
    read_access_paths: tuple[Path, ...] = ()
    maximum_parallel_tasks: int | None = None
    artifact_verification: str = "reduced"
    invocation_root: Path | None = None
    progress_root: Path | None = None
    input_root: Path | None = None
    collection_path: Path | None = None
    observation_root: Path | None = None
    operational_profile: Path | None = None

    SCHEMA: ClassVar[str] = "empirical-lawhood/application/context"
    VERSION: ClassVar[str] = APPLICATION_VERSION

    def __post_init__(self):
        identifier(self.context_id, "context_id")
        if type(self.label) is not str or not self.label.strip() or len(self.label) > 192:
            raise ApplicationError("INVALID_LABEL", "Select a short context label.", field="label")
        for name in ("python_executable", "project_root", "operator_profile", "artifact_root_contract",
                     "approval_checker_trust", "programme_request_path", "invocation_root", "progress_root", "input_root",
                     "collection_path", "observation_root", "operational_profile"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, Path) or absolute_path(value, name) != value:
                    raise ApplicationError("INVALID_PATH", "Context paths must be absolute Path selections.", field=name)
        if self.python_executable is None:
            raise ApplicationError("INTERPRETER_REQUIRED", "Select the engine interpreter.", field="python_executable")
        if type(self.read_access_paths) is not tuple or len(self.read_access_paths) > 32:
            raise ApplicationError("INVALID_ACCESS_SELECTION", "Select a bounded locator census.", field="read_access_paths")
        for path in self.read_access_paths:
            if not isinstance(path, Path):
                raise ApplicationError("INVALID_ACCESS_SELECTION", "Access locators must be Path selections.")
            absolute_path(path, "read_access_paths")
        if len(set(self.read_access_paths)) != len(self.read_access_paths):
            raise ApplicationError("INVALID_ACCESS_SELECTION", "Access locators must not repeat.")
        if self.maximum_parallel_tasks is not None and (
                type(self.maximum_parallel_tasks) is not int or not 1 <= self.maximum_parallel_tasks <= 64):
            raise ApplicationError("INVALID_WORKERS", "Use automatic selection or between one and 64 workers.",
                                   field="maximum_parallel_tasks", expected="null or an integer from 1 through 64",
                                   actual=type(self.maximum_parallel_tasks).__name__)
        if self.artifact_verification not in ("reduced", "strict"):
            raise ApplicationError("INVALID_VERIFICATION", "Select reduced or strict artifact verification.")
        if self.artifact_root_contract is not None and self.operator_profile is None:
            raise ApplicationError("PROFILE_REQUIRED", "A retained root selection requires its operator profile.")
        if self.catalog_relative_path is not None:
            path = Path(self.catalog_relative_path)
            if path.is_absolute() or ".." in path.parts or not path.parts or len(str(path)) > 4096:
                raise ApplicationError("INVALID_CATALOG", "Select a bounded relative catalog locator.")

    def to_document(self):
        value = {}
        for field in fields(self):
            item = getattr(self, field.name)
            # Old contexts keep their exact document/fingerprint and can still
            # enter older engines that do not negotiate these optional services.
            if field.name in ("collection_path", "observation_root", "operational_profile") and item is None:
                continue
            value[field.name] = [str(p) for p in item] if field.name == "read_access_paths" else str(item) if isinstance(item, Path) else item
        return {"schema": self.SCHEMA, "version": self.VERSION, "value": value}

    @classmethod
    def from_document(cls, document):
        exact_mapping(document, ("schema", "version", "value"), required=("schema", "version", "value"))
        if document["schema"] != cls.SCHEMA or document["version"] != cls.VERSION:
            raise ApplicationError("UNSUPPORTED_CONTEXT_VERSION", "This engine does not support the selected context contract.")
        names = {field.name for field in fields(cls)}
        value = dict(exact_mapping(document["value"], names, required=("context_id", "label", "python_executable"), field="context"))
        for name in ("python_executable", "project_root", "operator_profile", "artifact_root_contract",
                     "approval_checker_trust", "programme_request_path", "invocation_root", "progress_root", "input_root",
                     "collection_path", "observation_root", "operational_profile"):
            if value.get(name) is not None:
                value[name] = absolute_path(value[name], name)
        if "read_access_paths" in value:
            if type(value["read_access_paths"]) is not list:
                raise ApplicationError("INVALID_ACCESS_SELECTION", "Select an array of access locator paths.")
            value["read_access_paths"] = tuple(absolute_path(path, "read_access_paths") for path in value["read_access_paths"])
        return cls(**value)

    def fingerprint(self):
        return sha256(json.dumps(self.to_document(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ApplicationRequest:
    request_id: str
    context_id: str
    operation: str
    parameters: tuple[tuple[str, object], ...] = ()

    SCHEMA: ClassVar[str] = "empirical-lawhood/application/request"
    VERSION: ClassVar[str] = APPLICATION_VERSION

    def __post_init__(self):
        for field in ("request_id", "context_id", "operation"):
            identifier(getattr(self, field), field)
        if type(self.parameters) is not tuple or len(self.parameters) > 16:
            raise ApplicationError("INVALID_PARAMETERS", "Select a bounded parameter object.")
        names = []
        for pair in self.parameters:
            if type(pair) is not tuple or len(pair) != 2:
                raise ApplicationError("INVALID_PARAMETERS", "Select named application parameters.")
            key, value = pair
            identifier(key, "parameters")
            if type(value) not in (str, int, bool, type(None)):
                raise ApplicationError("INVALID_PARAMETERS", "Application controls must be scalar values.", field=key)
            maximum = MAX_EDIT_BYTES if key == "text" else 4096
            if type(value) is str and len(value.encode("utf-8")) > maximum:
                raise ApplicationError("PARAMETER_LIMIT", "Application control exceeds its byte limit.", field=key)
            names.append(key)
        if len(set(names)) != len(names):
            raise ApplicationError("DUPLICATE_FIELD", "Application parameters repeat a field.")

    def to_document(self):
        return {"schema": self.SCHEMA, "version": self.VERSION, "request_id": self.request_id,
                "context_id": self.context_id, "operation": self.operation, "parameters": dict(self.parameters)}

    @classmethod
    def from_document(cls, document):
        names = ("schema", "version", "request_id", "context_id", "operation", "parameters")
        exact_mapping(document, names, required=names)
        if document["schema"] != cls.SCHEMA or document["version"] != cls.VERSION:
            raise ApplicationError("UNSUPPORTED_REQUEST_VERSION", "This engine does not support the selected request contract.")
        if type(document["parameters"]) is not dict:
            raise ApplicationError("INVALID_PARAMETERS", "Select a parameter object.")
        return cls(document["request_id"], document["context_id"], document["operation"],
                   tuple(sorted(document["parameters"].items())))


def error_result(operation: str, error: BaseException, *, authored_object: str | None = None) -> ApiResult:
    if isinstance(error, ApplicationError):
        code, message, category, field = error.code, str(error), error.category, error.field
    elif isinstance(error, PermissionError):
        code, message, category, field = "CURRENT_CUSTODY_REFUSED", "The owning service refused current source, access or custody.", ErrorCategory.AUTHORITY, None
    elif isinstance(error, FileNotFoundError):
        code, message, category, field = "LOCATOR_UNAVAILABLE", "A selected locator is unavailable.", ErrorCategory.NOT_FOUND, None
    elif isinstance(error, OSError):
        code, message, category, field = "STORAGE_UNAVAILABLE", "The selected storage operation is unavailable.", ErrorCategory.STORAGE, None
    elif isinstance(error, (ValueError, TypeError)):
        code, message, category, field = "OWNER_CONTRACT_REFUSED", "The selected operands do not satisfy the owning contract.", ErrorCategory.VALIDATION, None
    else:
        code, message, category, field = "APPLICATION_FAILURE", "The application invocation failed. Inspect its retained diagnostic classification.", ErrorCategory.INTERNAL, None
    status = (OperationStatus.BLOCKED if category in (ErrorCategory.AUTHORITY, ErrorCategory.STORAGE, ErrorCategory.CAPABILITY)
              else OperationStatus.NOT_FOUND if category is ErrorCategory.NOT_FOUND
              else OperationStatus.CONFLICT if category is ErrorCategory.CONFLICT
              else OperationStatus.FAILED if category is ErrorCategory.INTERNAL else OperationStatus.INVALID)
    from empirical_lawhood.api.diagnostics import explain_failure
    from empirical_lawhood.api.invocation_retention import retain_failure_diagnostic
    diagnostic = explain_failure(operation=operation, error=error, contract=code,
        authored_object=getattr(error, "authored_object", None) or authored_object,
        expected=getattr(error, "expected", None), actual=getattr(error, "actual", None),
        owner=getattr(error, "owner", None))
    diagnostic = retain_failure_diagnostic(diagnostic)
    return ApiResult(operation, status, errors=(ApiError(category, code, message, field, diagnostic),), reason_codes=(code,))


def transport_value(value, *, _depth=0):
    """Preserve scientific exactness while avoiding JavaScript integer rounding."""
    if _depth > 64:
        raise ApplicationError("PROJECTION_DEPTH_LIMIT", "The projection exceeds its depth limit.")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ApplicationError("INVALID_DECIMAL", "The owning result contains a nonfinite Decimal.")
        return {"decimal": str(value)}
    if type(value) is int and abs(value) > 2**53 - 1:
        return {"integer": str(value)}
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, (list, tuple)):
        return [transport_value(item, _depth=_depth+1) for item in value]
    if isinstance(value, dict) and all(type(key) is str for key in value):
        return {key: transport_value(item, _depth=_depth+1) for key, item in value.items()}
    raise ApplicationError("INVALID_PROJECTION_VALUE", "The owning projection contains an unsupported value.")


def _immutable_payload(value):
    if type(value) in (list, tuple):
        return tuple(_immutable_payload(item) for item in value)
    if type(value) is dict:
        return {key: _immutable_payload(item) for key, item in value.items()}
    return value


def application_result(operation, payload):
    """Adapt JSON-facing owner projections to the established result envelope."""
    return ApiResult(operation, OperationStatus.SUCCEEDED, _immutable_payload(payload))


def response_bytes(result: ApiResult, *, maximum_bytes=MAX_RESPONSE_BYTES):
    value = transport_value(replace(result, payload=_immutable_payload(result.payload)).to_mapping())
    chunks, size = [], 0
    for chunk in json.JSONEncoder(sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")).iterencode(value):
        body = chunk.encode("ascii")
        size += len(body)
        if size + 1 > maximum_bytes:
            raise ApplicationError("RESPONSE_LIMIT", "Select a smaller projection or page.")
        chunks.append(body)
    return b"".join(chunks) + b"\n"
