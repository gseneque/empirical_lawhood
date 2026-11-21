# SPDX-License-Identifier: MPL-2.0
"""Static software installation selections; no source or scientific admission."""

from dataclasses import dataclass
import re

from empirical_lawhood.science.records.serialization import validate_sha256, validate_stable_id


@dataclass(frozen=True, slots=True)
class WorkerEnvironment:
    role_id: str
    environment_id: str
    selection: str = "controller"

    def __post_init__(self):
        validate_stable_id(self.role_id)
        validate_stable_id(self.environment_id)
        if self.role_id == "controller" or self.selection not in ("controller", "explicit"):
            raise ValueError("worker environment requires a distinct role and explicit selection policy")


@dataclass(frozen=True, slots=True)
class ExternalSoftware:
    software_id: str
    kind: str
    sha256: str
    maximum_bytes: int
    description: str

    def __post_init__(self):
        validate_stable_id(self.software_id)
        validate_sha256(self.sha256)
        if (self.kind not in ("executable", "module-file") or type(self.maximum_bytes) is not int
                or not 0 < self.maximum_bytes <= 512 * 1024**2
                or type(self.description) is not str or not self.description.strip()):
            raise ValueError("external software requires a bounded exact file identity and role")


@dataclass(frozen=True, slots=True)
class WorkflowInstallationDeclaration:
    workflow_id: str
    profile_id: str
    adapter_module: str
    adapter_version: str
    controller_environment: str
    workers: tuple[WorkerEnvironment, ...] = ()
    external_software: tuple[ExternalSoftware, ...] = ()
    source_prerequisites: tuple[str, ...] = ()
    continuing_source_prerequisites: tuple[str, ...] = ()
    descriptor_version: str = "1.0.0"

    def __post_init__(self):
        for identifier in (self.workflow_id, self.profile_id, self.controller_environment):
            validate_stable_id(identifier)
        if (type(self.adapter_module) is not str or not self.adapter_module.startswith("empirical_lawhood.")
                or not all(part.isidentifier() for part in self.adapter_module.split("."))
                or type(self.adapter_version) is not str
                or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", self.adapter_version) is None
                or self.descriptor_version != "1.0.0"):
            raise ValueError("workflow installation requires its code-owned adapter and exact descriptor revision")
        for rows, kind, key in ((self.workers, WorkerEnvironment, "role_id"),
                                (self.external_software, ExternalSoftware, "software_id")):
            if (type(rows) is not tuple or len(rows) > 32 or any(type(row) is not kind for row in rows)
                    or len({getattr(row, key) for row in rows}) != len(rows)):
                raise ValueError("workflow installation repeats or substitutes a bounded software role")
        for rows in (self.source_prerequisites, self.continuing_source_prerequisites):
            if (type(rows) is not tuple or len(rows) > 64 or len(set(rows)) != len(rows)
                    or any(type(value) is not str or not value.strip() or len(value) > 4096 for value in rows)):
                raise ValueError("workflow installation requires bounded unique prerequisite descriptions")
