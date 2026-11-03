# SPDX-License-Identifier: MPL-2.0
"""An explicit separate attempt scope; original uncertain custody is immutable."""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .artifacts import validate_relative_locator
from .development_controller_repair import DevelopmentControllerRepair
from .development_output_repair import DevelopmentOutputRepairRecoveryIndex
from .native_continuation_proposal import DevelopmentNativeContinuationProposal
from .native_effects import NativeEffectContact
from .recovery import DevelopmentRunRecoveryTerminalEvent


@dataclass(frozen=True, slots=True)
class NativeContinuationCustodyScope(CanonicalRecord):
    """One new attempt's storage namespace, never scientific entry authority."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/native-continuation-custody-scope'
    continuation: ObjectIdentity
    original_contact: NativeEffectContact
    attempt_id: str

    def __post_init__(self):
        if type(self.continuation) is not ObjectIdentity or (
                self.continuation.object_schema, self.continuation.object_version) != (
                DevelopmentNativeContinuation.SCHEMA, DevelopmentNativeContinuation.VERSION):
            raise ValueError('native continuation custody requires its exact continuation binding')
        if type(self.original_contact) is not NativeEffectContact:
            raise TypeError('native continuation custody requires its exact original contact')
        self.original_contact.__post_init__()
        validate_stable_id(self.attempt_id)
        if self.attempt_id == self.original_contact.attempt_id:
            raise ValueError('native continuation custody cannot reuse the original attempt')

    @property
    def task_id(self):
        return self.original_contact.task_id

    @property
    def expected_contact(self):
        return replace(self.original_contact, attempt_id=self.attempt_id)

    @property
    def relative_root(self):
        return f'runs/{self.original_contact.run_id}/native-continuations/{self.continuation.object_id}'

    def storage_key(self, original_key):
        return sha256((self.continuation.object_fingerprint + ':' + original_key).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class DevelopmentNativeContinuation(DevelopmentControllerRepair):
    """One explicit continuation retains, rather than relabels, old contacts."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-native-continuation'
    proposal: DevelopmentNativeContinuationProposal
    proposal_relative_path: str

    def __post_init__(self):
        super(DevelopmentNativeContinuation, self).__post_init__()
        if type(self.proposal) is not DevelopmentNativeContinuationProposal:
            raise TypeError('native continuation requires its exact reviewed proposal')
        self.proposal.__post_init__()
        validate_relative_locator(self.proposal_relative_path)
        if (self.proposal.execution_plan, self.proposal.original_index, self.proposal.worker,
                self.proposal.worker_environment, self.proposal.worker_source_root,
                self.proposal.completed_receipts, self.proposal.pure_output_bytes) != (
                self.execution_plan, self.original_index, self.worker, self.worker_environment,
                self.worker_source_root, self.completed_receipts, self.output_bytes):
            raise ValueError('native continuation changes its reviewed original selection')
        if (not set(self.continued_native_task_ids) <= set(self.pending_task_ids)
                or set(self.continued_native_task_ids) & (set(self.uncontacted_native_task_ids) | set(self.output_task_ids))):
            raise ValueError('native continuation cannot relabel uncertain contact as uncontacted or PURE')
        if tuple(key for key, _ in self.completed_native_contacts) != self.proposal.completed_native_task_ids:
            raise ValueError('native continuation changes its complete retained native successes')

    @property
    def continued_native_task_ids(self):
        return tuple(row.task_id for row in self.proposal.candidates)

    def custody_scopes(self, index):
        if type(index) is not DevelopmentNativeContinuationRecoveryIndex or index.repair != self:
            raise TypeError('native continuation custody requires its exact derived index')
        identity = self.identity
        return tuple(NativeContinuationCustodyScope(identity, candidate.invocation.expected_parent_contact,
            index.task(candidate.task_id).attempts[0].attempt_id) for candidate in self.proposal.candidates)


@dataclass(frozen=True, slots=True)
class DevelopmentNativeContinuationRecoveryIndex(DevelopmentOutputRepairRecoveryIndex):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-native-continuation-recovery-index'
    TERMINAL_EVENT_SCHEMA: ClassVar[str] = 'empirical-lawhood/runtime/development-native-continuation-terminal-event'
    REPAIR_TYPE: ClassVar[type] = DevelopmentNativeContinuation
    repair: DevelopmentNativeContinuation


@dataclass(frozen=True, slots=True)
class DevelopmentNativeContinuationTerminalEvent(DevelopmentRunRecoveryTerminalEvent):
    SCHEMA: ClassVar[str] = DevelopmentNativeContinuationRecoveryIndex.TERMINAL_EVENT_SCHEMA
    RECOVERY_INDEX_SCHEMA: ClassVar[str] = DevelopmentNativeContinuationRecoveryIndex.SCHEMA


def native_continuation_scopes(index):
    if type(index) is DevelopmentNativeContinuationRecoveryIndex:
        return index.repair.custody_scopes(index)
    return ()
