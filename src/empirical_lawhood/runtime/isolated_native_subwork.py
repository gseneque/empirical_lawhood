# SPDX-License-Identifier: MPL-2.0
"""Selected interpreter entry inside an already entered native parent task."""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import PurePath
import re
from typing import ClassVar, TYPE_CHECKING

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.execution import BoundedInputReader
if TYPE_CHECKING:
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract


@dataclass(frozen=True, slots=True)
class IsolatedNativeEntrySelection(CanonicalRecord):
    """Exact operational entry; no issue, qualification or retry authority."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/isolated-native-entry-selection"
    entry_id: str
    interpreter_path: str
    interpreter_sha256: str
    entry_module: str
    entry_function: str
    entry_source_path: str
    entry_source_sha256: str
    invocation_path: str
    invocation_sha256: str
    environment_sha256: str

    def __post_init__(self):
        validate_stable_id(self.entry_id)
        for name in ("interpreter_sha256", "entry_source_sha256", "invocation_sha256", "environment_sha256"):
            validate_sha256(getattr(self, name), field_name=name)
        for name in ("interpreter_path", "entry_source_path", "invocation_path"):
            value = getattr(self, name)
            if type(value) is not str or not PurePath(value).is_absolute() or ".." in PurePath(value).parts:
                raise ValueError("isolated native entry requires exact absolute selected paths")
        if not re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", self.entry_module):
            raise ValueError("isolated native entry requires a selected Python module")
        if not re.fullmatch(r"[A-Za-z_]\w*", self.entry_function):
            raise ValueError("isolated native entry requires a selected Python function")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.entry_id, self)


@dataclass(frozen=True, slots=True)
class IsolatedNativeInvocation:
    """Path-free, immutable selected invocation; the caller chooses read size."""

    selection: ObjectIdentity
    size_bytes: int
    content_sha256: str
    _reader: BoundedInputReader = field(repr=False, compare=False)
    prepared_invocation: "PreparedInvocationContract | None" = field(default=None, repr=False, compare=False)
    _prepared_identity: ObjectIdentity | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        if (type(self.selection) is not ObjectIdentity
                or self.selection.object_schema != IsolatedNativeEntrySelection.SCHEMA
                or type(self.size_bytes) is not int or self.size_bytes < 0):
            raise ValueError("isolated invocation changes its selected identity or complete byte count")
        validate_sha256(self.content_sha256, field_name="content_sha256")
        if self.prepared_invocation is not None:
            from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
            if type(self.prepared_invocation) is not PreparedInvocationContract:
                raise ValueError("isolated invocation requires its exact typed prepared binding")
            self.prepared_invocation.require_complete()
            selected = self.prepared_invocation.native_work
            if selected is not None and selected.isolated_selection is not None and (
                    self.selection != selected.isolated_selection.identity
                    or self.content_sha256 != selected.isolated_selection.invocation_sha256):
                raise ValueError("isolated invocation changes its frozen selection/input binding")
            object.__setattr__(self, "_prepared_identity", self.prepared_invocation.identity)

    def validate_prepared_invocation(self):
        if self.prepared_invocation is not None:
            from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract
            if type(self.prepared_invocation) is not PreparedInvocationContract:
                raise ValueError("isolated invocation changes its exact typed prepared binding")
        if (self.prepared_invocation is None) != (self._prepared_identity is None) or (
                self.prepared_invocation is not None and self.prepared_invocation.identity != self._prepared_identity):
            raise ValueError("isolated invocation changes its exact original prepared binding")

    @property
    def bytes_read(self):
        return self._reader.bytes_read

    def read(self, size=-1):
        self.validate_prepared_invocation()
        if type(size) is not int or size < -1:
            raise ValueError("isolated invocation requires an integer read size")
        return self._reader.read(size)

    def iter_chunks(self, *, maximum_chunk_bytes=1024 * 1024):
        if type(maximum_chunk_bytes) is not int or maximum_chunk_bytes <= 0:
            raise ValueError("isolated invocation requires a positive integer read frame")
        while chunk := self.read(maximum_chunk_bytes):
            yield chunk

    def cursor(self):
        """Own an independent position over the same kernel-sealed bytes."""
        self.validate_prepared_invocation()
        return IsolatedNativeInvocation(self.selection, self.size_bytes,
            self.content_sha256, self._reader.cursor(), self.prepared_invocation)

    def close(self):
        self._reader.close()


@dataclass(frozen=True, slots=True)
class IsolatedNativeEntryReturn(CanonicalRecord):
    """Known interpreter return; nested contacts retain their own dispositions."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/isolated-native-entry-return"
    selection: ObjectIdentity
    returncode: int
    handshake_completed: bool
    progress_requests: int
    wall_seconds: Decimal
    inclusive_cpu_seconds: Decimal
    peak_rss_bytes: int | None = None

    def __post_init__(self):
        if (type(self.selection) is not ObjectIdentity
                or self.selection.object_schema != IsolatedNativeEntrySelection.SCHEMA
                or type(self.returncode) is not int or type(self.handshake_completed) is not bool
                or type(self.progress_requests) is not int or self.progress_requests < 0):
            raise ValueError("isolated native return substitutes its observed entry/return census")
        for value in (self.wall_seconds, self.inclusive_cpu_seconds):
            if type(value) is not Decimal or not value.is_finite() or value < 0:
                raise ValueError("isolated native return requires actual nonnegative measured clocks")
        if self.peak_rss_bytes is not None and (type(self.peak_rss_bytes) is not int or self.peak_rss_bytes < 0):
            raise ValueError("isolated native peak memory must be measured or unknown")


@dataclass(frozen=True, slots=True)
class IsolatedNativeProcessStart(CanonicalRecord):
    """Observed process locator durably retained before acknowledging domain entry."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/isolated-native-process-start"
    selection: ObjectIdentity
    parent_contact: NativeEffectContact
    child_pid: int
    creator_pid: int
    process_group_id: int
    pid_namespace: str | None

    def __post_init__(self):
        if (type(self.selection) is not ObjectIdentity
                or self.selection.object_schema != IsolatedNativeEntrySelection.SCHEMA
                or type(self.parent_contact) is not NativeEffectContact
                or any(type(value) is not int or value <= 0 for value in (self.child_pid, self.creator_pid, self.process_group_id))
                or (self.pid_namespace is not None and (type(self.pid_namespace) is not str or not self.pid_namespace))):
            raise ValueError("isolated native start substitutes its actual process/parent locator")
