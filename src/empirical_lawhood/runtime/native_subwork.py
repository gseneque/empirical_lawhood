# SPDX-License-Identifier: MPL-2.0
"""Immutable native subcall progress, separate from scientific assessment.

These records refine an already entered native task. They confer no execution,
issue, reveal, qualification or retry authority, and introduce no task scheduler.
Adapters select the scientific configuration, complete operands and effect slots.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import ClassVar, Protocol

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    require_sorted_unique_ids,
    require_sorted_unique_strings,
    validate_nonempty,
    validate_schema,
    validate_sha256,
    validate_stable_id,
)
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.time import validate_utc_timestamp
from empirical_lawhood.runtime.artifacts import (
    ArtifactManifest, ArtifactProfile, ArtifactSemanticValidation, CanonicalTaskReceipt,
)
from empirical_lawhood.runtime.native_effects import NativeEffectContact, NativeEntryRefused


@dataclass(frozen=True, slots=True)
class NativeSubworkInputMismatch:
    """One operational input refusal; no scientific disposition or authority."""

    operand_id: str
    reason: str


class NativeSubworkInputError(ValueError):
    """Complete bounded metadata mismatch census for a selected definition."""

    def __init__(self, mismatches: tuple[NativeSubworkInputMismatch, ...]):
        self.mismatches = mismatches
        super().__init__("; ".join(f"{row.operand_id}: {row.reason}" for row in mismatches))


@dataclass(frozen=True, slots=True)
class NativeSubworkOutput(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-output"
    output_id: str
    payload_schema: str
    profile: ArtifactProfile
    media_type: str
    semantic_validation: ArtifactSemanticValidation | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.output_id, field_name="output_id")
        validate_schema(self.payload_schema)
        validate_nonempty(self.media_type, field_name="media_type")
        if type(self.profile) is not ArtifactProfile:
            raise ValueError("native subwork output requires its exact artifact profile")
        if self.semantic_validation is not None and (
                type(self.semantic_validation) is not ArtifactSemanticValidation
                or self.semantic_validation.payload_schema != self.payload_schema
                or self.semantic_validation.profile is not self.profile):
            raise ValueError("native subwork output substitutes its semantic validator")


@dataclass(frozen=True, slots=True)
class NativeSubworkDefinition(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-definition"
    subwork_id: str
    operation_id: str
    parent_contact: NativeEffectContact
    configuration: ObjectIdentity
    sources: tuple[ObjectIdentity, ...]
    code_sources_sha256: str
    dependency_lock_sha256: str
    input_materialization_ids: tuple[str, ...]
    streams: tuple[ObjectIdentity, ...]
    outputs: tuple[NativeSubworkOutput, ...]
    roster_id: str = "selected.native-subwork"

    def __post_init__(self) -> None:
        validate_stable_id(self.subwork_id, field_name="subwork_id")
        validate_stable_id(self.operation_id, field_name="operation_id")
        validate_stable_id(self.roster_id, field_name="roster_id")
        if type(self.parent_contact) is not NativeEffectContact:
            raise ValueError("native subwork requires its exact parent contact")
        if type(self.configuration) is not ObjectIdentity:
            raise ValueError("native subwork requires an immutable configuration")
        for name in ("sources", "streams"):
            rows = getattr(self, name)
            if any(type(row) is not ObjectIdentity for row in rows):
                raise ValueError("native subwork source/stream identities are invalid")
            require_sorted_unique_ids(rows, attribute="object_id", field_name=name)
        validate_sha256(self.code_sources_sha256, field_name="code_sources_sha256")
        validate_sha256(self.dependency_lock_sha256, field_name="dependency_lock_sha256")
        require_sorted_unique_strings(
            self.input_materialization_ids, field_name="input_materialization_ids",
            allow_empty=False,
        )
        if any(type(row) is not NativeSubworkOutput for row in self.outputs):
            raise ValueError("native subwork output census is invalid")
        require_sorted_unique_ids(self.outputs, attribute="output_id", field_name="outputs")

    @property
    def identity(self) -> ObjectIdentity:
        return ObjectIdentity.from_record(self.subwork_id, self)


@dataclass(frozen=True, slots=True)
class NativeSubworkRoster(CanonicalRecord):
    """Selected full unit/slot denominator, including work left unentered."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-roster"
    roster_id: str
    parent_contact: NativeEffectContact
    subworks: tuple[ObjectIdentity, ...]
    parent_subwork: ObjectIdentity | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.roster_id, field_name="roster_id")
        if type(self.parent_contact) is not NativeEffectContact:
            raise ValueError("native subwork roster requires its exact parent contact")
        if any(type(row) is not ObjectIdentity or row.object_schema != NativeSubworkDefinition.SCHEMA
               for row in self.subworks):
            raise ValueError("native subwork roster substitutes its definition identities")
        if not self.subworks:
            raise ValueError("native subwork roster requires its selected nonempty denominator")
        require_sorted_unique_ids(self.subworks, attribute="object_id", field_name="subworks")
        if self.parent_subwork is not None and (
                type(self.parent_subwork) is not ObjectIdentity
                or self.parent_subwork.object_schema != NativeSubworkDefinition.SCHEMA):
            raise ValueError("conditional native subwork roster substitutes its parent subwork")
        if self.parent_subwork is None and self.roster_id != "selected.native-subwork":
            raise ValueError("native task requires one complete initial native subwork roster")


@dataclass(frozen=True, slots=True)
class NativeSubworkBegin(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-begin"
    definition: ObjectIdentity

    def __post_init__(self) -> None:
        if self.definition.object_schema != NativeSubworkDefinition.SCHEMA:
            raise ValueError("native subwork begin substitutes its definition")


@dataclass(frozen=True, slots=True)
class NativeSubworkContact(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-contact"
    begin: ObjectIdentity

    def __post_init__(self) -> None:
        if self.begin.object_schema != NativeSubworkBegin.SCHEMA:
            raise ValueError("native subwork contact substitutes its begin record")


@dataclass(frozen=True, slots=True)
class NativeSubworkCallEntry(CanonicalRecord):
    """Observed call boundary, distinct from dispatch and possible contact.

    Publication precedes the native call. A lost process after this boundary
    still cannot prove a return or authorize another invocation.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-call-entry"
    definition: ObjectIdentity
    contact: ObjectIdentity
    invocation: ObjectIdentity
    entered_at_utc: str

    def __post_init__(self) -> None:
        if (type(self.definition) is not ObjectIdentity
                or self.definition.object_schema != NativeSubworkDefinition.SCHEMA
                or type(self.contact) is not ObjectIdentity
                or self.contact.object_schema != NativeSubworkContact.SCHEMA
                or type(self.invocation) is not ObjectIdentity
                or self.invocation.object_schema != "empirical-lawhood/runtime/prepared-invocation-contract"):
            raise ValueError("native call entry changes its exact definition, contact or invocation")
        validate_utc_timestamp(self.entered_at_utc, field_name="entered_at_utc")


@dataclass(frozen=True, slots=True)
class NativeSubworkCallReturn(CanonicalRecord):
    """Raw call return/error, before scientific classification or publication."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-call-return"
    entry: ObjectIdentity
    returned_at_utc: str
    error_type: str | None = None
    return_code: int | None = None

    def __post_init__(self) -> None:
        if (type(self.entry) is not ObjectIdentity
                or self.entry.object_schema != NativeSubworkCallEntry.SCHEMA):
            raise ValueError("native call return changes its exact observed entry")
        validate_utc_timestamp(self.returned_at_utc, field_name="returned_at_utc")
        if self.error_type is not None:
            if (type(self.error_type) is not str or not self.error_type.isidentifier()
                    or len(self.error_type.encode("utf-8")) > 256):
                raise ValueError("native call return error type requires its bounded actual class name")
        if self.return_code is not None and (type(self.return_code) is not int
                or not -(2**31) <= self.return_code < 2**31):
            raise ValueError("native call return requires its bounded actual integer process code")


@dataclass(frozen=True, slots=True)
class NativeSubworkCompletion(CanonicalRecord):
    """Known return/error and actual cost, never a scientific positive by default.

Returned scientific negatives use operational SUCCEEDED with their actual
scientific records. A caught native error uses FAILED and retains partial
outputs. None means unknown cost; nested windows must not be summed twice.
Stream identities name actually consumed selected streams, not fresh evidence
or an implicit mid-trajectory random-state restart contract.
"""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-completion"
    definition: ObjectIdentity
    contact: ObjectIdentity
    operational_status: OperationalStatus
    output_ids: tuple[str, ...]
    omitted_output_ids: tuple[str, ...]
    consumed_streams: tuple[ObjectIdentity, ...]
    unconsumed_streams: tuple[ObjectIdentity, ...]
    unknown_streams: tuple[ObjectIdentity, ...]
    cost: InquiryCost
    cost_scope: str
    peak_rss_bytes: int | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if (self.definition.object_schema != NativeSubworkDefinition.SCHEMA
                or self.contact.object_schema != NativeSubworkContact.SCHEMA):
            raise ValueError("native subwork completion changes its progress identities")
        if type(self.operational_status) is not OperationalStatus or self.operational_status not in (
                OperationalStatus.SUCCEEDED, OperationalStatus.FAILED):
            raise ValueError("native subwork completion requires a known return/error")
        for name in ("output_ids", "omitted_output_ids", "reason_codes"):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        if set(self.output_ids).intersection(self.omitted_output_ids):
            raise ValueError("native subwork output and omission census overlap")
        if self.operational_status is OperationalStatus.SUCCEEDED and (
                self.omitted_output_ids or self.reason_codes):
            raise ValueError("successful native subwork omits outputs or retains operational errors")
        if self.operational_status is OperationalStatus.FAILED and not self.reason_codes:
            raise ValueError("failed native subwork requires its actual error reasons")
        all_streams = []
        for name in ("consumed_streams", "unconsumed_streams", "unknown_streams"):
            rows = getattr(self, name)
            if any(type(row) is not ObjectIdentity for row in rows):
                raise ValueError("native subwork stream census contains invalid identities")
            require_sorted_unique_ids(rows, attribute="object_id", field_name=name)
            all_streams.extend(row.object_id for row in rows)
        if len(set(all_streams)) != len(all_streams):
            raise ValueError("native subwork consumed/unconsumed/unknown stream census overlaps")
        if type(self.cost) is not InquiryCost:
            raise ValueError("native subwork requires measured-or-unknown actual costs")
        validate_nonempty(self.cost_scope, field_name="cost_scope")
        if self.peak_rss_bytes is not None and (
                type(self.peak_rss_bytes) is not int or self.peak_rss_bytes < 0):
            raise ValueError("native subwork peak memory must be nonnegative or unknown")


def require_native_completion_receipt(
    completion: NativeSubworkCompletion,
    receipt: CanonicalTaskReceipt,
    *,
    outcome_access: OutcomeAccess | None = None,
    visibility_ceiling: VisibilityCeiling | None = None,
) -> None:
    """Join embedded completion bytes to their exact native receipt publication.

    This pure check supplies no storage authentication or authority. Callers
    retain their original definition, task, physical output and scientific
    stream-use checks; the storage owner authenticates the receipt itself.
    """
    if type(completion) is not NativeSubworkCompletion or type(receipt) is not CanonicalTaskReceipt:
        raise TypeError("native completion custody requires its exact completion and receipt types")
    logical_id = receipt.task_id + ".completion"
    logical = tuple(row for row in receipt.output_logical_artifacts if row.logical_artifact_id == logical_id)
    physical = tuple(row for row in receipt.output_materializations if row.logical_artifact_id == logical_id)
    raw = completion.canonical_bytes()
    digest = sha256(raw).hexdigest()
    if (len(logical) != 1 or len(physical) != 1
            or receipt.operational_status is not completion.operational_status
            or receipt.reason_codes != completion.reason_codes):
        raise ValueError("native receipt omits its exact canonical completion publication")
    selected, materialization = logical[0], physical[0]
    if ((selected.payload_schema, selected.profile, selected.media_type, selected.content_sha256,
            materialization.physical_sha256, materialization.size_bytes, materialization.compression,
            materialization.partition_selector) != (NativeSubworkCompletion.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", digest, digest, len(raw), "none", None)
            or outcome_access is not None and selected.outcome_access is not outcome_access
            or visibility_ceiling is not None and selected.visibility_ceiling is not visibility_ceiling
            or {row.identity for row in selected.lineage_parents} != {completion.definition, completion.contact}
            or len(selected.lineage_parents) != 2
            or any((row.visibility_ceiling, row.outcome_access) !=
                (selected.visibility_ceiling, selected.outcome_access) for row in selected.lineage_parents)):
        raise ValueError("native receipt changes its exact completion bytes, access or lineage")


@dataclass(frozen=True, slots=True)
class NativeSubworkPartialOutput(CanonicalRecord):
    """Authenticated received prefix, never the declared scientific output."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/runtime/native-subwork-partial-output"
    definition: ObjectIdentity
    contact: ObjectIdentity
    output_id: str
    maximum_bytes: int
    expected_size_bytes: int | None
    expected_physical_sha256: str | None
    received_size_bytes: int
    received_physical_sha256: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if (self.definition.object_schema != NativeSubworkDefinition.SCHEMA
                or self.contact.object_schema != NativeSubworkContact.SCHEMA):
            raise ValueError("partial native output substitutes its entered progress")
        validate_stable_id(self.output_id, field_name="output_id")
        if (type(self.maximum_bytes) is not int or self.maximum_bytes <= 0
                or type(self.received_size_bytes) is not int
                or not 0 <= self.received_size_bytes <= self.maximum_bytes
                or (self.expected_size_bytes is None) != (self.expected_physical_sha256 is None)
                or self.expected_size_bytes is not None and (
                    type(self.expected_size_bytes) is not int
                    or not 0 <= self.expected_size_bytes <= self.maximum_bytes)):
            raise ValueError("partial native output changes its exact received/selected byte census")
        validate_sha256(self.received_physical_sha256)
        if self.expected_physical_sha256 is not None:
            validate_sha256(self.expected_physical_sha256)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes", allow_empty=False)


class NativeSubworkState(StrEnum):
    NOT_ENTERED = "NOT_ENTERED"
    BEGUN = "BEGUN"
    UNKNOWN_COMPLETION = "UNKNOWN_COMPLETION"
    COMPLETED = "COMPLETED"


class NativeSubworkUncertainContact(ValueError):
    """Retained contact without completion forbids automatic duplicate effects."""


class NativeSubworkReceiptPublicationPending(OSError):
    """A known native return still lacks complete durable finalization custody."""


class NativeSubworkObservationPublicationError(RuntimeError):
    """Call observation publication was not acknowledged; no native error claim."""


@dataclass(frozen=True, slots=True)
class NativeSubworkInspection:
    """Compact authenticated progress; scientific payload bytes remain external."""

    definition: NativeSubworkDefinition
    state: NativeSubworkState
    begin: NativeSubworkBegin | None = None
    contact: NativeSubworkContact | None = None
    completion: NativeSubworkCompletion | None = None
    receipt: CanonicalTaskReceipt | None = None
    outputs: tuple[ArtifactManifest, ...] = ()
    partial_outputs: tuple[ArtifactManifest, ...] = ()
    partial_output_records: tuple[NativeSubworkPartialOutput, ...] = ()
    call_entry: NativeSubworkCallEntry | None = None
    call_return: NativeSubworkCallReturn | None = None

    @property
    def native_return_status(self) -> OperationalStatus | None:
        """Observed call status, separately from outputs and receipt completeness.

        A normal raw return does not establish successful publication or a
        scientific result. Completion can supply retained return knowledge when
        individual call observations were not recorded; it supplies no call
        timestamps or exception facts.
        """
        if self.call_return is not None:
            failed = (self.call_return.error_type is not None
                or self.call_return.return_code not in (None, 0))
            return OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED
        return None if self.completion is None else self.completion.operational_status

    @property
    def has_uncertain_contact(self) -> bool:
        return self.contact is not None and self.native_return_status is None


class NativeSubworkEntry(Protocol):
    """Opaque live-creator handle; persisted bytes cannot recreate one."""

    @property
    def definition(self) -> NativeSubworkDefinition: ...


class NativeSubworkProgress(Protocol):
    """Coordinator-backed progress port; it supplies no execution authority."""

    @property
    def parent_contact(self) -> NativeEffectContact: ...

    def inspect(self, definition: NativeSubworkDefinition) -> NativeSubworkInspection: ...

    def iter_inspections(self, definitions: Iterable[NativeSubworkDefinition]) -> Iterator[NativeSubworkInspection]: ...

    def recover(self, definition: NativeSubworkDefinition) -> NativeSubworkInspection | None: ...

    def resolve_completed_definition(self, identity: ObjectIdentity) -> NativeSubworkDefinition:
        """Resolve exact retained operands within this parent's completed census."""
        ...

    def iter_completed_output(self, definition: NativeSubworkDefinition, output_id: str, *,
                              maximum_chunk_bytes: int = 1024 * 1024) -> Iterator[bytes]:
        """Read exact receipted output bytes; partial/uncertain work cannot supply them."""
        ...

    def begin(self, definition: NativeSubworkDefinition,
              inputs: tuple[ArtifactManifest, ...] | None = None) -> NativeSubworkEntry: ...

    def contact(self, entry: NativeSubworkEntry) -> None: ...

    def call_entry(self, entry: NativeSubworkEntry, *, at_utc: str) -> None: ...

    def call_return(self, entry: NativeSubworkEntry, *, at_utc: str,
                    error_type: str | None = None, return_code: int | None = None) -> None: ...

    def publish_output(self, entry: NativeSubworkEntry, output_id: str, chunks: Iterable[bytes], *,
                       maximum_bytes: int, maximum_chunk_bytes: int = 1024 * 1024,
                       expected_size_bytes: int | None = None,
                       expected_physical_sha256: str | None = None) -> ArtifactManifest: ...

    def complete(self, entry: NativeSubworkEntry, *, operational_status: OperationalStatus,
                 cost: InquiryCost, cost_scope: str, consumed_streams: tuple[ObjectIdentity, ...] = (),
                 unconsumed_streams: tuple[ObjectIdentity, ...] = (), unknown_streams: tuple[ObjectIdentity, ...] = (),
                 peak_rss_bytes: int | None = None, reason_codes: tuple[str, ...] = ()) -> NativeSubworkInspection: ...
    def freeze_roster(self, roster: NativeSubworkRoster,
                      parent_entry: NativeSubworkEntry | None = None, *,
                      definitions: tuple[NativeSubworkDefinition, ...]) -> None: ...


def native_call_utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def invoke_native_subwork(progress: NativeSubworkProgress, entry: NativeSubworkEntry,
                          invoke, /, *args, **kwargs):
    """Observe only the actual call; later array/custody failures stay separate."""
    try:
        progress.call_entry(entry, at_utc=native_call_utc_now())
    except NativeEntryRefused:
        raise
    except Exception as error:
        raise NativeSubworkObservationPublicationError("native call entry observation publication was not acknowledged") from error
    try:
        result = invoke(*args, **kwargs)
    except BaseException as error:
        returned_at_utc = native_call_utc_now()
        try:
            progress.call_return(entry, at_utc=returned_at_utc, error_type=type(error).__name__)
        except Exception as publication_error:
            raise NativeSubworkObservationPublicationError(
                "native call error observation publication was not acknowledged") from publication_error
        raise
    returned_at_utc = native_call_utc_now()
    try:
        progress.call_return(entry, at_utc=returned_at_utc)
    except Exception as error:
        raise NativeSubworkObservationPublicationError("native call return observation publication was not acknowledged") from error
    return result

