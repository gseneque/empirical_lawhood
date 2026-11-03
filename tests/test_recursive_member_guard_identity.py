# SPDX-License-Identifier: MPL-2.0
"""Bounded guard registration with fresh reads; exposed software custody only."""
import json
from pathlib import Path
from weakref import ref

import pytest

from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads
from tests.test_selected_e3_current_access import published_packet


class CurrentAccess:
    def __init__(self):
        self.calls = 0
        self.allowed = True

    def require_current(self):
        self.calls += 1
        if not self.allowed:
            raise PermissionError('current original access revoked')

    def require_member(self, manifest):
        self.require_current()


@pytest.mark.parametrize('operation', ('getitem', 'chunks'))
def test_repeated_payload_reads_keep_one_guard_and_fresh_access(tmp_path, operation):
    plane, packet, _ = published_packet(tmp_path)
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    expected = (directory / 'private.json').read_bytes()
    access = CurrentAccess()
    work = []
    with plane.read_context() as reading:
        payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
            members=packet.members, original_input_access=access)
        for _ in range(8):
            before = access.calls
            actual = (payloads['private.json'] if operation == 'getitem'
                else b''.join(payloads.chunks('private.json')))
            assert actual == expected
            work.append(access.calls - before)
        guards = reading._read_verification.member_preflights
        census = [len(rows) for rows in guards.values()]
        (tmp_path / 'guard-work.json').write_text(json.dumps({
            'operation': operation, 'fresh_checks_per_read': work,
            'guards_per_member': census, 'native_execution': False,
        }, sort_keys=True) + '\n')
        assert work[0] > 0 and work == [work[0]] * len(work)
        assert census and set(census) == {1}
        access.allowed = False
        with pytest.raises(PermissionError, match='access revoked'):
            payloads['private.json']
        access.allowed = True
    assert (directory / 'private.json').read_bytes() == expected


@pytest.mark.parametrize('target', ('instance', 'class'))
def test_changed_payload_guard_is_not_hidden_by_stable_registration(tmp_path, monkeypatch, target):
    plane, packet, _ = published_packet(tmp_path)
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    access = CurrentAccess()
    with pytest.raises(PermissionError, match='replacement member guard'):
        with plane.read_context() as reading:
            payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                members=packet.members, original_input_access=access)
            payloads['private.json']

            def replacement(*args):
                raise PermissionError('replacement member guard refused')

            monkeypatch.setattr(payloads if target == 'instance' else AuthenticatedRecursivePayloads,
                '_before_member', replacement)
            payloads['private.json']


def test_distinct_payload_owners_retain_each_current_guard(tmp_path):
    plane, packet, _ = published_packet(tmp_path)
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    first, second = CurrentAccess(), CurrentAccess()
    with pytest.raises(PermissionError, match='access revoked'):
        with plane.read_context() as reading:
            left = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                members=packet.members, original_input_access=first)
            right = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                members=packet.members, original_input_access=second)
            left['private.json']
            right['private.json']
            first.allowed = False
            right['private.json']


def test_guard_lookup_does_not_extend_payload_lifetime(tmp_path):
    plane, packet, _ = published_packet(tmp_path)
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    with plane.read_context() as reading:
        payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
            members=packet.members, original_input_access=CurrentAccess())
        payloads['private.json']
        observed = ref(payloads)
    del payloads
    assert observed() is None
