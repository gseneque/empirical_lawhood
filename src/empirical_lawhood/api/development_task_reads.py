# SPDX-License-Identifier: MPL-2.0
"""Independent finite DEV preparation reads; never reusable access verdicts."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from threading import RLock, get_ident

from empirical_lawhood.infrastructure.artifacts import (
    ConcurrentArtifactMemberPreflight, ExternalArtifactPlane, GuardedExternalRoot,
    LocalFilesystemInspector, _has_stock_artifact_plane_state, _has_stock_manifest_reads,
)


@dataclass
class _DevelopmentRead:
    owner: object
    writer: object
    facts: set
    receipts: dict = field(default_factory=dict)
    thread_id: int = field(default_factory=get_ident)


_READ = ContextVar('current_development_task_read', default=None)


def development_read_call(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        with self.task_read_scope():
            return method(self, *args, **kwargs)
    return guarded


class DevelopmentTaskReadScopes:
    """Separate mutable read state without changing the public custody owner."""

    def _task_read(self):
        reading = _READ.get()
        return reading if reading is not None and reading.owner is self and reading.thread_id == get_ident() else None

    @property
    def writer(self):
        reading = self._task_read()
        return self._writer if reading is None else reading.writer

    @writer.setter
    def writer(self, value):
        self._writer = value

    @property
    def _original_member_facts(self):
        reading = self._task_read()
        return self._retained_member_facts if reading is None else reading.facts

    @_original_member_facts.setter
    def _original_member_facts(self, value):
        self._retained_member_facts = value

    def _independent_reads_supported(self):
        plane = self._writer
        return (type(plane) is ExternalArtifactPlane and _has_stock_manifest_reads(plane)
            and _has_stock_artifact_plane_state(plane) and type(plane.root) is GuardedExternalRoot
            and type(plane.root.inspector) is LocalFilesystemInspector)

    def initialize_task_reads(self):
        """Call only after the actual authored plan and input census close."""
        self._initial_member_facts = frozenset(self._retained_member_facts)
        self._facts_lock = RLock()
        owners = {}
        for task in self.plan.tasks:
            for output in task.outputs:
                owners.setdefault(output.logical_artifact_id, []).append(task)
        self._output_owners = {key: tuple(values) for key, values in owners.items()}
        self._concurrent_member_guard = ConcurrentArtifactMemberPreflight(self._concurrent_input_member, self.task_read_scope)
        self._ordinary_member_guard = self.require_input_member

    @property
    def member_preflight(self):
        if hasattr(self, '_initial_member_facts') and self._independent_reads_supported():
            return self._concurrent_member_guard
        return getattr(self, '_ordinary_member_guard', self.require_input_member)

    def _concurrent_input_member(self, manifest):
        if not self._independent_reads_supported():
            raise PermissionError('concurrent development custody changed its ordinary read policy')
        self.require_input_member(manifest)

    @contextmanager
    def task_read_scope(self):
        """Reuse only this call's exact facts; close all bytes before returning.

        Each task thread has a separate plane, authority reader and receipt
        DAG. Worker delivery remains with the scheduler's eager input owner.
        Custom readers keep their existing calls and serialization policy.
        """
        if (self._task_read() is not None or not hasattr(self, '_initial_member_facts')
                or not self._independent_reads_supported()):
            yield self
            return
        from .selected_e3_access import original_e3_authority_read_context
        original = self._writer
        # The scheduler owns the eight task slots. A task's small metadata
        # reads must not create another eight-worker pool inside each slot.
        plane = ExternalArtifactPlane(original.root, original.validators, original.semantic_validations,
            custody_limits=original.custody_limits, artifact_verification=original.artifact_verification)
        state = _DevelopmentRead(self, plane, set(self._initial_member_facts))
        token = _READ.set(state)
        try:
            with original_e3_authority_read_context(plane), plane.read_context() as reading:
                state.writer = reading
                self._require_current_original_access()
                yield self
                self._require_current_original_access()
            # These facts remain available for the existing metadata observers.
            # A later call still starts from original inputs and rejoins receipts.
            with self._facts_lock:
                self._retained_member_facts.update(state.facts)
        finally:
            _READ.reset(token)
            state.receipts.clear()
            state.facts.clear()
