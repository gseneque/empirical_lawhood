# SPDX-License-Identifier: MPL-2.0
"""Prepare immutable scientific selections for one registered inquiry read.

This is the operand lifetime used by inquiry hooks, not a custody cache. Each
new invocation repeats the owning selector. No read or access verdict is held.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from empirical_lawhood.science.records.decoded_record_store import record_store_key
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft

_selections = ContextVar('prepared_inquiry_selections', default=())


class _Selection:
    def __init__(self, draft, records, policy):
        self.draft, self.records, self.policy = draft, records, policy
        self.active = True

    def close(self):
        # A copied context must neither retain these bodies nor reuse the
        # original selector after its invocation has returned.
        self.active = False
        self.draft = self.policy = None
        self.records = ()


@dataclass(frozen=True, slots=True)
class InquirySelectionPreparation:
    prepare: object
    record_types: tuple[type[CanonicalRecord], ...]
    validators: tuple[object, ...]

    def __post_init__(self):
        if (not callable(self.prepare) or type(self.record_types) is not tuple or not self.record_types
                or any(not isinstance(kind, type) or not issubclass(kind, CanonicalRecord)
                    for kind in self.record_types)
                or type(self.validators) is not tuple or any(not callable(value) for value in self.validators)):
            raise TypeError('inquiry selection requires its registered record types and validation owners')

    def _policy(self, draft):
        if type(draft) is not RecursiveStudyDraft or not draft._is_cacheable():
            return None
        keys = tuple(record_store_key(kind, '', 0) for kind in (RecursiveStudyDraft, *self.record_types))
        return None if any(key is None for key in keys) else (self, *keys)

    def _prepare(self, draft):
        records = self.prepare(draft)
        if (type(records) is not tuple or not records
                or any(type(record) not in self.record_types for record in records)):
            raise TypeError('inquiry selection owner must return its complete immutable record tuple')
        return records

    def read(self, draft):
        policy = self._policy(draft)
        if policy is not None:
            for selection in reversed(_selections.get()):
                if selection.active and selection.draft is draft and selection.policy == policy:
                    return selection.records
        return self._prepare(draft)

    @contextmanager
    def scope(self, draft):
        policy = self._policy(draft)
        records = self.read(draft)
        if policy is None or not all(record._is_cacheable() for record in records):
            yield records
            return
        selection = _Selection(draft, records, policy)
        token = _selections.set((*_selections.get(), selection))
        try:
            yield records
        finally:
            selection.close()
            _selections.reset(token)
