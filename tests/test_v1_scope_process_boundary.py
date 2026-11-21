# SPDX-License-Identifier: MPL-2.0
"""A child must obtain fresh custody even when fork copies an active view."""

import multiprocessing
from threading import Event, Thread

import pytest

from tests.runtime_platform.test_artifact_verification_scope import _publication


def _child(scoped, original, manifest, channel):
    from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict
    checks = {}
    operations = {
        "lifetime": scoped.require_active_verification_scope,
        "snapshot": scoped.require_verification_snapshot,
        "metadata": lambda: scoped.read_manifest(manifest.materialization.relative_path),
        "members": lambda: scoped.verify_manifest_members(manifest,
            validate_members=lambda _members: None, before_member=lambda _member: None),
    }
    try:
        for name, operation in operations.items():
            try:
                operation()
            except ArtifactIdentityConflict:
                checks[name] = "REFUSED"
            else:
                checks[name] = "INHERITED"
        # The original unscoped plane can still create its own process-local
        # lifetime and authenticate the complete original publication afresh.
        with original.read_context() as fresh:
            fresh.verify_manifest(manifest)
            fresh.require_verification_snapshot()
        checks["fresh_scope"] = "VERIFIED"
        channel.send(checks)
    finally:
        channel.close()


@pytest.mark.skipif("fork" not in multiprocessing.get_all_start_methods(), reason="fork-specific inherited state control")
@pytest.mark.parametrize("context", ("verification_scope", "read_context"))
def test_forked_process_refuses_inherited_proof_but_accepts_fresh_lifetime(tmp_path, context):
    plane, (manifest,) = _publication(tmp_path, 1)
    fork = multiprocessing.get_context("fork")
    parent, child = fork.Pipe(duplex=False)
    with getattr(plane, context)() as scoped:
        scoped.verify_manifest(manifest)
        process = fork.Process(target=_child, args=(scoped, plane, manifest, child))
        process.start()
        child.close()
        try:
            assert parent.poll(20), "child custody check did not finish"
            result = parent.recv()
            process.join(20)
            assert process.exitcode == 0
            assert result == {"lifetime": "REFUSED", "snapshot": "REFUSED",
                "metadata": "REFUSED", "members": "REFUSED", "fresh_scope": "VERIFIED"}
        finally:
            parent.close()
            if process.is_alive():
                process.kill()
                process.join(5)
        # The original parent's lifetime remains valid.
        scoped.verify_manifest(manifest)


def _child_warmed_pool(inherited, channel):
    from empirical_lawhood.storage.parallel_verification import canonical_validation_scope
    try:
        inherited.close()  # Must not touch copied parent locks or workers.
        try:
            with canonical_validation_scope(1, shared_pool=inherited):
                pass
        except RuntimeError:
            explicit = "REFUSED"
        else:
            explicit = "INHERITED"
        with canonical_validation_scope(1) as fresh:
            result = fresh.project_ordered(abs, (-2,))
        channel.send((explicit, result))
    finally:
        channel.close()


@pytest.mark.skipif("fork" not in multiprocessing.get_all_start_methods(), reason="fork-specific pool lifetime control")
def test_warmed_pool_fork_uses_new_child_pool_and_preserves_parent():
    from empirical_lawhood.storage.parallel_verification import canonical_validation_scope
    fork = multiprocessing.get_context("fork")
    parent, child = fork.Pipe(duplex=False)
    with canonical_validation_scope(1) as original:
        assert original.project_ordered(abs, (-1,)) == (1,)
        process = fork.Process(target=_child_warmed_pool, args=(original, child))
        process.start()
        child.close()
        try:
            assert parent.poll(15), "fresh child pool did not finish"
            assert parent.recv() == ("REFUSED", (2,))
            process.join(3)
            assert process.exitcode == 0
        finally:
            parent.close()
            if process.is_alive():
                process.kill()
                process.join(3)
        assert original.project_ordered(abs, (-3,)) == (3,)


def _child_locked_ledger(inherited, plane, manifests, channel):
    from empirical_lawhood.storage.artifact_verification import artifact_verification_operation
    from tests.test_reduced_artifact_verification import _work
    try:
        checks = {}
        for name, operation in {
            "get": lambda: inherited.get(("foreign",)),
            "put": lambda: inherited.put(("foreign",), ("descriptor",), None),
        }.items():
            try:
                operation()
            except RuntimeError:
                checks[name] = "REFUSED"
            else:
                checks[name] = "INHERITED"
        inherited.close()
        with artifact_verification_operation() as fresh, _work() as work:
            checks["fresh"] = fresh is not inherited
            with plane.read_context() as reading:
                reading.verify_manifests(manifests)
        checks["deep_validations"] = work["deep_validations"]
        checks["final_hashes"] = work["checkpoint_hashes"]
        channel.send(checks)
    finally:
        channel.close()


@pytest.mark.skipif("fork" not in multiprocessing.get_all_start_methods(), reason="fork-specific ledger lifetime control")
def test_fork_with_parent_thread_holding_ledger_lock_authenticates_child_afresh(tmp_path):
    from empirical_lawhood.storage.artifact_verification import artifact_verification_operation
    from tests.test_reduced_artifact_verification import _case
    plane, manifests = _case(tmp_path, count=2)
    fork = multiprocessing.get_context("fork")
    parent, child = fork.Pipe(duplex=False)
    acquired, release = Event(), Event()
    with artifact_verification_operation() as ledger:
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)

        assert ledger.proofs
        def hold_parent_lock():
            with ledger.lock:
                acquired.set()
                release.wait(20)
        thread = Thread(target=hold_parent_lock)
        thread.start()
        assert acquired.wait(5)
        process = fork.Process(target=_child_locked_ledger, args=(ledger, plane, manifests, child))
        try:
            process.start()
            child.close()
            assert parent.poll(10), "child waited on copied parent verification lock"
            assert parent.recv() == {
                "get": "REFUSED", "put": "REFUSED", "fresh": True,
                "deep_validations": 2, "final_hashes": 5}
            process.join(3)
            assert process.exitcode == 0
        finally:
            parent.close()
            if process.is_alive():
                process.kill()
                process.join(3)
            release.set()
            thread.join(3)
        assert ledger.active and ledger.proofs
        with plane.read_context() as reading:
            reading.verify_manifests(manifests)


def _child_locked_record_store(inherited, original, key, channel):
    from empirical_lawhood.science.records.decoded_record_store import (
        current_decoded_record_store, decoded_record_scope, decode_scoped_canonical_bytes)
    try:
        checks = {"foreign_current_hidden": current_decoded_record_store() is None}
        for name, operation in {"get": lambda: inherited.get(key),
                                "put": lambda: inherited.put(key, original)}.items():
            try:
                operation()
            except RuntimeError:
                checks[name] = "REFUSED"
            else:
                checks[name] = "INHERITED"
        # Exercise the actual weakref callback as well as explicit cleanup.
        reference = inherited.records[key]
        reference.__callback__(reference)
        inherited.close()
        with decoded_record_scope() as fresh:
            raw = original.canonical_bytes()
            result = decode_scoped_canonical_bytes(raw, type(original), maximum_bytes=len(raw))
            checks.update(fresh=fresh is not inherited, decoded_again=result is not original,
                          same_bytes=result.canonical_bytes() == raw)
        channel.send(checks)
    finally:
        channel.close()


@pytest.mark.skipif("fork" not in multiprocessing.get_all_start_methods(), reason="fork-specific decoded-record lifetime control")
def test_fork_with_parent_thread_holding_record_store_lock_decodes_child_afresh():
    from empirical_lawhood.science.records.decoded_record_store import decoded_record_scope, record_store_key
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    value = ObjectIdentity("exposed.record-store", ObjectIdentity.SCHEMA, "1.0.0", "a" * 64)
    key = record_store_key(type(value), value.fingerprint(), len(value.canonical_bytes()))
    fork = multiprocessing.get_context("fork")
    parent, child = fork.Pipe(duplex=False)
    acquired, release = Event(), Event()
    with decoded_record_scope() as store:
        store.put(key, value)
        def hold_parent_lock():
            with store.lock:
                acquired.set()
                release.wait(20)
        thread = Thread(target=hold_parent_lock)
        thread.start()
        assert acquired.wait(5)
        process = fork.Process(target=_child_locked_record_store, args=(store, value, key, child))
        try:
            process.start()
            child.close()
            assert parent.poll(10), "child waited on copied parent decoded-record lock"
            assert parent.recv() == {"foreign_current_hidden": True, "get": "REFUSED", "put": "REFUSED",
                                     "fresh": True, "decoded_again": True, "same_bytes": True}
            process.join(3)
            assert process.exitcode == 0
        finally:
            parent.close()
            if process.is_alive():
                process.kill()
                process.join(3)
            release.set()
            thread.join(3)
        assert store.get(key) is value


def _child_locked_preflight(plane, manifest, channel):
    from empirical_lawhood.storage.artifacts import ArtifactIdentityConflict, ExternalArtifactPlane
    try:
        try:
            with plane.read_context(before_member=lambda _manifest: None) as reading:
                reading.verify_manifest(manifest)
        except ArtifactIdentityConflict as error:
            refused = "construct a child artifact plane" in str(error)
        else:
            refused = False
        child_plane = ExternalArtifactPlane(plane.root, plane.validators, plane.semantic_validations,
            custody_limits=plane.custody_limits,
            maximum_parallel_verifications=plane.maximum_parallel_verifications,
            artifact_verification=plane.artifact_verification)
        accessed = []
        def access(selected):
            accessed.append(selected.logical.logical_artifact_id)
        with child_plane.read_context(before_member=access) as reading:
            reading.verify_manifest(manifest)
        channel.send({"inherited_callback_plane_refused": refused,
                      "fresh_callback_invoked": bool(accessed)})
    finally:
        channel.close()


@pytest.mark.skipif("fork" not in multiprocessing.get_all_start_methods(), reason="fork-specific access callback lock control")
def test_fork_refuses_inherited_callback_lock_and_accepts_child_owned_plane(tmp_path):
    plane, (manifest,) = _publication(tmp_path, 1)
    fork = multiprocessing.get_context("fork")
    parent, child = fork.Pipe(duplex=False)
    acquired, release = Event(), Event()
    def hold_parent_lock():
        with plane._verification_preflight_lock:
            acquired.set()
            release.wait(20)
    thread = Thread(target=hold_parent_lock)
    thread.start()
    assert acquired.wait(5)
    process = fork.Process(target=_child_locked_preflight, args=(plane, manifest, child))
    try:
        process.start()
        child.close()
        assert parent.poll(10), "child waited on copied parent access callback lock"
        assert parent.recv() == {"inherited_callback_plane_refused": True, "fresh_callback_invoked": True}
        process.join(3)
        assert process.exitcode == 0
    finally:
        parent.close()
        if process.is_alive():
            process.kill()
            process.join(3)
        release.set()
        thread.join(3)
    with plane.read_context(before_member=lambda _manifest: None) as reading:
        reading.verify_manifest(manifest)
