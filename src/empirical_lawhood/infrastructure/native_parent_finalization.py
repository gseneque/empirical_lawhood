# SPDX-License-Identifier: MPL-2.0
"""Authenticate current native returns before ordinary parent publication.

These observations grant no entry or execution authority. The existing producer
must still assemble and validate its ordinary result, under a read-only native
progress port, before the original parent attempt can complete.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from empirical_lawhood.infrastructure.artifact_validation import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkInspection, NativeSubworkReceiptPublicationPending, NativeSubworkRoster, NativeSubworkState,
    NativeSubworkUncertainContact,
)
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork


class NativeParentFinalizationPending(RuntimeError):
    """Current native recovery is incomplete on its original attempt."""


@dataclass(frozen=True, slots=True)
class NativeParentReturn:
    """Authenticated custody observations, never a token or parent receipt."""

    work: PreparedNativeWork
    rosters: tuple[NativeSubworkRoster, ...]
    inspections: tuple[NativeSubworkInspection, ...]
    operational_status: OperationalStatus | None
    reason_codes: tuple[str, ...]
    pending_definition_ids: tuple[ObjectIdentity, ...]

    @property
    def uncertain_contact_definition_ids(self) -> tuple[ObjectIdentity, ...]:
        return tuple(row.definition.identity for row in self.inspections if row.has_uncertain_contact)

    @property
    def pending_publication_definition_ids(self) -> tuple[ObjectIdentity, ...]:
        return tuple(row.definition.identity for row in self.inspections
            if row.native_return_status is not None and row.state is not NativeSubworkState.COMPLETED)

    @property
    def uncontacted_definition_ids(self) -> tuple[ObjectIdentity, ...]:
        return tuple(row.definition.identity for row in self.inspections if row.contact is None)

    @property
    def failed_return_definition_ids(self) -> tuple[ObjectIdentity, ...]:
        return tuple(row.definition.identity for row in self.inspections
            if row.native_return_status is OperationalStatus.FAILED)


def _native_parent_definitions(*, store: ExternalNativeSubworkStore, work: PreparedNativeWork):
    if type(store) is not ExternalNativeSubworkStore or type(work) is not PreparedNativeWork:
        raise TypeError("native parent finalization requires its actual guarded store and prepared work")
    work.__post_init__()
    store.plane.require_verification_snapshot()
    if store.parent_contact != work.expected_parent:
        raise ValueError("native parent finalization substitutes its original prepared contact")
    if not work.definitions:
        raise NativeSubworkUncertainContact("native parent has no declared nested completion census")
    rosters = tuple(sorted(store.iter_rosters(work.expected_parent), key=lambda row: row.roster_id))
    by_roster = {row.roster_id: row for row in rosters}
    if len(by_roster) != len(rosters):
        raise ValueError("native parent finalization repeats a selected roster")
    for expected in work.rosters:
        if by_roster.get(expected.roster_id) != expected:
            raise NativeSubworkUncertainContact("native parent lacks its exact frozen initial roster")
    definitions = tuple(store.read_definition(identity) for roster in rosters for identity in roster.subworks)
    by_identity = {row.identity: row for row in definitions}
    if len(by_identity) != len(definitions) or len({row.subwork_id for row in definitions}) != len(definitions):
        raise ValueError("native parent finalization repeats a selected definition")
    for roster in rosters:
        if any(by_identity[identity].roster_id != roster.roster_id for identity in roster.subworks):
            raise ValueError("native parent finalization substitutes a definition's selected roster")
    if any(by_identity.get(row.identity) != row for row in work.definitions):
        raise ValueError("native parent finalization substitutes its prepared initial definition census")
    # Conditional rosters must remain rooted in this exact prepared denominator.
    reached = set(row.identity for row in work.definitions)
    while True:
        expanded = reached | {identity for roster in rosters if roster.parent_subwork in reached
            for identity in roster.subworks}
        if expanded == reached:
            break
        reached = expanded
    if reached != set(by_identity) or any(row not in work.rosters and row.parent_subwork not in reached
            for row in rosters):
        raise ValueError("native parent finalization has an orphaned conditional roster")
    return rosters, definitions


def _parent_observation(work, rosters, inspections):
    failed = tuple(row for row in inspections if row.state is NativeSubworkState.COMPLETED
        and row.completion.operational_status is OperationalStatus.FAILED)
    pending = tuple(row.definition.identity for row in inspections if row.state is not NativeSubworkState.COMPLETED)
    status = (None if any(row.has_uncertain_contact for row in inspections) else
        OperationalStatus.FAILED if failed else None if pending else OperationalStatus.SUCCEEDED)
    reasons = tuple(sorted({reason for row in failed for reason in row.completion.reason_codes}))
    return NativeParentReturn(work, rosters, inspections, status, reasons, pending)


def _scoped_parent_store(store, work, plane, *, completed_only):
    if type(store) is not ExternalNativeSubworkStore or type(work) is not PreparedNativeWork:
        raise TypeError("native parent inspection requires its actual store and original prepared work")
    if store.parent_contact != work.expected_parent:
        raise ValueError("native parent inspection substitutes its original prepared contact")
    selected = store.parent_contacts.for_task(work.expected_parent.task_id)
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=selected.execution_plan,
        visibility_ceiling=selected.visibility_ceiling, outcome_access=selected.outcome_access,
        minimum_free_bytes=selected.minimum_free_bytes,
        task_scopes={work.expected_parent.task_id: (selected.visibility_ceiling, selected.outcome_access)},
        continuation_scopes=tuple(row for row in selected.continuation_scopes if row.task_id == work.expected_parent.task_id),
    ).for_task(work.expected_parent.task_id)
    return ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts,
        parent_contact=work.expected_parent, parent_inputs=store.parent_inputs, completed_only=completed_only)


def inspect_native_parent_return(*, store: ExternalNativeSubworkStore,
                                 work: PreparedNativeWork) -> NativeParentReturn:
    """Inspect the exact whole census without recovering receipts or entering work.

    Return knowledge, publication completeness and the recorded parent status
    remain separate. An uncertain sibling is retained even beside known returns.
    """
    if type(store) is not ExternalNativeSubworkStore:
        raise TypeError("native parent inspection requires the actual guarded progress owner")
    # Keep this parent's census independent of an enclosing experiment read.
    # Its pure inspection shares immutable members internally; the explicit
    # closing snapshot still authenticates every observed byte before return.
    # Recovery/publication below retains its separate eager effect boundary.
    with store.plane.verification_scope() as scoped_plane, scoped_plane.read_context() as plane:
        scoped = _scoped_parent_store(store, work, plane, completed_only=True)
        rosters, definitions = _native_parent_definitions(store=scoped, work=work)
        inspections = tuple(scoped.inspect(definition) for definition in definitions)
        if tuple(sorted(scoped.iter_rosters(work.expected_parent), key=lambda row: row.roster_id)) != rosters:
            raise ValueError("native parent inspection changed its exact selected roster census")
        plane.require_verification_snapshot()
        return _parent_observation(work, rosters, inspections)


def _authenticate_native_parent_return(*, store: ExternalNativeSubworkStore,
                                       work: PreparedNativeWork) -> NativeParentReturn:
    rosters, definitions = _native_parent_definitions(store=store, work=work)

    # Inspect every declared unit before deciding whether a parent return is
    # known. A failed sibling cannot erase another child's uncertain contact.
    observed = {}
    interrupted_receipts = []
    for definition in definitions:
        try:
            observed[definition.identity] = store.inspect(definition)
        except ArtifactIdentityConflict:
            interrupted_receipts.append(definition)
    if any(row.has_uncertain_contact for row in observed.values()):
        raise NativeSubworkUncertainContact("native parent has a contacted child without a durable known return; no automatic replay")
    publication_failures = []
    for definition in definitions:
        inspection = observed.get(definition.identity)
        if definition in interrupted_receipts or (inspection.state is NativeSubworkState.UNKNOWN_COMPLETION
                and inspection.completion is not None):
            # The normal child receipt writer can finish its own interrupted
            # publication; it cannot infer a native return or reconstruct entry.
            try:
                recovered = store.recover(definition)
            except NativeSubworkReceiptPublicationPending as error:
                publication_failures.append(error)
                continue
            if recovered is None:
                raise NativeSubworkUncertainContact("native parent child lacks authenticated completion custody")
            observed[definition.identity] = recovered
    raw_returns_pending_products = tuple(row for row in observed.values()
        if row.state is NativeSubworkState.UNKNOWN_COMPLETION and row.completion is None
        and row.native_return_status is not None)
    if publication_failures or raw_returns_pending_products:
        # Even deferred receipt conflicts have now been checked. A genuinely
        # unknown contacted sibling or custody refusal takes precedence over a
        # known return whose receipt cannot yet be published.
        store.plane.require_verification_snapshot()
        reason = ("known native return has incomplete durable completion/output custody"
            if raw_returns_pending_products else "known native child receipt publication remains incomplete")
        if any(row.native_return_status is OperationalStatus.FAILED
                for row in raw_returns_pending_products):
            reason += "; original native error/exit observations remain retained"
        raise NativeParentFinalizationPending(reason) from (publication_failures[0] if publication_failures else None)
    inspections = tuple(observed[row.identity] for row in definitions)
    store.plane.require_verification_snapshot()
    return _parent_observation(work, rosters, inspections)


@contextmanager
def completed_native_parent_scope(*, store: ExternalNativeSubworkStore,
                                  work: PreparedNativeWork) -> Iterator[tuple[ExternalNativeSubworkStore, NativeParentReturn]]:
    """Keep authenticated native custody guarded through ordinary publication."""
    if type(store) is not ExternalNativeSubworkStore:
        raise TypeError("native parent finalization requires the actual guarded progress owner")
    with store.plane.verification_scope() as plane:
        scoped = _scoped_parent_store(store, work, plane, completed_only=False)
        observed = _authenticate_native_parent_return(store=scoped, work=work)
        scoped = _scoped_parent_store(store, work, plane, completed_only=True)
        yield scoped, observed
        if scoped.parent_contact != work.expected_parent or tuple(sorted(
                scoped.iter_rosters(work.expected_parent), key=lambda row: row.roster_id)) != observed.rosters:
            raise ValueError("native parent finalization changed its exact parent or selected roster census")


def authenticate_native_parent_return(*, store: ExternalNativeSubworkStore,
                                      work: PreparedNativeWork) -> NativeParentReturn:
    """Read the whole declared census and finish only known child receipts."""
    with completed_native_parent_scope(store=store, work=work) as (_, observed):
        return observed
