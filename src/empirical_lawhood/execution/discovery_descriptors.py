# SPDX-License-Identifier: MPL-2.0
"""Inward static environment and configuration facts; no imports of their owners."""

from dataclasses import dataclass
from pathlib import PurePosixPath
import re

from empirical_lawhood.science.records.serialization import validate_stable_id


def _source_path(value: str) -> None:
    if (type(value) is not str or not value or "\\" in value
            or PurePosixPath(value).is_absolute()
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError("discovery paths belong to the selected source distribution")


@dataclass(frozen=True, slots=True)
class EnvironmentDeclaration:
    """Exact metadata observations for a declared route, separate from readiness."""

    route_id: str
    python_version: str
    distribution_versions: tuple[tuple[str, str], ...]
    lock_path: str = "uv.lock"
    python_implementation: str = "CPython"
    descriptor_version: str = "1.0.0"
    dependency_groups: tuple[str, ...] = ()
    supported_platforms: tuple[tuple[str, str], ...] = (("Linux", "x86_64"),)

    def __post_init__(self):
        validate_stable_id(self.route_id)
        _source_path(self.lock_path)
        if (self.descriptor_version != "1.0.0" or type(self.python_version) is not str
                or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", self.python_version) is None
                or self.python_implementation not in ("CPython", "PyPy")):
            raise ValueError("environment descriptor requires its exact supported interpreter contract")
        rows = self.distribution_versions
        if type(rows) is not tuple or len(rows) > 512:
            raise TypeError("environment dependencies require a bounded immutable tuple")
        for row in rows:
            if (type(row) is not tuple or len(row) != 2 or any(type(v) is not str for v in row)
                    or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", row[0]) is None
                    or re.fullmatch(r"[0-9][A-Za-z0-9._!+-]{0,127}", row[1]) is None):
                raise ValueError("environment dependency requires an exact distribution and version")
        names = tuple(re.sub(r"[-_.]+", "-", row[0]).lower() for row in rows)
        if len(names) != len(set(names)):
            raise ValueError("environment descriptor repeats a distribution")
        if (type(self.dependency_groups) is not tuple
                or len(set(self.dependency_groups)) != len(self.dependency_groups)
                or any(type(v) is not str or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", v) is None
                       for v in self.dependency_groups)):
            raise ValueError("environment groups require unique code-owned identifiers")
        if (type(self.supported_platforms) is not tuple or not self.supported_platforms
                or len(set(self.supported_platforms)) != len(self.supported_platforms)
                or any(type(row) is not tuple or len(row) != 2
                       or any(type(v) is not str or not v for v in row) for row in self.supported_platforms)):
            raise ValueError("environment support requires explicit system and architecture pairs")


@dataclass(frozen=True, slots=True)
class ConfigurationDeclaration:
    """Cold input-role facts; the API resolves an explicit record only on request."""

    consumer: str
    schema_id: str | None
    record_module: str | None
    record_name: str | None
    disposition: str
    maximum_bytes: int | None
    requires_canonical: bool
    command: str
    owner: str
    supplied_inputs: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.consumer)
        if self.schema_id is not None and (type(self.schema_id) is not str or not self.schema_id):
            raise ValueError("configuration descriptor requires an exact schema or an explicit helper")
        if (self.record_module is None) != (self.record_name is None):
            raise ValueError("configuration descriptor must retain both record owner locators")
        if self.record_module is not None and (
                type(self.record_module) is not str or not self.record_module.startswith("empirical_lawhood.")
                or not all(part.isidentifier() for part in self.record_module.split("."))
                or type(self.record_name) is not str or not self.record_name.isidentifier()):
            raise ValueError("configuration descriptor record locators are code-owned Python identifiers")
        if (self.disposition not in ("editable", "retained", "import", "helper")
                or type(self.requires_canonical) is not bool
                or any(type(v) is not str or not v.strip() for v in (self.command, self.owner))):
            raise ValueError("configuration descriptor omits its supported role or consuming boundary")
        if self.maximum_bytes is not None and (type(self.maximum_bytes) is not int or self.maximum_bytes <= 0):
            raise ValueError("configuration byte bound must be a positive exact integer")
        if type(self.supplied_inputs) is not tuple or len(set(self.supplied_inputs)) != len(self.supplied_inputs):
            raise ValueError("configuration descriptor requires unique immutable source paths")
        for path in self.supplied_inputs:
            _source_path(path)
