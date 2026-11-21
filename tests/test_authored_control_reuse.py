# SPDX-License-Identifier: MPL-2.0
"""Authored typed reuse keeps current access and final complete byte guards."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import sys

import pytest

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.recursive_control_read import decode_authored_control
from empirical_lawhood.storage.recursive_custody import AuthenticatedRecursivePayloads
from empirical_lawhood.science.records import decoding
from tests.runtime_platform.test_recursive_compiler import Config
from tests.test_recursive_member_guard_identity import CurrentAccess
from tests.test_selected_e3_current_access import published_packet


@contextmanager
def _work(path):
    counts = Counter()
    def observe(frame, event, _arg):
        if event != 'call':
            return
        if frame.f_code is read_bounded_bytes.__code__ and Path(frame.f_locals['path']) == path:
            counts['body_reads'] += 1
        if frame.f_code is decoding._decode_canonical_bytes.__code__ and frame.f_locals['record_type'] is Config:
            counts['typed_decodes'] += 1
    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        yield counts
    finally:
        sys.setprofile(previous)


def test_typed_control_reuses_live_bytes_but_later_scope_decodes_again(tmp_path, record_property):
    plane, packet, _ = published_packet(tmp_path)
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    work = []
    retained = []
    for legacy in (True, False, False):
        access = CurrentAccess()
        with plane.read_context() as reading:
            payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                members=packet.members, original_input_access=access)
            options = {'read_payload': payloads.__getitem__} if legacy else {}
            with _work(directory / 'private.json') as counts:
                first = decode_authored_control(payloads, 'private.json', Config, **options)
                before = access.calls
                second = decode_authored_control(payloads, 'private.json', Config, **options)
                assert access.calls > before
                assert first is second
            retained.append(first)
            work.append(dict(counts))
    assert retained[0] == retained[1] == retained[2]
    assert retained[1] is not retained[2]
    assert work == [dict(body_reads=2, typed_decodes=1),
        dict(body_reads=1, typed_decodes=1), dict(body_reads=1, typed_decodes=1)]
    record_property('authored_control_work', work)


@pytest.mark.parametrize('damage', ('selected', 'sibling', 'revoked', 'limit', 'revision', 'member-pin'))
def test_reused_authored_control_keeps_current_and_final_refusals(tmp_path, damage):
    plane, packet, _ = published_packet(tmp_path)
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    access = CurrentAccess()
    with pytest.raises((ValueError, RuntimeError, PermissionError)):
        with plane.read_context() as reading:
            payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory,
                members=packet.members, original_input_access=access)
            original = decode_authored_control(payloads, 'private.json', Config)
            assert original is not None
            if damage == 'revoked':
                access.allowed = False
            elif damage == 'member-pin':
                member = payloads._members['private.json']
                payloads._members['private.json'] = replace(member,
                    identity=replace(member.identity, object_fingerprint='b' * 64))
            elif damage in ('selected', 'sibling'):
                path = directory / ('private.json' if damage == 'selected' else 'draft.json')
                raw = path.read_bytes()
                path.write_bytes(raw.replace(b'config.', b'broken.', 1))
            kind = Config
            if damage == 'revision':
                class Changed(Config):
                    VERSION = '2.0.0'
                kind = Changed
            decode_authored_control(payloads, 'private.json', kind,
                maximum_bytes=1 if damage == 'limit' else None)


@pytest.mark.parametrize('hook', ('payload', 'plane'))
def test_custom_authored_read_hooks_remain_eager(tmp_path, monkeypatch, hook):
    plane, packet, _ = published_packet(tmp_path)
    directory = Path(plane.root.contract.canonical_path) / 'authored'
    calls = []
    with plane.read_context() as reading:
        payloads = AuthenticatedRecursivePayloads(plane=reading, directory=directory, members=packet.members)
        if hook == 'payload':
            original = payloads.__getitem__
            def custom(name):
                calls.append(name)
                return original(name)
            monkeypatch.setattr(payloads, '__getitem__', custom)
        else:
            original = reading.verify_manifest
            def custom(*args, **kwargs):
                calls.append(args[0])
                return original(*args, **kwargs)
            monkeypatch.setattr(reading, 'verify_manifest', custom)
        first = decode_authored_control(payloads, 'private.json', Config)
        second = decode_authored_control(payloads, 'private.json', Config)
        assert first == second and len(calls) >= 2
